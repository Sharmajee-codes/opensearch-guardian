"""AuthAdapter protocol and shared helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from guardian.core_types.connection_models import ConnectionProfile


class AuthAdapterProtocol(ABC):
    """Protocol for authentication adapters.

    Adapters resolve credentials from the keychain and configure
    the OpenSearch client with the appropriate TLS/auth settings.
    """

    @abstractmethod
    def resolve_credentials(self, profile: ConnectionProfile) -> dict[str, Any]:
        """Fetch credentials from the keychain for the given profile."""

    @abstractmethod
    def build_client_options(
        self, *, use_ssl: bool, tls_verify: bool
    ) -> dict[str, Any]:
        """Build keyword arguments for the OpenSearch client."""

    @abstractmethod
    def validate(self, credentials: dict[str, Any]) -> bool:
        """Validate that credentials are complete and usable."""

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up any temporary resources (e.g. temp cert files)."""
