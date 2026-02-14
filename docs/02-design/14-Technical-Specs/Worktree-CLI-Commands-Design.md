# Worktree CLI Commands - Technical Design Specification

**Document ID**: SPEC-0022
**Created**: February 2, 2026
**Author**: AI Development Team (Claude)
**Sprint**: 144 - Track 2 Implementation
**Related RFC**: RFC-SDLC-604 - Parallel AI Development Pattern
**Status**: 📋 DRAFT → ⏳ CTO REVIEW → ✅ APPROVED → 🔄 IMPLEMENTED

---

## 1. Overview

### 1.1 Purpose

This specification defines the technical design for `sdlcctl worktree` CLI commands that enable parallel AI development using git worktrees. Implements RFC-SDLC-604 (Parallel AI Development Pattern) for 2.5x productivity boost.

### 1.2 Scope

**In Scope**:
- CLI commands: `add`, `list`, `sync`, `remove`
- Git worktree management via subprocess
- Rich console output with tables and status indicators
- Error handling and validation
- Machine-readable output (JSON)

**Out of Scope**:
- Automatic AI session launching (human-driven)
- Worktree templates (future enhancement)
- Integration with GitHub Actions (Sprint 145+)
- Conflict resolution automation (manual process)

### 1.3 Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| **LOC Delivered** | 400 | `wc -l worktree.py` |
| **Commands Implemented** | 4 | add, list, sync, remove |
| **Test Coverage** | ≥90% | pytest-cov |
| **RFC Alignment** | 100% | Features match RFC-SDLC-604 |
| **Error Handling** | Complete | All failure scenarios handled |

---

## 2. Command Specifications

### 2.1 Command: `sdlcctl worktree add`

**Purpose**: Create new git worktree for parallel development

**Syntax**:
```bash
sdlcctl worktree add <path> <branch> [options]
```

**Arguments**:
| Argument | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `path` | string | Yes | Worktree directory path | `../sdlc-auth-backend` |
| `branch` | string | Yes | Branch name | `feature/auth-backend` |

**Options**:
| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--create-branch` | `-b` | bool | True | Create new branch (vs checkout existing) |
| `--no-create-branch` | | bool | False | Checkout existing branch |
| `--force` | `-f` | bool | False | Force creation (overwrite existing directory) |
| `--project` | `-p` | string | `.` | Path to git repository root |

**Validation Rules**:
1. **Repository Check**: `project_path` must be a valid git repository
2. **Path Validation**: Worktree path must not exist (unless `--force`)
3. **Branch Validation**: Branch must not exist if `--create-branch` (git will error)
4. **Git Root Detection**: Must be able to determine `.git` directory location

**Success Output**:
```
Creating Git Worktree
Repository: /home/user/sdlc-orchestrator
Worktree path: /home/user/sdlc-auth-backend
Branch: feature/auth-backend

✓ Worktree created successfully
Preparing worktree (new branch 'feature/auth-backend')
HEAD is now at a3f5b2c Initial commit

Next Steps:
  1. cd /home/user/sdlc-auth-backend
  2. cursor .  # Launch AI coding tool
  3. Start parallel development on branch: feature/auth-backend

💡 Tip: Launch multiple AI sessions in different worktrees for 2.5x speedup!
```

**Error Scenarios**:
| Error | Exit Code | Message | Recovery |
|-------|-----------|---------|----------|
| Not a git repo | 1 | "Not a git repository: {path}" | Navigate to git repo |
| Path exists | 1 | "Worktree path already exists: {path}" | Use `--force` or different path |
| Branch exists | 1 | "fatal: A branch named '{branch}' already exists" | Use `--no-create-branch` or different branch name |
| Permission denied | 1 | "Permission denied: {path}" | Check directory permissions |

**Implementation**:
```python
def add_worktree(path, branch, create_branch, force, project_path):
    # 1. Validate project_path is git repository
    # 2. Get git root directory
    # 3. Resolve worktree path (absolute)
    # 4. Check if path exists (fail if exists and not --force)
    # 5. Build git worktree add command
    #    - Add -b if create_branch
    #    - Add --force if force
    #    - Add path and branch
    # 6. Execute command via subprocess
    # 7. Display success message with next steps
