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

# Service base environment variables
. ./scripts/dev/base_env_nextjs.sh

# Service integrated secrets remappings
. ./scripts/dev/base_secrets_nextjs.sh

# Combine into single string
env_vars="${nextjs_secret_string} ${nextjs_envvar_string}"

# Entry-point
npx concurrently "${env_vars} next dev -p ${LOCAL_SERVICE_PORT}"
