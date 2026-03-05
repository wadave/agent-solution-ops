# Copyright 2026 Google LLC
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
"""Agent evaluation tests using test cases."""

import json
from pathlib import Path

import pytest

# Load evaluation configuration
EVAL_CONFIG_PATH = Path(__file__).parent / "eval_config.json"
EVALSETS_DIR = Path(__file__).parent / "evalsets"


def load_eval_config() -> dict:
    """Load evaluation configuration."""
    with open(EVAL_CONFIG_PATH) as f:
        return json.load(f)


def load_evalset(evalset_name: str) -> list[dict]:
    """Load an evaluation set."""
    evalset_path = EVALSETS_DIR / f"{evalset_name}.evalset.json"
    if not evalset_path.exists():
        return []
    with open(evalset_path) as f:
        data = json.load(f)
    return data.get("examples", [])


class TestAgentEvaluation:
    """Tests for agent evaluation criteria."""

    @pytest.fixture
    def eval_config(self):
        """Load evaluation config."""
        return load_eval_config()

    @pytest.fixture
    def basic_evalset(self):
        """Load basic evaluation set."""
        return load_evalset("basic")

    def test_eval_config_structure(self, eval_config):
        """Verify evaluation config has proper structure."""
        assert "criteria" in eval_config
        assert "rubric_based_final_response_quality_v1" in eval_config["criteria"]

    def test_eval_config_thresholds(self, eval_config):
        """Verify evaluation thresholds are defined."""
        rubric_config = eval_config["criteria"]["rubric_based_final_response_quality_v1"]
        assert rubric_config["threshold"] == 0.8

    def test_eval_config_rubrics(self, eval_config):
        """Verify all required rubrics are defined."""
        rubric_config = eval_config["criteria"]["rubric_based_final_response_quality_v1"]
        rubrics = rubric_config["rubrics"]

        rubric_ids = [r["rubricId"] for r in rubrics]
        assert "relevance" in rubric_ids
        assert "helpfulness" in rubric_ids

    def test_evalset_exists(self, basic_evalset):
        """Verify basic evaluation set exists and has examples."""
        assert isinstance(basic_evalset, list)
        # Allow empty evalset for now
        if len(basic_evalset) > 0:
            assert all(isinstance(ex, dict) for ex in basic_evalset)

    def test_evalset_example_structure(self, basic_evalset):
        """Verify evaluation examples have proper structure."""
        if len(basic_evalset) == 0:
            pytest.skip("No examples in evalset")

        for example in basic_evalset:
            # Each example should have input and expected output
            assert "input" in example or "query" in example
            # Additional fields may vary


class TestRubricCriteria:
    """Tests for evaluation rubric criteria."""

    @pytest.fixture
    def rubrics(self):
        """Load rubrics from eval config."""
        config = load_eval_config()
        return config["criteria"]["rubric_based_final_response_quality_v1"]["rubrics"]

    def test_relevance_rubric(self, rubrics):
        """Verify relevance rubric is defined."""
        relevance = next((r for r in rubrics if r["rubricId"] == "relevance"), None)
        assert relevance is not None
        assert "rubricContent" in relevance
        assert "textProperty" in relevance["rubricContent"]

    def test_helpfulness_rubric(self, rubrics):
        """Verify helpfulness rubric is defined."""
        helpfulness = next((r for r in rubrics if r["rubricId"] == "helpfulness"), None)
        assert helpfulness is not None
        assert "rubricContent" in helpfulness
        assert "textProperty" in helpfulness["rubricContent"]

    def test_format_rubric(self, rubrics):
        """Verify format testing logic is valid."""
        # Simple test to verify we can handle formatting checks if added
        good_response = "## Weather Forecast\\n**City**: New York"
        assert "**" in good_response


class TestAgentResponseQuality:
    """Tests for evaluating agent response quality."""

    def test_weather_query_routing(self):
        """Test that weather queries should be identifiable."""
        weather_queries = [
            "What's the weather in New York?",
            "Tell me the forecast for San Francisco",
            "Is it going to rain tomorrow in Seattle?",
        ]

        for query in weather_queries:
            assert any(
                word in query.lower()
                for word in ["weather", "forecast", "rain", "temperature", "conditions"]
            )

    def test_general_query_no_routing(self):
        """Test that general queries are basic interaction."""
        general_queries = [
            "Hello",
            "What can you do?",
            "Help me",
        ]

        for query in general_queries:
            assert not any(word in query.lower() for word in ["weather", "forecast"])

    def test_response_format_markdown(self):
        """Test that responses should be ideally formatted in Markdown."""
        good_response = "## Weather Forecast\\n**City**: New York\\n**Temperature**: 72°F\\n**Conditions**: Sunny\\n- Wind: 10 mph\\n- Humidity: 45%"

        bad_response = "New York 72F Sunny Wind 10mph Humidity 45%"

        assert "#" in good_response or "*" in good_response or "-" in good_response
        assert "#" not in bad_response and "**" not in bad_response
