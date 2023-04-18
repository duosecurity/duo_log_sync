from datetime import datetime
from unittest import TestCase

from duologsync.config import Config
from duologsync.producer.producer import Producer


class TestGetLogOffset(TestCase):
    def test_authlog_offset_value_producer(self):
        sample_authlog_response = {
            "authlogs": [
                {
                    "access_device": {
                        "browser": "Chrome",
                        "browser_version": "84.0.4147.125",
                        "flash_version": "uninstalled",
                        "hostname": None,
                        "ip": "107.137.171.62",
                        "is_encryption_enabled": "unknown",
                        "is_firewall_enabled": "unknown",
                        "is_password_set": "unknown",
                        "java_version": "uninstalled",
                        "location": {
                            "city": "Ann Arbor",
                            "country": "United States",
                            "state": "Michigan",
                        },
                        "os": "Mac OS X",
                        "os_version": "10.15.6",
                    },
                    "alias": "",
                    "application": {"key": "DINALEC345G8XZDFP7EP", "name": "Web SDK"},
                    "auth_device": {
                        "ip": None,
                        "location": {"city": None, "country": None, "state": None},
                        "name": "WAQWPO8MD9PPHPW2HPCI",
                    },
                    "email": "",
                    "event_type": "authentication",
                    "factor": None,
                    "isotimestamp": "2020-08-17T13:43:58.335969+00:00",
                    "ood_software": None,
                    "reason": "user_approved",
                    "result": "success",
                    "timestamp": 1597671838,
                    "trusted_endpoint_status": "not trusted",
                    "txid": "1f6e1807-1732-49aa-8068-a973e6144e5e",
                    "user": {"groups": [], "key": "DU50VRIGM3ELGSN0XAA3", "name": "hi"},
                    "eventtype": "authentication",
                    "host": "api-first.test.duosecurity.com",
                }
            ],
            "metadata": {
                "next_offset": [
                    "1597671838335",
                    "1f6e1807-1732-49aa-8068-a973e6144e5e",
                ],
                "total_objects": 94,
            },
        }
        offset_in_metadata = sample_authlog_response["metadata"]["next_offset"]
        producer_offset = Producer.get_log_offset(
            sample_authlog_response, log_type=Config.AUTH
        )
        self.assertEqual(offset_in_metadata, producer_offset)

    def test_authlog_offset_value_consumer(self):
        sample_authlog_response = {
            "authlogs": [
                {
                    "access_device": {
                        "browser": "Chrome",
                        "browser_version": "84.0.4147.125",
                        "flash_version": "uninstalled",
                        "hostname": None,
                        "ip": "107.137.171.62",
                        "is_encryption_enabled": "unknown",
                        "is_firewall_enabled": "unknown",
                        "is_password_set": "unknown",
                        "java_version": "uninstalled",
                        "location": {
                            "city": "Ann Arbor",
                            "country": "United States",
                            "state": "Michigan",
                        },
                        "os": "Mac OS X",
                        "os_version": "10.15.6",
                    },
                    "alias": "",
                    "application": {"key": "DINALEC345G8XZDFP7EP", "name": "Web SDK"},
                    "auth_device": {
                        "ip": None,
                        "location": {"city": None, "country": None, "state": None},
                        "name": "WAQWPO8MD9PPHPW2HPCI",
                    },
                    "email": "",
                    "event_type": "authentication",
                    "factor": None,
                    "isotimestamp": "2020-08-17T13:43:58.335969+00:00",
                    "ood_software": None,
                    "reason": "user_approved",
                    "result": "success",
                    "timestamp": 1597671838,
                    "trusted_endpoint_status": "not trusted",
                    "txid": "1f6e1807-1732-49aa-8068-a973e6144e5e",
                    "user": {"groups": [], "key": "DU50VRIGM3ELGSN0XAA3", "name": "hi"},
                    "eventtype": "authentication",
                    "host": "api-first.test.duosecurity.com",
                }
            ],
            "metadata": {
                "next_offset": [
                    "1597671838335",
                    "1f6e1807-1732-49aa-8068-a973e6144e5e",
                ],
                "total_objects": 94,
            },
        }
        offset_in_metadata = sample_authlog_response["metadata"]["next_offset"]
        producer_offset = Producer.get_log_offset(
            sample_authlog_response.get("authlogs")[-1], log_type=Config.AUTH
        )
        self.assertEqual(offset_in_metadata, producer_offset)

    def test_adminaction_offset_value_producer(self):
        adminaction_response = [
            {
                "action": "admin_login",
                "description": '{"ip_address": "72.35.40.116", "device": "248-971-9157", "primary_auth_method": "Password", "factor": "push"}',
                "isotimestamp": "2020-02-10T14:41:22+00:00",
                "object": None,
                "timestamp": 1581345682,
                "username": "CJ Na",
                "eventtype": "administrator",
                "host": "api-first.test.duosecurity.com",
            }
        ]
        adminaction_current_offset = adminaction_response[-1]["timestamp"] + 1
        adminaction_offset_to_set = Producer.get_log_offset(
            adminaction_response, log_type=Config.ADMIN
        )
        self.assertEqual(adminaction_current_offset, adminaction_offset_to_set)

    def test_adminaction_offset_value_consumer(self):
        adminaction_response = [
            {
                "action": "admin_login",
                "description": '{"ip_address": "72.35.40.116", "device": "248-971-9157", "primary_auth_method": "Password", "factor": "push"}',
                "isotimestamp": "2020-02-10T14:41:22+00:00",
                "object": None,
                "timestamp": 1581345682,
                "username": "CJ Na",
                "eventtype": "administrator",
                "host": "api-first.test.duosecurity.com",
            }
        ]
        adminaction_current_offset = adminaction_response[0]["timestamp"] + 1
        adminaction_offset_to_set = Producer.get_log_offset(
            adminaction_response[0], log_type=Config.ADMIN
        )
        self.assertEqual(adminaction_current_offset, adminaction_offset_to_set)

    def test_telephony_offset_value_producer(self):
        sample_telephony_response = {
            "items": [
                {
                    "context": "context1234",
                    "credits": 3,
                    "phone": "+11234567890",
                    "telephony_id": "93a67857-365a-4ff3-a445-e389c2ab2df6",
                    "ts": "2022-11-01T21:24:00.000000+00:00",
                    "txid": "1bc858de-cef7-4337-b5b3-80eca311af01",
                    "type": "sms",
                },
                {
                    "context": "context1234",
                    "credits": 3,
                    "phone": "+11234567890",
                    "telephony_id": "93a67857-365a-4ff3-a445-e389c2ab2df6",
                    "ts": "2022-11-01T21:24:00.000000+00:00",
                    "txid": "1bc858de-cef7-4337-b5b3-80eca311af02",
                    "type": "sms",
                },
                {
                    "context": "context1234",
                    "credits": 3,
                    "phone": "+11234567890",
                    "telephony_id": "93a67857-365a-4ff3-a445-e389c2ab2df6",
                    "ts": "2022-11-01T21:24:00.000000+00:00",
                    "txid": "1bc858de-cef7-4337-b5b3-80eca311af03",
                    "type": "sms",
                },
            ],
            "metadata": {
                "next_offset": "1664576469635,1c40324f-eb60-4e87-9ffb-656295fd235b",
                "total_objects": 4000,
            },
        }
        offset_in_metadata = sample_telephony_response["metadata"]["next_offset"]
        producer_offset = Producer.get_log_offset(
            sample_telephony_response, log_type=Config.TELEPHONY
        )
        self.assertEqual(offset_in_metadata, producer_offset)

    def test_telephony_offset_value_consumer(self):
        sample_telephony_response = {
            "context": "context1234",
            "credits": 3,
            "phone": "+11234567890",
            "telephony_id": "93a67857-365a-4ff3-a445-e389c2ab2df6",
            "ts": "2022-11-01T21:24:00.000000+00:00",
            "txid": "1bc858de-cef7-4337-b5b3-80eca311af03",
            "type": "sms",
        }
        next_timestamp_to_poll_from = (
            datetime.strptime(
                sample_telephony_response.get("ts", ""),
                "%Y-%m-%dT%H:%M:%S.%f+00:00",
            ).timestamp()
            * 1000
        )
        telephony_id = sample_telephony_response.get("telephony_id")
        next_timestamp = int(next_timestamp_to_poll_from) + 1
        next_offset = f"{next_timestamp},{telephony_id}"
        consumer_offset = Producer.get_log_offset(
            sample_telephony_response, log_type=Config.TELEPHONY
        )
        self.assertEqual(next_offset, consumer_offset)

    def test_trust_monitor_offset_value_producer(self):
        dtm_response = {
            "events": [
                {
                    "explanations": [
                        {
                            "summary": "angela_rees has not logged in from this IP recently.",
                            "type": "NEW_NETBLOCK",
                        },
                        {
                            "summary": "angela_rees has rarely used this IP.",
                            "type": "UNUSUAL_NETBLOCK",
                        },
                    ],
                    "from_common_netblock": False,
                    "from_new_user": False,
                    "low_risk_ip": False,
                    "priority_event": False,
                    "priority_reasons": [],
                    "sekey": "SEISSBQR6V0LSGE0MU56",
                    "state": "new",
                    "state_updated_timestamp": None,
                    "surfaced_auth": {
                        "access_device": {
                            "hostname": None,
                            "ip": "71.105.79.160",
                            "location": {
                                "city": "Tokyo",
                                "country": "Japan",
                                "state": "Tokyo",
                            },
                        },
                        "alias": "unknown",
                        "application": {"key": "DINZS2RAF7F5VBO0K75C", "name": "api"},
                        "auth_device": {
                            "ip": None,
                            "location": {"city": None, "country": None, "state": None},
                            "name": "503-543-1175",
                        },
                        "email": "",
                        "event_type": None,
                        "factor": "duo_push",
                        "isotimestamp": "2020-08-21T18:25:49.033490+00:00",
                        "ood_software": "",
                        "reason": "user_mistake",
                        "result": "denied",
                        "timestamp": 1598034349,
                        "txid": "1bc858de-cef7-4337-b5b3-80eca311af08",
                        "user": {
                            "groups": ["Engineering"],
                            "key": "DU6SNRESCBCXEKOJYL7V",
                            "name": "angela_rees",
                        },
                    },
                    "surfaced_timestamp": 1598034349059,
                    "triage_event_uri": "https://admin-dev-main-dataeng.trustedpath.info/trust-monitor?sekey=SEISSBQR6V0LSGE0MU56",
                    "triaged_as_interesting": False,
                    "type": "auth",
                }
            ],
            "metadata": {"next_offset": 2},
        }
        dtm_current_offset = dtm_response["metadata"]["next_offset"]
        dtm_offset_to_set = Producer.get_log_offset(
            dtm_response, log_type=Config.TRUST_MONITOR
        )
        self.assertEqual(dtm_current_offset, dtm_offset_to_set)

    def test_trust_monitor_offset_value_consumer(self):
        dtm_response = {
            "explanations": [
                {
                    "summary": "angela_rees has not logged in from this IP recently.",
                    "type": "NEW_NETBLOCK",
                },
                {
                    "summary": "angela_rees has rarely used this IP.",
                    "type": "UNUSUAL_NETBLOCK",
                },
            ],
            "from_common_netblock": False,
            "from_new_user": False,
            "low_risk_ip": False,
            "priority_event": False,
            "priority_reasons": [],
            "sekey": "SEISSBQR6V0LSGE0MU56",
            "state": "new",
            "state_updated_timestamp": None,
            "surfaced_auth": {
                "access_device": {
                    "hostname": None,
                    "ip": "71.105.79.160",
                    "location": {"city": "Tokyo", "country": "Japan", "state": "Tokyo"},
                },
                "alias": "unknown",
                "application": {"key": "DINZS2RAF7F5VBO0K75C", "name": "api"},
                "auth_device": {
                    "ip": None,
                    "location": {"city": None, "country": None, "state": None},
                    "name": "503-543-1175",
                },
                "email": "",
                "event_type": None,
                "factor": "duo_push",
                "isotimestamp": "2020-08-21T18:25:49.033490+00:00",
                "ood_software": "",
                "reason": "user_mistake",
                "result": "denied",
                "timestamp": 1598034349,
                "txid": "1bc858de-cef7-4337-b5b3-80eca311af08",
                "user": {
                    "groups": ["Engineering"],
                    "key": "DU6SNRESCBCXEKOJYL7V",
                    "name": "angela_rees",
                },
            },
            "surfaced_timestamp": 1598034349059,
            "triage_event_uri": "https://admin-dev-main-dataeng.trustedpath.info/trust-monitor?sekey=SEISSBQR6V0LSGE0MU56",
            "triaged_as_interesting": False,
            "type": "auth",
        }
        dtm_offset_to_set = Producer.get_log_offset(
            dtm_response, log_type=Config.TRUST_MONITOR
        )
        expected_offset = 1598034349060
        self.assertEqual(dtm_offset_to_set, expected_offset)

    def test_offset_is_retained_when_no_logs(self):
        sample_authlog_response = {
            "authlogs": [],
            "metadata": {"next_offset": None, "total_objects": 94},
        }
        current_log_offset = ["1596815692352", "aecef809-a026-464f-9ba6-cc88920cd55d"]
        new_log_offset = Producer.get_log_offset(
            sample_authlog_response, current_log_offset
        )
        self.assertEqual(current_log_offset, new_log_offset)

    def test_dtm_offset_is_updated_when_no_logs_left_to_fetch(self):
        dtm_response = {
            "events": [
                {
                    "explanations": [
                        {
                            "summary": "angela_rees has not logged in from this IP recently.",
                            "type": "NEW_NETBLOCK",
                        },
                        {
                            "summary": "angela_rees has rarely used this IP.",
                            "type": "UNUSUAL_NETBLOCK",
                        },
                    ],
                    "from_common_netblock": False,
                    "from_new_user": False,
                    "low_risk_ip": False,
                    "priority_event": False,
                    "priority_reasons": [],
                    "sekey": "SEISSBQR6V0LSGE0MU56",
                    "state": "new",
                    "state_updated_timestamp": None,
                    "surfaced_auth": {
                        "access_device": {
                            "hostname": None,
                            "ip": "71.105.79.160",
                            "location": {
                                "city": "Tokyo",
                                "country": "Japan",
                                "state": "Tokyo",
                            },
                        },
                        "alias": "unknown",
                        "application": {"key": "DINZS2RAF7F5VBO0K75C", "name": "api"},
                        "auth_device": {
                            "ip": None,
                            "location": {"city": None, "country": None, "state": None},
                            "name": "503-543-1175",
                        },
                        "email": "",
                        "event_type": None,
                        "factor": "duo_push",
                        "isotimestamp": "2020-08-21T18:25:49.033490+00:00",
                        "ood_software": "",
                        "reason": "user_mistake",
                        "result": "denied",
                        "timestamp": 1598034349,
                        "txid": "1bc858de-cef7-4337-b5b3-80eca311af08",
                        "user": {
                            "groups": ["Engineering"],
                            "key": "DU6SNRESCBCXEKOJYL7V",
                            "name": "angela_rees",
                        },
                    },
                    "surfaced_timestamp": 1598034349059,
                    "triage_event_uri": "https://admin-dev-main-dataeng.trustedpath.info/trust-monitor?sekey=SEISSBQR6V0LSGE0MU56",
                    "triaged_as_interesting": False,
                    "type": "auth",
                }
            ],
            "metadata": {},
        }
        new_log_offset = Producer.get_log_offset(
            dtm_response, log_type=Config.TRUST_MONITOR
        )
        expected_log_offset = dtm_response["events"][-1]["surfaced_timestamp"] + 1
        self.assertEqual(new_log_offset, expected_log_offset)

    def test_activity_offset_value_producer(self):
        sample_activity_response = {
            "items": [
                {
                    "action": "phone_create",
                    "activity_id": "49922e59-0ebe-421a-9635-9846252f6c0a",
                    "actor": {
                        "details": '{"created": "2022-07-10T00:00:00.000000+00:00", "last_login": "2022-07-11T00:00:00.000000+00:00", "status": "Active", "groups": [{"name": "Jedi", "key": "DG0DU4883PFLGTUIDIXG"}]}',
                        "key": "DU123456789012345678",
                        "name": "samplename",
                        "type": "user",
                    },
                    "akey": "DA0STO6EVV8EAONUD8P7",
                    "ts": "2022-09-30T23:10:39.635000+00:00",
                },
                {
                    "action": "phone_create",
                    "activity_id": "5943daea-24cd-43c8-8c4b-1870cbdd9b8f",
                    "actor": {
                        "details": '{"created": "2022-07-10T00:00:00.000000+00:00", "last_login": "2022-07-11T00:00:00.000000+00:00", "status": "Active", "groups": [{"name": "Jedi", "key": "DG0DU4883PFLGTUIDIXG"}]}',
                        "key": "DU123456789012345678",
                        "name": "samplename",
                        "type": "user",
                    },
                    "akey": "DA0STO6EVV8EAONUD8P7",
                    "ts": "2022-09-30T23:10:09.635000+00:00",
                },
                {
                    "action": "phone_create",
                    "activity_id": "9906fb6c-177e-4a70-8c1a-d22951b62781",
                    "actor": {
                        "details": '{"created": "2022-07-10T00:00:00.000000+00:00", "last_login": "2022-07-11T00:00:00.000000+00:00", "status": "Active", "groups": [{"name": "Jedi", "key": "DG0DU4883PFLGTUIDIXG"}]}',
                        "key": "DU123456789012345678",
                        "name": "samplename",
                        "type": "user",
                    },
                    "akey": "DA0STO6EVV8EAONUD8P7",
                    "ts": "2022-09-30T23:09:39.635000+00:00",
                },
            ],
            "metadata": {
                "next_offset": "1664576469635,1c40324f-eb60-4e87-9ffb-656295fd235b",
                "total_objects": 4000,
            },
        }
        offset_in_metadata = sample_activity_response["metadata"]["next_offset"]
        producer_offset = Producer.get_log_offset(
            sample_activity_response, log_type=Config.ACTIVITY
        )
        self.assertEqual(offset_in_metadata, producer_offset)

    def test_activity_offset_value_consumer(self):
        sample_activity_response = {
            "action": "phone_create",
            "activity_id": "9906fb6c-177e-4a70-8c1a-d22951b62781",
            "actor": {
                "details": '{"created": "2022-07-10T00:00:00.000000+00:00", "last_login": "2022-07-11T00:00:00.000000+00:00", "status": "Active", "groups": [{"name": "Jedi", "key": "DG0DU4883PFLGTUIDIXG"}]}',
                "key": "DU123456789012345678",
                "name": "samplename",
                "type": "user",
            },
            "akey": "DA0STO6EVV8EAONUD8P7",
            "ts": "2022-09-30T23:09:39.635000+00:00",
        }
        next_timestamp_to_poll_from = (
            datetime.strptime(
                sample_activity_response.get("ts", ""),
                "%Y-%m-%dT%H:%M:%S.%f+00:00",
            ).timestamp()
            * 1000
        )
        activity_id = sample_activity_response.get("activity_id")
        next_timestamp = int(next_timestamp_to_poll_from) + 1
        next_offset = f"{next_timestamp},{activity_id}"
        consumer_offset = Producer.get_log_offset(
            sample_activity_response, log_type=Config.ACTIVITY
        )
        self.assertEqual(next_offset, consumer_offset)
