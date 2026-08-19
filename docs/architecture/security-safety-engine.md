# Security & Safety Engine Design

## Purpose
The Security & Safety Engine (SSE) enforces the defensive posture defined in SOP §8 and ADR‑002. It provides:

1. **Operation Classification** – 4‑tier safety classification for all external and internal operations (Informational, Safe‑Reversible, Approval‑Required, Destructive).
2. **Access Control** – read‑only default, with independent per‑connection write mode and optional operation gating.
3. **Dry‑run / Diff** – side‑by‑side rendering of current vs proposed infrastructure changes.
4. **Immutable Auditing** – cryptographically signed before/after snapshots for every mutation.
5. **Guardrails** – destructive‑operation checks aligning with V1 guarantees (no auto‑delete of indices/PVCs/nodes/snapshots).
6. **Allow‑listed Ops** – explicit whitelist of mutation primitives.
7. **Secret Management** – OS keychain (or platform-specific credential store) backed, never persisted in plain.

### Architecture Overview
```
+---------------------+      +-------------------+      +---------------------+
|  Connection Manager|<---> |   Policy Engine  |<--->|  Audit & Log Store |
+---------------------+      +-------------------+      +---------------------+
            |                        |                          |
            v                        v                          |
   +-----------------+     +-------------------+                 |
   |  Resource Sync   |<--->|  Operation Class |<-----------------|
   +-----------------+     +-------------------+                 |
            |                        |                          |
            v                        v                          |
   +-----------------+     +-------------------+                 |
   |  Dry‑run Engine |<--->|  Mutation Filter |<-----------------|
   +-----------------+     +-------------------+                 |
            |                        |                          |
            v                        v                          |
   +-----------------+     +-------------------+                 |
   |  Keychain Store |<--->|  Secret Proxy    |                 |
   +-----------------+     +-------------------+                 |
```

#### 1. Connection Manager
- Maintains per‑connection state (read‑only flag, write‑enablement).  
- Loads credentials via `KeychainProxy` and lazily injects into APIs.

#### 2. Policy Engine
- Evaluates operation classification according to SOP §8.
- Applies approval workflow for *Approval‑Required* ops (expects explicit human pick‑up).
- Enforces *Destructive* guard: denies removal of core resources unless pre‑approved.

#### 3. Mutation Filter & Dry‑run Engine
- `MutationFilter` checks submitted mutation requests against an allow‑list.
- For destructive ops, runs simulation (`dry_run=True`) generating diff objects (before/after snapshots).
- Diff is presented via `DiffUI` (CLI/table) for operator review.

#### 4. Audit & Log Store
- Every mutation, after validation, is recorded as an immutable log entry:
  ```json
  {
    "uuid": "<uuid>",
    "timestamp": "ISO8601",
    "operation": "<action>",
    "classification": "<tier>",
    "before_hash": "sha256-…",
    "after_hash": "sha256-…",
    "performed_by": "<user>"|
    "details": {…}
  }
  ```
- Entries are `write_once` – no updates allowed.

#### 5. Keychain Proxy
- Implements a lazy, thread‑safe fetch of credentials from OS keychain.
- Supports multiple backends: macOS Keychain, Windows Credential Vault, Linux Secret Service.
- Never stores or logs secrets in cleartext.

### Integration Points
- **T8 – Connection & Collection Design** – SSE plugs into the Connection Manager to provide per‑connection write flags.
- **T7 – Component Contract** – SSE exposes a REST / gRPC API to mutation callers; its contract respects the component-whitelist.

### Operational Flow (example: Add node via Docker)
1. Caller invokes `sse.mutate({"type":"node-add", "container":{…}})`.
2. `MutationFilter` validates against allow‑list. Destructive? no.
3. `PolicyEngine` classifies as *Safe‑Reversible*.
4. `Dry‑run Engine` obtains current cluster state, simulates addition, produces diff.
5. Diff returned to caller for review.
6. After operator approval, `MutationFilter` executes the real change.
7. `Audit Log Store` records entry with before/after hashes.

### Security Assertions
- **No auto‑deletion**: `MutationFilter` throws for any operation that deletes indices, PVCs, nodes, or snapshots.
- **Read‑only default**: Connections start read‑only. Write mode requires explicit `enable_write()` from the caller.
- **Allow‑list constraint**: Each integration declares its verb set; SSE rejects unknown mutator names.
- **Secret protection**: All credentials accessed via `KeychainProxy`; operations never expose keys.

---

## Next Steps
- Draft `tests/` covering classification, dry‑run, audit log, and keychain stubs.
- Prepare a mock implementation in the repo (mocks only, no commits).
- Update ADR‑002 to document the SSE contract.
- Communicate design to Phyllis for alignment with component contract.

---

*Author: Angela (angela‑msyilhk2)*