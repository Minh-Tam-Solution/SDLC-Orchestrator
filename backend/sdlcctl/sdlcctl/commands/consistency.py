"""sdlcctl validate-consistency command.

SDLC 6.0.5 - SPEC-0021 Stage Consistency Validation.
Sprint 136 - Validate Consistency Command Implementation.

Validates cross-stage consistency between:
- Stage 01 (Planning) ↔ Stage 02 (Design)
- Stage 02 (Design) ↔ Stage 03 (Integrate)
- Stage 03 (Integrate) ↔ Stage 04 (Build)
- Stage 01 (Planning) ↔ Stage 04 (Build)

Usage:
    sdlcctl validate-consistency \\
        --stage-01 docs/01-planning/ \\
        --stage-02 docs/02-design/ \\
        --stage-03 docs/03-integrate/ \\
        --stage-04 backend/app/ \\
        --tier PROFESSIONAL \\
        --format json \\
        --output consistency-report.json
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..validation.consistency import (
    ConsistencyEngine,
    ConsistencyReportFormatter,
)
from ..validation.tier import Tier
from ..validation.violation import Severity

console = Console()


def validate_consistency_command(
    stage_01: Path = typer.Option(
        ...,
        "--stage-01",
        "-s1",
        help="Path to Stage 01 (Planning) folder",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    stage_02: Path = typer.Option(
        ...,
        "--stage-02",
        "-s2",
        help="Path to Stage 02 (Design) folder",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    stage_03: Path = typer.Option(
        ...,
        "--stage-03",
        "-s3",
        help="Path to Stage 03 (Integrate) folder",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    stage_04: Path = typer.Option(
        ...,
        "--stage-04",
        "-s4",
        help="Path to Stage 04 (Build) folder",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    tier: Optional[str] = typer.Option(
        None,
        "--tier",
        "-t",
        help="Project tier: lite, standard, professional, enterprise (auto-detect if not specified)",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text, json, github, summary",
    ),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to file (default: stdout)",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        "-s",
        help="Exit with error code 1 if any violations found (including warnings)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output with context",
    ),
    check_checksums: Optional[Path] = typer.Option(
        None,
        "--check-checksums",
        help="Verify artifact integrity against checksums file",
    ),
) -> None:
    """
    Validate cross-stage consistency per SPEC-0021.

    Checks consistency between Stage 01 (Planning), Stage 02 (Design),
    Stage 03 (Integrate), and Stage 04 (Build) artifacts.

    Examples:

        sdlcctl validate-consistency \\
            --stage-01 docs/01-planning/ \\
            --stage-02 docs/02-design/ \\
            --stage-03 docs/03-integrate/ \\
            --stage-04 backend/app/

        sdlcctl validate-consistency \\
            --stage-01 docs/01-planning/ \\
            --stage-02 docs/02-design/ \\
            --stage-03 docs/03-integrate/ \\
            --stage-04 backend/app/ \\
            --tier professional \\
            --format json \\
            --output report.json

        sdlcctl validate-consistency \\
            --stage-01 docs/01-planning/ \\
            --stage-02 docs/02-design/ \\
            --stage-03 docs/03-integrate/ \\
            --stage-04 backend/app/ \\
            --format github \\
            --strict
    """
    # Parse tier
    project_tier: Optional[Tier] = None
    if tier:
        try:
            project_tier = Tier.from_string(tier)
        except ValueError:
            console.print(
                f"[red]Error:[/red] Invalid tier '{tier}'. "
                f"Valid options: lite, standard, professional, enterprise"
            )
            raise typer.Exit(code=1)

    # Create engine
    try:
        engine = ConsistencyEngine.from_paths(
            stage_01=stage_01,
            stage_02=stage_02,
            stage_03=stage_03,
            stage_04=stage_04,
            tier=project_tier,
            strict=strict,
            check_checksums=check_checksums is not None,
            checksums_path=check_checksums,
            verbose=verbose,
        )
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    # Run validation
    with console.status("[bold blue]Validating stage consistency...[/bold blue]"):
        try:
            result = engine.validate()
        except Exception as e:
            console.print(f"[red]Error during validation:[/red] {e}")
            raise typer.Exit(code=1)

    # Format output
    formatter = ConsistencyReportFormatter()
    fmt = output_format.lower().strip()

    if fmt == "json":
        output = formatter.format_json(result)
    elif fmt == "github":
        output = formatter.format_github(result)
    elif fmt == "summary":
        output = formatter.format_summary(result)
    else:
        output = formatter.format_text(result, verbose=verbose)

    # Write output
    if output_path:
        output_path.write_text(output, encoding="utf-8")
        console.print(f"[green]Report written to:[/green] {output_path}")
    else:
        print(output)

    # Exit code logic
    has_errors = result.error_count > 0
    has_violations = result.total_violations > 0

    if has_errors:
        raise typer.Exit(code=1)

    if strict and has_violations:
        raise typer.Exit(code=1)
