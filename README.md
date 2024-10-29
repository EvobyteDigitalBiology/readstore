# ReadStore Basic

This README introduces ReadStore Data Platform, the lean solution for managing FASTQ and NGS data.

**Please read and follow the instructions carefully**. In particular the [Security, Permissions and Backup](#backup) section contains important information related to data security and backup.

You need a license key for using ReadStore Basic, please check the [ReadStore website](https://https://evo-byte.com/readstore/) for more information or reach out to license@evo-byte.com

Tutorials and Intro Videos: https://www.youtube.com/@evobytedigitalbio

Blog posts and How-Tos: https://evo-byte.com/blog/

For general questions reach out to info@evo-byte.com

Happy analysis :)

## Table of Contents
- [Description](#description)
- [Security, Permissions and Backup](#backup)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Credits and Acknowledgments](#acknowledgments)

## The Lean Solution for Managing FASTQ and NGS Data

ReadStore is a platform for storing, managing, and integrating genomic data. It speeds up analysis and offers a simple way of managing and sharing FASTQ and NGS datasets. Built-in project and metadata management structures your workflows, and a collaborative web app enhances teamwork — so you can focus on generating insights.

The integrated Webservice enables you to directly retrieve data from ReadStore via the terminal Command-Line Interface (CLI) or Python/R SDKs.

The ReadStore Basic version offered here provides a local web server with simple user management. If you need organization-wide deployment, advanced user and group management, or cloud integration, please check the ReadStore Advanced versions and reach out to info@evo-byte.com.

## Description

ReadStore facilitates managing FASTQ files and NGS data, along with experimental (meta)data. It provides a database and a web app with a simple user interface to create and edit datasets and projects. You can create your own structure using metadata key-value pairs (e.g., replicate: 1 or condition: control) or attach files as additional information.

Metadata and attachments can be accessed along with your NGS datasets from analysis scripts or data pipelines, providing consistent workflow automation.

ReadStore Basic enables you to manage NGS data from your local Linux environment and can be set up in a few minutes. It comprises a local web server and web app that you can connect to via your browser to explore and edit your NGS experiments.

To upload FASTQ files into the ReadStore database, you’ll also need to install the ReadStore CLI, which offers a connection through your command line.

Logging into the ReadStore web app via the browser requires a user account, which is created by an admin.

ReadStore Basic provides a shared work environment for all registered users. Users can collaborate on editing datasets, projects, metadata, and attachments, with shared access to all resources. This facilitates cross-functional projects, connecting data analysts and experimental researchers.

If you would like to have more advanced user, group, and permission management, please reach out for a demo of the ReadStore Advanced version.

## Security, Permissions and Backup<a id="backup"></a>

**PLEASE READ AND FOLLOW THESE INSTRUCTIONS CAREFULLY!**

ReadStore Basic comes with simple security and permission management based on Linux file permissions, which govern access to the ReadStore database.

### Database Permissions <a id="permission"></a>

The Linux user running the `readstore-server` is, by default, the **Data Owner**. In this role, the **Data Owner** has exclusive read/write permissions (`chmod 600`) to the database files, database backups, secret key, and ReadStore configuration.

The **Data Owner** must ensure that access rights to these files remain restricted to prevent unauthorized access to the ReadStore database (see [Installation](#installation)). By default, the secret key and configuration files are stored in your home directory (`~/.rs-server/`), but you can change the `--config-directory` to specify a different folder path.

The ReadStore secret key is located in your `--config-dir` (default `~/.rs-server/secret_key`). It is recommended to **keep a secured copy of the secret key** to allow access to backups or restore the database in case of an incident.

### Admin Account

Upon the first launch of the ReadStore Basic web server, the Admin account is created with a password provided along with your license key.

The **Admin must change the Admin password immediately** upon the first login.


### User Account Passwords and Tokens

To log in to the ReadStore web app via a web browser, each **User** needs a user account. User accounts are created by the **Admin** from within the web app. The Admin sets an account password when creating new users. Each **User** can later change their account password.

Each **User** has a unique **Token** assigned, which is required to connect to ReadStore via the Command-Line Interface (CLI) or through the Python and R SDKs. This token should not be shared. Tokens can be easily regenerated from the Settings page in the ReadStore CLI.

A **User** is required to have **staging permissions** to upload FASTQ files into the ReadStore database.

See [Installation](#installation) for instructions how to setup Users

### Backups

ReadStore automatically performs regular backups. The backup directory (see Installation) should be different from the database directory. ReadStore logs are also saved to a predefined folder. Each folder should have sufficient space to store database, backup, and log files.

### Deployment and Server Configurations

**You are responsible for hosting and deploying the ReadStore server in a secure environment**. This includes, but is not limited to, access management, active firewall protection of your servers, and regular patching of your operating system.

If you need a ReadStore version with more advanced permission and group management, database server support, or customization for your infrastructure, please reach out.

## Installation

### 1. Install the ReadStore Basic Server

`pip3 install readstore-basic`

You can perform the install in a conda or venv virtual environment to simplify package management.

A local install is also possible

`pip3 install --user readstore-basic`

Make sure that `~/.local/bin` is on your `$PATH` in case you encounter problems when starting the server.

Validate the install by running

`readstore-server -v`

This should print the ReadStore Basic version

### 2. Start the Webserver

#### Prepare Output Folders 

Create output folders for the ReadStore database files (`db-directory`), the backups (`db-backup-directory`) and log files (`log-directory`).

All ReadStore database, backup and log files are created with user-exclusive read/write permissions (`chmod 600`) when starting the ReadStore server for the first time. Make sure that restricted permissions are maintained to avoid unwanted access to database files.

The readstore configuration files and secret key are by default written to you home dir `~/.rs-server` (user-exclusive read/write permissions `chmod 600`). You can specify another `config-directory`. Ensure restricted permissions for this folder and files. It is recommended to create a [secure backup of the secret key](#permission) 

#### Start the Server

`readstore-server --db-directory /path/to/database_dir --db-backup-directory /path/to/backup_dir --log-directory /path/to/logs_dir`

ReadStore Server requires ports 8000 and 8501. See [below](#advancedconfig) if there is a problem with blocked ports.

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

The ReadStore web app should be available via your browser under localhost port 8501 (`http://127.0.0.1:8501` or `http://localhost:8501/`). You should see a login screen.

**NOTE** The port can change depending on your server settings (s. [below](#advancedconfig)).

#### Access ReadStore Web App via SSH Tunnel

If you run ReadStore Basic on a Linux server that you connect to via SSH, consider using SSH tunneling / port forwarding to access the server port 8501 from your local machine's browser (Tutorial: https://linuxize.com/post/how-to-setup-ssh-tunneling/). Tools like PuTTY help Windows users to easily set up SSH tunnels (https://www.putty.org/).

In any case make sure that server connections are established *in agreement with your organizations IT security guidelines* or ask your IT admins for support. 

If you need support in making ReadStore available for users in your organization, reach out to info@evo-byte.com. We will find a solution for you!

### 4. Setup Admin Account and First Users

#### Change your Admin password IMMEDIATELY!

Together with you ReadStore License Key you should have received a the login password for the Admin account.

1. Log into the web app with the username `admin` and the received admin password
2. Move to the `Settings` page and click the `Reset Password` button
3. Enter a new password and `Confirm`
4. Login out and into the admin account again to validate the new password

#### Enter your License Key

You need to enter your license key before you can create users.

1. Log into the Admin account
2. Move to the `Settings` page
3. Click the `License Key` button. You should see information on the current status of you license
4. Click `Enter New Key` and enter you license key and `Confirm`

This activates your license and you should see an expiration date and the maximum number of user/seats in the `License Key` overview.

#### Create new User(s)

1. Log into the Admin account, move to the `Admin` page
2. Click the `Create` button to create a new user
3. Add name, email and password. If the user should be allowed to upload FASTQ files you must enable `Staging Permissions`
4. Click `Confirm`. You should see the new user in the overview

Users can change their password in their `Settings` page. The number of users is limited by the seats of your license.

### 5. Install the ReadStore Command Line Interface (CLI)

You need to install the ReadStore CLI if you want to upload FASTQ files and access ReadStore data from the CLI.

For more information check the [ReadStore CLI GitHub Repository](https://github.com/EvobyteDigitalBiology/readstore-cli)

**NOTE** Uploading FASTQ files requires users to have `staging permission` set in their account.  

#### Install Command

`pip3 install readstore-cli`

Validate successful install by running

`readstore-cli -v`

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
  --config-directory    Directory for storing readstore_server_config.yaml (~/.rs-server)
  --django-port         Port of Django Backend
  --streamlit-port      Port of Streamlit Frontend
  --debug               Run In Debug Mode
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



## Usage

Detailed tutorials, videos and explanations are found on [YouTube](https://www.youtube.com/playlist?list=PLk-WMGySW9ySUfZU25NyA5YgzmHQ7yquv) or on the [**EVO**BYTE blog](https://evo-byte.com/blog).

### Quickstart

Let's upload some FASTQ files.

#### 1. Account Settings

Make sure you have the [ReadStore CLI](https://github.com/EvobyteDigitalBiology/readstore-cli) installed and configured (s. [Installation](#installation)).

Run the command to check if your configuration is in place.

`readstore configure list`

For uploading FASTQ files your User Account needs to have `Staging Permission`. Check this in the `Settings` page of your account. If you do not have `Staging Permission`, ask the Admin to grant you permission.

#### 2. Upload Files

Move to a folder that contains some FASTQ files.

`readstore upload myfile_r1.fastq`

This will upload the file and run the QC check. You can select several files at once using the `*` wildcard.

#### 3. Stage Files

Login to the User Interface on your browser and move to the `Staging` page. Here you find a list of all FASTQ files you just upload.

For large files the QC step can take a while to complete. FASTQ files are grouped in Datasets which you can `Check In`. Then they appear in the `Datasets` page.

#### 4. Access Datasets via the CLI

The ReadStore CLI enables programmatic access to Projects, Datasets, metadata and attachments.

Some examples commands are:

`readstore list` : List all FASTQ files

`readstore get --id 25` : Get detailed view on Dataset 25

`readstore get --id 25 --read1-path` : Get path for Read1 FASTQ file

`readstore get --id 25 --meta` : Get metadata for Dataset 25

`readstore project get --name cohort1 --attachment` : Get attachment files for Project "cohort1"

You can find a full documentation in the [ReadStore CLI Repository](https://github.com/EvobyteDigitalBiology/readstore-cli)

## Contributing

Please feel free to create an issue for problems with the software or feature suggestions.

## License

ReadStore Basic Server is distributed under a commercial/proprietary license.
Details are found in the LICENSE file.

You need a license key for using ReadStore Basic, please check the ReadStore website for more information or reach out to license@evo-byte.com. Using ReadStore Basic without a valid license key is not permitted.

ReadStore CLI is distributed under an Open Source Apache 2.0 License. 

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




