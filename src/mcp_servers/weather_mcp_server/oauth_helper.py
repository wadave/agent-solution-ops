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

"""OAuth2 helper for Google authentication."""

import json
import logging
import secrets
import webbrowser
from typing import Optional
from urllib.parse import urlencode
from pathlib import Path

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class OAuthToken(BaseModel):
    """OAuth token model."""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    scope: str


class OAuthConfig(BaseModel):
    """OAuth configuration.

    Note: For Agentspace production deployment:
    - The MCP server receives tokens from Agentspace (not via direct OAuth callback)
    - Agentspace handles the OAuth flow using redirect_uri_prod
    - The server validates tokens passed in Authorization headers
    """

    client_id: str
    client_secret: str
    redirect_uri: str = "http://localhost:8080/oauth/callback"
    redirect_uri_prod: Optional[str] = (
        None  # For Agentspace: "https://vertexaisearch.cloud.google.com/oauth-redirect"
    )
    auth_uri: str = "https://accounts.google.com/o/oauth2/v2/auth"
    token_uri: str = "https://oauth2.googleapis.com/token"
    scopes: list[str] = ["openid", "email", "profile"]
    use_prod_redirect: bool = False  # Set to True when registering with Agentspace


class OAuthFlow:
    """Handles OAuth2 authorization code flow."""

    def __init__(self, config: OAuthConfig):
        self.config = config
        self.state: Optional[str] = None
        self.token_file = Path.home() / ".weather_mcp_token.json"
        self.state_file = Path.home() / ".weather_mcp_state.json"

    def get_authorization_url(self) -> str:
        """Generate authorization URL for OAuth flow."""
        self.state = secrets.token_urlsafe(32)

        # Save state to file for persistence across requests
        try:
            self.state_file.write_text(json.dumps({"state": self.state}))
            self.state_file.chmod(0o600)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

        # Use production redirect URI if configured
        redirect_uri = (
            self.config.redirect_uri_prod
            if self.config.use_prod_redirect and self.config.redirect_uri_prod
            else self.config.redirect_uri
        )

        params = {
            "client_id": self.config.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.config.scopes),
            "state": self.state,
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Force consent to get refresh token
        }

        return f"{self.config.auth_uri}?{urlencode(params)}"

    async def exchange_code_for_token(
        self, code: str, state: Optional[str] = None
    ) -> OAuthToken:
        """Exchange authorization code for access token."""
        # Load the saved state from file
        saved_state = None
        try:
            if self.state_file.exists():
                state_data = json.loads(self.state_file.read_text())
                saved_state = state_data.get("state")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")

        # Validate state parameter
        if state and state != saved_state:
            raise ValueError("State mismatch - possible CSRF attack")

        # Clean up state file after validation
        try:
            if self.state_file.exists():
                self.state_file.unlink()
        except Exception as e:
            logger.error(f"Failed to clean up state file: {e}")

        # Use production redirect URI if configured
        redirect_uri = (
            self.config.redirect_uri_prod
            if self.config.use_prod_redirect and self.config.redirect_uri_prod
            else self.config.redirect_uri
        )

        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.config.token_uri, data=data)
            response.raise_for_status()
            token_data = response.json()

        token = OAuthToken(**token_data)
        self.save_token(token)
        return token

    async def refresh_access_token(self, refresh_token: str) -> OAuthToken:
        """Refresh access token using refresh token."""
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.config.token_uri, data=data)
            response.raise_for_status()
            token_data = response.json()

        # Preserve refresh token if not returned
        if "refresh_token" not in token_data:
            token_data["refresh_token"] = refresh_token

        token = OAuthToken(**token_data)
        self.save_token(token)
        return token

    def save_token(self, token: OAuthToken) -> None:
        """Save token to file."""
        try:
            self.token_file.write_text(token.model_dump_json(indent=2))
            self.token_file.chmod(0o600)  # Secure file permissions
            logger.info(f"Token saved to {self.token_file}")
        except Exception as e:
            logger.error(f"Failed to save token: {e}")

    def load_token(self) -> Optional[OAuthToken]:
        """Load token from file."""
        try:
            if self.token_file.exists():
                token_data = json.loads(self.token_file.read_text())
                return OAuthToken(**token_data)
        except Exception as e:
            logger.error(f"Failed to load token: {e}")
        return None

    def clear_token(self) -> None:
        """Delete saved token."""
        try:
            if self.token_file.exists():
                self.token_file.unlink()
                logger.info("Token cleared")
        except Exception as e:
            logger.error(f"Failed to clear token: {e}")

    async def get_valid_token(self) -> Optional[OAuthToken]:
        """Get a valid token, refreshing if necessary."""
        token = self.load_token()

        if not token:
            return None

        # For simplicity, always refresh if we have a refresh token
        # In production, you'd check expiry time
        if token.refresh_token:
            try:
                return await self.refresh_access_token(token.refresh_token)
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                return None

        return token

    def start_browser_auth(self) -> str:
        """Start browser-based OAuth flow."""
        auth_url = self.get_authorization_url()
        logger.info("Opening browser for authentication...")
        logger.info(f"If browser doesn't open, visit: {auth_url}")

        try:
            webbrowser.open(auth_url)
        except Exception as e:
            logger.warning(f"Failed to open browser: {e}")

        return auth_url


def create_oauth_flow_from_env(use_production: bool = False) -> OAuthFlow:
    """Create OAuth flow from environment variables.

    Args:
        use_production: If True, use production redirect URI
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Determine redirect URIs
    redirect_uri_local = os.getenv(
        "OAUTH_REDIRECT_URI_LOCAL", "http://localhost:8080/oauth/callback"
    )
    redirect_uri_prod = os.getenv("OAUTH_REDIRECT_URI_PROD", "")

    config = OAuthConfig(
        client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
        redirect_uri=redirect_uri_local,
        redirect_uri_prod=redirect_uri_prod if redirect_uri_prod else None,
        scopes=os.getenv("OAUTH_SCOPES", "openid email profile").split(),
        use_prod_redirect=use_production,
    )

    return OAuthFlow(config)
