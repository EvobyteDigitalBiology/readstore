# Goal

Develop a database application for managing next generation sequencing datasets and projects, and data analysis

# Implementation

## readstore_basic/readstore_server.py

- Add function to run the readstore_server.py python script without any mandatory command line argument in the directory from which the script is executed. In this case 3 folder are created for db-directory, db-backup-directory and log-directory. Each folder is prefixed by readstore-.
Make sure folders are successfully created. If folders with that name exists, then do use those folders as input arguments for db-directory, db-backup-directory and log-directory respectively.

- Validate that a help message is printed if user enters invalid argument, e.g. --db_directory instead of --db-directory

- Make the login optional. For this add a boolean --enable-login to argument parser. If that flag is false, then set 'global/enable_login' to false in readstore_server_config.yaml. If  true then create a random password and write it to a secret_default_user_key file in config_directory, and change to read only permissions. Add this key path as env variable. RS_DEFAULT_USER_KEY_PATH env. Run launch_backend with --create-default-user-with-password argument and password.

- If enable-login is true, then run launch_backend with --create-admin-user-with-password argument and initial password 'readstore'.


## readstore_basic/backend/setup_user.py

- Add an argument parser with arguments
    
    - One argument --create-default-user-with-password creates a AppUser instance with username = 'default'. This user is part of appuser_group and staging_group. A password string must be passed to the argument as a string and set when instantiating the user. If an environement variable DEFAULT_USER_PWD is found, the overwrite the argument input through the parser.
    
    - One argument --create-admin-user-with-password creates a User instance with username = 'admin' and is_staff = True. This user is part of admin. A password string must be passed to the argument as a string and set when instantiating the user. If an environement variable ADMIN_USER_PWD is found, the overwrite the argument input through the parser.
    
    - One argument --create-examples creates a Project instance with name "hello_readstore_project" and description "This is you first ReadStore Project". Metadata JSON must be {"project_owner":  "John Doe", "project_start": "2025-05-05"}. dataset_metadata_keys is a JSON with {"species": "", "assay": ""}. owner_group is "default" OwnerGroup.
    
    It also creates a dataset with name "hello_dataset" and description "This is your first ReadStore dataset. It is part of the hello_readstore_project project and has no FASTQ files attached". project is set to project hello_readstore_project defined above. metadata fields are set to {"species": "mus musculus", "assay": "RNA-Seq"}.

- On both cases create a OwnerGroup with name 'default'. If an admin is created, the admin should be owner of OwnerGroup "default". If a default user but no admin is created, then the default user should be owner of OwnerGroup "default"


## readstore_basic/backend/launch_backend.py

- Add an argument parser with 
    
    - One argument --create-default-user-with-password creates a User instance with username = 'default'. This user is part of appuser_group and staging_group. A password string must be passed to the argument as a string and set when instantiating the user. If an environement variable DEFAULT_USER_PWD is found, the overwrite the argument input through the parser.
    
    - One argument --create-admin-user-with-password creates a User instance with username = 'admin' and is_staff = True. This user is part of admin. A password string must be passed to the argument as a string and set when instantiating the user. If an environement variable ADMIN_USER_PWD is found, the overwrite the argument input through the parser.
    
    - One argument --rs-config-path. If an environement variable RS_CONFIG_PATH is found, the overwrite the argument input through the parser. If not export the RS_CONFIG_PATH environment variable.
    
    - One argument --rs-key-path. If an environement variable RS_KEY_PATH is found, the overwrite the argument input through the parser. If not export the RS_KEY_PATH environment variable.
    
    - Invoke the setup_user.py command with the --create-default-user-with-password argument if no DEFAULT_USER_PWD is set and --create-default-user-with-password is passed in launch_backend.py
    
    - Invoke the setup_user.py command with the --create-admin-user-with-password argument if no ADMIN_USER_PWD is set and --create-admin-user-with-password is passed in launch_backend.py
 

## readstore_basic/backend/app/ext_views.py

- The `authentication_classes` attribute for each view class in `ext_views.py` should be configurable from `readstore_server_config.yaml` `enable_API_token` parameter.
If started without login_enabled. The `enable_API_token` should be set in `settings/development.py` and `settings/production.py`.


## readstore_basic/frontend/streamlit/app.py

- Modification of the login process. 

Check if `uiconfig.ENABLE_LOGIN` is False, i.e. if default login should be used. If so add a check to see of the the secret_default_user_key file is found at the uiconfig.CONFIG_DIR and if file can be read.
Read the default user password from the file and run extensions.get_jwt_token with password and username "default". If the file could not be read return an error.
For the above login process restructure the `login.py` auth process (obtaining tokens, validating endpoints, starting thread) into the `extensions.py` file function to have a reusable login function.

Change the logic of the page rendering. If `uiconfig.ENABLE_LOGIN` and auth status is true then show pages project_page, dataset_page, pro_data_page, staging_page. If `auth_status` is false then show an error. 
If `uiconfig.ENABLE_LOGIN` is false then keep the login as is, and if `auth_status` is false then show login.

Remove the license key check `datamanager.valid_license`.