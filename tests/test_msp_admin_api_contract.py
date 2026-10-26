"""Offline tests for Duo's documented Admin API subaccount contract.

Source: https://duo.com/docs/adminapi#subaccounts

Duo requires a parent Admin API integration to discover subaccounts with
``POST /accounts/v1/account/list``. Requests made for a returned subaccount
must use that subaccount's ``api_hostname`` and include its ``account_id`` in
the request parameters.
"""

import asyncio
import json
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, patch
from urllib.parse import parse_qs, urlsplit

import duo_client

from duologsync.app import create_consumer_producer_pair
from duologsync.config import Config
from duologsync.consumer.activity_consumer import ActivityConsumer
from duologsync.consumer.authlog_consumer import AuthlogConsumer
from duologsync.consumer.telephony_consumer import TelephonyConsumer
from duologsync.producer.activity_producer import ActivityProducer
from duologsync.producer.authlog_producer import AuthlogProducer
from duologsync.producer.telephony_producer import TelephonyProducer
from duologsync.program import Program


ACCOUNT_ID = "DA9VZOC5X63I2W72NRP9"
API_HOSTNAME = "api-abcd1234.duosecurity.com"
MINTIME = 1_725_000_000_000


def decode_params(params):
    """Decode Duo's normalized byte parameters for readable assertions."""

    decoded = {}
    for key, values in params.items():
        decoded_key = key.decode("utf-8") if isinstance(key, bytes) else key
        decoded[decoded_key] = [
            value.decode("utf-8") if isinstance(value, bytes) else value
            for value in values
        ]
    return decoded


class TestMspAdminApiRequestContract(TestCase):
    def setUp(self):
        Config.set_config(
            {
                "dls_settings": {
                    "checkpointing": {"enabled": False, "directory": "/tmp"}
                },
                "account": {"is_msp": True},
            }
        )

    def tearDown(self):
        Config._config = None
        Config._config_is_set = False

    @staticmethod
    def call_log_api(producer):
        event_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(event_loop)
            return event_loop.run_until_complete(producer.call_log_api())
        finally:
            asyncio.set_event_loop(None)
            event_loop.close()

    def assert_child_request(self, api_call, expected_path):
        api_call.assert_called_once()
        request = api_call.call_args.kwargs

        self.assertEqual(request["method"], "GET")
        self.assertEqual(request["path"], expected_path)

        params = decode_params(request["params"])
        self.assertEqual(params["account_id"], [ACCOUNT_ID])
        self.assertEqual(params["mintime"], [str(MINTIME)])
        self.assertEqual(params["limit"], ["1000"])
        self.assertEqual(params["sort"], ["ts:asc"])
        self.assertIn("maxtime", params)

    @patch(
        "duologsync.producer.producer.get_log_offset",
        return_value=MINTIME,
    )
    def test_authentication_request_contains_subaccount_id(self, _):
        api_call = Mock(return_value={"authlogs": [], "metadata": {}})
        producer = AuthlogProducer(
            api_call,
            asyncio.Queue(),
            child_account_id=ACCOUNT_ID,
            url_path="/admin/v2/logs/authentication",
        )

        self.call_log_api(producer)

        self.assert_child_request(api_call, "/admin/v2/logs/authentication")

    @patch(
        "duologsync.producer.producer.get_log_offset",
        return_value=MINTIME,
    )
    def test_telephony_request_contains_subaccount_id(self, _):
        api_call = Mock(return_value={"items": [], "metadata": {}})
        producer = TelephonyProducer(
            api_call,
            asyncio.Queue(),
            child_account_id=ACCOUNT_ID,
            url_path="/admin/v2/logs/telephony",
        )

        self.call_log_api(producer)

        self.assert_child_request(api_call, "/admin/v2/logs/telephony")

    @patch(
        "duologsync.producer.producer.get_log_offset",
        return_value=MINTIME,
    )
    def test_activity_request_contains_subaccount_id(self, _):
        api_call = Mock(return_value={"items": [], "metadata": {}})
        producer = ActivityProducer(
            api_call,
            asyncio.Queue(),
            child_account_id=ACCOUNT_ID,
            url_path="/admin/v2/logs/activity",
        )

        self.call_log_api(producer)

        self.assert_child_request(api_call, "/admin/v2/logs/activity")

    @patch("duologsync.producer.producer.datetime")
    @patch(
        "duologsync.producer.producer.get_log_offset",
        return_value=MINTIME,
    )
    def test_log_query_respects_documented_two_minute_availability_delay(
        self, _, datetime_class
    ):
        current_time = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
        datetime_class.now.return_value = current_time
        producer = TelephonyProducer(Mock(), asyncio.Queue())

        params = decode_params(producer.get_admin_api_log_parameters())

        expected_maxtime = int(current_time.timestamp() * 1000) - 120_000
        self.assertEqual(params["maxtime"], [str(expected_maxtime)])

    @patch(
        "duologsync.producer.producer.get_log_offset",
        return_value=MINTIME,
    )
    def test_duo_client_signs_child_hostname_and_account_id_without_network(self, _):
        admin = duo_client.Admin(
            ikey="DIXXXXXXXXXXXXXXXXXX",
            skey="offline-test-secret",
            host=API_HOSTNAME,
        )
        response = Mock(status=200, reason="OK")
        response_data = json.dumps(
            {"stat": "OK", "response": {"items": [], "metadata": {}}}
        ).encode("utf-8")
        admin._make_request = Mock(return_value=(response, response_data))
        producer = TelephonyProducer(
            admin.json_api_call,
            asyncio.Queue(),
            child_account_id=ACCOUNT_ID,
            url_path="/admin/v2/logs/telephony",
        )

        self.call_log_api(producer)

        request = admin._make_request.call_args
        self.assertEqual(admin.host, API_HOSTNAME)
        self.assertEqual(request.args[0], "GET")
        self.assertEqual(
            urlsplit(request.args[1]).path,
            "/admin/v2/logs/telephony",
        )
        self.assertEqual(
            parse_qs(urlsplit(request.args[1]).query)["account_id"],
            [ACCOUNT_ID],
        )
        self.assertIn(b"Authorization", request.args[3])


