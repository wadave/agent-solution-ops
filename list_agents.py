import subprocess
import json
import logging
import requests
import google.auth
from google.auth.transport.requests import Request

def get_token():
    credentials, project = google.auth.default()
    credentials.refresh(Request())
    return credentials.token

project_id = "dw-genai-dev"
location = "us-central1"
token = get_token()

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("--- Reasoning Engines ---")
url = f"https://us-central1-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/reasoningEngines"
res = requests.get(url, headers=headers)
print(json.dumps(res.json(), indent=2))
