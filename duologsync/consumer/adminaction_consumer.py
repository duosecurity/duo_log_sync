"""
Definition of the AdminactionConsumer class
"""

from duologsync.consumer.consumer import Consumer

class AdminactionConsumer(Consumer):
    """
    An implementation of the Consumer class for adminaction logs
    """

    def __init__(self, producer, writer):
        super().__init__(producer, writer)
        self.log_type = "adminaction"
