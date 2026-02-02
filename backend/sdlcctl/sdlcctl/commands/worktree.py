"""
Git Worktree Management Commands

CLI commands for managing git worktrees for parallel AI development.
Part of RFC-SDLC-604: Parallel AI Development Pattern.

Commands:
- sdlcctl worktree add: Create new worktree for parallel development
- sdlcctl worktree list: List all worktrees in repository
- sdlcctl worktree sync: Sync and rebase all worktrees
- sdlcctl worktree remove: Remove worktree and clean up

Sprint 144 Day 1 - Track 2 Implementation (Boris Cherny Integration)
"""

import subprocess
from pathlib import Path
from typing import Optional, List
import json

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()
app = typer.Typer(
    name="worktree",
    help="Git worktree management for parallel AI development",
    no_args_is_help=True,
)


def run_git_command(args: List[str], cwd: Optional[Path] = None) -> tuple[int, str, str]:
    """
    Run a git command and return exit code, stdout, stderr.

    Args:
        args: Git command arguments (e.g., ['worktree', 'list'])
        cwd: Working directory for command execution

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out after 30 seconds"
    except Exception as e:
        return 1, "", str(e)


def is_git_repository(path: Path) -> bool:
    """Check if path is inside a git repository."""
    code, _, _ = run_git_command(['rev-parse', '--git-dir'], cwd=path)
    return code == 0


def get_git_root(path: Path) -> Optional[Path]:
    """Get the root directory of the git repository."""
    code, stdout, _ = run_git_command(
        ['rev-parse', '--show-toplevel'],
        cwd=path
    )
    if code == 0:
        return Path(stdout.strip())
    return None


@app.command("add")
def add_worktree(
    path: str = typer.Argument(
        ...,
        help="Path where worktree will be created (e.g., ../sdlc-auth-backend)"
    ),
    branch: str = typer.Argument(
        ...,
        help="Branch name for the worktree (e.g., feature/auth-backend)"
    ),
    create_branch: bool = typer.Option(
        True,
        "--create-branch/--no-create-branch",
        "-b",
        help="Create new branch (default: True)"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force creation even if worktree directory exists"
    ),
    project_path: str = typer.Option(
        ".",
        "--project",
        "-p",
        help="Path to git repository root"
    ),
) -> None:
    """
    Create a new git worktree for parallel development.

    Creates a new working directory linked to the same repository,
    allowing parallel AI sessions to work on different branches
    simultaneously without conflicts.

    Examples:
        # Create worktree with new branch
        sdlcctl worktree add ../sdlc-auth-backend feature/auth-backend

        # Create worktree from existing branch
        sdlcctl worktree add ../sdlc-auth-tests feature/auth-tests --no-create-branch

        # Force creation (overwrite existing directory)
        sdlcctl worktree add ../sdlc-auth-api feature/auth-api --force

    RFC-SDLC-604: Enables 2.5x productivity boost via parallel AI sessions.
    """
    project_root = Path(project_path).resolve()

    # Validation: Check if project_path is a git repository
    if not project_root.exists():
        console.print(f"[red]✗[/red] Project path not found: {project_path}")
        raise typer.Exit(code=1)

    if not is_git_repository(project_root):
        console.print(f"[red]✗[/red] Not a git repository: {project_path}")
        console.print("[dim]Hint: Run 'git init' or navigate to a git repository[/dim]")
        raise typer.Exit(code=1)

    git_root = get_git_root(project_root)
    if not git_root:
        console.print(f"[red]✗[/red] Could not determine git root for: {project_path}")
        raise typer.Exit(code=1)

    # Resolve worktree path (relative to git root)
    worktree_path = Path(path)
    if not worktree_path.is_absolute():
        worktree_path = (git_root / path).resolve()

    # Check if worktree path already exists
    if worktree_path.exists() and not force:
        console.print(f"[red]✗[/red] Worktree path already exists: {worktree_path}")
        console.print("[dim]Hint: Use --force to overwrite or choose a different path[/dim]")
        raise typer.Exit(code=1)

    console.print(f"\n[bold blue]Creating Git Worktree[/bold blue]")
    console.print(f"[dim]Repository: {git_root}[/dim]")
    console.print(f"[dim]Worktree path: {worktree_path}[/dim]")
    console.print(f"[dim]Branch: {branch}[/dim]\n")

    # Build git worktree add command
    git_args = ['worktree', 'add']

    if create_branch:
        git_args.extend(['-b', branch])

    if force:
        git_args.append('--force')

    git_args.append(str(worktree_path))

    if not create_branch:
        git_args.append(branch)

    # Execute git worktree add
    code, stdout, stderr = run_git_command(git_args, cwd=git_root)

    if code != 0:
        console.print(f"[red]✗[/red] Failed to create worktree")
        console.print(f"[dim]Error: {stderr}[/dim]")
        raise typer.Exit(code=1)

    # Success output
    console.print(f"[green]✓[/green] Worktree created successfully")
    console.print(f"[dim]{stdout}[/dim]")

    # Display next steps
    console.print("\n[bold]Next Steps:[/bold]")
    console.print(f"  1. cd {worktree_path}")
    console.print(f"  2. cursor .  [dim]# Launch AI coding tool (Claude Code, Cursor, etc.)[/dim]")
    console.print(f"  3. Start parallel development on branch: {branch}")

    console.print("\n[dim]💡 Tip: Launch multiple AI sessions in different worktrees for 2.5x speedup![/dim]")


@app.command("list")
def list_worktrees(
    project_path: str = typer.Option(
        ".",
        "--project",
        "-p",
        help="Path to git repository root"
    ),
    porcelain: bool = typer.Option(
        False,
        "--porcelain",
        help="Output in machine-readable format (JSON)"
    ),
    show_details: bool = typer.Option(
        True,
        "--details/--no-details",
        help="Show detailed information (branch, commit, locked status)"
    ),
) -> None:
    """
    List all git worktrees in the repository.

    Shows all working directories associated with the repository,
    including the main worktree and any additional worktrees created
    for parallel development.

    Examples:
        # List all worktrees
        sdlcctl worktree list

        # List worktrees in specific project
        sdlcctl worktree list --project /path/to/repo

        # Machine-readable output (JSON)
        sdlcctl worktree list --porcelain

        # Simple output (paths only)
        sdlcctl worktree list --no-details

    RFC-SDLC-604: Monitor parallel AI development sessions.
    """
    project_root = Path(project_path).resolve()

    # Validation: Check if project_path is a git repository
    if not project_root.exists():
        console.print(f"[red]✗[/red] Project path not found: {project_path}")
        raise typer.Exit(code=1)

    if not is_git_repository(project_root):
        console.print(f"[red]✗[/red] Not a git repository: {project_path}")
        console.print("[dim]Hint: Run 'git init' or navigate to a git repository[/dim]")
        raise typer.Exit(code=1)

    git_root = get_git_root(project_root)
    if not git_root:
        console.print(f"[red]✗[/red] Could not determine git root for: {project_path}")
        raise typer.Exit(code=1)

    # Get worktree list in porcelain format for parsing
    code, stdout, stderr = run_git_command(
        ['worktree', 'list', '--porcelain'],
        cwd=git_root
    )

    if code != 0:
        console.print(f"[red]✗[/red] Failed to list worktrees")
        console.print(f"[dim]Error: {stderr}[/dim]")
        raise typer.Exit(code=1)

    # Parse worktree list output
    worktrees = []
    current_worktree = {}

    for line in stdout.strip().split('\n'):
        if not line:
            if current_worktree:
                worktrees.append(current_worktree)
                current_worktree = {}
            continue

        if line.startswith('worktree '):
            current_worktree['path'] = line.split(' ', 1)[1]
        elif line.startswith('HEAD '):
            current_worktree['commit'] = line.split(' ', 1)[1]
        elif line.startswith('branch '):
            current_worktree['branch'] = line.split(' ', 1)[1]
        elif line.startswith('detached'):
            current_worktree['detached'] = True
        elif line.startswith('locked'):
            current_worktree['locked'] = line.split(' ', 1)[1] if ' ' in line else True
        elif line.startswith('prunable'):
            current_worktree['prunable'] = line.split(' ', 1)[1] if ' ' in line else True

    if current_worktree:
        worktrees.append(current_worktree)

    if not worktrees:
        console.print("[yellow]⚠[/yellow] No worktrees found")
        raise typer.Exit(code=0)

    # Output format
    if porcelain:
        # JSON output for machine parsing
        print(json.dumps(worktrees, indent=2))
    elif show_details:
        # Rich table output
        console.print(f"\n[bold blue]Git Worktrees[/bold blue]")
        console.print(f"[dim]Repository: {git_root}[/dim]\n")

        table = Table(
            title=f"{len(worktrees)} Worktree(s)",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )

        table.add_column("Path", style="white")
        table.add_column("Branch", style="green")
        table.add_column("Commit", style="dim", max_width=12)
        table.add_column("Status", style="yellow")

        for wt in worktrees:
            path = wt.get('path', '')
            branch = wt.get('branch', 'N/A')
            commit = wt.get('commit', 'N/A')[:8]  # Short commit hash

            # Status indicators
            status_parts = []
            if wt.get('detached'):
                status_parts.append("detached")
            if wt.get('locked'):
                status_parts.append("locked")
            if wt.get('prunable'):
                status_parts.append("prunable")

            status = ", ".join(status_parts) if status_parts else "active"

            # Highlight main worktree
            if branch.endswith('/main') or branch.endswith('/master') or path == str(git_root):
                path = f"[bold]{path}[/bold] (main)"

            table.add_row(path, branch, commit, status)

        console.print(table)

        # Display summary and tips
        console.print(f"\n[dim]💡 Tip: Use 'sdlcctl worktree add' to create new worktrees for parallel AI sessions[/dim]")

    else:
        # Simple output (paths only)
        for wt in worktrees:
            print(wt.get('path', ''))


@app.command("sync")
def sync_worktrees(
    project_path: str = typer.Option(
        ".",
        "--project",
        "-p",
        help="Path to git repository root"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes"
    ),
) -> None:
    """
    Sync all worktrees by rebasing on latest main/master.

    Rebases each worktree branch on the latest main/master branch
    to keep worktrees up to date. This prevents merge conflicts
    when merging parallel development branches.

    Examples:
        # Sync all worktrees
        sdlcctl worktree sync

        # Preview sync without making changes
        sdlcctl worktree sync --dry-run

    RFC-SDLC-604: Maintain consistency across parallel AI sessions.
    """
    project_root = Path(project_path).resolve()

    if not project_root.exists():
        console.print(f"[red]✗[/red] Project path not found: {project_path}")
        raise typer.Exit(code=1)

    if not is_git_repository(project_root):
        console.print(f"[red]✗[/red] Not a git repository: {project_path}")
        raise typer.Exit(code=1)

    git_root = get_git_root(project_root)
    if not git_root:
        console.print(f"[red]✗[/red] Could not determine git root")
        raise typer.Exit(code=1)

    # Get list of worktrees
    code, stdout, stderr = run_git_command(
        ['worktree', 'list', '--porcelain'],
        cwd=git_root
    )

    if code != 0:
        console.print(f"[red]✗[/red] Failed to list worktrees")
        console.print(f"[dim]Error: {stderr}[/dim]")
        raise typer.Exit(code=1)

    # Parse worktrees
    worktrees = []
    current_worktree = {}

    for line in stdout.strip().split('\n'):
        if not line:
            if current_worktree:
                worktrees.append(current_worktree)
                current_worktree = {}
            continue

        if line.startswith('worktree '):
            current_worktree['path'] = line.split(' ', 1)[1]
        elif line.startswith('branch '):
            current_worktree['branch'] = line.split(' ', 1)[1]

    if current_worktree:
        worktrees.append(current_worktree)

    # Find main/master branch
    main_branch = None
    for wt in worktrees:
        branch = wt.get('branch', '')
        if branch.endswith('/main') or branch.endswith('/master'):
            main_branch = branch.split('/')[-1]
            break

    if not main_branch:
        console.print("[yellow]⚠[/yellow] Could not determine main branch (main/master)")
        main_branch = 'main'  # Default to main

    console.print(f"\n[bold blue]Syncing Worktrees[/bold blue]")
    console.print(f"[dim]Base branch: {main_branch}[/dim]")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    # Sync each worktree (skip main/master)
    synced_count = 0
    skipped_count = 0

    for wt in worktrees:
        path = wt.get('path')
        branch = wt.get('branch', '').split('/')[-1]

        if branch == main_branch:
            console.print(f"[dim]Skipping main worktree: {path}[/dim]")
            skipped_count += 1
            continue

        if not branch:
            console.print(f"[dim]Skipping worktree (no branch): {path}[/dim]")
            skipped_count += 1
            continue

        console.print(f"[cyan]→[/cyan] Syncing {branch}...")

        if not dry_run:
            # Fetch latest changes
            fetch_code, _, fetch_err = run_git_command(
                ['fetch', 'origin', main_branch],
                cwd=Path(path)
            )

            if fetch_code != 0:
                console.print(f"[red]✗[/red] Fetch failed: {fetch_err}")
                continue

            # Rebase on main/master
            rebase_code, rebase_out, rebase_err = run_git_command(
                ['rebase', f'origin/{main_branch}'],
                cwd=Path(path)
            )

            if rebase_code != 0:
                console.print(f"[red]✗[/red] Rebase failed: {rebase_err}")
                console.print(f"[dim]Hint: Resolve conflicts manually in {path}[/dim]")
                continue

            console.print(f"[green]✓[/green] Synced successfully")
            synced_count += 1
        else:
            console.print(f"[dim]Would sync: git fetch origin {main_branch} && git rebase origin/{main_branch}[/dim]")
            synced_count += 1

    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Synced: {synced_count}")
    console.print(f"  Skipped: {skipped_count}")

    if not dry_run and synced_count > 0:
        console.print("\n[dim]💡 Tip: All worktrees now rebased on latest {main_branch}[/dim]")


@app.command("remove")
def remove_worktree(
    path: str = typer.Argument(
        ...,
        help="Path to worktree to remove"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force removal even if worktree contains uncommitted changes"
    ),
    project_path: str = typer.Option(
        ".",
        "--project",
        "-p",
        help="Path to git repository root"
    ),
) -> None:
    """
    Remove a git worktree.

    Removes the worktree and cleans up the working directory.
    By default, refuses to remove worktrees with uncommitted changes
    unless --force is used.

    Examples:
        # Remove worktree
        sdlcctl worktree remove ../sdlc-auth-backend

        # Force removal (discard uncommitted changes)
        sdlcctl worktree remove ../sdlc-auth-tests --force

    RFC-SDLC-604: Clean up after parallel development complete.
    """
    project_root = Path(project_path).resolve()

    if not project_root.exists():
        console.print(f"[red]✗[/red] Project path not found: {project_path}")
        raise typer.Exit(code=1)

    if not is_git_repository(project_root):
        console.print(f"[red]✗[/red] Not a git repository: {project_path}")
        raise typer.Exit(code=1)

    git_root = get_git_root(project_root)
    if not git_root:
        console.print(f"[red]✗[/red] Could not determine git root")
        raise typer.Exit(code=1)

    # Resolve worktree path
    worktree_path = Path(path)
    if not worktree_path.is_absolute():
        worktree_path = (git_root / path).resolve()

    console.print(f"\n[bold blue]Removing Git Worktree[/bold blue]")
    console.print(f"[dim]Repository: {git_root}[/dim]")
    console.print(f"[dim]Worktree path: {worktree_path}[/dim]\n")

    # Build git worktree remove command
    git_args = ['worktree', 'remove']

    if force:
        git_args.append('--force')

    git_args.append(str(worktree_path))

    # Execute git worktree remove
    code, stdout, stderr = run_git_command(git_args, cwd=git_root)

    if code != 0:
        console.print(f"[red]✗[/red] Failed to remove worktree")
        console.print(f"[dim]Error: {stderr}[/dim]")

        # Check for uncommitted changes error messages
        if ("uncommitted changes" in stderr.lower() or
            "modified or untracked files" in stderr.lower()) and not force:
            console.print("\n[yellow]Hint:[/yellow] Use --force to remove worktree with uncommitted changes")

        raise typer.Exit(code=1)

    console.print(f"[green]✓[/green] Worktree removed successfully")
    if stdout:
        console.print(f"[dim]{stdout}[/dim]")

    console.print("\n[dim]💡 Tip: Use 'sdlcctl worktree list' to see remaining worktrees[/dim]")


if __name__ == "__main__":
    app()
