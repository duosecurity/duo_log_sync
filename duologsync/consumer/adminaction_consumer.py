"""
Definition of the AdminactionConsumer class
"""

from duologsync.consumer.consumer import Consumer

ADMINACTION_KEYS_TO_LABELS = {
    ('action'):         {'name': 'action', 'is_custom': True},
    ('description'):    {'name': 'msg', 'is_valid_cef_labl': False},
    ('eventtype'):      {'name': 'event_type', 'is_custom': True},
    ('object'):         {'name': 'object', 'is_custom': True},
    ('timestamp'):      {'name': 'rt', 'is_custom': False},
    ('type'):           {'name': 'type', 'is_custom': True},
    ('username'):       {'name': 'suser', 'is_custom': False}
}

class AdminactionConsumer(Consumer):
    """
    An implementation of the Consumer class for adminaction logs
    """

    def __init__(self, log_queue, writer):
        super().__init__(ADMINACTION_KEYS_TO_LABELS, log_queue, 'adminaction',
                         writer)
