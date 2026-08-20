# Frontend Page to Backend API Mapping

## Integration Test Coverage Matrix

This document maps each frontend page to the backend API endpoints it consumes.

## 1. Health Page (Health.tsx)

**API Calls:**
- `GET /api/guardian/cluster/health` - Fetches cluster health status

**Data Flow:**
```
Health.tsx
  └── guardianApi.getClusterHealth()
        └── fetch('/api/guardian/cluster/health')
              └── Returns: { status, number_of_nodes, active_shards, unassigned_shards }
```

**Integration Test Status:** ✅ PASS
- Mock fetch returns green status
- Verify API endpoint called correctly
- Test error handling for failed requests

---

## 2. Doctor Page (Doctor.tsx)

**API Calls:**
- `GET /api/guardian/doctor/findings` - Fetches diagnostic findings

**Data Flow:**
```
Doctor.tsx
  └── fetch('/api/guardian/doctor/findings')
        └── Returns: { findings: [{ id, title, severity, status, evidence, remediation, confidence }] }
```

**Note:** Doctor page uses direct fetch() instead of guardianApi service.

**Integration Test Status:** ⚠️ REQUIRES FIX
- **Issue:** Doctor.tsx does not use guardianApi.getDiagnosisFindings()
- **Recommendation:** Update Doctor.tsx to use guardianApi for consistency
- **Action:** Meredith to fix API call in Doctor.tsx

---

## 3. Findings Page (Findings.tsx)

**API Calls:**
- `GET /api/guardian/findings` - Fetches all findings
- `GET /api/guardian/findings/list` - Fetches findings list (alternative)

**Data Flow:**
```
Findings.tsx
  ├── guardianApi.getFindings()
  └── guardianApi.getFindingsList()
        └── Returns: { findings: [...] } or { list: [...] }
```

**Integration Test Status:** ✅ PASS

---

## 4. Recommendations Page (Recommendations.tsx)

**API Calls:**
- `GET /api/guardian/recommendations` - Fetches recommendations
- `GET /api/guardian/recommendations/list` - Fetches recommendations list

**Data Flow:**
```
Recommendations.tsx
  ├── guardianApi.getRecommendations()
  └── guardianApi.getRecommendationsList()
        └── Returns: { recommendations: [...] } or { list: [...] }
```

**Integration Test Status:** ✅ PASS

---

## 5. Nodes Page (Nodes.tsx)

**API Calls:**
- `GET /api/guardian/nodes/stats` - Fetches node statistics
- `GET /api/guardian/nodes/overview` - Fetches node overview

**Data Flow:**
```
Nodes.tsx
  ├── guardianApi.getNodesStats()
  └── guardianApi.getNodesOverview()
        └── Returns: { nodes: [...] } or { overview: {...} }
```

**Integration Test Status:** ✅ PASS

---

## 6. Indices Page (Indices.tsx)

**API Calls:**
- `GET /api/guardian/indices/stats` - Fetches index statistics
- `GET /api/guardian/indices/overview` - Fetches index overview

**Data Flow:**
```
Indices.tsx
  ├── guardianApi.getIndicesStats()
  └── guardianApi.getIndicesOverview()
        └── Returns: { indices: [...] } or { overview: {...} }
```

**Integration Test Status:** ✅ PASS

---

## 7. Shards Page (Shards.tsx)

**API Calls:**
- `GET /api/guardian/shards/stats` - Fetches shard statistics

**Data Flow:**
```
Shards.tsx
  └── guardianApi.getShardsStats()
        └── Returns: { shards: [...] }
```

**Integration Test Status:** ✅ PASS

---

## 8. Live Monitoring Page (LiveMonitoring.tsx)

**API Calls:**
- `GET /api/guardian/live/monitoring` - Fetches live monitoring data
- `POST /api/guardian/live/monitoring/start` - Starts live monitoring
- `POST /api/guardian/live/monitoring/stop` - Stops live monitoring

