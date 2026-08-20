"""Built-in Lightweight Anomaly Detection for Collected Metrics.

This module implements simple statistical anomaly detection on key time series
metrics. Anomalies are emitted as plugin-specific cluster stats or sent to
.guardian-anomalies* index.

Based on Ryan's suggestion for Doctor Rules enhancement.
"""

from __future__ import annotations

import logging
import math
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AnomalySeverity(str, Enum):
    """Severity levels for detected anomalies."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    """Types of anomalies that can be detected."""

    SPIKE = "spike"  # Sudden increase
    DROP = "drop"  # Sudden decrease
    TREND_CHANGE = "trend_change"  # Change in trend direction
    SEASONAL_DEVIATION = "seasonal_deviation"  # Deviation from expected seasonal pattern
    OUTLIER = "outlier"  # Statistical outlier
    THRESHOLD_BREACH = "threshold_breach"  # Breached configured threshold


@dataclass
class Anomaly:
    """Represents a detected anomaly."""

    anomaly_id: str
    metric_name: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    timestamp: datetime
    value: float
    expected_value: float
    deviation: float
    deviation_percent: float
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "anomaly_id": self.anomaly_id,
            "metric_name": self.metric_name,
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "expected_value": self.expected_value,
            "deviation": self.deviation,
            "deviation_percent": self.deviation_percent,
            "context": self.context,
        }


class StatisticalAnomalyDetector:
    """
    Lightweight statistical anomaly detector for time series metrics.

    Uses simple statistical methods:
    - Z-score based outlier detection
    - Moving average with threshold
    - Exponential smoothing for trend detection
    - Percentage change thresholds

    Designed for real-time detection with minimal memory overhead.
    """

    DEFAULT_WINDOW_SIZE = 100
    DEFAULT_Z_SCORE_THRESHOLD = 3.0
    DEFAULT_CHANGE_THRESHOLD = 0.5  # 50% change
    MIN_SAMPLES = 10

    def __init__(
        self,
        window_size: int = DEFAULT_WINDOW_SIZE,
        z_score_threshold: float = DEFAULT_Z_SCORE_THRESHOLD,
        change_threshold: float = DEFAULT_CHANGE_THRESHOLD,
    ):
        """
        Initialize the anomaly detector.

        Args:
            window_size: Size of rolling window for statistics
            z_score_threshold: Z-score threshold for outlier detection
            change_threshold: Minimum relative change to flag as anomaly
        """
        self.window_size = window_size
        self.z_score_threshold = z_score_threshold
        self.change_threshold = change_threshold

        # Per-metric state
        self._values: dict[str, deque] = {}
        self._means: dict[str, float] = {}
        self._stds: dict[str, float] = {}
        self._last_values: dict[str, float] = {}
        self._trends: dict[str, float] = {}

    def add_value(self, metric_name: str, value: float, timestamp: datetime | None = None) -> list[Anomaly]:
        """
        Add a new metric value and detect anomalies.

        Args:
            metric_name: Name of the metric
            value: Current value
            timestamp: Optional timestamp (defaults to now)

        Returns:
            List of detected anomalies
        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        anomalies = []

        # Initialize tracking for new metrics
        if metric_name not in self._values:
            self._values[metric_name] = deque(maxlen=self.window_size)
            self._means[metric_name] = 0.0
            self._stds[metric_name] = 0.0

        values = self._values[metric_name]
        values.append(value)

        # Need minimum samples for statistical detection
        if len(values) < self.MIN_SAMPLES:
            self._update_stats(metric_name)
            self._last_values[metric_name] = value
            return anomalies

        # Update statistics
        self._update_stats(metric_name)

        mean = self._means[metric_name]
        std = self._stds[metric_name]
        last_value = self._last_values.get(metric_name, value)

        # 1. Z-score based outlier detection
        if std > 0:
            z_score = abs(value - mean) / std
            if z_score > self.z_score_threshold:
                severity = self._z_score_to_severity(z_score)
                anomalies.append(Anomaly(
                    anomaly_id=f"anom-{metric_name}-{int(timestamp.timestamp())}",
                    metric_name=metric_name,
                    anomaly_type=AnomalyType.OUTLIER,
                    severity=severity,
                    timestamp=timestamp,
                    value=value,
                    expected_value=mean,
                    deviation=value - mean,
                    deviation_percent=((value - mean) / mean * 100) if mean != 0 else 0,
                    context={
                        "z_score": z_score,
                        "mean": mean,
                        "std": std,
                        "window_size": len(values),
                    },
                ))

        # 2. Sudden change detection (percentage change from last value)
        if last_value != 0:
            relative_change = abs(value - last_value) / abs(last_value)
            if relative_change > self.change_threshold:
                anomaly_type = AnomalyType.SPIKE if value > last_value else AnomalyType.DROP
                severity = self._change_to_severity(relative_change)
                anomalies.append(Anomaly(
                    anomaly_id=f"anom-{metric_name}-{int(timestamp.timestamp())}",
                    metric_name=metric_name,
                    anomaly_type=anomaly_type,
                    severity=severity,
                    timestamp=timestamp,
                    value=value,
                    expected_value=last_value,
                    deviation=value - last_value,
                    deviation_percent=relative_change * 100,
                    context={
                        "previous_value": last_value,
                        "relative_change": relative_change,
                    },
                ))

        # 3. Trend change detection (simple linear trend)
        trend = self._calculate_trend(metric_name)
        if self._trends.get(metric_name) is not None:
            trend_change = abs(trend - self._trends[metric_name])
            if trend_change > 0.5:  # Significant trend change
                anomalies.append(Anomaly(
                    anomaly_id=f"anom-{metric_name}-{int(timestamp.timestamp())}",
                    metric_name=metric_name,
                    anomaly_type=AnomalyType.TREND_CHANGE,
                    severity=AnomalySeverity.MEDIUM,
                    timestamp=timestamp,
                    value=trend,
                    expected_value=self._trends[metric_name],
                    deviation=trend - self._trends[metric_name],
                    deviation_percent=((trend - self._trends[metric_name]) / abs(self._trends[metric_name]) * 100) if self._trends[metric_name] != 0 else 0,
                    context={
                        "new_trend": trend,
                        "old_trend": self._trends[metric_name],
                    },
                ))
        self._trends[metric_name] = trend

        # Update last value
        self._last_values[metric_name] = value

        # Log anomalies
        for anomaly in anomalies:
            logger.info(
                "Anomaly detected: metric=%s type=%s severity=%s value=%.2f expected=%.2f",
                anomaly.metric_name,
                anomaly.anomaly_type.value,
                anomaly.severity.value,
                anomaly.value,
                anomaly.expected_value,
            )

        return anomalies

    def _update_stats(self, metric_name: str):
        """Update mean and standard deviation for a metric."""
        values = list(self._values[metric_name])
        n = len(values)
        if n == 0:
            return

        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std = math.sqrt(variance) if variance > 0 else 0.0

        self._means[metric_name] = mean
        self._stds[metric_name] = std

    def _calculate_trend(self, metric_name: str) -> float:
        """Calculate simple linear trend using least squares."""
        values = list(self._values[metric_name])
        n = len(values)
        if n < 2:
            return 0.0

        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _z_score_to_severity(self, z_score: float) -> AnomalySeverity:
        """Map Z-score to severity."""
        if z_score > 5:
            return AnomalySeverity.CRITICAL
        elif z_score > 4:
            return AnomalySeverity.HIGH
        elif z_score > 3:
            return AnomalySeverity.MEDIUM
        return AnomalySeverity.LOW

    def _change_to_severity(self, relative_change: float) -> AnomalySeverity:
        """Map relative change to severity."""
        if relative_change > 2.0:
            return AnomalySeverity.CRITICAL
        elif relative_change > 1.0:
            return AnomalySeverity.HIGH
        elif relative_change > 0.5:
            return AnomalySeverity.MEDIUM
        return AnomalySeverity.LOW

    def get_statistics(self, metric_name: str) -> dict[str, Any]:
        """Get current statistics for a metric."""
        if metric_name not in self._values:
            return {}

        return {
            "metric_name": metric_name,
            "sample_count": len(self._values[metric_name]),
            "mean": self._means.get(metric_name, 0),
            "std": self._stds.get(metric_name, 0),
            "last_value": self._last_values.get(metric_name, 0),
            "trend": self._trends.get(metric_name, 0),
            "min": min(self._values[metric_name]) if self._values[metric_name] else 0,
            "max": max(self._values[metric_name]) if self._values[metric_name] else 0,
        }


