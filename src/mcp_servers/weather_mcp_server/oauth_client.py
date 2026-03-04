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

"""OAuth client for authenticating and using the Weather MCP Server."""

import asyncio
import logging
import sys
import webbrowser

import click

from oauth_helper import create_oauth_flow_from_env

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Weather MCP Server OAuth Client."""
    pass


@cli.command()
def login():
    """Start the OAuth login flow."""
    logger.info("Starting OAuth login flow...")

    oauth_flow = create_oauth_flow_from_env()
    auth_url = oauth_flow.get_authorization_url()

    logger.info("=" * 60)
    logger.info("OAuth Login URL:")
    logger.info(auth_url)
    logger.info("=" * 60)
    logger.info("")
    logger.info("Opening browser for authentication...")
    logger.info("If browser doesn't open, copy and paste the URL above.")
    logger.info("")
    logger.info("After authentication, the server will handle the callback.")
    logger.info("Check http://localhost:8080/oauth/callback")

    try:
        webbrowser.open(auth_url)
    except Exception as e:
        logger.warning(f"Failed to open browser: {e}")

    logger.info("\nAlternatively, you can visit http://localhost:8080/oauth/login")


@cli.command()
def token_info():
    """Display current token information."""
    oauth_flow = create_oauth_flow_from_env()
    token = oauth_flow.load_token()

    if not token:
        logger.error("No token found. Please login first using 'oauth_client.py login'")
        sys.exit(1)

    logger.info("Current Token Information:")
    logger.info("=" * 60)
    logger.info(f"Token Type: {token.token_type}")
    logger.info(f"Expires In: {token.expires_in} seconds")
    logger.info(f"Scope: {token.scope}")
    logger.info(f"Has Refresh Token: {'Yes' if token.refresh_token else 'No'}")
    logger.info(f"Token File: {oauth_flow.token_file}")
    logger.info("=" * 60)


@cli.command()
def refresh():
    """Refresh the access token."""

    async def refresh_token():
        oauth_flow = create_oauth_flow_from_env()
        token = oauth_flow.load_token()

        if not token:
            logger.error("No token found. Please login first.")
            sys.exit(1)

        if not token.refresh_token:
            logger.error("No refresh token available. Please login again.")
            sys.exit(1)

        logger.info("Refreshing access token...")
        try:
            new_token = await oauth_flow.refresh_access_token(token.refresh_token)
            logger.info("✅ Token refreshed successfully!")
            logger.info(f"New token expires in: {new_token.expires_in} seconds")
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            sys.exit(1)

    asyncio.run(refresh_token())


@cli.command()
def logout():
    """Clear saved token."""
    oauth_flow = create_oauth_flow_from_env()
    oauth_flow.clear_token()
    logger.info("✅ Token cleared. You have been logged out.")


@cli.command()
def status():
    """Check authentication status."""
    oauth_flow = create_oauth_flow_from_env()
    token = oauth_flow.load_token()

    if token:
        logger.info("✅ You are logged in.")
        logger.info(f"Token expires in: {token.expires_in} seconds")
        logger.info(f"Scopes: {token.scope}")
    else:
        logger.info("❌ You are not logged in.")
        logger.info("Run 'oauth_client.py login' to authenticate.")


if __name__ == "__main__":
    cli()
