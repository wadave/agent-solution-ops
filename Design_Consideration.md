# Design Considerations & Architecture

This document outlines the architectural decisions and design considerations for the ADK Weather Agent with OAuth Authentication.

## The Challenge

The core challenge in building authenticated agents on Google Cloud's Agent Engine is that **Agent Engine is a headless backend service**. It does not have a native graphical user interface (UI) to display to the end-user. 

Because OAuth 2.0 requires active user participation (e.g., clicking "Allow" on a consent screen and logging in via a browser), an agent running purely in the backend cannot complete an interactive OAuth flow on its own. It needs a frontend to handle browser redirects and user interaction.

## The Solution: Frontend Proxying via Gemini Enterprise

To solve this, we leverage **Gemini Enterprise (GE)** as our user-facing frontend. Gemini Enterprise provides the chat interface that users interact with, and it has native capabilities to handle OAuth authorizations securely.

Here is how the architecture and authentication flow works:

1.  **User Interaction in GE UI**: The user interacts with the Gemini Enterprise UI.
2.  **OAuth Flow Initiation**: When the user's query requires accessing a protected resource (like our Weather MCP Server), Gemini Enterprise recognizes the need for authentication based on its configuration. It prompts the user in the UI to authenticate via Google OAuth 2.0.
3.  **Token Acquisition**: The user completes the browser-based OAuth flow, and Gemini Enterprise securely receives and stores the resulting OAuth access token.
4.  **Agent Invocation with Context**: Gemini Enterprise resumes the conversational flow. When it invokes our backend Agent Engine (ADK Agent), it securely passes the user's active OAuth token within the invocation session state and context.
5.  **MCP Tool Access**: 
    - The ADK Agent is configured with a custom `mcp_header_provider`. 
    - Before calling the external MCP Server, the agent extracts the user's OAuth token from the session context (passed down by GE).
    - It injects this token into the `Authorization: Bearer <token>` header of the outgoing request to the MCP Server.
    - Notably, the ADK Agent suppresses its own default credentials manager checks because it knows the token is already provided dynamically by the frontend.
6.  **Secure Execution**: The Cloud Run-hosted MCP Server validates the Bearer token and serves the requested data (e.g., weather forecasts) back to the agent.

## Why This Architecture Matters

- **Security**: The Agent Engine itself never has to store or manage long-lived secrets or refresh tokens for the end-user. It temporarily handles short-lived bearer tokens passed securely in memory per request.
- **User Experience**: The user experiences a seamless login flow directly within the chat interface they are already using (Gemini Enterprise), rather than being pushed to a separate management portal.
- **Standardization**: By relying on Gemini Enterprise and Model Context Protocol (MCP), we decouple the agent logic from the authentication mechanism, standardizing how external tools are integrated and secured. 
- **Dual-Mode Capability**: Our specific implementation allows the agent to dynamically switch behaviors. When running locally (where GE isn't present), the agent instantiates its own lightweight web UI to handle the OAuth flow directly. When deployed, it defers completely to Gemini Enterprise, ensuring flexibility across the entire development lifecycle.
