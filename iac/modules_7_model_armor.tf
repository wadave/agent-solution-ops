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
  model_armor_tmpl_name_7    = "${var.app_namespace}-armr-tmpl"
  dlp_inspect_tmpl_name_7    = "${var.app_namespace}-dlp-inspect-tmpl"
  dlp_deidentify_tmpl_name_7 = "${var.app_namespace}-dlp-deidentify-tmpl"
  enable_enforcement_7       = false
}

# Grant the Model Armor user permission to the Vertex AI service account.
resource "google_project_iam_member" "vertexai_model_armor_access_7" {
  depends_on = [
    google_project_service.iam_manager_api,
    google_project_service.aiplatform_api,
    google_project_service.model_armor_api,
  ]

  project = var.project_id
  role    = "roles/modelarmor.user"
  member  = "serviceAccount:service-${data.google_project.main_project.number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
}

# Grant the DLP user permission to the Vertex AI service account.
resource "google_project_iam_member" "model_armor_dlp_user_7" {
  depends_on = [
    google_project_service.iam_manager_api,
    google_project_service.dlp_api,
    google_project_service.aiplatform_api,
  ]

  project = var.project_id
  role    = "roles/dlp.user"
  member  = "serviceAccount:service-${data.google_project.main_project.number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
}

# Grant the DLP reader permission to the Vertex AI service account.
resource "google_project_iam_member" "model_armor_dlp_reader_7" {
  depends_on = [
    google_project_service.iam_manager_api,
    google_project_service.dlp_api,
    google_project_service.aiplatform_api,
  ]

  project = var.project_id
  role    = "roles/dlp.reader"
  member  = "serviceAccount:service-${data.google_project.main_project.number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
}

# Create the DLP and Model armor templates
module "model_armor_template_7" {
  source = "git::git@gitlab.com:google-cloud-ce/communities/Starter-Packs/field-solutions-arch-building-blocks/iac/terraform/model-armor-template.git?ref=v0.0.1"

  project_id               = var.project_id
  tmpl_region              = var.region
  model_armor_tmpl_name    = local.model_armor_tmpl_name_7
  dlp_inspect_tmpl_name    = local.dlp_inspect_tmpl_name_7
  dlp_deidentify_tmpl_name = local.dlp_deidentify_tmpl_name_7
}

# Configure the Model Armor Gemini Floor Settings
module "model_armor_vertexai_7" {
  depends_on = [
    module.model_armor_template_7,
  ]
  source = "git::git@gitlab.com:google-cloud-ce/communities/Starter-Packs/field-solutions-arch-building-blocks/iac/terraform/model-armor-vertexai.git?ref=v0.1.0"

  project_id             = var.project_id
  region                 = var.agents_region
  dlp_inspect_tmpl_id    = module.model_armor_template_7.dlp_inspect_template_id
  dlp_deidentify_tmpl_id = module.model_armor_template_7.dlp_deidentify_template_id

  enable_enforcement = local.enable_enforcement_7
}

# Output the dlp_inspect_template_id.
output "dlp_inspect_template_id_7" {
  value       = module.model_armor_template_7.dlp_inspect_template_id
  description = "The DLP inspection template ID."
}

# Output the dlp_deidentify_template_id.
output "dlp_deidentify_template_id_7" {
  value       = module.model_armor_template_7.dlp_deidentify_template_id
  description = "The DLP deidentify template ID."
}

# Output the model_armor_template_id.
output "model_armor_template_id_7" {
  value       = module.model_armor_template_7.model_armor_template_id
  description = "The Model Armor template ID."
}
