"""Tests for security permissions, roles, and config."""

import pytest

from guardian.security.permissions import (
    GuardianPermission,
    ClusterReadPermission,
    ClusterMonitorPermission,
    ClusterManagePermission,
    ALL_GUARDIAN_PERMISSIONS,
    PERMISSIONS_BY_NAME,
    PERMISSIONS_BY_ROLE,
    get_permission_by_name,
    get_permissions_for_role,
    check_permission,
    get_permission_instance,
)
from guardian.security.roles import (
    GuardianRole,
    GUARDIAN_MONITOR_ROLE,
    GUARDIAN_MANAGER_ROLE,
    GUARDIAN_INTERNAL_ROLE,
    ALL_GUARDIAN_ROLES,
    ROLES_BY_NAME,
    ROLES_BY_BACKEND_ROLE,
    get_role_by_name,
    get_role_by_backend_role,
    get_all_roles,
    generate_roles_yml,
    generate_roles_mapping_yml,
    generate_internal_users_yml,
    generate_action_groups_yml,
)
from guardian.security.config import (
    PluginSecurityPolicy,
    get_plugin_security_policy,
    generate_security_config,
    validate_security_config,
)


class TestGuardianPermission:
    """Tests for GuardianPermission base class and implementations."""

    def test_cluster_read_permission(self):
        perm = ClusterReadPermission()
        assert perm.permission_name == "org.opensearch.guardian.security.ClusterReadPermission"
        assert "Read access" in perm.description
        required = perm.required_roles()
        assert "guardian_monitor" in required
        assert "guardian_manager" in required
        assert "guardian_internal" in required

    def test_cluster_monitor_permission(self):
        perm = ClusterMonitorPermission()
        assert "MonitorPermission" in perm.permission_name
        assert "diagnostic" in perm.description.lower()
        required = perm.required_roles()
        assert "guardian_monitor" in required
        assert "guardian_manager" in required

    def test_cluster_manage_permission(self):
        perm = ClusterManagePermission()
        assert "ManagePermission" in perm.permission_name
        assert "provisioning" in perm.description.lower()
        required = perm.required_roles()
        assert "guardian_manager" in required
        assert "guardian_internal" in required

    def test_equality(self):
        p1 = ClusterReadPermission()
        p2 = ClusterReadPermission()
        assert p1 == p2

    def test_hash(self):
        p1 = ClusterReadPermission()
        p2 = ClusterReadPermission()
        assert hash(p1) == hash(p2)

    def test_all_permissions_registered(self):
        assert len(ALL_GUARDIAN_PERMISSIONS) == 3
        assert ClusterReadPermission() in ALL_GUARDIAN_PERMISSIONS
        assert ClusterMonitorPermission() in ALL_GUARDIAN_PERMISSIONS
        assert ClusterManagePermission() in ALL_GUARDIAN_PERMISSIONS

    def test_permissions_by_name(self):
        assert get_permission_by_name("org.opensearch.guardian.security.ClusterReadPermission") is not None
        assert get_permission_by_name("nonexistent") is None

    def test_permissions_by_role(self):
        monitor_perms = get_permissions_for_role("guardian_monitor")
        assert len(monitor_perms) == 2

        manager_perms = get_permissions_for_role("guardian_manager")
        assert len(manager_perms) == 3

        unknown_perms = get_permissions_for_role("unknown_role")
        assert len(unknown_perms) == 0

    def test_check_permission(self):
        assert check_permission(ClusterReadPermission, {"guardian_monitor"}) is True
        assert check_permission(ClusterReadPermission, {"unknown"}) is False
        assert check_permission(ClusterManagePermission, {"guardian_manager"}) is True
        assert check_permission(ClusterManagePermission, {"guardian_monitor"}) is False

    def test_get_permission_instance(self):
        p1 = get_permission_instance(ClusterReadPermission)
        p2 = get_permission_instance(ClusterReadPermission)
        assert p1 == p2
        assert p1 is p2  # Same instance from registry


