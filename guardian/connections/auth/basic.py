"""Basic-auth adapter — the only adapter required for V1.

Wraps ``opensearch-py`` client initialisation using username + password
credentials retrieved from the OS keychain.  The secret values never
leave the connection layer; the rest of Guardian only ever sees a
configured ``OpenSearch`` client instance.
"""

from __future__ import annotations

import logging
from typing import Any

from guardian.connections.keychain import KeychainStore
from guardian.core_types.connection_models import (
    ConnectionMode,
    ConnectionProfile,
    ConnectionStatus,
)

logger = logging.getLogger(__name__)


class BasicCredentials:
    """Lightweight credential holder for Basic auth.

    Values come from the keychain and are held in memory only long
    enough to configure the ``opensearch-py`` client.
    """

    __slots__ = ("username", "password")

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password  # pragma: allowlist secret

    def client_kwargs(self, profile: ConnectionProfile) -> dict[str, Any]:
        """Return the kwargs for ``OpenSearch(..., **kwargs)``."""
        return {
            "hosts": [str(profile.opensearch_url)],
            "http_auth": (self.username, self.password),
            "use_ssl": profile.opensearch_url.scheme == "https",
            "verify_certs": profile.tls_verify,
        }


def resolve_basic_credentials(
    profile: ConnectionProfile,
    store: KeychainStore | None = None,
) -> BasicCredentials:
    """Fetch username + password from the keychain for *profile*.

    Raises
    ------
    KeychainError
        If the credential entry does not exist or cannot be read.
    """
    store = store or KeychainStore()
    creds = store.load_basic(profile.credential_ref)
    return BasicCredentials(username=creds.username, password=creds.password)


def build_opensearch_client(
    profile: ConnectionProfile,
    store: KeychainStore | None = None,
):
    """Create and return a configured ``opensearch-py`` ``OpenSearch`` client.

    The returned client is bound to the credentials in the keychain and
    respects ``write_enabled`` / ``provisioning_enabled`` by **not**
    granting additional OpenSearch permissions at this point; that
    enforcement happens through connection mode flags and audit logging.
    """
    try:
        from opensearchpy import OpenSearch
    except ImportError:
        raise RuntimeError(
            "opensearch-py is required for the connection management package. "
            "Install it with: pip install opensearch-py"
        )

    creds = resolve_basic_credentials(profile, store)
    kwargs = creds.client_kwargs(profile)
    client = OpenSearch(**kwargs)
    logger.debug(
        "Built OpenSearch client for profile '%s' (%s, %s).",
        profile.name,
        profile.id,
        profile.mode.value,
    )
    return client