import argparse
import asyncio
import duologsync.duo_log_sync_base

from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from duologsync.config_generator import ConfigGenerator
from duologsync.util import create_admin

def main():
    """
    Kicks off DuoLogSync by setting important variables, creating and running
    a Producer-Consumer pair for each log-type defined in a config file passed
    to the program.
    """

    arg_parser = argparse.ArgumentParser(prog='duologsync',
                                         description="Path to config file")
    arg_parser.add_argument('ConfigPath', metavar='config-path', type=str,
                            help='Config to start application')
    args = arg_parser.parse_args()

    # namedtuple containing important variables used through DuoLogSync
    g_vars = create_global_tuple(args.ConfigPath)

    logger = duologsync.duo_log_sync_base.LogSyncBase()
    logger.start(g_vars)

def create_global_tuple(config_path):
    """
    Initialize important variables used throughout DuoLogSync and return a
    namedtuple which contains them and allows accessing the variables by name.

    @param config_path  Location of a config file which is used to create a
                        config dictionary object.

    @return a namedtuple with important variables used throughout DuoLogSync
    """

    # Create a tuple containing global variables that may be indexed by name
    g_vars = namedtuple(
        'g_vars',
        ['admin', 'config', 'event_loop', 'executor', 'last_offset_read'])

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

    # Dictionary for storing the latest timestamp received for each log type
    g_vars.last_offset_read = {}

    return g_vars
