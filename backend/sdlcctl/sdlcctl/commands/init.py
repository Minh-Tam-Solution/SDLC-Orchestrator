"""
SDLC 6.0.0 Init Command.

Initialize a new SDLC 6.0.0 project structure.

Sprint 129 Day 5 - Added GitHub Integration
Reference: ADR-044-GitHub-Integration-Strategy.md

Sprint 147: Added telemetry tracking for project initialization events.
"""

import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

from ..lib.telemetry import track_command, track_project_init
from ..services.github_service import (
    GitHubService,
    GitHubRepoFormatError,
    GitHubAppNotInstalledError,
    GitHubCloneError,
    get_github_app_install_url,
)
from ..validation.tier import STAGE_NAMES, Tier, TierDetector

console = Console()


def init_command(
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Project root path to initialize",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    docs_root: str = typer.Option(
        "docs",
        "--docs",
        "-d",
        help="Documentation folder name",
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
        help="Team size (used to auto-detect tier)",
    ),
    github: Optional[str] = typer.Option(
        None,
        "--github",
        "-g",
        help="GitHub repository to connect (format: owner/repo or full URL)",
    ),
    clone: bool = typer.Option(
        True,
        "--clone/--no-clone",
        help="Clone the GitHub repository if not exists locally",
    ),
    scaffold: bool = typer.Option(
        True,
        "--scaffold",
        help="Create full folder structure with READMEs",
    ),
    no_scaffold: bool = typer.Option(
        False,
        "--no-scaffold",
        help="Do not create READMEs and templates",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing docs folder",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive",
        "-i",
        help="Interactive mode with prompts",
    ),
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Do not prompt; use defaults where needed",
    ),
) -> None:
    """
    Initialize SDLC 6.0.0 project structure.

    Creates the complete documentation folder structure with stage folders,
    README templates, and P0 artifacts based on the selected tier.

    GitHub Integration (Sprint 129):
    Connect a GitHub repository during initialization. The CLI will check
    for SDLC Orchestrator GitHub App installation and optionally clone
    the repository.

    Examples:

        sdlcctl init --tier professional

        sdlcctl init --team-size 25

        sdlcctl init --github owner/repo --tier standard

        sdlcctl init --github https://github.com/owner/repo --no-clone

        sdlcctl init --no-interactive --tier standard
    """
    console.print()
    console.print(
        Panel(
            "[bold]SDLC 6.0.0 Project Initialization[/bold]\n\n"
            "This wizard will set up your documentation structure\n"
            "following SDLC 6.0.0 best practices.",
            title="[bold blue]sdlcctl init[/bold blue]",
            border_style="blue",
        )
    )

    # Resolve boolean flag precedence (Click 8.3.x is incompatible with
    # Typer's '--foo/--no-foo' style declarations).
    if no_interactive:
        interactive = False
    if no_scaffold:
        scaffold = False

    # GitHub integration - Sprint 129
    github_repo = None
    if github:
        github_repo = _handle_github_integration(
            github_input=github,
            target_path=path,
            clone_repo=clone,
            interactive=interactive,
        )

    # Check if docs folder already exists
    docs_path = path / docs_root
    if docs_path.exists() and not force:
        if interactive:
            if not Confirm.ask(
                f"[yellow]Warning:[/yellow] {docs_path} already exists. Overwrite?"
            ):
                console.print("[dim]Initialization cancelled.[/dim]")
                raise typer.Exit(code=0)
        else:
            console.print(
                f"[red]Error:[/red] {docs_path} already exists. "
                f"Use --force to overwrite."
            )
            raise typer.Exit(code=1)

    # Determine tier
    project_tier: Tier
    if tier:
        try:
            project_tier = Tier(tier.lower())
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid tier '{tier}'")
            raise typer.Exit(code=1)
    elif team_size:
        detector = TierDetector()
        project_tier = detector.detect_from_team_size(team_size)
        console.print(
            f"[cyan]Auto-detected tier:[/cyan] {project_tier.value.upper()} "
            f"(team size: {team_size})"
        )
    elif interactive:
        project_tier = _prompt_for_tier()
    else:
        project_tier = Tier.PROFESSIONAL
        console.print(
            f"[cyan]Using default tier:[/cyan] {project_tier.value.upper()}"
        )

    # Get tier requirements
    detector = TierDetector()
    requirements = detector.get_requirements(project_tier)

    # Show what will be created
    console.print()
    console.print(f"[bold]Tier:[/bold] {project_tier.value.upper()}")
    console.print(f"[bold]Required Stages:[/bold] {len(requirements.required_stages)}")
    console.print(f"[bold]P0 Artifacts Required:[/bold] {'Yes' if requirements.p0_required else 'No'}")

    if interactive:
        console.print()
        if not Confirm.ask("Proceed with initialization?"):
            console.print("[dim]Initialization cancelled.[/dim]")
            raise typer.Exit(code=0)

    # Create structure
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating SDLC structure...", total=None)

        # Create docs folder
        docs_path.mkdir(parents=True, exist_ok=True)

        # Create main README
        main_readme = docs_path / "README.md"
        main_readme.write_text(
            _generate_main_readme(path.name, project_tier, requirements),
            encoding="utf-8",
        )
        progress.update(task, description="Created main README")

        # Create stage folders
        for stage_id in requirements.required_stages:
            stage_name = STAGE_NAMES.get(stage_id, f"{stage_id}-Unknown")
            stage_path = docs_path / stage_name

            if scaffold:
                _create_stage_folder(stage_path, stage_id, stage_name)
            else:
                stage_path.mkdir(parents=True, exist_ok=True)

            progress.update(task, description=f"Created {stage_name}")

        # Create optional stages (as placeholders)
        if scaffold:
            optional_stages = [
                s for s in STAGE_NAMES.keys()
                if s not in requirements.required_stages
            ]
            for stage_id in optional_stages:
                stage_name = STAGE_NAMES.get(stage_id)
                if stage_name:
                    stage_path = docs_path / stage_name
                    if not stage_path.exists():
                        stage_path.mkdir(parents=True, exist_ok=True)
                        readme = stage_path / "README.md"
                        readme.write_text(
                            f"# {stage_name}\n\n"
                            f"**Status**: OPTIONAL for {project_tier.value.upper()} tier\n\n"
                            f"This stage is not required for your current tier.\n",
                            encoding="utf-8",
                        )
                    progress.update(task, description=f"Created {stage_name} (optional)")

        # Create centralized 10-archive with stage-aligned Legacy subdirs (RFC-001, SDLC 6.0.5)
        if scaffold:
            _create_archive_structure(docs_path, requirements.required_stages)
            progress.update(task, description="Created 10-archive structure")

    # Success message
    console.print()
    console.print("[bold green]✓ SDLC 6.0.0 structure initialized successfully![/bold green]")
    console.print()
    console.print(f"[dim]Project root:[/dim] {path}")
    console.print(f"[dim]Docs folder:[/dim] {docs_path}")
    if github_repo:
        console.print(f"[dim]GitHub repo:[/dim] {github_repo.full_name}")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Review and customize the generated READMEs")
    console.print("  2. Fill in P0 artifacts for your tier")
    console.print("  3. Run 'sdlcctl validate' to check compliance")
    if github_repo:
        console.print("  4. Push changes to GitHub to sync with SDLC Orchestrator")
    console.print()

    # Track project initialization telemetry (Sprint 147 - Product Truth Layer)
    # Generate a project ID from path name for tracking purposes
    project_id = f"cli-{path.name}"
    track_project_init(
        project_id=project_id,
        tier=project_tier.value.upper(),
        template="sdlcctl-init",
    )
    track_command(
        command="init",
        success=True,
        exit_code=0,
    )


