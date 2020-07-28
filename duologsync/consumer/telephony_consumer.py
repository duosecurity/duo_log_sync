"""
Definition of the TelephonyConsumer class
"""

from duologsync.consumer.consumer import Consumer

class TelephonyConsumer(Consumer):
    """
    An implementation of the Consumer class for telephony logs
    """

    def __init__(self, log_queue, writer):
        super().__init__(log_queue, 'telephony', writer)
