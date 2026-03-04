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

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Literal

import click
import httpx
from fastmcp import FastMCP
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse

from oauth_helper import OAuthConfig, OAuthFlow

# Root .env is 4 levels up: weather_mcp_server/ -> mcp_servers/ -> src/ -> project root
_ROOT_ENV = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class ServerSettings(BaseSettings):
    """Settings for the MCP Server."""

    model_config = SettingsConfigDict(
        env_file=str(_ROOT_ENV), env_file_encoding="utf-8", extra="ignore"
    )

    # GCP settings
    service_name: str = "weather-mcp-server-oauth"
    location: str = "us-central1"
    project_id: str = ""
    project_number: str = ""

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8080
    # In a deployed Cloud Run environment, the server_url will be provided by the environment
    server_url: AnyHttpUrl | None = None
    mcp_scope: str = "user"
    mcp_server_url: AnyHttpUrl | None = None


class OAuthSettings(BaseSettings):
    """OAuth settings from environment."""

    model_config = SettingsConfigDict(
        env_file=str(_ROOT_ENV), env_file_encoding="utf-8", extra="ignore"
    )

    google_client_id: str = ""
    google_client_secret: str = ""
    oauth_scopes: str = "openid email profile"
    oauth_redirect_uri_local: str = "http://localhost:8080/oauth/callback"
    oauth_redirect_uri_prod: str = ""
    use_production_redirect: bool = False  # Set via environment variable


async def verify_google_token(token: str, client_id: str) -> dict[str, Any] | None:
    """Verify Google ID token and return user info."""
    try:
        async with httpx.AsyncClient() as client:
            # Verify the token with Google's tokeninfo endpoint
            response = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"access_token": token},
            )

            if response.status_code != 200:
                print(f"⚠️ Token verification failed: {response.status_code}")
                return None

            token_info = response.json()

            # Verify the token is for our client
            if token_info.get("aud") != client_id and token_info.get("azp") != client_id:
                print("⚠️ Token client ID mismatch")
                return None

            # Check if token is expired
            exp = token_info.get("exp")
            if exp and int(exp) < time.time():
                print("⚠️ Token expired")
                return None

            return token_info

    except Exception as e:
        print(f"❌ Token verification error: {e}")
        return None


class OAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce OAuth authentication on MCP endpoints."""

    def __init__(self, app, oauth_flow: OAuthFlow, client_id: str):
        super().__init__(app)
        self.oauth_flow = oauth_flow
        self.client_id = client_id
        # Paths that don't require authentication
        self.public_paths = {
            "/",
            "/oauth/login",
            "/oauth/callback",
            "/oauth/token-info",
        }

    async def dispatch(self, request: Request, call_next):
        """Check authentication for protected endpoints."""
        path = request.url.path
        method = request.method
        print(f"📥 OAuth Middleware: {method} {path}")

        # Allow public paths
        if path in self.public_paths:
            print(f"✅ OAuth Middleware: {path} is a public path, allowing")
            response = await call_next(request)
            print(f"📤 Response status: {response.status_code} for {method} {path}")
            return response

        # Check if this is an MCP endpoint
        if path.startswith("/mcp"):
            print(f"🔍 OAuth Middleware: {path} is MCP endpoint, checking auth")

            # For GET requests (SSE/streaming), skip body inspection
            # GET requests for SSE should also be allowed for MCP protocol
            if method == "GET":
                print("✅ OAuth Middleware: GET request to MCP endpoint, allowing for SSE")
                response = await call_next(request)
                print(f"📤 Response status: {response.status_code} for {method} {path}")
                return response

            if method == "POST":
                body = await request.body()

                is_public_request = False
                try:
                    body_json = json.loads(body) if body else {}
                    rpc_method = body_json.get("method", "")

                    # Allow initialize, ping, notifications/initialized, and tools/list
                    # without authentication to enable tool discovery before login.
                    if rpc_method in [
                        "initialize",
                        "ping",
                        "notifications/initialized",
                        "tools/list",
                    ]:
                        print(f"✅ OAuth Middleware: Allowing {rpc_method} request without auth")
                        is_public_request = True
                except Exception:
                    pass

                # Set the consumed body back on the request
                request._body = body

                # If it's a public request (init/tools/list), allow without auth
                if is_public_request:
                    response = await call_next(request)
                    print(f"📤 Response status: {response.status_code} for {rpc_method}")
                    return response

                # Otherwise, check authentication
                # Try to get token from Authorization header
                auth_header = request.headers.get("Authorization", "")
                token = None

                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]  # Remove "Bearer " prefix

                # If no token in header, check for stored token (for local testing)
                if not token:
                    stored_token = self.oauth_flow.load_token()
                    if stored_token:
                        token = stored_token.access_token

                # Verify token
                if not token:
                    print(f"⚠️ No token provided for {path}")
                    return JSONResponse(
                        status_code=401,
                        content={
                            "error": "unauthorized",
                            "message": "Authentication required. Please login at /oauth/login",
                        },
                    )

                # Verify the token with Google
                user_info = await verify_google_token(token, self.client_id)
                if not user_info:
                    print(f"⚠️ Invalid token for {path}")
                    msg = "Invalid or expired token. Please login again at /oauth/login"
                    return JSONResponse(
                        status_code=401,
                        content={"error": "invalid_token", "message": msg},
                    )

                # Add user info to request state for use in handlers
                request.state.user = user_info
                print(f"✅ Authenticated user: {user_info.get('email', 'unknown')}")

        response = await call_next(request)

        # Print response details for debugging
        print(f"📤 Response status: {response.status_code} for {method} {path}")

        # For MCP endpoints, print the response body to debug tool calls
        if path.startswith("/mcp") and method == "POST":
            if isinstance(response, StreamingResponse):
                # For streaming responses, we can't easily read the body without consuming it
                print("   Response type: StreamingResponse (body not printed to avoid consumption)")
            else:
                # For regular responses, read and print the body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                try:
                    body_json = json.loads(body.decode())
                    print(f"   Response body: {json.dumps(body_json, indent=2)}")
                except Exception:
                    print(f"   Response body (raw): {body.decode()[:500]}")

                # Reconstruct the response with the body we read
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )

        return response


class HttpClientHolder:
    """Holds the HTTP client instance for weather API requests."""

    client: httpx.AsyncClient | None = None


# Global client holder - accessible for testing
_client_holder = HttpClientHolder()


def create_mcp_server(
    settings: ServerSettings, oauth_settings: OAuthSettings
) -> tuple[FastMCP, OAuthFlow, str]:
    """Create MCP Server with Google ID token verification."""
    from contextlib import asynccontextmanager

    # Use global client holder for testability
    client_holder = _client_holder

    @asynccontextmanager
    async def lifespan(app):
        """Lifespan context manager for resource cleanup."""
        # Create client on startup
        client_holder.client = httpx.AsyncClient(
            base_url="https://api.weather.gov",
            headers={"User-Agent": "weather-agent", "Accept": "application/geo+json"},
            timeout=20.0,
            follow_redirects=True,
        )

        yield

        # Close client on shutdown
        if client_holder.client:
            await client_holder.client.aclose()
            client_holder.client = None

    # Note: Authentication will be handled via OAuth flow and custom middleware
    # FastMCP's auth parameter expects OAuthProvider which is not the same as our setup
    mcp = FastMCP(
        name="weather MCP server",
        instructions="A weather server protected by Google OAuth.",
        host=settings.host,
        port=settings.port,
        debug=True,
        lifespan=lifespan,
    )

    # Create OAuth flow instance
    oauth_config = OAuthConfig(
        client_id=oauth_settings.google_client_id,
        client_secret=oauth_settings.google_client_secret,
        redirect_uri=oauth_settings.oauth_redirect_uri_local,
        redirect_uri_prod=oauth_settings.oauth_redirect_uri_prod
        if oauth_settings.oauth_redirect_uri_prod
        else None,
        scopes=oauth_settings.oauth_scopes.split(),
        use_prod_redirect=oauth_settings.use_production_redirect,
    )
    oauth_flow = OAuthFlow(oauth_config)

    # Note: Middleware will be passed to run() method, not added here
    # Return the MCP server along with OAuth components for middleware setup

    # Add OAuth routes to the MCP server
    @mcp.custom_route("/oauth/login", methods=["GET"])
    async def oauth_login(request):
        """Initiate OAuth login flow."""
        from starlette.responses import HTMLResponse

        auth_url = oauth_flow.get_authorization_url()
        return HTMLResponse(f"""
        <html>
            <head><title>Weather MCP Server - OAuth Login</title></head>
            <body>
                <h1>Weather MCP Server Authentication</h1>
                <p>Click the button below to authenticate with Google:</p>
                <a href="{auth_url}" style="display: inline-block; padding: 10px 20px;
                   background-color: #4285f4; color: white; text-decoration: none;
                   border-radius: 4px;">Sign in with Google</a>
            </body>
        </html>
        """)

    @mcp.custom_route("/oauth/callback", methods=["GET"])
    async def oauth_callback(request):
        """Handle OAuth callback."""
        from starlette.responses import HTMLResponse

        code = request.query_params.get("code")
        state = request.query_params.get("state")
        try:
            token = await oauth_flow.exchange_code_for_token(code, state)
            return HTMLResponse(f"""
            <html>
                <head><title>Authentication Successful</title></head>
                <body>
                    <h1>✅ Authentication Successful!</h1>
                    <p>You have successfully authenticated with Google.</p>
                    <p>Your access token has been saved.</p>
                    <p>You can now close this window and use the MCP client.</p>
                    <h3>Token Information:</h3>
                    <pre>Token Type: {token.token_type}
