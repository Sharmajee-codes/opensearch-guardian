# Licensing Stack & OSS Compliance

**Document Purpose**: Validate that OpenSearch Guardian's OSS posture satisfies SOP §9 and ADR-007 before public release.

**Author**: Angela (angela-msyilhk2) — research completed 2026-08-19
**Reviewer**: Pam (pam-msyilds6)
**Status**: Draft — pending review

---

## 1. Apache-2.0 Fit Analysis

### 1.1 Why Apache-2.0?

OpenSearch Guardian adopts Apache License 2.0 as its primary license for three aligned reasons:

| Factor | Analysis |
|--------|----------|
| **OpenSearch alignment** | OpenSearch itself is Apache-2.0 (see https://github.com/opensearch-project/OpenSearch). Compatibility avoids license friction for users already working in the ecosystem. |
| **Patent grant** | Apache-2.0 includes an explicit patent license grant (Section 3), which is important for a project that may interact with Docker, Kubernetes, and OpenSearch APIs. |
| **Commercial friendliness** | Apache-2.0 permits commercial use, fork, and distribution without copyleft requirements, aligning with the "no proprietary backend" principle in SOP §9. |
| **Notice requirement** | The NOTICE file mechanism lets us credit dependencies without implying endorsement. |

### 1.2 Compatibility Check

| Dependency | License | Apache-2.0 Compatible? | Notes |
|------------|---------|------------------------|-------|
| Electron | MIT | ✅ Yes | Permissive; no restrictions on redistribution |
| React | MIT | ✅ Yes | Permissive; attribution required |
| TypeScript | Apache-2.0 | ✅ Yes | Same license family |
| FastAPI | MIT | ✅ Yes | Permissive |
| Pydantic | MIT | ✅ Yes | Permissive |
| opensearch-py | Apache-2.0 | ✅ Yes | Same license; direct compatibility |
| Typer | MIT | ✅ Yes | Permissive |
| Rich | MIT | ✅ Yes | Permissive |
| SQLite | Public Domain | ✅ Yes | No restrictions |
| Kubernetes Python client | Apache-2.0 | ✅ Yes | Same license family |
| Docker Engine API | Apache-2.0 | ✅ Yes | Same license family |

**Conclusion**: All planned dependencies use permissive licenses (MIT or Apache-2.0). No license incompatibility exists.

---

## 2. Trademark Compliance

### 2.1 OpenSearch Trademark Policy

OpenSearch is a **registered trademark of Amazon Web Services (AWS)**. Per the OpenSearch trademark policy:

> "Guardian is compatible with OpenSearch but is not an official OpenSearch project."

**Required compliance actions:**

1. **NOTICE file disclaimer**: Must explicitly state non-affiliation with the OpenSearch Project.
2. **No misleading naming**: Cannot use "OpenSearch" in the project name in a way that suggests official endorsement.
3. **Logo usage**: Cannot use the OpenSearch logo or trademarked visual identity without explicit permission.
4. **Documentation clarity**: All user-facing documentation must include the trademark disclaimer.

### 2.2 Current Compliance Status

| Requirement | Status | Action Required |
|-------------|--------|-----------------|
| NOTICE file with disclaimer | ✅ Implemented | None — already present in NOTICE |
| Project naming | ✅ Compliant | "OpenSearch Guardian" clearly distinguishes as a third-party tool |
| Logo usage | ✅ Not applicable | No OpenSearch logo used |
| Documentation disclaimer | ⚠️ Partial | Add trademark notice to README.md and CONTRIBUTING.md |

**Recommendation**: Add the following line to README.md:

> "OpenSearch is a trademark of Amazon Web Services. OpenSearch Guardian is not affiliated with or endorsed by the OpenSearch Project."

---

## 3. Dependency License Review Obligations

### 3.1 Review Process

Before each public release, the following process must be executed:

1. **Generate dependency list**:
   ```bash
   # Python dependencies
   pip freeze > requirements-generated.txt
   
   # Node.js dependencies
   npm ls --production --depth=0 > deps-node.txt
   ```

2. **Scan for license violations**:
   ```bash
   # Python
   pip-license-check requirements-generated.txt
   
   # Node.js
   npx license-checker --summary
   ```

3. **Flag non-permissive licenses**:
   - **PROHIBITED**: GPL, AGPL, LGPL (unless statically linked with explicit compliance)
   - **REVIEW REQUIRED**: SSPL, BSL, MPL-2.0, LGPL with dynamic linking
   - **APPROVED**: MIT, BSD-2/3, Apache-2.0, ISC, Public Domain

4. **Document findings**: Add a `LICENSES/` directory in the release with full license texts.

### 3.2 Ongoing Obligations

| Obligation | Frequency | Tool |
|------------|-----------|------|
| Dependency scan | Pre-release | `pip-licenses`, `license-checker` |
| CVE scanning | Pre-release + weekly CI | `safety`, `npm audit` |
| SBOM generation | Pre-release | `syft`, `cyclonedx` |
| Secret scanning | Pre-release + CI | `gitleaks`, `trufflehog` |

---

## 4. SBOM & Dependency Scanning Posture

### 4.1 SBOM (Software Bill of Materials)

**Requirement**: Every release must include an SBOM listing all dependencies and their licenses.

**Tooling**:
- **Primary**: Syft (https://github.com/anchore/syft)
- **Format**: CycloneDX JSON (recommended for OSS projects)
- **Placement**: `releases/<version>/SBOM.json`

**Example generation**:
```bash
# Generate SBOM for the full application
syft . -o cyclonedx-json > SBOM.json

# Filter to production dependencies only
syft . --scope production -o cyclonedx-json > SBOM.json
```

### 4.2 Dependency Scanning

| Scan Type | Tool | When |
|-----------|------|------|
| License compliance | `pip-licenses`, `license-checker` | Pre-release, CI |
| CVE vulnerability | `safety`, `npm audit` | Pre-release, CI, weekly |
| Secret detection | `gitleaks` | Pre-release, CI on push |
| Supply chain attack | `deps.dev` (ossf) | Quarterly review |

### 4.3 Secret Scanning Policy

Per SOP §8, the project must:
- Run `gitleaks` or equivalent on every PR
- Block merges if secrets are detected
- Rotate any accidentally committed credentials
- Document the scanning process in SECURITY.md

---

## 5. License Header Policy

### 5.1 Required Header Format

All source files must include a license header identifying the Apache-2.0 license:

```python
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements. See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership. The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
```

### 5.2 Enforcement

- **Pre-commit hook**: Check for missing headers
- **CI check**: `spotless` or similar tool to enforce headers
- **Contributor workflow**: Template in `.github/PULL_REQUEST_TEMPLATE.md` reminding contributors

---

## 6. Pre-Release Compliance Checklist

### 6.1 Mandatory Checks (Block Release if Failing)

- [ ] All dependencies use approved licenses (MIT, BSD, Apache-2.0, ISC, Public Domain)
- [ ] No GPL/AGPL/LGPL dependencies without explicit legal review
- [ ] SBOM generated and included in release artifacts
- [ ] Secret scanning passes (zero detections)
- [ ] CVE scan passes (no critical/high vulnerabilities)
- [ ] NOTICE file present and includes trademark disclaimer
- [ ] README.md includes trademark disclaimer
- [ ] LICENSE file present at repository root
- [ ] CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, SUPPORT.md, GOVERNANCE.md all present

### 6.2 Recommended Checks (Document if Skipped)

- [ ] Reproducible build documentation exists
- [ ] Release signed with GPG key
- [ ] Checksums published for all release artifacts
- [ ] Changelog updated with dependency changes
- [ ] ADR-007 reviewed and still accurate

### 6.3 Release Checklist Template

Create a `RELEASE-CHECKLIST.md` in the repository root referencing this document.

---

## 7. Trademark Usage Guidelines

### 7.1 Permitted Uses

- Describing compatibility: "Guardian works with OpenSearch"
- Referencing OpenSearch APIs: "Uses OpenSearch REST API"
- Linking to OpenSearch documentation

### 7.2 Prohibited Uses

- Using "OpenSearch" as a standalone project name
- Implying official endorsement or affiliation
- Modifying the OpenSearch logo
- Using "OpenSearch" in domain names without permission

### 7.3 Required Disclaimers

All public-facing materials must include:
> "OpenSearch is a trademark of Amazon Web Services. This project is not affiliated with or endorsed by the OpenSearch Project or Amazon Web Services."

---

## 8. References

- **Apache License 2.0**: https://www.apache.org/licenses/LICENSE-2.0
- **OpenSearch License**: https://github.com/opensearch-project/OpenSearch
- **OpenSearch Trademark Policy**: https://github.com/opensearch-project/.github/blob/main/TRAD.markdown
- **SBOM Specification**: https://cyclonedx.org/
- **SOP Section 9**: Open-Source Strategy
- **ADR-007**: Open-Source Strategy (accepted)

---

## 9. Action Items

| Item | Owner | Priority |
|------|-------|----------|
| Add trademark disclaimer to README.md | T3 (Angela) | High |
| Add license header to Python files | T3 (Angela) | Medium |
| Create `.github/workflows/license-check.yml` | T5 (Michael) | Medium |
| Create `RELEASE-CHECKLIST.md` | T5 (Michael) | Low |
| Review for GPL dependencies in final build | T5 (Michael) | High |

---

*Last updated: 2026-08-19 by Angela (angela-msyilhk2)*