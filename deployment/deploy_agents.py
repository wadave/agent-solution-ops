# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Deploy the ADK agent to Vertex AI Agent Engine.

This script is the single owner of the Agent Engine resource. It creates the
engine on first run and updates it on subsequent runs. Terraform manages all
supporting infrastructure (Cloud Run MCP server, IAM, Artifact Registry, GCS,
Gemini Enterprise registration) but does not touch the Agent Engine itself.

Environment variables:
    PROJECT_ID:             GCP project ID for deployment.
    GOOGLE_CLOUD_REGION:    GCP region (default: us-central1).
    APP_SERVICE_ACCOUNT:    Service account email for the agent.
    MCP_URL:                Full URL of the Cloud Run MCP server (including /mcp path).
    AUTH_ID:                Agentspace authorization ID for OAuth token retrieval.
    LOGS_BUCKET_NAME:       GCS bucket for agent artifact/log storage
                            (default: {PROJECT_ID}-agents-solution-ops-logs).
    DISPLAY_NAME_SUFFIX:    Human-readable env suffix, e.g. "Staging" or "Prod".
    BUCKET_NAME:            GCS staging bucket for source upload (default: {PROJECT_ID}-bucket).
    REQUIREMENTS_FILE:      Path to requirements.txt (default: src/adk_agent/app_utils/.requirements.txt).
    HOSTING_AGENT_ID_FILE:  File path to write the deployed resource name for CI/CD
                            handoff (default: /workspace/hosting_agent_id.txt).
"""

import importlib
import logging
import os
import shutil
import sys
import tempfile

import vertexai
from dotenv import load_dotenv
from google.genai.errors import ClientError
from vertexai._genai import _agent_engines_utils
from vertexai._genai.types import AgentEngineConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


_EXCLUDE = {
    ".env", ".env.example", "client_secret.json", "client_secrets.json",
    "credentials.json", "token.json",
}
_EXCLUDE_DIRS = {"__pycache__", ".gemini"}
_EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".ipynb"}


def _copy_source_clean(src_dir: str, dest_dir: str) -> None:
    """Copy src_dir to dest_dir, omitting credentials, caches, and notebooks."""
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in _EXCLUDE_DIRS]
        rel_root = os.path.relpath(root, src_dir)
        target_root = os.path.join(dest_dir, rel_root)
        os.makedirs(target_root, exist_ok=True)
        for fname in files:
            if fname in _EXCLUDE or any(fname.endswith(s) for s in _EXCLUDE_SUFFIXES):
                continue
            shutil.copy2(os.path.join(root, fname), os.path.join(target_root, fname))


def generate_class_methods_from_agent(agent_instance):
    """Generate class method specs from the agent's register_operations()."""
    registered = _agent_engines_utils._get_registered_operations(agent=agent_instance)
    spec = _agent_engines_utils._generate_class_methods_spec_or_raise(
        agent=agent_instance, operations=registered
    )
    return [_agent_engines_utils._to_dict(m) for m in spec]


def list_existing_agents(client):
    """Return a dict of {display_name: resource_name} for all Agent Engine resources."""
    agents = {}
    try:
        for agent in client.agent_engines.list():
            name = agent.api_resource.display_name
            if name:
                agents[name] = agent.api_resource.name
    except Exception as e:
        logger.warning(f"Failed to list existing agents: {e}")
    return agents


