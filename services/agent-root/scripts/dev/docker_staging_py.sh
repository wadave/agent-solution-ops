#!/bin/bash
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

# Service base environment variables
. ./scripts/dev/base_env.sh

service_slug="$1"
src_dir_certs="$2"

function rsync_to_staging() {
  local src=$1
  local dst=$2

  echo -n "rsync from ${src} to ${dst}: "

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
    "${src}" "${dst}"

  if [ $? -ne 0 ]; then
    echo "Failure"
    exit 1
  fi
  echo "Success"
}

if [ -z "$service_slug" ]; then
  echo "Error: Missing positional parameter 1: service_slug."
  exit 1
fi

if [ -z "$src_dir_certs" ]; then
  echo "Error: Missing positional parameter 2: src_dir_certs."
  exit 1
fi

# Associative array to store module dependencies
declare -A local_libs
declare -A gitssh_libs
declare -A gitssh_urls
declare -A gitssh_branches
declare -A gitssh_subdirs
declare -A gitssh_lib_subdir_raw

local_lib_pattern="^(.*) @ file:../../libs/.*$"
gitssh_lib_pattern="^(.*) @ (git\+ssh://git@.*)@([^#]*)(#.*)?$"

final_lib_dir="./build/docker/${service_slug}/services/${service_slug}/src"
#final_lib_dir="./build/docker/${service_slug}/services/${service_slug}/libs"

rm -rf ./build/docker
rm -rf ./build/staging
mkdir -p ./build/docker/${service_slug}/services/${service_slug}
mkdir -p ${final_lib_dir}


src_dir_service="../../services/${service_slug}"
dst_dir_service="./build/docker/${service_slug}/services"

rsync_to_staging "${src_dir_service}" "${dst_dir_service}"

while IFS= read -r -d '' toml_file; do
    echo "Reading file: $toml_file"

    # Read the TOML deps and process them line by line.
    while IFS= read -r line; do
        #echo "Processing dependency: $line"
        if [[ $line =~ $local_lib_pattern ]]; then
            lib_name="${BASH_REMATCH[1]}"
            local_libs[$lib_name]="$lib_name"

            # Re-write requirements to use local path.
            sed -i -e "s|\"${lib_name} @ .*|\"${lib_name} @ file:///code/${lib_name}\",|g" ${dst_dir_service}/${service_slug}/pyproject.toml
        fi
        if [[ $line =~ $gitssh_lib_pattern ]]; then
            lib_name="${BASH_REMATCH[1]}"
            lib_url="${BASH_REMATCH[2]}"
            lib_branch="${BASH_REMATCH[3]}"
            lib_subdir_raw="${BASH_REMATCH[4]}"
            gitssh_libs[$lib_name]="$lib_name"
            gitssh_urls[$lib_name]="$lib_url"
            gitssh_branches[$lib_name]="$lib_branch"
            if [[ -n "$lib_subdir_raw" ]]; then
                # expecting format like #subdirectory=path/to/dir
                lib_subdir="${lib_subdir_raw#*=}"
                gitssh_subdirs[$lib_name]="$lib_subdir"
            fi

            #echo "lib_name: $lib_name, lib_url: $lib_url, lib_branch: $lib_branch"

            # Re-write requirements to use local path.
            sed -i -e "s|\"${lib_name} @ .*|\"${lib_name} @ file:///code/${lib_name}\",|g" ${dst_dir_service}/${service_slug}/pyproject.toml
        fi
    done < <(python $src_dir_service/scripts/dev/_read_toml_deps.py $toml_file)
done < <(find . -name "pyproject.toml" -print0)


# Print list for debugging
#for lib_name in "${!local_libs[@]}"; do
#  IFS=',' read -ra map_value <<< "${local_libs[$lib_name]}"
#  if [[ ${local_libs[$lib_name]} == "" ]]; then
#    echo "Local lib: $lib_name"
#  else
#    echo "Local lib: $lib_name, map_value: ${map_value[@]}"
#  fi
#done

# Print list for debugging
#for lib_name in "${!gitssh_libs[@]}"; do
#  IFS=',' read -ra map_value <<< "${gitssh_libs[$lib_name]}"
#  if [[ ${gitssh_libs[$lib_name]} == "" ]]; then
#    echo "git+ssh lib: $lib_name"
#  else
#    echo "git+ssh lib: $lib_name, map_value: ${map_value[@]}"
#  fi
#done


# Stage Local Libs
for lib_name in "${!local_libs[@]}"; do
  IFS=',' read -ra map_value <<< "${local_libs[$lib_name]}"
  if [[ ${local_libs[$lib_name]} != "" ]]; then

    echo "Local lib: $lib_name, map_value: ${map_value[@]}"

    src_dir_libs="../../libs/${lib_name}"
    dst_dir_libs="${final_lib_dir}"

    rsync_to_staging "${src_dir_libs}" "${dst_dir_libs}"

    # Re-write requirements to use local path.
    sed -i -e "s|\"\([-_a-zA-Z0-9]\{1,\}\) @ .*|\"\1 @ file:///code/\1\",|g" ${dst_dir_libs}/${lib_name}/pyproject.toml
  fi
done


# Stage ssh+git Libs
for lib_name in "${!gitssh_libs[@]}"; do
  IFS=',' read -ra map_value <<< "${gitssh_libs[$lib_name]}"
  if [[ ${gitssh_libs[$lib_name]} != "" ]]; then

    echo "gitssh lib: $lib_name, map_value: ${map_value[@]}"

    full_lib_path=$(find . -name $lib_name)

    src_dir_libs="${full_lib_path}"
    dst_dir_libs="${final_lib_dir}"
    stage_dir_libs="./build/staging/${service_slug}/libs/${lib_name}"

    gitssh_url=${gitssh_urls[$lib_name]}
    gitssh_branch=${gitssh_branches[$lib_name]}
    gitssh_subdir=${gitssh_subdirs[$lib_name]}

    echo "gitssh_url: ${gitssh_url}, gitssh_branch: ${gitssh_branch}"

    GIT_CONFIG_PARAMETERS="'advice.detachedHead=false'" git clone --branch ${gitssh_branch} --single-branch ${gitssh_url} ${stage_dir_libs}

    if [[ -n "$gitssh_subdir" ]]; then
      # Re-write requirements to use local path.
      sed -i -e "s|\"\([-_a-zA-Z0-9]\{1,\}\) @ .*|\"\1 @ file:///code/\1\",|g" ${stage_dir_libs}/${gitssh_subdir}/pyproject.toml
      rsync_to_staging "${stage_dir_libs}/${gitssh_subdir}/" "${dst_dir_libs}/${lib_name}"
    else
      # Re-write requirements to use local path.
      sed -i -e "s|\"\([-_a-zA-Z0-9]\{1,\}\) @ .*|\"\1 @ file:///code/\1\",|g" ${stage_dir_libs}/pyproject.toml
      rsync_to_staging "${stage_dir_libs}/" "${dst_dir_libs}/${lib_name}"
    fi
  fi
done

# Copy certs directory into final AE image.
if [ "$src_dir_certs" != "na" ]; then
    dst_dir_certs="${final_lib_dir}/certs/"

    rsync_to_staging "${src_dir_certs}" "${dst_dir_certs}"
fi


exit 0
