"""
Test cases for validating optimizer and capacity planning logic in OpenSearch plugin context.
Tests the correctness of algorithms, projections, and recommendation generation.
"""
import pytest
from datetime import datetime, timezone, timedelta
from guardian.optimizer import (
    OptimizerConfig,
    OptimizationEngine,
    ReclaimableStorage,
    ShardReduction,
    ReplicaOptimization,
    MappingOptimization,
    CapacityRecovery,
    OptimizationResult,
    RetentionAnalysisResult,
    StorageAnalysisResult,
    ShardAnalysisResult,
    ReplicaAnalysisResult,
    MappingAnalysisResult,
    CapacityAnalysisResult
)
from guardian.planner import (
    CapacityPlanner,
    ProjectionConfig,
    GrowthRate,
    ProjectionWindow,
    UtilizationProjection,
    SizingRecommendation,
    calculate_rightsizing
)
from guardian.models import (
    CollectionResult,
    ClusterSnapshot,
    IndexSnapshot,
    NodeSnapshot,
    JvmSnapshot,
    OsSnapshot,
    ProcessSnapshot,
    ThreadPoolSnapshot,
    FilesystemSnapshot
)
from guardian.safety import OperationContext, SafetyClassification
from guardian.security import SecurityContext, UserIdentity, TenantContext


def setup_security_context():
    """Set up a security context with guardian_monitor role for tests."""
    user = UserIdentity(
        username="test-user",
        backend_roles=["guardian_monitor"],
        custom_attribute={}
    )
    tenant = TenantContext(
        tenant_name="global",
        is_global_tenant=True,
        is_private_tenant=False
    )
    SecurityContext.set_context(user, tenant)


def teardown_security_context():
    """Clear the security context after tests."""
    SecurityContext.clear_context()


def create_mock_cluster_snapshot(
    cluster_name="test-cluster",
    health_status="green",
    total_nodes=3,
    data_nodes=3,
    master_nodes=1,
    ingest_nodes=0,
    active_primary_shards=10,
    active_shards=20,
    relocating_shards=0,
    initializing_shards=0,
    unassigned_shards=0,
    delayed_unassigned_shards=0,
    pending_cluster_tasks=0,
    failed_cluster_tasks=0
):
    """Create a mock cluster snapshot for testing."""
    return ClusterSnapshot(
        snapshot_id="test-snapshot-123",
        cluster_name=cluster_name,
        collected_at=datetime.now(timezone.utc),
        health_status=health_status,
        total_nodes=total_nodes,
        data_nodes=data_nodes,
        master_nodes=master_nodes,
        ingest_nodes=ingest_nodes,
        active_primary_shards=active_primary_shards,
        active_shards=active_shards,
        relocating_shards=relocating_shards,
        initializing_shards=initializing_shards,
        unassigned_shards=unassigned_shards,
        delayed_unassigned_shards=delayed_unassigned_shards,
        pending_cluster_tasks=pending_cluster_tasks,
        failed_cluster_tasks=failed_cluster_tasks,
        source_api="_cluster/health",
        source_version="2.17.1",
        raw_response_hash="abc123"
    )


