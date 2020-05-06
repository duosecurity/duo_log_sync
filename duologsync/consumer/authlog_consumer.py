from duologsync.consumer import base_consumer
import json
import logging
import os
import sys

class AuthlogConsumer(base_consumer.BaseConsumer):

    def __init__(self):
        super.__init__()

    async def consumer(self):
        """
        Authlog consumer that will consume data from authlog_queue that
        authlog producer writes to. This data is then sent over configured
        transport protocol to respective siems or server.
        """
        while True:  # TODO: Change to True
            logging.info("Consuming authlogs")
            logs = await self.authlog_queue.get()

            if logs is None:
                logging.info(
                    "Logs empty. Nothing to write...")
                continue
            logging.info(
                "Consumed {} logs...".format(len(logs)))

            try:
                for log in logs:
                    self.writer.write(json.dumps(log).encode() + b'\n')
                    await self.writer.drain()
            except Exception as e:
                logging.error("Failed to write data to transport with {}".format(e))
                sys.exit(1)

            # Idea is to write to last_offset_read file after data is sent
            # When user sets recover=True in toml, we will read from this file
            # if it exists and grab data from that offset
            logging.info("Wrote data over tcp socket...")
            checkpoint_file = os.path.join(self.config['logs']['checkpointDir'],"authlog_checkpoint_data.txt")
            checkpointing_data = open(checkpoint_file, "w")
            logging.info(self.last_offset_read)
            checkpointing_data.write(json.dumps(self.last_offset_read['auth_last_fetched']))
            checkpointing_data.flush()
            checkpointing_data.close()
        self.writer.close()