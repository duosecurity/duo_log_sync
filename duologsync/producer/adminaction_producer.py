import functools
from duologsync.producer.producer import Producer

class AdminactionProducer(Producer):
    """
    Implement the functionality of the Producer class to support the polling
    and placement into a queue of Adminaction logs.
    """

    def __init__(self, config, last_offset_read, log_queue, inherited_self):
        super().__init__(config, last_offset_read, log_queue, inherited_self)

        self.log_type = 'adminaction'

    async def _call_log_api(self, mintime):
        """
        Make a call to the administrator log endpoint and return the result of
        that API call

        @param mintime  The oldest timestamp acceptable for a new
                        administrator log

        @return the result of a call to the administrator log API endpoint
        """

        return await self.loop.run_in_executor(
            self._executor,
            functools.partial(
                self.admin_api.get_administrator_log,
                mintime=mintime
            )
        )