class AnomalyStore:
    """
    Store for persisting anomalies to OpenSearch index.

    Anomalies are stored in .guardian-anomalies-* index with
    proper mappings for querying and visualization.
    """

    INDEX_PATTERN = ".guardian-anomalies-*"
    INDEX_TEMPLATE = ".guardian-anomalies-template"

    def __init__(self, client: Any):
        """
        Initialize anomaly store.

        Args:
            client: OpenSearch client instance
        """
        self.client = client
        self._ensure_index_template()

    def _ensure_index_template(self):
        """Create index template for anomaly indices."""
        try:
            self.client.indices.put_index_template(
                name=self.INDEX_TEMPLATE,
                body={
                    "index_patterns": [".guardian-anomalies-*"],
                    "template": {
                        "mappings": {
                            "properties": {
                                "anomaly_id": {"type": "keyword"},
                                "metric_name": {"type": "keyword"},
                                "anomaly_type": {"type": "keyword"},
                                "severity": {"type": "keyword"},
                                "timestamp": {"type": "date"},
                                "value": {"type": "float"},
                                "expected_value": {"type": "float"},
                                "deviation": {"type": "float"},
                                "deviation_percent": {"type": "float"},
                                "context": {"type": "object", "dynamic": True},
                            }
                        },
                        "settings": {
                            "number_of_shards": 1,
                            "number_of_replicas": 1,
                        },
                    },
                },
            )
            logger.info("Created anomaly index template")
        except Exception as e:
            logger.warning("Failed to create anomaly index template: %s", e)

    def _get_daily_index(self, timestamp: datetime) -> str:
        """Get the daily index name for a timestamp."""
        return f".guardian-anomalies-{timestamp.strftime('%Y.%m.%d')}"

    def store_anomaly(self, anomaly: Anomaly) -> bool:
        """Store an anomaly in OpenSearch."""
        try:
            index = self._get_daily_index(anomaly.timestamp)
            doc = anomaly.to_dict()
            self.client.index(
                index=index,
                id=anomaly.anomaly_id,
                body=doc,
                refresh="wait_for",
            )
            return True
        except Exception as e:
            logger.error("Failed to store anomaly: %s", e)
            return False

    def store_anomalies(self, anomalies: list[Anomaly]) -> int:
        """Store multiple anomalies."""
        stored = 0
        for anomaly in anomalies:
            if self.store_anomaly(anomaly):
                stored += 1
        return stored

    def query_anomalies(
        self,
        metric_name: str | None = None,
        anomaly_type: AnomalyType | None = None,
        severity: AnomalySeverity | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[Anomaly]:
        """Query anomalies from OpenSearch."""
        query = {"query": {"bool": {"must": []}}}

        if metric_name:
            query["query"]["bool"]["must"].append({"term": {"metric_name": metric_name}})
        if anomaly_type:
            query["query"]["bool"]["must"].append({"term": {"anomaly_type": anomaly_type.value}})
        if severity:
            query["query"]["bool"]["must"].append({"term": {"severity": severity.value}})
        if since:
            query["query"]["bool"]["filter"] = [
                {"range": {"timestamp": {"gte": since.isoformat()}}}
            ]

        query["size"] = limit
        query["sort"] = [{"timestamp": {"order": "desc"}}]

        try:
            response = self.client.search(index=self.INDEX_PATTERN, body=query)
            anomalies = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                anomalies.append(Anomaly(
                    anomaly_id=source["anomaly_id"],
                    metric_name=source["metric_name"],
                    anomaly_type=AnomalyType(source["anomaly_type"]),
                    severity=AnomalySeverity(source["severity"]),
                    timestamp=datetime.fromisoformat(source["timestamp"]),
                    value=source["value"],
                    expected_value=source["expected_value"],
                    deviation=source["deviation"],
                    deviation_percent=source["deviation_percent"],
                    context=source.get("context", {}),
                ))
            return anomalies
        except Exception as e:
            logger.error("Failed to query anomalies: %s", e)
            return []


# Pre-configured detector for common OpenSearch metrics
def create_opensearch_detector() -> StatisticalAnomalyDetector:
    """Create a detector tuned for common OpenSearch metrics."""
    return StatisticalAnomalyDetector(
        window_size=200,  # Keep more history for trend analysis
        z_score_threshold=3.0,
        change_threshold=0.3,  # 30% change threshold
    )

# Metrics to monitor with anomaly detection
OPENSEARCH_METRICS = [
    "cluster.health_status",  # 0=green, 1=yellow, 2=red
    "nodes.disk.usage_percent",
    "nodes.heap.usage_percent",
    "nodes.cpu.usage_percent",
    "nodes.thread_pool.search.queue_size",
    "nodes.thread_pool.write.queue_size",
    "nodes.thread_pool.search.rejected",
    "nodes.thread_pool.write.rejected",
    "cluster.unassigned_shards",
    "cluster.relocating_shards",
    "cluster.initializing_shards",
    "indices.docs.count",
    "indices.store.size",
    "indices.segments.count",
]