class TestMspTaskContract(TestCase):
    def setUp(self):
        Config.set_config({"dls_settings": {"log_format": Config.JSON}})

    def tearDown(self):
        Config._config = None
        Config._config_is_set = False

    @patch("duologsync.app.asyncio.ensure_future", side_effect=lambda value: value)
    @patch("duologsync.app.AuthlogConsumer")
    @patch("duologsync.app.AuthlogProducer")
    def test_authentication_pair_preserves_subaccount_context(
        self, producer_class, consumer_class, _
    ):
        admin = Mock()
        writer = Mock()

        create_consumer_producer_pair(Config.AUTH, writer, admin, ACCOUNT_ID)
        log_queue = producer_class.call_args.args[1]

        producer_class.assert_called_once_with(
            admin.json_api_call,
            log_queue,
            child_account_id=ACCOUNT_ID,
            url_path="/admin/v2/logs/authentication",
        )
        consumer_class.assert_called_once_with(
            Config.JSON,
            log_queue,
            writer,
            ACCOUNT_ID,
        )

    @patch("duologsync.app.asyncio.ensure_future", side_effect=lambda value: value)
    @patch("duologsync.app.TelephonyConsumer")
    @patch("duologsync.app.TelephonyProducer")
    def test_telephony_pair_preserves_subaccount_context(
        self, producer_class, consumer_class, _
    ):
        admin = Mock()
        writer = Mock()

        create_consumer_producer_pair(Config.TELEPHONY, writer, admin, ACCOUNT_ID)
        log_queue = producer_class.call_args.args[1]

        producer_class.assert_called_once_with(
            admin.json_api_call,
            log_queue,
            child_account_id=ACCOUNT_ID,
            url_path="/admin/v2/logs/telephony",
        )
        consumer_class.assert_called_once_with(
            Config.JSON,
            log_queue,
            writer,
            ACCOUNT_ID,
        )

    @patch("duologsync.app.asyncio.ensure_future", side_effect=lambda value: value)
    @patch("duologsync.app.ActivityConsumer")
    @patch("duologsync.app.ActivityProducer")
    def test_activity_pair_preserves_subaccount_context(
        self, producer_class, consumer_class, _
    ):
        admin = Mock()
        writer = Mock()

        create_consumer_producer_pair(Config.ACTIVITY, writer, admin, ACCOUNT_ID)
        log_queue = producer_class.call_args.args[1]

        producer_class.assert_called_once_with(
            admin.json_api_call,
            log_queue,
            child_account_id=ACCOUNT_ID,
            url_path="/admin/v2/logs/activity",
        )
        consumer_class.assert_called_once_with(
            Config.JSON,
            log_queue,
            writer,
            ACCOUNT_ID,
        )


