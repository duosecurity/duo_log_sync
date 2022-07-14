"""
Definition of the TrustMonitorProducer class
"""
import functools
import datetime
import json
import math

from duologsync.config import Config
from duologsync.producer.producer import Producer
from duologsync.program import Program
from duologsync.util import run_in_executor


class TrustMonitorProducer(Producer):
    """
    Implement the functionality of the Producer class to support the polling
    and placement into a queue of Trust Monitor logs
    """

    def __init__(self, api_call, log_queue, child_account_id=None, url_path=None):
        super().__init__(
            api_call,
            log_queue,
            Config.TRUST_MONITOR,
            account_id=child_account_id,
            url_path=url_path,
        )

        self.first_pass = True
        self.mintime = self.log_offset

    async def call_log_api(self):
        """
        Make a call to the Trust Monitor Admin API endpoint and return the result

        @return the result of a call to the DTM API endpoint
        """
        today = datetime.datetime.now(tz=datetime.timezone.utc)
        maxtime = math.floor(today.timestamp() * 1000)

        # At the first call of the DTM API,
        # we need to force self.log_offset to be None
        # so that the API can fetch events correctly.
        # Currently, self.log_offset is set to the mintime
        # that's set in the config, which will fail for the API.
        if self.first_pass:
            self.log_offset = None
            self.first_pass = False

        # Once DLS has paginated through and transported
        # all existing events, the self.log_offset that is
        # returned is the last transported event's timestamp. With this,
        # we can use this value as the new mintime so that DLS
        # can keep polling for new events.
        if self.mintime and self.log_offset:
            if self.log_offset > self.mintime:
                self.mintime = self.log_offset
                self.log_offset = None

        api_result = await run_in_executor(
            functools.partial(
                self.api_call,
                mintime=self.mintime,
                maxtime=maxtime,
                offset=self.log_offset,
            )
        )

        return api_result
