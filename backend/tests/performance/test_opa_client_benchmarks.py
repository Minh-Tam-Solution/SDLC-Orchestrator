"""
=========================================================================
OPA Client Performance Benchmarks - SDLC 6.0.5
SDLC Orchestrator - Sprint 140 (CLI Orchestration Upgrade)

Version: 1.0.0
Date: February 14, 2026
Status: ACTIVE - Sprint 140 Day 5 (Performance Testing)
Authority: Backend Lead + CTO Approved
Foundation: RFC-SDLC-602 E2E API Testing Enhancement
Framework: SDLC 6.0.5 Complete Lifecycle

Purpose:
- Performance benchmarking for OPA client policy evaluation
- Measure policy evaluation latency
- Batch evaluation throughput
- Fallback mode performance
- Parse result overhead
- Concurrent evaluation load testing

Performance Targets:
- Single evaluation: <100ms p95 latency (mock OPA)
- Health check: <50ms p95 latency
- Batch evaluation (10 policies): <500ms total
- Fallback evaluation: <10ms p95 latency
- Parse result: <1ms p95 latency
- 50 concurrent evaluations: <1000ms total

Test Scenarios:
1. Single Policy Evaluation Latency
2. Batch Evaluation Performance
3. Health Check Latency
4. Fallback Mode Performance
5. Parse Result Overhead
6. Concurrent Evaluation Load
7. E2E Compliance Fallback
8. Cross-Reference Fallback

Zero Mock Policy: Mocked OPA HTTP responses for deterministic testing
=========================================================================
"""

import asyncio
import statistics
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from sdlcctl.lib.opa_client import (
    OPAClient,
    OPAClientConfig,
    OPAResult,
    get_opa_client,
)


# =========================================================================
# Performance Measurement Utilities
# =========================================================================


class PerformanceMetrics:
    """Track and calculate performance metrics for OPA operations."""

    def __init__(self, operation_name: str = "operation"):
        self.operation_name = operation_name
        self.durations: List[float] = []
        self.errors: int = 0
        self.start_time: Optional[float] = None

    def add_measurement(self, duration_ms: float, error: bool = False):
        """Add a single measurement."""
        self.durations.append(duration_ms)
        if error:
            self.errors += 1

    def start(self):
        """Start timing an operation."""
        self.start_time = time.perf_counter()

    def stop(self, error: bool = False) -> float:
        """Stop timing and record the measurement."""
        if self.start_time is None:
            raise ValueError("Timer not started")
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        self.add_measurement(duration_ms, error)
        self.start_time = None
        return duration_ms

    def get_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics."""
        if not self.durations:
            return {
                "operation": self.operation_name,
                "count": 0,
                "errors": self.errors,
            }

        sorted_durations = sorted(self.durations)
        total_requests = len(self.durations)
        p95_index = int(total_requests * 0.95)
        p99_index = int(total_requests * 0.99)

        return {
            "operation": self.operation_name,
            "count": total_requests,
            "errors": self.errors,
            "success_rate": ((total_requests - self.errors) / total_requests) * 100,
            # Latency stats (ms)
            "latency_min_ms": min(self.durations),
            "latency_max_ms": max(self.durations),
            "latency_mean_ms": statistics.mean(self.durations),
            "latency_median_ms": statistics.median(self.durations),
            "latency_p95_ms": sorted_durations[min(p95_index, total_requests - 1)],
            "latency_p99_ms": sorted_durations[min(p99_index, total_requests - 1)],
            "latency_stdev_ms": (
                statistics.stdev(self.durations) if len(self.durations) > 1 else 0
            ),
            "total_duration_ms": sum(self.durations),
        }

    def print_summary(self):
        """Print formatted summary."""
        summary = self.get_summary()
        print(f"\n{'='*60}")
        print(f"Performance Summary: {summary['operation']}")
        print(f"{'='*60}")
        print(f"  Total Operations: {summary['count']}")
        print(f"  Errors: {summary['errors']}")
        print(f"  Success Rate: {summary.get('success_rate', 0):.2f}%")
        print(f"  Latency (ms):")
        print(f"    Min: {summary.get('latency_min_ms', 0):.3f}")
        print(f"    Max: {summary.get('latency_max_ms', 0):.3f}")
        print(f"    Mean: {summary.get('latency_mean_ms', 0):.3f}")
        print(f"    Median: {summary.get('latency_median_ms', 0):.3f}")
        print(f"    P95: {summary.get('latency_p95_ms', 0):.3f}")
        print(f"    P99: {summary.get('latency_p99_ms', 0):.3f}")
        print(f"    StdDev: {summary.get('latency_stdev_ms', 0):.3f}")
        print(f"  Total Duration: {summary.get('total_duration_ms', 0):.2f} ms")
        print(f"{'='*60}\n")


def create_mock_response(allow: bool, violations: List[str] = None, details: Dict = None):
    """Create a mock OPA response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": {
            "allow": allow,
            "violations": violations or [],
            "warnings": [],
            "details": details or {"checked": 5},
        }
    }
    return mock_response


