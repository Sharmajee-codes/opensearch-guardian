# Test Strategy — OpenSearch Guardian

## Overview
This document defines the comprehensive test strategy for OpenSearch Guardian, covering both Python backend and OpenSearch plugin (Java/Node.js) components.

## Test Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      E2E / Acceptance                       │
│  Full integration over acceptance criteria (test/e2e/)      │
├─────────────────────────────────────────────────────────────┤
│                    Integration Tests                        │
│  OpenSearch fixtures, connection tests, plugin smoke tests  │
├─────────────────────────────────────────────────────────────┤
│                      Unit Tests                             │
│  Pure unit tests, no Docker, no network (tests/unit/)       │
├─────────────────────────────────────────────────────────────┤
│                      Plugin Tests                           │
│  Java backend + Frontend plugin (Gradle + Jest)             │
└─────────────────────────────────────────────────────────────┘
```

## Backend (Python) Tests

### Location
- `tests/unit/` — Pure unit tests (no Docker, no network)
- `tests/integration/` — Integration tests (requires OpenSearch fixture)
- `tests/e2e/` — End-to-end regression tests
- `tests/fixtures/` — Test data / JSON fixtures
- `tests/conftest.py` — Shared fixtures

### Coverage Targets
| Layer | Target | Current |
|-------|--------|---------|
| Unit tests | 80%+ | ~65% (Phase 2 progress) |
| Integration tests | All critical paths | Partial |
| E2E tests | Acceptance criteria | 80%+ |

### Key Test Files

| File | Description | Lines |
|------|-------------|-------|
| `tests/test_doctor_rules.py` | Doctor rules engine (29 tests) | 22182 |
| `tests/test_safety_*.py` | Safety engine tests | 6 files |
| `tests/unit/test_safety/` | Safety unit tests (6 files) | 600+ |
| `tests/e2e/test_acceptance_regression.py` | Acceptance regression (24 tests) | 8862 |
| `tests/e2e/test_regression_matrix.py` | Regression matrix | 1887 |
| `tests/integration/test_connections/test_connection_health.py` | Connection health tests | 1 file |
| `tests/integration/test_connections/test_opensearch_api.py` | OpenSearch API tests | 1 file |
| `tests/unit/test_core_types/` | Core type tests | 2 files |
| `tests/unit/test_models/test_models.py` | Model tests | 1 file |
| `tests/unit/test_streaming/test_sse.py` | Streaming tests | 1 file |
| `tests/unit/test_fixtures.py` | Fixture tests | 374 |
| `tests/unit/test_project_structure.py` | Project structure tests | 2678 |
| `tests/validation/test_optimizer_logic.py` | Optimizer validation | 1 file |
| `tests/validation/test_safety_logic.py` | Safety validation | 1 file |

### Running Tests (Python)

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all unit tests (no Docker)
uv run python -m pytest tests/unit -v --tb=short --no-cov

# Run with coverage
uv run python -m pytest tests/unit -v --cov=guardian --cov-report=term-missing

# Run integration tests (requires OpenSearch fixture)
uv run python -m pytest tests/integration -v --tb=short

# Run e2e tests (requires mock OpenSearch)
uv run python -m pytest tests/e2e -v --tb=short

# Run full suite
uv run python -m pytest tests/ -v --tb=short
```

### Mocking Strategy

```python
# Use aioresponses for OpenSearch client mocking
from aioresponses import aioresponses

@pytest.mark.asyncio
async def test_cluster_health(mock_opensearch):
    with aioresponses() as m:
        m.get('http://localhost:9200/_cluster/health',
              payload={'status': 'green'})
        result = await client.get_cluster_health()
        assert result['status'] == 'green'
```

### Integration Test Fixtures
```python
@pytest.fixture(scope="session")
def opensearch_container():
    """Docker container for OpenSearch test cluster."""
    # Uses testcontainers or local Docker Compose
    ...
```

## Backend Plugin (Java) Tests

### Location
- `backend/src/test/java/org/opensearch/guardian/`

### Test Categories

| Category | Package | Purpose |
|----------|---------|---------|
| Plugin Tests | `GuardianPluginTest.java` | Plugin lifecycle, SPI registration |
| Integration Tests | `GuardianPluginIntegTest.java` | End-to-end with test OpenSearch cluster |
| Service Tests | `service/*Test.java` | Service unit tests |
| Model Tests | `model/*Test.java` | Data model validation |
| Action Tests | `action/*Test.java` | Transport action tests |
| REST Tests | `rest/*Test.java` | REST endpoint tests |

