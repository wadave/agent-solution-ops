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

# Read base64-encoded dummy source tarball from GCS for initial Agent Engine creation
# CI/CD pipelines will update with actual source code after creation
# Note: The file is already base64-encoded to avoid binary corruption when reading via Terraform
data "google_storage_bucket_object_content" "dummy_source_b64" {
  name   = "dummy/source-b64.txt"
  bucket = "agent-starter-pack"
}

# Create an Artifact Registry repository for the MCP server
resource "google_artifact_registry_repository" "mcp_repo" {
  location      = var.region
  repository_id = "mcp-server-repo"
  description   = "Docker repository for MCP server images"
  format        = "DOCKER"
  project       = var.dev_project_id
}

# Create a Cloud Run service for the MCP server
resource "google_cloud_run_v2_service" "mcp_server" {
  name     = "weather-mcp-server-oauth-dev"
  location = var.region
  project  = var.dev_project_id
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.dev_project_id}/mcp-server-repo/weather-mcp-server:${var.mcp_image_tag}"

      env {
        name  = "GOOGLE_CLIENT_ID"
        value = var.google_client_id
      }
      env {
        name  = "GOOGLE_CLIENT_SECRET"
        value = var.google_client_secret
      }
    }
    service_account = google_service_account.app_sa.email
  }

  depends_on = [
    google_artifact_registry_repository.mcp_repo,
    google_project_service.services
  ]
}

resource "google_vertex_ai_reasoning_engine" "app" {
  display_name = "ADK Hosting Agent (dev)"
  description  = "Agent deployed via Terraform"
  region       = var.region
  project      = var.dev_project_id

  spec {
    agent_framework = "google-adk"
    service_account = google_service_account.app_sa.email

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
        value = google_storage_bucket.logs_data_bucket.name
      }

      env {
        name  = "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"
        value = "true"
      }

      env {
        name  = "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY"
        value = "true"
      }
    }

    source_code_spec {
      inline_source {
        source_archive = trimspace(data.google_storage_bucket_object_content.dummy_source_b64.content)
      }

      python_spec {
        entrypoint_module  = "adk_agent.agent_engine_app"
        entrypoint_object  = "agent_engine"
        requirements_file  = "adk_agent/app_utils/.requirements.txt"
        version            = "3.12"
      }
    }
  }

  # This lifecycle block prevents Terraform from overwriting the source code when it's
  # updated by Agent Engine deployments outside of Terraform (e.g., via CI/CD pipelines)
  lifecycle {
    ignore_changes = [
      spec[0].source_code_spec,
    ]
  }

  # Make dependencies conditional to avoid errors.
  depends_on = [google_project_service.services]
}
