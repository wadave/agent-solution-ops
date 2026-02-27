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

PROJECT_ID="dw-genai-dev"
PROJECT_NUMBER="496235138247"
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

ROLES=(
  "roles/artifactregistry.admin"
  "roles/iam.serviceAccountAdmin"
  "roles/resourcemanager.projectIamAdmin"
  "roles/run.admin"
  "roles/storage.admin"
  "roles/secretmanager.viewer"
  "roles/secretmanager.secretAccessor"
)

echo "Granting required roles to Cloud Build service account: ${CB_SA} in project: ${PROJECT_ID}"

for ROLE in "${ROLES[@]}"; do
  echo "Granting ${ROLE}..."
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${CB_SA}" \
    --role="${ROLE}" \
    --quiet > /dev/null
done

echo "Successfully granted all roles."
