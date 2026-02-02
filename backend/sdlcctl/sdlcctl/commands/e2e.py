"""sdlcctl e2e commands.

Sprint 137 implementation: RFC-SDLC-602 E2E API Testing Enhancement.

Commands:
  - validate-e2e: Validate E2E testing compliance for stage transitions
  - validate-cross-reference: Validate Stage 03 ↔ Stage 05 cross-references
  - generate-report: Generate E2E API test report from results

Reference:
  - RFC-SDLC-602-E2E-API-TESTING
  - SDLC Framework 6.0.2
  - OPA Policy: e2e_testing_compliance.rego
  - OPA Policy: stage_cross_reference.rego
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

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
    """
    with console.status("[bold blue]Validating E2E testing compliance...[/bold blue]"):
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
    """
    # Auto-discover stage folders if not provided
    if stage_03 is None:
        stage_03 = project_path / "docs" / "03-Integration-APIs"
    if stage_05 is None:
        stage_05 = project_path / "docs" / "05-Testing-Quality"

    with console.status("[bold blue]Validating cross-references...[/bold blue]"):
        result = _validate_cross_references(
            stage_03=stage_03,
            stage_05=stage_05,
            project_path=project_path,
        )

    _render_cross_reference_result(result, output_format)

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
**Framework**: SDLC 6.0.2
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
  "framework_version": "6.0.2",
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
