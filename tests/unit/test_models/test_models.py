"""Unit tests for Guardian data models."""

import pytest
from datetime import datetime, timezone
from guardian.models import (
    ClusterSnapshot,
    JvmSnapshot,
    OsSnapshot,
    ProcessSnapshot,
    ThreadPoolSnapshot,
    FilesystemSnapshot,
    NodeSnapshot,
    ShardState,
    IndexSnapshot,
    CollectionResult,
)


class TestClusterSnapshot:
    """Tests for ClusterSnapshot model."""

    def test_minimal_valid(self):
        """Minimal valid snapshot."""
        snapshot = ClusterSnapshot(
            snapshot_id="snap-1",
            cluster_name="test-cluster",
            collected_at=datetime.now(timezone.utc),
            health_status="green",
            total_nodes=1,
            data_nodes=1,
            master_nodes=1,
            ingest_nodes=0,
            active_primary_shards=5,
            active_shards=5,
            relocating_shards=0,
            initializing_shards=0,
            unassigned_shards=0,
            pending_cluster_tasks=0,
        )
        assert snapshot.health_status == "green"
        assert snapshot.source_api == "_cluster/health"
        assert snapshot.delayed_unassigned_shards == 0

    def test_yellow_health(self):
        """Yellow health status."""
        snapshot = ClusterSnapshot(
            snapshot_id="snap-2",
            cluster_name="test-cluster",
            collected_at=datetime.now(timezone.utc),
            health_status="yellow",
            total_nodes=2,
            data_nodes=2,
            master_nodes=1,
            ingest_nodes=0,
            active_primary_shards=10,
            active_shards=15,
            relocating_shards=0,
            initializing_shards=0,
            unassigned_shards=5,
            pending_cluster_tasks=0,
        )
        assert snapshot.unassigned_shards == 5

    def test_red_health_with_failures(self):
        """Red health with failed cluster tasks."""
        snapshot = ClusterSnapshot(
            snapshot_id="snap-3",
            cluster_name="test-cluster",
            collected_at=datetime.now(timezone.utc),
            health_status="red",
            total_nodes=1,
            data_nodes=1,
            master_nodes=1,
            ingest_nodes=0,
            active_primary_shards=3,
            active_shards=3,
            relocating_shards=0,
            initializing_shards=0,
            unassigned_shards=10,
            pending_cluster_tasks=2,
            failed_cluster_tasks=1,
        )
        assert snapshot.failed_cluster_tasks == 1


class TestJvmSnapshot:
    """Tests for JvmSnapshot model."""

    def test_normal_heap(self):
        snapshot = JvmSnapshot(
            mem_heap_used_bytes=134217728,  # 128 MB
            mem_heap_max_bytes=536870912,   # 512 MB
            mem_heap_used_percent=25,
            mem_non_heap_used_bytes=33554432,
            gc_collectors_young_count=10,
            gc_collectors_young_time_ms=100,
            gc_collectors_old_count=0,
            gc_collectors_old_time_ms=0,
            buffer_pools_direct_count=5,
            buffer_pools_direct_used_bytes=1024,
            buffer_pools_mapped_count=0,
            buffer_pools_mapped_used_bytes=0,
            uptime_ms=3600000,
        )
        assert snapshot.mem_heap_used_percent == 25
        assert snapshot.gc_collectors_old_count == 0

    def test_high_heap_usage(self):
        """Simulate high heap usage."""
        snapshot = JvmSnapshot(
            mem_heap_used_bytes=510000000,  # ~486 MB
            mem_heap_max_bytes=536870912,   # 512 MB
            mem_heap_used_percent=95,
            mem_non_heap_used_bytes=50000000,
            gc_collectors_young_count=100,
            gc_collectors_young_time_ms=5000,
            gc_collectors_old_count=10,
            gc_collectors_old_time_ms=2000,
            buffer_pools_direct_count=20,
            buffer_pools_direct_used_bytes=2048,
            buffer_pools_mapped_count=0,
            buffer_pools_mapped_used_bytes=0,
            uptime_ms=7200000,
        )
        assert snapshot.mem_heap_used_percent == 95
        assert snapshot.gc_collectors_old_count > 0


