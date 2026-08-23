"""Validation tests for RuleBasedPlanner deterministic planning engine.

Tests the RuleBasedPlanner that composes plan and capacity findings from
deterministic rules without LLM involvement.
"""

import pytest
from datetime import UTC, datetime
from unittest.mock import Mock

from guardian.planner import (
    PlanAction,
    PlanRule,
    PlannedAction,
    RuleBasedPlan,
    RuleBasedPlanner,
)
from guardian.planner.planner import (
    CapacityPlanner,
    ProjectionConfig,
    ProjectionWindow,
    SizingRecommendation,
    UtilizationProjection,
)
from guardian.optimizer import OptimizationEngine, OptimizerConfig
from guardian.models import (
    CollectionResult,
    ClusterSnapshot,
    IndexSnapshot,
    NodeSnapshot,
    JvmSnapshot,
    OsSnapshot,
    ProcessSnapshot,
    FilesystemSnapshot,
    ThreadPoolSnapshot,
)


def test_rule_based_planner_initialization():
    """Test RuleBasedPlanner initializes with default rules."""
    planner = RuleBasedPlanner()

    assert isinstance(planner, RuleBasedPlanner)
    assert len(planner._rules) > 0
    assert any(rule.name == "critical_capacity" for rule in planner._rules)
    assert any(rule.name == "no_action" for rule in planner._rules)


def test_rule_based_planner_with_config():
    """Test RuleBasedPlanner initialization with custom configs."""
    from guardian.planner.planner import GrowthRate

    config = ProjectionConfig(
        default_window=ProjectionWindow.ONE_MONTH,
        growth_method=GrowthRate.EXPONENTIAL,
        min_history_points=5,
    )
    optimizer_config = OptimizerConfig()

    planner = RuleBasedPlanner(
        config=config,
        optimizer_config=optimizer_config,
    )

    assert planner.config.default_window == ProjectionWindow.ONE_MONTH
    assert planner.config.growth_method == GrowthRate.EXPONENTIAL
    assert planner.config.min_history_points == 5


def test_plan_action_enum():
    """Test PlanAction enum values."""
    assert PlanAction.SCALE_UP.value == "scale_up"
    assert PlanAction.SCALE_DOWN.value == "scale_down"
    assert PlanAction.RIGHT_SIZE.value == "right_size"
    assert PlanAction.RECLAIM_STORAGE.value == "reclaim_storage"
    assert PlanAction.OPTIMIZE_SHARDS.value == "optimize_shards"
    assert PlanAction.OPTIMIZE_REPLICAS.value == "optimize_replicas"
    assert PlanAction.OPTIMIZE_MAPPINGS.value == "optimize_mappings"
    assert PlanAction.CAPACITY_RECOVERY.value == "capacity_recovery"
    assert PlanAction.NO_ACTION.value == "no_action"


def test_planned_action_creation():
    """Test PlannedAction dataclass creation."""
    action = PlannedAction(
        action=PlanAction.SCALE_UP,
        summary="Test scale-up action",
        rationale=["Reason 1", "Reason 2"],
        safety_tier="APPROVAL_REQUIRED",
        priority=10,
        estimated_impact="Scale from 3 to 5 nodes",
        confidence=0.85,
    )

    assert action.action == PlanAction.SCALE_UP
    assert action.summary == "Test scale-up action"
    assert action.rationale == ["Reason 1", "Reason 2"]
    assert action.safety_tier == "APPROVAL_REQUIRED"
    assert action.priority == 10
    assert action.estimated_impact == "Scale from 3 to 5 nodes"
    assert action.confidence == 0.85
    assert isinstance(action.recommended_at, datetime)


