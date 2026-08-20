# CI/CD Credentials and Secrets Management

## Overview
This document describes the secrets required for the OpenSearch Guardian CI/CD pipelines, their purpose, and rotation guidance.

## Required GitHub Secrets

### Maven Central Publishing (Backend Plugin)

| Secret | Description | Required For | Rotation |
|--------|-------------|--------------|----------|
| `MAVEN_USERNAME` | Sonatype OSSRH username | Maven publishing | Every 90 days or on team change |
| `MAVEN_PASSWORD` | Sonatype OSSRH password/token | Maven publishing | Every 90 days or on team change |
| `GPG_PRIVATE_KEY` | GPG private key (ASCII-armored) | Artifact signing | Every 1 year |
| `GPG_KEY_ID` | GPG key ID (e.g., `ABCD1234`) | Artifact signing | When key rotates |
| `GPG_PASSPHRASE` | GPG key passphrase | Artifact signing | Every 90 days |

**Setup:**
1. Generate GPG key: `gpg --full-generate-key` (RSA 4096, no expiration)
2. Export public key to keyservers: `gpg --keyserver keyserver.ubuntu.com --send-keys <KEY_ID>`
3. Export private key: `gpg --export-secret-keys --armor <KEY_ID>`
4. Add secrets to GitHub repository settings

### Container Registry (Docker Images)

| Secret | Description | Required For | Rotation |
|--------|-------------|--------------|----------|
| `CR_PAT` | GitHub Container Registry PAT | Docker image publishing | Every 90 days |

**Setup:**
1. Create PAT at https://github.com/settings/tokens with `write:packages`, `read:packages`, `delete:packages`
2. Add as `CR_PAT` secret

### npm Publishing (Frontend Plugin)

| Secret | Description | Required For | Rotation |
|--------|-------------|--------------|----------|
| `NPM_TOKEN` | npm authentication token | Frontend plugin publishing | Every 90 days |

**Setup:**
1. Create token at https://www.npmjs.com/settings/tokens (Automation type)
2. Add as `NPM_TOKEN` secret

### Security Scanning

| Secret | Description | Required For | Rotation |
|--------|-------------|--------------|----------|
| `GITLEAKS_LICENSE` | Gitleaks license key | Secret scanning | Per license terms |

**Setup:**
1. Obtain license from https://gitleaks.io/
2. Add as `GITLEAKS_LICENSE` secret

## CI/CD Workflow Configuration

### Maven Publishing (Backend)
Enabled when `publish` Gradle property is set:

```bash
# Local test
./gradlew publish -Ppublish \
  -PossrhUsername=$MAVEN_USERNAME \
  -PossrhPassword=$MAVEN_PASSWORD \
  -Psigning.gnupg.keyId=$GPG_KEY_ID \
  -Psigning.gnupg.passphrase=$GPG_PASSPHRASE
```

In CI, the `publish` property is implicitly set when secrets are available.

### npm Publishing (Frontend)
```bash
# Local test
cd frontend/src/plugins/guardian
npm publish --access public
```

In CI, uses `NPM_TOKEN` from secrets.

### Docker Publishing
```bash
# Local test
echo $CR_PAT | docker login ghcr.io -u <username> --password-stdin
docker push ghcr.io/opensearch-guardian/opensearch-guardian:<version>
```

## Secret Rotation Procedure

### Monthly (Automated)
- Dependency check workflow runs weekly and creates issues for outdated dependencies
- Review and merge dependency updates

### Quarterly (Manual)
1. **GPG Keys**: Verify key validity, rotate if approaching expiration
2. **Sonatype Credentials**: Rotate OSSRH token in Sonatype portal
3. **GitHub PAT**: Rotate `CR_PAT` and any other PATs
4. **npm Token**: Rotate in npm settings

### On Team Changes
Immediately rotate all secrets accessible by departing members:
1. Revoke old credentials in source systems (Sonatype, GitHub, npm)
2. Generate new credentials
3. Update GitHub secrets
4. Verify CI pipelines work with new credentials

## Credential Storage Best Practices

### Do NOT
- Commit any secrets to the repository
- Store secrets in plain text in config files
- Share secrets via chat/email
- Use the same credentials across environments

### DO
- Use GitHub Environments for production secrets
- Use GitHub Actions OIDC for cloud provider auth where possible
- Store secrets in GitHub Secrets (encrypted at rest)
- Use short-lived tokens where available
- Audit secret access quarterly

## Environment-Specific Configuration

### Development
- No publishing secrets needed
- Local GPG key for testing
- Local Docker for container builds

### Staging
- Separate Sonatype staging repository
- Separate npm registry (if using private registry)
- GHCR with staging tag prefix

### Production
- Production Sonatype OSSRH
- Public npm registry
- GHCR with version tags
- All secrets in GitHub Environments with required reviewers

## Troubleshooting

### Maven Publish Fails
```bash
# Check credentials
echo $MAVEN_USERNAME
echo $MAVEN_PASSWORD | wc -c  # Should be > 0

# Test locally
./gradlew publish -Ppublish --info
```

### GPG Signing Fails
```bash
# Verify key
gpg --list-secret-keys --keyid-format LONG

# Test sign
echo "test" | gpg --batch --yes --detach-sign --armor --passphrase "$GPG_PASSPHRASE"
```

### Docker Push Fails
```bash
# Verify login
docker login ghcr.io -u <username> --password-stdin <<< "$CR_PAT"

# Check image exists
docker images | grep opensearch-guardian
```

## References
- [Sonatype OSSRH Guide](https://central.sonatype.org/pages/ossrh-guide.html)
- [GPG Signing for Maven](https://central.sonatype.org/pages/working-with-pgp-signatures.html)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [npm Publishing](https://docs.npmjs.com/packages-and-modules/contributing-packages-to-the-registry)