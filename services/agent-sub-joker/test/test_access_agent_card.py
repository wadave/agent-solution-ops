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

import os
from fastapi.testclient import TestClient
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch

# Mock environment variables before importing app
os.environ["GCP_PROJECT"] = "test-project"
os.environ["GCP_REGION"] = "us-central1"
os.environ["AGENT_CARD_BUCKET_URI"] = "gs://test-bucket"
os.environ["SERVICE_NAME"] = "agent-sub-joker"

# We mock cloudrun to avoid issues with service info fetching during import/startup
with patch("common_gcp.cloudrun.get_service_info") as mock_get_service:
    mock_get_service.return_value.uri = "https://agent-sub-joker-test.a.run.app"
    from app import app


@pytest_asyncio.fixture(autouse=True)
def change_working_directory():
    cwd = os.getcwd()
    app_dir = os.path.dirname(os.path.abspath("src/app.py"))
    # Change the working directory to load the app correctly
    os.chdir(app_dir)
    try:
        yield # Run the tests
    finally:
        os.chdir(cwd)


@pytest_asyncio.fixture
async def mock_test_client(mocker):
    """
    Fixture to mock GCS and other cloud services during startup.
    This fulfills the requirement to mock GCS bucket upload.
    """
    # Mock Google Cloud Storage Client to avoid authentication issues
    mock_storage_client = mocker.patch("google.cloud.storage.Client")
    mock_bucket = MagicMock()
    mock_storage_client.return_value.bucket.return_value = mock_bucket
    mock_blob = MagicMock()
    mock_bucket.blob.return_value = mock_blob

    # Mock Vertex AI and GenAI client to avoid side effects during module load/startup
    mocker.patch("vertexai.init")
    mocker.patch("google.genai.Client")

    with TestClient(app) as test_client:
        # The startup events (including build_and_log_agent_card) run here
        yield test_client


@pytest.mark.asyncio
async def test_access_agent_card(mock_test_client):
    """
    Test accessing the published agent card via the app's root endpoint.
    """
    # Invoke the root endpoint which returns the agent card in A2A applications
    response = mock_test_client.get("/.well-known/agent.json")

    # Assert the response is successful
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response body: {response.text}")

    assert response.status_code == 200

    response_json = response.json()

    print(f"{response_json}")

    # Assert that the response contains expected agent card fields
    # Based on the AgentCard structure and what AgentCardBuilder produces
    assert "name" in response_json
    assert response_json["name"] == "joke_telling_agent"
    assert "description" in response_json
    assert "joke" in response_json["description"].lower()

    print("Successfully accessed agent card via root endpoint")
