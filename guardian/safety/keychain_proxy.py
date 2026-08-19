"""
Keychain Proxy for the Security & Safety Engine.
Implements lazy, thread-safe fetch of credentials from OS keychain.
Supports macOS Keychain, Windows Credential Vault, and Linux Secret Service.
"""

import os
import platform
import threading
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum


class KeychainBackend(Enum):
    """Supported keychain backends."""
    MACOS_KEYCHAIN = "macos_keychain"
    WINDOWS_CREDENTIAL_VAULT = "windows_credential_vault"
    LINUX_SECRET_SERVICE = "linux_secret_service"
    MEMORY_FALLBACK = "memory_fallback"


@dataclass
class SecretNotFoundError(Exception):
    """Exception raised when a secret is not found in the keychain."""
    service: str
    account: str

    def __str__(self):
        return f"Secret not found: service={self.service}, account={self.account}"


class KeychainProxy:
    """
    Lazy, thread-safe keychain proxy that fetches credentials from
    the operating system credential store.
    """

    def __init__(self):
        self._backend = self._detect_backend()
        self._lock = threading.RLock()
        self._cache: Dict[str, Dict[str, str]] = {}  # service -> {account: secret}
        self._injected_secrets: Dict[str, Dict[str, str]] = {}  # For testing

    def _detect_backend(self) -> KeychainBackend:
        """Detect the appropriate keychain backend for the OS."""
        system = platform.system().lower()

        if system == "darwin":
            return KeychainBackend.MACOS_KEYCHAIN
        elif system == "windows":
            return KeychainBackend.WINDOWS_CREDENTIAL_VAULT
        elif system.startswith("linux"):
            return KeychainBackend.LINUX_SECRET_SERVICE
        else:
            # Fallback for other systems
            return KeychainBackend.MEMORY_FALLBACK

    def get_secret(
        self,
        service: str,
        account: str,
        prompt_callback=None
    ) -> str:
        """
        Retrieve a secret from the keychain.

        Args:
            service: Service name (e.g., "opensearch-guardian")
            account: Account name (e.g., "cluster-primary")
            prompt_callback: Optional callback to prompt user for secret

        Returns:
            Secret value

        Raises:
            SecretNotFoundError: If secret is not found
        """
        cache_key = f"{service}:{account}"

        # Check cache first
        with self._lock:
            if cache_key in self._cache and self._cache[cache_key].get(account):
                return self._cache[cache_key][account]

            # Check injected secrets (for testing)
            if service in self._injected_secrets and account in self._injected_secrets[service]:
                self._cache[cache_key] = {account: self._injected_secrets[service][account]}
                return self._injected_secrets[service][account]

        # Fetch from keychain backend
        secret = self._fetch_secret(service, account, prompt_callback)

        # Cache the result
        with self._lock:
            if cache_key not in self._cache:
                self._cache[cache_key] = {}
            self._cache[cache_key][account] = secret

        return secret

    def _fetch_secret(
        self,
        service: str,
        account: str,
        prompt_callback=None
    ) -> str:
        """Fetch secret from the appropriate backend."""
        if self._backend == KeychainBackend.MACOS_KEYCHAIN:
            return self._fetch_macos(service, account, prompt_callback)
        elif self._backend == KeychainBackend.WINDOWS_CREDENTIAL_VAULT:
            return self._fetch_windows(service, account, prompt_callback)
        elif self._backend == KeychainBackend.LINUX_SECRET_SERVICE:
            return self._fetch_linux(service, account, prompt_callback)
        elif self._backend == KeychainBackend.MEMORY_FALLBACK:
            return self._fetch_memory(service, account, prompt_callback)
        else:
            raise SecretNotFoundError(service, account)

    def _fetch_macos(
        self,
        service: str,
        account: str,
        prompt_callback=None
    ) -> str:
        """Fetch secret from macOS Keychain using security command."""
        import subprocess

        try:
            result = subprocess.run(
                [
                    "security",
                    "find-generic-password",
                    "-s", service,
                    "-a", account,
                    "-w"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            # If command fails, check for environment variable
            env_var = f"{service.upper()}_{account.upper()}_SECRET"
            secret = os.environ.get(env_var)
            if secret:
                return secret

            # Fall back to prompt callback
            if prompt_callback:
                return prompt_callback(service, account)

            raise SecretNotFoundError(service, account)

    def _fetch_windows(
        self,
        service: str,
        account: str,
        prompt_callback=None
    ) -> str:
        """Fetch secret from Windows Credential Vault."""
        try:
            import subprocess
            result = subprocess.run(
                ["cmdkey", "/list"],
                capture_output=True,
                text=True,
                check=True
            )
            # Parse output for the credential
            for line in result.stdout.split("\n"):
                if service.lower() in line.lower() and account.lower() in line.lower():
                    # Extract the credential (simplified)
                    parts = line.split("\\")
                    if len(parts) > 1:
                        return parts[-1].strip()
        except subprocess.CalledProcessError:
            pass

        # Fallback to environment variable
        env_var = f"{service.upper()}_{account.upper()}_SECRET"
        secret = os.environ.get(env_var)
        if secret:
            return secret

        # Fall back to prompt callback
        if prompt_callback:
            return prompt_callback(service, account)

        raise SecretNotFoundError(service, account)

    def _fetch_linux(
        self,
        service: str,
        account: str,
        prompt_callback=None
    ) -> str:
        """Fetch secret from Linux Secret Service (GNOME Keyring/KWallet)."""
        try:
            import subprocess
            result = subprocess.run(
                [
                    "secret-tool",
                    "lookup",
                    "service", service,
                    "account", account
                ],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            pass

        # Fallback to environment variable
        env_var = f"{service.upper()}_{account.upper()}_SECRET"
        secret = os.environ.get(env_var)
        if secret:
            return secret

        # Fall back to prompt callback
        if prompt_callback:
            return prompt_callback(service, account)

        raise SecretNotFoundError(service, account)

    def _fetch_memory(
        self,
        service: str,
        account: str,
        prompt_callback=None
    ) -> str:
        """Fallback secret retrieval from memory/environment."""
        # Check environment variable
        env_var = f"{service.upper()}_{account.upper()}_SECRET"
        secret = os.environ.get(env_var)
        if secret:
            return secret

        # Fall back to prompt callback
        if prompt_callback:
            return prompt_callback(service, account)

        raise SecretNotFoundError(service, account)

    def store_secret(
        self,
        service: str,
        account: str,
        secret: str,
        prompt_callback=None
    ) -> bool:
        """
        Store a secret in the keychain.

        Args:
            service: Service name
            account: Account name
            secret: Secret value to store
            prompt_callback: Optional callback to handle storage prompts

        Returns:
            True if stored successfully, False otherwise
        """
        if self._backend == KeychainBackend.MACOS_KEYCHAIN:
            return self._store_macos(service, account, secret, prompt_callback)
        elif self._backend == KeychainBackend.WINDOWS_CREDENTIAL_VAULT:
            return self._store_windows(service, account, secret, prompt_callback)
        elif self._backend == KeychainBackend.LINUX_SECRET_SERVICE:
            return self._store_linux(service, account, secret, prompt_callback)
        else:
            # For memory fallback, store in injected secrets
            if service not in self._injected_secrets:
                self._injected_secrets[service] = {}
            self._injected_secrets[service][account] = secret
            return True

    def _store_macos(
        self,
        service: str,
        account: str,
        secret: str,
        prompt_callback=None
    ) -> bool:
        """Store secret in macOS Keychain."""
        import subprocess

        try:
            subprocess.run(
                [
                    "security",
                    "add-generic-password",
                    "-s", service,
                    "-a", account,
                    "-w", secret,
                    "-U"  # Update if exists
                ],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _store_windows(
        self,
        service: str,
        account: str,
        secret: str,
        prompt_callback=None
    ) -> bool:
        """Store secret in Windows Credential Vault."""
        try:
            import subprocess
            result = subprocess.run(
                ["cmdkey", "/add", service, "/user", account, "/pass", secret],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _store_linux(
        self,
        service: str,
        account: str,
        secret: str,
        prompt_callback=None
    ) -> bool:
        """Store secret in Linux Secret Service."""
        try:
            import subprocess
            proc = subprocess.run(
                ["secret-tool", "store", "--label", "Guardian Secret"],
                input=f"{secret}\n",
                capture_output=True,
                text=True,
                check=True
            )
            # Store via secret-tool
            subprocess.run(
                [
                    "secret-tool",
                    "store",
                    "service", service,
                    "account", account
                ],
                input=secret,
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def clear_cache(self, service: Optional[str] = None, account: Optional[str] = None):
        """
        Clear cached secrets.

        Args:
            service: Clear secrets for specific service (or None for all)
            account: Clear secrets for specific account (or None for all)
        """
        with self._lock:
            if service and account:
                cache_key = f"{service}:{account}"
                if cache_key in self._cache:
                    del self._cache[cache_key]
            elif service:
                keys_to_remove = [
                    k for k in self._cache.keys() if k.startswith(f"{service}:")
                ]
                for key in keys_to_remove:
                    del self._cache[key]
            else:
                self._cache.clear()

    def inject_secret(self, service: str, account: str, secret: str):
        """
        Inject a secret for testing purposes.

        Args:
            service: Service name
            account: Account name
            secret: Secret value
        """
        if service not in self._injected_secrets:
            self._injected_secrets[service] = {}
        self._injected_secrets[service][account] = secret

    def clear_injected_secrets(self):
        """Clear all injected test secrets."""
        self._injected_secrets.clear()
        self._cache.clear()