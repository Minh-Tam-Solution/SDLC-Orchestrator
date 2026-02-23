"""
Quality Pipeline Benchmark Tests.

Sprint 197 — CF-02: Benchmarks for Gate 1-4 latency.
Uses pytest-benchmark to measure per-gate execution time.

Run with:
    pytest backend/tests/unit/services/codegen/test_quality_pipeline_benchmark.py -v --benchmark-only
"""

from app.services.codegen.quality_pipeline import QualityPipeline, GateStatus


# ---------------------------------------------------------------------------
# Sample code fixtures
# ---------------------------------------------------------------------------

SIMPLE_PYTHON = {
    "app/models/user.py": '''"""User model."""
from datetime import datetime
from typing import Optional


class User:
    """User entity."""

    def __init__(self, name: str, email: str) -> None:
        self.name = name
        self.email = email
        self.created_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<User(name={self.name})>"
''',
}

MULTI_FILE_PYTHON = {
    "app/models/order.py": '''"""Order model."""
from datetime import datetime
from typing import Optional
import uuid


class Order:
    """Order entity."""

    def __init__(self, customer_id: str, total: float) -> None:
        self.id = str(uuid.uuid4())
        self.customer_id = customer_id
        self.total = total
        self.created_at = datetime.utcnow()
''',
    "app/services/order_service.py": '''"""Order service."""
from typing import Optional


class OrderService:
    """Service for managing orders."""

    def __init__(self) -> None:
        self.orders: list = []

    def create_order(self, customer_id: str, total: float) -> dict:
        """Create a new order."""
        order = {"customer_id": customer_id, "total": total}
        self.orders.append(order)
        return order

    def get_order(self, order_id: str) -> Optional[dict]:
        """Get order by ID."""
        for order in self.orders:
            if order.get("id") == order_id:
                return order
        return None
''',
    "app/api/routes/orders.py": '''"""Order API routes."""
from typing import Optional


def get_orders() -> list:
    """Get all orders."""
    return []


def create_order(customer_id: str, total: float) -> dict:
    """Create order endpoint."""
    return {"customer_id": customer_id, "total": total, "status": "created"}
''',
}


def _find_gate(gates, gate_number):
    """Find gate result by gate number from the gates list."""
    for g in gates:
        if g.gate_number == gate_number:
            return g
    return None


# ---------------------------------------------------------------------------
# Benchmark: Gate 1 — Syntax Check (ast.parse + ruff)
# ---------------------------------------------------------------------------

class TestGate1Benchmark:
    """Benchmark Gate 1 (Syntax) latency."""

    def test_gate1_single_file(self, benchmark):
        """Benchmark Gate 1 on a single Python file."""
        pipeline = QualityPipeline(skip_security=True, skip_tests=True)

        def run():
            return pipeline.run(SIMPLE_PYTHON, language="python")

        result = benchmark(run)
        gate1 = _find_gate(result.gates, 1)
        assert gate1 is not None
        assert gate1.status in (GateStatus.PASSED, GateStatus.FAILED)

    def test_gate1_multi_file(self, benchmark):
        """Benchmark Gate 1 on 3 Python files."""
        pipeline = QualityPipeline(skip_security=True, skip_tests=True)

        def run():
            return pipeline.run(MULTI_FILE_PYTHON, language="python")

        result = benchmark(run)
        gate1 = _find_gate(result.gates, 1)
        assert gate1 is not None
        assert gate1.status in (GateStatus.PASSED, GateStatus.FAILED)


# ---------------------------------------------------------------------------
# Benchmark: Gate 2 — Security Scan (Semgrep)
# ---------------------------------------------------------------------------

class TestGate2Benchmark:
    """Benchmark Gate 2 (Security) latency."""

    def test_gate2_single_file(self, benchmark):
        """Benchmark Gate 2 on a single Python file."""
        pipeline = QualityPipeline(skip_security=False, skip_tests=True)

        def run():
            return pipeline.run(SIMPLE_PYTHON, language="python")

        result = benchmark(run)
        gate2 = _find_gate(result.gates, 2)
        if gate2:
            assert gate2.status in (
                GateStatus.PASSED,
                GateStatus.FAILED,
                GateStatus.SKIPPED,
            )


# ---------------------------------------------------------------------------
# Benchmark: Gate 3 — Context Validation
# ---------------------------------------------------------------------------

class TestGate3Benchmark:
    """Benchmark Gate 3 (Context) latency."""

    def test_gate3_multi_file(self, benchmark):
        """Benchmark Gate 3 on 3 Python files."""
        pipeline = QualityPipeline(skip_security=True, skip_tests=True)

        def run():
            return pipeline.run(MULTI_FILE_PYTHON, language="python")

        result = benchmark(run)
        gate3 = _find_gate(result.gates, 3)
        if gate3:
            assert gate3.status in (
                GateStatus.PASSED,
                GateStatus.FAILED,
                GateStatus.SOFT_FAIL,
                GateStatus.SKIPPED,
            )


# ---------------------------------------------------------------------------
# Benchmark: Full Pipeline (Gate 1 + Gate 3, skip security + tests)
# ---------------------------------------------------------------------------

class TestFullPipelineBenchmark:
    """Benchmark full pipeline (G1 + G3) latency."""

    def test_full_pipeline_single_file(self, benchmark):
        """Benchmark full pipeline on single file (G1+G3 only)."""
        pipeline = QualityPipeline(skip_security=True, skip_tests=True)

        def run():
            return pipeline.run(SIMPLE_PYTHON, language="python")

        result = benchmark(run)
        assert len(result.gates) >= 1
        assert result.gates[0].status in (GateStatus.PASSED, GateStatus.FAILED)

    def test_full_pipeline_multi_file(self, benchmark):
        """Benchmark full pipeline on 3 files (G1+G3 only)."""
        pipeline = QualityPipeline(skip_security=True, skip_tests=True)

        def run():
            return pipeline.run(MULTI_FILE_PYTHON, language="python")

        result = benchmark(run)
        assert len(result.gates) >= 1
        assert result.gates[0].status in (GateStatus.PASSED, GateStatus.FAILED)
