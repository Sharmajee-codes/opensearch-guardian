"""Unit tests for Core exceptions."""

import pytest
from guardian.core_types.exceptions import (
    GuardianError,
    ConnectionError,
    AuthError,
    TLSError,
    ProfileError,
    KeychainError,
    PermissionError,
    WriteModeError,
    CollectionError,
    SafetyError,
    AuditError,
)


class TestGuardianError:
    """Base exception tests."""

    def test_is_exception(self):
        assert issubclass(GuardianError, Exception)

    def test_can_be_raised(self):
        with pytest.raises(GuardianError) as exc_info:
            raise GuardianError("test error")
        assert "test error" in str(exc_info.value)


class TestConnectionError:
    """Connection error hierarchy tests."""

    def test_subclass_of_guardian_error(self):
        assert issubclass(ConnectionError, GuardianError)

    def test_auth_error_is_connection_error(self):
        assert issubclass(AuthError, ConnectionError)

    def test_tls_error_is_connection_error(self):
        assert issubclass(TLSError, ConnectionError)

    def test_auth_error_message(self):
        err = AuthError("Invalid credentials")
        assert "Invalid credentials" in str(err)

    def test_tls_error_message(self):
        err = TLSError("Certificate validation failed")
        assert "Certificate" in str(err)


class TestPermissionErrors:
    """Permission-related error tests."""

    def test_profile_error_is_guardian_error(self):
        assert issubclass(ProfileError, GuardianError)

    def test_keychain_error_is_guardian_error(self):
        assert issubclass(KeychainError, GuardianError)

    def test_permission_error_is_guardian_error(self):
        assert issubclass(PermissionError, GuardianError)

    def test_write_mode_error_is_permission_error(self):
        assert issubclass(WriteModeError, PermissionError)

    def test_write_mode_error_message(self):
        err = WriteModeError("Write access required for this operation")
        assert "Write access" in str(err)


class TestCollectionErrors:
    """Collection error tests."""

    def test_collection_error_is_guardian_error(self):
        assert issubclass(CollectionError, GuardianError)

    def test_collection_error_message(self):
        err = CollectionError("Failed to collect node stats")
        assert "node stats" in str(err)


class TestSafetyAuditErrors:
    """Safety and audit error tests."""

    def test_safety_error_is_guardian_error(self):
        assert issubclass(SafetyError, GuardianError)

    def test_audit_error_is_guardian_error(self):
        assert issubclass(AuditError, GuardianError)

    def test_safety_error_message(self):
        err = SafetyError("Operation blocked by policy")
        assert "blocked" in str(err)

    def test_audit_error_message(self):
        err = AuditError("Failed to write audit log")
        assert "audit log" in str(err)


class TestExceptionChaining:
    """Test exception inheritance chain."""

    def test_exception_hierarchy(self):
        """Verify the full exception hierarchy."""
        assert issubclass(AuthError, ConnectionError)
        assert issubclass(TLSError, ConnectionError)
        assert issubclass(ConnectionError, GuardianError)
        assert issubclass(WriteModeError, PermissionError)
        assert issubclass(PermissionError, GuardianError)
        assert issubclass(CollectionError, GuardianError)
        assert issubclass(SafetyError, GuardianError)
        assert issubclass(AuditError, GuardianError)
