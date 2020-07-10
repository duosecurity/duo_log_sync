"""
Definition of the AdminactionProducer class
"""

import functools
from duologsync.producer.producer import Producer
from duologsync.util import run_in_executor, get_admin

class AdminactionProducer(Producer):
    """
    Implement the functionality of the Producer class to support the polling
    and placement into a queue of Adminaction logs.
    """

    def __init__(self, log_queue):
        super().__init__(log_queue, 'adminaction')

    async def call_log_api(self):
        """
        Make a call to the administrator log endpoint and return the result of
        that API call

        @param mintime  The oldest timestamp (in seconds) acceptable for a new
                        administrator log

        @return the result of a call to the administrator log API endpoint
        """

        # Make an API call to retrieve adminaction logs
        adminaction_api_result = await run_in_executor(
            functools.partial(
                get_admin().get_administrator_log,
                mintime=self.log_offset
            )
        )

        return adminaction_api_result
