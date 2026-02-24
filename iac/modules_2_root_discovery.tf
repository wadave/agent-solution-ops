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

resource "null_resource" "agent_discovery_barrier_2" {
  depends_on = [
    # TODO: Insert Agent Dependencies Here
    google_storage_bucket.agent_card_bucket_2,
    module.adk_a2a_service_4,
  ]

  provisioner "local-exec" {
    command     = "echo 'Dependency barrier triggered at ${timestamp()}'"
    interpreter = ["/bin/bash", "-c"]
  }
}

locals {
  # Service
  agent_card_bucket_name_2 = "${var.app_namespace}-a2a-agent-cards"
  agent_card_bucket_uri_2  = "gs://${local.agent_card_bucket_name_2}"
}

# Create dedicated bucket for cards
resource "google_storage_bucket" "agent_card_bucket_2" {
  depends_on = [
    google_project_service.storage_api
  ]
  name                        = local.agent_card_bucket_name_2
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
}
