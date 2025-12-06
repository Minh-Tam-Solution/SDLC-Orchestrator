"""
SDLC 5.0.0 Validate Command.

Validates project folder structure against SDLC 5.0.0 standards.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..validation.engine import SDLCValidator, ValidationResult, ValidationSeverity
from ..validation.tier import Tier

console = Console()


def validate_command(
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Project root path to validate",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    docs_root: str = typer.Option(
        "docs",
        "--docs",
        "-d",
        help="Documentation folder name (relative to project root)",
    ),
    tier: Optional[str] = typer.Option(
        None,
        "--tier",
        "-t",
        help="Project tier: lite, standard, professional, enterprise",
    ),
    team_size: Optional[int] = typer.Option(
        None,
        "--team-size",
        help="Team size (used to auto-detect tier if --tier not specified)",
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
        help="Exit with error code 1 if any issues found (not just errors)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output including info-level issues",
    ),
) -> None:
    """
    Validate SDLC 5.0.0 folder structure.

    Checks project documentation structure against SDLC 5.0.0 standards
    including stage folders, naming conventions, and P0 artifacts.

    Examples:

        sdlcctl validate

        sdlcctl validate --path ./my-project --tier professional

        sdlcctl validate --format json --output report.json
    """
    # Parse tier if provided
    project_tier: Optional[Tier] = None
    if tier:
        try:
            project_tier = Tier(tier.lower())
        except ValueError:
            console.print(
                f"[red]Error:[/red] Invalid tier '{tier}'. "
                f"Valid options: lite, standard, professional, enterprise"
            )
            raise typer.Exit(code=1)

    # Initialize validator
    try:
        validator = SDLCValidator(
            project_root=path,
            docs_root=docs_root,
            tier=project_tier,
            team_size=team_size,
        )
    except Exception as e:
        console.print(f"[red]Error initializing validator:[/red] {str(e)}")
        raise typer.Exit(code=1)

    # Run validation
    with console.status("[bold blue]Validating SDLC structure...[/bold blue]"):
        result = validator.validate()

    # Output results
    if output_format == "json":
        _output_json(result)
    elif output_format == "summary":
        _output_summary(result)
    else:
        _output_text(result, verbose)

    # Determine exit code
    if result.error_count > 0:
        raise typer.Exit(code=1)
    elif strict and result.warning_count > 0:
        raise typer.Exit(code=1)


def _output_text(result: ValidationResult, verbose: bool) -> None:
    """Output validation result as formatted text."""
    # Header
    status_color = "green" if result.is_compliant else "red"
    status_text = "COMPLIANT" if result.is_compliant else "NON-COMPLIANT"

    console.print()
    console.print(
        Panel(
            f"[bold]SDLC 5.0.0 Validation Report[/bold]\n\n"
            f"Project: {result.project_root}\n"
            f"Tier: {result.tier.value.upper()}\n"
            f"Status: [{status_color}]{status_text}[/{status_color}]\n"
            f"Score: {result.compliance_score}/100",
            title="[bold blue]sdlcctl validate[/bold blue]",
            border_style="blue",
        )
    )

    # Summary table
    summary_table = Table(title="Summary", show_header=True, header_style="bold")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", justify="right")

    summary_table.add_row(
        "Stages Found",
        f"{len(result.scan_result.stages_found)}/{len(result.tier_requirements.required_stages)}",
    )
    summary_table.add_row(
        "Stages Missing", str(len(result.scan_result.stages_missing))
    )
    summary_table.add_row(
        "P0 Artifacts",
        f"{result.p0_result.artifacts_found}/{result.p0_result.artifacts_checked}",
    )
    summary_table.add_row("Files Scanned", str(result.scan_result.total_files))
    summary_table.add_row(
        "Validation Time", f"{result.validation_time_ms:.1f}ms"
    )

    console.print()
    console.print(summary_table)

    # Issues table
    if result.issues:
        issues_to_show = result.issues
        if not verbose:
            issues_to_show = [
                i for i in result.issues if i.severity != ValidationSeverity.INFO
            ]

        if issues_to_show:
            console.print()
            issues_table = Table(
                title="Issues Found", show_header=True, header_style="bold"
            )
            issues_table.add_column("Severity", style="bold", width=10)
            issues_table.add_column("Code", style="cyan", width=10)
            issues_table.add_column("Message")
            issues_table.add_column("Fix", style="dim")

            for issue in issues_to_show:
                severity_style = {
                    ValidationSeverity.ERROR: "red",
                    ValidationSeverity.WARNING: "yellow",
                    ValidationSeverity.INFO: "blue",
                }.get(issue.severity, "white")

                issues_table.add_row(
                    Text(issue.severity.value.upper(), style=severity_style),
                    issue.code,
                    issue.message,
                    issue.fix_suggestion or "",
                )

            console.print(issues_table)

    # Footer
    console.print()
    if result.is_compliant:
        console.print("[bold green]✓ Project is SDLC 5.0.0 compliant![/bold green]")
    else:
        console.print(
            f"[bold red]✗ {result.error_count} error(s) must be fixed for compliance.[/bold red]"
        )
        if result.warning_count > 0:
            console.print(
                f"[yellow]  {result.warning_count} warning(s) should be addressed.[/yellow]"
            )

    console.print()


def _output_json(result: ValidationResult) -> None:
    """Output validation result as JSON."""
    print(json.dumps(result.to_dict(), indent=2))


def _output_summary(result: ValidationResult) -> None:
    """Output a one-line summary."""
    status = "PASS" if result.is_compliant else "FAIL"
    print(
        f"{status} | Score: {result.compliance_score}/100 | "
        f"Errors: {result.error_count} | Warnings: {result.warning_count} | "
        f"Tier: {result.tier.value}"
    )
