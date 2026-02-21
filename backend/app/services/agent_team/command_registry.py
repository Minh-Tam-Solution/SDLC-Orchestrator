"""
Unified Command Registry — Single Source of Truth for CLI + OTT.

Sprint 191 (SPRINT-191-UNIFIED-COMMAND-REGISTRY).

Declarative command definitions shared by:
  - OTT channels (chat_command_router.py — LLM function calling)
  - CLI (sdlcctl governance — Typer commands)

Design references:
  - OpenClaw: 56 skills, declarative registration, per-channel command name overrides
  - TinySDLC: In-chat regex commands, @mention routing

Constraints:
  - Maximum 10 commands in registry (Expert 9 correction — prevent unbounded growth)
  - Each command MUST have: name, params, permission, handler, cli_name, ott_aliases
  - Permission matrix reuses existing RBAC scopes
"""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Tool Parameter Schemas (Pydantic v2 — moved from chat_command_router.py)
# ============================================================================


class CreateProjectParams(BaseModel):
    """Parameters for create_project command."""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=2000, description="Project description")


class GetGateStatusParams(BaseModel):
    """Parameters for get_gate_status command."""

    project_id: Optional[int] = Field(None, description="Project ID (integer)")
    gate_id: Optional[UUID] = Field(None, description="Gate UUID")


class SubmitEvidenceParams(BaseModel):
    """Parameters for submit_evidence command."""

    gate_id: UUID = Field(..., description="Gate UUID")
    evidence_type: str = Field(
        ..., min_length=1, max_length=50,
        description="Evidence type (e.g., test_report)",
    )
    file_url: str = Field(..., min_length=1, description="URL or path to evidence file")


class RequestApprovalParams(BaseModel):
    """Parameters for request_approval command."""

    gate_id: UUID = Field(..., description="Gate UUID")
    action: Literal["approve", "reject"] = Field(..., description="Approval action")


class ExportAuditParams(BaseModel):
    """Parameters for export_audit command."""

    project_id: int = Field(..., description="Project ID")
    format: Literal["json", "csv"] = Field(default="json", description="Export format")


# ============================================================================
# Tool Name Enum — Bounded Allowlist (T-01)
# ============================================================================


class ToolName(str, Enum):
    """Bounded allowlist of governance tools (T-01)."""

    CREATE_PROJECT = "create_project"
    GET_GATE_STATUS = "get_gate_status"
    SUBMIT_EVIDENCE = "submit_evidence"
    REQUEST_APPROVAL = "request_approval"
    EXPORT_AUDIT = "export_audit"


# ============================================================================
# Command Definition
# ============================================================================

# Maximum number of commands allowed in the registry (Expert 9 correction).
MAX_COMMANDS = 10


@dataclasses.dataclass(frozen=True)
class CommandDef:
    """Declarative command definition — single source of truth for CLI + OTT."""

    name: str
    """Canonical command name (matches ToolName value)."""

    description: str
    """English description for help text and LLM prompts."""

    params: type[BaseModel]
    """Pydantic v2 model for parameter validation."""

    permission: str
    """RBAC scope required (e.g., 'governance:read')."""

    handler: str
    """Dotted path to handler (informational — actual dispatch in adapters)."""

    cli_name: str
    """CLI command name for sdlcctl (e.g., 'gate-status')."""

    ott_description: str
    """Description including Vietnamese aliases for LLM function calling."""

    ott_aliases: tuple[str, ...]
    """Vietnamese and English aliases for OTT matching."""

    required_params: tuple[str, ...] = ()
    """Parameter names required in the JSON Schema."""


# ============================================================================
# Governance Commands — The 5 Tools (T-01)
# ============================================================================

