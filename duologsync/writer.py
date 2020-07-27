"""
This module contains functions related to creating open_connection objects /
Asyncio streams.
"""

import asyncio
import ssl
import logging
from socket import gaierror
from duologsync.program import Program

class DatagramProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport

class Writer:

    def __init__(self, transport_settings):
        # Needed to determine what type of writer to create and how to use it
        self.protocol = transport_settings['protocol']
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

        writer = None

        # UDP connection is very different from creating a TCP connection
        # because UDP is unsorted and not buffered
        if self.protocol == 'UDP':
            writer = await Writer.create_datagram_writer(host, port)

        # Create an SSL context if the protocol is TCP over SSL
        elif self.protocol == 'TCPSSL':
            writer = await Writer.create_tcpssl_writer(host, port, cert_filepath)

        # Default to creating a regular TCP connection and writer
        else:
            writer = await Writer.create_writer(host, port)

        return writer

    @staticmethod
    async def create_datagram_writer(host, port):
        """
        Wrapper function for creating a connection via UDP.

        @param host Hostname of the network connection to establish
        @param port Port of the network connection to establish

        @return an Asyncio Datagram transport object
        """

        # TODO: error handling for this section!
        writer, _ = await asyncio.get_event_loop().create_datagram_endpoint(
            DatagramProtocol,
            remote_addr=(host, port))

        return writer

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
            Program.initiate_shutdown(
                f"The certificate file {cert_filename} could not be opened.")
            Program.log('DuoLogSync: Make sure the filepath for SSL cert '
                        'file is correct.', logging.ERROR)
            return None

        writer = await Writer.create_writer(host, port, ssl_context)
        return writer

    @staticmethod
    async def create_writer(host, port, ssl_context=None):
        """
        Wrapper around the asyncio.open_connection function with exception
        handling for creating a network connection to host and port.

        @param host Hostname of the network connection to establish
        @param port Port of the network connection to establish
        @param ssl  Used to create an encrypted connect. Not required

        @return an asyncio open_connection object used to write over an
                established network connection to the host and port specified
        """

        shutdown_reason = None
        Program.log(f"DuoLogSync: Opening connection to {host}:{port}",
                    logging.INFO)

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
                    "correct in the config file")
        return None
