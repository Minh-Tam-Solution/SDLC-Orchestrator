"""
Integration Test: EP-06 Quality Pipeline against NQH-Bot Platform Code

Sprint 196 — Track B-03: Cross-project quality pipeline validation.
Validates the 4-Gate Quality Pipeline against NQH-Bot Platform source files
to prove the pipeline works on external codebases (not just self-referential).

NQH-Bot Platform:
  - Vietnamese HRM/Payroll platform (200K users, 3 years production)
  - FastAPI + SQLAlchemy + Celery
  - Different coding style and patterns from SDLC Orchestrator
"""

import sys
import json
import time
from pathlib import Path

# Ensure SDLC Orchestrator backend is importable (for QualityPipeline)
SDLC_BACKEND = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SDLC_BACKEND))

from app.services.codegen.quality_pipeline import (
    QualityPipeline,
    GateStatus,
    PipelineResult,
)

NQH_BOT_ROOT = Path("/home/nqh/shared/NQH-Bot-Platform/backend")


def load_nqhbot_files(rel_paths: list[str]) -> dict[str, str]:
    """Load source files from NQH-Bot Platform."""
    files: dict[str, str] = {}
    for rel_path in rel_paths:
        full_path = NQH_BOT_ROOT / rel_path
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
        for issue in gate["issues"][:5]:
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

def test_nqhbot_agents() -> PipelineResult:
    """NQH-Bot AI agent modules (orchestrator, base_agent, tool_registry)."""
    print("\n--- NQH-Bot Scenario 1: AI Agent Modules ---")
    files = load_nqhbot_files([
        "app/agents/base_agent.py",
        "app/agents/orchestrator.py",
        "app/agents/tool_registry.py",
    ])
    pipeline = QualityPipeline(skip_tests=True)
    result = pipeline.run(files, language="python")
    print_pipeline_result(result, "NQH-Bot S1: AI Agent modules (3 files)")
    return result


def test_nqhbot_api_routes() -> PipelineResult:
    """NQH-Bot API route files (auth, attendance, analytics)."""
    print("\n--- NQH-Bot Scenario 2: API Routes ---")
    files = load_nqhbot_files([
        "app/api/v1/auth.py",
        "app/api/v1/attendance.py",
        "app/api/v1/analytics.py",
    ])
    pipeline = QualityPipeline(skip_tests=True)
    result = pipeline.run(files, language="python")
    print_pipeline_result(result, "NQH-Bot S2: API routes (3 files)")
    return result


def test_nqhbot_anomaly_module() -> PipelineResult:
    """NQH-Bot anomaly detection module (service, detector, schemas)."""
    print("\n--- NQH-Bot Scenario 3: Anomaly Detection Module ---")
    files = load_nqhbot_files([
        "app/anomaly/__init__.py",
        "app/anomaly/detector.py",
        "app/anomaly/service.py",
        "app/anomaly/schemas.py",
    ])
    pipeline = QualityPipeline(skip_tests=True)
    result = pipeline.run(files, language="python")
    print_pipeline_result(result, "NQH-Bot S3: Anomaly detection (4 files)")
    return result


def test_nqhbot_security_scan() -> PipelineResult:
    """NQH-Bot auth files — security scan with Semgrep."""
    print("\n--- NQH-Bot Scenario 4: Security Scan (auth + RBAC) ---")
    files = load_nqhbot_files([
        "app/api/v1/auth.py",
        "app/api/deps.py",
        "app/api/rbac_endpoints.py",
    ])
    pipeline = QualityPipeline(skip_tests=True)
    result = pipeline.run(files, language="python")
    print_pipeline_result(result, "NQH-Bot S4: Auth security scan (3 files)")
    return result


def test_nqhbot_workflows() -> PipelineResult:
    """NQH-Bot workflow/saga modules."""
    print("\n--- NQH-Bot Scenario 5: Workflow/Saga Modules ---")
    files = load_nqhbot_files([
        "app/workflows/compensations/saga_schedule_workflow.py",
        "app/workflows/compensations/compensation_activities.py",
        "app/workflows/activities/notification_activities.py",
    ])
    pipeline = QualityPipeline(skip_tests=True)
    result = pipeline.run(files, language="python")
    print_pipeline_result(result, "NQH-Bot S5: Workflows/Sagas (3 files)")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all NQH-Bot quality pipeline tests."""
    print("=" * 70)
    print("  EP-06 Quality Pipeline — NQH-Bot Platform Integration Test")
    print("  Sprint 196 — Track B-03 (Cross-Project Validation)")
    print(f"  NQH-Bot root: {NQH_BOT_ROOT}")
    print("=" * 70)

    if not NQH_BOT_ROOT.exists():
        print(f"\n  ERROR: NQH-Bot Platform not found at {NQH_BOT_ROOT}")
        print("  Skipping NQH-Bot tests.")
        return

    results: dict[str, PipelineResult] = {}
    start = time.time()

    results["N1_agents"] = test_nqhbot_agents()
    results["N2_api_routes"] = test_nqhbot_api_routes()
    results["N3_anomaly"] = test_nqhbot_anomaly_module()
    results["N4_security"] = test_nqhbot_security_scan()
    results["N5_workflows"] = test_nqhbot_workflows()

    elapsed = time.time() - start

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY — NQH-Bot Platform")
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

    # Export results
    output_path = SDLC_BACKEND / "tests" / "integration" / "quality_pipeline_nqhbot_results.json"
    export = {
        "project": "NQH-Bot-Platform",
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