def create_mock_node_snapshot(
    node_id="node-1",
    node_name="test-node-1",
    host="localhost",
    ip="127.0.0.1",
    roles=["master", "data", "ingest"],
    version="2.17.1",
    jvm_heap_used_bytes=1073741824,  # 1GB
    jvm_heap_max_bytes=4294967296,    # 4GB
    jvm_heap_used_percent=25,
    cpu_percent=30.0,
    mem_total_bytes=8589934592,       # 8GB
    mem_used_bytes=2576980378,        # ~2.4GB
    mem_free_bytes=6012954214,        # ~5.6GB
    open_file_descriptors=150,
    max_file_descriptors=65536
):
    """Create a mock node snapshot for testing."""
    jvm_snapshot = JvmSnapshot(
        mem_heap_used_bytes=jvm_heap_used_bytes,
        mem_heap_max_bytes=jvm_heap_max_bytes,
        mem_heap_used_percent=jvm_heap_used_percent,
        mem_non_heap_used_bytes=104857600,  # 100MB
        gc_collectors_young_count=10,
        gc_collectors_young_time_ms=100,
        gc_collectors_old_count=0,
        gc_collectors_old_time_ms=0,
        buffer_pools_direct_count=10,
        buffer_pools_direct_used_bytes=10240,
        buffer_pools_mapped_count=5,
        buffer_pools_mapped_used_bytes=5120,
        uptime_ms=86400000  # 1 day
    )

    os_snapshot = OsSnapshot(
        cpu_percent=cpu_percent,
        load_average_1m=1.5,
        load_average_5m=1.2,
        load_average_15m=1.0,
        mem_total_bytes=mem_total_bytes,
        mem_used_bytes=mem_used_bytes,
        mem_free_bytes=mem_free_bytes,
        mem_free_percent=70,
        mem_used_percent=30
    )

    process_snapshot = ProcessSnapshot(
        cpu_percent=5.0,
        cpu_total_ms=3600000,  # 1 hour
        open_file_descriptors=open_file_descriptors,
        max_file_descriptors=max_file_descriptors,
        mem_swap_used_bytes=0,
        mem_swap_max_bytes=0
    )

    thread_pools = {
        "write": ThreadPoolSnapshot(name="write", threads=4, queue=0, active=0, rejected=0, completed=1000),
        "search": ThreadPoolSnapshot(name="search", threads=8, queue=0, active=0, rejected=0, completed=5000)
    }

    filesystems = [
        FilesystemSnapshot(
            total_bytes=107374182400,  # 100GB
            available_bytes=53687091200,  # 50GB
            used_bytes=53687091200,      # 50GB
            available_percent=50.0,
            disk_reads=1000,
            disk_writes=500,
            disk_total_size_bytes=107374182400
        )
    ]

    return NodeSnapshot(
        node_id=node_id,
        node_name=node_name,
        host=host,
        ip=ip,
        roles=roles,
        version=version,
        collected_at=datetime.now(timezone.utc),
        jvm=jvm_snapshot,
        os=os_snapshot,
        process=process_snapshot,
        thread_pools=thread_pools,
        filesystems=filesystems,
        indices_doc_count=1000000,
        indices_store_size_bytes=53687091200,  # 50GB
        source_api="_nodes/stats",
        source_version="",
        raw_response_hash=""
    )


def create_mock_index_snapshot(
    index_name="test-index",
    uuid="test-index-uuid",
    doc_count=500000,
    deleted_doc_count=5000,
    store_size_bytes=53687091200,  # 50GB
    primary_size_bytes=26843545600,  # 25GB
    number_of_shards=5,
    number_of_replicas=1,
    total_shards=10,
    search_query_total=10000,
    search_query_time_ms=50000,
    indexing_index_total=50000,
    indexing_index_time_ms=25000,
    segment_count=10,
    segment_memory_bytes=5242880,  # 5MB
    refresh_interval_ms=30000,
    codec="lucene",
    lifecycle_policy=None,
    read_only=False,
    read_only_allow_delete=False,
    field_count=500,
    has_keyword_explosion=False,
    source_api="_stats",
    source_version="",
    raw_response_hash=""
):
    """Create a mock index snapshot for testing."""
    return IndexSnapshot(
        index_name=index_name,
        uuid=uuid,
        collected_at=datetime.now(timezone.utc),
        doc_count=doc_count,
        deleted_doc_count=deleted_doc_count,
        store_size_bytes=store_size_bytes,
        primary_size_bytes=primary_size_bytes,
        number_of_shards=number_of_shards,
        number_of_replicas=number_of_replicas,
        total_shards=total_shards,
        search_query_total=search_query_total,
        search_query_time_ms=search_query_time_ms,
        indexing_index_total=indexing_index_total,
        indexing_index_time_ms=indexing_index_time_ms,
        segment_count=segment_count,
        segment_memory_bytes=segment_memory_bytes,
        refresh_interval_ms=refresh_interval_ms,
        codec=codec,
        lifecycle_policy=lifecycle_policy,
        read_only=read_only,
        read_only_allow_delete=read_only_allow_delete,
        field_count=field_count,
        has_keyword_explosion=has_keyword_explosion,
        source_api=source_api,
        source_version=source_version,
        raw_response_hash=raw_response_hash
    )


