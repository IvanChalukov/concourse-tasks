import time
import os.path
import sys
import logging
from typing import List

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def check_arguments():
    """Check if directory name is provided as argument."""
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        logger.error(f"Usage: {sys.argv[0]} <directory>")
        sys.exit(1)


def initialize_state_file(directory: str) -> str:
    """
    Initialize state file in given directory.
    :param directory: Directory path
    :return: path to the state file
    """
    state_filename = "state.txt"
    state_file_path = os.path.join(directory, state_filename)
    if not os.path.isfile(state_file_path):
        open(state_file_path, "a").close()
        logger.info("Initialized state file: {}".format(state_file_path))

    return state_file_path


def check_running_time(start_time: float):
    """
    Check if the script has been running for more than 15 minutes.
    :param start_time: The time when script is started.
    """
    current_time = time.time()
    if current_time - start_time > 900:
        logger.error("Script has been running for more than 15 minutes. Exiting...")
        sys.exit(1)


def get_uploaded_files(state_file_path: str):
    """Read the state file and return a list of files already uploaded."""
    try:
        with open(state_file_path) as f:
            files_uploaded = [line.strip() for line in f]
            logger.info("Successfully retrieved the list of files that have already been uploaded.")
            return files_uploaded
    except FileNotFoundError:
        logger.error("State file not found: {}".format(state_file_path))
        return []


def upload_file(s3_client, file_path: str, bucket_name: str) -> bool:
    """
    Upload a file to the specified S3 bucket.
    :param s3_client: Boto Service client instance
    :param file_path: Path to the file to be uploaded
    :param bucket_name: Name of the S3 bucket
    :return: True if upload is successful, False otherwise
    """
    try:
        file_name = os.path.basename(file_path)
        s3_client.upload_file(file_path, bucket_name, file_name)
        logger.info(f"Uploaded file: {file_path} to bucket: {bucket_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to upload {file_path}: {e}")
        return False


def retrieve_bucket(s3_client, bucket_name: str) -> List:
    """
    Retrieve the list of objects and their last modified dates in the specified S3 bucket.
    :param s3_client: Boto Service client instance
    :param bucket_name: Name of the S3 bucket
    """
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' not in response:
            logger.info(f"The bucket {bucket_name} is empty.")
            return []

        bucket_info = [(obj['Key'], f"LastModified: {obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')}") for obj in
                       response['Contents']]
        return bucket_info
    except Exception as e:
        logger.error(f"Failed to retrieve bucket {bucket_name}: {e}")
        return []


def update_state_file(file_name, state_file):
    """Add the uploaded file name to the state file."""
    with open(state_file, 'a') as f:
        f.write(file_name + '\n')
        logger.info("Updated state file with file: {}".format(file_name))


def main():
    check_arguments()
    state_file_path = initialize_state_file('./')
    dir_name = sys.argv[1]
    # Consider reading of aws_access_key_id, aws_secret_access_key, aws_region from env vars
    # instead of .aws/credentials file
    s3 = boto3.client('s3')
    bucket_name = "candidatetask"

    start_time = time.time()
    while True:
        check_running_time(start_time)
        new_files_uploaded = False
        uploaded_files = get_uploaded_files(state_file_path)

        for file_name in os.listdir(dir_name):
            if file_name in uploaded_files:
                continue

            file_path = os.path.join(dir_name, file_name)
            if not os.path.isfile(file_path):
                continue

            if upload_file(s3, file_name, bucket_name):
                update_state_file(file_name, state_file_path)
                new_files_uploaded = True

        if not new_files_uploaded:
            logger.info("No new files to upload.")
        else:
            logger.info(
                f"New files uploaded to {bucket_name}. Current bucket contents: {retrieve_bucket(s3, bucket_name)}")

        time.sleep(10)


if __name__ == "__main__":
    main()
