"""
Definition of the Consumer class
"""

import sys
import json
import logging

from duologsync.util import update_log_checkpoint

class Consumer():
    """
    Read logs from a queue shared with a Producer and write those logs
    somewhere using the writer object passed. Additionally, once logs have
    been written successfully, take the latest log_offset - also shared with
    the Producer pair - and save it to a checkpointing file in order to recover
    progress if a crash occurs.
    """

    def __init__(self, log_queue, log_offset, writer):
        self.log_offset = log_offset
        self.log_queue = log_queue
        self.writer = writer
        self.log_type = None

    async def consume(self):
        """
        Consumer that will consume data from log_queue that a corresponding
        Producer writes to. This data is then sent over a configured transport
        protocol to respective SIEMs or server.
        """
        while True:
            logging.info("Consuming %s logs...", self.log_type)
            logs = await self.log_queue.get()

            if logs is None:
                logging.info("%s logs empty. Nothing to write...", self.log_type)
                continue

            logging.info("Consumed %s %s logs...", len(logs), self.log_type)

            try:
                for log in logs:
                    self.writer.write(json.dumps(log).encode() + b'\n')
                    await self.writer.drain()
                logging.info("Wrote data over tcp socket...")
            except Exception as error:
                logging.error("Failed to write data to transport: %s", error)
                sys.exit(1)

            # Save log_offset to log specific checkpoint file
            update_log_checkpoint(self.log_type, self.log_offset)
