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


# Check if running Cloud Shell
check_google_cloud_shell
is_google_cloud_shell=$?

if [ $is_google_cloud_shell -eq 1 ]; then
    echo "No need to invoke gcloud login within Google Cloud Shell"
fi


# Capture GCP Project ID
current_gcloud_login_user=$(get_gcloud_login_user)
echo "Current Login (change via OAuth2 login): $current_gcloud_login_user"


# Capture GCP Project ID
if [ -n "$1" ]; then
  gcp_project="$1"
  echo "Using GCP project from argument: $gcp_project"
else
  current_gcp_project=$(get_current_gcp_project)
  echo -n "Enter GCP project [$current_gcp_project]: "
  gcp_project=$(read_gcp_project "$current_gcp_project")
  echo "    Using GCP project: $gcp_project"
fi


# Login to GCloud
gcloud auth login --quiet --update-adc
if [ $? -ne 0 ]; then
    echo "[Error]: Failed to login to gcloud"
    exit 1
fi


# Change Default Project
gcloud config set project "$gcp_project"
if [ $? -ne 0 ]; then
    echo "[Error]: Failed to set gcloud project config parameter"
    exit 1
fi

gcloud auth application-default set-quota-project "$gcp_project"
if [ $? -ne 0 ]; then
    echo "[Error]: Failed to set gcloud quote project parameter"
    exit 1
fi


exit 0
