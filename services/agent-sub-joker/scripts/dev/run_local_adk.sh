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
. ./scripts/dev/base_env.sh

# Service integrated secrets remappings
. ./scripts/dev/base_secrets.sh

PID_FILE=./build/.run_local.pid
LOG_FILE=./build/adk_web_local.log

# Entry-point
if [ "$1" == "--background" ]; then
  ./venv/bin/adk web > $LOG_FILE 2>&1 &
  echo $! > $PID_FILE
else
  ./venv/bin/adk web
fi
