"""
Definition of the Writer class
"""

import asyncio
import ssl
import logging
import socket
from socket import gaierror
import sys

from duologsync.config import Config
from duologsync.program import Program
from duologsync import util


class DatagramProtocol(asyncio.DatagramProtocol):
    """
    DLS implementation of Asyncio's abstract DatagramProtocol class. This is
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
                f"UDP connection with host-{self.host} and port-{self.port}"
                f"was closed for the following reason [{exc}]"
            )

        else:
            shutdown_reason = (
                f"UDP connection with host-{self.host} and port-{self.port} "
                "was closed"
            )

        Program.initiate_shutdown(shutdown_reason)


class Writer:
    """
    Class for creating Writer objects which are a wrapper for Asyncio streams
    and open_connections objects for sending data over UDP, TCP and TCPSSL.
    """

    def __init__(self, server):
        # Needed to determine what type of writer to create and how to use it
        self.protocol = server['protocol']
        self.hostname = server['hostname']
        self.port = server['port']

        # Create the actual writer
        if sys.version_info >= (3, 12):
            self.writer = asyncio.run(
                    self.create_writer(
                    self.hostname,
                    self.port,
                    server.get('cert_filepath')
                )
            )

        else:
            self.writer = asyncio.get_event_loop().run_until_complete(
                    self.create_writer(
                    self.hostname,
                    self.port,
                    server.get('cert_filepath')
                )
            )


    @staticmethod
    def create_writers(servers):
        """
        For each server, create a writer object and add a dictionary entry mapping
        the server name to the writer object. Return the resulting dictionary.

        @param servers  List of servers for which to create writer objects

        @return a dictionary mapping server name to writer object
        """

        writers = {}

        for server in servers:
            server_id = server['id']
            writer = Writer(server)
            writers[server_id] = writer

        return writers

    async def write(self, data, log_type):
        """
        Wrapper for writer functions. Makes it easy for parts of a program that
        uses a writer to forget what type of connection is being used (UDP vs
        TCP.)

        @param data The information to be written over a network connection
        """
        if self.protocol == 'UDP':
            try:
                self.writer.sendto(data, (self.hostname, self.port))
            except OSError as error:
                # If the message is too long, the UDP socket will throw an error
                # and we need to handle it
                # Store the failed UDP ingestion logs in a file and log the error
                # message to the console
                error_code, error_message = getattr(error, "args")
                Program.log(f"{log_type} producer: error while sending data to {self.hostname}:{self.port} error_message: {error_message} error_code: {error_code}", logging.WARNING)
                util.store_failed_udp_ingestion_logs(
                    log_type,
                    Config.get_checkpoint_dir(),
                    data,
                )
        else:
            self.writer.write(data)
            await self.writer.drain()

    async def create_writer(self, host, port, cert_filepath):
        """
        Wrapper for functions to create TCP or UDP connections.

        @param host             Hostname of the network connection to establish
        @param port             Port of the network connection to establish
        @param cert_filepath    Path to file containing SSL certificate

        @return a 'writer' object for writing data over the connection made
        """

        Program.log(f"DuoLogSync: Opening connection to {host}:{port} with protocol {self.protocol}",
                    logging.INFO)

        # Message to be logged if an error occurs in this function
        help_message = f"DuoLogSync: check that host-{host} and port-{port} are correct in the configuration file '{Config.get_config_file_path()}'"
        writer = None

        try:
            if self.protocol == 'UDP':
                writer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            elif self.protocol == 'TCPSSL':
                ssl_context = ssl.create_default_context(
                    ssl.Purpose.SERVER_AUTH, cafile=cert_filepath)

                writer = await Writer.create_tcp_writer(host, port, ssl_context)

            elif self.protocol == 'TCP':
                writer = await Writer.create_tcp_writer(host, port)

        # Failed to open the certificate file
        except FileNotFoundError as fnf_error:
            error_code, error_message = getattr(fnf_error, "args")
            shutdown_reason = f"certificate file '{cert_filepath}' could not be opened due to error: {error_message} error_code: {error_code}"
            help_message = f"make sure that certificate file '{cert_filepath}' to establish SSL connection is correct."

        # Couldn't establish a connection within 60 seconds
        except asyncio.TimeoutError:
            shutdown_reason = 'connection to the destination server timed-out after 60 seconds'

        # If an invalid hostname or port number is given or simply failed to
        # connect using the host and port given
        except (gaierror, OSError) as error:
            error_code, error_message = getattr(error, "args")
            shutdown_reason = f"error while connecting to {host}:{port} error_message: {error_message} error_code: {error_code}"

        # An error did not occur and the writer was successfully created
        else:
            return writer

        Program.initiate_shutdown(shutdown_reason)
        Program.log(help_message, logging.ERROR)
        return None

    @staticmethod
    async def create_tcp_writer(host, port, ssl_context=None):
        """
        Wrapper around the asyncio.open_connection function with exception
        handling for creating a network connection to host and port.

        @param host           Hostname of the network connection to establish
        @param port           Port of the network connection to establish
        @param ssl_context    Used for creating TCP over SSL connections

        @return an asyncio object used to write data over a network connection
                using TCP
        """

        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port, ssl=ssl_context),
            timeout=60
        )

        return writer
