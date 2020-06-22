from duologsync.consumer import base_consumer

class AdminactionConsumer(base_consumer.BaseConsumer):

    def __init__(self, config, last_offset_read, log_queue, writer):
        super().__init__(config, last_offset_read, log_queue, writer)
        self.log_type = "adminaction"
