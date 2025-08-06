# Goal

Develop a database application for managing next generation sequencing datasets and projects, and data analysis

# Implementation

## readstore_basic/readstore_server.py

- Add function to run the readstore_server.py python script without any mandatory command line argument in the directory from which the script is executed. In this case 3 folder are created for db-directory, db-backup-directory and log-directory. Each folder is prefixed by readstore-.
Make sure folders are successfully created. If folders with that name exists, then show a warning stating that directory path need to be specified with command line arguments. Then specify args.

- Validate that a help message is printed if user enters invalid argument, e.g. --db_directory instead of --db-directory

- Make the login optional. For this add a boolean --enable-login to argument parser. If that flag is false, then set 'global/enable_login' to false in readstore_server_config.yaml. If  true then create a random password and write it to a secret_default_user_key file in config_directory, and change to read only permissions. Add this key path as env variable. RS_DEFAULT_USER_KEY_PATH env. Run launch_backend with --create-default-user-with-password argument and password.

- If enable-login is true, then run launch_backend with --create-admin-user-with-password argument and initial password 'readstore'.


## readstore_basic/backend/setup_user.py

- Add an argument parser with arguments
    - One argument --create-default-user-with-password creates a User instance with username = 'default'. This user is part of appuser_group and staging_group. A password string must be passed to the argument as a string and set when instantiating the user. If an environement variable DEFAULT_USER_PWD is found, the overwrite the argument input through the parser.
    - One argument --create-admin-user-with-password creates a User instance with username = 'admin' and is_staff = True. This user is part of admin. A password string must be passed to the argument as a string and set when instantiating the user. If an environement variable ADMIN_USER_PWD is found, the overwrite the argument input through the parser.
- On both cases create a OwnerGroup with name 'default'. If an admin is created, the admin should be owner of OwnerGroup "default". If a default user but no admin is created, then the default user should be owner of OwnerGroup "default"


## readstore_basic/backend/launch_backend.py

- Add an argument parser with 
    
    - One argument --create-default-user-with-password creates a User instance with username = 'default'. This user is part of appuser_group and staging_group. A password string must be passed to the argument as a string and set when instantiating the user. If an environement variable DEFAULT_USER_PWD is found, the overwrite the argument input through the parser.
    
    - One argument --create-admin-user-with-password creates a User instance with username = 'admin' and is_staff = True. This user is part of admin. A password string must be passed to the argument as a string and set when instantiating the user. If an environement variable ADMIN_USER_PWD is found, the overwrite the argument input through the parser.
    
    - One argument --rs-config-path. If an environement variable RS_CONFIG_PATH is found, the overwrite the argument input through the parser. If not export the RS_CONFIG_PATH environment variable.
    
    - One argument --rs-key-path. If an environement variable RS_KEY_PATH is found, the overwrite the argument input through the parser. If not export the RS_KEY_PATH environment variable.
    
    - Invoke the setup_user.py command with the --create-default-user-with-password argument if no DEFAULT_USER_PWD is set and --create-default-user-with-password is passed in launch_backend.py
    
    - Invoke the setup_user.py command with the --create-admin-user-with-password argument if no ADMIN_USER_PWD is set and --create-admin-user-with-password is passed in launch_backend.py
