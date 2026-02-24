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
  # Agent Engine
  agent_name_6                        = local.agent_name_3
  agent_desc_6                        = local.agent_desc_3

  # Agentspace
  gemini_enterprise_app_id_6           = var.gemini_enterprise_app_id
  gemini_enterprise_agent_name_6       = local.agent_name_6
  gemini_enterprise_tool_description_6 = local.agent_desc_6

  # OAuth
  auth_id_6                         = "ui_oauth_token"
  oauth_client_id_secret_name_6     = var.oauth_client_id_secret_name
  oauth_client_secret_secret_name_6 = var.oauth_client_secret_secret_name
  authorization_uri_base_6          = "https://accounts.google.com/o/oauth2/v2/auth"
  oauth_token_uri_6                 = "https://oauth2.googleapis.com/token"
  oauth_scopes_6 = {
    "Account Email"         = "https://www.googleapis.com/auth/userinfo.email"
    "Personal Profile"      = "https://www.googleapis.com/auth/userinfo.profile"
    "Chat Messages Create"  = "https://www.googleapis.com/auth/chat.messages.create",
    "GMail Send Email"      = "https://www.googleapis.com/auth/gmail.send",
    "Google Cloud Platform" = "https://www.googleapis.com/auth/cloud-platform",
    "Dialogflow API"        = "https://www.googleapis.com/auth/dialogflow",
    "Google Calendar"       = "https://www.googleapis.com/auth/calendar",
  }

  authorization_ids_6 = {
    "AUTH_ID" = local.auth_id_6
  }
}

# Create Agentspac Authorization
module "gemini_enterprise_oauth_6" {
  depends_on = [
    module.adk_agent_engine_3,
  ]
  source = "git::git@gitlab.com:google-cloud-ce/communities/Starter-Packs/field-solutions-arch-building-blocks/iac/terraform/agentspace-authorization-register.git?ref=v0.0.3"

  project_id                      = var.project_id
  agentspace_region               = var.agents_region
  authorization_id                = local.auth_id_6
  oauth_client_id_secret_name     = local.oauth_client_id_secret_name_6
  oauth_client_secret_secret_name = local.oauth_client_secret_secret_name_6
  authorization_uri_base          = local.authorization_uri_base_6
  token_uri                       = local.oauth_token_uri_6
  scopes                          = local.oauth_scopes_6
}

# Register an Agent Engine ADK Agent with Gemini Enterprise
module "gemini_enterprise_agent_engine_register_6" {
  depends_on = [
    module.gemini_enterprise_oauth_6,
    module.adk_agent_engine_3,
  ]
  source = "git::git@gitlab.com:google-cloud-ce/communities/Starter-Packs/field-solutions-arch-building-blocks/iac/terraform/agentspace-agent-engine-register.git?ref=v0.0.6"

  project_id          = var.project_id
  agent_engine_region = var.region
  agentspace_region   = var.agents_region

  agent_display_name = local.agent_name_6
  agent_description  = local.agent_desc_6

  agentspace_agent_name       = local.gemini_enterprise_agent_name_6
  agentspace_tool_description = local.gemini_enterprise_tool_description_6
  agentspace_app_id           = local.gemini_enterprise_app_id_6
  authorization_ids           = local.authorization_ids_6
}
 */