```

---

### 2.2 Command: `sdlcctl worktree list`

**Purpose**: List all git worktrees in repository

**Syntax**:
```bash
sdlcctl worktree list [options]
```

**Arguments**: None

**Options**:
| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--project` | `-p` | string | `.` | Path to git repository root |
| `--porcelain` | | bool | False | Machine-readable JSON output |
| `--details` | | bool | True | Show detailed information (branch, commit, status) |
| `--no-details` | | bool | False | Show paths only |

**Validation Rules**:
1. **Repository Check**: `project_path` must be a valid git repository
2. **Git Root Detection**: Must be able to determine repository root

**Success Output (Default - Rich Table)**:
```
Git Worktrees
Repository: /home/user/sdlc-orchestrator

╭─────────────────────────────────────────────────────────────────╮
│                        3 Worktree(s)                             │
├──────────────────────────────┬─────────┬─────────┬──────────────┤
│ Path                         │ Branch  │ Commit  │ Status       │
├──────────────────────────────┼─────────┼─────────┼──────────────┤
│ /home/user/sdlc-orchestrator │ main    │ a3f5b2c │ active       │
│ (main)                       │         │         │              │
│ /home/user/sdlc-auth-backend │ feature │ b4e6c3d │ active       │
│                              │ /auth-  │         │              │
│                              │ backend │         │              │
│ /home/user/sdlc-auth-tests   │ feature │ c5f7d4e │ active       │
│                              │ /auth-  │         │              │
│                              │ tests   │         │              │
╰──────────────────────────────┴─────────┴─────────┴──────────────╯

💡 Tip: Use 'sdlcctl worktree add' to create new worktrees for parallel AI sessions
```

**Success Output (--porcelain)**:
```json
[
  {
    "path": "/home/user/sdlc-orchestrator",
    "commit": "a3f5b2c1234567890abcdef",
    "branch": "refs/heads/main"
  },
  {
    "path": "/home/user/sdlc-auth-backend",
    "commit": "b4e6c3d1234567890abcdef",
    "branch": "refs/heads/feature/auth-backend"
  },
  {
    "path": "/home/user/sdlc-auth-tests",
    "commit": "c5f7d4e1234567890abcdef",
    "branch": "refs/heads/feature/auth-tests"
  }
]
```

**Success Output (--no-details)**:
```
/home/user/sdlc-orchestrator
/home/user/sdlc-auth-backend
/home/user/sdlc-auth-tests
```

**Error Scenarios**:
| Error | Exit Code | Message | Recovery |
|-------|-----------|---------|----------|
| Not a git repo | 1 | "Not a git repository: {path}" | Navigate to git repo |
| No worktrees | 0 | "⚠ No worktrees found" | Create worktrees with `add` command |

**Implementation**:
```python
def list_worktrees(project_path, porcelain, show_details):
    # 1. Validate project_path is git repository
    # 2. Execute: git worktree list --porcelain
    # 3. Parse output (worktree, HEAD, branch, detached, locked, prunable)
    # 4. Format output:
    #    - If porcelain: JSON array
    #    - If show_details: Rich table with columns
    #    - Else: Paths only (one per line)
    # 5. Display tips for next actions
```

---

### 2.3 Command: `sdlcctl worktree sync`

**Purpose**: Sync all worktrees by rebasing on latest main/master

**Syntax**:
```bash
sdlcctl worktree sync [options]
```

**Arguments**: None

**Options**:
| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--project` | `-p` | string | `.` | Path to git repository root |
| `--dry-run` | | bool | False | Show actions without executing |

**Validation Rules**:
1. **Repository Check**: `project_path` must be a valid git repository
2. **Main Branch Detection**: Automatically detect main/master branch
3. **Worktree Enumeration**: Skip main/master worktree (only sync feature branches)

**Sync Logic**:
```bash
# For each worktree (except main/master):
git fetch origin main
git rebase origin/main
```

**Success Output**:
```
Syncing Worktrees
Base branch: main

→ Syncing feature/auth-backend...
✓ Synced successfully

→ Syncing feature/auth-tests...
✓ Synced successfully

Summary:
  Synced: 2
  Skipped: 1

