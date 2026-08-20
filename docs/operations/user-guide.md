# User Guide

## Overview
OpenSearch Guardian is a comprehensive monitoring, diagnosis, optimization, and provisioning plugin for OpenSearch. This guide covers how to use the Guardian features through the OpenSearch Dashboards UI and REST API.

## Getting Started

### Accessing Guardian
1. Open OpenSearch Dashboards
2. Navigate to **Guardian** in the left navigation menu
3. You'll see the Guardian Overview dashboard

### Required Permissions
- **Monitor**: `guardian_monitor` role - View dashboards, run diagnoses
- **Manage**: `guardian_manager` role - All monitor permissions plus provisioning, configuration changes

## Dashboard Overview

### Guardian Overview
The main dashboard provides:
- Cluster health status (green/yellow/red)
- Node count and status
- Critical findings summary
- Quick action buttons

### Navigation Tabs
| Tab | Description |
|-----|-------------|
| Overview | Cluster health, nodes, key metrics |
| Doctor | Run diagnoses, view findings |
| Optimizer | View optimization recommendations |
| Provisioning | Manage cluster changes |

## Running a Diagnosis

### Quick Diagnosis
1. Go to **Doctor** tab
2. Click **Run Diagnosis**
3. Wait for results (typically 10-30 seconds)
4. Review findings table

### Targeted Diagnosis
1. Go to **Doctor** tab
2. Select specific rules from the checklist
3. Choose target cluster (if multi-cluster)
4. Click **Run Selected Rules**

### Interpreting Findings

#### Finding Severity
- **Critical** 🔴 - Immediate action required
- **High** 🟠 - Action needed within 1 hour
- **Medium** 🟡 - Schedule for maintenance window
- **Low** 🟢 - Optional improvements
- **Info** 🔵 - Informational only

#### Finding Actions
| Action | Description |
|--------|-------------|
| View Details | Click finding row for full evidence |
| Remediation | Follow guidance in finding details |
| Provisioning | Generate provisioning plan (if applicable) |
| Acknowledge | Mark as reviewed (requires manager role) |

### Scheduling Diagnoses
1. Go to **Doctor** → **Settings**
2. Enable **Scheduled Diagnoses**
3. Set cron schedule (e.g., `0 */6 * * *` for every 6 hours)
4. Select default rule set
5. Save

## Optimization Recommendations

### Viewing Recommendations
1. Go to **Optimizer** tab
2. Select recommendation type:
   - **Retention** - Index lifecycle policies
   - **Storage** - Compression, force merge
   - **Shard** - Shard count optimization
   - **Replica** - Replica count adjustments
   - **Mapping** - Field mapping improvements
   - **Capacity** - Capacity planning projections

### Understanding Savings
Each recommendation shows:
- **Estimated Savings**: Monthly cost reduction
- **Impact**: Performance/availability impact
- **Effort**: Implementation complexity
- **Risk**: Safety level (safe/caution/dangerous)

### Applying Recommendations
1. Click recommendation to view details
2. Review dry-run results
3. Click **Create Provisioning Plan**
4. Review and approve in Provisioning tab

## Provisioning Workflow

### Overview
The provisioning engine safely applies cluster changes with:
- Pre-flight checks
- Dry-run simulation
- Audit trail
- Rollback capability

### Creating a Plan
1. Go to **Provisioning** tab
2. Click **Create Plan**
3. Select operation type:
   - Scale cluster (add/remove nodes)
   - Change index settings
   - Update ILM policies
   - Modify shard allocation
4. Configure parameters
5. Click **Generate Plan**

### Plan Review
The plan shows:
- Step-by-step operations
- Pre-flight check results
- Estimated duration
- Risk assessment
- Rollback steps

### Execution
1. Review plan thoroughly
2. Click **Dry Run** to simulate
3. Verify no errors in dry-run output
4. Click **Execute** (requires manager role)
4. Monitor progress in real-time

### Operation Status
Track operations:
- **Pending** - Waiting for approval
- **Running** - In progress
- **Completed** - Success
- **Failed** - Error occurred
- **Rolled Back** - Reverted

## Cluster Management

### Viewing Cluster Details
**Overview** tab shows:
- Health status with details
- Node list with roles, disk, heap
- Index count and size
- Shard distribution

### Node Operations
From **Overview** → **Nodes**:
- View node details (click node)
- Decommission node (manager only)
- Restart node (manager only)
- View node-specific metrics

### Index Management
From **Overview** → **Indices**:
- Filter by size, age, health
- View index details
- Apply ILM policies
- Force merge (read-only indices)

## Alerting and Notifications

### Configuring Alerts
1. Go to **Settings** → **Notifications**
2. Add webhook URL (Slack, PagerDuty, etc.)
3. Select severity thresholds
4. Test notification

### Alert Types
- Critical findings detected
- Diagnosis failures
- Provisioning operation status
- Collection failures
- Optimization savings opportunities

## Multi-Cluster Management

### Adding Clusters
1. Go to **Settings** → **Clusters**
2. Click **Add Cluster**
3. Provide:
   - Cluster ID
   - Endpoint URLs
   - Credentials (stored in keystore)
4. Test connection

### Switching Clusters
Use cluster selector in top navigation to switch between managed clusters.

## Best Practices

### Daily Operations
- Check Overview dashboard each morning
- Review overnight findings
- Monitor provisioning operations

### Weekly Operations
- Run full diagnosis manually
- Review optimization recommendations
- Check capacity projections

### Monthly Operations
- Review and update retention policies
- Audit user permissions
- Update plugin if new version available

## Troubleshooting

### Common Issues

#### "No data available" on Dashboard
- Verify collection is enabled: `GET /_guardian/collection/status`
- Check cluster connectivity
- Verify permissions

#### Diagnosis Fails
- Check OpenSearch logs
- Verify rule configurations
- Try running individual rules

#### Provisioning Stuck
- Check operation status: `GET /_guardian/provision/{id}/status`
- Review pre-flight check failures
- Manual rollback if needed

#### Slow Dashboard Loading
- Reduce time range in filters
- Clear browser cache
- Check OpenSearch Dashboards performance

## Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| `G` `D` | Go to Doctor tab |
| `G` `O` | Go to Optimizer tab |
| `G` `P` | Go to Provisioning tab |
| `R` | Refresh current view |
| `?` | Show help |

## API Reference
For programmatic access, see [API Documentation](../API.md).

## Related Documentation
- [Admin Guide](../operations/admin-guide.md)
- [Quickstart Guide](../operations/quickstart.md)
- [Doctor Runbook](../operations/doctor-runbook.md)
- [Plugin Development Guide](../plugins/backend-plugin-development.md)