#!/usr/bin/env python3
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

"""Direct test of weather tools by importing them."""

import asyncio
import logging

import httpx

from weather_server import (
    OAuthSettings,
    ServerSettings,
    _client_holder,
    create_mcp_server,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


async def main():
    """Test the weather tools directly."""

    logger.info("=" * 70)
    logger.info("WEATHER MCP SERVER - DIRECT TOOL TESTING")
    logger.info("=" * 70)
    logger.info("")

    # Create server instance (but don't run it)
    settings = ServerSettings()
    oauth_settings = OAuthSettings()

    logger.info("Creating MCP server instance...")
    mcp, oauth_flow, client_id = create_mcp_server(settings, oauth_settings)
    logger.info("✓ Server instance created\n")

    # Initialize the HTTP client directly for testing
    logger.info("Initializing HTTP client for testing...")
    _client_holder.client = httpx.AsyncClient(
        base_url="https://api.weather.gov",
        headers={"User-Agent": "weather-agent", "Accept": "application/geo+json"},
        timeout=20.0,
        follow_redirects=True,
    )
    logger.info("✓ HTTP client initialized\n")

    try:
        logger.info("✓ Lifespan context entered (HTTP client initialized)\n")

        # List available tools
        logger.info("Available tools:")
        tools = await mcp.get_tools()
        for i, (name, tool_info) in enumerate(tools.items(), 1):
            logger.info(f"  {i}. {name}")
            if hasattr(tool_info, "description"):
                logger.info(f"     Description: {tool_info.description}")
            logger.info("")

        # Test 1: Get alerts for California
        logger.info("=" * 70)
        logger.info("TEST 1: Get weather alerts for California (CA)")
        logger.info("=" * 70)

        try:
            # Call the tool directly
            result = await mcp._call_tool("get_alerts", {"state": "CA"})
            logger.info(f"\nResult:\n{result}\n")
        except Exception as e:
            logger.error(f"❌ Error: {e}\n")

        # Test 2: Get forecast for San Francisco
        logger.info("=" * 70)
        logger.info("TEST 2: Get weather forecast for San Francisco, CA")
        logger.info("=" * 70)

        try:
            result = await mcp._call_tool(
                "get_forecast_by_city", {"city": "San Francisco", "state": "CA"}
            )
            logger.info(f"\nResult:\n{result}\n")
        except Exception as e:
            logger.error(f"❌ Error: {e}\n")

        # Test 3: Get forecast by coordinates
        logger.info("=" * 70)
        logger.info("TEST 3: Get forecast by coordinates (37.7749, -122.4194)")
        logger.info("=" * 70)

        try:
            result = await mcp._call_tool(
                "get_forecast", {"latitude": 37.7749, "longitude": -122.4194}
            )
            logger.info(f"\nResult:\n{result}\n")
        except Exception as e:
            logger.error(f"❌ Error: {e}\n")

        logger.info("=" * 70)
        logger.info("TESTING COMPLETE")
        logger.info("=" * 70)
    finally:
        # Clean up the HTTP client
        if _client_holder.client:
            await _client_holder.client.aclose()
            _client_holder.client = None
            logger.info("✓ HTTP client closed")


if __name__ == "__main__":
    asyncio.run(main())
