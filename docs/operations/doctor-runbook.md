# Doctor Runbook

## Overview
The OpenSearch Guardian Doctor is a diagnostic engine that evaluates cluster health, identifies issues, and provides remediation guidance. This runbook covers operational procedures for running, interpreting, and acting on Doctor diagnoses.

## Quick Reference

| Command | Description |
|---------|-------------|
| `GET /_guardian/doctor/run` | Run full diagnosis |
| `GET /_guardian/doctor/rules` | List all available rules |
| `GET /_guardian/doctor/findings` | Retrieve previous findings |
| `GET /_guardian/cluster/health` | Check cluster health |

## Running a Diagnosis

### Standard Diagnosis
```bash
curl -X GET "localhost:9200/_guardian/doctor/run" \
  -H "Authorization: Bearer <token>"
```

### Targeted Diagnosis (Specific Rules)
```bash
curl -X POST "localhost:9200/_guardian/doctor/run" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "ruleIds": ["cluster-health", "shard-allocation", "disk-usage"],
    "clusterId": "production-cluster"
  }'
```

### Using a Specific Snapshot
```bash
curl -X POST "localhost:9200/_guardian/doctor/run" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "snapshotId": "snapshot-2024-01-15T10:30:00Z",
    "clusterId": "production-cluster"
  }'
```

## Understanding Findings

### Finding Structure
```json
{
  "findingId": "uuid",
  "ruleId": "disk-usage",
  "ruleName": "Disk Usage Check",
  "severity": "critical|high|medium|low|info",
  "entityType": "node|index|cluster",
  "entityId": "node-1",
  "conditionDescription": "Disk usage at 92% on node-1",
  "remediationGuidance": "Add disk capacity or reduce index size",
  "safetyLevel": "safe|caution|dangerous",
  "confidence": 0.95,
  "timestamp": "2024-01-15T10:30:00Z",
  "evidence": {
    "diskUsagePercent": 92,
    "availableBytes": 10737418240
  }
}
```

### Severity Levels
| Severity | Meaning | Response Time |
|----------|---------|---------------|
| critical | Cluster at risk of data loss or outage | Immediate |
| high | Performance degradation likely | Within 1 hour |
| medium | Optimization opportunity | Within 24 hours |
| low | Minor improvement possible | Next maintenance window |
| info | Informational | As needed |

### Safety Levels
| Level | Description | Examples |
|-------|-------------|----------|
| safe | Read-only, no risk | Increasing replica count |
| caution | Potential performance impact | Rebalancing shards |
| dangerous | Data loss or downtime risk | Deleting indices, changing mappings |

## Common Diagnoses and Actions

### 1. Cluster Health Degraded (critical)
**Finding:** Cluster status is RED or YELLOW
**Actions:**
1. Check `GET /_cluster/health` for details
2. Identify unassigned shards: `GET /_cat/shards?v&h=index,shard,prirep,state,unassigned.reason`
3. Run allocation explain: `GET /_cluster/allocation/explain`
4. Restart affected nodes if needed
5. Check disk space on all nodes

### 2. High Disk Usage (critical/high)
**Finding:** Disk usage > 85% (high) or > 95% (critical)
**Actions:**
1. Identify largest indices: `GET /_cat/indices?v&h=index,store.size&s=store.size:desc`
2. Delete old indices per retention policy
3. Enable ILM rollover if not configured
4. Add disk capacity or new nodes
5. Consider force merge for read-only indices

### 3. Shard Allocation Issues (high)
**Finding:** Unassigned shards or allocation stuck
**Actions:**
1. Run allocation explain API
2. Check node disk watermarks
3. Verify shard allocation awareness settings
4. Restart node if persistent
5. Consider manual shard allocation

### 4. JVM Heap Pressure (high)
**Finding:** Heap usage > 75% sustained
**Actions:**
1. Check circuit breaker stats: `GET /_nodes/stats/breaker`
2. Reduce fielddata/cache sizes
3. Increase heap if < 50% of RAM
4. Optimize queries causing high memory
5. Consider adding data nodes

### 5. Slow Search/Latency (medium)
**Finding:** P99 latency > threshold
**Actions:**
1. Profile slow queries: `GET /_nodes/hot_threads`
2. Check for missing mappings/analyzers
3. Optimize index settings (shards, refresh_interval)
4. Consider search throttling
5. Add search-optimized nodes

## Automated Remediation

### Safe Auto-Remediation (safe level only)
Enable in `opensearch.yml`:
```yaml
guardian.doctor.auto_remediate: true
guardian.doctor.auto_remediate_safety: safe
```

### Manual Approval Required
For `caution` and `dangerous` findings, use the provisioning workflow:
```bash
# Dry run first
curl -X POST "localhost:9200/_guardian/provision/dry-run" \
  -H "Content-Type: application/json" \
  -d '{"planId": "remediation-plan-123"}'

# Execute after review
curl -X POST "localhost:9200/_guardian/provision" \
  -H "Content-Type: application/json" \
  -d '{"planId": "remediation-plan-123", "approvedBy": "admin-user"}'
```

## Scheduling Regular Diagnoses

### Via Cluster Settings (Dynamic)
```bash
curl -X PUT "localhost:9200/_cluster/settings" \
  -H "Content-Type: application/json" \
  -d '{
    "persistent": {
      "guardian.doctor.enabled": true,
      "guardian.doctor.schedule": "0 */6 * * *",  # Every 6 hours
      "guardian.doctor.default_rules": ["cluster-health", "disk-usage", "shard-allocation"]
    }
  }'
```

### Via Cron (External)
```bash
# Add to crontab for external scheduler
0 */6 * * * curl -X GET "https://opensearch:9200/_guardian/doctor/run" -H "Authorization: Bearer $TOKEN"
```

## Troubleshooting

### Doctor Returns No Findings
- Check if rules are enabled: `GET /_guardian/doctor/rules`
- Verify collection is running: `GET /_guardian/cluster/nodes`
- Check collection tier status in logs

### Diagnosis Times Out
- Reduce rule set: specify only critical rules
- Check cluster load during diagnosis
- Increase timeout in client settings

### Permission Denied
- Verify user has `guardian_monitor` or `guardian_manager` role
- Check OpenSearch Security plugin configuration
- Ensure REST endpoint permissions in `plugin-security.policy`

## Escalation Procedures

### Critical Findings Not Auto-Remediated
1. Page on-call engineer immediately
2. Run targeted diagnosis to confirm
3. Execute manual remediation steps
4. Document incident in runbook
5. Update rules if false positive

### Recurring Issues
1. Track finding frequency in Guardian audit log
2. Create GitHub issue for root cause analysis
3. Adjust collection cadence if needed
4. Consider adding custom rules

## Monitoring and Alerting

### Key Metrics to Alert On
- `guardian.doctor.findings.critical` > 0
- `guardian.doctor.findings.high` > 5
- `guardian.doctor.execution_time` > 300s
- `guardian.doctor.last_run_age` > 12h

### Grafana Dashboard
Import the Guardian Doctor dashboard (JSON in `docs/operations/dashboards/doctor.json`)

## Version Compatibility
| Guardian Version | OpenSearch Version | Notes |
|-----------------|-------------------|-------|
| 1.0.x | 2.11+ | Initial release |
| 1.1.x | 2.14+ | Enhanced rule engine |

## Related Documentation
- [Diagnostic Rules Reference](../architecture/doctor-rules.md)
- [Plugin Development Guide](../plugins/backend-plugin-development.md)
- [Security Integration](../research/opensearch-security-integration.md)
- [Provisioning Workflow](../architecture/connection-and-collection.md)