def create_mock_health_response(healthy: bool = True):
    """Create a mock health check response."""
    mock_response = Mock()
    mock_response.status_code = 200 if healthy else 500
    return mock_response


def create_mock_policies_response():
    """Create a mock policies list response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": [
            {"id": "sdlc/e2e_testing/compliance"},
            {"id": "sdlc/e2e_testing/cross_reference"},
            {"id": "sdlc/security/baseline"},
        ]
    }
    return mock_response


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def client():
    """Create OPA client for testing."""
    config = OPAClientConfig(
        base_url="http://localhost:8181",
        timeout=10.0,
    )
    return OPAClient(config)


@pytest.fixture
def test_input_e2e_compliance():
    """Generate test input for E2E compliance policy."""
    return {
        "project_path": "/test/project",
        "min_pass_rate": 80,
        "evidence": [
            {
                "artifact_type": "E2E_TESTING_REPORT",
                "metadata": {"pass_rate": 95},
            },
            {
                "artifact_type": "API_DOCUMENTATION_REFERENCE",
            },
        ],
    }


@pytest.fixture
def test_input_cross_reference():
    """Generate test input for cross-reference policy."""
    return {
        "project_path": "/test/project",
        "stage_03_path": "/test/project/docs/03-Integration-APIs",
        "stage_05_path": "/test/project/docs/05-Testing-Quality",
    }


# =========================================================================
# Test Class: Single Policy Evaluation
# =========================================================================


class TestSingleEvaluationLatency:
    """Test single policy evaluation latency."""

    def test_evaluate_success_latency(self, client, test_input_e2e_compliance):
        """Benchmark: Single policy evaluation should be <100ms p95 (mocked)."""
        metrics = PerformanceMetrics("single_evaluate_success")
        iterations = 100

        mock_response = create_mock_response(allow=True)

        with patch.object(client._session, "post", return_value=mock_response):
            for _ in range(iterations):
                metrics.start()
                try:
                    client.evaluate(
                        "sdlc.e2e_testing.e2e_testing_compliance",
                        test_input_e2e_compliance,
                    )
                except Exception:
                    metrics.stop(error=True)
                    continue
                metrics.stop()

        summary = metrics.get_summary()
        metrics.print_summary()

        assert summary["count"] == iterations
        assert summary["success_rate"] == 100.0
        assert summary["latency_p95_ms"] < 100.0, (
            f"Evaluate p95 latency {summary['latency_p95_ms']:.2f}ms exceeds 100ms target"
        )

    def test_evaluate_deny_latency(self, client, test_input_e2e_compliance):
        """Benchmark: Evaluation with violations should have same latency."""
        metrics = PerformanceMetrics("single_evaluate_deny")
        iterations = 100

        mock_response = create_mock_response(
            allow=False,
            violations=["E2E_REPORT_MISSING", "PASS_RATE_LOW"],
        )

        with patch.object(client._session, "post", return_value=mock_response):
            for _ in range(iterations):
                metrics.start()
                result = client.evaluate(
                    "sdlc.e2e_testing.e2e_testing_compliance",
                    test_input_e2e_compliance,
                )
                metrics.stop()
                assert result.allow is False
                assert len(result.violations) == 2

        summary = metrics.get_summary()
        metrics.print_summary()

        assert summary["latency_p95_ms"] < 100.0


# =========================================================================
# Test Class: Batch Evaluation
# =========================================================================


class TestBatchEvaluationPerformance:
    """Test batch evaluation performance."""

    def test_batch_10_policies_latency(self, client):
        """Benchmark: Batch evaluation of 10 policies should be <500ms total."""
        metrics = PerformanceMetrics("batch_10_policies")

        mock_response = create_mock_response(allow=True)

        evaluations = [
            (f"sdlc.policy_{i}", {"input": f"data_{i}"})
            for i in range(10)
        ]

        with patch.object(client._session, "post", return_value=mock_response):
            for _ in range(10):  # Run 10 batches
                metrics.start()
                results = client.evaluate_batch(evaluations)
                metrics.stop()
                assert len(results) == 10

        summary = metrics.get_summary()
        metrics.print_summary()

        # Each batch of 10 should complete in <500ms
        assert summary["latency_p95_ms"] < 500.0, (
            f"Batch p95 latency {summary['latency_p95_ms']:.2f}ms exceeds 500ms target"
        )

    def test_batch_throughput(self, client):
        """Benchmark: Measure throughput for batch evaluations."""
        mock_response = create_mock_response(allow=True)

        evaluations = [
            (f"sdlc.policy_{i}", {"input": f"data_{i}"})
            for i in range(100)
        ]

        with patch.object(client._session, "post", return_value=mock_response):
            start = time.perf_counter()
            results = client.evaluate_batch(evaluations)
            duration_ms = (time.perf_counter() - start) * 1000

        throughput = len(results) / (duration_ms / 1000)

        print(f"\n{'='*60}")
        print("Batch Throughput Analysis")
        print(f"{'='*60}")
        print(f"  Policies evaluated: {len(results)}")
        print(f"  Total time: {duration_ms:.2f}ms")
        print(f"  Throughput: {throughput:.2f} policies/sec")
        print(f"{'='*60}\n")

        # Should evaluate at least 100 policies per second
        assert throughput > 100.0


# =========================================================================
# Test Class: Health Check Latency
# =========================================================================


class TestHealthCheckLatency:
    """Test health check latency."""

    def test_health_check_success_latency(self, client):
        """Benchmark: Health check should be <50ms p95."""
        metrics = PerformanceMetrics("health_check_success")
        iterations = 100

        mock_response = create_mock_health_response(healthy=True)

        with patch.object(client._session, "get", return_value=mock_response):
            for _ in range(iterations):
                metrics.start()
                result = client.check_health()
                metrics.stop()
                assert result is True

        summary = metrics.get_summary()
        metrics.print_summary()

        assert summary["latency_p95_ms"] < 50.0, (
            f"Health check p95 latency {summary['latency_p95_ms']:.2f}ms exceeds 50ms target"
        )

    def test_get_policies_latency(self, client):
        """Benchmark: Get policies list should be <100ms p95."""
        metrics = PerformanceMetrics("get_policies")
        iterations = 100

        mock_response = create_mock_policies_response()

        with patch.object(client._session, "get", return_value=mock_response):
            for _ in range(iterations):
                metrics.start()
                policies = client.get_policies()
                metrics.stop()
                assert len(policies) == 3

        summary = metrics.get_summary()
        metrics.print_summary()

        assert summary["latency_p95_ms"] < 100.0


# =========================================================================
# Test Class: Fallback Performance
# =========================================================================


class TestFallbackPerformance:
    """Test fallback mode performance (when OPA unavailable)."""

    def test_e2e_compliance_fallback_latency(self, client, test_input_e2e_compliance):
        """Benchmark: E2E compliance fallback should be <10ms p95."""
        metrics = PerformanceMetrics("e2e_compliance_fallback")
        iterations = 100

        for _ in range(iterations):
            metrics.start()
            result = client._fallback_e2e_compliance(
                test_input_e2e_compliance,
                "Connection refused",
            )
            metrics.stop()
            # With valid input, should pass
            assert result.allow is True
            assert len(result.warnings) > 0  # Should have OPA unavailable warning

        summary = metrics.get_summary()
        metrics.print_summary()

        assert summary["latency_p95_ms"] < 10.0, (
            f"E2E fallback p95 latency {summary['latency_p95_ms']:.2f}ms exceeds 10ms target"
        )

    def test_cross_reference_fallback_latency(self, client):
        """Benchmark: Cross-reference fallback should be <10ms p95."""
        metrics = PerformanceMetrics("cross_ref_fallback")
        iterations = 100

        # Create temp directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            stage_03 = project_path / "docs" / "03-Integration-APIs"
            stage_05 = project_path / "docs" / "05-Testing-Quality"
            stage_03.mkdir(parents=True)
            stage_05.mkdir(parents=True)

            input_data = {
                "project_path": str(project_path),
                "stage_03_path": str(stage_03),
                "stage_05_path": str(stage_05),
            }

            for _ in range(iterations):
                metrics.start()
                result = client._fallback_cross_reference(
                    input_data,
                    "Connection refused",
                )
                metrics.stop()

        summary = metrics.get_summary()
        metrics.print_summary()

        assert summary["latency_p95_ms"] < 10.0, (
            f"Cross-ref fallback p95 latency {summary['latency_p95_ms']:.2f}ms exceeds 10ms target"
        )

    def test_fallback_with_violations_latency(self, client):
        """Benchmark: Fallback with missing evidence should detect violations quickly."""
        metrics = PerformanceMetrics("fallback_with_violations")
        iterations = 100

        input_data = {
            "project_path": "/test/project",
            "min_pass_rate": 80,
            "evidence": [],  # No evidence - should trigger violations
        }

        for _ in range(iterations):
            metrics.start()
            result = client._fallback_e2e_compliance(input_data, "OPA timeout")
            metrics.stop()
            assert result.allow is False
            assert len(result.violations) >= 2  # E2E_REPORT_MISSING + API_DOCS_MISSING

        summary = metrics.get_summary()
        metrics.print_summary()

        assert summary["latency_p95_ms"] < 10.0


# =========================================================================
# Test Class: Parse Result Performance
# =========================================================================


class TestParseResultPerformance:
    """Test result parsing performance."""

    def test_parse_bool_result_latency(self, client):
        """Benchmark: Parse boolean result should be <1ms p95."""
        metrics = PerformanceMetrics("parse_bool_result")
        iterations = 1000

        data = {"result": True}

        for _ in range(iterations):
            metrics.start()
            result = client._parse_result(data, "test.policy")
            metrics.stop()
            assert result.allow is True

        summary = metrics.get_summary()
        metrics.print_summary()

        assert summary["latency_p95_ms"] < 1.0, (
            f"Parse bool p95 latency {summary['latency_p95_ms']:.3f}ms exceeds 1ms target"
        )

    def test_parse_dict_result_latency(self, client):
        """Benchmark: Parse dict result with violations should be <1ms p95."""
        metrics = PerformanceMetrics("parse_dict_result")
        iterations = 1000

        data = {
            "result": {
                "allow": False,
                "violations": [f"VIOLATION_{i}" for i in range(10)],
                "warnings": [f"WARNING_{i}" for i in range(5)],
                "details": {
                    "checked_items": 100,
                    "failed_items": 10,
                    "passed_items": 90,
                },
            }
        }

        for _ in range(iterations):
            metrics.start()
            result = client._parse_result(data, "test.policy")
            metrics.stop()
            assert result.allow is False
            assert len(result.violations) == 10

        summary = metrics.get_summary()
        metrics.print_summary()

        assert summary["latency_p95_ms"] < 1.0, (
            f"Parse dict p95 latency {summary['latency_p95_ms']:.3f}ms exceeds 1ms target"
        )

    def test_parse_large_result_latency(self, client):
        """Benchmark: Parse large result (100+ violations) should be <5ms p95."""
        metrics = PerformanceMetrics("parse_large_result")
        iterations = 100

        data = {
            "result": {
                "allow": False,
                "violations": [f"VIOLATION_{i}: Description of violation {i}" for i in range(100)],
                "warnings": [f"WARNING_{i}" for i in range(50)],
                "details": {
                    f"item_{i}": {
                        "status": "failed" if i % 2 == 0 else "passed",
                        "message": f"Details for item {i}",
                    }
                    for i in range(100)
                },
            }
        }

        for _ in range(iterations):
            metrics.start()
            result = client._parse_result(data, "test.policy")
            metrics.stop()
            assert len(result.violations) == 100

        summary = metrics.get_summary()
        metrics.print_summary()

        assert summary["latency_p95_ms"] < 5.0, (
            f"Parse large p95 latency {summary['latency_p95_ms']:.3f}ms exceeds 5ms target"
        )


# =========================================================================
# Test Class: Concurrent Evaluation
# =========================================================================


class TestConcurrentEvaluation:
    """Test concurrent evaluation performance."""

    def test_50_concurrent_evaluations(self, client, test_input_e2e_compliance):
        """Benchmark: 50 concurrent evaluations should complete in <1000ms total."""
        metrics = PerformanceMetrics("concurrent_50_evaluations")

        mock_response = create_mock_response(allow=True)

        def evaluate_single(index: int) -> tuple[float, bool]:
            """Evaluate single policy."""
            start = time.perf_counter()
            try:
                with patch.object(client._session, "post", return_value=mock_response):
                    client.evaluate(
                        f"sdlc.policy_{index}",
                        test_input_e2e_compliance,
                    )
                duration_ms = (time.perf_counter() - start) * 1000
                return duration_ms, False
            except Exception:
                duration_ms = (time.perf_counter() - start) * 1000
                return duration_ms, True

        # Sequential simulation of concurrent requests (OPA client is sync)
        total_start = time.perf_counter()

        for i in range(50):
            duration_ms, error = evaluate_single(i)
            metrics.add_measurement(duration_ms, error)

        total_duration_ms = (time.perf_counter() - total_start) * 1000

        summary = metrics.get_summary()
        metrics.print_summary()

        print(f"Total wall-clock time for 50 evaluations: {total_duration_ms:.2f}ms")

        assert summary["count"] == 50
        assert summary["success_rate"] == 100.0
        assert total_duration_ms < 1000.0, (
            f"50 evaluations took {total_duration_ms:.2f}ms, exceeds 1000ms target"
        )


# =========================================================================
# Test Class: OPA Client Config Performance
# =========================================================================


class TestClientConfigPerformance:
    """Test client configuration and initialization performance."""

    def test_client_init_latency(self):
        """Benchmark: Client initialization should be <5ms p95."""
        metrics = PerformanceMetrics("client_init")
        iterations = 100

        for _ in range(iterations):
            metrics.start()
            config = OPAClientConfig(
                base_url="http://localhost:8181",
                timeout=10.0,
            )
            client = OPAClient(config)
            metrics.stop()
            assert client is not None

        summary = metrics.get_summary()
        metrics.print_summary()

        assert summary["latency_p95_ms"] < 5.0, (
            f"Client init p95 latency {summary['latency_p95_ms']:.2f}ms exceeds 5ms target"
        )

    def test_get_opa_client_latency(self):
        """Benchmark: get_opa_client() should be <5ms p95."""
        metrics = PerformanceMetrics("get_opa_client")
        iterations = 100

        for _ in range(iterations):
            metrics.start()
            client = get_opa_client()
            metrics.stop()
            assert client is not None

        summary = metrics.get_summary()
        metrics.print_summary()

        assert summary["latency_p95_ms"] < 5.0


# =========================================================================
# Summary Report Generator
# =========================================================================


def test_generate_opa_performance_report(client, test_input_e2e_compliance):
    """Generate comprehensive OPA client performance report for Sprint 140."""
    print("\n")
    print("=" * 70)
    print("OPA CLIENT PERFORMANCE REPORT")
    print("Sprint 140 - SDLC 6.0.5")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    results = {}

    # Test 1: Single Evaluation
    metrics = PerformanceMetrics("Single Evaluation")
    mock_response = create_mock_response(allow=True)
    with patch.object(client._session, "post", return_value=mock_response):
        for _ in range(100):
            metrics.start()
            client.evaluate("sdlc.e2e.compliance", test_input_e2e_compliance)
            metrics.stop()
    results["evaluate"] = metrics.get_summary()

    # Test 2: Health Check
    metrics = PerformanceMetrics("Health Check")
    mock_health = create_mock_health_response()
    with patch.object(client._session, "get", return_value=mock_health):
        for _ in range(100):
            metrics.start()
            client.check_health()
            metrics.stop()
    results["health"] = metrics.get_summary()

    # Test 3: E2E Fallback
    metrics = PerformanceMetrics("E2E Fallback")
    for _ in range(100):
        metrics.start()
        client._fallback_e2e_compliance(test_input_e2e_compliance, "error")
        metrics.stop()
    results["e2e_fallback"] = metrics.get_summary()

    # Test 4: Parse Result
    metrics = PerformanceMetrics("Parse Result")
    data = {"result": {"allow": True, "violations": [], "details": {}}}
    for _ in range(1000):
        metrics.start()
        client._parse_result(data, "test")
        metrics.stop()
    results["parse"] = metrics.get_summary()

    # Test 5: Client Init
    metrics = PerformanceMetrics("Client Init")
    for _ in range(100):
        metrics.start()
        OPAClient(OPAClientConfig())
        metrics.stop()
    results["init"] = metrics.get_summary()

    # Print summary table
    print("\n" + "-" * 70)
    print("| Operation          | Count  | p95 (ms) | p99 (ms) | Target  | Status |")
    print("-" * 70)

    targets = {
        "evaluate": 100.0,
        "health": 50.0,
        "e2e_fallback": 10.0,
        "parse": 1.0,
        "init": 5.0,
    }

    for op_name, summary in results.items():
        p95 = summary["latency_p95_ms"]
        p99 = summary["latency_p99_ms"]
        target = targets[op_name]
        status = "✅ PASS" if p95 < target else "❌ FAIL"

        print(
            f"| {op_name.capitalize():<18} | {summary['count']:>6} | "
            f"{p95:>8.3f} | {p99:>8.3f} | {target:>5.1f}ms | {status} |"
        )

    print("-" * 70)

    # Overall assessment
    all_pass = all(
        results[op]["latency_p95_ms"] < targets[op]
        for op in targets
    )

    print("\n" + "=" * 70)
    if all_pass:
        print("OVERALL: ✅ ALL OPA CLIENT PERFORMANCE TARGETS MET")
    else:
        print("OVERALL: ❌ SOME PERFORMANCE TARGETS NOT MET")
    print("=" * 70 + "\n")

    assert all_pass, "Not all OPA client performance targets were met"
