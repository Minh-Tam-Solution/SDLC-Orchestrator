"""
=========================================================================
Auth Commands - CLI Authentication for SDLC Orchestrator
SDLC Orchestrator - Sprint 212 (Track B - CLI Auth Login)

Version: 1.0.0
Date: February 28, 2026
Status: ACTIVE - Sprint 212 Implementation
Authority: CTO + Backend Team Approved
Reference: ADR-053-Governance-Loop-State-Machine.md

Purpose:
- Interactive email+password login (JWT flow)
- API key mode for CI/CD pipelines
- Auth status display (user, token expiry, API URL)
- Logout (clear stored credentials)
- Auto-refresh JWT when expiry is within 5 minutes

Interface Role: Developer + CI/CD authentication

Zero Mock Policy: Real API calls via httpx
=========================================================================
"""

import base64
import json
import os
import time
from pathlib import Path

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
    name="auth",
    help="Authentication commands (login, logout, status)",
    no_args_is_help=True,
)

CONFIG_DIR = Path.home() / ".sdlcctl"
CONFIG_PATH = CONFIG_DIR / "config.json"
DEFAULT_TIMEOUT = 30


def _ensure_httpx() -> None:
    """Ensure httpx is available."""
    if not HTTPX_AVAILABLE:
        console.print("[red]Error:[/red] httpx package required. Install with: pip install httpx")
        raise typer.Exit(1)


def _load_config() -> dict:
    """Load config from ~/.sdlcctl/config.json, returning defaults if absent."""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "server": {"url": "https://api.sdlc.nhatquangholding.com"},
        "auth": {"token": "", "api_key": "", "user_email": ""},
        "project": {"id": ""},
    }


def _save_config(config: dict) -> None:
    """Persist config to ~/.sdlcctl/config.json with safe permissions."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2))
    CONFIG_PATH.chmod(0o600)


def _decode_jwt_payload(token: str) -> dict:
    """Decode the payload segment of a JWT (no signature verification)."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        payload_b64 = parts[1]
        # Pad base64url to standard base64
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        decoded = base64.urlsafe_b64decode(payload_b64)
        return json.loads(decoded)
    except Exception:
        return {}


def _get_api_url(config: dict) -> str:
    """Resolve API base URL from config or environment."""
    url = os.environ.get(
        "SDLC_API_URL",
        config.get("server", {}).get("url", "https://api.sdlc.nhatquangholding.com"),
    )
    if url and not url.endswith("/api/v1"):
        url = f"{url.rstrip('/')}/api/v1"
    return url


# ============================================================================
# Commands
# ============================================================================


@app.command("login")
def login_command(
    api_key: str = typer.Option(
        "", "--api-key", "-k",
        help="API key for CI/CD (skips interactive prompt)",
    ),
) -> None:
    """
    Authenticate with the SDLC Orchestrator API.

    Interactive mode (default): prompts for email and password.
    CI/CD mode: pass --api-key to verify and store a service key.

    Example:
        sdlcctl auth login
        sdlcctl auth login --api-key sk-abc123
    """
    _ensure_httpx()
    config = _load_config()
    api_url = _get_api_url(config)

    if api_key:
        # ---- API-key mode (CI/CD) ----
        with console.status("[bold blue]Verifying API key...[/bold blue]"):
            try:
                with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                    response = client.post(
                        f"{api_url}/auth/verify-key",
                        json={"api_key": api_key},
                    )
            except httpx.RequestError as exc:
                console.print(f"[red]Error:[/red] Could not connect to API: {exc}")
                raise typer.Exit(1)

        if response.status_code != 200:
            console.print("[red]Error:[/red] Invalid API key.")
            raise typer.Exit(1)

        data = response.json()
        config["auth"]["api_key"] = api_key
        config["auth"]["token"] = ""
        config["auth"]["user_email"] = data.get("email", "service-account")
        _save_config(config)

        console.print(Panel(
            f"[bold]Mode:[/bold]  API Key\n"
            f"[bold]User:[/bold]  {config['auth']['user_email']}\n"
            f"[bold]API:[/bold]   {api_url}",
            title="[bold green]Authenticated[/bold green]",
            border_style="green",
        ))
        return

    # ---- Interactive email + password mode ----
    email = typer.prompt("Email")
    password = typer.prompt("Password", hide_input=True)

    with console.status("[bold blue]Authenticating...[/bold blue]"):
        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                response = client.post(
                    f"{api_url}/auth/login",
                    json={"email": email, "password": password},
                )
        except httpx.RequestError as exc:
            console.print(f"[red]Error:[/red] Could not connect to API: {exc}")
            raise typer.Exit(1)

    if response.status_code != 200:
        detail = ""
        try:
            detail = response.json().get("detail", "")
        except Exception:
            pass
        console.print(f"[red]Error:[/red] Login failed. {detail}")
        raise typer.Exit(1)

    data = response.json()
    token = data.get("access_token", "")

    config["auth"]["token"] = token
    config["auth"]["api_key"] = ""
    config["auth"]["user_email"] = email
    _save_config(config)

    payload = _decode_jwt_payload(token)
    exp = payload.get("exp", 0)
    exp_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(exp)) if exp else "unknown"

    console.print(Panel(
        f"[bold]Email:[/bold]   {email}\n"
        f"[bold]Expiry:[/bold]  {exp_str}\n"
        f"[bold]API:[/bold]     {api_url}",
        title="[bold green]Login Successful[/bold green]",
        border_style="green",
    ))


