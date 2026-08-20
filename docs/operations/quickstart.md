# Quickstart Guide

## Overview
Get OpenSearch Guardian up and running in 5 minutes.

## Prerequisites
- OpenSearch 2.11+ cluster
- OpenSearch Dashboards 2.11+
- Admin access to both

## Installation

### 1. Install Backend Plugin
```bash
# On each OpenSearch node
wget https://github.com/opensearch-guardian/opensearch-guardian/releases/latest/download/guardian-plugin.zip
bin/opensearch-plugin install file:///path/to/guardian-plugin.zip
systemctl restart opensearch
```

### 2. Install Frontend Plugin
```bash
# On OpenSearch Dashboards
wget https://github.com/opensearch-guardian/opensearch-guardian/releases/latest/download/guardian-dashboards-plugin.zip
bin/opensearch-dashboards-plugin install file:///path/to/guardian-dashboards-plugin.zip
systemctl restart opensearch-dashboards
```

### 3. Verify Installation
```bash
# Check backend
curl -X GET "localhost:9200/_guardian/cluster/health"

# Check frontend
# Open Dashboards → Guardian menu should appear
```

## Initial Configuration

### 1. Create Security Roles (if using OpenSearch Security)
```bash
# Create guardian_monitor role
curl -X PUT "localhost:9200/_plugins/_security/api/roles/guardian_monitor" \
  -H "Content-Type: application/json" -d @guardian_monitor_role.json

# Create guardian_manager role
curl -X PUT "localhost:9200/_plugins/_security/api/roles/guardian_manager" \
  -H "Content-Type: application/json" -d @guardian_manager_role.json
```

### 2. Map Roles to Users
```bash
# Map to backend roles or users
curl -X PUT "localhost:9200/_plugins/_security/api/rolesmapping/guardian_monitor" \
  -H "Content-Type: application/json" -d '{"backend_roles": ["monitoring-team"]}'
```

### 3. Enable Collection
```bash
curl -X PUT "localhost:9200/_cluster/settings" -H "Content-Type: application/json" -d '{
  "persistent": {
    "guardian.collection.enabled": true,
    "guardian.diagnosis.enabled": true
  }
}'
```

## First Diagnosis

### Via Dashboards
1. Open OpenSearch Dashboards
2. Click **Guardian** in left menu
3. Go to **Doctor** tab
4. Click **Run Diagnosis**
5. Review findings

### Via API
```bash
# Run full diagnosis
curl -X GET "localhost:9200/_guardian/doctor/run" \
  -H "Authorization: Bearer <your-token>"

# View findings
curl -X GET "localhost:9200/_guardian/doctor/findings" \
  -H "Authorization: Bearer <your-token>"
```

## First Optimization

### Via Dashboards
1. Go to **Optimizer** tab
2. Review recommendations by category
3. Click any recommendation for details
4. Click **Create Provisioning Plan** to apply

### Via API
```bash
# Get all recommendations
curl -X GET "localhost:9200/_guardian/optimize" \
  -H "Authorization: Bearer <your-token>"

# Get specific type
curl -X GET "localhost:9200/_guardian/optimize?type=retention" \
  -H "Authorization: Bearer <your-token>"
```

## Next Steps

### Configure Scheduled Diagnoses
```bash
curl -X PUT "localhost:9200/_cluster/settings" -H "Content-Type: application/json" -d '{
  "persistent": {
    "guardian.doctor.schedule": "0 */6 * * *"
  }
}'
```

### Set Up Notifications
```bash
curl -X PUT "localhost:9200/_cluster/settings" -H "Content-Type: application/json" -d '{
  "persistent": {
    "guardian.notifications.webhook.url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    "guardian.notifications.webhook.severity": "high"
  }
}'
```

### Add Credentials for Provisioning (Optional)
```bash
# AWS for EC2 provisioning
bin/opensearch-keystore add guardian.aws.access_key
bin/opensearch-keystore add guardian.aws.secret_key
bin/opensearch-keystore add guardian.aws.region
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Plugin not found | Restart OpenSearch after install |
| Permission denied | Check security roles mapping |
| No data in dashboard | Wait 30s for first collection cycle |
| Diagnosis timeout | Run targeted rules instead |

## Resources
- [Admin Guide](admin-guide.md) - Detailed configuration
- [User Guide](user-guide.md) - Feature usage
- [Doctor Runbook](doctor-runbook.md) - Diagnosis procedures
- [API Reference](../API.md) - Programmatic access