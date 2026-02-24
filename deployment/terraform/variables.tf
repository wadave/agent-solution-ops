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

variable "project_name" {
  type        = string
  description = "Project name used as a base for resource naming"

}

variable "prod_project_id" {
  type        = string
  description = "**Production** Google Cloud Project ID for resource deployment."

}

variable "staging_project_id" {
  type        = string
  description = "**Staging** Google Cloud Project ID for resource deployment."

}

variable "cicd_runner_project_id" {
  type        = string
  description = "Google Cloud Project ID where CI/CD pipelines will execute."

}

variable "region" {
  type        = string
  description = "Google Cloud region for resource deployment."
  default     = "us-central1"
}

variable "host_connection_name" {
  description = "Name of the host connection to create in Cloud Build (used by cicd_runner_project_id for PR checks and prod deploy)"
  type        = string

}

variable "staging_connection_name" {
  description = "Name of the Cloud Build connection in the staging project for the CD pipeline trigger"
  type        = string

}

variable "repository_name" {
  description = "Name of the repository you'd like to connect to Cloud Build"
  type        = string

}

variable "app_sa_roles" {
  description = "List of roles to assign to the application service account"
  type        = list(string)
  default = [

    "roles/aiplatform.user",
    "roles/discoveryengine.editor",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
    "roles/storage.admin",
    "roles/serviceusage.serviceUsageConsumer",
  ]
}

variable "cicd_roles" {
  description = "List of roles to assign to the CICD runner service account in the CICD project"
  type        = list(string)
  default = [
    "roles/storage.admin",
    "roles/aiplatform.user",
    "roles/discoveryengine.editor",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
    "roles/artifactregistry.writer",
    "roles/cloudbuild.builds.builder",
    "roles/serviceusage.serviceUsageAdmin",
    "roles/run.admin",
    "roles/resourcemanager.projectIamAdmin"
  ]
}

variable "cicd_sa_deployment_required_roles" {
  description = "List of roles to assign to the CICD runner service account for the Staging and Prod projects."
  type        = list(string)
  default = [    
    "roles/iam.serviceAccountUser",
    "roles/aiplatform.user",
    "roles/storage.admin",
    "roles/serviceusage.serviceUsageAdmin",
    "roles/run.admin"
  ]
}


variable "repository_owner" {
  description = "Owner of the Git repository - username or organization"
  type        = string

}


variable "github_app_installation_id" {
  description = "GitHub App Installation ID for Cloud Build"
  type        = string
  default     = null
}


variable "github_pat_secret_id" {
  description = "GitHub PAT Secret ID created by gcloud CLI"
  type        = string
  default     = null
}

variable "create_cb_connection" {
  description = "Flag indicating if a Cloud Build connection already exists"
  type        = bool
  default     = true
}

variable "create_repository" {
  description = "Flag indicating whether to create a new Git repository"
  type        = bool
  default     = false
}


variable "feedback_logs_filter" {
  type        = string
  description = "Log Sink filter for capturing feedback data. Captures logs where the `log_type` field is `feedback`."
  default     = "jsonPayload.log_type=\"feedback\" jsonPayload.service_name=\"agents-solution-ops\""
}

variable "mcp_image_tag" {
  type        = string
  description = "Docker image tag for the MCP Server deployed to Cloud Run"
  default     = "latest"
}

variable "google_client_id" {
  type        = string
  description = "Google Client ID for GCP authentication in MCP server"
  default     = ""
}

variable "google_client_secret" {
  type        = string
  description = "Google Client Secret for GCP authentication in MCP server"
  default     = ""
  sensitive   = true
}

variable "ge_app_staging" {
  type        = string
  description = "Gemini Enterprise App ID for Staging"

}

variable "ge_app_prod" {
  type        = string
  description = "Gemini Enterprise App ID for Production"

}

variable "oauth_client_id_secret_name" {
  type        = string
  description = "Secret Manager secret name containing the OAuth client credentials JSON (web app format). Leave empty to skip Gemini Enterprise OAuth registration."
  default     = ""
}

variable "agents_region" {
  type        = string
  description = "Gemini Enterprise region. Typically 'global' for Discovery Engine."
  default     = "global"
}
