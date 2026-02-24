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

# Define locals
locals {
  base_env_tpl = templatefile("${path.module}/templates/base_env_tpl.sh", {
    project_id          = var.project_id,
    location            = var.region,
    app_namespace       = var.app_namespace,
    app_namespace_under = local.app_namespace_under,
  })
  makefile = templatefile("${path.module}/templates/Makefile_tpl", {
    env_script = "iac/build/base_env.sh",
  })
  dev_container_env_tpl = templatefile("${path.module}/templates/dev_container_env_tpl", {
    project_id = var.project_id,
  })
}


# Create Module Build Directory if missing
resource "null_resource" "create_build_dir_if_missing" {
  provisioner "local-exec" {
    command = "mkdir -p ${path.module}/build"
  }
}


# Generate Project-level Makefile
resource "local_file" "out_makefile" {
  content         = local.makefile
  filename        = "${path.root}/../Makefile"
  file_permission = "0755"
}


# Generate base_env.sh
resource "local_file" "out_base_env_folder" {
  content         = local.base_env_tpl
  filename        = "${path.module}/build/base_env.sh"
  file_permission = "0755"
}

# Generate devcontainer .env
resource "local_file" "out_dev_container_env" {
  content         = local.dev_container_env_tpl
  filename        = "${path.root}/../.devcontainer/.env"
  file_permission = "0755"
}


###########
# Outputs #
###########

# Output the project_id.
output "project_id" {
  value       = var.project_id
  description = "The project ID"
}
