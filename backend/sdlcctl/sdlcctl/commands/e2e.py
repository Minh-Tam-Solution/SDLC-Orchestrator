"""sdlcctl e2e commands.

Sprint 138 implementation: RFC-SDLC-602 E2E API Testing Enhancement.
Sprint 140 updates: --init flag, auth-setup command, --fix flag, OPA integration.
Sprint 141 updates: parse-openapi command, run-tests command.

Commands:
  - validate: Validate E2E testing compliance + optional --init for folder setup
  - cross-reference: Validate Stage 03 ↔ Stage 05 cross-references + --fix
  - generate-report: Generate E2E API test report (from JSON or OpenAPI)
  - auth-setup: Setup authentication for E2E API testing (Sprint 140)
  - parse-openapi: Parse OpenAPI spec and extract testable endpoints (Sprint 141)
  - run-tests: Execute E2E tests using Newman/pytest (Sprint 141)

Reference:
  - RFC-SDLC-602-E2E-API-TESTING
  - SDLC Framework 6.0.5
  - Skill: e2e-api-testing (6-phase workflow)
  - OPA Policy: e2e_testing_compliance.rego, stage_cross_reference.rego
"""

import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

from ..lib.opa_client import OPAClient, get_opa_client

console = Console()

# Create sub-app for E2E testing commands
app = typer.Typer(
    name="e2e",
    help="E2E API Testing validation commands (RFC-SDLC-602)",
    no_args_is_help=True,
)


