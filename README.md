# RLMF Scripts - Evaluation Viewer

This directory contains scripts for the RLMF project. The primary script detailed here is `view_evaluations.py`, a Streamlit application designed to view and browse evaluation data.

This project uses [uv](https://astral.sh/uv) for Python package management and virtual environments.

## Prerequisites

- Python 3.10 (as specified in `.python-version`)
- [uv](https://astral.sh/uv) installed

## Setup Instructions

1.  **Navigate to the script directory**:
    Open your terminal and change to the `rlmf_scripts` directory:

    ```bash
    cd path/to/your/rlmf_scripts
    ```

2.  **Create a virtual environment**:
    Use `uv` to create a virtual environment. It will attempt to use Python 3.10 if available.

    ```bash
    uv venv
    ```

    If you need to specify your Python 3.10 interpreter:

    ```bash
    uv venv -p /path/to/your/python3.10
    ```

3.  **Activate the virtual environment**:

    - On macOS and Linux:
      ```bash
      source .venv/bin/activate
      ```
    - On Windows (Command Prompt):
      ```bash
      .venv\Scripts\activate.bat
      ```
    - On Windows (PowerShell):
      ```powershell
      .venv\Scripts\Activate.ps1
      ```

4.  **Install dependencies**:
    Install all required packages listed in `pyproject.toml`:
    ```bash
    uv sync
    ```

## Configuration

The `view_evaluations.py` script requires access to an `evaluations.json` data file. The path to the directory containing this file is specified by the `DATA_DIR` environment variable.

1.  **Download the data file**:

    - Download the JSON file from the following link:
      [Download Evaluation Data](https://bytedance.larkoffice.com/drive/folder/Rh8QfxDL4lvozld19cVcf5Vgn8e?from=from_copylink)
    - Rename the downloaded file to `evaluations.json`.

2.  **Set up `DATA_DIR`**:

    - Create a directory anywhere accessible by the script where you will store `evaluations.json`. Let's call this your `<your_data_directory_path>`.
    - Place the renamed `evaluations.json` file into this `<your_data_directory_path>`.

3.  **Inform the script about `DATA_DIR`**:
    You need to set the `DATA_DIR` environment variable to point to `<your_data_directory_path>`. You can do this by creating a `.env` file in the `rlmf_scripts` directory: - Create a file named `.env` in the `rlmf_scripts` directory. - Add the following line to the `.env` file, replacing `<your_data_directory_path>` with the actual path to the directory you created in step 2:
    `env
DATA_DIR=<your_data_directory_path>
`
    For example, if you created a directory `../my_rlmf_data` (relative to `rlmf_scripts`) and placed `evaluations.json` there, your `.env` file would contain:
    `env
DATA_DIR=../my_rlmf_data
`
    Or, if you used an absolute path like `/Users/yourname/rlmf_data_store`:
    `env
DATA_DIR=/Users/yourname/rlmf_data_store
`
    The script uses `python-dotenv` to load this configuration automatically when it starts.

## Running the Evaluation Viewer

Once the setup and configuration are complete, and with the virtual environment activated:

1.  **Run the Streamlit application**:
    ```bash
    streamlit run view_evaluations.py
    ```
    This will start the Streamlit server, and you should be able to access the application in your web browser (usually at `http://localhost:8501`).

## Features

The Evaluation Viewer allows you to:

- View detailed information for each evaluation entry.
- Navigate between evaluations using "Previous" and "Next" buttons.
- Search for specific evaluations by "task ID".

## Project Structure

Below is an example of how your project directory might be structured. The key is the location of your `DATA_DIR` (which can be anywhere accessible) and the `evaluations.json` file within it, along with the `rlmf_scripts` directory.

```
<project_root>/
├── <your_data_directory_path>/      <-- This is the directory you set as DATA_DIR
│   └── evaluations.json             <-- Downloaded and renamed file goes here
│
├── rlmf_scripts/                    <-- Current directory for these scripts
│   ├── .venv/                       <-- Virtual environment (created by uv venv )
│   ├── .env                         <-- Configuration file where you define DATA_DIR
│   ├── .gitignore
│   ├── .python-version
│   ├── README.md                    <-- This file
│   ├── pyproject.toml               <-- Project dependencies for uv
│   ├── uv.lock                      <-- Lock file (created by uv sync )
│   └── view_evaluations.py          <-- The Streamlit application
│
├── (other_project_files_...)
```

**Explanation:**

- **`<project_root>/`**: The main folder containing your overall RLMF project.
- **`<your_data_directory_path>/`**: This is the directory you choose to store your data. You will set the `DATA_DIR` environment variable (in `rlmf_scripts/.env`) to point to this path.
  - `evaluations.json`: The evaluation data file you download and rename, placed inside your chosen `DATA_DIR`.
- **`rlmf_scripts/`**: The directory containing the evaluation viewer script and its related files.
  - `.env`: You create this file inside `rlmf_scripts/` to specify `DATA_DIR=<your_data_directory_path>`.
  - Other files like `view_evaluations.py`, `pyproject.toml`, etc., are part of the scripting environment.

This structure ensures that the `view_evaluations.py` script can locate the `evaluations.json` file by reading the `DATA_DIR` path from the `.env` file.
