"""
Team management commands — Sprint 212 Track C (Team Invite Parity).

Commands:
    sdlcctl team invite <email> --role member --team-id <uuid>
    sdlcctl team list --team-id <uuid>
    sdlcctl team remove <user-id> --team-id <uuid>
"""

import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.table import Table

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

console = Console()

app = typer.Typer(
    name="team",
    help="Team management commands (Sprint 212)",
    no_args_is_help=True,
)

DEFAULT_TIMEOUT = 30


def _get_api_config() -> tuple:
    """Get API URL, project ID, and auth token from env or .sdlc/config.json."""
    api_url = os.environ.get("SDLC_API_URL", "https://sdlc.mtsolution.com.vn/api/v1")
    auth_token = os.environ.get("SDLC_AUTH_TOKEN", "")
    project_id = os.environ.get("SDLC_PROJECT_ID", "")

    config_path = Path.cwd() / ".sdlc" / "config.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
            api_url = config.get("server", {}).get("url", api_url)
            if api_url and not api_url.endswith("/api/v1"):
                api_url = f"{api_url.rstrip('/')}/api/v1"
            project_id = config.get("project", {}).get("id", project_id)
            auth_token = config.get("auth", {}).get("token", auth_token)
        except (json.JSONDecodeError, KeyError):
            pass

    return api_url, project_id, auth_token


def _ensure_deps(auth_token: str) -> None:
    """Validate httpx is installed and auth token is present."""
    if not HTTPX_AVAILABLE:
        console.print("[red]Error:[/red] httpx required. Install with: pip install httpx")
        raise typer.Exit(1)
    if not auth_token:
        console.print("[red]Error:[/red] Auth token not found.")
        console.print("Set via SDLC_AUTH_TOKEN env var or .sdlc/config.json")
        raise typer.Exit(1)


@app.command("invite")
def invite_command(
    email: str = typer.Argument(..., help="Email address to invite"),
    role: str = typer.Option("member", "--role", "-r", help="Role: member, admin, viewer"),
    team_id: Optional[str] = typer.Option(None, "--team-id", "-t", help="Team UUID"),
) -> None:
    """Invite a user to a team by email."""
    api_url, _, auth_token = _get_api_config()
    _ensure_deps(auth_token)

    if not team_id:
        console.print("[red]Error:[/red] --team-id is required.")
        raise typer.Exit(1)

    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.post(
                f"{api_url}/teams/{team_id}/invitations",
                headers=headers,
                json={"email": email, "role": role},
            )
            if resp.status_code in (200, 201):
                console.print(f"[green]Invited[/green] {email} as [cyan]{role}[/cyan]")
            else:
                console.print(f"[red]Error:[/red] {resp.status_code} — {resp.text[:200]}")
                raise typer.Exit(1)
    except httpx.RequestError as e:
        console.print(f"[red]Error:[/red] Could not connect to API: {e}")
        raise typer.Exit(1)


@app.command("list")
def list_command(
    team_id: Optional[str] = typer.Option(None, "--team-id", "-t", help="Team UUID"),
) -> None:
    """List team members."""
    api_url, _, auth_token = _get_api_config()
    _ensure_deps(auth_token)

    if not team_id:
        console.print("[red]Error:[/red] --team-id is required.")
        raise typer.Exit(1)

    headers = {"Authorization": f"Bearer {auth_token}"}

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.get(f"{api_url}/teams/{team_id}/members", headers=headers)
            if resp.status_code == 200:
                members = resp.json()
                if not members:
                    console.print("[dim]No members found.[/dim]")
                    return
                table = Table(title="Team Members", box=box.ROUNDED, show_header=True)
                table.add_column("Name", width=25)
                table.add_column("Email", width=30)
                table.add_column("Role", width=12)
                for m in members:
                    table.add_row(
                        m.get("full_name", m.get("username", "N/A")),
                        m.get("email", "N/A"),
                        m.get("role", "N/A"),
                    )
                console.print(table)
                console.print(f"\n[dim]Total: {len(members)} members[/dim]")
            else:
                console.print(f"[red]Error:[/red] {resp.status_code} — {resp.text[:200]}")
                raise typer.Exit(1)
    except httpx.RequestError as e:
        console.print(f"[red]Error:[/red] Could not connect to API: {e}")
        raise typer.Exit(1)


@app.command("remove")
def remove_command(
    user_id: str = typer.Argument(..., help="User UUID to remove"),
    team_id: Optional[str] = typer.Option(None, "--team-id", "-t", help="Team UUID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Remove a member from a team."""
    api_url, _, auth_token = _get_api_config()
    _ensure_deps(auth_token)

    if not team_id:
        console.print("[red]Error:[/red] --team-id is required.")
        raise typer.Exit(1)

    if not yes:
        confirm = typer.confirm(f"Remove user {user_id} from team {team_id}?")
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit(0)

    headers = {"Authorization": f"Bearer {auth_token}"}

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.delete(
                f"{api_url}/teams/{team_id}/members/{user_id}",
                headers=headers,
            )
            if resp.status_code in (200, 204):
                console.print(f"[green]Removed[/green] user {user_id} from team.")
            else:
                console.print(f"[red]Error:[/red] {resp.status_code} — {resp.text[:200]}")
                raise typer.Exit(1)
    except httpx.RequestError as e:
        console.print(f"[red]Error:[/red] Could not connect to API: {e}")
        raise typer.Exit(1)
