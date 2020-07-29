"""
Definition of the Consumer class
"""

import os
import json
import logging
from duologsync.config import Config
from duologsync.program import Program
from duologsync.producer.producer import Producer

class Consumer():
    """
    Read logs from a queue shared with a producer object and write those logs
    somewhere using the write object passed. Additionally, once logs have been
    written successfully, take the latest log_offset - also shared with the
    Producer pair - and save it to a checkpointing file in order to recover
    progress if a crash occurs.
    """

    def __init__(self, keys_to_labels, log_queue, log_type, writer):
        # Tuple of keys to access the value wanted, and the desired label for
        # the value. If the desired label has 'True' then it is a custom label
        # and must be generated
        self.keys_to_labels = keys_to_labels
        self.log_queue = log_queue
        self.log_type = log_type
        self.writer = writer
        self.log_offset = None

    async def consume(self):
        """
        Consumer that will consume data from a queue shared with a producer
        object. Data from the queue is then sent over a configured transport
        protocol to respective SIEMs or servers.
        """

        while Program.is_running():
            Program.log(f"{self.log_type} consumer: waiting for logs",
                        logging.INFO)

            # Call unblocks only when there is an element in the queue to get
            logs = await self.log_queue.get()

            # Time to shutdown
            if not Program.is_running():
                continue

            Program.log(f"{self.log_type} consumer: received {len(logs)} logs "
                        "from producer", logging.INFO)

            # Keep track of the latest log written in the case that a problem
            # occurs in the middle of writing logs
            last_log_written = None
            successful_write = False

            try:
                Program.log(f"{self.log_type} consumer: writing logs",
                            logging.INFO)
                for log in logs:
                    await self.writer.write(json.dumps(log).encode() + b'\n')
                    last_log_written = log

                # All the logs were written successfully
                successful_write = True

            # Specifically watch out for errno 32 - Broken pipe. This means
            # that the connect established by writer was reset or shutdown.
            except BrokenPipeError as broken_pipe_error:
                shutdown_reason = f"{broken_pipe_error}"
                Program.initiate_shutdown(shutdown_reason)
                Program.log("DuoLogSync: connection to server was reset",
                            logging.WARNING)

            finally:
                if successful_write:
                    Program.log(f"{self.log_type} consumer: successfully wrote "
                                "all logs", logging.INFO)
                else:
                    Program.log(f"{self.log_type} consumer: failed to write "
                                "some logs", logging.WARNING)

                self.log_offset = Producer.get_log_offset(last_log_written)
                self.update_log_checkpoint(self.log_type, self.log_offset)

        Program.log(f"{self.log_type} consumer: shutting down", logging.INFO)

    @staticmethod
    def update_log_checkpoint(log_type, log_offset):
        """
        Save log_offset to the checkpoint file for log_type.

        @param log_type     Used to determine which checkpoint file to open
        @param log_offset   Information to save in the checkpoint file
        """

        Program.log(f"{log_type} consumer: saving latest log offset to a "
                    "checkpointing file", logging.INFO)

        checkpoint_filename = os.path.join(
            Config.get_checkpoint_directory(),
            f"{log_type}_checkpoint_data.txt")

        # Open file checkpoint_filename in writing mode only
        checkpoint_file = open(checkpoint_filename, 'w')
        checkpoint_file.write(json.dumps(log_offset))

        # According to Python docs, closing a file also flushes the file
        checkpoint_file.close()