@app.command(name="validate")
def validate_e2e_command(
    project_path: Path = typer.Option(
        Path.cwd(),
        "--project-path",
        "-p",
        help="Project root path",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    min_pass_rate: int = typer.Option(
        80,
        "--min-pass-rate",
        "-m",
        help="Minimum E2E test pass rate (0-100)",
        min=0,
        max=100,
    ),
    from_stage: str = typer.Option(
        "05-TESTING",
        "--from-stage",
        help="Source stage for transition validation",
    ),
    to_stage: str = typer.Option(
        "06-DEPLOY",
        "--to-stage",
        help="Target stage for transition validation",
    ),
    evidence_path: Optional[Path] = typer.Option(
        None,
        "--evidence",
        "-e",
        help="Path to evidence JSON file (default: auto-discover)",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text, json, summary",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        "-s",
        help="Exit with error code 1 if validation fails",
    ),
    init: bool = typer.Option(
        False,
        "--init",
        help="Initialize E2E testing folder structure before validation (Sprint 140)",
    ),
    use_opa: bool = typer.Option(
        True,
        "--use-opa/--no-opa",
        help="Use OPA for policy evaluation (Sprint 140)",
    ),
) -> None:
    """
    Validate E2E testing compliance for stage transitions.

    Checks RFC-SDLC-602 requirements:
    - E2E test report exists in evidence
    - Pass rate meets minimum threshold
    - API documentation reference exists

    Examples:

        sdlcctl e2e validate

        sdlcctl e2e validate --min-pass-rate 90

        sdlcctl e2e validate --evidence ./e2e-evidence.json --strict

        sdlcctl e2e validate --init  # Initialize folder structure first

        sdlcctl e2e validate --no-opa  # Skip OPA, use local validation
    """
    # Handle --init flag: Create E2E testing folder structure
    if init:
        console.print("[blue]Initializing E2E testing structure...[/blue]")
        init_result = _initialize_e2e_folders(project_path)
        if init_result["success"]:
            console.print(f"[green]✓ E2E structure initialized at {init_result['path']}[/green]")
            for file_created in init_result.get("files_created", []):
                console.print(f"  [dim]• {file_created}[/dim]")
        else:
            console.print(f"[red]✗ Initialization failed: {init_result['error']}[/red]")
            if strict:
                raise typer.Exit(code=1)
            return

    # Run validation (with OPA integration if enabled)
    with console.status("[bold blue]Validating E2E testing compliance...[/bold blue]"):
        if use_opa:
            result = _validate_e2e_compliance_opa(
                project_path=project_path,
                min_pass_rate=min_pass_rate,
                from_stage=from_stage,
                to_stage=to_stage,
                evidence_path=evidence_path,
            )
        else:
            result = _validate_e2e_compliance(
                project_path=project_path,
                min_pass_rate=min_pass_rate,
                from_stage=from_stage,
                to_stage=to_stage,
                evidence_path=evidence_path,
            )

    _render_e2e_result(result, output_format)

    if strict and not result["allow_transition"]:
        raise typer.Exit(code=1)


@app.command(name="cross-reference")
def validate_cross_reference_command(
    stage_03: Path = typer.Option(
        None,
        "--stage-03",
        help="Path to Stage 03 (Integration & APIs) folder",
    ),
    stage_05: Path = typer.Option(
        None,
        "--stage-05",
        help="Path to Stage 05 (Testing & Quality) folder",
    ),
    project_path: Path = typer.Option(
        Path.cwd(),
        "--project-path",
        "-p",
        help="Project root path (used for auto-discovery)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text, json, summary",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        "-s",
        help="Exit with error code 1 if validation fails",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Auto-fix SSOT violations (create symlinks for duplicates) (Sprint 140)",
    ),
    use_opa: bool = typer.Option(
        True,
        "--use-opa/--no-opa",
        help="Use OPA for policy evaluation (Sprint 140 Day 2)",
    ),
) -> None:
    """
    Validate Stage 03 ↔ Stage 05 cross-references.

    Checks bidirectional traceability:
    - Stage 03 API Reference links to Stage 05 test reports
    - Stage 05 E2E reports link back to Stage 03 API docs
    - SSOT compliance (no duplicate openapi.json)

    Examples:

        sdlcctl e2e cross-reference

        sdlcctl e2e cross-reference \\
            --stage-03 docs/03-Integration-APIs \\
            --stage-05 docs/05-Testing-Quality

        sdlcctl e2e cross-reference --strict

        sdlcctl e2e cross-reference --fix  # Auto-fix SSOT violations

        sdlcctl e2e cross-reference --no-opa  # Skip OPA, use local validation
    """
    # Auto-discover stage folders if not provided
    if stage_03 is None:
        stage_03 = project_path / "docs" / "03-Integration-APIs"
    if stage_05 is None:
        stage_05 = project_path / "docs" / "05-Testing-Quality"

    with console.status("[bold blue]Validating cross-references...[/bold blue]"):
        if use_opa:
            result = _validate_cross_references_opa(
                stage_03=stage_03,
                stage_05=stage_05,
                project_path=project_path,
            )
        else:
            result = _validate_cross_references(
                stage_03=stage_03,
                stage_05=stage_05,
                project_path=project_path,
            )

    _render_cross_reference_result(result, output_format)

    # Handle --fix flag: Auto-fix SSOT violations
    if fix and result["duplicate_openapi_locations"]:
        console.print()
        console.print("[yellow]Attempting to fix SSOT violations...[/yellow]")
        fix_result = _fix_ssot_violations(
            duplicates=result["duplicate_openapi_locations"],
            canonical_path=stage_03 / "02-API-Specifications" / "openapi.json",
        )
        if fix_result["success"]:
            console.print(f"[green]✓ Fixed {fix_result['fixed_count']} SSOT violations[/green]")
            for fixed_file in fix_result.get("fixed_files", []):
                console.print(f"  [dim]• {fixed_file}[/dim]")
        else:
            console.print(f"[red]✗ Fix failed: {fix_result['error']}[/red]")

    if strict and not result["cross_reference_valid"]:
        raise typer.Exit(code=1)


@app.command(name="generate-report")
def generate_e2e_report_command(
    results_path: Path = typer.Option(
        ...,
        "--results",
        "-r",
        help="Path to test results JSON file",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    output_dir: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for report (default: docs/05-Testing-Quality/03-E2E-Testing/reports/)",
    ),
    project_path: Path = typer.Option(
        Path.cwd(),
        "--project-path",
        "-p",
        help="Project root path",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    api_reference: Optional[Path] = typer.Option(
        None,
        "--api-reference",
        help="Path to API reference document (for cross-reference)",
    ),
    openapi_spec: Optional[Path] = typer.Option(
        None,
        "--openapi",
        help="Path to OpenAPI spec (for SSOT link)",
    ),
) -> None:
    """
    Generate E2E API test report from test results.

    Creates a markdown report with:
    - Test execution summary
    - Pass/fail statistics by category
    - Cross-reference links to Stage 03
    - SSOT compliance note

    Examples:

        sdlcctl e2e generate-report --results test_results.json

        sdlcctl e2e generate-report \\
            --results test_results.json \\
            --output docs/05-Testing-Quality/03-E2E-Testing/reports/
    """
    # Auto-discover output directory if not provided
    if output_dir is None:
        output_dir = project_path / "docs" / "05-Testing-Quality" / "03-E2E-Testing" / "reports"

    # Auto-discover API reference if not provided
    if api_reference is None:
        api_reference = project_path / "docs" / "03-Integration-APIs" / "02-API-Specifications" / "COMPLETE-API-ENDPOINT-REFERENCE.md"

    # Auto-discover OpenAPI spec if not provided
    if openapi_spec is None:
        openapi_spec = project_path / "docs" / "03-Integration-APIs" / "02-API-Specifications" / "openapi.json"

    with console.status("[bold blue]Generating E2E report...[/bold blue]"):
        report_path = _generate_e2e_report(
            results_path=results_path,
            output_dir=output_dir,
            api_reference=api_reference,
            openapi_spec=openapi_spec,
        )

    console.print(f"[green]✓[/green] Report generated: {report_path}")


def _validate_e2e_compliance(
    project_path: Path,
    min_pass_rate: int,
    from_stage: str,
    to_stage: str,
    evidence_path: Optional[Path],
) -> dict:
    """Validate E2E testing compliance against RFC-SDLC-602 requirements."""
    result = {
        "has_e2e_report": False,
        "has_api_documentation": False,
        "e2e_pass_rate": 0.0,
        "total_endpoints": 0,
        "failed_endpoints": 0,
        "min_pass_rate_threshold": min_pass_rate,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "violations": [],
        "allow_transition": False,
    }

    # Check if not transitioning from Stage 05, E2E not required
    if from_stage != "05-TESTING":
        result["allow_transition"] = True
        result["violations"].append("E2E validation not required for this stage transition")
        return result

    # Load evidence
    evidence = _load_evidence(project_path, evidence_path)

    # Check for E2E test report
    e2e_reports = [e for e in evidence if e.get("artifact_type") == "E2E_TESTING_REPORT"]
    if e2e_reports:
        result["has_e2e_report"] = True
        latest_report = e2e_reports[-1]
        metadata = latest_report.get("metadata", {})
        result["e2e_pass_rate"] = metadata.get("pass_rate", 0)
        result["total_endpoints"] = metadata.get("total_endpoints", 0)
        result["failed_endpoints"] = metadata.get("failed_endpoints", 0)
    else:
        result["violations"].append(
            "E2E_REPORT_MISSING: E2E API test report required for Stage 05 → 06 transition"
        )

    # Check for API documentation reference
    api_docs = [e for e in evidence if e.get("artifact_type") == "API_DOCUMENTATION_REFERENCE"]
    if api_docs:
        result["has_api_documentation"] = True
    else:
        result["violations"].append(
            "API_DOCS_MISSING: API documentation reference required for Stage 05 → 06 transition"
        )

    # Check pass rate
    if result["has_e2e_report"] and result["e2e_pass_rate"] < min_pass_rate:
        result["violations"].append(
            f"E2E_PASS_RATE_LOW: E2E pass rate {result['e2e_pass_rate']:.1f}% is below minimum {min_pass_rate}%"
        )

    # Determine if transition is allowed
    result["allow_transition"] = (
        result["has_e2e_report"]
        and result["has_api_documentation"]
        and result["e2e_pass_rate"] >= min_pass_rate
    )

    return result


def _validate_cross_references(
    stage_03: Path,
    stage_05: Path,
    project_path: Path,
) -> dict:
    """Validate bidirectional cross-references between Stage 03 and Stage 05."""
    result = {
        "stage_03_exists": stage_03.exists(),
        "stage_05_exists": stage_05.exists(),
        "has_stage_03_links": False,
        "has_stage_05_links": False,
        "ssot_compliance": True,
        "duplicate_openapi_locations": [],
        "violations": [],
        "cross_reference_valid": False,
    }

    if not result["stage_03_exists"]:
        result["violations"].append(f"STAGE_03_MISSING: Stage 03 folder not found at {stage_03}")
        return result

    if not result["stage_05_exists"]:
        result["violations"].append(f"STAGE_05_MISSING: Stage 05 folder not found at {stage_05}")
        return result

    # Check Stage 03 → Stage 05 links
    api_reference = stage_03 / "02-API-Specifications" / "COMPLETE-API-ENDPOINT-REFERENCE.md"
    if api_reference.exists():
        content = api_reference.read_text(encoding="utf-8")
        if "05-Testing-Quality" in content or "Stage 05" in content:
            result["has_stage_03_links"] = True
        else:
            result["violations"].append(
                "MISSING_STAGE_05_LINK: API Reference missing links to Stage 05 test reports"
            )
    else:
        result["violations"].append(
            f"API_REFERENCE_MISSING: {api_reference} not found"
        )

    # Check Stage 05 → Stage 03 links
    e2e_reports_dir = stage_05 / "03-E2E-Testing" / "reports"
    if e2e_reports_dir.exists():
        for report_file in e2e_reports_dir.glob("*.md"):
            content = report_file.read_text(encoding="utf-8")
            if "03-Integration-APIs" in content or "Stage 03" in content:
                result["has_stage_05_links"] = True
                break
        if not result["has_stage_05_links"]:
            result["violations"].append(
                "MISSING_STAGE_03_LINK: E2E reports missing links to Stage 03 API documentation"
            )
    else:
        # E2E reports directory doesn't exist yet - not necessarily a violation
        result["violations"].append(
            f"E2E_REPORTS_DIR_MISSING: {e2e_reports_dir} not found (create with 'sdlcctl e2e generate-report')"
        )

    # Check SSOT compliance (no duplicate openapi.json)
    openapi_locations = list(project_path.rglob("openapi.json"))
    ssot_location = stage_03 / "02-API-Specifications" / "openapi.json"

    for loc in openapi_locations:
        # Skip symlinks (they're OK)
        if loc.is_symlink():
            continue
        # Skip the SSOT location
        if loc.resolve() == ssot_location.resolve():
            continue
        # Found a duplicate
        result["duplicate_openapi_locations"].append(str(loc))

    if result["duplicate_openapi_locations"]:
        result["ssot_compliance"] = False
        result["violations"].append(
            f"SSOT_VIOLATION: Duplicate openapi.json found at: {', '.join(result['duplicate_openapi_locations'])}"
        )

    # Determine overall validity
    result["cross_reference_valid"] = (
        result["has_stage_03_links"]
        and (result["has_stage_05_links"] or "E2E_REPORTS_DIR_MISSING" in str(result["violations"]))
        and result["ssot_compliance"]
    )

    return result


def _load_evidence(project_path: Path, evidence_path: Optional[Path]) -> list:
    """Load evidence from JSON file or auto-discover."""
    if evidence_path and evidence_path.exists():
        return json.loads(evidence_path.read_text(encoding="utf-8"))

    # Auto-discover evidence files
    evidence = []
    evidence_dirs = [
        project_path / "docs" / "02-design" / "evidence",
        project_path / "docs" / "05-Testing-Quality" / "03-E2E-Testing" / "evidence",
    ]

    for evidence_dir in evidence_dirs:
        if evidence_dir.exists():
            for evidence_file in evidence_dir.glob("*.json"):
                try:
                    data = json.loads(evidence_file.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        evidence.append(data)
                    elif isinstance(data, list):
                        evidence.extend(data)
                except json.JSONDecodeError:
                    continue

    return evidence


def _generate_e2e_report(
    results_path: Path,
    output_dir: Path,
    api_reference: Path,
    openapi_spec: Path,
) -> Path:
    """Generate E2E API test report from test results JSON."""
    # Load test results
    results = json.loads(results_path.read_text(encoding="utf-8"))

    # Calculate statistics
    total = results.get("total_tests", 0)
    passed = results.get("passed", 0)
    failed = results.get("failed", 0)
    skipped = results.get("skipped", 0)
    pass_rate = (passed / total * 100) if total > 0 else 0

    # Generate report filename with date
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_filename = f"E2E-API-REPORT-{date_str}.md"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / report_filename

    # Build relative paths for cross-references
    try:
        api_ref_rel = api_reference.relative_to(output_dir.parent.parent.parent)
    except ValueError:
        api_ref_rel = api_reference

    try:
        openapi_rel = openapi_spec.relative_to(output_dir.parent.parent.parent)
    except ValueError:
        openapi_rel = openapi_spec

    # Generate report content
    report_content = f"""# E2E API Test Report

**Project**: SDLC Orchestrator
**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Framework**: SDLC 6.0.5
**Stage**: 05-Testing-Quality

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {total} |
| Passed | {passed} |
| Failed | {failed} |
| Skipped | {skipped} |
| **Pass Rate** | **{pass_rate:.1f}%** |

### Status: {"✅ PASS" if pass_rate >= 80 else "❌ FAIL"} (Threshold: 80%)

---

## Test Results by Category

"""

    # Add category breakdown if available
    categories = results.get("categories", {})
    if categories:
        report_content += "| Category | Total | Passed | Failed | Pass Rate |\n"
        report_content += "|----------|-------|--------|--------|----------|\n"
        for cat_name, cat_data in categories.items():
            cat_total = cat_data.get("total", 0)
            cat_passed = cat_data.get("passed", 0)
            cat_failed = cat_data.get("failed", 0)
            cat_rate = (cat_passed / cat_total * 100) if cat_total > 0 else 0
            status = "✅" if cat_rate >= 80 else "❌"
            report_content += f"| {cat_name} | {cat_total} | {cat_passed} | {cat_failed} | {status} {cat_rate:.1f}% |\n"
        report_content += "\n"

    # Add failed tests details if available
    failed_tests = results.get("failed_tests", [])
    if failed_tests:
        report_content += "## Failed Tests\n\n"
        for test in failed_tests[:10]:  # Limit to first 10
            report_content += f"### {test.get('name', 'Unknown Test')}\n\n"
            report_content += f"- **Endpoint**: `{test.get('endpoint', 'N/A')}`\n"
            report_content += f"- **Method**: `{test.get('method', 'N/A')}`\n"
            report_content += f"- **Expected**: `{test.get('expected', 'N/A')}`\n"
            report_content += f"- **Actual**: `{test.get('actual', 'N/A')}`\n"
            report_content += f"- **Error**: {test.get('error', 'N/A')}\n\n"

    # Add cross-reference section
    report_content += f"""---

## Cross-Reference

### Stage 03 - Integration & APIs
- **API Documentation**: [{api_ref_rel}](../../../{api_ref_rel})
- **OpenAPI Spec**: [{openapi_rel}](../../../{openapi_rel}) (SSOT)

### SSOT Note
The `openapi.json` file is maintained in Stage 03 (Integration & APIs).
Stage 05 references this file via relative path - **do not duplicate**.

---

## Artifact Metadata

```json
{{
  "artifact_type": "E2E_TESTING_REPORT",
  "generated_at": "{datetime.now().isoformat()}Z",
  "framework_version": "6.0.5",
  "pass_rate": {pass_rate:.1f},
  "total_endpoints": {total},
  "failed_endpoints": {failed},
  "cross_reference": {{
    "stage_03_api_reference": "{api_ref_rel}",
    "stage_03_openapi_spec": "{openapi_rel}"
  }}
}}
```

---

*Generated by sdlcctl e2e generate-report (RFC-SDLC-602)*
"""

    # Write report
    report_path.write_text(report_content, encoding="utf-8")

    return report_path


def _render_e2e_result(result: dict, output_format: str) -> None:
    """Render E2E validation result."""
    fmt = output_format.lower().strip()

    if fmt == "json":
        console.print(json.dumps(result, indent=2))
        return

    if fmt == "summary":
        status = "PASS" if result["allow_transition"] else "FAIL"
        console.print(
            f"{status} | Pass Rate: {result['e2e_pass_rate']:.1f}% | "
            f"Threshold: {result['min_pass_rate_threshold']}% | "
            f"Violations: {len(result['violations'])}"
        )
        return

    # Default: text format
    status_color = "green" if result["allow_transition"] else "red"
    status_text = "PASS" if result["allow_transition"] else "FAIL"

    console.print()
    console.print(Panel(
        f"[bold {status_color}]{status_text}[/bold {status_color}]",
        title="E2E Testing Compliance (RFC-SDLC-602)",
    ))

    table = Table(show_header=True, header_style="bold")
    table.add_column("Check", width=30)
    table.add_column("Status", justify="center", width=10)
    table.add_column("Details", width=40)

    # E2E Report check
    e2e_status = "✅" if result["has_e2e_report"] else "❌"
    table.add_row(
        "E2E Test Report",
        e2e_status,
        f"Pass rate: {result['e2e_pass_rate']:.1f}%" if result["has_e2e_report"] else "Not found",
    )

    # API Documentation check
    api_status = "✅" if result["has_api_documentation"] else "❌"
    table.add_row(
        "API Documentation Reference",
        api_status,
        "Found" if result["has_api_documentation"] else "Not found",
    )

    # Pass rate check
    rate_status = "✅" if result["e2e_pass_rate"] >= result["min_pass_rate_threshold"] else "❌"
    table.add_row(
        "Pass Rate Threshold",
        rate_status,
        f"{result['e2e_pass_rate']:.1f}% >= {result['min_pass_rate_threshold']}%",
    )

    console.print(table)

    # Show violations if any
    if result["violations"]:
        console.print()
        console.print("[bold red]Violations:[/bold red]")
        for violation in result["violations"]:
            console.print(f"  • {violation}")

    console.print()


def _render_cross_reference_result(result: dict, output_format: str) -> None:
    """Render cross-reference validation result."""
    fmt = output_format.lower().strip()

    if fmt == "json":
        console.print(json.dumps(result, indent=2))
        return

    if fmt == "summary":
        status = "PASS" if result["cross_reference_valid"] else "FAIL"
        ssot = "✅" if result["ssot_compliance"] else "❌"
        console.print(
            f"{status} | Stage 03→05: {'✅' if result['has_stage_03_links'] else '❌'} | "
            f"Stage 05→03: {'✅' if result['has_stage_05_links'] else '❌'} | "
            f"SSOT: {ssot}"
        )
        return

    # Default: text format
    status_color = "green" if result["cross_reference_valid"] else "red"
    status_text = "PASS" if result["cross_reference_valid"] else "FAIL"

    console.print()
    console.print(Panel(
        f"[bold {status_color}]{status_text}[/bold {status_color}]",
        title="Cross-Reference Validation (Stage 03 ↔ Stage 05)",
    ))

    table = Table(show_header=True, header_style="bold")
    table.add_column("Check", width=35)
    table.add_column("Status", justify="center", width=10)

    table.add_row(
        "Stage 03 → Stage 05 Links",
        "✅" if result["has_stage_03_links"] else "❌",
    )
    table.add_row(
        "Stage 05 → Stage 03 Links",
        "✅" if result["has_stage_05_links"] else "❌",
    )
    table.add_row(
        "SSOT Compliance (no duplicate openapi.json)",
        "✅" if result["ssot_compliance"] else "❌",
    )

    console.print(table)

    # Show violations if any
    if result["violations"]:
        console.print()
        console.print("[bold red]Violations:[/bold red]")
        for violation in result["violations"]:
            console.print(f"  • {violation}")

    # Show duplicate locations if any
    if result["duplicate_openapi_locations"]:
        console.print()
        console.print("[bold yellow]Duplicate openapi.json locations:[/bold yellow]")
        for loc in result["duplicate_openapi_locations"]:
            console.print(f"  • {loc}")

    console.print()


# =============================================================================
# Sprint 140: New Commands and Helper Functions
# =============================================================================


@app.command(name="auth-setup")
def auth_setup_command(
    auth_type: str = typer.Option(
        "oauth2",
        "--type",
        "-t",
        help="Auth type: oauth2, api_key, basic, bearer",
    ),
    output_path: Path = typer.Option(
        Path(".env.test"),
        "--output",
        "-o",
        help="Output file for credentials",
    ),
    project_path: Path = typer.Option(
        Path.cwd(),
        "--project-path",
        "-p",
        help="Project root path",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    token_url: Optional[str] = typer.Option(
        None,
        "--token-url",
        help="Token URL for OAuth2 flow",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--non-interactive",
        help="Prompt for credentials interactively",
    ),
) -> None:
    """
    Setup authentication for E2E API testing.

    Automates RFC-SDLC-602 Phase 1: Setup & Authentication.
    Supports OAuth2, API Key, Basic Auth, and Bearer token.

    Examples:

        sdlcctl e2e auth-setup --type oauth2

        sdlcctl e2e auth-setup --type api_key --output .env.test

        sdlcctl e2e auth-setup --type bearer --non-interactive
    """
    console.print(Panel(
        f"[bold blue]E2E API Authentication Setup[/bold blue]\n"
        f"[dim]Auth Type: {auth_type}[/dim]",
        title="RFC-SDLC-602 Phase 1",
    ))

    credentials = {}

    if auth_type == "oauth2":
        credentials = _setup_oauth2_auth(token_url, interactive)
    elif auth_type == "api_key":
        credentials = _setup_api_key_auth(interactive)
    elif auth_type == "basic":
        credentials = _setup_basic_auth(interactive)
    elif auth_type == "bearer":
        credentials = _setup_bearer_auth(interactive)
    else:
        console.print(f"[red]✗ Unknown auth type: {auth_type}[/red]")
        console.print("[dim]Supported types: oauth2, api_key, basic, bearer[/dim]")
        raise typer.Exit(code=1)

    if not credentials:
        console.print("[red]✗ No credentials provided[/red]")
        raise typer.Exit(code=1)

    # Save credentials to output file
    output_file = project_path / output_path
    _save_credentials(output_file, credentials, auth_type)

    console.print()
    console.print(f"[green]✓ Credentials saved to {output_file}[/green]")
    console.print("[dim]Remember to add this file to .gitignore![/dim]")


def _setup_oauth2_auth(token_url: Optional[str], interactive: bool) -> dict:
    """Setup OAuth2 authentication."""
    if interactive:
        console.print()
        client_id = Prompt.ask("Client ID")
        client_secret = Prompt.ask("Client Secret", password=True)
        if not token_url:
            token_url = Prompt.ask("Token URL")
        scope = Prompt.ask("Scope (optional)", default="")
    else:
        client_id = os.getenv("E2E_CLIENT_ID", "")
        client_secret = os.getenv("E2E_CLIENT_SECRET", "")
        token_url = token_url or os.getenv("E2E_TOKEN_URL", "")
        scope = os.getenv("E2E_SCOPE", "")

    if not all([client_id, client_secret, token_url]):
        console.print("[red]✗ Missing required OAuth2 credentials[/red]")
        return {}

    # Get access token
    with console.status("[blue]Obtaining access token...[/blue]"):
        try:
            import requests
            response = requests.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": scope,
                },
                timeout=30,
            )
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data.get("access_token", "")

            console.print("[green]✓ Access token obtained[/green]")
            return {
                "E2E_AUTH_TYPE": "oauth2",
                "E2E_ACCESS_TOKEN": access_token,
                "E2E_TOKEN_URL": token_url,
                "E2E_CLIENT_ID": client_id,
                "E2E_EXPIRES_IN": str(token_data.get("expires_in", 3600)),
            }
        except Exception as e:
            console.print(f"[red]✗ Failed to obtain token: {e}[/red]")
            # Still save credentials for manual token refresh
            return {
                "E2E_AUTH_TYPE": "oauth2",
                "E2E_TOKEN_URL": token_url,
                "E2E_CLIENT_ID": client_id,
                "E2E_CLIENT_SECRET": client_secret,
                "E2E_SCOPE": scope,
            }


def _setup_api_key_auth(interactive: bool) -> dict:
    """Setup API Key authentication."""
    if interactive:
        console.print()
        api_key = Prompt.ask("API Key", password=True)
        header_name = Prompt.ask("Header name", default="X-API-Key")
    else:
        api_key = os.getenv("E2E_API_KEY", "")
        header_name = os.getenv("E2E_API_KEY_HEADER", "X-API-Key")

    if not api_key:
        console.print("[red]✗ API Key is required[/red]")
        return {}

    return {
        "E2E_AUTH_TYPE": "api_key",
        "E2E_API_KEY": api_key,
        "E2E_API_KEY_HEADER": header_name,
    }


def _setup_basic_auth(interactive: bool) -> dict:
    """Setup Basic authentication."""
    if interactive:
        console.print()
        username = Prompt.ask("Username")
        password = Prompt.ask("Password", password=True)
    else:
        username = os.getenv("E2E_USERNAME", "")
        password = os.getenv("E2E_PASSWORD", "")

    if not all([username, password]):
        console.print("[red]✗ Username and password are required[/red]")
        return {}

    import base64
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()

    return {
        "E2E_AUTH_TYPE": "basic",
        "E2E_BASIC_CREDENTIALS": credentials,
        "E2E_USERNAME": username,
    }


def _setup_bearer_auth(interactive: bool) -> dict:
    """Setup Bearer token authentication."""
    if interactive:
        console.print()
        token = Prompt.ask("Bearer Token", password=True)
    else:
        token = os.getenv("E2E_BEARER_TOKEN", "")

    if not token:
        console.print("[red]✗ Bearer token is required[/red]")
        return {}

    return {
        "E2E_AUTH_TYPE": "bearer",
        "E2E_BEARER_TOKEN": token,
    }


def _save_credentials(output_file: Path, credentials: dict, auth_type: str) -> None:
    """Save credentials to .env file."""
    lines = [
        f"# E2E API Testing Credentials",
        f"# Generated by: sdlcctl e2e auth-setup --type {auth_type}",
        f"# Date: {datetime.now().isoformat()}",
        f"# RFC-SDLC-602 Phase 1: Setup & Authentication",
        "",
    ]

    for key, value in credentials.items():
        lines.append(f"{key}={value}")

    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _initialize_e2e_folders(project_path: Path) -> dict:
    """Initialize E2E testing folder structure.

    Creates:
    - docs/05-Testing-Quality/03-E2E-Testing/
    - docs/05-Testing-Quality/03-E2E-Testing/tests/
    - docs/05-Testing-Quality/03-E2E-Testing/reports/
    - docs/05-Testing-Quality/03-E2E-Testing/evidence/
    - Template test files (Newman, REST Assured)

    Returns:
        dict with success status, path, and files_created
    """
    try:
        # Define folder structure
        e2e_base = project_path / "docs" / "05-Testing-Quality" / "03-E2E-Testing"
        folders = [
            e2e_base,
            e2e_base / "tests",
            e2e_base / "reports",
            e2e_base / "evidence",
            e2e_base / "collections",
        ]

        files_created = []

        # Create folders
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)

        # Create README
        readme_path = e2e_base / "README.md"
        if not readme_path.exists():
            readme_content = _get_e2e_readme_template()
            readme_path.write_text(readme_content, encoding="utf-8")
            files_created.append(str(readme_path.relative_to(project_path)))

        # Create example Postman collection
        collection_path = e2e_base / "collections" / "example-collection.json"
        if not collection_path.exists():
            collection_content = _get_example_postman_collection()
            collection_path.write_text(collection_content, encoding="utf-8")
            files_created.append(str(collection_path.relative_to(project_path)))

        # Create example pytest test file
        pytest_path = e2e_base / "tests" / "test_api_endpoints.py"
        if not pytest_path.exists():
            pytest_content = _get_example_pytest_template()
            pytest_path.write_text(pytest_content, encoding="utf-8")
            files_created.append(str(pytest_path.relative_to(project_path)))

        # Create .gitkeep files for empty folders
        for folder in [e2e_base / "reports", e2e_base / "evidence"]:
            gitkeep = folder / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()

        return {
            "success": True,
            "path": str(e2e_base),
            "files_created": files_created,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _get_e2e_readme_template() -> str:
    """Get README template for E2E testing folder."""
    return """# E2E API Testing

**Stage**: 05-Testing-Quality
**Framework**: SDLC 6.0.5
**RFC**: RFC-SDLC-602 E2E API Testing Enhancement

---

## Overview

This folder contains E2E API testing artifacts per RFC-SDLC-602.

## Folder Structure

```
03-E2E-Testing/
├── README.md           # This file
├── tests/              # Test files (pytest, REST Assured)
├── collections/        # Postman/Newman collections
├── reports/            # Test execution reports
└── evidence/           # Evidence artifacts for gate transitions
```

## 6-Phase Workflow

1. **Phase 0**: Check Stage 03 Documentation (OpenAPI spec exists)
2. **Phase 1**: Setup & Authentication (`sdlcctl e2e auth-setup`)
3. **Phase 2**: Execute Tests (`sdlcctl e2e run-tests`)
4. **Phase 3**: Generate Report (`sdlcctl e2e generate-report`)
5. **Phase 4**: Update Stage 03 (if needed)
6. **Phase 5**: Validate Cross-References (`sdlcctl e2e cross-reference`)

## Quick Start

```bash
# Validate E2E compliance
sdlcctl e2e validate

# Setup authentication
sdlcctl e2e auth-setup --type oauth2

# Validate cross-references
sdlcctl e2e cross-reference
```

## Cross-Reference

- **Stage 03 API Spec**: `../../../03-Integration-APIs/02-API-Specifications/openapi.json`
- **API Reference**: `../../../03-Integration-APIs/02-API-Specifications/COMPLETE-API-ENDPOINT-REFERENCE.md`

---

*Generated by `sdlcctl e2e validate --init`*
"""


def _get_example_postman_collection() -> str:
    """Get example Postman collection template."""
    return json.dumps({
        "info": {
            "name": "SDLC Orchestrator E2E Tests",
            "description": "E2E API tests for SDLC Orchestrator (RFC-SDLC-602)",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": "Health Check",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{baseUrl}}/health",
                        "host": ["{{baseUrl}}"],
                        "path": ["health"]
                    }
                },
                "response": []
            },
            {
                "name": "List Projects",
                "request": {
                    "method": "GET",
                    "header": [
                        {
                            "key": "Authorization",
                            "value": "Bearer {{accessToken}}"
                        }
                    ],
                    "url": {
                        "raw": "{{baseUrl}}/api/v1/projects",
                        "host": ["{{baseUrl}}"],
                        "path": ["api", "v1", "projects"]
                    }
                },
                "response": []
            }
        ],
        "variable": [
            {
                "key": "baseUrl",
                "value": "http://localhost:8000"
            },
            {
                "key": "accessToken",
                "value": ""
            }
        ]
    }, indent=2)


