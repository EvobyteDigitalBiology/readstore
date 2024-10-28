# ReadStore

This ReadMe introduces ReadStore Data Platform, the lean solution for managing FASTQ and NGS data.

**Please read the instructions carefully before using the app**. In particular the [Security, Permissions and Backup](#backup) section contains information related to data security and backup.

Find Tutorials and Intro Videos on 
https://www.youtube.com/@evobytedigitalbio

Or as blog posts https://evo-byte.com/blog/

General information on www.evo-byte.com/readstore

For questions reach out to info@evo-byte.com

## Table of Contents
- [Description](#description)
- [Security, Permissions and Backup](#backup)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Credits and Acknowledgments](#acknowledgments)

## The Lean Solution for Managing FASTQ and NGS Data

ReadStore is a platform for storing, managing, and integrating genomic data. It speeds up analysis and offers a simple way of managing and sharing FASTQ and NGS datasets. Built-in project and metadata management structures your workflows and a collaborative user interface enhances teamwork — so you can focus on generating insights.

The integrated Webservice enables your to directly retrieve data from ReadStore via the terminal Command-Line-Interface (CLI) or Python / R SDKs.

The ReadStore Basic version offered here provides a local webserver with a simple user management. If you need an organization-wide deployment, advanced user and group management or cloud integration please check the ReadStore Advanced versions and reach out to info@evo-byte.com.

## Description

ReadStore facilitates managing FASTQ files and NGS data along with experimental (meta)data. For this, ReadStore provides a database and a simple User Interface to create and edit Datasets and Projects. You can create your own structure by using metadata key-value pairs (e.g. replicate: 1, or condition: control), or attach files as additional information. 

Metadata and attachments can be access along with your NGS datasets from analysis scripts or data pipelines, providing a consistent automation of your workflows.

ReadStore Basic enables you manage NGS data from your local Linux environment and can be setup in a few minutes. ReadStore Basic comprises a local Webserver and User Interface that you can connect to via you browser in order to explore and edit your NGS experiments.

In order to upload FASTQ files into the ReadStore database, you also need to install the ReadStore CLI that offers a connection via your command line.

Login to the ReadStore User Interface via the browser requires a user account. User accounts are created by the Admin. 

ReadStore Basic provides a shared work environment for all registered users. Users can collaborate on editing Datasets, Projects, metadata and attachments and have shared access to all resources. This facilitates cross-functional projects and connects data analysts and experimental researchers.

If you would like to have more advances user, group and permission management, please reach out for an demo of the ReadStore Advanced version.

## Security, Permissions and Backup<a id="backup"></a>

**PLEASE READ AND FOLLOW THESE INSTRUCTIONS CAREFULLY!**

ReadStore Basic comes with simple security and permission management based on Linux file permissions, which govern access to the ReadStore database.

### Database Permissions <a id="permission"></a>

The Linux User running the readstore-server is by default the **Data Owner**. In this role, the **User** has exclusive read/write permissions (chmod 600) to the database files, database backups, secret key and ReadStore configuration.

The **Data Owner** must ensure that access rights to those files remain restricted, otherwise unwanted access to the ReadStore database is possible (s. [Installation](#installation)). Secret key and configuration files are by default written to your home directory (`~/.readstore/`), but you can change your `--config-directory` and specify a different folder path.

The ReadStore secret key is found in your `--config-dir` (default `~/.readstore/secret_key`). It is recommended to **keep a secured copy of the secret key** to be able to access backups or restore the database in case of an incident.

### Admin Account

Upon first launch of the ReadStore Basic Webserver, the Admin account is created with a password, which your receive along with your license key. 

The **Admin or must change the Admin password immediately** on first login.

### User Account Passwords and Token

In order to login to the ReadStore User Interface via your webbrowser, each **User** needs a user account. User accounts are created by the **Admin** from the User Interface. The Admin is required to set an account password when creating new users. A **User** can later change his or her account password.

Each **User** has a unique **Token** assigned. The **Token** is required to connect to ReadStore via the Command-Line-Interface (CLI) or via the Python & R SDKs. Do not share the token. You can easily regenerate the token via the Settings page in the ReadStore CLI.

A **User** is required to have **staging permissions** to upload FASTQ files into the ReadStore database (s. [Installation](#installation)).

### Backups

ReadStore is automatically performing regular backups. The backup directory (s. Installation) should be different from the database directory. ReadStore Logs are also saved to a predefined folder. Each folder should have sufficient space to save database, backup and log files.

### Deployment and Server Configurations

**You are responsible for hosting and deploying the ReadStore Server in a secured environment**. This includes, but is not limited to, access management, active firewall protection of your servers, or regular patching of you operating system.

If you need a ReadStore version with more advanced permission and group management, database servers, or customization to your infrastructure, please reach out.


## Installation

### 1. Install the ReadStore Basic Server

`pip3 install readstore-basic`

You can perform the install in a conda or venv virtual environment to simplify package management.

A local install is also possible

`pip3 install --user readstore-basic`

Make sure that `~/.local/bin` is on your `$PATH` in case you encounter problems when starting the server.

Validate the install by running, which should print the ReadStore version

`readstore-server -v`

### 2. Start the Webserver

#### Prepare output folders 

Create output folders for the ReadStore database files (`db-directory`), the backups (`db-backup-directory`) and log files (`log-directory`).

All ReadStore database, backup and log files are created with user-specific read/write (`chmod 600`) when starting the ReadStore server for the first time. Make sure that restricted permissions are maintained to avoid unwanted access to database files.

The readstore configuration files and secret key are by default written to you home dir `~/.readstore` (user-only read/write permissions `chmod 600`). You can specify another `config-directory`. Ensure restricted permissions for this folder and files. It is recommended to create a [secure backup of the secret key](#permission) 

#### Start the server

`readstore-server --db-directory /path/to/database_dir --db-backup-directory /path/to/backup_dir --log-directory /path/to/logs_dir`

ReadStore Server requires ports 8000 and 8501. See [below](#advancedconfig) if there is a problem with blocked ports.

The command will run the server in your current terminal session, but you probably want to keep your server running after closing the terminal.
There are different options

- Use a terminal multiplexer like `screen` or `tmux` to start a persistent session and run the server
- Start the server with `nohup` to keep running after closing you session (`nohup readstore-server ...`)
- Configure a `systemd` service, which can for instance handle automatic (re)start procedures (s. [below](#systemd))

You can configure the readstore-server using environment variables. This can be useful in containerized or cloud applications. (s. [Advanced Configuration](#advancedconfig))

#### What if my server terminates?

The database and backups persist also if the ReadStore server is terminated or updated. 
The database files remain stored in the `db-directory` or `db-backup-directory` folders.

You can simply restart the `readstore-server` with the same directories, and you will be able to access all data in your database. 

**NOTE** The database files and backups must match to the secret key in your `config-dir`. Hence it is recommended to consistently use the `config-dir` with the same `db-directory` and `db-backup-directory`.

### 3. Connect to the ReadStore User Interface with your Browser

After the launch of the webserver you should to be able to connect to the ReadStore Web App and User Interface from your browser.

The ReadStore User Interface should be available via your browser under localhost port 8501 (`http://127.0.0.1:8501` or `http://localhost:8501/`). You should see a login screen.

**NOTE** The port can differ depending on your server settings (s. [below](#advancedconfig)).

#### ReadStore User Interface via SSH Tunnel

If you run ReadStore Basic on a Linux server that you connect to via SSH, consider using SSH tunneling / port forwarding to access the server port 8501 from your local machine's browser (Tutorial: https://linuxize.com/post/how-to-setup-ssh-tunneling/). Tools like PuTTY help Windows users to easily set up SSH tunnels (https://www.putty.org/).

In any case make sure that server connections are established *in agreement with your organizations IT security guidelines* or ask your IT admins for support. 

If you need support in making ReadStore available for users in your organization, reach out to info@evo-byte.com. We will find a solution for you!

### 4. Setup Admin acccount and first users

#### Change Admin password IMMEDIATELY!

Together with you ReadStore License Key you should have received a the login password for the Admin account.

1. Log into the User Interface with the username `admin` and the received password.
2. Move to the `Settings` page and click the `Reset Password` button.
3. Enter a new password and `Confirm`.
4. Login out and into the admin account again to validate the new password.

#### Enter you License Key

You need to enter you license key first before you can create Users.

1. Log into the Admin account
2. Move to the `Settings` page.
3. Click the `License Key` button. You should see information on the current status of you license.
4. Click `Enter New Key` and enter you license key and `Confirm`. 

This activates you license and you should see expiration date and the maximum number of user/seats in the `License Key` overview.

#### Create User(s)

1. Log into the Admin account, move to the `Admin` page.
2. Click the `Create` button to create a new user.
3. Add name, email and password. If the user should be allowed to upload FASTQ files you must enable `Staging Permissions`.
4. Click `Confirm` you should see the new user in the overview.

Users can change their password in the `Settings` page. The number of users is limited by the seats of your license.

### 5. Install the ReadStore Command Line Interface (CLI)

You need to install the ReadStore CLI if you want to upload FASTQ files and access ReadStore data from the CLI.

!!!! ADDReadStore CLI Repo reference

**NOTE** Uploading FASTQ files requires users to have `staging permission` set in their account.  

`pip3 install readstore-cli`

Validate successful install by running, which should print the version.

`readstore-cli -v`

You need to configure the ReadStore CLI client with your username and token.
You can find and change you user `token` in the User Interface in the `Settings` page. Click on `Token` to retrieve the token value.

Run

`readstore configure`

Enter you `username`, `token`, and your preferred output format `json, text or csv`.
Check the status of your CLI config with

`readstore configure list`

You should see the credentials you entered.

### Advanced ReadStore Basic Server Configuration<a id="advancedconfig"></a>

`readstore-server -h`

```
ReadStore Server

options:
  -h, --help            show this help message and exit
  --db-directory        Directory for Storing ReadStore Database.
  --db-backup-directory
                        Directory for Storing ReadStore Database Backups
  --log-directory       Directory for Storing ReadStore Logs
  --config-directory    Directory for storing readstore_server_config.yaml (~/.readstore)
  --django-port         Port of Django Backend
  --streamlit-port      Port of Streamlit Frontend
  --debug               Run In Debug Mode
```

ReadStore requires different directories for storing the database file, backups, logs and configurations. It is important to make sure that the user launching the ReadStore server has read and write permissions for each folder. The files created have user-exclusive read/write permissions (`chmod 600`) and it is important to ensure that permissions are kept restrictive.

You can run ReadStore in a more verbose `--debug` mode, which is not recommended.

#### Adapting Port Settings

ReadStores uses a Django Webserver and Streamlit Frontend with default ports 8000 and 8501. If other applications are running on these ports, change the respective ReadStore ports `--django-port` or `--streamlit-port` to an available port.

**NOTE** Changing ports requires users to connect to the User Interface using a different port. Users also need to update their default CLI/SDK configurations.

ADD!!!! Link repo update

#### Configure ReadStore with environment variables

In some cases you may want to setup ReadStore with environment variables, for instance if you run containers or cloud applications.

The following environment variables can be used to configure the ReadStore server

```
RS_DB_DIRECTORY         Corresponds to db-directory argument
RS_DB_BACKUP_DIRECTORY  Corresponds to db-backup-directory argument
RS_LOG_DIRECTORY        Corresponds to log-directory argument
RS_CONFIG_DIRECTORY     Corresponds to config-directory argument
RS_DJANGO_PORT          Corresponds to django-port argument
RS_STREAMLIT_PORT       Corresponds to streamlit-port argument

RS_PYTHON      Path to Python executable    (default: python3)
RS_STREAMLIT   Path to Streamlit executable (default: streamlit)
RS_GUNICORN    Path to Gunicorn executable  (default: gunicorn)
```

### Create ReadStore systemd Linux service<a id="systemd"></a>

Creating a Linux service has the several advantages for running the ReadStore server: 
This includes automatic restart of the ReadStore server in case of a restart, crash or update of your Linux instance.

You can find here a starting point for setting up a service using `systemd` but you may need superuser (`sudo`) privileges to actually start the service. Get in touch with you IT admins if you need support.

1. Check the `readstore.service` file provided here in the repository and adapt it with your environment configurations

    - `User`: Linux Username to run service. Will be the **Data Owner** for database files, logs, secrets and config.
    !!! ADD CHECK
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



## Usage

Detailed tutorials, videos and explanations are found on [YouTube](https://www.youtube.com/playlist?list=PLk-WMGySW9ySUfZU25NyA5YgzmHQ7yquv) or on the [**EVO**BYTE blog](https://evo-byte.com/blog).

### Quickstart

Let's upload some FASTQ files.

#### 1. Account Settings

Make sure you have the ReadStore CLI installed (s. above) and configured.
Run the command to check if your configuration is in place.

`readstore configure list`

For uploading FASTQ files your User Account needs to have `Staging Permission`. If you can check this in the `Settings` page of your account. If you not have `Staging Permission`, ask the ReadStore Server Admin to grant you permission.

#### 2. Upload Files

Move to a folder that contains some FASTQ files.

`readstore upload myfile_r1.fastq`

Will upload the file and run the QC check. You can select several files at once using the `*` wildcard.

#### 3. Stage Files

Login to the User Interface on your browser and move to the `Staging` page. Here you find a list of all FASTQ files you just upload. For large files the QC step can take a while to complete. FASTQ files are grouped in Datasets which you can `Check In`. Then they appear in the `Datasets` page and for instance be assigned to a Project.

#### 4. Access Datasets via the CLI

The ReadStore CLI enables programmatic access to Datasets and FASTQ files. Some examples are:

`readstore list` : List all FASTQ files

`readstore get --id 25` : Get detailed view on Dataset 25

`readstore get --id 25 --read1-path` : Get path for Read1 FASTQ file

`readstore get --id 25 --meta` : Get metadata for Dataset 25

`readstore project get --name cohort1 --attachment` : Get attachment files for Project "cohort1"

You can find a full list in the readstore documentation

## Contributing

Please feel free to create an issue for problems with the software or feature suggestions.

## License

ReadStore Basic Server is distributed under a commercial / proprietary license.
Details are found in the LICENSE file

ReadStore CLI is distributed under ?
ReadStore SDK is distributed under ?


## Credits and Acknowledgments<a id="acknowledgments"></a>

ReadStore is built upon the following open-source python packages and would like to thank all contributing authors, developers and partners.

- Django (https://www.djangoproject.com/)
- djangorestframework (https://www.django-rest-framework.org/)
- requests (https://requests.readthedocs.io/en/latest/)
- gunicorn (https://gunicorn.org/)
- pysam (https://pysam.readthedocs.io/en/latest/api.html)
- pyyaml (https://pyyaml.org/)
- streamlit (https://streamlit.io/)
- pydantic (https://docs.pydantic.dev/latest/)
- pandas (https://pandas.pydata.org/)




