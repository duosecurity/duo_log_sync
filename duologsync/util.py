"""
Unrelated, but useful functions used in various places throughout DuoLogSync.

Functions
---------

run_in_executor()
    The function represented by function_obj is a high latency call which will
    block the event loop. Thus, the function is run in an executor - a
    dedicated thread pool - which allows for the event loop to do other work
    while the given function is being made.

create_writer()
    Create a network connection for writing logs to wherever the user would
    like. Values in the user defined config determine where the connection
    leads to, and the protocol used to send logs.

get_log_offset()
    Retrieve the offset from which logs of log_type should be fetched either by
    using the default offset or by using a timestamp saved in a checkpoint file

update_log_checkpoint()
    Save offset to the checkpoint file for the log type calling this function

set_logger():
    Function to set up logging for DuoLogSync
"""

import os
import ssl
import sys
import json
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
import duo_client
from duologsync.config import Config
from duologsync.__version__ import __version__

MILLISECONDS_PER_SECOND = 1000
EXECUTOR = ThreadPoolExecutor(3)

def set_logger():
    """
    Function to set up logging for DuoLogSync.

    @param log_dir  Directory where logging messages should be saved
    """

    log_directory = Config.get_value(['logs', 'logDir'])

    logging.basicConfig(
        # Where to save logs
        filename=os.path.join(log_directory, "duologsync.log"),

        # How logs should be formatted
        format='%(asctime)s %(levelname)-8s %(message)s',

        # Minimum level required of a log in order to be seen / written
        level=logging.INFO,

        # Date format to use with logs
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logging.info("Starting duologsync...")

async def run_in_executor(function_obj):
    """
    The function represented by function_obj is a high latency call which will
    block the event loop. Thus, the function is run in an executor - a
    dedicated thread pool - which allows for the event loop to do other work
    while the given function is being made.

    @param function_obj A high-latency, callable object to run in the executor

    @return the result of calling the function in function_obj
    """

    result = await asyncio.get_event_loop().run_in_executor(
        EXECUTOR,
        function_obj
    )

    return result

async def create_writer():
    """
    Create a network connection for writing logs to wherever the user would
    like. Values in the user defined config determine where the connection
    leads to, and the protocol used to send logs.

    @return the writer object, used to write logs to a specific location
    """
    host = Config.get_value(['transport', 'host'])
    port = Config.get_value(['transport', 'port'])
    protocol = Config.get_value(['transport', 'protocol'])

    if protocol == 'TCPSSL':
        try:
            logging.info("Opening connection to server over encrypted tcp...")
            cert_file = os.path.join(
                Config.get_value(['transport', 'certFileDir']),
                Config.get_value(['transport', 'certFileName'])
            )

            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,
                                                 cafile=cert_file)

            _, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    host,
                    port,
                    loop=asyncio.get_event_loop(),
                    ssl=context),
                timeout=60)
            return writer
        except ConnectionError:
            logging.error("Connection to server failed at host %s and "
                          "port %s", 'localhost', '8888')
            sys.exit(1)
        except Exception as error:
            logging.error("Connection to server failed with exception "
                          "%s", error)
            logging.error("Terminating the application...")
            sys.exit(1)

    if protocol == 'TCP':
        try:
            logging.info(
                "Opening connection to server over tcp...")
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    host,
                    port,
                    loop=asyncio.get_event_loop()
                ),
                timeout=60
            ) # Default connection timeout set to 1min
            return writer
        except asyncio.TimeoutError as timeout_error:
            logging.error("Connection to server timedout after 60 seconds "
                          "%s", timeout_error)
            logging.error("Terminating the application...")
            sys.exit(1)
        except Exception as error:
            logging.error("Connection to server failed with exception "
                          "%s", error)
            logging.error("Terminating the application...")
            sys.exit(1)

def get_log_offset(log_type):
    """
    Retrieve the offset from which logs of log_type should be fetched either by
    using the default offset or by using a timestamp saved in a checkpoint file

    @param log_type             Name of the log for which recovery is occurring

    @return the last offset read for a log type based on checkpointing data
    """

    # Whether checkpoint files should be used to retrieve log offset info
    recover_log_offset = Config.get_value(['recoverFromCheckpoint', 'enabled'])

    log_offset = Config.get_value(['logs', 'offset'])

    # Auth must have timestamp represented in milliseconds, not seconds
    if log_type == 'auth':
        log_offset *= MILLISECONDS_PER_SECOND

    # In this case, look for a checkpoint file from which to read the log offset
    if recover_log_offset:
        # Directory where log offset checkpoint files are saved
        checkpoint_directory = Config.get_value(['Logs', 'checkpointDir'])

        try:
            # Open the checkpoint file, 'with' statement automatically closes it
            with open(os.path.join(
                    checkpoint_directory,
                    f"{log_type}_checkpoint_data.txt")) as checkpoint:

                # Set log_offset equal to the contents of the checkpoint file
                log_offset = json.loads(checkpoint.read())

        # Most likely, the checkpoint file doesn't exist
        except OSError:
            logging.warning("Could not read checkpoint file for %s logs, "
                            "consuming logs from %s timestamp",
                            log_type, log_offset)

    return log_offset

def create_admin(ikey=None, skey=None, host=None):
    """
    Create an Admin object (from the duo_client library) with the given values.
    The Admin object has many functions for using Duo APIs and retrieving logs.

    @param ikey Duo Client ID (Integration Key)
    @param skey Duo Client Secret for proving identity / access (Secrey Key)
    @param host URI where data / logs will be fetched from

    @return a newly created Admin object
    """


    ikey = ikey or Config.get_value(['duoclient', 'ikey'])
    skey = skey or Config.get_value(['duoclient', 'skey'])
    host = host or Config.get_value(['duoclient', 'host'])

    admin = duo_client.Admin(
        ikey=ikey,
        skey=skey,
        host=host,
        user_agent=f"Duo Log Sync/{__version__}"
    )

    logging.info("duo_client Admin initialized for ikey: %s, host: %s",
                 ikey, host)

    return admin
