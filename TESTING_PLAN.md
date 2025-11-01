# huproof Testing Plan

## Overview

This document outlines the testing strategy for huproof, covering unit tests, integration tests, security testing, and manual verification.

## Test Categories

### 1. Unit Tests

#### 1.1 Core Utilities
- [ ] **Calibration (`tests/test_calibration.py`)**
  - [x] L1 distance calculation
  - [x] Feature averaging
  - [x] Adaptive tau calculation
  - [x] Template quality metrics
  - [ ] Edge cases (empty vectors, single sample, etc.)

- [ ] **Challenge Generation (`tests/test_challenge.py`)**
  - [ ] Challenge length validation
  - [ ] Challenge character set (alphanumeric only)
  - [ ] Nonce uniqueness
  - [ ] Nonce format (URL-safe)

- [ ] **Crypto (`tests/test_crypto.py`)**
  - [ ] SHA256 hashing consistency
  - [ ] Origin hash format validation

- [ ] **Security (`tests/test_security.py`)**
  - [ ] JWT token creation with JTI
  - [ ] JWT token decoding
  - [ ] Token expiration handling
  - [ ] JTI generation uniqueness

- [ ] **Metrics (`tests/test_metrics.py`)**
  - [ ] Timing metric recording
  - [ ] Counter metric recording
  - [ ] Metric statistics calculation
  - [ ] Context manager timing

#### 1.2 Database Models
- [ ] **Models (`tests/test_models.py`)**
  - [ ] User creation
  - [ ] KeystrokeCommitment creation
  - [ ] NonceRecord lifecycle (creation, expiration, consumption)
  - [ ] SessionToken creation and revocation
  - [ ] Foreign key constraints
  - [ ] Unique constraints (nonce value, JTI)

#### 1.3 Schemas
- [ ] **Input Validation (`tests/test_schemas.py`)**
  - [ ] EnrollFinishRequest validation
  - [ ] LoginFinishRequest validation
  - [ ] PublicInputs validation (hex, decimal strings, bounds)
  - [ ] ProofSchema validation
  - [ ] Error messages for invalid inputs

### 2. Integration Tests

#### 2.1 API Endpoints
- [ ] **Enrollment Flow (`tests/test_enroll_integration.py`)**
  - [x] Basic enrollment start → finish
  - [ ] Nonce validation (expired, consumed, invalid)
  - [ ] Origin validation
  - [ ] Rate limiting (429 responses)
  - [ ] ZK proof verification (with real circuit, if available)
  - [ ] Commitment storage
  - [ ] User creation

- [ ] **Login Flow (`tests/test_login_integration.py`)**
  - [ ] Login start with valid user_id
  - [ ] Login start with invalid user_id (404)
  - [ ] Login finish with valid proof
  - [ ] Login finish with invalid proof
  - [ ] Token issuance and JTI tracking
  - [ ] SessionToken creation

- [ ] **Logout Flow (`tests/test_logout_integration.py`)**
  - [x] Logout with invalid token format
  - [ ] Logout with valid token
  - [ ] Logout with revoked token
  - [ ] Logout with expired token
  - [ ] Token revocation persistence

- [ ] **Health & Metrics (`tests/test_health_integration.py`)**
  - [x] Health check endpoint
  - [ ] Metrics endpoint (after some operations)
  - [ ] Metrics accuracy (counts, timings)

#### 2.2 ZK Proof Verification
- [ ] **Proof Verification (`tests/test_zk_integration.py`)**
  - [ ] Valid proof verification (requires compiled circuit)
  - [ ] Invalid proof rejection
  - [ ] Missing vkey handling
  - [ ] snarkjs CLI availability check
  - [ ] Verification timing metrics

#### 2.3 Database Operations
- [ ] **Database (`tests/test_db_integration.py`)**
  - [ ] Session management (commit, rollback)
  - [ ] Concurrent access (if using SQLite in WAL mode)
  - [ ] Nonce expiration cleanup
  - [ ] Token expiration cleanup

### 3. Security Tests

#### 3.1 Rate Limiting
- [ ] **Rate Limit Tests (`tests/test_rate_limiting.py`)**
  - [ ] Enrollment start rate limit (5/min)
  - [ ] Login start rate limit (10/min)
  - [ ] Finish endpoint rate limit (20/min)
  - [ ] IP-based rate limiting
  - [ ] Rate limit reset after window

