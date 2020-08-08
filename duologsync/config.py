"""
Definition of the Config class
"""

from datetime import datetime, timedelta
from cerberus import Validator, schema_registry
import yaml
from yaml import YAMLError
from duologsync.program import Program

class Config:
    """
    This class is unique in that no instances of it should be created. It is
    used as a wrapper around a Dictionary object named config that is contains
    important values used throughout DuoLogSync. The _config class variable
    should only be accessed through getter and setter methods and should only
    be set once. There are useful methods defined in this class for generating
    a config Dictionary from a YAML file, validating the config against a
    Schema and setting defaults for a config Dictionary when optional fields
    are not given values.
    """

    # Format type constants
    CEF = 'CEF'
    JSON = 'JSON'

    # Log type constants
    ADMIN = 'adminaction'
    AUTH = 'auth'
    TELEPHONY = 'telephony'

    DIRECTORY_DEFAULT = '/tmp'
    LOG_FILEPATH_DEFAULT = DIRECTORY_DEFAULT + '/' + 'duologsync.log'
    LOG_FORMAT_DEFAULT = 'JSON'
    API_OFFSET_DEFAULT = 180
    API_TIMEOUT_DEFAULT = 120
    CHECKPOINTING_ENABLED_DEFAULT = False
    CHECKPOINTING_DIRECTORY_DEFAULT = DIRECTORY_DEFAULT

    # Version of the config file
    VERSION = {
        'type': 'string',
        'empty': False,
        'required': True
    }

    # Fields for changing the functionality of DuoLogSync
    DLS_SETTINGS = {
        'type': 'dict',
        'default': {},
        'schema': {
            'log_filepath': {
                'type': 'string',
                'empty': False,
                'default': LOG_FILEPATH_DEFAULT
            },
            'log_format': {
                'type': 'string',
                'empty': False,
                'allowed': [CEF, JSON],
                'default': LOG_FORMAT_DEFAULT
            },
            'api': {
                'type': 'dict',
                'default': {},
                'schema': {
                    'offset': {
                        'type': 'number',
                        'min': 0,
                        'max': 180,
                        'default': API_OFFSET_DEFAULT
                    },
                    'timeout': {
                        'type': 'number',
                        'min': 120,
                        'default': API_TIMEOUT_DEFAULT
                    }
                }
            },
            'checkpointing': {
                'type': 'dict',
                'default': {},
                'schema': {
                    'enabled': {
                        'type': 'boolean',
                        'default': CHECKPOINTING_ENABLED_DEFAULT
                    },
                    'directory': {
                        'type': 'string',
                        'empty': False,
                        'default': CHECKPOINTING_DIRECTORY_DEFAULT}
                }
            }
        }
    }

    # Schema for a server inside of servers list
    schema_registry.add(
        'server',
        {
            'id': {'type': 'string', 'required': True, 'empty': False},
            'hostname': {'type': 'string', 'required': True, 'empty': False},
            'port': {
                'type': 'integer',
                'required': True,
                'min': 0,
                'max': 65535
            },
            'protocol': {
                'type': 'string',
                'required': True,
                'oneof': [
                    {
                        'allowed': ['TCPSSL'],
                        'dependencies': ['cert_filepath']
                    },
                    {'allowed': ['TCP', 'UDP']}
                ]
            },
            'cert_filepath': {'type': 'string', 'empty': False}
        })

    # List of servers and how DLS will communicate with them
    SERVERS = {
        'type': 'list',
        'required': True,
        'minlength': 1,
        'schema': {'type': 'dict', 'schema': 'server'}
    }

    # Describe which servers the logs of certain endpoints should be sent to
    schema_registry.add(
        'endpoint_server_mapping',
        {
            'servers': {
                'type': 'list',
                'empty': False,
                'required': True
            },
            'endpoints': {
                'type': 'list',
                'empty': False,
                'required': True,
                'allowed': [ADMIN, AUTH, TELEPHONY]
            }
        }
    )

    # Account definition, which is used to access Duo logs and tell DLS which
    # logs to fetch and to which servers those logs should be sent
    ACCOUNT = {
        'type': 'dict',
        'required': True,
        'schema': {
            'skey': {'type': 'string', 'required': True, 'empty': False},
            'ikey': {'type': 'string', 'required': True, 'empty': False},
            'hostname': {'type': 'string', 'required': True, 'empty': False},
            'endpoint_server_mappings': {
                'type': 'list',
                'empty': False,
                'required': True,
                'schema': {'type': 'dict', 'schema': 'endpoint_server_mapping'}
            },
            'is_msp': {'type': 'boolean', 'default': False},
            'block_list': {'type': 'list', 'default': []}
        }
    }

    # Schema for validating the structure of a config dictionary generated from
    # a user-provided YAML file
    SCHEMA = {
        'version': VERSION,
        'dls_settings': DLS_SETTINGS,
        'servers': SERVERS,
        'account': ACCOUNT
    }

    # Generate a Validator object with the given schema
    SCHEMA_VALIDATOR = Validator(SCHEMA)

    # Private class variable, should not be accessed directly, only through
    # getter and setter methods
    _config = None

    # Used to ensure that the _config variable is set once and only once
    _config_is_set = False

    @classmethod
    def _check_config_is_set(cls):
        """
        Used to check that this Config object is set before trying to access
        or set values
        """
        if cls._config_is_set:
            return

        raise RuntimeError('Cannot access values of config before setting it')

    @classmethod
    def set_config(cls, config):
        """
        Function used to set the config of a Config object once and only once.

        @param config   Dictionary used to set a Config object's 'config'
                        instance variable
        """
        if cls._config_is_set:
            raise RuntimeError('Config object already set. Cannot set Config '
                               'object more than once')

        cls._config = config
        cls._config_is_set = True

    @classmethod
    def get_value(cls, keys):
        """
        Getter for a Config object's 'config' instance variable
        """

        cls._check_config_is_set()
        curr_value = cls._config
        for key in keys:
            curr_value = curr_value.get(key)

            if curr_value is None:
                raise ValueError(f"{key} is an invalid key for this Config")

        return curr_value

    @classmethod
    def get_log_filepath(cls):
        """@return the filepath where DLS program messages should be saved"""
        return cls.get_value(['dls_settings', 'log_filepath'])

    @classmethod
    def get_log_format(cls):
        """@return how Duo logs should be formatted"""
        return cls.get_value(['dls_settings', 'log_format'])

    @classmethod
    def get_api_offset(cls):
        """@return the timestamp from which record retrieval should begin"""
        return cls.get_value(['dls_settings', 'api', 'offset'])

    @classmethod
    def get_api_timeout(cls):
        """@return the seconds to wait between API calls"""
        return cls.get_value(['dls_settings', 'api', 'timeout'])

    @classmethod
    def get_checkpointing_enabled(cls):
        """@return whether checkpoint files should be used to recover offsets"""
        return cls.get_value(['dls_settings', 'checkpointing', 'enabled'])

    @classmethod
    def get_checkpoint_dir(cls):
        """@return the directory where checkpoint files should be stored"""
        return cls.get_value(
            ['dls_settings', 'checkpointing', 'directory'])

    @classmethod
    def get_servers(cls):
        """@return the list of servers to which Duo logs will be written"""
        return cls.get_value(['servers'])

    @classmethod
    def get_account_ikey(cls):
        """@return the ikey of the account in config"""
        return cls.get_value(['account', 'ikey'])

    @classmethod
    def get_account_skey(cls):
        """@return the skey of the account in config"""
        return cls.get_value(['account', 'skey'])

    @classmethod
    def get_account_hostname(cls):
        """@return the hostname of the account in config"""
        return cls.get_value(['account', 'hostname'])

    @classmethod
    def get_account_endpoint_server_mappings(cls):
        """@return the endpoint_server_mappings of the account in config"""
        return cls.get_value(['account', 'endpoint_server_mappings'])

    @classmethod
    def get_account_block_list(cls):
        """@return the block_list of the account in config"""
        return cls.get_value(['account', 'block_list'])

    @classmethod
    def account_is_msp(cls):
        """@return whether the account in config is an MSP account"""
        return cls.get_value(['account', 'is_msp'])

    @classmethod
    def create_config(cls, config_filepath):
        """
        Attemp to read the file at config_filepath and generate a config
        Dictionary object based on a defined JSON schema

        @param config_filepath  File from which to generate a config object
        """

        shutdown_reason = None

        try:
            with open(config_filepath) as config_file:
                # PyYAML gives better error messages for streams than for files
                config_file_data = config_file.read()
                config = yaml.full_load(config_file_data)

                # Check config against a schema to ensure all the needed fields
                # and values are defined
                config = cls._validate_and_normalize_config(config)

        # Will occur when given a bad filepath or a bad file
        except OSError as os_error:
            shutdown_reason = f"{os_error}"
            Program.log('DuoLogSync: Failed to open the config file. Check '
                        'that the filename is correct')

        # Will occur if the config file does not contain valid YAML
        except YAMLError as yaml_error:
            shutdown_reason = f"{yaml_error}"
            Program.log('DuoLogSync: Failed to parse the config file. Check '
                        'that the config file has valid YAML.')

        # Validation of the config against a schema failed
        except ValueError:
            shutdown_reason = f"{cls.SCHEMA_VALIDATOR.errors}"
            Program.log('DuoLogSync: Validation of the config file failed. '
                        'Check that required fields have proper values.')

        # No exception raised during the try block, return config
        else:
            # Calculate offset as a timestamp and rewrite its value in config
            offset = config.get('dls_settings').get('api').get('offset')
            offset = datetime.utcnow() - timedelta(days=offset)
            config['dls_settings']['api']['offset'] = int(offset.timestamp())
            return config

        # At this point, it is guaranteed that an exception was raised, which
        # means that it is shutdown time
        Program.initiate_shutdown(shutdown_reason)
        return None

    @classmethod
    def _validate_and_normalize_config(cls, config):
        """
        Use a schema and the cerberus library to validate that the given config
        dictionary has a valid structure

        @param config   Dictionary for which to validate the structure
        """

        # Config is not a valid structure
        if not cls.SCHEMA_VALIDATOR.validate(config):
            raise ValueError

        config = cls.SCHEMA_VALIDATOR.normalized(config)
        return config

    @staticmethod
    def get_value_from_keys(dictionary, keys):
        """
        Drill down into dictionary to retrieve a value given a list of keys

        @param dictionary   dict to retrieve a value from
        @param fields       List of fields to follow to retrieve a value

        @return value from the log found after following the list of keys given
        """

        value = dictionary

        for key in keys:
            value = value.get(key)

            if value is None:
                break

        return value
