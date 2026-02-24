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

import os
import sys  # Import sys for stderr

from dotenv import load_dotenv
from fastapi.openapi.models import OAuth2, OAuthFlowAuthorizationCode, OAuthFlows
from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.auth import AuthCredential, AuthCredentialTypes, OAuth2Auth
from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    StreamableHTTPConnectionParams,
)

load_dotenv()

# Constants
MIN_TOKEN_LENGTH = 20  # OAuth tokens are typically longer than 20 characters
AUTH_HEADER_PREFIX = "Bearer"

# Configuration
mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:5000")
AGENTSPACE_AUTH_ID = os.getenv("AUTH_ID")
DEBUG_CONTEXT = (
    os.getenv("DEBUG_CONTEXT", "true").lower() == "true"
)  # Set to false to disable debug logging

# Environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "deployment").lower()
IS_DEVELOPMENT = ENVIRONMENT == "development"

# OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
OAUTH_REDIRECT_URI_DEV = os.getenv(
    "OAUTH_REDIRECT_URI_DEV", "http://127.0.0.1:8000/dev-ui/"
)
OAUTH_REDIRECT_URI_PROD = os.getenv(
    "OAUTH_REDIRECT_URI_PROD", "https://vertexaisearch.cloud.google.com/oauth-redirect"
)

# Select redirect URI based on environment
redirect_uri = OAUTH_REDIRECT_URI_DEV if IS_DEVELOPMENT else OAUTH_REDIRECT_URI_PROD

# Validation
if not AGENTSPACE_AUTH_ID:
    raise ValueError(
        "AUTH_ID environment variable must be set. Please configure it in your .env file."
    )

# Only validate OAuth credentials in development mode
# In production, AgentSpace provides tokens through the context
if IS_DEVELOPMENT:
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ValueError(
            "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set for development environment."
        )
else:
    # In production, these credentials should NOT be set for security
    # AgentSpace handles OAuth and provides tokens via the context
    print("Production mode: OAuth tokens will be provided by AgentSpace via context")


