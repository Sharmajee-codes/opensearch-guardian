# OpenSearch Guardian Backend Plugin Development Guide

## Overview
This guide covers developing the OpenSearch Guardian backend plugin — a native OpenSearch plugin that provides monitoring, diagnosis, optimization, and provisioning capabilities.

## Plugin Architecture

### Plugin Entry Point
The main plugin class extends `org.opensearch.plugins.Plugin` and implements the SPI:

```java
package org.opensearch.guardian;

import org.opensearch.common.settings.Setting;
import org.opensearch.common.settings.Settings;
import org.opensearch.common.unit.TimeValue;
import org.opensearch.plugins.ActionPlugin;
import org.opensearch.plugins.Plugin;
import org.opensearch.plugins.RestPlugin;
import org.opensearch.rest.RestHandler;
import org.opensearch.action.Action;
import org.opensearch.cluster.service.ClusterService;
import org.opensearch.threadpool.ThreadPool;

import java.util.Arrays;
import java.util.List;
import java.util.function.Supplier;

/**
 * Main plugin entry point for OpenSearch Guardian.
 * Implements ActionPlugin and RestPlugin SPI interfaces.
 * Follows OpenSearch plugin best practices.
 */
public class GuardianPlugin extends Plugin implements ActionPlugin, RestPlugin {

    // Plugin settings
    public static final Setting<Boolean> ENABLED = Setting.boolSetting(
        "guardian.enabled", true, Setting.Property.NodeScope
    );
    public static final Setting<TimeValue> COLLECTION_INTERVAL = Setting.timeSetting(
        "guardian.collection.interval", TimeValue.timeValueSeconds(30),
        Setting.Property.NodeScope
    );
    public static final Setting<Integer> MAX_CONCURRENT_COLLECTIONS = Setting.intSetting(
        "guardian.max.concurrent.collections", 10, 1, 100, Setting.Property.NodeScope
    );

    public GuardianPlugin(Settings settings) {
        // Register settings
        super(settings);
    }

    @Override
    public List<Setting<?>> getSettings() {
        return Arrays.asList(ENABLED, COLLECTION_INTERVAL, MAX_CONCURRENT_COLLECTIONS);
    }

    @Override
    public List<RestHandler> getRestHandlers(Settings settings, org.opensearch.rest.RestController controller,
                                             org.opensearch.cluster.ClusterSettings clusterSettings,
                                             org.opensearch.index.IndexNameExpressionResolver resolver,
                                             Supplier<org.opensearch.cluster.node.DiscoveryNodes> nodesSupplier,
                                             org.opensearch.common.io.NamedWriteableRegistry registry,
                                             Supplier<org.opensearch.script.ScriptService> scriptService) {
        // Check if plugin is enabled
        if (!ENABLED.get(settings)) {
            return List.of();
        }

        // REST handlers will be instantiated via DI, return empty list for now
        // Actual handlers are registered via module bindings
        return List.of();
    }

    @Override
    public List<Action<?>> getActions() {
        return List.of(
            GuardianStartCollectionAction.INSTANCE,
            GuardianStopCollectionAction.INSTANCE,
            GuardianGetStatusAction.INSTANCE
        );
    }
}
```

### Plugin Descriptor
Create `plugin-descriptor.properties` in `src/main/resources`:

```properties
opensearch.plugin.class=org.opensearch.guardian.GuardianPlugin
opensearch.plugin.name=guardian
opensearch.plugin.version=1.0.0
opensearch.plugin.description=OpenSearch Guardian - Monitoring, Diagnosis, Optimization, and Provisioning
opensearch.plugin.java.version=11
opensearch.plugin.minimum_snapshot_version=2.11.0
opensearch.plugin.minimum_compatible_version=2.11.0
```

## Service Implementation

### Base Service Pattern
Each service follows this pattern:

```java
package org.opensearch.guardian.service;

import org.opensearch.cluster.service.ClusterService;
import org.opensearch.common.settings.Settings;
import org.opensearch.threadpool.ThreadPool;

public class GuardianService {
    protected final Settings settings;
    protected final ClusterService clusterService;
    protected final ThreadPool threadPool;
    
    public GuardianService(Settings settings, 
                          ClusterService clusterService,
                          ThreadPool threadPool) {
        this.settings = settings;
        this.clusterService = clusterService;
        this.threadPool = threadPool;
    }
}
```

### Collector Service
Implements tiered collection strategy (ADR-005):

