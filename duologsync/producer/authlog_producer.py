"""
Definition of the Authlog Producer class
"""

import functools
import time
from duologsync.config import Config
from duologsync.util import run_in_executor, normalize_params
from duologsync.producer.producer import Producer


class AuthlogProducer(Producer):
    """
    Implement the functionality of the Producer class to support the polling
    and placement into a queue of Authentication logs
    """

    def __init__(self, api_call, log_queue, child_account_id=None, url_path=None):
        super().__init__(api_call, log_queue, Config.AUTH, account_id=child_account_id,
                         url_path=url_path)
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

        if Config.account_is_msp():
            # In case of recovering from checkpoint, self.mintime is None since its not init
            # anywhere. When duo_client is directly used, client will initialize self.mintime to
            # time.time() - 86400 (1 day in past). We will have to do similar thing when directly
            # calling logs endpoint for MSP accounts. Mintime is never used when next offset is
            # present
            if not self.mintime:
                self.mintime = (int(time.time()) - 86400) * 1000

            # Make an API call to retrieve authlog logs for MSP accounts
            parameters = normalize_params({"mintime": str(self.mintime), "maxtime": str(int(time.time()) * 1000),
                                           "limit": '1000',
                                           "account_id": self.account_id, "sort": 'ts:asc'})

            if self.log_offset is not None:
                parameters["next_offset"] = self.log_offset

            authlog_api_result = await run_in_executor(
                functools.partial(
                    self.api_call,
                    method="GET",
                    path=self.url_path,
                    params=parameters
                )
            )
        else:
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

        return api_result