class TestOsSnapshot:
    """Tests for OsSnapshot model."""

    def test_normal_load(self):
        snapshot = OsSnapshot(
            cpu_percent=15.5,
            load_average_1m=0.5,
            load_average_5m=0.3,
            load_average_15m=0.2,
            mem_total_bytes=8589934592,
            mem_used_bytes=4294967296,
            mem_free_bytes=4294967296,
            mem_free_percent=50,
            mem_used_percent=50,
        )
        assert snapshot.cpu_percent == 15.5
        assert snapshot.mem_free_percent == 50

    def test_high_cpu(self):
        snapshot = OsSnapshot(
            cpu_percent=95.0,
            load_average_1m=4.5,
            load_average_5m=3.2,
            load_average_15m=2.1,
            mem_total_bytes=8589934592,
            mem_used_bytes=7500000000,
            mem_free_bytes=1089934592,
            mem_free_percent=12,
            mem_used_percent=88,
        )
        assert snapshot.cpu_percent == 95.0
        assert snapshot.mem_used_percent == 88


class TestProcessSnapshot:
    """Tests for ProcessSnapshot model."""

    def test_normal_process(self):
        snapshot = ProcessSnapshot(
            cpu_percent=2.5,
            cpu_total_ms=50000,
            open_file_descriptors=150,
            max_file_descriptors=65536,
            mem_swap_used_bytes=0,
            mem_swap_max_bytes=0,
        )
        assert snapshot.open_file_descriptors == 150
        assert snapshot.mem_swap_used_bytes == 0

    def test_file_descriptor_pressure(self):
        snapshot = ProcessSnapshot(
            cpu_percent=1.0,
            cpu_total_ms=10000,
            open_file_descriptors=60000,
            max_file_descriptors=65536,
            mem_swap_used_bytes=104857600,
            mem_swap_max_bytes=209715200,
        )
        assert snapshot.open_file_descriptors == 60000
        assert snapshot.mem_swap_used_bytes > 0


class TestThreadPoolSnapshot:
    """Tests for ThreadPoolSnapshot model."""

    def test_healthy_thread_pool(self):
        pool = ThreadPoolSnapshot(
            name="write",
            threads=4,
            queue=0,
            active=0,
            rejected=0,
            completed=1000,
        )
        assert pool.rejected == 0
        assert pool.leaked == 0

    def test_rejected_threads(self):
        """Thread pool with rejections indicates overload."""
        pool = ThreadPoolSnapshot(
            name="index",
            threads=8,
            queue=150,
            active=8,
            rejected=25,
            completed=5000,
        )
        assert pool.rejected == 25
        assert pool.queue > 0

    def test_leaked_threads(self):
        pool = ThreadPoolSnapshot(
            name="search",
            threads=10,
            queue=0,
            active=2,
            rejected=0,
            completed=800,
            leaked=3,
        )
        assert pool.leaked == 3


class TestFilesystemSnapshot:
    """Tests for FilesystemSnapshot model."""

    def test_normal_disk(self):
        fs = FilesystemSnapshot(
            total_bytes=107374182400,      # 100 GB
            available_bytes=53687091200,   # 50 GB
            used_bytes=53687091200,
            available_percent=50.0,
            disk_reads=10000,
            disk_writes=50000,
            disk_total_size_bytes=107374182400,
        )
        assert fs.available_percent == 50.0
        assert fs.disk_reads == 10000

    def test_high_disk_usage(self):
        fs = FilesystemSnapshot(
            total_bytes=107374182400,
            available_bytes=536870912,     # 512 MB remaining
            used_bytes=106837311488,
            available_percent=0.5,
            disk_reads=50000,
            disk_writes=200000,
            disk_total_size_bytes=107374182400,
        )
        assert fs.available_percent == 0.5
        assert fs.disk_writes > fs.disk_reads


