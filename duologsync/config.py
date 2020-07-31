"""
Definition of the Config class
"""

import logging
from datetime import datetime, timedelta
from cerberus import Validator
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

    DEFAULT_DIRECTORY = '/tmp'
    DEFAULT_LOG_PATH = DEFAULT_DIRECTORY + '/duologsync.log'
    DEFAULT_DAYS_IN_PAST = 180
    DEFAULT_LOG_FORMAT = JSON

    # How many seconds to wait between API requests
    MINIMUM_POLLING_DURATION = 120

    PATHS_TO_DEFAULTS = {
        ('logs', 'polling', 'duration'): MINIMUM_POLLING_DURATION,
        ('logs', 'logFilepath'): DEFAULT_LOG_PATH,
        ('logs', 'polling', 'daysinpast'): DEFAULT_DAYS_IN_PAST,
        ('logs', 'checkpointDir'): DEFAULT_DIRECTORY,
        ('logs', 'log_format'): DEFAULT_LOG_FORMAT,
        ('recoverFromCheckpoint', 'enabled'): False
    }

    # Duo credentials used to access a client's logs
    DUOCLIENT = {
        'type': 'dict',
        'required': True,
        'schema': {
            'skey': {'type': 'string', 'required': True, 'empty': False},
            'ikey': {'type': 'string', 'required': True, 'empty': False},
            'host': {'type': 'string', 'required': True, 'empty': False}
        }
    }

    # What types of logs to fetch, how often to fetch, from what point in
    # time logs should begin to be fetched
    LOGS = {
        'type': 'dict',
        'required': True,
        'schema': {
            'logFilepath': {'type': 'string', 'empty': False},
            'endpoints': {
                'type': 'dict',
                'required': True,
                'schema': {
                    'enabled': {
                        'type': ['string', 'list'],
                        'required': True,
                        'empty': False,
                        'allowed': [ADMIN, AUTH, TELEPHONY],
                    }
                }
            },
            'polling': {
                'type': 'dict',
                'schema': {
                    'duration': {
                        'type': 'number'
                    },
                    'daysinpast': {'type': 'integer', 'min': 0}
                }
            },
            'checkpointDir': {'type': 'string', 'empty': False},
            'log_format': {
                'type': 'string',
                'empty': False,
                'allowed': [CEF, JSON]
            }
        }
    }

    # How and where fetched logs should be sent
    TRANSPORT = {
        'type': 'dict',
        'required': True,
        'schema': {
            'protocol': {
                'type': 'string',
                'required': True,
                'oneof': [
                    {
                        'allowed': ['TCPSSL'],
                        'dependencies': ['certFilepath']
                    },
                    {'allowed': ['TCP', 'UDP']}
                ]
            },
            'host': {'type': 'string', 'required': True, 'empty': False},
            'port': {
                'type': 'integer',
                'min': 0,
                'max': 65535,
                'required': True
            },
            'certFilepath': {'type': 'string', 'empty': False}
        }
    }

    # Whether or not log-specific checkpoint files should be used in the
    # case of an error or crash
    RECOVER_FROM_CHECKPOINT = {
        'type': 'dict',
        'schema': {
            'enabled': {'type': 'boolean'}
        }
    }

    # Schema for validating the structure of a config dictionary generated from
    # a user-provided YAML file
    SCHEMA = {
        'duoclient': DUOCLIENT,
        'logs': LOGS,
        'transport': TRANSPORT,
        'recoverFromCheckpoint': RECOVER_FROM_CHECKPOINT
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
    def get_enabled_endpoints(cls):
        """
        @return the list of log_types for which logs should be fetched
        """

        return cls.get_value(['logs', 'endpoints', 'enabled'])

    @classmethod
    def get_polling_duration(cls):
        """
        @return the seconds to wait before fetching logs from an endpoint
        """

        return cls.get_value(['logs', 'polling', 'duration'])

    @classmethod
    def get_checkpoint_directory(cls):
        """
        @return the directory where log offset checkpoint files are saved
        """

        return cls.get_value(['logs', 'checkpointDir'])

    @classmethod
    def get_ikey(cls):
        """
        @return the ikey used by Duo to identify a customer
        """

        return cls.get_value(['duoclient', 'ikey'])

    @classmethod
    def get_skey(cls):
        """
        @return the skey used by Duo to authenticate access to a customer's logs
        """

        return cls.get_value(['duoclient', 'skey'])

    @classmethod
    def get_host(cls):
        """
        @return the host where a customer's logs are stored
        """

        return cls.get_value(['duoclient', 'host'])

    @classmethod
    def get_recover_log_offset(cls):
        """
        @return boolean indicating if checkpoint files should be used to
                recover log offsets
        """

        return cls.get_value(['recoverFromCheckpoint', 'enabled'])

    @classmethod
    def get_log_filepath(cls):
        """
        @return the directory where DuoLogSync's logs should be saved
        """

        return cls.get_value(['logs', 'logFilepath'])

    @classmethod
    def get_log_format(cls):
        """
        @return the format that logs should take on before being written
        """

        return cls.get_value(['logs', 'log_format'])

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
                cls._validate_config(config)

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
            # For fields that are optional and not given a value, populate with
            # default values
            cls._set_config_defaults(config)
            return config

        # At this point, it is guaranteed that an exception was raised, which
        # means that it is shutdown time
        Program.initiate_shutdown(shutdown_reason)
        return None

    @classmethod
    def _validate_config(cls, config):
        """
        Use a schema and the cerberus library to validate that the given config
        dictionary has a valid structure

        @param config   Dictionary for which to validate the structure
        """

        # Config is not a valid structure
        if not cls.SCHEMA_VALIDATOR.validate(config):
            raise ValueError

    @classmethod
    def _set_config_defaults(cls, config):
        """
        Check if optional fields within a config are empty. If they are empty
        or if they have a bad value, set those values to a default and log a
        message about the decision to set a default.

        @param config   Config dict for which to set defaults
        """

        # Message format for informing a user that an optional field in their
        # config file was not set and thus a default value is being used
        template = "Config: No value given for %s, using default value of %s"

        if config.get('logs').get('polling') is None:
            config['logs']['polling'] = {}

        if config.get('recoverFromCheckpoint') is None:
            config['recoverFromCheckpoint'] = {}

        for keys, default in cls.PATHS_TO_DEFAULTS.items():
            value = Config.get_value_from_keys(config, keys)

            if value is None:
                # Let the user know that a default value is being set
                Program.log(template % ('.'.join(keys), default), logging.INFO)
                config = Config.set_value_from_keys(config, keys, default)

        polling_duration = config.get('logs').get('polling').get('duration')
        if polling_duration < cls.MINIMUM_POLLING_DURATION:
            Program.log("Config: Value given for logs.polling.duration was too "
                        "low. Set to %s" % cls.MINIMUM_POLLING_DURATION,
                        logging.INFO)
            config['logs']['polling']['duration'] = cls.MINIMUM_POLLING_DURATION

        # Add a default offset from which to fetch logs
        # The maximum amount of days in the past that a log may be fetched from
        days_in_past = config['logs']['polling']['daysinpast']

        # Create a timestamp for screening logs that are too old
        default_log_offset = datetime.utcnow() - timedelta(days=days_in_past)
        config['logs']['offset'] = int(default_log_offset.timestamp())

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

    @staticmethod
    def set_value_from_keys(dictionary, keys, value):
        """
        Drill down into dictionary to set a value given a list of keys

        @param dictionary   dict for which to set a value
        @param fields       List of fields to follow in order to set a value

        @return dictionary with the value set
        """

        entry = dictionary

        for key in keys[:-1]:
            entry = entry.get(key)

        entry[keys[-1]] = value
        return dictionary
