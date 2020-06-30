import functools
from duologsync.producer.producer import Producer

class TelephonyProducer(Producer):
    """
    Implement the functionality of the Producer class to support the polling
    and placement into a queue of Telephony logs
    """

    def __init__(self, config, last_offset_read, log_queue, inherited_self):
        super().__init__(config, last_offset_read, log_queue, inherited_self)

        self.log_type = 'telephony'

    async def _call_log_api(self, mintime):
        """
        Make a call to the telephony log endpoint and return the result of
        that API call

        @param mintime  The oldest timestamp (in seconds) acceptable for a new
                        administrator log

        @return the result of a call to the telephony log API endpoint
        """

        # If last_offset_read is None, then set mintime to mintime
        mintime = self.last_offset_read.get(f"{self.log_type}_last_fetched",
                                            mintime)

        # get_telephony_log is a high latency call which will block the event
        # loop. Thus it is run in an executor - a dedicated thread pool -
        # which allows for asyncio to do other work while this call is being
        # made
        telephony_api_result = await self.event_loop.run_in_executor(
            self._executor,
            functools.partial(
                self.admin.get_telephony_log,
                mintime=mintime
            )
        )

        return telephony_api_result
