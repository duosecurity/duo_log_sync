import asyncio
import logging

from duologsync.util import create_writer, get_last_offset_read

class LogSyncBase:

    @staticmethod
    def start(g_vars):
        """
        Driver class for duologsync application which initializes event loop
        and sets producer consumer for different endpoints as specified by
        user in config file.
        """
        from duologsync.producer.authlog_producer import AuthlogProducer
        from duologsync.producer.telephony_producer import TelephonyProducer
        from duologsync.consumer.authlog_consumer import AuthlogConsumer
        from duologsync.consumer.telephony_consumer import TelephonyConsumer
        from duologsync.producer.adminaction_producer import AdminactionProducer
        from duologsync.consumer.adminaction_consumer import AdminactionConsumer

        writer = g_vars.loop.run_until_complete(
            create_writer(g_vars.config, g_vars.loop)
        )

        # Enable endpoints based on user selection
        tasks = []
        enabled_endpoints = g_vars.config['logs']['endpoints']['enabled']
        for endpoint in enabled_endpoints:
            new_queue = asyncio.Queue(loop=g_vars.loop)
            producer = consumer = None

            # Populate last_offset_read for each enabled endpoint
            if g_vars.config['recoverFromCheckpoint']['enabled']:
                g_vars.last_offset_read[
                    f"{endpoint}_checkpoint_data.txt"
                ] = get_last_offset_read(
                    g_vars.config['logs']['checkpointDir'],
                    endpoint
                )

            if endpoint == 'auth':
                producer = AuthlogProducer(g_vars.config, g_vars.last_offset_read,
                                           new_queue, g_vars)
                consumer = AuthlogConsumer(g_vars.config, g_vars.last_offset_read,
                                           new_queue, writer)
            elif endpoint == "telephony":
                producer = TelephonyProducer(g_vars.config, g_vars.last_offset_read,
                                             new_queue, g_vars)
                consumer = TelephonyConsumer(g_vars.config, g_vars.last_offset_read,
                                             new_queue, writer)
            elif endpoint == "adminaction":
                producer = AdminactionProducer(g_vars.config,
                                               g_vars.last_offset_read,
                                               new_queue, g_vars)
                consumer = AdminactionConsumer(g_vars.config,
                                               g_vars.last_offset_read,
                                               new_queue, writer)
            else:
                logging.info("%s is not a recognized endpoint", endpoint)
                del new_queue
                continue

            tasks.append(asyncio.ensure_future(producer.produce()))
            tasks.append(asyncio.ensure_future(consumer.consume()))

        g_vars.loop.run_until_complete(asyncio.gather(*tasks))
        g_vars.loop.close()
