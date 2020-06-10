import asyncio
import ssl
import logging
import sys
import os

from duologsync.duo_log_sync_base import LogSyncBase


class BaseConsumer(LogSyncBase):
    def __init__(self):
        super().__init__()
        self.writer = self.get_connection()

    async def get_connection(self):
        host = self.config['transport']['host']
        port = self.config['transport']['port']
        protocol = self.config['transport']['protocol']

        if protocol == 'TCPSSL':
            try:
                logging.info("Opening connection to server over encrypted tcp...")
                certFile = os.path.join(self.config['transport']['certFileDir'], self.config['transport']['certFileName'])
                sc = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,
                                                cafile=certFile)

                _, writer = await asyncio.open_connection(host, port,
                                                               loop=self.loop, ssl=sc)
                self.writer = writer
            except ConnectionError:
                logging.error("Connection to server failed at host {} and "
                              "port {}".format('localhost', '8888'))
            except Exception as e:
                logging.error("Connection to server failed with exception "
                              "{}".format(e))
                logging.error("Terminating the application...")
                sys.exit(1)

        if protocol == 'TCP':
            try:
                logging.info(
                    "Opening connection to server over tcp...")
                _, writer = await asyncio.wait_for(asyncio.open_connection(host, port,
                                                          loop=self.loop), timeout=60) # Default connection timeout set to 1min
                self.writer = writer
            except asyncio.TimeoutError as te:
                logging.error("Connection to server timedout after 60 seconds "
                              "{}".format(te))
                logging.error("Terminating the application...")
                sys.exit(1)
            except Exception as e:
                logging.error("Connection to server failed with exception "
                              "{}".format(e))
                logging.error("Terminating the application...")
                sys.exit(1)