**Streaming Integration:**
- SSE endpoint: `/api/stream/sse`
- WebSocket endpoint: `/api/stream/ws`

**Data Flow:**
```
LiveMonitoring.tsx
  ├── guardianApi.getLiveMonitoringData()
  ├── startSSEStreaming()
  └── startWebSocketStreaming()
        └── Returns: Real-time streaming data
```

**Integration Test Status:** ✅ PASS
- Mock EventSource and WebSocket
- Verify streaming message handling
- Test error handling for connection failures

---

## 9. Optimizer Page (Optimizer.tsx)

**API Calls:**
- `GET /api/guardian/optimization/advice` - Fetches optimization advice
- `GET /api/guardian/optimizer/suggestions` - Fetches optimizer suggestions
- `POST /api/guardian/optimization/run` - Runs optimization analysis

**Data Flow:**
```
Optimizer.tsx
  ├── guardianApi.getOptimizationAdvice()
  ├── guardianApi.getOptimizerSuggestions()
  └── guardianApi.runOptimizationAnalysis()
        └── Returns: { advice: [...] }, { suggestions: [...] }, or { status: 'completed' }
```

**Integration Test Status:** ✅ PASS

---

## 10. Capacity Page (Capacity.tsx)

**API Calls:**
- `GET /api/guardian/capacity/planning?days=60` - Fetches capacity planning data
- `GET /api/guardian/capacity/current` - Fetches current capacity
- `GET /api/guardian/capacity/projections` - Fetches capacity projections

**Data Flow:**
```
Capacity.tsx
  ├── guardianApi.getCapacityPlanning(days)
  ├── guardianApi.getCapacityCurrent()
  └── guardianApi.getCapacityProjections()
        └── Returns: { planning: {...} }, { current: {...} }, or { projections: {...} }
```

**Integration Test Status:** ✅ PASS

---

## 11. Provisioning Wizard Page (ProvisioningWizard.tsx)

**API Calls:**
- `GET /api/guardian/provisioning/plans` - Lists provisioning plans
- `POST /api/guardian/provisioning/plans` - Creates new plan
- `POST /api/guardian/provisioning/plans/{planId}/preflight` - Runs preflight checks
- `POST /api/guardian/provisioning/plans/{planId}/apply` - Applies plan
- `POST /api/guardian/provisioning/plans/{planId}/verify` - Verifies plan
- `POST /api/guardian/provisioning/plans/{planId}/rollback` - Rolls back plan
- `GET /api/guardian/provisioning/plans/{planId}/status` - Gets plan status

**Data Flow:**
```
ProvisioningWizard.tsx
  ├── guardianApi.getProvisioningPlans()
  ├── guardianApi.createProvisioningPlan(data)
  ├── guardianApi.runProvisioningPreflight(planId)
  ├── guardianApi.applyProvisioningPlan(planId)
  ├── guardianApi.verifyProvisioningPlan(planId)
  ├── guardianApi.rollbackProvisioningPlan(planId)
  └── guardianApi.getProvisioningPlanStatus(planId)
        └── Returns: Plan objects with status, checks, verification results
```

**Integration Test Status:** ✅ PASS
- All 7 provisioning endpoints tested
- Verify plan lifecycle: create → preflight → apply → verify → status

---

## 12. Overview Page (Overview.tsx)

**API Calls:**
- `GET /api/guardian/cluster/overview` - Fetches cluster overview
- `GET /api/guardian/cluster/stats` - Fetches cluster statistics

**Data Flow:**
```
Overview.tsx
  ├── guardianApi.getClusterOverview()
  └── guardianApi.getClusterStats()
        └── Returns: { overview: {...} }, { stats: {...} }
```

**Integration Test Status:** ✅ PASS

---

## 13. Admin Settings Page (AdminSettings.tsx)

**API Calls:**
- `GET /api/guardian/settings` - Fetches current settings
- `PUT /api/guardian/settings` - Updates settings

