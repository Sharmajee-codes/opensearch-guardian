# Release Hardening Guide

This document outlines the release hardening practices for OpenSearch Guardian, covering CI/CD, SBOM generation, artifact signing, and release documentation.

## Release Process Overview

A hardened release for OpenSearch Guardian includes:
1. Continuous Integration (CI) pipeline with security scanning
2. Software Bill of Materials (SBOM) generation
3. Release artifact signing (checksums and GPG)
4. Comprehensive release documentation
5. Dependency and license compliance verification
6. Secret scanning and CVE vulnerability checks

## CI/CD Pipeline (.github/workflows/ci.yml)

The recommended CI workflow performs the following checks on every push and pull request:

### Security Scanning
- Dependency license compliance (`pip-licenses`, `license-checker`)
- CVE vulnerability scanning (`safety`, `npm audit`)
- Secret detection (`gitleaks`, `trufflehog`)
- Supply chain security review (`deps.dev` ossf)

### Quality Gates
- License header verification
- Code formatting and linting
- Unit and integration tests
- Build verification for all supported platforms

### Release Preparation
- SBOM generation (CycloneDX JSON format)
- Artifact packaging and checksum generation
- GPG signing of release artifacts (when maintaining keys)

## SBOM Generation

Every release must include a Software Bill of Materials (SBOM) listing all dependencies and their licenses.

