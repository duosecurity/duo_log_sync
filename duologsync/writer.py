"""
This module contains functions related to creating open_connection objects /
Asyncion streams.
"""

import asyncio
import logging
import ssl
from socket import gaierror
from duologsync.config import Config

@staticmethod
async def create_tcpssl_writer(host, port, cert_filename):
    """
    Wrapper for the create_writer function for the encrypted TCP protocol.

    @param host Hostname of the network connection to establish
    @param port Port of the network connection to establish

    @return an asyncio open_connection object
    """

    try:
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,
                                                 cafile=cert_filename)

    except FileNotFoundError:
        Config.initiate_shutdown(
            f"The certificate file {cert_filename} could not be opened.")
        return None

    writer = create_writer(host, port, ssl_context)
    return writer

@staticmethod
async def create_writer(host, port, ssl_context=None):
    """
    Wrapper around the asyncio.open_connection function with exception handling
    for creating a network connection to host and port.

    @param host Hostname of the network connection to establish
    @param port Port of the network connection to establish
    @paral ssl  Used to create an encrypted connect. Not required

    @return an asyncio open_connection object used to write over an established
            network connection to the host and port specified
    """

    shutdown_reason = None
    logging.info("DuoLogSync: Opening connection to %s:%s", host, port)

    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port, ssl=ssl_context),
            timeout=60
        )

    # Couldn't establish a connection within 60 seconds
    except asyncio.TimeoutError:
        shutdown_reason = 'connection to server timed-out after 60 seconds'

    # If an invalid hostname or port number is given
    except gaierror as gai_error:
        shutdown_reason = f"{gai_error}"

    # Simply failed to connect using the host and port given
    except OSError as os_error:
        shutdown_reason = f"{os_error}"

    # An error did not occur and the writer was successfully created
    else:
        return writer

    Config.initiate_shutdown(shutdown_reason)
    logging.warning("DuoLogSync: check that host - %s and port - %s are "
                    "correct in the config file", host, port)
    return None
