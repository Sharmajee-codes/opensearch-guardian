# Release Automation Guide

## Overview
This guide covers the automated release pipeline for OpenSearch Guardian plugins, including CI/CD workflows, SBOM generation, artifact signing, and multi-channel publishing.

## Release Pipeline Architecture

### Workflow Overview
```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Push      │   │  Quality    │   │    Build    │   │   Release   │
│   Tag       │───▶│   Gates     │───▶│   Plugins   │───▶│  Assembly   │
│  (v*)       │   │             │   │             │   │             │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
      │                │                 │                 │
      ▼                ▼                 ▼                 ▼
  Trigger         License,          Backend:         GitHub
  Release         Security,      Gradle build,      Release,
  Pipeline       Dependency       Frontend:        SBOMs,
                 Checks          npm build        Checksums,
                                           Tests         Signatures
```

### GitHub Actions Workflows

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| CI | `.github/workflows/ci.yml` | PR, push, schedule | Security, tests, SBOM (tags) |
| OpenSearch Plugin CI | `.github/workflows/opensearch-plugin-ci.yml` | PR, push, tags, schedule | **Consolidated**: Backend security/test/build, Frontend security/test/build, Integration tests, SBOM, Release |
| Release | `.github/workflows/release.yml` | Version tags | Quality gates, assemble, publish |

**Note:** The backend and frontend plugin workflows are now consolidated into a single `opensearch-plugin-ci.yml` for better cross-platform coordination and shared dependency management.

## Quality Gates

### Pre-Release Checks (run on every tag)
1. **VERSION file validation** - Must match git tag
2. **CHANGELOG entry** - Must have entry for version
3. **License compliance** - No GPL/AGPL/LGPL dependencies
4. **Security scan** - No critical/high CVEs (safety + npm audit)
5. **Unit tests** - All tests pass
6. **Integration tests** - Mock server tests pass

### Enforcement
Quality gates run in `release.yml` as `quality-gates` job and must pass before build proceeds.

## Building Plugins

### Backend Plugin (Gradle)
```bash
# Local build
cd backend
./gradlew clean build buildPluginZip

# Output: build/distributions/guardian-<version>.zip
# Run tests
./gradlew test
```

### Frontend Plugin (npm)
```bash
# Local build
cd frontend/src/plugins/guardian
npm install
npm run build

# Output: target/guardian-<version>.zip
# Run tests
npm test
```

## SBOM Generation

### Tool: Syft (Anchore)
Generates CycloneDX JSON format SBOMs for supply chain transparency.

### Generation Process
```bash
# Install Syft
curl -sSfL https://raw.githubusercontent.com/anchore/sbom-action/install.sh | sh -s -- -b /usr/local/bin v0.80.0

# Generate for backend plugin
unzip guardian-<version>.zip -d plugin-extract
syft plugin-extract/guardian-* -o cyclonedx-json > sbom-backend.json
syft plugin-extract/guardian-* -o table > sbom-backend.txt

# Generate for frontend plugin
unzip guardian-dashboards-<version>.zip -d plugin-extract
syft plugin-extract/guardian-* -o cyclonedx-json > sbom-frontend.json
syft plugin-extract/guardian-* -o table > sbom-frontend.txt
```

### SBOM Contents
- All transitive dependencies
- Package names, versions, licenses
- CPE identifiers for vulnerability matching
- Build metadata (timestamp, tool version)

### CI Integration
SBOMs generated automatically in:
- `ci.yml` → `sbom` job (on tags)
- `backend-plugin.yml` → `sbom` job
- `frontend-plugin.yml` → `sbom` job
- `release.yml` → `generate-sbom` job

## Artifact Signing

### Checksums
SHA256 checksums generated for all release artifacts:
```bash
find . -name "guardian-*.zip" -exec sha256sum {} \; > checksums.txt
```

### GPG Signing
```bash
# Import private key (in CI from secrets)
echo "$GPG_PRIVATE_KEY" | gpg --import

# Sign checksums
gpg --batch --yes --detach-sign --armor checksums.txt
# Output: checksums.txt.asc
```

### Verification
```bash
# Verify signature
gpg --verify checksums.txt.asc checksums.txt

# Verify checksums
sha256sum -c checksums.txt
```

### CI Configuration
- GPG key stored in GitHub Secrets (`GPG_PRIVATE_KEY`)
- Key ID in `GPG_KEY_ID`
- Passphrase in `GPG_PASSPHRASE`
- Fallback: placeholder signature if secrets not configured

## Publishing Channels

### 1. GitHub Releases
Primary distribution channel for plugin ZIPs.

**Assets included:**
- `guardian-<version>.zip` (backend)
- `guardian-dashboards-<version>.zip` (frontend)
- `checksums.txt` + `checksums.txt.asc`
- `sbom-backend.json`, `sbom-frontend.json`

### 2. Maven Central (Backend)
Publishes backend plugin JAR to Maven Central via Sonatype OSSRH.

