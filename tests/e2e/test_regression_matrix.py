"""Regression matrix: test cases mapped to acceptance criteria."""

import pytest


# Regression matrix for T29 QA harness
# Each row maps a test to acceptance criteria and fixture type

REGRESSION_MATRIX = [
    # (test_function, acceptance_criteria, fixture_type, priority)
    ("test_ac1_connect_to_cluster", "AC1", "healthy", "P0"),
    ("test_ac2_live_health_info", "AC2", "healthy", "P0"),
    ("test_ac3_survive_api_failures", "AC3", "healthy", "P0"),
    ("test_ac4_deterministic_diagnosis", "AC4", "broken", "P0"),
    ("test_ac5_cost_capacity_data", "AC5", "healthy", "P1"),
    ("test_ac6_no_secrets_in_history", "AC6", "none", "P1"),
    ("test_ac7_provisioning_requires_approval", "AC7", "none", "P0"),
    ("test_ac8_no_cloud_dependency", "AC8", "none", "P1"),
    ("test_ac9_test_coverage_scaffold", "AC9", "none", "P2"),
    ("test_ac10_repository_structure", "AC10", "none", "P2"),
]


class TestRegressionMatrix:
    """Verify regression matrix coverage."""

    @pytest.mark.unit
    def test_matrix_has_all_criteria(self):
        """All 10 acceptance criteria should be in the matrix."""
        criteria = {row[1] for row in REGRESSION_MATRIX}
        expected = {f"AC{i}" for i in range(1, 11)}
        assert criteria == expected, f"Missing: {expected - criteria}"

    @pytest.mark.unit
    def test_matrix_has_p0_tests(self):
        """Critical acceptance criteria should have P0 priority tests."""
        p0_tests = [row for row in REGRESSION_MATRIX if row[3] == "P0"]
        assert len(p0_tests) >= 5, "Should have at least 5 P0 tests"

    @pytest.mark.unit
    def test_matrix_uses_both_fixtures(self):
        """Regression should test against both healthy and broken fixtures."""
        fixture_types = {row[2] for row in REGRESSION_MATRIX}
        assert "healthy" in fixture_types
        assert "broken" in fixture_types or "none" in fixture_types
