"""Unit tests for repository structure and configuration."""

import pytest
from pathlib import Path


class TestRepositoryStructure:
    """Tests for project structure and configuration."""

    def test_pyproject_exists(self):
        """pyproject.toml should exist."""
        root = Path(__file__).parent.parent.parent
        assert (root / "pyproject.toml").exists()

    def test_guardian_package_exists(self):
        """guardian/ package should exist."""
        root = Path(__file__).parent.parent.parent
        assert (root / "guardian").exists()
        assert (root / "guardian" / "__init__.py").exists()

    def test_tests_directory_exists(self):
        """tests/ directory should exist."""
        root = Path(__file__).parent.parent.parent
        assert (root / "tests").exists()

    def test_readme_exists(self):
        """README.md should exist."""
        root = Path(__file__).parent.parent.parent
        assert (root / "README.md").exists()

    def test_fixtures_directory_exists(self):
        """fixtures/ directory should exist."""
        root = Path(__file__).parent.parent.parent
        assert (root / "deploy" / "docker" / "fixtures").exists()


class TestPyprojectConfig:
    """Tests for pyproject.toml configuration."""

    def test_project_name(self):
        """Project name should be opensearch-guardian."""
        import tomllib
        root = Path(__file__).parent.parent.parent
        with open(root / "pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        assert config["project"]["name"] == "opensearch-guardian"

    def test_python_requires(self):
        """Python version requirement should be >= 3.12."""
        import tomllib
        root = Path(__file__).parent.parent.parent
        with open(root / "pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        assert config["project"]["requires-python"] == ">=3.12"

    def test_pytest_configured(self):
        """pytest configuration should exist."""
        import tomllib
        root = Path(__file__).parent.parent.parent
        with open(root / "pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        assert "tool" in config
        assert "pytest" in config["tool"]

    def test_dev_dependencies_include_pytest(self):
        """Dev dependencies should include pytest."""
        import tomllib
        root = Path(__file__).parent.parent.parent
        with open(root / "pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        dev_deps = config["project"]["optional-dependencies"]["dev"]
        pytest_deps = [d for d in dev_deps if "pytest" in d]
        assert len(pytest_deps) > 0