def _prompt_for_tier() -> Tier:
    """Interactive prompt for tier selection."""
    console.print()
    console.print("[bold]Select your project tier:[/bold]")
    console.print()
    console.print("  [cyan]1)[/cyan] LITE        - 1-2 people, 4 stages")
    console.print("  [cyan]2)[/cyan] STANDARD    - 3-10 people, 6 stages")
    console.print("  [cyan]3)[/cyan] PROFESSIONAL- 10-50 people, 10 stages, P0 required")
    console.print("  [cyan]4)[/cyan] ENTERPRISE  - 50+ people, 11 stages, full compliance")
    console.print()

    choice = Prompt.ask(
        "Enter choice",
        choices=["1", "2", "3", "4"],
        default="3",
    )

    tier_map = {
        "1": Tier.LITE,
        "2": Tier.STANDARD,
        "3": Tier.PROFESSIONAL,
        "4": Tier.ENTERPRISE,
    }

    return tier_map[choice]


def _handle_github_integration(
    github_input: str,
    target_path: Path,
    clone_repo: bool,
    interactive: bool,
) -> Optional["ParsedRepository"]:
    """
    Handle GitHub repository integration.

    Sprint 129 Day 5 - CLI GitHub Integration

    Args:
        github_input: Repository identifier (owner/repo or URL).
        target_path: Target path for project.
        clone_repo: Whether to clone the repository.
        interactive: Whether to prompt for user input.

    Returns:
        ParsedRepository if successful, None otherwise.
    """
    from ..services.github_service import ParsedRepository

    github_service = GitHubService()

    # Step 1: Parse and validate repository format
    console.print()
    console.print("[bold]GitHub Integration[/bold]")
    console.print()

    try:
        repo = github_service.parse_repository(github_input)
        console.print(f"[green]✓[/green] Repository: {repo.full_name}")
    except GitHubRepoFormatError as e:
        console.print(f"[red]✗ Error:[/red] {e.message}")
        if interactive:
            console.print()
            console.print("[dim]Continuing without GitHub integration...[/dim]")
            return None
        raise typer.Exit(code=1)

    # Step 2: Check GitHub App installation
    console.print("[dim]Checking GitHub App installation...[/dim]")

    app_installed = github_service.check_app_installed(repo.owner, repo.repo)

    if not app_installed:
        install_url = get_github_app_install_url()
        console.print()
        console.print(
            "[yellow]⚠ Warning:[/yellow] SDLC Orchestrator GitHub App is not installed "
            f"on {repo.full_name}"
        )
        console.print()
        console.print(f"[bold]Install the app at:[/bold] {install_url}")
        console.print()

        if interactive:
            if not Confirm.ask(
                "Continue without GitHub App? (Some features will be unavailable)"
            ):
                console.print("[dim]Initialization cancelled.[/dim]")
                raise typer.Exit(code=0)
        else:
            console.print("[dim]Continuing without GitHub App integration...[/dim]")
    else:
        console.print("[green]✓[/green] GitHub App installed")

    # Step 3: Clone repository if requested
    if clone_repo:
        console.print()
        console.print("[dim]Checking repository...[/dim]")

        # Check if directory already exists with content
        repo_dir = target_path / repo.repo
        if repo_dir.exists() and any(repo_dir.iterdir()):
            console.print(f"[dim]Directory {repo_dir} already exists[/dim]")

            # Check if it's the same repo
            if github_service._is_same_remote(repo_dir, repo):
                console.print(f"[green]✓[/green] Repository already cloned at {repo_dir}")
            else:
                console.print(
                    f"[yellow]⚠ Warning:[/yellow] Directory exists but is not {repo.full_name}"
                )
                if interactive:
                    if not Confirm.ask("Continue without cloning?"):
                        console.print("[dim]Initialization cancelled.[/dim]")
                        raise typer.Exit(code=0)
        else:
            # Clone the repository
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    progress.add_task(f"Cloning {repo.full_name}...", total=None)
                    clone_path = github_service.clone_repository(
                        repo, target_path, shallow=True
                    )
                console.print(f"[green]✓[/green] Cloned to {clone_path}")
            except GitHubCloneError as e:
                console.print(f"[red]✗ Clone failed:[/red] {e.reason}")
                if interactive:
                    if not Confirm.ask("Continue without cloning?"):
                        console.print("[dim]Initialization cancelled.[/dim]")
                        raise typer.Exit(code=0)
                else:
                    console.print("[dim]Continuing without cloning...[/dim]")

    console.print()
    return repo


