---
sdlc_version: "6.1.0"
document_type: "Functional Requirement"
status: "PROPOSED"
sprint: "176"
spec_id: "FR-038"
tier: "PROFESSIONAL"
stage: "01 - Planning"
---

# FR-038: Agent Delegation and Tool Restriction

**Version**: 1.0.0
**Status**: PROPOSED
**Created**: February 2026
**Sprint**: 176-177
**Framework**: SDLC 6.1.0
**Epic**: EP-07 Multi-Agent Team Engine
**ADR**: ADR-056 (Non-Negotiable #6: Tool-Level Workspace Restriction)
**Owner**: Backend Team

---

## 1. Overview

### 1.1 Purpose

Implement agent delegation with depth-limited chains and tool-level permission control. Prevents infinite delegation, enforces workspace boundaries, and restricts subagent capabilities.

### 1.2 Business Value

- Prevents infinite agent spawning chains (security critical)
- Enables least-privilege tool access per agent role
- Restricts file system access to project workspace
- Supports ADR-055 Initializer → Coder → Reviewer flow

---

## 2. Functional Requirements

### 2.1 Tool Permission Checking

**GIVEN** an agent definition with `allowed_tools`, `denied_tools`, and `allowed_paths`
**WHEN** the agent attempts to use a tool
**THEN** the system SHALL:
1. Check `denied_tools` first — if tool is in deny list, REJECT
2. Check `allowed_tools` — if `["*"]`, allow all; otherwise tool must be in list
3. For file operations, check `allowed_paths` — file path must start with an allowed prefix

### 2.2 Spawn Permission

**GIVEN** an agent with `can_spawn_subagent = false`
**WHEN** the agent attempts to use `spawn_agent` tool
**THEN** the system SHALL reject with `(False, "no spawn permission")`

**GIVEN** an agent with `can_spawn_subagent = true` and `delegation_depth < max_delegation_depth`
**WHEN** the agent attempts to use `spawn_agent` tool
**THEN** the system SHALL allow the spawn

### 2.3 Subagent Restrictions (Nanobot N2)

**GIVEN** a spawned subagent
**THEN** the subagent SHALL have:
- `denied_tools = ["spawn_agent", "send_message"]` (cannot spawn further or message users)
- `max_delegation_depth` inherited from parent but decremented
- `allowed_paths` inherited from parent (no broader access)

### 2.4 Shell Command Guard (Non-Negotiable #5)

**GIVEN** an agent attempts to execute a shell command
**WHEN** the command matches any of 8 deny patterns:
- recursive_delete (`rm -rf /`)
- fork_bomb (`:(){ :|:& };:`)
- system_control (`shutdown`, `reboot`, `halt`)
- disk_operations (`mkfs`, `fdisk`, `dd if=`)
- raw_disk_write (`> /dev/sd`)
- unsafe_permissions (`chmod 777`)
- pipe_to_shell (`curl | bash`)
- eval_injection (`eval(`)

**THEN** the system SHALL block the command and log a security warning

### 2.5 Path Traversal Detection

**GIVEN** a shell command containing `..`
**THEN** the system SHALL block the command as path traversal

### 2.6 Output Truncation

**GIVEN** a shell command produces output > 10KB
**THEN** the system SHALL truncate to 10KB with a notice appended

---

## 3. Test Coverage

| Test ID | Description | Non-Negotiable |
|---------|-------------|---------------|
| TC-01 to TC-09 | Tool context permission tests | #6 |
| SG-01 to SG-11 | Shell guard tests | #5 |
| CL-10 to CL-13 | Delegation depth tests | #6 |

---

## 4. Dependencies

- `ToolContext` class (`tool_context.py`)
- `ShellGuard` class (`shell_guard.py`)
- `ConversationLimits.check_delegation_depth()` (`conversation_limits.py`)
