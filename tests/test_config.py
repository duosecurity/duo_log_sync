from unittest import mock, TestCase
import os
import sys
from yaml import YAMLError
from duologsync.config import Config

class TestConfig(TestCase):
    @staticmethod
    def reset_config_variables():
        Config._config = None
        Config._config_is_set = False

    def test_set_config_normal(self):
        config = {'field_one': {'nested_field': True}, 'field_two': 100}

        Config.set_config(config)

        self.assertEqual(Config._config['field_one']['nested_field'], True)
        self.assertEqual(Config._config['field_two'], 100)

        self.reset_config_variables()

    def test_set_config_twice(self):
        config = {'field_one': {'nested_field': True}, 'field_two': 100}

        Config.set_config(config)
        
        with self.assertRaises(RuntimeError):
            Config.set_config(config)

        self.reset_config_variables()

    def test_get_value_normal(self):
        config = {'field_one': {'nested_field': True}, 'field_two': 100}

        Config.set_config(config)
        value_one = Config.get_value(['field_one', 'nested_field'])
        value_two = Config.get_value(['field_two'])

        self.assertEqual(value_one, True)
        self.assertEqual(value_two, 100)
        
        self.reset_config_variables()

    def test_get_value_before_setting_config(self):
        config = {'field_one': {'nested_field': True}, 'field_two': 100}

        with self.assertRaises(RuntimeError):
            Config.get_value(['field_one', 'nested_field'])

        self.reset_config_variables()

    def test_get_value_with_invalid_keys(self):
        config = {'field_one': {'nested_field': True}, 'field_two': 100}

        Config.set_config(config)

        with self.assertRaises(ValueError):
            Config.get_value(['house_key', 'car_key'])

        self.reset_config_variables()

    def test_get_enabled_endpoints(self):
        config = {'logs': {'endpoints': {'enabled': ['one', 'two', 'three']}}}

        Config.set_config(config)
        enabled_endpoints = Config.get_enabled_endpoints()

        self.assertEqual(enabled_endpoints, ['one', 'two', 'three'])

        self.reset_config_variables()

    def test_get_polling_duration(self):
        config = {'logs': {'polling': {'duration': 1234}}}

        Config.set_config(config)
        polling_duration = Config.get_polling_duration()

        self.assertEqual(polling_duration, 1234)

        self.reset_config_variables()

    def test_get_checkpoint_directory(self):
        config = {'logs': {'checkpointDir': '/tmp'}}

        Config.set_config(config)
        checkpoint_directory = Config.get_checkpoint_directory()

        self.assertEqual(checkpoint_directory, '/tmp')

        self.reset_config_variables()

    def test_get_ikey(self):
        config = {'duoclient': {'ikey': 'Integration Key'}}

        Config.set_config(config)
        ikey = Config.get_ikey()

        self.assertEqual(ikey, 'Integration Key')

        self.reset_config_variables()

    def test_get_skey(self):
        config = {'duoclient': {'skey': 'Secret Key'}}

        Config.set_config(config)
        skey = Config.get_skey()

        self.assertEqual(skey, 'Secret Key')

        self.reset_config_variables()

    def test_get_host(self):
        config = {'duoclient': {'host': 'duosecurity.com'}}

        Config.set_config(config)
        host = Config.get_host()

        self.assertEqual(host, 'duosecurity.com')

        self.reset_config_variables()

    def test_get_recover_log_offset(self):
        config = {'recoverFromCheckpoint': {'enabled': True}}

        Config.set_config(config)
        recover_log_offset = Config.get_recover_log_offset()

        self.assertEqual(recover_log_offset, True)

        self.reset_config_variables()

    def test_get_log_directory(self):
        config = {'logs': {'logDir': '/tmp'}}

        Config.set_config(config)
        log_directory = Config.get_log_directory()

        self.assertEqual(log_directory, '/tmp')

        self.reset_config_variables()

    def test_create_config_normal(self):
        config_filepath = 'tests/resources/config_files/standard.yml'
        correct_config = {
            'duoclient': {
                'skey': 'Shhh, this is a secret...',
                'ikey': 'BUNCH OF RANDOM CHARACTERS ALL UPPER CASE',
                'host': 'duosecurity.com'
            },
            'logs': {
                'logDir': '/tmp',
                'endpoints': {
                    'enabled': ['auth', 'adminaction', 'telephony']
                },
                'polling': {
                    'duration': 120,
                    'daysinpast': 180
                },
                'checkpointDir': '/tmp',
                'offset': None
            },
            'transport': {
                'protocol': 'TCP',
                'host': 'localhost',
                'port': 8888
            },
            'recoverFromCheckpoint': {
                'enabled': False
            }
        }

        config = Config.create_config(config_filepath)
        config['logs']['offset'] = None

        self.assertEqual(correct_config, config)

    def test_create_config_bad_filepath(self):
        config_filepath = 'absolute/nonsense/this/goes/nowhere.yml'

        with self.assertRaises(OSError):
            Config.create_config(config_filepath)

    def test_create_config_invalid_yaml(self):
        config_filepath = 'tests/resources/config_files/bad_yaml.yml'

        with self.assertRaises(YAMLError):
            Config.create_config(config_filepath)

    def test_create_config_invalid_config(self):
        config_filepath = 'tests/resources/config_files/bad_config.yml'

        with self.assertRaises(ValueError):
            Config.create_config(config_filepath)

    def test_create_config_with_missing_optional_fields(self):
        config_filepath = 'tests/resources/config_files/no_optional_fields.yml'

        config = Config.create_config(config_filepath)

        self.assertNotEqual(config['logs']['logDir'], None)
        self.assertNotEqual(config['logs']['polling']['duration'], None)
        self.assertNotEqual(config['logs']['polling']['daysinpast'], None)
        self.assertNotEqual(config['logs']['checkpointDir'], None)
        self.assertNotEqual(config['recoverFromCheckpoint']['enabled'], None)

    def test_create_config_with_polling_too_low(self):
        config_filepath = 'tests/resources/config_files/polling_too_low.yml'

        config = Config.create_config(config_filepath)

        self.assertEqual(config['logs']['polling']['duration'], 120)
