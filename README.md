# ADK Weather Agent with OAuth Authentication

Complete guide for setting up an ADK agent with dual-mode OAuth authentication to access MCP (Model Context Protocol) weather services.

## High-Level Component Diagram

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

**Key Feature:** The agent automatically switches between development and production authentication modes based on the `ENVIRONMENT` variable:
- **Development**: OAuth2Auth with client credentials (browser-based OAuth flow)
- **Production**: Token retrieval from Gemini Enterprise context via `header_provider` — no `auth_scheme` is passed, ensuring the credential manager is bypassed entirely

**Use Cases:**
- Local testing with `adk web`
- Deployed agents on Vertex AI Agent Engine registered to Gemini Enterprise

---

## Quick Start

### Prerequisites
- Python 3.12+
- Google Cloud Project with OAuth credentials
- uv package manager: [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- Project dependencies: `uv sync`

### 1. Clone and Setup

```bash
cp .env.example .env
```

### 2. Configure Google OAuth

Go to: https://console.cloud.google.com/apis/credentials

Click your OAuth 2.0 Client ID and add the redirect URIs below.

**For Development:**
```
http://127.0.0.1:8000/dev-ui/
http://localhost:8000/dev-ui/
```

**For Production (Gemini Enterprise):**
```
https://vertexaisearch.cloud.google.com/oauth-redirect
```

### 3. Set Environment Variables

Edit `src/adk_agent/.env`:

```bash
# Environment — set to 'development' for local testing.
# Any value other than 'development' activates production mode.
ENVIRONMENT=development

# Google Cloud
GOOGLE_CLOUD_PROJECT="your-project-id"
GOOGLE_CLOUD_LOCATION="us-central1"

# MCP Server URL (Cloud Run service URL + /mcp)
MCP_URL='https://your-mcp-server.run.app/mcp'

# OAuth Credentials (required for development mode only)
GOOGLE_CLIENT_ID='your-client-id'
GOOGLE_CLIENT_SECRET='your-client-secret'

# OAuth Redirect URIs
OAUTH_REDIRECT_URI_DEV='http://127.0.0.1:8000/dev-ui/'
OAUTH_REDIRECT_URI_PROD='https://vertexaisearch.cloud.google.com/oauth-redirect'

# Auth ID — must match the authorization registered in Gemini Enterprise
AUTH_ID='staging-ui_oauth_token'
```

### 4. Run Locally

```bash
make playground
```

Visit http://localhost:8501 and try: "What's the weather in Los Angeles?"

---

## Deployment

### Architecture

Deployment is split across two tools, each owning what it is best suited for:

| Layer | Tool | Resources |
|---|---|---|
| Infrastructure | Terraform | Cloud Run (MCP server), Artifact Registry, GCS buckets, IAM, Gemini Enterprise OAuth registration |
| Agent Engine | `deployment/deploy_agents.py` | Vertex AI Agent Engine (create + update) |

Terraform manages registration but **not** the Agent Engine source/env-vars. `deploy_agents.py` is the single owner of that resource — it creates it on first run and updates source code and env vars on every subsequent run. This avoids the split-ownership problem where two tools fight over env vars.

### CI/CD Pipeline

Push to the configured branch triggers Cloud Build:

```
build MCP Docker image
        ↓
push image to Artifact Registry
        ↓
terraform apply  ──── Cloud Run MCP server
                 ──── GE OAuth authorization
                 ──── GE agent registration
        ↓
extract Cloud Run URL  (gcloud run services describe)
        ↓
deploy_agents.py  ──── Agent Engine (create or update)
                       env vars: MCP_URL, AUTH_ID, LOGS_BUCKET_NAME, telemetry
        ↓
load test  (staging only)
        ↓
trigger prod pipeline  (staging only)
```

### One-time Setup

This section is for someone setting up the project from scratch in their own GCP environment. Follow the steps in order — each step is a prerequisite for the next.

#### Prerequisites

**GCP Projects**

You need two or three GCP projects:

| Variable | Purpose |
|---|---|
| `cicd_runner_project_id` | Hosts the Cloud Build triggers for PR checks and prod deploys. Can be the same as `prod_project_id`. |
| `staging_project_id` | Hosts the staging Cloud Run service, Agent Engine, and the staging CD pipeline trigger. |
| `prod_project_id` | Hosts the production Cloud Run service and Agent Engine. |

**Required caller permissions**

The identity running the initial `terraform apply` (your personal account or a bootstrap SA) needs the following on all three projects:

- `roles/owner` or `roles/editor` + `roles/resourcemanager.projectIamAdmin`

This is required because Terraform creates service accounts and grants them IAM roles. After the bootstrap, the CI/CD service accounts take over and manage their own permissions going forward.

**Tools**

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.0.0
- [gcloud CLI](https://cloud.google.com/sdk/docs/install)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

---

#### Step 1 — Create the Terraform state bucket

Terraform state is stored in GCS. The bucket must exist before running `terraform init`. Create it manually:

```bash
gcloud storage buckets create gs://<YOUR_CICD_PROJECT_ID>-terraform-state \
  --project=<YOUR_CICD_PROJECT_ID> \
  --location=us-central1 \
  --uniform-bucket-level-access
```

Then update `deployment/terraform/backend.tf` to match:

```hcl
terraform {
  backend "gcs" {
    bucket = "<YOUR_CICD_PROJECT_ID>-terraform-state"
    prefix = "agent-solution-ops/prod"
  }
}
```

#### Step 2 — Configure `deployment/terraform/variables.tf`

All Terraform variables are stored as `default` values directly in `variables.tf` — no separate `.tfvars` file is needed (and `*.tfvars` is git-ignored anyway). Edit the placeholder defaults:

```hcl
variable "prod_project_id"        { default = "your-production-project-id" }
variable "staging_project_id"     { default = "your-staging-project-id" }
variable "cicd_runner_project_id" { default = "your-cicd-project-id" }   # often same as prod
variable "repository_owner"       { default = "your-github-org-or-username" }
variable "repository_name"        { default = "your-github-repo-name" }
variable "region"                 { default = "us-central1" }
variable "ge_app_staging"         { default = "your-ge-app-id-staging" }
variable "ge_app_prod"            { default = "your-ge-app-id-prod" }
```

Also update the Cloud Build connection names to match what you'll create in Step 3:

```hcl
variable "host_connection_name"    { default = "your-cicd-project-connection-name" }
variable "staging_connection_name" { default = "your-staging-project-connection-name" }
```

To enable Gemini Enterprise OAuth registration, set the name of the Secret Manager secret that holds your OAuth client JSON:

```hcl
variable "oauth_client_id_secret_name" { default = "your-oauth-secret-name" }
```

Leave it as `""` to skip GE registration during the initial bootstrap. You can enable it in a later apply once the infrastructure is stable.

#### Step 3 — Set up Cloud Build GitHub connections

Two Cloud Build GitHub connections are required — one in each project that runs a pipeline trigger:

| Project | Connection name (must match `variables.tf`) | Used by |
|---|---|---|
| `cicd_runner_project_id` | `host_connection_name` | PR checks + prod deploy trigger |
| `staging_project_id` | `staging_connection_name` | Staging CD trigger |

**To create each connection:**

1. In the GCP Console, go to **Cloud Build → Repositories** for the target project
2. Click **Create host connection**, choose GitHub, and follow the OAuth flow
3. Once the connection exists, link your repository to it

Alternatively, store a GitHub Personal Access Token (PAT) in Secret Manager and set `github_pat_secret_id` and `github_app_installation_id` in `variables.tf` — Terraform will create the connection automatically if `create_cb_connection = false`.

#### Step 4 — Configure Cloud Build substitutions

Edit the `substitutions` block at the bottom of `.cloudbuild/staging.yaml` and `.cloudbuild/deploy-to-prod.yaml`:

| Substitution | Description |
|---|---|
| `_STAGING_PROJECT_ID` | GCP project ID for staging |
| `_PROD_PROJECT_ID` | GCP project ID for production |
| `_REGION` | GCP region (default: `us-central1`) |
| `_APP_SERVICE_ACCOUNT_STAGING` | Service account email for the staging Agent Engine (created by Terraform — set after first apply) |
| `_APP_SERVICE_ACCOUNT_PROD` | Service account email for the prod Agent Engine (created by Terraform — set after first apply) |
| `_AUTH_ID_STAGING` | GE authorization ID for staging (default: `staging-ui_oauth_token`) |
| `_AUTH_ID_PROD` | GE authorization ID for prod (default: `prod-ui_oauth_token`) |
| `_LOGS_BUCKET_NAME_STAGING` | GCS bucket for load test result export |

The `AUTH_ID` values must match the `${each.key}-${local.auth_id}` pattern in `deployment/terraform/gemini_enterprise.tf`.

The service account emails follow the pattern `{project_name}-app@{project_id}.iam.gserviceaccount.com`. You can fill them in after the first `terraform apply` creates the accounts, or pre-compute them if you know the values.

#### Step 5 — Bootstrap Terraform

Authenticate with your personal account (which has the required permissions from the Prerequisites section):

```bash
gcloud auth application-default login
```

Then run the initial apply:

```bash
cd deployment/terraform
terraform init
terraform apply
```

This creates all supporting infrastructure: service accounts, IAM bindings, Cloud Build triggers, Artifact Registry repositories, GCS buckets, and Cloud Run services.

> **Note:** The Agent Engine itself is not created here. It is created on the first successful Cloud Build run by `deploy_agents.py`.

#### Step 6 — Update Cloud Build substitutions with created service account emails

After Step 5, retrieve the service account emails Terraform created and update the substitutions in the Cloud Build YAML files:

```bash
# Staging
gcloud iam service-accounts list --project=<YOUR_STAGING_PROJECT_ID> --filter="displayName:Agent Service Account"

# Prod
gcloud iam service-accounts list --project=<YOUR_PROD_PROJECT_ID> --filter="displayName:Agent Service Account"
```

Update `_APP_SERVICE_ACCOUNT_STAGING` and `_APP_SERVICE_ACCOUNT_PROD` in the Cloud Build YAML files accordingly.

#### Step 7 — Push to trigger CI/CD

The pipelines are triggered by branch pushes:

| Branch | Pipeline | File |
|---|---|---|
| `staging` | Build, deploy to staging, load test | `.cloudbuild/staging.yaml` |
| `main` | Deploy to production (requires manual approval in Cloud Build) | `.cloudbuild/deploy-to-prod.yaml` |

Push to `staging` to trigger the first automated deployment:

```bash
git push origin staging
```

---

#### Ongoing IAM changes

The CI/CD pipelines include their own IAM bindings as Terraform targets, so changes to `cicd_roles` in `variables.tf` are applied automatically on the next pipeline run — no manual intervention needed for own-project role changes.

Cross-project IAM grants (defined in `cicd_sa_deployment_required_roles`) still require a manual local `terraform apply` because the staging SA cannot grant itself roles in the prod project:

```bash
cd deployment/terraform
terraform apply -target=google_project_iam_member.staging_cicd_deployment_roles \
                -target=google_project_iam_member.other_projects_roles
```

---

#### Manual operations (outside CI/CD)

**Deploy agent manually:**

```bash
make deploy
```

Runs `deployment/deploy_agents.py` directly. Useful for one-off deploys from a developer machine.

**Register to Gemini Enterprise manually:**

```bash
make register-gemini-enterprise
```

Handled automatically by Terraform in CI/CD when `oauth_client_id_secret_name` is set. The Makefile target is available for manual registration or re-registration.

---

## What This Project Does

This project demonstrates how to build an ADK agent that:

1. **Uses OAuth 2.0 authentication** to access protected MCP servers
2. **Automatically switches** between development and production authentication modes
3. **Handles OAuth flows differently** for local testing vs. Gemini Enterprise deployment
4. **Calls MCP tools** (weather forecasts) with authenticated requests

### Authentication Architecture

**Development Mode (Local Testing):**
```
User → ADK Web UI → Agent (OAuth2Auth) → Google OAuth → Token → MCP Server → Weather API
```
- Uses `auth_scheme` and `auth_credential` to trigger OAuth flow
- ADK manages token storage and refresh automatically

**Production Mode (Gemini Enterprise):**
```
User → Gemini Enterprise UI → Agent (header_provider) → Context Token → MCP Server → Weather API
```
- `McpToolset` is created with `header_provider=mcp_header_provider` and **no** `auth_scheme`
- Omitting `auth_scheme` ensures `_credentials_manager = None` in `MCPTool`, so the credential check is skipped and `header_provider` is called directly on every request
- `mcp_header_provider` reads the OAuth token from `session.state` keyed by `AUTH_ID`
- Token is injected into MCP requests via `Authorization: Bearer` header

The agent **automatically selects** the correct mode based on the `ENVIRONMENT` variable (`"development"` → dev mode, anything else → production mode).

---

## Environment Variables Reference

### Agent (`src/adk_agent/.env`)

| Variable | Required | Description |
|---|---|---|
| `ENVIRONMENT` | No | `development` enables dev OAuth flow. Default: `deployment` (production mode). |
| `MCP_URL` | Yes | Full URL of the MCP server including `/mcp` path. |
| `AUTH_ID` | Yes | Gemini Enterprise authorization ID (e.g. `staging-ui_oauth_token`). |
| `GOOGLE_CLIENT_ID` | Dev only | OAuth client ID for browser-based flow. |
| `GOOGLE_CLIENT_SECRET` | Dev only | OAuth client secret for browser-based flow. |
| `GOOGLE_CLOUD_PROJECT` | No | GCP project ID. |
| `GOOGLE_CLOUD_LOCATION` | No | GCP region. Default: `us-central1`. |
| `OAUTH_REDIRECT_URI_DEV` | No | Dev redirect URI. Default: `http://127.0.0.1:8000/dev-ui/`. |
| `OAUTH_REDIRECT_URI_PROD` | No | Prod redirect URI. Default: `https://vertexaisearch.cloud.google.com/oauth-redirect`. |
| `DEBUG_CONTEXT` | No | Set to `true` to dump full session context to stderr on each MCP call. |
| `LOGS_BUCKET_NAME` | No | GCS bucket for artifact storage. Default: none (uses in-memory). |

### MCP Server (`src/mcp_servers/weather_mcp_server/.env`)

| Variable | Required | Description |
|---|---|---|
| `PROJECT_ID` | Yes | GCP project ID. |
| `GOOGLE_CLIENT_ID` | Yes | OAuth client ID for MCP server OAuth middleware. |
| `GOOGLE_CLIENT_SECRET` | Yes | OAuth client secret. |
| `OAUTH_REDIRECT_URI_PROD` | No | Production redirect URI. |
