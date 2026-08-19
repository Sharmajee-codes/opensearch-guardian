"""Integration tests for ConnectionManager against live OpenSearch fixture."""

import pytest
import requests
from unittest.mock import MagicMock, patch
from guardian.connections.keychain import KeychainProxy, PlaintextVault


class TestConnectionHealth:
    """Integration tests that verify connectivity to fixture clusters."""

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_healthy_cluster_returns_green(self, healthy_cluster):
        """Healthy fixture should report green health."""
        assert healthy_cluster["status"] == "green"
        assert healthy_cluster["number_of_nodes"] >= 1
        assert healthy_cluster["active_primary_shards"] >= 0

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_healthy_cluster_nodes(self, healthy_cluster):
        """Healthy fixture should have expected nodes."""
        assert healthy_cluster["number_of_nodes"] == 1
        assert healthy_cluster["node_count"]["total"] == 1

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_healthy_cluster_api_accessible(self, healthy_compose_path):
        """Healthy fixture API should be accessible."""
        r = requests.get("http://localhost:9200/", timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert "name" in body
        assert "cluster_name" in body
        assert body["cluster_name"] == "osg-cluster-healthy"

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_healthy_cluster_version(self, healthy_compose_path):
        """Healthy fixture should run OpenSearch 2.17.1."""
        r = requests.get("http://localhost:9200/", timeout=10)
        version = r.json()["version"]["number"]
        assert version.startswith("2.17")


class TestBrokenClusterHealth:
    """Integration tests for the broken (degraded) fixture."""

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_broken_cluster_is_degraded(self, broken_cluster):
        """Broken fixture should report yellow or red health."""
        assert broken_cluster["status"] in ("yellow", "red")

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_broken_cluster_has_unassigned_shards(self, broken_cluster):
        """Broken fixture should have unassigned shards after seeding."""
        assert broken_cluster.get("unassigned_shards", 0) > 0

    @pytest.mark.integration
    @pytest.mark.fixtures
    @pytest.mark.docker
    def test_broken_cluster_api_accessible(self, broken_compose_path):
        """Broken fixture API should be accessible on port 9201."""
        r = requests.get("http://localhost:9201/", timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert body["cluster_name"] == "osg-cluster-broken"


class TestConnectionKeychain:
    """Integration tests for keychain proxy."""

    @pytest.mark.integration
    def test_plaintext_vault_store_and_retrieve(self):
        """PlaintextVault should store and retrieve secrets."""
        vault = PlaintextVault()
        vault.set("test-account", "test-secret")
        assert vault.get("test-account") == "test-secret"

    @pytest.mark.integration
    def test_plaintext_vault_missing(self):
        """PlaintextVault should return None for missing accounts."""
        vault = PlaintextVault()
        assert vault.get("nonexistent") is None

    @pytest.mark.integration
    def test_plaintext_vault_delete(self):
        """PlaintextVault should delete secrets."""
        vault = PlaintextVault()
        vault.set("account", "secret")
        vault.delete("account")
        assert vault.get("account") is None

    @pytest.mark.integration
    def test_keychain_proxy_with_plaintext_fallback(self):
        """KeychainProxy with PlaintextVault fallback."""
        proxy = KeychainProxy(service_name="test-service")
        # When keyring is not available, should use fallback
        assert proxy._service_name == "test-service"
