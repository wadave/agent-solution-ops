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
import toml

if len(sys.argv) < 2:
    print("Usage: python script.py <path_to_pyproject.toml>")
    sys.exit(1)

file_path = sys.argv[1]

try:
    with open(file_path, "r") as f:
        data = toml.load(f)

    dependencies = data.get("project", {}).get("dependencies", [])

    if dependencies:
        for dep in dependencies:
            print(dep)
    else:
        print("")

except FileNotFoundError:
    print(f"Error: The file '{file_path}' was not found.")
    sys.exit(1)
except Exception as e:
    print(f"Error parsing '{file_path}': {e}")
    sys.exit(1)
