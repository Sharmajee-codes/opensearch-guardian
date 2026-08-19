"""Connection and authentication exceptions."""


class GuardianError(Exception):
    """Base exception for OpenSearch Guardian."""


class ConnectionError(GuardianError):
    """Raised when a connection cannot be established or maintained."""


class AuthError(ConnectionError):
    """Raised when authentication fails."""


class TLSError(ConnectionError):
    """Raised when TLS verification or handshake fails."""


class ProfileError(GuardianError):
    """Raised when a connection profile is invalid or missing required fields."""


class KeychainError(GuardianError):
    """Raised when the OS keychain cannot be accessed or a secret is missing."""


class PermissionError(GuardianError):
    """Raised when an operation requires permissions not held by the connection."""


class WriteModeError(PermissionError):
    """Raised when a write operation is attempted on a read-only connection."""


class CollectionError(GuardianError):
    """Raised when the collector encounters an unrecoverable error."""


class SafetyError(GuardianError):
    """Raised when a safety policy violation is detected."""


class AuditError(GuardianError):
    """Raised when the audit log cannot be written."""