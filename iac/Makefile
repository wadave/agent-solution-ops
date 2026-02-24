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

# Define Timestamped Files
CONFIG_TIMESTAMP = build/.make.config.done
INIT_TIMESTAMP = build/.make.init.done

# Default target
.PHONY: all
all: help


# Create Terrafrom Configuration
${CONFIG_TIMESTAMP}: templates/config_tpl.tfvars_
	@mkdir -p build
	GCP_PROJECT=${project} GCP_REGION=${region} APP_NAME=${app_name} bash -c ./scripts/_tf_config_init.sh
	@touch ${CONFIG_TIMESTAMP}

.PHONY: config
config: ${CONFIG_TIMESTAMP}


# Initialize Terraform
${INIT_TIMESTAMP}: ${CONFIG_TIMESTAMP} *.tf
	@mkdir -p ../docs
	terraform init
	@touch ${INIT_TIMESTAMP}

.PHONY: init
init:
ifndef project
	@make ${INIT_TIMESTAMP}
else
	@make ${INIT_TIMESTAMP} project=${project} region=${region} app_name=${app_name}
endif


# Check the Active GCloud Login
.PHONY: gcloud-check
gcloud-check:
	@echo -n "Active GCP Login: "
	@gcloud config list account --format "value(core.account)"
	@echo -n "Active GCP Project: "
	@gcloud config get-value project 2>&1 | grep -v 'Your active configuration is: '
	@echo -n "Active GCP Env. Service Account: "
	@curl "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email" -H "Metadata-Flavor: Google" && echo ""


# Login and Configure GCloud Project
.PHONY: login
login:
ifndef project
	@bash -c ./scripts/_gcloud_login.sh
else
	@bash -c "./scripts/_gcloud_login.sh ${project}"
endif


# Configure GCloud Project
.PHONY: set-project
set-project:
ifndef project
	$(error project is not set!)
endif
	gcloud config set project "${project}"
	gcloud auth application-default set-quota-project "${project}"


# Push Terraform Deployment Configuration
.PHONY: config-push
config-push: config
	@bash -c ./scripts/_tf_config_push.sh


# Pull Terraform Deployment Configuration
.PHONY: config-pull
config-pull: config
	@bash -c ./scripts/_tf_config_pull.sh


# Plan Terraform Deployment
.PHONY: plan
plan: init
	terraform plan -out .terraform.plan --var-file=config.tfvars


# Create a PNG and SVG Graph of the Terraform Deployment
.PHONY: graph
graph: plan
	terraform graph -plan=.terraform.plan | dot -Tpng > ../docs/terraform-graph.png
	terraform graph -plan=.terraform.plan | dot -Tsvg > ../docs/terraform-graph.svg


# Create a Module-focused Graph of the Terraform Deployment
.PHONY: mod-graph
mod-graph:
	@bash -c ./scripts/_tf_module_graph.sh


# Plan Terraform Deployment
.PHONY: happen
happen: .terraform.plan
	terraform apply .terraform.plan


# Upgrade Terraform Modules
.PHONY: upgrade
upgrade: init
ifndef module
	@echo "Upgrading all Terraform modules"
	terraform init -upgrade
else
	@echo "Upgrading Terraform module ${module}"
	terraform init -upgrade -target="module.${module}"
endif


# Destroy Terraform Deployment
.PHONY: disappear
disappear:
	terraform destroy --var-file=config.tfvars


# Destroy Terraform Format
.PHONY: format
format:
	terraform fmt


# Clean Environment
.PHONY: clean
clean:
	rm -rf .terraform .terraform.plan .terraform.lock.hcl build ../exports
	find . -type d -name "build" -exec rm -rf {} +
	find ../ -type d -name "build" -exec rm -rf {} +
	find ../ -type d -name "venv" -exec rm -rf {} +
	find ../ -type d -name "__pycache__" -exec rm -rf {} +
	find ../ -type d -name ".pytest_cache" -exec rm -rf {} +
	find ../ -maxdepth 3 -type d -name "node_modules" -exec rm -rf {} +
	find ../services -type d -name "dist" -exec rm -rf {} +


# De-initialize Terraform
.PHONY: wipe
wipe: clean
	@bash -c ./scripts/_tf_config_deinit.sh


# Fetch the Metadata Service Account
.PHONY: get-sa
get-sa:
	@curl "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email" -H "Metadata-Flavor: Google" && echo ""

# Override Parent Allow-All for Domain Restricted Sharing
.PHONY: allow-drs
allow-drs:
ifndef project
	$(error project is not set!)
endif
	@bash -c "scripts/_gcloud_allow_all_drs.sh $(project)"


# Help
.PHONY: help
help:
	@echo "Usage:"
	@echo "  make config            - Create base Terraform config"
	@echo "  make config-push       - Push Terraform config to GCS bucket"
	@echo "  make config-pull       - Pull Terraform config to GCS bucket"
	@echo "  make gcloud-check      - Check the gcloud active login and project"
	@echo "  make login             - Change the gcloud login and project"
	@echo "  make set-project       - Change the gcloud project"
	@echo "  make init              - Initiatize Terraform providers and modules"
	@echo "  make wipe              - Clean environment and Destroy Terraform configuration and backend"
	@echo "  make plan              - Plan Terraform resource changes"
	@echo "  make get-sa            - Fetch the service account associated with the environment"
	@echo "  make allow-drs         - (Must of Org Admin) Forces Domain Restricted Sharing policy to \"Allow All\""
	@echo "  make graph             - Generate a graph of Terraform resources"
	@echo "  make mod-graph         - Generate a module graph of Terraform resources"
	@echo "  make format            - Format Terraform files"
	@echo "  make happen            - Deploy Terraform resources"
	@echo "  make disappear         - Destroy Terraform resources"
	@echo "  make clean             - Clean environment"
	@echo "  make help              - Show help"
