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

# a. Create PR checks trigger (runs in cicd_runner_project_id = dw-genai-pre-prod)
resource "google_cloudbuild_trigger" "pr_checks" {
  name            = "pr-${var.project_name}"
  project         = var.cicd_runner_project_id
  location        = var.region
  description     = "Trigger for PR checks"
  service_account = resource.google_service_account.cicd_runner_sa.id

  repository_event_config {
    repository = google_cloudbuildv2_repository.repo.id
    pull_request {
      branch = "^(main|staging)$"
    }
  }

  filename = ".cloudbuild/pr_checks.yaml"
  included_files = [
    ".cloudbuild/**",
    "src/adk_agent/**",
    "src/mcp_servers/**",
    "tests/**",
    "deployment/**",
    "uv.lock",
  ]
  include_build_logs = "INCLUDE_BUILD_LOGS_WITH_STATUS"
  depends_on = [
    resource.google_project_service.cicd_services,
    resource.google_project_service.deploy_project_services,
    google_cloudbuildv2_repository.repo,
  ]
}

# b. Create CD pipeline trigger (runs in staging_project_id = dw-genai-dev)
resource "google_cloudbuild_trigger" "cd_pipeline" {
  name            = "cd-${var.project_name}"
  project         = var.staging_project_id
  location        = var.region
  service_account = google_service_account.cicd_runner_sa_staging.id
  description     = "Trigger for CD pipeline"

  repository_event_config {
    repository = google_cloudbuildv2_repository.repo_staging.id
    push {
      branch = "staging"
    }
  }

  filename = ".cloudbuild/staging.yaml"
  included_files = [
    ".cloudbuild/**",
    "src/adk_agent/**",
    "src/mcp_servers/**",
    "tests/**",
    "deployment/**",
    "uv.lock"
  ]
  include_build_logs = "INCLUDE_BUILD_LOGS_WITH_STATUS"
  substitutions = {
    _STAGING_PROJECT_ID          = var.staging_project_id
    _LOGS_BUCKET_NAME_STAGING    = resource.google_storage_bucket.logs_data_bucket[var.staging_project_id].name
    _APP_SERVICE_ACCOUNT_STAGING = google_service_account.app_sa["staging"].email
    _AUTH_ID_STAGING             = "staging-ui_oauth_token"
    _REGION                      = var.region
  }
  depends_on = [
    resource.google_project_service.cicd_services,
    resource.google_project_service.deploy_project_services,
    google_cloudbuildv2_repository.repo_staging,
    google_service_account.cicd_runner_sa_staging,
  ]
}

# c. Create Deploy to production trigger (runs in cicd_runner_project_id = dw-genai-pre-prod)
resource "google_cloudbuild_trigger" "deploy_to_prod_pipeline" {
  name            = "deploy-${var.project_name}"
  project         = var.cicd_runner_project_id
  location        = var.region
  description     = "Trigger for deployment to production"
  service_account = resource.google_service_account.cicd_runner_sa.id
  repository_event_config {
    repository = google_cloudbuildv2_repository.repo.id
    push {
      branch = "main"
    }
  }
  filename = ".cloudbuild/deploy-to-prod.yaml"
  include_build_logs = "INCLUDE_BUILD_LOGS_WITH_STATUS"
  approval_config {
    approval_required = true
  }
  substitutions = {
    _PROD_PROJECT_ID          = var.prod_project_id
    _LOGS_BUCKET_NAME_PROD    = resource.google_storage_bucket.logs_data_bucket[var.prod_project_id].name
    _APP_SERVICE_ACCOUNT_PROD = google_service_account.app_sa["prod"].email
    _AUTH_ID_PROD             = "prod-ui_oauth_token"
    _REGION                   = var.region
  }
  depends_on = [
    resource.google_project_service.cicd_services,
    resource.google_project_service.deploy_project_services,
    google_cloudbuildv2_repository.repo,
  ]
}
