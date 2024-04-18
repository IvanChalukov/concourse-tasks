import datetime
import logging
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

from dateutil.tz import tzutc

from script import check_arguments, initialize_state_file, check_elapsed_time, get_uploaded_files, upload_file, \
    retrieve_bucket, update_state_file, main, process_files


class TestScript(unittest.TestCase):
    def setUp(self):
        self.script_name = 'script_name.py'
        self.tests_dir = 'tests_dir'

    @patch('script.os.path.isdir', return_value=True)
    def test_valid_directory(self, mock_isdir):
        sys.argv = [self.script_name, self.tests_dir]
        check_arguments()

        self.assertEqual(logging.getLogger(__name__).hasHandlers(), False)

    @patch('script.logger')
    def test_invalid_directory(self, mock_logger):
        sys.argv = [self.script_name, 'invalid_directory']
        with self.assertRaises(SystemExit) as cm:
            check_arguments()

        self.assertEqual(cm.exception.code, 1)
        mock_logger.error.assert_called_once_with(f"Usage: {self.script_name} <directory>")

    @patch('script.logger')
    def test_no_directory_name(self, mock_logger):
        sys.argv = [self.script_name]
        with self.assertRaises(SystemExit) as cm:
            check_arguments()

        self.assertEqual(cm.exception.code, 1)
        mock_logger.error.assert_called_once_with(f"Usage: {self.script_name} <directory>")

    @patch('script.logger')
    def test_multiple_arguments(self, mock_logger):
        sys.argv = [self.script_name, 'dir1', 'arg2']
        with self.assertRaises(SystemExit) as cm:
            check_arguments()

        self.assertEqual(cm.exception.code, 1)
        mock_logger.error.assert_called_once_with(f"Usage: {self.script_name} <directory>")

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
        mock_path.isfile.return_value = True

        initialize_state_file(self.tests_dir)

        mock_open.assert_not_called()
        mock_logger.info.assert_not_called()

    @patch('script.sys.exit')
    @patch('script.logger')
    @patch('script.time.time')
    def test_check_elapsed_time_less_than_15_minutes(self, mock_current_time, mock_logger, mock_exit):
        start_time = 1000
        mock_current_time.return_value = start_time + 600
        check_elapsed_time(start_time)

        mock_exit.assert_not_called()
        mock_logger.assert_not_called()

    @patch('script.sys.exit')
    @patch('script.logger')
    @patch('script.time.time')
    def test_check_elapsed_time_more_than_15_minutes(self, mock_current_time, mock_logger, mock_exit):
        start_time = 1000
        mock_current_time.return_value = start_time + 1200

        check_elapsed_time(start_time)

        mock_logger.error.assert_called_once_with("Script has been running for more than 15 minutes. Exiting...")
        mock_exit.assert_called_once_with(1)

    @patch('script.open', create=True)
    @patch('script.logger')
    @patch('script.os.path.isfile', return_value=True)
    def test_get_uploaded_files_success(self, mock_isfile, mock_logger, mock_open):
        state_file_path = 'state.txt'
        get_uploaded_files(state_file_path)
        mock_open.assert_called_once_with(state_file_path)
        mock_logger.info.assert_called_once_with(
            "Successfully retrieved the list of files that have already been uploaded.")

    @patch('script.open', side_effect=FileNotFoundError)
    @patch('script.logger')
    @patch('script.os.path.isfile', return_value=False)
    def test_get_uploaded_files_file_not_found(self, mock_isfile, mock_logger, mock_open):
        state_file_path = 'state.txt'
        uploaded_files = get_uploaded_files(state_file_path)
        self.assertEqual(uploaded_files, [])
        mock_logger.error.assert_called_once_with(f"State file not found: {state_file_path}")

    @patch('script.logger')
    @patch('script.os.path.basename', return_value='file.txt')
    def test_upload_file_success(self, mock_basename, mock_logger):
        s3_client = MagicMock()
        s3_client.upload_file.return_value = None

        mocked_file_path = '/path/to/file.txt'
        mocked_bucket_name = 'test_bucket'

        result = upload_file(s3_client, mocked_file_path, mocked_bucket_name)

        self.assertTrue(result)
        s3_client.upload_file.assert_called_once_with(mocked_file_path, mocked_bucket_name, 'file.txt')
        mock_logger.info.assert_called_once_with(f"Uploaded file: {mocked_file_path} to bucket: {mocked_bucket_name}")

    @patch('script.logger')
    @patch('script.os.path.basename', return_value='file.txt')
    def test_upload_file_failure(self, mock_basename, mock_logger):
        s3_client = MagicMock()
        s3_client.upload_file.side_effect = Exception('Upload failed')

        mocked_file_path = '/path/to/file.txt'
        mocked_bucket_name = 'test_bucket'

        result = upload_file(s3_client, mocked_file_path, mocked_bucket_name)

        self.assertFalse(result)
        s3_client.upload_file.assert_called_once_with(mocked_file_path, mocked_bucket_name, 'file.txt')
        mock_logger.error.assert_called_once_with(f"Failed to upload {mocked_file_path}: Upload failed")

    @patch('script.logger')
    def test_retrieve_bucket_success_empty_content(self, mock_logger):
        # Mocking boto3 client
        s3_client = MagicMock()
        s3_client.list_objects_v2.return_value = {}

        bucket_name = 'test_bucket'

        result = retrieve_bucket(s3_client, bucket_name)

        self.assertEqual(result, [])
        s3_client.list_objects_v2.assert_called_once_with(Bucket=bucket_name)
        mock_logger.info.assert_called_once_with(f"The bucket {bucket_name} is empty.")

    @patch('script.logger')
    def test_retrieve_bucket_success_content(self, mock_logger):
        s3_client = MagicMock()
        s3_client.list_objects_v2.return_value = {
            'ResponseMetadata': {'RequestId': 'testRequestId', 'RetryAttempts': 1}, 'Contents': [
                {'Key': 'Concourse_ID_1011.md',
                 'LastModified': datetime.datetime(2024, 4, 18, 14, 26, 46, tzinfo=tzutc()),
                 'ETag': '"eefd009945205ed786a9e61274a316e8"', 'Size': 8407, 'StorageClass': 'STANDARD'}],
            'Name': 'candidatetask', 'Prefix': '', 'MaxKeys': 1000, 'EncodingType': 'url', 'KeyCount': 1}

        bucket_name = 'test_bucket'

        result = retrieve_bucket(s3_client, bucket_name)

        self.assertEqual(result, [('Concourse_ID_1011.md', 'LastModified: 2024-04-18 14:26:46')])
        s3_client.list_objects_v2.assert_called_once_with(Bucket=bucket_name)

    @patch('script.logger')
    def test_retrieve_bucket_failure(self, mock_logger):
        s3_client = MagicMock()
        s3_client.list_objects_v2.side_effect = Exception('List files failed')

        bucket_name = 'test_bucket'

        result = retrieve_bucket(s3_client, bucket_name)

        self.assertEqual(result, [])
        s3_client.list_objects_v2.assert_called_once_with(Bucket=bucket_name)
        mock_logger.error.assert_called_once_with(f"Failed to retrieve bucket {bucket_name}: List files failed")

    @patch('script.open', create=True)
    @patch('script.logger')
    def test_update_state_file(self, mock_logger, mock_open):
        mocked_file_name = "test_file.md"
        mocked_state_file = 'state.txt'

        update_state_file(mocked_file_name, mocked_state_file)
        mock_open.assert_called_once_with(mocked_state_file, 'a')
        mock_logger.info.assert_called_once_with(f"Updated state file with file: {mocked_file_name}")

    @patch('script.get_uploaded_files', return_value=['/directory/file1.txt'])
    @patch('os.listdir', return_value=['file1.txt', 'file2.txt', 'file3.txt'])
    @patch('script.os.path.isfile', return_value=True)
    @patch('script.upload_file', return_value=True)
    @patch('script.update_state_file')
    def test_process_files_with_new_files_uploaded(self, mock_update_state_file, mock_upload_file, mock_isfile,
                                                   mock_listdir, mock_get_uploaded_files):
        mocked_state_file_path = 'state.txt'
        mocked_dir_name = '/directory'
        mocked_bucket_name = 'my_bucket'
        mocked_s3_client = MagicMock()

        result = process_files(mocked_state_file_path, mocked_dir_name, mocked_bucket_name, mocked_s3_client)

        self.assertTrue(result)
        mock_get_uploaded_files.assert_called_once_with(mocked_state_file_path)
        mock_listdir.assert_called_once_with(mocked_dir_name)
        mock_isfile.assert_called()
        mock_upload_file.assert_any_call(mocked_s3_client, '/directory/file2.txt', mocked_bucket_name)
        mock_upload_file.assert_any_call(mocked_s3_client, '/directory/file3.txt', mocked_bucket_name)
        mock_update_state_file.assert_any_call('/directory/file2.txt', mocked_state_file_path)
        mock_update_state_file.assert_any_call('/directory/file3.txt', mocked_state_file_path)

    @patch('script.get_uploaded_files', return_value=['/directory/file1.txt', '/directory/file2.txt'])
    @patch('os.listdir', return_value=['file1.txt', 'file2.txt'])
    @patch('script.os.path.isfile', return_value=True)
    @patch('script.upload_file', return_value=False)
    @patch('script.update_state_file')
    def test_process_files_with_no_new_files_uploaded(self, mock_update_state_file, mock_upload_file, mock_isfile,
                                                      mock_listdir, mock_get_uploaded_files):
        state_file_path = 'state.txt'
        dir_name = '/directory'
        bucket_name = 'my_bucket'
        s3_client = MagicMock()

        result = process_files(state_file_path, dir_name, bucket_name, s3_client)

        self.assertFalse(result)
        mock_get_uploaded_files.assert_called_once_with(state_file_path)
        mock_listdir.assert_called_once_with(dir_name)
        mock_upload_file.assert_not_called()
        mock_update_state_file.assert_not_called()

    @patch('script.sys.argv', ['script.py', 'test_directory'])
    @patch('script.check_elapsed_time', side_effect=SystemExit)
    @patch('script.boto3.client')
    @patch('script.time.time')
    @patch('script.check_arguments')
    @patch('script.initialize_state_file')
    @patch('script.process_files', return_value=False)
    @patch('script.retrieve_bucket')
    @patch('script.logger')
    def test_main_no_new_files(self, mock_logger, mock_retrieve_bucket, mock_process_files, mock_initialize_state_file,
                               mock_check_arguments, mock_time, mock_boto3, mock_check_elapsed_time):
        with self.assertRaises(SystemExit) as cm:
            main()

        mock_logger.info.assert_called_once_with("No new files to upload.")

    @patch('script.sys.argv', ['script.py', 'test_directory'])
    @patch('script.check_elapsed_time', side_effect=SystemExit)
    @patch('script.boto3.client')
    @patch('script.time.time')
    @patch('script.check_arguments')
    @patch('script.initialize_state_file')
    @patch('script.process_files', return_value=True)
    @patch('script.retrieve_bucket', return_value='mocked_bucket_contents')
    @patch('script.logger')
    def test_main_with_new_files(self, mock_logger, mock_retrieve_bucket, mock_process_files,
                                 mock_initialize_state_file, mock_check_arguments, mock_time, mock_boto3,
                                 mock_check_elapsed_time):
        with self.assertRaises(SystemExit) as cm:
            main()

        mock_retrieve_bucket.assert_called_once()
        mock_logger.info.assert_called_once_with(
            "New files uploaded to candidatetask. Current bucket contents: mocked_bucket_contents")


if __name__ == '__main__':
    unittest.main()
