# SDLC Orchestrator Interface Selection Guide

**Version**: 1.0.0
**Framework**: SDLC 6.0.6
**Last Updated**: February 2, 2026
**Sprint**: 138

---

## Overview

SDLC Orchestrator provides **3 interfaces** for different use cases. This guide helps you choose the right interface for your workflow.

| Interface | Version | Best For |
|-----------|---------|----------|
| **CLI (sdlcctl)** | v1.4.0 | Automation, CI/CD, batch operations |
| **VS Code Extension** | v1.4.0 | Active development, real-time feedback |
| **Web Dashboard** | v1.0.0 | Team management, reports, approvals |

---

## Interface Comparison Matrix

| Scenario | CLI | VS Code | Web App |
|----------|-----|---------|---------|
| **Validate project structure** | ✅ Best | ✅ Good | ❌ |
| **Fix compliance issues** | ✅ Best | ⚠️ Manual | ❌ |
| **Generate AGENTS.md** | ✅ Best | ❌ | ❌ |
| **E2E testing validation** | ✅ Best | ✅ Good | ❌ |
| **Real-time code feedback** | ❌ | ✅ Best | ❌ |
| **Gate status monitoring** | ⚠️ API | ✅ Best | ✅ Good |
| **Team collaboration** | ❌ | ⚠️ | ✅ Best |
| **Approval workflows** | ❌ | ⚠️ | ✅ Best |
| **Evidence submission** | ✅ Good | ✅ Best | ✅ Good |
| **Dashboard & reports** | ⚠️ Text | ❌ | ✅ Best |
| **CI/CD integration** | ✅ Best | ❌ | ⚠️ API |

---

## 1. CLI Interface (sdlcctl)

### When to Use
- **Automation**: CI/CD pipelines, pre-commit hooks, batch processing
- **Validation**: Quick compliance checks before commits
- **Fixing**: Auto-fix structure issues, generate artifacts
- **Scripting**: Integration with other tools

### Key Commands

```bash
# Compliance & Validation
sdlcctl compliance score          # Check overall compliance
sdlcctl compliance duplicates     # Detect duplicate stages
sdlcctl validate --tier PROFESSIONAL  # Full structure validation
sdlcctl validate-consistency      # Cross-stage consistency

# E2E Testing (RFC-SDLC-602)
sdlcctl e2e validate              # E2E testing compliance
sdlcctl e2e cross-reference       # Stage 03 ↔ 05 links
sdlcctl e2e generate-report       # Generate test report

# Fixing Issues
sdlcctl fix --dry-run             # Preview fixes
sdlcctl agents init               # Generate AGENTS.md
sdlcctl spec init                 # Create new spec

# Reports
sdlcctl report                    # Generate compliance report
sdlcctl evidence check            # Spec-to-code alignment
```

### CI/CD Integration Example

```yaml
# .github/workflows/sdlc-compliance.yml
name: SDLC Compliance
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install sdlcctl
        run: pip install sdlcctl
      - name: Validate Structure
        run: sdlcctl validate --strict --ci
      - name: Check E2E Compliance
        run: sdlcctl e2e validate --min-pass-rate 80
```

### Best Practices
- Use `--dry-run` before making changes
- Add `sdlcctl validate` to pre-commit hooks
- Use `--format json` for CI/CD parsing
- Run `sdlcctl compliance score` regularly

---

## 2. VS Code Extension Interface

### When to Use
- **Active Development**: Real-time compliance feedback while coding
- **Evidence Submission**: Quick evidence upload with `Cmd+Shift+E`
- **Gate Monitoring**: Live gate status in sidebar
- **AI Assistance**: `@gate` chat for compliance help

### Key Features

| Feature | Shortcut | Description |
|---------|----------|-------------|
| Gate Status Sidebar | - | Real-time G0-G5 progress |
| Refresh Gates | `Cmd+Shift+R` | Manual refresh |
| Validate Spec | `Cmd+Shift+V` | Validate current file |
| Generate Code | `Cmd+Shift+G` | IR-based code generation |
| Magic Mode | `Cmd+Shift+M` | Natural language to code |
| Lock Contract | `Cmd+Shift+L` | Lock blueprint |
| App Builder | `Cmd+Shift+B` | Visual blueprint editor |

### @gate Chat Commands

```
@gate /status      - Show current gate status (G0-G5)
@gate /evaluate    - Run compliance evaluation
@gate /fix <id>    - Get AI recommendation for violation
@gate /council <id> - AI Council deliberation
```

### Best Practices
- Keep extension sidebar open while developing
- Use `@gate /status` before committing
- Submit evidence immediately after completing features
- Enable auto-refresh (30 seconds default)

---

## 3. Web Dashboard Interface

### When to Use
- **Team Management**: Invite members, assign roles
- **Approval Workflows**: Gate approvals, override requests
- **Reports & Analytics**: DORA metrics, compliance trends
- **Project Overview**: Multi-project status at a glance

### Key Sections

