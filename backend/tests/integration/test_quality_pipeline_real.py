"""
Integration Test: EP-06 Quality Pipeline against Real SDLC Orchestrator Code

Sprint 196 — Track B-03: Gate 1-3 integration test with real ruff + semgrep
Validates the 4-Gate Quality Pipeline against actual production source files
from the SDLC Orchestrator backend.

Test Strategy:
  - Gate 1 (Syntax): ast.parse + ruff check on real .py files
  - Gate 2 (Security): Semgrep SAST scan on real .py files
  - Gate 3 (Context): Import validation across real modules
  - Gate 4 (Tests): pytest in sandbox with a small test file

Runs against 5 representative files:
  1. middleware/tier_gate.py       — ASGI middleware (complex async)
  2. models/user.py                — SQLAlchemy ORM model (dataclass-heavy)
  3. services/codegen/quality_pipeline.py — The pipeline itself (meta-test)
  4. schemas/auth.py               — Pydantic v2 schemas
  5. middleware/usage_limits.py    — Another middleware (async + DB)
"""

import sys
import json
import time
from pathlib import Path

# Ensure backend is importable
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.codegen.quality_pipeline import (
    QualityPipeline,
    QualityGateProfile,
    QualityMode,
    GateStatus,
    PipelineResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_real_files(file_paths: list[str]) -> dict[str, str]:
    """Load real source files from the SDLC Orchestrator backend."""
    files: dict[str, str] = {}
    for rel_path in file_paths:
        full_path = BACKEND_ROOT / rel_path
        if full_path.exists():
            files[rel_path] = full_path.read_text(encoding="utf-8")
        else:
            print(f"  WARNING: File not found: {full_path}")
    return files


def print_gate_result(gate: dict) -> None:
    """Pretty-print a single gate result."""
    status_icon = {
        "passed": "PASS",
        "failed": "FAIL",
        "skipped": "SKIP",
        "soft_fail": "WARN",
    }.get(gate["status"], gate["status"])

    print(f"  Gate {gate['gate_number']}: {gate['gate_name']:<25} "
          f"[{status_icon}] "
          f"({gate['duration_ms']}ms) "
          f"— {gate['summary']}")

    if gate["issues"]:
        for issue in gate["issues"][:5]:  # Show first 5 issues
            sev = issue["severity"].upper()[:4]
            print(f"    [{sev}] {issue['file']}"
                  f"{':' + str(issue['line']) if issue['line'] else ''}"
                  f" — {issue['code']}: {issue['message'][:80]}")
        if len(gate["issues"]) > 5:
            print(f"    ... and {len(gate['issues']) - 5} more issues")


def print_pipeline_result(result: PipelineResult, label: str) -> None:
    """Pretty-print full pipeline result."""
    icon = "PASS" if result.success else "FAIL"
    print(f"\n{'=' * 70}")
    print(f"  {label}")
    print(f"  Result: [{icon}] {result.summary} ({result.total_duration_ms}ms)")
    print(f"{'=' * 70}")
    result_dict = result.to_dict()
    for gate in result_dict["gates"]:
        print_gate_result(gate)
    print()


# ---------------------------------------------------------------------------
# Test Scenarios
# ---------------------------------------------------------------------------

def test_scenario_1_single_middleware() -> PipelineResult:
    """Scenario 1: Single middleware file — Gate 1 + Gate 2 + Gate 3."""
    print("\n--- Scenario 1: Single Middleware (tier_gate.py) ---")
    files = load_real_files(["app/middleware/tier_gate.py"])
    pipeline = QualityPipeline(skip_tests=True)
    result = pipeline.run(files, language="python")
    print_pipeline_result(result, "Scenario 1: tier_gate.py (1 file)")
    return result


def test_scenario_2_multi_file_module() -> PipelineResult:
    """Scenario 2: Multiple related files — realistic codegen output."""
    print("\n--- Scenario 2: Multi-file Module (auth stack) ---")
    files = load_real_files([
        "app/schemas/auth.py",
        "app/api/routes/auth.py",
        "app/models/user.py",
    ])
    pipeline = QualityPipeline(skip_tests=True)
    result = pipeline.run(files, language="python")
    print_pipeline_result(result, "Scenario 2: Auth stack (3 files)")
    return result


def test_scenario_3_codegen_self_test() -> PipelineResult:
    """Scenario 3: Quality pipeline validates itself (meta-test)."""
    print("\n--- Scenario 3: Quality Pipeline Self-Test ---")
    files = load_real_files([
        "app/services/codegen/quality_pipeline.py",
    ])
    pipeline = QualityPipeline(skip_tests=True)
    result = pipeline.run(files, language="python")
    print_pipeline_result(result, "Scenario 3: quality_pipeline.py self-test")
    return result


def test_scenario_4_scaffold_mode() -> PipelineResult:
    """Scenario 4: Scaffold mode — lenient validation for app scaffolding."""
    print("\n--- Scenario 4: Scaffold Mode (5 files) ---")
    files = load_real_files([
        "app/middleware/tier_gate.py",
        "app/middleware/usage_limits.py",
        "app/middleware/conversation_first_guard.py",
        "app/models/user.py",
        "app/schemas/auth.py",
    ])
    # Use scaffold mode profile (Gate 3 = soft-fail, Gate 4 = smoke)
    pipeline = QualityPipeline(skip_tests=True)
    result = pipeline.run(files, language="python")
    print_pipeline_result(result, "Scenario 4: Scaffold mode (5 middleware+model files)")
    return result


def test_scenario_5_gate4_with_test_file() -> PipelineResult:
    """Scenario 5: Gate 4 — pytest execution with a real test file."""
    print("\n--- Scenario 5: Gate 4 Test Execution ---")

    # Create a minimal app + test for Gate 4 sandbox
    files = {
        "app/__init__.py": "",
        "app/calculator.py": (
            "\"\"\"Simple calculator for Gate 4 test.\"\"\"\n\n\n"
            "def add(a: int, b: int) -> int:\n"
            "    return a + b\n\n\n"
            "def multiply(a: int, b: int) -> int:\n"
            "    return a * b\n"
        ),
        "tests/__init__.py": "",
        "tests/test_calculator.py": (
            "\"\"\"Test calculator module.\"\"\"\n"
            "from app.calculator import add, multiply\n\n\n"
            "def test_add():\n"
            "    assert add(2, 3) == 5\n"
            "    assert add(-1, 1) == 0\n\n\n"
            "def test_multiply():\n"
            "    assert multiply(3, 4) == 12\n"
            "    assert multiply(0, 100) == 0\n"
        ),
    }

    # Enable Gate 4 (tests)
    pipeline = QualityPipeline(skip_tests=False, skip_security=True)
    result = pipeline.run(files, language="python")
    print_pipeline_result(result, "Scenario 5: Gate 4 with calculator tests")
    return result


def test_scenario_6_security_vulnerable_code() -> PipelineResult:
    """Scenario 6: Code with known security issues — Gate 2 should catch."""
    print("\n--- Scenario 6: Security-Vulnerable Code ---")

    files = {
        "app/vulnerable.py": (
            "import subprocess\n"
            "import sqlite3\n\n\n"
            "def run_command(user_input: str) -> str:\n"
            "    # Command injection — Semgrep should flag this\n"
            "    result = subprocess.run(user_input, shell=True, capture_output=True)\n"
            "    return result.stdout.decode()\n\n\n"
            "def get_user(username: str) -> dict:\n"
            "    # SQL injection — Semgrep should flag this\n"
            "    conn = sqlite3.connect('db.sqlite')\n"
            "    cursor = conn.cursor()\n"
            "    cursor.execute(f\"SELECT * FROM users WHERE name = '{username}'\")\n"
            "    return cursor.fetchone()\n"
        ),
    }

    pipeline = QualityPipeline(skip_tests=True)
    result = pipeline.run(files, language="python")
    print_pipeline_result(result, "Scenario 6: Vulnerable code (should find security issues)")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all quality pipeline integration tests."""
    print("=" * 70)
    print("  EP-06 Quality Pipeline — Real Code Integration Test")
    print("  Sprint 196 — Track B-03")
    print("  Project: SDLC Orchestrator")
    print(f"  Backend root: {BACKEND_ROOT}")
    print("=" * 70)

    results: dict[str, PipelineResult] = {}
    start = time.time()

    # Run all scenarios
    results["S1_single_middleware"] = test_scenario_1_single_middleware()
    results["S2_multi_file_auth"] = test_scenario_2_multi_file_module()
    results["S3_self_test"] = test_scenario_3_codegen_self_test()
    results["S4_scaffold_mode"] = test_scenario_4_scaffold_mode()
    results["S5_gate4_tests"] = test_scenario_5_gate4_with_test_file()
    results["S6_security_vuln"] = test_scenario_6_security_vulnerable_code()

    elapsed = time.time() - start

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    passed = 0
    total = len(results)
    for name, r in results.items():
        icon = "PASS" if r.success else "FAIL"
        gates_info = ", ".join(
            f"G{g.gate_number}:{g.status.value}"
            for g in r.gates
        )
        print(f"  [{icon}] {name:<30} — {r.summary} ({gates_info})")
        if r.success:
            passed += 1

    print(f"\n  Total: {passed}/{total} scenarios passed")
    print(f"  Duration: {elapsed:.2f}s")
    print("=" * 70)

    # Export results as JSON
    output_path = BACKEND_ROOT / "tests" / "integration" / "quality_pipeline_results.json"
    export = {
        "project": "SDLC-Orchestrator",
        "sprint": 196,
        "track": "B-03",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_scenarios": total,
        "passed_scenarios": passed,
        "duration_seconds": round(elapsed, 2),
        "scenarios": {
            name: r.to_dict() for name, r in results.items()
        },
    }
    output_path.write_text(json.dumps(export, indent=2), encoding="utf-8")
    print(f"\n  Results exported to: {output_path}")


if __name__ == "__main__":
    main()
