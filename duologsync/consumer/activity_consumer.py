from duologsync.config import Config
from duologsync.consumer.consumer import Consumer

ACTIVITY_KEYS_TO_LABELS = {
    ('access_device', 'ip', 'address'): {'name': 'src', 'is_custom': False},
    ('action', 'name'): {'name': 'act', 'is_custom': False},
    ('actor', 'name'): {'name': 'suser', 'is_custom': False},
    ('ts',): {'name': 'rt', 'is_custom': False},
    ('target', 'details'): {'name': 'msg', 'is_custom': False},
    ('result',): {'name': 'outcome', 'is_custom': False},
    ('application', 'name'): {'name': 'integration_name', 'is_custom': True},
    ('application', 'type'): {'name': 'integration_type', 'is_custom': True},
}


class ActivityConsumer(Consumer):
    """
    An implementation of the Consumer class for user activity logs
    """

    def __init__(self, log_format, log_queue, writer, child_account_id=None):
        super().__init__(log_format, log_queue, writer, child_account_id=child_account_id)
        self.keys_to_labels = ACTIVITY_KEYS_TO_LABELS
        self.log_type = Config.ACTIVITY
