"""
Entry point into DuoLogSync, this module has many important functions and
tasks for initializing important variables used through DuoLogSync, creating
asyncio tasks for Producer and Consumer objects, and running those tasks.

Functions
---------

main():
    Parses the config file path passed from the command line, calls functions
    for initializing important variables and creating Producers / Consumers

create_consumer_producer_tasks():
    Create Producer/Consumer objects and return them as a list of runnable
    asyncio tasks
"""

import argparse
import asyncio
import logging
import signal
from duologsync.consumer.adminaction_consumer import AdminactionConsumer
from duologsync.producer.adminaction_producer import AdminactionProducer
from duologsync.consumer.authlog_consumer import AuthlogConsumer
from duologsync.producer.authlog_producer import AuthlogProducer
from duologsync.consumer.telephony_consumer import TelephonyConsumer
from duologsync.producer.telephony_producer import TelephonyProducer
from duologsync.util import create_admin, create_writer, set_logger
from duologsync.config import Config

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

    # Handle shutting down the program via Ctrl-C
    signal.signal(signal.SIGINT, sigint_handler)

    # Create a config Dictionary from a YAML file located at args.ConfigPath
    config = Config.create_config(args.ConfigPath)
    Config.set_config(config)

    set_logger(Config.get_log_directory())

    # List of Producer/Consumer objects as asyncio tasks to be run
    tasks = create_consumer_producer_tasks(Config.get_enabled_endpoints())

    # Run the Producers and Consumers
    asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))
    asyncio.get_event_loop().close()

    print("DuoLogSync: shutdown successfully. Check %s/duologsync.log for "
          "program messages and logs." % Config.get_log_directory())

def sigint_handler(signal_number, stack_frame):
    """
    Handler for SIGINT (Ctrl-c) to gracefully shutdown DuoLogSync
    """

    if signal_number is signal.SIGINT:
        logging.info('DuoLogSync: recevied SIGINT (Ctrl-c). Shutting down')

    if stack_frame:
        logging.info('DuoLogSync')

    Config.initiate_shutdown()

def create_consumer_producer_tasks(enabled_endpoints):
    """
    Create a pair of Producer-Consumer objects for each enabled endpoint, and
    return a list containing asyncio tasks for running those objects.

    @param enabled_endpoints    List of endpoints for which to create Producer
                                / Consumer objects

    @return list of asyncio tasks for running the Producer and Consumer objects
    """

    # Object with functions needed to utilize log API calls
    admin = create_admin(Config.get_ikey(), Config.get_skey(),
                         Config.get_host())

    # Object for writing data / logs across a network, used by Consumers
    writer = asyncio.get_event_loop().run_until_complete(create_writer())
    tasks = []

    # Enable endpoints based on user selection
    for endpoint in enabled_endpoints:
        log_queue = asyncio.Queue()
        producer = consumer = None

        # Create the right pair of Producer-Consumer objects based on endpoint
        if endpoint == 'auth':
            producer = AuthlogProducer(admin.get_authentication_log, log_queue)
            consumer = AuthlogConsumer(log_queue, producer, writer)
        elif endpoint == 'telephony':
            producer = TelephonyProducer(admin.get_telephony_log, log_queue)
            consumer = TelephonyConsumer(log_queue, producer, writer)
        elif endpoint == 'adminaction':
            producer = AdminactionProducer(admin.get_administrator_log,
                                           log_queue)
            consumer = AdminactionConsumer(log_queue, producer, writer)
        else:
            logging.info("%s is not a recognized endpoint", endpoint)
            del log_queue
            continue

        tasks.append(asyncio.ensure_future(producer.produce()))
        tasks.append(asyncio.ensure_future(consumer.consume()))

    return tasks
