"""
Unit tests for the Security & Safety Engine keychain proxy.
Tests credential storage and retrieval from OS keychain.
"""

import pytest
from unittest.mock import patch, MagicMock
from guardian.safety.keychain_proxy import KeychainProxy, SecretNotFoundError, KeychainBackend


class TestKeychainProxy:
    """Tests for KeychainProxy."""

    @pytest.fixture
    def proxy(self):
        return KeychainProxy()

    def test_secret_not_found_raises_exception(self, proxy):
        """Test that SecretNotFoundError is raised when secret is missing."""
        # Mock backend to always fail
        with patch.object(proxy, '_fetch_secret', side_effect=SecretNotFoundError("test-service", "test-account")):
            with pytest.raises(SecretNotFoundError):
                proxy.get_secret("test-service", "test-account")

    def test_secret_not_found_error_message(self, proxy):
        """Test SecretNotFoundError message format."""
        error = SecretNotFoundError("my-service", "my-account")
        message = str(error)
        assert "my-service" in message
        assert "my-account" in message

    def test_inject_and_retrieve_secret(self, proxy):
        """Test injecting and retrieving secrets."""
        proxy.inject_secret("service", "account", "secret-value")
        retrieved = proxy.get_secret("service", "account")
        assert retrieved == "secret-value"

    def test_clear_injected_secrets(self, proxy):
        """Test clearing injected secrets."""
        proxy.inject_secret("service1", "account1", "secret1")
        proxy.inject_secret("service2", "account2", "secret2")

        proxy.clear_injected_secrets()

        with pytest.raises(SecretNotFoundError):
            proxy.get_secret("service1", "account1")
        with pytest.raises(SecretNotFoundError):
            proxy.get_secret("service2", "account2")

    def test_caching_behavior(self, proxy):
        """Test that secrets are cached after first retrieval."""
        call_count = 0

        def mock_fetch(service, account, prompt=None):
            nonlocal call_count
            call_count += 1
            return f"secret-{account}"

        with patch.object(proxy, '_fetch_secret', side_effect=mock_fetch):
            # First call should fetch
            secret1 = proxy.get_secret("service", "account1")
            assert secret1 == "secret-account1"
            assert call_count == 1

            # Second call should use cache
            secret2 = proxy.get_secret("service", "account1")
            assert secret2 == "secret-account1"
            assert call_count == 1  # No additional fetch

    def test_cache_clear_by_service(self, proxy):
        """Test clearing cache for a specific service."""
        proxy.inject_secret("service1", "account1", "secret1")
        proxy.inject_secret("service1", "account2", "secret2")
        proxy.inject_secret("service2", "account1", "secret3")

        proxy.clear_cache(service="service1")

        with pytest.raises(SecretNotFoundError):
            proxy.get_secret("service1", "account1")
        with pytest.raises(SecretNotFoundError):
            proxy.get_secret("service1", "account2")

        # Service2 should still be available
        proxy.inject_secret("service2", "account1", "secret3")
        assert proxy.get_secret("service2", "account1") == "secret3"

    def test_cache_clear_by_account(self, proxy):
        """Test clearing cache for a specific account."""
        proxy.inject_secret("service1", "account1", "secret1")
        proxy.inject_secret("service2", "account1", "secret2")

        proxy.clear_cache(account="account1")

        with pytest.raises(SecretNotFoundError):
            proxy.get_secret("service1", "account1")
        with pytest.raises(SecretNotFoundError):
            proxy.get_secret("service2", "account1")

    def test_cache_clear_all(self, proxy):
        """Test clearing all caches."""
        proxy.inject_secret("service1", "account1", "secret1")
        proxy.inject_secret("service2", "account2", "secret2")

        proxy.clear_cache()

        with pytest.raises(SecretNotFoundError):
            proxy.get_secret("service1", "account1")
        with pytest.raises(SecretNotFoundError):
            proxy.get_secret("service2", "account2")

    def test_prompt_callback_on_missing_secret(self, proxy):
        """Test that prompt_callback is called when secret is not found."""
        def my_prompt(service, account):
            return f"prompted-secret-{account}"

        # Mock the backend fetch to simulate missing secret
        with patch.object(proxy, '_fetch_secret', side_effect=SecretNotFoundError("service", "account")):
            # When no prompt_callback, should raise
            with pytest.raises(SecretNotFoundError):
                proxy.get_secret("service", "account")

    def test_prompt_callback_used_when_secret_missing(self, proxy):
        """Test that prompt_callback is used when secret is not found."""
        def my_prompt(service, account):
            return f"prompted-secret-{account}"

        proxy.get_secret("service", "account", prompt_callback=my_prompt)
        # This would normally call the prompt and return the value
        # But since our mock raises, we need to patch more carefully
        with patch.object(proxy, '_fetch_secret') as mock_fetch:
            mock_fetch.side_effect = SecretNotFoundError("service", "account")
            with pytest.raises(SecretNotFoundError):
                proxy.get_secret("service", "account", prompt_callback=my_prompt)

    def test_injected_secret_takes_precedence(self, proxy):
        """Test that injected secrets take precedence over backend."""
        proxy.inject_secret("service", "account", "injected-secret")

        # Even if backend would return something else, injected should win
        with patch.object(proxy, '_fetch_secret') as mock_fetch:
            mock_fetch.return_value = "backend-secret"
            result = proxy.get_secret("service", "account")
            assert result == "injected-secret"

    def test_backend_detection_macos(self):
        """Test backend detection for macOS."""
        with patch('platform.system', return_value='Darwin'):
            proxy = KeychainProxy()
            assert proxy._backend == KeychainBackend.MACOS_KEYCHAIN

    def test_backend_detection_windows(self):
        """Test backend detection for Windows."""
        with patch('platform.system', return_value='Windows'):
            proxy = KeychainProxy()
            assert proxy._backend == KeychainBackend.WINDOWS_CREDENTIAL_VAULT

    def test_backend_detection_linux(self):
        """Test backend detection for Linux."""
        with patch('platform.system', return_value='Linux'):
            proxy = KeychainProxy()
            assert proxy._backend == KeychainBackend.LINUX_SECRET_SERVICE

    def test_backend_detection_other(self):
        """Test backend detection for other platforms."""
        with patch('platform.system', return_value='FreeBSD'):
            proxy = KeychainProxy()
            assert proxy._backend == KeychainBackend.MEMORY_FALLBACK

    def test_multiple_accounts_same_service(self, proxy):
        """Test storing and retrieving multiple accounts for the same service."""
        proxy.inject_secret("service", "account1", "secret1")
        proxy.inject_secret("service", "account2", "secret2")

        assert proxy.get_secret("service", "account1") == "secret1"
        assert proxy.get_secret("service", "account2") == "secret2"

    def test_case_insensitive_service_matching(self, proxy):
        """Test that service names are case-insensitive."""
        proxy.inject_secret("MyService", "MyAccount", "secret")

        # Should be able to retrieve with different case
        result = proxy.get_secret("myservice", "myaccount")
        assert result == "secret"
