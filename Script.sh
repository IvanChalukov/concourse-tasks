#!/bin/bash

# Check if directory name is provided as argument
if [ $# -ne 1 ] || [ ! -d "$1" ]
then
  echo "Usage: $0 <directory>"
  exit 1
fi

# Define your directory and S3 bucket
DIR_NAME=$1
BUCKET_NAME="candidatetask"

# File to keep track of the last uploaded files
STATE_FILE="state.txt"

# If the state file doesn't exist, create an empty one
touch $STATE_FILE

# Store the start time
START=$(date +%s)

# Infinite loop - script will run until manually stopped
while :
do
  # Get the current time
  NOW=$(date +%s)

  # If the script has been running for more than 15 minutes, exit
  if (( NOW - START > 900 )); then
    echo "Script has been running for more than 15 minutes. Exiting..."
    exit 1
  fi

  # Initialize a flag to track if any new files have been uploaded
  new_files_uploaded=false

  # Loop over all files in the directory
  for file in "$DIR_NAME"/*
  do
    # Check if the file is already in the state file (already uploaded)
    if ! grep -qF "$file" "$STATE_FILE"
    then
      # If the file is not in the state file, upload it and add it to the state file
      aws s3 cp "$file" s3://$BUCKET_NAME
      if [ $? -eq 0 ]
      then
        echo "$file" >> $STATE_FILE
        new_files_uploaded=true
      else
        echo "Failed to upload $file" >&2
      fi
    fi
  done

  # If no new files have been uploaded, print a message.
  # Otherwise, print a message and display the current contents of the bucket.
  if [ $new_files_uploaded = false ]
  then
    echo "No new files to upload."
  else
    echo "New files uploaded to $BUCKET_NAME. Current bucket contents:"
    aws s3 ls s3://$BUCKET_NAME
  fi

  # Pause script execution for 30 seconds
  sleep 10
done