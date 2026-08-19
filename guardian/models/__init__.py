"""Normalized internal data models for the Guardian core.

All models are version-agnostic (OpenSearch 1.x and 2.x) and use Pydantic v2.
See docs/architecture/data-model.md for full field definitions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ClusterSnapshot(BaseModel):
    snapshot_id: str
    cluster_name: str
    collected_at: datetime
    health_status: str  # "green" | "yellow" | "red"

    total_nodes: int
    data_nodes: int
    master_nodes: int
    ingest_nodes: int

    active_primary_shards: int
    active_shards: int
    relocating_shards: int
    initializing_shards: int
    unassigned_shards: int
    delayed_unassigned_shards: int = 0
    pending_cluster_tasks: int
    failed_cluster_tasks: int = 0

    source_api: str = "_cluster/health"
    source_version: str = ""
    raw_response_hash: str = ""


class JvmSnapshot(BaseModel):
    mem_heap_used_bytes: int
    mem_heap_max_bytes: int
    mem_heap_used_percent: int
    mem_non_heap_used_bytes: int
    gc_collectors_young_count: int
    gc_collectors_young_time_ms: int
    gc_collectors_old_count: int
    gc_collectors_old_time_ms: int
    buffer_pools_direct_count: int
    buffer_pools_direct_used_bytes: int
    buffer_pools_mapped_count: int
    buffer_pools_mapped_used_bytes: int
    uptime_ms: int


class OsSnapshot(BaseModel):
    cpu_percent: float
    load_average_1m: float
    load_average_5m: float
    load_average_15m: float
    mem_total_bytes: int
    mem_used_bytes: int
    mem_free_bytes: int
    mem_free_percent: int
    mem_used_percent: int
    cgroup_cpu_percent: Optional[float] = None


class ProcessSnapshot(BaseModel):
    cpu_percent: float
    cpu_total_ms: int
    open_file_descriptors: int
    max_file_descriptors: int
    mem_swap_used_bytes: int
    mem_swap_max_bytes: int


class ThreadPoolSnapshot(BaseModel):
    name: str
    threads: int
    queue: int
    active: int
    rejected: int
    completed: int
    leaked: int = 0


class FilesystemSnapshot(BaseModel):
    total_bytes: int
    available_bytes: int
    used_bytes: int
    available_percent: float
    disk_reads: int
    disk_writes: int
    disk_total_size_bytes: int


class NodeSnapshot(BaseModel):
    node_id: str
    node_name: str
    host: str
    ip: str
    roles: list[str]
    version: str
    collected_at: datetime

    jvm: JvmSnapshot
    os: OsSnapshot
    process: ProcessSnapshot
    thread_pools: dict[str, ThreadPoolSnapshot]
    filesystems: list[FilesystemSnapshot]

    indices_doc_count: Optional[int] = None
    indices_store_size_bytes: Optional[int] = None

    source_api: str = "_nodes/stats"
    source_version: str = ""
    raw_response_hash: str = ""


class ShardState(BaseModel):
    shard_id: str
    index_name: str
    primary: bool
    node_id: Optional[str] = None
    node_name: Optional[str] = None
    state: str  # "STARTED" | "INITIALIZING" | "RELOCATING" | "UNASSIGNED"
    relocation_status: Optional[str] = None
    primary_node_id: Optional[str] = None
    replica_node_id: Optional[str] = None

    store_size_bytes: Optional[int] = None
    primary_size_bytes: Optional[int] = None
    doc_count: Optional[int] = None

    recovery_source_node: Optional[str] = None
    recovery_target_node: Optional[str] = None
    recovery_progress_percent: Optional[float] = None

    allocation_explanation: Optional[str] = None

    collected_at: datetime


class IndexSnapshot(BaseModel):
    index_name: str
    uuid: str
    collected_at: datetime

    doc_count: int
    deleted_doc_count: int

    store_size_bytes: int
    primary_size_bytes: int

    number_of_shards: int
    number_of_replicas: int
    total_shards: int

    search_query_total: int
    search_query_time_ms: int
    indexing_index_total: int
    indexing_index_time_ms: int

    segment_count: int
    segment_memory_bytes: int

    refresh_interval_ms: int
    codec: str
    lifecycle_policy: Optional[str] = None
    read_only: bool
    read_only_allow_delete: bool

    field_count: int
    has_keyword_explosion: bool

    source_api: str = "_stats"
    source_version: str = ""
    raw_response_hash: str = ""


class CollectionResult(BaseModel):
    cluster_snapshot: Optional[ClusterSnapshot] = None
    node_snapshots: dict[str, NodeSnapshot] = Field(default_factory=dict)
    index_snapshots: dict[str, IndexSnapshot] = Field(default_factory=dict)
    shard_states: list[ShardState] = Field(default_factory=list)
    collected_at: datetime
    errors: list[str] = Field(default_factory=list)
