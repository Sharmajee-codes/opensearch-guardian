"""Capacity Planner — deterministic capacity planning engine.

Projects future resource needs based on historical trends from the
Cost Optimizer and collector snapshots. Uses linear regression and
exponential smoothing for deterministic projections.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from guardian.models import (
    CollectionResult,
)
from guardian.optimizer import (
    CapacityAnalysisResult,
    CapacityRecovery,
    OptimizationEngine,
    OptimizerConfig,
)
from guardian.security import (
    ClusterMonitorPermission,
    SecurityContext,
    check_permission,
)


class ProjectionWindow(str, Enum):
    """Time windows for capacity projections."""

    ONE_WEEK = "1w"
    ONE_MONTH = "1m"
    THREE_MONTHS = "3m"
    SIX_MONTHS = "6m"
    ONE_YEAR = "1y"

    def to_timedelta(self) -> timedelta:
        """Convert to timedelta."""
        mapping = {
            ProjectionWindow.ONE_WEEK: timedelta(weeks=1),
            ProjectionWindow.ONE_MONTH: timedelta(days=30),
            ProjectionWindow.THREE_MONTHS: timedelta(days=90),
            ProjectionWindow.SIX_MONTHS: timedelta(days=180),
            ProjectionWindow.ONE_YEAR: timedelta(days=365),
        }
        return mapping[self]


class GrowthRate(str, Enum):
    """Growth rate estimation methods."""

    LINEAR = "linear"  # Linear extrapolation from historical data
    EXPONENTIAL = "exponential"  # Exponential growth from compounding
    CONSERVATIVE = "conservative"  # Linear with 20% buffer
    AGGRESSIVE = "aggressive"  # Exponential with 50% buffer


@dataclass
class ProjectionConfig:
    """Configuration for capacity projections."""

    # Default projection window
    default_window: ProjectionWindow = ProjectionWindow.THREE_MONTHS

    # Growth rate method
    growth_method: GrowthRate = GrowthRate.LINEAR

    # Minimum historical data points needed
    min_history_points: int = 7

    # Confidence thresholds
    high_confidence_threshold: float = 0.8
    low_confidence_threshold: float = 0.5

    # Safety buffers
    buffer_percent: float = 0.2  # 20% buffer on top of projection

    # Node sizing constraints
    min_nodes: int = 3
    max_nodes: int = 100
    target_utilization: float = 0.7  # Target 70% utilization

    # Resource limits (per node)
    max_heap_gb: int = 32
    max_disk_gb: int = 2000
    max_cpu_cores: int = 64


@dataclass
class UtilizationProjection:
    """Projected utilization for a specific resource."""

    resource: str  # "cpu", "heap", "disk", "combined"
    current_value: float  # 0.0 to 1.0
    projected_value: float  # 0.0 to 1.0+
    growth_rate_per_day: float
    window: ProjectionWindow
    confidence: float  # 0.0 to 1.0
    assumptions: list[str] = field(default_factory=list)
    projected_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SizingRecommendation:
    """Node sizing and count recommendation."""

    # Node count
    current_node_count: int
    recommended_node_count: int
    min_node_count: int
    max_node_count: int

    # Per-node resources
    recommended_heap_gb: int
    recommended_disk_gb: int
    recommended_cpu_cores: int

    # Confidence and reasoning
    confidence: float  # 0.0 to 1.0
    reasoning: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    projection_window: ProjectionWindow = ProjectionWindow.THREE_MONTHS
    projected_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Cost impact (qualitative)
    estimated_cost_change: str = "neutral"  # "decrease", "neutral", "increase"


class CapacityPlanner:
    """Main capacity planning engine.

    Takes optimizer analysis results and historical snapshots to project
    future capacity needs and provide sizing recommendations.
    """

    def __init__(
        self,
        config: ProjectionConfig | None = None,
        optimizer_config: OptimizerConfig | None = None,
    ) -> None:
        self.config = config or ProjectionConfig()
        self.optimizer_engine = OptimizationEngine(optimizer_config or OptimizerConfig())

    def plan_capacity(
        self,
        current_snapshot: CollectionResult,
        historical_snapshots: list[CollectionResult],
        require_permission: bool = True,
    ) -> dict[str, Any]:
        """Generate a complete capacity plan.

        Args:
            current_snapshot: Latest cluster snapshot
            historical_snapshots: List of historical snapshots (oldest first)
            require_permission: Whether to enforce ClusterMonitorPermission check

        Returns:
            Dict with projections, sizing recommendations, and metadata

        Raises:
            PermissionError: If require_permission is True and user lacks ClusterMonitorPermission
        """
        # Check permissions before running capacity planning
        if require_permission:
            user = SecurityContext.get_user()
            if user is None or not check_permission(ClusterMonitorPermission, set(user.backend_roles)):
                raise PermissionError("Insufficient permissions: requires ClusterMonitorPermission")

        # Run optimizer analysis on current snapshot (permission already checked by planner)
        optimizer_results = self.optimizer_engine.analyze_all(current_snapshot, require_permission=False)
        capacity_analysis = optimizer_results.get("capacity")

        # Analyze utilization trends from history
        trends = self._analyze_utilization_trends(historical_snapshots)

        # Project utilization for each resource
        projections = self._project_utilization(
            current_snapshot, trends
        )

        # Generate sizing recommendation
        sizing = self._generate_sizing_recommendation(
            current_snapshot, projections, capacity_analysis
        )

        return {
            "projections": [p.__dict__ for p in projections],
            "sizing_recommendation": sizing.__dict__,
            "optimizer_analysis": self._serialize_optimizer_results(optimizer_results),
            "cluster_name": current_snapshot.cluster_snapshot.cluster_name if current_snapshot.cluster_snapshot else "unknown",
            "generated_at": datetime.now(UTC).isoformat(),
            "projection_window": self.config.default_window.value,
        }

    def _analyze_utilization_trends(
        self,
        historical_snapshots: list[CollectionResult],
    ) -> dict[str, list[float]]:
        """Extract utilization trends from historical snapshots.

        Returns dict of resource -> list of utilization values over time.
        """
        if len(historical_snapshots) < self.config.min_history_points:
            return {}

        trends: dict[str, list[float]] = {
            "cpu": [],
            "heap": [],
            "disk": [],
            "combined": [],
        }

        for snapshot in historical_snapshots:
            util = self._calculate_utilization(snapshot)
            for resource, value in util.items():
                trends[resource].append(value)

        return trends

    def _calculate_utilization(
        self, snapshot: CollectionResult
    ) -> dict[str, float]:
        """Calculate utilization metrics from a snapshot."""
        if not snapshot.node_snapshots:
            return {"cpu": 0.0, "heap": 0.0, "disk": 0.0, "combined": 0.0}

        cpu_values = []
        heap_values = []
        disk_values = []

        for node in snapshot.node_snapshots.values():
            # CPU
            cpu_values.append(node.os.cpu_percent / 100.0)
            # Heap
            heap_values.append(node.jvm.mem_heap_used_percent / 100.0)
            # Disk (from first filesystem)
            if node.filesystems:
                fs = node.filesystems[0]
                if fs.total_bytes > 0:
                    disk_util = 1.0 - (fs.available_bytes / fs.total_bytes)
                    disk_values.append(disk_util)

        result = {}
        if cpu_values:
            result["cpu"] = statistics.mean(cpu_values)
        if heap_values:
            result["heap"] = statistics.mean(heap_values)
        if disk_values:
            result["disk"] = statistics.mean(disk_values)

        # Combined (average of available)
        available = [v for v in [result.get("cpu"), result.get("heap"), result.get("disk")] if v is not None]
        if available:
            result["combined"] = statistics.mean(available)

        return result

    def _project_utilization(
        self,
        current_snapshot: CollectionResult,
        trends: dict[str, list[float]],
    ) -> list[UtilizationProjection]:
        """Project utilization for each resource over the configured window."""
        projections = []
        current_util = self._calculate_utilization(current_snapshot)

        days = self.config.default_window.to_timedelta().days

        for resource in ["cpu", "heap", "disk", "combined"]:
            current_value = current_util.get(resource, 0.0)
            history = trends.get(resource, [])

            if len(history) >= 2:
                # Calculate growth rate from history
                growth_rate = self._calculate_growth_rate(history)
                projected_value = self._apply_growth_projection(
                    current_value, growth_rate, days
                )
                confidence = self._calculate_confidence(history, growth_rate)
            else:
                # No history - use conservative estimate
                growth_rate = 0.0
                projected_value = current_value * (1 + self.config.buffer_percent)
                confidence = self.config.low_confidence_threshold

            projections.append(UtilizationProjection(
                resource=resource,
                current_value=current_value,
                projected_value=projected_value,
                growth_rate_per_day=growth_rate,
                window=self.config.default_window,
                confidence=confidence,
                assumptions=self._build_projection_assumptions(
                    resource, current_value, projected_value, len(history)
                ),
            ))

        return projections

    def _calculate_growth_rate(self, history: list[float]) -> float:
        """Calculate daily growth rate from historical data.

        Uses linear regression slope for deterministic projection.
        """
        if len(history) < 2:
            return 0.0

        n = len(history)
        x = list(range(n))
        y = history

        # Linear regression: slope = sum((x - mean_x)*(y - mean_y)) / sum((x - mean_x)^2)
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        slope = numerator / denominator
        return max(0.0, slope)  # Don't project negative growth

    def _apply_growth_projection(
        self,
        current_value: float,
        daily_growth_rate: float,
        days: int,
    ) -> float:
        """Apply growth projection based on configured method."""
        if self.config.growth_method == GrowthRate.LINEAR:
            projected = current_value + (daily_growth_rate * days)
        elif self.config.growth_method == GrowthRate.EXPONENTIAL:
            # Compound growth: P = P0 * (1 + r)^t
            projected = current_value * ((1 + daily_growth_rate) ** days)
        elif self.config.growth_method == GrowthRate.CONSERVATIVE:
            projected = current_value + (daily_growth_rate * days * 1.2)
        elif self.config.growth_method == GrowthRate.AGGRESSIVE:
            projected = current_value * ((1 + daily_growth_rate * 1.5) ** days)
        else:
            projected = current_value + (daily_growth_rate * days)

        # Apply safety buffer
        return projected * (1 + self.config.buffer_percent)

    def _calculate_confidence(
        self, history: list[float], growth_rate: float
    ) -> float:
        """Calculate confidence in the projection based on data quality."""
        if len(history) < self.config.min_history_points:
            return self.config.low_confidence_threshold

        # Calculate R-squared (coefficient of determination) for linear fit
        if len(history) < 3:
            return self.config.low_confidence_threshold

        n = len(history)
        x = list(range(n))
        y = history

        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)

        ss_tot = sum((yi - mean_y) ** 2 for yi in y)
        if ss_tot == 0:
            return 1.0  # Perfect fit (constant)

        ss_res = sum((y[i] - (growth_rate * (x[i] - mean_x) + mean_y)) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot)

        return max(0.0, min(1.0, r_squared))

    def _build_projection_assumptions(
        self,
        resource: str,
        current: float,
        projected: float,
        history_points: int,
    ) -> list[str]:
        """Build human-readable assumptions for the projection."""
        assumptions = [
            f"Projection window: {self.config.default_window.value}",
            f"Growth method: {self.config.growth_method.value}",
            f"Safety buffer: {self.config.buffer_percent * 100:.0f}%",
        ]

        if history_points >= self.config.min_history_points:
            assumptions.append(f"Based on {history_points} historical data points")
        else:
            assumptions.append(f"Insufficient history ({history_points} points); using conservative estimate")

        if projected > 1.0:
            assumptions.append(
                f"Projected {resource} utilization ({projected:.1%}) exceeds 100% — "
                "capacity expansion required"
            )

        return assumptions

    def _generate_sizing_recommendation(
        self,
        current_snapshot: CollectionResult,
        projections: list[UtilizationProjection],
        capacity_analysis: CapacityAnalysisResult | None,
    ) -> SizingRecommendation:
        """Generate node sizing and count recommendation."""
        current_nodes = len(current_snapshot.node_snapshots)
        if current_nodes == 0:
            current_nodes = self.config.min_nodes

        # Find the most constrained resource projection
        combined_projection = next(
            (p for p in projections if p.resource == "combined"), None
        )
        max_projected_util = combined_projection.projected_value if combined_projection else 0.0

        # Calculate required node count to maintain target utilization
        if max_projected_util > 0:
            required_nodes = int(
                (current_nodes * max_projected_util) / self.config.target_utilization
            )
        else:
            required_nodes = current_nodes

        # Clamp to bounds
        recommended_nodes = max(
            self.config.min_nodes,
            min(self.config.max_nodes, required_nodes)
        )

        # Determine per-node sizing based on current snapshot
        recommended_heap = self._recommend_heap_size(current_snapshot)
        recommended_disk = self._recommend_disk_size(current_snapshot, recommended_nodes)
        recommended_cpu = self._recommend_cpu_cores(current_snapshot)

        # Build reasoning
        reasoning = [
            f"Current node count: {current_nodes}",
            f"Projected combined utilization: {max_projected_util:.1%}",
            f"Target utilization: {self.config.target_utilization:.0%}",
            f"Required nodes for target: {required_nodes}",
        ]

        if recommended_nodes > current_nodes:
            reasoning.append(f"Scale up from {current_nodes} to {recommended_nodes} nodes")
        elif recommended_nodes < current_nodes:
            reasoning.append(f"Scale down from {current_nodes} to {recommended_nodes} nodes")
        else:
            reasoning.append("Current node count is adequate for projected load")

        # Include optimizer findings
        if capacity_analysis:
            for rec in capacity_analysis.recommendations:
                if isinstance(rec, CapacityRecovery):
                    reasoning.append(
                        f"Optimizer: Node {rec.node_name} is {rec.reason} "
                        f"(current: {rec.current_utilization:.1%}, target: {rec.target_utilization:.1%})"
                    )

        assumptions = [
            f"Growth method: {self.config.growth_method.value}",
            f"Safety buffer: {self.config.buffer_percent * 100:.0f}%",
            f"Target utilization: {self.config.target_utilization:.0%}",
            "Assumes linear workload growth; burst capacity not modeled",
            "Per-node resource sizing based on current node specifications",
        ]

        # Determine cost impact
        if recommended_nodes > current_nodes:
            cost_change = "increase"
        elif recommended_nodes < current_nodes:
            cost_change = "decrease"
        else:
            cost_change = "neutral"

        # Confidence based on projection confidence
        avg_confidence = statistics.mean(p.confidence for p in projections) if projections else 0.5

        return SizingRecommendation(
            current_node_count=current_nodes,
            recommended_node_count=recommended_nodes,
            min_node_count=self.config.min_nodes,
            max_node_count=self.config.max_nodes,
            recommended_heap_gb=recommended_heap,
            recommended_disk_gb=recommended_disk,
            recommended_cpu_cores=recommended_cpu,
            confidence=avg_confidence,
            reasoning=reasoning,
            assumptions=assumptions,
            projection_window=self.config.default_window,
            estimated_cost_change=cost_change,
        )

    def _recommend_heap_size(self, snapshot: CollectionResult) -> int:
        """Recommend heap size based on current usage."""
        if not snapshot.node_snapshots:
            return 8  # Default 8GB

        max_heap = 0
        for node in snapshot.node_snapshots.values():
            heap_max_gb = node.jvm.mem_heap_max_bytes / (1024 ** 3)
            max_heap = max(max_heap, heap_max_gb)

        # Round up to next standard size, max 32GB
        standard_sizes = [4, 8, 16, 24, 32]
        for size in standard_sizes:
            if size >= max_heap:
                return size

        return self.config.max_heap_gb

    def _recommend_disk_size(
        self, snapshot: CollectionResult, node_count: int
    ) -> int:
        """Recommend per-node disk size."""
        if not snapshot.index_snapshots:
            return 100  # Default 100GB

        total_store = sum(idx.store_size_bytes for idx in snapshot.index_snapshots.values())
        total_store_gb = total_store / (1024 ** 3)

        # Per-node disk with replication factor
        replication_factor = 2  # Assume 1 replica by default
        per_node_gb = (total_store_gb * replication_factor) / node_count

        # Add 50% headroom
        per_node_gb *= 1.5

        # Round up to next standard size
        standard_sizes = [100, 200, 500, 1000, 2000]
        for size in standard_sizes:
            if size >= per_node_gb:
                return min(size, self.config.max_disk_gb)

        return self.config.max_disk_gb

    def _recommend_cpu_cores(self, snapshot: CollectionResult) -> int:
        """Recommend CPU cores based on current usage."""
        if not snapshot.node_snapshots:
            return 8  # Default 8 cores

        max_cpu = 0
        for node in snapshot.node_snapshots.values():
            cpu_util = node.os.cpu_percent / 100.0
            # Estimate total cores from utilization (this is approximate)
            # If we assume 8 cores and 50% util, that's 4 cores busy
            estimated_cores = 8  # Placeholder
            max_cpu = max(max_cpu, estimated_cores)

        standard_sizes = [4, 8, 16, 32, 64]
        for size in standard_sizes:
            if size >= max_cpu:
                return min(size, self.config.max_cpu_cores)

        return self.config.max_cpu_cores

    def _serialize_optimizer_results(
        self, results: dict[str, Any]
    ) -> dict[str, Any]:
        """Serialize optimizer results for output."""
        serialized = {}
        for key, result in results.items():
            if hasattr(result, "model_dump"):
                serialized[key] = result.model_dump()
            elif hasattr(result, "__dict__"):
                serialized[key] = result.__dict__
            else:
                serialized[key] = str(result)
        return serialized


def calculate_rightsizing(
    current_snapshot: CollectionResult,
    target_utilization: float = 0.7,
    growth_buffer: float = 0.2,
    require_permission: bool = True,
) -> dict[str, Any]:
    """Convenience function for quick rightsizing calculation.

    Args:
        current_snapshot: Current cluster snapshot
        target_utilization: Target utilization (0.0-1.0)
        growth_buffer: Additional buffer for growth (0.0-1.0)
        require_permission: Whether to enforce ClusterMonitorPermission check

    Returns:
        Dict with recommended node count and per-node resources

    Raises:
        PermissionError: If require_permission is True and user lacks ClusterMonitorPermission
    """
    if require_permission:
        user = SecurityContext.get_user()
        if user is None or not check_permission(ClusterMonitorPermission, set(user.backend_roles)):
            raise PermissionError("Insufficient permissions: requires ClusterMonitorPermission")

    config = ProjectionConfig(
        target_utilization=target_utilization,
        buffer_percent=growth_buffer,
    )
    planner = CapacityPlanner(config)

    # Use empty history for quick calculation
    result = planner.plan_capacity(current_snapshot, [], require_permission=False)

    return {
        "recommended_nodes": result["sizing_recommendation"]["recommended_node_count"],
        "heap_gb": result["sizing_recommendation"]["recommended_heap_gb"],
        "disk_gb": result["sizing_recommendation"]["recommended_disk_gb"],
        "cpu_cores": result["sizing_recommendation"]["recommended_cpu_cores"],
        "confidence": result["sizing_recommendation"]["confidence"],
    }