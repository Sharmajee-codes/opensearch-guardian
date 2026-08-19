"""Connection test — the five-dimension health check (see connection-and-collection.md §3.4)."""

from __future__ import annotations

import logging
import ssl
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import httpx

from guardian.core_types.connection_models import (
    AuthMethod,
    ClientCertCredentials,
    ConnectionProfile,
    ConnectionStatus,
    ConnectionTestResult,
)
from guardian.core_types.exceptions import AuthError, KeychainError, TLSError

if TYPE_CHECKING:
    from guardian.connections.keychain import KeychainStore

logger = logging.getLogger(__name__)


_ERR_MSG = "Failed to connect to {url}: {error}"


# ---------------------------------------------------------------------------
# TLS helpers
# ---------------------------------------------------------------------------


def _build_tls_context(profile: ConnectionProfile) -> ssl.SSLContext | bool:
    """Return an SSLContext matching *profile*'s TLS settings."""
    if profile.opensearch_url.scheme != "https":
        return False  # HTTP — no TLS
    ctx = ssl.create_default_context()
    if profile.tls_ca_path:
        try:
            ctx.load_verify_locations(profile.tls_ca_path)
        except ssl.SSLError as exc:
            raise TLSError(f"Failed to load CA bundle at {profile.tls_ca_path}: {exc}") from exc
    if not profile.tls_verify:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _inspect_cert(host: str, port: int, tls_ctx: ssl.SSLContext | bool) -> dict:
    """Open a TLS socket and return certificate fields (or an error dict)."""
    import socket
    from datetime import datetime

    result: dict = {}
    try:
        ctx = tls_ctx if isinstance(tls_ctx, ssl.SSLContext) else ssl.create_default_context()
        with socket.create_connection((host, port), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls_sock:
                cert = tls_sock.getpeercert()
                subject = _dict_from_x509_name(cert.get("subject", ()))
                issuer = _dict_from_x509_name(cert.get("issuer", ()))
                not_after = cert.get("notAfter", "")
                result.update(
                    subject=subject,
                    issuer=issuer,
                    not_valid_after=_parse_cert_date(not_after),
                    fingerprint_sha256="",  # requires hashlib
                )
    except Exception as exc:
        result["error"] = str(exc)
    return result


def _dict_from_x509_name(name_seq: tuple) -> dict[str, str]:
    out: dict[str, str] = {}
    for rdn in name_seq:
        for attr in rdn:
            out[attr[0]] = attr[1]
    return out


def _parse_cert_date(raw: str):
    from datetime import datetime

    for fmt in ("%b %d %H:%M:%S %Y %Z", "%b  %d %H:%M:%S %Y %Z"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------


class ConnectionTester:
    """Run the five-dimension connection test against an OpenSearch cluster.

    Parameters
    ----------
    store:
        KeychainStore for fetching credentials at test time.
    """

    def __init__(self, store: KeychainStore | None = None) -> None:
        self._store = store

    async def test(self, profile: ConnectionProfile) -> ConnectionTestResult:
        """Run all five test dimensions and return the composite result."""
        url = str(profile.opensearch_url)
        errors: list[str] = []
        fatal_errors: list[str] = []
        identity = None
        permissions = None
        tls_result = None
        passed = False

        auth = profile.auth_method

        # ---- 1. TLS ----
        if profile.opensearch_url.scheme == "https":
            try:
                raw_tls = _build_tls_context(profile)
                if isinstance(raw_tls, ssl.SSLContext):
                    tls_raw = _inspect_cert(
                        profile.opensearch_url.host, profile.opensearch_url.port or 443, raw_tls
                    )
                    from guardian.core_types.connection_models import TLSCheckResult

                    expiry = tls_raw.get("not_valid_after")
                    tls_valid = "error" not in tls_raw
                    if tls_valid and expiry and expiry < datetime.now(timezone.utc):
                        tls_valid = False
                        tls_raw["error"] = "Certificate has expired"
                    tls_result = TLSCheckResult(
                        valid=tls_valid,
                        subject=tls_raw.get("subject"),
                        issuer=tls_raw.get("issuer"),
                        not_valid_after=expiry,
                        error=tls_raw.get("error"),
                    )
                    if not tls_valid:
                        fatal_errors.append(f"TLS validation failed: {tls_result.error}")
            except TLSError as exc:
                fatal_errors.append(f"TLS error: {exc}")
                tls_result = None
        else:
            tls_result = None  # HTTP, no TLS to check

        # ---- 2-5. HTTP probes via httpx ----
        try:
            from opensearchpy import OpenSearch

            client_kwargs: dict = {
                "hosts": [url],
                "use_ssl": profile.opensearch_url.scheme == "https",
                "verify_certs": profile.tls_verify and auth != AuthMethod.NONE,
            }
            if auth == AuthMethod.BASIC and profile.credential_ref:
                store = self._store or _default_store()
                try:
                    creds = store.load_basic(profile.credential_ref)
                except KeychainError:
                    fatal_errors.append("Credentials not found in keychain for this profile.")
                    creds = None
                if creds:
                    client_kwargs["http_auth"] = (creds.username, creds.password)

            client = OpenSearch(**client_kwargs)
            # 2. Version + identity
            try:
                info = client.info()
                health = client.cluster.health()
                from guardian.core_types.connection_models import ClusterIdentity

                identity = ClusterIdentity(
                    cluster_name=health.get("cluster_name", ""),
                    cluster_uuid=health.get("cluster_uuid", ""),
                    version=info.get("version", {}).get("number", "unknown"),
                    tagline=info.get("tagline"),
                )
            except Exception as exc:
                fatal_errors.append(f"Failed to reach OpenSearch / gather identity: {exc}")

            # 3. Permissions
            read_permitted = False
            write_permitted = False
            user_roles: list[str] = []
            security_enabled = True
            try:
                nodes_stats = client.nodes.stats()
                read_permitted = bool(nodes_stats)
                # Detect security info endpoint
                try:
                    auth_info = client.security.get_auth_info()
                    user_roles = list(auth_info.get("roles", []))
                    security_enabled = True
                except Exception:
                    # No security plugin or endpoint unavailable
                    security_enabled = False
                # Test write via cluster put settings (no-op)
                try:
                    client.cluster.put_settings(body={"transient": {"action.destructive_requires_name": True}})
                    write_permitted = True
                except Exception:
                    write_permitted = False
            except Exception as exc:
                errors.append(f"Permission probe error: {exc}")

            from guardian.core_types.connection_models import PermissionCheckResult

            permissions = PermissionCheckResult(
                read_permitted=read_permitted,
                write_permitted=write_permitted,
                user_roles=user_roles,
                security_enabled=security_enabled,
            )

            passed = identity is not None and read_permitted and (tls_result is None or tls_result.valid)
            if not passed and not fatal_errors:
                fatal_errors.append("Connection test did not pass all checks — see errors list.")

        except Exception as exc:
            fatal_errors.append(f"Unexpected error during connection test: {exc}")

        return ConnectionTestResult(
            passed=passed,
            identity=identity,
            permissions=permissions,
            tls=tls_result,
            errors=errors,
            fatal_errors=fatal_errors,
            tested_at=datetime.now(timezone.utc),
        )


def _default_store() -> "KeychainStore":
    from guardian.connections.keychain import KeychainStore

    return KeychainStore()