"""Tests for connection auth adapters."""

from unittest.mock import MagicMock, patch

import pytest

from guardian.connections.auth.basic import BasicCredentials, resolve_basic_credentials
from guardian.connections.auth.client_cert import ClientCertAuthAdapter
from guardian.connections.auth.base import AuthAdapterProtocol
from guardian.core_types.connection_models import ConnectionProfile, AuthMethod, ClientCertCredentials


class TestAuthAdapterProtocol:
    """Tests for AuthAdapterProtocol base class."""

    def test_is_abc(self):
        assert issubclass(AuthAdapterProtocol, object)

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            AuthAdapterProtocol()


class TestBasicCredentials:
    """Tests for BasicCredentials."""

    def test_client_kwargs_http(self):
        profile = ConnectionProfile(
            name="test",
            opensearch_url="http://localhost:9200",
            auth_method=AuthMethod.BASIC,
            credential_ref="test",
        )
        creds = BasicCredentials(username="admin", password="secret")
        kwargs = creds.client_kwargs(profile)
        assert "localhost:9200" in kwargs["hosts"][0]
        assert kwargs["http_auth"] == ("admin", "secret")
        assert kwargs["use_ssl"] is False
        assert kwargs["verify_certs"] is True

    def test_client_kwargs_https(self):
        profile = ConnectionProfile(
            name="test",
            opensearch_url="https://localhost:9200",
            auth_method=AuthMethod.BASIC,
            credential_ref="test",
        )
        creds = BasicCredentials(username="admin", password="secret")
        kwargs = creds.client_kwargs(profile)
        assert kwargs["use_ssl"] is True
        assert kwargs["verify_certs"] is True

    def test_client_kwargs_tls_verify_false(self):
        profile = ConnectionProfile(
            name="test",
            opensearch_url="https://localhost:9200",
            auth_method=AuthMethod.BASIC,
            credential_ref="test",
            tls_verify=False,
        )
        creds = BasicCredentials(username="admin", password="secret")
        kwargs = creds.client_kwargs(profile)
        assert kwargs["verify_certs"] is False


class TestResolveBasicCredentials:
    """Tests for resolve_basic_credentials."""

    @patch("guardian.connections.auth.basic.KeychainStore")
    def test_loads_from_keychain(self, mock_keychain):
        mock_store = MagicMock()
        mock_creds = MagicMock()
        mock_creds.username = "admin"
        mock_creds.password = "secret"
        mock_store.load_basic.return_value = mock_creds
        mock_keychain.return_value = mock_store

        profile = ConnectionProfile(
            name="test",
            opensearch_url="http://localhost:9200",
            auth_method=AuthMethod.BASIC,
            credential_ref="test-ref",
        )
        result = resolve_basic_credentials(profile, mock_store)
        assert result.username == "admin"
        assert result.password == "secret"
        mock_store.load_basic.assert_called_once_with("test-ref")


class TestClientCertAuthAdapter:
    """Tests for ClientCertAuthAdapter."""

    def test_validate(self):
        adapter = ClientCertAuthAdapter(cert_path="/cert.pem", key_path="/key.pem")
        assert adapter.validate({"cert": "/cert.pem", "key": "/key.pem"}) is True
        assert adapter.validate({"cert": "/cert.pem"}) is False
        assert adapter.validate({"key": "/key.pem"}) is False
        assert adapter.validate({}) is False

    @patch("guardian.connections.keychain.KeychainStore")
    def test_resolve_credentials(self, mock_keychain):
        mock_store = MagicMock()
        mock_creds = MagicMock()
        mock_creds.cert_data = b"-----BEGIN CERTIFICATE-----test-----END CERTIFICATE-----"
        mock_creds.key_data = b"-----BEGIN PRIVATE KEY-----test-----END PRIVATE KEY-----"
        mock_store.load_client_cert.return_value = mock_creds
        mock_keychain.return_value = mock_store

        profile = ConnectionProfile(
            name="test",
            opensearch_url="https://localhost:9200",
            auth_method=AuthMethod.CLIENT_CERT,
            credential_ref="client-cert-ref",
        )
        adapter = ClientCertAuthAdapter()
        result = adapter.resolve_credentials(profile)

        assert "cert" in result
        assert "key" in result
        assert result["cert"].endswith(".pem")
        assert result["key"].endswith(".pem")

    @pytest.fixture(autouse=True)
    def _generate_certs(self, tmp_path):
        """Generate valid self-signed certs for SSL tests."""
        import subprocess
        cert_file = tmp_path / "cert.pem"
        key_file = tmp_path / "key.pem"
        subprocess.run(
            ["openssl", "req", "-x509", "-newkey", "rsa:2048",
             "-keyout", str(key_file), "-out", str(cert_file),
             "-days", "1", "-nodes", "-subj", "/CN=test"],
            capture_output=True,
        )
        self._cert_file = cert_file
        self._key_file = key_file

    def test_build_client_options(self):
        adapter = ClientCertAuthAdapter()
        adapter._tmp_cert = self._cert_file
        adapter._tmp_key = self._key_file
        options = adapter.build_client_options(use_ssl=True, tls_verify=True)
        assert options["use_ssl"] is True
        assert options["verify_certs"] is True
        assert "ssl_context" in options

    def test_build_client_options_no_verify(self):
        adapter = ClientCertAuthAdapter()
        adapter._tmp_cert = self._cert_file
        adapter._tmp_key = self._key_file
        options = adapter.build_client_options(use_ssl=True, tls_verify=False)
        assert options["verify_certs"] is False
        assert options["use_ssl"] is True

    def test_cleanup(self, tmp_path):
        cert_file = tmp_path / "cert.pem"
        key_file = tmp_path / "key.pem"
        cert_file.write_bytes(b"test")
        key_file.write_bytes(b"test")

        adapter = ClientCertAuthAdapter()
        adapter._tmp_cert = cert_file
        adapter._tmp_key = key_file
        adapter.cleanup()

        assert not cert_file.exists()
        assert not key_file.exists()

    def test_cleanup_no_files(self):
        adapter = ClientCertAuthAdapter()
        adapter.cleanup()

    def test_cleanup_with_missing_files(self, tmp_path):
        adapter = ClientCertAuthAdapter()
        adapter._tmp_cert = tmp_path / "nonexistent.pem"
        adapter._tmp_key = tmp_path / "nonexistent.pem"
        adapter.cleanup()
