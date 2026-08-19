"""Connection and profile Pydantic models for guardian.

These models are the single source of truth for all connection state
across the Guardian Core service. They live outside ``guardian/connections/``
so that other packages (cli, safety, audit, etc.) can import them without
creating a circular dependency on the connection-management layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


class AuthMethod(str, Enum):
    """Supported authentication adapters for OpenSearch."""

    BASIC = "basic"
    CLIENT_CERT = "client_cert"
    CUSTOM_CA = "custom_ca"
    API_KEY = "api_key"
    NONE = "none"  # development only; disabled by default in production


class ConnectionMode(str, Enum):
    """Operational mode for a connection profile."""

    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    PROVISIONING = "provisioning"


class ConnectionStatus(str, Enum):
    """Lifecycle state of an active connection."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ACTIVE = "active"
    DEGRADED = "degraded"
    ERROR = "error"
    FAILED = "failed"
    RECOVERING = "recovering"


# ---------------------------------------------------------------------------
# Credential payload (stored in OS keychain, never in this model / SQLite)
# ---------------------------------------------------------------------------


class BasicCredentials(BaseModel):
    """Username + password pair for Basic / API-Key auth.

    Stored in the OS keychain under the ``credential_ref`` key;
    this object is deserialised at connection time from the keychain.
    """

    model_config = {"frozen": True}

    username: str
    password: str  # pragma: allowlist secret

    def redacted(self) -> dict[str, str]:
        """Return a copy with the password masked for logging / display."""
        d = self.model_dump()
        d["password"] = "***"
        return d


class ClientCertCredentials(BaseModel):
    """mTLS client certificate + private key pair.

    Both the cert and key are stored in the OS keychain under
    ``credential_ref``.
    """

    model_config = {"frozen": True}

    cert_data: bytes  # PEM-encoded certificate (or path reference)
    key_data: bytes  # PEM-encoded private key (or path reference)

    def redacted(self) -> dict[str, Any]:
        d = self.model_dump()
        d["cert_data"] = f"<{len(self.cert_data)} bytes>"
        d["key_data"] = "<REDACTED>"
        return d


# discriminated union of credential types
Credentials = BasicCredentials | ClientCertCredentials


# ---------------------------------------------------------------------------
# Connection profile
# ---------------------------------------------------------------------------


class ConnectionProfile(BaseModel):
    """Persistent record for a single OpenSearch cluster connection.

    Secrets are stored in the OS keychain; this model only keeps a
    reference key (``credential_ref``).
    """

    model_config = {"use_enum_values": True}

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=255)
    opensearch_url: HttpUrl
    auth_method: AuthMethod = AuthMethod.BASIC

    # ----- keychain references (never the plaintext secrets) -----
    credential_ref: str = Field(..., description="keyring service:account key")
    custom_ca_ref: str | None = Field(
        default=None,
        description="keyring reference for a custom CA bundle (for custom_ca auth)",
    )

    # ----- TLS -----
    tls_verify: bool = True
    tls_ca_path: str | None = Field(
        default=None,
        description="Filesystem path to a custom CA bundle (alt to keychain)",
    )

    # ----- write / provisioning gating (ADR-002) -----
    write_enabled: bool = Field(default=False)
    provisioning_enabled: bool = Field(default=False)

    # ----- status -----
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    last_test_result: ConnectionTestResult | None = None
    last_test_at: datetime | None = None

    # ----- metadata -----
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ----- allowed safety level shortcut -----
    mode: ConnectionMode = Field(
        default=ConnectionMode.READ_ONLY,
        description="Operational mode inferred from write_enabled/provisioning_enabled",
    )

    @field_validator("mode", mode="after")
    def _sync_mode(cls, v: ConnectionMode, info: Any) -> ConnectionMode:
        """Derive mode from gating flags when not explicitly set."""
        # Pydantic v2: in field_validator mode="after", values is not passed.
        # We rely on defaults for the derived fields.
        return v

    def enable_write(self) -> None:
        """Enable write mode (does NOT grant OpenSearch permissions)."""
        self.write_enabled = True
        self.mode = ConnectionMode.READ_WRITE
        self.updated_at = datetime.utcnow()

    def enable_provisioning(self) -> None:
        """Enable provisioning mode (does NOT grant OpenSearch permissions)."""
        self.write_enabled = True
        self.provisioning_enabled = True
        self.mode = ConnectionMode.PROVISIONING
        self.updated_at = datetime.utcnow()

    def disable_write(self) -> None:
        """Revert to read-only mode."""
        self.write_enabled = False
        self.provisioning_enabled = False
        self.mode = ConnectionMode.READ_ONLY
        self.updated_at = datetime.utcnow()

    def is_read_only(self) -> bool:
        return self.mode == ConnectionMode.READ_ONLY


class PermissionCheckResult(BaseModel):
    """Outcome of a permission probe against an OpenSearch cluster."""

    read_permitted: bool
    write_permitted: bool
    user_roles: list[str] = Field(default_factory=list)
    security_enabled: bool = True


class TLSCheckResult(BaseModel):
    """Outcome of the TLS handshake / certificate validation."""

    valid: bool
    subject: str | None = None
    issuer: str | None = None
    not_valid_after: datetime | None = None
    not_valid_before: datetime | None = None
    fingerprint_sha256: str | None = None
    error: str | None = None


class ClusterIdentity(BaseModel):
    """Resolved cluster identity from ``GET /_cluster/health``."""

    cluster_name: str
    cluster_uuid: str
    version: str
    tagline: str | None = None


class ConnectionTestResult(BaseModel):
    """Composite result of the connection test (see §3.4 of the design doc)."""

    passed: bool
    identity: ClusterIdentity | None = None
    permissions: PermissionCheckResult | None = None
    tls: TLSCheckResult | None = None
    errors: list[str] = Field(default_factory=list)
    fatal_errors: list[str] = Field(default_factory=list)
    tested_at: datetime = Field(default_factory=datetime.utcnow)