def create_mock_collection_result(
    cluster_name="test-cluster",
    node_count=3,
    index_count=2
):
    """Create a mock collection result for testing."""
    cluster_snapshot = create_mock_cluster_snapshot(cluster_name=cluster_name)

    node_snapshots = {}
    for i in range(node_count):
        node_snapshot = create_mock_node_snapshot(
            node_id=f"node-{i+1}",
            node_name=f"test-node-{i+1}",
            host=f"10.0.0.{i+1}",
            ip=f"10.0.0.{i+1}"
        )
        node_snapshots[node_snapshot.node_id] = node_snapshot

    index_snapshots = {}
    for i in range(index_count):
        index_snapshot = create_mock_index_snapshot(
            index_name=f"test-index-{i+1}",
            uuid=f"test-index-{i+1}-uuid",
            doc_count=100000 * (i+1),  # Varying doc counts
            store_size_bytes=5368709120 * (i+1),  # Varying sizes
            number_of_shards=3 + i,  # Varying shard counts
            number_of_replicas=1,
            field_count=100 * (i+1)  # Varying field counts
        )
        index_snapshots[index_snapshot.index_name] = index_snapshot

    shard_states = []  # Simplified for testing

    return CollectionResult(
        cluster_snapshot=cluster_snapshot,
        node_snapshots=node_snapshots,
        index_snapshots=index_snapshots,
        shard_states=shard_states,
        collected_at=datetime.now(timezone.utc),
        errors=[]
    )


