"""OS keychain integration via the ``keyring`` library.

Secrets (passwords, client certs, private keys, CA bundles) are stored in
the OS-native credential store:

* macOS — Keychain
* Windows — Credential Manager
* Linux — Secret Service (``python-keyring`` + ``secretstorage``)

``keyring`` raises ``keyring.errors.KeyringError`` on failures; we wrap
those into ``KeychainError``.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TypeVar

from guardian.core_types.connection_models import ClientCertCredentials
from guardian.core_types.exceptions import KeychainError

logger = logging.getLogger(__name__)
T = TypeVar("T")


class KeychainProxy:
    """Thread-safe, lazy proxy to the OS credential store.

    Secrets are **never** cached beyond the call that fetched them.
    Callers receive a value and are responsible for zeroing it when done.
    In practice we don't zero strings (Python GC-managed), but the secret
    must not be stored in a long-lived object or written to disk.

    Parameters
    ----------
    service_name:
        The keyring *service* prefix (defaults to ``opensearch-guardian``).
        The full keychain key is ``service_name:account``.
    """

    def __init__(self, service_name: str = "opensearch-guardian") -> None:
        self._service_name = service_name
        self._keyring: Callable | None = None
        self._load_error: str | None = None

    # ------------------------------------------------------------------
    # Internal keyring accessor — lazy import so tests don't need it
    # ------------------------------------------------------------------

    def _get_keyring(self) -> Callable:
        if self._keyring is None:
            if self._load_error:
                # We've already failed to import — don't keep trying.
                raise KeychainError(self._load_error)
            try:
                import keyring

                self._keyring = keyring
            except ImportError as exc:
                self._load_error = (
                    "python-keyring is not installed. "
                    "Install it with: pip install keyring"
                )
                raise KeychainError(self._load_error) from exc
        return self._keyring

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def set(self, account: str, secret: str) -> None:
        """Store *secret* under *account* in the OS keychain."""
        kr = self._get_keyring()
        try:
            kr.set_password(self._service_name, account, secret)
        except Exception as exc:
            logger.error("Keychain store failed for %s: %s", account, exc)
            raise KeychainError(f"Failed to store secret for '{account}': {exc}") from exc
        logger.debug("Stored secret for %s in keychain.", account)

    def get(self, account: str) -> str | None:
        """Retrieve the secret for *account*, or ``None`` if not found."""
        kr = self._get_keyring()
        try:
            secret = kr.get_password(self._service_name, account)
        except Exception as exc:
            logger.error("Keychain retrieval failed for %s: %s", account, exc)
            raise KeychainError(
                f"Failed to retrieve secret for '{account}': {exc}"
            ) from exc
        if secret is not None:
            logger.debug("Retrieved secret for %s from keychain.", account)
        else:
            logger.warning("No secret found for %s in keychain.", account)
        return secret

    def delete(self, account: str) -> None:
        """Delete the secret for *account*."""
        kr = self._get_keyring()
        try:
            kr.delete_password(self._service_name, account)
        except Exception as exc:
            logger.error("Keychain delete failed for %s: %s", account, exc)
            raise KeychainError(f"Failed to delete secret for '{account}': {exc}") from exc
        logger.debug("Deleted secret for %s from keychain.", account)

    # ------------------------------------------------------------------
    # Convenience: return the full keychain key for an account
    # ------------------------------------------------------------------

    def full_key(self, account: str) -> str:
        return f"{self._service_name}:{account}"


class PlaintextVault:
    """Fallback in-memory vault for development/testing ONLY.

    Uses plaintext strings in ``dict[str, str]`` — the keychain is
    unavailable in the test runner or in environments without a
    credential service.

    **DO NOT use in production.**
    """

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def set(self, account: str, secret: str) -> None:
        self._store[account] = secret

    def get(self, account: str) -> str | None:
        return self._store.get(account)

    def delete(self, account: str) -> None:
        self._store.pop(account, None)


# ---------------------------------------------------------------------------
# Keychain-backed secret store (T23/T24 integration target)
# ---------------------------------------------------------------------------


class KeychainStore:
    """High-level secret manager used by ConnectionProfile and auth adapters.

    Wraps ``KeychainProxy`` with structured write / read helpers that
    encode / decode typed payloads (``BasicCredentials``,
    ``ClientCertCredentials``).  Credentials are serialised as JSON
    (basic auth) or base64 (certs) before being written to the keychain;
    raw secrets never hit SQLite or logs.
    """

    def __init__(
        self,
        proxy: KeychainProxy | PlaintextVault | None = None,
        service_name: str = "opensearch-guardian",
    ) -> None:
        self._proxy = proxy or KeychainProxy(service_name)

    # ----- basic credentials -----

    def save_basic(self, account: str, username: str, password: str) -> None:
        from guardian.core_types.connection_models import BasicCredentials

        creds = BasicCredentials(username=username, password=password)

        self._proxy.set(account, creds.model_dump_json())

    def load_basic(self, account: str) -> BasicCredentials:

        from guardian.core_types.connection_models import BasicCredentials

        raw = self._proxy.get(account)
        if raw is None:
            raise KeychainError(
                f"No credentials found for account '{account}'. "
                "Store credentials first with save_basic()."
            )
        return BasicCredentials.model_validate_json(raw)

    # ----- client cert credentials -----

    def save_client_cert(self, account: str, cert_data: bytes, key_data: bytes) -> None:
        from guardian.core_types.connection_models import ClientCertCredentials

        creds = ClientCertCredentials(cert_data=cert_data, key_data=key_data)
        import base64

        encoded = base64.b64encode(creds.model_dump_json().encode()).decode()
        self._proxy.set(account, encoded)

    def load_client_cert(self, account: str) -> ClientCertCredentials:
        import base64

        from guardian.core_types.connection_models import ClientCertCredentials

        raw = self._proxy.get(account)
        if raw is None:
            raise KeychainError(f"No client-cert credentials for account '{account}'.")
        decoded = base64.b64decode(raw).decode()
        return ClientCertCredentials.model_validate_json(decoded)

    # ----- generic -----

    def delete(self, account: str) -> None:
        """Remove credentials for *account* from the keychain."""
        self._proxy.delete(account)

    def exists(self, account: str) -> bool:
        """Return ``True`` if credentials exist for *account*."""
        return self._proxy.get(account) is not None