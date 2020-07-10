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

    skey, ikey, host = None, None, None
    endpoints = None
    polling_duration = None
    days = None

    SECONDS_PER_MINUTE = 60

    DEFAULT_LOG_DIR = '/tmp'
    DEFAULT_DAYS_IN_PAST = 180
    DEFAULT_CHECKPOINT_DIR = '/tmp'
    MINIMUM_POLLING_DURATION = 2

    ENABLED_ENDPOINTS = ['adminaction', 'auth', 'telephony']
    TRANSPORT_PROTOCOLS = ['TCP', 'TCPSSL', 'UDP']
    DUOCLIENT_REQUIRED_FIELDS = ['skey', 'ikey', 'host']

    # Schema for validating the structure of a config dictionary generated from
    # a user-provided YAML file
    SCHEMA = {
        'duoclient': {
            'type': 'dict',
            'schema': {
                'skey': {'type': 'string', 'required': True},
                'ikey': {'type': 'string', 'required': True},
                'host': {'type': 'string', 'required': True}
            },
            'required': True
        },
        'logs': {
            'type': 'dict',
            'schema': {
                'logDir': {'type': 'string'},
                'endpoints': {
                    'type': 'dict',
                    'schema': {
                        # Add way to check that enabled is in ENABLED_ENDPOINTS
                        'enabled': {'type': ['string', 'list'], 'required': True}
                    },
                    'required': True
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
                'checkpointDir': {'type': 'string'}
            },
            'required': True
        },
        'transport': {
            'type': 'dict',
            'schema': {
                'protocol': {'type': 'string', 'required': True},
                'host': {'type': 'string', 'required': True},
                'port': {
                    'type': 'integer',
                    'min': 0,
                    'max': 65535,
                    'required': True
                },
                'certFileDir': {},
                'certFileName': {}
            }
        },
        'recoverFromCheckpoint': {
            'type': 'dict',
            'schema': {
                'enabled': {'type': 'boolean'}
            }
        }
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
        print(schema.errors)