GOVERNANCE_COMMANDS: list[CommandDef] = [
    CommandDef(
        name="create_project",
        description="Create a new SDLC project",
        params=CreateProjectParams,
        permission="projects:write",
        handler="project_service.create_project",
        cli_name="create-project",
        ott_description=(
            "Create a new SDLC project. "
            "Use when user says 'tạo dự án', 'create project', etc."
        ),
        ott_aliases=("tạo dự án", "create project"),
        required_params=("name",),
    ),
    CommandDef(
        name="get_gate_status",
        description="Get quality gate status for a project",
        params=GetGateStatusParams,
        permission="governance:read",
        handler="gate_service.get_gate_status",
        cli_name="gate-status",
        ott_description=(
            "Get quality gate status for a project. "
            "Use when user says 'gate status', 'trạng thái gate', 'check gate', etc."
        ),
        ott_aliases=("gate status", "trạng thái gate", "check gate"),
        required_params=(),
    ),
    CommandDef(
        name="submit_evidence",
        description="Submit evidence for a quality gate",
        params=SubmitEvidenceParams,
        permission="governance:write",
        handler="evidence_service.submit_evidence",
        cli_name="submit-evidence",
        ott_description=(
            "Submit evidence for a quality gate. "
            "Use when user says 'upload evidence', 'nộp bằng chứng', 'submit', etc."
        ),
        ott_aliases=("nộp bằng chứng", "submit evidence", "upload evidence"),
        required_params=("gate_id", "evidence_type", "file_url"),
    ),
    CommandDef(
        name="request_approval",
        description="Request approval or rejection for a quality gate",
        params=RequestApprovalParams,
        permission="governance:approve",
        handler="gate_service.request_approval",
        cli_name="request-approval",
        ott_description=(
            "Request approval or rejection for a quality gate. "
            "Use when user says 'approve', 'reject', 'duyệt', 'từ chối', etc."
        ),
        ott_aliases=("approve", "reject", "duyệt", "từ chối"),
        required_params=("gate_id", "action"),
    ),
    CommandDef(
        name="export_audit",
        description="Export audit log for a project",
        params=ExportAuditParams,
        permission="governance:read",
        handler="audit_service.export_audit",
        cli_name="export-audit",
        ott_description=(
            "Export audit log for a project. "
            "Use when user says 'export audit', 'xuất báo cáo', 'compliance report', etc."
        ),
        ott_aliases=("export audit", "xuất báo cáo", "compliance report"),
        required_params=("project_id",),
    ),
]

assert len(GOVERNANCE_COMMANDS) <= MAX_COMMANDS, (
    f"Registry exceeds {MAX_COMMANDS} command limit "
    f"(has {len(GOVERNANCE_COMMANDS)})"
)


# ============================================================================
# Public API
# ============================================================================


def get_commands() -> list[CommandDef]:
    """Return all registered governance commands."""
    return list(GOVERNANCE_COMMANDS)


def get_command(name: str) -> CommandDef | None:
    """Look up a command by canonical name."""
    for cmd in GOVERNANCE_COMMANDS:
        if cmd.name == name:
            return cmd
    return None


def to_tool_schemas() -> dict[str, type[BaseModel]]:
    """Generate ToolName → Pydantic model mapping (replaces _TOOL_SCHEMAS).

    Used by chat_command_router.py for Pydantic validation of LLM tool calls.
    """
    return {cmd.name: cmd.params for cmd in GOVERNANCE_COMMANDS}


def to_ollama_tools() -> list[dict[str, Any]]:
    """Generate Ollama /api/chat tool definitions (replaces OLLAMA_TOOLS).

    Produces JSON Schema format compatible with Ollama's function calling.
    """
    tools: list[dict[str, Any]] = []
    for cmd in GOVERNANCE_COMMANDS:
        schema = cmd.params.model_json_schema()
        properties: dict[str, Any] = {}
        for prop_name, prop_schema in schema.get("properties", {}).items():
            prop_def: dict[str, Any] = {}
            # Map JSON Schema types
            if "type" in prop_schema:
                prop_def["type"] = prop_schema["type"]
            elif "anyOf" in prop_schema:
                # Optional fields: pick the non-null type
                for variant in prop_schema["anyOf"]:
                    if variant.get("type") != "null":
                        prop_def.update(variant)
                        break
            if "format" in prop_schema:
                prop_def["format"] = prop_schema["format"]
            if "enum" in prop_schema:
                prop_def["enum"] = prop_schema["enum"]
            if "description" in prop_schema:
                prop_def["description"] = prop_schema["description"]
            elif prop_name in ("description",):
                prop_def["description"] = f"{prop_name.replace('_', ' ').title()}"
            properties[prop_name] = prop_def

        tools.append({
            "type": "function",
            "function": {
                "name": cmd.name,
                "description": cmd.ott_description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": list(cmd.required_params),
                },
            },
        })
    return tools
