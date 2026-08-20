# Administrator Guide

## Overview
This guide covers the administration of the OpenSearch Guardian plugin, including installation, configuration, monitoring, and maintenance procedures.

## Installation

### Prerequisites
- OpenSearch 2.11.0 or later
- OpenSearch Security plugin (for RBAC)
- Java 11+ runtime
- Sufficient disk space for plugin and collected data

### Backend Plugin Installation

#### From Release Artifact
```bash
# Download the plugin ZIP from GitHub Releases
wget https://github.com/opensearch-guardian/opensearch-guardian/releases/download/v1.0.0/guardian-1.0.0.zip

# Install on each node
bin/opensearch-plugin install file:///path/to/guardian-1.0.0.zip

# Restart OpenSearch
systemctl restart opensearch
```

#### From Maven Central
```bash
# Add to opensearch.yml for plugin repository
plugins.repository.guardian: "https://repo1.maven.org/maven2/org/opensearch/guardian/guardian-plugin/"

# Install
bin/opensearch-plugin install guardian-plugin
```

### Frontend Plugin Installation (OpenSearch Dashboards)
```bash
# From OpenSearch Dashboards root
bin/opensearch-dashboards-plugin install file:///path/to/guardian-dashboards-1.0.0.zip

# Or from release
bin/opensearch-dashboards-plugin install https://github.com/opensearch-guardian/opensearch-guardian/releases/download/v1.0.0/guardian-dashboards-1.0.0.zip

# Restart Dashboards
systemctl restart opensearch-dashboards
```

### Verify Installation
```bash
# Check backend plugin
curl -X GET "localhost:9200/_guardian/cluster/health" -H "Authorization: Bearer <token>"

# Check plugin list
bin/opensearch-plugin list | grep guardian
```

## Configuration

### Cluster Settings (Dynamic)
All Guardian settings can be updated dynamically via cluster settings API:

```bash
# Enable/disable collection
curl -X PUT "localhost:9200/_cluster/settings" -H "Content-Type: application/json" -d '{
  "persistent": {
    "guardian.collection.enabled": true
  }
}'

# Configure collection intervals (ADR-005 tiered cadence)
curl -X PUT "localhost:9200/_cluster/settings" -H "Content-Type: application/json" -d '{
  "persistent": {
    "guardian.collection.tier1.interval": "5s",
    "guardian.collection.tier2.interval": "12s",
    "guardian.collection.tier3.interval": "45s",
    "guardian.collection.tier4.interval": "5m"
  }
}'

# Enable diagnosis
curl -X PUT "localhost:9200/_cluster/settings" -H "Content-Type: application/json" -d '{
  "persistent": {
    "guardian.diagnosis.enabled": true,
    "guardian.doctor.schedule": "0 */6 * * *"
  }
}'

# Enable optimization
curl -X PUT "localhost:9200/_cluster/settings" -H "Content-Type: application/json" -d '{
  "persistent": {
    "guardian.optimization.enabled": true
  }
}'
```

### Static Settings (opensearch.yml)
Settings that require node restart:

```yaml
# Plugin settings
guardian.collection.enabled: true
guardian.diagnosis.enabled: true
guardian.optimization.enabled: true
guardian.provisioning.enabled: true

# Keystore settings (for credentials)
# Store in OpenSearch keystore:
# bin/opensearch-keystore add guardian.aws.access_key
# bin/opensearch-keystore add guardian.aws.secret_key
```

### Security Configuration

#### Role Definitions
Create roles in OpenSearch Security:

```json
# guardian_monitor role (read-only)
{
  "cluster_permissions": ["cluster:monitor/main", "cluster:monitor/health"],
  "index_permissions": [{
    "index_patterns": ["*"],
    "allowed_actions": ["indices:monitor/stats", "indices:monitor/health"]
  }],
  "tenant_permissions": [{
    "tenant_patterns": ["*"],
    "allowed_actions": ["kibana_all_read"]
  }]
}

# guardian_manager role (read + manage)
{
  "cluster_permissions": ["cluster:monitor/*", "cluster:admin/*"],
  "index_permissions": [{
    "index_patterns": ["*"],
    "allowed_actions": ["indices:*"]
  }],
  "tenant_permissions": [{
    "tenant_patterns": ["*"],
    "allowed_actions": ["kibana_all_write"]
  }]
}
```

#### Map Roles to Users
```bash
# Via securityadmin.sh or REST API
curl -X PUT "localhost:9200/_plugins/_security/api/rolesmapping/guardian_monitor" \
  -H "Content-Type: application/json" \
  -d '{"backend_roles": ["guardian-monitor-group"]}'
```

### Keystore Integration
Store sensitive credentials in OpenSearch keystore:

```bash
# AWS credentials for provisioning
bin/opensearch-keystore add guardian.aws.access_key
bin/opensearch-keystore add guardian.aws.secret_key
bin/opensearch-keystore add guardian.aws.region

# Kubernetes credentials
bin/opensearch-keystore add guardian.k8s.config

# Docker registry
bin/opensearch-keystore add guardian.docker.username
bin/opensearch-keystore add guardian.docker.password
```

## Monitoring

