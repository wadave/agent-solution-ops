# Gemini Enterprise with ADK Agent for Secured Remote MCP Services

An ADK agent deployed on Google Cloud that uses OAuth 2.0 to securely call MCP (Model Context Protocol) tools. The included example fetches weather data from the National Weather Service API through a FastMCP server on Cloud Run.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Local Development](#local-development)
- [CI/CD Pipeline Setup](#cicd-pipeline-setup)
  - [Prerequisites](#prerequisites)
  - [Step 0 — Bootstrap IAM Permissions](#step-0--bootstrap-iam-permissions)
  - [Step 1 — Create Terraform State Bucket](#step-1--create-terraform-state-bucket)
  - [Step 2 — Configure Terraform Variables](#step-2--configure-terraform-variables)
  - [Step 3 — Set Up Cloud Build GitHub Connections](#step-3--set-up-cloud-build-github-connections)
  - [Step 4 — Configure Cloud Build Substitutions](#step-4--configure-cloud-build-substitutions)
  - [Step 5 — Bootstrap Terraform](#step-5--bootstrap-terraform)
  - [Step 6 — Push to Trigger CI/CD](#step-6--push-to-trigger-cicd)
- [How the Pipeline Works](#how-the-pipeline-works)
- [Post-Setup Reference](#post-setup-reference)
- [Environment Variables Reference](#environment-variables-reference)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

![architecture](./assets/ge-adk-mcp.png)

### Components

| Component | Role |
|---|---|
| **Gemini Enterprise Engine & UI** | User-facing interface, intent recognition, and dynamic token-passing |
| **VertexAISession Services** | Conversation history and state persistence |
| **ADK Agent** | Reasoning engine that invokes MCP tools; includes retry logic for transient API errors |
| **Weather MCP Server (Cloud Run)** | FastMCP microservice that calls the NWS Weather API |
| **Identity Provider** | OAuth 2.0 authentication for secure tool execution |
| **Model Armor** | Project-wide floor settings for prompt injection, harmful content, and malicious URI filtering |

### Component Diagram

```mermaid
graph TB
    subgraph "Google Cloud"
        subgraph "User Interface"
        UI["Gemini Enterprise UI"]
        end

        subgraph "Security"
            MA(["Model Armor<br/>Floor Settings"])
        end

        subgraph "Gemini Enterprise"
            AS["Gemini Enterprise Engine"]
            VS["VertexAISession Services"]
            RE["Agent Engine<br/>ADK Agent (w/ Retry Logic)"]
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
    AS -->|Manage Session| VS
    VS -->|Invoke Agent| RE
    RE -->|MCP Tool Call| MCP
    MCP -->|Fetch Weather| NWS

    AS -.->|Filtered by| MA
    RE -.->|Filtered by| MA

    AS -.->|OAuth Flow| OAUTH
    OAUTH -.->|Tokens| AS
    AS -.->|Pass Token| MCP

    style UI fill:#e1f5ff,stroke:#333,stroke-width:2px,color:#000
    style AS fill:#fff4e1,stroke:#333,stroke-width:2px,color:#000
    style RE fill:#f0e1ff,stroke:#333,stroke-width:2px,color:#000
    style MCP fill:#e1ffe1,stroke:#333,stroke-width:2px,color:#000
    style OAUTH fill:#ffe1e1,stroke:#333,stroke-width:2px,color:#000
    style NWS fill:#f5f5f5,stroke:#333,stroke-width:2px,color:#000
    style MA fill:#fff5f5,stroke:#cc0000,stroke-width:2px,stroke-dasharray: 5 5,color:#cc0000
```

### Authentication Modes

The agent automatically switches authentication modes based on the `ENVIRONMENT` variable:

| Mode | When | Auth Flow |
|---|---|---|
| **Development** | `ENVIRONMENT=development` | `User → ADK Web UI → Agent (OAuth2Auth) → Google OAuth → Token → MCP Server` |
| **Production** | Any other value | `User → Gemini Enterprise UI → Agent (header_provider) → Context Token → MCP Server` |

**Development mode** uses `auth_scheme` and `auth_credential` to trigger a browser-based OAuth flow. ADK manages token storage and refresh automatically.

**Production mode** creates `McpToolset` with `header_provider=mcp_header_provider` and **no** `auth_scheme`. Omitting `auth_scheme` ensures the credential manager is bypassed and `header_provider` is called directly on every request. The token is read from `session.state` (keyed by `AUTH_ID`) and injected as an `Authorization: Bearer` header.

### Security

Model Armor Floor Settings are configured at the project level via [`deployment/terraform/model_armor.tf`](deployment/terraform/model_armor.tf) to provide:

- **Prompt Injection & Jailbreak Protection** — blocks adversarial attempts to bypass model constraints
- **Harmful Content Filtering** — enforces RAI filters for hate speech, harassment, sexually explicit content, and dangerous activities
- **Malicious URI Detection** — blocks links to known malicious sites

See [`docs/model_armor_guide.md`](docs/model_armor_guide.md) for details.

---

## Local Development

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager
- Google Cloud project with [OAuth 2.0 credentials](https://console.cloud.google.com/apis/credentials)

### Setup

1. **Install dependencies:**

   ```bash
   uv sync
   ```

2. **Create your `.env` file:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in your `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLIENT_ID`, and `GOOGLE_CLIENT_SECRET`.

3. **Add OAuth redirect URIs** to your OAuth 2.0 Client ID in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials):

   ```
   http://127.0.0.1:8000/dev-ui/
   http://localhost:8000/dev-ui/
   ```

4. **Run the agent:**

   ```bash
   uv run adk web src
   ```

   Visit http://localhost:8000 and try: *"What's the weather in Los Angeles?"*

---

## CI/CD Pipeline Setup

This section walks you through setting up the CI/CD pipeline from scratch. Follow the steps in order — each step is a prerequisite for the next.

> **Summary of what you'll do:**
> 1. Grant IAM permissions so CI/CD service accounts can manage infrastructure
> 2. Create a GCS bucket for Terraform state
> 3. Configure Terraform variables for your projects
> 4. Connect your GitHub repo to Cloud Build
> 5. Configure Cloud Build substitution variables
> 6. Run `terraform apply` to provision all infrastructure (with dummy placeholders)
> 7. Push code to trigger the pipeline, which replaces the placeholders with real application code

### Prerequisites

**Google Cloud Projects** — You need two or three:

| Variable | Purpose |
|---|---|
| `cicd_runner_project_id` | Hosts Cloud Build triggers for PR checks and prod deploys. Can be the same as `prod_project_id`. |
| `staging_project_id` | Hosts the staging Cloud Run service, Agent Engine, and staging CD trigger. |
| `prod_project_id` | Hosts the production Cloud Run service and Agent Engine. |

**Gemini Enterprise** — Create a Gemini Enterprise app and note its ID. Set up OAuth 2.0 Web Client credentials and store the downloaded JSON in Secret Manager as `client_secret`.

**Required permissions** — The identity running the initial `terraform apply` needs:

- `roles/owner` **or** `roles/editor` + `roles/resourcemanager.projectIamAdmin`

  (Required because Terraform creates service accounts and grants IAM roles. After bootstrap, CI/CD service accounts manage their own permissions.)

**Tools:**

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.0.0
- [gcloud CLI](https://cloud.google.com/sdk/docs/install)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

---

### Step 0 — Bootstrap IAM Permissions

Grant the CI/CD service accounts the permissions they need to manage infrastructure across staging and production.

Run the setup script from your local machine (using an account with `roles/owner` or `roles/resourcemanager.projectIamAdmin`):

```bash
chmod +x deployment/scripts/setup_iam.sh
./deployment/scripts/setup_iam.sh <STAGING_PROJECT_ID> <PROD_PROJECT_ID> <STAGING_PROJECT_NUMBER>
```

Replace the placeholders with your actual values. `<STAGING_PROJECT_NUMBER>` is the numeric project number of your staging project (where the CI/CD runners live).

---

### Step 1 — Create Terraform State Bucket

Terraform state is stored in GCS. Create the bucket before running `terraform init`:

```bash
gcloud storage buckets create gs://<YOUR_PROJECT_ID>-terraform-state \
  --project=<YOUR_PROJECT_ID> \
  --location=us-central1 \
  --uniform-bucket-level-access
```

Then update `deployment/terraform/backend.tf` to match:

```hcl
terraform {
  backend "gcs" {
    bucket = "<YOUR_PROJECT_ID>-terraform-state"
    prefix = "agent-solution-ops/prod"
  }
}
```

---

### Step 2 — Configure Terraform Variables

Create `deployment/terraform/terraform.tfvars` (this file is git-ignored):

```hcl
# --- Required ---
prod_project_id        = "your-production-project-id"
staging_project_id     = "your-staging-project-id"
cicd_runner_project_id = "your-cicd-project-id"   # often same as prod
repository_owner       = "your-github-org-or-username"
repository_name        = "your-github-repo-name"
region                 = "us-central1"
ge_app_staging         = "your-ge-app-id-staging"
ge_app_prod            = "your-ge-app-id-prod"

# --- Cloud Build connections (must match names created in Step 3) ---
host_connection_name    = "your-cicd-project-connection-name"
staging_connection_name = "your-staging-project-connection-name"

# --- Gemini Enterprise OAuth (optional — leave "" to skip during bootstrap) ---
oauth_client_id_secret_name = "client_secret"
```

> **Tip:** Set `oauth_client_id_secret_name = ""` for the initial bootstrap. Enable it in a later `terraform apply` once the infrastructure is stable.

---

### Step 3 — Set Up Cloud Build GitHub Connections

Two GitHub connections are required — one per project that runs a pipeline trigger:

| Project | Connection name (must match Step 2) | Used by |
|---|---|---|
| `cicd_runner_project_id` | `host_connection_name` | PR checks + prod deploy trigger |
| `staging_project_id` | `staging_connection_name` | Staging CD trigger |

**Option A — Google Cloud Console (manual):**

1. Go to **Cloud Build → Repositories** in the target project
2. Click **Create host connection**, choose GitHub, follow the OAuth flow
3. Link your repository to the connection

**Option B — `agent-starter-pack` CLI (recommended):**

```bash
uvx agent-starter-pack setup-cicd
```

See [agent-starter-pack docs](https://googlecloudplatform.github.io/agent-starter-pack/cli/setup_cicd) for details.

**Option C — Terraform-managed (PAT):**

Store a GitHub Personal Access Token in Secret Manager and set `github_pat_secret_id` and `github_app_installation_id` in `variables.tf`. Terraform will create the connection automatically.

---

### Step 4 — Configure Cloud Build Substitutions

Edit the `substitutions` block at the bottom of `.cloudbuild/staging.yaml` and `.cloudbuild/deploy-to-prod.yaml`:

| Substitution | Description |
|---|---|
| `_STAGING_PROJECT_ID` | Google Cloud project ID for staging |
| `_PROD_PROJECT_ID` | Google Cloud project ID for production |
| `_REGION` | Google Cloud region (default: `us-central1`) |
| `_APP_SERVICE_ACCOUNT_STAGING` | Service account email for staging Agent Engine (set after first `terraform apply`) |
| `_APP_SERVICE_ACCOUNT_PROD` | Service account email for prod Agent Engine (set after first `terraform apply`) |
| `_AUTH_ID_STAGING` | GE authorization ID for staging (default: `staging-weather-oauth-token`) |
| `_AUTH_ID_PROD` | GE authorization ID for prod (default: `prod-weather-oauth-token`) |

**How `AUTH_ID` values are determined:** They follow the pattern `<environment>-<local.auth_id>` from `deployment/terraform/gemini_enterprise.tf`, where `local.auth_id = "weather-oauth-token"`. Use a project-specific suffix to avoid conflicts if multiple agents share the same GE app.

**Service account email pattern:** `{project_name}-app@{project_id}.iam.gserviceaccount.com`

> **Note:** You can skip this step. When you run `terraform apply` in Step 5, Terraform automatically configures these substitutions in the Cloud Build triggers it creates.

---

### Step 5 — Bootstrap Terraform

Authenticate and apply:

```bash
gcloud auth application-default login

cd deployment/terraform
terraform init
terraform apply
```

This creates all infrastructure: service accounts, IAM bindings, Cloud Build triggers, Artifact Registry, GCS buckets, Cloud Run services (with a dummy hello-world image), and the Agent Engine shell (with a dummy payload).

> **Important:** At this point, everything exists but runs dummy placeholder code. The CI/CD pipeline will deploy the real application on the first run.

---

### Step 6 — Push to Trigger CI/CD

Push to the appropriate branch to trigger the pipeline:

| Branch | Pipeline file | What it does |
|---|---|---|
| `staging` | `.cloudbuild/staging.yaml` | Build MCP image → Terraform → deploy Agent Engine → register to GE |
| `main` | `.cloudbuild/deploy-to-prod.yaml` | Deploy to production (requires manual approval in Cloud Build) |

```bash
git push origin staging
```

After this push, Cloud Build will:
1. Build the real Docker image for your MCP server
2. Push it to Artifact Registry
3. Deploy it to Cloud Run (replacing the dummy container)
4. Run `deploy_agents.py` to upload your agent code to Agent Engine (replacing the dummy payload)
5. Register the agent with Gemini Enterprise

Your pipeline is now live. Future pushes to `staging` or `main` will trigger redeployments automatically.

---

## How the Pipeline Works

### Deployment Architecture

The pipeline uses a hybrid approach — Terraform provisions infrastructure shells, while application code is deployed via SDK and CLI:

| Layer | Tool | What it manages |
|---|---|---|
| **Infrastructure** | Terraform | Cloud Run, Agent Engine, Artifact Registry, GCS, IAM, GE OAuth, Model Armor |
| **MCP Server code** | `gcloud run deploy` | Docker image → Cloud Run |
| **Agent code** | `deployment/deploy_agents.py` | Python tarball → Agent Engine |

Terraform uses `lifecycle { ignore_changes }` on application code fields so the CI/CD pipeline can deploy rapidly without causing state drift.

### Pipeline Execution Flow

```text
build MCP Docker image
        |
push image to Artifact Registry
        |
terraform apply  ---- Cloud Run MCP server (provision infrastructure shell)
                 ---- Agent Engine (provision infrastructure shell)
        |
extract Cloud Run URL  (terraform output)
        |
gcloud run deploy --- Deploy MCP Server Docker Image
        |
deploy_agents.py  --- Deploy Agent Engine Python Code
                      env vars: MCP_URL, AUTH_ID, LOGS_BUCKET_NAME, telemetry
        |
terraform apply  ---- GE OAuth authorization
                 ---- GE agent registration
```

### Agent Naming Convention

Agents are named consistently across Vertex AI Agent Engine and Gemini Enterprise:

```
ADK Hosting Agent for MCP (<environment>)
```

Example: `ADK Hosting Agent for MCP (staging)`

### Deployment Resilience

The `deploy_agents.py` script handles common failure scenarios:

- **API Migration** — Detects agents created with the legacy `package_spec` API and recreates them with the modern `deployment_source` API
- **State Recovery** — If the GCP API returns a stale failed LRO from a previous corrupted deployment, the script catches it and falls back to an `update()` call

---

## Post-Setup Reference

### Ongoing IAM Changes

CI/CD pipelines manage their own IAM bindings automatically. Cross-project IAM grants (e.g., staging SA accessing prod) require a manual local apply:

```bash
cd deployment/terraform
terraform apply -target=google_project_iam_member.staging_cicd_deployment_roles \
                -target=google_project_iam_member.other_projects_roles
```

### Gemini Enterprise OAuth Registration

Controlled by `oauth_client_id_secret_name` in `variables.tf`. Set it to the Secret Manager secret name holding your OAuth client JSON.

**For fresh setups:** The bootstrap `terraform apply` grants `roles/secretmanager.secretAccessor` to the CI/CD service account automatically.

**For existing deployments** where `oauth_client_id_secret_name` was previously empty: Setting a non-empty value causes a one-time bootstrapping issue (Terraform reads the secret at plan time before it can apply the IAM role). Fix it with a manual grant:

```bash
gcloud secrets add-iam-policy-binding <SECRET_NAME> \
  --project=<STAGING_PROJECT_ID> \
  --member="serviceAccount:<PROJECT_NAME>-cd@<STAGING_PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Manual Operations

**Deploy agent manually:**

```bash
uv run deployment/deploy_agents.py
```

**Register to Gemini Enterprise manually:**

```bash
uvx agent-starter-pack@0.36.0 register-gemini-enterprise
```

---

## Environment Variables Reference

### Agent (`src/adk_agent/.env`)

| Variable | Required | Description |
|---|---|---|
| `ENVIRONMENT` | No | `development` enables dev OAuth flow. Default: `deployment` (production mode). |
| `MCP_URL` | Yes | Full URL of the MCP server including `/mcp` path. |
| `AUTH_ID` | Yes | Gemini Enterprise authorization ID (e.g. `staging-weather-oauth-token`). |
| `GOOGLE_CLIENT_ID` | Dev only | OAuth client ID for browser-based flow. |
| `GOOGLE_CLIENT_SECRET` | Dev only | OAuth client secret for browser-based flow. |
| `GOOGLE_CLOUD_PROJECT` | No | Google Cloud project ID. |
| `GOOGLE_CLOUD_LOCATION` | No | Google Cloud region. Default: `us-central1`. |
| `OAUTH_REDIRECT_URI_DEV` | No | Dev redirect URI. Default: `http://127.0.0.1:8000/dev-ui/`. |
| `OAUTH_REDIRECT_URI_PROD` | No | Prod redirect URI. Default: `https://vertexaisearch.cloud.google.com/oauth-redirect`. |
| `GEMINI_MODEL` | No | Gemini model to use. Default: `gemini-2.5-flash`. |
| `RETRY_ATTEMPTS` | No | Number of retry attempts for transient errors. Default: `3`. |
| `MCP_TIMEOUT` | No | Timeout in seconds for MCP server calls. Default: `60`. |
| `LOGS_BUCKET_NAME` | No | GCS bucket for artifact storage. Default: none (uses in-memory). |

### MCP Server (`src/mcp_servers/weather_mcp_server/.env`)

| Variable | Required | Description |
|---|---|---|
| `PROJECT_ID` | Yes | Google Cloud project ID. |
| `GOOGLE_CLIENT_ID` | Yes | OAuth client ID for MCP server OAuth middleware. |
| `GOOGLE_CLIENT_SECRET` | Yes | OAuth client secret. |
| `OAUTH_SCOPES` | No | OAuth scopes requested during Google login. Default: `openid email profile`. |
| `OAUTH_REDIRECT_URI_LOCAL` | No | Redirect URI for the MCP server's local OAuth callback. Default: `http://localhost:8080/oauth/callback`. |
| `OAUTH_REDIRECT_URI_PROD` | No | Production redirect URI. |
| `USE_PRODUCTION_REDIRECT` | No | Set to `true` to use the production redirect URI. Default: `false`. |
| `PROJECT_NUMBER` | No | Google Cloud project number. |

---

## Troubleshooting

### Cloud Build fails with 403 downloading Python packages

**Symptom:**

```
Failed to download `python-dotenv==1.2.1`
HTTP status client error (403 Forbidden)
https://us-python.pkg.dev/artifact-foundry-prod/...
```

**Cause:** If your machine has a corporate Python package proxy (e.g., Google's internal Airlock), `uv lock` bakes internal mirror URLs into `uv.lock`. Cloud Build cannot access those URLs.

**Fix:** Pin the uv index to PyPI in `pyproject.toml`:

```toml
[[tool.uv.index]]
name = "pypi"
url = "https://pypi.org/simple"
default = true
```

Then regenerate the lockfile:

```bash
rm uv.lock && uv lock
git add pyproject.toml uv.lock
git commit -m "fix: pin uv index to PyPI"
```

> This is already configured in this project's `pyproject.toml`.
