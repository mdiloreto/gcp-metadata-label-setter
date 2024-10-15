# GCP Metadata Label Setter and Project Retriever

This repository contains a set of Python scripts designed to automate the management of labels in GCP resources based on metadata and to retrieve information about GCP projects. The scripts are useful for cloud administrators and engineers who need to ensure resource compliance and organization.

## Overview

- **main.py**: This is the entry point script that orchestrates the setting of metadata-based labels on GCP resources within a specified organization. It initializes the process and calls other scripts as required.
- **set_gcp_metadata_based_labels.py**: This script contains the core functionality for fetching resource details and setting labels based on predefined metadata keys. It interacts with GCP APIs to retrieve resource information and update their labels accordingly.
- **get_all_projects.py**: This script handles the retrieval of all projects under a specific organization or without any organization filter. It lists all projects based on the organizational structure provided or available in the credentials scope.

## Detailed File Descriptions

### main.py

- **Purpose**: Serves as the starting point for the label setting operation.
- **Functions**:
  - Initializes the `SetMetadatabasedLabels` class.
  - Calls the `main` method of the class with the organization ID to process all projects under this organization.

### set_gcp_metadata_based_labels.py

- **Purpose**: Manages the application of labels to GCP resources based on their metadata.
- **Classes and Major Methods**:
  - `SetMetadatabasedLabels`: Main class that handles the operations.
    - `__init__`: Initializes class variables including a list of metadata keys.
    - `fetch_resources`: Retrieves resources from GCP using the Asset API.
    - `merge_labels`: Merges new labels with existing ones, ensuring no important labels are overwritten.
    - `main`: Orchestrates the fetching, merging, and updating of labels on resources.

### get_all_projects.py

- **Purpose**: Retrieves a list of all GCP projects, optionally within a specific organizational structure.
- **Classes and Major Methods**:
  - `GetGCPFoldersAndProjects`: Handles the retrieval of project and folder IDs.
    - `get_all_projects_in_folder`: Retrieves all projects within a given folder.
    - `get_all_projects_no_org`: Retrieves all projects when no specific organization is targeted.
    - `get_all_projects_with_org`: Retrieves all projects within an organization based on folder hierarchy.

## Setup and Requirements

1. Ensure you have Python installed on your system.
2. Install required Python packages:
3. Setup authentication by setting the GOOGLE_APPLICATION_CREDENTIALS environment variable to point to your service account key file.
4. Modify the organization_id in main.py to match your GCP organization ID.


## Usage

Run the `main.py` script to start the label setting process across your GCP resources:
```bash
python main.py
```
## Contributing
Contributions to this project are welcome. Please fork the repository and submit a pull request with your changes.