def _get_example_pytest_template() -> str:
    """Get example pytest test file template."""
    return '''"""E2E API Tests for SDLC Orchestrator.

RFC-SDLC-602: E2E API Testing Enhancement
Framework: SDLC 6.0.5

Usage:
    pytest tests/test_api_endpoints.py -v
    pytest tests/test_api_endpoints.py -v --env staging
"""

import os
import pytest
import requests
from typing import Generator


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def base_url() -> str:
    """Get base URL from environment."""
    return os.getenv("E2E_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def auth_headers() -> dict:
    """Get authentication headers."""
    auth_type = os.getenv("E2E_AUTH_TYPE", "bearer")

    if auth_type == "bearer":
        token = os.getenv("E2E_BEARER_TOKEN", "")
        return {"Authorization": f"Bearer {token}"}
    elif auth_type == "api_key":
        key = os.getenv("E2E_API_KEY", "")
        header = os.getenv("E2E_API_KEY_HEADER", "X-API-Key")
        return {header: key}
    elif auth_type == "basic":
        creds = os.getenv("E2E_BASIC_CREDENTIALS", "")
        return {"Authorization": f"Basic {creds}"}
    else:
        return {}


@pytest.fixture(scope="session")
def session(auth_headers: dict) -> Generator[requests.Session, None, None]:
    """Create authenticated session."""
    s = requests.Session()
    s.headers.update(auth_headers)
    s.headers.update({"Content-Type": "application/json"})
    yield s
    s.close()


# =============================================================================
# Health Check Tests
# =============================================================================


class TestHealthCheck:
    """Health check endpoint tests."""

    def test_health_endpoint_returns_200(self, session: requests.Session, base_url: str):
        """Health check should return 200 OK."""
        response = session.get(f"{base_url}/health")
        assert response.status_code == 200

    def test_health_response_has_status(self, session: requests.Session, base_url: str):
        """Health response should include status field."""
        response = session.get(f"{base_url}/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


# =============================================================================
# API Endpoint Tests (Add your tests here)
# =============================================================================


class TestProjectsAPI:
    """Projects API endpoint tests."""

    def test_list_projects_requires_auth(self, base_url: str):
        """Projects endpoint should require authentication."""
        response = requests.get(f"{base_url}/api/v1/projects")
        assert response.status_code == 401

    def test_list_projects_with_auth(self, session: requests.Session, base_url: str):
        """Authenticated request should succeed."""
        response = session.get(f"{base_url}/api/v1/projects")
        # May return 200 or 403 depending on permissions
        assert response.status_code in [200, 403]


# =============================================================================
# Cross-Reference: Stage 03 API Spec
# =============================================================================
#
# This test file validates endpoints defined in:
#   ../../../03-Integration-APIs/02-API-Specifications/openapi.json
#
# SSOT: openapi.json is maintained in Stage 03 only.
# =============================================================================
'''


