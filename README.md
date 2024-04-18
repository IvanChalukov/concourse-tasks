# Concourse Exercises
Translate Bash Script to Python

### Prerequisite
1. Make sure to have installed python and pip
2. Install script dependencies
```sh
pip install -r requirements.txt
```
3. Setup AWS credentials in `.aws/credentials` file as follows:
```
[default]
aws_access_key_id=<add_aws_access_key_id>
aws_secret_access_key=<add_aws_secret_access_key>
aws_region=<add_aws_region>
```


### Start script
```sh
python script.py <path_to_dir>
```

### Run unittests
```sh
python -m unittest tests_script.py  
```

### Run unittests and coverage report
1. Make sure to install `coverage`:
```sh
pip install coverage 
```

2. Run tests with coverage report
```sh
python -m coverage run --source=. -m unittest discover && coverage report --show-missing --omit=tests_script.py
```

### Notes
1. Consider reading of aws_access_key_id, aws_secret_access_key, aws_region and bucket_name from env vars instead of .aws/credentials file
2. Extract s3 client as class to simplify current file
3. Move check_elapsed_time to bottom of while loop. It make easier to test and does not affect program flow
4. Is it possible to use ArgumentParser. This will change start command to: python script.py [--directory, -d] <path_to_dir>
5. Add new argument to script to allow changing of log-level on script startup(ex. --log-level DEBUG). This will lead to revisiting current logs.

