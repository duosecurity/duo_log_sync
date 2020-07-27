"""
Definition of the Writer class
"""

import asyncio
import ssl
import logging
import functools
from socket import gaierror
from duologsync.program import Program

class DatagramProtocol(asyncio.DatagramProtocol):
    """
    DLS implementation of Asyncio's abstact DatagramProtocol class. This is
    required for creating a network connection over UDP.
    """

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.transport = None
        super().__init__()

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        shutdown_reason = None

        if exc:
            shutdown_reason = (
                f"DuoLogSync: UDP connection with host-{self.host} and port-"
                f"{self.port} was closed for the following reason [{exc}]"
            )

        else:
            shutdown_reason = (
                f"DuoLogSync: UDP connection with host-{self.host} and port-"
                f"{self.port} was closed"
            )

        Program.initiate_shutdown(shutdown_reason)

class Writer:
    """
    Class for creating Writer objects which are a wrapper for Asyncio streams
    and open_connections objects for sending data over UDP, TCP and TCPSSL.
    """

    def __init__(self, transport_settings):
        # Needed to determine what type of writer to create and how to use it
        self.protocol = transport_settings['protocol']

        # Create the actual writer
        self.writer = asyncio.get_event_loop().run_until_complete(
            self.create_connection(
                transport_settings['host'],
                transport_settings['port'],
                transport_settings.get('certFilepath')
            )
        )

    async def write(self, data):
        """
        Wrapper for writer functions. Makes it easy for parts of a program that
        uses a writer to forget what type of connection is being used (UDP vs
        TCP.)

        @param data The information to be written over a network connection
        """
        if self.protocol == 'UDP':
            self.writer.sendto(data)
        else:
            self.writer.write(data)
            await self.writer.drain()

    async def create_connection(self, host, port, cert_filepath):
        """
        Wrapper for functions to create TCP or UDP connections.

        @param host             Hostname of the network connection to establish
        @param port             Port of the network connection to establish
        @param cert_filepath    Path to file containing SSL certificate

        @return a 'writer' object for writing data over the connection made
        """

        writer_func = None

        # Which component of the returned writer tuple is actually the writer
        writer_index = 1

        # UDP connection is very different from creating a TCP connection
        # because UDP is unsorted and not buffered
        if self.protocol == 'UDP':
            writer_index = 0
            writer_func = functools.partial(
                asyncio.get_event_loop().create_datagram_endpoint,
                lambda: DatagramProtocol(host, port), remote_addr=(host, port))

        # TCP connection (either over SSL or not)
        else:
            ssl_context = None

            if self.protocol == 'TCPSSL':
                ssl_context = Writer.get_ssl_context(cert_filepath)

            writer_func = functools.partial(
                asyncio.open_connection, host, port, ssl=ssl_context)

        writer_tuple = await Writer.create_writer(writer_func, host, port)
        return writer_tuple[writer_index]

    @staticmethod
    async def get_ssl_context(cert_filepath):
        """
        Wrapper for creating an ssl context.

        @param cert_filepath    Location of the certificate to use for SSL

        @return an ssl context
        """

        try:
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,
                                                     cafile=cert_filepath)

        except FileNotFoundError:
            Program.initiate_shutdown(
                f"The certificate file {cert_filepath} could not be opened.")
            Program.log('DuoLogSync: Make sure the filepath for SSL cert '
                        'file is correct.', logging.ERROR)
            return None

        else:
            return ssl_context

    @staticmethod
    async def create_writer(writer_function, host, port):
        """
        Wrapper around the asyncio.open_connection function with exception
        handling for creating a network connection to host and port.

        @param writer_function  Function used for creating a network connection
        @param host             Hostname of the network connection to establish
        @param port             Port of the network connection to establish

        @return an asyncio open_connection tuple containing an object used to
                write data over an established network connection
        """

        shutdown_reason = None
        Program.log(f"DuoLogSync: Opening connection to {host}:{port}",
                    logging.INFO)

        try:
            writer_tuple = await asyncio.wait_for(
                writer_function(),
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
            return writer_tuple

        Program.initiate_shutdown(shutdown_reason)
        Program.log(f"DuoLogSync: check that host-{host} and port-{port} are "
                    "correct in the config file")
        return None
