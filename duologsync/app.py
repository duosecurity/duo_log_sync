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
from duologsync.util import create_admin
from duologsync.writer import Writer
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

    # Dict of writers (server id: writer) to be used for consumer tasks
    writers = Writer.create_writers(Config.get_servers())

    # List of Producer/Consumer objects as asyncio tasks to be run
    tasks = create_tasks(Config.get_accounts(), writers)

    # Run the Producers and Consumers
    asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))
    asyncio.get_event_loop().close()

    if Program.is_logging_set():
        print(f"DuoLogSync: shutdown successfully. Check "
              f"{Config.get_log_filepath()} for program logs")

def sigint_handler(signal_number, stack_frame):
    """
    Handler for SIGINT (Ctrl-C) to gracefully shutdown DuoLogSync
    """

    shutdown_reason = f"received signal {signal_number} (Ctrl-C)"
    Program.initiate_shutdown(shutdown_reason)

    if stack_frame:
        Program.log(f"DuoLogSync: stack frame from Ctrl-C is {stack_frame}",
                    logging.INFO)

def create_tasks(accounts, server_to_writer):
   """
    Create a pair of Producer-Consumer objects for each endpoint enabled within
    each account in the accounts list and return a list containing the asyncio
    tasks for running those objects.

    @param accounts List of accounts for which Producer / Consumer objects
                    shall be created
    @param writer   Dictionary mapping server ids to writer objects

    @return list of asyncio tasks for running the Producer and Consumer objects
    """
    tasks = []

    for account in accounts:
        # If account['is_msp'], retrieve and iterate all child accounts,
        # future Accounts API change! Stay Tuned!!
        # Do a set comparison between child accounts received and the blocklist
        # AKA children NAND blocklist == working_set

        # Object with functions needed to utilize log API calls
        admin = create_admin(account['ikey'], account['skey'],
                             account['hostname'])

        for mapping in account['endpoint_server_mappings']:
            # Get list of writers to be used for this set of endpoints
            writers = [server_to_writer[server] for server in mapping['servers']]
            new_tasks = METHOD_NAME(endpoints, writers, admin)

            # Add the new_tasks to the ever growing list of tasks
            tasks.append(new_tasks)

    return tasks

def create_consumer_producer_pairs(endpoints, writers, admin):
    """
    Create a pair of Producer-Consumer objects for each endpoint and return a
    list containing the asyncio tasks for running those objects.

    @param endpoints    List of endpoints to create producers/consumers for
    @param writers      List of writers to pass on to a consumer object
    @param admin        Object from whcih to get the correct API endpoints

    @return list of asyncio tasks for running the Producer and Consumer objects
    """

    # The format a log should have before being consumed and sent
    log_format = Config.get_log_format()

    # List of Consumer / Writer tasks to be run in the Asyncio event loop
    tasks = []

    # Enable endpoints based on user selection
    for endpoint in endpoints:
        log_queue = asyncio.Queue()
        producer = consumer = None

        # Create the right pair of Producer-Consumer objects based on endpoint
        if endpoint == Config.AUTH:
            producer = AuthlogProducer(admin.get_authentication_log, log_queue)
            consumer = AuthlogConsumer(log_format, log_queue, writers)
        elif endpoint == Config.TELEPHONY:
            producer = TelephonyProducer(admin.get_telephony_log, log_queue)
            consumer = TelephonyConsumer(log_format, log_queue, writers)
        elif endpoint == Config.ADMIN:
            producer = AdminactionProducer(admin.get_administrator_log,
                                           log_queue)
            consumer = AdminactionConsumer(log_format, log_queue, writers)
        else:
            Program.log(f"{endpoint} is not a recognized endpoint",
                        logging.WARNING)
            del log_queue
            continue

        tasks.append(asyncio.ensure_future(producer.produce()))
        tasks.append(asyncio.ensure_future(consumer.consume()))

    return tasks
