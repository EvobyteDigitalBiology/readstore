# ReadStore


## Table of Contents
- [Description](#description)
- [Security, Permissions and Backup](#backup)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Credits and Acknowledgments](#acknowledgments)

## The Lean Solution for Managing FASTQ and NGS Data

ReadStore is a platform for storing, managing, and integrating genomic data. It speeds up analysis and offers a secure way of managing and sharing FASTQ and NGS datasets. Built-in project and metadata management structures your workflows and a collaborative user interface enhances teamwork — so you can focus on generating insights.

The integrated Webservice enables your to directly retrieve data from ReadStore via the terminal Command-Line-Interface (CLI) or Python / R SDKs.

The ReadStore Basic version offered here provides a local webserver and simple user management. If you would like access to organization-wide deployment, advanced user and group management or cloud integration please check the ReadStore Advanced versions. Reach out to info@evo-byte.com to learn more. 

## Description

ReadStore facilitates managing FASTQ files and NGS datasets together with experimental (meta)data. For this, ReadStore provides a database and a simple User Interface to create and edit Datasets and Projects. You can create your own structure by using metadata key-value pairs (e.g. replicate: 1, or condition: control), or attach files as additional information. 

Metadata and attachments can be access along with your NGS datasets from analysis scripts or data pipelines, providing a consistent automation of your workflows.

ReadStore Basic enables you manage NGS data from your local Linux environment and can be setup in a few minutes. ReadStore Basic comprises a local Webserver and User Interface that you can connect to via you browser in order to explore and edit your NGS experiments.

In order to upload FASTQ files into the ReadStore database, you also need to install the ReadStore CLI that offers a connection via your command line.

Login to the ReadStore User Interface via the browser requires a user account. User accounts are created by the Admin. 

ReadStore Basic provides a shared work environment for all registered users. Users can collaborate on editing Datasets, Projects, metadata and attachments and have shared access to all resources. This facilitates cross-functional projects and connects data analysts and experimental researchers.

If you would like to have more advances user, group and permission management, please reach out for an demo of the ReadStore Advanced version.

## Security, Permissions and Backup<a name="backup"></a>

ReadStore Basic comes with simple security and permission management based on file permissions, which govern access to the ReadStore sqlite3 database.  

### Database Permissions

The Linux user running the webserver is by default the data owner. In this role the user has exclusive read/write permissions (0o600) to the database file, database backups, secret key and ReadStore configuration.

The data owner must ensure that access rights to the mentioned files remain restricted, otherwise unauthorized access to the ReadStore database can be possible (s. Installation).

### Admin Account

Upon first launch of the ReadStore Basic Webserver, the Admin account is created with a default password. The admin or data owner must CHANGE THE ADMIN PASSWORD immediately on first login. 

### Backups

ReadStore is automatically performing regular backups. The backup directory (s. Installation) should be different from the database directory. ReadStore Logs are also saved to a predefined folder. Each folder should have sufficient space to save database, backup and log files.

If you need more advanced permission management, please reach out for the ReadStore Advanced versions.

## Installation

### 1. Install the ReadStore Basic Server

`pip3 install readstore-basic`

You can perform the install in a conda or venv virtual environment to simplify package management.

### 2. Start the Webserver

Create output folders for the ReadStore database files (`db-directory`), the backups (`db-backup-directory`) and log files (`log-directory`).

The readstore configuration files and secret key are by default written to you home dir `~/.readstore` (user-only read/write permissions `0o600`). You can specify another `config-directory`. Ensure restricted permissions for this folder.

#### Start the server

`readstore-server --db-directory /path/to/database_dir --db-backup-directory /path/to/backup_dir --log-directory /path/to/logs_dir`

ReadStore Server requires ports 8000 and 8501. See below if there are issues with blocked ports.

### 3. Connect to the ReadStore User Interface with your Browser

After the launch of the webserver you should to be able to connect to the ReadStore Web App and User Interface with your local browser.

The ReadStore User Interface should be available via your browser under localhost port 8501 (`http://127.0.0.1:8501` or `http://localhost:8501/`). You should see a login screen.

NOTE: The port can differ depending on your server settings (s.below).

#### ReadStore via SSH

If you run ReadStore Basic on a Linux server that you connect to via SSH, consider using SSH tunneling / port forwarding (https://linuxize.com/post/how-to-setup-ssh-tunneling/) to access the server port 8501 from your local machines browser. Tools like PuTTY (https://www.putty.org/) help Windows users to easily create SSH tunnels.

In any case make sure that server connections are established *in agreement with your organizations IT security guidelines* or ask your IT admins for support. 


### 4. Setup Admin acccount and first users

#### Change Admin password IMMEDIATELY!

Together with you ReadStore License Key you should have received a default login password for the Admin account.

Log into the User Interface with the username `admin` and the default password. Move to the `Settings` page and click the `Reset Password` button. Enter a new password and confirm.

Login out and into the admin account again to validate the new password.

#### Enter you License Key

You need to enter you license key first. After logging into the Admin account, move to the `Settings` page. Click the `License Key` button. You should see information on the current status of you license. Click `Enter New Key` and enter you license key and confirm. This activates you license and you should see an overview of expiration and the maximum number of user/seats in the `License Key` overview.

#### Create User(s)

After logging into the Admin account, move to the `Admin` page. Here you can click the `Create` button to create a new user. Add name, email and password. If the user should be allowed to upload FASTQ files using the ReadStore CLI, you must enable `Staging Permissions`. After confirm you should see the new user in the overview. User can change their password themselves afterwards.
The number of users is limited by the seats / users of your license.

### 5. Install the ReadStore Command Line Interface (CLI)

Each user who wants to upload FASTQ files and access NGS datasets from the ReadStore database from the command line needs the CLI installed. 

`pip3 install readstore-cli`

You need to configure the ReadStore CLI client with your username and token.
You can find and change you user `token` in the User Interface in the `Settings` page. Click on `Token` to retrieve the token value.

`readstore configure`

Enter you `username`, `token`, and your preferred output format `json, text or csv`.
Check the status of your CLI config with

`readstore configure list`

### Advanced ReadStore Basic Server Configuration 

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

ReadStore requires different directories for storing the database file, backups, logs and configurations. It is important to make sure that the user launching the ReadStore server has read and write permissions for each folder. The files created have user-exclusive read/write permissions `0o600` and it is important ensure that permissions are kept restrictive.

ReadStores uses a Django Webserver and Streamlit Frontend with default ports 8000 and 8501. If other applications are running on this ports, change the respective ReadStore ports `--django-port` or `--streamlit-port` to a free port.

You can run ReadStore in a more verbose `--debug`, but that is generally not recommended.

## Usage

Detailed tutorials, videos and explanations are found on YouTube (https://www.youtube.com/playlist?list=PLk-WMGySW9ySUfZU25NyA5YgzmHQ7yquv) or on the EVOBYTE blog (https://evo-byte.com/blog).

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


## Credits and Acknowledgments<a name="acknowledgments"></a>

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