Expires In: {token.expires_in} seconds
Scopes: {token.scope}</pre>
                    <p><a href="/oauth/token-info">View Token Info</a></p>
                </body>
            </html>
            """)
        except Exception as e:
            print(f"❌ OAuth callback error: {e}")
            return HTMLResponse(
                f"""
            <html>
                <head><title>Authentication Failed</title></head>
                <body>
                    <h1>❌ Authentication Failed</h1>
                    <p>Error: {str(e)}</p>
                    <p><a href="/oauth/login">Try Again</a></p>
                </body>
            </html>
            """,
                status_code=400,
            )

    @mcp.custom_route("/oauth/token-info", methods=["GET"])
    async def token_info(request):
        """Display current token information."""
        from starlette.responses import HTMLResponse

        token = oauth_flow.load_token()
        if not token:
            return HTMLResponse("""
            <html>
                <head><title>No Token Found</title></head>
                <body>
                    <h1>No Token Found</h1>
                    <p>Please <a href="/oauth/login">login</a> first.</p>
                </body>
            </html>
            """)

        return HTMLResponse(f"""
        <html>
            <head><title>Token Information</title></head>
            <body>
                <h1>Current Token Information</h1>
                <pre>{token.model_dump_json(indent=2, exclude={"access_token", "refresh_token"})}</pre>
                <p><strong>Note:</strong> Access token and refresh token are hidden for security.</p>
                <p>Token file location: {oauth_flow.token_file}</p>
            </body>
        </html>
        """)

    @mcp.custom_route("/", methods=["GET"])
    async def root(request):
        """Root endpoint with information."""
        from starlette.responses import HTMLResponse

        return HTMLResponse("""
        <html>
            <head>
                <title>Weather MCP Server</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                    .warning { background-color: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 4px; }
                    code { background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
                </style>
            </head>
            <body>
                <h1>Weather MCP Server with OAuth2</h1>
                <p>This is a Model Context Protocol (MCP) server for weather information.</p>

                <div class="warning">
                    <strong>⚠️ Authentication Required:</strong> The MCP endpoint is protected by OAuth2.
                    You must authenticate before accessing weather tools.
                </div>

                <h2>🔐 OAuth Authentication:</h2>
                <ul>
                    <li><a href="/oauth/login">Login with Google</a> - Start OAuth flow</li>
                    <li><a href="/oauth/token-info">View Token Info</a> - Check current authentication status</li>
                </ul>

                <h2>🌦️ MCP Endpoint:</h2>
                <ul>
                    <li>MCP Server: <code>/mcp</code> <strong>(🔒 OAuth protected)</strong></li>
                    <li>Include your access token in the <code>Authorization: Bearer &lt;token&gt;</code> header</li>
                </ul>

                <h2>📋 Available Tools (after authentication):</h2>
                <ul>
                    <li><code>get_alerts(state)</code> - Get active weather alerts for a US state</li>
                    <li><code>get_forecast(latitude, longitude)</code> - Get forecast by coordinates</li>
                    <li><code>get_forecast_by_city(city, state)</code> - Get forecast by city name</li>
                </ul>
            </body>
        </html>
        """)

    # --- Configuration & Constants ---
    GEOCODE_TIMEOUT = 10.0
    geolocator = Nominatim(user_agent="weather-agent")

    async def get_weather_response(endpoint: str) -> dict[str, Any] | None:
        """Make a request to the NWS API."""
        try:
            response = await client_holder.client.get(endpoint)
            response.raise_for_status()
            return response.json()
        except (
            httpx.HTTPStatusError,
            httpx.TimeoutException,
            httpx.RequestError,
            json.JSONDecodeError,
        ):
            return None

    def format_alert(feature: dict[str, Any]) -> str:
        """Format an alert feature into a readable string."""
        props = feature.get("properties", {})
        return f"""
                Event: {props.get("event", "Unknown Event")}
                Area: {props.get("areaDesc", "N/A")}
                Severity: {props.get("severity", "N/A")}
                Certainty: {props.get("certainty", "N/A")}
                Urgency: {props.get("urgency", "N/A")}
                Effective: {props.get("effective", "N/A")}
                Expires: {props.get("expires", "N/A")}
                Description: {props.get("description", "No description provided.").strip()}
                Instructions: {props.get("instruction", "No instructions provided.").strip()}
                """

    def format_forecast_period(period: dict[str, Any]) -> str:
        """Formats a single forecast period into a readable string."""
        return f"""
               {period.get("name", "Unknown Period")}:
                 Temperature: {period.get("temperature", "N/A")}°{period.get("temperatureUnit", "F")}
                 Wind: {period.get("windSpeed", "N/A")} {period.get("windDirection", "N/A")}
                 Short Forecast: {period.get("shortForecast", "N/A")}
                 Detailed Forecast: {period.get("detailedForecast", "No detailed forecast provided.").strip()}
               """

    @mcp.tool()
    async def get_alerts(state: str) -> str:
        """Get active weather alerts for a specific US state."""
        if not isinstance(state, str) or len(state) != 2 or not state.isalpha():
            return "Invalid input. Please provide a two-letter US state code (e.g., CA)."
        state_code = state.upper()
        endpoint = f"/alerts/active/area/{state_code}"
        data = await get_weather_response(endpoint)
        if data is None:
            return f"Failed to retrieve weather alerts for {state_code}."
        features = data.get("features")
        if not features:
            return f"No active weather alerts found for {state_code}."
        alerts = [format_alert(feature) for feature in features]
        return "\n---\n".join(alerts)

    async def _internal_get_forecast(latitude: float, longitude: float) -> str:
        """Internal helper to fetch and format forecast from coordinates."""
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return "Invalid latitude or longitude provided."
        point_endpoint = f"/points/{latitude:.4f},{longitude:.4f}"
        points_data = await get_weather_response(point_endpoint)
        if points_data is None or "properties" not in points_data:
            return (
                f"Unable to retrieve NWS gridpoint information for {latitude:.4f},{longitude:.4f}."
            )
        forecast_url = points_data["properties"].get("forecast")
        if not forecast_url:
            return f"Could not find the NWS forecast endpoint for {latitude:.4f},{longitude:.4f}."
        forecast_data = None
        try:
            response = await client_holder.client.get(forecast_url)
            response.raise_for_status()
            forecast_data = response.json()
        except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError):
            pass
        if forecast_data is None or "properties" not in forecast_data:
            return "Failed to retrieve detailed forecast data from NWS."
        periods = forecast_data["properties"].get("periods")
        if not periods:
            return "No forecast periods found for this location from NWS."
        forecasts = [format_forecast_period(period) for period in periods[:5]]
        return "\n---\n".join(forecasts)

    @mcp.tool()
    async def get_forecast(latitude: float, longitude: float) -> str:
        """Get the weather forecast for a specific location."""
        return await _internal_get_forecast(latitude, longitude)

    @mcp.tool()
    async def get_forecast_by_city(city: str, state: str) -> str:
        """Get the weather forecast for a specific US city and state."""
        if not city or not isinstance(city, str):
            return "Invalid city name provided."
        if not state or not isinstance(state, str) or len(state) != 2 or not state.isalpha():
            return "Invalid state code."
        query = f"{city.strip()}, {state.strip().upper()}, USA"
        try:
            location = await asyncio.to_thread(geolocator.geocode, query, timeout=GEOCODE_TIMEOUT)
        except (GeocoderTimedOut, GeocoderServiceError):
            return f"Could not get coordinates for '{query}'."
        if location is None:
            return f"Could not find coordinates for '{query}'."
        return await _internal_get_forecast(location.latitude, location.longitude)

    # Return MCP server along with OAuth components
    return mcp, oauth_flow, oauth_settings.google_client_id


@click.command()
@click.option("--port", default=8080, help="Port to listen on")
@click.option(
    "--transport",
    default="streamable-http",
    type=click.Choice(["sse", "streamable-http"]),
    help="Transport protocol to use ('sse' or 'streamable-http')",
)
def main(port: int, transport: Literal["sse", "streamable-http"]) -> int:
    """Run the MCP Server with Google OAuth."""
    settings = ServerSettings(port=port)
    oauth_settings = OAuthSettings()

    try:
        mcp_server, oauth_flow, client_id = create_mcp_server(settings, oauth_settings)
        print(f"🚀 MCP Server with Google Auth running on http://{settings.host}:{settings.port}")
        print(f"   OAuth Login: http://{settings.host}:{settings.port}/oauth/login")
        print(f"   MCP Endpoint: http://{settings.host}:{settings.port}/mcp")

        # Pass OAuth middleware through transport_kwargs
        from starlette.middleware import Middleware

        middleware = [Middleware(OAuthMiddleware, oauth_flow=oauth_flow, client_id=client_id)]
        print("✅ OAuth middleware configured to protect /mcp endpoint")

        mcp_server.run(transport=transport, middleware=middleware)
        print("🛑 Server stopped")
        return 0
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    main()
