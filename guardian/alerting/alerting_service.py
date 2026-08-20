"""OpenSearch Alerting Integration for Guardian.

This module integrates with OpenSearch's Alerting feature to create
monitors, triggers, and actions based on Guardian findings and events.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class GuardianAlertingService:
    """
    Service for creating and managing OpenSearch Alerting monitors.

    Integrates Guardian's diagnostic findings with OpenSearch's
    alerting capabilities to enable automated notifications and actions.
    """

    MONITOR_INDEX = ".opendistro-alerting-alerts"
    MONITOR_TYPE = "alert"

    def __init__(self, client: Any):
        """
        Initialize the alerting service.

        Args:
            client: OpenSearch client instance
        """
        self.client = client

    def create_monitor(
        self,
        name: str,
        query: dict[str, Any],
        severity_threshold: str = "WARNING",
        description: str = "",
        interval_minutes: int = 5,
    ) -> dict[str, Any]:
        """
        Create an OpenSearch Alerting monitor for Guardian.

        Args:
            name: Monitor name
            query: OpenSearch query to execute
            severity_threshold: Minimum severity to trigger alert
            description: Monitor description
            interval_minutes: Check interval in minutes

        Returns:
            Monitor response from OpenSearch
        """
        monitor = {
            "type": "monitor",
            "name": name,
            "enabled": True,
            "description": description or f"Guardian monitor: {name}",
            "schedule": {
                "period": {
                    "interval": interval_minutes,
                    "unit": "MINUTES",
                }
            },
            "query": query,
            "trigger": {
                "name": f"{name}-trigger",
                "severity": self._map_severity_to_threshold(severity_threshold),
                "condition": {
                    "script": {
                        "source": "return ctx.results[0].hits.total.value > 0",
                        "lang": "painless",
                    }
                },
            },
            "actions": [],
        }

        try:
            response = self.client.transport.perform_request(
                "PUT",
                "/_plugins/_alerting/monitors",
                body=json.dumps(monitor),
                headers={"Content-Type": "application/json"},
            )
            logger.info("Created alerting monitor: %s", name)
            return response
        except Exception as e:
            logger.error("Failed to create monitor: %s", e)
            raise

    def create_trigger(
        self,
        monitor_id: str,
        trigger_id: str,
        name: str,
        severity: str = "1",
        condition: dict[str, Any] = None,
        actions: list[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Create a trigger for an existing monitor.

        Args:
            monitor_id: Monitor ID
            trigger_id: Trigger ID
            name: Trigger name
            severity: Severity level (0=critical, 1=high, 2=medium, 3=low)
            condition: Trigger condition script
            actions: List of action definitions

        Returns:
            Trigger response
        """
        trigger = {
            "name": name,
            "severity": severity,
            "condition": condition or {
                "script": {
                    "source": "return ctx.results[0].hits.total.value > 0",
                    "lang": "painless",
                }
            },
            "actions": actions or [],
        }

        try:
            response = self.client.transport.perform_request(
                "PUT",
                f"/_plugins/_alerting/monitors/{monitor_id}/triggers/{trigger_id}",
                body=json.dumps(trigger),
                headers={"Content_Type": "application/json"},
            )
            logger.info("Created trigger: %s for monitor: %s", name, monitor_id)
            return response
        except Exception as e:
            logger.error("Failed to create trigger: %s", e)
            raise

    def create_action(
        self,
        action_id: str,
        name: str,
        action_type: str,
        destination_id: str,
        message_template: str,
    ) -> dict[str, Any]:
        """
        Create an action for alerts.

        Args:
            action_id: Unique action ID
            name: Action name
            action_type: Action type (e.g., "webhook", "email")
            destination_id: Destination ID
            message_template: Message template

        Returns:
            Action response
        """
        action = {
            "name": name,
            "action_type_id": action_type,
            "destination_id": destination_id,
            "subject_template": {"source": name},
            "message_template": {"source": message_template},
        }

        try:
            response = self.client.transport.perform_request(
                "PUT",
                f"/_plugins/_alerting/actions/{action_id}",
                body=json.dumps(action),
                headers={"Content_Type": "application/json"},
            )
            logger.info("Created action: %s", name)
            return response
        except Exception as e:
            logger.error("Failed to create action: %s", e)
            raise

    def create_destination(
        self,
        destination_id: str,
        name: str,
        type: str,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Create a destination for alerts (e.g., Slack, email, webhook).

        Args:
            destination_id: Unique destination ID
            name: Destination name
            type: Destination type
            config: Destination configuration

        Returns:
            Destination response
        """
        destination = {
            "name": name,
            "type": type,
            "config": config,
        }

        try:
            response = self.client.transport.perform_request(
                "POST",
                "/_plugins/_alerting/destinations",
                body=json.dumps(destination),
                headers={"Content_Type": "application/json"},
            )
            logger.info("Created destination: %s", name)
            return response
        except Exception as e:
            logger.error("Failed to create destination: %s", e)
            raise

    def get_monitor(self, monitor_id: str) -> dict[str, Any] | None:
        """Get a monitor by ID."""
        try:
            response = self.client.transport.perform_request(
                "GET",
                f"/_plugins/_alerting/monitors/{monitor_id}",
            )
            return response
        except Exception as e:
            logger.error("Failed to get monitor: %s", e)
            return None

    def get_alerts(
        self,
        monitor_id: str | None = None,
        severity: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get alerts from OpenSearch Alerting.

        Args:
            monitor_id: Filter by monitor ID
            severity: Filter by severity
            limit: Maximum number of alerts to return

        Returns:
            List of alert objects
        """
        query = {
            "size": limit,
            "query": {"bool": {"must": []}},
            "sort": [{"alert_history_timestamp": {"order": "desc"}}],
        }

        if monitor_id:
            query["query"]["bool"]["must"].append({"term": {"monitor_id": monitor_id}})
        if severity:
            query["query"]["bool"]["must"].append({"term": {"severity": severity}})

        try:
            response = self.client.search(
                index=self.MONITOR_INDEX,
                body=query,
            )
            alerts = []
            for hit in response["hits"]["hits"]:
                alert = hit["_source"]
                alert["alert_id"] = hit["_id"]
                alerts.append(alert)
            return alerts
        except Exception as e:
            logger.error("Failed to get alerts: %s", e)
            return []

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        try:
            response = self.client.transport.perform_request(
                "PUT",
                f"{self.MONITOR_INDEX}/{alert_id}/_acknowledge",
                headers={"Content-Type": "application/json"},
            )
            logger.info("Acknowledged alert: %s", alert_id)
            return True
        except Exception as e:
            logger.error("Failed to acknowledge alert: %s", e)
            return False

    def delete_monitor(self, monitor_id: str) -> bool:
        """Delete a monitor."""
        try:
            self.client.transport.perform_request(
                "DELETE",
                f"/_plugins/_alerting/monitors/{monitor_id}",
            )
            logger.info("Deleted monitor: %s", monitor_id)
            return True
        except Exception as e:
            logger.error("Failed to delete monitor: %s", e)
            return False

    # Predefined Guardian monitors
    def create_guardian_monitors(self) -> dict[str, str]:
        """
        Create standard Guardian alerting monitors.

        Returns:
            Dictionary mapping monitor name to ID
        """
        monitors = {}

        # Monitor for critical findings
        critical_monitor = self.create_monitor(
            name="Guardian-Critical-Findings",
            query={
                "query": {
                    "bool": {
                        "must": [{"term": {"severity": "CRITICAL"}}],
                    }
                },
                "size": 0,
                "_source": False,
            },
            severity_threshold="CRITICAL",
            description="Triggers when Guardian detects critical cluster issues",
            interval_minutes=5,
        )
        monitors["critical"] = critical_monitor.get("monitor_id")

        # Monitor for disk usage
        disk_monitor = self.create_monitor(
            name="Guardian-Disk-Usage",
            query={
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"category": "disk"}},
                            {"range": {"severity": {"lte": "WARNING"}}},
                        ]
                    }
                },
                "size": 0,
                "_source": False,
            },
            severity_threshold="WARNING",
            description="Triggers when disk usage thresholds are breached",
            interval_minutes=10,
        )
        monitors["disk"] = disk_monitor.get("monitor_id")

        # Monitor for thread pool rejections
        tp_monitor = self.create_monitor(
            name="Guardian-Thread-Pool",
            query={
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"category": "thread_pool"}},
                            {"range": {"severity": {"lte": "WARNING"}}},
                        ]
                    }
                },
                "size": 0,
                "_source": False,
            },
            severity_threshold="WARNING",
            description="Triggers when thread pool rejections are detected",
            interval_minutes=5,
        )
        monitors["thread_pool"] = tp_monitor.get("monitor_id")

        return monitors

    def _map_severity_to_threshold(self, severity: str) -> str:
        """Map Guardian severity to OpenSearch alerting severity."""
        mapping = {
            "CRITICAL": "1",
            "HIGH": "1",
            "WARNING": "2",
            "MEDIUM": "2",
            "INFO": "3",
            "LOW": "3",
        }
        return mapping.get(severity.upper(), "2")