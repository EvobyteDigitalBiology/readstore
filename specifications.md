# Goal

Develop a database application for managing next generation sequencing datasets and projects, and data analysis

# Implementation

## readstore_basic/readstore_server.py

- Add function to run the readstore_server.py python script without any mandatory command line argument in the directory from which the script is executed. In this case 3 folder are created for db-directory, db-backup-directory and log-directory. Each folder is prefixed by readstore-.
Make sure folders are successfully created. If folders with that name exists, then show a warning stating that directory path need to be specified with command line arguments. Then specify args.

- Validate that a help message is printed if user enters invalid argument, e.g. --db_directory instead of --db-directory

- Make the login optional

## readstore_basic/backend/setup_user.py

- Add an argument parser with arguments
    - One argument --create-default-user creates a User instance with username = 'default'. This user is part of appuser_group and staging_group. A password string must be passed to the argument as a string and set when instantiating the user. If an environement variable DEFAULT_USER_PWD is found, the overwrite the argument input through the parser.
    - One argument --create-admin-user creates a User instance with username = 'admin' and is_staff = True. This user is part of admin. A password string must be passed to the argument as a string and set when instantiating the user. If an environement variable ADMIN_USER_PWD is found, the overwrite the argument input through the parser.
- On both cases create a OwnerGroup with name 'default'. If an admin is created, the admin should be owner of OwnerGroup "default". If a default user but no admin is created, then the default user should be owner of OwnerGroup "default"