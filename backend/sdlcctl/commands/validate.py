"""sdlcctl validate command.

Sprint 44+ implementation: validate docs structure using the plugin-based
`SDLCStructureScanner` (15 rules across 5 validators).

Note: The legacy `SDLCValidator` (tier + P0 artifacts) remains available for
`sdlcctl fix` and `sdlcctl report`.
"""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..validation import ConfigLoader, ScanResult, SDLCStructureScanner, Severity
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
        help="(Legacy) Project tier: lite, standard, professional, enterprise",
    ),
    team_size: Optional[int] = typer.Option(
        None,
        "--team-size",
        help="(Legacy) Team size (used to auto-detect tier if --tier not specified)",
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
        help="Write output to a file (default: stdout)",
    ),
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to .sdlc-config.json (default: auto-discover)",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        "-s",
        help="Exit with error code 1 if any violations found",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output (includes context in text output)",
    ),
) -> None:
    """
    Validate SDLC docs folder structure.

    Checks project documentation structure against SDLC 5.0.0 standards
    including stage folders, naming conventions, and P0 artifacts.

    Examples:

        sdlcctl validate

        sdlcctl validate --path ./my-project --tier professional

        sdlcctl validate --format json --output report.json
        sdlcctl validate --format github --strict
    """
    # Parse tier if provided (kept for CLI compatibility; not used by scanner)
    if tier:
        try:
            Tier(tier.lower())
        except ValueError:
            console.print(
                f"[red]Error:[/red] Invalid tier '{tier}'. "
                f"Valid options: lite, standard, professional, enterprise"
            )
            raise typer.Exit(code=1)

    docs_path = (path / docs_root).resolve()

    # Load config (optional override) and initialize scanner
    try:
        config: Optional[dict] = None
        if config_path:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        else:
            # Auto-discover .sdlc-config.json if present (scanner also does this,
            # but we want access to fail_on_* and output defaults consistently).
            loader = ConfigLoader(path)
            config = loader.load(docs_path).to_dict()

        scanner = SDLCStructureScanner(
            docs_root=docs_path,
            config=config,
            project_root=path,
        )
    except Exception as e:
        console.print(f"[red]Error initializing structure scanner:[/red] {e}")
        raise typer.Exit(code=1)

    with console.status("[bold blue]Validating SDLC structure...[/bold blue]"):
        scan_result = scanner.scan()
        scan_result.violations = scanner.filter_violations(scan_result.violations)

    rendered = _render_output(scanner, scan_result, output_format, verbose)

    if output_path:
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)

    # Exit code policy
    fail_on_warning = bool(config and config.get("fail_on_warning"))
    fail_on_error = True if not config else bool(config.get("fail_on_error", True))

    if fail_on_error and scan_result.error_count > 0:
        raise typer.Exit(code=1)
    if strict and (scan_result.error_count > 0 or scan_result.warning_count > 0):
        raise typer.Exit(code=1)
    if (fail_on_warning or strict) and scan_result.warning_count > 0:
        raise typer.Exit(code=1)


def _render_output(
    scanner: SDLCStructureScanner,
    result: ScanResult,
    output_format: str,
    verbose: bool,
) -> str:
    """Render output for the selected format."""
    fmt = output_format.lower().strip()

    if fmt == "json":
        return scanner.format_json(result)
    if fmt == "github":
        return scanner.format_github_actions(result)
    if fmt == "summary":
        status = "PASS" if result.passed else "FAIL"
        return (
            f"{status} | Errors: {result.error_count} | Warnings: {result.warning_count} | "
            f"Info: {result.info_count} | Files: {result.files_scanned} | "
            f"Time: {result.scan_time_ms:.1f}ms"
        )

    # default text
    return scanner.format_text(result, show_context=verbose)
