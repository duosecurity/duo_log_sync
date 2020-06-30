import argparse
import asyncio
import duologsync.duo_log_sync_base

from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from duologsync.config_generator import ConfigGenerator
from duologsync.util import create_admin

def main():
    arg_parser = argparse.ArgumentParser(prog='duologsync',
                                         description="Path to config file")
    arg_parser.add_argument('ConfigPath', metavar='config-path', type=str,
                            help='Config to start application')
    args = arg_parser.parse_args()

    # Create a tuple containing global variables that may be indexed by name
    g_vars = namedtuple(
        'g_vars',
        ['admin', 'config', 'loop', 'executor', 'last_offset_read'])

    # Dictionary populated with values from the config file passed to DuoLogSync
    g_vars.config = ConfigGenerator().get_config(args.ConfigPath)

    # Object that allows for interaction with Duo APIs to fetch logs / data
    g_vars.admin = create_admin(
        g_vars.config['duoclient']['ikey'],
        g_vars.config['duoclient']['skey'],
        g_vars.config['duoclient']['host']
    )

    # TODO: rename this to event_loop
    # The core to asyncio applications. Event loops run asynchronous tasks and
    # call-backs, perform network IO operations and run subprocesses
    g_vars.loop = asyncio.get_event_loop()

    # Allocate an execution environment of 3 threads for high latency tasks
    g_vars.executor = ThreadPoolExecutor(3)

    # Dictionary for storing the latest timestamp received for each log type
    g_vars.last_offset_read = {}

    logger = duologsync.duo_log_sync_base.LogSyncBase()
    logger.start(g_vars)