def _create_stage_folder(stage_path: Path, stage_id: str, stage_name: str) -> None:
    """Create a stage folder with full scaffolding."""
    stage_path.mkdir(parents=True, exist_ok=True)

    # Create README
    readme_path = stage_path / "README.md"
    readme_path.write_text(
        _generate_stage_readme(stage_id, stage_name),
        encoding="utf-8",
    )

    # Create standard subfolders based on stage
    subfolders = _get_stage_subfolders(stage_id)
    for subfolder in subfolders:
        subfolder_path = stage_path / subfolder
        subfolder_path.mkdir(exist_ok=True)
        # Create placeholder README
        subfolder_readme = subfolder_path / "README.md"
        if not subfolder_readme.exists():
            subfolder_readme.write_text(
                f"# {subfolder}\n\n[Add content here]\n",
                encoding="utf-8",
            )

    # Note: Legacy archive is centralized in 10-archive/{NN}-Legacy/ per RFC-001 (SDLC 6.0.5)
    # Created by _create_archive_structure() after all stages are initialized


def _create_archive_structure(docs_path: Path, stage_ids: list) -> None:
    """Create centralized 10-archive with stage-aligned Legacy subdirs (RFC-001, SDLC 6.0.5)."""
    archive_path = docs_path / "10-archive"
    archive_path.mkdir(exist_ok=True)

    # Create archive README with AI-NEVER-READ directive
    archive_readme = archive_path / "README.md"
    archive_readme.write_text(
        "# 10-Archive: Centralized Legacy Archive\n\n"
        "```yaml\n"
        "directive: AI-NEVER-READ\n"
        "reason: Contains outdated, superseded, or historical content\n"
        "exception: User explicitly requests historical information\n"
        "```\n\n"
        "**Standard**: RFC-001 Legacy Document Organization (SDLC 6.0.5 MANDATORY)\n\n"
        "All legacy content is organized by stage: `{NN}-Legacy/` where `{NN}` is the stage number.\n"
        "Move deprecated documents to the appropriate `{NN}-Legacy/` folder instead of deleting them.\n",
        encoding="utf-8",
    )

    # Create {NN}-Legacy subdirs for each stage
    for stage_id in stage_ids:
        legacy_dir = archive_path / f"{stage_id}-Legacy"
        legacy_dir.mkdir(exist_ok=True)


