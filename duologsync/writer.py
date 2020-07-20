"""
This module contains functions related to creating open_connection objects /
Asyncion streams.
"""

import asyncio
import ssl
import logging
from socket import gaierror
from duologsync.program import Program

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
        Program.initiate_shutdown(
            f"The certificate file {cert_filename} could not be opened.")
        return None

    writer = create_writer(host, port, ssl_context)
    return writer

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
    Program.log(f"DuoLogSync: Opening connection to {host}:{port}")

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

    Program.initiate_shutdown(shutdown_reason)
    Program.log(f"DuoLogSync: check that host-{host} and port-{port} are "
                "correct in the config file", logging.WARNING)
    return None
