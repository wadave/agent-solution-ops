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

variable "project_id" {
  description = "The GCP project name."
  type        = string
}

variable "region" {
  description = "The GCP location region."
  type        = string
}

variable "agents_region" {
  description = "The GCP Agents location region."
  default     = "global"
  type        = string
}

variable "bq_region" {
  description = "The GCP BQ location region."
  default     = "global"
  type        = string
}

variable "app_namespace" {
  description = "The project application name."
  type        = string
}

variable "env_sas" {
  description = "The list of environment SAs for development testing."
  default     = []
  type        = list(string)
}

variable "test_user_emails" {
  description = "The list of test user email addresses."
  default     = []
  type        = list(string)
}

variable "gemini_enterprise_app_id" {
  description = "The Gemini Enterprise App ID"
  default     = "unset"
  type        = string
}

variable "oauth_client_id_secret_name" {
  description = "The existing OAuth Client ID secret name."
  default     = "OAUTH_CLIENT_ID"
  type        = string
}

variable "oauth_client_secret_secret_name" {
  description = "The existing OAuth Client Secret secret name."
  default     = "OAUTH_CLIENT_SECRET"
  type        = string
}