def _fix_ssot_violations(duplicates: list, canonical_path: Path) -> dict:
    """Fix SSOT violations by replacing duplicates with symlinks.

    Args:
        duplicates: List of duplicate openapi.json paths
        canonical_path: Path to the canonical (SSOT) openapi.json

    Returns:
        dict with success status, fixed_count, and fixed_files
    """
    try:
        if not canonical_path.exists():
            return {
                "success": False,
                "error": f"Canonical file not found: {canonical_path}",
            }

        fixed_files = []

        for dup_path_str in duplicates:
            dup_path = Path(dup_path_str)

            if not dup_path.exists():
                continue

            # Create backup
            backup_path = dup_path.with_suffix(".json.backup")
            shutil.copy2(dup_path, backup_path)

            # Remove duplicate
            dup_path.unlink()

            # Create relative symlink
            try:
                rel_path = os.path.relpath(canonical_path, dup_path.parent)
                dup_path.symlink_to(rel_path)
                fixed_files.append(f"{dup_path} → {rel_path}")
            except OSError:
                # Symlinks may not work on Windows without admin
                # Restore backup
                shutil.copy2(backup_path, dup_path)
                continue

        return {
            "success": True,
            "fixed_count": len(fixed_files),
            "fixed_files": fixed_files,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _validate_e2e_compliance_opa(
    project_path: Path,
    min_pass_rate: int,
    from_stage: str,
    to_stage: str,
    evidence_path: Optional[Path],
) -> dict:
    """Validate E2E testing compliance using OPA policy evaluation.

    Sprint 140: Uses OPA client instead of local validation logic.
    Falls back to local validation if OPA is unavailable.

    Args:
        project_path: Project root path
        min_pass_rate: Minimum pass rate threshold
        from_stage: Source stage for transition
        to_stage: Target stage for transition
        evidence_path: Optional path to evidence JSON

    Returns:
        Validation result dict
    """
    # Load evidence
    evidence = _load_evidence(project_path, evidence_path)

    # Prepare input for OPA
    input_data = {
        "project_path": str(project_path),
        "min_pass_rate": min_pass_rate,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "evidence": evidence,
    }

    # Call OPA
    opa_client = get_opa_client()
    opa_result = opa_client.evaluate(
        "sdlc.e2e_testing.e2e_testing_compliance",
        input_data,
    )

    # Convert OPA result to expected format
    result = {
        "has_e2e_report": False,
        "has_api_documentation": False,
        "e2e_pass_rate": 0.0,
        "total_endpoints": 0,
        "failed_endpoints": 0,
        "min_pass_rate_threshold": min_pass_rate,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "violations": list(opa_result.violations),
        "warnings": list(opa_result.warnings),
        "allow_transition": opa_result.allow,
        "opa_used": True,
    }

    # Extract details from OPA result if available
    if opa_result.details:
        result["has_e2e_report"] = opa_result.details.get("has_e2e_report", False)
        result["has_api_documentation"] = opa_result.details.get("has_api_documentation", False)
        result["e2e_pass_rate"] = opa_result.details.get("e2e_pass_rate", 0.0)
        result["total_endpoints"] = opa_result.details.get("total_endpoints", 0)
        result["failed_endpoints"] = opa_result.details.get("failed_endpoints", 0)

    return result


def _validate_cross_references_opa(
    stage_03: Path,
    stage_05: Path,
    project_path: Path,
) -> dict:
    """Validate cross-references using OPA policy evaluation.

    Sprint 140 Day 2: Uses OPA client for SSOT and cross-reference validation.
    Falls back to local validation if OPA is unavailable.

    Args:
        stage_03: Path to Stage 03 folder
        stage_05: Path to Stage 05 folder
        project_path: Project root path

    Returns:
        Validation result dict
    """
    # Prepare input for OPA
    input_data = {
        "project_path": str(project_path),
        "stage_03_path": str(stage_03),
        "stage_05_path": str(stage_05),
    }

    # Call OPA
    opa_client = get_opa_client()
    opa_result = opa_client.evaluate(
        "sdlc.e2e_testing.stage_cross_reference",
        input_data,
    )

    # Convert OPA result to expected format
    result = {
        "stage_03_exists": stage_03.exists(),
        "stage_05_exists": stage_05.exists(),
        "has_stage_03_links": False,
        "has_stage_05_links": False,
        "ssot_compliance": True,
        "duplicate_openapi_locations": [],
        "violations": list(opa_result.violations),
        "warnings": list(opa_result.warnings),
        "cross_reference_valid": opa_result.allow,
        "opa_used": True,
    }

    # Extract details from OPA result if available
    if opa_result.details:
        result["has_stage_03_links"] = opa_result.details.get("has_stage_03_links", False)
        result["has_stage_05_links"] = opa_result.details.get("has_stage_05_links", False)
        result["ssot_compliance"] = opa_result.details.get("ssot_compliance", True)
        result["duplicate_openapi_locations"] = opa_result.details.get("duplicate_openapi_locations", [])

    # If OPA fallback was used, run local validation for detailed results
    if opa_result.warnings and any("OPA unavailable" in w for w in opa_result.warnings):
        # Merge with local validation results for complete picture
        local_result = _validate_cross_references(stage_03, stage_05, project_path)
        result["has_stage_03_links"] = local_result.get("has_stage_03_links", False)
        result["has_stage_05_links"] = local_result.get("has_stage_05_links", False)
        result["duplicate_openapi_locations"] = local_result.get("duplicate_openapi_locations", [])

    return result


# =============================================================================
# Sprint 141: OpenAPI Parsing and Test Execution Commands
# =============================================================================


@app.command(name="parse-openapi")
def parse_openapi_command(
    openapi_path: Path = typer.Argument(
        ...,
        help="Path to openapi.json or openapi.yaml file",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for parsed results (JSON)",
    ),
    generate_tests: bool = typer.Option(
        False,
        "--generate-tests",
        "-g",
        help="Generate test scaffolds (Newman collection + pytest)",
    ),
    test_output_dir: Optional[Path] = typer.Option(
        None,
        "--test-output",
        help="Directory for generated test files",
    ),
    output_format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table, json, summary",
    ),
    filter_tag: Optional[str] = typer.Option(
        None,
        "--tag",
        "-t",
        help="Filter endpoints by OpenAPI tag",
    ),
    filter_method: Optional[str] = typer.Option(
        None,
        "--method",
        "-m",
        help="Filter by HTTP method (GET, POST, PUT, DELETE, PATCH)",
    ),
) -> None:
    """
    Parse OpenAPI spec and extract testable endpoints.

    RFC-SDLC-602 Phase 0: Check Documentation - validates OpenAPI spec
    and extracts endpoints for E2E testing.

    Features:
    - Load and validate OpenAPI 3.0/3.1 specifications
    - Extract testable endpoints (GET, POST, PUT, DELETE, PATCH)
    - Group endpoints by resource/tag
    - Generate test scaffold templates (Newman, pytest)
    - Display summary table with method, path, auth info

    Examples:

        sdlcctl e2e parse-openapi docs/03-Integration-APIs/02-API-Specifications/openapi.json

        sdlcctl e2e parse-openapi openapi.yaml --format json --output endpoints.json

        sdlcctl e2e parse-openapi openapi.json --generate-tests --test-output tests/e2e/

        sdlcctl e2e parse-openapi openapi.json --tag users --method GET
    """
    console.print(Panel(
        f"[bold blue]OpenAPI Parser[/bold blue]\n"
        f"[dim]File: {openapi_path}[/dim]",
        title="RFC-SDLC-602 Phase 0",
    ))

    with console.status("[bold blue]Parsing OpenAPI specification...[/bold blue]"):
        parse_result = _parse_openapi_spec(openapi_path)

    if not parse_result["success"]:
        console.print(f"[red]✗ Parse failed: {parse_result['error']}[/red]")
        raise typer.Exit(code=1)

    # Apply filters
    endpoints = parse_result["endpoints"]
    if filter_tag:
        endpoints = [e for e in endpoints if filter_tag.lower() in [t.lower() for t in e.get("tags", [])]]
    if filter_method:
        endpoints = [e for e in endpoints if e["method"].upper() == filter_method.upper()]

    # Render results
    _render_openapi_result(parse_result, endpoints, output_format)

    # Save to output file if specified
    if output:
        output_data = {
            "openapi_version": parse_result["openapi_version"],
            "api_title": parse_result["api_title"],
            "api_version": parse_result["api_version"],
            "total_endpoints": len(endpoints),
            "endpoints": endpoints,
            "tags": parse_result["tags"],
            "servers": parse_result["servers"],
            "security_schemes": parse_result["security_schemes"],
        }
        output.write_text(json.dumps(output_data, indent=2), encoding="utf-8")
        console.print(f"\n[green]✓ Parsed data saved to {output}[/green]")

    # Generate test scaffolds if requested
    if generate_tests:
        if test_output_dir is None:
            test_output_dir = openapi_path.parent.parent.parent / "05-Testing-Quality" / "03-E2E-Testing"

        console.print(f"\n[blue]Generating test scaffolds...[/blue]")
        gen_result = _generate_test_scaffolds(
            endpoints=endpoints,
            output_dir=test_output_dir,
            api_title=parse_result["api_title"],
            servers=parse_result["servers"],
            security_schemes=parse_result["security_schemes"],
        )

        if gen_result["success"]:
            console.print(f"[green]✓ Test scaffolds generated at {test_output_dir}[/green]")
            for file_path in gen_result.get("files_created", []):
                console.print(f"  [dim]• {file_path}[/dim]")
        else:
            console.print(f"[red]✗ Generation failed: {gen_result['error']}[/red]")


