# T73/T74 — Angular Support Assessment

Scope: support area for T73 (UI Component Implementation) and T74 (Visualization Integration) in the OpenSearch Guardian frontend plugin area under `frontend/src/plugins/guardian/`.

## Finding
The canonical plugin code is implemented as standard React (JSX/TSX) modules plus a service facade, not Angular. There is no Angular app bootstrap, NgModule, standalone component decorators, Angular router config, or Angular service pattern in the plugin tree under review. Therefore, Angular support is absent; Angular migration or co-implementation would require a parallel or replacement UI layer.

## Reviewed paths (relative to repo root)
- `frontend/src/plugins/guardian/src/App.tsx`
- `frontend/src/plugins/guardian/src/pages/*.tsx`
- `frontend/src/plugins/guardian/src/components/*.jsx`
- `frontend/src/plugins/guardian/src/services/apiService.js`
- `frontend/src/plugins/guardian/plugin-manifest.json`
- `frontend/src/plugins/guardian/package.json`

## Per-file status
- `App.tsx` — present; React root render; no Angular adapter detected.
- `pages/Overview.tsx` — 107L; React view; no Angular component.
- `pages/Nodes.tsx` — 126L; React view; no Angular component.
- `pages/Shards.tsx` — 109L; React view; no Angular component.
- `pages/Indices.tsx` — 103L; React view; no Angular component.
- `pages/Doctor.tsx` — 263L; React view; no Angular component.
- `pages/Optimizer.tsx` — 321L; React view; no Angular component.
- `pages/Capacity.tsx` — 182L; React view; no Angular component.
- `pages/LiveMonitoring.tsx` — 263L; React view; no Angular component.
- `pages/Findings.tsx` — 310L; React view; no Angular component.
- `pages/Recommendations.tsx` — 329L; React view; no Angular component.
- `pages/AdminSettings.tsx` — 396L; React view; no Angular component.
- `components/ClusterHealthChart.jsx` — 58L; React visualization; no Angular wrapper.
- `components/NodeMetricsChart.jsx` — 38L; React visualization; no Angular wrapper.
- `components/ShardAllocationChart.jsx` — 59L; React visualization; no Angular wrapper.
- `components/CapacityProjectionChart.jsx` — 81L; React visualization; no Angular wrapper.
- `components/OptimizerSavingsChart.jsx` — 43L; React visualization; no Angular wrapper.
- `services/apiService.js` — 201L; JS module; Angular-style service decorators/rxjs patterns not present; direct fetch/axios-style usage expected.
- `plugin-manifest.json` — plugin metadata only; no Angular framework declaration detected.
- `package.json` — plugin `name/version` and dependencies visible; no Angular package scope or CLI dependency seen.

## ClusterExplorer / DoctorView / OptimizerView mapping
Area: UI pages and chart components listed above provide the effective ClusterExplorer, DoctorView, and OptimizerView equivalents in React. If Angular support is required, each would need a corresponding Angular component and routing entry; none currently exist.

## Gap summary
- Angular bootstrap/root: missing.
- Angular router config: missing.
- Angular service layer replacing `services/apiService.js`: missing.
- Angular equivalents for the 12 page/components above: missing.

## Recommendation / verdict
Adopt the React implementation as the canonical frontend for T73/T74. Angular support should be tracked as a future parallel effort, beginning with a minimal Angular shell/bridge shell only if a downstream product requirement explicitly mandates it.