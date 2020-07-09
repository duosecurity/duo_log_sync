"""
Definition of the TelephonyProducer class
"""

import functools
from duologsync.producer.producer import Producer
from duologsync.util import run_in_executor, get_admin

class TelephonyProducer(Producer):
    """
    Implement the functionality of the Producer class to support the polling
    and placement into a queue of Telephony logs
    """

    def __init__(self, log_offset):
        super().__init__(log_offset)
        self.log_type = 'telephony'

    async def call_log_api(self):
        """
        Make a call to the telephony log endpoint and return the result of
        that API call

        @param mintime  The oldest timestamp (in seconds) acceptable for a new
                        administrator log

        @return the result of a call to the telephony log API endpoint
        """

        # Make an API call to retrieve telephony logs
        telephony_api_result = await run_in_executor(
            functools.partial(
                get_admin().get_telephony_log,
                mintime=self.log_offset
            )
        )

        return telephony_api_result
