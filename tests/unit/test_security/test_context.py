"""Tests for SecurityContext."""

import pytest

from guardian.security.context import (
    SecurityContext,
    UserIdentity,
    TenantContext,
    get_current_user,
    get_current_tenant,
    get_user_roles,
    require_permission,
)
from guardian.security.permissions import ClusterReadPermission, ClusterMonitorPermission, ClusterManagePermission


class TestSecurityContext:
    """Tests for SecurityContext."""

    def setup_method(self):
        """Clear context before each test."""
        SecurityContext.clear_context()

    def test_get_user_no_context(self):
        assert SecurityContext.get_user() is None

    def test_get_tenant_no_context(self):
        assert SecurityContext.get_tenant() is None

    def test_set_and_get_user(self):
        user = UserIdentity(username="admin", backend_roles=["guardian_monitor"])
        tenant = TenantContext(tenant_name="global", is_global_tenant=True, is_private_tenant=False)
        SecurityContext.set_context(user, tenant)
        assert SecurityContext.get_user() == user

    def test_set_and_get_tenant(self):
        user = UserIdentity(username="admin", backend_roles=["guardian_manager"])
        tenant = TenantContext(tenant_name="private", is_global_tenant=False, is_private_tenant=True, shared_tenant="shared1")
        SecurityContext.set_context(user, tenant)
        assert SecurityContext.get_tenant() == tenant

    def test_clear_context(self):
        user = UserIdentity(username="admin", backend_roles=["guardian_monitor"])
        tenant = TenantContext(tenant_name="global", is_global_tenant=True, is_private_tenant=False)
        SecurityContext.set_context(user, tenant)
        SecurityContext.clear_context()
        assert SecurityContext.get_user() is None
        assert SecurityContext.get_tenant() is None

    def test_has_permission_cluster_read(self):
        user = UserIdentity(username="admin", backend_roles=["guardian_monitor"])
        tenant = TenantContext(tenant_name="global", is_global_tenant=True, is_private_tenant=False)
        SecurityContext.set_context(user, tenant)
        assert SecurityContext.has_permission(ClusterReadPermission) is True

    def test_has_permission_no_roles(self):
        user = UserIdentity(username="admin", backend_roles=[])
        tenant = TenantContext(tenant_name="global", is_global_tenant=True, is_private_tenant=False)
        SecurityContext.set_context(user, tenant)
        assert SecurityContext.has_permission(ClusterReadPermission) is False

    def test_has_permission_unknown_class(self):
        user = UserIdentity(username="admin", backend_roles=["guardian_monitor"])
        tenant = TenantContext(tenant_name="global", is_global_tenant=True, is_private_tenant=False)
        SecurityContext.set_context(user, tenant)

        class UnknownPermission:
            __name__ = "UnknownPermission"

        assert SecurityContext.has_permission(UnknownPermission) is False

    def test_has_permission_no_user(self):
        assert SecurityContext.has_permission(ClusterReadPermission) is False


class TestGetCurrentUser:
    """Tests for get_current_user."""

    def setup_method(self):
        SecurityContext.clear_context()

    def test_returns_user(self):
        user = UserIdentity(username="admin", backend_roles=["guardian_manager"])
        tenant = TenantContext(tenant_name="global", is_global_tenant=True, is_private_tenant=False)
        SecurityContext.set_context(user, tenant)
        assert get_current_user() == user

    def test_returns_none(self):
        assert get_current_user() is None


class TestGetCurrentTenant:
    """Tests for get_current_tenant."""

    def setup_method(self):
        SecurityContext.clear_context()

    def test_returns_tenant(self):
        tenant = TenantContext(tenant_name="private", is_global_tenant=False, is_private_tenant=True)
        user = UserIdentity(username="admin", backend_roles=["guardian_monitor"])
        SecurityContext.set_context(user, tenant)
        assert get_current_tenant() == tenant

    def test_returns_none(self):
        assert get_current_tenant() is None


class TestGetUserRoles:
    """Tests for get_user_roles."""

    def setup_method(self):
        SecurityContext.clear_context()

    def test_returns_roles(self):
        user = UserIdentity(username="admin", backend_roles=["guardian_monitor", "guardian_manager"])
        tenant = TenantContext(tenant_name="global", is_global_tenant=True, is_private_tenant=False)
        SecurityContext.set_context(user, tenant)
        assert get_user_roles() == ["guardian_monitor", "guardian_manager"]

    def test_returns_empty(self):
        user = UserIdentity(username="admin", backend_roles=[])
        tenant = TenantContext(tenant_name="global", is_global_tenant=True, is_private_tenant=False)
        SecurityContext.set_context(user, tenant)
        assert get_user_roles() == []

    def test_returns_empty_when_no_user(self):
        assert get_user_roles() == []


class TestRequirePermission:
    """Tests for require_permission."""

    def setup_method(self):
        SecurityContext.clear_context()

    def test_require_permission_granted(self):
        user = UserIdentity(username="admin", backend_roles=["guardian_manager"])
        tenant = TenantContext(tenant_name="global", is_global_tenant=True, is_private_tenant=False)
        SecurityContext.set_context(user, tenant)
        # Should not raise
        require_permission(ClusterManagePermission)

    def test_require_permission_denied(self):
        user = UserIdentity(username="admin", backend_roles=["guardian_monitor"])
        tenant = TenantContext(tenant_name="global", is_global_tenant=True, is_private_tenant=False)
        SecurityContext.set_context(user, tenant)
        with pytest.raises(PermissionError):
            require_permission(ClusterManagePermission)

    def test_require_permission_no_user(self):
        with pytest.raises(PermissionError):
            require_permission(ClusterReadPermission)
