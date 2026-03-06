# Software Design Document: Remote MCP Server Integration with Gemini Enterprise

## 1. Introduction

- **Purpose**: This document defines the design and architecture of the Gemini Enterprise Weather Agent system, documenting how it leverages ADK, FastMCP, and Google Cloud services to provide a secured, authenticated weather forecasting experience.
- **Scope**: Includes the ADK Agent (reasoning engine), the Weather MCP Server (data provider), and the infrastructure/deployment automation (Terraform and Cloud Build). It covers the dual-mode OAuth authentication flow.
- **Definitions and Acronyms**:
  - **ADK**: Agent Development Kit (Google SDK for building agents).
  - **MCP**: Model Context Protocol.
  - **GE**: Gemini Enterprise.
  - **NWS**: National Weather Service.
- **References**:
  - [Project README](file:///usr/local/google/home/wangdave/remote_ws/projects/agent-solution-ops/README.md)
  - [Weather MCP Server Source](file:///usr/local/google/home/wangdave/remote_ws/projects/agent-solution-ops/src/mcp_servers/weather_mcp_server/weather_server.py)
  - [ADK Agent Source](file:///usr/local/google/home/wangdave/remote_ws/projects/agent-solution-ops/src/adk_agent/agent.py)

---

## 2. System Overview

- **System Description**: A cloud-native generative AI system that interprets natural language weather queries. It uses a reasoning agent to invoke a secured MCP server that fetches data from the NWS API.
- **Design Goals**:
  - **Security**: Strict OAuth 2.0 authentication for all tool calls.
  - **Portability**: Dual-mode authentication for seamless local development and production deployment.
  - **Observability**: Native integration with Google Cloud Logging and Monitoring.
- **Architecture Summary**: Decoupled architecture with a reasoning layer (ADK Agent on Vertex AI) and a capability layer (MCP Server on Cloud Run).
- **System Context Diagram**:
  ```mermaid
  graph LR
      User((User)) --> GE[Gemini Enterprise UI]
      GE --> Agent[ADK Weather Agent]
      Agent --> MCP[Weather MCP Server]
      MCP --> NWS[National Weather Service API]
      GE -.->|OAuth Flow| OAuth[Google OAuth 2.0]
      GE -.->|Filtered by| MA[Model Armor]
      Agent -.->|Filtered by| MA
  ```

---

## 3. Architectural Design

- **System Architecture Diagram**:

  ```mermaid
  graph TB
      subgraph "Google Cloud"
          direction TB
          subgraph "User Interface"
              GE_Engine[Gemini Enterprise Engine]
          end
          subgraph "Security"
              MA[Model Armor Floor Settings]
          end
          subgraph "Gemini Enterprise"
              VS[VertexAISession Services]
              Agent_Engine["Agent Engine / ADK Agent (Retry)"]
          end
          subgraph "Cloud Run"
              Cloud_Run[Weather MCP Server]
          end
          IAM[IAM & Secret Manager]
      end

      subgraph "External"
          NWS[Weather API]
          Google_Auth[Google OAuth Provider]
      end

      GE_Engine -->|Manage Session| VS
      VS -->|Invoke| Agent_Engine
      Agent_Engine -->|Authenticated Tool Call| Cloud_Run
      Cloud_Run -->|API Request| NWS

      GE_Engine -.->|Filtered by| MA
      Agent_Engine -.->|Filtered by| MA

      GE_Engine <-->|Token Exchange| Google_Auth
      GE_Engine -.->|Pass Token| Cloud_Run
      Cloud_Run -->|Verify Token| Google_Auth
  ```

- **Component Breakdown**:
  - **VertexAISession Services**: Manages session state, conversation history, and user context across multi-turn interactions.
  - **ADK Agent**: Orchestrates tool calls, handles session context, and implements environment-aware authentication logic. Features **Gemini model retry logic** to handle API quotas, rate limiting, and transient network errors gracefully.
  - **Weather MCP Server**: FastMCP-based service providing specific tools (`get_forecast`, `get_alerts`) with built-in OAuth verification middleware.
  - **Deployment Layer**: Terraform (Infrastructure Shells) + Cloud Build (CI/CD) + `deploy_agents.py` & `gcloud CLI` (Code Deployment).
- **Technology Stack**:
  - **Language**: Python 3.12+
  - **Frameworks**: ADK, FastMCP, FastAPI (via FastMCP), Pydantic.
  - **Model**: `gemini-2.5-flash` with `HttpRetryOptions(attempts=3)` for built-in transient error handling.
  - **Infrastructure**: Terraform, Google Cloud Run, Vertex AI Agent Engine, Google Artifact Registry, **Google Model Armor**.
- **Data Flow and Control Flow**:
  - User sends a query to Gemini Enterprise.
  - GE invokes the Vertex AI Agent.
  - In **Production**: Agent extracts OAuth token from `session.state` and adds it to the `Authorization` header.
  - In **Development**: Agent triggers a browser-based OAuth flow if no token is present.
  - MCP Server receives the request, verifies the token via Google's `tokeninfo` endpoint, and executes the weather tool logic.

---

## 4. Detailed Design

### VertexAISession Services

- **Responsibilities**: Manages persistent conversation history and user session state natively on Google Cloud.
- **Interfaces/APIs**: Provides state retrieval and storage for the ADK Agent across interactions.

### ADK Agent (`adk_agent`)

- **Responsibilities**: Reasoning, intent interpretation, secure tool invocation, and error handling.
- **Capabilities**: Features **Gemini model retry logic** using exponential backoff or similar policies to handle transient Google Cloud API failures or rate limits (429/503 errors).
- **Interfaces/APIs**:
  - **Input**: Natural language query + Session context from GE (via VertexAISession).
  - **Output**: Natural language response + Optional tool call results.
- **Authentication Logic**:
  - Implements `mcp_header_provider` to dynamically inject tokens.
  - Uses `header_provider` in production to bypass ADK's `CredentialManager` and read tokens directly from context state.
- **State Management**: Uses `ReadonlyContext` to access session data provided by Gemini Enterprise.

### Agent Engine App (`agent_engine_app`)

- **Responsibilities**: Production hosting wrapper that extends `AdkApp` for deployment on Vertex AI Agent Engine.
- **Key Class**: `AgentEngineApp(AdkApp)` — adds startup initialization, telemetry, and custom operations.
- **Initialization (`set_up`)**: Calls `vertexai.init()`, invokes `setup_telemetry()` to configure OpenTelemetry tracing, and initializes Google Cloud Logging.
- **Feedback Collection**: Exposes a `register_feedback` operation that validates incoming feedback via a Pydantic model (`Feedback`) and logs it as a structured entry to Google Cloud Logging.
- **Artifact Storage**: Conditionally uses `GcsArtifactService` (when `LOGS_BUCKET_NAME` is set) or falls back to `InMemoryArtifactService`.
- **Session Service**: Uses `VertexAiSessionService` for persistent session management.

### Telemetry (`app_utils/telemetry`)

- **Responsibilities**: Configures OpenTelemetry (OTEL) instrumentation for distributed tracing and GenAI content capture.
- **Environment Variables**:
  - `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY`: Enables native Agent Engine telemetry export.
  - `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`: Captures full GenAI message content in traces.

### Weather MCP Server (`weather_mcp_server`)

- **Responsibilities**: Tool execution and data fetching from NWS.
- **Interfaces/APIs**:
  - `get_alerts(state)`: Fetches active alerts for a US state.
  - `get_forecast(latitude, longitude)`: Fetches forecast by coordinates.
  - `get_forecast_by_city(city, state)`: Fetches forecast by city name using geocoding (Nominatim).
- **Security Middleware**: `OAuthMiddleware` intercepts `/mcp` calls to ensure a valid Bearer token is present and verified against Google's Auth provider.

---

## 5. Database Design

- **Tables/Collections**: This system is largely stateless.
- **Persistence**: OAuth tokens are stored in the ADK session state (managed by Gemini Enterprise) or local file cache in development.

---

## 6. External Interfaces

- **User Interface**: Gemini Enterprise side-panel / Chat interface.
- **External APIs**: National Weather Service (api.weather.gov).
- **Network Protocols**: REST over HTTPS, Model Context Protocol (MCP) over Streamable-HTTP/SSE.

---

## 7. Security Considerations

- **Authentication**: OIDC (OpenID Connect) via Google OAuth 2.0.
- **Security Filtering**: **Model Armor Floor Settings** automatically inspect and block adversarial prompts and harmful model responses across the project.
- **Authorization**: Token verification by the MCP server; Cloud Run service restricted via IAM (`roles/run.invoker`).
- **Data Protection**: Zero-trust approach; tokens are passed in headers and never logged in plain text.
- **Secret Management**: API keys and OAuth client secrets are managed via Google Secret Manager.

---

## 8. Performance and Scalability

- **Expected Load**: Designed for low-latency interactive chat (< 2s for reasoning + tool call).
- **Caching Strategy**: NWS API responses are processed in real-time; no cross-session caching implemented.
- **Scaling Strategy**: Cloud Run and Vertex AI Agent Engine scale horizontally and automatically based on request volume.

---

## 9. Deployment Architecture

- **Environments**: Support for `development` (local) and `production` (Google Cloud).
- **CI/CD Pipeline**: Cloud Build automates image builds, Terraform applies infrastructure shells, and SDKs/CLIs deploy the application code.
- **Infrastructure Diagram**:
  ```mermaid
  graph TD
      CB[Cloud Build] -->|Builds| AR[Artifact Registry]
      CB -->|Applies| TF[Terraform]
      TF -->|Provisions Shell| CR[Cloud Run]
      TF -->|Provisions Shell| AE[Agent Engine]
      TF -->|Creates| IAM[Service Accounts]
      TF -->|Configures| MA[Model Armor Floor Settings]
      CB -->|gcloud run deploy| CR
      CB -->|deploy_agents.py| AE
  ```

---

## 10. Testing Strategy

- **Unit Testing**: `pytest` under `tests/unit/` for discrete code component verification, and `src/mcp_servers/.../direct_test.py` for headless tool execution testing.
- **Integration Testing**: `pytest` under `tests/integration/` for testing the deployed agent Engine against real resources.
- **Load Testing**: Locust-based testing framework under `tests/load_test/` to simulate concurrent users.
- **Evaluation**: ADK evaluation framework under `tests/eval/` for checking agent behavioral accuracy.
- **Quality Metrics**: Code linting via `ruff`, security scanning via `gitleaks`/`secrets-baseline`.

---

## 11. Appendices

- **Glossary**:
  - **FastMCP**: A high-level framework for building MCP servers in Python.
  - **Agent Engine**: Vertex AI's managed runtime for hosting AI agents.
- **Change History**:
  - **v1.0.0 (2026-02-25)**: Initial design document creation.
  - **v1.1.0 (2026-02-25)**: Added trade-off analysis section.
  - **v1.2.0 (2026-02-27)**: Integrated Model Armor security architecture and comparison guide.
  - **v1.3.0 (2026-03-04)**: Added `get_forecast_by_city` tool; added model specification (`gemini-2.5-flash`); corrected MCP tools list.
  - **v1.4.0 (2026-03-06)**: Documented `AgentEngineApp` (feedback registration), telemetry setup, and OTEL environment variables.

---

## 12. Design Trade-offs

### 12.1 Agent Deployment: Agent Engine vs. Cloud Run

| Feature               | Vertex AI Agent Engine                                                                                                                                                                                                                          | Google Cloud Run                          |
| :-------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------- |
| **Primary Use Case**  | Reasoning Agent (ADK Agent)                                                                                                                                                                                                                     | Capability Layer (MCP Servers)            |
| **Agent Integration** | Native support for ADK primitives                                                                                                                                                                                                               | Requires manual state/auth management     |
| **Abstraction Level** | Higher (managed agent lifecycle)                                                                                                                                                                                                                | Lower (standard container orchestration)  |
| **Flexibility**       | Optimized for LLM workflows                                                                                                                                                                                                                     | Highly flexible for any containerized app |
| **Decision**          | **Agent Engine** is used for the reasoning agent to leverage its native integration with Gemini Enterprise and ADK, while **Cloud Run** hosts the Weather MCP Server for its superior scalability and support for standard serverless patterns. |

### 12.2 Authentication: OAuth 2.0 vs. Service Account

| Feature            | OAuth 2.0 (User Identity)                                                                                                                                                                                   | Service Account (App Identity)        |
| :----------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------ |
| **Security Model** | Zero-Trust (User-specific scopes)                                                                                                                                                                           | System-Trust (Shared app permissions) |
| **User Context**   | Full access to user data/location                                                                                                                                                                           | No inherent user context              |
| **Complexity**     | Higher (Token exchange, redirects)                                                                                                                                                                          | Lower (Static secrets/IAM)            |
| **Auditability**   | Granular (User-level)                                                                                                                                                                                       | Generic (App-level)                   |
| **Decision**       | **OAuth 2.0** is prioritized to ensure the agent acts strictly on behalf of the user, maintaining high security standards and allowing for future personalization (e.g., location-specific weather alerts). |

### 12.3 Security Enforcement: Floor Settings vs. Per-request Templates

| Feature            | Project-wide Floor Settings                                                                                                  | Per-request Templates                         |
| :----------------- | :--------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------- |
| **Scope**          | Project-wide (Baseline)                                                                                                      | Per-request (Granular)                        |
| **Implementation** | Infrastructure-as-Code (Terraform)                                                                                           | Code-integrated (Vertex AI Client)            |
| **Maintenance**    | Centralized (managed via `model_armor.tf`)                                                                                   | Distributed (requires per-agent code updates) |
| **Decision**       | **Floor Settings** are implemented via Terraform to provide a "secure-by-default" project baseline without adding code debt. |

### 12.4 Domain-Applied AI/ML Expertise

This project demonstrates expertise in applying AI to a specific industry vertical (Meteorology) with enterprise-grade constraints.

| Domain Challenge         | AI/ML Solution Pattern                   | Project Implementation                                                                                                   |
| :----------------------- | :--------------------------------------- | :----------------------------------------------------------------------------------------------------------------------- |
| **Vertical Integration** | Domain-specific API orchestration        | Integration with the **National Weather Service (NWS)** API via FastMCP tools.                                           |
| **Data Constraints**     | Structured parsing for LLM ingestion     | The `weather_server.py` parses complex GeoJSON into human-readable summaries (`format_alert`, `format_forecast_period`). |
| **Security KPI**         | Red Teaming & Prompt Filtering           | **Google Model Armor** implementation for project-wide adversarial threat mitigation.                                    |
| **Identity KPI**         | Verified User Identity for vertical data | **OAuth 2.0 (OIDC)** middleware to ensure the agent only fetches data the user is authorized to see.                     |
| **Performance KPI**      | Interactive Latency Targets              | Architecture optimized for **< 2s response times** using Cloud Run and Vertex AI Agent Engine.                           |

---

## 13. Resilience and Disaster Recovery

### 13.1 Infrastructure Resilience (via Terraform)

Terraform is the primary tool for defining and enforcing the project's resilience. Key patterns include:

- **Multi-Region Failover**: In a production environment, Terraform can define regional replicas of the **Weather MCP Server** (Cloud Run) and **Vertex AI Agent Engine**. A **Global Cloud Load Balancer** with a single anycast IP can then provide automated failover between regions.
- **Environment Parity**: Terraform ensures that the `staging` and `production` environments are identical except for scale and data, enabling high-fidelity resilience testing in staging before production deployment.
- **Resource Recovery**: By using `prevent_destroy` flags and automated backup configurations (e.g., for Cloud Storage and Secret Manager), Terraform minimizes the risk of accidental data loss.
- **Gemini Model Retry Logic**: The ADK Agent is configured with robust retry policies to ensure high availability and gracefully degrade or recover from transient Vertex AI API errors or rate limiting.
- **Agent Naming Consistency**: The host agent maintains a strict naming convention `ADK Hosting Agent for MCP (<environment>)` syncing identity across Vertex AI Agent Engine and Gemini Enterprise.
- **Deployment State Recovery**: The Python deployment script handles dirty states (e.g., stale failed LROs on creation) by gracefully catching the error, extracting the resource ID, and falling back to an `update()` operation, ensuring pipelines recover from transient GCP API issues. It also auto-migrates agents from legacy APIs to modern SDK formats.

### 13.2 Failure Testing Strategies

While not yet implemented, the architecture supports the following future testing paradigms:

- **Automated Failure Injection**: Terraform can provision "faulty" infrastructure (e.g., specific network restrictions or reduced quota limits) to test how the agent handles degraded MCP services.
- **Red Teaming (Prompt Injection)**: Integrated via **Model Armor**, which provides a project-wide filter against adversarial attacks.
- **Disaster Recovery Validation**: Periodic "Infrastructure-as-Code" destruction and re-provisioning tests in a standalone project to verify the completeness of the Terraform modules.