```java
package org.opensearch.guardian.service;

public class CollectorService extends GuardianService {
    
    private final Map<String, ScheduledFuture<?>> collectionTasks = new ConcurrentHashMap<>();
    
    public void startCollection() {
        // Tier 1: Live (~5s) - Cluster health, node status
        scheduleCollection("t1-live", Duration.ofSeconds(5), this::collectTier1);
        
        // Tier 2: Trending (~10-15s) - Node stats, shard state
        scheduleCollection("t2-trending", Duration.ofSeconds(12), this::collectTier2);
        
        // Tier 3: Deep (~30-60s) - Index stats, settings
        scheduleCollection("t3-deep", Duration.ofSeconds(45), this::collectTier3);
        
        // Tier 4: Diagnostic (~5min) - Mappings, ILM, allocation
        scheduleCollection("t4-diagnostic", Duration.ofMinutes(5), this::collectTier4);
    }
    
    private void collectTier1() {
        // Cluster health, node status
    }
    
    private void collectTier2() {
        // Node stats, shard state
    }
    
    private void collectTier3() {
        // Index stats, cluster settings
    }
    
    private void collectTier4() {
        // Mappings, ILM policies, allocation explain
    }
}
```

### Diagnosis Service
Executes rules against collected snapshots:

```java
package org.opensearch.guardian.service;

import org.opensearch.guardian.model.*;
import org.opensearch.guardian.rules.*;

public class DiagnosisService extends GuardianService {
    
    private final List<Rule> rules;
    
    public DiagnosisService(Settings settings, 
                           ClusterService clusterService,
                           ThreadPool threadPool,
                           List<Rule> rules) {
        super(settings, clusterService, threadPool);
        this.rules = rules;
    }
    
    public DiagnosisResult diagnose(CollectionResult snapshot) {
        DiagnosisEngine engine = new DiagnosisEngine(rules);
        return engine.evaluate(snapshot);
    }
    
    public List<Finding> runRule(String ruleId, CollectionResult snapshot) {
        Rule rule = findRule(ruleId);
        return rule.evaluate(snapshot, RuleConfig.defaultConfig());
    }
}
```

### REST Actions
Expose functionality via REST API:

```java
package org.opensearch.guardian.rest;

import org.opensearch.rest.*;
import org.opensearch.client.node.NodeClient;

public class ClusterHealthRestAction extends BaseRestHandler {
    
    @Override
    public List<Route> routes() {
        return Arrays.asList(
            new Route(RestRequest.Method.GET, "/_guardian/cluster/health"),
            new Route(RestRequest.Method.GET, "/_guardian/cluster/health/{clusterId}")
        );
    }
    
    @Override
    protected RestChannelConsumer prepareRequest(RestRequest request, NodeClient client) {
        return channel -> {
            String clusterId = request.param("clusterId");
            GuardianHealthService service = GuardianPlugin.getInstance().getHealthService();
            
            if (clusterId != null) {
                service.getClusterHealth(clusterId, channel::sendResponse);
            } else {
                service.getAllClusterHealth(channel::sendResponse);
            }
        };
    }
}
```

## Build Configuration

### build.gradle
```groovy
plugins {
    id 'java'
    id 'maven-publish'
}

group = 'org.opensearch.guardian'
version = '1.0.0'

sourceCompatibility = JavaVersion.VERSION_11
targetCompatibility = JavaVersion.VERSION_11

repositories {
    mavenCentral()
    maven { url 'https://artifacts.opensearch.org/releases/' }
}

dependencies {
    implementation 'org.opensearch:opensearch:2.14.0'
    implementation 'org.opensearch:opensearch-core:2.14.0'
    implementation 'org.opensearch:opensearch-security:2.14.0'
    
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.0'
    testImplementation 'org.mockito:mockito-core:5.8.0'
    testImplementation 'org.opensearch:opensearch-test:2.14.0'
}

tasks.withType(JavaCompile) {
    options.encoding = 'UTF-8'
    options.compilerArgs << '-Xlint:unchecked' << '-Xlint:deprecation'
}

jar {
    manifest {
        attributes(
            'Built-By': System.getProperty('user.name'),
            'Build-Date': new Date().toString(),
            'OpenSearch-Plugin-Class': 'org.opensearch.guardian.GuardianPlugin'
        )
    }
}

task buildPluginZip(type: Zip) {
    from 'src/main/resources'
    from jar.archiveFile
    from configurations.runtimeClasspath
    archiveFileName = "guardian-${version}.zip"
    destinationDirectory = file("$buildDir/distributions")
}
```

