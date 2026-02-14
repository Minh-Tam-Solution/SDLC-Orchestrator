"""sdlcctl project commands.

SDLC 6.0.5 - Sprint 136 - SSOT Design Principle.

Commands for managing project context (stage, gate, sprint).
Database is the Single Source of Truth - these commands write to backend API.

Usage:
    sdlcctl project context --stage BUILD --gate G3 --sprint 136
    sdlcctl project context --show
    sdlcctl project context --strict-mode
"""

from pathlib import Path
from typing import Optional
import json
import os

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

console = Console()

# Typer app for project commands
app = typer.Typer(
    name="project",
    help="Project management commands (SSOT)",
    no_args_is_help=True,
)


def get_api_config() -> tuple[str, str, str]:
    """
    Get API configuration from environment or .sdlc/config.json.
    
    Returns:
        tuple: (api_url, project_id, auth_token)
    """
    # Try environment variables first
    api_url = os.environ.get("SDLC_API_URL", "https://sdlc.mtsolution.com.vn/api/v1")
    auth_token = os.environ.get("SDLC_AUTH_TOKEN", "")
    project_id = os.environ.get("SDLC_PROJECT_ID", "")
    
    # Try .sdlc/config.json
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


@app.command("context")
def context_command(
    stage: Optional[str] = typer.Option(
        None,
        "--stage",
        "-s",
        help="Set current SDLC stage: FOUNDATION, PLANNING, DESIGN, INTEGRATE, BUILD, TEST, DEPLOY, OPERATE, GOVERN, ARCHIVE",
    ),
    gate: Optional[str] = typer.Option(
        None,
        "--gate",
        "-g",
        help="Set current/last passed gate: G0.1, G0.2, G1, G2, G3, G4, G5, G6, G7, G8, G9",
    ),
    sprint: Optional[int] = typer.Option(
        None,
        "--sprint",
        "-n",
        help="Set current sprint number (e.g., 136)",
    ),
    sprint_goal: Optional[str] = typer.Option(
        None,
        "--goal",
        help="Set current sprint goal",
    ),
    strict_mode: Optional[bool] = typer.Option(
        None,
        "--strict-mode/--no-strict-mode",
        help="Enable/disable post-G3 strict mode (bug fixes only)",
    ),
    show: bool = typer.Option(
        False,
        "--show",
        help="Show current project context (read from database)",
    ),
    project_id: Optional[str] = typer.Option(
        None,
        "--project-id",
        "-p",
        help="Project ID (overrides .sdlc/config.json)",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text, json",
    ),
) -> None:
    """
    Get or set project context (stage, gate, sprint).
    
    SSOT Design Principle (Sprint 136):
    - Database is the Single Source of Truth
    - This command writes to backend API
    - Extension/Dashboard read from the same source
    
    Examples:
        sdlcctl project context --show
        sdlcctl project context --stage BUILD --gate G3
        sdlcctl project context --sprint 136 --goal "Launch MVP"
        sdlcctl project context --strict-mode
    """
    if not HTTPX_AVAILABLE:
        console.print("[red]Error:[/red] httpx package required. Install with: pip install httpx")
        raise typer.Exit(1)
    
    api_url, config_project_id, auth_token = get_api_config()
    
    # Use provided project_id or from config
    effective_project_id = project_id or config_project_id
    
    if not effective_project_id:
        console.print("[red]Error:[/red] Project ID not found.")
        console.print("Set via --project-id flag, SDLC_PROJECT_ID env var, or .sdlc/config.json")
        raise typer.Exit(1)
    
    if not auth_token:
        console.print("[red]Error:[/red] Auth token not found.")
        console.print("Set via SDLC_AUTH_TOKEN env var or .sdlc/config.json")
        raise typer.Exit(1)
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }
    
    # Show mode - GET request
    if show or (stage is None and gate is None and sprint is None and sprint_goal is None and strict_mode is None):
        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(
                    f"{api_url}/projects/{effective_project_id}/context",
                    headers=headers,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if output_format == "json":
                        console.print_json(json.dumps(data, indent=2))
                    else:
                        # Rich table output
                        table = Table(title="Project Context (SSOT)", show_header=True)
                        table.add_column("Field", style="cyan")
                        table.add_column("Value", style="green")
                        
                        table.add_row("Project ID", data.get("project_id", "N/A"))
                        table.add_row("Stage", data.get("stage", "N/A"))
                        table.add_row("Gate", data.get("gate", "N/A"))
                        table.add_row("Sprint", str(data.get("sprint_number", "N/A")))
                        table.add_row("Sprint Goal", data.get("sprint_goal", "N/A") or "N/A")
                        table.add_row("Strict Mode", "✅ Yes" if data.get("strict_mode") else "❌ No")
                        table.add_row("Updated At", data.get("updated_at", "N/A"))
                        
                        console.print(table)
                        console.print("\n[dim]Source: Database (SSOT)[/dim]")
                elif response.status_code == 401:
                    console.print("[red]Error:[/red] Unauthorized. Check your auth token.")
                    raise typer.Exit(1)
                elif response.status_code == 404:
                    console.print("[red]Error:[/red] Project not found.")
                    raise typer.Exit(1)
                else:
                    console.print(f"[red]Error:[/red] API returned {response.status_code}")
                    console.print(response.text)
                    raise typer.Exit(1)
                    
        except httpx.RequestError as e:
            console.print(f"[red]Error:[/red] Could not connect to API: {e}")
            raise typer.Exit(1)
    
    # Update mode - PUT request
    else:
        payload = {}
        if stage is not None:
            payload["stage"] = stage.upper()
        if gate is not None:
            payload["gate"] = gate
        if sprint is not None:
            payload["sprint_number"] = sprint
        if sprint_goal is not None:
            payload["sprint_goal"] = sprint_goal
        if strict_mode is not None:
            payload["strict_mode"] = strict_mode
        
        try:
            with httpx.Client(timeout=30) as client:
                response = client.put(
                    f"{api_url}/projects/{effective_project_id}/context",
                    headers=headers,
                    json=payload,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if output_format == "json":
                        console.print_json(json.dumps(data, indent=2))
                    else:
                        console.print(Panel(
                            f"[green]✓ Project context updated successfully[/green]\n\n"
                            f"Stage: [cyan]{data.get('stage', 'N/A')}[/cyan]\n"
                            f"Gate: [cyan]{data.get('gate', 'N/A')}[/cyan]\n"
                            f"Sprint: [cyan]{data.get('sprint_number', 'N/A')}[/cyan]\n"
                            f"Strict Mode: [cyan]{'Yes' if data.get('strict_mode') else 'No'}[/cyan]",
                            title="SSOT Update",
                            border_style="green",
                        ))
                elif response.status_code == 400:
                    error = response.json().get("detail", "Invalid input")
                    console.print(f"[red]Error:[/red] {error}")
                    raise typer.Exit(1)
                elif response.status_code == 401:
                    console.print("[red]Error:[/red] Unauthorized. Check your auth token.")
                    raise typer.Exit(1)
                elif response.status_code == 403:
                    console.print("[red]Error:[/red] Permission denied. Only owners/admins can update context.")
                    raise typer.Exit(1)
                elif response.status_code == 404:
                    console.print("[red]Error:[/red] Project not found.")
                    raise typer.Exit(1)
                else:
                    console.print(f"[red]Error:[/red] API returned {response.status_code}")
                    console.print(response.text)
                    raise typer.Exit(1)
                    
        except httpx.RequestError as e:
            console.print(f"[red]Error:[/red] Could not connect to API: {e}")
            raise typer.Exit(1)


# Standalone function for CLI registration
def project_context_command(
    stage: Optional[str] = None,
    gate: Optional[str] = None,
    sprint: Optional[int] = None,
    sprint_goal: Optional[str] = None,
    strict_mode: Optional[bool] = None,
    show: bool = False,
    project_id: Optional[str] = None,
    output_format: str = "text",
) -> None:
    """Wrapper for CLI registration."""
    context_command(
        stage=stage,
        gate=gate,
        sprint=sprint,
        sprint_goal=sprint_goal,
        strict_mode=strict_mode,
        show=show,
        project_id=project_id,
        output_format=output_format,
    )
