"""
Definition of the AdminactionConsumer class
"""

from duologsync.config import Config
from duologsync.consumer.consumer import Consumer

ADMINACTION_KEYS_TO_LABELS = {
    ('action',):        {'name': 'action', 'is_custom': True},
    ('description',):   {'name': 'msg', 'is_custom': False},
    ('eventtype',):     {'name': 'event_type', 'is_custom': True},
    ('object',):        {'name': 'object', 'is_custom': True},
    ('timestamp',):     {'name': 'rt', 'is_custom': False},
    ('type',):          {'name': 'type', 'is_custom': True},
    ('username',):      {'name': 'suser', 'is_custom': False}
}

class AdminactionConsumer(Consumer):
    """
    An implementation of the Consumer class for adminaction logs
    """

    def __init__(self, log_format, log_queue, writer):
        super().__init__(log_format, log_queue, writer)
        self.keys_to_labels = ADMINACTION_KEYS_TO_LABELS
        self.log_type = Config.ADMIN
