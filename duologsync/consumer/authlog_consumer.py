"""
Definition of the AuthlogConsumer class
"""

from duologsync.consumer.consumer import Consumer

class AuthlogConsumer(Consumer):
    """
    An implementation of the Consumer class for auth logs
    """

    def __init__(self, producer, writer):
        super().__init__(producer, writer)
        self.log_type = "auth"
