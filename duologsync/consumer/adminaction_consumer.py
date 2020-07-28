"""
Definition of the AdminactionConsumer class
"""

from duologsync.consumer.consumer import Consumer

class AdminactionConsumer(Consumer):
    """
    An implementation of the Consumer class for adminaction logs
    """

    def __init__(self, log_queue, writer):
        super().__init__(log_queue, 'adminaction', writer)
