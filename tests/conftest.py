"""Project-wide pytest configuration and fixtures."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest
import requests


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
GUARDIAN_PKG = ROOT / "guardian"
FIXTURES_DIR = ROOT / "deploy" / "docker" / "fixtures"
HEALTHY_COMPOSE = FIXTURES_DIR / "healthy" / "docker-compose.yml"
BROKEN_COMPOSE = FIXTURES_DIR / "broken" / "docker-compose.yml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def wait_for_cluster(port: int = 9200, timeout: int = 120) -> dict:
    """Block until OpenSearch is healthy at *port*, then return cluster health."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(
                f"http://localhost:{port}/_cluster/health",
                params={"wait_for_status": "yellow"},
                timeout=5,
            )
            if r.status_code == 200:
                return r.json()
        except requests.ConnectionError:
            pass
        time.sleep(2)
    raise RuntimeError(f"OpenSearch not available at port {port} after {timeout}s")


def start_compose(compose_path: Path) -> None:
    """Bring up a fixture compose stack."""
    subprocess.run(
        ["docker", "compose", "-f", str(compose_path), "up", "-d"],
        check=True,
        capture_output=True,
    )


def stop_compose(compose_path: Path, remove_volumes: bool = True) -> None:
    """Tear down a fixture compose stack."""
    args = ["docker", "compose", "-f", str(compose_path), "down"]
    if remove_volumes:
        args.append("-v")
    subprocess.run(args, check=True, capture_output=True)


def seed_broken(compose_path: Path = BROKEN_COMPOSE) -> None:
    """Run the seed container for the broken fixture."""
    subprocess.run(
        ["docker", "compose", "-f", str(compose_path), "run", "--rm", "seed"],
        check=True,
        capture_output=True,
    )


def make_safe_request(port: int = 9200, path: str = "/") -> requests.Response:
    """Synchronous HTTP call to a fixture (no TLS, no auth)."""
    return requests.get(f"http://localhost:{port}{path}", timeout=10)


# ---------------------------------------------------------------------------
# Fixtures — unit-test helpers (no Docker required)
# ---------------------------------------------------------------------------


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def mock_httpx_client():
    """Return a MagicMock configured like httpx.Client for unit tests."""
    client = MagicMock()
    client.get.return_value.status_code = 200
    client.get.return_value.json.return_value = {"status": "green"}
    return client


@pytest.fixture
def tmp_audit_path(tmp_path: Path) -> Path:
    """Temporary directory for audit-store tests (no real disk writes)."""
    return tmp_path / "audit"


# ---------------------------------------------------------------------------
# Fixtures — integration / e2e (Docker required)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def healthy_compose_path() -> Path:
    return HEALTHY_COMPOSE


@pytest.fixture(scope="session")
def broken_compose_path() -> Path:
    return BROKEN_COMPOSE


@pytest.fixture(scope="session")
def healthy_cluster(healthy_compose_path: Path) -> Generator[dict, None, None]:
    """Start the healthy fixture, yield health JSON, tear down after."""
    start_compose(healthy_compose_path)
    health = wait_for_cluster(port=9200)
    try:
        yield health
    finally:
        stop_compose(healthy_compose_path, remove_volumes=True)


@pytest.fixture(scope="session")
def broken_cluster(broken_compose_path: Path) -> Generator[dict, None, None]:
    """Start the broken fixture, seed it, yield health JSON, tear down."""
    start_compose(broken_compose_path)
    health = wait_for_cluster(port=9201)
    try:
        seed_broken(broken_compose_path)
        # Re-check after seeding
        time.sleep(3)
        health = make_safe_request(port=9201).json()
        yield health
    finally:
        stop_compose(broken_compose_path, remove_volumes=True)


@pytest.fixture
def opensearch_client(healthy_cluster: dict):
    """Return a mock opensearch-py client configured for unit tests."""
    from unittest.mock import MagicMock
    client = MagicMock()
    client.info.return_value = {
        "name": "osg-node1",
        "cluster_name": "osg-cluster-healthy",
        "version": {"number": "2.17.1"},
        "tagline": "You Know, for Search",
    }
    client.cluster.health.return_value = healthy_cluster
    client.nodes.stats.return_value = {
        "nodes": {
            "node-1": {
                "name": "osg-node1",
                "host": "127.0.0.1",
                "roles": ["master", "data", "ingest"],
                "jvm": {
                    "mem": {
                        "heap_used_in_bytes": 134217728,
                        "heap_max_in_bytes": 536870912,
                        "heap_used_percent": 25,
                    },
                    "buf_pools": {
                        "direct": {"count": 10, "used_in_bytes": 1024},
                        "mapped": {"count": 0, "used_in_bytes": 0},
                    },
                    "gc": {
                        "collectors": {
                            "young": {"collection_count": 0, "collection_time_in_ms": 0},
                            "old": {"collection_count": 0, "collection_time_in_ms": 0},
                        }
                    },
                },
                "os": {
                    "cpu": {"percent": 10},
                    "mem": {
                        "total_in_bytes": 8589934592,
                        "used_in_bytes": 4294967296,
                        "free_in_bytes": 4294967296,
                    },
                },
                "process": {
                    "cpu": {"percent": 5, "total_in_millis": 10000},
                    "open_file_descriptors": 100,
                    "max_file_descriptors": 65536,
                },
                "thread_pool": {
                    "write": {"threads": 4, "queue": 0, "active": 0, "rejected": 0, "completed": 0},
                    "search": {"threads": 8, "queue": 0, "active": 0, "rejected": 0, "completed": 0},
                },
                "fs": [
                    {
                        "total": {
                            "total_in_bytes": 107374182400,
                            "free_in_bytes": 53687091200,
                            "available_in_bytes": 53687091200,
                        }
                    }
                ],
            }
        }
    }
    client.cluster.stats.return_value = {
        "cluster_name": "osg-cluster-healthy",
        "cluster_uuid": "test-uuid",
        "nodes": {
            "counts": {"total": 1, "data": 1, "master": 1, "ingest": 1},
        },
    }
    client.indices.stats.return_value = {
        "total": {"primaries": {"docs": {"count": 0}, "store": {"size_in_bytes": 0}}},
        "indices": {},
    }
    client.indices.get_settings.return_value = {}
    client.cluster.get_settings.return_value = {}
    client.nodes.info.return_value = {
        "nodes": {
            "node-1": {
                "name": "osg-node1",
                "version": "2.17.1",
                "roles": ["master", "data", "ingest"],
            }
        }
    }
    client.cluster.put_settings.return_value = {"acknowledged": True}
    client.indices.create.return_value = {"acknowledged": True, "shards_acknowledged": True}
    client.indices.delete.return_value = {"acknowledged": True}
    client.indices.put_settings.return_value = {"acknowledged": True}
    client.transport.transport = MagicMock()
    client.transport.transport.pool_mgr = MagicMock()
    return client
