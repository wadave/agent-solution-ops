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
      image = "${var.region}-docker.pkg.dev/${each.value}/mcp-server-repo/weather-mcp-server:${var.mcp_image_tag}"
      
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

  depends_on = [
    google_artifact_registry_repository.mcp_repo,
    google_project_service.deploy_project_services
  ]
}

# Agent Engine is deployed and managed entirely by deployment/deploy_agents.py in CI/CD.
# Terraform only manages the supporting infrastructure above (Cloud Run, Artifact Registry).

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
