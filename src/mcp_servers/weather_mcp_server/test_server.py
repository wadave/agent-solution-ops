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
# Author: Dave Wang

"""Test client for Weather MCP Server with OAuth authentication."""

import asyncio
import sys

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from oauth_helper import create_oauth_flow_from_env


async def test_server_with_oauth():
    """Tests the MCP server with OAuth authentication."""

    # Load OAuth token
    oauth_flow = create_oauth_flow_from_env()
    token = oauth_flow.load_token()

    if not token:
        print("❌ No OAuth token found.")
        print("Please authenticate first:")
        print("  1. Start the server: python weather_server.py")
        print("  2. Login: python oauth_client.py login")
        print("  3. Or visit: http://localhost:8080/oauth/login")
        sys.exit(1)

    # Check if we need to refresh the token
    valid_token = await oauth_flow.get_valid_token()
    if not valid_token:
        print("❌ Token is invalid or expired and couldn't be refreshed.")
        print("Please login again: python oauth_client.py login")
        sys.exit(1)

    print(f"✅ Using OAuth token (expires in {valid_token.expires_in}s)")
    print()

    # Test the MCP server using streamable-http transport with OAuth token
    # The ID token is what we pass for authentication
    headers = {"Authorization": f"Bearer {valid_token.access_token}"}

    # Create transport with headers for OAuth authentication
    transport = StreamableHttpTransport(
        url="http://localhost:8080/mcp",
        headers=headers,
    )

    try:
        async with Client(transport) as client:
            # List available tools
            print("📋 Listing available tools...")
            tools = await client.list_tools()
            for tool in tools:
                print(f"   🛠️  {tool.name}: {tool.description}")

            print()

            # Test get_forecast_by_city tool
            print("🌤️  Testing get_forecast_by_city...")
            result = await client.call_tool(
                "get_forecast_by_city", {"city": "New York", "state": "NY"}
            )
            print(f"   Result:\n{result[0].text}")

            print()

            # Test get_alerts tool
            print("⚠️  Testing get_alerts...")
            result = await client.call_tool("get_alerts", {"state": "CA"})
            print(f"   Result:\n{result[0].text}")

            print()
            print("✅ All tests completed successfully!")

    except Exception as e:
        print(f"❌ Error testing server: {e}")
        print("\nMake sure the server is running:")
        print("  python weather_server.py")
        sys.exit(1)


async def test_server_no_auth():
    """Test server without authentication (should fail)."""
    print("Testing server WITHOUT authentication (should fail)...")
    try:
        async with Client("http://localhost:8080/mcp") as client:
            await client.list_tools()
            print("❌ UNEXPECTED: Server allowed unauthenticated access!")
    except Exception as e:
        print(f"✅ EXPECTED: Authentication required - {type(e).__name__}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Weather MCP Server")
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Test without authentication (should fail)",
    )
    args = parser.parse_args()

    if args.no_auth:
        asyncio.run(test_server_no_auth())
    else:
        asyncio.run(test_server_with_oauth())
