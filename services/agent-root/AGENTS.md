<!--
 Copyright 2025 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
-->

# Gemini Agent Guide

This document provides a guide for a Gemini agent to effectively use the commands in the `Makefile`.

## Overview

The `Makefile` provides a set of commands to manage the microservice development lifecycle. It simplifies common tasks such as setting up the development environment, running tests, building and deploying the service.

## Commands

### `make all`

*   **Description**: This is the default command that is run when `make` is executed without any arguments. It displays the help message.
*   **Dependencies**: `help`
*   **Example**: `make`

### `make venv`

*   **Description**: Creates a Python virtual environment.
*   **Dependencies**: None
*   **Example**: `make venv`

### `make upgrade-pip`

*   **Description**: Upgrades the `pip` installer within the virtual environment.
*   **Dependencies**: `venv`
*   **Example**: `make upgrade-pip`

### `make install`

*   **Description**: Installs runtime dependencies for the service.
*   **Dependencies**: `venv`, `pyproject.toml`
*   **Example**: `make install`

### `make install-dev`

*   **Description**: Installs development and testing dependencies.
*   **Dependencies**: `venv`, `pyproject.toml`
*   **Example**: `make install-dev`

### `make install-docs`

*   **Description**: Installs documentation-specific dependencies.
*   **Dependencies**: `venv`, `pyproject.toml`
*   **Example**: `make install-docs`

### `make install-all`

*   **Description**: Installs all runtime, development, and documentation dependencies.
*   **Dependencies**: `install`, `install-dev`, `install-docs`
*   **Example**: `make install-all`

### `make upgrade`

*   **Description**: Upgrades all runtime dependencies.
*   **Dependencies**: `venv`, `upgrade-pip`
*   **Example**: `make upgrade`

### `make update-branch`

*   **Description**: Refreshes local remote-tracking Git branches.
*   **Dependencies**: None
*   **Example**: `make update-branch`

### `make run`

*   **Description**: Runs the local ADK agent development server. This is an interactive command and will block the terminal.  Do not run this as a coding agent, run `make run-background` instead.
*   **Dependencies**: `install`
*   **Example**: `make run`

### `make run-background`

*   **Description**: Runs the local ADK agent development server in the background. This is a non-interactive command.
*   **Dependencies**: `install`
*   **Example**: `make run-background`

### `make stop-background`

*   **Description**: Stops the background ADK agent development server.
*   **Dependencies**: None
*   **Example**: `make stop-background`

### `make tests`

*   **Description**: Executes unit and integration tests.
*   **Dependencies**: `install`, `install-dev`
*   **Example**: `make tests`

### `make coverage`

*   **Description**: Runs tests and generates a code coverage report.
*   **Dependencies**: `install`, `install-dev`
*   **Example**: `make coverage`

### `make lint`

*   **Description**: Runs code linting checks.
*   **Dependencies**: `install`, `install-dev`
*   **Example**: `make lint`

### `make format`

*   **Description**: Formats the code using configured formatters.
*   **Dependencies**: None
*   **Example**: `make format`

### `make docs`

*   **Description**: Generates API documentation for the service.
*   **Dependencies**: `install-docs`, `install`, `coverage`, `tests`
*   **Example**: `make docs`

### `make clean`

*   **Description**: Cleans up the environment by removing virtual environments, build artifacts, and cache directories.
*   **Dependencies**: None
*   **Example**: `make clean`

### `make deploy`

*   **Description**: Deploys the ADK agent to the Agent Engine.
*   **Dependencies**: `install`
*   **Example**: `make deploy`

### `make gcloud-check`

*   **Description**: Checks and displays the active Google Cloud Platform (GCP) login and project.
*   **Dependencies**: None
*   **Example**: `make gcloud-check`

### `make login`

*   **Description**: Initiates the GCP login process and application default login.
*   **Dependencies**: None
*   **Example**: `make login`

### `make set-project`

*   **Description**: Sets the active GCP project for `gcloud` and application default credentials.
*   **Dependencies**: None
*   **Arguments**:
    *   `project`: The GCP project ID to set.
*   **Example**: `make set-project project=my-gcp-project`

### `make help`

*   **Description**: Displays a help message with a list of all available commands and their descriptions.
*   **Dependencies**: None
*   **Example**: `make help`
