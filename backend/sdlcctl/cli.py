"""
SDLC 5.0.0 Structure Validator CLI.

Main entry point for the sdlcctl command-line tool.
"""

import typer
from rich.console import Console

from . import __version__, __framework__
from .commands.validate import validate_command
from .commands.fix import fix_command
from .commands.init import init_command
from .commands.report import report_command

console = Console()

# Create main Typer app
app = typer.Typer(
    name="sdlcctl",
    help="SDLC 5.0.0 Structure Validator CLI",
    add_completion=True,
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Print version information."""
    if value:
        console.print(f"[bold blue]sdlcctl[/bold blue] v{__version__}")
        console.print(f"[dim]Framework: {__framework__}[/dim]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """
    SDLC 5.0.0 Structure Validator CLI.

    Validate, fix, and initialize SDLC 5.0.0 compliant project structures.

    Supports 4-Tier Classification:
    - LITE: 1-2 people, 4 stages
    - STANDARD: 3-10 people, 6 stages
    - PROFESSIONAL: 10-50 people, 10 stages (P0 required)
    - ENTERPRISE: 50+ people, 11 stages (full compliance)
    """
    pass


# Register commands
app.command(name="validate", help="Validate SDLC 5.0.0 folder structure")(
    validate_command
)
app.command(name="fix", help="Automatically fix SDLC structure issues")(
    fix_command
)
app.command(name="init", help="Initialize SDLC 5.0.0 project structure")(
    init_command
)
app.command(name="report", help="Generate SDLC compliance report")(
    report_command
)


@app.command(name="tiers")
def show_tiers() -> None:
    """Show tier classification details."""
    from rich.table import Table

    from .validation.tier import TIER_REQUIREMENTS, Tier

    table = Table(title="SDLC 5.0.0 Tier Classification", show_header=True)
    table.add_column("Tier", style="cyan", width=15)
    table.add_column("Team Size", justify="right", width=12)
    table.add_column("Stages", justify="right", width=10)
    table.add_column("P0 Required", justify="center", width=12)
    table.add_column("Compliance", width=20)

    tier_sizes = {
        Tier.LITE: "1-2",
        Tier.STANDARD: "3-10",
        Tier.PROFESSIONAL: "10-50",
        Tier.ENTERPRISE: "50+",
    }

    for tier, req in TIER_REQUIREMENTS.items():
        compliance = ", ".join(req.compliance_required) if req.compliance_required else "-"
        table.add_row(
            tier.value.upper(),
            tier_sizes[tier],
            str(req.min_stages),
            "✅" if req.p0_required else "❌",
            compliance,
        )

    console.print()
    console.print(table)
    console.print()


@app.command(name="stages")
def show_stages() -> None:
    """Show SDLC 5.0.0 stage definitions."""
    from rich.table import Table

    from .validation.tier import STAGE_NAMES

    table = Table(title="SDLC 5.0.0 Stages", show_header=True)
    table.add_column("ID", style="cyan", width=5)
    table.add_column("Stage Name", width=30)
    table.add_column("Question", width=40)

    questions = {
        "00": "WHY does this project exist?",
        "01": "WHAT needs to be built?",
        "02": "HOW will it be built?",
        "03": "BUILD - How to implement?",
        "04": "TEST - How to verify quality?",
        "05": "DEPLOY - How to release?",
        "06": "OPERATE - How to run in production?",
        "07": "INTEGRATE - How to connect systems?",
        "08": "COLLABORATE - How do teams work together?",
        "09": "GOVERN - How to manage & report?",
        "10": "ARCHIVE - How to preserve history?",
    }

    for stage_id, stage_name in sorted(STAGE_NAMES.items()):
        table.add_row(stage_id, stage_name, questions.get(stage_id, ""))

    console.print()
    console.print(table)
    console.print()


@app.command(name="p0")
def show_p0() -> None:
    """Show P0 artifact requirements."""
    from rich.table import Table

    from .validation.p0 import P0_ARTIFACTS
    from .validation.tier import Tier

    table = Table(title="SDLC 5.0.0 P0 Artifacts", show_header=True)
    table.add_column("Artifact", style="cyan", width=25)
    table.add_column("Stage", width=8)
    table.add_column("Path", width=45)
    table.add_column("LITE", justify="center", width=6)
    table.add_column("STD", justify="center", width=6)
    table.add_column("PRO", justify="center", width=6)
    table.add_column("ENT", justify="center", width=6)

    for artifact in P0_ARTIFACTS:
        table.add_row(
            artifact.name,
            artifact.stage_id,
            artifact.relative_path[:42] + "..." if len(artifact.relative_path) > 45 else artifact.relative_path,
            "✅" if Tier.LITE in artifact.required_tiers else "❌",
            "✅" if Tier.STANDARD in artifact.required_tiers else "❌",
            "✅" if Tier.PROFESSIONAL in artifact.required_tiers else "❌",
            "✅" if Tier.ENTERPRISE in artifact.required_tiers else "❌",
        )

    console.print()
    console.print(table)
    console.print()
    console.print(f"[dim]Total P0 Artifacts: {len(P0_ARTIFACTS)}[/dim]")
    console.print()


def run() -> None:
    """Run the CLI application."""
    app()


if __name__ == "__main__":
    run()
