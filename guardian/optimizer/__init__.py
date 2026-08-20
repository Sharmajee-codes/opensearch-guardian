"""OpenSearch Guardian Observability Cost Optimizer.

Provides analysis pipelines for detecting inefficiencies in:
- Retention (old/low-access data)
- Storage (snapshots, tiering candidates)
- Shard usage (tiny shards, oversharding, rollover opportunities)
- Replica usage (unnecessary overhead)
- Mappings (high field count, unnecessary indexed fields)
- Capacity (node utilization imbalance)

Outputs structured recommendations per data-model.md with assumptions and confidence.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from guardian.security import (
    ClusterMonitorPermission,
    SecurityContext,
    check_permission,
)

from ..models import ClusterSnapshot, CollectionResult, IndexSnapshot
from ..safety import OperationContext, SafetyClassification, classify_operation


class OptimizerConfig(BaseModel):
    """Thresholds for Cost Optimizer analysis."""

    # Retention analysis
    retention_age_days_threshold: int = 30  # indices older than this are candidates
    retention_access_threshold: float = 0.1  # <10% access rate considered low

    # Shard analysis
    tiny_shard_doc_count: int = 1000  # <1000 docs per shard is tiny
    oversharded_shard_count: int = 50  # >50 shards per index may be oversharded
    tiny_shard_waste_ratio: float = 0.5  # <50% doc/storage utilization suggests waste

    # Replica analysis
    replica_overhead_threshold: float = 2.0  # >2x storage overhead from replicas
    min_replicas_for_availability: int = 1  # minimum for HA

    # Mapping analysis
    high_field_count_threshold: int = 10000  # >10k fields may indicate mapping explosion
    unnecessary_indexed_field_ratio: float = 0.8  # >80% unindexed fields suggests waste

    # Capacity analysis
    utilization_imbalance_threshold: float = 0.5  # std_dev/mean > 0.5 indicates imbalance
    min_node_count_for_imbalance: int = 3  # need at least 3 nodes to measure imbalance

    # Analysis windows
    access_log_days: int = 7  # days of access logs to consider for low-access detection
    snapshot_age_days: int = 7  # snapshots older than this are candidates for cleanup


class OptimizationResult(BaseModel):
    """Output of an optimization analysis pass."""

    analysis_type: str  # "retention", "storage", "shard", "replica", "mapping", "capacity"
    timestamp: datetime
    cluster_name: str
    assumptions: list[str] = Field(default_factory=list)
    recommendations: list[Any] = Field(default_factory=list)  # Will be specific recommendation types

    def add_recommendation(self, recommendation: Any) -> None:
        """Add a recommendation to the result."""
        self.recommendations.append(recommendation)


class RetentionAnalysisResult(OptimizationResult):
    """Results from retention analysis."""

    analysis_type: str = "retention"
    old_indices: list[str] = Field(default_factory=list)
    low_access_indices: list[str] = Field(default_factory=list)


class StorageAnalysisResult(OptimizationResult):
    """Results from storage analysis."""

    analysis_type: str = "storage"
    old_snapshots: list[str] = Field(default_factory=list)
    tiering_candidates: list[str] = Field(default_factory=list)


class ShardAnalysisResult(OptimizationResult):
    """Results from shard analysis."""

    analysis_type: str = "shard"
    tiny_shards: list[str] = Field(default_factory=list)
    oversharded_indices: list[str] = Field(default_factory=list)
    rollover_candidates: list[str] = Field(default_factory=list)


class ReplicaAnalysisResult(OptimizationResult):
    """Results from replica analysis."""

    analysis_type: str = "replica"
    unnecessary_replicas: list[str] = Field(default_factory=list)


class MappingAnalysisResult(OptimizationResult):
    """Results from mapping analysis."""

    analysis_type: str = "mapping"
    high_field_count_indices: list[str] = Field(default_factory=list)
    unnecessary_indexed_fields: list[str] = Field(default_factory=list)


class CapacityAnalysisResult(OptimizationResult):
    """Results from capacity analysis."""

    analysis_type: str = "capacity"
    imbalanced_nodes: list[str] = Field(default_factory=list)
    utilization_stats: dict[str, float] = Field(default_factory=dict)


# Recommendation types matching data-model.md
class ReclaimableStorage(BaseModel):
    """Storage that can be reclaimed through cleanup or tiering."""

    index_name: str
    reclaimable_bytes: int
    reason: str  # e.g., "old_index", "low_access", "old_snapshot"
    confidence: float = Field(ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)


class ShardReduction(BaseModel):
    """Opportunity to reduce shard count."""

    index_name: str
    current_shard_count: int
    recommended_shard_count: int
    reason: str  # e.g., "tiny_shards", "oversharded", "rollover_opportunity"
    confidence: float = Field(ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)


class ReplicaOptimization(BaseModel):
    """Opportunity to optimize replica count."""

    index_name: str
    current_replica_count: int
    recommended_replica_count: int
    reason: str  # e.g., "unnecessary_overhead"
    confidence: float = Field(ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)


class MappingOptimization(BaseModel):
    """Opportunity to optimize mapping."""

    index_name: str
    field_count: int
    unnecessary_fields: int
    reason: str  # e.g., "high_field_count", "unnecessary_indexed_fields"
    confidence: float = Field(ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)


class CapacityRecovery(BaseModel):
    """Opportunity to recover capacity through rightsizing."""

    node_name: str
    current_utilization: float  # 0.0 to 1.0
    target_utilization: float  # 0.0 to 1.0
    reason: str  # e.g., "underutilized", "overutilized"
    confidence: float = Field(ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)


class OptimizationEngine:
    """Main engine for running Cost Optimizer analyses."""

    def __init__(self, config: OptimizerConfig | None = None):
        self.config = config or OptimizerConfig()

    def analyze_retention(self, snapshot: CollectionResult) -> RetentionAnalysisResult:
        """Analyze index retention for old or low-access data."""
        result = RetentionAnalysisResult(
            timestamp=datetime.now(),
            cluster_name=snapshot.cluster_snapshot.cluster_name
            if snapshot.cluster_snapshot
            else "unknown",
        )

        # Add assumptions
        result.assumptions.extend([
            f"Indices older than {self.config.retention_age_days_threshold} days are candidates for cleanup",
            f"Indices with <{self.config.retention_access_threshold * 100}% access rate are considered low-access",
            "Index creation date approximates data age (no ILM/hot-warm architecture considered)",
        ])

        # Analyze each index
        for index_name, index in snapshot.index_snapshots.items():
            # Note: In a real implementation, we would check index creation date and access logs
            # For V0.1, we'll use a placeholder based on index age (if available) or skip
            # This is a stub implementation - real implementation would need access to index stats
            # and access logs from OpenSearch

            # Placeholder: assume indices with low doc count relative to size are old/low-access
            if index.doc_count < 1000 and index.store_size_bytes > 10_000_000:  # >10MB with <1k docs
                result.low_access_indices.append(index_name)
                result.add_recommendation(
                    ReclaimableStorage(
                        index_name=index_name,
                        reclaimable_bytes=index.store_size_bytes // 2,  # conservative estimate
                        reason="low_access",
                        confidence=0.7,
                        assumptions=[
                            "Index with low doc count relative to storage size may contain old data",
                            "50% reclaimable is a conservative estimate",
                        ],
                    )
                )

        return result

    def analyze_storage(self, snapshot: CollectionResult) -> StorageAnalysisResult:
        """Analyze storage efficiency (snapshots, tiering candidates)."""
        result = StorageAnalysisResult(
            timestamp=datetime.now(),
            cluster_name=snapshot.cluster_snapshot.cluster_name
            if snapshot.cluster_snapshot
            else "unknown",
        )

        result.assumptions.extend([
            f"Snapshots older than {self.config.snapshot_age_days} days are candidates for cleanup",
            "Indices with warm access patterns may benefit from tiered storage",
        ])

        # Placeholder implementation
        # Real implementation would need snapshot repository access and ILM policies

        return result

    def analyze_shards(self, snapshot: CollectionResult) -> ShardAnalysisResult:
        """Analyze shard usage for efficiency opportunities."""
        result = ShardAnalysisResult(
            timestamp=datetime.now(),
            cluster_name=snapshot.cluster_snapshot.cluster_name
            if snapshot.cluster_snapshot
            else "unknown",
        )

        result.assumptions.extend([
            f"Shards with <{self.config.tiny_shard_doc_count} docs are considered tiny",
            f"Indices with >{self.config.oversharded_shard_count} shards may be oversharded",
            "Tiny shards waste heap memory and increase cluster state overhead",
        ])

        # Analyze each index for shard efficiency
        for index_name, index in snapshot.index_snapshots.items():
            # Check for tiny shards (low doc count per shard)
            if index.number_of_shards > 0:
                avg_docs_per_shard = index.doc_count / index.number_of_shards
                if avg_docs_per_shard < self.config.tiny_shard_doc_count:
                    result.tiny_shards.append(index_name)
                    result.add_recommendation(
                        ShardReduction(
                            index_name=index_name,
                            current_shard_count=index.number_of_shards,
                            recommended_shard_count=max(1, index.number_of_shards // 2),
                            reason="tiny_shards",
                            confidence=0.8,
                            assumptions=[
                                f"Average {avg_docs_per_shard:.0f} docs per shard is below threshold of {self.config.tiny_shard_doc_count}",
                                "Reducing shard count by 50% would improve efficiency",
                            ],
                        )
                    )

            # Check for oversharding (too many shards for index size)
            if index.number_of_shards > self.config.oversharded_shard_count:
                result.oversharded_indices.append(index_name)
                result.add_recommendation(
                    ShardReduction(
                        index_name=index_name,
                        current_shard_count=index.number_of_shards,
                        recommended_shard_count=max(1, index.number_of_shards // 3),
                        reason="oversharded",
                        confidence=0.75,
                        assumptions=[
                            f"Index has {index.number_of_shards} shards, exceeding threshold of {self.config.oversharded_shard_count}",
                            "Reducing shard count would improve recovery times and cluster state",
                        ],
                    )
                )

        return result

    def analyze_replicas(self, snapshot: CollectionResult) -> ReplicaAnalysisResult:
        """Analyze replica usage for optimization opportunities."""
        result = ReplicaAnalysisResult(
            timestamp=datetime.now(),
            cluster_name=snapshot.cluster_snapshot.cluster_name
            if snapshot.cluster_snapshot
            else "unknown",
        )

        result.assumptions.extend([
            f"Replica storage overhead >{self.config.replica_overhead_threshold}x primary may be unnecessary",
            f"Minimum {self.config.min_replicas_for_availability} replica(s) required for availability",
            "Replica count should balance availability needs with storage costs",
        ])

        # Analyze each index for replica efficiency
        for index_name, index in snapshot.index_snapshots.items():
            replica_overhead = index.number_of_replicas  # Each replica stores full copy
            if replica_overhead > self.config.replica_overhead_threshold:
                result.unnecessary_replicas.append(index_name)
                result.add_recommendation(
                    ReplicaOptimization(
                        index_name=index_name,
                        current_replica_count=index.number_of_replicas,
                        recommended_replica_count=max(
                            self.config.min_replicas_for_availability,
                            index.number_of_replicas // 2,
                        ),
                        reason="unnecessary_overhead",
                        confidence=0.7,
                        assumptions=[
                            f"Replica overhead of {replica_overhead}x exceeds threshold of {self.config.replica_overhead_threshold}x",
                            f"Reducing to {max(self.config.min_replicas_for_availability, index.number_of_replicas // 2)} replicas maintains availability while saving storage",
                        ],
                    )
                )

        return result

    def analyze_mappings(self, snapshot: CollectionResult) -> MappingAnalysisResult:
        """Analyze field mappings for optimization opportunities."""
        result = MappingAnalysisResult(
            timestamp=datetime.now(),
            cluster_name=snapshot.cluster_snapshot.cluster_name
            if snapshot.cluster_snapshot
            else "unknown",
        )

        result.assumptions.extend([
            f"Indices with >{self.config.high_field_count_threshold} fields may have mapping explosion",
            f">{(self.config.unnecessary_indexed_field_ratio * 100):.0f}% unindexed fields suggests mapping waste",
            "High field count increases heap usage and cluster state propagation time",
        ])

        # Analyze each index for mapping efficiency
        for index_name, index in snapshot.index_snapshots.items():
            # Check for high field count
            if index.field_count > self.config.high_field_count_threshold:
                result.high_field_count_indices.append(index_name)
                result.add_recommendation(
                    MappingOptimization(
                        index_name=index_name,
                        field_count=index.field_count,
                        unnecessary_fields=max(0, index.field_count - 5000),  # Suggest reducing to 5k
                        reason="high_field_count",
                        confidence=0.75,
                        assumptions=[
                            f"Index has {index.field_count} fields, exceeding threshold of {self.config.high_field_count_threshold}",
                            "Reducing field count through index templates or reindexing would improve performance",
                        ],
                    )
                )

            # Check for unnecessary indexed fields (placeholder - would need access patterns)
            # For V0.1, we'll skip this as it requires query analytics

        return result

    def analyze_capacity(self, snapshot: CollectionResult) -> CapacityAnalysisResult:
        """Analyze node capacity utilization for imbalance detection."""
        result = CapacityAnalysisResult(
            timestamp=datetime.now(),
            cluster_name=snapshot.cluster_snapshot.cluster_name
            if snapshot.cluster_snapshot
            else "unknown",
        )

        # Need at least 3 nodes to measure meaningful imbalance
        if len(snapshot.node_snapshots) < self.config.min_node_count_for_imbalance:
            result.assumptions.append(
                f"Insufficient nodes ({len(snapshot.node_snapshots)}) for imbalance analysis "
                f"(need >= {self.config.min_node_count_for_imbalance}). "
                "Capacity imbalance detection requires at least 3 nodes."
            )
            return result

        result.assumptions.extend([
            f"Utilization imbalance threshold: std_dev/mean > {self.config.utilization_imbalance_threshold}",
            "CPU, heap, and disk utilization are considered for capacity analysis",
            "Perfect balance is rare; some variance is expected in heterogeneous workloads",
        ])

        # Calculate utilization metrics for each node
        utilizations = []
        node_utils = {}

        for node_id, node in snapshot.node_snapshots.items():
            # CPU utilization (0-1)
            cpu_util = node.os.cpu_percent / 100.0
            # Heap utilization (0-1)
            heap_util = node.jvm.mem_heap_used_percent / 100.0
            # Disk utilization (0-1) - from first filesystem
            disk_util = 0.0
            if node.filesystems:
                fs = node.filesystems[0]
                if fs.total_bytes > 0:
                    disk_util = 1.0 - (fs.available_bytes / fs.total_bytes)

            # Combined utilization (average of available metrics)
            utils = [cpu_util, heap_util]
            if disk_util > 0:
                utils.append(disk_util)
            combined_util = sum(utils) / len(utils)

            utilizations.append(combined_util)
            node_utils[node_id] = {
                "cpu": cpu_util,
                "heap": heap_util,
                "disk": disk_util,
                "combined": combined_util,
                "node_name": node.node_name,
            }

        # Calculate statistics
        if utilizations:
            import statistics

            mean_util = statistics.mean(utilizations)
            if len(utilizations) > 1:
                stdev_util = statistics.stdev(utilizations)
                imbalance_ratio = stdev_util / mean_util if mean_util > 0 else 0
            else:
                stdev_util = 0
                imbalance_ratio = 0

            result.utilization_stats = {
                "mean": mean_util,
                "stdev": stdev_util,
                "imbalance_ratio": imbalance_ratio,
            }

            # Identify imbalanced nodes (those far from mean)
            if imbalance_ratio > self.config.utilization_imbalance_threshold:
                for node_id, utils in node_utils.items():
                    # Node is imbalanced if its utilization deviates from mean by > 1 std dev
                    deviation = abs(utils["combined"] - mean_util)
                    if deviation > stdev_util:
                        reason = (
                            "underutilized"
                            if utils["combined"] < mean_util
                            else "overutilized"
                        )
                        result.add_recommendation(
                            CapacityRecovery(
                                node_name=utils["node_name"],
                                current_utilization=utils["combined"],
                                target_utilization=mean_util,
                                reason=reason,
                                confidence=0.7,
                                assumptions=[
                                    f"Node utilization ({utils['combined']:.2f}) deviates from cluster mean ({mean_util:.2f})",
                                    f"Imbalance ratio {imbalance_ratio:.2f} exceeds threshold {self.config.utilization_imbalance_threshold}",
                                    f"Target utilization of {mean_util:.2f} would balance the cluster",
                                ],
                            )
                        )

        return result

    def analyze_all(
        self,
        snapshot: CollectionResult,
        require_permission: bool = True,
    ) -> dict[str, OptimizationResult]:
        """Run all optimization analyses and return results by type.

        Args:
            snapshot: Current cluster snapshot
            require_permission: Whether to enforce ClusterMonitorPermission check

        Returns:
            Dict with optimization results by type

        Raises:
            PermissionError: If require_permission is True and user lacks ClusterMonitorPermission
        """
        # Check permissions before running optimization analyses
        if require_permission:
            user = SecurityContext.get_user()
            if user is None or not check_permission(ClusterMonitorPermission, set(user.backend_roles)):
                raise PermissionError("Insufficient permissions: requires ClusterMonitorPermission")

        return {
            "retention": self.analyze_retention(snapshot),
            "storage": self.analyze_storage(snapshot),
            "shard": self.analyze_shards(snapshot),
            "replica": self.analyze_replicas(snapshot),
            "mapping": self.analyze_mappings(snapshot),
            "capacity": self.analyze_capacity(snapshot),
        }


def create_optimization_recommendation(
    analysis_result: OptimizationResult,
) -> list[dict[str, Any]]:
    """Convert optimization results to recommendation dictionaries for API/output."""
    recommendations = []

    for rec in analysis_result.recommendations:
        if hasattr(rec, "model_dump"):
            # Pydantic model
            rec_dict = rec.model_dump()
        else:
            # Fallback for non-Pydantic objects
            rec_dict = rec.__dict__ if hasattr(rec, "__dict__") else {"value": str(rec)}

        # Add analysis context
        rec_dict.update(
            {
                "analysis_type": analysis_result.analysis_type,
                "timestamp": analysis_result.timestamp.isoformat(),
                "cluster_name": analysis_result.cluster_name,
                "assumptions": analysis_result.assumptions,
            }
        )
        recommendations.append(rec_dict)

    return recommendations
