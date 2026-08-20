"""Plugin Security Configuration for OpenSearch Security Integration.

Generates OpenSearch Security plugin configuration files for Guardian
including plugin-security.policy, securityconfig.yml snippets, and role definitions.
"""

from __future__ import annotations

from dataclasses import dataclass

from guardian.security.roles import (
    generate_action_groups_yml,
    generate_internal_users_yml,
    generate_roles_mapping_yml,
    generate_roles_yml,
)


@dataclass
class PluginSecurityPolicy:
    """Configuration for Guardian plugin security policy.

    Generates plugin-security.policy file for OpenSearch backend plugin.
    """
    plugin_name: str = "guardian"
    plugin_version: str = "1.0.0"

    def generate_policy_file(self) -> str:
        """Generate plugin-security.policy content."""
        return f"""# Guardian Plugin Security Policy
# This file defines custom permissions and their role mappings for the Guardian plugin

# Plugin metadata
plugin.name = {self.plugin_name}
plugin.version = {self.plugin_version}

# Custom permissions for Guardian operations
permission GuardianReadPermission "org.opensearch.guardian.security.ClusterReadPermission";
permission GuardianMonitorPermission "org.opensearch.guardian.security.ClusterMonitorPermission";
permission GuardianManagePermission "org.opensearch.guardian.security.ClusterManagePermission";

# Role mappings
grant role "guardian_monitor" {{
  permission GuardianReadPermission;
  permission GuardianMonitorPermission;
}}

grant role "guardian_manager" {{
  permission GuardianReadPermission;
  permission GuardianMonitorPermission;
  permission GuardianManagePermission;
}}

grant role "guardian_internal" {{
  permission GuardianReadPermission;
  permission GuardianMonitorPermission;
  permission GuardianManagePermission;
}}

# Endpoint protection
endpoint "/_plugins/guardian/*" {{
  permissions = [GuardianReadPermission, GuardianMonitorPermission]
  methods = ["GET", "POST"]
}}

endpoint "/_plugins/guardian/health" {{
  permissions = [GuardianReadPermission]
  methods = ["GET"]
}}

endpoint "/_plugins/guardian/diagnosis" {{
  permissions = [GuardianMonitorPermission]
  methods = ["GET", "POST"]
}}

endpoint "/_plugins/guardian/optimization" {{
  permissions = [GuardianReadPermission]
  methods = ["GET", "POST"]
}}

endpoint "/_plugins/guardian/provisioning" {{
  permissions = [GuardianManagePermission]
  methods = ["POST", "PUT", "DELETE"]
}}

endpoint "/_plugins/guardian/provisioning/approve" {{
  permissions = [GuardianManagePermission]
  methods = ["POST"]
}}

endpoint "/_plugins/guardian/audit" {{
  permissions = [GuardianReadPermission]
  methods = ["GET"]
}}
"""

    def generate_securityconfig_yml(self) -> str:
        """Generate securityconfig.yml additions for Guardian."""
        return """# Guardian Plugin Security Configuration
# Add to OpenSearch securityconfig.yml under config.dynamic.authc and config.dynamic.authz

config:
  dynamic:
    # Guardian plugin authentication - relies on OpenSearch built-in auth
    # No additional authc configuration needed

    # Guardian plugin authorization
    authz:
      # Guardian plugin roles
      guardian_roles:
        enabled: true
        order: 0

      # Guardian monitor role
      guardian_monitor:
        enabled: true
        order: 10
        cluster_permissions:
          - "cluster:monitor/main"
          - "cluster:monitor/health"
          - "cluster:monitor/state"
          - "cluster:monitor/nodes/stats"
          - "cluster:monitor/nodes/info"
          - "cluster:admin/allocation/explain"
        index_permissions:
          - index_patterns: ["*"]
            allowed_actions:
              - "indices:monitor/stats"
              - "indices:monitor/settings/get"
              - "indices:admin/get"
              - "indices:admin/mappings/fields/get"

      # Guardian manager role
      guardian_manager:
        enabled: true
        order: 10
        cluster_permissions:
          - "cluster:*"
        index_permissions:
          - index_patterns: ["*"]
            allowed_actions: ["indices:*"]

      # Guardian internal role
      guardian_internal:
        enabled: true
        order: 10
        cluster_permissions:
          - "cluster:monitor/main"
          - "cluster:monitor/health"
          - "cluster:monitor/state"
          - "cluster:monitor/nodes/stats"
          - "cluster:admin/plugin/guardian/internal/*"
        index_permissions:
          - index_patterns: [".guardian-*"]
            allowed_actions: ["indices:*"]
          - index_patterns: ["*"]
            allowed_actions:
              - "indices:monitor/stats"
              - "indices:admin/get"
"""

    def generate_roles_yml(self) -> str:
        """Generate roles.yml content for Guardian roles."""
        return generate_roles_yml()

    def generate_roles_mapping_yml(self) -> str:
        """Generate roles_mapping.yml content for Guardian roles."""
        return generate_roles_mapping_yml()

    def generate_internal_users_yml(self) -> str:
        """Generate internal_users.yml content for Guardian service account."""
        return generate_internal_users_yml()

    def generate_action_groups_yml(self) -> str:
        """Generate action_groups.yml content for Guardian action groups."""
        return generate_action_groups_yml()


def get_plugin_security_policy() -> PluginSecurityPolicy:
    """Get the default plugin security policy."""
    return PluginSecurityPolicy()


def generate_security_config() -> dict[str, str]:
    """Generate all security configuration files for Guardian plugin.

    Returns:
        Dictionary mapping file names to their content.
    """
    policy = get_plugin_security_policy()
    return {
        "plugin-security.policy": policy.generate_policy_file(),
        "securityconfig.yml": policy.generate_securityconfig_yml(),
        "roles.yml": policy.generate_roles_yml(),
        "roles_mapping.yml": policy.generate_roles_mapping_yml(),
        "internal_users.yml": policy.generate_internal_users_yml(),
        "action_groups.yml": policy.generate_action_groups_yml(),
    }


def validate_security_config(config: dict[str, str]) -> list[str]:
    """Validate generated security configuration for common issues.

    Args:
        config: Dictionary of security config files

    Returns:
        List of validation warnings/errors (empty if valid)
    """
    warnings = []

    # Check all required files present
    required_files = [
        "plugin-security.policy",
        "securityconfig.yml",
        "roles.yml",
        "roles_mapping.yml",
        "internal_users.yml",
        "action_groups.yml",
    ]

    for file in required_files:
        if file not in config:
            warnings.append(f"Missing required security config file: {file}")
        elif not config[file].strip():
            warnings.append(f"Security config file is empty: {file}")

    # Check plugin-security.policy has required permissions
    policy = config.get("plugin-security.policy", "")
    required_perms = [
        "GuardianReadPermission",
        "GuardianMonitorPermission",
        "GuardianManagePermission",
    ]
    for perm in required_perms:
        if perm not in policy:
            warnings.append(f"Missing permission in plugin-security.policy: {perm}")

    # Check roles.yml has Guardian roles
    roles = config.get("roles.yml", "")
    for role in ["guardian_monitor", "guardian_manager", "guardian_internal"]:
        if role not in roles:
            warnings.append(f"Missing role in roles.yml: {role}")

    return warnings