def debug_print_context(readonly_context: ReadonlyContext):
    """Print ALL context and session data for debugging."""
    if not DEBUG_CONTEXT:
        return
    import json

    def safe_serialize(obj, depth=0):
        """Recursively serialize object to JSON-compatible format."""
        if depth > 10:
            return f"<max depth reached: {type(obj).__name__}>"
        try:
            if obj is None or isinstance(obj, (str, int, float, bool)):
                return obj
            if isinstance(obj, dict):
                return {str(k): safe_serialize(v, depth + 1) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [safe_serialize(item, depth + 1) for item in obj]
            if hasattr(obj, "__dict__"):
                return {
                    "_type": type(obj).__name__,
                    **{
                        k: safe_serialize(v, depth + 1) for k, v in obj.__dict__.items()
                    },
                }
            if hasattr(obj, "items"):
                return {str(k): safe_serialize(v, depth + 1) for k, v in obj.items()}
            return str(obj)
        except Exception as e:
            return f"<error: {type(e).__name__}: {e}>"

    print("=" * 80, file=sys.stderr)
    print("DEBUG: FULL CONTEXT AND SESSION STATE DUMP", file=sys.stderr)
    print("=" * 80, file=sys.stderr)

    # 1. Print all attributes of readonly_context (including private ones)
    print("\n--- readonly_context ALL attributes ---", file=sys.stderr)
    for attr in dir(readonly_context):
        try:
            value = getattr(readonly_context, attr)
            if not callable(value):
                print(f"  {attr}: {safe_serialize(value)}", file=sys.stderr)
        except Exception as e:
            print(f"  {attr}: <error accessing: {e}>", file=sys.stderr)

    # 2. Print readonly_context.__dict__ directly
    print("\n--- readonly_context.__dict__ ---", file=sys.stderr)
    try:
        print(
            json.dumps(
                safe_serialize(readonly_context.__dict__), indent=2, default=str
            ),
            file=sys.stderr,
        )
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)

    # 3. Print session object fully (including private attributes)
    if hasattr(readonly_context, "session"):
        session = readonly_context.session
        print("\n--- session object ---", file=sys.stderr)
        print(f"  type: {type(session).__name__}", file=sys.stderr)
        print(f"  all attrs: {[a for a in dir(session)]}", file=sys.stderr)

        for attr in dir(session):
            try:
                value = getattr(session, attr)
                if not callable(value):
                    print(f"  session.{attr}: {safe_serialize(value)}", file=sys.stderr)
            except Exception as e:
                print(f"  session.{attr}: <error: {e}>", file=sys.stderr)

        # Print session.__dict__ directly
        print("\n--- session.__dict__ ---", file=sys.stderr)
        try:
            print(
                json.dumps(safe_serialize(session.__dict__), indent=2, default=str),
                file=sys.stderr,
            )
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)

        # 4. Print session.state specifically with ALL details
        if hasattr(session, "state"):
            print("\n--- session.state (FULL DUMP) ---", file=sys.stderr)
            try:
                state = session.state
                print(f"  type: {type(state).__name__}", file=sys.stderr)
                print(f"  repr: {repr(state)}", file=sys.stderr)
                print(f"  all attrs: {[a for a in dir(state)]}", file=sys.stderr)

                # Print state.__dict__
                if hasattr(state, "__dict__"):
                    print("\n  state.__dict__:", file=sys.stderr)
                    print(
                        json.dumps(
                            safe_serialize(state.__dict__), indent=4, default=str
                        ),
                        file=sys.stderr,
                    )

                # Try different ways to access state data
                if hasattr(state, "items"):
                    print("\n  state.items():", file=sys.stderr)
                    for k, v in state.items():
                        print(f"    '{k}': {safe_serialize(v)}", file=sys.stderr)
                if hasattr(state, "keys"):
                    print(f"\n  state.keys(): {list(state.keys())}", file=sys.stderr)
                if hasattr(state, "values"):
                    print(
                        f"\n  state.values(): {[safe_serialize(v) for v in state.values()]}",
                        file=sys.stderr,
                    )

                # Try to convert to dict
                try:
                    as_dict = dict(state)
                    print("\n  dict(state):", file=sys.stderr)
                    print(json.dumps(as_dict, indent=4, default=str), file=sys.stderr)
                except Exception as e:
                    print(f"\n  dict(state) failed: {e}", file=sys.stderr)

                # Iterate if iterable
                print("\n  Iterating state keys:", file=sys.stderr)
                try:
                    for i, item in enumerate(state):
                        print(f"    [{i}]: {safe_serialize(item)}", file=sys.stderr)
                        if i > 50:
                            print("    ... (truncated)", file=sys.stderr)
                            break
                except TypeError:
                    print("    (not directly iterable)", file=sys.stderr)
                except Exception as e:
                    print(f"    iteration error: {e}", file=sys.stderr)

            except Exception as e:
                print(f"  Error accessing session.state: {e}", file=sys.stderr)
                import traceback

                traceback.print_exc(file=sys.stderr)

    # 5. Print readonly_context.state if exists
    if hasattr(readonly_context, "state"):
        print("\n--- readonly_context.state ---", file=sys.stderr)
        try:
            state = readonly_context.state
            print(f"  type: {type(state).__name__}", file=sys.stderr)
            print(f"  repr: {repr(state)}", file=sys.stderr)
            if hasattr(state, "__dict__"):
                print(
                    f"  __dict__: {json.dumps(safe_serialize(state.__dict__), indent=4, default=str)}",
                    file=sys.stderr,
                )
            if hasattr(state, "items"):
                print("  items():", file=sys.stderr)
                for k, v in state.items():
                    print(f"    '{k}': {safe_serialize(v)}", file=sys.stderr)
            try:
                as_dict = dict(state)
                print(
                    f"  dict(): {json.dumps(as_dict, indent=4, default=str)}",
                    file=sys.stderr,
                )
            except Exception as e:
                print(f"  dict() failed: {e}", file=sys.stderr)
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)

    # 6. Check for auth-related attributes anywhere (deeper search)
    print(
        "\n--- Searching for auth/token/credential/key keywords (deep) ---",
        file=sys.stderr,
    )
    found_items = []

    def search_for_auth(obj, path="root", depth=0, visited=None):
        if visited is None:
            visited = set()
        obj_id = id(obj)
        if obj_id in visited or depth > 8:
            return
        visited.add(obj_id)
        try:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    key_lower = str(k).lower()
                    if any(
                        kw in key_lower
                        for kw in [
                            "auth",
                            "token",
                            "credential",
                            "oauth",
                            "bearer",
                            "key",
                            "secret",
                            "access",
                        ]
                    ):
                        found_items.append((f"{path}.{k}", safe_serialize(v)))
                    search_for_auth(v, f"{path}.{k}", depth + 1, visited)
            elif hasattr(obj, "__dict__"):
                for k, v in obj.__dict__.items():
                    key_lower = str(k).lower()
                    if any(
                        kw in key_lower
                        for kw in [
                            "auth",
                            "token",
                            "credential",
                            "oauth",
                            "bearer",
                            "key",
                            "secret",
                            "access",
                        ]
                    ):
                        found_items.append((f"{path}.{k}", safe_serialize(v)))
                    search_for_auth(v, f"{path}.{k}", depth + 1, visited)
            elif hasattr(obj, "items"):
                for k, v in obj.items():
                    key_lower = str(k).lower()
                    if any(
                        kw in key_lower
                        for kw in [
                            "auth",
                            "token",
                            "credential",
                            "oauth",
                            "bearer",
                            "key",
                            "secret",
                            "access",
                        ]
                    ):
                        found_items.append((f"{path}.{k}", safe_serialize(v)))
                    search_for_auth(v, f"{path}.{k}", depth + 1, visited)
        except Exception:
            pass

    search_for_auth(readonly_context)
    for path, val in found_items:
        print(f"  FOUND at {path}: {val}", file=sys.stderr)
    if not found_items:
        print("  (no auth-related keys found)", file=sys.stderr)

    print("=" * 80, file=sys.stderr)
    print("END DEBUG DUMP", file=sys.stderr)
    print("=" * 80, file=sys.stderr)


