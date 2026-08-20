"""Tests for CLI module."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from guardian.cli import app
from guardian.connections.manager import ConnectionManager
from guardian.cli import _manager


class TestCLI:
    """Tests for CLI commands."""

    def setup_method(self):
        """Reset manager singleton."""
        if hasattr(_manager, "_instance"):
            del _manager._instance

    def test_app_exists(self):
        assert app is not None

    def test_connection_list_empty(self):
        runner = CliRunner()
        result = runner.invoke(app, ["connection", "list"])
        assert result.exit_code == 0
        assert "No connection profiles found" in result.output

    @patch("guardian.cli.ConnectionManager")
    def test_connection_list_with_profiles(self, mock_mgr_class):
        mock_mgr = MagicMock()
        mock_mgr.list_profiles.return_value = [
            MagicMock(
                id="test-id-1",
                name="prod",
                opensearch_url="http://localhost:9200",
                mode=MagicMock(value="read_only"),
                status=MagicMock(value="active"),
                write_enabled=False,
            )
        ]
        mock_mgr_class.return_value = mock_mgr

        runner = CliRunner()
        result = runner.invoke(app, ["connection", "list"])
        assert result.exit_code == 0
        assert "prod" in result.output

    @patch("guardian.cli.ConnectionManager")
    def test_connection_add(self, mock_mgr_class):
        mock_mgr = MagicMock()
        mock_profile = MagicMock()
        mock_profile.id = "new-id"
        mock_mgr.add.return_value = mock_profile
        mock_mgr_class.return_value = mock_mgr

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "connection", "add",
                "--name", "test",
                "--url", "http://localhost:9200",
                "--auth", "basic",
                "--cred-ref", "test-ref",
            ],
        )
        assert result.exit_code == 0
        mock_mgr.add.assert_called_once()

    @patch("guardian.cli.ConnectionManager")
    def test_connection_test(self, mock_mgr_class):
        mock_mgr = MagicMock()
        mock_profile = MagicMock()
        mock_profile.id = "test-id"
        mock_profile.status = MagicMock(value="active")
        mock_mgr.test_connection = MagicMock(return_value=mock_profile)
        mock_mgr_class.return_value = mock_mgr

        runner = CliRunner()
        result = runner.invoke(app, ["connection", "test", "test-id"])
        assert result.exit_code == 0
        mock_mgr.test_connection.assert_called_once_with("test-id")

    @patch("guardian.cli.ConnectionManager")
    def test_connection_enable_write(self, mock_mgr_class):
        mock_mgr = MagicMock()
        mock_profile = MagicMock()
        mock_profile.id = "test-id"
        mock_profile.write_enabled = True
        mock_mgr.enable_write.return_value = mock_profile
        mock_mgr_class.return_value = mock_mgr

        runner = CliRunner()
        result = runner.invoke(app, ["connection", "enable-write", "test-id"])
        assert result.exit_code == 0
        mock_mgr.enable_write.assert_called_once_with("test-id")

    @patch("guardian.cli.ConnectionManager")
    def test_connection_enable_provisioning(self, mock_mgr_class):
        mock_mgr = MagicMock()
        mock_profile = MagicMock()
        mock_profile.id = "test-id"
        mock_profile.provisioning_enabled = True
        mock_mgr.enable_provisioning.return_value = mock_profile
        mock_mgr_class.return_value = mock_mgr

        runner = CliRunner()
        result = runner.invoke(app, ["connection", "enable-provisioning", "test-id"])
        assert result.exit_code == 0
        mock_mgr.enable_provisioning.assert_called_once_with("test-id")

    @patch("guardian.cli.ConnectionManager")
    def test_connection_delete(self, mock_mgr_class):
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr

        runner = CliRunner()
        result = runner.invoke(app, ["connection", "delete", "test-id"])
        assert result.exit_code == 0
        mock_mgr.delete.assert_called_once_with("test-id")

    @patch("guardian.cli.ConnectionManager")
    def test_connection_get(self, mock_mgr_class):
        mock_mgr = MagicMock()
        mock_profile = MagicMock(
            id="test-id",
            name="test",
            opensearch_url="http://localhost:9200",
            auth_method=MagicMock(value="basic"),
            credential_ref="test-ref",
            tls_verify=True,
            tls_ca_path=None,
            custom_ca_ref=None,
            metadata={},
            mode=MagicMock(value="read_only"),
            status=MagicMock(value="active"),
            write_enabled=False,
            provisioning_enabled=False,
            proxy_url=None,
            proxy_auth_username=None,
            proxy_auth_password=None,
            proxy_ssl_verify=True,
        )
        mock_mgr.get.return_value = mock_profile
        mock_mgr_class.return_value = mock_mgr

        runner = CliRunner()
        result = runner.invoke(app, ["connection", "get", "test-id"])
        assert result.exit_code == 0
        assert "test" in result.output


class TestManagerSingleton:
    """Tests for _manager singleton."""

    def setup_method(self):
        if hasattr(_manager, "_instance"):
            del _manager._instance

    def test_singleton(self):
        mgr1 = _manager()
        mgr2 = _manager()
        assert mgr1 is mgr2