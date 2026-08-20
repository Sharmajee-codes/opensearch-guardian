# OpenSearch Guardian API Reference

## Overview

This document provides a complete reference for the OpenSearch Guardian API, covering both the REST API (FastAPI) and the Streaming API (SSE/WebSocket). The API is organized around the core Guardian capabilities: cluster health monitoring, diagnostic rules execution, capacity planning, provisioning operations, and real-time streaming.

## Base URL

```
REST API:     http://<host>:<port>/api/v1
Streaming:    http://<host>:<port>/api/stream
Health Check: http://<host>:<port>/health
```

## Authentication

All API endpoints require authentication via Bearer token. The API implements role-based access control (RBAC) with three permission levels:

| Role | Description | Endpoints |
|------|-------------|-----------|
| `readonly` | Read-only cluster access | Doctor, Capacity, Streaming |
| `operator` | Read + diagnostic operations | All read + rule installation |
| `admin` | Full access including provisioning | All endpoints |

### Headers

```
Authorization: Bearer <token>
Content-Type: application/json
Accept: application/json
```

### Error Responses

All errors follow RFC 7807 Problem Details format:

```json
{
  "type": "https://tools.ietf.org/html/rfc7807",
  "title": "Error Title",
  "status": 403,
  "detail": "Human-readable error description",
  "instance": "/api/v1/doctor"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable (collector not active)

---

## Doctor API

### Run Diagnostic Rules

Execute all Doctor rules against the latest cluster snapshot.

**Endpoint:** `GET /api/v1/doctor`

**Permissions:** `cluster:read` (readonly, operator, admin)

**Response:**

```json
{
  "findings": [
    {
      "rule_id": "RULE-001",
      "name": "Cluster Health",
      "severity": "critical",
      "category": "cluster",
      "message": "Cluster status is RED",
      "details": {
        "cluster_status": "red",
        "unassigned_shards": 5
      },
      "safety_level": "informational",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "summary": {
    "total": 11,
    "critical": 1,
    "warning": 3,
    "info": 7
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Finding Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `rule_id` | string | Unique rule identifier |
| `name` | string | Human-readable rule name |
| `severity` | string | `critical`, `warning`, `info` |
| `category` | string | Rule category (`cluster`, `node`, `index`, `shard`) |
| `message` | string | Human-readable finding description |
| `details` | object | Rule-specific diagnostic data |
| `safety_level` | string | `informational`, `safe_reversible`, `approval_required`, `destructive` |
| `timestamp` | string | ISO 8601 timestamp |

---

### List All Doctor Rules

Retrieve metadata for all built-in diagnostic rules.

**Endpoint:** `GET /api/v1/doctor/rules`

**Permissions:** `cluster:read`

**Response:**

```json
{
  "rules": [
    {
      "id": "RULE-001",
      "name": "Cluster Health",
      "category": "cluster",
      "severity": "critical",
      "description": "Checks cluster health status",
      "configurable": false
    }
  ],
  "count": 11
}
```

---

### List Marketplace Rules

Retrieve rules available from the community marketplace.

**Endpoint:** `GET /api/v1/doctor/marketplace`

**Permissions:** `cluster:read`

**Response:**

```json
{
  "rules": [
    {
      "id": "custom-rule-001",
      "name": "Custom Heap Alert",
      "version": "1.0.0",
      "author": "community",
      "description": "Alerts when JVM heap exceeds threshold",
      "tags": ["jvm", "heap", "alerting"]
    }
  ],
  "count": 5
}
```

---

### Get Marketplace Rule Details

**Endpoint:** `GET /api/v1/doctor/marketplace/{rule_id}`

**Permissions:** `cluster:read`

---

### Install Marketplace Rule

Install a rule from the marketplace.

**Endpoint:** `POST /api/v1/doctor/marketplace/{rule_id}/install`

**Permissions:** `cluster:manage` (admin)

**Response:**

```json
{
  "rule_id": "custom-rule-001",
  "installed": true
}
```

---

### Uninstall Marketplace Rule

**Endpoint:** `POST /api/v1/doctor/marketplace/{rule_id}/uninstall`

**Permissions:** `cluster:manage` (admin)

---

### Run Single Rule

Execute a specific diagnostic rule by ID.

**Endpoint:** `POST /api/v1/doctor/rules/{rule_id}/run`

**Permissions:** `cluster:read`

**Response:**

```json
{
  "rule_id": "RULE-001",
  "findings": [...],
  "count": 1
}
```

---

## Capacity Planning API

### Analyze Capacity

Get predictive capacity analysis with trends and recommendations.

**Endpoint:** `GET /api/v1/capacity`

**Permissions:** `cluster:read`

**Response:**

```json
{
  "cluster_name": "production-cluster",
  "analysis_timestamp": "2024-01-15T10:30:00Z",
  "lookback_days": 30,
  "trends": {
    "disk": [
      {
        "resource": "disk",
        "metric": "disk_usage_percent",
        "slope": 0.5,
        "r_squared": 0.85,
        "projected_days_to_threshold": 45,
        "threshold": 85,
        "current_value": 62.5
      }
    ],
    "heap": [...],
    "shards": [...],
    "cpu": [...],
    "indices": [...]
  },
  "recommendations": [
    {
      "resource_type": "disk",
      "action": "add_node",
      "priority": "high",
      "description": "Add 2 data nodes within 30 days",
      "estimated_cost": "medium",
      "time_to_impact_days": 14
    }
  ],
  "risk_assessment": {
    "overall_risk": "medium",
    "critical_resources": ["disk"],
    "time_to_critical_days": 45,
    "confidence": 0.85
  }
}
```

**Trend Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `resource` | string | Resource type |
| `metric` | string | Specific metric name |
| `slope` | number | Growth rate (positive = increasing) |
| `r_squared` | number | Trend fit quality (0-1) |
| `projected_days_to_threshold` | number | Days until threshold breach |
| `threshold` | number | Alert threshold value |
| `current_value` | number | Current metric value |

---

### Get Trends for Specific Resource

**Endpoint:** `GET /api/v1/capacity/trends/{resource}`

**Parameters:** `resource` - one of `disk`, `heap`, `shards`, `cpu`, `indices`

**Permissions:** `cluster:read`

---

### Get Risk Assessment

**Endpoint:** `GET /api/v1/capacity/risk`

**Permissions:** `cluster:read`

**Response:**

```json
{
  "risk_assessment": {
    "overall_risk": "medium",
    "critical_resources": ["disk"],
    "time_to_critical_days": 45,
    "confidence": 0.85
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Provisioning API

### Provision Operation

Execute a full provisioning workflow with preflight, apply, verify, and rebalance stages.

**Endpoint:** `POST /api/v1/provision`

**Permissions:** `cluster:manage` (admin)

**Required:** Connection must have `write_enabled: true`

**Response (Success):**

```json
{
  "stage": "COMPLETED",
  "success": true,
  "apply_result": {
    "actions_applied": ["add_node", "rebalance_shards"],
    "duration_seconds": 120
  },
  "verification": {
    "cluster_health": "green",
    "shard_balance": "balanced",
    "duration_seconds": 30
  }
}
```

**Response (Preflight Failed):**

```json
{
  "stage": "PREFLIGHT",
  "passed": false,
  "checks": [
    {
      "name": "disk_space",
      "passed": false,
      "message": "Insufficient disk space on node-3"
    }
  ],
  "message": "Preflight checks failed"
}
```

**Workflow Stages:**
1. `PREFLIGHT` - Run all preflight checks
2. `PREFLIGHT_PASSED` - Checks passed
3. `APPROVAL_PENDING` - Awaiting human approval
4. `APPROVED` - Approved, ready to apply
5. `APPLYING` - Executing changes
6. `VERIFYING` - Post-apply verification
7. `REBALANCING` - Cluster rebalancing
8. `COMPLETED` - All stages successful

---

### Provision Dry Run

Simulate a provisioning operation without making changes.

**Endpoint:** `POST /api/v1/provision/dry-run`

**Permissions:** `cluster:manage`

**Response:**

```json
{
  "dry_run": true,
  "preflight_checks": [...],
  "passed": true,
  "message": "Dry-run completed successfully"
}
```

---

### Run Preflight Checks Only

**Endpoint:** `POST /api/v1/provision/preflight`

**Permissions:** `cluster:manage`

---

### Get Provisioning Status

**Endpoint:** `GET /api/v1/provision/status/{operation_id}`

**Permissions:** `cluster:read`

---

### Rollback Provisioning

**Endpoint:** `POST /api/v1/provision/rollback/{operation_id}`

**Permissions:** `cluster:manage`

---

### List Provisioning Operations

**Endpoint:** `GET /api/v1/provision/list`

**Permissions:** `cluster:read`

**Response:**

```json
{
  "operations": [
    {
      "operation_id": "prov-001",
      "status": "completed",
      "timestamp": "2024-01-15T10:30:00Z",
      "performed_by": "admin"
    }
  ],
  "count": 5
}
```

---

## Streaming API

The streaming API provides real-time cluster monitoring data via Server-Sent Events (SSE) or WebSocket. See [Live Monitoring Architecture](../architecture/live-monitoring.md) for design details.

### Message Format

All streaming messages use a unified envelope format:

```json
{
  "type": "snapshot|event|heartbeat",
  "connectionId": "uuid",
  "timestamp": "2024-01-15T10:30:00.123456Z",
  "payload": { ... }
}
```

**Message Types:**

| Type | Description | Frequency |
|------|-------------|-----------|
| `snapshot` | Tiered collection data | Per tier interval |
| `event` | State changes, incidents | On occurrence |
| `heartbeat` | Connection liveness | Every 30s |

---

### SSE Stream (Primary)

Server-Sent Events endpoint for real-time monitoring.

**Endpoint:** `GET /api/stream/sse`

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `last_event_id` | integer | 0 | Replay from event ID (for reconnection) |

**Headers:**
```
Accept: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**Example Event Stream:**
```
id: 123456
event: snapshot
data: {"type":"snapshot","connectionId":"...","timestamp":"...","payload":{"tier":"T1","data":{...}}}

id: 123457
event: heartbeat
data: {"type":"heartbeat","connectionId":"...","timestamp":"...","payload":{}}

: keep-alive
```

**Reconnection:**
1. On disconnect, client retains last received `id` value
2. Reconnect with `?last_event_id=<last_id>`
3. Server replays missed events from buffer (default 100 events)
4. If gap too large, `fullResyncRequired` event sent

---

### WebSocket Stream (Alternative)

WebSocket endpoint for environments requiring full-duplex or blocking SSE.

**Endpoint:** `GET /api/stream/ws`

**Protocol:**
- Connect via WebSocket upgrade
- Send/receive JSON messages
- Same envelope format as SSE

**Example Message:**
```json
{
  "type": "snapshot",
  "connectionId": "uuid",
  "timestamp": "2024-01-15T10:30:00.123456Z",
  "payload": {
    "tier": "T1",
    "data": { "cluster_health": "green", "nodes": 3 },
    "snapshotId": "uuid",
    "collectedAt": "2024-01-15T10:30:00.123456Z"
  }
}
```

---

### Tiered Collection Data

Streaming data follows ADR-005 tiered cadence:

| Tier | Name | Interval | Data |
|------|------|----------|------|
| T1 | Live | ~5s | Cluster health, node status |
| T2 | Trending | ~12s | Node stats, shard state |
| T3 | Deep | ~45s | Index stats, settings |
| T4 | Diagnostic | ~5min | Mappings, ILM, allocation |

Each tier event includes the tier identifier in the payload:
```json
{
  "type": "snapshot",
  "payload": {
    "tier": "T1",
    "data": { ... }
  }
}
```

---

### Event Messages

System events for state changes:

```json
{
  "type": "event",
  "connectionId": "uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "payload": {
    "eventType": "incidentDetected",
    "severity": "warning",
    "message": "Disk usage exceeded 80% on node-3",
    "details": { "node": "node-3", "disk_usage": 82 }
  }
}
```

**Event Types:**
| Event | Description |
|-------|-------------|
| `incidentDetected` | New issue found |
| `incidentCleared` | Issue resolved |
| `modeChanged` | Collection mode changed |
| `connectionStatus` | Collector connected/disconnected |
| `fullResyncRequired` | Replay buffer exhausted |

---

### Heartbeat

Sent every 30 seconds to maintain connection liveness:

```json
{
  "type": "heartbeat",
  "connectionId": "uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "payload": {}
}
```

---

## Security & RBAC

### Permission Mapping

| Endpoint | Required Permission | Roles |
|----------|---------------------|-------|
| `GET /api/v1/doctor` | `cluster:read` | readonly, operator, admin |
| `GET /api/v1/doctor/rules` | `cluster:read` | readonly, operator, admin |
| `POST /api/v1/doctor/marketplace/*/install` | `cluster:manage` | admin |
| `GET /api/v1/capacity` | `cluster:read` | readonly, operator, admin |
| `POST /api/v1/provision` | `cluster:manage` + `write_enabled` | admin |
| `POST /api/v1/provision/dry-run` | `cluster:manage` | admin |
| `GET /api/stream/sse` | `cluster:read` | readonly, operator, admin |
| `GET /api/stream/ws` | `cluster:read` | readonly, operator, admin |

### OpenSearch Security Integration

When deployed as an OpenSearch plugin, the API integrates with OpenSearch Security plugin:

- Authentication via Security plugin (Basic, JWT, SAML, OIDC)
- Authorization via backend roles mapped to Guardian roles
- Audit logging via Security plugin audit index
- Tenant isolation for multi-tenant deployments

---

## Connection Management

### Connection State

The API operates within a connection context. Connection profiles are managed via CLI or configuration file.

**Connection States:**
- `connected` - Active OpenSearch connection
- `disconnected` - No active connection
- `error` - Connection failed

### Write/Provisioning Mode

Per ADR-002, write operations require explicit enablement:

```python
# Enable write mode on connection
connection.write_enabled = True
```

Endpoints requiring write mode:
- `POST /api/v1/provision`
- `POST /api/v1/provision/preflight`
- `POST /api/v1/provision/rollback/*`

---

## Rate Limiting

API endpoints are rate-limited per connection:

| Endpoint Category | Limit |
|-------------------|-------|
| Read (doctor, capacity, status) | 100 req/min |
| Write (provision, rule install) | 10 req/min |
| Streaming (SSE/WS connections) | 5 concurrent per IP |

Exceeding limits returns `429 Too Many Requests` with `Retry-After` header.

---

## Versioning

API version included in URL path: `/api/v1/`

Breaking changes will increment version (`/api/v2/`). Deprecation notices provided 3 months in advance.

---

## SDK / Client Libraries

### Python
```python
from guardian_api import GuardianClient

client = GuardianClient(base_url="http://localhost:8000", token="your-token")

# Run diagnosis
result = client.doctor.run()

# Stream live data
async for event in client.stream.sse():
    print(event)
```

### JavaScript/TypeScript
```typescript
import { GuardianClient } from '@opensearch-guardian/client';

const client = new GuardianClient({ baseUrl: 'http://localhost:8000', token: '...' });

// Run diagnosis
const result = await client.doctor.run();

// Stream via SSE
const stream = client.stream.sse();
for await (const event of stream) {
    console.log(event);
}
```

---

## Related Documentation

- [Backend Plugin Development Guide](../plugins/backend-plugin-development.md) - OpenSearch plugin REST endpoints
- [Frontend Plugin Development Guide](../plugins/frontend-plugin-development.md) - Dashboards plugin API integration
- [Live Monitoring Architecture](../architecture/live-monitoring.md) - Streaming protocol design
- [Security Integration](../plugins/migration-guide.md#phase-1-security--rbac-mapping) - RBAC configuration
- [Test Runbook](../testing/test-runbook.md) - API testing procedures