### Health Endpoints
```bash
# Overall cluster health
GET /_guardian/cluster/health

# Node-level details
GET /_guardian/cluster/nodes

# Collection status
GET /_guardian/collection/status

# Diagnosis status
GET /_guardian/doctor/status
```

### Key Metrics (Prometheus/OpenTelemetry)
| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `guardian_collection_duration_seconds` | Collection execution time | > 30s |
| `guardian_collection_errors_total` | Collection error count | > 0 |
| `guardian_doctor_findings_total` | Findings by severity | critical > 0 |
| `guardian_optimizer_recommendations_total` | Optimization recommendations | N/A |
| `guardian_provisioning_operations_total` | Provisioning operations | failed > 0 |

### Logs
Guardian logs to standard OpenSearch log files:
- `logs/opensearch.log` - General plugin logs
- `logs/opensearch_index_indexing_slowlog.log` - Slow collection operations
- `logs/opensearch_index_search_slowlog.log` - Slow diagnosis queries

Enable debug logging:
```bash
curl -X PUT "localhost:9200/_cluster/settings" -H "Content-Type: application/json" -d '{
  "transient": {
    "logger.org.opensearch.guardian": "DEBUG"
  }
}'
```

## Maintenance

### Regular Tasks

#### Daily
- Verify collection is running: `GET /_guardian/collection/status`
- Check for critical findings: `GET /_guardian/doctor/findings?severity=critical`
- Monitor disk usage on data nodes

#### Weekly
- Review optimization recommendations: `GET /_guardian/optimize`
- Check provisioning operation status
- Verify SBOM and security scan results in CI

#### Monthly
- Update plugin to latest version
- Review and update retention policies
- Audit security roles and permissions
- Rotate keystore credentials

### Backup and Restore

#### Backup Guardian Data
```bash
# Snapshot Guardian indices
curl -X PUT "localhost:9200/_snapshot/guardian_backup/snapshot_$(date +%Y%m%d)" \
  -H "Content-Type: application/json" \
  -d '{
    "indices": "guardian-*",
    "ignore_unavailable": true,
    "include_global_state": false
  }'
```

#### Restore Guardian Data
```bash
# List snapshots
curl -X GET "localhost:9200/_snapshot/guardian_backup/_all"

# Restore
curl -X POST "localhost:9200/_snapshot/guardian_backup/snapshot_20240115/_restore" \
  -H "Content-Type: application/json" \
  -d '{"indices": "guardian-*"}'
```

### Upgrade Procedure

#### Rolling Upgrade (Zero Downtime)
1. Download new plugin version
2. Install on one node at a time:
   ```bash
   bin/opensearch-plugin remove guardian
   bin/opensearch-plugin install file:///path/to/guardian-new.zip
   systemctl restart opensearch
   ```
3. Verify plugin loads: `bin/opensearch-plugin list`
4. Check cluster health before proceeding to next node

#### Dashboards Plugin Upgrade
```bash
bin/opensearch-dashboards-plugin remove guardian
bin/opensearch-dashboards-plugin install file:///path/to/guardian-dashboards-new.zip
systemctl restart opensearch-dashboards
```

### Troubleshooting

#### Plugin Won't Load
1. Check OpenSearch logs: `grep -i guardian logs/opensearch.log`
2. Verify Java version compatibility
3. Check plugin descriptor: `opensearch-plugin.properties`
4. Ensure all dependencies in plugin ZIP

#### Collection Not Running
1. Check `guardian.collection.enabled` setting
2. Verify thread pool capacity
3. Check for errors in logs
4. Verify keystore credentials for external connections

#### Permission Errors
1. Verify user roles in OpenSearch Security
2. Check `plugin-security.policy` permissions
3. Ensure REST endpoints registered correctly

#### Performance Issues
1. Reduce collection frequency if needed
2. Check circuit breaker settings
3. Monitor JVM heap on data nodes
4. Consider dedicated coordinating nodes

## Advanced Configuration

### Custom Rules
Add custom diagnostic rules by implementing the `Rule` interface and registering via SPI.

### External Integrations
Configure webhook notifications for findings:
```yaml
guardian.notifications.webhook.url: "https://alerts.example.com/webhook"
guardian.notifications.webhook.severity: "high"
```

### Multi-Cluster Management
Guardian supports managing multiple clusters from a single installation:
```yaml
guardian.clusters:
  - id: "production"
    endpoints: ["https://prod-es:9200"]
    credentials: "keystore:guardian.prod"
  - id: "staging"
    endpoints: ["https://staging-es:9200"]
    credentials: "keystore:guardian.staging"
```

## Security Hardening

### Network
- Restrict OpenSearch transport port (9300) to cluster nodes only
- Use TLS for all HTTP communication
- Configure firewall rules for Dashboards access

### Access Control
- Use least-privilege roles
- Audit role assignments quarterly
- Rotate keystore credentials monthly
- Enable audit logging in OpenSearch Security

### Compliance
- Regular SBOM generation and review
- Dependency vulnerability scanning in CI
- License compliance verification

## Related Documentation
- [Installation Guide](../operations/quickstart.md)
- [User Guide](../operations/user-guide.md)
- [Security Integration](../research/opensearch-security-integration.md)
- [Plugin Development Guide](../plugins/backend-plugin-development.md)