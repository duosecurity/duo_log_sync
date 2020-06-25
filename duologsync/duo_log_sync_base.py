import asyncio
import logging
import duo_client
import json
import os
import sys

from concurrent.futures import ThreadPoolExecutor
from duologsync.config_generator import ConfigGenerator
from duologsync.__version__ import __version__

class LogSyncBase:

    def __init__(self, args):
        self.loop = asyncio.get_event_loop()
        self.authlog_queue = asyncio.Queue(loop=self.loop)
        self.telephonylog_queue = asyncio.Queue(loop=self.loop)
        self.adminlog_queue = asyncio.Queue(loop=self.loop)

        self._executor = ThreadPoolExecutor(3)
        self.last_offset_read = {}

        self.config = ConfigGenerator().get_config(args.ConfigPath)

        self.admin_api = self.init_duoclient(self.config)

        self.writer = None

    def init_duoclient(self, config):
        try:
            client = duo_client.Admin(
                ikey=config['duoclient']['ikey'],
                skey=config['duoclient']['skey'],
                host=config['duoclient']['host'],
                user_agent=('Duo Log Sync/' + __version__),
            )
            logging.info("Adminapi initialized for ikey {} and host {}...".
                         format(config['duoclient']['ikey'],
                                config['duoclient']['host']))
        except Exception as e:
            logging.error("Unable to create duo client. Pls check credentials...")
            sys.exit(1)

        return client

    def start(self):
        """
        Driver class for duologsync application which initializes event loop
        and sets producer consumer for different endpoints as specified by
        user in config file.
        """
        from duologsync.producer.authlog_producer import AuthlogProducer
        from duologsync.consumer.base_consumer import BaseConsumer
        from duologsync.producer.telephony_producer import TelephonyProducer
        from duologsync.consumer.authlog_consumer import AuthlogConsumer
        from duologsync.consumer.telephony_consumer import TelephonyConsumer
        from duologsync.producer.adminaction_producer import AdminactionProducer
        from duologsync.consumer.adminaction_consumer import AdminactionConsumer
        from duologsync.util import create_writer

        if self.config['recoverFromCheckpoint']['enabled']:
            self.update_last_offset_read()
            logging.info("Reading logs from last recorded offset...")

        self.writer = self.loop.run_until_complete(
            create_writer(self.config, self.loop)
        )

        # Enable endpoints based on user selection
        tasks = []
        enabled_endpoints = self.config['logs']['endpoints']['enabled']
        for endpoint in enabled_endpoints:
            new_queue = asyncio.Queue(loop=self.loop)
            producer = consumer = None

            if endpoint == 'auth':
                producer = AuthlogProducer(self.config, self.last_offset_read,
                                           new_queue, self)
                consumer = AuthlogConsumer(self.config, self.last_offset_read, 
                                           new_queue, self.writer)
            elif endpoint == "telephony":
                producer = TelephonyProducer(self.config, self.last_offset_read,
                                             new_queue, self)
                consumer = TelephonyConsumer(self.config, self.last_offset_read,
                                             new_queue, self.writer)
            elif endpoint == "adminaction":
                producer = AdminactionProducer(self.config, 
                                               self.last_offset_read,
                                               new_queue, self)
                consumer = AdminactionConsumer(self.config, 
                                               self.last_offset_read,
                                               new_queue, self.writer)
            else:
                logging.info("%s is not a recognized endpoint", endpoint)
                del new_queue
                continue

            tasks.append(asyncio.ensure_future(producer.produce()))
            tasks.append(asyncio.ensure_future(consumer.consume()))

        self.loop.run_until_complete(asyncio.gather(*tasks))
        self.loop.close()

    def update_last_offset_read(self):
        """
        This function is used to recover offset to restart from in case of
        application crash or network issue. User can specify if they want to
        recover from crash in config file.
        """

        # Reading checkpoint for auth logs
        authlog_checkpoint = open(os.path.join(self.config['logs']['checkpointDir'],
                                           "authlog_checkpoint_data.txt"))
        self.last_offset_read['auth_last_fetched'] = json.loads(authlog_checkpoint.read())
        authlog_checkpoint.close()

        # Reading checkpoint for telephony logs
        telephony_checkpoint = open(os.path.join(self.config['logs']['checkpointDir'],
                                           "telephony_checkpoint_data.txt"))
        self.last_offset_read['telephony_last_fetched'] = json.loads(telephony_checkpoint.read())
        telephony_checkpoint.close()

        # Reading checkpoint for adminaction logs
        adminaction_checkpoint = open(
            os.path.join(self.config['logs']['checkpointDir'],
                         "adminaction_checkpoint_data.txt"))
        self.last_offset_read['adminaction_last_fetched'] = json.loads(
            adminaction_checkpoint.read())
        adminaction_checkpoint.close()
