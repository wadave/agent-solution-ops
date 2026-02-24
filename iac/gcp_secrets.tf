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

locals {
  # Secrets-to-Create
  secrets = {
    "${local.app_namespace_under}_GCP_PROJECT"       = var.project_id,
    "${local.app_namespace_under}_GCP_REGION"        = var.region,
    "${local.app_namespace_under}_GCP_AGENTS_REGION" = var.agents_region,
    "${local.app_namespace_under}_GCP_BQ_REGION"     = var.bq_region,
    "${local.app_namespace_under}_APP_NAME"          = var.app_namespace,
  }
}

resource "random_password" "random_slug" {
  length  = 4
  special = false
  lower   = true
  upper   = false
}

# Create the secrets.
resource "google_secret_manager_secret" "mapped_secrets" {
  depends_on = [
    google_project_service.secret_manager_api,
  ]

  for_each = local.secrets

  secret_id = each.key

  replication {
    auto {}
  }
}

# Create the secret versions.
resource "google_secret_manager_secret_version" "mapped_secret_values" {
  depends_on = [
    google_secret_manager_secret.mapped_secrets,
  ]

  for_each = local.secrets

  secret      = google_secret_manager_secret.mapped_secrets[each.key].id
  secret_data = each.value
}
