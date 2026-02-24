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

import sys
import os
import toml
import importlib

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_plugins_from_toml(env: str = "live"):
    """
    Loads and instantiates ADK plugins from the pyproject.toml file for a specific environment.
    
    Args:
        env: The environment ('dev', 'live', 'test') for which to load plugins.
    """
    active_adk_plugins = []
    try:
        # Construct the path to pyproject.toml assuming it's in the root of the service
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        toml_path = os.path.join(base_dir, 'pyproject.toml')
        
        with open(toml_path, "r") as f:
            data = toml.load(f)
            plugin_paths = data.get("tool", {}).get("agent", {}).get("plugins", {}).get(env, [])
            
            for plugin_path in plugin_paths:
                try:
                    module_path, class_name = plugin_path.rsplit('.', 1)
                    module = importlib.import_module(module_path)
                    plugin_class = getattr(module, class_name)
                    active_adk_plugins.append(plugin_class())
                except (ImportError, AttributeError, ValueError) as e:
                    print(f"Error loading plugin '{plugin_path}' for env '{env}': {e}", file=sys.stderr)
                    
    except FileNotFoundError:
        print(f"Warning: pyproject.toml not found at '{toml_path}'. No plugins loaded.", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred while loading plugins: {e}", file=sys.stderr)
        
    return active_adk_plugins

active_adk_plugins = load_plugins_from_toml(env="live")
