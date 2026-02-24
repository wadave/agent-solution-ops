# AI Agent Component Discovery Guide

This document instructs AI agents on how to use the discovery index to find and integrate reusable components from this repository (Terraform modules, Python libraries, Blueprints, and Solution Templates).

## 1. Index Files

- **`discovery_index.json`**: The primary data source. Use this for programmatic filtering and retrieving specific configuration metadata (inputs, outputs, git sources).
- **`discovery_index.md`**: A human-readable summary. Use this for a quick high-level overview of available components.

## 2. Discovery Workflow

When tasked with adding a feature or infrastructure:

1.  **Search**: Read `discovery_index.json` and search for keywords in `name`, `description`, or `path`.
2.  **Filter by Type**:
    - `terraform-module`: For GCP infrastructure building blocks.
    - `shared-library`: For reusable Python utility functions.
    - `blueprint`: To see how multiple modules work together in a real-world scenario.
    - `solution-template`: To see the recommended end-to-end project structure.
3.  **Analyze Metadata**:
    - **`git_source`**: Use this exact string for the `source` attribute in your Terraform `module` blocks.
    - **`usage`**: Use this snippet as the baseline for implementation.
    - **`inputs_table`**: Check this to identify required and optional variables you must provide.

## 3. Integration Patterns

### 🛠 Terraform Modules
Find the module in the index and copy the `usage` snippet. Use the `git_source` provided to ensure you are pulling the latest version from the repository.

### 📚 Shared Libraries (Python)
Libraries are typically Git-based. Refer to the `usage` snippet in the index for the standard `pip install` or `requirements.txt` format.

### 💡 Blueprints
When you find a module but are unsure how to wire it to others (e.g., connecting a Cloud Run service to a Secret), search the index for `blueprint` items. Blueprints contain multi-file examples of module interactions.

## 4. Constraint Handling
If a component in the index seems relevant but the description is too brief, navigate to the `path` specified in the index entry and read the full `README.md` or source code in that directory.
