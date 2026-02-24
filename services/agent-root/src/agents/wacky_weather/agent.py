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

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import common_logging as logs
from config import agents as agents_config


load_dotenv()


log = logs.get_logger('adk.sub_agent.folder', logging.INFO)


PROJECT_ID = os.getenv("GCP_PROJECT", "unset")
LOCATION = os.getenv("GCP_REGION", "us-central1")
AUTH_ID = os.getenv("AUTH_ID", "ui_oauth_token")

required_vars = {
    "GCP_PROJECT": PROJECT_ID,
    "GCP_REGION": LOCATION,
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
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


# Agent
def create_agent():
    """
    Factory function to create the agent.
    """
    return Agent(
        name="wacky_weather_agent",
        model=agents_config.DEFAULT_MODEL_NAME,
        description=(
            "A fun, wacky weather prediction agent that provides silly and ridiculous forecasts that don't make sense, including the occasional appearance of movie monsters."
        ),
        instruction="""Provide a silly and ridiculous weather forecast that doesn't make sense. Include the occasional appearance of movie monsters in the forecast.""",
    )
