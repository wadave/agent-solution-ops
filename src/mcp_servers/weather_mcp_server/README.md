# Weather MCP Server with OAuth2

A Model Context Protocol (MCP) server for weather information, protected with Google OAuth2 authentication.

## Features

- ✅ OAuth2 authentication using Google
- ✅ Weather forecasts by coordinates or city/state
- ✅ Active weather alerts by US state
- ✅ Secure token storage and automatic refresh
- ✅ Web-based OAuth flow
- ✅ Cloud Run deployment ready

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Usage](#usage)
- [Testing](#testing)
- [Available Tools](#available-tools)
- [Deployment](#deployment)
- [Understanding OAuth](#understanding-oauth)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

---

## Prerequisites

- Python 3.12 or higher
- Google Cloud Project with OAuth2 credentials
- `uv` package manager for dependency management: [Install uv](https://docs.astral.sh/uv/getting-started/installation/)

---

## Setup

### Google OAuth Setup

#### Creating OAuth2 Credentials

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Select or create a project
3. Enable required APIs (if needed)
4. Navigate to **APIs & Services** > **Credentials**
5. Click **Create Credentials** > **OAuth 2.0 Client ID**
6. Choose **Web application**
7. Add authorized redirect URIs:
   - Local: `http://localhost:8080/oauth/callback`
   - Production: `https://your-service-url.run.app/oauth/callback`
8. Download credentials

#### Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and update with your actual values:
   ```bash
   # GCP Project Settings (REQUIRED - replace with your values)
   PROJECT_ID='your-project-id'
   PROJECT_NUMBER='your-project-number'

   # OAuth2 Configuration (REQUIRED - from Google Cloud Console)
   GOOGLE_CLIENT_ID=' '
   GOOGLE_CLIENT_SECRET=' '
   ```

3. Optional settings (defaults are usually fine):
   ```bash
   # Service configuration
   SERVICE_NAME='weather-mcp-server-oauth'
   LOCATION='us-central1'

   # OAuth Scopes
   OAUTH_SCOPES='openid email profile'

   # OAuth Redirect URIs
   OAUTH_REDIRECT_URI_LOCAL='http://localhost:8080/oauth/callback'
   OAUTH_REDIRECT_URI_PROD='https://vertexaisearch.cloud.google.com/oauth-redirect'
   USE_PRODUCTION_REDIRECT='false'

   # MCP Configuration
   MCP_SCOPE='user'
   MCP_SERVER_URL='http://localhost:8080/mcp'
   ```

### Installing Dependencies

```bash
# Install dependencies using uv
uv sync
```

---

## Usage

### Starting the Server

```bash
# Default settings (port 8080, streamable-http)
uv run python weather_server.py

# Custom port
uv run python weather_server.py --port 8080

# Different transport protocol
uv run python weather_server.py --transport sse
```

The server will display:
```
🚀 MCP Server with Google Auth running on http://0.0.0.0:8080
   OAuth Login: http://0.0.0.0:8080/oauth/login
   MCP Endpoint: http://0.0.0.0:8080/mcp
```

### Authentication

#### Option A: CLI Client

```bash
# Login (opens browser)
uv run python oauth_client.py login

# Check status
uv run python oauth_client.py status

# View token details
uv run python oauth_client.py token-info

# Refresh token
uv run python oauth_client.py refresh

# Logout
uv run python oauth_client.py logout
```

#### Option B: Web Browser

1. Visit http://localhost:8080/oauth/login
2. Click "Sign in with Google"
3. Authorize the application
4. You'll see a success page

**Token Storage:** Your authentication token is saved to `~/.weather_mcp_token.json` with secure permissions (600).

### Available Endpoints

- `GET /` - Server information page
- `GET /oauth/login` - Start OAuth flow
- `GET /oauth/callback` - OAuth callback handler
- `GET /oauth/token-info` - View current token information
- `POST /mcp/sse` - MCP protocol endpoint (requires authentication)

---

## Testing

### Test Files

#### 1. `direct_test.py` - Quick Tool Testing

Tests weather tools directly without server running.

```bash
uv run python direct_test.py
```

**What it tests:**
- All 3 weather tools
- Direct function calls
- Weather API integration

**Use when:**
- Fast development testing
- No server needed
- Debugging tool implementations

#### 2. `test_server.py` - Full Integration Testing

Tests complete MCP server with OAuth.

```bash
# Start server first
uv run python weather_server.py

# In another terminal - test with authentication
uv run python test_server.py

# Test without auth (should fail)
uv run python test_server.py --no-auth
```

**What it tests:**
- OAuth token validation
- MCP client connection
- Tool calls over MCP protocol
- Authentication requirements

**Use when:**
- Testing end-to-end functionality
- Verifying OAuth integration
- Pre-deployment validation

### Testing Workflow

**Initial Setup:**
```bash
# 1. Start the server
uv run python weather_server.py

# 2. Authenticate (in browser)
# Visit http://localhost:8080/oauth/login
```

**Quick Development Testing:**
```bash
# Test tools directly (no auth needed)
uv run python direct_test.py
```

**Full Integration Testing:**
```bash
# Test with OAuth (server must be running)
uv run python test_server.py
```

### Manual Testing

**Web Interface:**
- Server Info: http://localhost:8080/
- OAuth Login: http://localhost:8080/oauth/login
- Token Info: http://localhost:8080/oauth/token-info

**MCP Endpoint:**
- Endpoint: `http://localhost:8080/mcp`
- Transport: `streamable-http` or `sse`
- Authentication: Required (Bearer token)

---

## Available Tools

The server provides three weather-related MCP tools:

### 1. `get_alerts`
Get active weather alerts for a US state.

**Parameters:**
- `state` (string): 2-letter state code (e.g., "CA", "NY")

**Example:**
```python
result = await client.call_tool("get_alerts", {"state": "CA"})
```

### 2. `get_forecast`
Get weather forecast by coordinates.

**Parameters:**
- `latitude` (float): Latitude coordinate
- `longitude` (float): Longitude coordinate

**Example:**
```python
result = await client.call_tool("get_forecast", {"latitude": 37.7749, "longitude": -122.4194})
```

### 3. `get_forecast_by_city`
Get weather forecast by city and state.

**Parameters:**
- `city` (string): City name
- `state` (string): 2-letter state code

**Example:**
```python
result = await client.call_tool("get_forecast_by_city", {"city": "San Francisco", "state": "CA"})
```

---

## Deployment

### Cloud Run Deployment

#### Quick Deploy

```bash
# 1. Configure .env
vi .env  # Add PROJECT_ID, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

# 2. Deploy
./deploy.sh

# 3. Get service URL
gcloud run services describe weather-mcp-server-oauth \
  --region us-central1 \
  --format="value(status.url)"

# 4. Update OAuth redirect URI at Google Cloud Console
# Add: https://YOUR-SERVICE-URL/oauth/callback
```

#### Manual Deployment

```bash
# Set environment variables
export SERVICE_NAME='weather-mcp-server-oauth'
export LOCATION='us-central1'
export PROJECT_ID='your-project-id'
export PROJECT_NUMBER='your-project-number'

# Load .env variables
export $(sed -e '/^ *#/d' -e '/^$/d' -e 's/ *= */=/' -e "s/'//g" -e 's/"//g' .env | xargs)

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $LOCATION \
  --project $PROJECT_ID \
  --memory 4G \
  --no-allow-unauthenticated \
  --set-env-vars GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID}" \
  --set-env-vars GOOGLE_CLIENT_SECRET="${GOOGLE_CLIENT_SECRET}"
```

#### Add IAM Permissions

**Compute Service Account:**
```bash
gcloud run services add-iam-policy-binding $SERVICE_NAME \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/run.invoker" \
    --region="${LOCATION}"
```

#### Update OAuth Redirect URI

After deployment:
1. Get your Cloud Run URL
2. Add to Google Cloud Console > APIs & Credentials > OAuth 2.0 Client IDs
3. Add redirect URI: `https://your-service-url.run.app/oauth/callback`

#### Access Cloud Run Service

```bash
# Proxy to Cloud Run service
gcloud run services proxy $SERVICE_NAME --region=${LOCATION}

# View logs
gcloud run services logs tail $SERVICE_NAME --region=$LOCATION
```

---

## Understanding OAuth

### What is OAuth?

OAuth is like a **valet key** for your car:
- You give the valet a special key that only starts the car
- The valet can park your car but can't access your trunk
- You can revoke the key anytime

OAuth lets users:
- Give your app limited access to their Google account
- Without sharing their Google password
- Can revoke access anytime

### OAuth Flow

1. **Authorization**: User visits `/oauth/login` and is redirected to Google
2. **User Approval**: User signs in and approves requested permissions
3. **Callback**: Google redirects to `/oauth/callback` with authorization code
4. **Token Exchange**: Server exchanges code for access token, ID token, and refresh token
5. **Token Storage**: Tokens are saved to `~/.weather_mcp_token.json`
6. **API Access**: Client includes ID token in Authorization header
7. **Token Verification**: Server verifies ID token on each request
8. **Token Refresh**: Automatic refresh using refresh token when needed

### OAuth Scopes

The server requests these permissions:
- `openid` - Authenticate user's identity
- `email` - Get user's email address
- `profile` - Get user's name and profile picture

These are minimal scopes needed for basic authentication.

### Security Features

- **CSRF Protection**: State parameter with cryptographic random value
- **Secure Storage**: Token file has 600 permissions (owner-only read/write)
- **Automatic Refresh**: Tokens are refreshed automatically when expired
- **HTTPS in Production**: Cloud Run provides automatic HTTPS
- **Minimal Scopes**: Only request permissions actually needed

---

## OAuth Middleware Architecture

The server uses a two-layer authentication architecture to protect the MCP endpoint while allowing public access to OAuth routes.

### Two-Layer Authentication

**Layer 1: Cloud Run IAM** (`--allow-unauthenticated`)
- Allows anyone to reach the HTTP endpoints
- Required so users can access `/oauth/login` to authenticate

**Layer 2: Application OAuth Middleware**
- Protects the MCP endpoint and tools
- Validates Google OAuth tokens before allowing MCP access
- Implemented via `OAuthMiddleware` class

### Middleware Components

**OAuthMiddleware Class** (`weather_server.py:105-165`)
- Protects all `/mcp*` paths
- Allows public access to: `/`, `/oauth/login`, `/oauth/callback`, `/oauth/token-info`
- Checks `Authorization: Bearer <token>` header
- Falls back to locally saved token (for development)
- Adds `request.state.user` with user info on successful auth

**Token Verification** (`weather_server.py:71-102`)
1. Calls Google's tokeninfo endpoint
2. Validates `aud` or `azp` matches our `client_id`
3. Checks token hasn't expired
4. Returns user info or `None`

### Public vs Protected Endpoints

**Public** (No Authentication Required):
- `GET /` - Server information
- `GET /oauth/login` - Initiate OAuth flow
- `GET /oauth/callback` - OAuth redirect handler
- `GET /oauth/token-info` - View token status

**Protected** (OAuth Required):
- `POST /mcp` - MCP server endpoint
- All MCP tool calls



## Troubleshooting

### "No OAuth token found"
**Solution:** Authenticate first:
```bash
uv run python oauth_client.py login
# or visit http://localhost:8080/oauth/login
```

### "redirect_uri_mismatch"
**Solution:** Make sure the redirect URI matches exactly in:
1. Your `.env` file
2. Google Cloud Console OAuth credentials

For local: `http://localhost:8080/oauth/callback`

### "Token is invalid or expired"
**Solution:** Refresh or re-authenticate:
```bash
uv run python oauth_client.py refresh
# or
uv run python oauth_client.py login
```

### "State mismatch - possible CSRF attack"
**Solution:** This was fixed by persisting state to disk. If you see this:
1. Clear old state files: `rm ~/.weather_mcp_state.json`
2. Try logging in again

### Server not starting
**Solution:** Check environment variables:
```bash
cat .env
# Ensure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set
```

### Connection refused after OAuth redirect
**Solution:** Make sure the server is running:
```bash
uv run python weather_server.py
```

### Import errors
**Solution:** Install dependencies:
```bash
uv sync
```

### Cloud Run deployment fails
**Solution:** Check logs:
```bash
gcloud run services logs tail weather-mcp-server-oauth --region=us-central1
```

Common issues:
- Missing environment variables
- Incorrect redirect URI configuration
- Insufficient IAM permissions

---

## Development

### Project Structure

```
weather_mcp_server/
├── weather_server.py      # Main MCP server with OAuth
├── oauth_helper.py        # OAuth flow implementation
├── oauth_client.py        # CLI client for OAuth operations
├── direct_test.py         # Direct tool testing (no server needed)
├── test_server.py         # Integration testing (with OAuth)
├── .env                   # Environment configuration (create from .env.example)
├── .env.example           # Example environment configuration
├── pyproject.toml         # Python dependencies
├── deploy.sh              # Cloud Run deployment script
└── README.md              # This file
```

### Adding Dependencies

Edit `pyproject.toml` and run:

```bash
uv sync
```

### Code Organization

**`weather_server.py`:**

- FastMCP server setup
- OAuth route handlers
- Weather API tool implementations

**`oauth_helper.py`:**

- OAuth flow logic
- Token management (save/load/refresh)
- State persistence for CSRF protection

**`oauth_client.py`:**

- CLI interface for OAuth operations
- User-friendly authentication commands

### Contributing

When adding new features:

1. Add direct tests in `direct_test.py` for new tools
2. Add integration tests in `test_server.py` for OAuth flows
3. Update this README with new functionality
4. Test locally before deploying to Cloud Run

---

## Security Considerations

- **Token Storage**: Tokens stored in `~/.weather_mcp_token.json` with 600 permissions
- **State Parameter**: CSRF protection using cryptographic random state, persisted to disk
- **HTTPS**: Use HTTPS in production (Cloud Run provides this automatically)
- **Scopes**: Request minimal scopes needed (openid, email, profile)
- **Token Expiry**: Automatic token refresh using refresh tokens
- **Secrets**: Never commit `.env` file with real credentials to git
- **API Keys**: Store in environment variables, not in code

---

## License

Copyright 2025 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.

See LICENSE file for details.

---

## Additional Resources

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [National Weather Service API](https://www.weather.gov/documentation/services-web-api)
