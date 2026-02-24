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
  custom_role_id = "${local.app_namespace_under}_solution_users"
}

# Create Custom Roles for Solution Users
module "custom_user_role" {
  source = "git::git@gitlab.com:google-cloud-ce/communities/Starter-Packs/field-solutions-arch-building-blocks/iac/terraform/iam-roles-custom.git?ref=v0.0.2"

  project_id = var.project_id
  region     = var.region
  custom_roles = {
    solution_users = {
      role_id     = local.custom_role_id
      title       = "Custom Solution User Role"
      description = "Required end-user permissions to use the Solution."
      base_roles = [
        "roles/aiplatform.user",
        "roles/discoveryengine.user",
        "roles/dialogflow.client",
        "roles/serviceusage.serviceUsageConsumer"
      ]
      permissions_to_exclude = [
        "resourcemanager.projects.list"
      ]
    }
  }
}

# Assign Custom Role to Test Users
resource "google_project_iam_member" "test_users_custom_role" {
  depends_on = [module.custom_user_role]

  for_each = toset(var.test_user_emails)
  project  = var.project_id
  role     = "projects/${var.project_id}/roles/${local.custom_role_id}"
  member   = "user:${each.value}"
}