@app.command("status")
def status_command() -> None:
    """
    Show current authentication state.

    Displays logged-in user, token expiry, and API URL.
    Auto-refreshes token if expiry is within 5 minutes.

    Example:
        sdlcctl auth status
    """
    config = _load_config()
    api_url = _get_api_url(config)
    token = config.get("auth", {}).get("token", "")
    api_key = config.get("auth", {}).get("api_key", "")
    user_email = config.get("auth", {}).get("user_email", "")

    if api_key:
        console.print(Panel(
            f"[bold]Mode:[/bold]   API Key\n"
            f"[bold]User:[/bold]   {user_email or 'service-account'}\n"
            f"[bold]API:[/bold]    {api_url}\n"
            f"[bold]Key:[/bold]    {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '****'}",
            title="[bold blue]Auth Status[/bold blue]",
            border_style="blue",
        ))
        return

    if not token:
        console.print("[yellow]Not authenticated.[/yellow] Run: sdlcctl auth login")
        return

    payload = _decode_jwt_payload(token)
    exp = payload.get("exp", 0)
    sub = payload.get("sub", "")
    email = payload.get("email", user_email)
    now = int(time.time())
    remaining = exp - now if exp else 0

    # Auto-refresh if within 5 minutes of expiry
    if 0 < remaining < 300 and HTTPX_AVAILABLE:
        console.print("[yellow]Token expiring soon, refreshing...[/yellow]")
        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                resp = client.post(
                    f"{api_url}/auth/refresh",
                    headers={"Authorization": f"Bearer {token}"},
                )
            if resp.status_code == 200:
                new_token = resp.json().get("access_token", "")
                if new_token:
                    config["auth"]["token"] = new_token
                    _save_config(config)
                    token = new_token
                    payload = _decode_jwt_payload(token)
                    exp = payload.get("exp", 0)
                    remaining = exp - now if exp else 0
                    console.print("[green]Token refreshed.[/green]")
        except httpx.RequestError:
            console.print("[yellow]Warning:[/yellow] Could not refresh token.")

    if remaining <= 0:
        expiry_line = "[red]EXPIRED[/red]"
    else:
        exp_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(exp))
        mins = remaining // 60
        expiry_line = f"{exp_str} ({mins}m remaining)"

    console.print(Panel(
        f"[bold]Mode:[/bold]    JWT Token\n"
        f"[bold]Email:[/bold]   {email}\n"
        f"[bold]Subject:[/bold] {sub}\n"
        f"[bold]Expiry:[/bold]  {expiry_line}\n"
        f"[bold]API:[/bold]     {api_url}",
        title="[bold blue]Auth Status[/bold blue]",
        border_style="blue",
    ))


@app.command("logout")
def logout_command() -> None:
    """
    Clear stored credentials from ~/.sdlcctl/config.json.

    Example:
        sdlcctl auth logout
    """
    config = _load_config()
    config["auth"] = {"token": "", "api_key": "", "user_email": ""}
    _save_config(config)
    console.print("[green]Logged out.[/green] Credentials cleared from ~/.sdlcctl/config.json")
