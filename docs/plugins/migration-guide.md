# OpenSearch Guardian Migration Guide

## Overview
This guide provides a comprehensive migration path from the standalone OpenSearch Guardian (T28 Safety Engine) to the OpenSearch plugin architecture. It covers the architectural changes, configuration mapping, and step-by-step migration process.

## Migration Phases

### Phase 0: Preparation
Before beginning migration, ensure:
- OpenSearch 2.11+ cluster is running
- OpenSearch Security plugin is installed and configured
- Basic understanding of OpenSearch Security concepts (roles, action groups, tenants)
- Backup existing Guardian configuration and data

### Phase 1: Security & RBAC Mapping
Map Guardian's internal security model to OpenSearch Security primitives.

#### 1.1 Role Mapping
| Guardian Concept | OpenSearch Security Equivalent | Configuration File |
|------------------|--------------------------------|-------------------|
| T1-T3 Collectors (read-only) | `guardian_monitoring` role | `roles.yml` |
| Doctor/Diagnostic operations | `guardian_doctor` role | `roles.yml` |
| Optimizer/Analysis operations | `guardian_optimizer` role | `roles.yml` |
| Capacity Planner operations | `guardian_capacity` role | `roles.yml` |
| Provisioning/Admin operations | `guardian_admin` role | `roles.yml` |
| Internal service account | `guardian_internal` role | `roles.yml` |
| User-to-role mapping | Backend role assignments | `roles_mapping.yml` |
| Service account credentials | Internal user database | `internal_users.yml` |

#### 1.2 Permission Mapping
| Guardian Operation | Required OpenSearch Permission | Action Group |
|--------------------|--------------------------------|--------------|
| Cluster health read | `cluster:monitor/health` | `cluster:monitor/main` |
| Node stats read | `cluster:monitor/nodes/stats` | `cluster:monitor/main` |
| Index stats read | `indices:monitor/stats` | `indices:monitor/stats` |
| Cluster state read | `cluster:monitor/state` | `cluster:monitor/main` |
| Diagnostic read operations | `cluster:monitor/*` | `cluster:monitor` |
| Allocation explain | `cluster:admin/allocation/explain` | `cluster:admin/allocation/explain` |
| ILM policy read | `indices:ilm/get*` | `indices:ilm/get*` |
| Index template read | `indices:get/template/*` | `indices:get/template/*` |
| Snapshot read | `indices:snapshot/get*` | `indices:snapshot/get*` |
| Provisioning operations | `cluster:admin/plugin/guardian/*` | `cluster:admin/plugin/guardian/*` |
| Optimization recommendations | `cluster:admin/plugin/guardian/optimize/*` | `cluster:admin/plugin/guardian/optimize/*` |
| Dry-run validation | `cluster:admin/plugin/guardian/dry-run/*` | `cluster:admin/plugin/guardian/dry-run/*` |

#### 1.3 Tenant Mapping
| Guardian Concept | OpenSearch Security Equivalent |
|------------------|--------------------------------|
| Global context (admin) | Global tenant |
| User-specific context | Private tenant |
| Team/shared context | Shared tenant (role-based) |

### Phase 2: Configuration Migration
Convert Guardian configuration files to OpenSearch Security format.

#### 2.1 securityconfig.yml
```yaml
# OpenSearch Security configuration
config:
  dynamic:
    # Authentication methods
    authc:
      internal_user_database:
        enabled: true
        order: 0
        http_authenticator:
          type: basic
          challenge: false
        authentication_backend:
          type: intern
    # Authorization (RBAC)
    authz:
      roles_from_myldap:
        enabled: false
    # Audit logging
    audit:
      enabled: true
      log_requests: true
      log_ignored: true
      resolve_indices: true
      ignore_users: ["kibana_server", "guardian_service_account"]
      ignore_actions: ["cluster:monitor/main"]
      output:
        index:
          enabled: true
          index_name: "security-audit-log-%{+yyyy.MM.dd}"
        log4j:
          enabled: true
    # TLS (if needed)
    http:
      ssl:
        enabled: false
    transport:
      ssl:
        enabled: false
```

