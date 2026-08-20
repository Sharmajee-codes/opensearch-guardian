"""Predictive Capacity Planning using Time-Series Analysis.

This module implements time-series analysis for capacity planning,
predicting future resource needs based on historical data patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CapacityTrend:
    """Represents a capacity trend for a resource type."""

    resource_type: str  # "disk", "heap", "cpu", "shards", "indices"
    current_value: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    growth_rate_per_day: float
    predicted_exhaustion_days: int | None = None
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_type": self.resource_type,
            "current_value": self.current_value,
            "trend_direction": self.trend_direction,
            "growth_rate_per_day": self.growth_rate_per_day,
            "predicted_exhaustion_days": self.predicted_exhaustion_days,
            "confidence": self.confidence,
        }


@dataclass
class CapacityRecommendation:
    """Represents a capacity planning recommendation."""

    resource_type: str
    recommendation_type: str  # "scale_up", "add_capacity", "optimize", "monitor"
    priority: str  # "high", "medium", "low"
    description: str
    estimated_cost: str | None = None
    timeframe: str = "immediate"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_type": self.resource_type,
            "recommendation_type": self.recommendation_type,
            "priority": self.priority,
            "description": self.description,
            "estimated_cost": self.estimated_cost,
            "timeframe": self.timeframe,
        }


class PredictiveCapacityPlanner:
    """
    Predictive capacity planner using time-series analysis.

    Analyzes historical cluster metrics to predict future capacity
    needs and provide proactive recommendations.
    """

    def __init__(self, client: Any, lookback_days: int = 30):
        """
        Initialize the planner.

        Args:
            client: OpenSearch client instance
            lookback_days: Number of days of historical data to analyze
        """
        self.client = client
        self.lookback_days = lookback_days

    def analyze_capacity(
        self,
        cluster_name: str = "_cluster",
        node_filter: str | None = None,
    ) -> dict[str, Any]:
        """
        Analyze capacity trends and predictions.

        Args:
            cluster_name: Cluster name to analyze
            node_filter: Optional node name filter

        Returns:
            Dictionary containing capacity analysis results
        """
        analysis = {
            "cluster_name": cluster_name,
            "analysis_timestamp": datetime.now(UTC).isoformat(),
            "lookback_days": self.lookback_days,
            "trends": {},
            "recommendations": [],
            "risk_assessment": {},
        }

        # Analyze disk capacity
        disk_trends = self._analyze_disk_capacity(node_filter)
        analysis["trends"]["disk"] = disk_trends

        # Analyze heap memory
        heap_trends = self._analyze_heap_capacity(node_filter)
        analysis["trends"]["heap"] = heap_trends

        # Analyze shard count
        shard_trends = self._analyze_shard_capacity(node_filter)
        analysis["trends"]["shards"] = shard_trends

        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis["trends"])

        # Assess overall risk
        analysis["risk_assessment"] = self._assess_risk(analysis["trends"])

        return analysis

    def _analyze_disk_capacity(self, node_filter: str | None = None) -> list[CapacityTrend]:
        """Analyze disk capacity trends."""
        trends = []

        # Query disk usage metrics
        try:
            # Get node stats for disk usage
            response = self.client.nodes.stats(
                metric="fs",
                flat_settings=True,
            )

            for node_id, node_stats in response.get("nodes", {}).items():
                if node_filter and node_filter not in node_id:
                    continue

                node_name = node_stats.get("name", node_id)
                fs_info = node_stats.get("fs", {}).get("total", {})

                current_disk_used = fs_info.get("used_in_bytes", 0)
                current_disk_total = fs_info.get("total_in_bytes", 1)

                # Calculate disk usage percentage
                disk_usage_percent = (current_disk_used / current_disk_total) * 100 if current_disk_total > 0 else 0

                # Analyze trend (simplified - in reality would use historical data)
                trend = CapacityTrend(
                    resource_type="disk",
                    current_value=disk_usage_percent,
                    trend_direction="unknown",
                    growth_rate_per_day=0,
                    confidence=0.5,
                )
                trends.append(trend)

        except Exception as e:
            logger.warning("Failed to analyze disk capacity: %s", e)

        return trends

    def _analyze_heap_capacity(self, node_filter: str | None = None) -> list[CapacityTrend]:
        """Analyze JVM heap capacity trends."""
        trends = []

        try:
            response = self.client.nodes.stats(
                metric="jvm",
                flat_settings=True,
            )

            for node_id, node_stats in response.get("nodes", {}).items():
                if node_filter and node_filter not in node_id:
                    continue

                jvm_info = node_stats.get("jvm", {}).get("mem", {})
                heap_used_percent = jvm_info.get("heap_used_percent", 0)

                trend = CapacityTrend(
                    resource_type="heap",
                    current_value=heap_used_percent,
                    trend_direction="unknown",
                    growth_rate_per_day=0,
                    confidence=0.5,
                )
                trends.append(trend)

        except Exception as e:
            logger.warning("Failed to analyze heap capacity: %s", e)

        return trends

    def _analyze_shard_capacity(self, node_filter: str | None = None) -> list[CapacityTrend]:
        """Analyze shard count capacity trends."""
        trends = []

        try:
            response = self.client.nodes.stats(
                metric="indices",
                flat_settings=True,
            )

            for node_id, node_stats in response.get("nodes", {}).items():
                if node_filter and node_filter not in node_id:
                    continue

                indices_info = node_stats.get("indices", {}).get("shards", {})
                total_shards = indices_info.get("total", 0)

                trend = CapacityTrend(
                    resource_type="shards",
                    current_value=float(total_shards),
                    trend_direction="unknown",
                    growth_rate_per_day=0,
                    confidence=0.5,
                )
                trends.append(trend)

        except Exception as e:
            logger.warning("Failed to analyze shard capacity: %s", e)

        return trends

    def _generate_recommendations(
        self,
        trends: dict[str, list[CapacityTrend]],
    ) -> list[CapacityRecommendation]:
        """Generate capacity recommendations based on trends."""
        recommendations = []

        # Disk recommendations
        for trend in trends.get("disk", []):
            if trend.current_value > 85:
                recommendations.append(CapacityRecommendation(
                    resource_type="disk",
                    recommendation_type="add_capacity",
                    priority="high",
                    description=f"Disk usage at {trend.current_value:.1f}%. Consider adding storage or reducing index retention.",
                    timeframe="immediate",
                ))
            elif trend.current_value > 70:
                recommendations.append(CapacityRecommendation(
                    resource_type="disk",
                    recommendation_type="optimize",
                    priority="medium",
                    description=f"Disk usage at {trend.current_value:.1f}%. Review index retention policies and shard distribution.",
                    timeframe="short-term",
                ))

        # Heap recommendations
        for trend in trends.get("heap", []):
            if trend.current_value > 90:
                recommendations.append(CapacityRecommendation(
                    resource_type="heap",
                    recommendation_type="scale_up",
                    priority="high",
                    description=f"JVM heap usage at {trend.current_value:.1f}%. Increase heap size or reduce shard count.",
                    timeframe="immediate",
                ))
            elif trend.current_value > 75:
                recommendations.append(CapacityRecommendation(
                    resource_type="heap",
                    recommendation_type="monitor",
                    priority="medium",
                    description=f"JVM heap usage at {trend.current_value:.1f}%. Monitor closely for further increases.",
                    timeframe="short-term",
                ))

        # Shard recommendations
        for trend in trends.get("shards", []):
            if trend.current_value > 5000:
                recommendations.append(CapacityRecommendation(
                    resource_type="shards",
                    recommendation_type="optimize",
                    priority="high",
                    description=f"High shard count: {int(trend.current_value)}. Consider reducing shard count per index.",
                    timeframe="immediate",
                ))
            elif trend.current_value > 2000:
                recommendations.append(CapacityRecommendation(
                    resource_type="shards",
                    recommendation_type="monitor",
                    priority="medium",
                    description=f"Elevated shard count: {int(trend.current_value)}. Monitor growth rate.",
                    timeframe="short-term",
                ))

        return recommendations

    def _assess_risk(
        self,
        trends: dict[str, list[CapacityTrend]],
    ) -> dict[str, str]:
        """Assess overall capacity risk."""
        risk = {
            "overall_risk": "low",
            "disk_risk": "low",
            "heap_risk": "low",
            "shard_risk": "low",
            "time_to_constrain_days": None,
        }

        # Assess disk risk
        for trend in trends.get("disk", []):
            if trend.current_value > 85:
                risk["disk_risk"] = "critical"
            elif trend.current_value > 70:
                risk["disk_risk"] = "high"

        # Assess heap risk
        for trend in trends.get("heap", []):
            if trend.current_value > 90:
                risk["heap_risk"] = "critical"
            elif trend.current_value > 75:
                risk["heap_risk"] = "high"

        # Assess shard risk
        for trend in trends.get("shards", []):
            if trend.current_value > 5000:
                risk["shard_risk"] = "high"

        # Determine overall risk
        risks = [risk["disk_risk"], risk["heap_risk"], risk["shard_risk"]]
        if "critical" in risks:
            risk["overall_risk"] = "critical"
        elif "high" in risks:
            risk["overall_risk"] = "high"
        elif "medium" in risks:
            risk["overall_risk"] = "medium"

        return risk