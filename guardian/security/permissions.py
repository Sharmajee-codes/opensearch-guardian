"""Guardian Custom Permissions for OpenSearch Security Plugin.

Defines Guardian-specific permission classes that map to OpenSearch Security
plugin permissions. These are used for fine-grained authorization checks
in backend services.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class GuardianPermission(ABC):
    """Base class for Guardian permissions in OpenSearch Security plugin.

    In OpenSearch Security plugin, permissions are implemented as Java classes
    extending org.opensearch.security.SecurityPermission. This Python class
    mirrors that structure for use in Python-based backend services.
    """

    @property
    @abstractmethod
    def permission_name(self) -> str:
        """Fully qualified permission name (e.g., 'org.opensearch.guardian.security.ClusterReadPermission')."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this permission allows."""

    @abstractmethod
    def required_roles(self) -> set[str]:
        """Set of OpenSearch Security backend roles that grant this permission."""

    def __eq__(self, other: object) -> bool:
        """Compare permissions by permission_name for set membership."""
        if not isinstance(other, GuardianPermission):
            return NotImplemented
        return self.permission_name == other.permission_name

    def __hash__(self) -> int:
        """Hash based on permission_name for set/dict usage."""
        return hash(self.permission_name)


class ClusterReadPermission(GuardianPermission):
    """Permission to read cluster health and basic monitoring data.

    Maps to guardian_monitor role in OpenSearch Security.
    """

    @property
    def permission_name(self) -> str:
        return "org.opensearch.guardian.security.ClusterReadPermission"

    @property
    def description(self) -> str:
        return "Read access to cluster health, node status, and basic monitoring data"

    def required_roles(self) -> set[str]:
        return {"guardian_monitor", "guardian_manager", "guardian_internal"}


class ClusterMonitorPermission(GuardianPermission):
    """Permission to run diagnostic operations and access detailed metrics.

    Maps to guardian_monitor and guardian_manager roles in OpenSearch Security.
    """

    @property
    def permission_name(self) -> str:
        return "org.opensearch.guardian.security.ClusterMonitorPermission"

    @property
    def description(self) -> str:
        return "Run cluster diagnosis, access detailed metrics, and view diagnostic rules"

    def required_roles(self) -> set[str]:
        return {"guardian_monitor", "guardian_manager"}


class ClusterManagePermission(GuardianPermission):
    """Permission to manage cluster operations including provisioning.

    Maps to guardian_manager role in OpenSearch Security.
    """

    @property
    def permission_name(self) -> str:
        return "org.opensearch.guardian.security.ClusterManagePermission"

    @property
    def description(self) -> str:
        return "Approve and execute provisioning operations, manage cluster configuration"

    def required_roles(self) -> set[str]:
        return {"guardian_manager", "guardian_internal"}


# Permission registry for easy lookup
ALL_GUARDIAN_PERMISSIONS: set[GuardianPermission] = {
    ClusterReadPermission(),
    ClusterMonitorPermission(),
    ClusterManagePermission(),
}

PERMISSIONS_BY_NAME: dict[str, GuardianPermission] = {
    perm.permission_name: perm for perm in ALL_GUARDIAN_PERMISSIONS
}

PERMISSIONS_BY_ROLE: dict[str, set[GuardianPermission]] = {
    "guardian_monitor": {ClusterReadPermission(), ClusterMonitorPermission()},
    "guardian_manager": {ClusterReadPermission(), ClusterMonitorPermission(), ClusterManagePermission()},
    "guardian_internal": {ClusterReadPermission(), ClusterMonitorPermission(), ClusterManagePermission()},
}


def get_permission_by_name(name: str) -> GuardianPermission | None:
    """Get a permission by its fully qualified name."""
    return PERMISSIONS_BY_NAME.get(name)


def get_permissions_for_role(role: str) -> set[GuardianPermission]:
    """Get all permissions granted by a specific backend role."""
    return PERMISSIONS_BY_ROLE.get(role, set())


def check_permission(permission_class: type[GuardianPermission], user_roles: set[str]) -> bool:
    """
    Check if a user with the given roles has a specific permission.

    Args:
        permission_class: The GuardianPermission subclass to check
        user_roles: Set of backend roles the user has

    Returns:
        True if the user has the permission, False otherwise
    """
    perm = permission_class()
    required = perm.required_roles()
    return bool(required & user_roles)


def get_permission_instance(permission_class: type[GuardianPermission]) -> GuardianPermission:
    """Get the canonical instance for a permission class.

    This ensures consistent identity for use in set membership checks.
    """
    perm = permission_class()
    return PERMISSIONS_BY_NAME.get(perm.permission_name, perm)