# Security Policy

## Reporting Security Vulnerabilities

OpenSearch Guardian takes security seriously. If you discover a security vulnerability within the project, please report it privately to maintainers through one of the following channels:

- **Preferred**: Email security@opensearch-guardian.org
- **Alternative**: Open a private vulnerability report on GitHub (if available)
- **Last resort**: Direct message to project maintainers on GitHub

Please do **not** open public issues for security vulnerabilities.

## What to Include

When reporting a security issue, please include:

- A clear description of the vulnerability
- Steps to reproduce the issue
- Affected versions or components
- Potential impact
- Any proof-of-concept code or exploit details (if safe to share)

## Response Process

Our security team will:

1. Acknowledge receipt of your report within 48 hours
2. Investigate the issue and determine its validity and severity
3. Keep you informed of progress throughout the process
4. Coordinate a fix and disclosure timeline
5. Credit you in security advisories (if desired)

## Secrets and Credentials Policy

As outlined in the OpenSearch Guardian SOP section 8:

- **Read-only is the default connection mode**
- Separate monitoring permissions from provisioning/remediation permissions
- Store secrets in OS keychain/credential vault; redact them from logs, crash reports, exports, and diagnostics
- TLS certificate validation is enabled by default
- No arbitrary command execution from the renderer
- Use explicit allow-listed operations for Docker/Kubernetes/OpenSearch mutations
- Classify recommendations: Informational, Safe/Reversible, Approval Required, Destructive
- V1 must not autonomously delete indices, PVCs, nodes, snapshots, or other data-bearing resources
- Provide a dry-run/diff view for infrastructure changes
- Audit all write operations and retain before/after state

## Security Best Practices

OpenSearch Guardian follows these security principles:

- Principle of least privilege for all operations
- Defense in depth for critical operations
- Secure by default configurations
- Regular dependency scanning and updates
- Continuous security monitoring
- Transparent security disclosure process

## Supported Versions

Security updates will be provided for the current stable release and the previous major version.

## Contact

For security-related inquiries, please contact: security@opensearch-guardian.org