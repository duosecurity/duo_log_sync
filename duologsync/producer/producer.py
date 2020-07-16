"""
Definition of the Producer class
"""

import logging
import functools
from socket import gaierror
from duologsync.util import get_log_offset, run_in_executor, restless_sleep
from duologsync.config import Config

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
        while Config.program_is_running():
            logging.info("%s producer: begin polling for %d seconds",
                         self.log_type, Config.get_polling_duration())
            await restless_sleep(Config.get_polling_duration())

            # Time to shutdown
            if not Config.program_is_running():
                continue

            logging.info("%s producer: fetching logs after %d seconds",
                         self.log_type, Config.get_polling_duration())

            api_result = self.call_log_api_safely()

            if not Config.program_is_running():
                continue

            new_logs = self.get_logs(api_result)

            if new_logs:
                # Important for recovery in the event of a crash
                self.log_offset = self.get_api_result_offset(api_result)

                logging.info("%s producer: adding %d logs to the queue",
                             self.log_type, len(new_logs))
                await self.log_queue.put(new_logs)
                logging.info("%s producer: added %d logs to the queue",
                             self.log_type, len(new_logs))

            else:
                logging.info("%s producer: no new logs available, going back "
                             "to polling", self.log_type)

        # Put anything in the queue to unblock the consumer, since the
        # consumer will not be able to do anything until an item is
        # added to the queue
        await self.log_queue.put([])
        logging.info("%s producer: shutting down", self.log_type)

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
                logging.warning('DuoLogSync: check that the duoclient host '
                                'provided in the config file is correct')

        # OSError will be thrown if a horribly messed up hostname is given
        except OSError as os_error:
            shutdown_reason = (
                f"{self.log_type} producer: ran into the "
                f"following error [{os_error}]"
            )

            # No route to host, issue with hostname given
            if os_error.errno is not None and os_error.errno == 65:
                logging.warning('DuoLogSync: check that the duoclient host '
                                'provided in the config file is correct')

        # duo_client will throw a RuntimeError if the integration key or
        # secret key is invalid
        except RuntimeError as runtime_error:
            shutdown_reason = (
                f"{self.log_type} producer: ran into the "
                f"following error [{runtime_error}]"
            )

            logging.warning('DuoLogSync: check that the duoclient ikey '
                            'and skey in the config file are correct')

        # If no error occurred, go ahead and return the api_result
        else:
            return api_result

        # Can only reach this point if an error occurred, time to shutdown
        Config.initiate_shutdown(shutdown_reason)
        return None

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
