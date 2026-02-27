#!/bin/bash
# Copyright 2026 Google LLC
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

set -e

# This script bootstraps the required IAM permissions for the Cloud Build identities.
# It should be run once by a project owner before triggering the CI/CD pipeline.

usage() {
  echo "Usage: $0 <STAGING_PROJECT_ID> <PROD_PROJECT_ID> <PROJECT_NUMBER>"
  echo "Example: $0 my-staging-project my-prod-project 123456789012"
  exit 1
}

if [ "$#" -ne 3 ]; then
  usage
fi

STAGING_PROJECT=$1
PREPROD_PROJECT=$2
PROJECT_NUMBER=$3

# Service Accounts to grant permissions to
IDENTITIES=(
  "serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
  "serviceAccount:agents-solution-ops-cd@${STAGING_PROJECT}.iam.gserviceaccount.com"
)

# Projects to grant permissions in
TARGET_PROJECTS=(
  "${STAGING_PROJECT}"
  "${PREPROD_PROJECT}"
)

# Roles required for bootstrapping and managing infrastructure
ROLES=(
  "roles/artifactregistry.admin"
  "roles/iam.serviceAccountAdmin"
  "roles/resourcemanager.projectIamAdmin"
  "roles/run.admin"
  "roles/storage.admin"
  "roles/secretmanager.viewer"
  "roles/secretmanager.secretAccessor"
)

for PROJECT in "${TARGET_PROJECTS[@]}"; do
  echo "--------------------------------------------------------"
  echo "Processing project: ${PROJECT}"
  echo "--------------------------------------------------------"
  
  for IDENTITY in "${IDENTITIES[@]}"; do
    echo "Updating permissions for: ${IDENTITY}"
    
    # Check if identity exists
    if ! gcloud iam service-accounts describe "$(echo ${IDENTITY} | cut -d ':' -f 2)" --project="$(echo ${IDENTITY} | cut -d '@' -f 2)" &> /dev/null; then
       # For the default cloudbuild SA, it might not be discoverable via service-accounts describe if it's external, 
       # but we attempt to grant anyway.
       echo "  Note: Identity might not exist yet or is external. Attempting to grant roles anyway..."
    fi

    for ROLE in "${ROLES[@]}"; do
      echo "  Granting ${ROLE}..."
      gcloud projects add-iam-policy-binding "${PROJECT}" \
        --member="${IDENTITY}" \
        --role="${ROLE}" \
        --quiet > /dev/null || echo "  Warning: Failed to grant ${ROLE} to ${IDENTITY} in ${PROJECT}"
    done
  done
done

echo "--------------------------------------------------------"
echo "Successfully processed projects. Please verify permissions in the Cloud Console."
echo "--------------------------------------------------------"
