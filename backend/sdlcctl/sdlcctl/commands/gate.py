"""
=========================================================================
Gate Governance Commands - CLI Interface for Gate State Machine
SDLC Orchestrator - Sprint 173 (Governance Loop)

Version: 1.0.0
Date: February 15, 2026
Status: ACTIVE - Sprint 173 Implementation
Authority: CTO + Architect + SDLC Expert — All Approved v4 FINAL
Reference: ADR-053-Governance-Loop-State-Machine.md
           CONTRACT-GOVERNANCE-LOOP.md (Section 5.1)

Purpose:
- Complete the governance loop for CLI interface
- 7 commands: list, show, evaluate, submit, approve, reject, status
- All mutations call GET /gates/{id}/actions first (SSOT invariant)
- X-Idempotency-Key header on all mutations
- Server-driven permission model (no client-side logic)

Interface Role: DevOps/CI pipelines (Automated Approval)

Zero Mock Policy: Real API calls via httpx
=========================================================================
"""

import json
import os
from pathlib import Path
from typing import Optional
from uuid import uuid4

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False

console = Console()

app = typer.Typer(
    name="gate",
    help="Gate governance commands (ADR-053)",
    no_args_is_help=True,
)

# Timeout configuration
DEFAULT_TIMEOUT = 30
EVIDENCE_TIMEOUT = 120


def _get_api_config() -> tuple:
    """
    Get API configuration from environment or .sdlc/config.json.

    Returns:
        tuple: (api_url, project_id, auth_token)
    """
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


def _ensure_httpx() -> None:
    """Ensure httpx is available."""
    if not HTTPX_AVAILABLE:
        console.print("[red]Error:[/red] httpx package required. Install with: pip install httpx")
        raise typer.Exit(1)


def _get_headers(auth_token: str, idempotency: bool = False) -> dict:
    """Build request headers with auth and optional idempotency key."""
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }
    if idempotency:
        headers["X-Idempotency-Key"] = str(uuid4())
    return headers


def _handle_error_response(response: "httpx.Response") -> None:
    """Handle common HTTP error responses."""
    if response.status_code == 401:
        console.print("[red]Error:[/red] Unauthorized. Check your auth token.")
        console.print("[dim]Set via SDLC_AUTH_TOKEN env var or .sdlc/config.json[/dim]")
        raise typer.Exit(1)
    elif response.status_code == 403:
        detail = ""
        try:
            detail = response.json().get("detail", "")
        except Exception:
            pass
        console.print(f"[red]Error:[/red] Permission denied. {detail}")
        console.print("[dim]Missing scope: governance:approve[/dim]")
        console.print("[dim]Run: sdlcctl auth login --scope=full[/dim]")
        raise typer.Exit(1)
    elif response.status_code == 404:
        console.print("[red]Error:[/red] Gate not found.")
        raise typer.Exit(1)
    elif response.status_code == 409:
        detail = ""
        try:
            detail = response.json().get("detail", "")
        except Exception:
            pass
        console.print(f"[red]Error:[/red] Conflict — {detail}")
        raise typer.Exit(1)
    elif response.status_code == 422:
        detail = ""
        try:
            detail = response.json().get("detail", "")
        except Exception:
            pass
        console.print(f"[red]Error:[/red] Validation failed — {detail}")
        raise typer.Exit(1)
    elif response.status_code >= 400:
        console.print(f"[red]Error:[/red] API returned {response.status_code}")
        try:
            console.print(response.json())
        except Exception:
            console.print(response.text[:500])
        raise typer.Exit(1)


def _status_style(status: str) -> str:
    """Return Rich markup color for gate status."""
    styles = {
        "DRAFT": "dim",
        "EVALUATED": "blue",
        "EVALUATED_STALE": "yellow",
        "SUBMITTED": "cyan",
        "APPROVED": "green",
        "REJECTED": "red",
        "ARCHIVED": "dim",
    }
    return styles.get(status, "white")


# ============================================================================
# Commands
# ============================================================================


