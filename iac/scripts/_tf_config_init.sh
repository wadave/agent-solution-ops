#!/usr/bin/env bash
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


. scripts/_common_functions.sh

. scripts/_tf_pre_check.sh


# Define Global Variables
config_exists=0
tfstate_exists=0
handle_config=0
is_google_cloud_shell=0
is_gcloud_logged_in=0


# Create Shutdown Function to handle shutdown gracefully
handle_shutdown() {
  echo ""
  echo "Handling clean shutdown..."
  exit 1
}


# Handle successful exit
handle_exit_success() {
  echo "Ready for Terraform plan, apply, and destroy operations.  Exiting."
  exit 0
}


# Trap interruption and enforce graceful shutdown
trap handle_shutdown SIGINT SIGTERM SIGHUP


APP_NAME_RULES=$(cat <<EOF
App name must:
  - Be < 15 characters to prevent added suffixes from exceeding certain GCP component name limits.
  - Cannot containg "google" or any variation include "g00gl3".
  - May only contain lowercase letters, numbers, and hyphens, and must begin with a letter and end with a letter or number.
EOF
)


# Get Application Name
read_app_name() {
  # Capture App Name
  local current_app_name="$1"

  read -r input_app_name

  if [[ -z "$input_app_name" ]]; then
    input_app_name=$current_app_name
  fi

  # Check Max Length (due to use in service account names)
  if [ ${#input_app_name} -gt 15 ]; then
    echo "App name is great than 15 characters"
    echo "${APP_NAME_RULES}"
    return 1
  fi

  # Check No Google (due to restriction creating GCS buckets)
  if [[ $input_app_name =~ "[gG][oO0][oO0][gG][lL][eE3]" ]]; then
    echo "App name contains \"google\" or any variation include \"g00gl3\""
    echo "${APP_NAME_RULES}"
    return 1
  fi

  # Only valid characters
  if [[ ! $input_app_name =~ ^[a-z][-a-z0-9]*[a-z0-9]$ ]]; then
    echo "App name does not exclusively contain lowercase letters, numbers, and hyphens, and must begin with a letter and end with a letter or number"
    echo "${APP_NAME_RULES}"
    return 1
  fi

  echo "$input_app_name"
  return 0
}


# Get Bot Name
read_bot_name() {
  # Capture Bot Name
  local current_bot_name="$1"

  read -r input_bot_name

  if [[ -z "$input_bot_name" ]]; then
    input_bot_name=$current_bot_name
  fi

  echo "$input_bot_name"
  return 0
}


# Check if a remote config should be fetched
check_handle_config() {
  local config_exists="$1"
  local tfstate_exists="$2"

  if (( config_exists == 1 && tfstate_exists == 1 )); then
    return 0 # Ready to use Config
  elif (( config_exists == 0 && tfstate_exists == 1 )); then
    return 1 # Download Config
  else
    return 2 # Generate Config
  fi
}


# Generate the config
generate_config() {
  echo "Generating first time config and creating Terraform state bucket for initial deployment."

  # Collect Gitlab repository information
  local current_bot_name="Demo Bot"
  local current_gcp_project=$(get_current_gcp_project)
  local current_gcp_region=$(get_current_gcp_region)
  local current_app_name=$(basename "$(dirname "$(pwd)")")
  local current_deploy_env="$current_gitlab_repo_name"


  # Capture GCP Project ID
  if [[ -z "$GCP_PROJECT" ]]; then
    echo -n "Enter GCP project [$current_gcp_project]: "
    gcp_project=$(read_gcp_project "$current_gcp_project")
  else
    gcp_project=$GCP_PROJECT
  fi
  echo "    Using GCP project: $gcp_project"

  # Capture GCP Region
  if [[ -z "$GCP_REGION" ]]; then
    echo -n "Enter GCP region [$current_gcp_region]: "
    gcp_region=$(read_gcp_region "$current_gcp_region")
  else
    gcp_region=$GCP_REGION
  fi
  echo "    Using GCP region: $gcp_region"

  # Capture App Name
  if [[ -z "$APP_NAME" ]]; then
    echo -n "Enter App name [$current_app_name]: "
    app_name=$(read_app_name "$current_app_name")
  else
    app_name=$APP_NAME
  fi
  if [ $? -ne 0 ]; then
    echo "[Error]: ${app_name}"
    handle_shutdown
  fi
  echo "    Using App name: $app_name"

  # Initialize Terraform Backend
  echo "    Initializing Terraform Backend..."

  # Set gcloud project and billing.
  gcloud config set project "$gcp_project"

  # Enable Google Cloud Resource Manager API
  echo "Enabling Google Cloud Resource Manager APIs"
  gcloud services enable cloudresourcemanager.googleapis.com

  # Enable Service Usage API
  echo "Enabling Service Usage APIs"
  gcloud services enable serviceusage.googleapis.com

  # Run gcloud Auth if NOT in Cloud Shell Editor
  if [ $is_google_cloud_shell -eq 0 ]; then
    gcloud auth application-default set-quota-project "$gcp_project"
  fi

  # Enable Google Compute API
  echo "Enabling Google Compute APIs"
  gcloud services enable compute.googleapis.com

  # Set gcloud region
  gcloud config set compute/region "$gcp_region"

  # Enable Google IAM API
  echo "Enabling Google IAM APIs"
  gcloud services enable iam.googleapis.com

  # Enable Google Cloud Storage API
  echo "Enabling Google Storage APIs"
  gcloud services enable storage.googleapis.com

  # Enable Google Secret Manager API
  echo "Enabling Google Secret Manager APIs"
  gcloud services enable secretmanager.googleapis.com

  # Error if the bucket already exists
  if gsutil ls "gs://${app_name}_tfstate" >/dev/null 2>&1; then
    echo "Invalid App Name: A GCS bucket named \"gs://${app_name}_tfstate\" already exists, please pick another name \"app_name\"."
    exit 1
  fi

  # Create Storage Bucket
  echo -n "Creating GCS Bucket \"gs://${app_name}_tfstate/\" for Terraform state: "
  gcs_create_output=$(gsutil mb -p "$gcp_project" -c STANDARD -l "$gcp_region" -b on "gs://${app_name}_tfstate/")
  if [ $? -ne 0 ]; then
    echo "Failed to create GCS Bucket for Terraform state: ${gcs_create_output}"
    exit 1
  fi
  echo "Success"

  gsutil versioning set on "gs://${app_name}_tfstate/"

  # Substitute template variables in TF files.
  sed -i -e "s/__GCP_TFSTATE_BUCKET__/${app_name}_tfstate/" backend.tf

  # Substitute template variables in TF secrets.
  sed \
    -e "s/__GCP_PROJECT_NAME__/$gcp_project/" \
    -e "s/__GCP_REGION_NAME__/$gcp_region/" \
    -e "s/__APP_NAMESPACE__/$app_name/" \
    ./templates/config_tpl.tfvars_ > ./config.tfvars

  # Store config.tfvars in GCS bucket for collaboration.
  gsutil cp config.tfvars "gs://${app_name}_tfstate/"
}


# Check if running Cloud Shell
check_google_cloud_shell
is_google_cloud_shell=$?


# Check GCloud Login
check_gcloud_login
is_gcloud_logged_in=$?


# Check if Terraform config exists
check_config_exists
config_exists=$?


# Check Terraform state bucket already configured
bucket_value=$(get_tfstate_bucket_name)
check_tfstate_bucket_configured
tfstate_exists=$?


# Check how to proceed with Terraform config.
check_handle_config "$config_exists" "$tfstate_exists"
handle_config=$?


if [ $handle_config -eq 0 ] || [ $handle_config -eq 1 ]; then
  if [ $handle_config -eq 1 ]; then
    download_config "$bucket_value"
  fi
  handle_exit_success
elif [ $handle_config -eq 1 ]; then
  download_config "$bucket_value"
elif [ $handle_config -eq 2 ]; then
  generate_config
else
  echo "[Error]: Unhandled response code for check_handle_config()"
  handle_shutdown
fi


exit 0
