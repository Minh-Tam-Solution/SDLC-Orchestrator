---
sdlc_version: "6.1.0"
document_type: "Functional Requirement"
status: "PROPOSED"
sprint: "179"
spec_id: "FR-043"
tier: "PROFESSIONAL"
stage: "01 - Planning"
---

# FR-043: Environment Variable Scrubbing for Shell Execution

**Version**: 1.0.0
**Status**: PROPOSED
**Created**: February 2026
**Sprint**: 179
**Framework**: SDLC 6.1.0
**Epic**: EP-07 Multi-Agent Team Engine
**ADR**: ADR-058 (ZeroClaw Pattern C)
**Owner**: Backend Team
**Source**: ZeroClaw `src/tools/shell.rs` -> `env_clear()` + `SAFE_ENV_VARS` allowlist

---

## 1. Overview

### 1.1 Purpose

Clear environment variables before agent shell execution, injecting only safe variables from an explicit allowlist. Prevents `echo $API_KEY` and similar env exfiltration attacks by agents executing shell tools.

### 1.2 Business Value

- Prevents environment variable leakage (agent runs `env` or `printenv` -> secrets in tool output)
- Defense-in-depth: Complements `ShellGuard` command deny patterns (blocks dangerous COMMANDS) with env scrubbing (blocks env LEAKAGE)
- Vietnamese locale support: `LC_ALL` in allowlist ensures UTF-8 handling for Vietnamese content
- Compliance: CWE-200 mitigation

---

## 2. Functional Requirements

### 2.1 Safe Environment Variable Allowlist

**GIVEN** an agent requests shell command execution
**WHEN** `ShellGuard.scrub_environment()` is called
**THEN** the system SHALL return a dict containing ONLY these 9 safe environment variables:
1. `PATH` -- required for command resolution
2. `HOME` -- required for `~` expansion
3. `LANG` -- locale setting
4. `LC_ALL` -- full locale override (CTO amendment: Vietnamese UTF-8)
5. `TZ` -- timezone
6. `TERM` -- terminal type
7. `USER` -- current user
8. `SHELL` -- shell binary path
9. `TMPDIR` -- temporary file location

**AND** all other environment variables SHALL be excluded (cleared)

### 2.2 Integration with ShellGuard

**GIVEN** the `ShellGuard` class already provides `check_command()` and `truncate_output()`
**WHEN** `scrub_environment()` is added as a new method
**THEN** callers SHALL use the returned safe env dict as `subprocess.Popen(env=safe_env)`

### 2.3 Missing Variables

**GIVEN** a safe variable (e.g., `TMPDIR`) is not set in the host environment
**WHEN** `scrub_environment()` builds the safe env dict
**THEN** that variable SHALL be omitted (not set to empty string)

---

## 3. Test Coverage

| Test ID | Description | Reference |
|---------|-------------|-----------|
| ES-01 | Only safe vars returned from full host env | ADR-058 S2 |
| ES-02 | Secrets excluded (API_KEY, SECRET, etc.) | ADR-058 S2 |
| ES-03 | LC_ALL included when set in host | ADR-058 S2 |
| ES-04 | Missing var omitted (not empty string) | ADR-058 S2 |
| ES-05 | PATH preserved with exact value | ADR-058 S2 |
| ES-06 | Empty env returns empty dict | ADR-058 S2 |

---

## 4. Dependencies

- `ShellGuard` class (`shell_guard.py`, modified -- add `scrub_environment()` method)
- ZeroClaw source: `src/tools/shell.rs` -> `env_clear()`, `SAFE_ENV_VARS`
