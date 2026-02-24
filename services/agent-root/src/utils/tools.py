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
from google.adk.tools import ToolContext

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common_gcp import oauth

def search_id_token(key: str, tool_context: ToolContext):
    id_token = tool_context.state.get(f"temp:{key}")
    id_token = id_token if id_token else tool_context.state.get(f"{key}", oauth.get_default_access_token())
    return id_token
