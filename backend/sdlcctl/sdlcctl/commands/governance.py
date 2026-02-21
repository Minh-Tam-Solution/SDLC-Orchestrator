"""Governance Commands — Registry-Driven CLI for Sprint 191.

Sprint 191 (SPRINT-191-UNIFIED-COMMAND-REGISTRY).

CLI commands generated from the Unified Command Registry to ensure
parity with OTT chat commands. All 5 governance commands share
Pydantic schemas with chat_command_router.py.

Usage::

    sdlcctl governance gate-status --project-id 5
    sdlcctl governance create-project --name "My Project"
    sdlcctl governance submit-evidence --gate-id <UUID>
    sdlcctl governance request-approval --gate-id <UUID> --action approve
    sdlcctl governance export-audit --project-id 5 --format json
"""

from __future__ import annotations

import json
import os

import typer
from rich.console import Console
from rich.panel import Panel

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

console = Console()

app = typer.Typer(
    name="governance",
    help="Governance commands — same 5 commands available via OTT channels (Sprint 191)",
    no_args_is_help=True,
)


def _get_base_url() -> str:
    """Get the API base URL from environment or default."""
    return os.environ.get("SDLCCTL_API_URL", "http://localhost:8000/api/v1")


def _get_auth_headers() -> dict[str, str]:
    """Get authentication headers from environment."""
    token = os.environ.get("SDLCCTL_TOKEN", "")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _api_call(method: str, path: str, payload: dict | None = None) -> dict:
    """Make an authenticated API call to the backend."""
    if not HTTPX_AVAILABLE:
        console.print(
            "[red]httpx is required. Install: pip install httpx[/red]",
        )
        raise typer.Exit(1)

    url = f"{_get_base_url()}{path}"
    headers = _get_auth_headers()
    headers["Content-Type"] = "application/json"

    try:
        with httpx.Client(timeout=30.0) as client:
            if method == "GET":
                response = client.get(url, headers=headers, params=payload)
            else:
                response = client.post(url, headers=headers, json=payload)

        if response.status_code >= 400:
            console.print(
                f"[red]API Error {response.status_code}:[/red] {response.text}",
            )
            raise typer.Exit(1)

        try:
            return response.json()
        except (ValueError, json.JSONDecodeError):
            console.print(
                f"[red]Invalid JSON response:[/red] {response.text[:200]}",
            )
            raise typer.Exit(1) from None
    except httpx.ConnectError:
        console.print(f"[red]Cannot connect to {_get_base_url()}[/red]")
        console.print(
            "[dim]Set SDLCCTL_API_URL if not using default[/dim]",
        )
        raise typer.Exit(1) from None


@app.command(name="gate-status")
def gate_status(
    project_id: int | None = typer.Option(
        None, "--project-id", "-p", help="Project ID",
    ),
    gate_id: str | None = typer.Option(
        None, "--gate-id", "-g", help="Gate UUID",
    ),
) -> None:
    """Get quality gate status for a project.

    Same as OTT: "gate status", "trạng thái gate"
    """
    params: dict = {}
    if project_id is not None:
        params["project_id"] = project_id
    if gate_id is not None:
        params["gate_id"] = gate_id

    if not params:
        console.print("[yellow]Specify --project-id or --gate-id[/yellow]")
        raise typer.Exit(1)

    result = _api_call("GET", "/gates", params)
    console.print(Panel(
        json.dumps(result, indent=2, default=str),
        title="Gate Status",
        border_style="green",
    ))


@app.command(name="create-project")
def create_project(
    name: str = typer.Option(..., "--name", "-n", help="Project name"),
    description: str | None = typer.Option(
        None, "--description", "-d", help="Project description",
    ),
) -> None:
    """Create a new SDLC project.

    Same as OTT: "tạo dự án", "create project"
    """
    payload: dict = {"name": name}
    if description:
        payload["description"] = description

    result = _api_call("POST", "/projects", payload)
    console.print(Panel(
        json.dumps(result, indent=2, default=str),
        title=f"Project Created: {name}",
        border_style="green",
    ))


@app.command(name="submit-evidence")
def submit_evidence(
    gate_id: str = typer.Option(
        ..., "--gate-id", "-g", help="Gate UUID",
    ),
    evidence_type: str = typer.Option(
        ..., "--evidence-type", "-t", help="Evidence type (e.g., test_report)",
    ),
    file_url: str = typer.Option(
        ..., "--file-url", "-f", help="URL or path to evidence file",
    ),
) -> None:
    """Submit evidence for a quality gate.

    Same as OTT: "nộp bằng chứng", "submit evidence"
    """
    payload = {
        "gate_id": gate_id,
        "evidence_type": evidence_type,
        "file_url": file_url,
    }
    result = _api_call("POST", f"/gates/{gate_id}/evidence", payload)
    console.print(Panel(
        json.dumps(result, indent=2, default=str),
        title="Evidence Submitted",
        border_style="green",
    ))


@app.command(name="request-approval")
def request_approval(
    gate_id: str = typer.Option(
        ..., "--gate-id", "-g", help="Gate UUID",
    ),
    action: str = typer.Option(
        ..., "--action", "-a", help="Action: approve or reject",
    ),
) -> None:
    """Request approval or rejection for a quality gate.

    Same as OTT: "approve", "reject", "duyệt", "từ chối"
    """
    if action not in ("approve", "reject"):
        console.print(
            f"[red]Invalid action '{action}'. Use 'approve' or 'reject'[/red]",
        )
        raise typer.Exit(1)

    result = _api_call("POST", f"/gates/{gate_id}/{action}", {"gate_id": gate_id})
    console.print(Panel(
        json.dumps(result, indent=2, default=str),
        title=f"Gate {action.title()}d",
        border_style="green",
    ))


@app.command(name="export-audit")
def export_audit(
    project_id: int = typer.Option(
        ..., "--project-id", "-p", help="Project ID",
    ),
    format: str = typer.Option(
        "json", "--format", "-f", help="Export format: json or csv",
    ),
) -> None:
    """Export audit log for a project.

    Same as OTT: "export audit", "xuất báo cáo"
    """
    if format not in ("json", "csv"):
        console.print(
            f"[red]Invalid format '{format}'. Use 'json' or 'csv'[/red]",
        )
        raise typer.Exit(1)

    params = {"project_id": project_id, "format": format}
    result = _api_call("GET", "/enterprise/audit/export", params)
    console.print(Panel(
        json.dumps(result, indent=2, default=str),
        title=f"Audit Export (Project {project_id})",
        border_style="green",
    ))
