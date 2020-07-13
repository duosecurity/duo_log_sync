"""
Definition of the TelephonyProducer class
"""

from duologsync.producer.producer import Producer

class TelephonyProducer(Producer):
    """
    Implement the functionality of the Producer class to support the polling
    and placement into a queue of Telephony logs
    """

    def __init__(self, api_call, log_queue):
        super().__init__(api_call, log_queue, 'telephony')