def test_rule_based_plan_creation():
    """Test RuleBasedPlan dataclass creation."""
    plan_action = PlannedAction(
        action=PlanAction.SCALE_UP,
        summary="Test action",
        rationale=["Test rationale"],
        safety_tier="APPROVAL_REQUIRED",
        priority=5,
        estimated_impact="Test impact",
        confidence=0.9,
    )

    plan = RuleBasedPlan(
        plan_summary="Test plan summary",
        actions=[plan_action],
        capacity_projections=[{"resource": "cpu", "current_value": 0.5}],
        sizing_recommendation={"recommended_node_count": 5},
        optimizer_excerpt={"recommendations": []},
    )

    assert plan.plan_summary == "Test plan summary"
    assert len(plan.actions) == 1
    assert plan.actions[0].action == PlanAction.SCALE_UP
    assert plan.capacity_projections == [{"resource": "cpu", "current_value": 0.5}]
    assert plan.sizing_recommendation == {"recommended_node_count": 5}
    assert plan.optimizer_excerpt == {"recommendations": []}
    assert isinstance(plan.generated_at, datetime)
    assert plan.planner_version == "rule-based-v1"


def test_rule_based_plan_sorted_actions():
    """Test RuleBasedPlan sorted_actions method."""
    action1 = PlannedAction(
        action=PlanAction.SCALE_UP,
        summary="Low priority action",
        rationale=["Reason"],
        safety_tier="INFORMATIONAL",
        priority=50,
        estimated_impact="Low impact",
        confidence=0.5,
    )

    action2 = PlannedAction(
        action=PlanAction.SCALE_DOWN,
        summary="High priority action",
        rationale=["Reason"],
        safety_tier="APPROVAL_REQUIRED",
        priority=10,
        estimated_impact="High impact",
        confidence=0.8,
    )

    action3 = PlannedAction(
        action=PlanAction.RIGHT_SIZE,
        summary="Medium priority action",
        rationale=["Reason"],
        safety_tier="SAFE_REVERSIBLE",
        priority=25,
        estimated_impact="Medium impact",
        confidence=0.7,
    )

    plan = RuleBasedPlan(
        plan_summary="Test plan",
        actions=[action1, action2, action3],
        capacity_projections=[],
        sizing_recommendation={},
        optimizer_excerpt={},
    )

    sorted_actions = plan.sorted_actions()
    assert len(sorted_actions) == 3
    # Should be sorted by priority: action2 (10), action3 (25), action1 (50)
    assert sorted_actions[0].action == PlanAction.SCALE_DOWN
    assert sorted_actions[1].action == PlanAction.RIGHT_SIZE
    assert sorted_actions[2].action == PlanAction.SCALE_UP


def test_rule_based_plan_highest_priority_action():
    """Test RuleBasedPlan highest_priority_action method."""
    action1 = PlannedAction(
        action=PlanAction.SCALE_UP,
        summary="Low priority",
        rationale=["Reason"],
        safety_tier="INFORMATIONAL",
        priority=50,
        estimated_impact="Low",
        confidence=0.5,
    )

    action2 = PlannedAction(
        action=PlanAction.SCALE_DOWN,
        summary="High priority",
        rationale=["Reason"],
        safety_tier="APPROVAL_REQUIRED",
        priority=10,
        estimated_impact="High",
        confidence=0.8,
    )

    plan = RuleBasedPlan(
        plan_summary="Test plan",
        actions=[action1, action2],
        capacity_projections=[],
        sizing_recommendation={},
        optimizer_excerpt={},
    )

    highest = plan.highest_priority_action()
    assert highest is not None
    assert highest.action == PlanAction.SCALE_DOWN
    assert highest.priority == 10

    # Test with no actions
    empty_plan = RuleBasedPlan(
        plan_summary="Empty plan",
        actions=[],
        capacity_projections=[],
        sizing_recommendation={},
        optimizer_excerpt={},
    )

    assert empty_plan.highest_priority_action() is None


