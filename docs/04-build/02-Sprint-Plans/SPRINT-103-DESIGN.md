# Sprint 103: Context <60 Lines + Framework Version Tracking

**Version**: 1.0.0  
**Date**: January 23, 2026  
**Status**: DESIGN APPROVED - Ready for Implementation  
**Epic**: P1-002, P2-001 (SDLC 6.1.0 Compliance)

---

## Executive Summary

**Goal**: Enforce AGENTS.md context limits (<60 lines per file) and implement Framework version tracking for audit compliance.

**Timeline**: 3 days (Feb 10 - Feb 12, 2026)  
**Story Points**: 8 SP  
**Owner**: Backend Lead

**Key Deliverables**:
1. AGENTS.md Context Validator
2. Framework Version Tracker
3. CLI command: `sdlcctl validate-context`
4. GitHub check for context limits
5. 20+ tests

---

## Background

### Framework 5.2.0 Requirements

**AGENTS.md Context Limits**:
> "Context descriptions MUST remain under 60 lines per file reference to prevent token bloat in AI workflows."
> — SDLC Framework 5.2.0, Section 03-AI-GOVERNANCE

**Why <60 lines?**:
- Claude/GPT context window optimization
- Prevent "context creep" in agent orchestration
- Force developers to write concise summaries
- Faster agent startup (less reading overhead)

**Framework Version Tracking**:
> "All projects MUST track which Framework version they were built against for audit and compliance."
> — SDLC Framework 5.2.0, Section 09-GOVERN

**Why track versions?**:
- Compliance audits require version proof
- Framework updates need migration tracking
- Policy changes need retroactive application
- Training materials reference specific versions

---

## Architecture

### Component Overview

```
┌────────────────────────────────────────────────────────────────┐
│      SPRINT 103: CONTEXT VALIDATION + VERSION TRACKING         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 1. Context Validation                                     │ │
│  │                                                           │ │
│  │  Developer updates AGENTS.md                              │ │
│  │         ↓                                                 │ │
│  │  ContextValidationService                                 │ │
│  │    - Parse AGENTS.md                                      │ │
│  │    - Count lines per file reference                       │ │
│  │    - Validate <60 lines limit                            │ │
│  │         ↓                                                 │ │
│  │  GitHub Check (if over limit)                            │ │
│  │    ❌ Block merge                                         │ │
│  │    💡 Suggest: Break into sub-files or link to docs      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 2. Framework Version Tracking                             │ │
│  │                                                           │ │
│  │  Project created/updated                                  │ │
│  │         ↓                                                 │ │
│  │  FrameworkVersionService                                  │ │
│  │    - Store current Framework version                      │ │
│  │    - Track version history                                │ │
│  │    - Detect version drift                                 │ │
│  │         ↓                                                 │ │
│  │  Database: framework_versions table                       │ │
│  │    - project_id                                           │ │
│  │    - version (e.g., 5.2.0)                               │ │
│  │    - applied_at                                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 3. CLI: sdlcctl validate-context                         │ │
│  │                                                           │ │
│  │  $ sdlcctl validate-context                              │ │
│  │    ✅ AGENTS.md: All files <60 lines                      │ │
│  │    ⚠️  AGENTS.md: backend/main.py has 72 lines (OVER)    │ │
│  │                                                           │ │
│  │  $ sdlcctl validate-context --file AGENTS.md             │ │
│  │    File-by-file breakdown                                 │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Detailed Tasks

### Backend (6 SP - 2 days)

#### Task 1.1: ContextValidationService (3 SP - 1 day)

**File**: `backend/app/services/context_validation_service.py` (~400 lines)

**Key Methods**:
```python
from typing import NamedTuple
import re

class FileContext(NamedTuple):
    file_path: str
    line_count: int
    content: str
    start_line: int  # Line number in AGENTS.md where context starts

class ContextValidation(NamedTuple):
    total_files: int
    passed_files: int
    failed_files: int
    violations: list[FileContext]
    overall_passed: bool

