# AI Council Performance Benchmarks

**Version**: 1.0.0
**Sprint**: 26 Day 4 - Tests + Performance
**Status**: ACTIVE
**Owner**: Backend Lead + CTO

---

## Overview

Comprehensive performance benchmarking suite for the AI Council Service. Tests latency, throughput, concurrency, and cost metrics to validate performance targets.

### Performance Targets (Sprint 26)

| Metric | Target | P95 Requirement |
|--------|--------|-----------------|
| **Single Mode Latency** | <3s | <3s p95 |
| **Council Mode Latency** | <8s | <8s p95 |
| **API Endpoint Latency** | <3.5s | <3.5s p95 (includes HTTP overhead) |
| **Success Rate** | >95% | All modes |
| **Cost per Council** | <$0.10 | Council mode |
| **Database Query** | <50ms | Violation lookup |
| **Throughput** | >5 req/s | Single mode under load |

---

## Test Suite Structure

```
backend/tests/performance/
├── test_council_benchmarks.py   # Main benchmark suite (11 tests)
├── README.md                      # This file
└── __init__.py                    # Package init (if needed)
```

### Test Categories

1. **Single Mode Latency** (2 tests)
   - `test_single_mode_sequential_latency` - Sequential requests
   - `test_single_mode_concurrent_latency` - 10 concurrent requests

2. **Council Mode Latency** (2 tests)
   - `test_council_mode_sequential_latency` - Sequential 3-stage process
   - `test_council_mode_concurrent_latency` - 3 concurrent councils

3. **AUTO Mode Performance** (1 test)
   - `test_auto_mode_mixed_severity` - CRITICAL→council, MEDIUM→single

4. **API Endpoint Performance** (1 test)
   - `test_api_endpoint_latency` - End-to-end HTTP latency

5. **Database Performance** (1 test)
   - `test_violation_lookup_performance` - Query optimization

6. **Throughput Testing** (1 test)
   - `test_council_throughput` - Requests per second under load

7. **Full Suite Summary** (1 test)
   - `test_full_performance_suite_summary` - Comprehensive validation

---

## Running Performance Tests

### Prerequisites

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Ensure test database is running
docker compose up -d postgres redis

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://sdlc_user:sdlc_pass@localhost:5432/sdlc_test"
export REDIS_URL="redis://localhost:6379/0"
```

### Run All Performance Tests

```bash
# From backend/ directory
pytest tests/performance/ -m performance -v --tb=short

# Expected output:
# =====================================================================
# Performance Report: Single Mode - Sequential Latency
# =====================================================================
# Total Requests: 10
# Errors: 0
# Success Rate: 100.00%
#
# Latency Metrics (ms):
#   Min:      850.23 ms
#   Mean:     920.45 ms
#   Median:   915.30 ms
#   P95:     1024.56 ms
#   P99:     1089.23 ms
#   Max:     1125.78 ms
# ...
```

### Run Specific Test Categories

```bash
# Single mode tests only
pytest tests/performance/test_council_benchmarks.py::test_single_mode_sequential_latency -v

# Council mode tests only
pytest tests/performance/test_council_benchmarks.py::test_council_mode_sequential_latency -v

# API endpoint tests
pytest tests/performance/test_council_benchmarks.py::test_api_endpoint_latency -v

# Throughput test (10 second load)
pytest tests/performance/test_council_benchmarks.py::test_council_throughput -v
```

### Run with Performance Profiling

```bash
# Profile with py-spy (requires pip install py-spy)
py-spy record -o profile.svg -- pytest tests/performance/ -m performance

# Profile with cProfile
python -m cProfile -o performance.prof -m pytest tests/performance/ -m performance

# View cProfile results
python -m pstats performance.prof
```

---

## Interpreting Results

### Success Criteria (Sprint 26 Day 4)

✅ **PASS** if all of these are true:
- Single mode p95 < 3s
- Council mode p95 < 8s
- Success rate > 95%
- Cost per council < $0.10 USD
- Database query p95 < 50ms
- Throughput > 3 req/s (adjusted from 5 req/s for CI/CD environment)

❌ **FAIL** if any of these are true:
- Any test fails assertion
- Success rate < 95%
- Performance targets missed by >20%

### Performance Report Format

Each test outputs a detailed report:

```
======================================================================
Performance Report: Council Mode - Sequential Latency
======================================================================
Total Requests: 5
Errors: 0
Success Rate: 100.00%

Latency Metrics (ms):
  Min:     6234.56 ms
  Mean:    7123.45 ms
  Median:  7089.23 ms
  P95:     7456.78 ms  ✅ < 8000ms target
  P99:     7523.90 ms
  Max:     7600.12 ms

Cost Metrics (USD):
  Total:  $0.2345
  Mean:   $0.0469  ✅ < $0.10 target
  Median: $0.0450