### Running Tests (Java)
```bash
cd backend
./gradlew test              # Unit tests
./gradlew integrationTest   # Integration tests (requires OpenSearch)
./gradlew jacocoTestReport  # Coverage report
```

### Plugin Test Example
```java
@OpenSearchIntegTestCase.ClusterScope(scope = TEST, numDataNodes = 1)
class GuardianPluginIntegTest extends OpenSearchIntegTestCase {
    
    @Test
    void testPluginLoads() {
        assertTrue(internalCluster().getInstanceNames().contains("guardian"));
    }
    
    @Test
    void testClusterHealthEndpoint() throws Exception {
        String response = executeRequest(
            Requests.GET, "/_guardian/cluster/health", Collections.emptyMap()
        );
        assertNotNull(response);
        assertThat(response, containsString("status"));
    }
}
```

## Frontend Plugin (Node.js/React) Tests

### Location
- `frontend/src/plugins/guardian/test/`

### Test Categories

| Category | File | Purpose |
|----------|------|---------|
| Manifest | `manifest.test.js` | Plugin manifest validation |
| Cluster Explorer | `clusterExplorer.test.js` | Cluster explorer component |
| Doctor View | `DoctorView.test.js` | Doctor view component |
| Optimizer View | `OptimizerView.test.js` | Optimizer view component |
| Provisioning Wizard | `ProvisioningWizard.test.js` | Provisioning wizard |
| Audit Log View | `AuditLogView.test.js` | Audit log component |
| Health Page | `HealthPage.test.js` | Health page |

### Running Tests (Node.js)
```bash
cd frontend/src/plugins/guardian
npm test                    # Run all tests
npm test -- --watchAll=false  # Non-interactive
npm test -- --coverage      # With coverage
```

### Jest Configuration
```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['@testing-library/jest-dom/extend-expect'],
  collectCoverage: true,
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};
```

## CI/CD Test Pipeline

### GitHub Actions
```yaml
# .github/workflows/opensearch-plugin-ci.yml

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run unit tests
        run: cd backend && ./gradlew test
      - name: Run integration tests
        run: cd backend && ./gradlew integrationTest
      - name: Generate coverage
        run: cd backend && ./gradlew jacocoTestReport
      - name: Upload coverage
        uses: codecov/codecov-action@v4

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run unit tests
        run: |
          cd frontend/src/plugins/guardian
          npm ci
          npm test -- --coverage --watchAll=false

  python-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: |
          pip install uv
          uv sync --locked --extra dev
      - name: Run unit tests
        run: uv run python -m pytest tests/unit -v --tb=short --no-cov
      - name: Run integration tests
        run: uv run python -m pytest tests/integration -v --tb=short
      - name: Run e2e tests
        run: uv run python -m pytest tests/e2e -v --tb=short
```

## Test Documentation Requirements

### Per Module Documentation
For each tested module, create:
1. **Test Overview** — What is being tested and why
2. **Test Cases** — Individual test case descriptions
3. **Mock Data** — Description of mock fixtures
4. **Coverage Report** — Link to coverage report

### Test Runbook
Create a test runbook for:
- Pre-release test execution
- Regression test triggers
- Performance test procedures

## Quality Gates

### Python
- Unit tests: 80%+ coverage required
- All integration tests must pass
- E2E tests: Acceptance criteria coverage 90%+

### Java Backend
- Unit tests: All plugin lifecycle tests must pass
- Integration tests: REST endpoints functional
- Coverage: 70%+ (initial phase, target 85%)

### Frontend
- Component tests: All EUI components tested
- API integration tests: Backend API mocked
- Coverage: 80%+ required

## Test Automation

### Scheduled Tests
- Nightly: Full test suite (Python + Java + Frontend)
- Weekly: Integration test suite with real OpenSearch
- On PR: Unit tests only

### Flake Detection
- Rerun failed tests up to 3 times
- Report flaky tests in CI summary
- Investigate and fix flaky tests immediately

## Related Documentation
- [Python Test README](../tests/README.md)
- [Doctor Runbook](../operations/doctor-runbook.md)
- [Admin Guide](../operations/admin-guide.md)
- [Release Automation](../plugins/release-automation.md)
- [Integration Test Plan](integration-plan.md)
- [Test Runbook](test-runbook.md)