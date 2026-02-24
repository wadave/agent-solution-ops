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

import toml
import sys

def get_plugins_from_toml(file_path: str, env: str) -> str:
    """
    Reads a pyproject.toml file and extracts the plugins listed under
    the [tool.agent.plugins] section for a specific environment.

    Args:
        file_path: Path to the pyproject.toml file.
        env: The environment (e.g., 'dev', 'live', 'test').

    Returns:
        A comma-separated string of plugins.
    """
    with open(file_path, "r") as f:
        data = toml.load(f)
        plugins = data.get("tool", {}).get("agent", {}).get("plugins", {}).get(env, [])
        return ",".join(plugins)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        print(get_plugins_from_toml(sys.argv[1], sys.argv[2]))
    else:
        print("Usage: python _read_toml_plugins.py <path_to_pyproject.toml> <env>")
        sys.exit(1)