def _get_stage_subfolders(stage_id: str) -> list:
    """Get recommended subfolders for a stage."""
    subfolders = {
        "00": ["01-Vision", "02-Business-Case", "03-Design-Thinking", "04-Roadmap"],
        "01": ["01-Requirements", "02-User-Stories", "03-Analysis"],
        "02": ["01-System-Architecture", "02-Data-Model", "03-API-Design", "04-ADRs"],
        "03": ["01-Coding-Standards", "02-Sprint-Plans", "03-Setup-Guides", "04-Phase-Plans"],
        "04": ["01-Test-Plans", "02-Test-Cases", "03-Test-Reports"],
        "05": ["01-Release-Plans", "02-Deployment-Guides", "03-Runbooks"],
        "06": ["01-Monitoring", "02-Alerting", "03-Incident-Response"],
        "07": ["01-API-Documentation", "02-Integration-Guides", "03-External-Systems"],
        "08": ["01-Team-Structure", "02-RACI", "03-Communication"],
        "09": ["01-Executive-Reports", "02-Metrics", "03-Compliance"],
        "10": ["01-Archive", "02-Lessons-Learned", "03-Historical"],
    }
    return subfolders.get(stage_id, [])


def _generate_main_readme(project_name: str, tier: Tier, requirements) -> str:
    """Generate main docs README."""
    stage_list = "\n".join(
        f"- [{STAGE_NAMES[s]}](./{STAGE_NAMES[s]}/)"
        for s in requirements.required_stages
    )

    return f"""# {project_name} Documentation

**Framework**: SDLC 6.0.0
**Tier**: {tier.value.upper()}
**Status**: ACTIVE

---

## Overview

This documentation follows the SDLC 6.0.0 Complete Lifecycle methodology
with {len(requirements.required_stages)} stages.

---

## Documentation Structure

### Required Stages

{stage_list}

---

## Quick Navigation

| Stage | Purpose | Status |
|-------|---------|--------|
| 00 - Project Foundation | WHY - Vision & Business Case | Active |
| 01 - Planning & Analysis | WHAT - Requirements | Active |
| 02 - Design & Architecture | HOW - Technical Design | Active |
| 03 - Development | BUILD - Implementation | Active |

---

## AI Assistant Guidance

AI assistants should:
1. Start with this README for navigation
2. Read stage README.md files for context
3. **NEVER** read `10-archive/` folders

---

**Generated by**: sdlcctl init
**Framework**: SDLC 6.0.0
**Tier**: {tier.value.upper()}

"""


