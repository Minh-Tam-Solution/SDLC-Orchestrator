"""
Evidence Validation Commands

CLI commands for validating implementation evidence files.
Part of SPEC-0016: Implementation Evidence Validation.

Commands:
- sdlcctl evidence validate: Validate all evidence files
- sdlcctl evidence create: Create evidence file template
- sdlcctl evidence check: Check spec-to-code alignment

Sprint 132 - Go-Live Preparation
"""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ..validation.validators.evidence_validator import validate_evidence

console = Console()
app = typer.Typer(
    name="evidence",
    help="Implementation evidence validation",
    no_args_is_help=True,
)


@app.command("validate")
def validate_command(
    project_path: str = typer.Argument(
        ".",
        help="Path to SDLC project root"
    ),
    check_implementation_gaps: bool = typer.Option(
        True,
        "--check-implementation-gaps",
        help="Check for SPECs/ADRs without evidence files"
    ),
    fail_on_error: bool = typer.Option(
        False,
        "--fail-on-error",
        help="Exit with code 1 if errors found"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output validation report to file (JSON)"
    ),
) -> None:
    """
    Validate all implementation evidence files.

    Checks:
    - JSON schema compliance
    - File existence (backend, frontend, extension, CLI)
    - Test coverage (mandatory for backend)
    - Missing evidence files

    Example:
        sdlcctl evidence validate
        sdlcctl evidence validate --fail-on-error
        sdlcctl evidence validate --output gaps.json
    """
    project_root = Path(project_path).resolve()

    if not project_root.exists():
        console.print(f"[red]✗[/red] Project path not found: {project_path}")
        raise typer.Exit(code=1)

    console.print(f"\n[bold blue]SDLC Evidence Validator[/bold blue]")
    console.print(f"[dim]Project: {project_root}[/dim]\n")

    # Run validation
    with console.status("[bold green]Validating evidence files..."):
        violations, summary = validate_evidence(project_root)

    # Display summary
    _display_summary(summary, violations)

    # Display violations table
    if violations:
        _display_violations(violations)
    else:
        console.print("\n[green]✓[/green] All evidence files valid!")

    # Write output file if requested
    if output:
        _write_output(violations, summary, output)

    # Exit with error code if requested
    if fail_on_error and summary["errors"] > 0:
        console.print(f"\n[red]✗[/red] Validation failed with {summary['errors']} errors")
        raise typer.Exit(code=1)