class TestShardState:
    """Tests for ShardState model."""

    def test_started_shard(self):
        shard = ShardState(
            shard_id="0",
            index_name="logs-app-1",
            primary=True,
            node_id="node-1",
            node_name="node-1",
            state="STARTED",
            collected_at=datetime.now(timezone.utc),
        )
        assert shard.state == "STARTED"
        assert shard.primary is True

    def test_unassigned_shard(self):
        shard = ShardState(
            shard_id="1",
            index_name="logs-app-1",
            primary=False,
            node_id=None,
            node_name=None,
            state="UNASSIGNED",
            relocation_status="no_valid_shard_copy",
            allocation_explanation="no enough nodes",
            collected_at=datetime.now(timezone.utc),
        )
        assert shard.state == "UNASSIGNED"
        assert shard.node_id is None
        assert shard.allocation_explanation == "no enough nodes"

    def test_initializing_shard(self):
        shard = ShardState(
            shard_id="2",
            index_name="logs-app-1",
            primary=True,
            node_id="node-2",
            node_name="node-2",
            state="INITIALIZING",
            recovery_source_node="node-1",
            recovery_target_node="node-2",
            recovery_progress_percent=45.5,
            collected_at=datetime.now(timezone.utc),
        )
        assert shard.state == "INITIALIZING"
        assert shard.recovery_progress_percent == 45.5


class TestIndexSnapshot:
    """Tests for IndexSnapshot model."""

    def test_normal_index(self):
        idx = IndexSnapshot(
            index_name="logs-app-1",
            uuid="abc123",
            collected_at=datetime.now(timezone.utc),
            doc_count=10000,
            deleted_doc_count=0,
            store_size_bytes=5242880,  # 5 MB
            primary_size_bytes=5242880,
            number_of_shards=5,
            number_of_replicas=1,
            total_shards=10,
            search_query_total=500,
            search_query_time_ms=100,
            indexing_index_total=1000,
            indexing_index_time_ms=50,
            segment_count=15,
            segment_memory_bytes=1048576,
            refresh_interval_ms=1000,
            codec="Lucene_9_0",
            lifecycle_policy=None,
            read_only=False,
            read_only_allow_delete=False,
            field_count=25,
            has_keyword_explosion=False,
        )
        assert idx.doc_count == 10000
        assert idx.total_shards == 10
        assert idx.lifecycle_policy is None

    def test_read_only_index(self):
        idx = IndexSnapshot(
            index_name="frozen-logs",
            uuid="def456",
            collected_at=datetime.now(timezone.utc),
            doc_count=50000,
            deleted_doc_count=0,
            store_size_bytes=104857600,
            primary_size_bytes=52428800,
            number_of_shards=3,
            number_of_replicas=0,
            total_shards=3,
            search_query_total=10,
            search_query_time_ms=500,
            indexing_index_total=0,
            indexing_index_time_ms=0,
            segment_count=50,
            segment_memory_bytes=5242880,
            refresh_interval_ms=-1,
            codec="Lucene_9_0",
            lifecycle_policy="warm",
            read_only=True,
            read_only_allow_delete=False,
            field_count=15,
            has_keyword_explosion=False,
        )
        assert idx.read_only is True
        assert idx.lifecycle_policy == "warm"
        assert idx.indexing_index_total == 0

    def test_shard_explosion(self):
        """Index with excessive shards."""
        idx = IndexSnapshot(
            index_name="oversharded",
            uuid="ghi789",
            collected_at=datetime.now(timezone.utc),
            doc_count=100,
            deleted_doc_count=0,
            store_size_bytes=524288,  # 512 KB
            primary_size_bytes=524288,
            number_of_shards=50,
            number_of_replicas=0,
            total_shards=50,
            search_query_total=0,
            search_query_time_ms=0,
            indexing_index_total=100,
            indexing_index_time_ms=10,
            segment_count=100,
            segment_memory_bytes=1048576,
            refresh_interval_ms=1000,
            codec="Lucene_9_0",
            lifecycle_policy=None,
            read_only=False,
            read_only_allow_delete=False,
            field_count=30,
            has_keyword_explosion=True,
        )
        assert idx.number_of_shards == 50
        assert idx.has_keyword_explosion is True


