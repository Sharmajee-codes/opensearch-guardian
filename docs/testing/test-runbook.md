# Test Runbook — OpenSearch Guardian

## Overview
This runbook provides step-by-step procedures for executing test suites across all layers of the OpenSearch Guardian project.

## Quick Test Commands

### Python Tests
```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests (no Docker required)
make test

# Run unit tests only
make test-unit

# Run with coverage
make test-coverage

# Run integration tests (requires Docker)
make test-integration

# Run e2e tests (requires mock OpenSearch)
make test-e2e
```

### Java Backend Plugin Tests
```bash
cd backend

# Run all tests
./gradlew test

# Run integration tests (requires OpenSearch)
./gradlew integrationTest

# Generate coverage report
./gradlew jacocoTestReport

# Build plugin ZIP (for manual testing)
./gradlew buildPluginZip
```

### Frontend Plugin Tests
```bash
cd frontend/src/plugins/guardian

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- --testPathPattern=DoctorView

# Run in watch mode (development)
npm test -- --watch
```

## Pre-Release Test Execution

### Step 1: Run Full Python Test Suite
```bash
# Verify all Python tests pass
make test

# Check coverage
make test-coverage

# Verify no regressions
make test-all
```

**Expected Result:** All tests pass, coverage ≥80%

### Step 2: Run Java Backend Tests
```bash
cd backend
./gradlew clean test
./gradlew jacocoTestReport
```

**Expected Result:** All tests pass, coverage ≥70%

### Step 3: Run Frontend Plugin Tests
```bash
cd frontend/src/plugins/guardian
npm ci
npm test
```

**Expected Result:** All tests pass, coverage ≥80%

### Step 4: Run CI/CD Pipeline
```bash
# GitHub Actions will run automatically on push/PR
# Monitor: https://github.com/opensearch-guardian/opensearch-guardian/actions
```

**Expected Result:** All workflow jobs pass (green checks)

### Step 5: Manual Smoke Test (Optional)
```bash
# Start OpenSearch with Guardian plugin
docker-compose up -d

# Test backend endpoints
curl -s http://localhost:9200/_guardian/cluster/health | jq .

# Test frontend
open http://localhost:5601
# Navigate to Guardian in Dashboards
```

## Test Categories by Priority

### Critical (Must Pass)
- [ ] Doctor rules engine (`test_doctor_rules.py`)
- [ ] Safety classification (`test_safety_classification.py`)
- [ ] Plugin loading (`GuardianPluginTest.java`)
- [ ] Cluster health endpoint (`ClusterHealthRestActionTest.java`)

### High (Should Pass)
- [ ] Integration tests (`tests/integration/`)
- [ ] E2E regression (`test_acceptance_regression.py`)
- [ ] Frontend components (`DoctorView.test.js`, etc.)
- [ ] Security/permissions tests

### Medium (Nice to Pass)
- [ ] Coverage thresholds
- [ ] Cross-browser tests
- [ ] Performance benchmarks

## Troubleshooting Test Failures

### Python Tests Failing

**Issue:** Module not found
```bash
# Fix: Install package in development mode
pip install -e ".[dev]"
```

**Issue:** Fixture errors
```bash
# Fix: Check test fixtures exist
ls tests/fixtures/
python -c "import tests.conftest"  # Test fixture import
```

**Issue:** Coverage threshold not met
```bash
# Fix: Add more test cases or adjust threshold
# See docs/testing/strategy.md for requirements
```

### Java Tests Failing

**Issue:** OpenSearch not available
```bash
# Integration tests require OpenSearch
# Run unit tests only: ./gradlew test
# For integration tests, start test cluster first
```

**Issue:** Plugin loading failure
```bash
# Check plugin-descriptor.properties
cat backend/src/main/resources/plugin-descriptor.properties

# Verify plugin class exists
find backend/src -name "GuardianPlugin.java"
```

### Frontend Tests Failing

**Issue:** Missing dependencies
```bash
cd frontend/src/plugins/guardian
rm -rf node_modules
npm ci
npm test
```

**Issue:** Component not rendering
```bash
# Check EUI imports
npm list @elastic/eui
npm install @elastic/eui@^8.6.0
```

## Test Data Maintenance

### Adding Test Fixtures
```bash
# Create JSON fixture
cat > tests/fixtures/new_test_data.json << 'EOF'
{
  "cluster_health": {
    "status": "green",
    "number_of_nodes": 3,
    "active_shards": 100
  }
}
EOF
```

### Updating Test Expectations
```python
# When behavior changes, update test expectations
# Check: tests/test_safety_classification.py
# Update: expected SafetyClassification values
```

## Test Reporting

### Test Summary Output
```bash
# Python
pytest --tb=short --co  # Collect tests
pytest -v               # Verbose output
pytest --junitxml=results.xml  # JUnit format

# Java
./gradlew test --info   # Verbose output
./gradlew test --rerun-tasks  # Force rerun

# Frontend
npm test -- --verbose   # Verbose output
npm test -- --coverage  # Coverage report
```

### Coverage Reports
```bash
# Python coverage
coverage html  # HTML report in htmlcov/

# Java coverage
# Report at: backend/build/reports/jacoco/test/html/index.html

# Frontend coverage
# Report at: frontend/src/plugins/guardian/coverage/
```

## Continuous Integration Status

### GitHub Actions
Monitor at: https://github.com/opensearch-guardian/opensearch-guardian/actions

**Key Workflows:**
1. **CI** — Security scan, SBOM, unit tests, build-test
2. **OpenSearch Plugin CI** — Backend test, frontend test, integration test, SBOM, release
3. **Release** — Quality gates, build, SBOM + release

### Local CI Simulation
```bash
# Simulate CI locally
make test-all
./gradlew test
npm test
```

## Test-Driven Development (TDD) Workflow

### When Adding New Features
1. Write failing test first
2. Run test to confirm failure
3. Implement feature
4. Run test to confirm pass
5. Refactor
6. Update documentation

### Example
```python
# 1. Write test
def test_new_feature():
    result = new_feature_function()
    assert result == expected_value

# 2. Run test (FAILS)
pytest test_new_feature.py

# 3. Implement
def new_feature_function():
    return expected_value

# 4. Run test (PASSES)
pytest test_new_feature.py
```

## Related Documentation
- [Test Strategy](strategy.md)
- [Doctor Runbook](../operations/doctor-runbook.md)
- [Admin Guide](../operations/admin-guide.md)
- [API Reference](../API.md)