from unittest import mock, TestCase
import os
import sys

from duologsync.config import Config

class TestUtil(TestCase):

    def test_set_config_normal():

    def test_set_config_twice():

    def test_get_value_normal():

    def test_get_value_before_setting_config():

    def test_get_value_with_invalid_keys():

    def test_get_enabled_endpoints():

    def test_get_polling_duration():

    def test_get_checkpoint_directory():

    def test_get_ikey():

    def test_get_skey():

    def test_get_host():

    def test_get_recover_log_offset():

    def test_get_log_directory():

    def test_create_config_normal():

    def test_create_config_bad_filepath():

    def test_create_config_bad_file():

    def test_create_config_invalid_yaml():

    def test_create_config_invalid_config():

    def test_get_last_offset_read(self):
       checkpoint_dir = 'resources/checkpoint'
       log_type = 'auth'
       get_last_offset_read(checkpoint_dir, log_type) 
       assert 1 == 2
