"""Unit tests for ConnectionProfile model."""

import pytest
from guardian.core_types.connection_models import (
    AuthMethod,
    ConnectionMode,
    ConnectionStatus,
    ConnectionProfile,
    BasicCredentials,
    ClientCertCredentials,
    ConnectionTestResult,
    ClusterIdentity,
    PermissionCheckResult,
    TLSCheckResult,
)


class TestAuthMethod:
    """Tests for AuthMethod enum."""

    def test_all_values_present(self):
        assert AuthMethod.BASIC.value == "basic"
        assert AuthMethod.CLIENT_CERT.value == "client_cert"
        assert AuthMethod.CUSTOM_CA.value == "custom_ca"
        assert AuthMethod.API_KEY.value == "api_key"
        assert AuthMethod.NONE.value == "none"

    def test_none_is_for_development(self):
        """NONE should be for development only (per design doc)."""
        assert AuthMethod.NONE.value == "none"


class TestConnectionMode:
    """Tests for ConnectionMode enum."""

    def test_all_values_present(self):
        assert ConnectionMode.READ_ONLY.value == "read_only"
        assert ConnectionMode.READ_WRITE.value == "read_write"
        assert ConnectionMode.PROVISIONING.value == "provisioning"

    def test_read_only_default(self):
        """Default mode should be read-only (per SOP §8)."""
        profile = ConnectionProfile(
            name="test",
            opensearch_url="http://localhost:9200",
            auth_method=AuthMethod.NONE,
            credential_ref="test",
        )
        assert profile.mode == ConnectionMode.READ_ONLY


class TestConnectionStatus:
    """Tests for ConnectionStatus enum."""

    def test_all_values_present(self):
        values = {s.value for s in ConnectionStatus}
        expected = {"disconnected", "connecting", "active", "degraded", "error", "failed", "recovering"}
        assert values == expected

    def test_default_is_disconnected(self):
        profile = ConnectionProfile(
            name="test",
            opensearch_url="http://localhost:9200",
            auth_method=AuthMethod.NONE,
            credential_ref="test",
        )
        assert profile.status == ConnectionStatus.DISCONNECTED


class TestBasicCredentials:
    """Tests for BasicCredentials model."""

    def test_basic_credentials(self):
        creds = BasicCredentials(username="admin", password="secret")
        assert creds.username == "admin"
        assert creds.password == "secret"

    def test_frozen(self):
        """Credentials should be frozen (immutable)."""
        creds = BasicCredentials(username="admin", password="secret")
        with pytest.raises(Exception):
            creds.username = "other"

    def test_redacted(self):
        """Redacted should mask password."""
        creds = BasicCredentials(username="admin", password="secret123")
        redacted = creds.redacted()
        assert redacted["username"] == "admin"
        assert redacted["password"] == "***"
        assert "secret123" not in str(redacted)


class TestClientCertCredentials:
    """Tests for ClientCertCredentials model."""

    def test_client_cert(self):
        cert_data = b"-----BEGIN CERTIFICATE-----..."
        key_data = b"-----BEGIN PRIVATE KEY-----..."
        creds = ClientCertCredentials(cert_data=cert_data, key_data=key_data)
        assert len(creds.cert_data) > 0
        assert len(creds.key_data) > 0

    def test_redacted(self):
        """Redacted should mask cert/key data."""
        cert_data = b"cert-123456"
        key_data = b"key-data"
        creds = ClientCertCredentials(cert_data=cert_data, key_data=key_data)
        redacted = creds.redacted()
        assert redacted["cert_data"] == "<11 bytes>"
        assert redacted["key_data"] == "<REDACTED>"


