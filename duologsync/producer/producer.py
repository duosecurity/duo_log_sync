import asyncio
import logging
from abc import ABC, abstractmethod

from duologsync.util import get_polling_duration

class Producer(ABC):
    """
    Read data from a specific log endpoint via an API call at a polling
    duration that is user specified. The data is published to a queue which
    is only used for data of the same log type, and offset information is
    recorded to allow checkpointing and recovery from a crash.
    """

    def __init__(self, log_queue, log_offset, g_vars):
        self.log_queue = log_queue
        self.admin = g_vars.admin
        self.event_loop = g_vars.event_loop
        self.executor = g_vars.executor
        self.log_offset = log_offset
        self.log_type = None

    async def produce(self):
        """
        The main function of this class and subclasses. Runs a loop, sleeping
        for the polling duration then making an API call, consuming the logs
        from that API call and saving the offset of the latest log read.
        """

        # TODO: Implement interrupt handler / running variable so that the
        # while loop exits on failure or on user exit
        while True:
            await asyncio.sleep(get_polling_duration())
            logging.info("Getting data from %s endpoint after %s seconds",
                         self.log_type, get_polling_duration())

            api_result = await self._call_log_api()
            new_logs = self._get_logs(api_result)

            if new_logs:
                logging.info("Adding %d %s logs to the queue", len(new_logs),
                             self.log_type)
                await self.log_queue.put(new_logs)
                logging.info("Added %d %s logs to the queue", len(new_logs),
                             self.log_type)

                # Important for recovery in the event of a crash
                self.log_offset = self._get_log_offset(api_result)

    @abstractmethod
    async def _call_log_api(self):
        """
        Make a call to a log-specific API and return the API result. An
        implementation of call_log_api must be given by classes that extend
        this class.

        @return the result of the API call
        """

    @staticmethod
    def _get_logs(api_result):
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
    def _get_log_offset(api_result):
        """
        Return the newest offset read given the last api_result received. The
        default implementation given here will not suffice for every type of
        log API and so should be overriden by a child class when necessary.

        @param api_result   The result of an API call

        @return the offset of the latest fetched log
        """

        # No need to rewrite this function if the latest timestamp may be
        # obtained from api_result in the following manner
        return api_result[-1]['timestamp'] + 1