class ContextValidationService:
    MAX_CONTEXT_LINES = 60
    
    def __init__(self, github_service: GitHubService):
        self.github_service = github_service
    
    async def validate_agents_md(
        self,
        repo_full_name: str,
        branch: str = "main",
        agents_md_path: str = "AGENTS.md"
    ) -> ContextValidation:
        """
        Validate AGENTS.md context limits.
        
        Returns:
            ContextValidation with violations
        """
        # Fetch AGENTS.md from GitHub
        content = await self.github_service.get_file_content(
            repo_full_name,
            agents_md_path,
            branch
        )
        
        # Parse file contexts
        file_contexts = self._parse_file_contexts(content)
        
        # Validate each context
        violations = [
            ctx for ctx in file_contexts
            if ctx.line_count > self.MAX_CONTEXT_LINES
        ]
        
        return ContextValidation(
            total_files=len(file_contexts),
            passed_files=len(file_contexts) - len(violations),
            failed_files=len(violations),
            violations=violations,
            overall_passed=len(violations) == 0
        )
    
    def _parse_file_contexts(self, agents_md_content: str) -> list[FileContext]:
        """
        Parse AGENTS.md to extract file contexts.
        
        Expected format:
            ### File: backend/app/main.py
            Lines 1-50
            ```python
            ... (context)
            ```
        """
        file_contexts = []
        lines = agents_md_content.split('\n')
        
        current_file = None
        current_context_lines = []
        current_start_line = 0
        in_code_block = False
        
        for line_num, line in enumerate(lines, start=1):
            # Detect file header
            file_match = re.match(r'^###\s+File:\s+(.+)', line)
            if file_match:
                # Save previous file context
                if current_file:
                    file_contexts.append(FileContext(
                        file_path=current_file,
                        line_count=len(current_context_lines),
                        content='\n'.join(current_context_lines),
                        start_line=current_start_line
                    ))
                
                # Start new file context
                current_file = file_match.group(1).strip()
                current_context_lines = []
                current_start_line = line_num
                in_code_block = False
                continue
            
            # Track code block boundaries
            if line.startswith('```'):
                in_code_block = not in_code_block
                continue
            
            # Collect context lines (inside code blocks)
            if in_code_block and current_file:
                current_context_lines.append(line)
        
        # Save last file context
        if current_file:
            file_contexts.append(FileContext(
                file_path=current_file,
                line_count=len(current_context_lines),
                content='\n'.join(current_context_lines),
                start_line=current_start_line
            ))
        
        return file_contexts
    
    def format_violation_report(self, validation: ContextValidation) -> str:
        """
        Format validation report for GitHub check or CLI output.
        """
        if validation.overall_passed:
            return "✅ All file contexts are under 60 lines."
        
        report_lines = [
            f"❌ Context validation failed: {validation.failed_files}/{validation.total_files} files over 60 lines",
            "",
            "Violations:"
        ]
        
        for ctx in validation.violations:
            report_lines.append(
                f"  - {ctx.file_path}: {ctx.line_count} lines (AGENTS.md L{ctx.start_line})"
            )
        
        report_lines.extend([
            "",
            "💡 Suggestions:",
            "  - Break large contexts into sub-files (e.g., app/api/users → users_routes, users_schemas)",
            "  - Link to detailed docs instead of embedding full code",
            "  - Use '...existing code...' markers to abbreviate"
        ])
        
        return '\n'.join(report_lines)
```

**Tests**: 10 tests
- Parse AGENTS.md (various formats)
- Detect violations
- Count lines correctly (ignoring headers, code fence markers)
- Edge cases (empty file, no code blocks, malformed headers)

---

#### Task 1.2: FrameworkVersionService (2 SP - 0.5 day)

**File**: `backend/app/services/framework_version_service.py` (~250 lines)

**Key Methods**:
```python
from semantic_version import Version

