# Desktop Architecture: Electron ↔ Guardian Core Boundary

Architecture design for OpenSearch Guardian's Electron desktop application, defining renderer boundaries, restricted IPC/API surface, and live data streaming.

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        RENDERER (React/TypeScript)              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  UI Components  │  │  State (Zustand)│  │  Charts/Viz    │  │
│  │  (pure React)   │  │  (client-side)  │  │  (D3/Recharts) │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬───────┘  │
│           │                    │                    │            │
│           └────────────────────┴────────────────────┘            │
│                         guardianAPI                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │ contextBridge (read-only exposure)
┌───────────────────────────┴─────────────────────────────────────┐
│                         PRELOAD SCRIPT                          │
│  const { contextBridge, ipcRenderer } = require('electron');    │
│  contextBridge.exposeInMainWorld('guardianAPI', { ... });       │
└───────────────────────────┬─────────────────────────────────────┘
                            │ ipcMain.handle (validated)
┌───────────────────────────┴─────────────────────────────────────┐
│                         MAIN PROCESS                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  IPC Handlers (typed, validated)                         │   │
│  │  - Connection management                                 │   │
│  │  - Credential store access                               │   │
│  │  - Safe UI operations (themes, window management)        │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │ HTTP/WebSocket                       │
│  ┌────────────────────────▼─────────────────────────────────┐   │
│  │  Guardian Core Service (Python/FastAPI)                   │   │
│  │  - OpenSearch Collector                                  │   │
│  │  - Docker/K8s Adapters                                   │   │
│  │  - Doctor Rules Engine                                   │   │
│  │  - Cost Optimizer                                        │   │
│  │  - Provisioning/Safety Engine                            │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                    │
│  ┌────────────────────────▼─────────────────────────────────┐   │
│  │  Credential Store (native OS)                            │   │
│  │  - macOS Keychain                                        │   │
│  │  - Windows Credential Locker                             │   │
│  │  - Linux Secret Service                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Layer Boundaries

### 2.1 Renderer Process (React + TypeScript)
**Responsibilities:**
- Pure UI rendering (React components)
- Client-side state management (Zustand/Jotai)
- Data visualization (charts, dashboards)
- User input handling (forms, buttons, navigation)

**Restrictions:**
- ❌ No direct Electron API access
- ❌ No Node.js modules (fs, child_process, net)
- ❌ No credential/secret storage
- ❌ No direct OpenSearch/Docker/K8s API calls
- ❌ No shell command execution
- ❌ No raw `require('electron')` usage

### 2.2 Preload Script (Bridge Layer)
**Responsibilities:**
- Expose minimal, typed API to renderer via `contextBridge`
- Validate IPC call signatures (optional but recommended)
- Cannot access main process internals directly

**Interface Contract:**
```typescript
// Types exposed to renderer
interface GuardianAPI {
  // Connection management (read-only + safe mutations)
  listConnections(): Promise<ConnectionInfo[]>;
  testConnection(connectionId: string): Promise<ConnectionTestResult>;
  
  // Monitoring data
  getClusterHealth(): Promise<HealthSnapshot>;
  getNodeMetrics(nodeId: string): Promise<NodeMetrics>;
  getIndexStats(): Promise<IndexStats[]>;
  
  // Doctor & Optimizer
  runDoctor(): Promise<Diagnosis[]>;
  getCostRecommendations(): Promise<CostRecommendation[]>;
  
  // Provisioning (approval-required paths only)
  requestPreflightCheck(params: PreflightParams): Promise<PreflightResult>;
  requestApproveChange(changeId: string): Promise<ApprovalResult>;
  
  // UI configuration
  updateTheme(theme: 'light' | 'dark' | 'system'): Promise<void>;
  
  // Notifications
  subscribeToEvents(eventType: string, callback: (data: unknown) => void): () => void;
}

declare global {
  interface Window {
    guardianAPI: GuardianAPI;
  }
}
```

### 2.3 Main Process (IPC + Orchestration)
**Responsibilities:**
- Validate and route IPC messages
- Manage credential store access
- Orchestrate Guardian Core service lifecycle
- Handle window management and tray icon
- Audit logging for all privileged operations

