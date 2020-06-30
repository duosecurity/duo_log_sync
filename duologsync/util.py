"""
Unrelated, but useful functions used in various places throughout DuoLogSync.

Functions
---------

create_writer()
    Create a connection object with a specified protocol for sending logs to a
    specified location

update_last_offset_read()
    Recover the last offset for a log type in case of a crash or error.

create_admin()
    Create an Admin object (from the duo_client library) with user credentials
    passed to the function
"""

import asyncio
import duo_client
import json
import logging
import os
import ssl
import sys

from duologsync.__version__ import __version__

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

def get_last_offset_read(checkpoint_dir, log_type):
    """
    Recover the last offset for a log type in case of a crash or error.

    @param checkpoint_dir   Directory where checkpoint / recovery files
                            are stored
    @param log_type         Name of the log for which recovery is occurring

    @return the last offset read for a log type based on checkpointing data
    """

    # TODO: This method should be used not just to recover timestamps, but to
    # set timestamps from where to start polling for a log if recovery doesn't
    # work or if recovery is not set. Take this functionality out of Producer
    last_offset_read = None

    # Reading checkpoint for log_type
    try:
        # Open the checkpoint file. The with statement automatically closes it
        with open(os.path.join(
                checkpoint_dir,
                f"{log_type}_checkpoint_data.txt")) as checkpoint:

            # Set last_offset_read equal to the contents of the checkpoint file
            last_offset_read = json.loads(checkpoint.read())

    # Most likely, the checkpoint file doesn't exist
    except OSError:
        # TODO: Edit this error message with changes made to the above TODO
        logging.warning("Could not read checkpoint file for %s logs, consuming "
                        "logs from %s timestamp", log_type, last_offset_read)

    return last_offset_read

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
