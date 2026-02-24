# ADK MCP OAuth Architecture

This document describes the architecture of the Weather MCP Server with OAuth integration for Google Cloud Gemini Enterprise.

## Table of Contents

- [Overview](#overview)
- [Components](#components)
- [Development Architecture](#development-architecture)
- [Production Architecture](#production-architecture)
- [OAuth Flow Details](#oauth-flow-details)
- [Sequence Diagrams](#sequence-diagrams)

---

## Overview

This system demonstrates how to build an ADK (Agent Development Kit) agent that uses a remote MCP (Model Context Protocol) server with OAuth2 authentication, supporting both local development and production deployment to Google Cloud Gemini Enterprise.

**Key Feature:** The agent uses **dual-mode authentication** that automatically switches between:

- **Development Mode**: OAuth2Auth with client credentials (browser-based OAuth flow)
- **Production Mode**: Token retrieval from Gemini Enterprise context via header_provider

### Key Technologies

- **ADK (Agent Development Kit)**: Framework for building AI agents
- **MCP (Model Context Protocol)**: Protocol for tool/resource integration
- **FastMCP**: Python framework for building MCP servers
- **Google OAuth 2.0**: User authentication and authorization
- **Vertex AI Gemini Enterprise**: Production deployment platform
- **Cloud Run**: Serverless container hosting

---

## Components

### High-Level Component Diagram

```mermaid
graph TB
    subgraph "Google Cloud Platform"
        subgraph "User Interface"
        UI["Gemini Enterprise UI"]
        end
        subgraph "Gemini Enterprise"
            AS["Gemini Enterprise Engine"]
            RE["Agent Engine<br/>ADK Agent"]
        end

        subgraph "Cloud Run"
            MCP["Weather MCP Server<br/>FastMCP + OAuth"]
        end

    end

    subgraph "External Services"
            OAUTH["Google OAuth2.0
            or 3rd Party Provider"]
            NWS["NWS Weather API"]
        end

    UI -->|User Query| AS
    AS -->|Invoke Agent| RE
    RE -->|MCP Tool Call| MCP
    MCP -->|Fetch Weather| NWS

    AS -.->|OAuth Flow| OAUTH
    OAUTH -.->|Tokens| AS
    AS -.->|Pass Token| MCP

    style UI fill:#e1f5ff,stroke:#333,stroke-width:2px,color:#000
    style AS fill:#fff4e1,stroke:#333,stroke-width:2px,color:#000
    style RE fill:#f0e1ff,stroke:#333,stroke-width:2px,color:#000
    style MCP fill:#e1ffe1,stroke:#333,stroke-width:2px,color:#000
    style OAUTH fill:#ffe1e1,stroke:#333,stroke-width:2px,color:#000
    style NWS fill:#f5f5f5,stroke:#333,stroke-width:2px,color:#000
```

### Component Descriptions

| Component                    | Technology        | Purpose                                              | Location              |
| ---------------------------- | ----------------- | ---------------------------------------------------- | --------------------- |
| **Gemini Enterprise UI**     | Web UI            | User interface for interacting with agents           | Cloud-hosted          |
| **Gemini Enterprise Engine** | Vertex AI         | Orchestrates agents, handles OAuth, manages sessions | `global` or region    |
| **Agent Engine (ADK Agent)** | Python + ADK      | AI agent with LLM and MCP tool integration           | Deployed to Vertex AI |
| **Weather MCP Server**       | FastMCP + FastAPI | Provides weather tools via MCP protocol              | Cloud Run             |
| **Google OAuth 2.0**         | OAuth 2.0         | User authentication and authorization                | Google-managed        |
| **NWS Weather API**          | REST API          | National Weather Service data source                 | External              |

---

## Development Architecture

### Local Development Setup

```mermaid
graph TB
    subgraph "Developer Machine"
        DEV[Developer]
        BROWSER[Web Browser]

        subgraph "ADK Agent Process"
            AGENT[ADK Agent<br/>src/adk_agent/agent.py]
            WEBUI[ADK Web UI<br/>:8000]
        end

        subgraph "MCP Server Process"
            MCP[Weather MCP Server<br/>:8080]
            OAUTH_ROUTES[OAuth Routes<br/>/oauth/login<br/>/oauth/callback]
            TOKEN_STORE[Token Storage<br/>~/.weather_mcp_token.json]
        end
    end

    subgraph "External"
        GOOGLE_OAUTH[Google OAuth 2.0]
        WEATHER_API[NWS Weather API]
    end

    DEV -->|1. Start Server| MCP
    DEV -->|2. Visit| BROWSER
    BROWSER -->|3. http://localhost:8080/oauth/login| OAUTH_ROUTES
    OAUTH_ROUTES -->|4. Redirect| GOOGLE_OAUTH
    GOOGLE_OAUTH -->|5. User Authenticates| GOOGLE_OAUTH
    GOOGLE_OAUTH -->|6. Redirect + Code| OAUTH_ROUTES
    OAUTH_ROUTES -->|7. Exchange Code| GOOGLE_OAUTH
    GOOGLE_OAUTH -->|8. Return Tokens| OAUTH_ROUTES
    OAUTH_ROUTES -->|9. Save| TOKEN_STORE

    DEV -->|10. Start Agent| AGENT
    AGENT -->|11. Render UI| WEBUI
    DEV -->|12. Chat| WEBUI
    WEBUI -->|13. MCP Call + Token| MCP
    MCP -->|14. Validate Token| MCP
    MCP -->|15. Fetch Data| WEATHER_API
    WEATHER_API -->|16. Weather Data| MCP
    MCP -->|17. Response| AGENT
    AGENT -->|18. LLM Response| WEBUI

    style DEV fill:#e1f5ff
    style AGENT fill:#f0e1ff
    style MCP fill:#e1ffe1
    style GOOGLE_OAUTH fill:#ffe1e1
    style TOKEN_STORE fill:#fff4e1
```

### Development OAuth Flow

**Redirect URI:** `http://localhost:8080/oauth/callback`

**Environment Configuration:**

```bash
ENVIRONMENT=development
USE_PRODUCTION_REDIRECT=false
OAUTH_REDIRECT_URI_LOCAL=http://localhost:8080/oauth/callback
```

---

## Production Architecture

### Gemini Enterprise Deployment

```mermaid
graph TB
    USER[User]

    subgraph "Google Cloud Platform"
        UI[Gemini Enterprise UI<br/>Web Interface]

        subgraph "Gemini Enterprise"
            AS[Gemini Enterprise Engine]

            subgraph "Agent Components"
                RE[Agent Engine<br/>ADK Agent Deployed]
                AUTH_CONFIG[Authorization Config<br/>OAuth Client Credentials]
            end
        end

        subgraph "Cloud Run"
            MCP_SERVER[Weather MCP Server<br/>FastMCP Service]

            subgraph "MCP Endpoints"
                MCP_ENDPOINT[/mcp Endpoint<br/>SSE/HTTP Transport]
                TOOLS[Weather Tools<br/>get_forecast<br/>get_alerts<br/>get_forecast_by_city]
            end
        end
    end

    subgraph "External Services"
        GOOGLE_OAUTH[Google OAuth 2.0<br/>accounts.google.com]
        NWS[National Weather Service<br/>api.weather.gov]
    end

    USER -->|1. Query| UI
    UI -->|2. Route to Agent| AS
    AS -->|3. Check Auth| AUTH_CONFIG
    AS -.->|4. OAuth Flow<br/>if needed| GOOGLE_OAUTH
    GOOGLE_OAUTH -.->|5. Redirect to<br/>vertexaisearch.cloud.google.com| AS
    AS -->|6. Invoke with Token| RE
    RE -->|7. MCP Tool Call<br/>+ Auth Header| MCP_ENDPOINT
    MCP_ENDPOINT -->|8. Validate Token| MCP_ENDPOINT
    MCP_ENDPOINT -->|9. Execute Tool| TOOLS
    TOOLS -->|10. API Request| NWS
    NWS -->|11. Weather Data| TOOLS
    TOOLS -->|12. MCP Response| RE
    RE -->|13. LLM Processing| RE
    RE -->|14. Answer| AS
    AS -->|15. Display| UI
    UI -->|16. Show Result| USER

    style USER fill:#e1f5ff
    style UI fill:#fff4e1
    style AS fill:#ffe1e1
    style RE fill:#f0e1ff
    style MCP_SERVER fill:#e1ffe1
    style GOOGLE_OAUTH fill:#ffe1e1
    style NWS fill:#f5f5f5
```

### Production OAuth Flow

**Redirect URI:** `https://vertexaisearch.cloud.google.com/oauth-redirect`

**Environment Configuration:**

```bash
ENVIRONMENT=production
USE_PRODUCTION_REDIRECT=true
OAUTH_REDIRECT_URI_PROD=https://vertexaisearch.cloud.google.com/oauth-redirect
```

---

## OAuth Flow Details

### Development vs Production Comparison

```mermaid
graph LR
    subgraph "Development Flow"
        D1[User] --> D2[MCP Server<br/>/oauth/login]
        D2 --> D3[Google OAuth]
        D3 --> D4[MCP Server<br/>/oauth/callback]
        D4 --> D5[Token Storage<br/>~/.weather_mcp_token.json]
        D5 --> D6[MCP Client]
    end

    subgraph "Production Flow"
        P1[User] --> P2[Gemini Enterprise UI]
        P2 --> P3[Gemini Enterprise Engine]
        P3 --> P4[Google OAuth]
        P4 --> P5[Gemini Enterprise<br/>vertexaisearch redirect]
        P5 --> P6[Gemini Enterprise<br/>Token Manager]
        P6 --> P7[MCP Server<br/>via Auth Header]
    end

    style D1 fill:#e1f5ff
    style D2 fill:#e1ffe1
    style D4 fill:#e1ffe1
    style D5 fill:#fff4e1

    style P1 fill:#e1f5ff
    style P2 fill:#fff4e1
    style P3 fill:#ffe1e1
    style P5 fill:#ffe1e1
    style P7 fill:#e1ffe1
```

### Key Differences

| Aspect                | Development                               | Production                                               |
| --------------------- | ----------------------------------------- | -------------------------------------------------------- |
| **OAuth Handler**     | MCP Server                                | Gemini Enterprise                                        |
| **Redirect URI**      | `http://localhost:8080/oauth/callback`    | `https://vertexaisearch.cloud.google.com/oauth-redirect` |
| **Token Storage**     | File system (`~/.weather_mcp_token.json`) | Gemini Enterprise managed                                |
| **Token Delivery**    | Loaded from file                          | Passed via HTTP headers                                  |
| **OAuth Routes Used** | `/oauth/login`, `/oauth/callback`         | Not used (Gemini Enterprise handles)                     |

---

## Sequence Diagrams

### Production OAuth & Tool Call Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as Gemini Enterprise UI
    participant AS as Gemini Enterprise Engine
    participant OAuth as Google OAuth 2.0
    participant RE as Agent Engine<br/>(ADK Agent)
    participant MCP as MCP Server<br/>(Cloud Run)
    participant NWS as Weather API

    User->>UI: Ask "What's the weather in SF?"
    UI->>AS: Route query to agent

    rect rgb(255, 240, 240)
        Note over AS,OAuth: OAuth Flow (First Time Only)
        AS->>AS: Check if user has token
        AS->>OAuth: Redirect to authorization URL<br/>redirect_uri=vertexaisearch.cloud.google.com
        OAuth->>User: Show consent screen
        User->>OAuth: Approve permissions
        OAuth->>AS: Redirect with auth code
        AS->>OAuth: Exchange code for tokens
        OAuth->>AS: Return access_token, id_token, refresh_token
        AS->>AS: Store tokens
    end

    rect rgb(240, 255, 240)
        Note over AS,NWS: Agent Invocation & Tool Call
        AS->>RE: Invoke agent with query
        RE->>RE: LLM decides to call get_forecast_by_city
        RE->>MCP: POST /mcp<br/>Authorization: Bearer {token}<br/>Tool: get_forecast_by_city<br/>Args: {city: "San Francisco", state: "CA"}
        MCP->>MCP: Validate OAuth token
        MCP->>NWS: GET /points/{lat},{lon}
        NWS->>MCP: Return gridpoint data
        MCP->>NWS: GET /gridpoints/{office}/{x},{y}/forecast
        NWS->>MCP: Return forecast data
        MCP->>RE: Return formatted forecast
        RE->>RE: LLM formats response
        RE->>AS: Return answer
        AS->>UI: Display result
        UI->>User: "The weather in San Francisco..."
    end
```

### Development Local Testing Flow

```mermaid
sequenceDiagram
    actor Dev as Developer
    participant Browser
    participant MCP as MCP Server<br/>localhost:8080
    participant OAuth as Google OAuth
    participant Agent as ADK Agent<br/>localhost
    participant NWS as Weather API

    Dev->>MCP: python weather_server.py
    activate MCP

    rect rgb(255, 240, 240)
        Note over Dev,OAuth: Initial OAuth Setup
        Dev->>Browser: Visit http://localhost:8080/oauth/login
        Browser->>MCP: GET /oauth/login
        MCP->>Browser: Return HTML with auth link
        Browser->>OAuth: Redirect to Google OAuth<br/>redirect_uri=localhost:8080/oauth/callback
        OAuth->>Dev: Show consent screen
        Dev->>OAuth: Approve
        OAuth->>MCP: GET /oauth/callback?code=xyz&state=abc
        MCP->>OAuth: POST /token (exchange code)
        OAuth->>MCP: Return tokens
        MCP->>MCP: Save to ~/.weather_mcp_token.json
        MCP->>Browser: Show success page
    end

    rect rgb(240, 240, 255)
        Note over Dev,NWS: Agent Testing
        Dev->>Agent: python -m google.adk run agent.py
        activate Agent
        Agent->>Agent: Load MCP toolset with auth
        Dev->>Agent: Chat: "Weather in NYC?"
        Agent->>Agent: LLM plans to use get_forecast_by_city
        Agent->>MCP: Call tool with stored token
        MCP->>MCP: Load token from file
        MCP->>NWS: Fetch weather data
        NWS->>MCP: Return data
        MCP->>Agent: Tool response
        Agent->>Agent: LLM generates answer
        Agent->>Dev: "The weather in NYC is..."
        deactivate Agent
    end

    deactivate MCP
```

### Gemini Enterprise Registration Flow

```mermaid
sequenceDiagram
    actor Dev as Developer
    participant Notebook as Registration Notebook
    participant GCP as Google Cloud APIs
    participant AS as Gemini Enterprise

    Dev->>Notebook: Configure .env<br/>(PROJECT_ID, AUTH_ID, REASONING_ENGINE)

    rect rgb(255, 250, 240)
        Note over Dev,GCP: Step 1: Generate OAuth Config
        Dev->>Notebook: Run Cell 15: Generate OAuth URL
        Notebook->>Notebook: Create authorization URL<br/>redirect_uri=vertexaisearch.cloud.google.com
        Notebook->>Dev: Display OAuth authorization URL
    end

    rect rgb(240, 255, 240)
        Note over Dev,AS: Step 2: Register Authorization
        Dev->>Notebook: Run Cell 24: Register Authorization
        Notebook->>GCP: POST /authorizations<br/>authorizationId={AUTH_ID}
        Notebook->>GCP: Body: {client_id, client_secret,<br/>authorization_uri, token_uri}
        GCP->>AS: Create authorization config
        AS->>Notebook: Return authorization resource
        Notebook->>Dev: ✓ Authorization registered
    end

    rect rgb(240, 240, 255)
        Note over Dev,AS: Step 3: Link Agent to Gemini Enterprise
        Dev->>Notebook: Run Cell 26: Link Agent
        Notebook->>Notebook: Construct full agent engine name<br/>projects/{num}/locations/{loc}/reasoningEngines/{id}
        Notebook->>GCP: POST /engines/{AS_APP}/assistants/default_assistant/agents
        Notebook->>GCP: Body: {displayName, adk_agent_definition,<br/>provisioned_reasoning_engine, authorizations}
        GCP->>AS: Create agent with authorization link
        AS->>Notebook: Return agent resource
        Notebook->>Dev: ✓ Agent linked successfully
    end

    Dev->>AS: Visit Gemini Enterprise UI
    AS->>Dev: Agent appears in UI, ready to use
```

---

## Component Details

### ADK Agent (Agent Engine)

**File:** `src/adk_agent/agent.py`

The agent supports **dual-mode authentication** that automatically switches based on the `ENVIRONMENT` variable:

#### Development Mode (Local Testing)

```python
# Configuration for local development
environment = "development"

auth_scheme = OAuth2(
    flows=OAuthFlows(
        authorizationCode=OAuthFlowAuthorizationCode(
            authorizationUrl="https://accounts.google.com/o/oauth2/auth",
            tokenUrl="https://oauth2.googleapis.com/token",
            scopes={"openid": "Authenticate user identity", "email": "Access user's email address", "profile": "Access user's basic profile information"},
        )
    )
)

auth_credential = AuthCredential(
    auth_type=AuthCredentialTypes.OAUTH2,
    oauth2=OAuth2Auth(
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        redirect_uri="http://127.0.0.1:8000/dev-ui/",
    ),
)

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(url=mcp_url),
            auth_scheme=auth_scheme,
            auth_credential=auth_credential,
        )
    ],
)
```

**How it works:**

- Uses `auth_scheme` and `auth_credential` parameters
- Triggers browser-based OAuth flow on first MCP tool call
- ADK manages token storage and refresh automatically

#### Production Mode (Gemini Enterprise)

```python
# Configuration for Gemini Enterprise deployment
environment = "production"
auth_id = os.getenv("AUTH_ID")


def get_auth_header_provider(auth_id: str):
    """Retrieves OAuth token from Gemini Enterprise context."""

    def header_provider(readonly_context) -> dict[str, str]:
        try:
            credential_service = readonly_context.session.state.get("credential_service")
            if credential_service:
                token = credential_service.get_credential(auth_id)
                if token and hasattr(token, "access_token"):
                    return {"Authorization": f"Bearer {token.access_token}"}
        except Exception as e:
            print(f"Error retrieving token: {e}")
        return {}

    return header_provider


root_agent = LlmAgent(
    model="gemini-2.5-flash",
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(url=mcp_url),
            header_provider=get_auth_header_provider(auth_id),
        )
    ],
)
```

**How it works:**

- Uses `header_provider` function instead of auth_scheme/auth_credential
- Retrieves pre-authorized token from Gemini Enterprise context
- User completes OAuth in Gemini Enterprise UI (one-time setup)
- Token is injected into MCP requests via Authorization header

**Responsibilities:**

- Define LLM agent with instructions
- Configure MCP toolset with appropriate authentication method
- Connect to remote MCP server
- Process user queries and invoke tools

### Weather MCP Server

**File:** `src/mcp_servers/weather_mcp_server/weather_server.py`

```python
# OAuth Configuration
oauth_config = OAuthConfig(
    client_id=oauth_settings.google_client_id,
    client_secret=oauth_settings.google_client_secret,
    redirect_uri=oauth_settings.oauth_redirect_uri_local,
    redirect_uri_prod=oauth_settings.oauth_redirect_uri_prod,
    use_prod_redirect=oauth_settings.use_production_redirect,
)

# MCP Server with Tools
mcp = FastMCP(
    name="weather MCP server",
    instructions="A weather server protected by Google OAuth.",
)


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for coordinates"""


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state"""


@mcp.tool()
async def get_forecast_by_city(city: str, state: str) -> str:
    """Get weather forecast by city and state"""
```

**Responsibilities:**

- Provide MCP protocol endpoints
- Handle OAuth routes (development mode)
- Implement weather tool functions
- Validate OAuth tokens
- Call external weather APIs

### OAuth Helper

**File:** `src/mcp_servers/weather_mcp_server/oauth_helper.py`

**Responsibilities:**

- Generate OAuth authorization URLs
- Exchange authorization codes for tokens
- Store and load tokens securely
- Refresh expired tokens
- Handle CSRF protection with state parameter

---

## Data Flow

### Tool Invocation Data Flow

```mermaid
graph LR
    subgraph "Request"
        Q[User Query] --> LLM[LLM Decision]
        LLM --> TC[Tool Call Request]
        TC --> P[Parameters]
    end

    subgraph "Authentication"
        T[OAuth Token] --> H[HTTP Headers]
        H --> V[Token Validation]
    end

    subgraph "Execution"
        V --> E[Execute Tool]
        E --> API[External API]
        API --> D[Data Response]
    end

    subgraph "Response"
        D --> F[Format Response]
        F --> LLM2[LLM Formatting]
        LLM2 --> A[User Answer]
    end

    style Q fill:#e1f5ff
    style LLM fill:#f0e1ff
    style T fill:#ffe1e1
    style E fill:#e1ffe1
    style A fill:#e1f5ff
```

### Token Lifecycle

```mermaid
stateDiagram-v2
    [*] --> NoToken: User First Visit
    NoToken --> AuthFlow: Trigger OAuth
    AuthFlow --> ValidToken: Auth Success
    ValidToken --> ValidToken: Token Valid
    ValidToken --> Expired: Time Passes
    Expired --> RefreshFlow: Auto Refresh
    RefreshFlow --> ValidToken: Refresh Success
    RefreshFlow --> AuthFlow: Refresh Failed
    ValidToken --> Revoked: User Revokes
    Revoked --> AuthFlow: Re-authenticate
    AuthFlow --> [*]: Auth Failed

    note right of AuthFlow
        Development: MCP Server handles
        Production: Gemini Enterprise handles
    end note

    note right of RefreshFlow
        Uses refresh_token
        Automatic in both modes
    end note
```

---

## Security Architecture

### Security Layers

```mermaid
graph TB
    subgraph "Application Security"
        A1[OAuth 2.0 Authentication]
        A2[HTTPS/TLS Encryption]
        A3[Token Validation]
        A4[CSRF Protection State Parameter]
    end

    subgraph "Cloud Security"
        C1[Cloud Run IAM]
        C2[Service Accounts]
        C3[VPC Controls]
        C4[Cloud Armor optional]
    end

    subgraph "Data Security"
        D1[Token Encryption at Rest]
        D2[Secure Token Storage]
        D3[Token Expiration]
        D4[Minimal Scopes]
    end

    subgraph "Gemini Enterprise Security"
        S1[Managed OAuth Flow]
        S2[Session Management]
        S3[User Isolation]
        S4[Audit Logging]
    end

    A1 --> C1
    A3 --> D1
    C2 --> S1

    style A1 fill:#ffe1e1
    style C1 fill:#fff4e1
    style D1 fill:#e1ffe1
    style S1 fill:#e1f5ff
```

### OAuth Scopes & Permissions

| Scope                                                     | Purpose                    | Required For          |
| --------------------------------------------------------- | -------------------------- | --------------------- |
| `openid`                                                  | User identity              | Authentication        |
| `email`                                                   | User email address         | User identification   |
| `profile`                                                 | User profile info          | Display name, avatar  |
| `https://www.googleapis.com/auth/drive.metadata.readonly` | Drive metadata (optional)  | If accessing Drive    |
| `https://www.googleapis.com/auth/calendar.readonly`       | Calendar read (optional)   | If accessing Calendar |
| `https://www.googleapis.com/auth/bigquery`                | BigQuery access (optional) | If accessing BigQuery |

---

## Deployment Architecture

### Development Environment

```
┌─────────────────────────────────────┐
│     Developer Machine               │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Terminal 1                  │  │
│  │  python weather_server.py    │  │
│  │  → localhost:8080            │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Terminal 2                  │  │
│  │  python -m google.adk run... │  │
│  │  → localhost:8000            │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Browser                     │  │
│  │  → localhost:8000/dev-ui/    │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

### Production Environment

```
┌──────────────────────────────────────────────────────────┐
│                    Google Cloud                          │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │              Vertex AI Gemini Enterprise                  │ │
│  │                                                    │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │  Gemini Enterprise UI (Web Interface)              │ │ │
│  │  │  → vertexaisearch.cloud.google.com          │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  │                                                    │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │  Agent Engine (ADK Agent Deployed)      │ │ │
│  │  │  → Vertex AI Agent Engines API          │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  │                                                    │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │  Authorization Store                        │ │ │
│  │  │  → OAuth Client Credentials                 │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │              Cloud Run Service                     │ │
│  │                                                    │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │  Weather MCP Server Container              │ │ │
│  │  │  → weather-mcp-server-oauth.run.app        │ │ │
│  │  │  → /mcp endpoint (SSE or HTTP)             │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Network Flow

### Production Network Diagram

```mermaid
graph TB
    USER[End User Browser]

    subgraph "Google Cloud Platform"
        subgraph "Vertex AI"
            AS[Gemini Enterprise<br/>vertexaisearch.cloud.google.com]
            RE[Agent Engine<br/>us-central1]
        end

        subgraph "Cloud Run"
            MCP[Weather MCP Server<br/>weather-mcp-server-oauth.run.app]
        end
    end

    subgraph "External Services"
        OAUTH[accounts.google.com<br/>OAuth 2.0]
        NWS[api.weather.gov<br/>Weather Service]
    end

    USER -->|HTTPS| AS
    AS -->|HTTPS| OAUTH
    OAUTH -->|Redirect| AS
    AS -->|Private/Internal| RE
    RE -->|HTTPS + Auth| MCP
    MCP -->|HTTPS| NWS

    style USER fill:#e1f5ff
    style AS fill:#fff4e1
    style RE fill:#f0e1ff
    style MCP fill:#e1ffe1
    style OAUTH fill:#ffe1e1
    style NWS fill:#f5f5f5
```

---

## Troubleshooting Guide

### Common Issues Flow

```mermaid
graph TD
    START[Issue Detected] --> TYPE{Issue Type?}

    TYPE -->|OAuth Error| OAUTH_CHECK{Error Message?}
    OAUTH_CHECK -->|redirect_uri_mismatch| FIX1[Check redirect URI<br/>in Google Console]
    OAUTH_CHECK -->|invalid_client| FIX2[Verify client ID<br/>and secret]
    OAUTH_CHECK -->|State mismatch| FIX3[Clear state files<br/>and retry]

    TYPE -->|Agent Error| AGENT_CHECK{Error Type?}
    AGENT_CHECK -->|Invalid agent engine| FIX4[Check full resource name<br/>format in notebook]
    AGENT_CHECK -->|Authorization not found| FIX5[Re-run notebook<br/>cell 24 registration]
    AGENT_CHECK -->|MCP connection failed| FIX6[Check MCP_URL<br/>and server status]

    TYPE -->|MCP Error| MCP_CHECK{Error Type?}
    MCP_CHECK -->|Token validation failed| FIX7[Check token validity<br/>and scopes]
    MCP_CHECK -->|Tool execution failed| FIX8[Check external API<br/>connectivity]
    MCP_CHECK -->|Server not responding| FIX9[Check Cloud Run<br/>deployment and logs]

    FIX1 --> VERIFY[Verify Fix]
    FIX2 --> VERIFY
    FIX3 --> VERIFY
    FIX4 --> VERIFY
    FIX5 --> VERIFY
    FIX6 --> VERIFY
    FIX7 --> VERIFY
    FIX8 --> VERIFY
    FIX9 --> VERIFY

    VERIFY --> SUCCESS{Fixed?}
    SUCCESS -->|Yes| END[✓ Resolved]
    SUCCESS -->|No| DOCS[Check documentation<br/>or logs]

    style START fill:#ffe1e1
    style END fill:#e1ffe1
    style VERIFY fill:#fff4e1
```

---

## References

- [ADK Documentation](https://github.com/google/adk)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [Vertex AI Agent Builder](https://cloud.google.com/generative-ai-app-builder/docs/agent-intro)
- [National Weather Service API](https://www.weather.gov/documentation/services-web-api)

---

## License

Copyright 2025 Google LLC - Licensed under Apache 2.0
