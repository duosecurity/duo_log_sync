from duologsync.config import Config
from duologsync.consumer.consumer import Consumer


class ActivityConsumer(Consumer):
    """
    An implementation of the Consumer class for user activity logs
    """

    def __init__(self, log_format, log_queue, writer, child_account_id=None):
        super().__init__(log_format, log_queue, writer, child_account_id=child_account_id)
        self.log_type = Config.ACTIVITY
