"""Unit tests for Docker fixture management."""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestFixtureHelpers:
    """Tests for fixture management helpers in conftest.py."""

    def test_fixture_paths_exist(self):
        """Fixture compose files should exist."""
        root = Path(__file__).parent.parent.parent
        healthy = root / "deploy" / "docker" / "fixtures" / "healthy" / "docker-compose.yml"
        broken = root / "deploy" / "docker" / "fixtures" / "broken" / "docker-compose.yml"
        assert healthy.exists()
        assert broken.exists()

    def test_compose_files_valid_yaml(self):
        """Fixture compose files should be valid YAML."""
        import yaml
        root = Path(__file__).parent.parent.parent
        healthy = root / "deploy" / "docker" / "fixtures" / "healthy" / "docker-compose.yml"
        broken = root / "deploy" / "docker" / "fixtures" / "broken" / "docker-compose.yml"
        
        with open(healthy) as f:
            healthy_yaml = yaml.safe_load(f)
        assert "services" in healthy_yaml
        
        with open(broken) as f:
            broken_yaml = yaml.safe_load(f)
        assert "services" in broken_yaml

    @pytest.mark.docker
    def test_docker_compose_available(self):
        """Docker Compose should be available."""
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True,
                timeout=5,
            )
            assert result.returncode == 0
        except FileNotFoundError:
            pytest.skip("Docker Compose not available")


class TestMockClients:
    """Tests for mock OpenSearch client in conftest.py."""

    def test_mock_client_info(self, mock_httpx_client):
        """Mock client should return expected info."""
        mock_httpx_client.get.return_value.status_code = 200
        mock_httpx_client.get.return_value.json.return_value = {
            "status": "green"
        }
        response = mock_httpx_client.get("http://test/_cluster/health")
        assert response.status_code == 200
        assert response.json() == {"status": "green"}
