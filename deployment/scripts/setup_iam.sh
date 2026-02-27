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

# Configuration
STAGING_PROJECT="dw-genai-dev"
PREPROD_PROJECT="dw-genai-pre-prod"
PROJECT_NUMBER="496235138247"

# Service Accounts to grant permissions to
IDENTITIES=(
  "serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
  "serviceAccount:agents-solution-ops-cd@dw-genai-dev.iam.gserviceaccount.com"
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
    
    for ROLE in "${ROLES[@]}"; do
      echo "  Granting ${ROLE}..."
      gcloud projects add-iam-policy-binding "${PROJECT}" \
        --member="${IDENTITY}" \
        --role="${ROLE}" \
        --quiet > /dev/null
    done
  done
done

echo "--------------------------------------------------------"
echo "Successfully granted all roles across all identities and projects."
echo "--------------------------------------------------------"
