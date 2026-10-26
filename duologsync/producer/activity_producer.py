"""
Definition of the ActivityProducer class
"""
import functools

from duologsync.config import Config
from duologsync.producer.producer import Producer
from duologsync.util import run_in_executor


class ActivityProducer(Producer):
    """
    Implement the functionality of the Producer class to support the polling
    and placement into a queue of Activity logs
    """

    def __init__(self, api_call, log_queue, child_account_id=None, url_path=None):
        super().__init__(
            api_call,
            log_queue,
            Config.ACTIVITY,
            account_id=child_account_id,
            url_path=url_path,
        )
        self.first_pass = True
        self.mintime = None

        # Default to the generated mintime if no checkpoint is found
        if isinstance(self.log_offset, int):
            self.mintime = self.log_offset
            self.log_offset = None

        # If we have a string based offset, it's pulled from the checkpoint file
        if isinstance(self.log_offset, str):
            (previous_time, _) = self.log_offset.split(",")
            self.mintime = int(previous_time)
            self.log_offset = None

    async def call_log_api(self):
        """
        Make a call to the Activity Log API endpoint and return the result

        @return the result of a call to the Activity Log API endpoint
        """
        api_result = await run_in_executor(
            functools.partial(
                self.api_call,
                method="GET",
                path=self.url_path,
                params=self.get_admin_api_log_parameters(),
            )
        )

        return api_result
