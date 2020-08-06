from unittest import TestCase
from unittest.mock import patch
import os
import sys
from yaml import YAMLError
from duologsync.config import Config
from duologsync.program import Program

def running_is_false(msg):
    Program._running = False

class TestConfig(TestCase):
    def tearDown(self):
        Config._config = None
        Config._config_is_set = False
        Program._running = True

    def test_set_config_normal(self):
        config = {'field_one': {'nested_field': True}, 'field_two': 100}

        Config.set_config(config)

        self.assertEqual(Config._config['field_one']['nested_field'], True)
        self.assertEqual(Config._config['field_two'], 100)

    def test_set_config_twice(self):
        config = {'field_one': {'nested_field': True}, 'field_two': 100}

        Config.set_config(config)
        
        with self.assertRaises(RuntimeError):
            Config.set_config(config)

    def test_get_value_normal(self):
        config = {'field_one': {'nested_field': True}, 'field_two': 100}

        Config.set_config(config)
        value_one = Config.get_value(['field_one', 'nested_field'])
        value_two = Config.get_value(['field_two'])

        self.assertEqual(value_one, True)
        self.assertEqual(value_two, 100)

    def test_get_value_before_setting_config(self):
        config = {'field_one': {'nested_field': True}, 'field_two': 100}

        with self.assertRaises(RuntimeError):
            Config.get_value(['field_one', 'nested_field'])

    def test_get_value_with_invalid_keys(self):
        config = {'field_one': {'nested_field': True}, 'field_two': 100}

        Config.set_config(config)

        with self.assertRaises(ValueError):
            Config.get_value(['house_key', 'car_key'])

    def test_get_log_filepath(self):
        config = {'dls_settings': {'log_filepath': '/dev/null'}}

        Config.set_config(config)
        log_filepath = Config.get_log_filepath()

        self.assertEqual(log_filepath, '/dev/null')

    def test_get_log_format(self):
        config = {'dls_settings': {'log_format': 'JSON'}}

        Config.set_config(config)
        log_format = Config.get_log_format()

        self.assertEqual(log_format, 'JSON')

    def test_get_checkpointing_enabled(self):
        config = {'dls_settings': {'checkpointing': {'enabled': False}}}

        Config.set_config(config)
        checkpointing_enabled = Config.get_checkpointing_enabled()

        self.assertEqual(checkpointing_enabled, False)

    def test_get_checkpoint_dir(self):
        config = {'dls_settings': {'checkpointing': {'checkpoint_dir': '/tmp'}}}

        Config.set_config(config)
        checkpoint_dir = Config.get_checkpoint_dir()

        self.assertEqual(checkpoint_dir, '/tmp')

    def test_get_servers(self):
        config = {'servers': ['item1', 'item2']}

        Config.set_config(config)
        servers = Config.get_servers()

        self.assertEqual(servers, ['item1', 'item2'])

    def test_get_accounts(self):
        config = {'accounts': ['personal', 'private']}

        Config.set_config(config)
        accounts = Config.get_accounts()

        self.assertEqual(accounts, ['personal', 'private'])

    def test_create_config_normal(self):
        config_filepath = 'tests/resources/config_files/standard.yml'
        correct_config = {
            'version': '1.0.0',
            'dls_settings': {
                'log_filepath': '/tmp/duologsync.log',
                'log_format': 'JSON',
                'api': {
                    'offset': 180,
                    'timeout': 120
                },
                'checkpointing': {
                    'enabled': False,
                    'checkpoint_dir': '/tmp/dls_checkpoints'
                }
            },
            'servers': [
                {
                    'id': 'main server',
                    'hostname': 'mysiem.com',
                    'port': 8888,
                    'protocol': 'TCPSSL',
                    'cert_filepath': 'cert.crt'
                },
                {
                    'id': 'backup',
                    'hostname': 'safesiem.org',
                    'port': 13031,
                    'protocol': 'UDP'
                }
            ],
            'accounts': [
                {
                    'ikey': 'AAA101020K12K1K23',
                    'skey': 'jyJKYAGJKAYGDKJgyJygFUg9F9gyFuo9',
                    'hostname': 'api-test.first.duosecurity.com',
                    'endpoint_server_mappings': [
                        {
                            'endpoints': ['adminaction', 'auth'],
                            'servers': ['main server', 'backup']
                        },
                        {
                            'endpoints': ['telephony'],
                            'servers': ['backup']
                        }
                    ],
                    'is_msp': True,
                    'block_list': []
                },
                {
                    'ikey': 'DLFKSJFKJLALFK4444',
                    'skey': 'jln;89NO89898*(P',
                    'hostname': 'second.duosecurity.com',
                    'endpoint_server_mappings': [
                        {
                            'endpoints': ['auth'],
                            'servers': ['backup']
                        }
                    ]
                }
            ]
        }

        config = Config.create_config(config_filepath)
        config['dls_settings']['api']['offset'] = 180

        self.assertEqual(correct_config, config)

    @patch('duologsync.program.Program.initiate_shutdown')
    def test_create_config_bad_filepath(self, mock_initiate_shutdown):
        config_filepath = 'absolute/nonsense/this/goes/nowhere.yml'

        Config.create_config(config_filepath)

        mock_initiate_shutdown.assert_called_once()

    @patch('duologsync.program.Program.initiate_shutdown')
    def test_create_config_invalid_yaml(self, mock_initiate_shutdown):
        config_filepath = 'tests/resources/config_files/bad_yaml.yml'

        Config.create_config(config_filepath)

        mock_initiate_shutdown.assert_called_once()

    @patch('duologsync.program.Program.initiate_shutdown',
           side_effect=running_is_false)
    def test_create_config_invalid_config(self, mock_initiate_shutdown):
        config_filepath = 'tests/resources/config_files/bad_config.yml'

        Config.create_config(config_filepath)
        
        mock_initiate_shutdown.assert_called_once()

    @patch('duologsync.program.Program.initiate_shutdown',
           side_effect=running_is_false)
    def test_create_config_with_polling_too_low(self, mock_initiate_shutdown):
        config_filepath = 'tests/resources/config_files/polling_too_low.yml'

        config = Config.create_config(config_filepath)

        mock_initiate_shutdown.assert_called_once()

    def test_get_value_from_keys_normal(self):
        dictionary = {'level_one': '2FA',
                      'access_device': {'ip': '192.168.0.1'}}

        value_one = Config.get_value_from_keys(dictionary, ('level_one',))
        value_two = Config.get_value_from_keys(dictionary,
                                               ('access_device', 'ip'))

        self.assertEqual(value_one, '2FA')
        self.assertEqual(value_two, '192.168.0.1')

    def test_get_value_from_keys_bad_keys(self):
        dictionary = {'house': {'bedrooms': 2}}

        value_one = Config.get_value_from_keys(dictionary, ('hoose'))
        value_two = Config.get_value_from_keys(dictionary,
                                               ('house', 'badrooms'))

        self.assertEqual(value_one, None)
        self.assertEqual(value_two, None)
