# Changelog

## v1.4.0 - 2025-02-10

**Added**

- ProData page in dashboard

**Changed**

- Improved database storage of attachment files

**Bugfix**
- Change tab layout for better transistions in detail view

## v1.3.6 - 2025-01-10

**Added**

- Improved validation of API requests
- Adapted error message if user is inactive

**Changed**

- Selection of existing empty datasets to attach FASTQ files in staging area to

**Bugfix**

- Validate file path for upload of FASTQ files from template files. Only accept template upload if ALL FASTQ file path are found
- Error when updating readstore_config.yaml during update cycles

## v1.3.3/v1.3.4 - 2024-12-23

**Bugfix**

- Install Process Validation of Requirements

## v1.3.2 - 2024-12-23

**Changed**

- Require update Django Rest Framework

**Bugfix**

- Install Process Validation of Requirements

## v1.3.2 - 2024-12-21

**Bugfix**

- Install Process

## v1.3.0 - 2024-12-20

**Added**

- Create API Endpoints to create, update, and delete Projects, Datasets, FASTQ files via the CLI
- Crete Datasets from ReadStore Web App
- Options to check-in staged FASTQ Files to existing Datasets
- Attachent also work for Batch Import 
- Add new filter options for metadata
- Option to transfer ownership of objects like datasets between users

**Changed**

- Re-enter new password required when changing or resetting User passwords
- Align formatting of Project and Dataset dialogs
- Update streamlit settings to 1.41

**Removed**

## v1.2.0 - 2024-12-01

**Added**

- Management of Processed Data (ProData)
- Extend Dataset App page with ProData functions
- Add RSClientTokenAuth Token Based View Authentication
- Add option RSClientHasStaging
- Add automatic validation of file paths stored in ReadStore DB

**Changed**

- New endpoint for external API calls (api_x_v1)
- Update streamlit settings to 1.40

**Removed**
- Deprecate/token API mechanism

## v1.1.0 - 2024-11-14

**Added**

- Support for batch Check In of many FASTQ files
- Batch Upload of FASTQ files from Excel or csv files
- Batch delete function
- Frontend performance improvements

**Changed**

- Option to select multiple datasets and projects

**Removed**

## v1.0.3  - 2024-11-06

**Added**

**Changed**

- Fix: Python version in setup
- Doc: Minor documentatation

**Removed**

## v1.0.2

**Added**

**Changed**

- Fix: Performance related Backend Updates
- Refactor: Sizing of attachment detail fields and download button

**Removed**


## v1.0.1

**Added** - 2024-10-31

**Changed**

- Fix: Hide dataset update button if no dataset is selected

**Removed**

## v1.0.0 - 2024-10-30

Initial Version