"""
Definition of the AuthlogConsumer class
"""

from duologsync.consumer.consumer import Consumer

AUTHLOG_FIELDS_TO_LABELS = {
    ('access_device', 'host'):  {'name': 'dhost', 'is_custom': False},
    ('access_device', 'ip'):    {'name': 'ip', 'is_custom': False},
    ('application', 'name'):    {'name': 'integration', 'is_custom': True},
    ('eventtype'):              {'name': 'event_type', 'is_custom': True},
    ('factor'):                 {'name': 'factor', 'is_custom': True},
    ('result'):                 {'name': 'outcome', 'is_custom': False},
    ('timestamp'):              {'name': 'rt', 'is_custom': False},
    ('user', 'name'):           {'name': 'duser', 'is_custom': False}
}

class AuthlogConsumer(Consumer):
    """
    An implementation of the Consumer class for auth logs
    """

    def __init__(self, log_queue, writer):
        super().__init__(AUTHLOG_FIELDS_TO_LABELS, log_queue, 'auth', writer)
