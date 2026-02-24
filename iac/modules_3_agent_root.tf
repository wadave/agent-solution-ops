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

locals {
  # Service Configuration
  # Change to add suffix to agent resources.  Only [a-zA-Z][-a-zA-Z0-9]{2,14} allowed.
  dash_suffix_3  = "agent-root"
  agent_name_3   = "Root Agent Orchestrator_${local.app_namespace_under}"
  agent_desc_3   = "Root Orchestration Agent for a collection of Sub-Agents."
  service_name_3 = "${var.app_namespace}-${local.dash_suffix_3}"
  sa_name_ae_3   = "${var.app_namespace}-${local.dash_suffix_3}"

  # Assign the Local Existing Discovery Bucket Resource
  agent_discovery_bucket_3 = google_storage_bucket.agent_card_bucket_2

  # Assign the Local Agent Discovery Barrier
  agent_discovery_barrier_3 = null_resource.agent_discovery_barrier_2

  # Grant Mapped Service Account the Following Roles
  project_iam_roles_3 = {
    "Vertex AI Service Agent" = "roles/aiplatform.serviceAgent"
    "Cloud Trace Agent"       = "roles/cloudtrace.agent"
  }

  # Storage
  staging_bucket_name_3 = "${var.app_namespace}-staging-${local.dash_suffix_3}"
  staging_bucket_uri_3  = "gs://${local.staging_bucket_name_3}"

  # Service Configuration
  service_3 = {
    slug        = local.dash_suffix_3
    name        = local.service_name_3
    description = local.agent_desc_3
  }

  # Agent Engine Configuration
  agent_engine_3 = {
    agent_name         = local.agent_name_3
    staging_bucket_uri = local.staging_bucket_uri_3
    authorization_ids = {
      "AUTH_ID" = "ui_oauth_token"
    }
    service_account_email = google_service_account.sa_ae_3.email
    environment_variables = {
      "GOOGLE_CLOUD_PROJECT"                               = var.project_id
      "GOOGLE_CLOUD_LOCATION"                              = var.region
      #"MODEL_ARMOR_TEMPLATE_ID"                            = local.model_armor_tmpl_name_7
      "AGENT_CARD_BUCKET_URI"                              = "gs://${local.agent_discovery_bucket_3.name}"
      "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT" = "true"
      "OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED"   = "true"
      "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS"               = "true"
      "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY"         = "true"
      "OTEL_SERVICE_NAME"                                  = "${local.dash_suffix_3}"
    }
  }
}

# Create Dedicated Service Account
resource "google_service_account" "sa_ae_3" {
  depends_on = [
    google_project_service.iam_manager_api,
  ]
  account_id   = local.sa_name_ae_3
  display_name = "Dedicated Cloud Run SA for ${local.dash_suffix_3} service."
}

# Permit to Read A2A Agent Card from the GCS Bucket
resource "google_storage_bucket_iam_member" "agent_card_viewer_member_3" {
  depends_on = [
    google_project_service.iam_manager_api,
    google_project_service.storage_api,
    local.agent_discovery_bucket_3,
    google_service_account.sa_ae_3,
  ]

  bucket = local.agent_discovery_bucket_3.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.sa_ae_3.email}"
}

# Create Staging Bucket
resource "google_storage_bucket" "staging_bucket_3" {
  depends_on = [
    google_project_service.storage_api,
  ]
  name                        = local.staging_bucket_name_3
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
}

# Create Agent Engine ADK service
module "adk_agent_engine_3" {
  depends_on = [
    google_secret_manager_secret_version.mapped_secret_values,
    google_storage_bucket.staging_bucket_3,
    google_service_account.sa_ae_3,
    local.agent_discovery_barrier_3,
  ]
  source = "git::git@gitlab.com:google-cloud-ce/communities/Starter-Packs/field-solutions-arch-building-blocks/iac/terraform/agent-engine-adk?ref=v0.2.7"

  project_id        = var.project_id
  region            = var.region
  service           = local.service_3
  agent_engine      = local.agent_engine_3
  project_iam_roles = local.project_iam_roles_3
}
