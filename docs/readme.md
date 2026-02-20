![GitHub Release](https://img.shields.io/github/v/release/EvobyteDigitalBiology/readstore)
![PyPI - Version](https://img.shields.io/pypi/v/readstore-basic)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen)

<br>

![ReadStore Workspace](../readstore_basic/frontend/streamlit/static/tutorial/img_01_welcome_readstore.webp)

<br>

# ReadStore Basic

ReadStore is the lean data platform for managing NGS and Omics data and automating data analysis.

- **Database** for FASTQ, analysis and metadata files
- **Project management** and collaborative workspace
- **APIs** for Terminal, Python and R for automation of data analysis

<br>

The full documentation is available as [GitHub Page](https://evobytedigitalbiology.github.io/readstore/) 

**Please read and follow the instructions carefully**. In particular the [Security, Permissions and Backup](#backup) section contains important information related to data security and backup. In case of problems with the install or information on different Linux distributions, please check the separate [Installation Guide](installation.md).

For general questions reach out to info@evo-byte.com or in case of technical problems to support@evo-byte.com

Happy analysis :)

## Quickstart

ReadStore Basic allows you to manage NGS and omics data through a web interface and command-line tools. Follow these steps to get started:

1. **Install ReadStore Basic**

    `pip3 install readstore-basic`

2. **Start the server**: 

    `readstore-server`

3. **Access the web app**

    Open your browser and navigate to `http://localhost:8501`

4. **Upload FASTQ datasets**

    In the UI, navigate to the *Upload Page* and click Import to ingest FASTQ files.

    Check In datasets after QC is completed. 

5. **Install the CLI** (optional)

    `pip3 install readstore-cli`

6. **Configure the CLI**

    Run `readstore configure` and enter your username and token

7. **Upload FASTQ files**

    Use `readstore upload myfile_r1.fastq` to upload sequencing data


For detailed instructions how to enable user management, setup APIs and more, see the [Installation](#installation) and [Usage](#usage) sections below.

## Table of Contents
- [Description](#description)
- [Security, Permissions and Backup](#backup)
- [Installation](#installation)
    - [Update an existing ReadStore Server](#update)
    - [Advanced Server Configuration](#advancedconfig)
    - [Configure systemd Service](#systemd)
    - [Export Database to File](#export_dump)
- [ReadStore API](#api)
- [Usage](#usage)
    1. [Account Settings](#account_settings)
    2. [Upload Files](#upload_files)
    3. [Stage Files](#stage_files)
    4. [Access Datasets via the CLI](#access_via_cli)
    5. [Managing Processed Data](#manage_pro_data)
- [Contributing](#contributing)
- [License](#license)
- [Credits and Acknowledgments](#acknowledgments)

## The Lean Solution for Managing NGS and Omics Data

ReadStore is a platform for storing, managing, and integrating omics data. It speeds up analysis and offers a simple way of managing and sharing NGS omics datasets, metadata and processed data (ProData).
Built-in project and metadata management structures your workflows and a collaborative user interface enhances teamwork — so you can focus on generating insights.

The integrated Webservice enables you to directly retrieve data from ReadStore via the terminal [Command-Line Interface (CLI)](#https://github.com/EvobyteDigitalBiology/readstore-cli) or [Python](#https://github.com/EvobyteDigitalBiology/pyreadstore) / [R](#https://github.com/EvobyteDigitalBiology/r-readstore) SDKs.

The ReadStore Basic version offered here provides a local web server with simple user management. If you need organization-wide deployment, advanced user and group management, or cloud integration, please check the ReadStore Advanced versions and reach out to info@evo-byte.com.

## Description

ReadStore facilitates managing FASTQ files, NGS and Omics data, along with experimental (meta)data and Processed Datasets. It provides a database and a web app with a simple user interface to create and edit datasets and projects. You can create your own structure using metadata key-value pairs (e.g., replicate: 1 or condition: control) or attach files as additional information.

Metadata, file attachments and processed datasets (ProData) can be accessed along with your NGS datasets from analysis scripts or data pipelines, providing consistent workflow automation.

ReadStore Basic enables you to manage NGS data from your local Linux environment and can be set up in a few minutes. It comprises a local web server and web app that you can connect to via your browser to explore and edit your NGS experiments.

To upload FASTQ files and Processed Data from the command line into the ReadStore database, you’ll also need to install the ReadStore CLI.

ReadStore Basic provides a shared work environment. Users can collaborate on editing datasets, projects, metadata, and attachments, with shared access to all resources. This facilitates cross-functional projects, connecting data analysts and experimental researchers.

The ReadStore database can be accessed programmatically using the [Command-Line Interface (CLI)](#https://github.com/EvobyteDigitalBiology/readstore-cli) or [Python](#https://github.com/EvobyteDigitalBiology/pyreadstore) & [R](#https://github.com/EvobyteDigitalBiology/r-readstore) SDKs. This facilitates easy integration into bioinformatics pipelines and downstream analysis workflows.

If you would like to have more advanced user, group, and permission management, please reach out for a demo of the ReadStore Advanced version.

## Security, Permissions and Backup<a id="backup"></a>

**PLEASE READ AND FOLLOW THESE INSTRUCTIONS CAREFULLY!**

ReadStore Basic comes with simple security and permission management based on Linux file permissions, which govern access to the ReadStore database.

### Database Permissions <a id="permission"></a>

The Linux user running the `readstore-server` is, by default, the **Data Owner**. In this role, the **Data Owner** has exclusive read/write permissions (`chmod 600`) to the database files, database backups, secret key, and ReadStore configuration.

The **Data Owner** must ensure that access rights to these files remain restricted to prevent unauthorized access to the ReadStore database (see [Installation](#installation)). By default, the secret key and configuration files are stored in your home directory (`~/.rs-server/`), but you can change the `--config-directory` to specify a different folder path.

The ReadStore secret key is located in your `--config-directory` (default `~/.rs-server/secret_key`). It is recommended to **keep a secured copy of the secret key** to allow access to backups or restore the database in case of an incident.

If you run ReadStore without `--enable-login` (default), ReadStore creates a `secret_default_user_key` file in your `--config-directory` (default `~/.rs-server/secret_default_user_key`). The Streamlit app uses this key to automatically log in as the default user (`default`). Treat this file like a password and keep it protected with restrictive permissions. You can also set an custom default user key with the `--admin-password` parameter.

### Admin Account

ReadStore can be started in two modes:

- **Login enabled** (`--enable-login`): upon first launch, an Admin account (`admin`) is created using the password provided via `--admin-password`. Login to the admin account is required to create users and manage permissions.
- **Login disabled** (default): no interactive login is shown in the browser. The app automatically logs in as the default user (`default`) using the `secret_default_user_key` in your `--config-directory`.


### User Account Passwords and Tokens

To log in to the ReadStore web app via a web browser, each **User** needs a user account. User accounts are created by the **Admin** from within the web app. The Admin sets an account password when creating new users. Each **User** can later change their account password.

Each **User** has a unique **Token** assigned, which is required to connect to ReadStore via the Command-Line Interface (CLI) or through the Python and R SDKs. This token should not be shared. Tokens can be easily regenerated from the Settings page in the ReadStore CLI.

A **User** is required to have **upload permissions** to upload FASTQ files into the ReadStore database.

See [Installation](#installation) for instructions how to setup Users

#### What about user groups?

Group management to handle access permissions is available in the advanced versions of ReadStore. If you would like to learn more, reach out to info@evo-byte.com. 

### Backups

ReadStore automatically performs regular backups. The backup directory (see [Installation](#installation)) should be different from the database directory. ReadStore log files are also saved to a predefined folder. Each folder should have sufficient space to store database, backup, and log files.

It is posible to **export** (dump) the database into `.json` and `.csv` files using the `readstore-server export` method. More information below the [Export](#export_dump) section. 

### Deployment and Server Configurations

**You are responsible for hosting and deploying the ReadStore server in a secure environment**. This includes, but is not limited to, access management, active firewall protection of your servers, and regular patching of your operating system.

If you need a ReadStore version with more advanced permission and group management, database server support, or customization for your infrastructure, please reach out.

## Installation & Updates

**NOTE** Check the [Installation Guide](installation.md) for more information and common sources of errors or contact support@evo-byte.com in case of technical problems. We will certainly find a solution.

More information on [updating](#update) a running ReadStore server can be found below.

### 1. Install the ReadStore Basic Server

You need **Python version 3.10 or higher** to install ReadStore.

You can perform the install in a conda or venv virtual environment to simplify package management.
This is recommended to avoid potential conflicts in the required Python dependencies.

Here is an example how to setup a virtual environment using the venv module:

`python -m venv .venv`

`source .venv/bin/activate`

This provides you with a clean virtual environment avoiding potential issues with resolving Python dependencies. 

Next install the ReadStore Basic server.

`pip3 install readstore-basic`

A local install is also possible

`pip3 install --user readstore-basic`

Make sure that `~/.local/bin` is on your `$PATH` in case you encounter problems when starting the server.

Validate the install by running

`readstore-server -v`

This should print the ReadStore Basic version

### 2. Start the Webserver

#### Prepare Output Folders 

ReadStore stores the database, backups and logs in separate folders.

- You can **explicitly create folders** for the ReadStore database files (`db-directory`), the backups (`db-backup-directory`) and log files (`log-directory`) and pass them as arguments.
- If you start `readstore-server` **without providing any of these three directory arguments**, it will automatically create (or reuse, if already present) the folders `readstore-db/`, `readstore-db-backup/` and `readstore-log/` in your current working directory.

All ReadStore database, backup and log files are created with user-exclusive read/write permissions (`chmod 600`) when starting the ReadStore server for the first time. Make sure that restricted permissions are maintained to avoid unwanted access to database files.

The readstore configuration files and secret key are by default written to you home dir `~/.rs-server` (user-exclusive read/write permissions `chmod 600`). You can specify another `config-directory`. Ensure restricted permissions for this folder and files. It is recommended to create a [secure backup of the secret key](#permission) 

#### Start the Server

`readstore-server`

or run

`readstore-server --db-directory /path/to/database_dir --db-backup-directory /path/to/backup_dir --log-directory /path/to/logs_dir`

If you want to define database and log data path by yourself. ReadStore Server requires ports 8000 and 8501. See [below](#advancedconfig) if there is a problem with blocked ports.

#### User Management

To enable set the **interactive login** (creates `admin` user on first start):

Make sure to store the `admin-password` at a secure location.

##### Security note: reset the admin password on first login

When you start ReadStore with `--admin-password`, the password is part of the command you type. Depending on your environment, that can be exposed via your terminal scrollback, shell history, logs, or process listings.

To reduce the risk of accidental disclosure, use `--admin-password` only to bootstrap the initial `admin` account, then **log in once and immediately change the `admin` password** using the web app’s password change/reset functionality.

`readstore-server --enable-login --admin-password <your_admin_password> --db-directory /path/to/database_dir --db-backup-directory /path/to/backup_dir --log-directory /path/to/logs_dir`

#### How can I persist the server sesstion?

The command will run the server in your current terminal session, but you probably want to keep your server running after closing the terminal.
There are different options

- Use a terminal multiplexer like `screen` or `tmux` to start a persistent session and run the server from there
- Start the server with `nohup` to keep running after closing you session (`nohup readstore-server ...`)
- Configure a `systemd` service, which can for instance handle automatic (re)start procedures (s. [below](#systemd))

You can configure the readstore-server using environment variables. This can be useful in containerized or cloud applications. (s. [Advanced Configuration](#advancedconfig))

#### What if my Server Terminates?

The database and backups persist also if the ReadStore server is terminated or updated. 
The database files remain stored in the `db-directory` or `db-backup-directory` folders.

You can simply restart the `readstore-server` with the same directories, and you will be able to access all data in your database. 

**NOTE** The database files and backups must match to the secret key in your `config-dir`. Hence it is recommended to consistently use the `config-dir` with the same `db-directory` and `db-backup-directory` folders.

### 3. Connect to the ReadStore Web App with your Browser

After the launch of the webserver you should to be able to connect to the ReadStore web app from your browser.

The ReadStore web app should be available via your browser under localhost port 8501 (`http://127.0.0.1:8501` or `http://localhost:8501/`).

- With `--enable-login`, you should see a login screen.
- Without `--enable-login` (default), the app automatically logs in as the default user (`default`).

If you you want to connect to the ReadStore Web App from a remote connection, e.g. from you local PC via the browser, you may need to open the corresponing server ports or setup a SSH tunnel (s. below)

**NOTE** The port can change depending on your server settings (s. [Advanced Configuration](#advancedconfig)).

#### Access ReadStore Web App via SSH Tunnel

If you run ReadStore Basic on a Linux server that you connect to via SSH, consider using SSH tunneling / port forwarding to access the server port 8501 from your local machine's browser (Check this [Tutorial](#https://linuxize.com/post/how-to-setup-ssh-tunneling/)). Tools like [PuTTY](#https://www.putty.org/) help Windows users to easily set up SSH tunnels.

In any case make sure that server connections are established in agreement with your organizations IT security guidelines or ask your IT admins for support. 

If you need support in making ReadStore available for users in your organization, reach out to info@evo-byte.com. We will find a solution for you!

### 4. Setup Admin Account and First Users

**NOTE** This section applies when you start the server with `--enable-login`.

#### Create new User(s)

1. Open the webapp under `http://127.0.0.1:8501`
2. Log into the Admin account, move to the `Admin` page
3. Click the `Create` button to create a new user
4. Add name, email and password. If the user should be allowed to upload FASTQ files you must enable `Upload Permissions`
5. Click `Confirm`. You should see the new user in the overview

Users can change their password in their `Settings` page after login. The number of users is limited by the seats of your license.

#### Login with User Account

1. Open the webapp under `http://127.0.0.1:8501`
2. Login with the created user name and password
3. Get started creating project and datasets

### 5. Install the ReadStore Command Line Interface (CLI) (optional)

You need to install the ReadStore CLI if you want to upload FASTQ files and access ReadStore data from the CLI.

For more information check the [ReadStore CLI GitHub Repository](https://github.com/EvobyteDigitalBiology/readstore-cli)

**NOTE** Uploading FASTQ files requires users to have `Upload Permission` set in their account.  

#### Install Command Line Interface

`pip3 install readstore-cli`

Validate successful install by running

`readstore -v`

This should print the CLI's version

#### Configure CLI

You need to configure the ReadStore CLI client with your username and token.
You can find and change you user `token` in the `Settings` page of your account. Click on `Token` to retrieve the token value.

Run

`readstore configure`

Enter you `username`, `token`, and your preferred output format `json, text or csv`.

Check the status of your CLI config with

`readstore configure list`

You should see the credentials you entered.

### Update an existing ReadStore Basic Server<a id="update"></a>

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

**4. Continue Operations**

Resume your work as usual. If you encounter any questions or issues, contact support@evo-byte.com.

### Advanced ReadStore Basic Server Configuration<a id="advancedconfig"></a>

`readstore-server -h`

```
ReadStore Server

options:
  -h, --help             Show this help message and exit
  --db-directory         Directory for Storing ReadStore Database  (default: ./readstore-db)
  --db-backup-directory  Directory for Storing ReadStore Database Backups   (default: ./readstore-db-backup)
  --log-directory        Directory for Storing ReadStore Logs   (default: ./readstore-log)
  --config-directory     Directory for storing readstore_server_config.yaml (default: ~/.rs-server)
  --django-port          Port of Django Backend (default: 8001)
  --streamlit-port       Port of Streamlit Frontend (default: 8501)
  --debug                Run In Debug Mode
  --enable-login         Enable user authentication
  --admin-password       Password for admin user. Required if --enable-login is set
```

ReadStore requires different directories for storing the database file, backups, logs and configurations. It is important to make sure that the user launching the ReadStore server (**data owner**) has read and write permissions for each folder. The files created have user-exclusive read/write permissions (`chmod 600`) by default and it is important to ensure that permissions are kept restrictive.

You can run ReadStore in a more verbose `--debug` mode, which is not recommended.

#### Changing Server Ports

ReadStores uses a Django Webserver and Streamlit Frontend with default ports 8000 and 8501. If other applications are running on these ports, change the ports using the `--django-port` or `--streamlit-port` arguments to a free port.

**NOTE** Changing ports requires users to connect to the webapp using a different port. Users also need to update their default CLI/SDK configurations. More information in the ReadStore CLI's README.

#### Configure ReadStore using Environment Variables

In some cases you may want to setup the ReadStore server using environment variables, for instance if you run containers or cloud applications.

The following environment variables can be used to configure the ReadStore server

```
RS_DB_DIRECTORY         Corresponds to db-directory argument
RS_DB_BACKUP_DIRECTORY  Corresponds to db-backup-directory argument
RS_LOG_DIRECTORY        Corresponds to log-directory argument
RS_CONFIG_DIRECTORY     Corresponds to config-directory argument
RS_DJANGO_PORT          Corresponds to django-port argument
RS_STREAMLIT_PORT       Corresponds to streamlit-port argument

RS_ADMIN_PASSWORD       Admin password (overrides --admin-password)

RS_PYTHON      Path to Python executable    (default: python3)
RS_STREAMLIT   Path to Streamlit executable (default: streamlit)
RS_GUNICORN    Path to Gunicorn executable  (default: gunicorn)
```

### Create ReadStore systemd Linux service<a id="systemd"></a>

Creating a Linux service has the several advantages for running the ReadStore server. 
A service can take case of automatic restart of the ReadStore server in case of an update or crash of you Linux server.

You find here a starting point for setting up a service using `systemd` but you may need superuser (`sudo`) privileges to actually start the service. Get in touch with you IT admins if you need support.

1. Check the `readstore.service` file provided here in the repository and adapt it with your environment configurations

    - `User`: Linux Username to run service. Will be the **Data Owner** for database files, logs, secrets and config.
    - `WorkingDirectory`: Choose working directory for service
    - `ExecStart`: Command to run readstore-server. You need to define the python to the Python install you want to use (check with `which python`) and the path to the `readstore_server.py`, which is typically in your python3 site packages folder (e.g. `.local/lib/python3.11/site-packages/readstore_basic/readstore_server.py`). Specify the path to the database files, backup, config and logs in the ExecStart
    - `Environment=RS_STREAMLIT`: Path to Streamlit executable (run `which streamlit` to find the path)
    - `Environment=RS_PYTHON`: Path to Python executable (run `which python` to find the path). Should be   the same as in ExecStart
    - `Environment=RS_GUNICORN`: Path to Gunicorn executable (run `which gunicorn` to find the path)

2. Copy the `readstore.service` file to the system folder

    `cp readstore.service /etc/systemd/system/readstore.service`

3. Reload the Systemd Deamon

    `sudo systemctl daemon-reload`

4. Enable and Start the Service

    `sudo systemctl enable readstore.service`
    
    `sudo systemctl start readstore.service`

5. Check service status

    `sudo systemctl status readstore.service`

6. Check service logs

    `sudo journalctl -u readstore.service -f`

7. Stop or Restart Service

    Restarting might be required after installing a ReadStore Basic update

    `sudo systemctl stop readstore.service`

    `sudo systemctl restart readstore.service`

### Export (Dump) ReadStore Database<a id="export_dump"></a>

In some cases it might be necessary to retrieve the full database content including all tables in a flat file format (i.e. json or csv). This includes attachment files which have been uploaded for projects or datasets.

The `readstore-server export` command dump the database and stored files.

```
usage: readstore-server export [-h] [--config-directory] [--export_directory]

options:
  -h, --help           show this help message and exit
  --config-directory   Directory containing ReadStore Database (required)
  --export_directory   Directory for storing exported ReadStore Database files (required)
```

Example `readstore-server export --config-directory /path/to/config --export_directory /path/to/export_files`

The tables are exported as `.csv` and `.json` files. Project and Datasets attachment files are exported in their original file format, each in a separate folder for each Project or Dataset.

## ReadStore API<a id="api"></a>

The **ReadStore Basic** server provides a RESTful API for accessing resources via HTTP requests.  
This API extends the functionalities of the ReadStore CLI as well as the Python and R SDKs.

### API Endpoint
By default, the API is accessible at:  
`http://127.0.0.1:8000/api_x_v1/`

### Authentication
Users must authenticate using their username and token via the Basic Authentication scheme.

### Example Usage
Below is an example demonstrating how to use the ReadStore CLI to retrieve an overview of Projects by sending an HTTP `GET` request to the `project/` endpoint.  
In this example, the username is `testuser`, and the token is `0dM9qSU0Q5PLVgDrZRftzw`. You can find your token in the ReadStore settings.

```bash
curl -X GET -u testuser:0dM9qSU0Q5PLVgDrZRftzw http://localhost:8000/api_x_v1/project/
```

#### Example Reponse

A successful HTTP response returns a JSON-formatted string describing the project(s) in the ReadStore database. Example response:

```
[{
  "id": 4,
  "name": "TestProject99",
  "metadata": {
    "key1": "value1",
    "key2": "value2"
  },
  "attachments": []
}]
```

### Documentation

Comprehensive [API documentation](https://evobytedigitalbiology.github.io/readstore/rest_api/) is available in the ReadStore Basic Docs.

## Usage

### Quickstart

Let's upload some FASTQ files.

#### 1. Account Settings<a id="account_settings"></a>

Make sure you have the [ReadStore CLI](https://github.com/EvobyteDigitalBiology/readstore-cli) installed and configured (s. [Installation](#installation)).

Run the command to check if your configuration is in place.

`readstore configure list`

For uploading FASTQ files your User Account needs to have `Upload Permission`. Check this in the `Settings` page of your account. If you do not have `Upload Permission`, ask the Admin to grant you permission.

#### 2. Upload Files<a id="upload_files"></a>

Move to a folder that contains some FASTQ files.

`readstore upload myfile_r1.fastq`

This will upload the file and run the QC check. You can select several files at once using the `*` wildcard.

You can also upload multiple FASTQ files at once using the import function or perform a `Import From File` form the ReadStore app staging page. 

#### 3. Stage Files<a id="stage_files"></a>

Login to the User Interface on your browser and move to the `Upload` page. Here you find a list of all FASTQ files you just upload.

For large files the QC step can take a while to complete. FASTQ files are grouped in Datasets which you can `Check In`. Then they appear in the `Datasets` page.

If you uploaded a large number of FASTQ files at once, you can Check In multiple FASTQ files at once using the `Batch Check In` function. For this, click on `More` in the top right and select `Batch Check In`. Select all datasets that you want to check in and confirm.

Under `More`, you also find the `Import From File` method that allows you to get and upload Excel or .csv files with FASTQ paths to upload. 

#### 4. Access Datasets via the CLI<a id="access_via_cli"></a>

The ReadStore CLI enables programmatic access to Projects, Datasets, metadata and attachments.

Some example commands are:

`readstore dataset list`  List all datasets

`readstore dataset get --id 25`  Get detailed view on Dataset 25

`readstore dataset get --id 25 --read1-path`  Get path for Read1 FASTQ file

`readstore dataset get --id 25 --meta`  Get metadata for Dataset 25

`readstore project get --name cohort1 --attachment`  Get attachment files for Project "cohort1"

You can find a full documentation in the [ReadStore CLI Repository](https://github.com/EvobyteDigitalBiology/readstore-cli)

#### 5. Managing **Pro**cessed **Data**<a id="manage_pro_data"></a>

**Pro**cessed **Data** refer to files generated through processing of raw sequencing data.
Depending on the omics technology and assay used, this could be a transcript count file, variant files or gene count matrices. 

ProData are attached to Datasets, and can be uploaded via the ReadStore CLI or R & Python SDKs.
You can check the ProData for each Dataset in the ReadStore App under the `Datasets` section.

Processed Data are not directly uploaded to the ReadStore database, but similar to raw datasets
their path are stored in the database and validated.

Here's an example how to upload, retrieve and delete a processed file.

**NOTE** Your user account is required to have `Upload Permissions` to upload and delete ProData files:

`readstore pro-data upload -d test_dataset_1 -n test_dataset_count_matrix -t count_matrix test_count_matrix.h5`  
Upload count matrix test_count_matrix.h5 with name "test_dataset_count_matrix" for dataset with name "test_dataset_1"

`readstore pro-data list` List Processed Data for all Datasets and Projects

`readstore pro-data get -d test_dataset_1 -n test_dataset_count_matrix` Get ProData details for Dataset "test_dataset_1" with the name "test_dataset_count_matrix"

`readstore pro-data delete -d test_dataset_1 -n test_dataset_count_matrix` Delete ProData for dataset "test_dataset_1" with the name "test_dataset_count_matrix"

The delete operation does not remove the file from the file system, only from the database.

## Contributing

Please feel free to create an issue for problems with the software or feature suggestions.

## License

ReadStore Basic is distributed under an Open Source Apache 2.0 License.

## Credits and Acknowledgments<a id="acknowledgments"></a>

ReadStore Basic is built upon the following open-source python packages and would like to thank all contributing authors, developers and partners.

Check the LICENSE file for a full list of attributions and third-party license information.

- Django (https://www.djangoproject.com/)
- djangorestframework (https://www.django-rest-framework.org/)
- requests (https://requests.readthedocs.io/en/latest/)
- gunicorn (https://gunicorn.org/)
- pysam (https://pysam.readthedocs.io/en/latest/api.html)
- pyyaml (https://pyyaml.org/)
- streamlit (https://streamlit.io/)
- pydantic (https://docs.pydantic.dev/latest/)
- pandas (https://pandas.pydata.org/)
- python (https://www.python.org/)