"""
Definition of the Producer class
"""

import logging
import functools
from socket import gaierror
from duologsync.util import get_log_offset, run_in_executor, restless_sleep
from duologsync.config import Config
from duologsync.program import Program

class Producer():
    """
    Read data from a specific log endpoint via an API call at a polling
    duration that is user specified. The data is published to a queue which
    is only used for data of the same log type, and offset information is
    recorded to allow checkpointing and recovery from a crash.
    """

    def __init__(self, api_call, log_queue, log_type):
        self.api_call = api_call
        self.log_queue = log_queue
        self.log_type = log_type
        self.log_offset = get_log_offset(
            self.log_type,
            Config.get_recover_log_offset(),
            Config.get_checkpoint_directory())

    async def produce(self):
        """
        The main function of this class and subclasses. Runs a loop, sleeping
        for the polling duration then making an API call, consuming the logs
        from that API call and saving the offset of the latest log read.
        """

        # Exit when DuoLogSync is shutting down (due to error or Ctrl-C)
        while Program.is_running():
            Program.log(f"{self.log_type} producer: begin polling for "
                        f"{Config.get_polling_duration()} seconds",
                        logging.INFO)
            await restless_sleep(Config.get_polling_duration())

            # Time to shutdown
            if not Program.is_running():
                continue

            Program.log(f"{self.log_type} producer: fetching logs after "
                        f"{Config.get_polling_duration()} seconds",
                        logging.INFO)

            api_result = await self.call_log_api_safely()
            new_logs = self.get_logs(api_result)

            if new_logs:
                # Important for recovery in the event of a crash
                self.log_offset = self.get_api_result_offset(api_result)

                Program.log(f"{self.log_type} producer: adding {len(new_logs)} "
                            "logs to the queue", logging.INFO)
                await self.log_queue.put(new_logs)
                Program.log(f"{self.log_type} producer: added {len(new_logs)} "
                            "logs to the queue", logging.INFO)

            else:
                Program.log(f"{self.log_type} producer: no new logs available",
                            logging.INFO)

        # Put anything in the queue to unblock the consumer, since the
        # consumer will not be able to do anything until an item is
        # added to the queue
        await self.log_queue.put([])
        Program.log(f"{self.log_type} producer: shutting down", logging.INFO)

    async def call_log_api_safely(self):
        """
        Wrapper for the call_log_api function with error handling
        """

        shutdown_reason = None

        try:
            api_result = await self.call_log_api()

        # gai_error thrown for invalid hostnames
        except gaierror as gai_error:
            shutdown_reason = (
                f"{self.log_type} producer: ran into the "
                f"following error [{gai_error}]"
            )

            # Error with the Socket using the hostname provided
            if gai_error.errno is not None and gai_error.errno == 8:
                Program.log('DuoLogSync: check that the duoclient host provided'
                            ' in the config file is correct')

        # OSError will be thrown if a horribly messed up hostname is given
        except OSError as os_error:
            shutdown_reason = (
                f"{self.log_type} producer: ran into the "
                f"following error [{os_error}]"
            )

            # No route to host, issue with hostname given
            if os_error.errno is not None and os_error.errno == 65:
                Program.log('DuoLogSync: check that the duoclient host provided'
                            ' in the config file is correct')

        # duo_client will throw a RuntimeError if the integration key or
        # secret key is invalid
        except RuntimeError as runtime_error:
            shutdown_reason = (
                f"{self.log_type} producer: ran into the "
                f"following error [{runtime_error}]"
            )

            Program.log('DuoLogSync: check that the duoclient ikey and skey '
                        'in the config file are correct')

        # If no error occurred, go ahead and return the api_result
        else:
            return api_result

        # Can only reach this point if an error occurred, time to shutdown
        Program.initiate_shutdown(shutdown_reason)
        return {}

    async def call_log_api(self):
        """
        Make a call to a log-specific API and return the API result. The default
        implementation given here will not suffice for every type of log API and
        so should be overriden by a child clas when necessary.

        @return the result of the API call
        """

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
    def get_api_result_offset(api_result):
        """
        Get offset information given an API result. The default implementation
        given here will not suffice for every type of log API and so should be
        overriden by a child class when necessary.

        @param api_result   The result of an API call

        @return the offset of api_result
        """

        return api_result[-1]['timestamp'] + 1

    def get_log_offset(self, log=None):
        """
        Get offset information given an individual log. The default
        implementation given here will not suffice for every type of log API
        and so should be overriden by a child class when necessary.

        @param log  Individual log from which to get offset information

        @return the offset of the log
        """

        if log is None:
            return self.log_offset

        return log['timestamp'] + 1