def get_access_token(readonly_context: ReadonlyContext, auth_id: str) -> str | None:
    """Retrieves the OAuth access token from the ReadonlyContext state provided by Agentspace."""

    # Method 1: Try session.state (most common location in Agentspace)
    if hasattr(readonly_context, "session") and hasattr(
        readonly_context.session, "state"
    ):
        try:
            session_state = dict(readonly_context.session.state)

            # Try exact match
            if auth_id in session_state and isinstance(session_state[auth_id], str):
                return session_state[auth_id]

            # Try keys that start with the auth_id (e.g., "auth-0002" matches "auth-0002_123")
            # OR keys that end with the auth_id (e.g., "projects/.../auth-0002")
            for key, value in session_state.items():
                if (
                    (key.startswith(auth_id) or key.endswith(f"/{auth_id}"))
                    and isinstance(value, str)
                    and len(value) > MIN_TOKEN_LENGTH
                ):
                    return value
        except Exception:
            pass

    # Method 2: Try readonly_context.state
    if hasattr(readonly_context, "state"):
        try:
            state_dict = dict(readonly_context.state)
            if auth_id in state_dict and isinstance(state_dict[auth_id], str):
                return state_dict[auth_id]

            # Also check for suffix match in context.state
            for key, value in state_dict.items():
                if (
                    (key.startswith(auth_id) or key.endswith(f"/{auth_id}"))
                    and isinstance(value, str)
                    and len(value) > MIN_TOKEN_LENGTH
                ):
                    return value
        except Exception:
            pass

    # Method 3: Try readonly_context.auth_token
    if hasattr(readonly_context, "auth_token") and readonly_context.auth_token:
        if auth_id in readonly_context.auth_token:
            return readonly_context.auth_token[auth_id]

    # Method 4: Check for managed credentials object (e.g. from OAuth2CredentialExchanger)
    # The exchanger might place a google.oauth2.credentials.Credentials object in the context
    if hasattr(readonly_context, "credentials"):
        creds = readonly_context.credentials
        if hasattr(creds, "token") and creds.token:
            return creds.token

    # Not found - print user-facing error message
    print(f"OAuth token not found for AUTH_ID='{auth_id}'")
    print("User needs to authorize the agent in AgentSpace UI")
    return None


