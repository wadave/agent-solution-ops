#!/bin/bash
# Copyright 2025 Google LLC
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


# Associative array to store module dependencies
declare -A module_sources

export_name="repo_export"
staging_name="./exports/staging"
staging_services_name="./exports/staging-services"
module_pattern="^module\s+\"([^\"]+)\"\s+\{$"
source_pattern="source\s*=\s*\"([^\"]*)\""
source_repo_pattern="^git.*/([^.?]*)(\.git)?\\?.*"

rm -rf ./exports/${export_name}/
rm -rf ./exports/staging/
rm -rf ./exports/staging-services/

mkdir -p ./exports/${export_name}/
mkdir -p ./exports/staging/
mkdir -p ./exports/staging-services/

echo "Rsync into first staging area"
rsync -a \
  --exclude .env \
  --exclude *.env \
  --exclude scratch \
  --exclude exports \
  --exclude .vscode \
  --exclude '.git' \
  --exclude build \
  --exclude venv \
  --exclude __pycache__ \
  --exclude .pytest_cache \
  --exclude node_modules \
  --exclude .terraform \
  --exclude .terraform* \
  --exclude .next \
  --exclude config.tfvars \
  --exclude backend.tf \
  --exclude CONTRIBUTING.md \
  --exclude package-lock.json \
  --exclude base_env.sh \
  --exclude base_secrets.sh \
  --exclude run_remote_proxy.sh \
  --exclude 'services/**/Makefile' \
  --exclude agents-grafana \
  . ./exports/${export_name}/

rm -f ./exports/${export_name}/Makefile

cat <<EOF > ./exports/${export_name}/iac/backend.tf
terraform {
  backend "gcs" {
    bucket = "__GCP_TFSTATE_BUCKET__"
    prefix = "terraform/state"
  }
}
EOF

echo "Processing Terraform Modules for Remote Sources"
while IFS= read -r -d '' terraform_file; do
    # Read the Terraform file line by line
    while read -r line; do
        #echo "line: $line"
        # Check if the line starts with "module"
        if [[ $line =~ $module_pattern ]]; then
            module_name="${BASH_REMATCH[1]}"
            source_url=""
            source_repo=""

            #echo "module_name: $module_name"

            # Continue reading lines until the source is processed.
            while read -r inner_line; do
                # Check for the start of a "depends_on" block
                if [[ $inner_line =~ $source_pattern ]]; then
                    source_url="${BASH_REMATCH[1]}"
                    #echo "source_url: $source_url"

                    if [[ $source_url =~ $source_repo_pattern ]]; then
                        source_repo="${BASH_REMATCH[1]}"
                        echo "REMOTE source_repo: $source_repo"
                        module_sources[$module_name]="$source_repo"
                    else
                        echo "LOCAL source_repo: $source_url"
                    fi
                    break
                fi
            done
        fi
    done < "$terraform_file"
done < <(find ./exports/${export_name}/iac -name "*.tf" -print0)


# Print the module sources
for module_name in "${!module_sources[@]}"; do
  IFS=',' read -ra sources <<< "${module_sources[$module_name]}"
  if [[ ${module_sources[$module_name]} == "" ]]; then
    echo "Module: $module_name, Remote Source: <blank>"
  else
    echo "Module: $module_name, Remote Source: ${sources[@]}"
  fi
done

# Create the export Terraform staging module directory.
mkdir -p exports/${export_name}/iac/modules

# Copy each remote/git Terraform module into the staging module directory.
for module_name in "${!module_sources[@]}"; do
  IFS=',' read -ra sources <<< "${module_sources[$module_name]}"
  if [[ ${module_sources[$module_name]} != "" ]]; then
    echo "Module: $module_name, Remote Source: ${sources[@]}"
    rsync -a --exclude .git --exclude README.md --exclude CONTRIBUTING.md --exclude build iac/.terraform/modules/${module_name}/ exports/${export_name}/iac/modules/${sources[@]}/
  fi
done


# Apply transformations to Terraform staging modules.
while IFS= read -r -d '' terraform_file; do
    # Re-write Terraform module paths from git repo to local module.
    sed -i -e 's!source\s*=\s*\"git.*/\([^.?]*\)\(?:\.git\)*\?.*\"!source = "./modules/\1"!g' $terraform_file
    # Convert cloud run load balancer ingress to all ingress.
    sed -i -e 's!gcp_cloud_run_ingress\s*=\s*\"INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER\"!gcp_cloud_run_ingress = "INGRESS_TRAFFIC_ALL"!g' $terraform_file
done < <(find ./exports/${export_name}/iac -name "*.tf" -print0)


declare -A gitssh_libs
declare -A gitssh_branches
gitssh_lib_pattern="^(.*) @ (git\+ssh://git@.*)@([-_a-zA-Z0-9.]+)$"
python -m venv venv

