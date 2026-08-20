"""Connection-specific exception hierarchy.

These capture the fault modes documented in the security-safety-engine and
the connection-and-collection design doc.
"""

from guardian.core_types.exceptions import (
    AuthError,
    CollectionError,
    ConnectionError,
    KeychainError,
    TLSError,
    WriteModeError,
)

__all__ = [
    "AuthError",
    "CollectionError",
    "ConnectionError",
    "KeychainError",
    "TLSError",
    "WriteModeError",
]