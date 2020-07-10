"""
Definition of the AuthlogConsumer class
"""

from duologsync.consumer.consumer import Consumer

class AuthlogConsumer(Consumer):
    """
    An implementation of the Consumer class for auth logs
    """

    def __init__(self, log_queue, producer, writer):
        super().__init__(log_queue, 'auth', producer, writer)
