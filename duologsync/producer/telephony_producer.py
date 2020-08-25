"""
Definition of the TelephonyProducer class
"""

from duologsync.config import Config
from duologsync.producer.producer import Producer

class TelephonyProducer(Producer):
    """
    Implement the functionality of the Producer class to support the polling
    and placement into a queue of Telephony logs
    """

    def __init__(self, api_call, log_queue, child_account_id=None, url_path=None):
        super().__init__(api_call, log_queue, Config.TELEPHONY,
                         account_id=child_account_id,
                         url_path=url_path)
