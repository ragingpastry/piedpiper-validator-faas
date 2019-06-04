# PiedPiper Validator Function
[![Build Status](https://travis-ci.org/AFCYBER-DREAM/piedpiper-validator-faas.svg?branch=master)](https://travis-ci.org/AFCYBER-DREAM/piedpiper-validator-faas)

PiedPiper Validator

### Table of Contents

* [Getting Started](#getting-started)
* [Prerequisites](#prerequisites)
* [Installing](#installing)
* [Inputs and Outputs](#inputs-and-outputs)
* [Running the Tests](#running-the-tests)
* [Contributing](#contributing)
* [Versioning](#versioning)
* [Authors](#authors)
* [License](#license)
* [Acknowledgements](#acknowledgments)


## Getting Started

To deploy this function you must have OpenFaaS installed. To create a development environment see (https://github.com/AFCYBER-DREAM/ansible-collection-pidev)

### Prerequisites

OpenFaaS

### Installing

To install this function on OpenFaaS do the following after authentication:

```
git clone https://github.com/AFCYBER-DREAM/piedpiper-validator-faas.git
cd piedpiper-validator-faas
faas build
faas deploy
```

To validate that your function installed correctly you can run the following:

```
faas ls
```

## Inputs and Outputs

This function expects to receive its data via an HTTP POST request. The format of the request should be as follows:

```yaml
ci:
  ci_provider: gitlab-ci
  ci_provider_config: {{ contents of .gitlab-ci.yml }}
file_config:
  - file: test.sh
    linter: noop
  - file: etc
pi_global_vars:
  ci_provider: gitlab-ci
  project_name: {{ project_name }}
  vars_dir: default_vars.d
  version: {{ version }}
pi_lint_pipe_vars:
  run_pipe: True
  url: http://172.17.0.1:8080/function
  version: latest
pi_validate_pipe_vars:
  run_pipe: True
  url: http://172.17.0.1:8080/function
  policy:
    enabled: True
    enforcing: True
    version: 0.0.1
```

piedpiper-validator-faas will look at the contents of these run_vars and
run the specified version of the validators (given in `pi_validate_pipe_vars: policy: version:`)
Specifically, it will clone the Git repository `https://github.com/AFCYBER-DREAM/piedpiper-project-validations`
and load the required validation modules located in the `project_name`/`version`

Project structure for Project Validations git repository looks like the following:
```
├── project_name
│   └── releases
│       ├── 0.0.0
│       │   ├── __init__.py
│       │   └── pipes
│       │       ├── __init__.py
│       │       ├── pi_gitlab_ci
│       │       │   ├── __init__.py
│       │       │   └── pi_gitlab_ci.py
│       │       ├── pi_lint
│       │       │   ├── __init__.py
│       │       │   └── pi_lint.py
│       │       └── pi_validate
│       │           ├── __init__.py
│       │           ├── pi_files.py
│       │           └── pi_validate.py
│       └── 0.0.1
│           ├── __init__.py
│           └── pipes
│               ├── __init__.py
│               ├── pi_gitlab_ci
│               │   ├── __init__.py
│               │   └── pi_gitlab_ci.py
│               ├── pi_lint
│               │   ├── __init__.py
│               │   └── pi_lint.py
│               └── pi_validate
│                   ├── __init__.py
│                   ├── pi_files.py
│                   └── pi_validate.py
├── _master
│   └── releases
│       └── 0.0.0
│           └── pipes
│               ├── __init__.py
│               ├── pi_gitlab_ci
│               │   ├── __init__.py
│               │   └── pi_gitlab_ci.py
│               ├── pi_lint
│               │   ├── __init__.py
│               │   └── pi_lint.py
│               └── pi_validate
│                   ├── __init__.py
│                   ├── pi_files.py
│                   └── pi_validate.py
```

Let's take a look at the `_master` directory.

##### _master
This directory defines the latest definitions for our validation modules.
The only directory under this directory will be `releases` which contains
subdirectories named after the SymVer version number. This number will
be used in PiCli's validator pipe to target specific versions of validations.

Under the version directory there will be a pipes directory which contains
subdirectories for every pipe validation.

#### Validations
Validations are run using the [Marshmallow](https://marshmallow.readthedocs.io/en/3.0/)
library. We depend on functionality from the 3.0 pre-release version.

Every module under `pipes/` must provide a `validate` function which will
take one parameter, the dict to be validated.




## Running the tests

TBD

### Test Prerequisites


### Execute the tests

TBD

## Built With

## Contributing

Please read [CONTRIBUTING.md](https://github.com/AFCYBER-DREAM/piedpiper-picli) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/piedpiper-validator-faas/tags).

## Authors

See also the list of [contributors](https://github.com/AFCYBER-DREAM/piedpiper-validator-faas/contributors) who participated in this project.

## License

TBD

## Acknowledgments

* Inspiration for the CLI framework came from the Ansible Molecule project

