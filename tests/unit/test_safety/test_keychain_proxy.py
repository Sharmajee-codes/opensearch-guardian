"""Unit tests for KeychainProxy."""

import pytest
from unittest.mock import MagicMock, patch
from guardian.safety.keychain_proxy import KeychainProxy, SecretNotFoundError, KeychainBackend


class TestKeychainProxy:
    """Tests for KeychainProxy."""

    def test_detect_backend_macos(self):
        with patch('platform.system', return_value='Darwin'):
            proxy = KeychainProxy()
            assert proxy._backend == KeychainBackend.MACOS_KEYCHAIN

    def test_detect_backend_linux(self):
        with patch('platform.system', return_value='Linux'):
            proxy = KeychainProxy()
            assert proxy._backend == KeychainBackend.LINUX_SECRET_SERVICE

    def test_detect_backend_windows(self):
        with patch('platform.system', return_value='Windows'):
            proxy = KeychainProxy()
            assert proxy._backend == KeychainBackend.WINDOWS_CREDENTIAL_VAULT

    def test_detect_backend_other(self):
        with patch('platform.system', return_value='FreeBSD'):
            proxy = KeychainProxy()
            assert proxy._backend == KeychainBackend.MEMORY_FALLBACK

    def test_get_secret_from_cache(self):
        proxy = KeychainProxy()
        proxy._cache = {"svc:acc": {"acc": "secret123"}}
        result = proxy.get_secret("svc", "acc")
        assert result == "secret123"

    def test_get_secret_from_injected(self):
        proxy = KeychainProxy()
        proxy._injected_secrets = {"svc": {"acc": "test-secret"}}
        result = proxy.get_secret("svc", "acc")
        assert result == "test-secret"

    def test_get_secret_missing_raises(self):
        proxy = KeychainProxy()
        with patch.object(proxy, '_fetch_secret', side_effect=SecretNotFoundError("svc", "acc")):
            with pytest.raises(SecretNotFoundError):
                proxy.get_secret("svc", "acc")

    def test_store_secret_memory_fallback(self):
        proxy = KeychainProxy()
        result = proxy.store_secret("svc", "acc", "secret")
        assert result is True
        assert proxy._injected_secrets["svc"]["acc"] == "secret"

    def test_inject_and_retrieve(self):
        proxy = KeychainProxy()
        proxy.inject_secret("svc", "acc", "secret456")
        result = proxy.get_secret("svc", "acc")
        assert result == "secret456"

    def test_clear_injected_secrets(self):
        proxy = KeychainProxy()
        proxy.inject_secret("svc", "acc", "secret")
        proxy.clear_injected_secrets()
        with pytest.raises(SecretNotFoundError):
            proxy.get_secret("svc", "acc")

    def test_clear_cache_specific(self):
        proxy = KeychainProxy()
        proxy._cache = {"svc:acc": {"acc": "secret"}}
        proxy.clear_cache("svc", "acc")
        assert "svc:acc" not in proxy._cache

    def test_clear_cache_service(self):
        proxy = KeychainProxy()
        proxy._cache = {"svc:acc1": {"acc1": "s1"}, "svc:acc2": {"acc2": "s2"}}
        proxy.clear_cache("svc", None)
        assert len(proxy._cache) == 0


class TestSecretNotFoundError:
    """Tests for SecretNotFoundError."""

    def test_str_representation(self):
        exc = SecretNotFoundError("svc", "acc")
        assert "svc" in str(exc)
        assert "acc" in str(exc)

    def test_exception_type(self):
        exc = SecretNotFoundError("svc", "acc")
        assert isinstance(exc, Exception)
