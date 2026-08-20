"""Guardian Role Definitions for OpenSearch Security Plugin.

Defines Guardian-specific roles that map to OpenSearch Security backend roles.
These roles are configured in OpenSearch Security's roles.yml and mapped
to backend roles in roles_mapping.yml.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from guardian.security.permissions import (
    ClusterManagePermission,
    ClusterMonitorPermission,
    ClusterReadPermission,
    GuardianPermission,
)


@dataclass(frozen=True)
class GuardianRole:
    """Guardian role definition for OpenSearch Security plugin.

    Each role maps to a backend role in OpenSearch Security configuration.
    Roles define a set of permissions that are granted to users with this role.
    """
    name: str
    display_name: str
    description: str
    backend_role: str  # The role name used in OpenSearch Security (roles.yml)
    permissions: set[GuardianPermission] = field(default_factory=set)
    index_patterns: dict[str, set[str]] = field(default_factory=dict)  # pattern -> actions


# Guardian Role Definitions

GUARDIAN_MONITOR_ROLE = GuardianRole(
    name="guardian_monitor",
    display_name="Guardian Monitor",
    description="Read-only access to Guardian monitoring and diagnostic features. Can view cluster health, run diagnosis, and view optimization recommendations.",
    backend_role="guardian_monitor",
    permissions={
        ClusterReadPermission(),
        ClusterMonitorPermission(),
    },
    index_patterns={
        "*": {"indices:monitor/stats", "indices:monitor/settings/get", "indices:admin/get"}
    }
)

GUARDIAN_MANAGER_ROLE = GuardianRole(
    name="guardian_manager",
    display_name="Guardian Manager",
    description="Full access to Guardian features including provisioning approval and execution. Can approve and execute provisioning operations.",
    backend_role="guardian_manager",
    permissions={
        ClusterReadPermission(),
        ClusterMonitorPermission(),
        ClusterManagePermission(),
    },
    index_patterns={
        "*": {"indices:*"}
    }
)

GUARDIAN_INTERNAL_ROLE = GuardianRole(
    name="guardian_internal",
    display_name="Guardian Internal Service Account",
    description="Service account for Guardian plugin internal operations. Used for automated collection, scheduling, and internal API calls.",
    backend_role="guardian_internal",
    permissions={
        ClusterReadPermission(),
        ClusterMonitorPermission(),
        ClusterManagePermission(),
    },
    index_patterns={
        ".guardian-*": {"indices:*"},
        "*": {"indices:monitor/stats", "indices:admin/get"}
    }
)

ALL_GUARDIAN_ROLES: list[GuardianRole] = [
    GUARDIAN_MONITOR_ROLE,
    GUARDIAN_MANAGER_ROLE,
    GUARDIAN_INTERNAL_ROLE,
]

ROLES_BY_NAME: dict[str, GuardianRole] = {role.name: role for role in ALL_GUARDIAN_ROLES}
ROLES_BY_BACKEND_ROLE: dict[str, GuardianRole] = {role.backend_role: role for role in ALL_GUARDIAN_ROLES}


def get_role_by_name(name: str) -> GuardianRole | None:
    """Get a GuardianRole by its internal name."""
    return ROLES_BY_NAME.get(name)


def get_role_by_backend_role(backend_role: str) -> GuardianRole | None:
    """Get a GuardianRole by its OpenSearch Security backend role."""
    return ROLES_BY_BACKEND_ROLE.get(backend_role)


def get_all_roles() -> list[GuardianRole]:
    """Get all Guardian roles."""
    return list(ALL_GUARDIAN_ROLES)


def generate_roles_yml() -> str:
    """Generate OpenSearch Security roles.yml content for Guardian roles."""
    lines = []
    for role in ALL_GUARDIAN_ROLES:
        lines.append(f"  {role.backend_role}:")
        if role.permissions:
            perm_lines = [f'    - "{perm.permission_name}"' for perm in role.permissions]
            lines.append("    permissions:")
            lines.extend(perm_lines)

        if role.index_patterns:
            lines.append("    index_permissions:")
            for pattern, actions in role.index_patterns.items():
                lines.append(f'    - index_patterns: ["{pattern}"]')
                lines.append("      allowed_actions:")
                for action in sorted(actions):
                    lines.append(f'        - "{action}"')
        lines.append("")  # blank line between roles

    return "\n".join(lines)


def generate_roles_mapping_yml() -> str:
    """Generate OpenSearch Security roles_mapping.yml content for Guardian roles."""
    lines = []
    for role in ALL_GUARDIAN_ROLES:
        lines.append(f"  {role.backend_role}:")
        lines.append("    backend_roles:")
        lines.append(f'      - "{role.backend_role}"')
        lines.append("    users: []")
        lines.append("    hosts: []")
        lines.append("")

    return "\n".join(lines)


def generate_internal_users_yml() -> str:
    """Generate OpenSearch Security internal_users.yml content for Guardian service account."""
    return f"""guardian_service_account:
  hash: "$2a$12$..."  # bcrypt hash - set during deployment
  backend_roles:
    - "{GUARDIAN_INTERNAL_ROLE.backend_role}"
  attributes:
    plugin: "guardian"
    purpose: "internal-operations"
    type: "service_account"
"""


def generate_action_groups_yml() -> str:
    """Generate OpenSearch Security action_groups.yml for Guardian custom actions."""
    return """# Guardian Custom Action Groups
# These define reusable permission sets for Guardian operations

GUARDIAN_MONITOR_ACTIONS:
  allowed_actions:
    - "cluster:monitor/main"
    - "cluster:monitor/health"
    - "cluster:monitor/state"
    - "cluster:monitor/nodes/stats"
    - "cluster:monitor/nodes/info"
    - "cluster:admin/allocation/explain"
    - "indices:monitor/stats"
    - "indices:monitor/settings/get"
    - "indices:admin/get"
    - "indices:admin/mappings/fields/get"

GUARDIAN_MANAGE_ACTIONS:
  allowed_actions:
    - "cluster:*"
    - "indices:*"
    - "cluster:admin/plugin/guardian/*"

GUARDIAN_INTERNAL_ACTIONS:
  allowed_actions:
    - "cluster:monitor/main"
    - "cluster:monitor/health"
    - "cluster:monitor/state"
    - "cluster:monitor/nodes/stats"
    - "cluster:admin/plugin/guardian/internal/*"
    - "indices:*" on ".guardian-*"
"""