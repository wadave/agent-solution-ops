import os
import sys

# use the user's venv
sys.path.insert(0, "/workspace/.venv/lib/python3.13/site-packages")
sys.path.insert(0, "/usr/local/google/home/wangdave/remote_ws/projects/agents-solution-ops/.venv/lib/python3.13/site-packages")

import vertexai
from vertexai._genai import _agent_engines_utils
from vertexai._genai.types import AgentEngineConfig

def main():
    project_id = "dw-genai-dev"
    location = "us-central1"
    service_account = "agents-solution-ops-app@dw-genai-dev.iam.gserviceaccount.com"
    requirements_file = "src/adk_agent/app_utils/.requirements.txt"
    bucket_name = "dw-genai-dev-bucket"
    display_name = "ADK Hosting Agent (staging)"
    
    vertexai.init(project=project_id, location=location)
    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options={"api_version": "v1beta1"},
    )
    
    agents = {}
    for agent in client.agent_engines.list():
        if agent.api_resource.display_name:
            agents[agent.api_resource.display_name] = agent.api_resource.name
            
    if display_name not in agents:
        print("Agent not found!")
        return
        
    config = AgentEngineConfig(
        display_name=display_name,
        source_packages=["./src/adk_agent"],
        entrypoint_module="adk_agent.agent_engine_app",
        entrypoint_object="agent_engine",
        class_methods=[],
        env_vars={"FOO": "BAR"},
        service_account=service_account,
        requirements_file=requirements_file,
        staging_bucket=f"gs://{bucket_name}",
        agent_framework="google-adk",
    )
    
    try:
        remote_agent = client.agent_engines.update(
            name=agents[display_name], config=config
        )
        print("Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        if hasattr(e, 'response'):
            print(e.response.text)
        elif hasattr(e, 'message'):
            print(e.message)

if __name__ == "__main__":
    main()
