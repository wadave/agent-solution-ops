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
  dash_suffix_4          = "agent-sub-joker"
  service_slug_4         = "agent-sub-joker"
  service_name_4         = "${var.app_namespace}-${local.dash_suffix_4}"
  service_desc_4         = "ADK Agent for telling jokes."
  service_account_name_4 = "${var.app_namespace}-${local.dash_suffix_4}"

  # Assign the Local Existing Discovery Bucket Resource
  agent_discovery_bucket_4 = google_storage_bucket.agent_card_bucket_2
  # Assign the Local Root agent Service Account
  root_agent_service_account_4 = google_service_account.sa_ae_3

  # Grant Mapped Service Account the Following Roles
  project_iam_roles_4 = {
    "Vertex AI Service Agent" = "roles/aiplatform.serviceAgent"
    "Cloud Trace Agent"       = "roles/cloudtrace.agent"
  }

  # Cloud Run Configuration
  cloudrun_4 = {
    min_instances         = 1
    service_account_email = google_service_account.dsa_run_4.email
    docker_repo = {
      host = module.docker_repo_1.docker_repo_host
      name = module.docker_repo_1.docker_repo_name
    }
    request_timeout = "3600s"
    environment_variables = {
      "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT" = "true"
      "OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED"   = "true"
      "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS"               = "true"
      "OTEL_SERVICE_NAME"                                  = "${local.dash_suffix_4}"
    }
  }

  # Add Root Agent, Reasoning Engine, or any other Service Account to invoke this Cloud Run Service.
  service_run_invoker_members_4 = {
    #"AI Reasoning Engine Service Account" = "serviceAccount:service-${data.google_project.main_project.number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com",
    "Root Agent Dedicated Service Account" = "serviceAccount:${local.root_agent_service_account_4.email}",
  }
}

# Create dedicated SA account for Cloud Run service.
resource "google_service_account" "dsa_run_4" {
  account_id   = local.service_account_name_4
  display_name = "Dedicated SA for Cloud Run service."
}

# Permit Cloud Run to Publish A2A Agent Card to GCS Bucket
resource "google_storage_bucket_iam_member" "agent_card_admin_member_4" {
  depends_on = [
    google_project_service.iam_manager_api,
    google_project_service.storage_api,
    local.agent_discovery_bucket_4,
    google_service_account.dsa_run_4,
  ]

  bucket = local.agent_discovery_bucket_4.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.dsa_run_4.email}"
}

# Create an A2A-exposed ADK agent for interacting with the audio recording generation service.
module "adk_a2a_service_4" {
  depends_on = [
    module.docker_repo_1,
    local.agent_discovery_bucket_4,
    google_storage_bucket_iam_member.agent_card_admin_member_4,
    google_secret_manager_secret_version.mapped_secret_values,
  ]
  source = "git::git@gitlab.com:google-cloud-ce/communities/Starter-Packs/field-solutions-arch-building-blocks/iac/terraform/cloudrun-adk-a2a.git?ref=v0.0.5"

  agent_card_bucket_uri = "gs://${local.agent_discovery_bucket_4.name}"

  project_id = var.project_id
  region     = var.region

  project_iam_roles = {
    "Vertex AI Platform" = "roles/aiplatform.admin"
  }

  service = {
    slug        = local.service_slug_4
    name        = local.service_name_4
    description = local.service_desc_4
  }
  cloudrun = local.cloudrun_4
}

# Allow various SAs to access the Cloud Run service with the run.invoker role
resource "google_cloud_run_service_iam_member" "service_run_invoker_members_4" {
  for_each = local.service_run_invoker_members_4

  depends_on = [
    google_project_service.iam_manager_api,
    google_project_service.cloud_run_api,
    # Ensure service exists
    module.adk_a2a_service_4,
    # Ensure root agent service accounts exist
    local.root_agent_service_account_4,
  ]

  project  = var.project_id
  service  = module.adk_a2a_service_4.service_name
  location = module.adk_a2a_service_4.service_location
  role     = "roles/run.invoker"
  member   = each.value
}

# Allow SAs defined in var.env_sas Cloud Run Invoker access to the Service.
resource "google_cloud_run_service_iam_member" "service_run_invoker_members_env_sas_4" {
  for_each = toset(var.env_sas)

  depends_on = [
    google_project_service.iam_manager_api,
    google_project_service.cloud_run_api,
    google_project_service.aiplatform_api,
    # Ensure service exists
    module.adk_a2a_service_4,
  ]

  project  = var.project_id
  service  = module.adk_a2a_service_4.service_name
  location = module.adk_a2a_service_4.service_location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${each.value}"
}