#### 2.2 Plugin Security Policy
Create `plugin-security.policy` in the Guardian plugin resources:

```properties
grant {
    permission org.opensearch.guardian.security.ClusterReadPermission;
    permission org.opensearch.guardian.security.ClusterMonitorPermission;
    permission org.opensearch.guardian.security.ClusterManagePermission;
};

grant codeBase "file:${opensearch.install.dir}/plugins/guardian/-" {
    permission java.security.AllPermission;
};
```

### Phase 3: Data Migration
Migrate existing Guardian data to the new plugin architecture.

#### 3.1 Snapshot Store Migration
```bash
# Export existing snapshots from SQLite
sqlite3 guardian_snapshots.db ".mode csv" ".output snapshots.csv" "SELECT * FROM snapshots;"

# Import to new plugin storage (if needed)
# The plugin uses its own snapshot storage mechanism
```

#### 3.2 Audit Log Migration
If migrating from T28 audit store:
```bash
# Export HMAC-signed audit entries
sqlite3 audit_store.db ".mode csv" ".output audit.csv" "SELECT * FROM audit_entries;"

# Note: New audit goes to OpenSearch Security audit index
# Old entries can be queried but not automatically migrated
```

### Phase 4: Service Migration
Update service implementations to use plugin context.

#### 4.1 Context Changes
Replace direct OpenSearch client with plugin-provided services:

```java
// Before (T28)
private RestHighLevelClient client;

// After (Plugin)
private final ClusterService clusterService;
private final NodeClient nodeClient;

// Constructor
public GuardianService(ClusterService clusterService, NodeClient nodeClient) {
    this.clusterService = clusterService;
    this.nodeClient = nodeClient;
}
```

#### 4.2 Permission Checks
Integrate with SecurityContext:

```java
public class GuardianHealthService {
    
    public void getClusterHealth(RestChannel channel) {
        SecurityContext context = SecurityContext.getContext();
        
        if (!context.hasPermission(new ClusterReadPermission())) {
            throw new SecurityException("Insufficient permissions: cluster:read required");
        }
        
        // Proceed with health check
        // ...
    }
}
```

#### 4.3 Role Configuration Verification
**Important:** Verify that role names in `securityconfig.yml` match the custom permissions used in code:
- `guardian_monitor` → maps to `ClusterReadPermission` (cluster:read)
- `guardian_manager` → maps to `ClusterMonitorPermission` + `ClusterManagePermission`

```yaml
# securityconfig.yml example
roles:
  guardian_monitor:
    cluster_permissions:
      - "cluster:monitor/main"
      - "cluster:monitor/health"
    index_permissions:
      - index_patterns: ["*"]
        allowed_actions: ["indices:monitor/stats"]
  guardian_manager:
    cluster_permissions:
      - "cluster:admin/*"
    index_permissions:
      - index_patterns: ["*"]
        allowed_actions: ["indices:*"]
```

**Verify during migration:** Run `GET /_plugins/_security/api/roles/guardian_monitor` and confirm permissions match expected values.

#### 4.3 Tenant Propagation
For multi-tenant deployments:

```java
public class TenantAwareDiagnosisService {
    
    public DiagnosisResult diagnose(CollectionResult snapshot) {
        String tenant = SecurityContext.getContext().getTenant();
        
        // Pass tenant to downstream operations if needed
        return diagnosisEngine.evaluate(snapshot, tenant);
    }
}
```

### Phase 5: UI Migration
Update Dashboards plugin to use OpenSearch Security.

#### 5.1 Authentication
Use the Security plugin's authentication context:

```typescript
// Before (direct API calls)
const response = await fetch('/api/guardian/health', {
    headers: { Authorization: `Bearer ${token}` }
});

// After (via Security plugin)
const { user, roles, tenant } = useAuth(); // From @opensearch-dashboards/security
const response = await http.get('/guardian/health');
// Security plugin automatically handles authentication
```

#### 5.2 Permission Checks
Use role-based UI guards:

```typescript
import { useAuth } from '@opensearch-dashboards/security';

export const GuardianApp = () => {
  const { user, roles } = useAuth();
  
  // Conditional rendering based on roles
  const canProvision = roles.includes('guardian_admin_role');
  const canDiagnose = roles.includes('guardian_doctor_role') || 
                      roles.includes('guardian_admin_role');
  
  return (
    <div>
      {canProvision && <ProvisioningButton />}
      {canDiagnose && <DiagnosisButton />}
      <MonitoringButton /> // Available to all authenticated users
    </div>
  );
};
```

#### 5.3 Tenant Awareness
Respect tenant context in queries:

```typescript
export const useGuardianApi = () => {
  const { tenant } = useAuth();
  const http = useHttp();
  
  return {
    getClusterHealth: () => 
      http.get(`/guardian/cluster/health?tenant=${tenant}`),
    // ...
  };
};
```

## Verification Checklist

### Security Verification
- [ ] All roles defined in `roles.yml` with correct permissions
- [ ] Role mappings in `roles_mapping.yml` correct
- [ ] Service accounts in `internal_users.yml` with proper hashes
- [ ] Plugin security policy grants required permissions
- [ ] OpenSearch Security audit logging enabled
- [ ] TLS configuration (if used) matches cluster settings

### Functional Verification
- [ ] Guardian plugin loads successfully in OpenSearch
- [ ] REST endpoints accessible with appropriate roles
- [ ] Dashboard plugin loads and shows UI
- [ ] Permission denied responses (403) for insufficient privileges
- [ ] Audit logs capture authentication and authorization events
- [ ] Snapshot collection works across all tiers
- [ ] Diagnosis engine executes rules correctly
- [ ] Optimization provides recommendations
- [ ] Provisioning workflow completes successfully

### Performance Verification
- [ ] Collection intervals match ADR-005 (T1: 5s, T2: 12s, T3: 45s, T4: 5min)
- [ ] Resource usage within acceptable limits
- [ ] Query response times under SLA thresholds
- [ ] Concurrent user handling tested

## Rollback Procedure
If issues are discovered post-migration:

1. **Temporary Rollback**: Disable Guardian plugin while keeping Security plugin
   ```bash
   bin/opensearch-plugin remove guardian
   ```
2. **Data Preservation**: Existing snapshot data remains in plugin indices
3. **Configuration Backup**: Keep copies of `roles.yml`, `roles_mapping.yml`, etc.
4. **Re-enable**: Fix issues and reinstall plugin
   ```bash
   bin/opensearch-plugin install file:///path/to/guardian.zip
   ```

## Troubleshooting

### Common Issues

#### Plugin Fails to Load
- Check OpenSearch logs for `Plugin loading failed` errors
- Verify `plugin-descriptor.properties` points to correct class
- Ensure all dependencies are included in plugin ZIP
- Check Java version compatibility

#### Permission Denied Errors (403)
- Verify user has correct backend role assigned
- Check `roles_mapping.yml` maps backend roles to security roles
- Confirm `roles.yml` grants required permissions to security roles
- Review OpenSearch Security audit logs for denial reasons

#### Missing Audit Entries
- Verify `audit.enabled: true` in `securityconfig.yml`
- Check index pattern matches `security-audit-log-*`
- Ensure write permissions on audit index
- Look for index creation errors in logs

#### Tenant Isolation Issues
- Confirm tenant propagation in service layer
- Check that index patterns respect tenant context
- Verify private tenant data isolation
- Review Dashboard plugin tenant handling

#### Performance Degradation
- Verify collection schedules match ADR-005
- Check for unnecessary index refreshes
- Monitor heap usage and garbage collection
- Review slow query logs for optimization opportunities