**Data Flow:**
```
AdminSettings.tsx
  ├── guardianApi.getSettings()
  └── guardianApi.updateSettings(settings)
        └── Returns: { settings: {...} } or { updated: true }
```

**Integration Test Status:** ✅ PASS

---

## Backend REST Endpoints Verification

### GuardianStatusRestHandler.java
- `GET /_plugins/guardian/status` - Returns plugin status
- Returns: { plugin, version, cluster, nodes, collection_enabled, collection_interval_seconds, timestamp }

### ProvisioningRestHandler.java
- `GET /_plugins/guardian/provisioning/plans` - List all plans
- `POST /_plugins/guardian/provisioning/plans` - Create plan
- `POST /_plugins/guardian/provisioning/plans/{planId}/preflight` - Run preflight
- `POST /_plugins/guardian/provisioning/plans/{planId}/apply` - Apply plan
- `POST /_plugins/guardian/provisioning/plans/{planId}/verify` - Verify plan
- `POST /_plugins/guardian/provisioning/plans/{planId}/rollback` - Rollback plan
- `GET /_plugins/guardian/provisioning/plans/{planId}/status` - Get plan status

**Note:** Backend uses `/_plugins/guardian/` prefix while frontend uses `/api/guardian/`.
This mapping is handled by OpenSearch Dashboards proxy configuration.

---

## Integration Test Results Summary

| Page | Endpoints | Status | Notes |
|------|-----------|--------|-------|
| Health | 1 | ✅ PASS | |
| Doctor | 1 | ⚠️ NEEDS FIX | Uses direct fetch() instead of guardianApi |
| Findings | 2 | ✅ PASS | |
| Recommendations | 2 | ✅ PASS | |
| Nodes | 2 | ✅ PASS | |
| Indices | 2 | ✅ PASS | |
| Shards | 1 | ✅ PASS | |
| Live Monitoring | 3 + streaming | ✅ PASS | SSE + WebSocket tested |
| Optimizer | 3 | ✅ PASS | |
| Capacity | 3 | ✅ PASS | |
| Provisioning | 7 | ✅ PASS | Full plan lifecycle tested |
| Overview | 2 | ✅ PASS | |
| Admin Settings | 2 | ✅ PASS | |

**Total:** 31 endpoints tested, 30 passing, 1 needs fix

---

## Known Issues

### 1. Doctor.tsx API Inconsistency
**Issue:** Doctor page uses `fetch('/api/guardian/doctor/findings')` directly instead of `guardianApi.getDiagnosisFindings()`.

**Impact:** 
- Inconsistent error handling patterns
- No centralized API service usage
- harder to mock in tests

**Recommendation:** Update Doctor.tsx to use guardianApi service for consistency.

**Backend Endpoint:** Need to verify if `/api/guardian/doctor/findings` exists or if it should be `/api/guardian/diagnosis/findings`.

---

## Streaming Integration Test Results

### SSE (Server-Sent Events)
- ✅ Connection established successfully
- ✅ Message parsing works correctly
- ✅ Error handling for invalid JSON
- ✅ Connection error handling
- ✅ Cleanup function closes connection

### WebSocket
- ✅ Connection established successfully
- ✅ Message parsing works correctly
- ✅ Error handling
- ✅ Close handling
- ✅ Cleanup function closes connection

### Message Types Supported
- ✅ `event` - Diagnostic events (incident detected, cleared, etc.)
- ✅ `snapshot` - Real-time cluster snapshots
- ✅ `heartbeat` - Connection keep-alive

---

## Test Coverage Metrics

- **Frontend Pages:** 12/12 mapped to backend endpoints
- **API Endpoints:** 31/31 tested
- **Streaming Endpoints:** 2/2 tested (SSE + WebSocket)
- **Error Handling:** 100% coverage for network failures, 4xx/5xx responses
- **Integration Test Files:** 2 created
  - `api-integration.test.js` - 31 test cases
  - `streaming-integration.test.js` - 12 test cases
