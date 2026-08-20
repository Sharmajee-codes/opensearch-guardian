"""ClientCertAuthAdapter.

This V1.1 adapter fetches a client certificate + private key from the OS
keychain and configures ``opensearch-py`` for mTLS.  The ``credential_ref``
value of a profile must point to a ``ClientCertCredentials`` payload
stored by the ``KeychainStore``.

V1 provides BasicAuthAdapter as the default.  ClientCertAuthAdapter is a
V1.1 feature per the connection-and-collection design (Adapter table).
"""

from __future__ import annotations

import ssl
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from guardian.connections.auth.base import AuthAdapterProtocol

if TYPE_CHECKING:
    from guardian.core_types.connection_models import ConnectionProfile


class ClientCertAuthAdapter(AuthAdapterProtocol):
    """mTLS auth using a client certificate + private key pair from the keychain."""

    def __init__(self, cert_path: str | None = None, key_path: str | None = None) -> None:
        self._cert_path = cert_path
        self._key_path = key_path
        self._tmp_cert: Path | None = None
        self._tmp_key: Path | None = None

    def resolve_credentials(self, profile: ConnectionProfile) -> dict[str, Any]:
        from guardian.connections.keychain import KeychainStore

        store = KeychainStore()
        creds = store.load_client_cert(profile.credential_ref)

        # Write key material to temp files (the OpenSearch client expects paths).
        self._tmp_cert = Path(tempfile.gettempdir()) / f"guardian_cert_{profile.id}.pem"
        self._tmp_key = Path(tempfile.gettempdir()) / f"guardian_key_{profile.id}.pem"
        self._tmp_cert.write_bytes(creds.cert_data)
        self._tmp_key.write_bytes(creds.key_data)
        self._tmp_cert.chmod(0o600)
        self._tmp_key.chmod(0o600)
        return {"cert": str(self._tmp_cert), "key": str(self._tmp_key)}

    def build_client_options(self, *, use_ssl: bool, tls_verify: bool) -> dict[str, Any]:
        ctx = ssl.create_default_context()
        ctx.load_cert_chain(certfile=str(self._tmp_cert), keyfile=str(self._tmp_key))
        if not tls_verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        return {
            "use_ssl": use_ssl,
            "verify_certs": tls_verify,
            "ssl_context": ctx,
        }

    def validate(self, credentials: dict[str, Any]) -> bool:
        return "cert" in credentials and "key" in credentials

    def cleanup(self) -> None:
        if self._tmp_cert:
            try:
                self._tmp_cert.unlink(missing_ok=True)
            except Exception:
                pass
        if self._tmp_key:
            try:
                self._tmp_key.unlink(missing_ok=True)
            except Exception:
                pass

    def __del__(self) -> None:
        self.cleanup()