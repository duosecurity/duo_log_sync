import argparse

# Constant values for changeset types
RENAME = 'RENAME'
EDIT_VALUE = 'EDIT_VALUE'
ADD = 'ADD'
MOVE = 'MOVE'

# Latest version of config. Maybe keep this value in a central location like
# __version__.py? 
CURRENT_CONFIG_VERSION = '1.0.0'

# Patent pending, ingenius way to update config. Keep a list of changes between
# config version, map the config version for the old config to the changes
# needed to be made to upgrade an old config of that version to the newest
# version. There are 4 types of changes that can be made:
#   1. RENAME - simply rename a field of the config
#   2. EDIT_VALUE - make a change to value of an old config, such as that
#      the value is no represented in seconds instead of minutes
#   3. ADD - add a new field to the config
#   4. MOVE - field needs to be move to a different location (that includes 
#      nowhere / None for fields that are no longer in the config)
CONFIG_CHANGESET = {
    '0.0.0': {
        RENAME: [
            ('duoclient', 'host'): 'hostname',
            ('duoclient', 'account')
            ('logs', 'logDir'): 'log_filepath',
            ('logs', 'endpoints', 'enabled'): 'endpoints'
            ('logs', 'polling', 'duration'): 'timeout',
            ('logs', 'polling', 'daysinpast'): 'offset',
            ('logs', 'polling'): 'api'
            ('logs', 'checkpointDir'): 'checkpoint_dir',
            ('logs'): 'dls_settings'
            ('transport', 'host'): 'hostname',
            ('transport', 'certFileDir'): 'cert_filepath'
            
        ],
        EDIT_VALUE: [
            ('dls_settings', 'api', 'timeout'): multiply by 60,
            ('servers', 0, 'cert_filepath'): add correct slash (\ or /) and 
                                             certFileName
        ],
        ADD: [
            ('version'): '1.0.0',
            ('dls_settings', 'log_format'): 'JSON',
            ('dls_settings', 'checkpointing'): {},
            ('servers'): [('transport')],
            ('servers', 0, 'id'): 'Server 1',
            ('account', 'endpoint_server_mappings'): [{}],
            ('accounts', 'endpoint_server_mappings', 'server'): 'Server 1'
        ],
        MOVE: [
            ('dls_settings', 'checkpoint_dir'): ('dls_settings',
                                                 'checkpointing'),
            ('recoverFromCheckpoint', 'enabled'): ('dls_settings',
                                                   'checkpointing'),
            ('dls_settings', 'endpoints', 'endpoints'): (
                'accounts', 0, 'endpoint_server_mapping'),
            ('transport'): None,
            ('recoverFromCheckpoint'): None,
            ('dls_settings', 'endpoints')
        ]
    }
}


def main():
    """
    Parse command line arguments (such as to retrieve the old and new config
    filepaths) and call functions to upgrade the old config and write the
    upgraded config to a new file.
    """

    arg_parser = argparse.ArgumentParser(
        prog='Config Upgrader',
        description='Automatically generate a new config from an old version')

    arg_parser.add_argument(
        'old_config_path',
        metavar='old_config_path',
        type=str,
        help='Path to the old config for upgrading')

    arg_parser.add_argument(
        'new_config_path',
        metavar='new_config_path',
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

    with open(old_config_path) as config_file:
        # TODO: render the yaml and such

        # Check if the config has a version, if it doesn't then it is the
        # oldest config, and give it a version of '0.0.0'
        if not config.get('version', False):
            config['version'] = '0.0.0'

        # Apply changesets to the config until it is of the newest version
        while config.get('version') != CURRENT_CONFIG_VERSION:
            config = apply_changeset(config)

    return config

def write_config(config, config_path):
    """
    Write config to the filepath given. If there is no filepath given then
    config will be printed to stdout.

    @param config       The config to write
    @param config_path  Location where config should be written to
    """

    pass

def apply_changeset(config):
    """
    Given a config and its version number, apply the appropriate set of changes
    as defined in the version to changeset mapping in CONFIG_CHANGESET.

    @param config   The config for which changeset should be applied

    @return a version of the config with the changeset applied
    """

    version = config.get('version')
    changeset = CONFIG_CHANGESET.get(version)
    config = apply_rename_changeset(config, changeset.get(RENAME))
    config = apply_edit_value_changeset(config, changeset.get(EDIT_VALUE))
    config = apply_add_changeset(config, changeset.get(ADD))
    config = apply_move_changeset(config, changeset.get(MOVE))
    return config

def apply_rename_changeset(config):
    """
    Given a config, apply the rename changeset listed under the config's
    version.
    """

def apply_add_changeset():

def apply_edit_value_changeset():

def apply_move_changeset():

if __name__ == '__main__':
    main()