@app.command(name="run-tests")
def run_tests_command(
    runner: str = typer.Option(
        "pytest",
        "--runner",
        "-r",
        help="Test runner: pytest, newman, rest-assured",
    ),
    test_path: Optional[Path] = typer.Option(
        None,
        "--tests",
        "-t",
        help="Path to test file or directory",
    ),
    collection: Optional[Path] = typer.Option(
        None,
        "--collection",
        "-c",
        help="Path to Newman/Postman collection (for newman runner)",
    ),
    environment: Optional[Path] = typer.Option(
        None,
        "--environment",
        "-e",
        help="Path to environment file (.env or Postman env)",
    ),
    project_path: Path = typer.Option(
        Path.cwd(),
        "--project-path",
        "-p",
        help="Project root path",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    report_output: Optional[Path] = typer.Option(
        None,
        "--report-output",
        "-o",
        help="Output path for test results (JSON)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed test output",
    ),
    timeout: int = typer.Option(
        300,
        "--timeout",
        help="Test execution timeout in seconds",
    ),
    parallel: bool = typer.Option(
        False,
        "--parallel",
        help="Run tests in parallel (pytest only)",
    ),
) -> None:
    """
    Execute E2E tests using various test runners.

    RFC-SDLC-602 Phase 2: Execute Tests - runs E2E API tests
    and captures results for reporting.

    Supported Runners:
    - pytest: Python test framework (recommended for API tests)
    - newman: Postman/Newman CLI for collection-based testing
    - rest-assured: Java-based REST testing (requires Maven/Gradle)

    Examples:

        sdlcctl e2e run-tests --runner pytest --tests tests/e2e/

        sdlcctl e2e run-tests --runner newman --collection api-tests.json

        sdlcctl e2e run-tests --runner pytest --environment .env.test --verbose

        sdlcctl e2e run-tests --runner newman --collection tests.json -e staging.postman_env.json
    """
    console.print(Panel(
        f"[bold blue]E2E Test Execution[/bold blue]\n"
        f"[dim]Runner: {runner}[/dim]",
        title="RFC-SDLC-602 Phase 2",
    ))

    # Validate runner and required parameters
    runner = runner.lower().strip()
    if runner not in ["pytest", "newman", "rest-assured"]:
        console.print(f"[red]✗ Unknown runner: {runner}[/red]")
        console.print("[dim]Supported runners: pytest, newman, rest-assured[/dim]")
        raise typer.Exit(code=1)

    if runner == "newman" and not collection:
        console.print("[red]✗ Newman runner requires --collection parameter[/red]")
        raise typer.Exit(code=1)

    # Auto-discover test path if not provided
    if test_path is None and runner == "pytest":
        test_path = project_path / "docs" / "05-Testing-Quality" / "03-E2E-Testing" / "tests"
        if not test_path.exists():
            test_path = project_path / "tests" / "e2e"

    # Execute tests
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"[blue]Running {runner} tests...", total=None)

        if runner == "pytest":
            result = _run_pytest_tests(
                test_path=test_path,
                environment=environment,
                verbose=verbose,
                timeout=timeout,
                parallel=parallel,
            )
        elif runner == "newman":
            result = _run_newman_tests(
                collection=collection,
                environment=environment,
                verbose=verbose,
                timeout=timeout,
            )
        else:  # rest-assured
            result = _run_rest_assured_tests(
                test_path=test_path,
                environment=environment,
                verbose=verbose,
                timeout=timeout,
            )

        progress.remove_task(task)

    # Render results
    _render_test_execution_result(result, verbose)

    # Save results if output specified
    if report_output:
        result_data = {
            "runner": runner,
            "executed_at": datetime.now().isoformat(),
            "total_tests": result.get("total_tests", 0),
            "passed": result.get("passed", 0),
            "failed": result.get("failed", 0),
            "skipped": result.get("skipped", 0),
            "duration_seconds": result.get("duration_seconds", 0),
            "pass_rate": result.get("pass_rate", 0),
            "failed_tests": result.get("failed_tests", []),
        }
        report_output.parent.mkdir(parents=True, exist_ok=True)
        report_output.write_text(json.dumps(result_data, indent=2), encoding="utf-8")
        console.print(f"\n[green]✓ Test results saved to {report_output}[/green]")

    # Exit with error code if tests failed
    if result.get("failed", 0) > 0:
        raise typer.Exit(code=1)


