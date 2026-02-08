#!/usr/bin/env python3
"""
SDLC Orchestrator SDK Cookbook - Python Recipes.

5 production-ready recipes demonstrating common SDK usage patterns.
Each recipe is self-contained with error handling and inline comments.

Recipes:
  1. CI/CD Gate Guard - Block deploys on gate failure
  2. Batch Project Scaffolding - Async concurrent generation
  3. Evidence Lifecycle - Submit test results, manage review
  4. Custom Golden Path - Create and generate from templates
  5. Quality Dashboard - Aggregate compliance across projects

Prerequisites:
  pip install sdlc-client
  export SDLC_BASE_URL="http://localhost:8000"
  export SDLC_API_KEY="sdlc_live_your_key_here"

Reference: docs/03-integrate/03-Integration-Guides/SDK-Cookbook.md
Sprint 170 - Developer Experience
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from sdlc_client import SdlcClient
from sdlc_client.exceptions import (
    NotFoundError,
    SdlcApiError,
    ValidationError,
)


# ---------------------------------------------------------------------------
# Recipe 1: CI/CD Gate Guard
# ---------------------------------------------------------------------------

def recipe_gate_guard(project_id: str, gate_id: str) -> int:
    """Evaluate a gate and return exit code 0 (pass) or 1 (fail).

    Usage in GitHub Actions:
        python cookbook.py gate-guard <project_id> <gate_id>
    """
    with SdlcClient() as client:
        try:
            result = client.gates.evaluate(
                gate_id=gate_id,
                project_id=project_id,
                context={"triggered_by": "ci_pipeline"},
            )
        except NotFoundError:
            print(f"ERROR: Project {project_id} or gate {gate_id} not found")
            return 1
        except SdlcApiError as e:
            print(f"ERROR: API call failed [{e.status_code}]: {e.message}")
            return 1

    if result.passed:
        print(f"PASS  Gate {gate_id} (score: {result.score}/100)")
        return 0

    print(f"FAIL  Gate {gate_id} (score: {result.score}/100)")
    for v in result.violations:
        print(f"  - [{v.severity}] {v.message}")
        if v.suggestion:
            print(f"    Fix: {v.suggestion}")
    return 1


# ---------------------------------------------------------------------------
# Recipe 2: Batch Project Scaffolding (Async)
# ---------------------------------------------------------------------------

async def recipe_batch_scaffold() -> None:
    """Generate multiple projects concurrently using async API."""
    services = [
        ("fastapi", "user-service", "User management microservice"),
        ("fastapi", "order-service", "Order processing microservice"),
        ("nextjs", "admin-dashboard", "Internal admin dashboard"),
    ]

    async with SdlcClient() as client:
        tasks = [
            _generate_one(client, path_id, name, desc)
            for path_id, name, desc in services
        ]
        results = await asyncio.gather(*tasks)

    print(f"\n{'Project':<20} {'Template':<10} {'Files':>5} {'Quality':>8}")
    print("-" * 50)
    for r in results:
        if "error" in r:
            print(f"{r['project']:<20} {r['template']:<10} {'ERR':>5}  {r['error']}")
        else:
            q = "PASS" if r["quality"] else "FAIL"
            print(f"{r['project']:<20} {r['template']:<10} {r['files']:>5} {q:>8}")


async def _generate_one(
    client: SdlcClient, path_id: str, name: str, desc: str
) -> dict:
    try:
        result = await client.codegen.agenerate(
            path_id=path_id,
            project_name=name,
            project_description=desc,
            author="Platform Team",
        )
        return {
            "project": name,
            "template": path_id,
            "files": result.file_count,
            "quality": result.quality_passed,
        }
    except SdlcApiError as e:
        return {"project": name, "template": path_id, "error": str(e.message)}


# ---------------------------------------------------------------------------
# Recipe 3: Evidence Lifecycle Automation
# ---------------------------------------------------------------------------

def recipe_evidence_lifecycle(
    project_id: str, gate_id: str, report_path: str
) -> None:
    """Submit test results as evidence and manage review workflow."""
    report = json.loads(Path(report_path).read_text())
    total = report.get("total", 0)
    passed = report.get("passed", 0)
    pass_rate = (passed / total * 100) if total > 0 else 0

    with SdlcClient() as client:
        evidence = client.evidence.submit(
            project_id=project_id,
            evidence_type="test_result",
            title=f"Test Results ({passed}/{total} passed, {pass_rate:.0f}%)",
            description=f"Automated test run from {report_path}",
            gate_id=gate_id,
            tags=["automated", "test-results"],
        )
        print(f"Submitted: {evidence.id} (state: {evidence.state})")

        if pass_rate >= 90:
            client.evidence.update_state(
                evidence_id=evidence.id,
                state="reviewed",
                comment="Auto-reviewed: pass rate meets threshold",
            )
            client.evidence.update_state(
                evidence_id=evidence.id,
                state="accepted",
                comment=f"Auto-accepted: {pass_rate:.0f}% pass rate",
            )
            print(f"  -> accepted (pass rate: {pass_rate:.0f}%)")
        else:
            print(f"  -> manual review required (pass rate: {pass_rate:.0f}%)")


# ---------------------------------------------------------------------------
# Recipe 4: Custom Golden Path Builder
# ---------------------------------------------------------------------------

def recipe_custom_golden_path() -> None:
    """Create a custom template and generate a project from it."""
    with SdlcClient() as client:
        custom = client.codegen.create_custom_path(
            path_id="flask-micro",
            display_name="Flask Microservice",
            description="Lightweight Flask service with health check",
            category="backend",
            version="1.0.0",
            tech_stack=["python", "flask", "docker"],
            file_definitions=[
                {
                    "path_template": "{{project_name}}/app.py",
                    "content_template": (
                        'from flask import Flask, jsonify\n\n'
                        'app = Flask(__name__)\n\n'
                        "@app.route('/health')\n"
                        'def health():\n'
                        "    return jsonify(status='healthy', service='{{project_name}}')\n"
                    ),
                    "language": "python",
                    "category": "entry_point",
                },
                {
                    "path_template": "{{project_name}}/Dockerfile",
                    "content_template": (
                        "FROM python:3.12-slim\nWORKDIR /app\n"
                        "COPY requirements.txt .\n"
                        "RUN pip install --no-cache-dir -r requirements.txt\n"
                        "COPY . .\nEXPOSE 8000\n"
                        'CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]\n'
                    ),
                    "language": "dockerfile",
                    "category": "config_file",
                },
            ],
        )
        print(f"Created: {custom.path_id} ({custom.display_name})")

        validation = client.codegen.validate_custom_path("flask-micro")
        print(f"Validation: {'PASS' if validation.valid else 'FAIL'}")

        result = client.codegen.generate_from_custom(
            path_id="flask-micro",
            project_name="payment_service",
        )
        print(f"Generated {result.file_count} files ({result.total_lines} LOC)")


# ---------------------------------------------------------------------------
# Recipe 5: Quality Dashboard Reporter
# ---------------------------------------------------------------------------

def recipe_compliance_report() -> None:
    """Aggregate gate scores across all active projects."""
    with SdlcClient() as client:
        projects = client.projects.list(status="active", limit=100)

        total_score = 0.0
        passed_gates = 0
        total_gates = 0

        print(f"\n{'Project':<25} {'Tier':<12} {'Score':>7} {'Gates':>6}")
        print("-" * 55)

        for project in projects.items:
            try:
                gates = client.gates.list_gates(project.id)
            except SdlcApiError:
                print(f"{project.name:<25} {project.tier:<12} {'ERROR':>7}")
                continue

            scores = []
            for gate in gates:
                total_gates += 1
                if gate.status == "passed":
                    passed_gates += 1
                    score = gate.last_evaluation.score if gate.last_evaluation else 100
                    scores.append(score)

            avg = sum(scores) / len(scores) if scores else 0
            total_score += avg
            print(f"{project.name:<25} {project.tier:<12} {avg:>6.0f}% {len(gates):>5}")

        n = len(projects.items)
        overall = total_score / n if n > 0 else 0
        rate = (passed_gates / total_gates * 100) if total_gates > 0 else 0

        print(f"\n--- Summary ({datetime.now():%Y-%m-%d %H:%M}) ---")
        print(f"Projects: {n} | Overall: {overall:.0f}% | Gate pass rate: {rate:.0f}%")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print("SDLC SDK Cookbook - Python Recipes")
        print()
        print("Usage:")
        print("  python cookbook.py gate-guard <project_id> <gate_id>")
        print("  python cookbook.py batch-scaffold")
        print("  python cookbook.py evidence <project_id> <gate_id> <report.json>")
        print("  python cookbook.py custom-path")
        print("  python cookbook.py compliance-report")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "gate-guard" and len(sys.argv) == 4:
        sys.exit(recipe_gate_guard(sys.argv[2], sys.argv[3]))
    elif cmd == "batch-scaffold":
        asyncio.run(recipe_batch_scaffold())
    elif cmd == "evidence" and len(sys.argv) == 5:
        recipe_evidence_lifecycle(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "custom-path":
        recipe_custom_golden_path()
    elif cmd == "compliance-report":
        recipe_compliance_report()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(2)


if __name__ == "__main__":
    main()
