# Copyright 2026 Google LLC
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
# Author: Dave Wang

"""Integration tests for the deployed Hosting Agent (ADK)."""

import asyncio
import sys
from pathlib import Path

# Add tests directory to path
tests_dir = Path(__file__).parent.parent
sys.path.insert(0, str(tests_dir))

import pytest  # noqa: E402
from test_config import (  # noqa: E402
    DEFAULT_USER_ID,
    HOSTING_AGENT_ID,
    HOSTING_AGENT_RESOURCE_NAME,
    LOCATION,
    PROJECT_ID,
)
from test_utils import print_test_summary, run_adk_agent_test  # noqa: E402

pytestmark = pytest.mark.skipif(
    not HOSTING_AGENT_ID or not HOSTING_AGENT_RESOURCE_NAME,
    reason="HOSTING_AGENT_ID or HOSTING_AGENT_RESOURCE_NAME not set in environment. Skipping deployed tests.",
)


async def test_hosting_agent_weather():
    """Test the Hosting Agent with a weather query."""
    success, response = await run_adk_agent_test(
        agent_resource_name=HOSTING_AGENT_RESOURCE_NAME,
        query="weather in Dallas, TX",
        project_id=PROJECT_ID,
        location=LOCATION,
        user_id=DEFAULT_USER_ID,
    )
    assert success, f"Weather (Dallas) test failed. Response: {response}"


async def test_hosting_agent_houston_weather():
    """Test the Hosting Agent with Houston weather query."""
    success, response = await run_adk_agent_test(
        agent_resource_name=HOSTING_AGENT_RESOURCE_NAME,
        query="weather in Houston, TX",
        project_id=PROJECT_ID,
        location=LOCATION,
        user_id=DEFAULT_USER_ID,
    )
    assert success, f"Weather (Houston) test failed. Response: {response}"


async def test_hosting_agent_generic():
    """Test the Hosting Agent with a generic query."""
    success, response = await run_adk_agent_test(
        agent_resource_name=HOSTING_AGENT_RESOURCE_NAME,
        query="Hello, who are you?",
        project_id=PROJECT_ID,
        location=LOCATION,
        user_id=DEFAULT_USER_ID,
    )
    assert success, f"Generic query test failed. Response: {response}"


async def main():
    """Run all hosting agent tests."""
    print("=" * 80)
    print("TESTING DEPLOYED HOSTING AGENT (ADK)")
    print("=" * 80)

    results = []

    # Test weather queries
    dallas_passed = await test_hosting_agent_weather()
    results.append(("Hosting Agent - Weather (Dallas)", dallas_passed))

    await asyncio.sleep(2)

    houston_passed = await test_hosting_agent_houston_weather()
    results.append(("Hosting Agent - Weather (Houston)", houston_passed))

    await asyncio.sleep(2)

    # Test generic queries
    generic_passed = await test_hosting_agent_generic()
    results.append(("Hosting Agent - Generic Query", generic_passed))

    # Print summary
    all_passed = print_test_summary(results)
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
