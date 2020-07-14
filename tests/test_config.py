from unittest import mock, TestCase
import os
import sys

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
        pass
    def test_get_value_before_setting_config(self):
        pass
    def test_get_value_with_invalid_keys(self):
        pass
    def test_get_enabled_endpoints(self):
        pass
    def test_get_polling_duration(self):
        pass
    def test_get_checkpoint_directory(self):
        pass
    def test_get_ikey(self):
        pass
    def test_get_skey(self):
        pass
    def test_get_host(self):
        pass
    def test_get_recover_log_offset(self):
        pass
    def test_get_log_directory(self):
        pass
    def test_create_config_normal(self):
        pass
    def test_create_config_bad_filepath(self):
        pass
    def test_create_config_bad_file(self):
        pass
    def test_create_config_invalid_yaml(self):
        pass
    def test_create_config_invalid_config(self):
        pass