class TestConnectionProfile:
    """Tests for ConnectionProfile model."""

    def test_minimal_profile(self):
        """Create a minimal profile with required fields."""
        profile = ConnectionProfile(
            name="prod-cluster",
            opensearch_url="https://opensearch.example.com:9200",
            auth_method=AuthMethod.BASIC,
            credential_ref="opensearch-guardian:prod",
        )
        assert profile.name == "prod-cluster"
        assert profile.tls_verify is True
        assert profile.write_enabled is False
        assert profile.mode == ConnectionMode.READ_ONLY

    def test_auto_generate_id(self):
        """Profile should auto-generate a UUID."""
        profile = ConnectionProfile(
            name="test",
            opensearch_url="http://localhost:9200",
            auth_method=AuthMethod.NONE,
            credential_ref="test",
        )
        assert profile.id is not None
        assert len(profile.id) == 36  # UUID format

    def test_enable_write(self):
        """Enable write should set write_enabled and mode."""
        profile = ConnectionProfile(
            name="test",
            opensearch_url="http://localhost:9200",
            auth_method=AuthMethod.NONE,
            credential_ref="test",
        )
        profile.enable_write()
        assert profile.write_enabled is True
        assert profile.mode == ConnectionMode.READ_WRITE
        assert profile.provisioning_enabled is False

    def test_enable_provisioning(self):
        """Enable provisioning should set both flags."""
        profile = ConnectionProfile(
            name="test",
            opensearch_url="http://localhost:9200",
            auth_method=AuthMethod.NONE,
            credential_ref="test",
        )
        profile.enable_provisioning()
        assert profile.write_enabled is True
        assert profile.provisioning_enabled is True
        assert profile.mode == ConnectionMode.PROVISIONING

    def test_disable_write(self):
        """Disable write should revert to read-only."""
        profile = ConnectionProfile(
            name="test",
            opensearch_url="http://localhost:9200",
            auth_method=AuthMethod.NONE,
            credential_ref="test",
        )
        profile.enable_write()
        profile.disable_write()
        assert profile.write_enabled is False
        assert profile.provisioning_enabled is False
        assert profile.mode == ConnectionMode.READ_ONLY

    def test_is_read_only(self):
        """Check is_read_only helper."""
        profile = ConnectionProfile(
            name="test",
            opensearch_url="http://localhost:9200",
            auth_method=AuthMethod.NONE,
            credential_ref="test",
        )
        assert profile.is_read_only() is True
        profile.enable_write()
        assert profile.is_read_only() is False

    def test_custom_ca_ref(self):
        """Custom CA reference should be optional."""
        profile = ConnectionProfile(
            name="test",
            opensearch_url="https://opensearch.example.com:9200",
            auth_method=AuthMethod.CUSTOM_CA,
            credential_ref="test",
            custom_ca_ref="opensearch-guardian:ca-bundle",
        )
        assert profile.custom_ca_ref == "opensearch-guardian:ca-bundle"

    def test_metadata_default(self):
        """Metadata should default to empty dict."""
        profile = ConnectionProfile(
            name="test",
            opensearch_url="http://localhost:9200",
            auth_method=AuthMethod.NONE,
            credential_ref="test",
        )
        assert profile.metadata == {}


class TestConnectionTestResult:
    """Tests for ConnectionTestResult model."""

    def test_minimal_result(self):
        """Minimal result should pass with no errors."""
        result = ConnectionTestResult(
            passed=True,
            errors=[],
            fatal_errors=[],
        )
        assert result.passed is True
        assert result.errors == []

    def test_failed_result(self):
        """Failed result should have errors."""
        result = ConnectionTestResult(
            passed=False,
            errors=["Connection refused"],
            fatal_errors=["Authentication failed"],
        )
        assert result.passed is False
        assert "Connection refused" in result.errors
        assert "Authentication failed" in result.fatal_errors

    def test_with_identity(self):
        """Result should include cluster identity."""
        identity = ClusterIdentity(
            cluster_name="my-cluster",
            cluster_uuid="abc123",
            version="2.17.1",
        )
        result = ConnectionTestResult(
            passed=True,
            identity=identity,
        )
        assert result.identity.cluster_name == "my-cluster"


class TestPermissionCheckResult:
    """Tests for PermissionCheckResult model."""

    def test_read_only_permissions(self):
        result = PermissionCheckResult(
            read_permitted=True,
            write_permitted=False,
            user_roles=["monitoring"],
        )
        assert result.read_permitted is True
        assert result.write_permitted is False

    def test_full_permissions(self):
        result = PermissionCheckResult(
            read_permitted=True,
            write_permitted=True,
            user_roles=["monitoring", "all"],
        )
        assert result.write_permitted is True


class TestTLSCheckResult:
    """Tests for TLSCheckResult model."""

    def test_valid_tls(self):
        result = TLSCheckResult(
            valid=True,
            subject="CN=opensearch.example.com",
            issuer="CN=Example CA",
        )
        assert result.valid is True
        assert result.error is None

    def test_invalid_tls(self):
        result = TLSCheckResult(
            valid=False,
            error="Certificate expired",
        )
        assert result.valid is False
        assert "expired" in result.error.lower()