class TestOptimizerLogic:
    """Test optimizer logic validation in plugin context."""

    def test_optimizer_config_defaults(self):
        """Test that OptimizerConfig has sensible defaults."""
        config = OptimizerConfig()

        # Retention analysis defaults
        assert config.retention_age_days_threshold == 30
        assert config.retention_access_threshold == 0.1

        # Shard analysis defaults
        assert config.tiny_shard_doc_count == 1000
        assert config.oversharded_shard_count == 50
        assert config.tiny_shard_waste_ratio == 0.5

        # Replica analysis defaults
        assert config.replica_overhead_threshold == 2.0
        assert config.min_replicas_for_availability == 1

        # Mapping analysis defaults
        assert config.high_field_count_threshold == 10000
        assert config.unnecessary_indexed_field_ratio == 0.8

        # Capacity analysis defaults
        assert config.utilization_imbalance_threshold == 0.5
        assert config.min_node_count_for_imbalance == 3

        # Analysis windows
        assert config.access_log_days == 7
        assert config.snapshot_age_days == 7

    def test_optimization_engine_initialization(self):
        """Test that OptimizationEngine initializes correctly."""
        # With default config
        engine = OptimizationEngine()
        assert engine.config is not None
        assert isinstance(engine.config, OptimizerConfig)

        # With custom config
        custom_config = OptimizerConfig(
            retention_age_days_threshold=60,
            tiny_shard_doc_count=500
        )
        engine = OptimizationEngine(custom_config)
        assert engine.config.retention_age_days_threshold == 60
        assert engine.config.tiny_shard_doc_count == 500

    def test_analyze_all_returns_expected_types(self):
        """Test that analyze_all returns all expected optimization result types."""
        setup_security_context()
        try:
            engine = OptimizationEngine()
            snapshot = create_mock_collection_result()

            results = engine.analyze_all(snapshot)

            # Check that all expected analysis types are present
            expected_types = {"retention", "storage", "shard", "replica", "mapping", "capacity"}
            assert set(results.keys()) == expected_types

            # Check that each result is the correct type
            assert isinstance(results["retention"], RetentionAnalysisResult)
            assert isinstance(results["storage"], StorageAnalysisResult)
            assert isinstance(results["shard"], ShardAnalysisResult)
            assert isinstance(results["replica"], ReplicaAnalysisResult)
            assert isinstance(results["mapping"], MappingAnalysisResult)
            assert isinstance(results["capacity"], CapacityAnalysisResult)
        finally:
            teardown_security_context()

    def test_reclaimable_storage_creation(self):
        """Test ReclaimableStorage model creation and validation."""
        recommendation = ReclaimableStorage(
            index_name="old-logs-2023",
            reclaimable_bytes=10737418240,  # 10GB
            reason="old_index",
            confidence=0.85,
            assumptions=[
                "Index older than 60 days",
                "Low access patterns detected"
            ]
        )

        assert recommendation.index_name == "old-logs-2023"
        assert recommendation.reclaimable_bytes == 10737418240
        assert recommendation.reason == "old_index"
        assert recommendation.confidence == 0.85
        assert len(recommendation.assumptions) == 2

        # Test confidence bounds
        with pytest.raises(ValueError):
            ReclaimableStorage(
                index_name="test",
                reclaimable_bytes=1000,
                reason="test",
                confidence=1.5  # Too high
            )

        with pytest.raises(ValueError):
            ReclaimableStorage(
                index_name="test",
                reclaimable_bytes=1000,
                reason="test",
                confidence=-0.1  # Too low
            )

    def test_shard_reduction_creation(self):
        """Test ShardReduction model creation and validation."""
        recommendation = ShardReduction(
            index_name="oversharded-index",
            current_shard_count=10,
            recommended_shard_count=5,
            reason="oversharded",
            confidence=0.75,
            assumptions=[
                "Index has 10 shards but only 2GB of data",
                "Reducing to 5 shards will improve efficiency"
            ]
        )

        assert recommendation.index_name == "oversharded-index"
        assert recommendation.current_shard_count == 10
        assert recommendation.recommended_shard_count == 5
        assert recommendation.reason == "oversharded"
        assert recommendation.confidence == 0.75
        assert len(recommendation.assumptions) == 2

    def test_replica_optimization_creation(self):
        """Test ReplicaOptimization model creation and validation."""
        recommendation = ReplicaOptimization(
            index_name="high-replica-index",
            current_replica_count=3,
            recommended_replica_count=1,
            reason="unnecessary_overhead",
            confidence=0.8,
            assumptions=[
                "Index has 3 replicas but only 1 node",
                "Reducing to 1 replica saves storage while maintaining availability"
            ]
        )

        assert recommendation.index_name == "high-replica-index"
        assert recommendation.current_replica_count == 3
        assert recommendation.recommended_replica_count == 1
        assert recommendation.reason == "unnecessary_overhead"
        assert recommendation.confidence == 0.8
        assert len(recommendation.assumptions) == 2

    def test_mapping_optimization_creation(self):
        """Test MappingOptimization model creation and validation."""
        recommendation = MappingOptimization(
            index_name="field-explosion-index",
            field_count=15000,
            unnecessary_fields=10000,
            reason="high_field_count",
            confidence=0.7,
            assumptions=[
                "Index has 15K fields exceeding 10K threshold",
                "Many fields are not used in queries"
            ]
        )

        assert recommendation.index_name == "field-explosion-index"
        assert recommendation.field_count == 15000
        assert recommendation.unnecessary_fields == 10000
        assert recommendation.reason == "high_field_count"
        assert recommendation.confidence == 0.7
        assert len(recommendation.assumptions) == 2

    def test_capacity_recovery_creation(self):
        """Test CapacityRecovery model creation and validation."""
        recommendation = CapacityRecovery(
            node_name="overutilized-node",
            current_utilization=0.95,  # 95% utilized
            target_utilization=0.70,   # 70% target
            reason="overutilized",
            confidence=0.9,
            assumptions=[
                "Node consistently above 90% utilization",
                "Adding another node would balance load"
            ]
        )

        assert recommendation.node_name == "overutilized-node"
        assert recommendation.current_utilization == 0.95
        assert recommendation.target_utilization == 0.70
        assert recommendation.reason == "overutilized"
        assert recommendation.confidence == 0.9
        assert len(recommendation.assumptions) == 2

    def test_optimization_result_structure(self):
        """Test OptimizationResult structure and methods."""
        result = OptimizationResult(
            analysis_type="retention",
            timestamp=datetime.now(timezone.utc),
            cluster_name="test-cluster",
            assumptions=["Test assumption"],
            recommendations=[]
        )

        assert result.analysis_type == "retention"
        assert result.cluster_name == "test-cluster"
        assert len(result.assumptions) == 1
        assert len(result.recommendations) == 0

        # Test add_recommendation method
        recommendation = ReclaimableStorage(
            index_name="test-index",
            reclaimable_bytes=1000000,
            reason="test",
            confidence=0.8
        )
        result.add_recommendation(recommendation)
        assert len(result.recommendations) == 1
        assert result.recommendations[0].index_name == "test-index"