class TestGuardianRoles:
    """Tests for Guardian role definitions."""

    def test_monitor_role(self):
        assert GUARDIAN_MONITOR_ROLE.name == "guardian_monitor"
        assert GUARDIAN_MONITOR_ROLE.display_name == "Guardian Monitor"
        assert len(GUARDIAN_MONITOR_ROLE.permissions) == 2
        assert ClusterReadPermission() in GUARDIAN_MONITOR_ROLE.permissions
        assert ClusterMonitorPermission() in GUARDIAN_MONITOR_ROLE.permissions

    def test_manager_role(self):
        assert GUARDIAN_MANAGER_ROLE.name == "guardian_manager"
        assert len(GUARDIAN_MANAGER_ROLE.permissions) == 3

    def test_internal_role(self):
        assert GUARDIAN_INTERNAL_ROLE.name == "guardian_internal"
        assert ".guardian-*" in GUARDIAN_INTERNAL_ROLE.index_patterns

    def test_roles_by_name(self):
        assert get_role_by_name("guardian_monitor") == GUARDIAN_MONITOR_ROLE
        assert get_role_by_name("nonexistent") is None

    def test_roles_by_backend_role(self):
        assert get_role_by_backend_role("guardian_monitor") == GUARDIAN_MONITOR_ROLE
        assert get_role_by_backend_role("nonexistent") is None

    def test_get_all_roles(self):
        roles = get_all_roles()
        assert len(roles) == 3
        assert GUARDIAN_MONITOR_ROLE in roles
        assert GUARDIAN_MANAGER_ROLE in roles
        assert GUARDIAN_INTERNAL_ROLE in roles

    def test_generate_roles_yml(self):
        yml = generate_roles_yml()
        assert "guardian_monitor" in yml
        assert "guardian_manager" in yml
        assert "guardian_internal" in yml
        assert "permissions:" in yml

    def test_generate_roles_mapping_yml(self):
        yml = generate_roles_mapping_yml()
        assert "guardian_monitor" in yml
        assert "backend_roles:" in yml
        assert "users: []" in yml

    def test_generate_internal_users_yml(self):
        yml = generate_internal_users_yml()
        assert "guardian_service_account" in yml
        assert "backend_roles:" in yml

    def test_generate_action_groups_yml(self):
        yml = generate_action_groups_yml()
        assert "GUARDIAN_MONITOR_ACTIONS" in yml
        assert "GUARDIAN_MANAGE_ACTIONS" in yml
        assert "GUARDIAN_INTERNAL_ACTIONS" in yml


class TestPluginSecurityPolicy:
    """Tests for PluginSecurityPolicy."""

    def test_generate_policy_file(self):
        policy = PluginSecurityPolicy()
        content = policy.generate_policy_file()
        assert "guardian" in content
        assert "GuardianReadPermission" in content
        assert "GuardianManagePermission" in content

    def test_generate_securityconfig_yml(self):
        policy = PluginSecurityPolicy()
        content = policy.generate_securityconfig_yml()
        assert "guardian_monitor" in content
        assert "guardian_manager" in content

    def test_generate_roles_yml_delegates(self):
        policy = PluginSecurityPolicy()
        content = policy.generate_roles_yml()
        assert "guardian_monitor" in content

    def test_generate_all_configs(self):
        config = generate_security_config()
        assert "plugin-security.policy" in config
        assert "securityconfig.yml" in config
        assert "roles.yml" in config
        assert "roles_mapping.yml" in config
        assert "internal_users.yml" in config
        assert "action_groups.yml" in config

    def test_validate_security_config_valid(self):
        config = generate_security_config()
        warnings = validate_security_config(config)
        assert len(warnings) == 0

    def test_validate_security_config_missing_files(self):
        config = {"plugin-security.policy": "some content"}
        warnings = validate_security_config(config)
        assert any("Missing required" in w for w in warnings)

    def test_validate_security_config_empty_file(self):
        config = generate_security_config()
        config["roles.yml"] = ""
        warnings = validate_security_config(config)
        assert any("empty" in w for w in warnings)

    def test_validate_security_config_missing_permission(self):
        config = generate_security_config()
        config["plugin-security.policy"] = "no permissions here"
        warnings = validate_security_config(config)
        assert any("Missing permission" in w for w in warnings)

    def test_validate_security_config_missing_role(self):
        config = generate_security_config()
        config["roles.yml"] = "no roles here"
        warnings = validate_security_config(config)
        assert any("Missing role" in w for w in warnings)

    def test_get_plugin_security_policy(self):
        policy = get_plugin_security_policy()
        assert isinstance(policy, PluginSecurityPolicy)
        assert policy.plugin_name == "guardian"
        assert policy.plugin_version == "1.0.0"
