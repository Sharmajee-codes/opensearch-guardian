# Electron Security Posture for OpenSearch Guardian

Based on the [Electron Security Documentation](https://www.electronjs.org/docs/latest/tutorial/security) and applied to the OpenSearch Guardian architecture per SOP §4, §8, and ADR-003.

## Core Security Principles

### 1. Renderer Process Hardening
- **contextIsolation: true** (mandatory) - Prevents renderer from accessing Electron/Node.js internals
- **nodeIntegration: false** (mandatory) - Disables Node.js integration in renderer processes
- **sandbox: true** (enabled by default when contextIsolation is true) - Chromium process sandboxing
- **webPreferences**:
  - `webSecurity: true` (default) - Same-origin policy enforcement
  - `allowRunningInsecureContent: false` (default) - Blocks mixed content
  - `spellcheck: false` - Disables spellchecker to reduce attack surface

### 2. Preload Script Bridge (contextBridge)
All renderer-to-main communication must go through a tightly controlled preload script:

```javascript
// preload.js - exposed via webPreferences.preload
const { contextBridge, ipcRenderer } = require('electron');

// Expose only minimal, validated APIs to renderer
contextBridge.exposeInMainWorld('guardianAPI', {
  // Monitoring endpoints (read-only)
  getClusterHealth: () => ipcRenderer.invoke('guardian:getClusterHealth'),
  getNodeMetrics: (nodeId) => ipcRenderer.invoke('guardian:getNodeMetrics', nodeId),
  getIndexStats: () => ipcRenderer.invoke('guardian:getIndexStats'),
  
  // Configuration (validated inputs only)
  updateTheme: (theme) => ipcRenderer.invoke('guardian:updateTheme', theme),
  
  // IPC validation - renderer should NEVER receive raw ipcRenderer
  // All validation happens in main process via ipcMain.handle
});
```

### 3. Main Process IPC Contract
All IPC handlers must validate sender and use strict typing:

```javascript
// main.js - IPC handlers with validation
const { ipcMain } = require('electron');

// Typed IPC contract example
ipcMain.handle('guardian:getClusterHealth', async (event, /* no params */) => {
  // Validate sender (optional but recommended for sensitive ops)
  // if (!event.senderFrame.url.startsWith('app://')) throw new Error('Invalid sender');
  
  // No params expected - validate arity
  if (arguments.length !== 1) {
    throw new Error('Invalid argument count');
  }
  
  // Delegate to Guardian Core service (Python/FastAPI)
  // This is where actual security boundaries exist
  return await guardianCore.getClusterHealth();
});

// Example with validated parameters
ipcMain.handle('guardian:updateTheme', async (event, theme) => {
  // Validate input type and allowed values
  if (typeof theme !== 'string' || !['light', 'dark', 'system'].includes(theme)) {
    throw new Error('Invalid theme value');
  }
  
  return await guardianCore.updateTheme(theme);
});
```

### 4. Content Security Policy (CSP)
Implement restrictive CSP via HTTP headers or meta tag:

```http
Content-Security-Policy: 
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self';
  connect-src 'self' ws: wss:; /* WebSocket/SSE to core service */
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
```

Or via meta tag in index.html:
```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' ws: wss:; frame-ancestors 'none';">
```

### 5. Secrets and Credentials Management
Per SOP §8 and §4:
- **Never store secrets in renderer** - All credentials remain in main process
- **Use OS credential stores** - macOS Keychain, Windows Credential Locker, Linux Secret Service
- **Redact from logs/dumps** - Ensure credentials never appear in:
  - Console logs
  - Crash reports
  - DevTools output
  - Error boundaries
  - Telemetry (if any)

Implementation pattern:
```javascript
// main.js - Secure credential handling
const { ipcMain } = require('electron');
const { getCredentials, storeCredentials } = require('./credentialStore'); // Uses native OS APIs

ipcMain.handle('guardian:getCredentials', async (event, serviceName) => {
  // Validate serviceName
  if (typeof serviceName !== 'string') throw new Error('Invalid service');
  
  // Never return raw credentials to renderer
  // Instead, return only what's needed for API calls (tokens, etc.)
  const creds = await getCredentials(serviceName);
  return {
    hasCredentials: !!creds,
    // Return non-sensitive metadata only
    username: creds?.username || '', 
    // Actual token/password stays in main process
  };
});

// Actual credential usage happens in main process only
ipcMain.handle('guardian:testConnection', async (event, connectionConfig) => {
  // Validate connectionConfig structure
  const creds = await getCredentials(connectionConfig.serviceName);
  if (!creds) throw new Error('Credentials not found');
  
  // Use credentials HERE in main process - never expose to renderer
  return await openSearchClient.testConnection({
    ...connectionConfig,
    username: creds.username,
    password: creds.password // Never leaves main process
  });
});
```

### 6. Shell and Subprocess Safety
- **Never call shell.execute or shell.openExternal from renderer**
- **Validate all URLs before shell.openExternal** (if used in main process)
- **Avoid child_process usage** - If necessary, validate all inputs and use strict allowlists

```javascript
// main.js - Safe shell usage example
ipcMain.handle('guardian:openDocs', async (event, docPath) => {
  // Validate docPath is from known safe set
  const allowedPaths = ['/getting-started', '/api-reference', '/troubleshooting'];
  if (!allowedPaths.includes(docPath)) {
    throw new Error('Invalid documentation path');
  }
  
  // Only then use shell - still in main process
  const { shell } = require('electron');
  return shell.openExternal(`https://docs.opensearch.org${docPath}`);
});
```

### 7. Update and Code Signing Posture
- **Auto-update mechanism** - Use electron-builder or electron-updater with:
  - Signed updates (required for production)
  - Version validation
  - Rollback capabilities
- **Code signing** - All builds must be signed with:
  - Developer ID Application (macOS)
  - Authenticode (Windows)
  - AppImage/Linux signing as appropriate
- **Dependency verification** - Regular npm audit and dependency checking

### 8. Additional Hardening Measures
- **Disable deprecated APIs** - `allowRunningInsecureContent`, `webviewTag`, etc.
- **Session permission handling** - Implement handlers for:
  - `will-navigate` - Validate navigation targets
  - `new-window` - Restrict or validate new window creation
  - `permission-request` - Strictly control permission grants
- **Regular dependency updates** - Keep Electron, Node.js, and Chromium current

## OpenSearch Guardian Specific Applications

### IPC Boundary Design (SOP §4 Diagram)
```
Renderer (React)  ←[contextBridge]→  Preload Script  ←[ipcMain.handle]→  Main Process
        ↓                                                      ↓
  UI Components                                    Guardian Core Service (Python/FastAPI)
                                                      ↓
                                          OpenSearch / Docker / Kubernetes APIs
