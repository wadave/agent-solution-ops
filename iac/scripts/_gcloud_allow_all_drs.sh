#!/usr/bin/env bash
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

project_id=$1

if [ -z "${project_id}" ]; then
  echo "Error: No project specified, please include a project name as an argument."
  exit 1
fi

policy_yaml_path="./build/tmp-allow-all-sharing-policy.yaml"

mkdir -p "./build/"

POLICY_YAML=$(cat <<EOF
name: projects/${project_id}/policies/iam.allowedPolicyMemberDomains
spec:
  rules:
  - allowAll: true
EOF
)

echo "${POLICY_YAML}" > ${policy_yaml_path}

# Fetch Agent Engine Resource ID by Display Name
echo -n "Overriding Domain Restricted Sharing Policy YAML\"${policy_yaml_path}\": "
cmd_output=$(gcloud org-policies set-policy ${policy_yaml_path})
if [ $? -ne 0 ]; then
  echo "Failure: '${cmd_output}'"
  exit 1
fi

echo "${cmd_output}"
exit 0
