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
