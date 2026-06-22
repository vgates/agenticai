# Prerequisites

## Install Python

Visit https://www.python.org/downloads/ and follow the instructions as per your OS

## Install uv

uv is an extremely fast, all-in-one Python package and project manager written in Rust. Its a replacement for pip and virtualenv. It provides a seamless, unified command-line interface for the entire Python development lifecycle.

- Windows:
  `irm https://astral.sh/uv/install.ps1 | iex`
- macOS & Linux:
  `curl -LsSf https://astral.sh/uv/install.sh | sh`

Common uv commands

- Install packages: `uv pip install <package_name>`
- Create a virtual environment: `uv venv`
- Start a new project: `uv init <project_name>`
- Add a dependency: `uv add <package_name>`
- Run a script: `uv run script.py`
- Manage Python versions: `uv python install 3.13`
- Install from requirements.txt: `uv add -r .\requirements.txt`

## Create Virtual Environment

Creating a dedicated virtual environment is the absolute first step you should always take for any new project. if you don't create a virtual environment, packages are installed globally across your entire operating system. If Project A needs FastAPI version 0.100 and Project B needs FastAPI version 0.115, they will overwrite each other and break your applications. A virtual environment (.venv) creates an isolated sandbox directory inside your project folder so your dependencies never clash.

### Create a directory for your project and cd into that

Create the Virtual Environment. Run the following command. uv will instantly create a folder named .venv inside your project directory. This folder contains a completely isolated, standalone copy of the Python executable.
`uv venv`

### Activate the Virtual Environment

Before you install packages, you must tell your terminal session to use this new isolated sandbox instead of your system's global Python.

- macOS or Linux:
  `source .venv/bin/activate`

- Windows (Command Prompt):
  `.venv\Scripts\activate`
