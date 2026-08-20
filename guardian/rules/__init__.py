"""Rules module for Guardian.

Provides diagnostic rule engine with marketplace support and anomaly detection.
"""

from __future__ import annotations

__version__ = "0.1.0"

from pydantic import BaseModel, Field

from .anomaly import (
    OPENSEARCH_METRICS,
    Anomaly,
    AnomalySeverity,
    AnomalyStore,
    AnomalyType,
    StatisticalAnomalyDetector,
    create_opensearch_detector,
)
from .base import EvidenceItem, Finding, Rule, RuleConfig
from .builtin import BUILTIN_RULES
from .marketplace import RuleMarketplace, RuleMetadata

__all__ = [
    "BUILTIN_RULES",
    "OPENSEARCH_METRICS",
    "Anomaly",
    "AnomalySeverity",
    "AnomalyStore",
    "AnomalyType",
    "EvidenceItem",
    "Finding",
    "Rule",
    "RuleConfig",
    "RuleMarketplace",
    "RuleMetadata",
    "StatisticalAnomalyDetector",
    "create_opensearch_detector",
]