**IPC Handler Pattern:**
```javascript
// main.js - IPC handler with validation
ipcMain.handle('guardian:runDoctor', async (event) => {
  // 1. Validate sender origin
  if (!isTrustedSender(event.sender)) {
    auditLog.warn('Untrusted IPC sender', { sender: event.sender.id });
    throw new Error('IPC sender validation failed');
  }
  
  // 2. Check connection permissions
  const activeConnection = getActiveConnection();
  if (!activeConnection || activeConnection.mode === 'read-only') {
    throw new Error('Doctor requires write access or active connection');
  }
  
  // 3. Delegate to core service
  const results = await guardianCore.runDoctor(activeConnection);
  
  // 4. Audit the operation
  auditLog.info('Doctor run completed', {
    userId: getUserIdFromEvent(event),
    connectionId: activeConnection.id,
    findingCount: results.length,
  });
  
  return results;
});
```

### 2.4 Guardian Core Service (Python/FastAPI)
**Responsibilities:**
- OpenSearch REST API communication
- Docker Engine API integration (optional)
- Kubernetes API integration (optional)
- Doctor rules execution (deterministic)
- Cost optimization analysis
- Provisioning workflow orchestration
- Data collection and normalization
- WebSocket/SSE event streaming

**Key Subsystems:**
```
apps/api/
├── connections/        # OpenSearch/Docker/K8s connection managers
├── collectors/         # Polling and data normalization
├── models/            # Pydantic models for typed data
├── rules/             # Doctor rule definitions
├── diagnosis/         # Rule execution and correlation
├── optimizer/         # Cost analysis engine
├── capacity/          # Capacity planning
├── provisioning/      # Infrastructure change workflows
│   ├── docker/        # Docker adapter
│   └── kubernetes/    # Kubernetes adapter
├── safety/            # Approval gates and validation
├── audit/             # Immutable audit logging
└── llm/               # Optional AI explanation layer
```

## 3. Restricted IPC/API Surface

### 3.1 Allowed IPC Operations (Read-Only by Default)

```
┌─────────────────────────────────────────────────────────────────────┐
│ IPC CHANNELS (Renderer ↔ Main)                                      │
├─────────────────────────────────────────────────────────────────────┤
│ Channel                 │ Method    │ Purpose                        │
├─────────────────────────────────────────────────────────────────────┤
│ guardian:testConnection │ handle    │ Test cluster connectivity     │
│ guardian:getHealth      │ handle    │ Fetch cluster health          │
│ guardian:getNodes       │ handle    │ Fetch node list/metrics       │
│ guardian:getIndices     │ handle    │ Fetch index statistics        │
│ guardian:runDoctor      │ handle    │ Run diagnostic rules          │
│ guardian:getOptimizer   │ handle    │ Fetch cost recommendations    │
│ guardian:getHistory     │ handle    │ Fetch snapshot history        │
│ guardian:updateTheme    │ handle    │ Change UI theme               │
│ guardian:subscribe      │ handle    │ Subscribe to WebSocket        │
│ guardian:unsubscribe    │ handle    │ Unsubscribe from WebSocket    │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Approval-Gated IPC Operations (Write/Provisioning)

```
┌─────────────────────────────────────────────────────────────────────┐
│ IPC CHANNELS (Requires Explicit Approval)                           │
├─────────────────────────────────────────────────────────────────────┤
│ Channel                    │ Method  │ Purpose                        │
├─────────────────────────────────────────────────────────────────────┤
│ guardian:preflightCheck    │ handle  │ Run pre-provisioning checks    │
│ guardian:approveChange     │ handle  │ Approve infrastructure change  │
│ guardian:getApprovalStatus │ handle  │ Check approval workflow state  │
│ guardian:cancelChange      │ handle  │ Cancel pending infrastructure  │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Forbidden IPC Operations (Renderer Block)

```
┌─────────────────────────────────────────────────────────────────────┐
│ PROHIBITED OPERATIONS                                               │
├─────────────────────────────────────────────────────────────────────┤
│ Operation                     │ Reason                              │
├─────────────────────────────────────────────────────────────────────┤
│ shell.execute()               │ SOP §8: No arbitrary commands          │
│ shell.openExternal()          │ Must be validated in main process     │
│ child_process.*               │ SOP §8: No subprocess from renderer   │
│ ipcRenderer.send()            │ Use handle/response pattern           │
│ Any credential modification   │ Must go through secure main process   │
│ Direct OpenSearch mutations   │ Only via Core service with audit      │
│ Node.js fs/path/net           │ No direct Node access                 │
└─────────────────────────────────────────────────────────────────────┘
```

