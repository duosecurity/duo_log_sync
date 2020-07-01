"""
Entry point into DuoLogSync, this module has many important functions and
tasks for initializing important variables used through DuoLogSync, creating
asyncio tasks for Producer and Consumer objects, and running those tasks.

Functions
---------

main():
    Parses the config file path passed from the command line, calls functions
    for initializing important variables and creating Producers / Consumers

create_global_tuple():
    Initialize important variables used throughout DuoLogSync and return a
    namedtuple which contains them and allows accessing the variables by name

create_consumer_producer_tasks():
    Create Producer/Consumer objects and return them as a list of runnable
    asyncio tasks
"""

import argparse
import asyncio
import logging

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

    # TODO: Validate that the file path for config is valid and readable

    # namedtuple containing important variables used through DuoLogSync
    g_vars = create_global_tuple(args.ConfigPath)

    # List of Producer/Consumer objects as asyncio tasks to be run
    tasks = create_consumer_producer_tasks(
        g_vars.config['logs']['endpoints']['enabled'],
        g_vars)

    # Run the Producers and Consumers
    g_vars.event_loop.run_until_complete(asyncio.gather(*tasks))
    g_vars.event_loop.close()

# TODO: break this function up further when the config file begins to accept
# multiple connections. At that point, there will be a separate function for
# iterating through each connection which will set up a writer for a connection
# and then make a call to create consumer producer tasks while passing in the
# writer
def create_consumer_producer_tasks(enabled_endpoints, g_vars):
    """
    Create a pair of Producer-Consumer objects for each enabled endpoint, and
    return a list containing asyncio tasks for running those objects.

    @param enabled_endpoints    List of endpoints for which DuoLogSync should
                                Produce and Consume logs from
    @param g_vars               Tuple of important variables needed to create
                                the Producer and Consumer objects

    @return list of asyncio tasks for running the Producer and Consumer objects
    """
    # Object for writing data / logs across a network, used by Consumers
    writer = g_vars.event_loop.run_until_complete(
        create_writer(g_vars.config, g_vars.event_loop)
    )

    tasks = []

    # Enable endpoints based on user selection
    for endpoint in enabled_endpoints:
        new_queue = asyncio.Queue(loop=g_vars.event_loop)
        producer = consumer = None

        # Populate last_offset_read for each enabled endpoint
        if g_vars.config['recoverFromCheckpoint']['enabled']:
            g_vars.last_offset_read[endpoint] = get_last_offset_read(
                g_vars.config['logs']['checkpointDir'],
                endpoint
            )

        # Create the right pair of Producer-Consumer objects based on endpoint
        if endpoint == 'auth':
            producer = AuthlogProducer(new_queue, g_vars)
            consumer = AuthlogConsumer(new_queue, writer, g_vars)
        elif endpoint == 'telephony':
            producer = TelephonyProducer(new_queue, g_vars)
            consumer = TelephonyConsumer(new_queue, writer, g_vars)
        elif endpoint == 'adminaction':
            producer = AdminactionProducer(new_queue, g_vars)
            consumer = AdminactionConsumer(new_queue, writer, g_vars)
        else:
            logging.info("%s is not a recognized endpoint", endpoint)
            del new_queue
            continue

        tasks.append(asyncio.ensure_future(producer.produce()))
        tasks.append(asyncio.ensure_future(consumer.consume()))

    return tasks

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
