"""Security Context - Access to OpenSearch Security plugin context.

Provides access to current authenticated user, tenant, and roles
from OpenSearch Security plugin.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import local
from typing import Any

_thread_local = local()


@dataclass
class UserIdentity:
    """Authenticated user identity from OpenSearch Security."""
    username: str
    backend_roles: list[str]
    custom_attribute: dict[str, Any] | None = None


@dataclass
class TenantContext:
    """Current tenant context from OpenSearch Security."""
    tenant_name: str
    is_global_tenant: bool
    is_private_tenant: bool
    shared_tenant: str | None = None


class SecurityContext:
    """
    Thread-local security context for OpenSearch Security plugin integration.

    In OpenSearch plugin environment, this wraps OpenSearch's SecurityContext
    to provide easy access to authenticated user information.
    """

    @staticmethod
    def set_context(user: UserIdentity, tenant: TenantContext) -> None:
        """Set the current thread's security context."""
        _thread_local.user = user
        _thread_local.tenant = tenant

    @staticmethod
    def clear_context() -> None:
        """Clear the current thread's security context."""
        if hasattr(_thread_local, 'user'):
            del _thread_local.user
        if hasattr(_thread_local, 'tenant'):
            del _thread_local.tenant

    @staticmethod
    def get_user() -> UserIdentity | None:
        """Get the current authenticated user."""
        return getattr(_thread_local, 'user', None)

    @staticmethod
    def get_tenant() -> TenantContext | None:
        """Get the current tenant context."""
        return getattr(_thread_local, 'tenant', None)

    @staticmethod
    def has_permission(permission_class: type) -> bool:
        """
        Check if current user has a specific permission.

        In OpenSearch plugin, this delegates to SecurityContext.hasPermission().
        """
        user = SecurityContext.get_user()
        if user is None:
            return False

        # Map permission classes to backend role requirements
        required_roles = {
            'ClusterReadPermission': ['guardian_monitor', 'guardian_manager', 'guardian_internal'],
            'ClusterMonitorPermission': ['guardian_monitor', 'guardian_manager'],
            'ClusterManagePermission': ['guardian_manager', 'guardian_internal'],
        }

        permission_name = permission_class.__name__
        required = required_roles.get(permission_name, [])

        if not required:
            return False

        # Check if user has any required backend role
        return any(role in user.backend_roles for role in required)


def get_current_user() -> UserIdentity | None:
    """Get the current authenticated user."""
    return SecurityContext.get_user()


def get_current_tenant() -> TenantContext | None:
    """Get the current tenant context."""
    return SecurityContext.get_tenant()


def get_user_roles() -> list[str]:
    """Get the current user's backend roles."""
    user = SecurityContext.get_user()
    return user.backend_roles if user else []


def require_permission(permission_class: type) -> None:
    """
    Decorator/context manager to require a specific permission.

    Raises PermissionError if current user lacks the required permission.
    """
    if not SecurityContext.has_permission(permission_class):
        permission_name = permission_class.__name__
        user = SecurityContext.get_user()
        username = user.username if user else "anonymous"
        raise PermissionError(
            f"User '{username}' lacks required permission: {permission_name}"
        )