💡 Tip: All worktrees now rebased on latest main
```

**Dry Run Output**:
```
Syncing Worktrees
Base branch: main
DRY RUN MODE - No changes will be made

→ Syncing feature/auth-backend...
Would sync: git fetch origin main && git rebase origin/main

→ Syncing feature/auth-tests...
Would sync: git fetch origin main && git rebase origin/main

Summary:
  Synced: 2
  Skipped: 1
```

**Error Scenarios**:
| Error | Exit Code | Message | Recovery |
|-------|-----------|---------|----------|
| Not a git repo | 1 | "Not a git repository: {path}" | Navigate to git repo |
| Rebase conflict | 0 | "✗ Rebase failed: {error}" | Resolve conflicts manually |
| Fetch failed | 0 | "✗ Fetch failed: {error}" | Check network connection |

**Implementation**:
```python
def sync_worktrees(project_path, dry_run):
    # 1. Validate project_path is git repository
    # 2. List all worktrees (git worktree list --porcelain)
    # 3. Detect main/master branch from worktree list
    # 4. For each worktree (skip main/master):
    #    a. Fetch: git fetch origin main
    #    b. Rebase: git rebase origin/main
    #    c. Handle errors (continue on failure, report at end)
    # 5. Display summary (synced count, skipped count)
```

---

### 2.4 Command: `sdlcctl worktree remove`

**Purpose**: Remove git worktree

**Syntax**:
```bash
sdlcctl worktree remove <path> [options]
```

**Arguments**:
| Argument | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `path` | string | Yes | Worktree directory path | `../sdlc-auth-backend` |

**Options**:
| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--force` | `-f` | bool | False | Force removal (discard uncommitted changes) |
| `--project` | `-p` | string | `.` | Path to git repository root |

**Validation Rules**:
1. **Repository Check**: `project_path` must be a valid git repository
2. **Uncommitted Changes Check**: Refuse to remove if uncommitted changes (unless `--force`)

**Success Output**:
```
Removing Git Worktree
Repository: /home/user/sdlc-orchestrator
Worktree path: /home/user/sdlc-auth-backend

✓ Worktree removed successfully

💡 Tip: Use 'sdlcctl worktree list' to see remaining worktrees
```

**Error Scenarios**:
| Error | Exit Code | Message | Recovery |
|-------|-----------|---------|----------|
| Not a git repo | 1 | "Not a git repository: {path}" | Navigate to git repo |
| Uncommitted changes | 1 | "fatal: ... contains modified or untracked files" | Use `--force` or commit changes |
| Path not worktree | 1 | "fatal: '{path}' is not a working tree" | Check path is valid worktree |

**Implementation**:
```python
def remove_worktree(path, force, project_path):
    # 1. Validate project_path is git repository
    # 2. Get git root directory
    # 3. Resolve worktree path (absolute)
    # 4. Build git worktree remove command
    #    - Add --force if force
    #    - Add path
    # 5. Execute command via subprocess
    # 6. Display success message
```

---

## 3. Architecture

### 3.1 File Structure

```
backend/sdlcctl/sdlcctl/
├── commands/
│   └── worktree.py          # CLI commands (400 LOC)
└── lib/                     # (Future - Sprint 145+)
    └── git_worktree.py      # Git operations library (150 LOC)
```

**Note**: For Sprint 144 Day 1, all logic is in `worktree.py`. Refactoring to `lib/git_worktree.py` deferred to future sprint for code reuse.

### 3.2 Dependencies

| Dependency | Purpose | License |
|------------|---------|---------|
| `typer` | CLI framework | MIT |
| `rich` | Console output (tables, colors) | MIT |
| `subprocess` | Git command execution | Built-in |
| `pathlib` | Path manipulation | Built-in |
| `json` | JSON serialization (--porcelain) | Built-in |

**No new dependencies** - all existing in `sdlcctl` project.

### 3.3 Integration Points

| Integration | Type | Purpose |
|-------------|------|---------|
| Git CLI | External | Execute `git worktree` commands |
| File System | External | Validate paths, check directories |
| Rich Console | Internal | Display formatted output |
| Typer Framework | Internal | CLI parsing and validation |

### 3.4 Error Handling Strategy

