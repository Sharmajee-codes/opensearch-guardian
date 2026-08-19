"""Integration tests for OpenSearch API interactions with fixture clusters."""

import pytest
import requests


class TestClusterHealthAPI:
    """Test cluster health API endpoints against fixtures."""

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_cluster_health_endpoint(self, healthy_cluster):
        """Cluster health endpoint should return valid JSON."""
        r = requests.get(
            "http://localhost:9200/_cluster/health",
            params={"pretty": True},
            timeout=10,
        )
        assert r.status_code == 200
        body = r.json()
        assert "status" in body
        assert "timed_out" in body
        assert "number_of_nodes" in body

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_cluster_health_wait_for_status(self, healthy_cluster):
        """Cluster health with wait_for_status parameter."""
        r = requests.get(
            "http://localhost:9200/_cluster/health",
            params={"wait_for_status": "green", "timeout": "10s"},
            timeout=15,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "green"

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_nodes_stats_endpoint(self, healthy_cluster):
        """Nodes stats endpoint should return node information."""
        r = requests.get("http://localhost:9200/_nodes/stats", timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert "nodes" in body
        assert len(body["nodes"]) >= 1

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_cat_nodes_endpoint(self, healthy_cluster):
        """Cat nodes endpoint should list nodes."""
        r = requests.get("http://localhost:9200/_cat/nodes?h=name,role", timeout=10)
        assert r.status_code == 200
        lines = r.text.strip().split("\n")
        assert len(lines) >= 1

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_cluster_stats_endpoint(self, healthy_cluster):
        """Cluster stats endpoint should return cluster information."""
        r = requests.get("http://localhost:9200/_cluster/stats", timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert "cluster_name" in body
        assert "nodes" in body

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_indices_stats_endpoint(self, healthy_cluster):
        """Indices stats endpoint should be accessible."""
        r = requests.get("http://localhost:9200/_stats", timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert "total" in body


class TestBrokenClusterAPI:
    """Test APIs against broken fixture to verify degradation signals."""

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_broken_cluster_health_is_degraded(self, broken_cluster):
        """Broken fixture should have degraded health."""
        assert broken_cluster["status"] in ("yellow", "red")

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_broken_cluster_has_unassigned_shards(self, broken_cluster):
        """Broken fixture should report unassigned shards."""
        unassigned = broken_cluster.get("unassigned_shards", 0)
        assert unassigned > 0

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_broken_cluster_cat_shards(self, broken_compose_path):
        """Cat shards should show unassigned shards in broken fixture."""
        r = requests.get("http://localhost:9201/_cat/shards", timeout=10)
        assert r.status_code == 200
        lines = r.text.strip().split("\n")
        # At least some shards should be present
        assert len(lines) > 0

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_broken_cluster_nodes_stats(self, broken_cluster):
        """Nodes stats should be accessible even in broken state."""
        r = requests.get("http://localhost:9201/_nodes/stats", timeout=10)
        assert r.status_code == 200


class TestIndexOperations:
    """Test basic index operations against healthy fixture."""

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_create_and_delete_index(self, healthy_cluster):
        """Should be able to create and delete an index."""
        # Create index
        r = requests.put(
            "http://localhost:9200/test-guardian-index",
            json={"settings": {"number_of_shards": 1, "number_of_replicas": 0}},
            timeout=10,
        )
        assert r.status_code == 200
        assert r.json()["acknowledged"] is True

        # Verify index exists
        r = requests.get("http://localhost:9200/test-guardian-index", timeout=10)
        assert r.status_code == 200

        # Delete index
        r = requests.delete("http://localhost:9200/test-guardian-index", timeout=10)
        assert r.status_code == 200
        assert r.json()["acknowledged"] is True

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_index_exists_after_creation(self, healthy_cluster):
        """Index should exist after creation."""
        requests.put(
            "http://localhost:9200/test-exists-index",
            json={"settings": {"number_of_shards": 1}},
            timeout=10,
        )
        r = requests.head("http://localhost:9200/test-exists-index", timeout=10)
        assert r.status_code == 200
        requests.delete("http://localhost:9200/test-exists-index", timeout=10)
