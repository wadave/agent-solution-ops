# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for core application components."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from adk_agent.app_utils.typing import Feedback


class TestFeedbackModel:
    def test_valid_integer_score(self):
        fb = Feedback(score=5, text="Great!")
        assert fb.score == 5
        assert fb.text == "Great!"
        assert fb.log_type == "feedback"
        assert fb.service_name == "agents-solution-ops"

    def test_valid_float_score(self):
        fb = Feedback(score=4.5)
        assert fb.score == 4.5

    def test_text_defaults_to_empty_string(self):
        fb = Feedback(score=3)
        assert fb.text == ""

    def test_auto_generated_ids_are_unique(self):
        fb1 = Feedback(score=1)
        fb2 = Feedback(score=1)
        assert fb1.user_id != fb2.user_id
        assert fb1.session_id != fb2.session_id

    def test_model_dump_contains_expected_keys(self):
        fb = Feedback(score=5, text="ok")
        data = fb.model_dump()
        assert set(data.keys()) == {
            "score",
            "text",
            "log_type",
            "service_name",
            "user_id",
            "session_id",
        }

    def test_invalid_score_type_raises(self):
        with pytest.raises(ValidationError):
            Feedback(score="not-a-number")  # type: ignore


class TestGetAccessToken:
    """Tests for get_access_token() with mock contexts — no network calls."""

    def _make_context(self, session_state: dict | None = None, **attrs) -> MagicMock:
        ctx = MagicMock()
        if session_state is not None:
            ctx.session.state = session_state
        else:
            del ctx.session
        ctx.state = attrs.get("state", None)
        ctx.auth_token = attrs.get("auth_token", None)
        ctx.credentials = attrs.get("credentials", None)
        return ctx

    def test_returns_token_by_exact_auth_id(self):
        from adk_agent.agent import get_access_token

        ctx = self._make_context({"my-auth-id": "a" * 30})
        assert get_access_token(ctx, "my-auth-id") == "a" * 30

    def test_returns_token_by_prefix_match(self):
        from adk_agent.agent import get_access_token

        ctx = self._make_context({"my-auth-id_extra": "b" * 30})
        assert get_access_token(ctx, "my-auth-id") == "b" * 30

    def test_returns_token_by_suffix_match(self):
        from adk_agent.agent import get_access_token

        ctx = self._make_context({"prefix/my-auth-id": "c" * 30})
        assert get_access_token(ctx, "my-auth-id") == "c" * 30

    def test_returns_none_when_no_match(self):
        from adk_agent.agent import get_access_token

        ctx = self._make_context({"other-key": "c" * 30})
        assert get_access_token(ctx, "my-auth-id") is None

    def test_rejects_short_tokens(self):
        from adk_agent.agent import MIN_TOKEN_LENGTH, get_access_token

        short_token = "x" * (MIN_TOKEN_LENGTH - 1)
        ctx = self._make_context({"my-auth-id": short_token})
        assert get_access_token(ctx, "my-auth-id") is None

    def test_fallback_to_context_state(self):
        from adk_agent.agent import get_access_token

        ctx = self._make_context(session_state=None, state={"my-auth-id": "d" * 30})
        assert get_access_token(ctx, "my-auth-id") == "d" * 30

    def test_fallback_to_auth_token(self):
        from adk_agent.agent import get_access_token

        ctx = self._make_context(session_state=None, auth_token={"my-auth-id": "e" * 30})
        assert get_access_token(ctx, "my-auth-id") == "e" * 30

    def test_fallback_to_credentials(self):
        from adk_agent.agent import get_access_token

        creds = MagicMock()
        creds.token = "f" * 30
        ctx = self._make_context(session_state=None, credentials=creds)
        assert get_access_token(ctx, "my-auth-id") == "f" * 30


class TestMcpHeaderProvider:
    """Tests for mcp_header_provider() — no network calls."""

    def test_returns_bearer_header(self):
        from adk_agent.agent import mcp_header_provider

        ctx = MagicMock()
        ctx.session.state = {"test-auth-id": "t" * 30}
        with patch("adk_agent.agent.AGENTSPACE_AUTH_ID", "test-auth-id"):
            result = mcp_header_provider(ctx)
        assert result == {"Authorization": f"Bearer {'t' * 30}"}

    def test_returns_empty_dict_when_no_token(self):
        from adk_agent.agent import mcp_header_provider

        ctx = MagicMock()
        ctx.session.state = {}
        ctx.state = None
        ctx.auth_token = None
        ctx.credentials = None
        with patch("adk_agent.agent.AGENTSPACE_AUTH_ID", "test-auth-id"):
            result = mcp_header_provider(ctx)
        assert result == {}


class TestSetupTelemetry:
    """Tests for setup_telemetry() — verifies env var configuration."""

    def test_enables_telemetry_env_var(self):
        from adk_agent.app_utils.telemetry import setup_telemetry

        with patch.dict("os.environ", {}, clear=True):
            setup_telemetry()
            import os

            assert os.environ["GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY"] == "true"

    def test_sets_otel_vars_when_bucket_and_capture_enabled(self):
        from adk_agent.app_utils.telemetry import setup_telemetry

        env = {
            "LOGS_BUCKET_NAME": "my-bucket",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
        }
        with patch.dict("os.environ", env, clear=True):
            result = setup_telemetry()
            import os

            assert result == "my-bucket"
            assert os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] == "NO_CONTENT"
            assert "gs://my-bucket/" in os.environ["OTEL_INSTRUMENTATION_GENAI_UPLOAD_BASE_PATH"]

    def test_returns_none_when_no_bucket(self):
        from adk_agent.app_utils.telemetry import setup_telemetry

        with patch.dict("os.environ", {}, clear=True):
            result = setup_telemetry()
            assert result is None