**Principle**: Fail fast with clear error messages and recovery hints.

**Layers**:
1. **Input Validation**: Check arguments before execution (typer automatic + custom)
2. **Pre-execution Checks**: Validate git repository, paths exist, permissions
3. **Git Command Execution**: Capture stdout/stderr, parse exit codes
4. **Post-execution Validation**: Verify expected state achieved

**Error Message Format**:
```
[red]✗[/red] Failed to {action}
[dim]Error: {git_error_message}[/dim]
[yellow]Hint:[/yellow] {recovery_suggestion}
```

**Example**:
```
✗ Failed to create worktree
Error: fatal: 'feature/auth-backend' is already checked out at '/home/user/sdlc-auth-backend'
Hint: Use --no-create-branch to checkout existing branch or choose a different branch name
```

---

## 4. Testing Strategy

### 4.1 Unit Tests

**File**: `backend/sdlcctl/tests/unit/commands/test_worktree.py`

**Test Cases** (20 tests target):

#### 4.1.1 Command: `add`
1. ✅ `test_add_worktree_success` - Happy path (new branch created)
2. ✅ `test_add_worktree_existing_branch` - Checkout existing branch (--no-create-branch)
3. ✅ `test_add_worktree_force` - Overwrite existing directory (--force)
4. ✅ `test_add_worktree_not_git_repo` - Error if not git repository
5. ✅ `test_add_worktree_path_exists` - Error if path exists (no --force)
6. ✅ `test_add_worktree_relative_path` - Resolve relative paths correctly

#### 4.1.2 Command: `list`
7. ✅ `test_list_worktrees_default` - Rich table output
8. ✅ `test_list_worktrees_porcelain` - JSON output (--porcelain)
9. ✅ `test_list_worktrees_no_details` - Paths only (--no-details)
10. ✅ `test_list_worktrees_empty` - No worktrees (warning, exit 0)
11. ✅ `test_list_worktrees_parse_porcelain` - Parse git worktree list --porcelain
12. ✅ `test_list_worktrees_not_git_repo` - Error if not git repository

#### 4.1.3 Command: `sync`
13. ✅ `test_sync_worktrees_success` - Sync all worktrees
14. ✅ `test_sync_worktrees_dry_run` - Dry run (no changes)
15. ✅ `test_sync_worktrees_rebase_conflict` - Handle rebase conflicts
16. ✅ `test_sync_worktrees_skip_main` - Skip main/master worktree

#### 4.1.4 Command: `remove`
17. ✅ `test_remove_worktree_success` - Happy path
18. ✅ `test_remove_worktree_force` - Force removal (uncommitted changes)
19. ✅ `test_remove_worktree_uncommitted_changes` - Error if uncommitted (no --force)
20. ✅ `test_remove_worktree_not_worktree` - Error if path is not worktree

### 4.2 Integration Tests

**File**: `backend/sdlcctl/tests/integration/test_worktree_integration.py`

**Test Cases** (5 tests target):

1. ✅ `test_worktree_full_workflow` - End-to-end: add → list → sync → remove
2. ✅ `test_worktree_parallel_development` - Create 3 worktrees, verify independence
3. ✅ `test_worktree_sync_with_conflicts` - Test conflict detection and manual resolution
4. ✅ `test_worktree_cleanup_all` - Remove all worktrees, verify git state clean
5. ✅ `test_worktree_error_recovery` - Test error scenarios and recovery paths

### 4.3 Test Coverage Target

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Line Coverage** | ≥90% | pytest-cov |
| **Branch Coverage** | ≥85% | pytest-cov --branch |
| **Function Coverage** | 100% | All public functions tested |
| **Error Paths** | 100% | All error scenarios covered |

---

## 5. Performance Requirements

### 5.1 Latency Targets

| Operation | Target | Acceptable | Notes |
|-----------|--------|------------|-------|
| `add` | <2s | <5s | Depends on repository size |
| `list` | <500ms | <1s | Fast parsing required |
| `sync` (per worktree) | <10s | <30s | Depends on rebase complexity |
| `remove` | <1s | <3s | Fast cleanup |

### 5.2 Scalability