| Section | Purpose |
|---------|---------|
| **Dashboard** | Overview of all projects, gate status |
| **Projects** | Create, configure, archive projects |
| **Gates** | View gate details, approve/reject |
| **Evidence Vault** | Browse, search, verify evidence |
| **Team** | Invite members, manage roles |
| **Reports** | Generate compliance reports |
| **Settings** | API keys, integrations |

### Role-Based Access

| Role | CLI | Extension | Web App |
|------|-----|-----------|---------|
| **Developer** | ✅ Full | ✅ Full | ⚠️ Limited |
| **QA** | ✅ Full | ✅ Full | ✅ Evidence/Tests |
| **Tech Lead** | ✅ Full | ✅ Full | ✅ Approvals |
| **PM** | ⚠️ Read | ⚠️ Read | ✅ Full |
| **Admin** | ✅ Full | ✅ Full | ✅ Full |

### Best Practices
- Use Web App for team-wide visibility
- Set up approval workflows for critical gates
- Export reports for stakeholder meetings
- Configure Slack/Teams notifications

---

## Scenario-Based Recommendations

### Scenario 1: Starting a New Sprint

| Step | Interface | Command/Action |
|------|-----------|----------------|
| 1. Create sprint plan | Web App | Projects → Sprints → Create |
| 2. Initialize docs structure | CLI | `sdlcctl init --tier PROFESSIONAL` |
| 3. Generate AGENTS.md | CLI | `sdlcctl agents init` |
| 4. Start coding | VS Code | Open project with Extension |

### Scenario 2: Before Pull Request

| Step | Interface | Command/Action |
|------|-----------|----------------|
| 1. Validate structure | CLI | `sdlcctl validate --strict` |
| 2. Check compliance | CLI | `sdlcctl compliance score` |
| 3. Run E2E tests | CLI | `sdlcctl e2e validate` |
| 4. Submit evidence | VS Code | `Cmd+Shift+E` |
| 5. Create PR | CLI/GitHub | Link evidence in PR |

### Scenario 3: Gate Approval Process

| Step | Interface | Command/Action |
|------|-----------|----------------|
| 1. Check gate status | VS Code | @gate /status |
| 2. Review evidence | Web App | Evidence Vault → Filter by gate |
| 3. Approve/Reject | Web App | Gates → Select → Approve |
| 4. Notify team | Web App | Auto-notification sent |

### Scenario 4: Debugging Compliance Issues

| Step | Interface | Command/Action |
|------|-----------|----------------|
| 1. Get compliance score | CLI | `sdlcctl compliance score` |
| 2. Find violations | CLI | `sdlcctl validate --verbose` |
| 3. Get fix suggestions | VS Code | @gate /fix <violation-id> |
| 4. Apply fixes | CLI | `sdlcctl fix` |
| 5. Verify fix | CLI | `sdlcctl compliance score` |

### Scenario 5: Cross-Stage Consistency Check

| Step | Interface | Command/Action |
|------|-----------|----------------|
| 1. Run consistency check | CLI | `sdlcctl validate-consistency -s1 ... -s4 ...` |
| 2. Check E2E cross-refs | CLI | `sdlcctl e2e cross-reference` |
| 3. Review violations | VS Code | Context Overlay panel |
| 4. Fix references | VS Code | Edit files directly |
| 5. Re-validate | CLI | Re-run validation |

---

## Quick Reference Card

### CLI Quick Commands
```bash
sdlcctl compliance score   # Overall score
sdlcctl validate          # Structure check
sdlcctl fix               # Auto-fix
sdlcctl agents init       # Generate AGENTS.md
sdlcctl e2e validate      # E2E compliance
```

### VS Code Quick Actions
- `Cmd+Shift+R` - Refresh gates
- `Cmd+Shift+V` - Validate spec
- `Cmd+Shift+E` - Submit evidence
- `@gate /status` - Quick status

### Web App Quick Links
- `/dashboard` - Overview
- `/projects` - All projects
- `/evidence` - Evidence Vault
- `/reports` - Generate reports

---

## Troubleshooting

### CLI Issues
```bash
# Check version
sdlcctl --version

# Reinstall
pip install -e backend/sdlcctl

# Debug mode
sdlcctl validate --verbose
```

### VS Code Extension Issues
```bash
# Check installed version
code --list-extensions --show-versions | grep sdlc

# Reinstall
code --install-extension vscode-extension/sdlc-orchestrator-1.4.0.vsix --force

# Check logs
# VS Code → Output → SDLC Orchestrator
```

### Web App Issues
```bash
# Check backend health
curl http://localhost:8000/health

# Check logs
docker logs sdlc-backend
```

---

## Summary

| Interface | Strengths | Best For |
|-----------|-----------|----------|
| **CLI** | Automation, scripting, CI/CD | DevOps, automation |
| **VS Code** | Real-time, integrated | Active development |
| **Web App** | Visual, collaboration | Team management |

**Rule of Thumb**:
- **Developing?** → Use VS Code Extension
- **Automating?** → Use CLI
- **Managing?** → Use Web Dashboard

---

*SDLC Orchestrator v1.4.0 - Operating System for Software 3.0*
