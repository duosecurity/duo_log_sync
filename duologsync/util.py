"""
Unrelated, but useful functions used in various places throughout DuoLogSync.

Functions
---------

update_log_checkpoint()
    Save offset to the checkpoint file for the log type calling this function

set_util_globals():
    Initialize important variables used throughout DuoLogSync and return a
    namedtuple which contains them and allows accessing the variables by name

create_consumer_producer_tasks():
    Create Producer/Consumer objects and return them as a list of runnable
    asyncio tasks
"""

import os
import ssl
import sys
import json
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import duo_client
from duologsync.config_generator import ConfigGenerator
from duologsync.__version__ import __version__

# Default timestamp for how far in the past logs may be fetched. Used when a
# log-type does not have a recovery file containing a timestamp from which
# logs should be fetched
DEFAULT_LOG_OFFSET = None
MILLISECONDS_PER_SECOND = 1000
SECONDS_PER_MINUTE = 60
MINIMUM_POLLING_DURATION = 2 * SECONDS_PER_MINUTE

ADMIN = None
CONFIG = None
EXECUTOR = None
POLLING_DURATION = None

def get_enabled_endpoints():
    """
    Return the list of endpoints that are enabled from config

    @return the endpoints enabled in config
    """

    return CONFIG['logs']['endpoints']['enabled']

def get_admin():
    """
    Method to retrieve the admin global variable.

    @return the admin global variable
    """

    return ADMIN

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

def update_log_checkpoint(log_type, log_offset):
    """
    Save log_offset to the checkpoint file for log_type.

    @param log_type     Used to determine which checkpoint file open
    @param log_offset   Information to save in the checkpoint file
    """

    checkpoint_filename = os.path.join(
        CONFIG['logs']['checkpointDir'],
        f"{log_type}_checkpoint_data.txt")

    checkpoint_file = open(checkpoint_filename, 'w')
    checkpoint_file.write(json.dumps(log_offset))

    # According to Python docs, closing a file also flushes the file
    checkpoint_file.close()

def set_default_log_offset():
    """
    Setter for the variable 'default_log_offset'.
    """

    # Need to name default_log_offset as global in order to set it
    global DEFAULT_LOG_OFFSET

    # The maximum amount of days in the past that a log may be fetched from
    days_in_past = CONFIG['logs']['polling']['daysinpast']

    # Create a timestamp for screening logs that are too old
    DEFAULT_LOG_OFFSET = datetime.utcnow() - timedelta(days=days_in_past)
    DEFAULT_LOG_OFFSET = int(DEFAULT_LOG_OFFSET.timestamp())

async def create_writer():
    host = CONFIG['transport']['host']
    port = CONFIG['transport']['port']
    protocol = CONFIG['transport']['protocol']

    if protocol == 'TCPSSL':
        try:
            logging.info("Opening connection to server over encrypted tcp...")
            cert_file = os.path.join(
                CONFIG['transport']['certFileDir'],
                CONFIG['transport']['certFileName']
            )

            sc = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,
                                            cafile=cert_file)

            _, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    host,
                    port,
                    loop=asyncio.get_event_loop(),
                    ssl=sc),
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
    recover_log_offset = CONFIG['recoverFromCheckpoint']['enabled']

    log_offset = DEFAULT_LOG_OFFSET

    # Auth must have timestamp represented in milliseconds, not seconds
    if log_type == 'auth':
        log_offset *= MILLISECONDS_PER_SECOND

    # In this case, look for a checkpoint file from which to read the log offset
    if recover_log_offset:
        # Directory where log offset checkpoint files are saved
        checkpoint_directory = CONFIG['Logs']['checkpointDir']

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

def create_admin(ikey, skey, host):
    """
    Create an Admin object (from the duo_client library) with the given values.
    The Admin object has many functions for using Duo APIs and retrieving logs.

    @param ikey Duo Client ID (Integration Key)
    @param skey Duo Client Secret for proving identity / access (Secrey Key)
    @param host URI where data / logs will be fetched from

    @return a newly created Admin object
    """

    try:
        admin = duo_client.Admin(
            ikey=ikey,
            skey=skey,
            host=host,
            user_agent=f"Duo Log Sync/{__version__}"
        )

        logging.info("duo_client Admin initialized for ikey: %s, host: %s",
                     ikey, host)

    except Exception as error:
        logging.error("Failed to create duo_client Admin: %s", error)
        sys.exit(1)

    return admin

def set_polling_duration():
    """
    Method to set the value of the global variable polling_duration
    """

    global POLLING_DURATION

    # The number of minutes a producer will poll for logs
    POLLING_DURATION = CONFIG['logs']['polling']['duration']

    # Convert polling_duration to seconds
    POLLING_DURATION *= SECONDS_PER_MINUTE

    # Use the minimum polling duration if the user specifies a lower number
    POLLING_DURATION = max(POLLING_DURATION, MINIMUM_POLLING_DURATION)

def get_polling_duration():
    """
    Method to get the value of the global variable polling_duration

    @return polling_duration
    """

    return POLLING_DURATION

def set_util_globals(config_path):
    """
    Set global variables used throughout util

    @param config_path  Location of a config file which is used to create a
                        config dictionary object.
    """

    global CONFIG, ADMIN, EXECUTOR

    # Dictionary populated with values from the config file passed to DuoLogSync
    CONFIG = ConfigGenerator().get_config(config_path)

    # Object that allows for interaction with Duo APIs to fetch logs / data
    ADMIN = create_admin(
        CONFIG['duoclient']['ikey'],
        CONFIG['duoclient']['skey'],
        CONFIG['duoclient']['host']
    )

    # Allocate an execution environment of 3 threads for high latency tasks
    EXECUTOR = ThreadPoolExecutor(3)

    set_polling_duration()
    set_default_log_offset()