class FrameworkVersionService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def record_framework_version(
        self,
        project_id: UUID,
        version: str,
        applied_by: UUID | None = None
    ) -> FrameworkVersion:
        """
        Record Framework version for project.
        
        Used when:
            - Project created
            - Framework manually updated
            - Migration applied
        """
        version_obj = Version(version)  # Validate semantic version
        
        fv = FrameworkVersion(
            id=uuid4(),
            project_id=project_id,
            version=version,
            major=version_obj.major,
            minor=version_obj.minor,
            patch=version_obj.patch,
            applied_at=datetime.utcnow(),
            applied_by=applied_by
        )
        
        self.db.add(fv)
        await self.db.commit()
        
        return fv
    
    async def get_current_framework_version(
        self,
        project_id: UUID
    ) -> FrameworkVersion | None:
        """Get latest Framework version for project."""
        result = await self.db.execute(
            select(FrameworkVersion)
            .where(FrameworkVersion.project_id == project_id)
            .order_by(FrameworkVersion.applied_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_version_history(
        self,
        project_id: UUID
    ) -> list[FrameworkVersion]:
        """Get full version history for project."""
        result = await self.db.execute(
            select(FrameworkVersion)
            .where(FrameworkVersion.project_id == project_id)
            .order_by(FrameworkVersion.applied_at.desc())
        )
        return result.scalars().all()
    
    async def detect_version_drift(
        self,
        project_id: UUID,
        latest_framework_version: str
    ) -> dict:
        """
        Detect if project is behind latest Framework version.
        
        Returns:
            {
                "current": "5.1.3",
                "latest": "5.2.0",
                "drift": True,
                "major_drift": False,
                "minor_drift": True,
                "patch_drift": False
            }
        """
        current = await self.get_current_framework_version(project_id)
        if not current:
            return {
                "current": None,
                "latest": latest_framework_version,
                "drift": True,
                "major_drift": True
            }
        
        current_ver = Version(current.version)
        latest_ver = Version(latest_framework_version)
        
        return {
            "current": current.version,
            "latest": latest_framework_version,
            "drift": current_ver < latest_ver,
            "major_drift": current_ver.major < latest_ver.major,
            "minor_drift": current_ver.minor < latest_ver.minor,
            "patch_drift": current_ver.patch < latest_ver.patch
        }
```

**Tests**: 8 tests
- Record version
- Get current version
- Version history
- Drift detection (major/minor/patch)

---

#### Task 1.3: API Routes (1 SP - 0.5 day)

**File**: `backend/app/api/routes/compliance.py` (~200 lines)

**Endpoints**:
```python
# Context Validation
POST /api/v1/compliance/validate-context
  Body: { project_id }
  Response: ContextValidation

# Framework Version
GET /api/v1/framework-version/{project_id}
  Response: FrameworkVersion (current)

GET /api/v1/framework-version/{project_id}/history
  Response: { versions: FrameworkVersion[] }

POST /api/v1/framework-version/{project_id}
  Body: { version }
  Response: FrameworkVersion (newly recorded)

GET /api/v1/framework-version/{project_id}/drift
  Query: ?latest_version=5.2.0
  Response: { current, latest, drift, major_drift, minor_drift, patch_drift }
```

---

### CLI (2 SP - 0.5 day)

#### Task 2.1: sdlcctl validate-context

**File**: `backend/sdlcctl/commands/validate_context.py` (~200 lines)

**Usage**:
```bash
# Validate AGENTS.md in current directory
$ sdlcctl validate-context

# Validate specific file
$ sdlcctl validate-context --file CUSTOM_AGENTS.md

# Verbose mode (show all files, not just violations)
$ sdlcctl validate-context --verbose

# JSON output
$ sdlcctl validate-context --json
```

**Output Example**:
```
✅ Context Validation: PASSED

Files analyzed: 24
  Passed: 23
  Failed: 1

❌ Violations:
  - backend/app/services/planning_orchestrator.py: 72 lines (AGENTS.md L156)

💡 Suggestions:
  - Break into sub-files: planning_orchestrator_core.py, planning_orchestrator_utils.py
  - Link to full docs: docs/02-design/03-ADRs/ADR-027-Planning-Orchestrator.md
```

**Implementation**:
```python
import click
from rich.console import Console
from rich.table import Table

@click.command()
@click.option('--file', default='AGENTS.md', help='Path to AGENTS.md file')
@click.option('--verbose', is_flag=True, help='Show all files, not just violations')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def validate_context(file: str, verbose: bool, output_json: bool):
    """
    Validate AGENTS.md context limits (<60 lines per file).
    """
    console = Console()
    
    # Read AGENTS.md
    if not os.path.exists(file):
        console.print(f"❌ File not found: {file}", style="red")
        return 1
    
    with open(file, 'r') as f:
        content = f.read()
    
    # Validate
    validator = ContextValidationService(github_service=None)  # Local mode
    validation = validator._parse_file_contexts(content)
    
    # Build report
    passed = [ctx for ctx in validation if ctx.line_count <= 60]
    failed = [ctx for ctx in validation if ctx.line_count > 60]
    
    if output_json:
        print(json.dumps({
            "total_files": len(validation),
            "passed_files": len(passed),
            "failed_files": len(failed),
            "violations": [
                {"file": ctx.file_path, "lines": ctx.line_count, "start_line": ctx.start_line}
                for ctx in failed
            ]
        }, indent=2))
        return 0 if len(failed) == 0 else 1
    
    # Console output
    if len(failed) == 0:
        console.print("✅ Context Validation: PASSED", style="green bold")
    else:
        console.print("❌ Context Validation: FAILED", style="red bold")
    
    console.print(f"\nFiles analyzed: {len(validation)}")
    console.print(f"  Passed: {len(passed)}", style="green")
    console.print(f"  Failed: {len(failed)}", style="red")
    
    if len(failed) > 0:
        console.print("\n❌ Violations:", style="red")
        for ctx in failed:
            console.print(f"  - {ctx.file_path}: {ctx.line_count} lines (AGENTS.md L{ctx.start_line})")
        
        console.print("\n💡 Suggestions:")
        console.print("  - Break large contexts into sub-files")
        console.print("  - Link to detailed docs instead of embedding full code")
        console.print("  - Use '...existing code...' markers to abbreviate")
    
    if verbose:
        table = Table(title="All Files")
        table.add_column("File", style="cyan")
        table.add_column("Lines", justify="right")
        table.add_column("Status")
        
        for ctx in validation:
            status = "✅" if ctx.line_count <= 60 else "❌"
            table.add_row(ctx.file_path, str(ctx.line_count), status)
        
        console.print(table)
    
    return 0 if len(failed) == 0 else 1
```

**Tests**: 5 tests
- Parse local AGENTS.md
- Detect violations
- JSON output format
- Verbose mode
- Exit codes

---

### DevOps (Integration)

#### Task 3.1: GitHub Check for Context Validation

**File**: `.github/workflows/context-validation.yml` (~80 lines)

```yaml
name: Context Validation

on:
  pull_request:
    paths:
      - 'AGENTS.md'
  push:
    branches:
      - main
    paths:
      - 'AGENTS.md'

jobs:
  validate-context:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install sdlcctl
        run: |
          cd backend/sdlcctl
          pip install -e .
      
      - name: Validate AGENTS.md context
        run: sdlcctl validate-context --json > validation-result.json
      
      - name: Post GitHub Check
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const result = JSON.parse(fs.readFileSync('validation-result.json', 'utf8'));
            
            const conclusion = result.failed_files === 0 ? 'success' : 'failure';
            const summary = result.failed_files === 0
              ? `✅ All ${result.total_files} file contexts are under 60 lines.`
              : `❌ ${result.failed_files}/${result.total_files} file contexts exceed 60 lines.`;
            
            let text = `**Files analyzed**: ${result.total_files}\n`;
            text += `**Passed**: ${result.passed_files}\n`;
            text += `**Failed**: ${result.failed_files}\n\n`;
            
            if (result.violations.length > 0) {
              text += '## Violations\n\n';
              for (const v of result.violations) {
                text += `- \`${v.file}\`: ${v.lines} lines (AGENTS.md L${v.start_line})\n`;
              }
              
              text += '\n## Suggestions\n\n';
              text += '- Break large contexts into sub-files\n';
              text += '- Link to detailed docs instead of embedding full code\n';
              text += '- Use `...existing code...` markers to abbreviate\n';
            }
            
            await github.rest.checks.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              name: 'Context Validation',
              head_sha: context.sha,
              status: 'completed',
              conclusion,
              output: {
                title: 'AGENTS.md Context Validation',
                summary,
                text
              }
            });
