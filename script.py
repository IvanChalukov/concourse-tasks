import boto3
import time
import os.path
import sys
import logging
from typing import List


logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def parse_arguments():
    """
    Parse command-line arguments and return the directory name.
    :return: Directory name
    """
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        logger.error(f"Usage: {sys.argv[0]} <directory>")
        sys.exit(1)

    return sys.argv[1]


def initialize_state_file(directory: str) -> str:
    """
    Initialize state file in given directory.
    :param directory: Directory path where to store state.txt file
    :return: Full path to the state file
    """
    state_filename = "state.txt"
    state_file_path = os.path.join(directory, state_filename)
    if not os.path.isfile(state_file_path):
        open(state_file_path, "a").close()
        logger.info(f"Initialized state file: {state_file_path}")

    return state_file_path


def check_elapsed_time(start_time: float):
    """
    Check if the script has been running for more than 15 minutes.
    :param start_time: The time when script is started.
    """
    current_time = time.time()
    if current_time - start_time > 900:
        logger.error("Script has been running for more than 15 minutes. Exiting...")
        sys.exit(1)


def get_uploaded_files(state_file_path: str) -> List[str]:
    """
    Read the state file and return a list of files already uploaded.
    :param state_file_path: The path to the state file storing information about previously uploaded files.
    :return: A list of file names that have already been uploaded.
    """
    try:
        with open(state_file_path) as f:
            files_uploaded = [line.strip() for line in f]
            logger.info("Successfully read the list of files from the state file.")
            return files_uploaded
    except FileNotFoundError:
        logger.error(f"State file not found: {state_file_path}")
        return []


def upload_file(s3_client: boto3.client, file_path: str, bucket_name: str) -> bool:
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


def retrieve_bucket(s3_client: boto3.client, bucket_name: str) -> List:
    """
    Retrieve the list of objects and their last modified dates in the specified S3 bucket.
    :param s3_client: Boto Service client instance
    :param bucket_name: Name of the S3 bucket
    :return: A list of objects in the S3 bucket
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


def update_state_file(file_path: str, state_file: str):
    """
    Add the uploaded file name to the state file.
    :param file_path: The path to the file to be added to the state file.
    :param state_file: The path to the state file where the file name will be added.
    """
    with open(state_file, 'a') as f:
        f.write(file_path + '\n')
        logger.info(f"Updated state file with file: {file_path}")


def process_files(state_file_path: str, dir_name: str, bucket_name: str, s3_client: boto3.client) -> bool:
    """
    Process files in the specified directory for uploading to the S3 bucket.
    :param state_file_path: The path to the state file storing information about previously uploaded files.
    :param dir_name: The directory containing the files to be processed.
    :param bucket_name: The name of the S3 bucket where files will be uploaded.
    :param s3_client: The Boto3 S3 client instance.
    :return: True if new files were uploaded during the process, False otherwise.
    """
    new_files_uploaded = False
    uploaded_files = get_uploaded_files(state_file_path)

    for file_name in os.listdir(dir_name):
        file_path = os.path.join(dir_name, file_name)
        if not os.path.isfile(file_path) or file_path in uploaded_files:
            continue

        if upload_file(s3_client, file_path, bucket_name):
            update_state_file(file_path, state_file_path)
            new_files_uploaded = True

    return new_files_uploaded


def main():
    dir_name = parse_arguments()
    state_file_path = initialize_state_file(os.getcwd())
    s3 = boto3.client('s3')
    bucket_name = "candidatetask"

    start_time = time.time()
    while True:
        new_files_uploaded = process_files(state_file_path, dir_name, bucket_name, s3)

        if not new_files_uploaded:
            logger.info("No new files to upload.")
        else:
            logger.info(
                f"New files uploaded to {bucket_name}. Current bucket contents: {retrieve_bucket(s3, bucket_name)}")

        check_elapsed_time(start_time)
        time.sleep(10)


if __name__ == "__main__":
    main()
