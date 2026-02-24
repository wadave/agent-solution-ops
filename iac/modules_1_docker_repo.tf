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
  # Docker (Artifact Registry)
  docker_repo_host_1 = "${var.region}-docker.pkg.dev"
  docker_repo_name_1 = "${var.app_namespace}-source-deploy"
  docker_repo_path_1 = "${local.docker_repo_host_1}/${var.project_id}"
}

# Create the Docker repo for Cloud Run images.
module "docker_repo_1" {
  source = "git::git@gitlab.com:google-cloud-ce/communities/Starter-Packs/field-solutions-arch-building-blocks/iac/terraform/docker-repo.git?ref=latest"

  project_id       = var.project_id
  region           = var.region
  docker_repo_host = local.docker_repo_host_1
  docker_repo_name = local.docker_repo_name_1
}

# Output the docker_repo_host.
output "docker_repo_host_1" {
  value       = local.docker_repo_host_1
  description = "The artifact registry docker repo host"
}

# Output the docker_repo_name.
output "docker_repo_name_1" {
  value       = local.docker_repo_name_1
  description = "The artifact registry docker repo name"
}

# Output the docker_repo_path.
output "docker_repo_path_1" {
  value       = local.docker_repo_path_1
  description = "The artifact registry docker repo path"
}
