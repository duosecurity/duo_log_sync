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
from duologsync.consumer.trustmonitor_consumer import TrustMonitorConsumer
from duologsync.producer.trustmonitor_producer import TrustMonitorProducer
from duologsync.util import create_admin, check_for_specific_endpoint
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
    signal.signal(signal.SIGINT, signal_handler)
    # Handle shutting down the program via SIGTERM
    signal.signal(signal.SIGTERM, signal_handler)

    # Create a config Dictionary from a YAML file located at args.ConfigPath
    config = Config.create_config(args.ConfigPath)
    Config.set_config(config)

    # Do extra checks for Trust Monitor support
    is_dtm_in_config = check_for_specific_endpoint('trustmonitor', config)
    log_format = Config.get_log_format()
    is_msp = Config.account_is_msp()

    if (is_dtm_in_config and log_format != 'JSON'):
        Program.log(f"DuoLogSync: Trust Monitor endpoint only supports JSON", logging.WARNING)
        return

    if (is_dtm_in_config and is_msp):
        Program.log(f"DuoLogSync: Trust Monitor endpoint only supports non-msp", logging.WARNING)
        return

    Program.setup_logging(Config.get_log_filepath())

    # Dict of writers (server id: writer) to be used for consumer tasks
    server_to_writer = Writer.create_writers(Config.get_servers())

    # List of Producer/Consumer objects as asyncio tasks to be run
    tasks = create_tasks(server_to_writer)

    # Run the Producers and Consumers
    asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))
    asyncio.get_event_loop().close()

    if Program.is_logging_set():
        print(f"DuoLogSync: shutdown successfully. Check "
              f"{Config.get_log_filepath()} for program logs")

def signal_handler(signal_number, stack_frame):
    """
    Handler for signals to gracefully shutdown DuoLogSync
    """

    if signal_number == signal.SIGINT:
        shutdown_reason = f"received signal {signal_number} (Ctrl-C)"
    else:
        shutdown_reason = f"received signal {signal.strsignal(signal_number)}"

    Program.initiate_shutdown(shutdown_reason)

    if stack_frame:
        Program.log(f"DuoLogSync: stack frame from signal is {stack_frame}",
                    logging.INFO)

def create_tasks(server_to_writer):
    """
    Create a pair of Producer-Consumer objects for each endpoint enabled within
    the account defined in config, or retrieve child accounts and do the same
    if the account is MSP. Return a list containing the asyncio tasks for
    running those objects.

    @param writer   Dictionary mapping server ids to writer objects

    @return list of asyncio tasks for running the Producer and Consumer objects
    """
    tasks = []

    # Object with functions needed to utilize log API calls
    admin = create_admin(
        Config.get_account_ikey(), Config.get_account_skey(),
        Config.get_account_hostname(), is_msp=Config.account_is_msp(),
        proxy_server=Config.get_proxy_server(), proxy_port=Config.get_proxy_port())

    # This is where functionality would be added to check if an account is MSP
    # (Config.account_is_msp), and then retrieve child accounts (ignoring those
    # in a blocklist) if the account is indeed MSP
    # TODO: Implement blocklist
    if Config.account_is_msp():
        child_account = admin.get_child_accounts()
        child_accounts_id = [account['account_id'] for account in child_account]

        for account in child_accounts_id:
            # TODO: This can be made into a separate function
            for mapping in Config.get_account_endpoint_server_mappings():
                # Get the writer to be used for this set of endpoints
                writer = server_to_writer[mapping.get('server')]

                for endpoint in mapping.get('endpoints'):
                    new_tasks = create_consumer_producer_pair(endpoint, writer, admin, account)
                    tasks.extend(new_tasks)
    else:
        for mapping in Config.get_account_endpoint_server_mappings():
            # Get the writer to be used for this set of endpoints
            writer = server_to_writer[mapping.get('server')]

            for endpoint in mapping.get('endpoints'):
                new_tasks = create_consumer_producer_pair(endpoint, writer, admin)
                tasks.extend(new_tasks)

    return tasks

def create_consumer_producer_pair(endpoint, writer, admin, child_account=None):
    """
    Create a pair of Producer-Consumer objects for each endpoint and return a
    list containing the asyncio tasks for running those objects.

    @param endpoint     Log type to create producer/consumer pair for
    @param writer       Object for writing logs to a server
    @param admin        Object from which to get the correct API endpoints
    @param child_account If present, this is being used by MSP and pass appropriate account id

    @return list of asyncio tasks for running the Producer and Consumer objects
    """

    # The format a log should have before being consumed and sent
    log_format = Config.get_log_format()
    log_queue = asyncio.Queue()
    producer = consumer = None

    # Create the right pair of Producer-Consumer objects based on endpoint
    if endpoint == Config.AUTH:
        if Config.account_is_msp():
            producer = AuthlogProducer(admin.json_api_call, log_queue,
                                       child_account_id=child_account,
                                       url_path="/admin/v2/logs/authentication")
        else:
            producer = AuthlogProducer(admin.get_authentication_log, log_queue)
        consumer = AuthlogConsumer(log_format, log_queue, writer, child_account)
    elif endpoint == Config.TELEPHONY:
        if Config.account_is_msp():
            producer = TelephonyProducer(admin.json_api_call, log_queue,
                                         child_account_id=child_account,
                                         url_path='/admin/v1/logs/telephony')
        else:
            producer = TelephonyProducer(admin.get_telephony_log, log_queue)
        consumer = TelephonyConsumer(log_format, log_queue, writer, child_account)
    elif endpoint == Config.ADMIN:
        if Config.account_is_msp():
            producer = AdminactionProducer(admin.json_api_call, log_queue,
                                           child_account_id=child_account,
                                           url_path='/admin/v1/logs/administrator')
        else:
            producer = AdminactionProducer(admin.get_administrator_log, log_queue)
        consumer = AdminactionConsumer(log_format, log_queue, writer, child_account)
    elif endpoint == Config.TRUST_MONITOR:
        producer = TrustMonitorProducer(admin.get_trust_monitor_events_by_offset, log_queue)
        consumer = TrustMonitorConsumer(log_format, log_queue, writer, child_account)
    else:
        Program.log(f"{endpoint} is not a recognized endpoint", logging.WARNING)
        del log_queue
        return []

    tasks = [asyncio.ensure_future(producer.produce()),
             asyncio.ensure_future(consumer.consume())]

    return tasks
