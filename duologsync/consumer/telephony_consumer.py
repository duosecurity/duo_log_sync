from duologsync.consumer import base_consumer
import json
import logging
import os
import sys

class TelephonyConsumer(base_consumer.BaseConsumer):

    def __init__(self):
        super.__init__()

    async def consumer(self):
        """
        Telephony consumer that will consume data from telephonylog_queue that
        telephonylog producer writes to. This data is then sent over configured
        transport protocol to respective siems or server.
        """
        while True:
            logging.info("Consuming telephony log...")
            logs = await self.telephonylog_queue.get()

            if logs is None:
                logging.info(
                    "Telephony logs empty. Nothing to write...")
                continue
            logging.info(
                "Consumed {} telephony logs...".format(len(logs)))

            try:
                for log in logs:
                    self.writer.write(json.dumps(log).encode() + b'\n')
                    await self.writer.drain()
                logging.info("Wrote data over tcp socket...")
            except Exception as e:
                logging.error("Failed to write data to transport with {}".format(e))
                sys.exit(1)

            # Idea is to write to last_offset_read file after data is sent
            # When user sets recover=True in toml, we will read from this file
            # if it exists and grab data from that offset
            # Still testing out this logic
            logging.info(self.last_offset_read)
            checkpoint_file = os.path.join(self.config['logs']['checkpointDir'],
                                           "telephony_checkpoint_data.txt")
            checkpointing_data = open(checkpoint_file, "w")
            checkpointing_data.write(json.dumps(self.last_offset_read['telephony_last_fetched']))
            checkpointing_data.flush()
            checkpointing_data.close()
        self.writer.close()