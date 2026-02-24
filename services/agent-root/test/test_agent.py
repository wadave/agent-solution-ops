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

import os
import sys
import pytest
from src.agent import create_agent as create_agent

import asyncio
import logging
import common_logging as logs

from dotenv import load_dotenv
import google.auth
import vertexai
from google import genai
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.plugins import load_plugins_from_toml


# Logging
logging.getLogger("google_adk").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logs.get_logger('adk.sub_agent.folder', logging.INFO)


load_dotenv()


parameterized_test_data = [
    (
        "What's the weather today in Toronto, ON?"
    ),
]


PROJECT_ID = os.getenv("GCP_PROJECT", "unset")
LOCATION = os.getenv("GCP_REGION", "us-central1")
MAX_STEPS = int(os.getenv("MAX_STEPS", 30))

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION


async def call_agent_async(prompt: str|Content):
    # Create session service
    session_service = InMemorySessionService()

    # Create agent runner
    root_agent = create_agent()
    runner = Runner(
        agent=root_agent,
        app_name="root_agent",
        session_service=session_service,
        plugins=load_plugins_from_toml(env="test"),
    )

    # Create session
    session = await session_service.create_session(
        app_name="root_agent", user_id="default_user"
    )

    # Convert prompt
    if isinstance(prompt, str):
        message = Content(role="user", parts=[Part(text=prompt)])
    else: # is Content
        message = prompt

    # Log maximum steps
    log.info(f"🛑 [System] Safety Limit set to {MAX_STEPS} steps.")
    step_count = 0

    # Run the agent and print the response
    async for event in runner.run_async(
        session_id=session.id, user_id="default_user", new_message=message
    ):
        step_count += 1

        # Maximum steps threshold exceeded
        if step_count > MAX_STEPS:
            log.error(f"\n❌ [System] Exiting after reaching max steps ({MAX_STEPS}).")
            break

        # TODO: Insert custom validation logic in event loop or final respose.

        # Final response
        if event.is_final_response():
            if event.content and event.content.parts:
                log.info(f"\n🤖 [{root_agent.name}]: {event.content.parts[0].text}")
            else:
                log.info("\n🤖 [{root_agent.name}]: (Final response empty)")
            break

        # In-flight step update
        log.info(f"   ⚙️ [System] Step {step_count}: Processing...")


# Run parameterized tests N times
N = 1
@pytest.mark.parametrize(
    "run_number",
    range(N),
)
@pytest.mark.parametrize(
    "prompt",
    parameterized_test_data,
)
def test_agent_run(prompt, run_number):
    log.info(f"🚀 [root_agent] Launching test run {run_number}...")
    log.info(f"📝 Prompt: {prompt}")

    _, _ = google.auth.default()
    log.info(f"☁️ Project: {PROJECT_ID}, Region: {LOCATION}")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    _ = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
    )

    asyncio.run(call_agent_async(prompt))
