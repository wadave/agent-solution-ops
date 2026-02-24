# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# TODO: Customize to necessary APIs

# Enable the Identity and Access Management API
resource "google_project_service" "iam_manager_api" {
  service            = "iam.googleapis.com"
  disable_on_destroy = false
}

# Enable the Secret Manager API
resource "google_project_service" "secret_manager_api" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# Enable the Artifact Registry API
resource "google_project_service" "artifactregistry_api" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# Enable the Service Usage API
resource "google_project_service" "serviceusage_api" {
  service            = "serviceusage.googleapis.com"
  disable_on_destroy = false
}

# Enable the Service Management API
resource "google_project_service" "servicemanagement_api" {
  service            = "servicemanagement.googleapis.com"
  disable_on_destroy = false
}

# Enable the Compute API
resource "google_project_service" "compute_api" {
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

# Enable the Cloud Run API
resource "google_project_service" "cloud_run_api" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

# Enable the Storage API
resource "google_project_service" "storage_api" {
  service            = "storage.googleapis.com"
  disable_on_destroy = false
}

# Enable the Vertex AI Platform API
resource "google_project_service" "aiplatform_api" {
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

# Enable the Discovery Engine API
resource "google_project_service" "discoveryengine_api" {
  service            = "discoveryengine.googleapis.com"
  disable_on_destroy = false
}

# Enable the Telemtry API
resource "google_project_service" "telemetry_api" {
  service            = "telemetry.googleapis.com"
  disable_on_destroy = false
}

# Enable the Cloud Logging API
resource "google_project_service" "logging_api" {
  service            = "logging.googleapis.com"
  disable_on_destroy = false
}

# Enable the Cloud Trace API
resource "google_project_service" "cloudtrace_api" {
  service            = "cloudtrace.googleapis.com"
  disable_on_destroy = false
}

# Enable the Cloud Monitoring API
resource "google_project_service" "monitoring_api" {
  service            = "monitoring.googleapis.com"
  disable_on_destroy = false
}

# Enable Gemini for Google Cloud Code API.
resource "google_project_service" "gemini_for_gcp_api" {
  service            = "cloudaicompanion.googleapis.com"
  disable_on_destroy = false
}

# Enable the Model Armor API
resource "google_project_service" "model_armor_api" {
  depends_on = [
    google_project_service.aiplatform_api,
  ]
  service            = "modelarmor.googleapis.com"
  disable_on_destroy = false
}

# Enable the Data Loss Prevension API
resource "google_project_service" "dlp_api" {
  depends_on = [
    google_project_service.serviceusage_api,
  ]
  service            = "dlp.googleapis.com"
  disable_on_destroy = false
}