```

### Data Flow Security
1. **Rendering Layer** - Pure React/TypeScript, zero privileged access
2. **Preload Bridge** - Exposes only explicitly allowed guardianAPI methods
3. **Main Process** - Validates all IPC, handles credentials/secrets
4. **Core Service** - Python/FastAPI with its own security boundary
5. **External APIs** - OpenSearch REST, Docker Engine, Kubernetes (all with TLS/auth)

### No Secrets in Renderer - Enforced By
- All @AppStorage/@UserDefaults equivalents secured in main process
- Connection strings/API keys never cross IPC boundary
- HealthKit/WatchConnectivity equivalents (if any) handled in main process
- Any native module access restricted to main process

## Compliance Verification Checklist

For each renderer window/webView:
- [ ] contextIsolation: true
- [ ] nodeIntegration: false
- [ ] sandbox: true (implicit)
- [ ] preload script defined
- [ ] No direct require('electron') or remote module usage
- [ ] CSP header/meta tag present
- [ ] No shell.* calls in renderer code
- [ ] No process.* or require.* calls in renderer
- [ ] All IPC goes through contextBridge-exposed API
- [ ] No inline event handlers in HTML (mitigates XSS)

For main process:
- [ ] All ipcMain handlers validate sender (where appropriate)
- [ ] All ipcMain handlers validate input parameters
- [ ] Credentials/secrets only accessed in main process
- [ ] No arbitrary shell command execution
- [ ] All file system access validated and restricted
- [ ] Update mechanism uses signed packages
- [ ] Dependencies regularly audited

## References
- Electron Security Tutorial: https://www.electronjs.org/docs/latest/tutorial/security
- contextBridge Documentation: https://www.electronjs.org/docs/latest/api/context-bridge
- IPC Security Guidelines: https://www.electronjs.org/docs/latest/tutorial/ipc#security-considerations
- CSP Reference: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy
- SOP §4: Proper Implementation Architecture
- SOP §8: Security and Safety Requirements
- ADR-003: Technology Stack