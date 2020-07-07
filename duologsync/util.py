"""
Unrelated, but useful functions used in various places throughout DuoLogSync.

Functions
---------

update_log_checkpoint()
    Save offset to the checkpoint file for the log type calling this function

create_g_vars():
    Initialize important variables used throughout DuoLogSync and return a
    namedtuple which contains them and allows accessing the variables by name

create_consumer_producer_tasks():
    Create Producer/Consumer objects and return them as a list of runnable
    asyncio tasks
"""

import asyncio
import duo_client
import json
import logging
import os
import ssl
import sys

from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from duologsync.config_generator import ConfigGenerator
from duologsync.__version__ import __version__

# Default timestamp for how far in the past logs may be fetched. Used when a
# log-type does not have a recovery file containing a timestamp from which
# logs should be fetched
default_log_offset = None
MILLISECONDS_PER_SECOND = 1000

# Create a tuple containing global variables that may be indexed by name
g_vars = namedtuple(
    'g_vars',
    ['admin', 'config', 'event_loop', 'executor'])

def update_log_checkpoint(log_type, log_offset):
    """
    Save log_offset to the checkpoint file for log_type.

    @param log_type     Used to determine which checkpoint file open
    @param log_offset   Information to save in the checkpoint file
    """

    checkpoint_filename = os.path.join(
        g_vars.config['logs']['checkpointDir'],
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
    global default_log_offset

    # The maximum amount of days in the past that a log may be fetched from
    days_in_past = g_vars.config['logs']['polling']['daysinpast']

    # Create a timestamp for screening logs that are too old
    default_log_offset = datetime.utcnow() - timedelta(days=days_in_past)
    default_log_offset = int(default_log_offset.timestamp())

async def create_writer(config, loop):
    host = config['transport']['host']
    port = config['transport']['port']
    protocol = config['transport']['protocol']

    if protocol == 'TCPSSL':
        try:
            logging.info("Opening connection to server over encrypted tcp...")
            cert_file = os.path.join(
                config['transport']['certFileDir'],
                config['transport']['certFileName']
            )

            sc = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,
                                            cafile=cert_file)

            _, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    host,
                    port,
                    loop=loop,
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
                    loop=loop
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
    recover_log_offset = g_vars.config['recoverFromCheckpoint']['enabled']

    log_offset = default_log_offset

    # Auth must have timestamp represented in milliseconds, not seconds
    if log_type == 'auth':
        log_offset *= MILLISECONDS_PER_SECOND

    # In this case, look for a checkpoint file from which to read the log offset
    if recover_log_offset:
        # Directory where log offset checkpoint files are saved
        checkpoint_directory = g_vars.config['Logs']['checkpointDir']

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

def create_g_vars(config_path):
    """
    Set important variables used throughout DuoLogSync for the global 
    namedtuple variable g_vars.

    @param config_path  Location of a config file which is used to create a
                        config dictionary object.
    """

    global g_vars

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