## 4. Live Data Streaming Architecture

### 4.1 Event Flow (SSE/WebSocket Plan)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  OpenSearch  │────▶│  Collector   │────▶│  Core API    │────▶│  Main Proc   │
│   REST API   │     │  (Python)    │     │  (FastAPI)   │     │  (Node.js)   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                      │
                                                                      │ IPC: guardian:subscribe
                                                                      │
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────▼───────┐
│  Renderer    │◀────│  Preload     │◀────│  WebSocket   │◀────│  Event Bus   │
│  (React)     │     │  (Bridge)    │     │  (Core API)  │     │  (Main Proc) │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### 4.2 Streaming Implementation

**Core API (FastAPI) WebSocket/SSE:**
```python
# apps/api/main.py or streaming module
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from guardian.collectors import CollectorManager

router = APIRouter()

@router.websocket("/ws/events")
async def event_stream(websocket: WebSocket):
    await websocket.accept()
    collector = CollectorManager()
    
    try:
        async for event in collector.stream_events():
            # Normalize and push to connected clients
            await websocket.send_json({
                "type": event.type,  # 'health', 'metrics', 'diagnosis', etc.
                "timestamp": event.timestamp.isoformat(),
                "data": event.payload
            })
    except WebSocketDisconnect:
        collector.unsubscribe(websocket.client_id)
```

**Main Process IPC Subscription:**
```javascript
// main.js - WebSocket event relay to renderer
ipcMain.handle('guardian:subscribe', async (event, eventType) => {
  const { WebSocket } = require('ws');
  const coreUrl = getCoreServiceUrl(); // http://localhost:8000
  
  // Connect to Core API WebSocket
  const ws = new WebSocket(`${coreUrl}/ws/events`);
  
  ws.on('message', (data) => {
    const event = JSON.parse(data.toString());
    
    // Route only matching event types to this renderer
    if (eventType === '*' || event.type === eventType) {
      // Send to specific renderer window
      const window = BrowserWindow.fromWebContents(event.sender);
      if (window) {
        window.webContents.send('guardian:event', event);
      }
    }
  });
  
  return { status: 'subscribed', eventType };
});
```

**Renderer Event Handling:**
```typescript
// renderer/hooks/useGuardianEvents.ts
import { useEffect, useCallback } from 'react';

export function useGuardianEvents(eventType: string, callback: (data: any) => void) {
  useEffect(() => {
    const unsubscribe = window.guardianAPI.subscribe(eventType, callback);
    return unsubscribe;
  }, [eventType, callback]);
}

// Usage in component
function ClusterHealthCard() {
  const [health, setHealth] = useState(null);
  
  useGuardianEvents('health', (data) => {
    setHealth(data);
  });
  
  // ... render health data
}
```

### 4.3 Event Types

```typescript
interface GuardianEvent {
  type: 'health' | 'metrics' | 'diagnosis' | 'optimizer' | 'provisioning' | 'audit';
  timestamp: string;
  data: {
    // Per-type payload structure
  };
}

// Example: Health event
interface HealthEvent extends GuardianEvent {
  type: 'health';
  data: {
    clusterName: string;
    status: 'green' | 'yellow' | 'red';
    numberOfNodes: number;
    numberOfPendingTasks: number;
    activeShards: number;
    unassignedShards: number;
  };
}

// Example: Diagnosis event
interface DiagnosisEvent extends GuardianEvent {
  type: 'diagnosis';
  data: {
    findings: Array<{
      ruleId: string;
      severity: 'info' | 'warning' | 'critical';
      entity: string;
      observedValue: string;
      evidence: string[];
      recommendation: string;
    }>;
  };
}
```

### 4.4 Polling vs. Streaming Strategy

Per SOP §4.2 (Collection Strategy):
- **Polling** (Core API → OpenSearch): 5s health, 10-15s metrics, 30-60s index stats, 5min deep scans
- **Streaming** (Core API → Renderer): WebSocket pushes normalized events as they arrive
- **Adaptive**: During incidents, polling frequency increases (via Core API configuration)

