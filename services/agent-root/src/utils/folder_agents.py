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
import sys
import logging
import importlib.util
from typing import List
from google.adk.agents import Agent

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import common_logging as logs

log = logs.get_logger('MyAdkLogger', logging.INFO)

def get_folder_agents() -> List[Agent]:
    """
    Dynamically discovers and loads agents from subdirectories in the 'agents' folder.
    """
    folder_agents = []
    agents_dir = os.path.join(os.path.dirname(__file__), '..', 'agents')

    if not os.path.isdir(agents_dir):
        log.warning(f"Agents directory not found at: {agents_dir}")
        return []

    for agent_name in os.listdir(agents_dir):
        agent_dir = os.path.join(agents_dir, agent_name)
        agent_file = os.path.join(agent_dir, 'agent.py')

        if os.path.isdir(agent_dir) and os.path.isfile(agent_file):
            try:
                spec = importlib.util.spec_from_file_location(f"agents.{agent_name}.agent", agent_file)
                agent_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(agent_module)

                if hasattr(agent_module, 'create_agent') and callable(agent_module.create_agent):
                    agent_instance = agent_module.create_agent()
                    folder_agents.append(agent_instance)
                    log.info(f"Successfully loaded agent: {agent_name}")
                else:
                    log.warning(f"Agent module at {agent_file} does not have a create_agent function.")
            except Exception as e:
                log.error(f"Failed to load agent from {agent_dir}: {e}")

    return folder_agents
