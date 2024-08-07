# ai4os-demo-app

[![Build Status](https://jenkins.services.ai4os.eu/buildStatus/icon?job=AI4OS-hub/ai4os-demo-app/main)](https://jenkins.services.ai4os.eu/job/AI4OS-hub/job/ai4os-demo-app/job/main/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A _minimal_ toy application for demo and testing purposes.
It can serve as a reference implementation of current best practices in the project (mirroring the [DEEP template](https://github.com/ai4os/ai4-template)).

This demo module implements:
* **dummy inference**, ie. we return the same inputs we are fed. If some input is not fed we generate a default one.
* **dummy training**, ie. we sleep for some time and output some random monitoring metrics.

Samples for media files are provided in `./data`.

The two branches in this repo cover the two main usecases:
* [main](https://github.com/ai4os-hub/ai4os-demo-app/blob/main/ai4os_demo_app/api.py): this is a reference implementation on how to return a JSON response for `predict()`.
* [return-files](https://github.com/ai4os-hub/ai4os-demo-app/blob/return-files/ai4os_demo_app/api.py): this is a reference implementation on how to return non-JSON responses for `predict()`. This is particularly useful when returning:
     - long responses (that could better fit better in a `txt` file),
     - media files (eg. returning an image),
     - multiple files (for example returning an image and a text file at the same time, packing them into a zip file).

The `train()` function is common for both branches.

## Usage

To launch it, first install the package then run [deepaas](https://github.com/ai4os/DEEPaaS):
```bash
git clone https://github.com/ai4os-hub/ai4os-demo-app
cd ai4os-demo-app
pip install -e .
deepaas-run --listen-ip 0.0.0.0
```

To format the code using [Black](https://github.com/psf/black), run:
```bash
black ai4os_demo_app
```

## Project structure
```
│
├── Dockerfile             <- Describes main steps on integration of DEEPaaS API and
│                             ai4os_demo_app application in one Docker image
│
├── Jenkinsfile            <- Describes basic Jenkins CI/CD pipeline (see .sqa/)
│
├── LICENSE                <- License file
│
├── README.md              <- The top-level README for developers using this project.
│
├── .sqa/                  <- CI/CD configuration files
│
├── ai4os_demo_app    <- Source code for use in this project.
│   │
│   ├── __init__.py        <- Makes ai4os_demo_app a Python module
│   │
│   ├── api.py             <- Main script for the integration with DEEPaaS API
│   │
│   └── misc.py            <- Misc functions that were helpful accross projects
│
├── data/                  <- Folder to store the data
│
├── models/                <- Folder to store models
│
├── tests/                 <- Scripts to perfrom code testing
|
├── metadata.json          <- Defines information propagated to the AI4OS Hub
│
├── requirements.txt       <- The requirements file for reproducing the analysis environment, e.g.
│                             generated with `pip freeze > requirements.txt`
├── requirements-test.txt  <- The requirements file for running code tests (see tests/ directory)
│
└── setup.py, setup.cfg    <- makes project pip installable (pip install -e .) so
                              ai4os_demo_app can be imported
```