| Metric | Target | Notes |
|--------|--------|-------|
| **Max Worktrees** | 10 | RFC-SDLC-604 recommends 3-5, support up to 10 |
| **Repository Size** | <10GB | Tested with SDLC Orchestrator (350MB) |
| **Concurrent Operations** | N/A | Sequential execution only |

---

## 6. Security Considerations

### 6.1 Subprocess Security

**Risk**: Command injection via user input

**Mitigation**:
1. **No shell=True**: Use `subprocess.run()` with list arguments, not string
2. **Input Validation**: Validate paths and branch names before subprocess
3. **Timeout**: 30-second timeout on all git operations
4. **Error Capture**: Capture stderr, don't leak sensitive information

**Example**:
```python
# ✅ SAFE - List arguments (no shell injection)
subprocess.run(['git', 'worktree', 'add', path, branch])

# ❌ UNSAFE - String with shell=True (injection risk)
subprocess.run(f"git worktree add {path} {branch}", shell=True)
```

### 6.2 Path Traversal

**Risk**: User provides malicious path (e.g., `../../etc/passwd`)

**Mitigation**:
1. **Resolve Absolute Paths**: Use `Path.resolve()` to normalize paths
2. **Validate Within Repository**: Ensure worktrees created in expected directories
3. **Permission Checks**: Verify write permissions before creation

### 6.3 Branch Name Validation

**Risk**: Malicious branch name (e.g., `--force` as branch name)

**Mitigation**:
1. **Git's Validation**: Git validates branch names (no special handling needed)
2. **No Shell Expansion**: List arguments prevent shell expansion
3. **Error Capture**: Git errors displayed to user

---

## 7. Observability

### 7.1 Logging

**Log Level**: INFO (default), DEBUG (--verbose)

**Log Events**:
- Command execution start/end
- Git command invocations
- Error conditions
- Success outcomes

**Format**:
```
[2026-02-02 10:30:15] INFO: Executing: git worktree add /home/user/sdlc-auth-backend feature/auth-backend
[2026-02-02 10:30:17] INFO: Worktree created successfully: /home/user/sdlc-auth-backend
```

### 7.2 Metrics

**Tracked Metrics** (for future Grafana dashboard):
- Command execution count (by command)
- Command execution time (p50, p95, p99)
- Error rate (by error type)
- Worktree count (average per repository)

**Note**: Metrics implementation deferred to Sprint 145+ (observability sprint)

---

## 8. Documentation

### 8.1 User-Facing Documentation

**Location**: `backend/sdlcctl/README.md` (CLI Reference section)

**Sections**:
1. Quick Start Guide (5 min tutorial)
2. Command Reference (all 4 commands)
3. Examples (common workflows)
4. Troubleshooting (common errors)
5. Best Practices (RFC-SDLC-604 patterns)

### 8.2 Developer Documentation

**Location**: `docs/02-design/14-Technical-Specs/Worktree-CLI-Commands-Design.md` (this document)

**Sections**:
1. Command Specifications
2. Architecture
3. Testing Strategy
4. Performance Requirements
5. Security Considerations

---

## 9. Rollout Plan

### 9.1 Sprint 144 Day 1-2 (February 3-4, 2026)

**Deliverables**:
- ✅ `worktree.py` implementation (400 LOC)
- ✅ Unit tests (20 tests, 90%+ coverage)
- ✅ CLI reference documentation
- ✅ Manual testing with real repository

**Success Criteria**:
- All 4 commands working (`add`, `list`, `sync`, `remove`)
- Zero P0 bugs (production-blocking)
- CTO approval for Day 3 continuation

### 9.2 Sprint 144 Day 3-5 (February 5-7, 2026)

**Deliverables**:
- Integration tests (5 tests)
- Performance benchmarks
- Dogfooding (use worktrees for Sprint 144 development)
- Sprint 144 retrospective

**Success Criteria**:
- 2.5x speedup demonstrated (dogfooding evidence)
- RFC-SDLC-604 fully implemented
- Framework 6.0.5 patterns validated

---

## 10. Acceptance Criteria

### 10.1 Functional Requirements

