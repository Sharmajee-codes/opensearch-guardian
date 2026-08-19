# Kubernetes Provisioning Research

**For:** OpenSearch Guardian — K8s adapter design (T11)
**References:** SOP §3.3, §7, §8; ADR-001, ADR-002, ADR-006
**Status:** Research — feeds ADR-009

---

## 1. Problem Statement

Guardian must support scaling OpenSearch clusters deployed on Kubernetes. The key constraint from the SOP (§3.3) is:

> *"Where the OpenSearch Kubernetes Operator manages the cluster, Guardian should patch the appropriate OpenSearch custom resource/node pool and let the Operator reconcile StatefulSets, Pods, Services, storage, and lifecycle. Guardian must not create unmanaged OpenSearch pods beside an Operator-managed cluster."*

This research covers:
1. The **Operator-first** path (preferred)
2. The **Helm/StatefulSet fallback** path
3. **kubeconfig / in-cluster credential** handling
4. **RBAC scoping** — monitoring vs. provisioning
5. **Watch/reconcile/verify** loop design
6. **Dry-run/diff and approval** integration with the provisioning state machine (ADR-006)

---

## 2. OpenSearch Kubernetes Operator

### 2.1 What It Is

The OpenSearch Kubernetes Operator (maintained by the OpenSearch project) manages OpenSearch clusters as a **Custom Resource (CR)** of kind `OpenSearchCluster`. It reconciles StatefulSets, Services, PersistentVolumeClaims, RBAC, and security configurations.

**Key CR fields:**
- `opensearchImage` / `opensearchVersion`
- `clusterName`
- `instances` (per role: data, master, remote-cluster-client, etc.)
- `resources` (CPU, memory limits)
- `nodeConfig` (JVM options, heap size, disk settings)
- `pvc` (storage class, volume size)
- `security` (TLS, authentication)
- `service` (headless, load-balancer)

### 2.2 How Guardian Should Interact

Guardian **patches the CR** via the Kubernetes API, then waits for the Operator to reconcile. It does **not** create StatefulSets directly.

**Flow:**
1. Read current `OpenSearchCluster` CR → show desired-state diff
2. User approves → Guardian patches CR (e.g., increment `instances.data` from 3 → 4)
3. Guardian watches CR status and Pod readiness
4. Guardian switches verification back to OpenSearch APIs (node join, shard rebalance, health)

**API interaction:**
```yaml
# Example: patch the CR to add a data node
PATCH /apis/opensearch.threatgrid.io/v1/namespaces/{ns}/opensearchclusters/{name}
Body: { "spec": { "instances": { "data": 4 } } }
```

**Watch patterns:**
- Watch the `OpenSearchCluster` CR for `status.conditions` transitions
- Watch Pods for `Running` + `Ready`
- Poll OpenSearch `_nodes` and `_cluster/health` for join verification

### 2.3 Multi-Node Pool Support

Some deployments use **multiple OpenSearchCluster CRs** (one per node pool: data, master, ingest). Guardian must support:
- Detecting which CRs exist in the namespace
- Patching the correct CR for the requested role
- Handling cross-pool rebalancing implications

---

## 3. Helm / StatefulSet Alternative Path

Not all clusters use the Operator. Some use **Helm charts** or **hand-written StatefulSets**. Guardian should support these as secondary adapters.

### 3.1 Helm-Based Clusters

Guardian can:
- Detect Helm releases via `helm list` (or the Helm API if available)
- Read the current `values.yaml` from the release config
- Generate a desired-values diff
- Apply via `helm upgrade --dry-run` for review, then `helm upgrade` after approval

**Limitations:**
- Helm upgrades are less granular than CR patches
- Rollback requires helm history awareness
- Not all Helm charts expose per-pool scaling cleanly

### 3.2 Raw StatefulSets

For clusters managed by raw StatefulSets (no Operator, no Helm):
- Guardian reads the StatefulSet spec
- Patches the `replicas` field
- Waits for new Pods to join
- Verifies via OpenSearch APIs

**Caution:** This path is higher risk because there is no Operator validating the change. Preflight checks must be stricter.

---

## 4. Credential Management

### 4.1 External kubeconfig

Guardian reads the user's local kubeconfig (~/.kube/config) or a specified path. It:
- Parses contexts and clusters
- Validates access via `kubectl --context=<ctx> auth can-i` equivalents
- Stores only the context name (not raw credentials) in the connection profile
- Uses the OS keychain for sensitive auth tokens (per SOP §8)

### 4.2 In-Cluster Credentials

For deployments where Guardian runs inside the cluster (e.g., as a sidecar or CronJob):
- Guardian uses the in-cluster service account token
- The token's RBAC scope determines what Guardian can do
- Guardian must still require explicit user consent before using in-cluster creds for provisioning

### 4.3 Credential Flow