def mcp_header_provider(readonly_context: ReadonlyContext) -> dict[str, str]:
    """Provider function that returns HTTP headers with OAuth token for MCP requests.

    This function is called by McpToolset when making requests to the MCP server.
    It extracts the OAuth token from the Agentspace context and formats it as
    an Authorization header.

    Args:
        readonly_context: The context provided by ADK at runtime

    Returns:
        Dictionary with Authorization header, or empty dict if token not found
    """
    # Print to both stdout and stderr to ensure visibility
    print("=" * 60)
    print("MCP_HEADER_PROVIDER CALLED")
    print(f"readonly_context type: {type(readonly_context)}")
    print(f"readonly_context: {readonly_context}")
    print("=" * 60)

    try:
        # Print debug info if enabled
        debug_print_context(readonly_context)

        # Get the access token (AGENTSPACE_AUTH_ID validated at startup)
        assert AGENTSPACE_AUTH_ID is not None
        print(f"Looking for token with AUTH_ID: {AGENTSPACE_AUTH_ID}")

        access_token = get_access_token(readonly_context, AGENTSPACE_AUTH_ID)

        if not access_token:
            print("WARNING: No access token found!")
            print("Returning empty headers - MCP request will have no Authorization")
            return {}

        # Mask token for logging (show first/last 10 chars)
        masked_token = (
            f"{access_token[:10]}...{access_token[-10:]}"
            if len(access_token) > 25
            else "***"
        )
        print(f"SUCCESS: Found token: {masked_token}")
        print("Returning Authorization header")
        print("=" * 60)

        return {"Authorization": f"{AUTH_HEADER_PREFIX} {access_token}"}
    except Exception as e:
        print(f"ERROR in mcp_header_provider: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return {}


# Create agent with OAuth flow authentication
# Development: Uses OAuth2Auth with client credentials to trigger OAuth flow
# Production: Uses header_provider to retrieve token from Agentspace context

print(f"Environment: {ENVIRONMENT}")
print(f"Initializing agent with AUTH_ID: {AGENTSPACE_AUTH_ID}")
print(f"MCP Server URL: {mcp_url}")
if IS_DEVELOPMENT:
    print(f"OAuth Redirect URI: {redirect_uri}")

# Configure MCP Toolset based on environment
if IS_DEVELOPMENT:
    # Development: Configure OAuth flow with client credentials
    print("Using DEVELOPMENT mode: OAuth2 authentication with client credentials")

    # Create OAuth2 scheme
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

    # Create auth credential
    auth_credential = AuthCredential(
        auth_type=AuthCredentialTypes.OAUTH2,
        oauth2=OAuth2Auth(
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            redirect_uri=redirect_uri,
        ),
    )

    # Create MCP toolset with OAuth flow
    mcp_toolset = McpToolset(
        connection_params=StreamableHTTPConnectionParams(url=mcp_url, timeout=60),
        auth_scheme=auth_scheme,
        auth_credential=auth_credential,
        errlog=None,
    )
else:
    # Production: Use header_provider ONLY (no auth_scheme to avoid CredentialManager)
    print("Using PRODUCTION mode: header_provider only (no auth_scheme)")
    print(f"  -> MCP Server: {mcp_url}")
    print(f"  -> Auth ID: {AGENTSPACE_AUTH_ID}")
    print("  -> Authentication: header_provider reads token from session.state")
    print("  -> IMPORTANT: NOT passing auth_scheme to avoid CredentialManager blocking")

    try:
        # DO NOT pass auth_scheme or auth_credential!
        # This ensures _credentials_manager = None in MCPTool
        # So run_async() skips credential check and calls _run_async_impl()
        # Where header_provider is invoked
        mcp_toolset = McpToolset(
            connection_params=StreamableHTTPConnectionParams(url=mcp_url, timeout=60),
            header_provider=mcp_header_provider,
            errlog=None,
        )

        # Verify no auth_scheme was set
        print(
            f"McpToolset._auth_scheme = {getattr(mcp_toolset, '_auth_scheme', 'N/A')}"
        )
        print(
            f"McpToolset._header_provider = {getattr(mcp_toolset, '_header_provider', 'N/A')}"
        )
        print("MCP Toolset initialized successfully in production mode")
    except Exception as e:
        print(f"ERROR initializing MCP Toolset: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        raise


root_agent = LlmAgent(
    model="gemini-2.5-flash",
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

from google.adk.apps import App

app = App(root_agent=root_agent, name="adk_agent")
