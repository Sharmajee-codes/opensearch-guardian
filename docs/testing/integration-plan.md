# Integration Test Plan — OpenSearch Guardian

## Overview
This document defines the integration test strategy for OpenSearch Guardian, covering cross-component testing between Python backend, OpenSearch Java plugin, and Dashboards frontend plugin.

## Test Scope

### In Scope
- Python backend ↔ OpenSearch cluster communication
- Java backend plugin ↔ OpenSearch cluster integration
- Frontend Dashboards plugin ↔ Backend plugin REST API
- Security plugin RBAC enforcement
- Collection pipeline end-to-end
- Diagnosis engine execution
- Provisioning workflow validation

### Out of Scope
- Unit tests (covered in strategy.md)
- Performance/load testing (separate plan)
- Chaos engineering (separate plan)
- Contract testing (Consumer-Driven Contracts)

## Test Environments

### Local Development
```bash
# Start OpenSearch with Security plugin
docker-compose -f docker-compose.test.yml up -d

# Install Guardian plugin
bin/opensearch-plugin install file:///path/to/guardian.zip
```

### CI Environment
- GitHub Actions ubuntu-latest
- Service containers: OpenSearch 2.14.0 + Security plugin
- Test matrix: Multiple OpenSearch versions (2.11, 2.12, 2.13, 2.14, 2.15)

## Test Categories

### 1. Python Backend ↔ OpenSearch Integration
**Location:** `tests/integration/test_connections/`

