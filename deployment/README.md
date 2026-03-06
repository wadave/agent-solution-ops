# Deployment

This directory contains the Terraform configurations for provisioning the necessary Google Cloud infrastructure for your agent.

The recommended way to deploy the infrastructure and set up the CI/CD pipeline is by using the `agent-starter-pack setup-cicd` command from the root of your project:

```bash
uvx agent-starter-pack setup-cicd
```

## Manual Agent Engine Deployment (`deploy_agents.py`)

If you need to manually deploy or update the Agent Engine resource outside of the automated CI/CD pipeline, you can use the `deploy_agents.py` script.

### Environment Variables

The script expects the following environment variables. Required variables must be set before execution:

*   **`PROJECT_ID`**: (Required) GCP project ID for deployment.
*   **`APP_SERVICE_ACCOUNT`**: (Required) Service account email for the agent (pattern: `{project_name}-app@{project_id}.iam.gserviceaccount.com`).
*   **`AUTH_ID`**: (Required) Agentspace authorization ID for OAuth token retrieval (e.g., `staging-weather-oauth-token`).
*   `GOOGLE_CLOUD_REGION`: GCP region (default: `us-central1`).
*   `MCP_URL`: Full URL of the Cloud Run MCP server, including the `/mcp` path.
*   `GEMINI_MODEL`: Model ID to use (default: `gemini-2.5-flash`).
*   `RETRY_ATTEMPTS`: Number of retry attempts for the model (default: `3`).
*   `MCP_TIMEOUT`: Timeout in seconds for the MCP server (default: `60`).
*   `DISPLAY_NAME_SUFFIX`: Human-readable environment suffix, e.g. "Staging" or "Prod" (default: "Staging").
*   `LOGS_BUCKET_NAME`: GCS bucket for agent artifact/log storage (default: `{PROJECT_ID}-agents-solution-ops-logs`).
*   `REQUIREMENTS_FILE`: Path to requirements.txt generated from pyproject.toml (default: `/workspace/requirements.txt`).
*   `HOSTING_AGENT_ID_FILE`: File path to write the deployed resource name for CI/CD handoff (default: `/workspace/hosting_agent_id.txt`).

### Usage

```bash
export PROJECT_ID="your-project-id"
export APP_SERVICE_ACCOUNT="your-project-app@your-project-id.iam.gserviceaccount.com"
export AUTH_ID="staging-weather-oauth-token"
python deployment/deploy_agents.py
```

For detailed information on the deployment process, infrastructure, and CI/CD pipelines, please refer to the official documentation.
