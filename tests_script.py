import logging
import os
import sys
import unittest
from unittest.mock import patch

from script import check_arguments, initialize_state_file, check_running_time


class TestScript(unittest.TestCase):
    def setUp(self):
        self.script_name = 'script_name.py'
        self.tests_dir = 'tests_dir'

    def test_valid_directory(self):
        sys.argv = [self.script_name, self.tests_dir]
        check_arguments()

        self.assertEqual(logging.getLogger(__name__).hasHandlers(), False)

    def test_invalid_directory(self):
        sys.argv = [self.script_name, 'invalid_directory']
        with self.assertRaises(SystemExit) as cm:
            check_arguments()

        self.assertEqual(cm.exception.code, 1)

    def test_no_directory_name(self):
        sys.argv = [self.script_name]
        with self.assertRaises(SystemExit) as cm:
            check_arguments()

        self.assertEqual(cm.exception.code, 1)

    def test_multiple_arguments(self):
        sys.argv = [self.script_name, 'dir1', 'arg2']
        with self.assertRaises(SystemExit) as cm:
            check_arguments()

        self.assertEqual(cm.exception.code, 1)

    @patch('script.os.path')
    @patch('script.open', create=True)
    @patch('script.logger')
    def test_initialize_state_file_not_exist(self, mock_logger, mock_open, mock_path):
        mock_path.isfile.return_value = False

        initialize_state_file(self.tests_dir)

        mock_open.assert_called_once_with(os.path.join(self.tests_dir, "state.txt"), "a")
        mock_logger.info.assert_called_once_with(
            "Initialized state file: {}".format(os.path.join(self.tests_dir, "state.txt")))

    @patch('script.os.path')
    @patch('script.open', create=True)
    @patch('script.logger')
    def test_initialize_state_file_exist(self, mock_logger, mock_open, mock_path):
        directory = "/tests_dir"
        mock_path.isfile.return_value = True

        initialize_state_file(directory)

        mock_open.assert_not_called()
        mock_logger.info.assert_not_called()

    @patch('script.sys.exit')
    @patch('script.logger')
    @patch('script.time.time')
    def test_check_running_time_less_than_15_minutes(self, mock_current_time, mock_logger, mock_exit):
        start_time = 1000
        mock_current_time.return_value = start_time + 600
        check_running_time(start_time)

        mock_exit.assert_not_called()
        mock_logger.assert_not_called()

    @patch('script.sys.exit')
    @patch('script.logger')
    @patch('script.time.time')
    def test_check_running_time_less_than_15_minutes(self, mock_current_time, mock_logger, mock_exit):
        start_time = 1000
        mock_current_time.return_value = start_time + 1200

        check_running_time(start_time)

        mock_logger.error.assert_called_once_with("Script has been running for more than 15 minutes. Exiting...")
        mock_exit.assert_called_once_with(1)


if __name__ == '__main__':
    unittest.main()
