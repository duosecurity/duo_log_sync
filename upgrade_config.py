import argparse

def main():
    arg_parse = argparse.ArgumentParser(
        prog='Config Upgrader',
        description='Automatically generate a new config from an old version')

    arg_parser.add_argument(
        'old_config_path',
        metavar='old_path',
        type=str,
        help='Path to the old config for upgrading')

    arg_parser.add_argument(
        'new_config_path',
        metavar='new_path',
        type=str,
        help='Filepath where the upgraded config file should be saved')

    args = arg_parser.parse_args()

    upgraded_config = upgrade_config(args.old_config_path)
    write_config(upgraded_config, args.new_config_path)

def upgrade_config(old_config_path):
    """
    Create a new config base off of a config located at the given filepath.

    @param old_config_path  Location of the old config to upgrade

    @return an upgraded version of the old config
    """

    with open(old_config_path) as old_config_file:
        pass

def write_config(config, config_path):
    """
    Write config to the filepath given. If there is no filepath given then
    config will be printed to stdout.

    @param config       The config to write
    @param config_path  Location where config should be written to
    """

    pass
