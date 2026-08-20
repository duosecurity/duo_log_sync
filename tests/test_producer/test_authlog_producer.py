import asyncio
from unittest import TestCase
from unittest.mock import Mock, patch

from duologsync.config import Config
from duologsync.producer.authlog_producer import AuthlogProducer


class TestAuthlogProducer(TestCase):
    def tearDown(self):
        Config._config = None
        Config._config_is_set = False

    @patch(
        "duologsync.producer.producer.get_log_offset",
        return_value=1_725_000_000_000,
    )
    def test_regular_account_uses_standard_admin_api_handler(self, _):
        Config.set_config(
            {
                "dls_settings": {
                    "checkpointing": {"enabled": False, "directory": "/tmp"}
                },
                "account": {"is_msp": False},
            }
        )
        api_call = Mock(return_value={"authlogs": [], "metadata": {}})
        event_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(event_loop)
            producer = AuthlogProducer(api_call, asyncio.Queue())
            result = event_loop.run_until_complete(producer.call_log_api())
        finally:
            asyncio.set_event_loop(None)
            event_loop.close()

        api_call.assert_called_once_with(
            api_version=2,
            mintime=1_725_000_000_000,
            next_offset=None,
            sort="ts:asc",
            limit="1000",
        )
        self.assertEqual(result, {"authlogs": [], "metadata": {}})