### Tooling
- **Primary**: Syft (https://github.com/anchore/syft)
- **Format**: CycloneDX JSON (recommended for OSS projects)
- **Placement**: `releases/<version>/SBOM.json`

### Generation Commands
```bash
# Generate SBOM for the full application
syft . -o cyclonedx-json > SBOM.json

# Filter to production dependencies only (recommended)
syft . --scope production -o cyclonedx-json > SBOM.json

# Generate human-readable summary
syft . -o table > SBOM-summary.txt
```

### SBOM Contents
The SBOM should include:
- All direct and transitive dependencies
- License information for each component
- Version identifiers
- Package URLs (PURLs) where available
- Copyright information

## Release Signing

Release artifacts should be signed to ensure integrity and authenticity.

### Checksums
Generate SHA256 checksums for all release artifacts:
```bash
sha256sum opensearch-guardian-* > checksums.txt
```

### GPG Signing
Sign the checksums file with project maintainer's GPG key:
```bash
gpg --detach-sign --armor checksums.txt
```

This produces `checksums.txt.asc` which can be verified with:
```bash
gpg --verify checksums.txt.asc
```

## Release Documentation

Each release should include the following documentation in the `releases/<version>/` directory:

1. **RELEASE-NOTES.md** - User-facing release notes
2. **CHANGELOG.md** - Detailed technical changelog
3. **UPGRADE-GUIDE.md** - Migration instructions (if applicable)
4. **SBOM.json** - Software Bill of Materials
5. **checksums.txt** - SHA256 hashes of all artifacts
6. **checksums.txt.asc** - GPG signature of checksums
7. **LICENSES/** - Directory containing full license texts of all dependencies

## Release Checklist

Before publishing a release, verify the following:

### Mandatory Checks (Block Release if Failing)
- [ ] All dependencies use approved licenses (MIT, BSD, Apache-2.0, ISC, Public Domain)
- [ ] No GPL/AGPL/LGPL dependencies without explicit legal review
- [ ] SBOM generated and included in release artifacts
- [ ] Secret scanning passes (zero detections)
- [ ] CVE scan passes (no critical/high vulnerabilities)
- [ ] NOTICE file present and includes trademark disclaimer
- [ ] README.md includes trademark disclaimer
- [ ] LICENSE file present at repository root
- [ ] CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, SUPPORT.md, GOVERNANCE.md all present
- [ ] Release artifacts built for all supported platforms (macOS, Windows, Linux)
- [ ] Electron app properly packaged and notarized (where applicable)

### Recommended Checks (Document if Skipped)
- [ ] Reproducible build documentation exists
- [ ] Release signed with GPG key
- [ ] Checksums published for all release artifacts
- [ ] Changelog updated with dependency changes
- [ ] ADR-007 reviewed and still accurate
- [ ] Release notes written for end users
- [ ] Upgrade guide provided for breaking changes
- [ ] Docker images built and pushed (if applicable)
- [ ] Homebrew formula updated (if applicable)

## Dependency Scanning Policy

Per SOP §8 and ADR-007, the project must:

1. Run dependency license checks on every PR
2. Block merges if prohibited licenses are detected (GPL, AGPL, LGPL)
3. Review dependencies requiring special attention (SSPL, BSL, MPL-2.0)
4. Document the scanning process in SECURITY.md
5. Rotate any accidentally committed credentials
6. Maintain an audit trail of dependency changes

### Approved Licenses
- MIT, BSD-2/3, Apache-2.0, ISC, Public Domain

### Review Required
- SSPL, BSL, MPL-2.0, LGPL with dynamic linking

### PROHIBITED
- GPL, AGPL, LGPL (unless statically linked with explicit compliance)

## Secret Scanning

Secret scanning must be performed on every push and PR:

### Tools
- `gitleaks` - Primary secret detection tool
- `trufflehog` - Alternative/complementary secret scanner

### Policy
- Block merges if high-confidence secrets are detected
- Rotate any accidentally committed credentials immediately
- Document the scanning process and frequency in SECURITY.md
- Include secret scanning in pre-release checklist

## Trademark Compliance

All release materials must comply with OpenSearch trademark policy:

### Required Disclaimers
Include the following in all public-facing release materials:
> "OpenSearch is a trademark of Amazon Web Services. OpenSearch Guardian is not affiliated with or endorsed by the OpenSearch Project or Amazon Web Services."

### Documentation Requirements
- README.md must include trademark disclaimer
- Release notes must include trademark disclaimer
- Website and promotional materials must include trademark disclaimer
- NOTICE file must contain appropriate attribution

## Release Artifacts Structure

For each version `vX.Y.Z`, the release directory should contain:
```
releases/vX.Y.Z/
├── opensearch-guardian-darwin-arm64.zip      # macOS ARM64
├── opensearch-guardian-darwin-x64.zip        # macOS Intel
├── opensearch-guardian-linux-arm64.zip       # Linux ARM64
├── opensearch-guardian-linux-x64.zip         # Linux Intel
├── opensearch-guardian-win-arm64.zip         # Windows ARM64
├── opensearch-guardian-win-x64.zip           # Windows Intel
├── SBOM.json                                 # Software Bill of Materials
├── checksums.txt                             # SHA256 hashes
├── checksums.txt.asc                         # GPG signature of checksums
├── RELEASE-NOTES.md                          # User release notes
├── CHANGELOG.md                              # Technical changelog
├── UPGRADE-GUIDE.md                          # Migration guide (if needed)
└── LICENSES/                                 # Full license texts
    ├── dependency-1-LICENSE
    ├── dependency-2-LICENSE
    └── ...
```

## Automation

The CI workflow (`.github/workflows/ci.yml`) automates:
- Dependency scanning
- License compliance checking
- SBOM generation
- Build artifact creation
- Checksum generation
- Basic quality gates (lint, test, etc.)

Manual steps for release maintainers:
1. Tag the release commit (`git tag vX.Y.Z`)
2. Push tags (`git push --tags`)
3. Verify CI workflow completed successfully
4. Download artifacts from CI workflow run
5. Generate checksums and sign them
6. Upload all artifacts to GitHub release
6. Add release notes and trademark disclaimer
7. Publish the release

## References

- SOP §9 — Open-Source Strategy
- SOP §12 — Future Scope
- ADR-007 — Open-Source Strategy
- Licensing Stack & OSS Compliance research document
- Syft SBOM Generator: https://github.com/anchore/syft
- CycloneDX SBOM Specification: https://cyclonedx.org/
- OpenSearch Trademark Policy: https://github.com/opensearch-project/.github/blob/main/TRAD.markdown