# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.0] — 2026-08-19

### Added

- Project foundation: Apache-2.0 license, NOTICE, CODE_OF_CONDUCT, CONTRIBUTING, SECURITY, SUPPORT, and GOVERNANCE documents
- Architecture Decision Records (ADRs) covering open-source strategy, Docker integration, Kubernetes integration, and licensing compliance
- Standard Operating Procedure (SOP) documenting product definition, architecture, and delivery roadmap
- OpenSearch Guardian repository structure with apps/ (desktop, api, cli), guardian/ core modules, rules/, fixtures/, tests/, and docs/
- GitHub CI workflow for security scanning (license compliance, CVE checks, secret detection), SBOM generation (Syft CycloneDX), multi-platform builds, and release automation
- Release hardening guide documenting SBOM generation, artifact signing (checksums + GPG), release checklist, and dependency scanning policy
- Weekly dependency update checking workflow

### What's included in this release

- Documentation and configuration artifacts for OSS release readiness
- Versioning policy: SemVer, CHANGELOG (Keep-a-Changelog), VERSION file at repository root
- Release workflow: tag `v*` triggers CI build/test/release with SBOM and checksums
- Pre-release checklist: mandatory gates (license compliance, SBOM, secret scan, CVE scan) + recommended gates (reproducible builds, GPG signing)

### Notes

- This is the initial public release (baseline). v0.1.0 includes all Phase-1 foundation: governance docs, ADRs, SOP, CI/release workflows, and design artifacts. Application code is pending in later milestones per the roadmap.

## Upcoming

See the [roadmap](docs/operations/roadmap.md) for planned milestones.
