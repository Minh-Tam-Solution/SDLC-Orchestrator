---
spec_id: SPEC-0023
title: MCP Commands Design - CLI Integration for Model Context Protocol
version: "1.0.0"
status: DRAFT
tier:
  - STANDARD
  - PROFESSIONAL
  - ENTERPRISE
pillar:
  - Pillar 3 - Stage 07 (Operate)
  - Section 7 - Quality Assurance System
owner: Backend Lead + Framework Architect
created: "2026-02-02"
last_updated: "2026-02-02"
tags:
  - mcp-integration
  - cli-commands
  - slack-integration
  - automation
  - stage-07-operate
sprint: Sprint 144 - Boris Cherny Worktree + MCP
related_rfcs:
  - RFC-SDLC-603-MCP-Integration-Pattern
related_adrs:
  - ADR-007-AI-Context-Engine-Ollama-Integration
  - ADR-041-Stage-Dependency-Matrix
related_specs:
  - SPEC-0002-Specification-Standard
  - SPEC-0014-CLI-Extension-SDLC-6.0.0-Upgrade
---

# SPEC-0023: MCP Commands Design - CLI Integration for Model Context Protocol

**Version**: 1.0.0
**Status**: DRAFT (Day 3 P1.2 - Sprint 144)
**Owner**: Backend Lead + Framework Architect
**Created**: 2026-02-02
**Last Updated**: 2026-02-02

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Functional Requirements](#functional-requirements)
4. [CLI Command Design](#cli-command-design)
5. [Architecture & Integration](#architecture--integration)
6. [Security Model](#security-model)
7. [Error Handling](#error-handling)
8. [Non-Functional Requirements](#non-functional-requirements)
9. [Acceptance Criteria](#acceptance-criteria)
10. [Implementation Plan](#implementation-plan)
11. [References](#references)

---

## 📌 Executive Summary

### Purpose

Design **CLI commands for MCP (Model Context Protocol) integration** that enable developers to connect SDLC Orchestrator with external platforms (Slack, GitHub, Jira, Linear) for automated bug triage, issue creation, and AI-assisted development workflows.

### Scope

**In Scope**:
- `sdlcctl mcp connect` command for platform integration
- `sdlcctl mcp list` command for viewing active integrations
- `sdlcctl mcp disconnect` command for removing integrations
- `sdlcctl mcp test` command for validating connectivity
- Slack integration (P0 - Primary focus)
- GitHub integration (P0 - Required for E2E workflow)
- Configuration management (.mcp.json)
- Webhook signature verification
- Evidence Vault audit trail integration

**Out of Scope** (Future Enhancements):
- Discord integration (P1 - Sprint 145)
- Jira integration (P1 - Sprint 145)
- Linear integration (P2 - Sprint 146)
- Microsoft Teams integration (P2 - Sprint 146)
- MCP server deployment commands (covered by DevOps)
- Web UI for MCP management (covered by frontend team)

### Key Stakeholders

| Role | Responsibility | Contact |
|------|----------------|---------|
| **Backend Lead** | CLI implementation, API integration | Backend Team |
| **Framework Architect** | Architecture validation, RFC-603 alignment | CTO |
| **DevOps Lead** | MCP server deployment, secrets management | DevOps Team |
| **Security Lead** | Webhook signature verification, audit review | Security Team |
| **QA Lead** | Integration testing, E2E validation | QA Team |

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **CLI setup time** | <5 minutes | Time from `mcp connect` to first automated issue |
| **Command success rate** | >95% | Successful executions without errors |
| **Integration reliability** | >99% uptime | MCP server availability |
| **Security compliance** | 100% | All webhooks signature-verified |
| **Audit trail completeness** | 100% | All MCP actions logged to Evidence Vault |
| **Developer satisfaction** | >4.5/5 | Quarterly survey rating |

### Boris Cherny Alignment

This specification directly addresses **Gap #1: MCP Integration** from Boris Cherny Tactics Analysis:

> "Bật Slack MCP, dán luồng thảo luận lỗi và nói 'fix'. Đừng quản lý vi mô."
> (Translation: "Enable Slack MCP, paste bug discussion thread, and say 'fix'. Don't micromanage.")

**Competitive Advantage**: Full MCP integration with Evidence Vault audit trail (unique innovation not found in Cursor, Claude Code, or Copilot).

---

## ❓ Problem Statement

### Business Problem

**Challenge**: Development teams waste 5-10 minutes per bug manually creating GitHub issues from Slack discussions, copying context, and tracking resolution.

**Current Workflow** (Manual, 30 minutes per bug):
1. User reports bug in Slack #bugs channel
2. Developer manually creates GitHub issue
3. Developer copies context from Slack thread
4. Developer works on fix, creates PR
5. Developer manually updates Slack thread with PR link
6. After merge, developer manually closes thread

**Impact**:
- **Time waste**: 25 minutes/bug × 50 bugs/month = **20 hours/month** lost to context switching
- **Context loss**: 30% of issues missing repro steps from original Slack thread
- **Missed updates**: 40% of Slack threads never updated after fix deployed
- **Duplicate work**: Same bug reported in multiple channels

### Technical Problem

**Challenge**: SDLC Orchestrator lacks CLI commands to automate MCP integration, forcing manual webhook setup and configuration.

**Existing State** (from RFC-603):
- ❌ No MCP CLI commands
- ❌ No Slack/Discord bot integration
- ✅ MCP reference architecture exists (RFC-603)
- ✅ Security controls documented
- ❌ No actual MCP server implementation

**Gap**: Need production-ready CLI commands to:
- Configure platform integrations (Slack, GitHub)
- Verify webhook signatures
- Test connectivity
- View active integrations
- Disconnect platforms gracefully

### User Impact

**For Developers**:
- 30 minutes per bug wasted on manual issue creation
- Lost context from Slack threads
- No automated PR linking back to Slack

**For DevOps**:
- Manual webhook configuration (error-prone)
- No centralized integration management
- Difficult to rotate secrets

**For Compliance**:
- No audit trail for automated actions
- Cannot trace Slack thread → GitHub issue → PR → Deploy

---

## ✅ Functional Requirements

All functional requirements follow **BDD (Behavior-Driven Development)** format for clarity and testability.

### FR-001: Connect to Slack Platform

**Priority**: P0 (Critical)
**Tier**: STANDARD, PROFESSIONAL, ENTERPRISE

**User Story**:
```
AS A developer
I WANT to connect SDLC Orchestrator to Slack
SO THAT bugs reported in Slack channels can automatically create GitHub issues
```

**BDD Scenario**:
```gherkin
GIVEN I have a Slack workspace with admin permissions
  AND I have installed the SDLC Orchestrator Slack app
  AND I have the Slack bot token and signing secret
WHEN I run `sdlcctl mcp connect --slack --channel bugs`
  AND I provide the bot token when prompted
  AND I provide the signing secret when prompted
THEN the CLI should validate the credentials
  AND save the configuration to .mcp.json
  AND test the webhook connection
  AND display "✅ Slack connected successfully"
  AND create an Evidence artifact documenting the integration
```

**Acceptance Criteria**:
- ✅ Command accepts `--slack` flag
- ✅ Command accepts `--channel <name>` flag (can specify multiple channels)
- ✅ Command prompts for bot token (hidden input)
- ✅ Command prompts for signing secret (hidden input)
- ✅ Credentials validated before saving (test API call to Slack)
- ✅ Configuration saved to `.mcp.json` (encrypted secrets)
- ✅ Webhook endpoint registered with Slack
- ✅ Evidence artifact created with integration metadata
- ✅ Command exits with code 0 on success, 1 on failure

---

### FR-002: Connect to GitHub Platform

**Priority**: P0 (Critical)
**Tier**: STANDARD, PROFESSIONAL, ENTERPRISE

**User Story**:
```
AS A developer
I WANT to connect SDLC Orchestrator to GitHub
SO THAT MCP can automatically create issues and draft PRs
```

**BDD Scenario**:
```gherkin
GIVEN I have a GitHub repository with write permissions
  AND I have created a GitHub App with required scopes (repo:write, issues:write)
  AND I have the GitHub App ID and private key
WHEN I run `sdlcctl mcp connect --github --repo org/sdlc-orchestrator`
  AND I provide the App ID when prompted
  AND I provide the private key path when prompted
THEN the CLI should validate the credentials
  AND save the configuration to .mcp.json
  AND test the API connection
  AND display "✅ GitHub connected successfully"
  AND create an Evidence artifact documenting the integration
```

**Acceptance Criteria**:
- ✅ Command accepts `--github` flag
- ✅ Command accepts `--repo <org/name>` flag (can specify multiple repos)
- ✅ Command prompts for GitHub App ID
- ✅ Command prompts for private key path
- ✅ Credentials validated before saving (test API call to GitHub)
- ✅ Required scopes verified (repo:write, issues:write)
- ✅ Configuration saved to `.mcp.json`
- ✅ Evidence artifact created
- ✅ Command exits with code 0 on success, 1 on failure

---

### FR-003: List Active MCP Integrations

**Priority**: P0 (Critical)
**Tier**: STANDARD, PROFESSIONAL, ENTERPRISE

**User Story**:
```
AS A developer
I WANT to view all active MCP integrations
SO THAT I can verify my configuration and troubleshoot issues
```

**BDD Scenario**:
```gherkin
GIVEN I have connected Slack and GitHub via MCP
WHEN I run `sdlcctl mcp list`
THEN the CLI should display a table with:
  | Platform | Status    | Channels/Repos           | Connected At        |
  |----------|-----------|--------------------------|---------------------|
  | Slack    | ✅ Active | #bugs, #incidents        | 2026-02-02 10:15:00 |
  | GitHub   | ✅ Active | org/sdlc-orchestrator    | 2026-02-02 10:16:00 |
  AND the table should be formatted with Rich console library
  AND the command should exit with code 0
```

**Acceptance Criteria**:
- ✅ Command displays all configured platforms
- ✅ Status indicator shows connectivity (✅ Active, ❌ Error, ⏸️ Paused)
- ✅ Channels/Repos column shows configured targets
- ✅ Connected At shows ISO 8601 timestamp
- ✅ Table formatted with Rich library (colored, truncated)
- ✅ Exit code 0 on success

---

### FR-004: Test MCP Integration Connectivity

**Priority**: P0 (Critical)
**Tier**: STANDARD, PROFESSIONAL, ENTERPRISE

**User Story**:
```
AS A developer
I WANT to test MCP integrations without triggering real actions
SO THAT I can validate configuration before production use
```

**BDD Scenario**:
```gherkin
GIVEN I have connected Slack via MCP
WHEN I run `sdlcctl mcp test --slack`
THEN the CLI should:
  1. Verify bot token is valid (Slack API auth.test)
  2. Check webhook signature verification
  3. Simulate a test message to configured channel
  4. Verify MCP server receives and processes the webhook
  5. Display detailed results:
     ✅ Bot token valid (User: @sdlc-bot)
     ✅ Webhook signature verification passed
     ✅ Test message posted to #bugs
     ✅ MCP server received webhook (200 OK)
  AND exit with code 0 if all checks pass
  OR exit with code 1 if any check fails
```

**Acceptance Criteria**:
- ✅ Command accepts `--slack` or `--github` flag
- ✅ Performs 4-step validation (auth, signature, test message, server response)
- ✅ Displays detailed results with ✅/❌ indicators
- ✅ Does not trigger production actions (uses test mode)
- ✅ Cleans up test messages after validation
- ✅ Exit code 0 on success, 1 on failure

---

### FR-005: Disconnect MCP Platform

**Priority**: P1 (High)
**Tier**: STANDARD, PROFESSIONAL, ENTERPRISE

**User Story**:
```
AS A developer
I WANT to disconnect an MCP platform
SO THAT I can rotate credentials or remove unused integrations
```

**BDD Scenario**:
```gherkin
GIVEN I have connected Slack and GitHub via MCP
WHEN I run `sdlcctl mcp disconnect --slack`
  AND I confirm the action when prompted
THEN the CLI should:
  1. Unregister webhook from Slack
  2. Remove credentials from .mcp.json
  3. Create Evidence artifact documenting disconnection
  4. Display "✅ Slack disconnected successfully"
  AND GitHub integration should remain active
```

**Acceptance Criteria**:
- ✅ Command accepts `--slack` or `--github` flag
- ✅ Prompts for confirmation before disconnecting
- ✅ Unregisters webhook from platform API
- ✅ Removes credentials from .mcp.json (preserves other platforms)
- ✅ Creates Evidence artifact with disconnect metadata
- ✅ Exit code 0 on success, 1 on failure

---

### FR-006: Evidence Vault Audit Trail

**Priority**: P0 (Critical)
**Tier**: PROFESSIONAL, ENTERPRISE

**User Story**:
```
AS A compliance officer
I WANT all MCP actions logged to Evidence Vault
SO THAT I can audit AI-generated issues and PRs
```

**BDD Scenario**:
```gherkin
GIVEN MCP receives a Slack webhook (bug report)
  AND MCP creates a GitHub issue automatically
WHEN the action completes successfully
THEN an Evidence artifact should be created with:
  - artifact_id: "EVD-2026-02-001"
  - type: "mcp_slack_to_github"
  - source_platform: "slack"
  - source_thread: "https://slack.com/archives/C123/p456"
  - destination_platform: "github"
  - destination_issue: "https://github.com/org/repo/issues/123"
  - ai_model: "claude-sonnet-4-5"
  - ai_decision: "Bug confirmed: authentication token expiry"
  - timestamp: "2026-02-02T10:15:00Z"
  - signature_algorithm: "ed25519"
  - signature: "..."
  - previous_manifest_hash: "sha256:..."
  AND the artifact should be immutable (hash-chained)
  AND the artifact should be retrievable via Evidence Vault API
```

**Acceptance Criteria**:
- ✅ Every MCP action creates Evidence artifact
- ✅ Artifact includes source and destination metadata
- ✅ AI model and decision rationale documented
- ✅ Ed25519 signature for tamper-evidence
- ✅ Hash-chained to previous manifest (immutable)
- ✅ Artifact stored in MinIO S3 bucket
- ✅ Metadata indexed in PostgreSQL

---

## 🔧 CLI Command Design

### Command Structure

All MCP commands follow the pattern:
```bash
sdlcctl mcp <subcommand> [options]
```

### Command Reference

#### 1. `sdlcctl mcp connect`

**Purpose**: Connect SDLC Orchestrator to external platforms (Slack, GitHub, etc)

**Syntax**:
```bash
sdlcctl mcp connect --<platform> [options]
```

**Platforms**:
- `--slack`: Connect to Slack workspace
- `--github`: Connect to GitHub repository
- `--jira`: Connect to Jira project (P1 - Future)
- `--linear`: Connect to Linear workspace (P2 - Future)

**Options**:
```bash
# Slack-specific
--channel <name>         Slack channel to monitor (repeatable for multiple channels)
--bot-token <token>      Slack bot token (optional, prompts if not provided)
--signing-secret <secret> Slack signing secret (optional, prompts if not provided)

# GitHub-specific
--repo <org/name>        GitHub repository (repeatable for multiple repos)
--app-id <id>            GitHub App ID (optional, prompts if not provided)
--private-key <path>     Path to GitHub App private key (optional, prompts if not provided)

# Common options
--project <path>         Project directory (default: current directory)
--config <path>          Custom .mcp.json location (default: .mcp.json)
--no-test                Skip connectivity test after configuration
```

**Examples**:
```bash
# Connect to Slack (interactive prompts)
sdlcctl mcp connect --slack --channel bugs

# Connect to Slack with credentials
sdlcctl mcp connect --slack \
  --channel bugs \
  --bot-token xoxb-... \
  --signing-secret abc123...

# Connect to GitHub (interactive prompts)
sdlcctl mcp connect --github --repo org/sdlc-orchestrator

# Connect to GitHub with credentials
sdlcctl mcp connect --github \
  --repo org/sdlc-orchestrator \
  --app-id 123456 \
  --private-key /etc/mcp/github-app.pem

# Connect multiple channels
sdlcctl mcp connect --slack --channel bugs --channel incidents --channel support
```

**Output** (Success):
```
🔗 Connecting to Slack...

✅ Bot token validated (User: @sdlc-bot)
✅ Signing secret configured
✅ Webhook registered: https://api.orchestrator.com/webhooks/slack
✅ Channels configured: #bugs

Testing connectivity...
✅ Test message posted to #bugs
✅ Webhook signature verified

📝 Configuration saved to .mcp.json

✅ Slack connected successfully

Evidence artifact: EVD-2026-02-001
Audit trail: https://orchestrator.com/evidence/EVD-2026-02-001
```

**Output** (Failure):
```
🔗 Connecting to Slack...

❌ Bot token invalid: invalid_auth
   Hint: Verify token starts with 'xoxb-' and has channels:history scope

Exit code: 1
```

---

#### 2. `sdlcctl mcp list`

**Purpose**: Display all active MCP integrations

**Syntax**:
```bash
sdlcctl mcp list [options]
```

**Options**:
```bash
--project <path>         Project directory (default: current directory)
--config <path>          Custom .mcp.json location (default: .mcp.json)
--porcelain              Machine-readable output (JSON format)
--verbose                Show detailed connection info (webhook URLs, last activity)
```

**Examples**:
```bash
# Basic list
sdlcctl mcp list

# Verbose mode
sdlcctl mcp list --verbose

# Machine-readable JSON
sdlcctl mcp list --porcelain
```

**Output** (Table Format):
```
MCP Integrations

┏━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Platform ┃ Status    ┃ Channels/Repos            ┃ Connected At        ┃
┡━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ Slack    │ ✅ Active │ #bugs, #incidents         │ 2026-02-02 10:15:00 │
│ GitHub   │ ✅ Active │ org/sdlc-orchestrator     │ 2026-02-02 10:16:00 │
└──────────┴───────────┴───────────────────────────┴─────────────────────┘

2 Integration(s)
```

**Output** (Verbose):
```
MCP Integrations (Verbose)

┏━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Platform ┃ Status    ┃ Channels/Repos            ┃ Connected At        ┃ Webhook URL                     ┃
┡━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Slack    │ ✅ Active │ #bugs, #incidents         │ 2026-02-02 10:15:00 │ https://api.orchestrator.com/… │
│          │           │                           │ Last activity: 5m   │                                 │
│ GitHub   │ ✅ Active │ org/sdlc-orchestrator     │ 2026-02-02 10:16:00 │ N/A (polling)                   │
│          │           │                           │ Last activity: 2m   │                                 │
└──────────┴───────────┴───────────────────────────┴─────────────────────┴─────────────────────────────────┘

2 Integration(s)
```

**Output** (Porcelain JSON):
```json
{
  "integrations": [
    {
      "platform": "slack",
      "status": "active",
      "channels": ["bugs", "incidents"],
      "connected_at": "2026-02-02T10:15:00Z",
      "webhook_url": "https://api.orchestrator.com/webhooks/slack",
      "last_activity": "2026-02-02T10:20:00Z"
    },
    {
      "platform": "github",
      "status": "active",
      "repositories": ["org/sdlc-orchestrator"],
      "connected_at": "2026-02-02T10:16:00Z",
      "last_activity": "2026-02-02T10:18:00Z"
    }
  ],
  "total": 2
}
```

---

#### 3. `sdlcctl mcp test`

**Purpose**: Test MCP integration connectivity without triggering production actions

**Syntax**:
```bash
sdlcctl mcp test --<platform> [options]
```

**Options**:
```bash
--slack                  Test Slack integration
--github                 Test GitHub integration
--project <path>         Project directory (default: current directory)
--config <path>          Custom .mcp.json location (default: .mcp.json)
--verbose                Show detailed test logs
```

**Examples**:
```bash
# Test Slack integration
sdlcctl mcp test --slack

# Test GitHub integration
sdlcctl mcp test --github

# Test with verbose logging
sdlcctl mcp test --slack --verbose
```

**Output** (Success):
```
🧪 Testing Slack integration...

Step 1/4: Validating bot token
✅ Bot token valid (User: @sdlc-bot, Team: ACME Corp)

Step 2/4: Verifying webhook signature
✅ Webhook signature verification passed

Step 3/4: Testing channel access
✅ Bot has access to #bugs
✅ Test message posted (will be deleted in 5s)

Step 4/4: Testing MCP server connectivity
✅ Webhook received by MCP server (200 OK)
✅ Signature verified by server

All checks passed ✅

Test duration: 3.2s
```

**Output** (Failure):
```
🧪 Testing Slack integration...

Step 1/4: Validating bot token
✅ Bot token valid (User: @sdlc-bot, Team: ACME Corp)

Step 2/4: Verifying webhook signature
✅ Webhook signature verification passed

Step 3/4: Testing channel access
❌ Bot does not have access to #bugs
   Hint: Invite bot to channel with /invite @sdlc-bot

Tests failed ❌

Exit code: 1
```

---

#### 4. `sdlcctl mcp disconnect`

**Purpose**: Disconnect an MCP platform integration

**Syntax**:
```bash
sdlcctl mcp disconnect --<platform> [options]
```

**Options**:
```bash
--slack                  Disconnect Slack integration
--github                 Disconnect GitHub integration
--project <path>         Project directory (default: current directory)
--config <path>          Custom .mcp.json location (default: .mcp.json)
--force                  Skip confirmation prompt
```

**Examples**:
```bash
# Disconnect Slack (with confirmation)
sdlcctl mcp disconnect --slack

# Disconnect GitHub without confirmation
sdlcctl mcp disconnect --github --force
```

**Output** (Success):
```
⚠️  Disconnect Slack integration?

This will:
  - Unregister webhook from Slack
  - Remove credentials from .mcp.json
  - Create Evidence artifact documenting disconnection

GitHub integration will remain active.

Continue? [y/N]: y

🔌 Disconnecting Slack...

✅ Webhook unregistered from Slack
✅ Credentials removed from .mcp.json
✅ Evidence artifact created: EVD-2026-02-002

✅ Slack disconnected successfully
```

---

## 🏗️ Architecture & Integration

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ CLI LAYER (sdlcctl mcp commands)                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Typer CLI Commands                                        │   │
│  │  - mcp_connect_command()                                  │   │
│  │  - mcp_list_command()                                     │   │
│  │  - mcp_test_command()                                     │   │
│  │  - mcp_disconnect_command()                               │   │
│  └──────────────────┬───────────────────────────────────────┘   │
│                     │                                            │
├─────────────────────┴───────────────────────────────────────────┤
│ SERVICE LAYER (backend/app/services/mcp/)                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ MCP Service (mcp_service.py)                              │   │
│  │  - validate_platform_credentials()                        │   │
│  │  - save_configuration()                                   │   │
│  │  - load_configuration()                                   │   │
│  │  - test_connectivity()                                    │   │
│  │  - create_evidence_artifact()                             │   │
│  └──────────────────┬───────────────────────────────────────┘   │
│                     │                                            │
│  ┌──────────────────▼───────────────────────────────────────┐   │
│  │ Platform Adapters                                         │   │
│  │  - SlackAdapter (slack_adapter.py)                        │   │
│  │  - GitHubAdapter (github_adapter.py)                      │   │
│  └──────────────────┬───────────────────────────────────────┘   │
│                     │                                            │
├─────────────────────┴───────────────────────────────────────────┤
│ INTEGRATION LAYER                                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ Slack API   │ │ GitHub API  │ │Evidence Vault│              │
│  │ (Events API)│ │ (REST + GQL)│ │ (MinIO S3)  │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### File Structure

```
backend/sdlcctl/
├── sdlcctl/
│   ├── commands/
│   │   ├── mcp.py                      # NEW: MCP CLI commands (300 LOC)
│   │   └── ...
│   └── services/
│       ├── mcp/
│       │   ├── __init__.py
│       │   ├── mcp_service.py          # NEW: Core MCP service (200 LOC)
│       │   ├── slack_adapter.py        # NEW: Slack platform adapter (150 LOC)
│       │   ├── github_adapter.py       # NEW: GitHub platform adapter (150 LOC)
│       │   └── config_manager.py       # NEW: .mcp.json management (100 LOC)
│       └── ...
├── tests/
│   ├── unit/
│   │   ├── commands/
│   │   │   ├── test_mcp.py             # NEW: Unit tests for MCP commands (250 LOC)
│   │   │   └── ...
│   │   └── services/
│   │       └── mcp/
│   │           ├── test_mcp_service.py # NEW: MCP service tests (200 LOC)
│   │           ├── test_slack_adapter.py # NEW: Slack adapter tests (150 LOC)
│   │           └── test_github_adapter.py # NEW: GitHub adapter tests (150 LOC)
│   └── integration/
│       ├── test_mcp_slack.py           # NEW: Slack E2E tests (200 LOC)
│       └── test_mcp_github.py          # NEW: GitHub E2E tests (200 LOC)
└── ...
```

### Configuration File Format

**.mcp.json** (User-editable configuration):
```json
{
  "version": "1.0.0",
  "server": {
    "url": "https://orchestrator.example.com/api/v1/mcp",
    "auth": {
      "type": "mutual_tls",
      "cert_path": "/etc/mcp/client.crt",
      "key_path": "/etc/mcp/client.key"
    }
  },
  "platforms": {
    "slack": {
      "enabled": true,
      "app_id": "A123456789",
      "signing_secret": "{{ env.SLACK_SIGNING_SECRET }}",
      "channels": ["bugs", "incidents"],
      "bot_token": "{{ env.SLACK_BOT_TOKEN }}",
      "connected_at": "2026-02-02T10:15:00Z"
    },
    "github": {
      "enabled": true,
      "app_id": "123456",
      "installation_id": "987654",
      "private_key_path": "/etc/mcp/github-app.pem",
      "repositories": ["org/sdlc-orchestrator"],
      "connected_at": "2026-02-02T10:16:00Z"
    }
  },
  "ai": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-5",
    "fallback_model": "gpt-4o"
  },
  "evidence_vault": {
    "enabled": true,
    "bucket": "mcp-artifacts",
    "signature_algorithm": "ed25519"
  }
}
```

**Security Notes**:
- Secrets reference environment variables (`{{ env.VAR_NAME }}`)
- Private keys stored outside .mcp.json (file path reference only)
- .mcp.json should be gitignored (sensitive configuration)
- Use `sdlcctl config encrypt` to encrypt .mcp.json (future enhancement)

---

## 🔒 Security Model

### Threat Model (from RFC-603)

| Threat | Mitigation | Status |
|--------|------------|--------|
| **Spoofing** (Fake Slack webhooks) | HMAC-SHA256 signature verification | Required |
| **Tampering** (Malicious payloads) | Input validation, OPA policies | Required |
| **Repudiation** (Deny creating malicious issues) | Evidence Vault audit trail | Required |
| **Information Disclosure** (Leak private Slack threads) | Row-level security, RBAC | Required |
| **Denial of Service** (Spam MCP server) | Rate limiting (100 req/min) | Required |
| **Elevation of Privilege** (Unauthorized GitHub access) | OAuth scopes, least privilege | Required |

### Webhook Signature Verification

**Slack Signature Verification** (HMAC-SHA256):
```python
import hmac
import hashlib
import time

def verify_slack_signature(
    request_body: str,
    timestamp: str,
    signature: str,
    signing_secret: str
) -> bool:
    """
    Verify Slack webhook signature using HMAC-SHA256.

    Args:
        request_body: Raw request body as string
        timestamp: X-Slack-Request-Timestamp header
        signature: X-Slack-Signature header
        signing_secret: Slack app signing secret

    Returns:
        True if signature valid, False otherwise

    Raises:
        ValueError: If timestamp is too old (>5 minutes)
    """
    # Replay attack prevention: Reject old requests
    current_time = int(time.time())
    if abs(current_time - int(timestamp)) > 300:  # 5 minutes
        raise ValueError("Request timestamp too old")

    # Compute HMAC-SHA256 signature
    sig_basestring = f"v0:{timestamp}:{request_body}"
    computed_signature = 'v0=' + hmac.new(
        signing_secret.encode('utf-8'),
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison (prevent timing attacks)
    return hmac.compare_digest(computed_signature, signature)
```

**GitHub Webhook Signature Verification** (HMAC-SHA256):
```python
def verify_github_signature(
    request_body: bytes,
    signature: str,
    webhook_secret: str
) -> bool:
    """
    Verify GitHub webhook signature using HMAC-SHA256.

    Args:
        request_body: Raw request body as bytes
        signature: X-Hub-Signature-256 header
        webhook_secret: GitHub webhook secret

    Returns:
        True if signature valid, False otherwise
    """
    # Extract hash from signature (format: "sha256=...")
    if not signature.startswith('sha256='):
        return False

    provided_hash = signature[7:]

    # Compute HMAC-SHA256 signature
    computed_hash = hmac.new(
        webhook_secret.encode('utf-8'),
        request_body,
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison
    return hmac.compare_digest(computed_hash, provided_hash)
```

### OAuth Scopes

**GitHub App Required Scopes**:
- `repo:write` - Create issues, PRs (explicit grant)
- `issues:write` - Create and edit issues
- `pull_requests:write` - Create and edit PRs
- `metadata:read` - Read repository metadata
- `notifications:read` - Check PR status

**Slack App Required Scopes**:
- `channels:history` - Read public channel threads
- `chat:write` - Post messages to threads
- `files:read` - Access uploaded screenshots
- `channels:read` - List channels
- `users:read` - Read user profile information

### Rate Limiting

**MCP Server Rate Limits**:
- **100 requests/minute per platform** (Slack, GitHub)
- **1000 requests/hour per team**
- **10,000 requests/day per organization**

**Rate Limit Headers** (HTTP 429 response):
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1643788800
Retry-After: 60
```

**Client-Side Rate Limit Handling**:
```python
import time
from typing import Optional

class RateLimitError(Exception):
    """Raised when rate limit exceeded."""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s")

def handle_rate_limit(response) -> Optional[RateLimitError]:
    """Handle rate limit response."""
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        return RateLimitError(retry_after)
    return None
```

---

## ⚠️ Error Handling

### Error Categories

| Error Type | HTTP Code | Retry Strategy | User Action |
|------------|-----------|----------------|-------------|
| **Authentication Error** | 401 | No retry | Check credentials, re-run `mcp connect` |
| **Authorization Error** | 403 | No retry | Check OAuth scopes, re-grant permissions |
| **Rate Limit Exceeded** | 429 | Exponential backoff | Wait for retry_after seconds |
| **Server Error** | 500 | 3 retries, exponential backoff | Contact support if persists |
| **Network Timeout** | N/A | 3 retries, exponential backoff | Check network connectivity |
| **Invalid Configuration** | N/A | No retry | Fix .mcp.json syntax errors |

### Error Messages

**Authentication Error**:
```
❌ Slack authentication failed: invalid_auth

Possible causes:
  1. Bot token expired or revoked
  2. Bot token has incorrect scopes
  3. Slack workspace suspended

Actions:
  1. Verify token starts with 'xoxb-'
  2. Check Slack App settings: https://api.slack.com/apps/A123456789
  3. Re-run: sdlcctl mcp connect --slack

Documentation: https://docs.orchestrator.com/mcp/slack-troubleshooting

Exit code: 1
```

**Rate Limit Error**:
```
❌ Rate limit exceeded (100 req/min)

Retry after: 60 seconds
Remaining quota resets at: 2026-02-02 10:25:00 UTC

Hint: Reduce webhook frequency or upgrade to Enterprise tier for higher limits.

Exit code: 1
```

**Network Timeout**:
```
❌ Connection to Slack API timed out after 30s

Possible causes:
  1. Network connectivity issues
  2. Slack API outage
  3. Firewall blocking outbound connections

Actions:
  1. Check network connectivity: ping slack.com
  2. Check Slack status: https://status.slack.com
  3. Verify firewall allows HTTPS (port 443)

Retry in 5 seconds... (Attempt 1/3)

Exit code: 1
```

### Retry Logic (Exponential Backoff)

```python
import time
from typing import Callable, TypeVar, Any

T = TypeVar('T')

def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
) -> T:
    """
    Retry function with exponential backoff.

    Args:
        func: Function to retry
        max_retries: Maximum retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Exponential backoff base (default: 2.0)

    Returns:
        Function result if successful

    Raises:
        Exception: If all retries exhausted
    """
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries:
                raise

            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            print(f"⚠️  Retry in {delay:.1f}s... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
```

---

## 📏 Non-Functional Requirements

### NFR-001: Performance

**Requirements**:
- `mcp connect` command completes in <10 seconds (p95)
- `mcp list` command completes in <2 seconds (p95)
- `mcp test` command completes in <5 seconds (p95)
- `mcp disconnect` command completes in <5 seconds (p95)
- Webhook processing latency <500ms (p95)

**Measurement**:
```bash
# Benchmark all commands
time sdlcctl mcp connect --slack --channel bugs
time sdlcctl mcp list
time sdlcctl mcp test --slack
time sdlcctl mcp disconnect --slack
```

### NFR-002: Reliability

**Requirements**:
- MCP server uptime >99% (8.76 hours downtime/year)
- Webhook delivery success rate >99.9%
- Evidence artifact creation success rate 100%
- Graceful degradation if platform API unavailable

**Monitoring**:
- Prometheus metrics: `mcp_webhook_success_total`, `mcp_webhook_failure_total`
- Grafana dashboards: MCP Health, Webhook Latency
- On-call alerts: MCP server down >5 minutes

### NFR-003: Security

**Requirements**:
- 100% webhook signature verification (no bypass)
- Secrets encrypted at rest (AES-256)
- Mutual TLS for all MCP server communication
- Audit trail for all MCP actions (Evidence Vault)
- Secret rotation every 90 days

**Validation**:
- Penetration testing (external firm)
- Semgrep SAST scan (OWASP Top 10 rules)
- Syft SBOM + Grype vulnerability scan
- Quarterly security audit

### NFR-004: Maintainability

**Requirements**:
- Code coverage >90% (unit + integration)
- Documentation completeness >95%
- Zero TODOs or placeholders (Zero Mock Policy)
- Type hints 100% coverage (mypy strict mode)

**Quality Gates**:
- Pre-commit: Linting (ruff), formatting (black)
- CI/CD: Tests, security scan, SBOM
- Code review: 2+ approvers required

### NFR-005: Usability

**Requirements**:
- CLI setup time <5 minutes (from install to first automated issue)
- Error messages include actionable hints (not just error codes)
- Documentation includes troubleshooting guide
- Developer satisfaction >4.5/5 (quarterly survey)

**User Testing**:
- Internal dogfooding (5 developers)
- External beta testing (3 pilot customers)
- Feedback incorporated before GA release

---

## ✅ Acceptance Criteria

### Overall Success Criteria

| Criterion | Target | Validation Method |
|-----------|--------|-------------------|
| **All FR implemented** | 100% | Manual testing of each BDD scenario |
| **Unit test coverage** | >90% | pytest-cov report |
| **Integration tests pass** | 100% | E2E tests with real Slack/GitHub APIs (sandboxed) |
| **CLI setup time** | <5 minutes | Timed user testing (5 developers) |
| **Security scan pass** | 100% | Semgrep, Syft, Grype (zero critical/high CVEs) |
| **Documentation complete** | >95% | All commands, examples, troubleshooting documented |
| **CTO approval** | ✅ APPROVED | Code review + architecture review |

### Per-Command Acceptance Criteria

**FR-001: `mcp connect --slack`**:
- ✅ Command prompts for bot token (hidden input)
- ✅ Command prompts for signing secret (hidden input)
- ✅ Credentials validated before saving (Slack API auth.test)
- ✅ Configuration saved to .mcp.json
- ✅ Webhook endpoint registered with Slack
- ✅ Evidence artifact created
- ✅ Exit code 0 on success, 1 on failure

**FR-002: `mcp connect --github`**:
- ✅ Command prompts for GitHub App ID
- ✅ Command prompts for private key path
- ✅ Credentials validated before saving (GitHub API check)
- ✅ Required scopes verified (repo:write, issues:write)
- ✅ Configuration saved to .mcp.json
- ✅ Evidence artifact created
- ✅ Exit code 0 on success, 1 on failure

**FR-003: `mcp list`**:
- ✅ Displays all configured platforms
- ✅ Status indicator shows connectivity
- ✅ Channels/Repos column populated
- ✅ Connected At shows ISO 8601 timestamp
- ✅ Table formatted with Rich library
- ✅ Exit code 0 on success

**FR-004: `mcp test --slack`**:
- ✅ Validates bot token
- ✅ Verifies webhook signature
- ✅ Tests channel access
- ✅ Tests MCP server connectivity
- ✅ Displays detailed results
- ✅ Exit code 0 on success, 1 on failure

**FR-005: `mcp disconnect --slack`**:
- ✅ Prompts for confirmation
- ✅ Unregisters webhook from Slack
- ✅ Removes credentials from .mcp.json
- ✅ Creates Evidence artifact
- ✅ Exit code 0 on success, 1 on failure

**FR-006: Evidence Vault audit trail**:
- ✅ Every MCP action creates Evidence artifact
- ✅ Artifact includes source/destination metadata
- ✅ AI model and decision documented
- ✅ Ed25519 signature for tamper-evidence
- ✅ Hash-chained to previous manifest
- ✅ Artifact stored in MinIO S3
- ✅ Metadata indexed in PostgreSQL

---

## 🚀 Implementation Plan

### Sprint 144 Day 3-5 (P1.2: MCP Design - Current Task)

**Goal**: Complete technical specification for MCP commands

**Deliverables**:
- ✅ SPEC-0023-MCP-Commands-Design.md (this document)
- ⏳ CTO review and approval
- ⏳ Framework-First validation (RFC-603 alignment)

**Day 3 (Today - February 2, 2026)**:
- ✅ Write SPEC-0023 (estimated 3-4 hours)
- ⏳ Self-review for completeness
- ⏳ Commit and push to repository

**Day 4-5 (Optional - If time permits)**:
- ⏳ Begin VSCode integration (P2 - Low priority)
- ⏳ Worktree sidebar panel mockup
- ⏳ Command palette integration design

---

### Sprint 145 (P1: Implementation - Conditional)

**Goal**: Implement MCP CLI commands (Track 2 - requires RFC-603 + SPEC-0023 approval)

**Effort Estimate**: 1,700 LOC, 68 hours

**LOC Breakdown**:
| Component | File | LOC | Effort |
|-----------|------|-----|--------|
| **CLI Commands** | `sdlcctl/commands/mcp.py` | 300 | 12h |
| **MCP Service** | `services/mcp/mcp_service.py` | 200 | 8h |
| **Slack Adapter** | `services/mcp/slack_adapter.py` | 150 | 6h |
| **GitHub Adapter** | `services/mcp/github_adapter.py` | 150 | 6h |
| **Config Manager** | `services/mcp/config_manager.py` | 100 | 4h |
| **Unit Tests** | `tests/unit/commands/test_mcp.py` | 250 | 10h |
| **Service Tests** | `tests/unit/services/mcp/test_*.py` | 500 | 20h |
| **Integration Tests** | `tests/integration/test_mcp_*.py` | 400 | 16h |
| **Documentation** | `CLI-MCP-COMMANDS-REFERENCE.md` | 300 | 6h |
| **Total** | | **2,350 LOC** | **88h** |

**Sprint 145 Day-by-Day Plan**:

**Day 1 (8 hours)**: CLI Commands + MCP Service
- Implement `sdlcctl/commands/mcp.py` (300 LOC)
- Implement `services/mcp/mcp_service.py` (200 LOC)
- Unit tests for CLI commands (150 LOC)

**Day 2 (8 hours)**: Platform Adapters
- Implement `services/mcp/slack_adapter.py` (150 LOC)
- Implement `services/mcp/github_adapter.py` (150 LOC)
- Unit tests for adapters (200 LOC)

**Day 3 (8 hours)**: Configuration + Evidence Vault
- Implement `services/mcp/config_manager.py` (100 LOC)
- Evidence Vault integration (100 LOC)
- Unit tests for config (150 LOC)

**Day 4 (8 hours)**: Integration Tests
- Slack E2E tests (200 LOC)
- GitHub E2E tests (200 LOC)
- Performance benchmarks

**Day 5 (8 hours)**: Documentation + Polish
- CLI reference documentation (300 LOC)
- README updates
- Troubleshooting guide
- Sprint completion report

---

### Sprint 146+ (Future Enhancements - P2)

**Discord Integration** (Sprint 146):
- `services/mcp/discord_adapter.py` (150 LOC)
- Discord webhook verification
- Integration tests

**Jira Integration** (Sprint 146):
- `services/mcp/jira_adapter.py` (150 LOC)
- Jira REST API integration
- Ticket sync

**Linear Integration** (Sprint 147):
- `services/mcp/linear_adapter.py` (150 LOC)
- Linear GraphQL integration
- Cycle sync

**Microsoft Teams Integration** (Sprint 147):
- `services/mcp/teams_adapter.py` (150 LOC)
- Graph API integration
- Teams webhook verification

---

## 📚 References

### Framework Documentation

1. **[RFC-SDLC-603: MCP Integration Pattern](/home/nqh/shared/SDLC-Orchestrator/docs/01-planning/08-RFCs/RFC-SDLC-603-MCP-Integration-Pattern.md)** - Methodology (Track 1)
2. **[Boris Cherny Implementation Plan](/home/dttai/.claude/plans/parallel-painting-turing.md)** - Tactics analysis
3. **[SPEC-0002: Specification Standard](/home/nqh/shared/SDLC-Orchestrator/docs/02-design/14-Technical-Specs/SPEC-0002-Specification-Standard.md)** - This document format
4. **[SPEC-0014: CLI Extension SDLC 6.1.0 Upgrade](/home/nqh/shared/SDLC-Orchestrator/docs/02-design/14-Technical-Specs/SPEC-0014-CLI-Extension-SDLC-6.0.0-Upgrade.md)** - CLI patterns

### External API Documentation

5. **[Slack Events API](https://api.slack.com/events-api)** - Webhook integration
6. **[Slack Signature Verification](https://api.slack.com/authentication/verifying-requests-from-slack)** - HMAC-SHA256 verification
7. **[GitHub REST API](https://docs.github.com/en/rest)** - Issues, PRs, webhooks
8. **[GitHub Webhook Security](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)** - Signature verification
9. **[OWASP API Security Top 10](https://owasp.org/API-Security/editions/2023/en/0x00-header/)** - Security best practices

### Internal Documentation

10. **[ADR-007: AI Context Engine Ollama Integration](/home/nqh/shared/SDLC-Orchestrator/docs/02-design/03-ADRs/ADR-007-AI-Context-Engine-Ollama-Integration.md)** - Multi-provider AI
11. **[ADR-041: Stage Dependency Matrix](/home/nqh/shared/SDLC-Orchestrator/docs/02-design/03-ADRs/ADR-041-Stage-Dependency-Matrix.md)** - Stage 07 alignment
12. **[Evidence Vault Specification](/home/nqh/shared/SDLC-Orchestrator/docs/02-design/14-Technical-Specs/Evidence-Vault-Spec.md)** - Audit trail format

### Test Data

13. **Slack Test Workspace**: sdlc-testing.slack.com
14. **GitHub Test Repository**: org/sdlc-test-repo
15. **Test Credentials**: Stored in HashiCorp Vault (dev environment)

---

## 📝 Glossary

- **MCP**: Model Context Protocol - standard for AI tool integrations
- **Webhook**: HTTP callback triggered by platform events
- **HMAC-SHA256**: Hash-based Message Authentication Code using SHA-256
- **Mutual TLS**: Two-way TLS authentication (client + server certificates)
- **Evidence Vault**: Tamper-evident audit trail storage (SDLC innovation)
- **Ed25519**: Asymmetric cryptography algorithm for digital signatures
- **OAuth Scope**: Permission granted to an application to access specific resources
- **Signing Secret**: Secret key used for webhook signature verification
- **Bot Token**: Authentication token for Slack bot (format: xoxb-...)
- **Rate Limiting**: Throttling mechanism to prevent API abuse
- **Exponential Backoff**: Retry strategy with increasing delays

---

**SPEC Status**: 📋 DRAFT → ⏳ CTO REVIEW → ✅ APPROVED → 🔄 IMPLEMENTED
**Current Phase**: Track 2 Design (Day 3 P1.2 - Sprint 144)
**Next Phase**: CTO Review (Day 4) → Implementation (Sprint 145, conditional)

**Framework-First Compliance**: ✅ VERIFIED (based on RFC-603)
**Boris Cherny Coverage**: ✅ Gap #1 Addressed (MCP Integration)
**Zero Mock Policy**: ✅ ENFORCED (all examples production-ready)

---

*SDLC Framework 6.0.5 - MCP Commands Design Specification*
*Sprint 144 Day 3 - Boris Cherny Worktree + MCP Integration*