#### 3.2 Input Validation
- [ ] **Input Validation (`tests/test_security_input.py`)**
  - [ ] SQL injection attempts (nonce, user_id)
  - [ ] XSS attempts (if any string inputs)
  - [ ] Oversized payloads
  - [ ] Malformed JSON
  - [ ] Type coercion attacks

#### 3.3 Authentication & Authorization
- [ ] **Auth Tests (`tests/test_security_auth.py`)**
  - [ ] Token replay prevention
  - [ ] Revoked token rejection
  - [ ] Expired token rejection
  - [ ] Invalid token format rejection
  - [ ] Missing token handling

#### 3.4 Origin Validation
- [ ] **Origin Tests (`tests/test_security_origin.py`)**
  - [ ] Valid origin acceptance
  - [ ] Invalid origin rejection
  - [ ] Missing origin header rejection
  - [ ] Origin hash mismatch detection

#### 3.5 Nonce Security
- [ ] **Nonce Tests (`tests/test_security_nonce.py`)**
  - [ ] Nonce reuse prevention
  - [ ] Expired nonce rejection
  - [ ] Nonce from different purpose rejection
  - [ ] Nonce binding to user/origin

### 4. End-to-End Tests

#### 4.1 Complete User Flows
- [ ] **E2E Enrollment (`tests/test_e2e_enroll.py`)**
  - [ ] Full enrollment: start → capture → proof → finish
  - [ ] Multi-sample enrollment (3 attempts, average template)
  - [ ] Enrollment with adaptive tau calculation
  - [ ] Template quality metrics

- [ ] **E2E Login (`tests/test_e2e_login.py`)**
  - [ ] Full login: start → capture → proof → finish → token
  - [ ] Login with stored template
  - [ ] Login failure (typing mismatch)
  - [ ] Login with revoked token attempt

- [ ] **E2E Logout (`tests/test_e2e_logout.py`)**
  - [ ] Login → logout → verify token revoked
  - [ ] Multiple logout attempts
  - [ ] Logout with invalid token

#### 4.2 Web Client Integration
- [ ] **Browser Tests (`tests/test_e2e_browser.py`)**
  - [ ] Keystroke capture accuracy
  - [ ] Feature vector generation
  - [ ] Template storage/retrieval
  - [ ] Proof generation (if artifacts available)
  - [ ] Error handling and user feedback

### 5. Performance Tests

#### 5.1 Load Testing
- [ ] **Load Tests (`tests/test_performance.py`)**
  - [ ] Concurrent enrollment requests
  - [ ] Concurrent login requests
  - [ ] Proof verification throughput
  - [ ] Database query performance
  - [ ] Memory usage under load

#### 5.2 Benchmarking
- [ ] **Benchmarks (`tests/benchmarks/`)**
  - [ ] Proof generation time (client-side)
  - [ ] Proof verification time (server-side)
  - [ ] Feature extraction time
  - [ ] Template averaging time
  - [ ] Database operation latency

### 6. Calibration & Accuracy Tests

#### 6.1 FRR/FAR Testing
- [ ] **Accuracy Tests (`tests/test_frr_far.py`)**
  - [x] Synthetic FRR/FAR with known variance
  - [ ] Real user typing samples (if available)
  - [ ] Cross-device typing variation
  - [ ] Tau threshold optimization
  - [ ] False accept rate with impostor samples

#### 6.2 Template Quality
- [ ] **Quality Tests (`tests/test_template_quality.py`)**
  - [ ] Consistency score calculation
  - [ ] Multi-sample vs single-sample comparison
  - [ ] Template stability over time
  - [ ] Variance analysis

### 7. Edge Cases & Error Handling

#### 7.1 Error Scenarios
- [ ] **Error Handling (`tests/test_errors.py`)**
  - [ ] Database connection failure
  - [ ] snarkjs not found
  - [ ] Corrupted verification key
  - [ ] Invalid circuit inputs
  - [ ] Network timeouts
  - [ ] Concurrent nonce consumption

#### 7.2 Boundary Conditions
- [ ] **Boundary Tests (`tests/test_boundaries.py`)**
  - [ ] Maximum feature vector size
  - [ ] Maximum tau value
  - [ ] Minimum/maximum timestamp
  - [ ] Very long challenge strings
  - [ ] Empty feature vectors
  - [ ] Zero distance matches

### 8. Manual Testing Checklist

