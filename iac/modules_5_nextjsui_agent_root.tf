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

/* locals {
  # Agent Configuration
  agent_name_5          = "Agent Hub"
  agent_description_5   = "Your central hub for interacting with data and systems through natural language."
  agent_intro_message_5 = "Hi there, how can I help you today?"

  # Service Configuration
  dash_suffix_5         = "root-nextjsui"
  service_name_5        = "${var.app_namespace}-${local.dash_suffix_5}"
  service_slug_5        = "nextjsui-agent-root"
  service_description_5 = "Microservice for hosting the NextJS UI for an Agent Engine Agent."
  sa_name_nextjs_ui_5   = "${var.app_namespace}-${local.dash_suffix_5}"

  # Assign the Local Agent Engine Module for the NextJS UI
  agent_engine_agent_module_5 = module.adk_agent_engine_3

  # Cloud Run Configuration
  cloudrun_5 = {
    local_service_port    = 3000
    service_account_email = google_service_account.sa_nexjs_ui_5.email
    shared_secrets = {
      "NEXT_PUBLIC_GOOGLE_CLIENT_ID" = var.oauth_client_id_secret_name
    }
    docker_repo = {
      host = module.docker_repo_1.docker_repo_host
      name = module.docker_repo_1.docker_repo_name
    }
  }

  # Website Configuration
  website_title_5       = local.agent_name_5
  website_description_5 = local.agent_description_5

  # Agent Engine URL
  agent_engine_url_5 = "https://${var.region}-aiplatform.googleapis.com/v1/${local.agent_engine_agent_module_5.agent_engine_resource_name}"
}


# Create dedicated SA account for sa_nexjs_ui_5
resource "google_service_account" "sa_nexjs_ui_5" {
  depends_on   = [google_project_service.iam_manager_api]
  account_id   = local.sa_name_nextjs_ui_5
  display_name = "Dedicated Cloud Run SA for sa_nexjs_ui_5 service."
}

# Create a NextJS UI service
module "nextjs_agent_engine_ui_5" {
  depends_on = [
    module.docker_repo_1,
    local.agent_engine_agent_module_5,
  ]
  source = "git::git@gitlab.com:google-cloud-ce/communities/Starter-Packs/field-solutions-arch-building-blocks/iac/terraform/cloudrun-nextjs-agent-engine-ui.git?ref=v0.0.4"

  # The GCP project name.
  project_id = var.project_id
  region     = var.region

  # The website details
  website_title       = local.website_title_5
  website_description = local.website_description_5

  agent_name          = local.agent_name_5
  agent_description   = local.agent_description_5
  agent_engine_url    = local.agent_engine_url_5
  agent_intro_message = local.agent_intro_message_5

  service = {
    name        = local.service_name_5
    slug        = local.service_slug_5
    description = local.service_description_5
  }
  cloudrun = local.cloudrun_5
}
 */