echo "Processing Local Folder-based Library for Remote Sources"
# Update Local Folder-based Library Dependencies
while IFS= read -r -d '' toml_file; do
    echo "Process TOML file: $toml_file"
    # Read the file line by line
    while IFS= read -r line || [[ -n "$line" ]]; do
        #echo "toml_file line: $line"
        if [[ $line =~ $gitssh_lib_pattern ]]; then
            lib_name="${BASH_REMATCH[1]}"
            gitssh_name="${BASH_REMATCH[2]}"
            gitssh_branch="${BASH_REMATCH[3]}"

            # Re-write local requirements to use local path.
            sed -i -e "s|\"${lib_name} @ .*\"|\"${lib_name} @ file:../${lib_name}\"|g" ${toml_file}

            echo "Cloning from ${gitssh_name}"
            gitssh_libs[$lib_name]="$lib_name"
            src_dir_libs="${staging_name}/${lib_name}"
            GIT_CONFIG_PARAMETERS="'advice.detachedHead=false'" git clone --branch ${gitssh_branch} --single-branch ${gitssh_name} ${src_dir_libs}

            # Re-write remote requirements to use local path.
            sed -i -e "s|\"\([-_a-zA-Z0-9]\{1,\}\) @ .*\"|\"\1 @ file:../\1\"|g" ${src_dir_libs}/pyproject.toml

            dst_dir_libs="./exports/${export_name}/libs"

            echo -n "rsync from ${src_dir_libs} to ${dst_dir_libs}: "

            rsync -a \
                --exclude README.md \
                --exclude CONTRIBUTING.md \
                --exclude .env \
                --exclude *.env \
                --exclude scratch \
                --exclude exports \
                --exclude .vscode \
                --exclude '.git' \
                --exclude build \
                --exclude venv \
                --exclude __pycache__ \
                --exclude .pytest_cache \
                --exclude node_modules \
                --exclude .terraform \
                --exclude .terraform* \
                --exclude .next \
                --exclude config.tfvars \
                --exclude backend.tf \
                --exclude package-lock.json \
            ${src_dir_libs} ${dst_dir_libs}

            if [ $? -ne 0 ]; then
                echo "Failure"
                exit 1
            fi
            echo "Success"
        fi
    done < <(python ./iac/scripts/_read_toml_deps.py $toml_file)
done < <(find ./exports/${export_name}/libs -name pyproject.toml -print0)


echo "Processing Services for Remote Sources"
# Update Services Dependencies
while IFS= read -r -d '' toml_file; do
    echo "Process TOML file: $toml_file"
    # Read the file line by line
    while IFS= read -r line || [[ -n "$line" ]]; do
        echo "toml_file line: $line"
        if [[ $line =~ $gitssh_lib_pattern ]]; then
            lib_name="${BASH_REMATCH[1]}"
            gitssh_name="${BASH_REMATCH[2]}"
            gitssh_branch="${BASH_REMATCH[3]}"

            # Re-write local requirements to use local path.
            sed -i -e "s|\"${lib_name} @ .*\"|\"${lib_name} @ file:../../libs/${lib_name}\"|g" ${toml_file}

            echo "Cloning from ${gitssh_name}"
            gitssh_libs[$lib_name]="$lib_name"
            src_dir_libs="${staging_services_name}/${lib_name}"
            GIT_CONFIG_PARAMETERS="'advice.detachedHead=false'" git clone --branch ${gitssh_branch} --single-branch ${gitssh_name} ${src_dir_libs}

            # Re-write remote requirements to use local path.
            sed -i -e "s|\"\([-_a-zA-Z0-9]\{1,\}\) @ .*\"|\"\1 @ file:../\1\"|g" "${src_dir_libs}/pyproject.toml"

            # Rsync to final libs directory
            dst_dir_libs="./exports/${export_name}/libs"
            echo -n "rsync from ${src_dir_libs} to ${dst_dir_libs}: "
            rsync -a \
                --exclude README.md \
                --exclude CONTRIBUTING.md \
                --exclude .env \
                --exclude *.env \
                --exclude scratch \
                --exclude exports \
                --exclude .vscode \
                --exclude '.git' \
                --exclude build \
                --exclude venv \
                --exclude __pycache__ \
                --exclude .pytest_cache \
                --exclude node_modules \
                --exclude .terraform \
                --exclude .terraform* \
                --exclude .next \
                --exclude config.tfvars \
                --exclude backend.tf \
                --exclude package-lock.json \
            ${src_dir_libs} ${dst_dir_libs}

            if [ $? -ne 0 ]; then
                echo "Failure"
                exit 1
            fi
            echo "Success"
        fi
    done < <(python ./iac/scripts/_read_toml_deps.py $toml_file)
done < <(find ./exports/${export_name}/services -name pyproject.toml -print0)


cd exports/${export_name}

zip -r ${export_name}.zip .
mv ${export_name}.zip ../
