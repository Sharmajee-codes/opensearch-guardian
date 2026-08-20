"""Capacity planning module for Guardian.

Provides predictive capacity analysis using time-series trends.
"""

from __future__ import annotations

__version__ = "0.1.0"

from .predictive_planner import (
    CapacityRecommendation,
    CapacityTrend,
    PredictiveCapacityPlanner,
)

__all__ = ["CapacityRecommendation", "CapacityTrend", "PredictiveCapacityPlanner"]
