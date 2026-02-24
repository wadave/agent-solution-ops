# Copyright 2025 Google LLC
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

import importlib.metadata
import os
from dotenv import load_dotenv
import logging
import common_logging as logs
from common_gcp import cloudrun as cloudrun
from google.cloud import storage
import json
import tempfile

from agent import root_agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder


load_dotenv()


project_id = os.getenv('GCP_PROJECT', 'unset')
location = os.getenv('GCP_REGION', 'unset')
service_slug = os.getenv('SERVICE_SLUG', 'unset')
service_name = os.getenv('SERVICE_NAME', 'unset')
service_description = os.getenv('SERVICE_DESC', 'unset')
service_port = int(os.getenv('LOCAL_SERVICE_PORT', '8080'))
service_version = importlib.metadata.version('src')
gcs_a2a_bucket = os.getenv('AGENT_CARD_BUCKET_URI', 'unset')


log = logs.get_logger('adk.to_a2a.app', logging.INFO)


cloudrun_service = cloudrun.get_service_info(project_id=project_id, service_name=service_name, region=location)
protocol = "https"
host = cloudrun_service.uri.replace("https://", "")
port = 443
rpc_url = f"{protocol}://{host}:{port}/"

card_builder = AgentCardBuilder(
    agent=root_agent,
    rpc_url=rpc_url,
)

global a2a_card
a2a_card = None


app = to_a2a(agent=root_agent, host=host, port=port, protocol="https")

@app.on_event("startup")
async def build_and_log_agent_card():
    """Builds the agent card and stores it in a global variable on startup."""
    global a2a_card
    try:
        # We are now inside an async function, so 'await' works correctly
        a2a_card = await card_builder.build()
        log.info("Successfully built a2a_card during startup.")
        log.info(f"a2a_card: {a2a_card}")

        # Publish Agent Card for Discovery if GCS Bucket is set
        if gcs_a2a_bucket and gcs_a2a_bucket != 'unset':
            try:
                storage_client = storage.Client()
                bucket_name = gcs_a2a_bucket.replace("gs://", "")
                bucket = storage_client.bucket(bucket_name)

                # Use a temporary file to upload the JSON
                with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".json") as temp_file:
                    json.dump(a2a_card.model_dump(), temp_file, indent=2)
                    temp_file.flush() # Ensure all data is written to the file

                    blob_name = f"{service_name}.json"
                    blob = bucket.blob(blob_name)

                    log.info(f"Uploading agent card to gs://{bucket_name}/{blob_name}")
                    blob.upload_from_filename(temp_file.name)
                    log.info("Successfully uploaded agent card to GCS.")

                os.remove(temp_file.name) # Clean up the temporary file
            except Exception as e:
                log.error(f"Failed to upload agent card to GCS: {e}")
    except Exception as e:
        log.error(f"Failed to build agent card during startup: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