| Test | Description | Priority |
|------|-------------|----------|
| Connection health | Basic connectivity, auth, TLS | Critical |
| Cluster health API | GET /_cluster/health parsing | Critical |
| Node stats API | GET /_nodes/stats collection | Critical |
| Index stats API | GET /_stats parsing | High |
| ILM policy API | GET /_ilm/policy retrieval | Medium |
| Snapshot API | GET /_snapshot/* operations | Medium |
| Template API | GET /_template/* retrieval | Medium |

### 2. Java Backend Plugin ↔ OpenSearch Integration
**Location:** `backend/src/test/java/.../IntegTest.java`

| Test | Description | Priority |
|------|-------------|----------|
| Plugin lifecycle | Load/unload, settings, health | Critical |
| REST endpoints | All /_guardian/* endpoints | Critical |
| Transport actions | Custom actions execution | Critical |
| Collector service | Tiered collection execution | High |
| Diagnosis service | Rule engine execution | High |
| Provisioning service | Preflight-apply-verify-audit | High |
| Security permissions | RBAC enforcement on endpoints | Critical |
| Tenant isolation | Multi-tenant data separation | Medium |

### 3. Frontend ↔ Backend Plugin Integration
**Location:** `frontend/src/plugins/guardian/test/integration/`

| Test | Description | Priority |
|------|-------------|----------|
| Auth flow | Security plugin session, tenant | Critical |
| Cluster health page | Data fetching, display | Critical |
| Diagnosis console | Run diagnosis, show findings | Critical |
| Optimizer view | Display recommendations | High |
| Provisioning wizard | Full workflow execution | Critical |
| Audit log view | Display audit entries | Medium |
| Error handling | 401, 403, 500 responses | High |

## Test Data & Fixtures

### OpenSearch Test Cluster Setup
```yaml
# docker-compose.test.yml
services:
  opensearch:
    image: opensearchproject/opensearch:2.14.0
    environment:
      - discovery.type=single-node
      - plugins.security.disabled=false
      - DISABLE_SECURITY_PLUGIN=false
    ports:
      - "9200:9200"
      - "9600:9600"
    volumes:
      - test-data:/usr/share/opensearch/data
```

### Security Configuration for Tests
```yaml
# securityconfig.yml (test)
config:
  dynamic:
    authc:
      internal_user_database:
        enabled: true
        order: 0
    authz:
      roles_from_myldap:
        enabled: false
    audit:
      enabled: true
```

### Test Users
| User | Backend Role | Purpose |
|------|--------------|---------|
| monitor_user | guardian_monitoring_role | Read-only cluster monitoring |
| doctor_user | guardian_doctor_role | Diagnosis operations |
| optimizer_user | guardian_optimizer_role | Optimization operations |
| admin_user | guardian_admin_role | Provisioning/admin |
| guardian_service | guardian_internal_role | Internal service account |

## Test Execution

### Local Integration Test Run
```bash
# 1. Start test cluster
docker-compose -f docker-compose.test.yml up -d
sleep 30  # Wait for OpenSearch + Security init

# 2. Install Guardian plugin
cd backend && ./gradlew buildPluginZip
bin/opensearch-plugin install file:///path/to/guardian.zip

# 3. Run Python integration tests
cd ../..
uv run python -m pytest tests/integration -v --tb=short

# 4. Run Java integration tests
cd backend && ./gradlew integrationTest

# 5. Run Frontend integration tests
cd ../frontend/src/plugins/guardian
npm test -- --testPathPattern=integration
```

### CI Integration Test Run
```yaml
# .github/workflows/opensearch-plugin-ci.yml
integration-test:
  runs-on: ubuntu-latest
  services:
    opensearch:
      image: opensearchproject/opensearch:2.14.0
      env:
        discovery.type: single-node
        plugins.security.disabled: "false"
      ports:
        - 9200:9200
      options: >-
        --health-cmd="curl -f http://localhost:9200/_cluster/health"
        --health-interval=10s
        --health-timeout=5s
        --health-retries=10
  steps:
    - uses: actions/checkout@v4
    - name: Run Python integration tests
      run: uv run python -m pytest tests/integration -v
    - name: Run Java integration tests
      run: cd backend && ./gradlew integrationTest
    - name: Run Frontend integration tests
      run: cd frontend/src/plugins/guardian && npm test -- --testPathPattern=integration
```

## Test Cases Detail

### TC-INT-001: Cluster Health Collection
**Preconditions:** OpenSearch cluster green, Guardian plugin installed
**Steps:**
1. Call GET /_guardian/cluster/health
2. Verify response matches OpenSearch _cluster/health structure
3. Verify status field present (green/yellow/red)
**Expected:** 200 OK, valid health response

### TC-INT-002: Tiered Collection Execution
**Preconditions:** Plugin running, collection enabled
**Steps:**
1. Start collection via POST /_guardian/collection/start
2. Wait for T1 (5s), T2 (12s), T3 (45s), T4 (5min) intervals
3. Verify snapshots stored in .guardian-snapshots index
4. Stop collection via POST /_guardian/collection/stop
**Expected:** Snapshots created at each tier interval

### TC-INT-003: Diagnosis Engine Execution
**Preconditions:** Collection snapshots available
**Steps:**
1. Call POST /_guardian/diagnose
2. Verify findings returned with severity and safety level
3. Verify rule IDs match known rules
**Expected:** 200 OK, array of findings with required fields

### TC-INT-004: Provisioning Workflow
**Preconditions:** Admin user authenticated
**Steps:**
1. Call POST /_guardian/provision/dry-run with valid config
2. Verify dry-run response shows changes
3. Call POST /_guardian/provision with same config
4. Verify changes applied (index settings, ILM, etc.)
5. Call GET /_guardian/provision/audit
6. Verify audit entry created
**Expected:** Dry-run shows changes, apply succeeds, audit recorded

### TC-INT-005: RBAC Enforcement - Monitor Role
**Preconditions:** monitor_user credentials
**Steps:**
1. Authenticate as monitor_user
2. Call GET /_guardian/cluster/health
3. Call POST /_guardian/provision
**Expected:** Step 2 = 200 OK, Step 3 = 403 Forbidden

### TC-INT-006: RBAC Enforcement - Admin Role
**Preconditions:** admin_user credentials
**Steps:**
1. Authenticate as admin_user
2. Call GET /_guardian/cluster/health
3. Call POST /_guardian/provision
**Expected:** Both = 200 OK

### TC-INT-007: Frontend Dashboard Data Flow
**Preconditions:** OpenSearch Dashboards running, Guardian plugin installed
**Steps:**
1. Login as monitor_user in Dashboards
2. Navigate to Guardian → Monitoring
3. Verify cluster health data loads
4. Navigate to Guardian → Diagnosis
4. Run diagnosis, verify findings display
**Expected:** UI loads data from backend plugin, displays correctly

### TC-INT-008: Frontend Provisioning Wizard
**Preconditions:** OpenSearch Dashboards, admin_user
**Steps:**
1. Login as admin_user
2. Navigate to Guardian → Provisioning
3. Complete wizard steps 1-4
4. Verify audit log shows entry
**Expected:** Wizard completes, audit entry created

### TC-INT-009: Tenant Isolation
**Preconditions:** Multi-tenant OpenSearch Security configured
**Steps:**
1. Create tenant A with data
2. Create tenant B with different data
3. Authenticate as tenant A user
4. Call GET /_guardian/cluster/health?tenant=A
5. Verify only tenant A data returned
6. Repeat for tenant B
**Expected:** Data isolation per tenant

### TC-INT-010: Audit Logging
**Preconditions:** Security audit enabled
**Steps:**
1. Perform various Guardian operations
2. Query security-audit-log-* index
3. Verify audit entries for each operation
4. Verify user, action, timestamp present
**Expected:** All operations audited with required fields

## Test Dependencies

### Required Services
- OpenSearch 2.11+ with Security plugin
- OpenSearch Dashboards 2.11+ with Security Dashboards plugin
- Network connectivity between components

### Required Configuration
- `roles.yml`, `roles_mapping.yml`, `internal_users.yml` loaded
- `securityconfig.yml` applied
- Guardian plugin installed and enabled

## Test Reporting

### Coverage Targets
| Component | Target |
|-----------|--------|
| Python integration | 100% critical paths |
| Java integration | 100% REST endpoints |
| Frontend integration | 100% API interactions |
| RBAC enforcement | 100% role/permission combos |

### Report Artifacts
- JUnit XML (Python, Java)
- Jest coverage (Frontend)
- HTML reports (JaCoCo, pytest-html)
- CI dashboard summary

## Failure Handling

### Flaky Test Policy
1. Rerun up to 3 times on failure
2. Mark as flaky if passes on retry
3. Create GitHub issue for flaky test
4. Fix within 1 sprint

### Infrastructure Failures
- OpenSearch container startup timeout → Retry with longer wait
- Security plugin init failure → Check securityconfig.yml
- Plugin install failure → Check plugin-descriptor.properties

## Related Documentation
- [Test Strategy](strategy.md)
- [Test Runbook](test-runbook.md)
- [Backend Plugin Development](../plugins/backend-plugin-development.md)
- [Frontend Plugin Development](../plugins/frontend-plugin-development.md)
- [Migration Guide](../plugins/migration-guide.md)
- [Release Automation](../plugins/release-automation.md)