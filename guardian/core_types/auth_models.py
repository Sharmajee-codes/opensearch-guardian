"""Auth credential dataclasses used at connection-time only.

These objects are deserialised from the OS keychain and are never
persisted to disk or transmitted over IPC.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BasicCredentials:
    """Username + password pair for Basic / API-Key auth.

    Stored in the OS keychain under the ``credential_ref`` key;
    this object is deserialised at connection time from the keychain.
    """

    username: str
    password: str  # pragma: allowlist secret

    def redacted(self) -> dict[str, str]:
        """Return a copy with the password masked for logging / display."""
        return {"username": self.username, "password": "***"}


@dataclass(frozen=True)
class ClientCertCredentials:
    """mTLS client certificate + private key pair.

    Both the cert and key are stored in the OS keychain under
    ``credential_ref``.
    """

    cert_data: bytes  # PEM-encoded certificate (or path reference)
    key_data: bytes  # PEM-encoded private key (or path reference)

    def redacted(self) -> dict[str, Any]:
        return {
            "cert_data": f"<{len(self.cert_data)} bytes>",
            "key_data": "<REDACTED>",
        }


# discriminated union of credential types
Credentials = BasicCredentials | ClientCertCredentials
