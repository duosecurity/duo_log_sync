import argparse
import duologsync.duo_log_sync_base


def main():
    arg_parser = argparse.ArgumentParser(prog='duologsync',
                                         description="Path to config file")
    arg_parser.add_argument('ConfigPath', metavar='config-path', type=str,
                            help='Config to start application')
    args = arg_parser.parse_args()
    logger = duologsync.duo_log_sync_base.LogSyncBase(args)
    logger.start()
