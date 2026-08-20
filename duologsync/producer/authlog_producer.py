"""
Definition of the Authlog Producer class
"""

import functools
from duologsync.config import Config
from duologsync.util import run_in_executor
from duologsync.producer.producer import Producer


class AuthlogProducer(Producer):
    """
    Implement the functionality of the Producer class to support the polling
    and placement into a queue of Authentication logs
    """

    def __init__(
        self,
        api_call,
        log_queue,
        child_account_id=None,
        url_path=None,
    ):
        super().__init__(
            api_call,
            log_queue,
            Config.AUTH,
            account_id=child_account_id,
            url_path=url_path,
        )
        self.mintime = None

        # log_offset for Auth can be an int or a tuple, depending on if there
        # was a checkpoint file. Appropriately set mintime and log_offset if
        # log_offset is just an int
        if isinstance(self.log_offset, int):
            self.mintime = self.log_offset
            self.log_offset = None

        if isinstance(self.log_offset, (list, tuple)) and self.log_offset:
            self.mintime = int(self.log_offset[0])

    async def call_log_api(self):
        """
        Make a call to the authentication log endpoint and return the result of
        that API call

        @return the result of a call to the authentication log API endpoint
        """

        if self.account_id is not None:
            authlog_api_result = await run_in_executor(
                functools.partial(
                    self.api_call,
                    method="GET",
                    path=self.url_path,
                    params=self.get_admin_api_log_parameters(),
                )
            )
        else:
            authlog_api_result = await run_in_executor(
                functools.partial(
                    self.api_call,
                    api_version=2,
                    mintime=self.mintime,
                    next_offset=self.log_offset,
                    sort="ts:asc",
                    limit="1000",
                )
            )

        return authlog_api_result

    def get_logs(self, api_result):
        """
        Retrieve authentication logs from the API result of a call to the
        authentication log endpoint

        @param api_result   The result of an API call to the authentication
                            log endpoint

        @return authentication logs from the result of an API call to the
                authentication log endpoint
        """

        if self.account_id is not None:
            for authlog in api_result.get("authlogs", []):
                authlog.setdefault("eventtype", "authentication")

        return api_result
