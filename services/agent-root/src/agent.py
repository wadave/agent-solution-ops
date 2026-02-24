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

import os
import sys
import logging
from dotenv import load_dotenv


import vertexai
from google.adk.agents import Agent
from google import genai
from google.adk.tools.tool_context import ToolContext

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.remote_agents import get_remote_agents, retrieve_agent_cards
from utils.folder_agents import get_folder_agents
from utils import tools as tools_utils

import common_logging as logs
from common_gcp import oauth
from config import agents as agents_config


load_dotenv()


log = logs.get_logger('adk.root_agent', logging.INFO)


PROJECT_ID = os.getenv("GCP_PROJECT", "unset")
LOCATION = os.getenv("GCP_REGION", "us-central1")
STAGING_BUCKET = os.getenv("STAGING_BUCKET_URI")
AUTH_ID = os.getenv("AUTH_ID", "ui_oauth_token")
gcs_a2a_bucket = os.getenv('AGENT_CARD_BUCKET_URI')

required_vars = {
    "GCP_PROJECT_ID": PROJECT_ID,
    "GCP_STAGING_BUCKET": STAGING_BUCKET,
    "AGENT_CARD_BUCKET_URI": gcs_a2a_bucket,
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

log.info(f"Initialized Vertex AI with project: {PROJECT_ID}, location: {LOCATION}")

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION

genai_client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION,
)
log.info(f"Initialized GenAI Client for project: {PROJECT_ID}, location: {LOCATION}")


def get_user_email(tool_context: ToolContext):
    """Fetches the user's email using the userinfo.email scope."""
    try:
        access_token = tools_utils.search_id_token(AUTH_ID, tool_context)
        user_info = oauth.get_user_info_from_access_token(access_token)

        # Print the user's email
        log.info(f"User's email: {user_info.get('email')}")

        return user_info
    except Exception as e:
        log.error(f"An error occurred: {e}")


# Agent
def create_agent():
    """
    Factory function to create the root agent.
    """
    agent_cards = retrieve_agent_cards()
    remote_agents = get_remote_agents(agent_cards=agent_cards)
    log.info(f"Remote agents: {remote_agents}")

    folder_agents = get_folder_agents()
    log.info(f"Folder agents: {folder_agents}")

    all_agents = remote_agents + folder_agents

    # Dynamically construct the description and instructions from remote agents
    capabilities = [
        "AI agent with the following capabilities via tools:\n\n",
        "   *get_user_email*: Use this tool to look up the current user's profile and email address.\n",
        "\n",
        "AI agent with the following capabilities via sub-agents:\n\n",
    ]
    instructions = [
        "Always use the most relevant tool or sub-agent to respond to user utterances.\n\n"
        "Tools:\n\n",
        "   *get_user_email*: Use this tool to look up the current user's profile and confirm their email address.\n",
        "\nSub-Agents:\n\n",
    ]

    for i, agent in enumerate(all_agents):
        capabilities.append(
            f"{i+1}. **{agent.name}**: Use this agent when you need: {agent.description}.\n"
        )
        instructions.append(
            f"{i+1}. **{agent.name}**: Use this agent when you need: {agent.description}.\n"
        )

    description = " ".join(capabilities)
    instruction = "\n".join(instructions) + "\nStart by greeting the user and asking how you can help them today."

    return Agent(
        name="root_agent",
        model=agents_config.DEFAULT_MODEL_NAME,
        description=description,
        instruction=instruction,
        sub_agents=[*all_agents],
        tools=[get_user_email],
    )

# Create the agent instance for local use
root_agent = create_agent()
