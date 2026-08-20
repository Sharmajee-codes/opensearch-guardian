# Documentation Index

## Overview
Complete index of all OpenSearch Guardian documentation organized by category.

## Architecture & ADRs

### Architecture Decision Records
- [ADR-001: Project Structure](adr/ADR-001.md)
- [ADR-002: Technology Stack](adr/ADR-002.md)
- [ADR-003: Authentication & Authorization](adr/ADR-003.md)
- [ADR-004: Collection Architecture](adr/ADR-004.md)
- [ADR-005: Tiered Collection Cadence](adr/ADR-005.md)
- [ADR-006: Safety Engine Design](adr/ADR-006.md)
- [ADR-007: Release & Distribution Strategy](adr/ADR-007.md)
- [ADR-008: Architecture Migration](adr/ADR-008.md)
- [ADR-009: Plugin Architecture](adr/ADR-009.md)
- [ADR-010: Observability Strategy](adr/ADR-010.md)
- [ADR-011: Release & Distribution](adr/ADR-011.md)

### Architecture Documents
- [Desktop Architecture](architecture/desktop-architecture.md)
- [Data Model](architecture/data-model.md)
- [Doctor Rules Engine](architecture/doctor-rules.md)
- [Security & Safety Engine](architecture/security-safety-engine.md)
- [Connection & Collection](architecture/connection-and-collection.md)
- [Component Contract](architecture/component-contract.md)
- [Migration Report](architecture/migration-report.md)

### Research Artifacts
- [OpenSearch APIs](architecture/research/opensearch-apis.md)
- [Kubernetes Provisioning](architecture/research/kubernetes-provisioning.md)
- [Electron Security](architecture/research/electron-security.md)
- [Licensing Stack & Compliance](architecture/research/licensing-stack.md)

## Implementation Guides

### Plugin Development
- [Backend Plugin Development Guide](plugins/backend-plugin-development.md)
- [Frontend Plugin Development Guide](plugins/frontend-plugin-development.md)
- [Migration Guide](plugins/migration-guide.md)

### Research Guides
- [OpenSearch Dashboards Plugin Research](research/opensearch-dashboards-plugin.md)
- [OpenSearch Backend Plugin Research](research/opensearch-backend-plugin.md)
- [OpenSearch Security Integration](research/opensearch-security-integration.md)
- [Plugin Packaging & Distribution](research/plugin-packaging-distribution.md)

## Security & Safety

- [Security Engine Architecture](architecture/security-safety-engine.md)
- [OpenSearch Security Integration](research/opensearch-security-integration.md)
- [Licensing Stack & Compliance](architecture/research/licensing-stack.md)

## Release & Operations

### Release Management
- [Release Hardening Guide](release.md)
- [Versioning Strategy](versioning.md)
- [Release Automation Guide](../plugins/release-automation.md)
- [CI/CD Credentials & Secrets](credentials.md)

## Testing

- [Test Strategy](testing/strategy.md)
- [Test Runbook](testing/test-runbook.md)
- [Integration Test Plan](testing/integration-plan.md)

## External Resources

### OpenSearch Documentation
- [OpenSearch Plugin Development](https://opensearch.org/docs/latest/plugins/)
- [OpenSearch Dashboards Plugins](https://opensearch.org/docs/latest/dashboards/plugins/)
- [OpenSearch Security](https://opensearch.org/docs/latest/security-plugin/)

### Standards & Compliance
- [CycloneDX SBOM Specification](https://cyclonedx.org/specification/overview/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)

## Document Status

| Document | Status | Last Updated | Owner |
|----------|--------|--------------|-------|
| ADR-001 to ADR-011 | ✅ Complete | 2024-01 | Architecture |
| Architecture Docs | ✅ Complete | 2024-01 | Architecture |
| Backend Plugin Guide | ✅ Complete | 2024-01 | Kevin |
| Frontend Plugin Guide | ✅ Complete | 2024-01 | Meredith |
| Migration Guide | ✅ Complete | 2024-01 | Pam |
| Doctor Runbook | ✅ Complete | 2024-01 | Pam |
| Admin Guide | ✅ Complete | 2024-01 | Pam |
| User Guide | ✅ Complete | 2024-01 | Pam |
| Quickstart Guide | ✅ Complete | 2024-01 | Pam |
| PMO Process | ✅ Complete | 2024-01 | Kelly |
| Release Hardening | ✅ Complete | 2024-01 | Pam |
| Versioning | ✅ Complete | 2024-01 | Pam |
| API Documentation | ✅ Complete | 2026-08-20 | Pam |

## Contributing to Documentation

### Adding New Documents
1. Create `.md` file in appropriate directory
2. Follow existing formatting conventions
3. Add entry to this index
4. Update PMO dashboard links if needed

### Style Guide
- Use Markdown with frontmatter for metadata
- Include table of contents for long documents
- Use relative links for internal references
- Include code examples where applicable
- Keep line length reasonable for diffs

### Review Process
1. Submit PR with documentation changes
2. Assign to Documentation Lead (pam-mszwz30z)
3. Peer review for accuracy
4. Merge after approval

---

*Last updated: 2026-08-20*
*Maintained by: Documentation Lead (pam-mszwz30z)*