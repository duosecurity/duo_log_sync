"""
Definition of the Producer class
"""

from abc import ABC, abstractmethod
from duologsync.util import get_log_offset

class Producer(ABC):
    """
    Define common function for fetching data from a log specific API endpoint
    and getting offset information for a log or API result.
    """

    def __init__(self, log_type):
        self.log_type = log_type
        self.log_offset = get_log_offset(self.log_type)

    @abstractmethod
    async def call_log_api(self):
        """
        Make a call to a log-specific API and return the API result. An
        implementation of call_log_api must be given by classes that extend
        this class.

        @return the result of the API call
        """

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

    def get_api_result_offset(self, api_result):
        """
        Return the offset of the newest log given api_result.
        The default implementation given here will not suffice for every type of
        log API and so should be overriden by a child class when necessary.

        @param api_result   The result of an API call

        @return the offset of the latest fetched log
        """

        # No need to rewrite this function if the latest timestamp may be
        # obtained from api_result in the following manner
        return self.get_log_offset(api_result[-1])

    @staticmethod
    def get_log_offset(log):
        """
        Get offset information given an individual log from an API result. The
        default implementation given here will not suffice for every type of
        log API and so should be overriden by a child class when necessary.

        @param log  Individual log from which to get offset information

        @return the offset of the log
        """

        return log['timestamp'] + 1