#### 8.1 Setup & Configuration
- [ ] Environment variables loaded correctly
- [ ] Database initialized on startup
- [ ] Rate limiting configured
- [ ] CORS configured correctly
- [ ] Logging configured

#### 8.2 API Endpoints (Manual)
- [ ] **GET /health** - Returns status and version
- [ ] **GET /metrics** - Returns metrics after operations
- [ ] **GET /docs** - OpenAPI docs accessible
- [ ] **GET /api/enroll/start** - Returns challenge and nonce
- [ ] **POST /api/enroll/finish** - Creates user and commitment
- [ ] **GET /api/login/start** - Returns challenge and commitment
- [ ] **POST /api/login/finish** - Returns access token
- [ ] **POST /api/logout** - Revokes token

#### 8.3 Web Client (Manual)
- [ ] Challenge display
- [ ] Keystroke capture works
- [ ] Progress indicators show during proof generation
- [ ] Error messages display correctly
- [ ] Success messages display
- [ ] Template storage/retrieval
- [ ] Logout button appears after login
- [ ] Logout works and hides button

#### 8.4 Security (Manual)
- [ ] Rate limiting kicks in after limits
- [ ] Invalid origin rejected
- [ ] Expired nonce rejected
- [ ] Revoked token rejected
- [ ] Generic error messages (no info leakage)

### 9. Test Data & Fixtures

#### 9.1 Test Fixtures
- [ ] **Fixtures (`tests/fixtures/`)**
  - [ ] Sample feature vectors (64-element)
  - [ ] Sample templates
  - [ ] Valid proof JSON (if circuit compiled)
  - [ ] Test user IDs
  - [ ] Test nonces

#### 9.2 Mock Data
- [ ] Mock keystroke events
- [ ] Mock challenge strings
- [ ] Mock timestamps
- [ ] Mock origin hashes

### 10. CI/CD Testing

#### 10.1 Continuous Integration
- [x] **GitHub Actions (`.github/workflows/ci.yml`)**
  - [x] Ruff linting
  - [x] pytest execution
  - [ ] Test coverage reporting
  - [ ] Test failures block merge

#### 10.2 Pre-commit Hooks
- [ ] Ruff auto-fix
- [ ] Ruff lint check
- [ ] Quick pytest run (smoke tests)

### 11. Documentation Tests

#### 11.1 API Documentation
- [ ] OpenAPI schema valid
- [ ] All endpoints documented
- [ ] Request/response examples
- [ ] Error response examples

#### 11.2 Code Documentation
- [ ] All public functions have docstrings
- [ ] Type hints on all functions
- [ ] README examples work
- [ ] Setup instructions accurate

## Test Execution

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_calibration.py

# Run with coverage
uv run pytest --cov=huproof --cov-report=html

# Run integration tests only
uv run pytest tests/test_*_integration.py

# Run security tests only
uv run pytest tests/test_security*.py

# Run with verbose output
uv run pytest -v

# Run a specific test
uv run pytest tests/test_calibration.py::test_l1_distance
```

### Test Environment Setup

```bash
# Set required environment variables
export APP_SECRET=test-secret
export BYPASS_ZK_VERIFY=1  # For tests without compiled circuit
export DB_URL=sqlite:///./test.db

# Run tests
uv run pytest
```

## Test Coverage Goals

- **Unit Tests**: 80%+ coverage
- **Integration Tests**: All critical paths covered
- **Security Tests**: All security features tested
- **E2E Tests**: Core user flows covered

## Known Gaps

### Requires Circuit Compilation
- Full ZK proof verification tests
- Real proof generation/verification E2E
- Circuit constraint validation

### Requires Real User Data
- Real typing pattern analysis
- Cross-device variation testing
- Long-term template stability

### Future Enhancements
- Browser automation tests (Playwright/Selenium)
- Stress testing with high concurrent load
- Network failure simulation
- Chaos engineering tests

## Notes

- Use `BYPASS_ZK_VERIFY=1` for tests that don't require compiled circuits
- Create a test database separate from dev database
- Mock external dependencies (snarkjs CLI) where possible
- Use fixtures for common test data
- Keep tests fast (< 1s per test when possible)
- Use descriptive test names that explain what's being tested

## Maintenance

- Review and update this plan quarterly
- Add new tests when features are added
- Remove obsolete tests when features are removed
- Keep test coverage above 80%
- Document any test failures and fixes

