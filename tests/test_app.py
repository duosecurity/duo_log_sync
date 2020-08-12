from unittest import TestCase
from unittest.mock import patch, call
from duologsync.app import *
from duologsync.config import Config

def running_is_false(msg):
    Program._running = False

class TestApp(TestCase):
    def tearDown(self):
        Config._config = None
        Config._config_is_set = False
        Program._running = True
    
    @patch('duologsync.app.create_admin', return_value='duo_admin')
    @patch('duologsync.app.create_consumer_producer_pair')
    def test_create_tasks_one_server_multiple_endpoints(self, mock, _):
        
        server_to_writer = {'Main': 'writer_1'}
        config = {
            'account': {
                'ikey': 'a', 'skey': 'a', 'hostname': 'a',
                'endpoint_server_mappings': [
                    {
                        'endpoints': ['adminaction', 'auth', 'telephony'],
                        'server': 'Main'
                    }
                ]
            }
        }
        Config.set_config(config)

        create_tasks(server_to_writer)

        calls = [
            call('adminaction', 'writer_1', 'duo_admin'),
            call('auth', 'writer_1', 'duo_admin'),
            call('telephony', 'writer_1', 'duo_admin')
        ]

        self.assertEquals(mock.call_count, 3)
        mock.assert_has_calls(calls, any_order=True)

    @patch('duologsync.app.create_admin', return_value='duo_admin')
    @patch('duologsync.app.create_consumer_producer_pair')
    def test_create_tasks_multiple_servers_multiple_endpoints(self, mock, _):
        server_to_writer = {'Main': 'writer_1', 'Backup': 'writer_2'}
        config = {
            'account': {
                'ikey': 'a', 'skey': 'a', 'hostname': 'a',
                'endpoint_server_mappings': [
                    {
                        'endpoints': ['auth', 'telephony'],
                        'server': 'Main'
                    },
                    {
                        'endpoints': ['adminaction'],
                        'server': 'Backup'
                    }
                ]
            }
        }
        Config.set_config(config)

        create_tasks(server_to_writer)

        calls = [
            call('adminaction', 'writer_2', 'duo_admin'),
            call('auth', 'writer_1', 'duo_admin'),
            call('telephony', 'writer_1', 'duo_admin')
        ]

        self.assertEquals(mock.call_count, 3)
        mock.assert_has_calls(calls, any_order=True)

    @patch('duologsync.app.create_admin', return_value='duo_admin')
    @patch('duologsync.app.create_consumer_producer_pair')
    def test_create_tasks_one_server_per_endpoint(self, mock, _):
        server_to_writer = {'AuthServer': 'writer_1',
                            'AdminServer': 'writer_2',
                            'TelephonyServer': 'writer_3'}
        config = {
            'account': {
                'ikey': 'a', 'skey': 'a', 'hostname': 'a',
                'endpoint_server_mappings': [
                    {
                        'endpoints': ['auth'],
                        'server': 'AuthServer'
                    },
                    {
                        'endpoints': ['adminaction'],
                        'server': 'AdminServer'
                    },
                    {
                        'endpoints': ['telephony'],
                        'server': 'TelephonyServer'
                    }
                ]
            }
        }
        Config.set_config(config)

        create_tasks(server_to_writer)

        calls = [
            call('adminaction', 'writer_2', 'duo_admin'),
            call('auth', 'writer_1', 'duo_admin'),
            call('telephony', 'writer_3', 'duo_admin')
        ]

        self.assertEquals(mock.call_count, 3)
        mock.assert_has_calls(calls, any_order=True)