@app.command("list")
def list_command(
    project_id: Optional[str] = typer.Option(
        None, "--project-id", "-p",
        help="Project ID (overrides .sdlc/config.json)",
    ),
    output_format: str = typer.Option(
        "text", "--format", "-f",
        help="Output format: text, json",
    ),
) -> None:
    """
    List all gates for a project.

    Example:
        sdlcctl gate list
        sdlcctl gate list --project-id <uuid>
        sdlcctl gate list --format json
    """
    _ensure_httpx()
    api_url, config_project_id, auth_token = _get_api_config()
    effective_project_id = project_id or config_project_id

    if not effective_project_id:
        console.print("[red]Error:[/red] Project ID not found.")
        console.print("Set via --project-id flag, SDLC_PROJECT_ID env var, or .sdlc/config.json")
        raise typer.Exit(1)

    if not auth_token:
        console.print("[red]Error:[/red] Auth token not found.")
        console.print("Set via SDLC_AUTH_TOKEN env var or .sdlc/config.json")
        raise typer.Exit(1)

    headers = _get_headers(auth_token)

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.get(
                f"{api_url}/gates",
                params={"project_id": effective_project_id},
                headers=headers,
            )

            if response.status_code == 200:
                gates = response.json()

                if output_format == "json":
                    console.print_json(json.dumps(gates, indent=2))
                    return

                if not gates:
                    console.print("[dim]No gates found for this project.[/dim]")
                    return

                table = Table(
                    title="Project Gates",
                    box=box.ROUNDED,
                    show_header=True,
                )
                table.add_column("Gate", style="cyan", width=12)
                table.add_column("Name", width=30)
                table.add_column("Status", width=18)
                table.add_column("Stage", width=10)
                table.add_column("Updated", width=20)

                for g in gates:
                    status = g.get("status", "UNKNOWN")
                    style = _status_style(status)
                    table.add_row(
                        g.get("gate_number", "N/A"),
                        g.get("name", "N/A"),
                        f"[{style}]{status}[/{style}]",
                        g.get("stage", "N/A"),
                        g.get("updated_at", "N/A")[:19] if g.get("updated_at") else "N/A",
                    )

                console.print(table)
                console.print(f"\n[dim]Total: {len(gates)} gates[/dim]")
            else:
                _handle_error_response(response)

    except httpx.RequestError as e:
        console.print(f"[red]Error:[/red] Could not connect to API: {e}")
        raise typer.Exit(1)


