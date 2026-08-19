"""
Unit tests for the Security & Safety Engine dry-run engine.
Tests dry-run execution and diff generation.
"""

import pytest
import asyncio
from guardian.safety.dryrun_engine import DryRunEngine, DiffResult


class TestDryRunEngine:
    """Tests for DryRunEngine."""

    @pytest.fixture
    def engine(self):
        return DryRunEngine()

    @pytest.mark.asyncio
    async def test_node_add_dry_run(self, engine):
        """Test dry-run for node-add operation."""
        current_state = {
            "nodes": [
                {"node_id": "node-1", "role": "master"},
                {"node_id": "node-2", "role": "data"}
            ],
            "cluster_stats": {"total_nodes": 2}
        }

        parameters = {
            "role": "data",
            "ip_address": "10.0.0.4"
        }

        result = await engine.execute_dry_run(
            operation_type="node-add",
            target_resource="node-3",
            parameters=parameters,
            current_state=current_state
        )

        assert isinstance(result, DiffResult)
        assert result.operation_type == "node-add"
        assert result.target_resource == "node-3"
        assert "before" in str(result.before_snapshot)
        assert "after" in str(result.after_snapshot)

        # Verify changes summary
        assert "changes" in result.changes_summary
        assert "node_count" in str(result.changes_summary["changes"])

        # Verify risk assessment
        assert "risk" in result.risk_assessment.lower()

    @pytest.mark.asyncio
    async def test_node_remove_dry_run(self, engine):
        """Test dry-run for node-remove operation."""
        current_state = {
            "nodes": [
                {"node_id": "node-1", "role": "master"},
                {"node_id": "node-2", "role": "data"}
            ],
            "cluster_stats": {"total_nodes": 2}
        }

        result = await engine.execute_dry_run(
            operation_type="node-remove",
            target_resource="node-2",
            parameters={},
            current_state=current_state
        )

        assert isinstance(result, DiffResult)
        assert result.operation_type == "node-remove"

    @pytest.mark.asyncio
    async def test_index_create_dry_run(self, engine):
        """Test dry-run for index-create operation."""
        current_state = {
            "indices": [
                {"index_name": "existing-index", "status": "green"}
            ]
        }

        parameters = {
            "number_of_shards": 5,
            "number_of_replicas": 1
        }

        result = await engine.execute_dry_run(
            operation_type="index-create",
            target_resource="new-index",
            parameters=parameters,
            current_state=current_state
        )

        assert isinstance(result, DiffResult)
        assert result.operation_type == "index-create"
        assert "index_count" in str(result.changes_summary["changes"])

    @pytest.mark.asyncio
    async def test_index_delete_dry_run(self, engine):
        """Test dry-run for index-delete operation."""
        current_state = {
            "indices": [
                {"index_name": "index-to-delete", "status": "green"},
                {"index_name": "index-to-keep", "status": "green"}
            ]
        }

        result = await engine.execute_dry_run(
            operation_type="index-delete",
            target_resource="index-to-delete",
            parameters={},
            current_state=current_state
        )

        assert isinstance(result, DiffResult)
        assert result.operation_type == "index-delete"

    @pytest.mark.asyncio
    async def test_docker_compose_up_dry_run(self, engine):
        """Test dry-run for docker-compose-up operation."""
        current_state = {
            "docker_services": []
        }

        parameters = {
            "service": {
                "image": "opensearchproject/opensearch:latest",
                "ports": ["9200:9200"]
            }
        }

        result = await engine.execute_dry_run(
            operation_type="docker-compose-up",
            target_resource="opensearch",
            parameters=parameters,
            current_state=current_state
        )

        assert isinstance(result, DiffResult)
        assert result.operation_type == "docker-compose-up"

    @pytest.mark.asyncio
    async def test_k8s_scale_up_dry_run(self, engine):
        """Test dry-run for k8s-scale-up operation."""
        current_state = {
            "k8s_deployments": [
                {
                    "name": "opensearch",
                    "replicas": 3,
                    "image": "opensearchproject/opensearch:2.11"
                }
            ]
        }

        parameters = {"replica_count": 2}

        result = await engine.execute_dry_run(
            operation_type="k8s-scale-up",
            target_resource="opensearch",
            parameters=parameters,
            current_state=current_state
        )

        assert isinstance(result, DiffResult)
        assert result.operation_type == "k8s-scale-up"

    def test_risk_assessment_for_high_risk_operations(self, engine):
        """Test risk assessment for high-risk operations."""
        changes_summary = {"changes": []}

        risk = engine._assess_risk(
            "index-delete",
            changes_summary,
            {}
        )

        assert "HIGH" in risk or "high" in risk.lower()

    def test_risk_assessment_for_medium_risk_operations(self, engine):
        """Test risk assessment for medium-risk operations."""
        changes_summary = {"changes": []}

        risk = engine._assess_risk(
            "node-add",
            changes_summary,
            {}
        )

        assert "MEDIUM" in risk or "medium" in risk.lower()

    def test_risk_assessment_for_low_risk_operations(self, engine):
        """Test risk assessment for low-risk operations."""
        changes_summary = {"changes": []}

        risk = engine._assess_risk(
            "cluster-health",
            changes_summary,
            {}
        )

        assert "LOW" in risk or "low" in risk.lower()

    def test_diff_result_structure(self, engine):
        """Test that DiffResult has the expected structure."""
        diff = DiffResult(
            operation_type="test",
            target_resource="test-resource",
            before_snapshot={"key": "value"},
            after_snapshot={"key": "new-value"},
            changes_summary={"changes": []},
            risk_assessment="LOW"
        )

        assert diff.operation_type == "test"
        assert diff.target_resource == "test-resource"
        assert hasattr(diff, "before_snapshot")
        assert hasattr(diff, "after_snapshot")
        assert hasattr(diff, "changes_summary")
        assert hasattr(diff, "risk_assessment")
        assert hasattr(diff, "timestamp")
        assert hasattr(diff, "diff_id")
        assert len(diff.diff_id) > 0
