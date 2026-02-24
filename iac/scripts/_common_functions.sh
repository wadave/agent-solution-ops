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

# Check if Running in Google Cloud Shell
check_google_cloud_shell() {
  echo -n "Checking for Shell: "
  if [[ -v CLOUD_SHELL ]]; then
    echo "Google Cloud Shell"
    return 1 # Running in Google Cloud Shell
  else
    echo "Standard Shell"
    return 0 # Not Running in Google Cloud Shell
  fi
}


# Get the GCloud login user
get_gcloud_login_user() {
  local active_login=$(gcloud config list account --format "value(core.account)")
  echo "$active_login"
}


# Read GCloud login user
read_gcloud_login_user() {
  local current_gcloud_login_user="$1"

  read -r input_gcloud_login_user

  if [[ -z "$input_gcloud_login_user" ]]; then
    echo "$current_gcloud_login_user"
  else
    echo "$input_gcloud_login_user"
  fi
}


# Check if config.tfvars already exists
check_gcloud_login() {
  echo -n "Checking for gcloud active login: "
  local active_login=$(get_gcloud_login_user)
  if [ $? -eq 0 ]; then
    echo "Found \"${active_login}\""
    return 1
  else
    echo "Not Found"
    return 0
  fi
}


# Check if config.tfvars already exists
check_config_exists() {
  echo -n "Checking for config.tfvars: "
  if [ -f "config.tfvars" ]; then
    echo "Found"
    return 1
  else
    echo "Not Found"
    return 0
  fi
}


#Extract the Terraform GCS state bucket name.
get_tfstate_bucket_name() {
  local bucket_value=$(grep 'bucket' "backend.tf" | sed -e 's/.*bucket\s*=\s*"\(.*\)\"/\1/g')
  echo "$bucket_value"
}


# Check if Terraform HCS state bucket name is configured.
check_tfstate_bucket_configured() {
  echo -n "Checking for existing Terraform GCS Backend: "
  grep '__GCP_TFSTATE_BUCKET__' backend.tf > /dev/null
  if [ $? -eq 0 ]; then
    echo "Not Found"
    return 0
  else
    local bucket_name=$(get_tfstate_bucket_name)
    echo "Found \"${bucket_name}\""
    return 1
  fi
}


# Extract the Gitlab repo
get_gitlab_repo_url() {
  local gitlab_repo_url=$(git config --get remote.origin.url)
  echo "$gitlab_repo_url"
}


# Extract the Gitlab repo owner
get_gitlab_repo_owner() {
  local gitlab_repo_url="$1"
  local gitlab_repo_owner=$(echo $gitlab_repo_url | sed -n 's#.*[:]\(.*\)/.*#\1#p')
  echo "$gitlab_repo_owner"
}


# Get Gitlab Repo Owner
read_gitlab_repo_owner() {
  local current_gitlab_repo_owner="$1"

  read -r input_gitlab_repo_owner

  if [[ -z "$input_gitlab_repo_owner" ]]; then
    echo "$current_gitlab_repo_owner"
  else
    echo "$input_gitlab_repo_owner"
  fi
}


# Extract the Gitlab repo name
get_gitlab_repo_name() {
  local gitlab_repo_url="$1"
  local gitlab_repo_name=$(echo $current_gitlab_remote_url | sed -n 's#.*/\([^/]*\)\.git#\1#p')
  echo "$gitlab_repo_name"
}


# Get Gitlab Repo Name
read_gitlab_repo_name() {
  local current_gitlab_repo_name="$1"

  read -r input_gitlab_repo_name

  if [[ -z "$input_gitlab_repo_name" ]]; then
    echo "$current_gitlab_repo_name"
  else
    echo "$input_gitlab_repo_name"
  fi
}


# Get gcloud currently selected project
get_current_gcp_project() {
  local current_gcp_project=$(gcloud config get-value project 2>&1 | grep -v 'Your active configuration is: ')
  echo "$current_gcp_project"
}


# Get GCP Project from CLI
read_gcp_project() {
  local current_gcp_project="$1"

  read -r input_gcp_project

  if [[ -z "$input_gcp_project" ]]; then
    if [[ -z "$current_gcp_project" ]]; then
      echo "Error: GCP project is required, and no default project is set."
      handle_shutdown
    fi
    echo "$current_gcp_project"
  else
    echo "$input_gcp_project"
  fi
}


# Get gcloud currently selected region
get_current_gcp_region() {
  local current_gcp_region=$(gcloud config get-value compute/region 2>&1 | grep -v 'Your active configuration is: ')
  echo "$current_gcp_region"
}


# Get GCP Region from CLI
read_gcp_region() {
  local current_gcp_region="$1"

  read -r input_gcp_region

  if [[ -z "$input_gcp_region" ]]; then
    if [[ -z "$current_gcp_region" ]]; then
      echo "Error: GCP region is required, and no default region is set."
      handle_shutdown
    fi
    echo "$current_gcp_region"
  else
    echo "$input_gcp_region"
  fi
}


# Download the config from GCS Bucket
download_config() {
  local bucket_value="$1"

  echo "Need to download config.tfvars from ${bucket_value}.".
  gsutil cp gs://$bucket_value/config.tfvars .
  if [ $? -eq 0 ]; then
    echo "Successfully retrieved config.tfvars"
  else
    echo "Failed to retrieve config.tfvars"
    handle_shutdown
  fi
}

# Define color variables
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check for the presence of a necessary command.
check_command() {
  local command_name="$1"

  # Check if the command exists
  if command -v "$command_name" &> /dev/null; then
      echo -e "    ${command_name} ${GREEN}✓${NC}"
      return 1
  else
      echo -e "    ${command_name} ${RED}✗${NC}"
      return 0
  fi
}