@app.command("show")
def show_command(
    gate_id: str = typer.Argument(..., help="Gate UUID"),
    output_format: str = typer.Option(
        "text", "--format", "-f",
        help="Output format: text, json",
    ),
) -> None:
    """
    Show gate details including exit criteria and evidence.

    Example:
        sdlcctl gate show <gate-id>
        sdlcctl gate show <gate-id> --format json
    """
    _ensure_httpx()
    api_url, _, auth_token = _get_api_config()

    if not auth_token:
        console.print("[red]Error:[/red] Auth token not found.")
        raise typer.Exit(1)

    headers = _get_headers(auth_token)

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            # Fetch gate details
            response = client.get(
                f"{api_url}/gates/{gate_id}",
                headers=headers,
            )

            if response.status_code != 200:
                _handle_error_response(response)
                return

            gate = response.json()

            # Also fetch actions to show available actions
            actions_resp = client.get(
                f"{api_url}/gates/{gate_id}/actions",
                headers=headers,
            )
            actions = actions_resp.json() if actions_resp.status_code == 200 else None

            if output_format == "json":
                combined = {"gate": gate}
                if actions:
                    combined["actions"] = actions
                console.print_json(json.dumps(combined, indent=2))
                return

            # Gate info panel
            status = gate.get("status", "UNKNOWN")
            style = _status_style(status)

            info_lines = [
                f"[bold]ID:[/bold]     {gate.get('id', 'N/A')}",
                f"[bold]Name:[/bold]   {gate.get('name', 'N/A')}",
                f"[bold]Number:[/bold] {gate.get('gate_number', 'N/A')}",
                f"[bold]Stage:[/bold]  {gate.get('stage', 'N/A')}",
                f"[bold]Status:[/bold] [{style}]{status}[/{style}]",
                f"[bold]Created:[/bold] {gate.get('created_at', 'N/A')[:19] if gate.get('created_at') else 'N/A'}",
                f"[bold]Updated:[/bold] {gate.get('updated_at', 'N/A')[:19] if gate.get('updated_at') else 'N/A'}",
            ]

            if gate.get("evaluated_at"):
                info_lines.append(
                    f"[bold]Evaluated:[/bold] {gate['evaluated_at'][:19]}"
                )

            console.print(Panel(
                "\n".join(info_lines),
                title=f"[bold blue]Gate: {gate.get('gate_number', gate_id)}[/bold blue]",
                border_style="blue",
            ))

            # Exit criteria
            exit_criteria = gate.get("exit_criteria", [])
            if exit_criteria:
                criteria_table = Table(
                    title="Exit Criteria",
                    box=box.SIMPLE,
                    show_header=True,
                )
                criteria_table.add_column("Criterion", width=40)
                criteria_table.add_column("Required", justify="center", width=10)

                for criterion in exit_criteria:
                    if isinstance(criterion, dict):
                        criteria_table.add_row(
                            criterion.get("name", str(criterion)),
                            "Yes" if criterion.get("required", True) else "No",
                        )
                    else:
                        criteria_table.add_row(str(criterion), "Yes")

                console.print(criteria_table)

            # Available actions
            if actions:
                action_items = actions.get("actions", {})
                reasons = actions.get("reasons", {})

                action_table = Table(
                    title="Available Actions",
                    box=box.SIMPLE,
                    show_header=True,
                )
                action_table.add_column("Action", width=20)
                action_table.add_column("Allowed", justify="center", width=10)
                action_table.add_column("Reason", width=40)

                for action_name, allowed in action_items.items():
                    label = action_name.replace("can_", "").replace("_", " ").title()
                    allowed_str = "[green]Yes[/green]" if allowed else "[red]No[/red]"
                    reason = reasons.get(action_name, "") if not allowed else ""
                    action_table.add_row(label, allowed_str, reason)

                console.print(action_table)

                # Evidence summary
                missing = actions.get("missing_evidence", [])
                submitted = actions.get("submitted_evidence", [])

                if submitted or missing:
                    console.print("\n[bold]Evidence:[/bold]")
                    for ev in submitted:
                        console.print(f"  [green]✓[/green] {ev}")
                    for ev in missing:
                        console.print(f"  [red]✗[/red] {ev} [dim](missing)[/dim]")

    except httpx.RequestError as e:
        console.print(f"[red]Error:[/red] Could not connect to API: {e}")
        raise typer.Exit(1)


@app.command("evaluate")
def evaluate_command(
    gate_id: str = typer.Argument(..., help="Gate UUID"),
    output_format: str = typer.Option(
        "text", "--format", "-f",
        help="Output format: text, json",
    ),
) -> None:
    """
    Evaluate gate against exit criteria.

    Allowed from: DRAFT, EVALUATED, EVALUATED_STALE, REJECTED.
    Requires scope: governance:write.

    Example:
        sdlcctl gate evaluate <gate-id>
    """
    _ensure_httpx()
    api_url, _, auth_token = _get_api_config()

    if not auth_token:
        console.print("[red]Error:[/red] Auth token not found.")
        raise typer.Exit(1)

    headers = _get_headers(auth_token, idempotency=True)

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            # Pre-check: call /actions to verify permission
            actions_resp = client.get(
                f"{api_url}/gates/{gate_id}/actions",
                headers=_get_headers(auth_token),
            )
            if actions_resp.status_code != 200:
                _handle_error_response(actions_resp)
                return

            actions = actions_resp.json()
            if not actions.get("actions", {}).get("can_evaluate"):
                reason = actions.get("reasons", {}).get("can_evaluate", "Unknown")
                console.print(f"[red]Error:[/red] Cannot evaluate: {reason}")
                raise typer.Exit(1)

            # Execute evaluation
            with console.status("[bold blue]Evaluating gate...[/bold blue]"):
                response = client.post(
                    f"{api_url}/gates/{gate_id}/evaluate",
                    headers=headers,
                )

            if response.status_code == 200:
                data = response.json()

                if output_format == "json":
                    console.print_json(json.dumps(data, indent=2))
                    return

                status = data.get("status", "EVALUATED")
                style = _status_style(status)
                console.print(f"\n[green]✓[/green] Gate evaluated → [{style}]{status}[/{style}]")

                # Show criteria results
                criteria_results = data.get("criteria_results", [])
                if criteria_results:
                    for cr in criteria_results:
                        name = cr.get("criterion", "unknown")
                        met = cr.get("met", False)
                        icon = "[green]✓[/green]" if met else "[red]✗[/red]"
                        console.print(f"  {icon} {name}")

                missing = data.get("missing_evidence", [])
                if missing:
                    console.print(f"\n[yellow]Warning:[/yellow] Missing evidence: {', '.join(missing)}")
                    console.print("[dim]Upload evidence before submitting for approval.[/dim]")
            else:
                _handle_error_response(response)

    except httpx.RequestError as e:
        console.print(f"[red]Error:[/red] Could not connect to API: {e}")
        raise typer.Exit(1)


