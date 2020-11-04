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

    def test_trust_monitor_offset_value_producer(self):
        dtm_response = {'events': [{"explanations": [{"summary": "angela_rees has not logged in from this IP recently.", "type": "NEW_NETBLOCK"}, {"summary": "angela_rees has rarely used this IP.", "type": "UNUSUAL_NETBLOCK"}], "from_common_netblock": False, "from_new_user": False, "low_risk_ip": False, "priority_event": False, "priority_reasons": [], "sekey": "SEISSBQR6V0LSGE0MU56", "state": "new", "state_updated_timestamp": None, "surfaced_auth": {"access_device": {"hostname": None, "ip": "71.105.79.160", "location": {"city": "Tokyo", "country": "Japan", "state": "Tokyo"}}, "alias": "unknown", "application": {"key": "DINZS2RAF7F5VBO0K75C", "name": "api"}, "auth_device": {"ip": None, "location": {"city": None, "country": None, "state": None}, "name": "503-543-1175"}, "email": "", "event_type": None, "factor": "duo_push", "isotimestamp": "2020-08-21T18:25:49.033490+00:00", "ood_software": "", "reason": "user_mistake", "result": "denied", "timestamp": 1598034349, "txid": "1bc858de-cef7-4337-b5b3-80eca311af08", "user": {"groups": ["Engineering"], "key": "DU6SNRESCBCXEKOJYL7V", "name": "angela_rees"}}, "surfaced_timestamp": 1598034349059, "triage_event_uri": "https://admin-dev-main-dataeng.trustedpath.info/trust-monitor?sekey=SEISSBQR6V0LSGE0MU56", "triaged_as_interesting": False, "type": "auth"}], 'metadata': {'next_offset': 2}}
        dtm_current_offset = dtm_response['metadata']['next_offset']
        dtm_offset_to_set = Producer.get_log_offset(dtm_response)
        self.assertEqual(dtm_current_offset, dtm_offset_to_set)

    def test_trust_monitor_offset_value_consumer(self):
        dtm_response = {"explanations": [{"summary": "angela_rees has not logged in from this IP recently.", "type": "NEW_NETBLOCK"}, {"summary": "angela_rees has rarely used this IP.", "type": "UNUSUAL_NETBLOCK"}], "from_common_netblock": False, "from_new_user": False, "low_risk_ip": False, "priority_event": False, "priority_reasons": [], "sekey": "SEISSBQR6V0LSGE0MU56", "state": "new", "state_updated_timestamp": None, "surfaced_auth": {"access_device": {"hostname": None, "ip": "71.105.79.160", "location": {"city": "Tokyo", "country": "Japan", "state": "Tokyo"}}, "alias": "unknown", "application": {"key": "DINZS2RAF7F5VBO0K75C", "name": "api"}, "auth_device": {"ip": None, "location": {"city": None, "country": None, "state": None}, "name": "503-543-1175"}, "email": "", "event_type": None, "factor": "duo_push", "isotimestamp": "2020-08-21T18:25:49.033490+00:00", "ood_software": "", "reason": "user_mistake", "result": "denied", "timestamp": 1598034349, "txid": "1bc858de-cef7-4337-b5b3-80eca311af08", "user": {"groups": ["Engineering"], "key": "DU6SNRESCBCXEKOJYL7V", "name": "angela_rees"}}, "surfaced_timestamp": 1598034349059, "triage_event_uri": "https://admin-dev-main-dataeng.trustedpath.info/trust-monitor?sekey=SEISSBQR6V0LSGE0MU56", "triaged_as_interesting": False, "type": "auth"}
        dtm_offset_to_set = Producer.get_log_offset(dtm_response)
        expected_offset = None
        self.assertEqual(dtm_offset_to_set, expected_offset)

    def test_offset_is_retained_when_no_logs(self):
        sample_authlog_response = {'authlogs': [], 'metadata': {'next_offset': None, 'total_objects': 94}}
        current_log_offset = ['1596815692352', 'aecef809-a026-464f-9ba6-cc88920cd55d']
        new_log_offset = Producer.get_log_offset(sample_authlog_response, current_log_offset)
        self.assertEqual(current_log_offset, new_log_offset)

    def test_dtm_offset_is_updated_when_no_logs_left_to_fetch(self):
        dtm_response = {'events': [{"explanations": [{"summary": "angela_rees has not logged in from this IP recently.", "type": "NEW_NETBLOCK"}, {"summary": "angela_rees has rarely used this IP.", "type": "UNUSUAL_NETBLOCK"}], "from_common_netblock": False, "from_new_user": False, "low_risk_ip": False, "priority_event": False, "priority_reasons": [], "sekey": "SEISSBQR6V0LSGE0MU56", "state": "new", "state_updated_timestamp": None, "surfaced_auth": {"access_device": {"hostname": None, "ip": "71.105.79.160", "location": {"city": "Tokyo", "country": "Japan", "state": "Tokyo"}}, "alias": "unknown", "application": {"key": "DINZS2RAF7F5VBO0K75C", "name": "api"}, "auth_device": {"ip": None, "location": {"city": None, "country": None, "state": None}, "name": "503-543-1175"}, "email": "", "event_type": None, "factor": "duo_push", "isotimestamp": "2020-08-21T18:25:49.033490+00:00", "ood_software": "", "reason": "user_mistake", "result": "denied", "timestamp": 1598034349, "txid": "1bc858de-cef7-4337-b5b3-80eca311af08", "user": {"groups": ["Engineering"], "key": "DU6SNRESCBCXEKOJYL7V", "name": "angela_rees"}}, "surfaced_timestamp": 1598034349059, "triage_event_uri": "https://admin-dev-main-dataeng.trustedpath.info/trust-monitor?sekey=SEISSBQR6V0LSGE0MU56", "triaged_as_interesting": False, "type": "auth"}], 'metadata': {}}
        new_log_offset = Producer.get_log_offset(dtm_response)
        expected_log_offset = dtm_response['events'][-1]['surfaced_timestamp'] + 1
        self.assertEqual(new_log_offset, expected_log_offset)