## Security Integration

### Plugin Security Policy
Create `plugin-security.policy` in `src/main/resources`:

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

### Permission Classes
```java
package org.opensearch.guardian.security;

import java.security.BasicPermission;

public class ClusterReadPermission extends BasicPermission {
    public ClusterReadPermission() { super("cluster:read"); }
}

public class ClusterMonitorPermission extends BasicPermission {
    public ClusterMonitorPermission() { super("cluster:monitor"); }
}

public class ClusterManagePermission extends BasicPermission {
    public ClusterManagePermission() { super("cluster:manage"); }
}
```

### Checking Permissions in Services
```java
package org.opensearch.guardian.service;

import org.opensearch.guardian.security.*;

public class GuardianHealthService {
    
    public void getClusterHealth(RestChannel channel) {
        SecurityContext context = SecurityContext.getContext();
        
        if (!context.hasPermission(new ClusterReadPermission())) {
            throw new SecurityException("Insufficient permissions: cluster:read required");
        }
        
        // ... actual implementation
    }
}
```

### Role-Based Access Control (RBAC) Configuration

#### roles.yml
```yaml
# Guardian monitoring role (least privilege for T1-T3 collectors)
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

# Guardian diagnostic role (doctor operations)
guardian_doctor:
  cluster_permissions:
    - "cluster:monitor/*"
    - "cluster:admin/allocation/explain"
  index_permissions:
    - index_patterns: ["*"]
      allowed_actions:
        - "indices:monitor/*"
        - "indices:admin/get"
        - "indices:admin/mappings/fields/get"

# Guardian optimizer role
guardian_optimizer:
  cluster_permissions:
    - "cluster:monitor/*"
  index_permissions:
    - index_patterns: ["*"]
      allowed_actions:
        - "indices:monitor/*"
        - "indices:admin/get"
        - "indices:admin/settings/get"

# Guardian capacity planner role
guardian_capacity:
  cluster_permissions:
    - "cluster:monitor/*"
  index_permissions:
    - index_patterns: ["*"]
      allowed_actions:
        - "indices:monitor/*"
        - "indices:admin/get"

# Guardian admin role (provisioning)
guardian_admin:
  cluster_permissions:
    - "cluster:*"
    - "cluster:admin/plugin/guardian/*"
  index_permissions:
    - index_patterns: ["*"]
      allowed_actions: ["indices:*"]

# Guardian internal service account role
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

#### roles_mapping.yml
```yaml
guardian_monitoring:
  backend_roles:
    - "guardian_monitoring_role"
  users:
    - "guardian_user"
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
  users:
    - "guardian_admin"
  hosts: []

guardian_internal:
  backend_roles:
    - "guardian_internal_role"
  users: []
  hosts: []
```

#### internal_users.yml
```yaml
guardian_service_account:
  hash: "$2a$12$..."  # bcrypt hash
  backend_roles:
    - "guardian_internal"
  attributes:
    plugin: "guardian"
    purpose: "internal-operations"

guardian_admin_user:
  hash: "$2a$12$..."
  backend_roles:
    - "guardian_admin_role"
  attributes:
    plugin: "guardian"
    purpose: "administrator"
```

### Audit Logging Integration
Configure in `securityconfig.yml`:

```yaml
config:
  dynamic:
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
```

### Tenant-Aware Operations
For multi-tenant deployments, propagate tenant context:

```java
public class TenantAwareService {
    
    public DiagnosisResult diagnoseWithTenant(CollectionResult snapshot, String tenant) {
        // Set tenant context for OpenSearch Security
        SecurityContext context = SecurityContext.getContext();
        context.setTenant(tenant);
        
        try {
            return diagnose(snapshot);
        } finally {
            context.clearTenant();
        }
    }
}
```

## Testing

### Unit Test Example
```java
@ExtendWith(MockitoExtension.class)
class CollectorServiceTest {
    
    @Mock ClusterService clusterService;
    @Mock ThreadPool threadPool;
    @Mock Settings settings;
    
    CollectorService service;
    
    @BeforeEach
    void setUp() {
        service = new CollectorService(settings, clusterService, threadPool);
    }
    
    @Test
    void testTier1Collection() {
        service.startCollection();
        verify(threadPool).schedule(
            eq(ThreadPool.Names.GENERIC),
            any(Runnable.class),
            eq(Duration.ofSeconds(5))
        );
    }
}
```

### Integration Test
```java
@OpenSearchIntegTestCase.ClusterScope(scope = TEST, numDataNodes = 1)
class GuardianPluginIT extends OpenSearchIntegTestCase {
    
