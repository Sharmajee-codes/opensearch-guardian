"""
Dry-run Engine for the Security & Safety Engine.
Provides dry-run/diff functionality for infrastructure changes,
generating before/after snapshots for review.
"""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from .classification import SafetyClassification


@dataclass
class DiffResult:
    """Result of a dry-run diff operation."""
    operation_type: str
    target_resource: str
    before_snapshot: Dict[str, Any]
    after_snapshot: Dict[str, Any]
    changes_summary: Dict[str, Any]
    risk_assessment: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    diff_id: str = field(default_factory=lambda: hashlib.sha256(
        f"{datetime.utcnow().isoformat()}".encode()
    ).hexdigest()[:16])


class DryRunEngine:
    """
    Dry-run engine that simulates mutation operations and generates
    diff reports for operator review, per SOP §8 and ADR-002.
    """

    def __init__(self):
        # In a real implementation, this would connect to actual OpenSearch/Docker/K8s
        # For now, we'll simulate the behavior
        pass

    async def execute_dry_run(
        self,
        operation_type: str,
        target_resource: str,
        parameters: Dict[str, Any],
        current_state: Dict[str, Any]
    ) -> DiffResult:
        """
        Execute a dry-run of a mutation operation and generate a diff.

        Args:
            operation_type: Type of operation to simulate
            target_resource: Resource being operated on
            parameters: Operation parameters
            current_state: Current system state snapshot

        Returns:
            DiffResult containing before/after snapshots and changes summary
        """
        # Generate before snapshot (current state)
        before_snapshot = await self._capture_snapshot(current_state)

        # Simulate the operation to get after state
        after_state = await self._simulate_operation(
            operation_type, target_resource, parameters, current_state.copy()
        )
        after_snapshot = await self._capture_snapshot(after_state)

        # Generate changes summary
        changes_summary = self._generate_changes_summary(
            before_snapshot, after_snapshot, operation_type
        )

        # Assess risk
        risk_assessment = self._assess_risk(
            operation_type, changes_summary, parameters
        )

        return DiffResult(
            operation_type=operation_type,
            target_resource=target_resource,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            changes_summary=changes_summary,
            risk_assessment=risk_assessment
        )

    async def _capture_snapshot(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Capture a point-in-time snapshot of the system state.
        In practice, this would collect from OpenSearch, Docker, etc.
        """
        # Normalize and hash the state for immutability
        snapshot = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "state_hash": self._compute_state_hash(state),
            "components": state
        }
        return snapshot

    def _compute_state_hash(self, state: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of state for immutability verification."""
        state_json = json.dumps(state, sort_keys=True, default=str)
        return hashlib.sha256(state_json.encode()).hexdigest()

    async def _simulate_operation(
        self,
        operation_type: str,
        target_resource: str,
        parameters: Dict[str, Any],
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulate an operation on a copy of the current state.
        Returns the predicted state after the operation.
        """
        # This is a simplified simulation - in practice would involve
        # calling actual APIs with dry_run=true or using mocks
        after_state = current_state.copy()

        # Apply operation-specific transformations
        if operation_type == "node-add":
            after_state.setdefault("nodes", []).append({
                "node_id": parameters.get("node_id", f"node-{len(after_state.get('nodes', [])) + 1}"),
                "role": parameters.get("role", "data"),
                "status": "joining",
                "ip_address": parameters.get("ip_address"),
                "added_at": datetime.utcnow().isoformat() + "Z"
            })
            # Update cluster stats
            after_state["cluster_stats"] = after_state.get("cluster_stats", {})
            after_state["cluster_stats"]["total_nodes"] = \
                after_state["cluster_stats"].get("total_nodes", 0) + 1

        elif operation_type == "node-remove":
            # Remove node from state
            nodes = after_state.get("nodes", [])
            after_state["nodes"] = [
                n for n in nodes if n.get("node_id") != target_resource
            ]
            # Update cluster stats
            after_state["cluster_stats"] = after_state.get("cluster_stats", {})
            after_state["cluster_stats"]["total_nodes"] = \
                max(0, after_state["cluster_stats"].get("total_nodes", 0) - 1)

        elif operation_type == "index-create":
            # Add index to state
            indices = after_state.get("indices", [])
            indices.append({
                "index_name": target_resource,
                "settings": parameters.get("settings", {}),
                "mappings": parameters.get("mappings", {}),
                "status": "created",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "shards": parameters.get("number_of_shards", 1),
                "replicas": parameters.get("number_of_replicas", 1)
            })
            after_state["indices"] = indices

        elif operation_type == "index-delete":
            # Remove index from state
            indices = after_state.get("indices", [])
            after_state["indices"] = [
                idx for idx in indices if idx.get("index_name") != target_resource
            ]

        elif operation_type == "index-update-settings":
            # Update index settings
            indices = after_state.get("indices", [])
            for idx in indices:
                if idx.get("index_name") == target_resource:
                    idx["settings"].update(parameters.get("settings", {}))
                    idx["updated_at"] = datetime.utcnow().isoformat() + "Z"
                    break

        elif operation_type == "docker-compose-up":
            # Simulate Docker compose up
            services = after_state.get("docker_services", [])
            service_config = parameters.get("service", {})
            services.append({
                "service_name": target_resource,
                "image": service_config.get("image"),
                "ports": service_config.get("ports", []),
                "environment": service_config.get("environment", {}),
                "status": "starting",
                "deployed_at": datetime.utcnow().isoformat() + "Z"
            })
            after_state["docker_services"] = services

        elif operation_type == "docker-compose-down":
            # Simulate Docker compose down
            services = after_state.get("docker_services", [])
            after_state["docker_services"] = [
                s for s in services if s.get("service_name") != target_resource
            ]

        elif operation_type == "k8s-scale-up":
            # Simulate K8s scale up
            deployments = after_state.get("k8s_deployments", [])
            for dep in deployments:
                if dep.get("name") == target_resource:
                    dep["replicas"] = dep.get("replicas", 1) + parameters.get("replica_count", 1)
                    dep["scaled_at"] = datetime.utcnow().isoformat() + "Z"
                    break
            else:
                # New deployment
                deployments.append({
                    "name": target_resource,
                    "replicas": parameters.get("replica_count", 1),
                    "image": parameters.get("image"),
                    "status": "scaling",
                    "scaled_at": datetime.utcnow().isoformat() + "Z"
                })
            after_state["k8s_deployments"] = deployments

        elif operation_type == "k8s-scale-down":
            # Simulate K8s scale down
            deployments = after_state.get("k8s_deployments", [])
            for dep in deployments:
                if dep.get("name") == target_resource:
                    current_replicas = dep.get("replicas", 1)
                    scale_down_by = parameters.get("replica_count", 1)
                    new_replicas = max(0, current_replicas - scale_down_by)
                    dep["replicas"] = new_replicas
                    dep["scaled_at"] = datetime.utcnow().isoformat() + "Z"
                    if new_replicas == 0:
                        # Mark for removal
                        dep["status"] = "terminating"
                    break
            after_state["k8s_deployments"] = deployments

        # Add operation metadata
        after_state["last_operation"] = {
            "type": operation_type,
            "target": target_resource,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "parameters": parameters,
            "dry_run": True
        }

        return after_state

    def _generate_changes_summary(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
        operation_type: str
    ) -> Dict[str, Any]:
        """Generate a human-readable summary of changes."""
        summary = {
            "operation": operation_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "changes": []
        }

        # Compare key metrics
        before_nodes = len(before.get("components", {}).get("nodes", []))
        after_nodes = len(after.get("components", {}).get("nodes", []))
        if before_nodes != after_nodes:
            summary["changes"].append({
                "type": "node_count",
                "change": after_nodes - before_nodes,
                "description": f"Node count changed from {before_nodes} to {after_nodes}"
            })

        before_indices = len(before.get("components", {}).get("indices", []))
        after_indices = len(after.get("components", {}).get("indices", []))
        if before_indices != after_indices:
            summary["changes"].append({
                "type": "index_count",
                "change": after_indices - before_indices,
                "description": f"Index count changed from {before_indices} to {after_indices}"
            })

        before_services = len(before.get("components", {}).get("docker_services", []))
        after_services = len(after.get("components", {}).get("docker_services", []))
        if before_services != after_services:
            summary["changes"].append({
                "type": "docker_service_count",
                "change": after_services - before_services,
                "description": f"Docker service count changed from {before_services} to {after_services}"
            })

        # Add operation-specific details
        summary["operation_details"] = {
            "operation_type": operation_type,
            "target_resource": after.get("components", {}).get(
                "last_operation", {}
            ).get("target", "unknown")
        }

        return summary

    def _assess_risk(
        self,
        operation_type: str,
        changes_summary: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> str:
        """Assess the risk level of the simulated operation."""
        # High-risk operations
        high_risk_ops = {"index-delete", "node-delete", "cluster-shutdown", "data-purge"}
        if operation_type in high_risk_ops:
            return "HIGH - Potential data loss or cluster instability"

        # Medium-risk operations
        medium_risk_ops = {"node-add", "node-remove", "index-create", "index-update-settings"}
        if operation_type in medium_risk_ops:
            return "MEDIUM - May cause temporary cluster rebalancing"

        # Low-risk operations
        return "LOW - Minimal impact expected"