def create_mock_snapshot() -> CollectionResult:
    """Helper to create a mock CollectionResult for testing."""
    # Create a basic node snapshot
    node_snapshot = NodeSnapshot(
        node_id="test-node-1",
        node_name="test-node-1",
        host="test-node-1",
        ip="192.168.1.100",
        roles=["data", "master"],
        version="2.0.0",
        collected_at=datetime.now(UTC),
        jvm=JvmSnapshot(
            mem_heap_used_bytes=8 * (1024 ** 3),
            mem_heap_max_bytes=16 * (1024 ** 3),
            mem_heap_used_percent=50,
            mem_non_heap_used_bytes=512 * (1024 ** 2),
            gc_collectors_young_count=0,
            gc_collectors_young_time_ms=0,
            gc_collectors_old_count=0,
            gc_collectors_old_time_ms=0,
            buffer_pools_direct_count=0,
            buffer_pools_direct_used_bytes=0,
            buffer_pools_mapped_count=0,
            buffer_pools_mapped_used_bytes=0,
            uptime_ms=86400000,
        ),
        os=OsSnapshot(
            cpu_percent=65.0,
            load_average_1m=1.0,
            load_average_5m=1.0,
            load_average_15m=1.0,
            mem_total_bytes=32 * (1024 ** 3),
            mem_used_bytes=16 * (1024 ** 3),
            mem_free_bytes=16 * (1024 ** 3),
            mem_free_percent=50,
            mem_used_percent=50,
        ),
        process=ProcessSnapshot(
            cpu_percent=30.0,
            cpu_total_ms=10000,
            open_file_descriptors=100,
            max_file_descriptors=1000,
            mem_swap_used_bytes=0,
            mem_swap_max_bytes=0,
        ),
        thread_pools={},
        filesystems=[
            FilesystemSnapshot(
                total_bytes=1000 * (1024 ** 3),
                available_bytes=500 * (1024 ** 3),
                used_bytes=500 * (1024 ** 3),
                available_percent=50.0,
                disk_reads=100,
                disk_writes=50,
                disk_total_size_bytes=1000 * (1024 ** 3),
            )
        ],
    )

    # Create index snapshots
    index_snapshots = {
        "test-index-1": IndexSnapshot(
            index_name="test-index-1",
            uuid="test-uuid-1",
            collected_at=datetime.now(UTC),
            doc_count=500000,
            deleted_doc_count=5000,
            store_size_bytes=100 * (1024 ** 3),
            primary_size_bytes=50 * (1024 ** 3),
            number_of_shards=3,
            number_of_replicas=1,
            total_shards=5,
            search_query_total=500000,
            search_query_time_ms=25000,
            indexing_index_total=1000000,
            indexing_index_time_ms=50000,
            segment_count=10,
            segment_memory_bytes=1024 * 1024,
            refresh_interval_ms=1000,
            codec="lucene90",
            read_only=False,
            read_only_allow_delete=False,
            field_count=20,
            has_keyword_explosion=False,
            source_api="_stats",
            source_version="1.0",
            raw_response_hash="abc123",
        )
    }

    # Create cluster snapshot
    cluster_snapshot = ClusterSnapshot(
        snapshot_id="test-snap-1",
        cluster_name="test-cluster",
        collected_at=datetime.now(UTC),
        health_status="green",
        total_nodes=1,
        data_nodes=1,
        master_nodes=1,
        ingest_nodes=0,
        active_primary_shards=3,
        active_shards=5,
        relocating_shards=0,
        initializing_shards=0,
        unassigned_shards=0,
        delayed_unassigned_shards=0,
        pending_cluster_tasks=0,
        failed_cluster_tasks=0,
        source_api="_cluster/health",
        source_version="1.0",
        raw_response_hash="abc123",
    )

    # Create collection result
    return CollectionResult(
        node_snapshots={"test-node-1": node_snapshot},
        index_snapshots=index_snapshots,
        cluster_snapshot=cluster_snapshot,
        shard_states=[],
        collected_at=datetime.now(UTC),
        errors=[],
    )


