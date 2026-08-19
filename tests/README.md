# Test package — OpenSearch Guardian QA Harness
# T29 deliverable
#
# Layers:
#   tests/unit/        — Pure unit tests, no Docker, no network
#   tests/integration/ — Requires OpenSearch fixture (Docker)
#   tests/e2e/         — Full regression over acceptance criteria
#   tests/fixtures/    — Test data / JSON fixtures
#   tests/conftest.py  — Shared fixtures
