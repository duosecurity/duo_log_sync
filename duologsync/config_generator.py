"""
Definition of the ConfigGenerator class
"""

from cerberus import Validator
import yaml
from yaml import YAMLError

class ConfigGenerator:
    """
    This class is used to create an Dictionary-like object based on a YAML file
    for which the filepath is given. The information in a Config object is used
    to determine what logs to fetch, how to fetch logs and where to send logs.
    Additionally, Config handles checking the YAML against a schema to ensure
    that all required fields are provided with a value and that for any field,
    the values given are valid.
    """

    SECONDS_PER_MINUTE = 60
    DEFAULT_DIRECTORY = '/tmp'
    DEFAULT_DAYS_IN_PAST = 180
    MINIMUM_POLLING_DURATION = 2
    VALID_ENDPOINTS = ['adminaction', 'auth', 'telephony']

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
            'logDir': {'type': 'string', 'empty': False},
            'endpoints': {
                'type': 'dict',
                'required': True,
                'schema': {
                    # Add way to check that enabled is in ENABLED_ENDPOINTS
                    'enabled': {
                        'type': ['string', 'list'],
                        'required': True,
                        'empty': False,
                        'allowed': VALID_ENDPOINTS,
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
            'checkpointDir': {'type': 'string', 'empty': False}
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
                        'dependencies': ['certFileDir', 'certFileName']
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
            'certFileDir': {'type': 'string', 'empty': False},
            'certFileName': {'type': 'string', 'empty': False}
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

    @staticmethod
    def get_config(config_filepath):
        """
        Attemp to read the file at config_filepath and generate a config
        Dictionary object based on a defined JSON schema

        @param config_filepath  File from which to generate a config object
        """

        try:
            with open(config_filepath) as config_file:
                # PyYAML gives better error messages for streams than for files
                config_file_data = config_file.read()
                config = yaml.full_load(config_file_data)

        # Will occur when given a bad filepath or a bad file
        except OSError:
            print('An error occurred while opening the config file. Check '
                  'that the filename and filepath are correct')
            # Re-raise exception to be re-handled and for stopping the program
            raise

        # Will occur if the config file does not contain valid YAML
        except YAMLError:
            print('An error occurred while reading the config file. Check '
                  'that the file has valid YAML.')
            # Re-raise exception to be re-handled and for stopping the program
            raise

        # If no exception was raised during the try block, return config
        else:
            return config

    @staticmethod
    def validate_config(config):
        # Check that duoclient field exists and that it contains values for
        # skey, ikey, host

        # Check that transport field exists and that it contains values for
        # protocol, host, port, and that protocol is valid (along with host
        # and port
        schema = Validator(ConfigGenerator.SCHEMA)
        result = schema.validate(config)
        print("Result of validating config is: %s" % result)
        # If there are errors, need to create a helpful message and raise the
        # error to stop the program
        print(schema.errors)
