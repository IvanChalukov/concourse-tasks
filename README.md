# Concourse Exercises

This repository contains solutions to six different exercises, each separated into branches. Below is a links to each exercise:
- [Exercise 1 – Start Concourse on Your Local System](https://github.com/IvanChalukov/concourse-tasks/tree/task-1)
- [Exercise 2 – Create a GitHub repo and script](https://github.com/IvanChalukov/concourse-tasks/tree/task-2)
- [Exercise 3 – Add a second resource to your pipeline](https://github.com/IvanChalukov/concourse-tasks/tree/task-3)
- [Exercise 4 – Build a custom Docker image.](https://github.com/IvanChalukov/concourse-tasks/tree/task-4)
- [Exercise 5 – Extend your script](https://github.com/IvanChalukov/concourse-tasks/tree/task-5)
- [Exercise 6 – Troubleshooting](https://github.com/IvanChalukov/concourse-tasks/tree/task-6)
- [Translate Bash Script to Python](https://github.com/IvanChalukov/concourse-tasks/tree/sh-to-py)

## Notes:
1. Setup: 
```sh
fly -t tutorial set-pipeline -p hello-sap -c hello-sap.yaml 
fly -t tutorial unpause-pipeline -p hello-sap
fly -t tutorial trigger-job --job hello-sap/hello-sap-job --watch
```

## Challanges
1. Default configuration for concourse does not work for M1, M2 MacOS 
```sh
run check: find or create container on worker bd02b84ce469: starting task: new task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: waiting for init preliminary setup: read init-p: connection reset by peer: unknown
```

**Solution**:   
CONCOURSE_WORKER_RUNTIME: "houdini" in docker-compose for M1, M2 

2. Cannot clone repository in local setup of concourse
```
Cloning into '/tmp/build/get'...
fatal: detected dubious ownership in repository at '/tmp/build/get'
To add an exception for this directory, call:

        git config --global --add safe.directory /tmp/build/get
failed
```

**Solution**:   
```yaml
git_config:
- name: safe.directory
    value: /tmp/build/get
```

3. Setup exact docker image version

**Solution**:   
```yaml
image_resource:
    source:
        repository: python
        tag: 3.11-alpine
    type: registry-image
```

4. Commit and push to repository

**Solution**:   
I needed to set up private key authentication for updating the GitHub repository. Additionally, I had to configure the following settings before making any commits:
```sh
git config --global --add safe.directory "*"
git config --global user.email "ichalukov@gmail.com"
git config --global user.name "Ivan Chalakov"
```

5. How to store already greeted people

**Solution**:   
I decide to use file stored in this repository in branch `task-6`. File is updated by pipeline for every new person added in `personas.json`.
tees
