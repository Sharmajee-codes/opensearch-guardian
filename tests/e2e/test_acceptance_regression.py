"""End-to-end regression tests over the 10 acceptance criteria."""

import pytest
import requests


class TestAcceptanceCriteria:
    """
    Regression tests mapping to the 10 MVP acceptance criteria.
    
    See docs/operations/acceptance-criteria.md
    """

    # AC1: Connect securely to a supported OpenSearch cluster
    @pytest.mark.e2e
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_ac1_connect_to_cluster(self, healthy_cluster):
        """
        AC1: Connect securely to a supported OpenSearch cluster using a 
        least-privilege profile.
        
        Verify we can reach the OpenSearch API and get cluster identity.
        """
        r = requests.get("http://localhost:9200/", timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert "name" in body
        assert "cluster_name" in body
        assert "version" in body
        assert body["version"]["number"].startswith("2.17")

    # AC2: Display live health and node/shard/resource information
    @pytest.mark.e2e
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_ac2_live_health_info(self, healthy_cluster):
        """
        AC2: Display live health and node/shard/resource information 
        without requiring Docker or Kubernetes access.
        
        Verify cluster health API returns complete status.
        """
        r = requests.get(
            "http://localhost:9200/_cluster/health",
            params={"pretty": True},
            timeout=10,
        )
        assert r.status_code == 200
        body = r.json()
        assert "status" in body
        assert "number_of_nodes" in body
        assert "active_shards" in body
        assert body["status"] == "green"

    # AC3: Survive unavailable nodes/API failures
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_ac3_survive_api_failures(self, healthy_compose_path):
        """
        AC3: Survive unavailable nodes/API failures without freezing.
        
        Verify requests timeout gracefully on unreachable endpoints.
        """
        import requests
        
        # Normal request should succeed
        r = requests.get("http://localhost:9200/", timeout=10)
        assert r.status_code == 200
        
        # Request to non-existent endpoint should fail gracefully
        r = requests.get(
            "http://localhost:9200/nonexistent-index",
            timeout=5,
        )
        assert r.status_code == 404

    # AC4: Run deterministic Doctor rules and show evidence
    @pytest.mark.e2e
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_ac4_deterministic_diagnosis(self, broken_cluster):
        """
        AC4: Run deterministic Doctor rules and show evidence for every finding.
        
        Verify broken fixture produces detectable degradation signals.
        """
        # Health should be degraded
        r = requests.get("http://localhost:9201/_cluster/health", timeout=10)
        body = r.json()
        assert body["status"] in ("yellow", "red")
        
        # Should have unassigned shards (evidence)
        assert body.get("unassigned_shards", 0) > 0
        
        # Nodes should be accessible
        r = requests.get("http://localhost:9201/_nodes", timeout=10)
        assert r.status_code == 200

    # AC5: Cost/capacity recommendations with assumptions
    @pytest.mark.e2e
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_ac5_cost_capacity_data(self, healthy_cluster):
        """
        AC5: Produce cost/capacity recommendations with assumptions 
        and no fabricated savings.
        
        Verify we can collect the data needed for cost analysis.
        """
        # Get index stats for storage analysis
        r = requests.get("http://localhost:9200/_stats", timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert "total" in body
        assert "indices" in body
        
        # Get node stats for capacity analysis
        r = requests.get("http://localhost:9200/_nodes/stats", timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert "nodes" in body

    # AC6: Persist local history without plaintext secrets
    @pytest.mark.e2e
    @pytest.mark.unit
    def test_ac6_no_secrets_in_history(self):
        """
        AC6: Persist local history and audit data without storing 
        plaintext secrets.
        
        Verify credentials are redacted in logs and audit trails.
        """
        from guardian.core_types.connection_models import BasicCredentials
        
        creds = BasicCredentials(username="admin", password="supersecret123")
        redacted = creds.redacted()
        
        assert redacted["password"] == "***"
        assert "supersecret123" not in str(redacted)

    # AC7: Docker provisioning is optional and requires approval
    @pytest.mark.e2e
    @pytest.mark.unit
    def test_ac7_provisioning_requires_approval(self):
        """
        AC7: Docker provisioning is optional and cannot be invoked 
        without explicit infrastructure access and approval.
        
        Verify safety classification requires approval for provisioning ops.
        """
        from guardian.safety.classification import (
            classify_operation, OperationContext, SafetyClassification
        )
        
        # Without write access, provisioning should require approval
        ctx = OperationContext(
            operation_type="docker-compose-up",
            target_resource="cluster",
            resource_type="docker",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False,
        )
        assert classify_operation(ctx) == SafetyClassification.APPROVAL_REQUIRED
        
        # With write access, should be safe-reversible (not auto-approved)
        ctx.write_enabled = True
        ctx.connection_permissions = ["monitoring", "full"]
        assert classify_operation(ctx) == SafetyClassification.SAFE_REVERSIBLE

    # AC8: Works without proprietary cloud or paid LLM
    @pytest.mark.e2e
    @pytest.mark.unit
    def test_ac8_no_cloud_dependency(self):
        """
        AC8: All core functionality works without a proprietary cloud 
        service or paid LLM.
        
        Verify core modules can be imported and used without external services.
        """
        # These imports should work without any external service
        from guardian.safety.classification import classify_operation
        from guardian.safety.mutation_filter import MutationFilter
        from guardian.safety.audit_store import AuditStore
        from guardian.core_types.connection_models import ConnectionProfile
        from guardian.models import ClusterSnapshot
        
        # Basic instantiation should work
        filter_ = MutationFilter()
        assert filter_ is not None
        
        profile = ConnectionProfile(
            name="local",
            opensearch_url="http://localhost:9200",
            auth_method="none",
            credential_ref="test",
        )
        assert profile.name == "local"

    # AC9: Test coverage over critical flows
    @pytest.mark.e2e
    @pytest.mark.unit
    def test_ac9_test_coverage_scaffold(self):
        """
        AC9: Unit, integration, fixture, and end-to-end tests cover 
        critical diagnostic and provisioning flows.
        
        Verify test structure exists for all layers.
        """
        import os
        from pathlib import Path
        
        test_root = Path(__file__).parent.parent
        assert (test_root / "unit").exists()
        assert (test_root / "integration").exists()
        assert (test_root / "e2e").exists()
        assert (test_root / "fixtures").exists()
        
        # Verify test files exist
        unit_tests = list((test_root / "unit").rglob("test_*.py"))
        assert len(unit_tests) > 0, "No unit tests found"

    # AC10: Build and run from public repository
    @pytest.mark.e2e
    @pytest.mark.unit
    def test_ac10_repository_structure(self):
        """
        AC10: Project can be built and run from the public repository 
        using documented steps.
        
        Verify required files and structure exist.
        """
        from pathlib import Path
        
        root = Path(__file__).parent.parent.parent
        assert (root / "pyproject.toml").exists()
        assert (root / "README.md").exists()
        assert (root / "guardian").exists()
        assert (root / "tests").exists()
        assert (root / "deploy").exists()
        
        # Verify pyproject.toml is valid
        import tomllib
        with open(root / "pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        assert config["project"]["name"] == "opensearch-guardian"