def test_rule_based_planner_basic_plan():
    """Test basic plan generation with mock data."""
    planner = RuleBasedPlanner()

    # Create minimal mock snapshot
    mock_snapshot = create_mock_snapshot()

    # Generate plan
    plan = planner.plan(
        current_snapshot=mock_snapshot,
        historical_snapshots=[],  # No history for simplicity
        require_permission=False,  # Skip permission check for test
    )

    assert isinstance(plan, RuleBasedPlan)
    assert isinstance(plan.plan_summary, str)
    assert isinstance(plan.actions, list)
    assert isinstance(plan.capacity_projections, list)
    assert isinstance(plan.sizing_recommendation, dict)
    assert isinstance(plan.optimizer_excerpt, dict)
    assert isinstance(plan.generated_at, datetime)

    # Additional assertions to verify plan content
    assert len(plan.actions) >= 0  # Actions may be empty if no issues detected
    assert len(plan.capacity_projections) > 0  # Should have capacity projections
    assert "recommended_node_count" in plan.sizing_recommendation  # Should have node count recommendation
    assert "reclaimable_storage" in plan.optimizer_excerpt  # Should have optimizer findings


def test_rule_evaluation_critical_capacity():
    """Test rule evaluation for critical capacity scenario."""
    planner = RuleBasedPlanner()

    # Mock high projected utilization
    capacity_projections = [
        {
            "resource": "combined",
            "current_value": 0.7,
            "projected_value": 1.2,  # > 1.0 triggers critical capacity
            "growth_rate_per_day": 0.01,
            "window": "3m",
            "confidence": 0.8,
            "assumptions": ["Test assumption"],
        }
    ]

    sizing = {
        "current_node_count": 5,
        "recommended_node_count": 8,
        "confidence": 0.75,
        "reasoning": ["Test reasoning"],
        "assumptions": ["Test assumption"],
        "projection_window": "3m",
        "estimated_cost_change": "increase",
    }

    optimizer_excerpt = {
        "reclaimable_storage": [],
        "shard_reduction": [],
        "replica_optimization": [],
        "mapping_optimization": [],
        "capacity_recovery": [],
    }

    # Create minimal mock objects
    mock_snapshot = create_mock_snapshot()

    actions = planner._evaluate_rules(
        optimizer_excerpt=optimizer_excerpt,
        capacity_projections=capacity_projections,
        sizing=sizing,
        current_snapshot=mock_snapshot,
        historical_snapshots=[],
    )

    # Should have at least one action for critical capacity
    assert len(actions) >= 1
    critical_actions = [a for a in actions if a.action == PlanAction.SCALE_UP]
    assert len(critical_actions) >= 1
    assert critical_actions[0].safety_tier == "APPROVAL_REQUIRED"
    assert "Critical" in critical_actions[0].summary

    # Additional assertions to verify specific action details
    assert critical_actions[0].priority == 1  # Should have highest priority for critical capacity
    assert "Scale from 5 to 8 nodes" in critical_actions[0].estimated_impact  # Should show correct node scaling
    assert critical_actions[0].confidence == 0.75  # Should match sizing confidence