class TestNodeSnapshot:
    """Tests for NodeSnapshot model."""

    def test_master_data_node(self):
        node = NodeSnapshot(
            node_id="node-1",
            node_name="master-node",
            host="127.0.0.1",
            ip="192.168.1.10",
            roles=["master", "data", "ingest"],
            version="2.17.1",
            collected_at=datetime.now(timezone.utc),
            jvm=JvmSnapshot(
                mem_heap_used_bytes=134217728,
                mem_heap_max_bytes=536870912,
                mem_heap_used_percent=25,
                mem_non_heap_used_bytes=33554432,
                gc_collectors_young_count=10,
                gc_collectors_young_time_ms=100,
                gc_collectors_old_count=0,
                gc_collectors_old_time_ms=0,
                buffer_pools_direct_count=5,
                buffer_pools_direct_used_bytes=1024,
                buffer_pools_mapped_count=0,
                buffer_pools_mapped_used_bytes=0,
                uptime_ms=3600000,
            ),
            os=OsSnapshot(
                cpu_percent=15.5,
                load_average_1m=0.5,
                load_average_5m=0.3,
                load_average_15m=0.2,
                mem_total_bytes=8589934592,
                mem_used_bytes=4294967296,
                mem_free_bytes=4294967296,
                mem_free_percent=50,
                mem_used_percent=50,
            ),
            process=ProcessSnapshot(
                cpu_percent=2.0,
                cpu_total_ms=10000,
                open_file_descriptors=150,
                max_file_descriptors=65536,
                mem_swap_used_bytes=0,
                mem_swap_max_bytes=0,
            ),
            thread_pools={
                "write": ThreadPoolSnapshot(
                    name="write", threads=4, queue=0, active=0,
                    rejected=0, completed=500,
                ),
                "search": ThreadPoolSnapshot(
                    name="search", threads=8, queue=0, active=1,
                    rejected=0, completed=1000,
                ),
            },
            filesystems=[
                FilesystemSnapshot(
                    total_bytes=107374182400,
                    available_bytes=53687091200,
                    used_bytes=53687091200,
                    available_percent=50.0,
                    disk_reads=1000,
                    disk_writes=5000,
                    disk_total_size_bytes=107374182400,
                )
            ],
        )
        assert node.node_name == "master-node"
        assert len(node.thread_pools) == 2
        assert node.jvm.mem_heap_used_percent == 25

    def test_data_only_node(self):
        node = NodeSnapshot(
            node_id="node-2",
            node_name="data-node",
            host="127.0.0.1",
            ip="192.168.1.11",
            roles=["data"],
            version="2.17.1",
            collected_at=datetime.now(timezone.utc),
            jvm=JvmSnapshot(
                mem_heap_used_bytes=480000000,
                mem_heap_max_bytes=536870912,
                mem_heap_used_percent=89,
                mem_non_heap_used_bytes=50000000,
                gc_collectors_young_count=50,
                gc_collectors_young_time_ms=5000,
                gc_collectors_old_count=5,
                gc_collectors_old_time_ms=1000,
                buffer_pools_direct_count=10,
                buffer_pools_direct_used_bytes=2048,
                buffer_pools_mapped_count=0,
                buffer_pools_mapped_used_bytes=0,
                uptime_ms=7200000,
            ),
            os=OsSnapshot(
                cpu_percent=85.0,
                load_average_1m=3.5,
                load_average_5m=2.8,
                load_average_15m=2.0,
                mem_total_bytes=8589934592,
                mem_used_bytes=7500000000,
                mem_free_bytes=1089934592,
                mem_free_percent=12,
                mem_used_percent=88,
            ),
            process=ProcessSnapshot(
                cpu_percent=15.0,
                cpu_total_ms=50000,
                open_file_descriptors=500,
                max_file_descriptors=65536,
                mem_swap_used_bytes=104857600,
                mem_swap_max_bytes=209715200,
            ),
            thread_pools={
                "write": ThreadPoolSnapshot(
                    name="write", threads=4, queue=50, active=4,
                    rejected=10, completed=2000,
                ),
            },
            filesystems=[
                FilesystemSnapshot(
                    total_bytes=107374182400,
                    available_bytes=5368709120,
                    used_bytes=102005473536,
                    available_percent=5.0,
                    disk_reads=50000,
                    disk_writes=200000,
                    disk_total_size_bytes=107374182400,
                )
            ],
            indices_doc_count=500000,
            indices_store_size_bytes=1073741824,
        )
        assert node.jvm.mem_heap_used_percent == 89
        assert node.os.cpu_percent == 85.0
        assert node.thread_pools["write"].rejected == 10


