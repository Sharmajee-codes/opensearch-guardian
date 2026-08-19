"""Unit tests for DryRunEngine."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from guardian.safety.dryrun_engine import DryRunEngine, DiffResult


@pytest.fixture
def dry_run_engine():
    return DryRunEngine()


class TestDiffResult:
    """Tests for DiffResult dataclass."""

    def test_defaults(self):
        result = DiffResult(
            operation_type="test",
            target_resource="res",
            before_snapshot={"a": 1},
            after_snapshot={"a": 2},
            changes_summary={},
            risk_assessment="low",
        )
        assert isinstance(result.timestamp, __import__("datetime").datetime)
        assert len(result.diff_id) == 16

    def test_has_required_fields(self):
        result = DiffResult(
            operation_type="op",
            target_resource="res",
            before_snapshot={},
            after_snapshot={},
            changes_summary={},
            risk_assessment="medium",
        )
        assert result.operation_type == "op"
        assert result.target_resource == "res"


class TestDryRunEngine:
    """Tests for DryRunEngine."""

    @pytest.mark.asyncio
    async def test_execute_dry_run_returns_diff_result(self, dry_run_engine):
        """Dry run should return a DiffResult with all required fields."""
        current_state = {
            "nodes": [{"name": "node-1", "roles": ["master"]}],
            "cluster": {"health": "green"},
        }
        with patch.object(dry_run_engine, '_capture_snapshot', new_callable=AsyncMock) as mock_capture, \
             patch.object(dry_run_engine, '_simulate_operation', new_callable=AsyncMock) as mock_simulate, \
             patch.object(dry_run_engine, '_generate_changes_summary', return_value={}) as mock_changes, \
             patch.object(dry_run_engine, '_assess_risk', return_value="low") as mock_risk:

            mock_capture.side_effect = [current_state, current_state]
            mock_simulate.return_value = current_state

            result = await dry_run_engine.execute_dry_run(
                operation_type="index-create",
                target_resource="test-index",
                parameters={"settings": {}},
                current_state=current_state,
            )

            assert isinstance(result, DiffResult)
            assert result.operation_type == "index-create"
            assert result.target_resource == "test-index"
            mock_capture.assert_called()
            mock_simulate.assert_called_once()
            mock_changes.assert_called_once()
            mock_risk.assert_called_once()

    @pytest.mark.asyncio
    async def test_dry_run_changes_summary(self, dry_run_engine):
        """Verify changes summary is generated from before/after snapshots."""
        before = {"shards": 5}
        after = {"shards": 10}

        with patch.object(dry_run_engine, '_capture_snapshot', new_callable=AsyncMock, side_effect=[before, after]), \
             patch.object(dry_run_engine, '_simulate_operation', new_callable=AsyncMock, return_value=after), \
             patch.object(dry_run_engine, '_generate_changes_summary', return_value={"shard_change": 5}) as mock_gen, \
             patch.object(dry_run_engine, '_assess_risk', return_value="medium"):

            result = await dry_run_engine.execute_dry_run(
                operation_type="index-update-settings",
                target_resource="test",
                parameters={"number_of_shards": 10},
                current_state=before,
            )

            assert result.changes_summary == {"shard_change": 5}
            mock_gen.assert_called_once_with(before, after, "index-update-settings")

    @pytest.mark.asyncio
    async def test_dry_run_risk_assessment(self, dry_run_engine):
        """Verify risk assessment is called with correct parameters."""
        current_state = {"nodes": 1}
        risk_level = "high"

        with patch.object(dry_run_engine, '_capture_snapshot', new_callable=AsyncMock, side_effect=[current_state, current_state]), \
             patch.object(dry_run_engine, '_simulate_operation', new_callable=AsyncMock, return_value=current_state), \
             patch.object(dry_run_engine, '_generate_changes_summary', return_value={}), \
             patch.object(dry_run_engine, '_assess_risk', return_value=risk_level) as mock_risk:

            result = await dry_run_engine.execute_dry_run(
                operation_type="node-add",
                target_resource="new-node",
                parameters={"role": "data"},
                current_state=current_state,
            )

            assert result.risk_assessment == risk_level
            mock_risk.assert_called_once()
            args, kwargs = mock_risk.call_args
            assert args[0] == "node-add"
            assert args[2] == {"role": "data"}
