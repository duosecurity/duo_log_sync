"""
Definition of the AuthlogConsumer class
"""

from duologsync.config import Config
from duologsync.consumer.consumer import Consumer

AUTHLOG_KEYS_TO_LABELS = {
    ('access_device', 'host'): {'name': 'dhost', 'is_custom': False},
    ('access_device', 'ip'): {'name': 'src', 'is_custom': False},
    ('application', 'name'): {'name': 'integration', 'is_custom': True},
    ('eventtype',): {'name': 'event_type', 'is_custom': True},
    ('factor',): {'name': 'factor', 'is_custom': True},
    ('result',): {'name': 'outcome', 'is_custom': False},
    ('timestamp',): {'name': 'rt', 'is_custom': False},
    ('user', 'name'): {'name': 'duser', 'is_custom': False}
}


class AuthlogConsumer(Consumer):
    """
    An implementation of the Consumer class for auth logs
    """

    def __init__(self, log_format, log_queue, writer, child_account_id=None):
        super().__init__(log_format, log_queue, writer, child_account_id=child_account_id)
        self.keys_to_labels = AUTHLOG_KEYS_TO_LABELS
        self.log_type = Config.AUTH
