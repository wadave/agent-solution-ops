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

# Create an Artifact Registry repository for the MCP server
resource "google_artifact_registry_repository" "mcp_repo" {
  for_each = local.deploy_project_ids

  location      = var.region
  repository_id = "mcp-server-repo"
  description   = "Docker repository for MCP server images"
  format        = "DOCKER"
  project       = each.value
}

# Create a Cloud Run service for the MCP server
resource "google_cloud_run_v2_service" "mcp_server" {
  for_each = local.deploy_project_ids

  name                = "weather-mcp-server-oauth-${each.key}"
  location            = var.region
  project             = each.value
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      env {
        name  = "GOOGLE_CLIENT_ID"
        value = local.oauth_client_id
      }
      env {
        name  = "GOOGLE_CLIENT_SECRET"
        value = local.oauth_client_secret
      }
    }
    service_account = google_service_account.app_sa[each.key].email
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }

  depends_on = [
    google_artifact_registry_repository.mcp_repo,
    google_project_service.deploy_project_services
  ]
}

# Read base64-encoded dummy source tarball from GCS for initial Agent Engine creation
# CI/CD pipelines will update with actual source code after creation
data "google_storage_bucket_object_content" "dummy_source_b64" {
  name   = "dummy/source-b64.txt"
  bucket = "agent-starter-pack"
}

resource "google_vertex_ai_reasoning_engine" "app" {
  for_each = local.deploy_project_ids

  display_name = "ADK Hosting Agent for MCP (${each.key})"
  description  = "Agent deployed via Terraform"
  region       = var.region
  project      = each.value

  spec {
    agent_framework = "google-adk"
    service_account = google_service_account.app_sa[each.key].email

    deployment_spec {
      min_instances         = 1
      max_instances         = 10
      container_concurrency = 9

      resource_limits = {
        cpu    = "4"
        memory = "8Gi"
      }

      env {
        name  = "LOGS_BUCKET_NAME"
        value = google_storage_bucket.logs_data_bucket[each.value].name
      }
    }

    source_code_spec {
      inline_source {
        source_archive = trimspace(data.google_storage_bucket_object_content.dummy_source_b64.content)
      }

      python_spec {
        entrypoint_module  = "adk_agent.agent_engine_app"
        entrypoint_object  = "agent_engine"
        requirements_file  = "adk_agent/requirements.txt"
        version            = "3.12"
      }
    }
  }

  # This lifecycle block prevents Terraform from overwriting the source code and deployment spec
  # when it's updated by Agent Engine deployments outside of Terraform (e.g., via CI/CD pipelines)
  lifecycle {
    ignore_changes = [
      spec[0].source_code_spec,
      spec[0].deployment_spec,
      display_name
    ]
  }

  depends_on = [google_project_service.deploy_project_services]
}

# Allow unauthenticated invocations so the Python app can do its own OAuth validation
resource "google_cloud_run_v2_service_iam_binding" "mcp_server_public_access" {
  for_each = local.deploy_project_ids

  project  = each.value
  location = google_cloud_run_v2_service.mcp_server[each.key].location
  name     = google_cloud_run_v2_service.mcp_server[each.key].name
  role     = "roles/run.invoker"

  members = [
    "allUsers"
  ]
}
