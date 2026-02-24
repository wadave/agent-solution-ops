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

# Monkey patch for ModelArmorSafetyFilterPlugin
try:
    from safety_plugins.plugins.model_armor import ModelArmorSafetyFilterPlugin
    from google.api_core.client_options import ClientOptions
    from google.cloud import modelarmor_v1
    import os
    import logging

    def _patched_model_armor_init(self, **kwargs):
        # Call super with name as a positional argument
        super(ModelArmorSafetyFilterPlugin, self).__init__("ModelArmorPlugin")

        # The rest of the original __init__ logic.
        project_id = kwargs.get("project_id", os.environ.get("GOOGLE_CLOUD_PROJECT", ""))
        location_id = kwargs.get("location_id", os.environ.get("GOOGLE_CLOUD_LOCATION", ""))
        template_id = kwargs.get("template_id", os.environ.get("MODEL_ARMOR_TEMPLATE_ID", ""))

        self._project_id = project_id
        self._location_id = location_id
        self._template_id = template_id
        self._model_armor_url = f"projects/{self._project_id}/locations/{self._location_id}/templates/{self._template_id}"
        self._client = modelarmor_v1.ModelArmorClient(
            client_options=ClientOptions(
                api_endpoint=f"modelarmor.{self._location_id}.rep.googleapis.com"
            ),
        )

    ModelArmorSafetyFilterPlugin.__init__ = _patched_model_armor_init
    logging.info("Successfully applied REVISED monkey patch to ModelArmorSafetyFilterPlugin.")

except ImportError:
    logging.warning("ModelArmorSafetyFilterPlugin not found, skipping monkey patch.")


