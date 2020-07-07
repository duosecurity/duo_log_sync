from duologsync.consumer.consumer import Consumer

class AdminactionConsumer(Consumer):

    def __init__(self, log_queue, log_offset, writer, checkpoint_dir):
        super().__init__(log_queue, log_offset, writer, checkpoint_dir)
        self.log_type = "adminaction"
