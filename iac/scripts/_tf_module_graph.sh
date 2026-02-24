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


# Path to your Terraform file
#terraform_file="./main.tf"

#cat $terraform_file

# Associative array to store module dependencies
declare -A module_dependencies

module_pattern="^module\s+\"([^\"]+)\"\s+\{$"
dependency_pattern="depends_on\s*=\s*\[([^]]*)"
module_dependency_pattern="^module\.(.+)[,\s]*$"

for terraform_file in modules_*.tf; do
    # Read the Terraform file line by line
    while read -r line; do
        #echo "line: $line"
        # Check if the line starts with "module"
        if [[ $line =~ $module_pattern ]]; then
            module_name="${BASH_REMATCH[1]}"
            dependencies=""

            #echo "module_name: $module_name"

            # Continue reading lines until the closing brace of the module block
            while read -r inner_line; do
                # Check for the start of a "depends_on" block
                if [[ $inner_line =~ $dependency_pattern ]]; then
                    # Initialize a variable to accumulate dependencies across multiple lines
                    current_dependencies=""

                    # Keep reading lines until the closing bracket of the depends_on block
                    while read -r dependency_line; do
                        # Break if we find the closing bracket
                        if [[ $dependency_line == *"]" ]]; then
                            break
                        fi
                        current_dependencies+="$dependency_line"
                    done

                    # Extract dependencies from the accumulated string
                    dependencies=$(echo "$current_dependencies" | sed -e 's/[[:space:]]//g' -e 's/"//g' | tr '\n' ',' | sed 's/,$//')
                fi

                # Break the inner loop when we reach the closing brace
                if [[ $inner_line == "}" ]]; then
                    break
                fi
            done

            # Add the module and its dependencies to the map
            module_dependencies[$module_name]="$dependencies"
        fi
    done < "$terraform_file"
done


# Print the module dependencies (split into arrays)
for module_name in "${!module_dependencies[@]}"; do
  IFS=',' read -ra deps <<< "${module_dependencies[$module_name]}"
  if [[ ${module_dependencies[$module_name]} == "" ]]; then
    echo "Module: $module_name, Dependencies: []"
  else
    echo "Module: $module_name, Dependencies: ${deps[@]}"
  fi
done


# Create the DOT file content
dot_content="digraph TerraformDependencies {  "

# Process each module dependency
for module_name in "${!module_dependencies[@]}"; do
    IFS=',' read -ra deps <<< "${module_dependencies[$module_name]}"

    # Determine node color based on prefix
    if [[ $module_name == tool_* ]]; then
        node_color="deepskyblue"
    elif [[ $module_name == webhook_* ]]; then
        node_color="aqua"
    elif [[ $module_name == docker_* ]]; then
        node_color="silver"
    elif [[ $module_name == memorystore_* ]]; then
        node_color="mistyrose"
    elif [[ $module_name == vais_* ]]; then
        node_color="darkolivegreen1"
    elif [[ $module_name == *grafana ]]; then
        node_color="mistyrose"
    elif [[ $module_name == dfcx_* ]]; then
        node_color="khaki1"
    elif [[ $module_name == bigquery_app* ]]; then
        node_color="thistle"
    elif [[ $module_name == bigquery_agents* ]]; then
        node_color="mistyrose"
    else
        node_color="lightgrey"  # Default color for other modules
    fi

    # Add the module to the DOT file
    #dot_content+="  \"$module_name\"  "
    dot_content+="  \"$module_name\" [style=filled, fillcolor=$node_color]  "

    # Add edges for dependencies (if any)
    for dep in "${deps[@]}"; do
        if [[ -n "$dep" ]]; then  # Check if dependency is not empty
            if [[ $dep =~ ^module ]]; then # only include modules.
                dependency_line=$dep
                dependency_line=$(echo "$dependency_line" | sed -e 's/module\.//g')
                dot_content+="  \"$module_name\" -> \"$dependency_line\"  "
            fi
        fi
    done
done

dot_content+="}"

# Remove all newline characters from the dot_content
dot_content=$(echo "$dot_content" | tr -d '\n')

# Write the DOT content to a file
echo "$dot_content" > ../docs/terraform_dependencies.dot

# Generate the PNG image using Graphviz
dot -Tpng -Gdpi=300 -Gsize="10,10!" -Gnodesep=1.0 -Granksep=1.0 ../docs/terraform_dependencies.dot -o ../docs/terraform_dependencies.png

# Generate the SVG image using Graphviz
dot -Tsvg -Gdpi=300 -Gsize="10,10!" -Gnodesep=1.0 -Granksep=1.0 ../docs/terraform_dependencies.dot -o ../docs/terraform_dependencies.svg
