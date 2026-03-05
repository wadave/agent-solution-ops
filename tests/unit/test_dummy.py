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

from unittest.mock import MagicMock

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

    def _make_context(self, state: dict) -> MagicMock:
        ctx = MagicMock()
        ctx.session.state = state
        ctx.state = None
        ctx.auth_token = None
        ctx.credentials = None
        return ctx

    def test_returns_token_by_exact_auth_id(self):
        from adk_agent.agent import get_access_token

        ctx = self._make_context({"my-auth-id": "a" * 30})
        assert get_access_token(ctx, "my-auth-id") == "a" * 30

    def test_returns_token_by_prefix_match(self):
        from adk_agent.agent import get_access_token

        ctx = self._make_context({"my-auth-id_extra": "b" * 30})
        assert get_access_token(ctx, "my-auth-id") == "b" * 30

    def test_returns_none_when_no_match(self):
        from adk_agent.agent import get_access_token

        ctx = self._make_context({"other-key": "c" * 30})
        assert get_access_token(ctx, "my-auth-id") is None
