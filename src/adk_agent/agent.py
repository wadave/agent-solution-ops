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

import logging
import os

from dotenv import find_dotenv, load_dotenv
from fastapi.openapi.models import OAuth2, OAuthFlowAuthorizationCode, OAuthFlows
from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.apps import App
from google.adk.auth import AuthCredential, AuthCredentialTypes, OAuth2Auth
from google.adk.models import Gemini
from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    StreamableHTTPConnectionParams,
)
from google.genai import types

load_dotenv(find_dotenv(".env"))

logger = logging.getLogger(__name__)

# Constants
MIN_TOKEN_LENGTH = 20

# Configuration
mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:5000")
AGENTSPACE_AUTH_ID = os.getenv("AUTH_ID")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS") or "3")
MCP_TIMEOUT = int(os.getenv("MCP_TIMEOUT") or "60")

# Environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "deployment").lower()
IS_DEVELOPMENT = ENVIRONMENT == "development"

# OAuth Configuration (development mode only)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
OAUTH_REDIRECT_URI_DEV = os.getenv("OAUTH_REDIRECT_URI_DEV", "http://127.0.0.1:8000/dev-ui/")
OAUTH_REDIRECT_URI_PROD = os.getenv(
    "OAUTH_REDIRECT_URI_PROD", "https://vertexaisearch.cloud.google.com/oauth-redirect"
)

redirect_uri = OAUTH_REDIRECT_URI_DEV if IS_DEVELOPMENT else OAUTH_REDIRECT_URI_PROD

if not AGENTSPACE_AUTH_ID:
    raise ValueError(
        "AUTH_ID environment variable must be set. Please configure it in your .env file."
    )

if IS_DEVELOPMENT:
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ValueError(
            "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set for development environment."
        )
else:
    logger.info("Production mode: OAuth tokens will be provided by AgentSpace via context")


def get_access_token(readonly_context: ReadonlyContext, auth_id: str) -> str | None:
    """Retrieves the OAuth access token from the ReadonlyContext state provided by Agentspace."""

    # Method 1: Try session.state (most common location in Agentspace)
    if hasattr(readonly_context, "session") and hasattr(readonly_context.session, "state"):
        try:
            session_state = dict(readonly_context.session.state)

            if (
                auth_id in session_state
                and isinstance(session_state[auth_id], str)
                and len(session_state[auth_id]) > MIN_TOKEN_LENGTH
            ):
                return session_state[auth_id]

            for key, value in session_state.items():
                if (
                    (key.startswith(auth_id) or key.endswith(f"/{auth_id}"))
                    and isinstance(value, str)
                    and len(value) > MIN_TOKEN_LENGTH
                ):
                    return value
        except Exception:
            logger.debug("Failed to read session.state for token lookup", exc_info=True)

    # Method 2: Try readonly_context.state
    if hasattr(readonly_context, "state"):
        try:
            state_dict = dict(readonly_context.state)
            if (
                auth_id in state_dict
                and isinstance(state_dict[auth_id], str)
                and len(state_dict[auth_id]) > MIN_TOKEN_LENGTH
            ):
                return state_dict[auth_id]

            for key, value in state_dict.items():
                if (
                    (key.startswith(auth_id) or key.endswith(f"/{auth_id}"))
                    and isinstance(value, str)
                    and len(value) > MIN_TOKEN_LENGTH
                ):
                    return value
        except Exception:
            logger.debug("Failed to read context.state for token lookup", exc_info=True)

    # Method 3: Try readonly_context.auth_token
    auth_token = getattr(readonly_context, "auth_token", None)
    if auth_token:
        if auth_id in auth_token:  # type: ignore
            return auth_token[auth_id]  # type: ignore

    # Method 4: Check for managed credentials object
    creds = getattr(readonly_context, "credentials", None)
    if creds:
        token = getattr(creds, "token", None)
        if token:
            return str(token)

    logger.warning("OAuth token not found for AUTH_ID='%s'. User may need to authorize.", auth_id)
    return None


def mcp_header_provider(readonly_context: ReadonlyContext) -> dict[str, str]:
    """Returns HTTP headers with OAuth token for MCP requests.

    Called by McpToolset on every request to the MCP server. Extracts the
    OAuth token from the Agentspace context and formats it as an Authorization header.
    """
    try:
        assert AGENTSPACE_AUTH_ID is not None
        access_token = get_access_token(readonly_context, AGENTSPACE_AUTH_ID)

        if not access_token:
            logger.warning("No access token found — MCP request will have no Authorization header")
            return {}

        masked = f"{access_token[:10]}...{access_token[-10:]}" if len(access_token) > 25 else "***"
        logger.debug("Injecting Authorization header with token: %s", masked)
        return {"Authorization": f"Bearer {access_token}"}
    except Exception:
        logger.exception("Error in mcp_header_provider")
        return {}


logger.info("Environment: %s | AUTH_ID: %s | MCP URL: %s", ENVIRONMENT, AGENTSPACE_AUTH_ID, mcp_url)

if IS_DEVELOPMENT:
    logger.info("Development mode: OAuth2 authentication with client credentials")
    auth_scheme = OAuth2(
        flows=OAuthFlows(
            authorizationCode=OAuthFlowAuthorizationCode(
                authorizationUrl="https://accounts.google.com/o/oauth2/auth",
                tokenUrl="https://oauth2.googleapis.com/token",
                scopes={
                    "openid": "Authenticate user identity",
                    "email": "Access user's email address",
                    "profile": "Access user's basic profile information",
                },
            )
        )
    )
    auth_credential = AuthCredential(
        auth_type=AuthCredentialTypes.OAUTH2,
        oauth2=OAuth2Auth(
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            redirect_uri=redirect_uri,
        ),
    )
    mcp_toolset = McpToolset(
        connection_params=StreamableHTTPConnectionParams(url=mcp_url, timeout=MCP_TIMEOUT),
        auth_scheme=auth_scheme,
        auth_credential=auth_credential,
        errlog=None,
    )
else:
    logger.info("Production mode: header_provider only (token from AgentSpace session.state)")
    try:
        mcp_toolset = McpToolset(
            connection_params=StreamableHTTPConnectionParams(url=mcp_url, timeout=MCP_TIMEOUT),
            header_provider=mcp_header_provider,
            errlog=None,
        )
    except Exception:
        logger.exception("Failed to initialize MCP Toolset")
        raise


root_agent = LlmAgent(
    model=Gemini(
        model=GEMINI_MODEL,
        retry_options=types.HttpRetryOptions(attempts=RETRY_ATTEMPTS),
    ),
    name="root_agent",
    description="weather agent that tells weather forecast",
    instruction="""You are a weather forecast assistant.

IMPORTANT INSTRUCTIONS:
1. Call the weather tool ONLY ONCE per user query
2. If the tool call fails due to authentication, inform the user they need to authorize the app
3. DO NOT retry failed tool calls - just report the error to the user
4. After receiving tool results (success or failure), respond directly to the user
5. Never make more than 2 tool calls total per user message""",
    tools=[mcp_toolset],
)

app_name = os.environ.get("ADK_AGENT_ENGINE_ID")
if app_name:
    # If it's a full resource path, extract the ID part
    if "/" in app_name:
        app_name = app_name.split("/")[-1]
    logger.info("Initializing ADK App with ID-based name: %s", app_name)
else:
    app_name = "adk_agent"
    logger.warning("ADK_AGENT_ENGINE_ID not set, falling back to default name: %s", app_name)

app = App(root_agent=root_agent, name=app_name)
