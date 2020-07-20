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
import os
import signal
from duologsync.consumer.adminaction_consumer import AdminactionConsumer
from duologsync.producer.adminaction_producer import AdminactionProducer
from duologsync.consumer.authlog_consumer import AuthlogConsumer
from duologsync.producer.authlog_producer import AuthlogProducer
from duologsync.consumer.telephony_consumer import TelephonyConsumer
from duologsync.producer.telephony_producer import TelephonyProducer
from duologsync.util import create_admin
from duologsync.writer import create_tcpssl_writer, create_writer
from duologsync.config import Config
from duologsync.program import Program

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

    Program.setup_logging(Config.get_log_filepath())

    # List of Producer/Consumer objects as asyncio tasks to be run
    tasks = create_consumer_producer_tasks(Config.get_enabled_endpoints())

    # Run the Producers and Consumers
    asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))
    asyncio.get_event_loop().close()

    print("DuoLogSync: shutdown successfully. Check %s for "
          "program messages and logs." % Config.get_log_filepath())

def sigint_handler(signal_number, stack_frame):
    """
    Handler for SIGINT (Ctrl-C) to gracefully shutdown DuoLogSync
    """

    shutdown_reason = ''

    if signal_number == signal.SIGINT:
        shutdown_reason = 'received SIGINT (Ctrl-C)'

    print(shutdown_reason)
    Program.initiate_shutdown(shutdown_reason)

    if stack_frame:
        Program.log(f"DuoLogSync: stack frame from Ctrl-C is {stack_frame}")

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
    protocol = Config.get_value(['transport', 'protocol'])
    host = Config.get_value(['transport', 'host'])
    port = Config.get_value(['transport', 'port'])
    writer = None

    if protocol == 'TCPSSL':
        writer = asyncio.get_event_loop().run_until_complete(
            create_tcpssl_writer(
                host,
                port,
                os.path.join(
                    Config.get_value(['transport', 'certFileDir']),
                    Config.get_value(['transport', 'certFileName'])
                )
            )
        )
    else:
        writer = asyncio.get_event_loop().run_until_complete(
            create_writer(host, port)
        )

    tasks = []

    # Check if an error from creating the writer caused a program shutdown
    if not Program.is_running():
        return tasks

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
            Program.log(f"{endpoint} is not a recognized endpoint")
            del log_queue
            continue

        tasks.append(asyncio.ensure_future(producer.produce()))
        tasks.append(asyncio.ensure_future(consumer.consume()))

    return tasks
