"""
Definition of the Producer class
"""

import logging
import functools
import datetime
import six
from socket import gaierror
from duologsync.util import get_log_offset, run_in_executor, restless_sleep, normalize_params
from duologsync.config import Config
from duologsync.program import Program, ProgramShutdownError

class Producer():
    """
    Read data from a specific log endpoint via an API call at a polling
    duration that is user specified. The data is published to a queue which
    is only used for data of the same log type, and offset information is
    recorded to allow checkpointing and recovery from a crash.
    """

    def __init__(self, api_call, log_queue, log_type, account_id=None, url_path=None):
        self.api_call = api_call
        self.log_queue = log_queue
        self.log_type = log_type
        self.account_id = account_id
        self.log_offset = get_log_offset(
            self.log_type,
            Config.get_checkpointing_enabled(),
            Config.get_checkpoint_dir(),
            self.account_id)
        self.url_path = url_path

    async def produce(self):
        """
        The main function of this class and subclasses. Runs a loop, sleeping
        for the polling duration then making an API call, consuming the logs
        from that API call and saving the offset of the latest log read.
        """

        # Exit when DuoLogSync is shutting down (due to error or Ctrl-C)
        while Program.is_running():
            shutdown_reason = None
            Program.log(f"{self.log_type} producer: fetching next logs after "
                        f"{Config.get_api_timeout()} seconds",
                        logging.INFO)

            try:
                # Sleep for api_timeout amount of time, but check for program
                # shutdown every second
                await restless_sleep(Config.get_api_timeout())
                Program.log(f"{self.log_type} producer: fetching logs",
                            logging.INFO)
                api_result = await self.call_log_api()
                if api_result:
                    await self.add_logs_to_queue(self.get_logs(api_result))
                else:
                    Program.log(f"{self.log_type} producer: no new logs available",
                                logging.INFO)

            # Horribly messed up hostname was provided for duoclient host
            except (gaierror, OSError) as error:
                shutdown_reason = f"{self.log_type} producer: [{error}]"
                Program.log('DuoLogSync: check that the duoclient host '
                            'provided in the config file is correct')

            # duo_client throws a RuntimeError if the ikey or skey is invalid
            except RuntimeError as runtime_error:
                shutdown_reason = f"{self.log_type} producer: [{runtime_error}]"
                Program.log('DuoLogSync: check that the duoclient ikey and '
                            'skey in the config file are correct')

            # Shutdown hath been noticed and thus shutdown shall begin
            except ProgramShutdownError:
                break

            if shutdown_reason:
                Program.initiate_shutdown(shutdown_reason)

        # Unblock consumer but putting anything in the shared queue
        await self.log_queue.put([])
        Program.log(f"{self.log_type} producer: shutting down", logging.INFO)

    async def add_logs_to_queue(self, logs):
        """
        If logs is not none, add them to this Writer's queue

        @param logs The logs to be added
        """

        # Important for recovery in the event of a crash
        self.log_offset = Producer.get_log_offset(logs, current_log_offset=self.log_offset)

        # Authlogs v2 endpoint returns dict response
        if isinstance(logs, dict):
            logs = logs['authlogs']

        Program.log(f"{self.log_type} producer: adding {len(logs)} "
                    "logs to the queue", logging.INFO)

        await self.log_queue.put(logs)
        Program.log(f"{self.log_type} producer: added {len(logs)} "
                    "logs to the queue", logging.INFO)

    async def call_log_api(self):
        """
        Make a call to a log-specific API and return the API result. The default
        implementation given here will not suffice for every type of log API and
        so should be overriden by a child clas when necessary.

        @return the result of the API call
        """

        if Config.account_is_msp():
            # Make an API call to retrieve authlog logs for MSP accounts
            parameters = {"mintime": six.ensure_str(str(self.log_offset)),
                          "account_id": six.ensure_str(self.account_id)}

            api_result = await run_in_executor(
                functools.partial(
                    self.api_call,
                    method="GET",
                    path=self.url_path,
                    params=parameters
                )
            )
        else:
            api_result = await run_in_executor(
                functools.partial(
                    self.api_call,
                    mintime=self.log_offset
                )
            )

        return api_result

    @staticmethod
    def get_logs(api_result):
        """
        Perform an action to retrieve logs from a log-specific api_result. The
        default implementation given here will not suffice for every type of
        log API and so should be overriden by a child class when necessary.

        @param api_result   The result of an API call

        @return the logs contained within api_result
        """

        # No need to rewrite this function if api_result is a conatiner of logs
        return api_result

    @staticmethod
    def get_log_offset(log, current_log_offset=None):
        """
        Get offset information given an individual log.

        @param log  Individual log from which to get offset information

        @return the offset of the log
        """

        # In case of authlogs, dict is returned as response. So we check for that and record
        # information from metadata field. This is applicable for producer log offset
        # Elif loops are considered when offset is calculated for checkpointing. Here logs will be
        # of type dict. Authlog will have txid field in addition to timestamp field which can be
        # used for identification. Direct timestamp field cannot be used since it loses precision.
        # Hence calculating timestamp from isotimestamp field.
        if isinstance(log, dict):
            if log.get('authlogs') and log.get('metadata').get('next_offset') is not None:
                return log.get('metadata').get('next_offset')

            if log.get('isotimestamp') and log.get('txid'):
                value = int((datetime.datetime.strptime
                             (six.ensure_str(log.get('isotimestamp')),
                              "%Y-%m-%dT%H:%M:%S.%f+00:00") - datetime.datetime(1970, 1, 1)).
                            total_seconds() * 1000)
                return [six.ensure_str(str(value)), log.get('txid')]

            if log.get('timestamp'):
                return log.get('timestamp') + 1

            return current_log_offset

        else:
            timestamp = log[-1]['timestamp']
            return timestamp + 1
