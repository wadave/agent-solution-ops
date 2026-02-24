*Last updated: 2025/02/28*

Repository Structure
==================

Project Folder Structure
============================

```
repository_root/
 ├── docs/              - Documentation
 ├── exports/           - External repo exports
 ├── iac/               - Infrastructure as Code
 │ ├── modules/         - Local filesystem Terraform modules
 │ | ├── {module_name}  - Local filesystem Terraform module instance folder.
 │ ├── scripts/         - Local scripts to orchestrate intrastructure-as-code workflow
 │ ├── templates/       - Terraform templatefile and template assets
 │ ├── gcp_xxxx.tf      - Shared GCP resources across modules (service accounts, secrets, etc.)
 │ ├── module_xxxx.tf   - Custom modules for specific solution components (agents, analytics, vertex search, etc.)
 │ ├── tf_inputs.tf     - Terraform input variables.
 │ ├── tf_locals.tf     - Terraform main variable configuration file.  Input-derived variables are created here.
 │ ├── tf_outputs.tf    - Terraform output assets.  This separation exists to keep output assets organized in a single place for accountability.
 │ ├── tf_providers.tf  - Terraform providers dependency file.
 ├── libs/              - Local filesystem shared libraries
 │ ├── {lib_name}       - Local filesystem shared library instance folder.
 ├── notes/             - Notebooks
 ├── services/          - Services Implementations
 │ ├── {service_name}   - Services Implementation instance folder.
```


Change Management and Commits
==============================

Prefix the name of each commit line entry with one of the following (but not exclusive) list:

```
wip:
fix:
feat:
del:
add:
update:
doc:
rel:
```

For example, **fix: Corrected undefined refrence access.**, for a branch to add a new feature relating to calendar events.  Use markdown list syntax for multiple commits entries in a single commit message.


Change Management and Branches
==============================

Create change-specific branches with an expected time-to-live (TTL) of **7 days or less**, encourating frequent merges to the **main** branch.

Prefix the name of the branch with one of the following (but not exclusive) list:

```
wip-
fix-
feat-
del-
add-
update-
doc-
rel-
```

For example, **feat-add-new-calendar-event**, for a branch to add a new feature relating to calendar events.

Once the branch is ready to merge, create a Merge Request (MR) with one of the repository maintainers as assigned reviewer.


Change Management and Tags/Releases
===================================

While developing a new release, use a release candidate version scheme to ensure you can test pre-release module assets from other projects.

## Develop Release: Dev Branches and Release Candidates

### Python Modules

Update the following assets in your python modules:

```
shared_lib_python/
 ├── docs/           - Documentation
   ├── src/          - Documentation-as-code
     ├── conf.py     - Update: Sphinx version config
 ├── pyproject.toml  - Update: Poetry version config
 ├── setup.py        - Update: setuptools version config
```

Using the version schema "v0.0.1", add the suffix "-rc{*BuildNumber*}".  For example, "v0.0.1-rc1".

Assuming you created branch **fix-bug144123** to fix a bug, you would update your requirements in the downstream dependent accordingly:

```
common_logging_py @ git+ssh://git@gitlab.com/<repo_path>/<lib_repo_name>.git@fix-bug144123
```

When commiting new test builds, ensuring to increment the release candidate number and confirm the new module is installed in your development environment after using the **make upgrade** target (or **pip install -U -r requirements.txt**)


## Publish Releases: Tags and Releases

Upon achieving version milestones, perform the following actions for Tags and Releases:

### Publish Release: Tags

 - Create a tag with the new version (starting at "v0.0.1", for example)
   - Include changelist of important commits.  For example:
   ```
    - feat: Added new calendar event feature.
    - fix: Corrected undefined refrence access.
   ```
 - Create (or replace) the tag **latest** based off of the latest created tag (i.e. "v0.0.1")

### Publish Release: Releases

 - Create a release with the new version (starting at "v0.0.1", for example)
   - Include changelist of important commits.  For example:
   ```
    - feat: Added new calendar event feature.
    - fix: Corrected undefined refrence access.
   ```
