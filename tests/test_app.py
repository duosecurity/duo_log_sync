from unittest import TestCase
from unittest.mock import patch, call
from duologsync.app import Program, create_tasks
from duologsync.config import Config


def running_is_false(msg):
    Program._running = False


class TestApp(TestCase):
    def tearDown(self):
        Config._config = None
        Config._config_is_set = False
        Program._running = True

    @patch("duologsync.app.get_subaccounts")
    @patch("duologsync.app.create_admin", return_value="duo_admin")
    @patch("duologsync.app.create_consumer_producer_pair")
    def test_create_tasks_one_server_multiple_endpoints(
        self, mock_pair, mock_create_admin, mock_get_subaccounts
    ):

        server_to_writer = {"Main": "writer_1"}
        config = {
            "dls_settings": {
                "proxy": {"proxy_server": "test.com", "proxy_port": 1234},
            },
            "account": {
                "ikey": "a",
                "skey": "a",
                "hostname": "a",
                "endpoint_server_mappings": [
                    {
                        "endpoints": [
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
            call("auth", "writer_1", "duo_admin"),
            call("telephony", "writer_1", "duo_admin"),
            call("trustmonitor", "writer_1", "duo_admin"),
            call("activity", "writer_1", "duo_admin"),
        ]

        mock_get_subaccounts.assert_not_called()
        mock_create_admin.assert_called_once_with(
            "a",
            "a",
            "a",
            proxy_server="test.com",
            proxy_port=1234,
        )
        self.assertEqual(mock_pair.call_count, 4)
        mock_pair.assert_has_calls(calls, any_order=True)

    @patch(
        "duologsync.app.create_admin",
        side_effect=["parent_admin", "child_admin_1", "child_admin_2"],
    )
    @patch("duologsync.app.get_subaccounts")
    @patch("duologsync.app.create_consumer_producer_pair")
    def test_create_tasks_one_server_multiple_endpoints_msp(
        self, mock_pair, mock_get_subaccounts, mock_create_admin
    ):
        mock_get_subaccounts.return_value = [
            {
                "account_id": "DA9VZOC5X63I2W72NRP9",
                "api_hostname": "api-abcd1234.duosecurity.com",
            },
            {
                "account_id": "DAAAAAAAAAAAAAAAAAAA",
                "api_hostname": "api-efgh5678.duosecurity.com",
            },
        ]
        server_to_writer = {"Main": "writer_1"}
        config = {
            "dls_settings": {
                "proxy": {"proxy_server": "test.com", "proxy_port": 1234},
            },
            "account": {
                "ikey": "a",
                "skey": "a",
                "hostname": "a",
                "endpoint_server_mappings": [
                    {
                        "endpoints": ["auth", "telephony", "activity"],
                        "server": "Main",
                    }
                ],
                "is_msp": True,
            },
        }
        Config.set_config(config)

        create_tasks(server_to_writer)

        task_calls = [
            call(
                "auth",
                "writer_1",
                "child_admin_1",
                "DA9VZOC5X63I2W72NRP9",
            ),
            call(
                "telephony",
                "writer_1",
                "child_admin_1",
                "DA9VZOC5X63I2W72NRP9",
            ),
            call(
                "activity",
                "writer_1",
                "child_admin_1",
                "DA9VZOC5X63I2W72NRP9",
            ),
            call(
                "auth",
                "writer_1",
                "child_admin_2",
                "DAAAAAAAAAAAAAAAAAAA",
            ),
            call(
                "telephony",
                "writer_1",
                "child_admin_2",
                "DAAAAAAAAAAAAAAAAAAA",
            ),
            call(
                "activity",
                "writer_1",
                "child_admin_2",
                "DAAAAAAAAAAAAAAAAAAA",
            ),
        ]
        admin_calls = [
            call(
                "a",
                "a",
                "a",
                proxy_server="test.com",
                proxy_port=1234,
            ),
            call(
                "a",
                "a",
                "api-abcd1234.duosecurity.com",
                proxy_server="test.com",
                proxy_port=1234,
            ),
            call(
                "a",
                "a",
                "api-efgh5678.duosecurity.com",
                proxy_server="test.com",
                proxy_port=1234,
            ),
        ]

        mock_get_subaccounts.assert_called_once_with("parent_admin")
        self.assertEqual(mock_pair.call_count, 6)
        self.assertEqual(mock_pair.call_args_list, task_calls)
        self.assertEqual(mock_create_admin.call_args_list, admin_calls)

    @patch("duologsync.app.create_admin", return_value="duo_admin")
    @patch("duologsync.app.create_consumer_producer_pair")
    def test_create_tasks_multiple_servers_multiple_endpoints(self, mock, _):
        server_to_writer = {"Main": "writer_1", "Backup": "writer_2"}
        config = {
            "dls_settings": {
                "proxy": {"proxy_server": "test.com", "proxy_port": 1234},
            },
            "account": {
                "ikey": "a",
                "skey": "a",
                "hostname": "a",
                "endpoint_server_mappings": [
                    {"endpoints": ["auth", "telephony"], "server": "Main"},
                    {
                        "endpoints": ["trustmonitor", "activity"],
                        "server": "Backup",
                    },
                ],
                "is_msp": False,
            },
        }
        Config.set_config(config)

        create_tasks(server_to_writer)

        calls = [
            call("trustmonitor", "writer_2", "duo_admin"),
            call("activity", "writer_2", "duo_admin"),
            call("auth", "writer_1", "duo_admin"),
            call("telephony", "writer_1", "duo_admin"),
        ]

        self.assertEqual(mock.call_count, 4)
        mock.assert_has_calls(calls, any_order=True)

    @patch("duologsync.app.create_admin", return_value="duo_admin")
    @patch("duologsync.app.create_consumer_producer_pair")
    def test_create_tasks_one_server_per_endpoint(self, mock, _):
        server_to_writer = {
            "AuthServer": "writer_1",
            "TelephonyServer": "writer_3",
            "TrustMonitorServer": "writer_4",
            "ActivityServer": "writer_5",
        }
        config = {
            "dls_settings": {
                "proxy": {"proxy_server": "test.com", "proxy_port": 1234},
            },
            "account": {
                "ikey": "a",
                "skey": "a",
                "hostname": "a",
                "endpoint_server_mappings": [
                    {"endpoints": ["auth"], "server": "AuthServer"},
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
            call("auth", "writer_1", "duo_admin"),
            call("telephony", "writer_3", "duo_admin"),
            call("trustmonitor", "writer_4", "duo_admin"),
            call("activity", "writer_5", "duo_admin"),
        ]

        self.assertEqual(mock.call_count, 4)
        mock.assert_has_calls(calls, any_order=True)