@app.command("submit")
def submit_command(
    gate_id: str = typer.Argument(..., help="Gate UUID"),
    output_format: str = typer.Option(
        "text", "--format", "-f",
        help="Output format: text, json",
    ),
) -> None:
    """
    Submit gate for approval. Blocked if evidence is missing.

    Allowed from: EVALUATED only (no missing evidence).
    Requires scope: governance:write.

    Example:
        sdlcctl gate submit <gate-id>
    """
    _ensure_httpx()
    api_url, _, auth_token = _get_api_config()

    if not auth_token:
        console.print("[red]Error:[/red] Auth token not found.")
        raise typer.Exit(1)

    headers = _get_headers(auth_token, idempotency=True)

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            # Pre-check: call /actions to verify permission + evidence
            actions_resp = client.get(
                f"{api_url}/gates/{gate_id}/actions",
                headers=_get_headers(auth_token),
            )
            if actions_resp.status_code != 200:
                _handle_error_response(actions_resp)
                return

            actions = actions_resp.json()
            if not actions.get("actions", {}).get("can_submit"):
                reason = actions.get("reasons", {}).get("can_submit", "Unknown")
                console.print(f"[red]Error:[/red] Cannot submit: {reason}")

                missing = actions.get("missing_evidence", [])
                if missing:
                    console.print(f"\n[yellow]Missing evidence:[/yellow]")
                    for ev in missing:
                        console.print(f"  [red]✗[/red] {ev}")
                    console.print("\n[dim]Upload evidence first: sdlcctl evidence submit --gate <id> --type <type> --file <path>[/dim]")

                raise typer.Exit(1)

            # Execute submit
            response = client.post(
                f"{api_url}/gates/{gate_id}/submit",
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()

                if output_format == "json":
                    console.print_json(json.dumps(data, indent=2))
                    return

                status = data.get("status", "SUBMITTED")
                style = _status_style(status)
                console.print(f"\n[green]✓[/green] Gate submitted → [{style}]{status}[/{style}]")
                console.print("[dim]Awaiting approval from governance:approve scope holder.[/dim]")
            else:
                _handle_error_response(response)

    except httpx.RequestError as e:
        console.print(f"[red]Error:[/red] Could not connect to API: {e}")
        raise typer.Exit(1)


@app.command("approve")
def approve_command(
    gate_id: str = typer.Argument(..., help="Gate UUID"),
    comment: Optional[str] = typer.Option(
        None, "--comment", "-c",
        help="Approval comment (required, prompted if omitted)",
    ),
    output_format: str = typer.Option(
        "text", "--format", "-f",
        help="Output format: text, json",
    ),
) -> None:
    """
    Approve a submitted gate. Comment is mandatory.

    Allowed from: SUBMITTED only.
    Requires scope: governance:approve (CTO/CPO/CEO).

    Example:
        sdlcctl gate approve <gate-id> --comment "All criteria met"
        sdlcctl gate approve <gate-id>  # prompts for comment
    """
    _ensure_httpx()
    api_url, _, auth_token = _get_api_config()

    if not auth_token:
        console.print("[red]Error:[/red] Auth token not found.")
        raise typer.Exit(1)

    # Prompt for comment if not provided
    if not comment:
        comment = typer.prompt("Approval reason (required)")
    if not comment or not comment.strip():
        console.print("[red]Error:[/red] Comment is required for approval.")
        raise typer.Exit(1)

    headers = _get_headers(auth_token, idempotency=True)

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            # Pre-check: call /actions to verify permission
            actions_resp = client.get(
                f"{api_url}/gates/{gate_id}/actions",
                headers=_get_headers(auth_token),
            )
            if actions_resp.status_code != 200:
                _handle_error_response(actions_resp)
                return

            actions = actions_resp.json()
            if not actions.get("actions", {}).get("can_approve"):
                reason = actions.get("reasons", {}).get("can_approve", "Unknown")
                console.print(f"[red]Error:[/red] Cannot approve: {reason}")
                raise typer.Exit(1)

            # Execute approve
            response = client.post(
                f"{api_url}/gates/{gate_id}/approve",
                headers=headers,
                json={"comment": comment.strip()},
            )

            if response.status_code == 200:
                data = response.json()

                if output_format == "json":
                    console.print_json(json.dumps(data, indent=2))
                    return

                status = data.get("status", "APPROVED")
                style = _status_style(status)
                console.print(f"\n[green]✓[/green] Gate approved → [{style}]{status}[/{style}]")
                console.print(f"[dim]Comment: {comment.strip()}[/dim]")
            else:
                _handle_error_response(response)

    except httpx.RequestError as e:
        console.print(f"[red]Error:[/red] Could not connect to API: {e}")
        raise typer.Exit(1)


@app.command("reject")
def reject_command(
    gate_id: str = typer.Argument(..., help="Gate UUID"),
    comment: Optional[str] = typer.Option(
        None, "--comment", "-c",
        help="Rejection comment (required, opens $EDITOR if omitted)",
    ),
    output_format: str = typer.Option(
        "text", "--format", "-f",
        help="Output format: text, json",
    ),
) -> None:
    """
    Reject a submitted gate. Comment is mandatory.

    Opens $EDITOR for long rejection comments if --comment not provided.
    Allowed from: SUBMITTED only.
    Requires scope: governance:approve (CTO/CPO/CEO).

    Example:
        sdlcctl gate reject <gate-id> --comment "Missing security scan evidence"
        sdlcctl gate reject <gate-id>  # opens $EDITOR for comment
    """
    _ensure_httpx()
    api_url, _, auth_token = _get_api_config()

    if not auth_token:
        console.print("[red]Error:[/red] Auth token not found.")
        raise typer.Exit(1)

    # For reject: use click.edit() for long explanations (Architect v2 fix)
    if not comment:
        if CLICK_AVAILABLE:
            console.print("[dim]Opening editor for rejection comment...[/dim]")
            comment = click.edit(
                text="# Enter rejection reason below.\n"
                "# Lines starting with # will be stripped.\n\n"
            )
            if comment:
                # Strip comment lines
                lines = [
                    line for line in comment.splitlines()
                    if not line.strip().startswith("#")
                ]
                comment = "\n".join(lines).strip()
        else:
            comment = typer.prompt("Rejection reason (required)")

    if not comment or not comment.strip():
        console.print("[red]Error:[/red] Comment is required for rejection.")
        raise typer.Exit(1)

    headers = _get_headers(auth_token, idempotency=True)

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            # Pre-check: call /actions to verify permission
            actions_resp = client.get(
                f"{api_url}/gates/{gate_id}/actions",
                headers=_get_headers(auth_token),
            )
            if actions_resp.status_code != 200:
                _handle_error_response(actions_resp)
                return

            actions = actions_resp.json()
            if not actions.get("actions", {}).get("can_reject"):
                reason = actions.get("reasons", {}).get("can_reject", "Unknown")
                console.print(f"[red]Error:[/red] Cannot reject: {reason}")
                raise typer.Exit(1)

            # Execute reject
            response = client.post(
                f"{api_url}/gates/{gate_id}/reject",
                headers=headers,
                json={"comment": comment.strip()},
            )

            if response.status_code == 200:
                data = response.json()

                if output_format == "json":
                    console.print_json(json.dumps(data, indent=2))
                    return

                status = data.get("status", "REJECTED")
                style = _status_style(status)
                console.print(f"\n[yellow]✗[/yellow] Gate rejected → [{style}]{status}[/{style}]")
                console.print(f"[dim]Comment: {comment.strip()[:100]}{'...' if len(comment.strip()) > 100 else ''}[/dim]")
                console.print("[dim]Gate can be re-evaluated after addressing feedback.[/dim]")
            else:
                _handle_error_response(response)

    except httpx.RequestError as e:
        console.print(f"[red]Error:[/red] Could not connect to API: {e}")
        raise typer.Exit(1)


@app.command("status")
def status_command(
    project_id: Optional[str] = typer.Option(
        None, "--project-id", "-p",
        help="Project ID (overrides .sdlc/config.json)",
    ),
    output_format: str = typer.Option(
        "text", "--format", "-f",
        help="Output format: text, json",
    ),
) -> None:
    """
    Show compact gate status summary for a project.

    Example:
        sdlcctl gate status
        sdlcctl gate status --project-id <uuid>
        sdlcctl gate status --format json
    """
    _ensure_httpx()
    api_url, config_project_id, auth_token = _get_api_config()
    effective_project_id = project_id or config_project_id

    if not effective_project_id:
        console.print("[red]Error:[/red] Project ID not found.")
        console.print("Set via --project-id flag, SDLC_PROJECT_ID env var, or .sdlc/config.json")
        raise typer.Exit(1)

    if not auth_token:
        console.print("[red]Error:[/red] Auth token not found.")
        raise typer.Exit(1)

    headers = _get_headers(auth_token)

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.get(
                f"{api_url}/gates",
                params={"project_id": effective_project_id},
                headers=headers,
            )

            if response.status_code == 200:
                gates = response.json()

                if output_format == "json":
                    console.print_json(json.dumps(gates, indent=2))
                    return

                if not gates:
                    console.print("[dim]No gates found for this project.[/dim]")
                    return

                # Compact status table
                table = Table(
                    title="Gate Status",
                    box=box.SIMPLE_HEAVY,
                    show_header=True,
                    padding=(0, 1),
                )
                table.add_column("Gate", style="cyan", width=8)
                table.add_column("Status", width=18)
                table.add_column("Progress", width=20)

                status_counts = {}
                for g in gates:
                    status = g.get("status", "UNKNOWN")
                    style = _status_style(status)
                    status_counts[status] = status_counts.get(status, 0) + 1

                    # Build progress bar
                    progress_map = {
                        "DRAFT": "░░░░░░",
                        "EVALUATED": "██░░░░",
                        "EVALUATED_STALE": "█▒░░░░",
                        "SUBMITTED": "████░░",
                        "APPROVED": "██████",
                        "REJECTED": "██▓░░░",
                    }
                    progress = progress_map.get(status, "░░░░░░")

                    table.add_row(
                        g.get("gate_number", "N/A"),
                        f"[{style}]{status}[/{style}]",
                        progress,
                    )

                console.print(table)

                # Summary line
                summary_parts = []
                for s, count in sorted(status_counts.items()):
                    style = _status_style(s)
                    summary_parts.append(f"[{style}]{s}: {count}[/{style}]")
                console.print(f"\n{' | '.join(summary_parts)}")
                console.print(f"[dim]Total: {len(gates)} gates[/dim]")

            else:
                _handle_error_response(response)

    except httpx.RequestError as e:
        console.print(f"[red]Error:[/red] Could not connect to API: {e}")
        raise typer.Exit(1)