class TestMspCheckpointContract(TestCase):
    def setUp(self):
        Config.set_config(
            {
                "dls_settings": {
                    "checkpointing": {"enabled": True, "directory": "/tmp"}
                }
            }
        )

    def tearDown(self):
        Config._config = None
        Config._config_is_set = False
        Program._running = True

    @patch(
        "duologsync.producer.producer.get_log_offset",
        return_value=MINTIME,
    )
    def test_all_msp_producers_read_subaccount_specific_checkpoints(
        self, get_log_offset
    ):
        queue = asyncio.Queue()

        AuthlogProducer(
            Mock(),
            queue,
            child_account_id=ACCOUNT_ID,
            url_path="/admin/v2/logs/authentication",
        )
        TelephonyProducer(Mock(), queue, child_account_id=ACCOUNT_ID)
        ActivityProducer(Mock(), queue, child_account_id=ACCOUNT_ID)

        self.assertEqual(
            [call.args[3] for call in get_log_offset.call_args_list],
            [ACCOUNT_ID, ACCOUNT_ID, ACCOUNT_ID],
        )

    def test_all_msp_consumers_write_subaccount_specific_checkpoints(self):
        queue = asyncio.Queue()
        writer = Mock()
        consumers = [
            AuthlogConsumer(Config.JSON, queue, writer, ACCOUNT_ID),
            TelephonyConsumer(Config.JSON, queue, writer, ACCOUNT_ID),
            ActivityConsumer(Config.JSON, queue, writer, ACCOUNT_ID),
        ]

        self.assertEqual(
            [consumer.child_account_id for consumer in consumers],
            [ACCOUNT_ID, ACCOUNT_ID, ACCOUNT_ID],
        )

    @patch("duologsync.consumer.consumer.Consumer.update_log_checkpoint")
    @patch(
        "duologsync.consumer.consumer.Producer.get_log_offset",
        return_value="next-offset",
    )
    def test_all_msp_consumers_add_subaccount_id_to_serialized_events(self, *_):
        consumer_classes = [AuthlogConsumer, TelephonyConsumer, ActivityConsumer]

        for consumer_class in consumer_classes:
            with self.subTest(consumer=consumer_class.__name__):
                Program._running = True
                writer = Mock()

                async def capture_write(data, _):
                    writer.serialized_event = json.loads(data.decode("utf-8"))
                    Program._running = False

                writer.write = AsyncMock(side_effect=capture_write)
                event_loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(event_loop)
                    queue = asyncio.Queue()
                    queue.put_nowait([{"timestamp": 1}])
                    consumer = consumer_class(
                        Config.JSON,
                        queue,
                        writer,
                        ACCOUNT_ID,
                    )
                    event_loop.run_until_complete(consumer.consume())
                finally:
                    asyncio.set_event_loop(None)
                    event_loop.close()

                self.assertEqual(
                    writer.serialized_event["child_account_id"],
                    ACCOUNT_ID,
                )
