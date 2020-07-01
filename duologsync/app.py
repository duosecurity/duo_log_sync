import argparse
import asyncio

from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from duologsync.config_generator import ConfigGenerator
from duologsync.util import create_admin, create_writer, get_last_offset_read
from duologsync.consumer.adminaction_consumer import AdminactionConsumer
from duologsync.producer.adminaction_producer import AdminactionProducer
from duologsync.consumer.authlog_consumer import AuthlogConsumer
from duologsync.producer.authlog_producer import AuthlogProducer
from duologsync.consumer.telephony_consumer import TelephonyConsumer
from duologsync.producer.telephony_producer import TelephonyProducer

def main():
    """
    Kicks off DuoLogSync by setting important variables, creating and running
    a Producer-Consumer pair for each log-type defined in a config file passed
    to the program.
    """

    arg_parser = argparse.ArgumentParser(prog='duologsync',
                                         description="Path to config file")
    arg_parser.add_argument('ConfigPath', metavar='config-path', type=str,
                            help='Config to start application')
    args = arg_parser.parse_args()

    # namedtuple containing important variables used through DuoLogSync
    g_vars = create_global_tuple(args.ConfigPath)

    #####################

    writer = g_vars.event_loop.run_until_complete(
        create_writer(g_vars.config, g_vars.event_loop)
    )

    # Enable endpoints based on user selection
    tasks = []
    enabled_endpoints = g_vars.config['logs']['endpoints']['enabled']
    for endpoint in enabled_endpoints:
        new_queue = asyncio.Queue(loop=g_vars.event_loop)
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
            consumer = AuthlogConsumer(new_queue, writer, g_vars)
        elif endpoint == "telephony":
            producer = TelephonyProducer(g_vars.config, g_vars.last_offset_read,
                                         new_queue, g_vars)
            consumer = TelephonyConsumer(new_queue, writer, g_vars)
        elif endpoint == "adminaction":
            producer = AdminactionProducer(g_vars.config,
                                           g_vars.last_offset_read,
                                           new_queue, g_vars)
            consumer = AdminactionConsumer(new_queue, writer, g_vars)
        else:
            logging.info("%s is not a recognized endpoint", endpoint)
            del new_queue
            continue

        tasks.append(asyncio.ensure_future(producer.produce()))
        tasks.append(asyncio.ensure_future(consumer.consume()))

    g_vars.event_loop.run_until_complete(asyncio.gather(*tasks))
    g_vars.event_loop.close()

    #####################

    logger = duologsync.duo_log_sync_base.LogSyncBase()
    logger.start(g_vars)

def create_global_tuple(config_path):
    """
    Initialize important variables used throughout DuoLogSync and return a
    namedtuple which contains them and allows accessing the variables by name.

    @param config_path  Location of a config file which is used to create a
                        config dictionary object.

    @return a namedtuple with important variables used throughout DuoLogSync
    """

    # Create a tuple containing global variables that may be indexed by name
    g_vars = namedtuple(
        'g_vars',
        ['admin', 'config', 'event_loop', 'executor', 'last_offset_read'])

    # Dictionary populated with values from the config file passed to DuoLogSync
    g_vars.config = ConfigGenerator().get_config(config_path)

    # Object that allows for interaction with Duo APIs to fetch logs / data
    g_vars.admin = create_admin(
        g_vars.config['duoclient']['ikey'],
        g_vars.config['duoclient']['skey'],
        g_vars.config['duoclient']['host']
    )

    # Object that can run asynchronous tasks, call-backs and subprocesses
    g_vars.event_loop = asyncio.get_event_loop()

    # Allocate an execution environment of 3 threads for high latency tasks
    g_vars.executor = ThreadPoolExecutor(3)

    # Dictionary for storing the latest timestamp received for each log type
    g_vars.last_offset_read = {}

    return g_vars
