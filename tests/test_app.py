from unittest import TestCase
from unittest.mock import patch, call
from duologsync.app import Program, create_tasks
from duologsync.config import Config
import duo_client


def running_is_false(msg):
    Program._running = False


class TestApp(TestCase):
    def tearDown(self):
        Config._config = None
        Config._config_is_set = False
        Program._running = True

    @patch("duologsync.app.create_admin", return_value="duo_admin")
    @patch("duologsync.app.create_consumer_producer_pair")
    def test_create_tasks_one_server_multiple_endpoints(self, mock, _):

        server_to_writer = {"Main": "writer_1"}
        config = {
            "dls_settings": {"proxy": {"proxy_server": "test.com", "proxy_port": 1234}},
            "account": {
                "ikey": "a",
                "skey": "a",
                "hostname": "a",
                "endpoint_server_mappings": [
                    {
                        "endpoints": [
                            "adminaction",
                            "auth",
                            "telephony",
                            "trustmonitor",
                            "activity",
                        ],
                        "server": "Main",
                    }
                ],
                "is_msp": False,
            },
        }
        Config.set_config(config)

        create_tasks(server_to_writer)

        calls = [
            call("adminaction", "writer_1", "duo_admin"),
            call("auth", "writer_1", "duo_admin"),
            call("telephony", "writer_1", "duo_admin"),
            call("trustmonitor", "writer_1", "duo_admin"),
            call("activity", "writer_1", "duo_admin"),
        ]

        self.assertEquals(mock.call_count, 5)
        mock.assert_has_calls(calls, any_order=True)

    @patch("duologsync.app.create_admin", return_value=duo_client.Accounts)
    @patch(
        "duo_client.Accounts.get_child_accounts",
        return_value=[{"account_id": "12345"}, {"account_id": "56789"}],
    )
    @patch("duologsync.app.create_consumer_producer_pair")
    def test_create_tasks_one_server_multiple_endpoints_msp(
        self, mock, mock_childaccount, mock_createadmin
    ):
        server_to_writer = {"Main": "writer_1"}
        config = {
            "dls_settings": {"proxy": {"proxy_server": "test.com", "proxy_port": 1234}},
            "account": {
                "ikey": "a",
                "skey": "a",
                "hostname": "a",
                "endpoint_server_mappings": [
                    {
                        "endpoints": ["adminaction", "auth", "telephony", "activity"],
                        "server": "Main",
                    }
                ],
                "is_msp": True,
            },
        }
        Config.set_config(config)

        create_tasks(server_to_writer)

        calls = [
            call("adminaction", "writer_1", duo_client.Accounts, "12345"),
            call("auth", "writer_1", duo_client.Accounts, "12345"),
            call("telephony", "writer_1", duo_client.Accounts, "12345"),
            call("adminaction", "writer_1", duo_client.Accounts, "56789"),
            call("auth", "writer_1", duo_client.Accounts, "56789"),
            call("telephony", "writer_1", duo_client.Accounts, "56789"),
            call("activity", "writer_1", duo_client.Accounts, "56789"),
        ]

        self.assertEqual(mock_childaccount.call_count, 1)
        self.assertEqual(mock.call_count, 8)
        mock.assert_has_calls(calls, any_order=True)

    @patch("duologsync.app.create_admin", return_value="duo_admin")
    @patch("duologsync.app.create_consumer_producer_pair")
    def test_create_tasks_multiple_servers_multiple_endpoints(self, mock, _):
        server_to_writer = {"Main": "writer_1", "Backup": "writer_2"}
        config = {
            "dls_settings": {"proxy": {"proxy_server": "test.com", "proxy_port": 1234}},
            "account": {
                "ikey": "a",
                "skey": "a",
                "hostname": "a",
                "endpoint_server_mappings": [
                    {"endpoints": ["auth", "telephony"], "server": "Main"},
                    {
                        "endpoints": ["adminaction", "trustmonitor", "activity"],
                        "server": "Backup",
                    },
                ],
                "is_msp": False,
            },
        }
        Config.set_config(config)

        create_tasks(server_to_writer)

        calls = [
            call("adminaction", "writer_2", "duo_admin"),
            call("trustmonitor", "writer_2", "duo_admin"),
            call("activity", "writer_2", "duo_admin"),
            call("auth", "writer_1", "duo_admin"),
            call("telephony", "writer_1", "duo_admin"),
        ]

        self.assertEquals(mock.call_count, 5)
        mock.assert_has_calls(calls, any_order=True)

    @patch("duologsync.app.create_admin", return_value="duo_admin")
    @patch("duologsync.app.create_consumer_producer_pair")
    def test_create_tasks_one_server_per_endpoint(self, mock, _):
        server_to_writer = {
            "AuthServer": "writer_1",
            "AdminServer": "writer_2",
            "TelephonyServer": "writer_3",
            "TrustMonitorServer": "writer_4",
            "ActivityServer": "writer_5",
        }
        config = {
            "dls_settings": {"proxy": {"proxy_server": "test.com", "proxy_port": 1234}},
            "account": {
                "ikey": "a",
                "skey": "a",
                "hostname": "a",
                "endpoint_server_mappings": [
                    {"endpoints": ["auth"], "server": "AuthServer"},
                    {"endpoints": ["adminaction"], "server": "AdminServer"},
                    {"endpoints": ["telephony"], "server": "TelephonyServer"},
                    {"endpoints": ["trustmonitor"], "server": "TrustMonitorServer"},
                    {"endpoints": ["activity"], "server": "ActivityServer"},
                ],
                "is_msp": False,
            },
        }
        Config.set_config(config)

        create_tasks(server_to_writer)

        calls = [
            call("adminaction", "writer_2", "duo_admin"),
            call("auth", "writer_1", "duo_admin"),
            call("telephony", "writer_3", "duo_admin"),
            call("trustmonitor", "writer_4", "duo_admin"),
            call("activity", "writer_5", "duo_admin"),
        ]

        self.assertEquals(mock.call_count, 5)
        mock.assert_has_calls(calls, any_order=True)