class TestCollectionResult:
    """Tests for CollectionResult model."""

    def test_empty_collection(self):
        result = CollectionResult(
            collected_at=datetime.now(timezone.utc),
            errors=[],
        )
        assert result.cluster_snapshot is None
        assert result.node_snapshots == {}
        assert result.index_snapshots == {}
        assert result.shard_states == []

    def test_full_collection(self):
        cluster = ClusterSnapshot(
            snapshot_id="snap-1",
            cluster_name="test-cluster",
            collected_at=datetime.now(timezone.utc),
            health_status="green",
            total_nodes=1,
            data_nodes=1,
            master_nodes=1,
            ingest_nodes=0,
            active_primary_shards=5,
            active_shards=5,
            relocating_shards=0,
            initializing_shards=0,
            unassigned_shards=0,
            pending_cluster_tasks=0,
        )
        node = NodeSnapshot(
            node_id="node-1",
            node_name="node-1",
            host="localhost",
            ip="127.0.0.1",
            roles=["master", "data"],
            version="2.17.1",
            collected_at=datetime.now(timezone.utc),
            jvm=JvmSnapshot(
                mem_heap_used_bytes=100000000,
                mem_heap_max_bytes=500000000,
                mem_heap_used_percent=20,
                mem_non_heap_used_bytes=30000000,
                gc_collectors_young_count=5,
                gc_collectors_young_time_ms=50,
                gc_collectors_old_count=0,
                gc_collectors_old_time_ms=0,
                buffer_pools_direct_count=3,
                buffer_pools_direct_used_bytes=512,
                buffer_pools_mapped_count=0,
                buffer_pools_mapped_used_bytes=0,
                uptime_ms=1800000,
            ),
            os=OsSnapshot(
                cpu_percent=10.0,
                load_average_1m=0.3,
                load_average_5m=0.2,
                load_average_15m=0.1,
                mem_total_bytes=8589934592,
                mem_used_bytes=3000000000,
                mem_free_bytes=5589934592,
                mem_free_percent=65,
                mem_used_percent=35,
            ),
            process=ProcessSnapshot(
                cpu_percent=1.0,
                cpu_total_ms=5000,
                open_file_descriptors=100,
                max_file_descriptors=65536,
                mem_swap_used_bytes=0,
                mem_swap_max_bytes=0,
            ),
            thread_pools={},
            filesystems=[],
        )
        result = CollectionResult(
            cluster_snapshot=cluster,
            node_snapshots={"node-1": node},
            index_snapshots={},
            shard_states=[],
            collected_at=datetime.now(timezone.utc),
        )
        assert result.cluster_snapshot is not None
        assert "node-1" in result.node_snapshots
        assert len(result.errors) == 0

    def test_collection_with_errors(self):
        result = CollectionResult(
            collected_at=datetime.now(timezone.utc),
            errors=["Failed to collect JVM stats", "Node unreachable"],
        )
        assert len(result.errors) == 2
        assert "Failed to collect JVM stats" in result.errors