def _parse_openapi_spec(openapi_path: Path) -> dict:
    """Parse OpenAPI specification and extract endpoints.

    Args:
        openapi_path: Path to openapi.json or openapi.yaml

    Returns:
        dict with parsed spec data, endpoints, and metadata
    """
    try:
        content = openapi_path.read_text(encoding="utf-8")

        # Determine format and parse
        if openapi_path.suffix in [".yaml", ".yml"]:
            try:
                import yaml
                spec = yaml.safe_load(content)
            except ImportError:
                return {
                    "success": False,
                    "error": "PyYAML not installed. Run: pip install pyyaml",
                }
        else:
            spec = json.loads(content)

        # Validate OpenAPI version
        openapi_version = spec.get("openapi", spec.get("swagger", ""))
        if not openapi_version:
            return {
                "success": False,
                "error": "Not a valid OpenAPI specification (missing 'openapi' or 'swagger' field)",
            }

        # Extract API metadata
        info = spec.get("info", {})
        api_title = info.get("title", "Unknown API")
        api_version = info.get("version", "1.0.0")
        api_description = info.get("description", "")

        # Extract servers
        servers = spec.get("servers", [])
        if not servers and "host" in spec:
            # OpenAPI 2.0 format
            scheme = spec.get("schemes", ["https"])[0]
            host = spec.get("host", "localhost")
            base_path = spec.get("basePath", "/")
            servers = [{"url": f"{scheme}://{host}{base_path}"}]

        # Extract security schemes
        security_schemes = {}
        if "components" in spec and "securitySchemes" in spec["components"]:
            security_schemes = spec["components"]["securitySchemes"]
        elif "securityDefinitions" in spec:
            security_schemes = spec["securityDefinitions"]

        # Extract global security
        global_security = spec.get("security", [])

        # Extract tags
        tags = spec.get("tags", [])
        tag_descriptions = {t.get("name", ""): t.get("description", "") for t in tags}

        # Extract endpoints
        endpoints = []
        paths = spec.get("paths", {})

        for path, path_item in paths.items():
            # Skip path-level parameters
            path_params = path_item.get("parameters", [])

            for method in ["get", "post", "put", "delete", "patch", "head", "options"]:
                if method not in path_item:
                    continue

                operation = path_item[method]

                # Extract operation details
                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "operation_id": operation.get("operationId", f"{method}_{path.replace('/', '_')}"),
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                    "tags": operation.get("tags", ["default"]),
                    "deprecated": operation.get("deprecated", False),
                    "parameters": [],
                    "request_body": None,
                    "responses": {},
                    "security": [],
                }

                # Extract parameters (path + operation level)
                all_params = path_params + operation.get("parameters", [])
                for param in all_params:
                    param_info = {
                        "name": param.get("name", ""),
                        "in": param.get("in", ""),
                        "required": param.get("required", False),
                        "type": _get_param_type(param),
                        "description": param.get("description", ""),
                    }
                    endpoint["parameters"].append(param_info)

                # Extract request body (OpenAPI 3.0)
                if "requestBody" in operation:
                    req_body = operation["requestBody"]
                    content = req_body.get("content", {})
                    body_info = {
                        "required": req_body.get("required", False),
                        "content_types": list(content.keys()),
                        "description": req_body.get("description", ""),
                    }
                    # Get schema for first content type
                    if content:
                        first_content = list(content.values())[0]
                        body_info["schema"] = first_content.get("schema", {})
                    endpoint["request_body"] = body_info

                # Extract responses
                for status_code, response in operation.get("responses", {}).items():
                    endpoint["responses"][status_code] = {
                        "description": response.get("description", ""),
                        "content_types": list(response.get("content", {}).keys()) if "content" in response else [],
                    }

                # Extract security requirements
                op_security = operation.get("security", global_security)
                for sec_req in op_security:
                    for sec_name, scopes in sec_req.items():
                        endpoint["security"].append({
                            "name": sec_name,
                            "scopes": scopes,
                            "type": security_schemes.get(sec_name, {}).get("type", "unknown"),
                        })

                endpoints.append(endpoint)

        # Group by tags for summary
        endpoints_by_tag = {}
        for ep in endpoints:
            for tag in ep["tags"]:
                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []
                endpoints_by_tag[tag].append(ep)

        return {
            "success": True,
            "openapi_version": openapi_version,
            "api_title": api_title,
            "api_version": api_version,
            "api_description": api_description,
            "servers": servers,
            "security_schemes": security_schemes,
            "tags": tag_descriptions,
            "endpoints": endpoints,
            "endpoints_by_tag": endpoints_by_tag,
            "total_endpoints": len(endpoints),
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _get_param_type(param: dict) -> str:
    """Extract parameter type from OpenAPI parameter definition."""
    if "schema" in param:
        schema = param["schema"]
        return schema.get("type", schema.get("$ref", "object"))
    return param.get("type", "string")


def _render_openapi_result(parse_result: dict, endpoints: list, output_format: str) -> None:
    """Render OpenAPI parse results."""
    fmt = output_format.lower().strip()

    if fmt == "json":
        output_data = {
            "openapi_version": parse_result["openapi_version"],
            "api_title": parse_result["api_title"],
            "total_endpoints": len(endpoints),
            "endpoints": endpoints,
        }
        console.print(json.dumps(output_data, indent=2))
        return

    if fmt == "summary":
        console.print(
            f"API: {parse_result['api_title']} v{parse_result['api_version']} | "
            f"OpenAPI: {parse_result['openapi_version']} | "
            f"Endpoints: {len(endpoints)}"
        )
        return

    # Default: table format
    console.print()
    console.print(f"[bold]API:[/bold] {parse_result['api_title']} v{parse_result['api_version']}")
    console.print(f"[bold]OpenAPI Version:[/bold] {parse_result['openapi_version']}")
    console.print(f"[bold]Total Endpoints:[/bold] {len(endpoints)}")

    if parse_result["servers"]:
        console.print(f"[bold]Servers:[/bold] {', '.join(s.get('url', '') for s in parse_result['servers'])}")

    console.print()

    # Create endpoint table
    table = Table(show_header=True, header_style="bold", expand=True)
    table.add_column("Method", width=8, justify="center")
    table.add_column("Path", width=40)
    table.add_column("Tags", width=15)
    table.add_column("Auth", width=12)
    table.add_column("Summary", width=30)

    # Method colors
    method_colors = {
        "GET": "green",
        "POST": "blue",
        "PUT": "yellow",
        "PATCH": "cyan",
        "DELETE": "red",
        "HEAD": "magenta",
        "OPTIONS": "white",
    }

    for ep in endpoints:
        method = ep["method"]
        color = method_colors.get(method, "white")

        # Auth info
        auth_info = ""
        if ep["security"]:
            auth_types = list(set(s["type"] for s in ep["security"]))
            auth_info = ", ".join(auth_types[:2])
            if not auth_info:
                auth_info = "🔒 Yes"
        else:
            auth_info = "-"

        # Tags
        tags_str = ", ".join(ep["tags"][:2])
        if len(ep["tags"]) > 2:
            tags_str += "..."

        # Deprecation indicator
        summary = ep["summary"][:28] + "..." if len(ep["summary"]) > 30 else ep["summary"]
        if ep["deprecated"]:
            summary = f"[dim strikethrough]{summary}[/dim strikethrough]"

        table.add_row(
            f"[{color}]{method}[/{color}]",
            ep["path"],
            tags_str,
            auth_info,
            summary,
        )

    console.print(table)

    # Summary by tag
    if parse_result.get("endpoints_by_tag"):
        console.print()
        console.print("[bold]Endpoints by Tag:[/bold]")
        for tag, eps in parse_result["endpoints_by_tag"].items():
            console.print(f"  • {tag}: {len(eps)} endpoints")


def _generate_test_scaffolds(
    endpoints: list,
    output_dir: Path,
    api_title: str,
    servers: list,
    security_schemes: dict,
) -> dict:
    """Generate test scaffold files (Newman collection + pytest).

    Args:
        endpoints: List of parsed endpoints
        output_dir: Output directory for test files
        api_title: API title for naming
        servers: Server URLs from OpenAPI spec
        security_schemes: Security schemes from OpenAPI spec

    Returns:
        dict with success status and files created
    """
    try:
        files_created = []

        # Ensure output directories exist
        collections_dir = output_dir / "collections"
        tests_dir = output_dir / "tests"
        collections_dir.mkdir(parents=True, exist_ok=True)
        tests_dir.mkdir(parents=True, exist_ok=True)

        # Generate Newman collection
        collection_path = collections_dir / f"{_slugify(api_title)}-e2e-collection.json"
        collection = _generate_newman_collection(endpoints, api_title, servers, security_schemes)
        collection_path.write_text(json.dumps(collection, indent=2), encoding="utf-8")
        files_created.append(str(collection_path))

        # Generate pytest file
        pytest_path = tests_dir / f"test_{_slugify(api_title)}_api.py"
        pytest_content = _generate_pytest_file(endpoints, api_title, servers, security_schemes)
        pytest_path.write_text(pytest_content, encoding="utf-8")
        files_created.append(str(pytest_path))

        # Generate environment template
        env_path = output_dir / ".env.e2e.template"
        env_content = _generate_env_template(servers, security_schemes)
        env_path.write_text(env_content, encoding="utf-8")
        files_created.append(str(env_path))

        return {
            "success": True,
            "files_created": files_created,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _slugify(text: str) -> str:
    """Convert text to slug format."""
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')


def _generate_newman_collection(
    endpoints: list,
    api_title: str,
    servers: list,
    security_schemes: dict,
) -> dict:
    """Generate Postman/Newman collection from endpoints."""
    base_url = servers[0].get("url", "http://localhost:8000") if servers else "http://localhost:8000"

    # Group endpoints by tag for folders
    endpoints_by_tag = {}
    for ep in endpoints:
        for tag in ep["tags"]:
            if tag not in endpoints_by_tag:
                endpoints_by_tag[tag] = []
            endpoints_by_tag[tag].append(ep)

    # Build collection items
    items = []
    for tag, tag_endpoints in endpoints_by_tag.items():
        folder_items = []
        for ep in tag_endpoints:
            # Build request
            request = {
                "method": ep["method"],
                "header": [
                    {"key": "Content-Type", "value": "application/json"},
                    {"key": "Authorization", "value": "Bearer {{accessToken}}"},
                ],
                "url": {
                    "raw": f"{{{{baseUrl}}}}{ep['path']}",
                    "host": ["{{baseUrl}}"],
                    "path": [p for p in ep["path"].split("/") if p],
                },
            }

            # Add query parameters
            query_params = [p for p in ep["parameters"] if p["in"] == "query"]
            if query_params:
                request["url"]["query"] = [
                    {"key": p["name"], "value": "", "description": p["description"]}
                    for p in query_params
                ]

            # Add request body for POST/PUT/PATCH
            if ep["request_body"] and ep["method"] in ["POST", "PUT", "PATCH"]:
                request["body"] = {
                    "mode": "raw",
                    "raw": "{}",
                    "options": {"raw": {"language": "json"}},
                }

            # Build test script
            test_script = f"""
pm.test("Status code is 2xx", function () {{
    pm.response.to.have.status(200);
}});

pm.test("Response time is less than 500ms", function () {{
    pm.expect(pm.response.responseTime).to.be.below(500);
}});

pm.test("Response has valid JSON", function () {{
    pm.response.to.be.json;
}});
"""

            folder_items.append({
                "name": ep["summary"] or ep["operation_id"],
                "request": request,
                "response": [],
                "event": [
                    {
                        "listen": "test",
                        "script": {
                            "type": "text/javascript",
                            "exec": test_script.strip().split("\n"),
                        },
                    }
                ],
            })

        items.append({
            "name": tag,
            "item": folder_items,
        })

    return {
        "info": {
            "name": f"{api_title} E2E Tests",
            "description": f"Auto-generated E2E tests from OpenAPI spec (sdlcctl e2e parse-openapi)",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": items,
        "variable": [
            {"key": "baseUrl", "value": base_url},
            {"key": "accessToken", "value": ""},
        ],
    }


def _generate_pytest_file(
    endpoints: list,
    api_title: str,
    servers: list,
    security_schemes: dict,
) -> str:
    """Generate pytest test file from endpoints."""
    base_url = servers[0].get("url", "http://localhost:8000") if servers else "http://localhost:8000"

    # Group by tag for test classes
    endpoints_by_tag = {}
    for ep in endpoints:
        tag = ep["tags"][0] if ep["tags"] else "default"
        if tag not in endpoints_by_tag:
            endpoints_by_tag[tag] = []
        endpoints_by_tag[tag].append(ep)

    # Build test file content
    content = f'''"""Auto-generated E2E API Tests for {api_title}.

Generated by: sdlcctl e2e parse-openapi
RFC-SDLC-602: E2E API Testing Enhancement
Framework: SDLC 6.0.5

Usage:
    pytest {_slugify(api_title)}_api.py -v
    pytest {_slugify(api_title)}_api.py -v --env staging
"""

import os
import pytest
import requests
from typing import Generator


# =============================================================================
# Configuration
# =============================================================================

BASE_URL = os.getenv("E2E_BASE_URL", "{base_url}")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def base_url() -> str:
    """Get base URL from environment."""
    return BASE_URL


@pytest.fixture(scope="session")
def auth_headers() -> dict:
    """Get authentication headers."""
    auth_type = os.getenv("E2E_AUTH_TYPE", "bearer")

    if auth_type == "bearer":
        token = os.getenv("E2E_BEARER_TOKEN", "")
        return {{"Authorization": f"Bearer {{token}}"}}
    elif auth_type == "api_key":
        key = os.getenv("E2E_API_KEY", "")
        header = os.getenv("E2E_API_KEY_HEADER", "X-API-Key")
        return {{header: key}}
    elif auth_type == "basic":
        creds = os.getenv("E2E_BASIC_CREDENTIALS", "")
        return {{"Authorization": f"Basic {{creds}}"}}
    else:
        return {{}}


@pytest.fixture(scope="session")
def session(auth_headers: dict) -> Generator[requests.Session, None, None]:
    """Create authenticated session."""
    s = requests.Session()
    s.headers.update(auth_headers)
    s.headers.update({{"Content-Type": "application/json"}})
    yield s
    s.close()


'''

    # Generate test classes for each tag
    for tag, tag_endpoints in endpoints_by_tag.items():
        class_name = ''.join(word.capitalize() for word in tag.replace('-', '_').split('_'))
        content += f'''
# =============================================================================
# {tag.title()} Tests
# =============================================================================


class Test{class_name}API:
    """{tag.title()} API endpoint tests."""

'''
        for ep in tag_endpoints:
            method = ep["method"].lower()
            path = ep["path"]
            test_name = _slugify(ep["operation_id"] or f"{method}_{path}")

            # Handle path parameters
            path_params = [p for p in ep["parameters"] if p["in"] == "path"]
            if path_params:
                for param in path_params:
                    path = path.replace(f"{{{param['name']}}}", f"{{test_{param['name']}}}")

            # Generate test method
            content += f'''    def test_{test_name}(self, session: requests.Session, base_url: str):
        """{ep['summary'] or f'{method.upper()} {path}'}"""
        response = session.{method}(f"{{base_url}}{path}")
        assert response.status_code in [200, 201, 204, 401, 403]
        if response.status_code in [200, 201]:
            assert response.headers.get("Content-Type", "").startswith("application/json")

'''

    # Add cross-reference footer
    content += '''
# =============================================================================
# Cross-Reference: Stage 03 API Spec
# =============================================================================
#
# This test file validates endpoints defined in the OpenAPI specification.
# Generated by: sdlcctl e2e parse-openapi
#
# SSOT: openapi.json is maintained in Stage 03 only.
# =============================================================================
'''

    return content


def _generate_env_template(servers: list, security_schemes: dict) -> str:
    """Generate environment template file."""
    base_url = servers[0].get("url", "http://localhost:8000") if servers else "http://localhost:8000"

    content = f"""# E2E Testing Environment Configuration
# Generated by: sdlcctl e2e parse-openapi
# Copy to .env.e2e and fill in values

# Base URL
E2E_BASE_URL={base_url}

# Authentication Type (bearer, api_key, basic, oauth2)
E2E_AUTH_TYPE=bearer

# Bearer Token Auth
E2E_BEARER_TOKEN=your_token_here

# API Key Auth
# E2E_API_KEY=your_api_key
# E2E_API_KEY_HEADER=X-API-Key

# Basic Auth
# E2E_USERNAME=user
# E2E_PASSWORD=password

# OAuth2 Auth
# E2E_CLIENT_ID=client_id
# E2E_CLIENT_SECRET=client_secret
# E2E_TOKEN_URL=https://auth.example.com/oauth/token
# E2E_SCOPE=read write

"""
    return content


def _run_pytest_tests(
    test_path: Path,
    environment: Optional[Path],
    verbose: bool,
    timeout: int,
    parallel: bool,
) -> dict:
    """Execute pytest tests and return results.

    Args:
        test_path: Path to test file or directory
        environment: Path to .env file
        verbose: Show verbose output
        timeout: Timeout in seconds
        parallel: Run tests in parallel

    Returns:
        dict with test results
    """
    import time

    start_time = time.time()

    try:
        # Build pytest command
        cmd = ["python", "-m", "pytest", str(test_path), "--tb=short", "-q"]

        if verbose:
            cmd.append("-v")

        if parallel:
            cmd.extend(["-n", "auto"])  # pytest-xdist

        # Add JSON report output
        json_report = test_path.parent / ".pytest_results.json" if test_path.is_dir() else test_path.with_suffix(".results.json")
        cmd.extend(["--json-report", f"--json-report-file={json_report}"])

        # Load environment if provided
        env = os.environ.copy()
        if environment and environment.exists():
            env_content = environment.read_text(encoding="utf-8")
            for line in env_content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env[key.strip()] = value.strip()

        # Run pytest
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=str(test_path.parent) if test_path.is_file() else str(test_path),
        )

        duration = time.time() - start_time

        # Parse results
        if json_report.exists():
            report_data = json.loads(json_report.read_text(encoding="utf-8"))
            summary = report_data.get("summary", {})

            return {
                "success": result.returncode == 0,
                "total_tests": summary.get("total", 0),
                "passed": summary.get("passed", 0),
                "failed": summary.get("failed", 0),
                "skipped": summary.get("skipped", 0),
                "duration_seconds": duration,
                "pass_rate": (summary.get("passed", 0) / max(summary.get("total", 1), 1)) * 100,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "failed_tests": [
                    {
                        "name": t.get("nodeid", ""),
                        "error": t.get("call", {}).get("longrepr", ""),
                    }
                    for t in report_data.get("tests", [])
                    if t.get("outcome") == "failed"
                ],
            }
        else:
            # Parse from stdout if JSON report not available
            lines = result.stdout.split("\n")
            for line in lines:
                if "passed" in line or "failed" in line:
                    # Parse pytest summary line like "5 passed, 2 failed in 1.23s"
                    passed = failed = skipped = 0
                    if "passed" in line:
                        match = re.search(r"(\d+) passed", line)
                        if match:
                            passed = int(match.group(1))
                    if "failed" in line:
                        match = re.search(r"(\d+) failed", line)
                        if match:
                            failed = int(match.group(1))
                    if "skipped" in line:
                        match = re.search(r"(\d+) skipped", line)
                        if match:
                            skipped = int(match.group(1))

                    total = passed + failed + skipped
                    return {
                        "success": result.returncode == 0,
                        "total_tests": total,
                        "passed": passed,
                        "failed": failed,
                        "skipped": skipped,
                        "duration_seconds": duration,
                        "pass_rate": (passed / max(total, 1)) * 100,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "failed_tests": [],
                    }

            return {
                "success": result.returncode == 0,
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration_seconds": duration,
                "pass_rate": 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "failed_tests": [],
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Test execution timed out after {timeout} seconds",
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration_seconds": timeout,
            "pass_rate": 0,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "pytest not found. Install with: pip install pytest pytest-json-report",
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration_seconds": 0,
            "pass_rate": 0,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration_seconds": time.time() - start_time,
            "pass_rate": 0,
        }


def _run_newman_tests(
    collection: Path,
    environment: Optional[Path],
    verbose: bool,
    timeout: int,
) -> dict:
    """Execute Newman tests and return results.

    Args:
        collection: Path to Postman/Newman collection
        environment: Path to Postman environment file
        verbose: Show verbose output
        timeout: Timeout in seconds

    Returns:
        dict with test results
    """
    import time

    start_time = time.time()

    try:
        # Build newman command
        cmd = ["newman", "run", str(collection)]

        if environment:
            cmd.extend(["-e", str(environment)])

        # JSON reporter for parsing results
        json_report = collection.with_suffix(".newman.json")
        cmd.extend(["-r", "json", "--reporter-json-export", str(json_report)])

        if not verbose:
            cmd.append("--silent")

        # Run newman
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        duration = time.time() - start_time

        # Parse results
        if json_report.exists():
            report_data = json.loads(json_report.read_text(encoding="utf-8"))
            run_data = report_data.get("run", {})
            stats = run_data.get("stats", {})

            assertions = stats.get("assertions", {})
            total = assertions.get("total", 0)
            failed = assertions.get("failed", 0)
            passed = total - failed

            return {
                "success": result.returncode == 0,
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "skipped": 0,
                "duration_seconds": duration,
                "pass_rate": (passed / max(total, 1)) * 100,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "failed_tests": [
                    {
                        "name": f.get("source", {}).get("name", "Unknown"),
                        "error": f.get("error", {}).get("message", ""),
                    }
                    for f in run_data.get("failures", [])
                ],
            }
        else:
            return {
                "success": result.returncode == 0,
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration_seconds": duration,
                "pass_rate": 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "failed_tests": [],
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Newman execution timed out after {timeout} seconds",
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration_seconds": timeout,
            "pass_rate": 0,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "newman not found. Install with: npm install -g newman",
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration_seconds": 0,
            "pass_rate": 0,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration_seconds": time.time() - start_time,
            "pass_rate": 0,
        }


def _run_rest_assured_tests(
    test_path: Path,
    environment: Optional[Path],
    verbose: bool,
    timeout: int,
) -> dict:
    """Execute REST Assured tests (placeholder for Java-based testing).

    Args:
        test_path: Path to test directory (Maven/Gradle project)
        environment: Path to properties file
        verbose: Show verbose output
        timeout: Timeout in seconds

    Returns:
        dict with test results
    """
    # REST Assured requires Maven or Gradle project structure
    # This is a placeholder - full implementation would detect build tool and run
    return {
        "success": False,
        "error": "REST Assured runner not yet implemented. Use pytest or newman instead.",
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "duration_seconds": 0,
        "pass_rate": 0,
    }


def _render_test_execution_result(result: dict, verbose: bool) -> None:
    """Render test execution results."""
    if "error" in result and not result.get("success"):
        console.print(f"\n[red]✗ Error: {result['error']}[/red]")
        return

    console.print()

    # Status panel
    status_color = "green" if result.get("success") else "red"
    status_text = "PASS" if result.get("success") else "FAIL"
    pass_rate = result.get("pass_rate", 0)

    console.print(Panel(
        f"[bold {status_color}]{status_text}[/bold {status_color}] | "
        f"Pass Rate: {pass_rate:.1f}%",
        title="Test Results",
    ))

    # Summary table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Metric", width=20)
    table.add_column("Value", justify="right", width=15)

    table.add_row("Total Tests", str(result.get("total_tests", 0)))
    table.add_row("[green]Passed[/green]", f"[green]{result.get('passed', 0)}[/green]")
    table.add_row("[red]Failed[/red]", f"[red]{result.get('failed', 0)}[/red]")
    table.add_row("[yellow]Skipped[/yellow]", f"[yellow]{result.get('skipped', 0)}[/yellow]")
    table.add_row("Duration", f"{result.get('duration_seconds', 0):.2f}s")

    console.print(table)

    # Show failed tests if any
    failed_tests = result.get("failed_tests", [])
    if failed_tests:
        console.print()
        console.print("[bold red]Failed Tests:[/bold red]")
        for test in failed_tests[:10]:  # Limit to first 10
            console.print(f"  • {test.get('name', 'Unknown')}")
            if verbose and test.get("error"):
                console.print(f"    [dim]{test['error'][:200]}...[/dim]")

    # Show stdout/stderr in verbose mode
    if verbose:
        if result.get("stdout"):
            console.print()
            console.print("[dim]--- stdout ---[/dim]")
            console.print(result["stdout"][:2000])
        if result.get("stderr"):
            console.print()
            console.print("[dim]--- stderr ---[/dim]")
            console.print(result["stderr"][:1000])
