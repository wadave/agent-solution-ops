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

.PHONY: help lint format test test-unit test-integration run-local

help:
	@echo "Available targets:"
	@echo "  lint              Check code style with ruff"
	@echo "  format            Auto-format code with ruff"
	@echo "  test              Run all tests (unit + integration)"
	@echo "  test-unit         Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  run-local         Start full local stack with Docker Compose"

lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format:
	uv run ruff format src/ tests/

test:
	uv run pytest tests/

test-unit:
	uv run pytest tests/unit

test-integration:
	uv run pytest tests/integration

run-local:
	docker compose up
