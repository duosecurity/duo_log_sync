from unittest import TestCase
from unittest.mock import Mock, patch

from duologsync.util import create_admin, get_subaccounts


class TestAdminApiClients(TestCase):
    @patch("duologsync.util.duo_client.Admin")
    def test_create_admin_configures_regular_account(self, mock_admin_class):
        admin = Mock()
        mock_admin_class.return_value = admin

        result = create_admin("ikey", "skey", "api.example.com")

        mock_admin_class.assert_called_once_with(
            ikey="ikey",
            skey="skey",
            host="api.example.com",
            user_agent="Duo Log Sync/2.4.1",
        )
        admin.set_proxy.assert_not_called()
        self.assertIs(result, admin)

    @patch("duologsync.util.duo_client.Admin")
    def test_create_admin_configures_child_hostname_and_proxy(self, mock_admin_class):
        admin = Mock()
        mock_admin_class.return_value = admin

        result = create_admin(
            "ikey",
            "skey",
            "api-child.example.com",
            proxy_server="proxy.example.com",
            proxy_port=8080,
        )

        mock_admin_class.assert_called_once_with(
            ikey="ikey",
            skey="skey",
            host="api-child.example.com",
            user_agent="Duo Log Sync/2.4.1",
        )
        admin.set_proxy.assert_called_once_with(host="proxy.example.com", port=8080)
        self.assertIs(result, admin)

    def test_get_subaccounts_uses_admin_api_subaccount_endpoint(self):
        admin = Mock()
        expected_subaccounts = [
            {"account_id": "DA123", "api_hostname": "api-child.example.com"}
        ]
        admin.json_api_call.return_value = expected_subaccounts

        result = get_subaccounts(admin)

        admin.json_api_call.assert_called_once_with(
            "POST", "/accounts/v1/account/list", {}
        )
        self.assertIs(result, expected_subaccounts)

    def test_get_subaccounts_rejects_incomplete_admin_api_response(self):
        admin = Mock()
        invalid_responses = [None, {}, [{"account_id": "DA123"}]]

        for invalid_response in invalid_responses:
            with self.subTest(response=invalid_response):
                admin.json_api_call.return_value = invalid_response

                with self.assertRaisesRegex(
                    ValueError, r"Admin API returned (an )?invalid"
                ):
                    get_subaccounts(admin)
