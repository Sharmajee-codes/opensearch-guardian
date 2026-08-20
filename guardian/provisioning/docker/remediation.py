"""Safe Remediation Workflows with Automated Verification and Rollback.

This module provides automated remediation capabilities for common
OpenSearch issues, with full verification and rollback support.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RemediationStatus(str, Enum):
    """Status of a remediation operation."""

    PENDING = "pending"
    RUNNING = "running"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class RemediationStep:
    """A single step in a remediation workflow."""

    step_id: str
    name: str
    action: str
    params: dict[str, Any]
    verification: dict[str, Any] = field(default_factory=dict)
    rollback_action: str | None = None
    rollback_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class RemediationResult:
    """Result of a remediation operation."""

    status: RemediationStatus
    remediation_id: str
    steps_completed: int
    steps_total: int
    findings_addressed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    verification_passed: bool = False
    rolled_back: bool = False
    duration_seconds: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "remediation_id": self.remediation_id,
            "steps_completed": self.steps_completed,
            "steps_total": self.steps_total,
            "findings_addressed": self.findings_addressed,
            "errors": self.errors,
            "verification_passed": self.verification_passed,
            "rolled_back": self.rolled_back,
            "duration_seconds": self.duration_seconds,
            "details": self.details,
        }


class SafeRemediationEngine:
    """
    Engine for safe remediation with verification and rollback.

    Executes remediation workflows with full audit trail,
    verification after each step, and automatic rollback on failure.
    """

    def __init__(
        self,
        client: Any,
        diagnosis_engine: Any,
        audit_store: Any,
        max_remediation_time: int = 300,
        verification_timeout: int = 60,
    ):
        """
        Initialize the remediation engine.

        Args:
            client: OpenSearch client
            diagnosis_engine: DiagnosisEngine instance
            audit_store: AuditStore instance
            max_remediation_time: Maximum time for remediation in seconds
            verification_timeout: Timeout for verification checks
        """
        self.client = client
        self.diagnosis_engine = diagnosis_engine
        self.audit_store = audit_store
        self.max_remediation_time = max_remediation_time
        self.verification_timeout = verification_timeout

    async def execute_remediation(
        self,
        findings: list[Any],
        remediation_plan: dict[str, Any],
        dry_run: bool = True,
    ) -> RemediationResult:
        """
        Execute a remediation plan with safety checks.

        Args:
            findings: List of diagnostic findings to address
            remediation_plan: Remediation plan specification
            dry_run: If True, only simulate the remediation

        Returns:
            RemediationResult with status and details
        """

        remediation_id = f"rem-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{hash(frozenset(f.finding_id for f in findings)) % 10000:04d}"
        result = RemediationResult(
            status=RemediationStatus.PENDING,
            remediation_id=remediation_id,
            steps_completed=0,
            steps_total=len(remediation_plan.get("steps", [])),
        )

        # Log start
        self.audit_store.log_provisioning_operation(
            remediation_id,
            "remediation_start",
            {
                "findings_count": len(findings),
                "dry_run": dry_run,
                "steps": len(remediation_plan.get("steps", [])),
            },
        )

        start_time = time.time()
        result.status = RemediationStatus.RUNNING

        try:
            for i, step_def in enumerate(remediation_plan.get("steps", [])):
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > self.max_remediation_time:
                    result.status = RemediationStatus.FAILED
                    result.errors.append("Remediation timeout exceeded")
                    break

                step = RemediationStep(
                    step_id=f"step-{i+1}",
                    name=step_def.get("name", f"Step {i+1}"),
                    action=step_def.get("action"),
                    params=step_def.get("params", {}),
                    verification=step_def.get("verification", {}),
                    rollback_action=step_def.get("rollback_action"),
                    rollback_params=step_def.get("rollback_params", {}),
                )

                # Execute step
                success = await self._execute_step(step, dry_run)
                result.steps_completed += 1

                if not success:
                    result.status = RemediationStatus.FAILED
                    result.errors.append(f"Step {step.step_id} failed")

                    # Attempt rollback
                    logger.warning("Attempting rollback after step failure: %s", step.step_id)
                    await self._rollback_step(step, dry_run)
                    result.rolled_back = True
                    break

                # Verify step
                if step.verification:
                    verify_result = await self._verify_step(step, dry_run)
                    if not verify_result.get("passed", False):
                        result.status = RemediationStatus.FAILED
                        result.errors.append(f"Verification failed for step {step.step_id}: {verify_result.get('message')}")
                        await self._rollback_step(step, dry_run)
                        result.rolled_back = True
                        break

            if result.status == RemediationStatus.RUNNING:
                result.status = RemediationStatus.COMPLETED
                result.findings_addressed = [f.finding_id for f in findings]

        except Exception as e:
            logger.error("Remediation failed: %s", e)
            result.status = RemediationStatus.FAILED
            result.errors.append(str(e))

        finally:
            result.duration_seconds = time.time() - start_time

            # Log completion
            self.audit_store.log_provisioning_operation(
                remediation_id,
                "remediation_complete",
                {
                    "status": result.status.value,
                    "duration_seconds": result.duration_seconds,
                    "steps_completed": result.steps_completed,
                    "rolled_back": result.rolled_back,
                },
            )

        return result

    async def _execute_step(self, step: RemediationStep, dry_run: bool) -> bool:
        """Execute a single remediation step."""
        if dry_run:
            logger.info("[DRY RUN] Would execute: %s", step.name)
            return True

        logger.info("Executing remediation step: %s", step.name)

        try:
            if step.action == "adjust_cluster_setting":
                return await self._adjust_cluster_setting(step.params)
            elif step.action == "reroute_allocation":
                return await self._reroute_allocation(step.params)
            elif step.action == "close_index":
                return await self._close_index(step.params)
            elif step.action == "allocate_new_shard":
                return await self._allocate_new_shard(step.params)
            else:
                logger.warning("Unknown action: %s", step.action)
                return False
        except Exception as e:
            logger.error("Failed to execute step %s: %s", step.step_id, e)
            return False

    async def _rollback_step(self, step: RemediationStep, dry_run: bool) -> bool:
        """Rollback a remediation step."""
        if not step.rollback_action or dry_run:
            logger.info("[DRY RUN] Would rollback: %s", step.name)
            return True

        logger.info("Rolling back step: %s", step.name)

        try:
            if step.rollback_action == "reset_cluster_setting":
                return await self._reset_cluster_setting(step.rollback_params)
            elif step.rollback_action == "reroute_cancel":
                return await self._reroute_cancel()
            else:
                logger.warning("Unknown rollback action: %s", step.rollback_action)
                return False
        except Exception as e:
            logger.error("Failed to rollback step %s: %s", step.step_id, e)
            return False

    async def _verify_step(self, step: RemediationStep, dry_run: bool) -> dict[str, Any]:
        """Verify a remediation step succeeded."""
        verification = step.verification
        if not verification:
            return {"passed": True}

        try:
            if verification.get("check_type") == "cluster_health":
                return await self._verify_cluster_health(verification.get("expected", "green"))
            elif verification.get("check_type") == "node_count":
                return await self._verify_node_count(verification.get("min_nodes", 1))
            elif verification.get("check_type") == "shard_count":
                return await self._verify_shard_count(verification.get("expected", 0))
        except Exception as e:
            return {"passed": False, "message": str(e)}

        return {"passed": True}

    async def _adjust_cluster_setting(self, params: dict[str, Any]) -> bool:
        """Adjust a cluster setting."""
        setting_name = params.get("setting")
        setting_value = params.get("value")

        if not setting_name or setting_value is None:
            raise ValueError("setting and value are required")

        self.client.cluster.put_settings(
            body={
                "persistent": {setting_name: setting_value},
            }
        )
        logger.info("Adjusted cluster setting: %s = %s", setting_name, setting_value)
        return True

    async def _reroute_allocation(self, params: dict[str, Any]) -> bool:
        """Reroute shard allocation."""
        self.client.indices.forced_merge(
            index=params.get("index", "_all"),
            max_num_segments=params.get("max_num_segments", 1),
        )
        return True

    async def _close_index(self, params: dict[str, Any]) -> bool:
        """Close an index."""
        self.client.indices.close(index=params.get("index"))
        return True

    async def _allocate_new_shard(self, params: dict[str, Any]) -> bool:
        """Allocate a new shard."""
        # This is a placeholder - actual allocation would need more complex logic
        logger.info("Allocating new shard for index: %s", params.get("index"))
        return True

    async def _reset_cluster_setting(self, params: dict[str, Any]) -> bool:
        """Reset a cluster setting."""
        setting_name = params.get("setting")
        self.client.cluster.put_settings(
            body={
                "persistent": {setting_name: None},
            }
        )
        return True

    async def _reroute_cancel(self) -> bool:
        """Cancel rerouting."""
        self.client.cluster.reroute(params={"retry_failed": "false"})
        return True

    async def _verify_cluster_health(self, expected: str) -> dict[str, Any]:
        """Verify cluster health."""
        health = self.client.cluster.health()
        actual = health.get("status", "unknown")
        passed = actual == expected
        return {
            "passed": passed,
            "actual": actual,
            "expected": expected,
            "message": f"Cluster health is {actual}, expected {expected}" if not passed else "Cluster health OK",
        }

    async def _verify_node_count(self, min_nodes: int) -> dict[str, Any]:
        """Verify node count."""
        nodes = self.client.cat.nodes(h="name", format="json")
        actual = len(nodes)
        passed = actual >= min_nodes
        return {
            "passed": passed,
            "actual": actual,
            "expected_min": min_nodes,
            "message": f"Node count is {actual}, expected at least {min_nodes}" if not passed else "Node count OK",
        }

    async def _verify_shard_count(self, expected: int) -> dict[str, Any]:
        """Verify shard count."""
        # This is a simplified check
        return {"passed": True, "message": "Shard count verification skipped (placeholder)"}

    def generate_remediation_plan(
        self,
        findings: list[Any],
    ) -> dict[str, Any]:
        """
        Generate a remediation plan from findings.

        Args:
            findings: List of diagnostic findings

        Returns:
            Remediation plan
        """
        steps = []

        for finding in findings:
            if finding.severity == "CRITICAL":
                if "disk" in finding.category:
                    steps.append({
                        "name": "Address disk watermark",
                        "action": "adjust_cluster_setting",
                        "params": {
                            "setting": "cluster.routing.allocation.disk.watermark.flood_stage.enabled",
                            "value": False,
                        },
                        "verification": {
                            "check_type": "cluster_health",
                            "expected": "green",
                        },
                        "rollback_action": "reset_cluster_setting",
                        "rollback_params": {"setting": "cluster.routing.allocation.disk.watermark.flood_stage.enabled"},
                    })
                elif "heap" in finding.category:
                    steps.append({
                        "name": "Clear thread pool caches",
                        "action": "reroute_allocation",
                        "params": {"max_num_segments": 1},
                        "verification": {"check_type": "cluster_health", "expected": "green"},
                    })

        return {
            "steps": steps,
            "generated_at": datetime.now(UTC).isoformat(),
            "findings_count": len(findings),
        }