**Configuration (backend/build.gradle):**
```groovy
publishing {
    publications {
        mavenJava(MavenPublication) {
            from components.java
            artifactId = 'guardian-plugin'
            // ... pom configuration
        }
    }
    repositories {
        maven {
            name = "sonatype"
            url = version.endsWith('SNAPSHOT') 
                ? "https://oss.sonatype.org/content/repositories/snapshots"
                : "https://oss.sonatype.org/service/local/staging/deploy/maven2/"
            credentials {
                username = System.getenv('MAVEN_USERNAME')
                password = System.getenv('MAVEN_PASSWORD')
            }
        }
    }
}
signing {
    required { project.hasProperty('publish') }
    sign publishing.publications.mavenJava
}
```

**CI Credentials (GitHub Secrets):**
- `MAVEN_USERNAME` / `MAVEN_PASSWORD` (Sonatype credentials)
- `GPG_KEY_ID` / `GPG_PASSPHRASE` (for signing)

**Commands:**
```bash
./gradlew publish -Psigning.gnupg.keyId=$GPG_KEY_ID -Psigning.gnupg.passphrase=$GPG_PASSPHRASE
```

### 3. Docker Images (GHCR)
Docker images with pre-installed Guardian plugin.

**Dockerfile:**
```dockerfile
FROM opensearchproject/opensearch:2.14.0
COPY guardian-*.zip /tmp/guardian.zip
RUN bin/opensearch-plugin install file:///tmp/guardian.zip
```

**CI Build & Push:**
```bash
docker build -t ghcr.io/opensearch-guardian/opensearch-guardian:<version> .
echo "$CR_PAT" | docker login ghcr.io -u <actor> --password-stdin
docker push ghcr.io/opensearch-guardian/opensearch-guardian:<version>
```

### 4. Helm Charts (Kubernetes)
Helm chart for deploying OpenSearch with Guardian via Operator.

**Chart Structure:**
```
helm-chart/
└── opensearch-guardian/
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
        └── deployment.yaml
```

**Packaging:**
```bash
helm package helm-chart/opensearch-guardian
# Upload to GitHub Release or Helm repository
```

## Version Compatibility Matrix

### Automated Checking
The `release-automation-and-version-compatibility.yml` workflow validates:

**Backend Plugin:**
- `opensearch.plugin.minimum_compatible_version` in `plugin-descriptor.properties`
- `opensearch.plugin.version` matches project version
- Java version compatibility

**Frontend Plugin:**
- `opensearchDashboardsVersion` in `package.json`
- Peer dependencies compatibility

### Matrix Testing (Future)
Planned: Test against multiple OpenSearch versions:
- 2.11, 2.12, 2.13, 2.14, 2.15
- Automated in CI matrix strategy

## Release Checklist

### Pre-Release
- [ ] All CI checks passing on main
- [ ] CHANGELOG.md updated with new version
- [ ] VERSION file updated
- [ ] Release notes drafted
- [ ] Dependencies reviewed for updates

### Release Creation
```bash
# 1. Update version
echo "1.0.0" > VERSION

# 2. Update CHANGELOG
# Add ## [1.0.0] section following Keep a Changelog

# 3. Commit and tag
git add VERSION CHANGELOG.md
git commit -m "chore: release v1.0.0"
git tag v1.0.0
git push origin main --tags
```

### Post-Release Verification
- [ ] GitHub Release created with all assets
- [ ] SBOMs attached and downloadable
- [ ] Checksums verified
- [ ] Maven publication successful (backend)
- [ ] Docker image pushed and pullable
- [ ] Helm chart available
- [ ] Dashboards plugin installable

### Rollback Procedure
If critical issue found post-release:
1. Delete GitHub Release and tag
2. Fix issue on main branch
3. Re-tag and re-release
4. Communicate to users

## Required GitHub Secrets

| Secret | Purpose | Required For |
|--------|---------|--------------|
| `GPG_PRIVATE_KEY` | Artifact signing | Release |
| `GPG_KEY_ID` | Key identification | Release |
| `GPG_PASSPHRASE` | Key passphrase | Release |
| `MAVEN_USERNAME` | Sonatype username | Maven publish |
| `MAVEN_PASSWORD` | Sonatype password | Maven publish |
| `CR_PAT` | Container Registry token | Docker publish |
| `GITLEAKS_LICENSE` | Secret scanning | CI |

## Troubleshooting

### Common Issues

#### Maven Publish Fails
- Verify Sonatype credentials
- Check GPG key is imported and valid
- Ensure version doesn't already exist in staging

#### Docker Push Fails
- Check `CR_PAT` has write:packages scope
- Verify repository exists in GHCR
- Check Dockerfile syntax

#### SBOM Generation Fails
- Ensure Syft installed correctly
- Check plugin ZIP extracted properly
- Verify Syft version compatibility

#### Quality Gates Fail
- License: Check for new GPL dependencies
- Security: Review CVE findings, update deps
- Tests: Fix failing tests before release

## Related Documentation
- [Release Hardening Guide](../operations/release.md)
- [Versioning Strategy](../operations/versioning.md)
- [Backend Plugin Development](../plugins/backend-plugin-development.md)
- [Frontend Plugin Development](../plugins/frontend-plugin-development.md)
- [Migration Guide](../plugins/migration-guide.md)