class TestCapacityPlannerLogic:
    """Test capacity planner logic validation in plugin context."""

    def test_projection_config_defaults(self):
        """Test that ProjectionConfig has sensible defaults."""
        config = ProjectionConfig()

        assert config.default_window == ProjectionWindow.THREE_MONTHS
        assert config.growth_method == GrowthRate.LINEAR
        assert config.min_history_points == 7
        assert config.high_confidence_threshold == 0.8
        assert config.low_confidence_threshold == 0.5
        assert config.buffer_percent == 0.2
        assert config.min_nodes == 3
        assert config.max_nodes == 100
        assert config.target_utilization == 0.7
        assert config.max_heap_gb == 32
        assert config.max_disk_gb == 2000
        assert config.max_cpu_cores == 64

    def test_projection_window_enum(self):
        """Test ProjectionWindow enum values and timedelta conversion."""
        assert ProjectionWindow.ONE_WEEK.value == "1w"
        assert ProjectionWindow.ONE_MONTH.value == "1m"
        assert ProjectionWindow.THREE_MONTHS.value == "3m"
        assert ProjectionWindow.SIX_MONTHS.value == "6m"
        assert ProjectionWindow.ONE_YEAR.value == "1y"

        # Test timedelta conversion
        assert ProjectionWindow.ONE_WEEK.to_timedelta().days == 7
        assert ProjectionWindow.ONE_MONTH.to_timedelta().days == 30
        assert ProjectionWindow.THREE_MONTHS.to_timedelta().days == 90
        assert ProjectionWindow.SIX_MONTHS.to_timedelta().days == 180
        assert ProjectionWindow.ONE_YEAR.to_timedelta().days == 365

    def test_growth_rate_enum(self):
        """Test GrowthRate enum values."""
        assert GrowthRate.LINEAR.value == "linear"
        assert GrowthRate.EXPONENTIAL.value == "exponential"
        assert GrowthRate.CONSERVATIVE.value == "conservative"
        assert GrowthRate.AGGRESSIVE.value == "aggressive"

    def test_utilization_projection_creation(self):
        """Test UtilizationProjection creation."""
        projection = UtilizationProjection(
            resource="heap",
            current_value=0.65,
            projected_value=0.78,
            growth_rate_per_day=0.002,
            window=ProjectionWindow.THREE_MONTHS,
            confidence=0.85,
            assumptions=[
                "Based on 10 historical data points",
                "Linear growth projection"
            ],
            projected_at=datetime.now(timezone.utc)
        )

        assert projection.resource == "heap"
        assert projection.current_value == 0.65
        assert projection.projected_value == 0.78
        assert projection.growth_rate_per_day == 0.002
        assert projection.window == ProjectionWindow.THREE_MONTHS
        assert projection.confidence == 0.85
        assert len(projection.assumptions) == 2

    def test_sizing_recommendation_creation(self):
        """Test SizingRecommendation creation."""
        recommendation = SizingRecommendation(
            current_node_count=3,
            recommended_node_count=4,
            min_node_count=3,
            max_node_count=20,
            recommended_heap_gb=16,
            recommended_disk_gb=1000,
            recommended_cpu_cores=8,
            confidence=0.78,
            reasoning=[
                "Current node count: 3",
                "Projected combined utilization: 75%",
                "Target utilization: 70%",
                "Required nodes for target: 4"
            ],
            assumptions=[
                "Growth method: linear",
                "Safety buffer: 20%",
                "Target utilization: 70%"
            ],
            projection_window=ProjectionWindow.THREE_MONTHS,
            estimated_cost_change="increase",
            projected_at=datetime.now(timezone.utc)
        )

        assert recommendation.current_node_count == 3
        assert recommendation.recommended_node_count == 4
        assert recommendation.min_node_count == 3
        assert recommendation.max_node_count == 20
        assert recommendation.recommended_heap_gb == 16
        assert recommendation.recommended_disk_gb == 1000
        assert recommendation.recommended_cpu_cores == 8
        assert recommendation.confidence == 0.78
        assert len(recommendation.reasoning) == 4
        assert len(recommendation.assumptions) == 3
        assert recommendation.projection_window == ProjectionWindow.THREE_MONTHS
        assert recommendation.estimated_cost_change == "increase"

    def test_capacity_planner_initialization(self):
        """Test that CapacityPlanner initializes correctly."""
        # With default configs
        planner = CapacityPlanner()
        assert planner.config is not None
        assert isinstance(planner.config, ProjectionConfig)
        assert planner.optimizer_engine is not None

        # With custom configs
        custom_projection_config = ProjectionConfig(
            default_window=ProjectionWindow.SIX_MONTHS,
            target_utilization=0.8
        )
        custom_optimizer_config = OptimizerConfig(
            retention_age_days_threshold=60
        )
        planner = CapacityPlanner(custom_projection_config, custom_optimizer_config)
        assert planner.config.default_window == ProjectionWindow.SIX_MONTHS
        assert planner.config.target_utilization == 0.8
        assert planner.optimizer_engine.config.retention_age_days_threshold == 60

    def test_plan_capacity_with_empty_history(self):
        """Test plan_capacity with empty historical snapshots."""
        setup_security_context()
        try:
            planner = CapacityPlanner()
            snapshot = create_mock_collection_result()

            # Should work even with empty history
            result = planner.plan_capacity(snapshot, [])

            assert "projections" in result
            assert "sizing_recommendation" in result
            assert "optimizer_analysis" in result
            assert "cluster_name" in result
            assert "generated_at" in result
            assert result["cluster_name"] == "test-cluster"

            # Should have projections for all resources
            projections = result["projections"]
            assert len(projections) == 4  # cpu, heap, disk, combined
            resources = [p["resource"] for p in projections]
            assert set(resources) == {"cpu", "heap", "disk", "combined"}

            # Should have sizing recommendation
            sizing = result["sizing_recommendation"]
            assert sizing["current_node_count"] == 3
            assert sizing["recommended_node_count"] >= 3  # At least minimum
        finally:
            teardown_security_context()

    def test_calculate_rightsizing_convenience_function(self):
        """Test the calculate_rightsizing convenience function."""
        setup_security_context()
        try:
            snapshot = create_mock_collection_result()

            result = calculate_rightsizing(
                current_snapshot=snapshot,
                target_utilization=0.7,
                growth_buffer=0.2
            )

            assert "recommended_nodes" in result
            assert "heap_gb" in result
            assert "disk_gb" in result
            assert "cpu_cores" in result
            assert "confidence" in result

            # Should return reasonable values
            assert isinstance(result["recommended_nodes"], int)
            assert result["recommended_nodes"] >= 3
            assert isinstance(result["heap_gb"], int)
            assert result["heap_gb"] > 0
            assert isinstance(result["disk_gb"], int)
            assert result["disk_gb"] > 0
            assert isinstance(result["cpu_cores"], int)
            assert result["cpu_cores"] > 0
            assert isinstance(result["confidence"], float)
            assert 0 <= result["confidence"] <= 1
        finally:
            teardown_security_context()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])