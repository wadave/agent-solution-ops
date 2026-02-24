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

#!/bin/bash

# Adds all private SSH keys from ~/.ssh to the ssh-agent within the DevContainer.

echo "Adding SSH keys from ~/.ssh..."

# Loop through all files in ~/.ssh
for key_file in ~/.ssh/*; do
  filename=$(basename "$key_file")
  # Check if the file is a regular file and does not end with .pub
  if [[ -f "$key_file" && "$key_file" != *.pub && "$filename" != "known_hosts"* ]]; then

    echo "  - Attempting to add key: $filename"

    # Try to add the key; suppress errors for invalid key files
    # The '|| true' part ensures the script doesn't fail if a file is not a valid key
    ssh-add "$key_file" 2>/dev/null || true
  fi
done

echo "Finished adding keys."
