"""Trend Analyzer — analyzes utilization trends from historical snapshots.

Provides deterministic trend analysis for capacity planning.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class ResourceTrend:
    """Trend for a single resource over time."""

    resource: str  # "cpu", "heap", "disk", "shards", "indices"
    values: list[float]
    timestamps: list[datetime]
    slope: float  # Rate of change per day
    r_squared: float  # Goodness of fit for linear trend
    is_increasing: bool
    is_stable: bool  # Low variance around trend
    volatility: float  # Standard deviation of residuals


@dataclass
class UtilizationTrend:
    """Overall utilization trend analysis."""

    cluster_name: str
    resource_trends: dict[str, ResourceTrend]
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    data_points: int = 0
    time_span_days: float = 0.0


class TrendAnalyzer:
    """Analyzes utilization trends from historical snapshots."""

    def __init__(self, min_points: int = 7) -> None:
        self.min_points = min_points

    def analyze(
        self,
        snapshots: list[Any],  # CollectionResult list
    ) -> UtilizationTrend | None:
        """Analyze trends from a list of historical snapshots.

        Args:
            snapshots: List of CollectionResult objects (oldest first)

        Returns:
            UtilizationTrend with per-resource analysis, or None if insufficient data
        """
        if len(snapshots) < self.min_points:
            return None

        # Extract resource values over time
        resources = {
            "cpu": [],
            "heap": [],
            "disk": [],
            "shards": [],
            "indices": [],
            "docs": [],
        }
        timestamps = []

        for snapshot in snapshots:
            timestamps.append(snapshot.collected_at)
            util = self._extract_utilization(snapshot)
            for resource, value in util.items():
                if resource in resources:
                    resources[resource].append(value)

        # Analyze each resource
        resource_trends = {}
        for resource, values in resources.items():
            if len(values) >= 2:
                trend = self._analyze_resource_trend(
                    resource, values, timestamps[:len(values)]
                )
                resource_trends[resource] = trend

        if not resource_trends:
            return None

        time_span = (timestamps[-1] - timestamps[0]).total_seconds() / 86400

        return UtilizationTrend(
            cluster_name=snapshots[0].cluster_snapshot.cluster_name
            if snapshots[0].cluster_snapshot
            else "unknown",
            resource_trends=resource_trends,
            data_points=len(snapshots),
            time_span_days=time_span,
        )

    def _extract_utilization(self, snapshot: Any) -> dict[str, float]:
        """Extract utilization metrics from a snapshot."""
        result = {}

        if snapshot.cluster_snapshot:
            cs = snapshot.cluster_snapshot
            result["shards"] = float(cs.active_shards + cs.unassigned_shards)
            result["indices"] = float(len(snapshot.index_snapshots))

        if snapshot.node_snapshots:
            cpu_values = []
            heap_values = []
            disk_values = []
            doc_values = []

            for node in snapshot.node_snapshots.values():
                cpu_values.append(node.os.cpu_percent / 100.0)
                heap_values.append(node.jvm.mem_heap_used_percent / 100.0)
                doc_values.append(node.indices_doc_count or 0)

                if node.filesystems:
                    fs = node.filesystems[0]
                    if fs.total_bytes > 0:
                        disk_util = 1.0 - (fs.available_bytes / fs.total_bytes)
                        disk_values.append(disk_util)

            if cpu_values:
                result["cpu"] = statistics.mean(cpu_values)
            if heap_values:
                result["heap"] = statistics.mean(heap_values)
            if disk_values:
                result["disk"] = statistics.mean(disk_values)
            if doc_values:
                result["docs"] = statistics.mean(doc_values)

        return result

    def _analyze_resource_trend(
        self,
        resource: str,
        values: list[float],
        timestamps: list[datetime],
    ) -> ResourceTrend:
        """Analyze trend for a single resource."""
        n = len(values)
        x = [i for i in range(n)]

        # Linear regression
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(values)

        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

        if denominator == 0:
            slope = 0.0
            r_squared = 1.0
        else:
            slope = numerator / denominator
            # Calculate R-squared
            ss_tot = sum((yi - mean_y) ** 2 for yi in values)
            if ss_tot == 0:
                r_squared = 1.0
            else:
                predicted = [slope * (xi - mean_x) + mean_y for xi in x]
                ss_res = sum((values[i] - predicted[i]) ** 2 for i in range(n))
                r_squared = 1 - (ss_res / ss_tot)

        # Volatility (std dev of residuals)
        if denominator == 0:
            volatility = 0.0
        else:
            predicted = [slope * (xi - mean_x) + mean_y for xi in x]
            residuals = [values[i] - predicted[i] for i in range(n)]
            volatility = statistics.stdev(residuals) if len(residuals) > 1 else 0.0

        # Per-day slope (normalize by time interval)
        if len(timestamps) > 1:
            time_interval = (timestamps[-1] - timestamps[0]).total_seconds() / 86400 / (n - 1)
            slope_per_day = slope / time_interval if time_interval > 0 else slope
        else:
            slope_per_day = slope

        is_increasing = slope_per_day > 0.001  # Meaningful increase threshold
        is_stable = volatility < 0.05  # Low volatility threshold

        return ResourceTrend(
            resource=resource,
            values=values,
            timestamps=timestamps,
            slope=slope_per_day,
            r_squared=r_squared,
            is_increasing=is_increasing,
            is_stable=is_stable,
            volatility=volatility,
        )

    def get_resource_growth_rate(
        self, trend: UtilizationTrend, resource: str
    ) -> float | None:
        """Get the daily growth rate for a specific resource."""
        if resource in trend.resource_trends:
            return trend.resource_trends[resource].slope
        return None

    def is_resource_critical(
        self,
        trend: UtilizationTrend,
        resource: str,
        threshold: float = 0.8,
    ) -> bool:
        """Check if a resource is projected to exceed threshold within 30 days."""
        rt = trend.resource_trends.get(resource)
        if not rt:
            return False

        current = rt.values[-1] if rt.values else 0.0
        projected_30d = current + (rt.slope * 30)

        return projected_30d >= threshold

    def get_trend_summary(self, trend: UtilizationTrend) -> dict[str, Any]:
        """Generate a human-readable trend summary."""
        summary = {
            "cluster": trend.cluster_name,
            "data_points": trend.data_points,
            "time_span_days": round(trend.time_span_days, 1),
            "resources": {},
        }

        for resource, rt in trend.resource_trends.items():
            current = rt.values[-1] if rt.values else 0.0
            projected_7d = current + (rt.slope * 7)
            projected_30d = current + (rt.slope * 30)

            summary["resources"][resource] = {
                "current": round(current, 3),
                "slope_per_day": round(rt.slope, 6),
                "r_squared": round(rt.r_squared, 3),
                "is_increasing": rt.is_increasing,
                "is_stable": rt.is_stable,
                "volatility": round(rt.volatility, 4),
                "projected_7d": round(projected_7d, 3),
                "projected_30d": round(projected_30d, 3),
            }

        return summary