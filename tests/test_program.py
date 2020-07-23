from unittest import TestCase
from unittest.mock import patch
from duologsync.program import Program

class TestConfig(TestCase):
    
    def tearDown(self):
        Program._running = True
        Program._logging_set = False

    def test_is_logging_set(self):
        self.assertEqual(Program.is_logging_set(), False)

        Program._logging_set = True

        self.assertEqual(Program.is_logging_set(), True)

    def test_is_running(self):
        self.assertEqual(Program.is_running(), True)

        Program._running = False

        self.assertEqual(Program.is_running(), False)

    def test_initiate_shutdown(self):
        self.assertEqual(Program._running, True)

        Program.initiate_shutdown('test')

        self.assertEqual(Program._running, False)
 
    def test_setup_logging_normal(self):
        filepath = 'logs.txt'

        Program.setup_logging(filepath)

        self.assertEqual(Program._logging_set, True)

    @patch('builtins.print')
    def test_log_without_logging_set(self, mock_print):
        Program.log('Oh no, logging has not been set!')

        mock_print.assert_called_once()

    @patch('logging.log')
    def test_log_with_logging_set(self, mock_log):
        Program._logging_set = True

        Program.log('Everything is A-Ok')

        mock_log.assert_called_once()
