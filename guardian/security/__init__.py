"""OpenSearch Security Plugin Integration for Guardian.

This module provides integration with OpenSearch Security plugin for
authentication and authorization. It leverages OpenSearch's built-in
authentication backends and authorization engine rather than implementing
custom authentication logic.

Key Components:
- SecurityContext: Access to current authenticated user
- Custom Permissions: Guardian-specific permission classes
- Role Mapping: Guardian roles mapped to OpenSearch Security roles
- Configuration: Plugin security policy and role definitions
"""

from .config import (
    PluginSecurityPolicy,
    generate_security_config,
    get_plugin_security_policy,
)
from .context import (
    SecurityContext,
    TenantContext,
    UserIdentity,
    get_current_tenant,
    get_current_user,
    get_user_roles,
)
from .permissions import (
    ClusterManagePermission,
    ClusterMonitorPermission,
    ClusterReadPermission,
    GuardianPermission,
    check_permission,
)
from .roles import (
    GUARDIAN_INTERNAL_ROLE,
    GUARDIAN_MANAGER_ROLE,
    GUARDIAN_MONITOR_ROLE,
    GuardianRole,
)

__all__ = [
    "GUARDIAN_INTERNAL_ROLE",
    "GUARDIAN_MANAGER_ROLE",
    "GUARDIAN_MONITOR_ROLE",
    "ClusterManagePermission",
    "ClusterMonitorPermission",
    "ClusterReadPermission",
    "GuardianPermission",
    "GuardianRole",
    "PluginSecurityPolicy",
    "SecurityContext",
    "generate_security_config",
    "get_current_tenant",
    "get_current_user",
    "get_plugin_security_policy",
    "get_user_roles",
]