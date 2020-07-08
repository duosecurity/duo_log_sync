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
from duologsync.consumer.adminaction_consumer import AdminactionConsumer
from duologsync.producer.adminaction_producer import AdminactionProducer
from duologsync.consumer.authlog_consumer import AuthlogConsumer
from duologsync.producer.authlog_producer import AuthlogProducer
from duologsync.consumer.telephony_consumer import TelephonyConsumer
from duologsync.producer.telephony_producer import TelephonyProducer
from duologsync.util import (set_util_globals, create_writer, get_log_offset,
                             get_enabled_endpoints)

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

    # TODO: Validate that the file path for config is valid and readable

    # Call a function to set all the Global variables in util
    set_util_globals(args.ConfigPath)

    # List of Producer/Consumer objects as asyncio tasks to be run
    tasks = create_consumer_producer_tasks(get_enabled_endpoints())

    # Run the Producers and Consumers
    asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))
    asyncio.get_event_loop().close()

# TODO: break this function up further when the config file begins to accept
# multiple connections. At that point, there will be a separate function for
# iterating through each connection which will set up a writer for a connection
# and then make a call to create consumer producer tasks while passing in the
# writer
def create_consumer_producer_tasks(enabled_endpoints):
    """
    Create a pair of Producer-Consumer objects for each enabled endpoint, and
    return a list containing asyncio tasks for running those objects.

    @param enabled_endpoints    List of endpoints for which to create Producer
                                / Consumer objects

    @return list of asyncio tasks for running the Producer and Consumer objects
    """

    # Object for writing data / logs across a network, used by Consumers
    writer = asyncio.get_event_loop().run_until_complete(create_writer())

    tasks = []

    # Enable endpoints based on user selection
    for endpoint in enabled_endpoints:
        log_queue = asyncio.Queue()
        producer = consumer = None

        # Create log_offset var for each endpoint
        log_offset = get_log_offset(endpoint)

        # Create the right pair of Producer-Consumer objects based on endpoint
        if endpoint == 'auth':
            producer = AuthlogProducer(log_queue, log_offset)
            consumer = AuthlogConsumer(log_queue, log_offset, writer)
        elif endpoint == 'telephony':
            producer = TelephonyProducer(log_queue, log_offset)
            consumer = TelephonyConsumer(log_queue, log_offset, writer)
        elif endpoint == 'adminaction':
            producer = AdminactionProducer(log_queue, log_offset)
            consumer = AdminactionConsumer(log_queue, log_offset, writer)
        else:
            logging.info("%s is not a recognized endpoint", endpoint)
            del log_queue
            continue

        tasks.append(asyncio.ensure_future(producer.produce()))
        tasks.append(asyncio.ensure_future(consumer.consume()))

    return tasks
