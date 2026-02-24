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

"""
ADK to AgentEngine deployment script.
"""
import sys
import os
from dotenv import load_dotenv
import vertexai
from vertexai import agent_engines
import argparse
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.deploy_base import (
    App,
    get_dependencies_from_toml,
    get_folder_or_gitssh_dependencies_from_toml,
    format_dependencies_list,
)


def deploy_agent_engine_app():
    """Deploy the ADK Agent to Agent Engine."""
    parser = argparse.ArgumentParser(
        description="Deploy or update the ADK Agent to Agent Engine."
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="If included, updates the agent engine resource if it exists."
    )
    args = parser.parse_args()

    load_dotenv()

    # Load configuration
    PROJECT_ID = os.getenv("GCP_PROJECT", "unset")
    LOCATION = os.getenv("GCP_REGION", "unset")
    STAGING_BUCKET = os.getenv("STAGING_BUCKET_URI")
    AGENT_NAME = os.getenv("AGENT_NAME")
    SERVICE_ACCOUNT_EMAIL = os.getenv("SERVICE_ACCOUNT_EMAIL")

    print(f"Deploying {AGENT_NAME} to Agent Engine...")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Staging Bucket: {STAGING_BUCKET}")
    if SERVICE_ACCOUNT_EMAIL:
        print(f"Service Account: {SERVICE_ACCOUNT_EMAIL}\n")

    # Initialize Vertex AI
    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=STAGING_BUCKET,
    )

    # Prepare requirements
    src_deps = get_dependencies_from_toml('../pyproject.toml')
    requirements = format_dependencies_list(list(src_deps))

    print(f"Final requirements: {requirements}")

    # Load PSC interface configuration if provided via environment variable
    psc_interface_config = None
    psc_config_env = os.getenv("PSC_INTERFACE_CONFIG")
    if psc_config_env and psc_config_env != "na":
        try:
            psc_interface_config = json.loads(psc_config_env)
            print("Loaded PSC interface configuration from environment variable.")
        except json.JSONDecodeError as e:
            print(f"Error parsing PSC_INTERFACE_CONFIG environment variable: {e}")
            sys.exit(1)

    # Wrap the agent for Agent Engine deployment
    #agent_engine_app = reasoning_engines.AdkApp(
    #    agent=root_agent,
    #    plugins=[ModelArmorSafetyFilterPlugin()],
    #)

    # Agent configuration
    agent_config = {
        "agent_engine": App(),
        #"agent_engine": agent_engine_app,
        "display_name": AGENT_NAME,
        "service_account": SERVICE_ACCOUNT_EMAIL,
        "requirements": requirements,
        "extra_packages": [
            *get_folder_or_gitssh_dependencies_from_toml('../pyproject.toml'),
            "agent.py", # Your main agent file
            # Add any other necessary files here
            "config",
            "agents",
            "utils",
            "certs",
        ],
    }

    if psc_interface_config:
        agent_config["psc_interface_config"] = psc_interface_config

    try:
        # Check for existing agents
        existing_agents = list(agent_engines.list(filter=f'display_name="{AGENT_NAME}"'))

        if existing_agents:
            print(f"Found {len(existing_agents)} existing agent(s) with display name: {AGENT_NAME}")
            print(f"Resource name: {existing_agents[0].resource_name}")

            # Update the existing agent
            if args.update:
                remote_app = agent_engines.update(
                    resource_name=existing_agents[0].resource_name,
                    **agent_config
                )
                print("Updated existing agent.")
            else:
                print("Skipping agent update due to lack of --update flag.")
                sys.exit(0)
        else:
            # Create a new agent
            remote_app = agent_engines.create(**agent_config)
            print("Created new agent.")

        print("\nDeployment successful!")
        print(f"Resource name: {remote_app.resource_name}")
        print("\nIMPORTANT: Save this resource name for registering with AgentSpace!")
        print("\nThe agent will take several minutes to fully deploy.")
        print("Monitor the deployment in Cloud Console > Vertex AI > Agent Builder")

        return remote_app

    except Exception as e:
        print(f"Deployment failed: {str(e)}")
        raise


if __name__ == "__main__":
    deploy_agent_engine_app()
