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

. scripts/_common_functions.sh

# Define color variables
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Configuration ---
commands_to_check=("git" "python3" "rsync" "gcloud" "jq" "zip" "make" "bash" "terraform" "sudo" "sed" "cut" "tr" "wget" "curl")
go_commands_to_check=("go")
go_tools_to_check=("$HOME/go/bin/addlicense" "$HOME/gopath/bin/addlicense")
pip_packages_to_check=("toml" "pre-commit" "md-toc" "bandit" "pip-audit")

# --- Main Logic ---
echo -e "\nVerifying presence of required system utilities\n"

missing_system_commands=()
missing_go_tools=()
missing_pip_packages=()

# Check for system commands
for command_name in "${commands_to_check[@]}"; do
    check_command "$command_name"
    if [ $? -eq 0 ]; then
        missing_system_commands+=("$command_name")
    fi
done

# Check for Go commands
for command_name in "${go_commands_to_check[@]}"; do
    check_command "$command_name"
    if [ $? -eq 0 ]; then
        missing_system_commands+=("golang-go") # Add package name for installation
    fi
done

# Check for Go tools
addlicense_found=false
for tool_path in "${go_tools_to_check[@]}"; do
    if [ -f "$tool_path" ]; then
        addlicense_found=true
        break
    fi
done

if [ "$addlicense_found" = true ]; then
    echo -e "    addlicense ${GREEN}✓${NC}"
else
    missing_go_tools+=("addlicense")
fi

# Check for pip packages
for package_name in "${pip_packages_to_check[@]}"; do
    pip show "$package_name" >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        missing_pip_packages+=("$package_name")
    else
        echo -e "    $package_name ${GREEN}✓${NC}"
    fi
done

# --- Output and Exit ---
print_missing_dependencies_and_exit() {
    echo -e "\n[${RED}ERROR${NC}]: Do not proceed with the onboarding - Prerequisites not met.${NC}"

    if [ ${#missing_system_commands[@]} -ne 0 ]; then
        echo -e "\nPlease ensure to install the following system commands using your package manager:"
        echo "    sudo apt-get install -y ${missing_system_commands[*]}"
    fi

    if [ ${#missing_go_tools[@]} -ne 0 ]; then
        echo -e "\nPlease ensure to install the following Go tools:"
        echo "    go install github.com/google/addlicense@latest"
    fi

    if [ ${#missing_pip_packages[@]} -ne 0 ]; then
        echo -e "\nPlease ensure to install the following Python packages:"
        echo "    pip install ${missing_pip_packages[*]}"
    fi

    echo ""
    exit 1
}

if [ ${#missing_system_commands[@]} -eq 0 ] && [ ${#missing_go_tools[@]} -eq 0 ] && [ ${#missing_pip_packages[@]} -eq 0 ]; then
    echo -e "\n[${GREEN}OK${NC}]: Please proceed with the onboarding - All prerequisites are met.${NC}\n"
else
    print_missing_dependencies_and_exit
fi
