"""
Definition of the ConfigGenerator class
"""

from cerberus import Validator
import yaml
from yaml import YAMLError

DEFAULT_DIRECTORY = '/tmp'
DEFAULT_DAYS_IN_PAST = 180
# How many seconds to wait between API requests
MINIMUM_POLLING_DURATION = 120
VALID_ENDPOINTS = ['adminaction', 'auth', 'telephony']


class ConfigGenerator:
    """
    This class is used to create an Dictionary-like object based on a YAML file
    for which the filepath is given. The information in a Config object is used
    to determine what logs to fetch, how to fetch logs and where to send logs.
    Additionally, Config handles checking the YAML against a schema to ensure
    that all required fields are provided with a value and that for any field,
    the values given are valid.
    """

    def __init__(self):
        self.config = None
        self.config_set = False

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

    def check_config_is_set(self):
        """
        Used to check that this Config object is set before trying to access 
        or set values
        """
        if self.config_set:
            return

        raise RuntimeError('Cannot access values of a Config object before the '
                           'object is set.')

    def set_config(self, config):
        """
        Function used to set the config of a Config object once and only once.

        @param config   Dictionary used to set a Config object's 'config'
                        instance variable
        """
        if self.config_set is True:
            raise RuntimeError('Config object already set. Cannot set Config '
                               'object more than once')
        self.config = config
        self.config_set = True

    def get_value(self, keys):
        """
        Getter for a Config object's 'config' instance variable
        """

        self.check_config_is_set()
        curr_value = self.config
        for key in keys:
            curr_value = curr_value.get(key)
            
            if curr_value is None:
                raise ValueError(f"{key} is an invalid key for this Config")

        return curr_value
    
    @staticmethod
    def create_config(config_filepath):
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

    @staticmethod
    def set_config_defaults(config):
        """
        Check if optional fields within a config are empty. If they are empty
        or if they have a bad value, set those values to a default and log a
        message about the decision to set a default.

        @param config   Config dict for which to set defaults
        """

        if config.get('logs').get('polling') is None:
            config['logs']['polling'] = {}

        if config.get('recoverFromCheckpoint') is None:
            config['recoverFromCheckpoint'] = {}

        if config.get('logs').get('logDir') is None:
            print("Config: No value given for logs: logDir, set to default "
                  "value of %s", DEFAULT_DIRECTORY)
            config['logs']['logDir'] = DEFAULT_DIRECTORY

        polling_duration = config.get('logs', {}).get('polling', {}).get(
            'duration')
        if polling_duration is None:
            print("Config: No value given for logs: polling: duration, set to "
                  "default value of %s", MINIMUM_POLLING_DURATION)
            config['logs']['polling']['duration'] = MINIMUM_POLLING_DURATION
        elif polling_duration < MINIMUM_POLLING_DURATION:
            print("Config: Value given for logs: polling: duration was too "
                  "low. Set to default value of %s" % MINIMUM_POLLING_DURATION)
            config['logs']['polling']['duration'] = MINIMUM_POLLING_DURATION

        if config.get('logs', {}).get('polling', {}).get('daysinpast') is None:
            print("Config: No value given for logs: polling: daysinpast, set "
                  "to default value of %s" % DEFAULT_DAYS_IN_PAST)
            config['logs']['polling']['daysinpast'] = DEFAULT_DAYS_IN_PAST

        if config.get('logs').get('checkpointDir') is None:
            print("Config: No value given for logs: checkpointDir, set to "
                  "default value of %s" % DEFAULT_DIRECTORY)
            config['logs']['checkpointDir'] = DEFAULT_DIRECTORY

        if config.get('recoverFromCheckpoint', {}).get('enabled') is None:
            print("Config: No value given for recoverFromCheckpoint: enabled, "
                  "set to default value of %s" % False)
            config['recoverFromCheckpoint']['enabled'] = False
