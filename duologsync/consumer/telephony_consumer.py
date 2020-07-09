"""
Definition of the TelephonyConsumer class
"""

from duologsync.consumer.consumer import Consumer

class TelephonyConsumer(Consumer):
    """
    An implementation of the Consumer class for telephony logs
    """

    def __init__(self, log_queue, producer, writer):
        super().__init__(log_queue, producer, writer)
        self.log_type = "telephony"
