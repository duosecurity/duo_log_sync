import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, patch

from duologsync.config import Config
from duologsync.producer.producer import Producer
from duologsync.program import Program, ProgramShutdownError


class TestProducerErrorHandling(TestCase):
    def setUp(self):
        self.producer = object.__new__(Producer)
        self.producer.log_type = Config.AUTH

    def tearDown(self):
        Config._config = None
        Config._config_is_set = False
        Program._running = True

    @patch("duologsync.producer.producer.Program.log")
    def test_timeout_is_logged_and_retried(self, mock_log):
        self.producer.handle_timeout_error_gracefully(
            TimeoutError("request timed out")
        )

        mock_log.assert_called_once()

    @patch("duologsync.producer.producer.Program.initiate_shutdown")
    @patch("duologsync.producer.producer.Program.log")
    @patch(
        "duologsync.producer.producer.restless_sleep", new_callable=AsyncMock
    )
    def test_produce_retries_timeout_without_shutting_down(
        self, _, __, mock_initiate_shutdown
    ):
        Config.set_config({"dls_settings": {"api": {"timeout": 120}}})
        event_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(event_loop)
            self.producer.log_offset = 1
            self.producer.mintime = None
            self.producer.log_queue = asyncio.Queue()
            self.producer.call_log_api = AsyncMock(
                side_effect=[TimeoutError("request timed out"), ProgramShutdownError()]
            )

            event_loop.run_until_complete(self.producer.produce())
        finally:
            asyncio.set_event_loop(None)
            event_loop.close()

        self.assertEqual(self.producer.call_log_api.await_count, 2)
        mock_initiate_shutdown.assert_not_called()

    @patch("duologsync.producer.producer.Program.log")
    def test_504_with_string_data_is_logged_and_retried(self, mock_log):
        error = RuntimeError("Received 504 Gateway Time-out")
        error.status = 504
        error.data = "upstream request timeout"

        result = self.producer.handle_runtime_error_gracefully(error)

        self.assertIsNone(result)
        mock_log.assert_called_once()

    def test_all_server_errors_and_rate_limits_are_retryable(self):
        retryable_statuses = [429, 500, 502, 503, 504, 599]

        for status in retryable_statuses:
            with self.subTest(status=status):
                self.assertTrue(Producer.eligible_for_retry(status))

    def test_client_errors_other_than_rate_limits_are_not_retryable(self):
        non_retryable_statuses = [None, 400, 401, 403, 404]

        for status in non_retryable_statuses:
            with self.subTest(status=status):
                self.assertFalse(Producer.eligible_for_retry(status))

    def test_non_retryable_error_with_dictionary_data_preserves_error_code(self):
        error = RuntimeError("Invalid integration key")
        error.status = 401
        error.data = {"code": 40001}

        result = self.producer.handle_runtime_error_gracefully(error)

        self.assertIn("error_code: 40001", result)
        self.assertIn("http_status_code: 401", result)
