"""ConnectionManager — CRUD + lifecycle + write-mode gating for connection profiles.

This is the live owner for T13.  The ConnectionManager:

* maintains an in-memory registry of ``ConnectionProfile`` objects,
* resolves credentials lazily via the ``KeychainStore`` (no plaintext caching),
* executes the connection test to move profiles through their lifecycle states,
* enforces ADR-002 write/provisioning gating (``enable_write`` / ``enable_provisioning``),
* detects connection failures and drives reconnection with the backoff from the
  connection-and-collection design.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from guardian.connections.keychain import KeychainStore
from guardian.connections.tester import ConnectionTester
from guardian.core_types.connection_models import (
    AuthMethod,
    ConnectionMode,
    ConnectionProfile,
    ConnectionStatus,
)
from guardian.core_types.exceptions import ProfileError

logger = logging.getLogger(__name__)

# --- callbacks -------------------------------------------------------------

ProfileSubscriber = Callable[[ConnectionProfile, str], None]
# (profile, event_name) -> None


# --- manager ---------------------------------------------------------------


class ConnectionManager:
    """Thread-safe registry and lifecycle manager for OpenSearch connection profiles.

    Usage
    -----
    ::

        mgr = ConnectionManager()
        profile = mgr.add(name="prod", opensearch_url="https://…", credential_ref="key")
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(mgr.test_connection(profile.id))
        profile = mgr.enable_write(profile.id)  # ADR-002 gating
    """

    # Exponential backoff caps from connection-and-collection §3.6
    _BACKOFF_INITIAL = 2
    _BACKOFF_MAX = 32
    _PERSISTENT_FAILURE_THRESHOLD = 10

    def __init__(
        self,
        store: KeychainStore | None = None,
        tester: ConnectionTester | None = None,
    ) -> None:
        self._store = store or KeychainStore()
        self._tester = tester or ConnectionTester(store=self._store)
        self._profiles: dict[str, ConnectionProfile] = {}
        self._subscribers: dict[str, list[ProfileSubscriber]] = {}
        self._lock = threading.RLock()
        # per-connection recovery state
        self._reconnect_attempts: dict[str, int] = {}
        self._reconnect_tasks: dict[str, asyncio.Task[None]] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _publish(self, profile: ConnectionProfile, event: str) -> None:
        for cb in self._subscribers.get(profile.id, []):
            try:
                cb(profile, event)
            except Exception:
                logger.exception("Subscriber callback failed for profile %s", profile.id)

    def _now(self) -> datetime:
        return datetime.now(UTC)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add(
        self,
        *,
        name: str,
        opensearch_url: str,
        auth_method: AuthMethod = AuthMethod.BASIC,
        credential_ref: str,
        tls_verify: bool = True,
        tls_ca_path: str | None = None,
        custom_ca_ref: str | None = None,
        metadata: dict[str, Any] | None = None,
        mode: ConnectionMode = ConnectionMode.READ_ONLY,
        proxy_url: str | None = None,
        proxy_auth_username: str | None = None,
        proxy_auth_password: str | None = None,
        proxy_ssl_verify: bool = True,
    ) -> ConnectionProfile:
        """Create and register a new connection profile.

        The profile starts in ``CREATED`` state with ``write_enabled=False``
        (ADR-002).  Credentials are assumed to already exist in the keychain
        under *credential_ref*.
        """
        from pydantic import HttpUrl, ValidationError

        try:
            url = HttpUrl(opensearch_url)
        except ValidationError as exc:
            raise ProfileError(f"Invalid OpenSearch URL: {exc}") from exc

        profile = ConnectionProfile(
            name=name,
            opensearch_url=url,
            auth_method=auth_method,
            credential_ref=credential_ref,
            tls_verify=tls_verify,
            tls_ca_path=tls_ca_path,
            custom_ca_ref=custom_ca_ref,
            metadata=metadata or {},
            mode=mode,
            proxy_url=proxy_url,
            proxy_auth_username=proxy_auth_username,
            proxy_auth_password=proxy_auth_password,
            proxy_ssl_verify=proxy_ssl_verify,
        )
        # (SQLite persistence for profiles is stubbed by the broader app store layer)
        with self._lock:
            self._profiles[profile.id] = profile
        logger.info("Created connection profile '%s' (%s).", name, profile.id)
        self._publish(profile, "profile_created")
        return profile

    def get(self, profile_id: str) -> ConnectionProfile:
        try:
            return self._profiles[profile_id]
        except KeyError:
            raise ProfileError(f"No connection profile with id '{profile_id}'.")

    def list_profiles(self) -> list[ConnectionProfile]:
        return list(self._profiles.values())

    def update(self, profile: ConnectionProfile) -> ConnectionProfile:
        profile.updated_at = self._now()
        # (SQLite persistence stub — the app store layer calls update() to sync)
        self._profiles[profile.id] = profile
        self._publish(profile, "profile_updated")
        return profile

    def delete(self, profile_id: str) -> None:
        profile = self.get(profile_id)
        profile.is_active = False
        profile.status = ConnectionStatus.DISCONNECTED
        self._cancel_recovery(profile_id)
        self.update(profile)
        with self._lock:
            self._profiles.pop(profile_id, None)
        logger.info("Soft-deleted connection profile '%s' (%s).", profile.name, profile_id)

    # ------------------------------------------------------------------
    # Connection test + lifecycle
    # ------------------------------------------------------------------

    async def test_connection(self, profile_id: str) -> ConnectionProfile:
        profile = self.get(profile_id)
        profile.status = ConnectionStatus.CONNECTING
        self.update(profile)

        try:
            result = await self._tester.test(profile)
        except Exception as exc:
            profile.status = ConnectionStatus.FAILED
            profile.last_test_result = None
            profile.last_test_at = self._now()
            self.update(profile)
            raise ProfileError(
                f"Connection test for '{profile.name}' failed: {exc}"
            ) from exc

        profile.last_test_result = result
        profile.last_test_at = result.tested_at
        if result.passed:
            profile.status = ConnectionStatus.ACTIVE
        else:
            profile.status = ConnectionStatus.ERROR if result.fatal_errors else ConnectionStatus.FAILED
        self.update(profile)
        logger.info(
            "Connection test for '%s' (%s): passed=%s.",
            profile.name,
            profile.id,
            result.passed,
        )
        return profile

    # ------------------------------------------------------------------
    # ADR-002 write / provisioning gating
    # ------------------------------------------------------------------

    def enable_write(self, profile_id: str) -> ConnectionProfile:
        """Enable write mode after an explicit confirmation flow.

        The caller must have performed the user-facing confirmation prompt
        *before calling this*.  This method flips the flag and re-runs the
        connection test to confirm ``write_permitted`` is true; it raises
        ``PermissionError`` (to match the canonical dummy exception here)
        if the cluster token lacks write privileges.
        """
        profile = self.get(profile_id)
        if profile.write_enabled:
            return profile  # idempotent

        loop = asyncio.get_event_loop()
        refreshed = loop.run_until_complete(self.test_connection(profile_id))
        if not (refreshed.last_test_result and refreshed.last_test_result.write_permitted):
            raise ProfileError(
                "Cannot enable write mode: connection does not have write permissions. "
                "Update the OpenSearch role and retry."
            )
        refreshed.enable_write()
        logger.info("Write mode enabled for profile '%s'.", refreshed.name)
        self._publish(refreshed, "write_enabled")
        return refreshed

    def enable_provisioning(self, profile_id: str) -> ConnectionProfile:
        """Enable provisioning mode (superset of write)."""
        profile = self.get(profile_id)
        if profile.provisioning_enabled:
            return profile
        self.enable_write(profile_id)  # checks write permissions
        profile = self.get(profile_id)  # re-fetch after update
        profile.enable_provisioning()
        self.update(profile)
        logger.info("Provisioning mode enabled for profile '%s'.", profile.name)
        self._publish(profile, "provisioning_enabled")
        return profile

    def disable_write(self, profile_id: str) -> ConnectionProfile:
        profile = self.get(profile_id)
        profile.disable_write()
        self.update(profile)
        logger.info("Write/provisioning disabled for profile '%s'.", profile.name)
        return profile

    def is_read_only(self, profile_id: str) -> bool:
        return self.get(profile_id).is_read_only()

    # ------------------------------------------------------------------
    # Reconnection backoff (synchronous wrapper around async workflow)
    # ------------------------------------------------------------------

    def _cancel_recovery(self, profile_id: str) -> None:
        task = self._reconnect_tasks.pop(profile_id, None)
        if task and not task.done():
            task.cancel()
        self._reconnect_attempts.pop(profile_id, None)

    async def _reconnect_loop(self, profile_id: str) -> None:
        backoff = self._BACKOFF_INITIAL
        attempts = 0
        try:
            while True:
                with self._lock:
                    profile = self._profiles.get(profile_id)
                if profile is None:
                    return
                try:
                    profile = await self.test_connection(profile_id)
                    logger.info("Reconnected to '%s' after %d attempts.", profile.name, attempts)
                    return
                except Exception:
                    attempts += 1
                    if attempts >= self._PERSISTENT_FAILURE_THRESHOLD:
                        profile.status = ConnectionStatus.FAILED
                        self.update(profile)
                        logger.error("Persistent failure for '%s'; stopped reconnecting.", profile.name)
                        return
                    logger.info(
                        "Reconnect attempt %d for '%s' failed; retrying in %ds.",
                        attempts,
                        profile.name,
                        backoff,
                    )
                    profile.status = ConnectionStatus.RECOVERING
                    self.update(profile)
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, self._BACKOFF_MAX)
        except asyncio.CancelledError:
            logger.debug("Reconnect loop cancelled for %s.", profile_id)

    def start_recovery(self, profile_id: str) -> None:
        self._cancel_recovery(profile_id)
        loop = asyncio.get_event_loop()
        task = loop.create_task(self._reconnect_loop(profile_id))
        self._reconnect_tasks[profile_id] = task
        logger.debug("Started reconnect loop for profile %s.", profile_id)

    # ------------------------------------------------------------------
    # Subscriptions
    # ------------------------------------------------------------------

    def subscribe(self, profile_id: str, callback: ProfileSubscriber) -> None:
        self._subscribers.setdefault(profile_id, []).append(callback)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def __contains__(self, profile_id: str) -> bool:
        return profile_id in self._profiles

    def __repr__(self) -> str:
        return f"<ConnectionManager profiles={len(self._profiles)}>"