# Versioning Policy

This document defines how OpenSearch Guardian manages versions, tags, and releases.

## SemVer

OpenSearch Guardian follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality
- **PATCH** version for backwards-compatible bug fixes

### Bump Rules

| Change Type | Bump |
|-------------|------|
| Incompatible API change | MAJOR |
| New feature (backwards-compatible) | MINOR |
| Bug fix (backwards-compatible) | PATCH |
| Documentation-only change | PATCH |
| Dependency update (no behavior change) | PATCH |
| New milestone/phase delivery | MINOR or MAJOR depending on scope |

### Pre-releases

Pre-release versions follow the format `v0.1.0-alpha.1`, `v0.1.0-beta.1`, etc. Use pre-releases for:
- Release candidates
- Nightly builds
- Feature branches exposed to testers

## Version File

A `VERSION` file at the repository root contains the current version as a plain semver string (e.g., `0.1.0`). This file is:
- Updated at the same time as the CHANGELOG entry
- Checked by CI quality-gates to ensure tag matches VERSION
- Read by build scripts to set the application version

## Changelog

The project uses [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. Every release must have:
- A `## [vX.Y.Z] — YYYY-MM-DD` section
- Categorized changes under Added/Changed/Deprecated/Removed/Fixed/Security
- A link to the full release notes if applicable

## Release Workflow

1. **Commit**: Update `VERSION` and `CHANGELOG.md` together in a single commit
2. **Tag**: Create an annotated tag `git tag -a v0.1.0 -m "v0.1.0 description"`
3. **Push**: Push main and tags: `git push origin main --tags`
4. **Release**: GitHub Actions (`release.yml`) triggers automatically on tag push
5. **Verification**: Confirm the GitHub Release was created with all artifacts

### Manual Release (if CI unavailable)

```bash
git tag -a v0.1.0 -m "v0.1.0 baseline"
git push origin main --tags
gh release create v0.1.0 --title "v0.1.0" --notes-file CHANGELOG.md
```

## Milestones

Release milestones align with the project roadmap (see `docs/operations/roadmap.md`). Each milestone includes:
- A CHANGELOG entry with the milestone scope
- A VERSION bump
- A git tag
- A GitHub Release with artifacts and SBOM

## Governance

- Release approvals follow the project GOVERNANCE.md process
- Maintainers review CHANGELOG entries before merge
- Breaking changes require ADR documentation
- Security releases follow the responsible disclosure process in SECURITY.md

## References

- SemVer 2.0.0: https://semver.org/spec/v2.0.0.html
- Keep a Changelog: https://keepachangelog.com/en/1.1.0/
- SOP §11 — Delivery Roadmap
- ADR-007 — Open-Source Strategy