def _generate_stage_readme(stage_id: str, stage_name: str) -> str:
    """Generate README content for a stage folder."""
    display_name = stage_name.split("-", 1)[1].replace("-", " ") if "-" in stage_name else stage_name

    descriptions = {
        "00": "Define **WHY** this project exists. Vision, problem statement, and business case.",
        "01": "Define **WHAT** needs to be built. Requirements, user stories, and acceptance criteria.",
        "02": "Define **HOW** it will be built. Architecture, design, and technical specifications.",
        "03": "**BUILD** the solution. Sprint plans, coding standards, and implementation guides.",
        "04": "**TEST** the implementation. Test plans, test cases, and quality assurance.",
        "05": "**DEPLOY** to production. Release plans, deployment guides, and rollback procedures.",
        "06": "**OPERATE** the system. Monitoring, alerting, and incident response.",
        "07": "**INTEGRATE** with other systems. API documentation, integration guides.",
        "08": "**COLLABORATE** effectively. Team structure, RACI, communication protocols.",
        "09": "**GOVERN** the project. Executive reports, metrics, and compliance.",
        "10": "**ARCHIVE** completed work. Historical records and lessons learned.",
    }

    description = descriptions.get(stage_id, "[Describe the purpose of this stage]")

    return f"""# Stage {stage_id}: {display_name}

**Version**: 5.0.0
**Stage**: {stage_id} - {display_name}
**Status**: ACTIVE
**Framework**: SDLC 6.0.0 Complete Lifecycle

---

## Purpose

{description}

---

## Folder Structure

```
{stage_name}/
├── README.md                         # This file (P0 entry point)
├── 01-[Subfolder]/                   # [Description]
├── 02-[Subfolder]/                   # [Description]
```

Legacy content archived in `docs/10-archive/{stage_id}-Legacy/` per RFC-001 (SDLC 6.0.5).

---

## Key Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [Document-Name.md](./Document-Name.md) | [Purpose] | Draft |

---

## AI Assistant Guidance

**DO Read**:
- This README for context
- Key documents listed above

**DO NOT Read**:
- `10-archive/` folder - Contains archived, outdated content

---

**Document Status**: P0 Entry Point
**Compliance**: SDLC 6.0.0 Stage {stage_id}
**Last Updated**: [Date]
**Owner**: [Role]

"""