def test_rule_evaluation_reclaim_storage():
    """Test rule evaluation for reclaimable storage scenario."""
    planner = RuleBasedPlanner()

    # Mock reclaimable storage exceeding threshold
    optimizer_excerpt = {
        "reclaimable_storage": [
            {"reclaimable_bytes": 150 * (1024 ** 3)},  # 150 GB
        ],
        "shard_reduction": [],
        "replica_optimization": [],
        "mapping_optimization": [],
        "capacity_recovery": [],
    }

    capacity_projections = [
        {
            "resource": "combined",
            "current_value": 0.5,
            "projected_value": 0.6,
            "growth_rate_per_day": 0.001,
            "window": "3m",
            "confidence": 0.7,
            "assumptions": ["Test assumption"],
        }
    ]

    # Mock snapshot with 500GB total store (so 150GB reclaimable = 30%)
    mock_snapshot = create_mock_snapshot()
    # Modify index snapshot to have larger store size
    for idx in mock_snapshot.index_snapshots.values():
        idx.store_size_bytes = 500 * (1024 ** 3)  # 500 GB

    sizing = {
        "current_node_count": 3,
        "recommended_node_count": 3,
        "confidence": 0.8,
        "reasoning": ["Test reasoning"],
        "assumptions": ["Test assumption"],
        "projection_window": "3m",
        "estimated_cost_change": "neutral",
    }

    actions = planner._evaluate_rules(
        optimizer_excerpt=optimizer_excerpt,
        capacity_projections=capacity_projections,
        sizing=sizing,
        current_snapshot=mock_snapshot,
        historical_snapshots=[],
    )

    # Should have reclaim storage action
    reclaim_actions = [a for a in actions if a.action == PlanAction.RECLAIM_STORAGE]
    assert len(reclaim_actions) >= 1
    assert reclaim_actions[0].safety_tier == "SAFE_REVERSIBLE"
    assert "reclaimable storage" in reclaim_actions[0].summary.lower()

    # Additional assertions to verify specific action details
    assert reclaim_actions[0].priority == 15  # Should have correct priority for reclaim storage
    assert "Potential 30.0% storage recovery" in reclaim_actions[0].estimated_impact  # Should show correct recovery percentage
    assert reclaim_actions[0].confidence == 0.8  # Should have correct confidence level


def test_deduplicate_actions():
    """Test action deduplication keeps highest priority."""
    planner = RuleBasedPlanner()

    # Create two actions of same type with different priorities
    action_high_priority = PlannedAction(
        action=PlanAction.SCALE_UP,
        summary="High priority scale-up",
        rationale=["Reason"],
        safety_tier="APPROVAL_REQUIRED",
        priority=5,  # Higher priority (lower number)
        estimated_impact="High impact",
        confidence=0.9,
    )

    action_low_priority = PlannedAction(
        action=PlanAction.SCALE_UP,
        summary="Low priority scale-up",
        rationale=["Reason"],
        safety_tier="APPROVAL_REQUIRED",
        priority=20,  # Lower priority (higher number)
        estimated_impact="Low impact",
        confidence=0.6,
    )

    actions = [action_low_priority, action_high_priority]
    deduped = planner._deduplicate_actions(actions)

    # Should only have one SCALE_UP action (the high priority one)
    assert len(deduped) == 1
    assert deduped[0].action == PlanAction.SCALE_UP
    assert deduped[0].priority == 5  # High priority kept


def test_build_plan_summary():
    """Test plan summary generation."""
    planner = RuleBasedPlanner()

    # Test with no actions
    summary = planner._build_plan_summary([])
    assert "No optimization actions required" in summary

    # Test with high priority actions
    high_action = PlannedAction(
        action=PlanAction.SCALE_UP,
        summary="Critical action",
        rationale=["Reason"],
        safety_tier="APPROVAL_REQUIRED",
        priority=5,
        estimated_impact="High impact",
        confidence=0.9,
    )

    summary = planner._build_plan_summary([high_action])
    assert "1 high-priority action(s)" in summary
    assert "Total: 1 action(s)" in summary

    # Test with mixed priority actions
    med_action = PlannedAction(
        action=PlanAction.RIGHT_SIZE,
        summary="Medium action",
        rationale=["Reason"],
        safety_tier="INFORMATIONAL",
        priority=25,
        estimated_impact="Medium impact",
        confidence=0.7,
    )

    summary = planner._build_plan_summary([high_action, med_action])
    assert "1 high-priority action(s)" in summary
    assert "1 medium-priority action(s)" in summary
    assert "Total: 2 action(s)" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])