## 5. Security Boundary Enforcement

### 5.1 Layer Responsibilities

| Layer | Credential Access | API Access | Audit Logging |
|-------|-------------------|------------|---------------|
| Renderer | ❌ None | ❌ None | Optional (UI events) |
| Preload | ❌ None | ✅ Bridge only | No |
| Main Process | ✅ Secure Store | ✅ IPC only | ✅ All privileged ops |
| Core API | ✅ Connection config | ✅ OpenSearch/Docker/K8s | ✅ All mutations |

### 5.2 Credential Flow
```
Renderer Request
    ↓
Preload Bridge (no credential access)
    ↓
Main Process IPC (credential lookup)
    ↓
Core API (credential injection for API calls)
    ↓
External Service (OpenSearch/Docker/K8s)
```

### 5.3 Audit Trail
All privileged operations logged immutably:
```typescript
interface AuditEntry {
  timestamp: string;
  userId: string;
  operation: string;
  connectionId: string;
  entityType: 'connection' | 'diagnosis' | 'provisioning' | 'settings';
  entityId: string;
  before?: any;
  after?: any;
  result: 'success' | 'failure' | 'approved' | 'rejected';
  approvalRequired?: boolean;
  approvalGranted?: boolean;
}
```

## 6. Integration with Creed T23 (Streaming)

The streaming layer hooks into the broader Guardian platform:

```
┌─────────────────────────────────────────────────────────────┐
│  OpenSearch Guardian Platform                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Desktop (Electron)                                 │    │
│  │    ├─ Renderer (React)                              │    │
│  │    ├─ Main (IPC)                                    │    │
│  │    └─ Core API Bridge                               │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Creed T23: Event Streaming Service                  │    │
│  │    ├─ WebSocket Gateway                              │    │
│  │    ├─ Event Bus (Kafka/RabbitMQ)                     │    │
│  │    └─ Event Normalization Layer                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Guardian Core (Python/FastAPI)                      │    │
│  │    ├─ Collectors (OpenSearch/Docker/K8s)             │    │
│  │    ├─ Rules Engine                                   │    │
│  │    └─ Provisioning Engine                            │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**T23 Integration Points:**
1. Core API publishes events to event bus (Kafka/RabbitMQ)
2. T23 WebSocket gateway subscribes and streams to connected clients
3. Desktop subscribes via IPC to T23 gateway
4. Renderer receives normalized events via guardianAPI

## 7. DoD Compliance Checklist

### SOP §8 Security Requirements Addressed

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Read-only default | IPC handlers enforce read-only unless write permission granted | ✅ |
| Separate monitoring/provisioning | Different IPC channels, approval gates for provisioning | ✅ |
| Secrets in OS keychain | CredentialStore module using native OS APIs | ✅ |
| TLS validation enabled | Core API enforces TLS; main process validates certs | ✅ |
| No renderer shell execution | Forbidden operations table; no shell access in renderer | ✅ |
| Allow-listed mutations | Explicit IPC handlers for each operation | ✅ |
| Recommendation classification | Doctor rules tagged with severity/safety level | ✅ |
| V1 no autonomous deletion | Provisioning requires explicit approval + dry-run | ✅ |
| Dry-run/diff view | Pre-flight checks and approval workflow | ✅ |
| Audit write operations | Audit module logs all privileged operations | ✅ |

### ADR-003 Stack Alignment

| Layer | Technology | Used In |
|-------|------------|---------|
| Desktop UI | Electron + React + TypeScript | Renderer + Main + Preload |
| Core/API | Python + FastAPI + Pydantic | Guardian Core Service |
| OpenSearch | opensearch-py + REST adapters | Collector layer |
| Streaming | WebSocket/SSE | T23 integration, IPC relay |
| Container | Docker Engine API | Provisioning adapter |
| K8s | Official Python client | Provisioning adapter |

## 8. References

- SOP §4: Proper Implementation Architecture
- SOP §8: Security and Safety Requirements
- ADR-003: Technology Stack
- [Electron Security Tutorial](https://www.electronjs.org/docs/latest/tutorial/security)
- [contextBridge API](https://www.electronjs.org/docs/latest/api/context-bridge)
- [IPC Security](https://www.electronjs.org/docs/latest/tutorial/ipc#security-considerations)
