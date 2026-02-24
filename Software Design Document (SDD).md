# Software Design Document (SDD): ADK Weather Agent

## 1. Introduction

- **Purpose**: To define the software architecture and design of the ADK Weather Agent system, outlining the components, data flow, and deployment strategy for an authenticated, enterprise-grade AI agent.
- **Scope**: Covers the backend Agent Engine application, the Model Context Protocol (MCP) server running on Cloud Run, and the integration with Gemini Enterprise which acts as the frontend and handles user OAuth authentication.

---

## 2. System Overview

- **System Description**: The ADK Weather Agent is a conversational AI assistant capable of retrieving and reporting weather information. It uses the Google Agent Development Kit (ADK) and is deployed on Vertex AI Agent Engine. Because Agent Engine is a headless service, Gemini Enterprise is used to provide the chat UI and manage the OAuth 2.0 flow.
- **Design Goals**:
  - **Security-First**: Ensure tokens are securely passed and managed without the backend needing to capture raw user credentials.
  - **Scalability**: Leverage fully managed, serverless GCP services.
  - **Maintainability**: Clear separation of concerns between the language model orchestration (Agent Engine) and tool execution (MCP server).
- **Architecture Summary**: Serverless microservices architecture utilizing Vertex AI Agent Engine for LLM reasoning and Cloud Run for fulfilling MCP tool-call requests.
- **System Context Diagram**:
  ```mermaid
  flowchart LR
      User((User)) <--> GE[Gemini Enterprise]
      GE <--> AE[Vertex AI Agent Engine]
      AE <--> MCP[Cloud Run MCP Server]
      MCP <--> WeatherAPI[External Weather API]
  ```

---

## 3. Architectural Design

- **System Architecture Diagram**:
  ```mermaid
  flowchart TD
      subgraph Frontend
          UI[Gemini Enterprise UI]
          OAuth[OAuth 2.0 Identity Provider]
      end

      subgraph Google Cloud Platform
          AE[Vertex AI Agent Engine]
          CR[Cloud Run MCP Server]
          SM[Secret Manager]
      end

      UI -- "Authenticates via" --> OAuth
      OAuth -- "Returns Token" --> UI
      UI -- "Chat Request + Bearer Token" --> AE
      AE -- "Executes Tools via MCP" --> CR
      CR -- "Reads Client Secrets" --> SM
  ```
- **Component Breakdown**:
  - **Gemini Enterprise**: Acts as the user-facing frontend. Handles user authentication (OAuth 2.0 approval) and passes the authenticated context down to the Agent Engine.
  - **Vertex AI Agent Engine**: The core reasoning engine built with the ADK. It receives user prompts, decides which tools to call, and delegates tool execution to the MCP server.
  - **Cloud Run MCP Server**: Hosts the Model Context Protocol (MCP) tools (e.g., getting weather forecasts). It receives requests from the Agent Engine and executes the corresponding Python utility functions.
- **Technology Stack**:
  - **Language**: Python 3.12
  - **Frameworks**: Google Agent Development Kit (ADK), Model Context Protocol (MCP)
  - **Infrastructure**: Vertex AI Agent Engine, Cloud Run, Secret Manager, Cloud Build
  - **IaC**: Terraform
- **Data Flow and Control Flow**:

  ```mermaid
  sequenceDiagram
      actor User
      participant GE as Gemini Enterprise
      participant AE as Agent Engine
      participant MCP as Cloud Run MCP

      User->>GE: "What is the weather?" (Requires Login)
      GE->>User: Prompts for OAuth Consent
      User->>GE: Grants Consent
      GE->>AE: Invokes Agent with Bearer Token
      AE->>AE: Reasons about prompt
      AE->>MCP: Tool Request (GetWeather)
      MCP->>AE: Tool Response (72°F and Sunny)
      AE->>GE: Formats Final Response
      GE->>User: Displays "It's 72°F and Sunny"
  ```

---

## 4. Detailed Design

### Vertex AI Agent Engine Component

- **Responsibilities**: Orchestrates the conversation, maintains memory/state during the session, and determines when to trigger external tools.
- **Interfaces/APIs**:
  - Inputs: Natural language prompts and user context (with OAuth Bearer token headers).
  - Outputs: Natural language responses.
- **State Management**: Conversational state is managed either implicitly by Gemini Enterprise or within the Agent Engine sessions.

### Cloud Run MCP Server Component

- **Responsibilities**: Executes concrete business logic (tools) securely. Isolates tool execution from the reasoning engine for security and scalability.
- **Interfaces/APIs**:
  - Inputs: MCP protocol requests over HTTP POST.
  - Outputs: JSON-formatted tool execution results.
  - Error Handling: Returns standard HTTP status codes and JSON error messages if tools fail or timeout.

---

## 5. External Interfaces

- **User Interface**: Gemini Enterprise provides the web-based chat interface. No custom frontend code is maintained in this repository.
- **External APIs**:
  - The MCP Server may reach out to public weather REST APIs.
- **Network Protocols/Communication**:
  - REST/HTTPS for all service-to-service communication.
  - Internal communication authenticated via Identity-Aware Proxy (IAP) or native GCP IAM.

---

## 6. Security Considerations

- **Authentication**: Dual-mode authentication:
  - **Production**: Gemini Enterprise handles the user-facing OAuth 2.0 flow. The token is securely passed to the backend headers.
  - **Development**: Local JSON file credentials (`client_secret.json`) are used.
- **Authorization**:
  - The Agent Engine service account is granted precise IAM permissions (e.g., `roles/run.invoker` for the Cloud Run MCP server).
- **Data Protection**:
  - Secrets (OAuth client IDs and configurations) are stored centrally in Google Cloud Secret Manager.
- **Threat Model**:
  - Ensure the MCP server strictly validates input to prevent Prompt Injection leading to RCE (Remote Code Execution) via the tool interface.

---

## 7. Performance and Scalability

- **Expected Load**: Handles enterprise-scale chat requests.
- **Scaling Strategy**:
  - Vertex AI Agent Engine scales automatically based on incoming query volume.
  - Cloud Run scales container instances horizontally from 0 up to a configured maximum limit, easily handling varied concurrency.

---

## 8. Deployment Architecture

- **Environments**: Support for `dev`, `staging`, and `prod` isolation through distinct Google Cloud Projects.
- **CI/CD Pipeline**:
  - Managed by Google Cloud Build.
  - Stages: Linting (`ruff`), Unit Testing (`pytest`), Terraform Plan, Terraform Apply, Python Script Deployment (`deploy_agents.py`).
- **Cloud/Hosting**: Google Cloud Platform (GCP).
- **Containerization**: The MCP server is containerized and deployed to Cloud Run. The Agent Engine packages standard Python code.

---

## 9. Testing Strategy

- **Unit Testing**: Python unit tests written via `pytest` to validate individual ADK tools and logic.
- **Integration Testing**: Testing the complete chain from Agent Engine to the MCP server.
- **Load Testing**: `locust` scripts simulate concurrent users to validate rate limits and response latency.

---

## 10. Appendices

- **Glossary**:
  - **ADK**: Agent Development Kit.
  - **GE**: Gemini Enterprise.
  - **MCP**: Model Context Protocol, an open standard for connecting AI models to data sources and tools.
  - **Agent Engine**: A managed Vertex AI service for hosting generative AI agents.
- **Change History**:
  - v1.0, 2026-02-24, Assistant, Initial Design Document mapped to existing ADK Weather Agent architecture.