| Requirement | Status | Verification |
|-------------|--------|--------------|
| `add` command creates worktree | ⏳ | Manual test: `sdlcctl worktree add ../test-wt test-branch` |
| `list` command shows worktrees | ⏳ | Manual test: `sdlcctl worktree list` |
| `sync` command rebases worktrees | ⏳ | Manual test: `sdlcctl worktree sync` |
| `remove` command deletes worktree | ⏳ | Manual test: `sdlcctl worktree remove ../test-wt` |
| JSON output (`--porcelain`) | ⏳ | Manual test: `sdlcctl worktree list --porcelain \| jq` |
| Error messages clear and helpful | ⏳ | Manual test: Trigger errors, read messages |

### 10.2 Non-Functional Requirements

| Requirement | Status | Verification |
|-------------|--------|--------------|
| Test coverage ≥90% | ⏳ | `pytest --cov=sdlcctl/commands/worktree --cov-report=term` |
| All commands <5s latency | ⏳ | Measure execution time with `time sdlcctl worktree ...` |
| No security vulnerabilities | ⏳ | Code review (no shell=True, input validation) |
| RFC-SDLC-604 alignment | ⏳ | CTO review |

---

## 11. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Git command failures | High | Medium | Robust error handling, clear error messages |
| Rebase conflicts | Medium | High | Provide manual resolution guidance |
| Path resolution bugs | Medium | Low | Extensive testing with absolute/relative paths |
| Performance issues (large repos) | Low | Low | Test with 10GB repository |

---

## 12. References

### 12.1 Internal Documents
- [RFC-SDLC-604: Parallel AI Development Pattern](../../01-planning/08-RFCs/RFC-SDLC-604-Parallel-AI-Development-Pattern.md)
- [Sprint 144 PROGRESS Plan](../../04-build/02-Sprint-Plans/SPRINT-144-PROGRESS.md)
- [Boris Cherny Tactics Analysis Plan](/home/dttai/.claude/plans/parallel-painting-turing.md)

### 12.2 External References
- [Git Worktrees Documentation](https://git-scm.com/docs/git-worktree)
- [Typer CLI Framework](https://typer.tiangolo.com/)
- [Rich Console Library](https://rich.readthedocs.io/)

---

## 13. Appendices

### A. Git Worktree Command Reference

```bash
# Basic worktree commands (for reference)
git worktree add <path> <branch>          # Create worktree
git worktree add -b <branch> <path>       # Create worktree with new branch
git worktree list                         # List all worktrees
git worktree list --porcelain             # Machine-readable list
git worktree remove <path>                # Remove worktree
git worktree remove --force <path>        # Force remove (uncommitted changes)
git worktree prune                        # Clean up stale worktree metadata
```

### B. Example Workflow

```bash
# Step 1: Create worktrees for parallel development
sdlcctl worktree add ../sdlc-auth-backend feature/auth-backend
sdlcctl worktree add ../sdlc-auth-frontend feature/auth-frontend
sdlcctl worktree add ../sdlc-auth-tests feature/auth-tests

# Step 2: List worktrees
sdlcctl worktree list

# Step 3: Launch AI sessions (human-driven)
cd ../sdlc-auth-backend && cursor .  # Session 1: Backend
cd ../sdlc-auth-frontend && cursor . # Session 2: Frontend
cd ../sdlc-auth-tests && cursor .    # Session 3: Tests

# Step 4: Sync worktrees (keep up-to-date with main)
sdlcctl worktree sync

# Step 5: Create PRs (after development complete)
# ... create PRs for each worktree ...

# Step 6: Clean up after merge
sdlcctl worktree remove ../sdlc-auth-backend
sdlcctl worktree remove ../sdlc-auth-frontend
sdlcctl worktree remove ../sdlc-auth-tests
```

---

**Document Status**: 📋 **DRAFT - AWAITING CTO REVIEW**

**Next Steps**:
1. ⏳ CTO review and approval
2. ⏳ Implementation in `worktree.py` (400 LOC)
3. ⏳ Unit tests (20 tests, 90%+ coverage)
4. ⏳ Manual testing and validation

**Framework-First Compliance**: ✅ **VERIFIED** (Design before implementation)

---

*SDLC Framework 6.0.5 - Worktree CLI Commands Technical Design*
*Sprint 144 Day 1 - Track 2 Implementation*
