import argparse
import yaml

# Constant values for changeset types
ADD = 'ADD'
MOVE = 'MOVE'
EDIT = 'EDIT'
DELETE = 'DELETE'

# Latest version of config. Maybe keep this value in a central location like
# __version__.py? 
CURRENT_CONFIG_VERSION = '1.0.0'

# Patent pending, ingenius way to update config. Keep a list of changes between
# config version, map the config version for the old config to the changes
# needed to be made to upgrade an old config of that version to the newest
# version. There are 4 types of changes that can be made:
#   1. ADD - add a new field to the config
#   2. MOVE - move a value to a different field, getting rid of the old field
#   3. EDIT - make a change to value of an old config
#   4. DELETE - delete a field
CONFIG_CHANGESET = {
    '0.0.0': {
        ADD: {
            ('logs', 'log_format'): 'JSON',
            ('servers',): [{}],
            ('transport', 'id'): 'Server 1',
            ('duoclient', 'endpoint_server_mappings'): [{}],
            ('duoclient', 'endpoint_server_mappings', 0, 'server'): 'Server 1'
        },
        MOVE: {
            ('duoclient',): ('account',),
            ('account', 'host'): ('account', 'hostname'),
            ('logs', 'logDir'): ('logs', 'log_filepath'),
            ('logs', 'endpoints', 'enabled'): (
                'logs', 'endpoints', 'endpoints'),
            ('logs', 'polling'): ('logs', 'api'),
            ('logs', 'api', 'duration'): ('logs', 'api', 'timeout'),
            ('logs', 'api', 'daysinpast'): ('logs', 'api', 'offset'),
            ('logs', 'checkpointDir'): ('logs', 'directory'),
            ('logs',): ('dls_settings',),
            ('transport', 'host'): ('transport', 'hostname'),
            ('transport', 'certFileDir'): ('transport', 'cert_filepath'),
            ('recoverFromCheckpoint',): ('checkpointing',),
            ('checkpointing',): ('dls_settings', 'checkpointing'),
            ('dls_settings', 'directory'): (
                'dls_settings', 'checkpointing', 'directory'),
            ('dls_settings', 'endpoints', 'endpoints'): (
                'account', 'endpoint_server_mappings', 0, 'endpoints'),
            ('transport',): ('servers', 0)
        },
        EDIT: {
            ('version',): (lambda _ : '1.0.0'),
            ('dls_settings', 'api', 'timeout'): (lambda timeout : timeout * 60),
        },
        DELETE: [
            ('dls_settings', 'endpoints'),
            ('servers', 0, 'certFileName')
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
    Create a new config based off of a config located at the given filepath.

    @param old_config_path  Location of the old config to upgrade

    @return an upgraded version of the old config
    """

    with open(old_config_path) as config_file:
        config_file_data = config_file.read()
        config = yaml.full_load(config_file_data)

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
   
    with open(config_path, 'w') as config_file:
        yaml.dump(config, config_file)

def apply_changeset(config):
    """
    Given a config and its version number, apply the appropriate set of changes
    as defined in the version to changeset mapping in CONFIG_CHANGESET.

    @param config   The config for which changeset should be applied

    @return a version of the config with the changeset applied
    """

    version = config.get('version')
    config = apply_hard_coded_changes(config, version)

    changeset = CONFIG_CHANGESET.get(version)
    config = apply_add_changeset(config, changeset.get(ADD))
    config = apply_move_changeset(config, changeset.get(MOVE))
    config = apply_edit_changeset(config, changeset.get(EDIT))
    config = apply_delete_changeset(config,changeset.get(DELETE))
    return config

def apply_hard_coded_changes(config, version):
    """
    Unfortunately, some changes made between config version are too complex
    to implement using the versioning dict to make it worth while. Best to
    hard code changes like this for each version and update the config as
    needed.

    @param config   Dictionary that changes should be applied to
    @param version  What changes should be applied to the config
    @return config with updates according to the version specified
    """

    if version == '0.0.0':
        slash = '/'

        # Catch the case where Windows paths exist
        if '\\' in config['transport']['certFileDir']:
            slash = '\\'

        cert_filepath = config['transport']['certFileDir'] + slash + config[
            'transport']['certFileName']
        config['transport']['certFileDir'] = cert_filepath
        config['logs']['logDir'] += slash + 'duologsync.log'

    return config


def apply_add_changeset(config, add_changeset):
    """
    Add new fields to the config as specified by the add changeset.

    @param config           Config to add fields to
    @param add_changeset    Dictionary specifying what fields to add and with
                            what values
    @return config with the add changeset applied
    """

    for keys, value in add_changeset.items():
        elem_to_add = get_elem(config, keys[:-1])
        elem_to_add[keys[-1]] = value

    return config

def apply_move_changeset(config, move_changeset):
    """
    Move fields to different locations within config as specified by the
    move_changeset.

    @param config           Config to move fields for
    @param move_changeset   Dictionary specifying where to move certain fields
                            to
    @return config with the move changeset applied
    """

    for keys, new_path in move_changeset.items():
        elem_to_move = get_elem(config, keys[:-1])
        temp = elem_to_move.pop(keys[-1])

        if new_path is not None:
            new_elem = get_elem(config, new_path[:-1])
            new_elem[new_path[-1]] = temp 

    return config

def apply_edit_changeset(config, edit_changeset):
    """
    Edit certain values within config as specified by the edit_changeset.

    @param config           Config to edit values for
    @param edit_changeset   Dictionary of fields and lambdas to change the
                            values of those fields
    @return config with the edit changeset applied
    """

    for keys, func in edit_changeset.items():
        elem_to_edit = get_elem(config, keys[:-1])
        elem_to_edit[keys[-1]] = func(elem_to_edit[keys[-1]])

    return config

def apply_delete_changeset(config, delete_changeset):
    """
    Delete certain elements  within config as specified by the delete_changeset.

    @param config           Config to delete elements for
    @param delete_changeset List of elements to delete
    @return config with the delete changeset applied
    """

    for keys in delete_changeset:
        elem_to_delete = get_elem(config, keys[:-1])
        del elem_to_delete[keys[-1]]

    return config


def get_elem(dictionary, keys):
    """
    Given a dictionary and a tuple of keys, retrieve the element found by
    following the tuple of keys.

    @param dictionary   Dictionary to retrieve an element from
    @param keys         Tuple of keys to follow to find a element
    @return the elemetn found in the dictionary by following the tuple of keys
    """

    curr_elem = dictionary

    for key in keys:
        curr_elem = curr_elem[key]

    return curr_elem

if __name__ == '__main__':
    main()
