from unittest import TestCase

from duologsync.consumer.cef import _construct_extension


class TestCef(TestCase):

    def test_construct_extension_always_returns_rt_as_milliseconds(self):

        ts_test_params = [(1631542762, 'rt=1631542762000'), (1631542762123, 'rt=1631542762123')]

        for param1, param2 in ts_test_params:
            with self.subTest():

                keys_to_label = {
                    ('ts',): {'name': 'rt', 'is_custom': False}
                }
                mock_log = {
                    'ts': param1
                }

                response = _construct_extension(mock_log, keys_to_label)

                self.assertEqual(param2, response)
