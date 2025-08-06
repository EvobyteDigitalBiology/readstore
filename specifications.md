# Goal

Develop a database application for managing next generation sequencing datasets and projects, and data analysis

# Implementation

## readstore_basic/readstore_server.py

- Add function to run the readstore_server.py python script without any mandatory command line argument in the directory from which the script is executed. In this case 3 folder are created for db-directory, db-backup-directory and log-directory. Each folder is prefixed by readstore-.
Make sure folders are successfully created. If folders with that name exists, then show a warning stating that directory path need to be specified with command line arguments. Then specify args.

- Validate that a help message is printed if user enters invalid argument, e.g. --db_directory instead of --db-directory

- Make the login optional

## readstore_basic/readstore_server.py