## References
- [OpenSearch Security Documentation](https://docs.opensearch.org/latest/security-plugin/)
- [OpenSearch Security Configuration Guide](https://docs.opensearch.org/latest/security-plugin/configuration/)
- [OpenSearch Plugin Development Guide](https://docs.opensearch.org/latest/plugindev/)
- [OpenSearch Dashboards Security Guide](https://docs.opensearch.org/latest/dashboards/security/)
- [OpenSearch TLS Configuration](https://docs.opensearch.org/latest/security-plugin/configuration/tls/)

## Appendix A: Complete Configuration Examples

### roles.yml
```yaml
# Monitoring role - T1-T3 collectors
guardian_monitoring:
  cluster_permissions:
    - "cluster:monitor/main"
    - "cluster:monitor/health"
    - "cluster:monitor/state"
    - "cluster:monitor/nodes/stats"
    - "cluster:monitor/nodes/info"
  index_permissions:
    - index_patterns: ["*"]
      allowed_actions:
        - "indices:monitor/stats"
        - "indices:monitor/settings/get"
        - "indices:admin/get"

# Diagnostic role - Doctor operations
guardian_doctor:
  cluster_permissions:
    - "cluster:monitor/*"
    - "cluster:admin/allocation/explain"
    - "cluster:admin/node/shutdown"
  index_permissions:
    - index_patterns: ["*"]
      allowed_actions:
        - "indices:monitor/*"
        - "indices:admin/get"
        - "indices:admin/mappings/fields/get"
        - "indices:admin/templates/get"

# Optimizer role - Analysis operations
guardian_optimizer:
  cluster_permissions:
    - "cluster:monitor/*"
    - "cluster:admin/plugin/guardian/optimize/read/*"
  index_permissions:
    - index_patterns: ["*"]
      allowed_actions:
        - "indices:monitor/*"
        - "indices:admin/get"
        - "indices:admin/settings/get"
        - "indices:admin/template/get"

# Capacity Planner role
guardian_capacity:
  cluster_permissions:
    - "cluster:monitor/*"
  index_permissions:
    - index_patterns: ["*"]
      allowed_actions:
        - "indices:monitor/*"
        - "indices:admin/get"

# Provisioning role - Admin operations
guardian_admin:
  cluster_permissions:
    - "cluster:*"
    - "cluster:admin/plugin/guardian/*"
  index_permissions:
    - index_patterns: ["*"]
      allowed_actions: ["indices:*"]

# Internal service account
guardian_internal:
  cluster_permissions:
    - "cluster:monitor/main"
    - "cluster:monitor/health"
    - "cluster:monitor/state"
    - "cluster:admin/plugin/guardian/internal/*"
  index_permissions:
    - index_patterns: [".guardian-*"]
      allowed_actions: ["indices:*"]
```

### roles_mapping.yml
```yaml
guardian_monitoring:
  backend_roles:
    - "guardian_monitoring_role"
  users:
    - "monitor_user"
    - "metrics_collector"
  hosts: []

guardian_doctor:
  backend_roles:
    - "guardian_doctor_role"
  users: []
  hosts: []

guardian_optimizer:
  backend_roles:
    - "guardian_optimizer_role"
  users: []
  hosts: []

guardian_capacity:
  backend_roles:
    - "guardian_capacity_role"
  users: []
  hosts: []

guardian_admin:
  backend_roles:
    - "guardian_admin_role"
    - "admin_user"
  users:
    - "admin"
    - "opensearch_admin"
  hosts: []

guardian_internal:
  backend_roles:
    - "guardian_internal_role"
  users: []
  hosts: []
  # Service account only - no direct user login
```

### internal_users.yml
```yaml
# Service account for internal plugin operations
guardian_service_account:
  hash: "$2a$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # example bcrypt hash for "secret"
  backend_roles:
    - "guardian_internal"
  attributes:
    plugin: "guardian"
    purpose: "internal-operations"
    version: "1.0.0"

# Administrative user (optional)
guardian_admin_user:
  hash: "$2a$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
  backend_roles:
    - "guardian_admin_role"
  attributes:
    plugin: "guardian"
    purpose: "administrator"
```

### securityconfig.yml (minimal)
```yaml
config:
  dynamic:
    authc:
      internal_user_database:
        enabled: true
        http_enabled: true
        transport_enabled: true
        order: 0
        http_authenticator:
          type: basic
          challenge: false
        authentication_backend:
          type: internal
    authz:
      roles_from_internal:
        enabled: true
    audit:
      enabled: true
      volume: 64
```