```

---

## Success Metrics

| Metric | Target | Verification |
|--------|--------|--------------|
| AGENTS.md compliance | 100% projects | Audit sample of 20 projects |
| Context validation latency | <5s | Monitor GitHub check runs |
| Framework version tracking | 100% projects | Database query |
| Version drift detection accuracy | 100% | Manual review |
| CLI adoption | 50% of projects | Usage analytics |

---

## Testing Strategy

### Unit Tests (18 tests)

**ContextValidationService** (10 tests):
- Parse AGENTS.md (various formats)
- Detect violations
- Count lines correctly
- Edge cases (empty, no code blocks, malformed)
- Report formatting

**FrameworkVersionService** (8 tests):
- Record version
- Get current version
- Version history
- Drift detection (major/minor/patch)

### Integration Tests (3 tests)

- End-to-end context validation (API)
- Framework version workflow (create project → record version → query)
- GitHub webhook → Context validation → Check run

### E2E Tests (2 tests)

- CLI: `sdlcctl validate-context` with violations
- View Framework version in Project Settings UI

---

## Migration Plan

### Database Migration

**File**: `backend/alembic/versions/s103_001_framework_versions.py`

```python
def upgrade():
    # Create framework_versions table
    op.create_table(
        'framework_versions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('major', sa.Integer(), nullable=False),
        sa.Column('minor', sa.Integer(), nullable=False),
        sa.Column('patch', sa.Integer(), nullable=False),
        sa.Column('applied_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('applied_by', sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['applied_by'], ['users.id'])
    )
    
    op.create_index('idx_framework_versions_project', 'framework_versions', ['project_id'])
    op.create_index('idx_framework_versions_applied_at', 'framework_versions', ['applied_at'])
    
    # Backfill existing projects with Framework 5.2.0
    op.execute("""
        INSERT INTO framework_versions (id, project_id, version, major, minor, patch, applied_at)
        SELECT gen_random_uuid(), id, '5.2.0', 5, 2, 0, created_at
        FROM projects
    """)

def downgrade():
    op.drop_table('framework_versions')
```

---

## Documentation Updates

### Framework

**File**: `SDLC-Enterprise-Framework/03-AI-GOVERNANCE/02-Context-Limits.md`

- Document <60 lines rule
- Provide examples of good vs bad contexts
- Link to validator tool

### Orchestrator

**Files**:
- `PROJECT-STATUS.md` - Sprint 103 completion
- `docs/02-design/03-ADRs/ADR-037-Context-Limits-Enforcement.md` - New ADR
- `backend/sdlcctl/README.md` - Add `validate-context` command

---

## Timeline

| Day | Tasks | Owner | Hours |
|-----|-------|-------|-------|
| **Day 1** | ContextValidationService + Tests | Backend | 8h |
| **Day 2** | FrameworkVersionService + API Routes | Backend | 8h |
| **Day 3** | CLI + GitHub workflow + E2E tests | Backend + DevOps | 8h |

**Total Effort**: 24 hours (8 SP = 3 hours/SP)

---

## Approval

**Status**: ✅ APPROVED FOR IMPLEMENTATION

```
┌─────────────────────────────────────────────────────────────────┐
│                    ✅ SPRINT 103 APPROVED                       │
│                                                                 │
│  Sprint: 103 - Context Limits + Framework Versioning           │
│  Date: January 23, 2026                                        │
│  Story Points: 8 SP                                            │
│  Timeline: 3 days (Feb 10 - Feb 12)                           │
│                                                                 │
│  "Enforces AI governance best practices and enables            │
│   compliance audits with version tracking."                    │
│                                                                 │
│  — CTO, SDLC Orchestrator                                      │
└─────────────────────────────────────────────────────────────────┘
```
