# Installation Guide

This guide contains information how to setup and install ReadStore Basic along with potential errors and information on different Linux distributions.

The full **ReadStore Basic documentation** is available [here](https://evobytedigitalbiology.github.io/readstore/).

For general questions reach out to info@evo-byte.com or in case of technical problems to support@evo-byte.com


## Table of Contents

1. [Install](#install)
2. [Update](#update)
3. [Python Versions and Dependency Management](#versions_dependencies)
4. [Common Errors and Solutions](#errors)
5. [Examples Installing ReadStore on Different Distributions](#examples)

## 1. Install<a id="install"></a>

It is recommended to use ReadStore Basic using the Python package manager `pip`.
Make sure that pip is installed and available by running
`pip --version`.

You need **Python version 3.10 or higher** to install ReadStore.

You can perform the install in a conda or venv virtual environment to simplify package management.
This is recommended to avoid potential conflicts in the required Python dependencies.

Here is an example how to setup a **virtual environment** using the venv module. You can find more examples how to setup venv on different environments below.

`python -m venv .venv`

`source .venv/bin/activate`

This provides you with a clean virtual environment avoiding potential issues with resolving Python dependencies. 

Next install the ReadStore Basic server.

`pip3 install readstore-basic`

A local install is also possible:

`pip3 install --user readstore-basic`

Make sure that `~/.local/bin` is on your `$PATH` in case you encounter problems when starting the server.

Validate the install by running

`readstore-server -v`

This should print the ReadStore Basic version

### Install from Source

You can also download and install the `readstore-basic` package by downloading the source or built distribution after downloading the packages from [PyPI Repository](https://pypi.org/project/readstore-basic/#files).

More information on how to install source packages can be found [here](https://packaging.python.org/en/latest/tutorials/installing-packages/).

## 2. Update<a id="update"></a>

If you already have a running ReadStore Server and want to upgrade to a new version, follow these simple steps:

**0. Backup Validation**

Ensure that ReadStore database backups are in place and up-to-date (located in the --db-directory folder). Optionally, copy the latest backup file (.sqlite3) to a secure location for potential rollback.

**1. Stop the Running Server**

Stop the running server by terminating the server process or stopping the corresponding Linux service. This will not affect the data.

**2. Update the ReadStore-Basic Python Package**

Within the Python environment used to run the ReadStore Server, update the `readstore-basic` package by running the following command:

`pip install readstore-basic --upgrade`

After updating, verify that the new version is installed and the old version is removed:

`readstore-server -v`

This command should print the new version number.

**3. Restart the Server**

Restart the ReadStore Server with the same folder directories and settings as before the update.

## 3. Python Versions and Dependency Management<a id="versions_dependencies"></a>

### Python version

ReadStore Basic strictly requires **Python version 3.10** or above for installation. If your current Python version does not fulfill those requiements, you will receive an error like:

```
ERROR: Could not find a version that satisfies the requirement readstore-basic (from versions: none)
ERROR: No matching distribution found for readstore-basic
```

### Managing multiple Python versions

It is possible that multiple Python version are installed at the same time on your system. This can cause issues in managing a valid Python environment with correct dependencies and lead to unexpected errors.

It is highly recommended to operate in **virtual environments** using the Python `venv` module or a [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html). This will help managing consistent dependencies, also in cases that multiple Python versions are installed.

In any cases you need to ensure that the `python3` command is available on you system before starting the ReadStore server.

`python3 --version`

Run the version command and make sure you see the right Python version. If your Python binary cannot be reached, it is possible to configure other paths or aliases in the config. Please get in touch for more information.

## 4. Common Errors and Solutions<a id="errors"></a>

###  Wrong Python version

Your current Python version is below Python 3.10, which will lead to an error like:

```
ERROR: Could not find a version that satisfies the requirement readstore-basic (from versions: none)
ERROR: No matching distribution found for readstore-basic
```

*Solution* Update your systems Python version or install [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html) with newer Python version.

###  Error Installing package via Python pip

In case that a package manager is managing a Python environment, you may encounter errors when trying to install `readstore-basic` via Python pip.

```
error: externally-managed-environment
```

*Solution* In this case you may need to setup a virtual environment using `venv` module or usign a [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html).

The venv environment can be installed using on your system using for instance the apt package manager
`sudo apt install python3-venv`

`python -m venv .venv`

`source .venv/bin/activate`


## 5. Example Install on different Distributions<a id="examples"></a>

Here you can find a number of examples for setting up a ReadStore Basic server on different distributions. Those examples were tested on AWS EC2 Instances with different Linux distributions, starting from an empty environment.

### Ubuntu 24.04

ReadStore Basic install using venv virtual environment.
Installed **Python v3.12**.

```
sudo apt-get update

sudo apt-get upgrade -y

sudo apt-get install python3-venv

python3 -m venv .venv

source .venv/bin/activate

pip3 install readstore-basic

readstore-server --db-directory readstore_dir --db-backup-directory readstore_backup_dir --log-directory readstore_log_dir
```

### Debian 12

ReadStore Basic install using venv virtual environment.
Installed **Python v3.11**.

```
sudo apt-get update

sudo apt-get upgrade -y

sudo apt-get install python3-venv

python3 -m venv .venv

source .venv/bin/activate

pip3 install readstore-basic

readstore-server --db-directory readstore_dir --db-backup-directory readstore_backup_dir --log-directory readstore_log_dir
```

### Amazon Linux 2023

Installed **Python v3.9** version. Requires update of Python before installing ReadStore.

```
sudo yum update

sudo yum upgrade -y

sudo yum install python3.11

python3.11 -m venv .venv

source .venv/bin/activate

pip3 install readstore-basic

readstore-server --db-directory readstore_dir --db-backup-directory readstore_backup_dir --log-directory readstore_log_dir
```
