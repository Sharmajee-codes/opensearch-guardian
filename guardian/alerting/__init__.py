"""Alerting module for Guardian.

Integrates with OpenSearch Alerting for automated notifications.
"""

from __future__ import annotations

__version__ = "0.1.0"

from .alerting_service import GuardianAlertingService

__all__ = ["GuardianAlertingService"]
