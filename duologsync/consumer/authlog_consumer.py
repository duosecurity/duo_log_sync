"""
Definition of the AuthlogConsumer class
"""

from duologsync.consumer.consumer import Consumer

class AuthlogConsumer(Consumer):
    """
    An implementation of the Consumer class for auth logs
    """

    def __init__(self, log_queue, log_offset, writer):
        super().__init__(log_queue, log_offset, writer)
        self.log_type = "auth"
