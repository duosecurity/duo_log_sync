import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

class Producer(ABC):
    """
    Read data from a specific log endpoint via an API call at a polling
    duration that is user specified. The data is published to a queue which
    is only used for data of the same log type, and offset information is
    recorded to allow checkpointing and recovery from a crash.
    """

    MILLISECONDS_PER_SECOND = 1000
    SECONDS_PER_MINUTE = 60
    MINIMUM_POLLING_DURATION = 2 * SECONDS_PER_MINUTE

    def __init__(self, config, last_offset_read, log_queue, inherited_self):
        self.config = config
        self.last_offset_read = last_offset_read
        self.log_queue = log_queue

        # TODO: make these values available globally
        self._executor = inherited_self.executor
        self.loop = inherited_self.loop
        self.admin = inherited_self.admin

        self.log_type = None

    async def produce(self):
        """
        The main function of this class and subclasses. Runs a loop, sleeping
        for the polling duration then making an API call, consuming the logs
        from that API call and saving the offset of the latest log read.
        """

        # The key into the last_offset_read dictionary for this log type
        offset_key = f"{self.log_type}_last_fetched"

        # The maximum age in days of any newly retrieved log
        days_in_past = self.config['logs']['polling']['daysinpast']

        # Create a timestamp for screening logs that are too old
        mintime = datetime.utcnow() - timedelta(days=days_in_past)
        mintime = int(mintime.timestamp())

        # The number of minutes a producer will poll for logs
        polling_duration = self.config['logs']['polling']['duration']

        # Convert polling_duration to seconds
        polling_duration *= self.SECONDS_PER_MINUTE

        # Use the minimum polling duration if the user specifies a lower number
        polling_duration = max(polling_duration, self.MINIMUM_POLLING_DURATION)

        # TODO: Implement interrupt handler / running variable so that the
        # while loop exits on failure or on user exit
        while True:
            await asyncio.sleep(polling_duration)
            logging.info("Getting data from %s endpoint after %d seconds",
                         self.log_type, polling_duration)

            api_result = await self._call_log_api(mintime)
            new_logs = self._get_logs(api_result)

            if new_logs:
                last_offset = self._get_last_offset_read(api_result)

                logging.info("Adding %d %s logs to the queue", len(new_logs),
                             self.log_type)
                await self.log_queue.put(new_logs)
                logging.info("Added %d %s logs to the queue", len(new_logs),
                             self.log_type)

                # Important for recovery in the event of a crash
                self.last_offset_read[offset_key] = last_offset

    @abstractmethod
    async def _call_log_api(self, mintime):
        """
        Make a call to a log-specific API and return the API result. An
        implementation of call_log_api must be given by classes that extend
        this class.

        @param mintime  The oldest timestamp (in seconds) acceptable for a log
                        to have. All logs returned from the API call should
                        have a timestamp of mintime or newer

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
    def _get_last_offset_read(api_result):
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