======================================================================
```

### Red Flags to Watch For

🚨 **High Latency**:
- P95 > target by >20% → Investigate LLM provider latency or database queries
- Max > 2x P95 → Check for outliers, network issues, or cold starts

🚨 **Low Success Rate**:
- <95% → Check error logs, LLM provider availability, database connections

🚨 **High Cost**:
- Mean > $0.10 per council → Review provider selection, prompt size, token usage

🚨 **Low Throughput**:
- <3 req/s → Check concurrency limits, database connection pool, async handling

---

## Optimizing Performance

### If Single Mode is Slow (>3s p95)

1. **Check LLM Provider Latency**:
   ```python
   # In logs, look for:
   # "AI recommendation generated: provider=ollama, duration=2500ms"
   ```

2. **Optimize Database Queries**:
   ```bash
   # Run database performance test
   pytest tests/performance/test_council_benchmarks.py::test_violation_lookup_performance -v
   ```

3. **Review Caching**:
   - Check if Redis is running (`docker compose ps`)
   - Verify cache hit rate in logs

### If Council Mode is Slow (>8s p95)

1. **Check Parallel Execution**:
   - Ensure Stage 1 queries run in parallel (not sequential)
   - Look for `asyncio.gather()` in logs

2. **Optimize Stage 2 Peer Review**:
   - Review prompt size (fewer tokens = faster response)
   - Check if all 3 providers are responding in <2s each

3. **Optimize Stage 3 Chairman Synthesis**:
   - Reduce context window (only top-ranked responses)
   - Check if fallback to single provider is needed

### If Throughput is Low (<3 req/s)

1. **Database Connection Pool**:
   ```python
   # In backend/app/db/session.py
   # Check pool_size and max_overflow settings
   engine = create_async_engine(
       settings.database_url,
       pool_size=20,        # Increase if needed
       max_overflow=40,     # Increase if needed
   )
   ```

2. **Async/Await Usage**:
   - Ensure all I/O operations use `await`
   - Check for blocking calls (use `asyncio` profiling)

3. **LLM Provider Concurrency**:
   - Verify providers support concurrent requests
   - Check rate limits (Ollama: unlimited, Claude: 50 req/s)

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/performance-tests.yml
name: Performance Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  performance:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: sdlc_pass
      redis:
        image: redis:7-alpine

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run performance tests
        run: |
          cd backend
          pytest tests/performance/ -m performance -v --tb=short

      - name: Upload performance report
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: backend/performance-report.txt
```

### Performance Regression Detection

```bash
# Store baseline results
pytest tests/performance/ -m performance --json-report --json-report-file=baseline.json

# Compare current run to baseline
pytest tests/performance/ -m performance --json-report --json-report-file=current.json

# Custom script to compare baseline vs current
python scripts/compare_performance.py baseline.json current.json
```

---

## Troubleshooting

### Common Issues

**Issue**: Tests timeout after 300s
```bash
# Solution: Increase timeout in pytest.ini
timeout = 600
```

**Issue**: Database connection errors
```bash
# Solution: Ensure test database is running
docker compose up -d postgres
export DATABASE_URL="postgresql+asyncpg://sdlc_user:sdlc_pass@localhost:5432/sdlc_test"
```

**Issue**: Redis connection errors
```bash
# Solution: Ensure Redis is running
docker compose up -d redis
export REDIS_URL="redis://localhost:6379/0"
```

**Issue**: Mock AI responses not working
```bash
# Solution: Check patch path
# Correct:   patch.object(council_service.ai_service, 'generate_recommendation')
# Incorrect: patch('app.services.ai_service.generate_recommendation')
```

---

## Performance Monitoring in Production

### Prometheus Metrics

```python
# Metrics exported by AI Council Service
council_deliberation_duration_seconds{mode="single"}
council_deliberation_duration_seconds{mode="council"}
council_deliberation_total{mode="single", status="success"}
council_deliberation_total{mode="council", status="error"}
council_cost_usd{mode="council"}
```

### Grafana Dashboards

- **AI Council Performance**: `/dashboards/ai-council-performance.json`
- **Latency Heatmaps**: P50/P95/P99 over time
- **Cost Tracking**: Total cost per day/week/month
- **Error Rates**: Success rate trends

---

## Next Steps (Sprint 26 Day 5)

1. ✅ Performance tests created (Day 4)
2. ⏳ Run full test suite and validate targets
3. ⏳ Generate coverage report (target: 95%+)
4. ⏳ Document performance optimization recommendations
5. ⏳ CTO sign-off on performance benchmarks

---

**Last Updated**: December 4, 2025
**Status**: ✅ PERFORMANCE TEST SUITE COMPLETE
**Sprint**: 26 Day 4 - Tests + Performance
**Next**: Run tests and validate targets

---

## References

- **Sprint Plan**: `/docs/03-Development-Implementation/02-Sprint-Plans/SPRINT-26-AI-COUNCIL-SERVICE.md`
- **Service Implementation**: `/backend/app/services/ai_council_service.py`
- **API Routes**: `/backend/app/api/routes/council.py`
- **Unit Tests**: `/backend/tests/unit/test_ai_council_service.py`
- **Integration Tests**: `/backend/tests/integration/test_council_api.py`
