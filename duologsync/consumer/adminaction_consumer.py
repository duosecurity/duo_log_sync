from duologsync.consumer import base_consumer

class AdminactionConsumer(base_consumer.BaseConsumer):

    def __init__(self, log_queue, log_offset, writer, g_vars):
        super().__init__(log_queue, log_offset, writer, g_vars)
        self.log_type = "adminaction"
