from duologsync.consumer.consumer import Consumer

class AdminactionConsumer(Consumer):

    def __init__(self, log_queue, log_offset, writer):
        super().__init__(log_queue, log_offset, writer)
        self.log_type = "adminaction"
