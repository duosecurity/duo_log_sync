from unittest import TestCase
from unittest.mock import patch

from duologsync.producer.producer import Producer

class TestGetLogOffset(TestCase):

    def test_authlog_offset_value_producer(self):
        sample_authlog_response = {'authlogs': [{'access_device': {'browser': 'Chrome', 'browser_version': '84.0.4147.125', 'flash_version': 'uninstalled', 'hostname': None, 'ip': '107.137.171.62', 'is_encryption_enabled': 'unknown', 'is_firewall_enabled': 'unknown', 'is_password_set': 'unknown', 'java_version': 'uninstalled', 'location': {'city': 'Ann Arbor', 'country': 'United States', 'state': 'Michigan'}, 'os': 'Mac OS X', 'os_version': '10.15.6'}, 'alias': '', 'application': {'key': 'DINALEC345G8XZDFP7EP', 'name': 'Web SDK'}, 'auth_device': {'ip': None, 'location': {'city': None, 'country': None, 'state': None}, 'name': 'WAQWPO8MD9PPHPW2HPCI'}, 'email': '', 'event_type': 'authentication', 'factor': None, 'isotimestamp': '2020-08-17T13:43:58.335969+00:00', 'ood_software': None, 'reason': 'user_approved', 'result': 'success', 'timestamp': 1597671838, 'trusted_endpoint_status': 'not trusted', 'txid': '1f6e1807-1732-49aa-8068-a973e6144e5e', 'user': {'groups': [], 'key': 'DU50VRIGM3ELGSN0XAA3', 'name': 'hi'}, 'eventtype': 'authentication', 'host': 'api-first.test.duosecurity.com'}], 'metadata': {'next_offset': ['1597671838335', '1f6e1807-1732-49aa-8068-a973e6144e5e'], 'total_objects': 94}}
        offset_in_metadata = sample_authlog_response['metadata']['next_offset']
        producer_offset = Producer.get_log_offset(sample_authlog_response)
        self.assertEqual(offset_in_metadata, producer_offset)

    def test_authlog_offset_value_consumer(self):
        sample_authlog_response = {'authlogs': [{'access_device': {'browser': 'Chrome', 'browser_version': '84.0.4147.125', 'flash_version': 'uninstalled', 'hostname': None, 'ip': '107.137.171.62', 'is_encryption_enabled': 'unknown', 'is_firewall_enabled': 'unknown', 'is_password_set': 'unknown', 'java_version': 'uninstalled', 'location': {'city': 'Ann Arbor', 'country': 'United States', 'state': 'Michigan'}, 'os': 'Mac OS X', 'os_version': '10.15.6'}, 'alias': '', 'application': {'key': 'DINALEC345G8XZDFP7EP', 'name': 'Web SDK'}, 'auth_device': {'ip': None, 'location': {'city': None, 'country': None, 'state': None}, 'name': 'WAQWPO8MD9PPHPW2HPCI'}, 'email': '', 'event_type': 'authentication', 'factor': None, 'isotimestamp': '2020-08-17T13:43:58.335969+00:00', 'ood_software': None, 'reason': 'user_approved', 'result': 'success', 'timestamp': 1597671838, 'trusted_endpoint_status': 'not trusted', 'txid': '1f6e1807-1732-49aa-8068-a973e6144e5e', 'user': {'groups': [], 'key': 'DU50VRIGM3ELGSN0XAA3', 'name': 'hi'}, 'eventtype': 'authentication', 'host': 'api-first.test.duosecurity.com'}], 'metadata': {'next_offset': ['1597671838335', '1f6e1807-1732-49aa-8068-a973e6144e5e'], 'total_objects': 94}}
        offset_in_metadata = sample_authlog_response['metadata']['next_offset']
        producer_offset = Producer.get_log_offset(sample_authlog_response.get('authlogs')[-1])
        self.assertEqual(offset_in_metadata, producer_offset)

    def test_adminaction_offset_value_producer(self):
        adminaction_response = [{'action': 'admin_login', 'description': '{"ip_address": "72.35.40.116", "device": "248-971-9157", "primary_auth_method": "Password", "factor": "push"}', 'isotimestamp': '2020-02-10T14:41:22+00:00', 'object': None, 'timestamp': 1581345682, 'username': 'CJ Na', 'eventtype': 'administrator', 'host': 'api-first.test.duosecurity.com'}]
        adminaction_current_offset = adminaction_response[-1]['timestamp'] + 1
        adminaction_offset_to_set = Producer.get_log_offset(adminaction_response)
        self.assertEqual(adminaction_current_offset, adminaction_offset_to_set)

    def test_adminaction_offset_value_consumer(self):
        adminaction_response = [{'action': 'admin_login', 'description': '{"ip_address": "72.35.40.116", "device": "248-971-9157", "primary_auth_method": "Password", "factor": "push"}', 'isotimestamp': '2020-02-10T14:41:22+00:00', 'object': None, 'timestamp': 1581345682, 'username': 'CJ Na', 'eventtype': 'administrator', 'host': 'api-first.test.duosecurity.com'}]
        adminaction_current_offset = adminaction_response[0]['timestamp'] + 1
        adminaction_offset_to_set = Producer.get_log_offset(adminaction_response[0])
        self.assertEqual(adminaction_current_offset, adminaction_offset_to_set)

    def test_telephony_offset_value_producer(self):
        telephony_response = [{'context': 'authentication', 'credits': 2, 'isotimestamp': '2020-05-18T11:32:53+00:00', 'phone': '+13135105356', 'timestamp': 1589801573, 'type': 'phone', 'eventtype': 'telephony', 'host': 'api-first.test.duosecurity.com'}]
        telephony_current_offset = telephony_response[-1]['timestamp'] + 1
        telephony_offset_to_set = Producer.get_log_offset(telephony_response)
        self.assertEqual(telephony_current_offset, telephony_offset_to_set)

    def test_telephony_offset_value_consumer(self):
        telephony_response = [{'action': 'admin_login', 'description': '{"ip_address": "72.35.40.116", "device": "248-971-9157", "primary_auth_method": "Password", "factor": "push"}', 'isotimestamp': '2020-02-10T14:41:22+00:00', 'object': None, 'timestamp': 1581345682, 'username': 'CJ Na', 'eventtype': 'administrator', 'host': 'api-first.test.duosecurity.com'}]
        telephony_current_offset = telephony_response[0]['timestamp'] + 1
        telephony_offset_to_set = Producer.get_log_offset(telephony_response[0])
        self.assertEqual(telephony_current_offset, telephony_offset_to_set)
