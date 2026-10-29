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
import os
import signal

from duologsync.consumer.authlog_consumer import AuthlogConsumer
from duologsync.producer.authlog_producer import AuthlogProducer
from duologsync.consumer.telephony_consumer import TelephonyConsumer
from duologsync.producer.telephony_producer import TelephonyProducer
from duologsync.consumer.trustmonitor_consumer import TrustMonitorConsumer
from duologsync.producer.trustmonitor_producer import TrustMonitorProducer
from duologsync.consumer.activity_consumer import ActivityConsumer
from duologsync.producer.activity_producer import ActivityProducer
from duologsync.util import create_admin, get_subaccounts, check_for_specific_endpoint
from duologsync.writer import Writer
from duologsync.config import Config
from duologsync.program import Program


def main():
    """
    Kicks off DuoLogSync by setting important variables, creating and running
    a Producer-Consumer pair for each log-type defined in a config file passed
    to the program.
    """

    arg_parser = argparse.ArgumentParser(
        prog="duologsync", description="Path to config file"
    )
    arg_parser.add_argument(
        "ConfigPath",
        metavar="config-path",
        type=str,
        help="Config to start application",
    )
    args = arg_parser.parse_args()

    # Handle shutting down the program via Ctrl-C
    signal.signal(signal.SIGINT, signal_handler)
    # Handle shutting down the program via SIGTERM
    signal.signal(signal.SIGTERM, signal_handler)

    # Create a config Dictionary from a YAML file located at args.ConfigPath
    config = Config.create_config(args.ConfigPath)
    Config.set_config(config)

    # Do extra checks for Trust Monitor support
    is_dtm_in_config = check_for_specific_endpoint("trustmonitor", config)
    log_format = Config.get_log_format()
    is_msp = Config.account_is_msp()

    if is_dtm_in_config and log_format != "JSON":
        Program.log(
            "DuoLogSync: Trust Monitor endpoint only supports JSON", logging.WARNING
        )
        return

    if is_dtm_in_config and is_msp:
        Program.log(
            "DuoLogSync: Trust Monitor endpoint only supports non-msp", logging.WARNING
        )
        return

    Program.setup_logging(Config.get_log_filepath())
    if not Program.is_running() or not ensure_checkpoint_directory():
        return

    # Dict of writers (server id: writer) to be used for consumer tasks
    server_to_writer = Writer.create_writers(Config.get_servers())

    # List of Producer/Consumer objects as asyncio tasks to be run
    tasks = create_tasks(server_to_writer)

    # Run the Producers and Consumers
    asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))
    asyncio.get_event_loop().close()

    if Program.is_logging_set():
        print(
            f"DuoLogSync: shutdown successfully. Check "
            f"{Config.get_log_filepath()} for program logs"
        )


def ensure_checkpoint_directory():
    """Create the configured checkpoint directory before collection starts."""

    checkpoint_directory = Config.get_checkpoint_dir()

    try:
        os.makedirs(checkpoint_directory, mode=0o700, exist_ok=True)
    except OSError as os_error:
        Program.initiate_shutdown(
            "checkpoint directory "
            f"'{checkpoint_directory}' could not be created: {os_error}"
        )
        return False

    if not os.access(checkpoint_directory, os.W_OK):
        Program.initiate_shutdown(
            f"checkpoint directory '{checkpoint_directory}' is not writable"
        )
        return False

    return True


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
        Program.log(
            f"DuoLogSync: stack frame from signal is {stack_frame}", logging.INFO
        )


def create_tasks(server_to_writer):
    """
    Create a pair of Producer-Consumer objects for each endpoint enabled within
    the account defined in config, or retrieve child accounts and do the same
    if the account is MSP. Return a list containing the asyncio tasks for
    running those objects.

    @param server_to_writer   Dictionary mapping server ids to writer objects

    @return list of asyncio tasks for running the Producer and Consumer objects
    """
    tasks = []

    account_ikey = Config.get_account_ikey()
    account_skey = Config.get_account_skey()
    proxy_server = Config.get_proxy_server()
    proxy_port = Config.get_proxy_port()
    request_timeout = Config.get_api_request_timeout()

    # Parent Admin API client. For MSP accounts it is used to discover
    # subaccounts; log calls use a child-scoped Admin client created below.
    admin = create_admin(
        account_ikey,
        account_skey,
        Config.get_account_hostname(),
        proxy_server=proxy_server,
        proxy_port=proxy_port,
        request_timeout=request_timeout,
    )

    # TODO: Ignore configured subaccounts when blocklist support is implemented.
    if Config.account_is_msp():
        subaccounts = get_subaccounts(admin)

        if not subaccounts:
            Program.log(
                "DuoLogSync: no MSP subaccounts were returned by the Admin API",
                logging.WARNING,
            )
            return tasks

        for subaccount in subaccounts:
            account_id = subaccount["account_id"]
            child_admin = create_admin(
                account_ikey,
                account_skey,
                subaccount["api_hostname"],
                proxy_server=proxy_server,
                proxy_port=proxy_port,
                request_timeout=request_timeout,
            )
            # TODO: This can be made into a separate function
            for mapping in Config.get_account_endpoint_server_mappings():
                # Get the writer to be used for this set of endpoints
                writer = server_to_writer[mapping.get("server")]

                for endpoint in mapping.get("endpoints"):
                    new_tasks = create_consumer_producer_pair(
                        endpoint, writer, child_admin, account_id
                    )
                    tasks.extend(new_tasks)
    else:
        for mapping in Config.get_account_endpoint_server_mappings():
            # Get the writer to be used for this set of endpoints
            writer = server_to_writer[mapping.get("server")]

            for endpoint in mapping.get("endpoints"):
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
        if child_account is not None:
            producer = AuthlogProducer(
                admin.json_api_call,
                log_queue,
                child_account_id=child_account,
                url_path="/admin/v2/logs/authentication",
            )
        else:
            producer = AuthlogProducer(admin.get_authentication_log, log_queue)
        consumer = AuthlogConsumer(log_format, log_queue, writer, child_account)
    elif endpoint == Config.TELEPHONY:
        producer = TelephonyProducer(
            admin.json_api_call,
            log_queue,
            child_account_id=child_account,
            url_path="/admin/v2/logs/telephony",
        )
        consumer = TelephonyConsumer(log_format, log_queue, writer, child_account)
    elif endpoint == Config.TRUST_MONITOR:
        producer = TrustMonitorProducer(
            admin.get_trust_monitor_events_by_offset, log_queue
        )
        consumer = TrustMonitorConsumer(log_format, log_queue, writer, child_account)
    elif endpoint == Config.ACTIVITY:
        producer = ActivityProducer(
            admin.json_api_call,
            log_queue,
            child_account_id=child_account,
            url_path="/admin/v2/logs/activity",
        )
        consumer = ActivityConsumer(log_format, log_queue, writer, child_account)
    else:
        Program.log(f"{endpoint} is not a recognized endpoint", logging.WARNING)
        del log_queue
        return []

    tasks = [
        asyncio.ensure_future(producer.produce()),
        asyncio.ensure_future(consumer.consume()),
    ]

    return tasks
