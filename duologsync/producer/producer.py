"""
Definition of the Producer class
"""

import asyncio
import logging
import functools
from duologsync.util import get_log_offset, run_in_executor
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

        # TODO: Implement interrupt handler / running variable so that the
        # while loop exits on failure or on user exit
        while Config.program_is_running():
            logging.info("%s producer: begin polling for %d seconds",
                         self.log_type, Config.get_polling_duration())
            await asyncio.sleep(Config.get_polling_duration())

            logging.info("%s producer: fetching logs after %d seconds",
                         self.log_type, Config.get_polling_duration())
            
            # If given a bad integration key: RuntimeError: Received 401 
            # Invalid integration key in request credentials
            # If given a bad secret key: RuntimeError: Received 401 Invalid
            # signature in request credentials
            # If given a bad host: socket.gaierror [Errno 8] nodename nor 
            # servname provided, or not known; TimeoutError: operation timed,
            # out; OSError: [Errno 65] No route to host
            # If your computer has no connection: socket.gaierror: [Errno 8]
            # nodename nor servname provided, or not known
            api_result = await self.call_log_api()
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

        logging.info("%s producer: shutting down", self.log_type)

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