```
User adds connection
  → Guardian prompts: "Select kubeconfig context" or "Use in-cluster credentials?"
  → Guardian tests access: GET /api/v1/namespaces, GET /apis/opensearch.threatgrid.io
  → Guardian stores context name + RBAC scope in connection profile (encrypted)
  → Guardian reports: "Monitoring: ✅ | Provisioning: ⚠️ (needs RBAC approval)"
```

---

## 5. RBAC Scoping

The SOP (§3.3) requires: *"monitoring access and provisioning access should be separate."*

### 5.1 Monitoring Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: opensearch
  name: guardian-monitor
rules:
- apiGroups: [""]
  resources: ["pods", "services", "persistentvolumeclaims"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["statefulsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["opensearch.threatgrid.io"]
  resources: ["opensearchclusters"]
  verbs: ["get", "list"]
```

### 5.2 Provisioning Role (Separate)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: opensearch
  name: guardian-provisioner
rules:
- apiGroups: ["opensearch.threatgrid.io"]
  resources: ["opensearchclusters"]
  verbs: ["get", "list", "patch"]
- apiGroups: ["apps"]
  resources: ["statefulsets"]
  verbs: ["get", "list", "patch"]
# NOTE: No delete verbs — Guardian never deletes cluster resources
```

### 5.3 Permission Detection

Guardian tests at connection time:
- `can-i get opensearchclusters` → monitoring enabled
- `can-i patch opensearchclusters` → provisioning enabled
- Report both independently in the connection profile status

---

## 6. Watch / Reconcile / Verify Loop

### 6.1 Post-Patch Watch

After Guardian patches the CR/StatefulSet:
1. **Watch CR status** — poll every 5s for `Ready` condition
2. **Watch Pod readiness** — poll every 3s for new Pods reaching `Running`
3. **Timeout** — if no new node joins within 5 minutes, surface a warning

### 6.2 OpenSearch Verification

After K8s reports the Pod is ready, Guardian switches to OpenSearch APIs:
- `GET _nodes` → confirm new node appears with correct roles
- `GET _cluster/health` → confirm green/yellow status
- `GET _cat/shards` → confirm shard allocation on new node
- `GET _cat/recovery` → confirm no abnormal recovery pressure

### 6.3 State Machine Integration (ADR-006)

The K8s watch loop maps to provisioning stages 8–11:
- **Step 8 (Observe):** Watch CR/Pod readiness
- **Step 9 (Verify join):** OpenSearch `_nodes` API
- **Step 10 (Rebalance):** Monitor shard relocation via `_cat/shards`
- **Step 11 (Validate):** Before/after comparison of health, disk, JVM, CPU

---

## 7. Dry-Run / Diff and Approval

Guardian must show the exact desired-state change before applying it (SOP §7, step 5).

### 7.1 Diff Display

For a CR patch, Guardian computes:
```diff
 spec:
   instances:
     data: 3 → 4
   resources:
     data:
       limits:
         memory: 8Gi  (unchanged)
```

For a StatefulSet patch:
```diff
 spec:
   replicas: 3 → 4
```

### 7.2 Dry-Run Execution

Guardian performs a client-side dry-run:
- Simulate the patch locally
- Validate schema (crd validation rules)
- Estimate rebalance impact (shard count × replica factor / node count)
- Surface risks: disk capacity, network bandwidth, recovery time

### 7.3 Approval Gate

The approval UI (step 6) shows:
- The diff
- Estimated cluster impact (rebalance time, disk growth)
- Rollback plan (revert to previous CR spec)
- Explicit "Approve" / "Cancel" buttons

---

## 8. Safety Constraints

Per SOP §8 and ADR-002:

1. **No destructive operations** — Guardian never deletes OpenSearchClusters, StatefulSets, or PVCs
2. **Read-only default** — Monitoring RBAC is granted by default; provisioning RBAC requires explicit enablement
3. **Version compatibility** — Preflight checks that the new node's OpenSearch version matches the cluster
4. **Cluster name validation** — New nodes must belong to the same cluster (same `cluster.name` setting)
5. **Immutable audit log** — Every patch is logged with who, when, what change, and verification evidence

---

## 9. OpenSearch Operator Documentation References

- **OpenSearch Operator CRD:** https://opensearch.org/docs/latest/install-and-configure/install-plugins/opensearch-operator/
- **Kubernetes API docs:** https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.31/
- **Controller-runtime (Operator pattern):** https://book.kubebuilder.io/

---

## 10. Summary of Decisions

| Question | Decision |
|----------|----------|
| Primary K8s interaction model | Patch OpenSearchCluster CR; never manage pods directly |
| Fallback for non-Operator clusters | Helm values patch → `helm upgrade`; raw StatefulSet replicas patch |
| Credential source | User kubeconfig context (preferred) or in-cluster SA (with consent) |
| RBAC model | Separate monitoring role (read-only) and provisioning role (patch only) |
| Verification path | K8s watch → Pod ready → OpenSearch `_nodes` / `_cluster/health` |
| Approval model | Diff view → explicit approve → apply → watch → verify → audit |

These decisions feed into **ADR-009** (Kubernetes Adapter Decision).