    @Test
    void testPluginLoads() throws Exception {
        assertTrue(internalCluster().getInstanceNames().contains("guardian"));
    }
    
    @Test
    void testHealthEndpoint() throws Exception {
        String response = executeRequest(
            Requests.GET, "/_guardian/cluster/health", Collections.emptyMap()
        );
        assertNotNull(response);
    }
}
```

### Security Integration Tests
```java
@OpenSearchIntegTestCase.ClusterScope(scope = TEST, numDataNodes = 1)
class GuardianSecurityIT extends OpenSearchIntegTestCase {
    
    @Test
    void testMonitorRoleCanAccessHealth() throws Exception {
        // Create user with guardian_monitoring role
        createUser("monitor_user", "guardian_monitoring_role");
        
        String response = executeRequest(
            Requests.GET, "/_guardian/cluster/health",
            Collections.singletonMap("Authorization", "Basic " + encode("monitor_user:password"))
        );
        assertNotNull(response);
        // Verify response contains health data
    }
    
    @Test
    void testMonitorRoleCannotProvision() throws Exception {
        createUser("monitor_user", "guardian_monitoring_role");
        
        String response = executeRequest(
            Requests.POST, "/_guardian/provision",
            Collections.singletonMap("Authorization", "Basic " + encode("monitor_user:password"))
        );
        assertEquals(403, getStatusCode(response));
    }
    
    @Test
    void testAdminRoleCanProvision() throws Exception {
        createUser("admin_user", "guardian_admin_role");
        
        String response = executeRequest(
            Requests.POST, "/_guardian/provision",
            Collections.singletonMap("Authorization", "Basic " + encode("admin_user:password"))
        );
        assertEquals(200, getStatusCode(response));
    }
}
```

## Configuration

### Plugin Settings
```java
public class GuardianSettings {
    
    public static final Setting<Boolean> COLLECTION_ENABLED = 
        Setting.boolSetting("guardian.collection.enabled", true, Property.Dynamic);
    
    public static final Setting<TimeValue> TIER1_INTERVAL = 
        Setting.timeSetting("guardian.collection.tier1.interval", "5s", Property.Dynamic);
    
    public static final Setting<TimeValue> TIER2_INTERVAL = 
        Setting.timeSetting("guardian.collection.tier2.interval", "12s", Property.Dynamic);
    
    public static final Setting<TimeValue> TIER3_INTERVAL = 
        Setting.timeSetting("guardian.collection.tier3.interval", "45s", Property.Dynamic);
    
    public static final Setting<TimeValue> TIER4_INTERVAL = 
        Setting.timeSetting("guardian.collection.tier4.interval", "5m", Property.Dynamic);
    
    public static final Setting<Boolean> DIAGNOSIS_ENABLED = 
        Setting.boolSetting("guardian.diagnosis.enabled", true, Property.Dynamic);
    
    public static final Setting<Boolean> OPTIMIZATION_ENABLED = 
        Setting.boolSetting("guardian.optimization.enabled", true, Property.Dynamic);
}
```

## Build and Install

### Build Plugin
```bash
./gradlew build buildPluginZip
```

Output: `build/distributions/guardian-1.0.0.zip`

### Install Plugin
```bash
# Install from local file
bin/opensearch-plugin install file:///path/to/guardian-1.0.0.zip

# Verify installation
bin/opensearch-plugin list

# Test endpoint
curl -X GET "localhost:9200/_guardian/cluster/health"
```

## Common Issues

### Plugin Not Loading
1. Check `plugin-descriptor.properties` has correct class name
2. Verify `opensearch.minimum_compatible_version` matches target OpenSearch version
3. Check OpenSearch logs for `Plugin load failed` errors

### ClassNotFoundException
1. Ensure all dependencies are included in plugin ZIP `lib/` directory
2. Check `build.gradle` includes all transitive dependencies

### Security Exceptions
1. Verify `plugin-security.policy` grants necessary permissions
2. Check OpenSearch security plugin logs for permission details
3. Ensure roles.yml and roles_mapping.yml are properly installed

### REST Endpoint Not Found
1. Ensure `RestPlugin` interface is implemented
2. Check routes are registered in `getRestHandlers()`
3. Verify endpoint path matches expected format

## Next Steps
- Implement [Frontend Plugin Development](./frontend-plugin-development.md)
- Set up [Release Automation](./release-automation.md)
- Review [Migration Guide](./migration-guide.md)