def main():
    load_dotenv()

    project_id = os.environ.get("PROJECT_ID")
    location = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
    service_account = os.environ.get("APP_SERVICE_ACCOUNT")
    mcp_url = os.environ.get("MCP_URL", "")
    auth_id = os.environ.get("AUTH_ID", "")
    display_name_suffix = os.environ.get("DISPLAY_NAME_SUFFIX", "Staging")
    bucket_name = os.environ.get("BUCKET_NAME", f"{project_id}-bucket")
    # Bucket name follows the pattern set in deployment/terraform/storage.tf:
    #   google_storage_bucket.logs_data_bucket = "{project_id}-{project_name}-logs"
    logs_bucket_name = os.environ.get(
        "LOGS_BUCKET_NAME", f"{project_id}-agents-solution-ops-logs"
    )
    requirements_file = os.environ.get(
        "REQUIREMENTS_FILE", "src/adk_agent/app_utils/.requirements.txt"
    )

    if not project_id or not service_account:
        logger.error(
            "Missing required environment variables: PROJECT_ID, APP_SERVICE_ACCOUNT"
        )
        sys.exit(1)

    if not auth_id:
        logger.error(
            "AUTH_ID is required so that adk_agent.agent can initialise at import time. "
            "Pass the Agentspace authorization ID (e.g. staging-ui_oauth_token)."
        )
        sys.exit(1)

    display_name = f"ADK Hosting Agent for MCP ({display_name_suffix.lower()})"

    # adk_agent.agent validates AUTH_ID (and optionally MCP_URL) at module level.
    # Set them in the environment so the import succeeds before we introspect the agent.
    os.environ["AUTH_ID"] = auth_id
    if mcp_url:
        os.environ["MCP_URL"] = mcp_url

    # Ensure the src/ layout is importable when running from the repo root.
    sys.path.insert(0, "src")

    # Load the agent instance to generate the class-methods spec required by Agent Engine.
    module = importlib.import_module("adk_agent.agent_engine_app")
    agent_instance = module.agent_engine
    class_methods_list = generate_class_methods_from_agent(agent_instance)

    # Build the environment variables that will be injected into the deployed agent.
    env_vars = {
        "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
        "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
        "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
        # Note: GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION are reserved by
        # Agent Engine and injected by the platform — do not set them here.
        "AUTH_ID": auth_id,
        "LOGS_BUCKET_NAME": logs_bucket_name,
    }
    if mcp_url:
        env_vars["MCP_URL"] = mcp_url

    with tempfile.TemporaryDirectory(dir=".") as tmpdir:
        clean_pkg = os.path.join(tmpdir, "adk_agent")
        _copy_source_clean("./src/adk_agent", clean_pkg)

        config = AgentEngineConfig(
            display_name=display_name,
            source_packages=[clean_pkg],
            entrypoint_module="adk_agent.agent_engine_app",
            entrypoint_object="agent_engine",
            class_methods=class_methods_list,
            env_vars=env_vars,
            service_account=service_account,
            requirements_file=requirements_file,
            staging_bucket=f"gs://{bucket_name}",
            agent_framework="google-adk",
        )

        vertexai.init(project=project_id, location=location)
        client = vertexai.Client(
            project=project_id,
            location=location,
            http_options={"api_version": "v1beta1"},
        )

        existing_agents = list_existing_agents(client)

        if display_name in existing_agents:
            logger.info(f"Updating existing agent: {display_name}")
            try:
                remote_agent = client.agent_engines.update(
                    name=existing_agents[display_name], config=config
                )
            except ClientError as e:
                if "spec.package_spec" in str(e):
                    # The existing agent was created with the legacy package_spec
                    # API. The platform does not allow switching to deployment_source
                    # in-place, so delete and recreate it once to migrate.
                    # Gemini Enterprise registration will be refreshed on the next
                    # Terraform run.
                    logger.warning(
                        "Existing agent uses the legacy package_spec spec and cannot "
                        "be updated to deployment_source. Deleting and recreating it "
                        "to migrate to the current SDK. GE registration will be "
                        "refreshed by Terraform on the next run."
                    )
                    client.agent_engines.delete(name=existing_agents[display_name], force=True)
                    remote_agent = client.agent_engines.create(config=config)
                else:
                    raise
        else:
            logger.info(f"Creating new agent: {display_name}")
            remote_agent = client.agent_engines.create(config=config)

        agent_resource_name = remote_agent.api_resource.name
    logger.info(f"Deployed '{display_name}': {agent_resource_name}")

    # Write agent resource name for downstream CI/CD steps (e.g. frontend deployment).
    hosting_agent_id_path = os.environ.get(
        "HOSTING_AGENT_ID_FILE", "/workspace/hosting_agent_id.txt"
    )
    try:
        with open(hosting_agent_id_path, "w") as f:
            f.write(agent_resource_name)
        logger.info(f"Wrote agent resource name to {hosting_agent_id_path}")
    except OSError:
        logger.warning(
            f"Could not write agent resource name to {hosting_agent_id_path}"
        )


if __name__ == "__main__":
    main()
