"""
Definition of the Authlog Producer class
"""

import functools
from duologsync.producer.producer import Producer
from duologsync.util import run_in_executor

class AuthlogProducer(Producer):
    """
    Implement the functionality of the Producer class to support the polling
    and placement into a queue of Authentication logs
    """

    def __init__(self, api_call, log_queue):
        super().__init__(api_call, log_queue, 'auth')
        self.mintime = None

        # log_offset for Auth can be an int or a tuple, depending on if there
        # was a checkpoint file. Appropriately set mintime and log_offset if
        # log_offset is just an int
        if isinstance(self.log_offset, int):
            self.mintime = self.log_offset
            self.log_offset = None

    async def call_log_api(self):
        """
        Make a call to the authentication log endpoint and return the result of
        that API call

        @return the result of a call to the authentication log API endpoint
        """

        # Make an API call to retrieve authlog logs
        authlog_api_result = await run_in_executor(
            functools.partial(
                self.api_call,
                api_version=2,
                mintime=self.mintime,
                next_offset=self.log_offset,
                sort='ts:asc',
                limit='1000'
            )
        )

        return authlog_api_result

    @staticmethod
    def get_logs(api_result):
        """
        Retrieve authentication logs from the API result of a call to the
        authentication log endpoint

        @param api_result   The result of an API call to the authentication
                            log endpoint

        @return authentication logs from the result of an API call to the
                authentication log endpoint
        """

        return api_result.get('authlogs')

    @staticmethod
    def get_api_result_offset(api_result):
        """
        Return the next_offset given by the result of a call to the
        authentication log API endpoint

        @param api_result   The result of an API call to the authentication
                            log endpoint

        @return the next_offset given by the result of a call to the
                authentication log API endpoint
        """

        return api_result['metadata']['next_offset']

    def get_log_offset(self, log=None):
        """
        Return offset information from the authentication log.

        @param log  Authentication log from which to retrieve offset info. None
                    indicates that the latest log offset is required

        @return offset information from log
        """

        if log is None:
            return self.log_offset

        timestamp = log['timestamp'] * 1000
        txid = log['txid']
        return [timestamp, txid]
