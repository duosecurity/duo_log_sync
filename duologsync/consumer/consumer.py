"""
Definition of the Consumer class
"""

import sys
import json
import asyncio
import logging
from duologsync.util import get_polling_duration, update_log_checkpoint

class Consumer():
    """
    Read logs from a log API call function provided by a log-specific producer
    object and write those logs somewhere using the writer object passed.
    Additionally, once logs have been written successfully, take the latest
    log_offset - also shared with the Producer pair - and save it to a
    checkpointing file in order to recover progress if a crash occurs.
    """

    def __init__(self, producer, writer):
        self.log_offset = None
        self.producer = producer
        self.writer = writer
        self.log_type = None

    async def consume(self):
        """
        Consumer that will consume data from using a log API call function
        from producer. This data is then sent over a configured transport
        protocol to respective SIEMs or server.
        """
        while True:
            logging.info(
                '%s: polling for %s seconds',
                self.log_type,
                get_polling_duration())
            await asyncio.sleep(get_polling_duration())

            logging.info("%s: making API call", self.log_type)
            api_result = await self.producer.call_log_api()
            logs = self.producer.get_logs(api_result)

            if logs is None:
                logging.info("%s logs empty. Nothing to write.", self.log_type)
                continue

            logging.info('%s: received %s logs...', self.log_type, len(logs))

            # Keep track of the latest log written in order to have accurate
            # offset information in the case that a problem occurs in the
            # middle of writing logs
            last_log_written = None

            try:
                for log in logs:
                    self.writer.write(json.dumps(log).encode() + b'\n')
                    await self.writer.drain()
                    last_log_written = log

                # All the logs were written successfully
                last_log_written = None
            except Exception as error:
                logging.error("Failed to write data to transport: %s", error)
                sys.exit(1)
            finally:
                if last_log_written is not None:
                    logging.warning('%s: failed to write some logs',
                                    self.log_type)

                self.log_offset = self.producer.get_log_offset(
                    api_result,
                    last_log_written)

                # Save log_offset to log specific checkpoint file
                update_log_checkpoint(self.log_type, self.log_offset)