@app.command("create")
def create_command(
    spec_id: str = typer.Argument(
        ...,
        help="Spec ID (e.g., SPEC-0013, ADR-043)"
    ),
    spec_title: str = typer.Option(
        ...,
        "--title",
        "-t",
        prompt="Spec title",
        help="Human-readable specification title"
    ),
    spec_type: str = typer.Option(
        "feature",
        "--type",
        help="Spec type (feature, architecture, api, security, performance)"
    ),
    sprint: Optional[str] = typer.Option(
        None,
        "--sprint",
        "-s",
        help="Sprint when implemented (e.g., Sprint 128)"
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory (default: same as spec file)"
    ),
) -> None:
    """
    Create evidence file template for a SPEC or ADR.

    Example:
        sdlcctl evidence create SPEC-0013 --title "Compliance Validation Service"
        sdlcctl evidence create ADR-043 --title "Team Invitation System" --sprint "Sprint 128"
    """
    # Validate spec_id format
    if not (spec_id.startswith("SPEC-") or spec_id.startswith("ADR-")):
        console.print("[red]✗[/red] Invalid spec ID format. Must start with SPEC- or ADR-")
        raise typer.Exit(code=1)

    # Determine output path
    if spec_id.startswith("SPEC-"):
        default_dir = Path("docs/02-design/14-Technical-Specs")
    else:  # ADR-
        default_dir = Path("docs/02-design/01-ADRs")

    if output_dir:
        evidence_path = Path(output_dir) / f"{spec_id}-evidence.json"
    else:
        evidence_path = default_dir / f"{spec_id}-evidence.json"

    # Check if file already exists
    if evidence_path.exists():
        console.print(f"[yellow]⚠[/yellow] Evidence file already exists: {evidence_path}")
        overwrite = typer.confirm("Overwrite existing file?")
        if not overwrite:
            console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit(code=0)

    # Create template
    from datetime import datetime
    today = datetime.utcnow().strftime("%Y-%m-%d")

    template = {
        "spec_id": spec_id,
        "spec_title": spec_title,
        "spec_type": spec_type,
        "implementation_date": today,
        "sprint": sprint or f"Sprint XXX",
        "interfaces": {
            "backend": {
                "api_routes": [],
                "services": [],
                "models": [],
                "schemas": [],
                "tests": [],
                "migrations": []
            },
            "frontend": {
                "components": [],
                "pages": [],
                "hooks": [],
                "api_client": [],
                "tests": []
            },
            "extension": {
                "commands": [],
                "services": [],
                "views": [],
                "package_json": [],
                "tests": []
            },
            "cli": {
                "commands": [],
                "services": [],
                "tests": []
            }
        },
        "documentation": {
            "user_guide": [],
            "api_docs": [],
            "runbooks": []
        },
        "validation": {
            "last_checked": f"{today}T00:00:00Z",
            "checker_version": "1.0.0",
            "status": "missing",
            "missing_files": [],
            "warnings": ["Template created - populate with actual implementation files"]
        },
        "notes": "TODO: Fill in actual implementation file paths"
    }

    # Ensure directory exists
    evidence_path.parent.mkdir(parents=True, exist_ok=True)

    # Write template
    with open(evidence_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
        f.write('\n')

    console.print(f"\n[green]✓[/green] Evidence template created: {evidence_path}")
    console.print("\n[dim]Next steps:")
    console.print("  1. Fill in actual implementation file paths")
    console.print("  2. Run: sdlcctl evidence validate")
    console.print("  3. Fix any missing files or gaps[/dim]")


@app.command("check")
def check_command(
    project_path: str = typer.Argument(
        ".",
        help="Path to SDLC project root"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output gap analysis report (Markdown)"
    ),
) -> None:
    """
    Check spec-to-code alignment and generate gap report.

    This command:
    - Finds all SPECs and ADRs
    - Checks for missing evidence files
    - Validates implementation completeness
    - Generates gap analysis report

    Example:
        sdlcctl evidence check
        sdlcctl evidence check --output gaps.md
    """
    project_root = Path(project_path).resolve()

    if not project_root.exists():
        console.print(f"[red]✗[/red] Project path not found: {project_path}")
        raise typer.Exit(code=1)

    console.print(f"\n[bold blue]SDLC Alignment Checker[/bold blue]")
    console.print(f"[dim]Project: {project_root}[/dim]\n")

    # Run validation
    with console.status("[bold green]Checking spec-to-code alignment..."):
        violations, summary = validate_evidence(project_root)

    # Generate gap analysis
    gaps = _analyze_gaps(violations, project_root)

    # Display gaps
    _display_gaps(gaps)

    # Write markdown report if requested
    if output:
        _write_markdown_report(gaps, output, project_root)
        console.print(f"\n[green]✓[/green] Gap analysis written to: {output}")


def _display_summary(summary: dict, violations: list) -> None:
    """Display validation summary."""
    table = Table(title="Validation Summary", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Total Violations", str(summary["total_violations"]))
    table.add_row(
        "Errors",
        f"[red]{summary['errors']}[/red]" if summary["errors"] > 0 else "[green]0[/green]"
    )
    table.add_row(
        "Warnings",
        f"[yellow]{summary['warnings']}[/yellow]" if summary["warnings"] > 0 else "[green]0[/green]"
    )

    console.print(table)


def _display_violations(violations: list) -> None:
    """Display violations table."""
    table = Table(title="Violations", box=box.ROUNDED)
    table.add_column("Severity", style="bold", width=10)
    table.add_column("Rule", width=15)
    table.add_column("File", width=40)
    table.add_column("Message", width=60)

    for v in violations[:50]:  # Limit to first 50 for readability
        severity_style = "red" if v.severity == "error" else "yellow"
        table.add_row(
            f"[{severity_style}]{v.severity.upper()}[/{severity_style}]",
            v.rule_id,
            v.file_path,
            v.message
        )

    if len(violations) > 50:
        table.add_row("[dim]...", "...", f"... and {len(violations) - 50} more", "...")

    console.print("\n")
    console.print(table)


def _write_output(violations: list, summary: dict, output_path: str) -> None:
    """Write validation results to JSON file."""
    output = {
        "summary": summary,
        "violations": [
            {
                "rule_id": v.rule_id,
                "severity": v.severity,
                "message": v.message,
                "file_path": v.file_path,
                "line_number": v.line_number,
                "suggestion": v.suggestion
            }
            for v in violations
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write('\n')

    console.print(f"\n[green]✓[/green] Validation results written to: {output_path}")


def _analyze_gaps(violations: list, project_root: Path) -> dict:
    """Analyze violations to identify implementation gaps."""
    gaps = {
        "missing_evidence": [],
        "backend_gaps": [],
        "frontend_gaps": [],
        "extension_gaps": [],
        "cli_gaps": [],
        "test_gaps": []
    }

    for v in violations:
        if v.rule_id == "EVIDENCE-014":  # Missing evidence file
            gaps["missing_evidence"].append({
                "file": v.file_path,
                "message": v.message
            })
        elif v.rule_id == "EVIDENCE-006":  # Backend file missing
            gaps["backend_gaps"].append({
                "file": v.file_path,
                "message": v.message
            })
        elif v.rule_id == "EVIDENCE-007":  # Frontend file missing
            gaps["frontend_gaps"].append({
                "file": v.file_path,
                "message": v.message
            })
        elif v.rule_id == "EVIDENCE-008":  # Extension file missing
            gaps["extension_gaps"].append({
                "file": v.file_path,
                "message": v.message
            })
        elif v.rule_id == "EVIDENCE-009":  # CLI file missing
            gaps["cli_gaps"].append({
                "file": v.file_path,
                "message": v.message
            })
        elif v.rule_id in ["EVIDENCE-010", "EVIDENCE-011", "EVIDENCE-012", "EVIDENCE-013"]:  # Test coverage
            gaps["test_gaps"].append({
                "file": v.file_path,
                "message": v.message
            })

    return gaps


def _display_gaps(gaps: dict) -> None:
    """Display gap analysis results."""
    console.print("\n[bold]Gap Analysis[/bold]\n")

    total_gaps = sum(len(gaps[k]) for k in gaps)
    if total_gaps == 0:
        console.print("[green]✓[/green] No implementation gaps found!")
        return

    for category, items in gaps.items():
        if items:
            title = category.replace("_", " ").title()
            console.print(f"\n[bold yellow]{title}:[/bold yellow] {len(items)} issues")
            for item in items[:5]:  # Show first 5
                console.print(f"  • {item['message']}")
            if len(items) > 5:
                console.print(f"  [dim]... and {len(items) - 5} more[/dim]")


def _write_markdown_report(gaps: dict, output_path: str, project_root: Path) -> None:
    """Write gap analysis to Markdown file."""
    from datetime import datetime

    lines = [
        "# Implementation Gap Analysis Report",
        "",
        f"**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Project**: {project_root.name}",
        "",
        "## Summary",
        ""
    ]

    total_gaps = sum(len(gaps[k]) for k in gaps)
    lines.append(f"**Total Gaps**: {total_gaps}")
    lines.append("")

    for category, items in gaps.items():
        if items:
            title = category.replace("_", " ").title()
            lines.append(f"### {title} ({len(items)})")
            lines.append("")
            for item in items:
                lines.append(f"- {item['message']}")
                lines.append(f"  - File: `{item['file']}`")
            lines.append("")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


if __name__ == "__main__":
    app()
