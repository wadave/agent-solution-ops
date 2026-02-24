# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import toml
import importlib.metadata
import os
import sys


# Determine project name from pyproject.toml
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

some_path = os.path.abspath("../../")

pyproject_path = os.path.join(some_path, "pyproject.toml")

# Try to read the project name from pyproject.toml
project = "UNKNOWN_PROJECT"
try:
    with open(pyproject_path, "r") as f:
        pyproject_data = toml.load(f)
    project = pyproject_data["tool"]["poetry"]["name"]
except FileNotFoundError:
    print(f"Warning: pyproject.toml not found at {pyproject_path}. Cannot dynamically determine project name.")
except KeyError:
    print("Warning: 'project.name' not found in pyproject.toml. Cannot dynamically determine project name.")
except Exception as e:
    print(f"Warning: An error occurred while reading pyproject.toml: {e}")

sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

copyright = "2025, Google LLC"
author = "Justin Randall"
try:
    release = importlib.metadata.version(project)
except importlib.metadata.PackageNotFoundError:
    release = "0.0.0"
    print(f"Warning: Package '{project}' not found by importlib.metadata. Using default version '{release}'.")

pygments_style = "sphinx"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx_needs",
    "sphinxcontrib.test_reports",
    "sphinxcontrib.plantuml",
    "sphinx_reports",
    "sphinx.ext.coverage",
    "sphinx_markdown_builder",
]

templates_path = ["_templates"]
exclude_patterns = []

coverage_modules = [project]
coverage_show_missing_items = True

report_codecov_packages = {
    "src": {
        "name": "src",
        "json_report": "../build/coverage-results.json",
        "fail_below": 80,
        "levels": "default",
    }
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]

html_theme_options = {
    # 'logo_only': True,  # Only display the logo (optional)
    "logo": "google_cloud_logo_small.png",  # Path to your logo within _static
}

latex_engine = "xelatex"
latex_logo = "_static/google_cloud_logo_small.png"
latex_elements = {
    "preamble": r"""
\usepackage[utf8]{inputenc}
\usepackage{xcolor}
\usepackage{hyperref}
"""
}
