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


# Define Global Variables
config_exists=0
tfstate_exists=0
handle_config=0
is_google_cloud_shell=0


# Check if running Cloud Shell
check_google_cloud_shell
is_google_cloud_shell=$?


# Check if Terraform config exists
check_config_exists
config_exists=$?


# Check Terraform state bucket already configured
bucket_value=$(get_tfstate_bucket_name)
check_tfstate_bucket_configured
tfstate_exists=$?

bucket_value=$(grep 'bucket' "backend.tf" | sed -e 's/.*bucket\s*=\s*"\(.*\)\"/\1/g')

if [ $tfstate_exists -eq 1 ]; then
    echo -n "Destroying GCS bucket: ${bucket_value}: "
    gsutil rb -f "gs://${bucket_value}"
    echo "Success"

    echo -n "Resetting terraform backend: "
    cat <<EOF > backend.tf
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

terraform {
  backend "gcs" {
    bucket = "__GCP_TFSTATE_BUCKET__"
    prefix = "terraform/state"
  }
}
EOF

	rm -rf config.tfvars
    if [ $? -ne 0 ]; then
        echo "Failure: Failed to delete config.tfvars"
        exit 1
    fi

    echo "Success"
    exit 0
else
    echo "Nothing to destroy"
    exit 0
fi
