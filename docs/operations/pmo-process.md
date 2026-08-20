# PMO Process

## Overview
This document defines the Project Management Office (PMO) processes for the OpenSearch Guardian project, including task management, status reporting, review cycles, and release management.

## Governance Structure

### Roles and Responsibilities

| Role | Agent | Responsibilities |
|------|-------|------------------|
| **Project Lead** | god | Overall direction, task assignment, final decisions |
| **PMO Coordinator** | kelly-mt0d89bk | Status consolidation, dashboard maintenance, communication |
| **Backend Lead** | kevin-mszwzzlo | Backend plugin architecture, SPI, collection services |
| **Security Lead** | angela-mszx0wm5 | Security integration, RBAC, permissions |
| **Documentation Lead** | pam-mszwz30z | Documentation, guides, release automation |
| **Provisioning Lead** | dwight-mszwzfte | Provisioning engine, Doctor rules integration |
| **Frontend Lead** | meredith-mt02f5qz | Dashboards plugin, UI components |
| **QA Lead** | jim-mszwyrge | Test strategy, integration tests |
| **Shared Logic Lead** | stanley-mt02ls7u | Optimizer, capacity, safety validation |
| **UI/Visualization Lead** | andy-mt02hg1j | UI components, visualizations, QA |
| **Code Review** | phyllis-mt02hwxa | Peer review coordination, approval |

### Workstreams
1. **PMO** - Project management and reporting
2. **Backend Plugin** - Core plugin SPI and services
3. **Security** - Authentication, authorization, RBAC
4. **Documentation** - Guides, API docs, runbooks
5. **Release** - CI/CD, SBOM, signing, publishing
6. **Provisioning** - Engine adaptation, Doctor rules
7. **Frontend Plugin** - Dashboards plugin, UI
8. **Testing** - Unit, integration, e2e tests
9. **Shared Logic** - Optimizer, capacity, safety
10. **UI/Visualization** - Components, charts, QA

## Task Management

### Task Lifecycle
```
NOT STARTED → IN PROGRESS → REVIEW → DONE
                ↓
             BLOCKED (if impeded)
```

### Task Assignment
- Tasks assigned by god via inbox messages
- Each task has: ID, title, assignee, reviewer, dependencies, phase, workstream
- Tasks tracked in PMO Status Dashboard (`pmo-status-report.html`)

### Dependency Management
- Tasks declare dependencies in `deps` field
- Blocked tasks cannot start until dependencies are DONE
- Circular dependencies must be resolved immediately

### Status Updates
- Agents update status via inbox messages to PMO
- PMO consolidates weekly (T58)
- Dashboard auto-refreshes from task data

## Status Reporting

### Weekly Status Report (T58)
**Frequency**: Every Monday 09:00 UTC
**Contents**:
- Requirements received from god
- Assignments distributed
- Completed tasks (DONE)
- In-progress work (IN PROGRESS)
- Blockers (BLOCKED)
- Upcoming priorities

**Output**: Updated `docs/operations/pmo-status-report.html`

### Dashboard Maintenance
- PMO updates task data in dashboard HTML
- Peer review comments aggregated automatically
- Documentation links verified monthly

### Escalation Process
1. Agent identifies blocker → messages god
2. god assigns resolution or re-prioritizes
3. PMO updates dashboard with blocker status
4. Resolution tracked to completion

## Review Cycles

### Peer Review (Every 4 Hours)
- Each agent reviews at least one peer's work
- Submit via `peer-review-comments` conversation
- Format: task_id, reviewed_agent, review_type, opinion, details
- phyllis-mt02hwxa coordinates and aggregates

### Code Review
- All PRs require review from phyllis-mt02hwxa
- At least one domain expert review
- Security changes require angela-mszx0wm5 approval

### Architecture Review
- Major changes require ADR
- ADR reviewed by god + relevant leads
- Documented in `docs/adr/`

## Release Management

### Release Criteria
- All quality gates pass (CI)
- SBOM generated and signed
- CHANGELOG updated
- VERSION file matches tag
- Documentation updated

### Release Process
1. Create release branch from main
2. Update VERSION and CHANGELOG
3. Tag release: `v<major>.<minor>.<patch>`
4. CI builds, tests, signs artifacts
5. GitHub Release created automatically
6. Artifacts published to Maven, Docker, Helm
7. Announce via project channels

### Versioning (SemVer)
- MAJOR: Breaking changes, plugin API changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes, security patches

See [Versioning Strategy](versioning.md) for details.

## Communication

### Channels
- **Inbox messages**: Formal task assignment, decisions
- **Peer review comments**: Structured feedback
- **Dashboard**: Real-time status visibility

### Meeting Cadence
- Daily standup: Async via status updates
- Weekly sync: Monday with god (requirements)
- Sprint review: End of each phase
- Retrospective: Monthly

## Risk Management

### Risk Register
Tracked in PMO dashboard:
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Plugin API instability | Medium | High | Version compatibility matrix |
| Security audit findings | Low | Critical | Continuous scanning |
| Resource constraints | Medium | Medium | Cross-training, priority queue |
| Dependency vulnerabilities | High | Medium | Weekly dependency check |

### Issue Tracking
- GitHub Issues for bugs/features
- Linked to tasks in dashboard
- Prioritized by god

## Continuous Improvement

### Process Reviews
- Monthly retrospective
- Action items tracked as tasks
- Process docs updated accordingly

### Metrics
- Task cycle time (NOT STARTED → DONE)
- Peer review coverage
- Release frequency
- Defect escape rate

## Tools
- **Task Tracking**: PMO Status Dashboard (HTML)
- **Code**: GitHub (PRs, Issues, Actions)
- **Documentation**: Markdown in `docs/`
- **CI/CD**: GitHub Actions workflows
- **Communication**: Hive inbox/outbox

## Related Documentation
- [SOP](SOP.md) - Standard Operating Procedures
- [Roadmap](roadmap.md) - Project roadmap
- [Versioning](versioning.md) - Release versioning
- [Release Hardening](release.md) - Release procedures