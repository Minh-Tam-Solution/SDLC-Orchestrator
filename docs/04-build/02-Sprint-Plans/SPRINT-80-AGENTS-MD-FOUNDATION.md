# Sprint 80: AGENTS.md Foundation & Static Generator

**Sprint ID:** S80
**Status:** ✅ CTO APPROVED (Jan 19, 2026)
**Duration:** 10 days (February 3-14, 2026)
**Goal:** Implement AGENTS.md Generator + Static/Dynamic Overlay Architecture
**Story Points:** 42 SP
**Framework Reference:** SDLC 5.1.3 P5 (SASE Integration)
**Prerequisite:** Sprint 79 ✅ + ADR-029 ✅

---

## 🎯 Sprint 80 Objectives

### Primary Goals (P0)

1. **AGENTS.md Generator Service** - Generate compliant AGENTS.md from project analysis
2. **CLI Command: `sdlc agents init`** - Create/update AGENTS.md via CLI
3. **AGENTS.md Validator/Linter** - Validate structure and forbidden content

### Secondary Goals (P1)

4. **Context Overlay Service** - Generate dynamic overlays (NOT committed to git)
5. **PR Comment Integration** - Post overlays as structured PR comments
6. **MTS/BRS/LPS Deprecation** - Mark as deprecated in Framework

---

## ✅ Sprint 79 Handoff

### Expected Completion (Sprint 79)

| Feature | Status | Notes |
|---------|--------|-------|
| Landing Page MVP | ✅ Expected | Marketing ready |
| Expert Feedback fixes | ✅ Expected | Over-claims resolved |
| Pre-launch hardening | ✅ Expected | Per CTO approval |

### Sprint 80 Focus

| Feature | Description | Priority | ADR |
|---------|-------------|----------|-----|
| AGENTS.md Generator | Generate from project config | P0 | ADR-029 |
| Static + Overlay Arch | Two-layer architecture | P0 | ADR-029 |
| CLI Integration | `sdlc agents init` | P0 | ADR-029 |
| MTS/BRS/LPS Deprecation | Framework update | P1 | ADR-029 |

---

## 📋 Sprint 80 Backlog

### Day 1-2: AGENTS.md Generator Service (12 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `AgentsMdService` class | Backend | 4h | P0 | ⏳ |
| Implement project analysis (docker, config) | Backend | 4h | P0 | ⏳ |
| Section generators (Quick Start, Arch, etc) | Backend | 4h | P0 | ⏳ |
| 150-line limit enforcement | Backend | 2h | P0 | ⏳ |
| Unit tests (12 tests) | Backend | 3h | P0 | ⏳ |

**Implementation:**

```python
# backend/app/services/agents_md_service.py
from typing import Optional
from uuid import UUID
from datetime import datetime
import hashlib

from pydantic import BaseModel


class AgentsMdConfig(BaseModel):
    """Configuration for AGENTS.md generation."""
    include_quick_start: bool = True
    include_architecture: bool = True
    include_conventions: bool = True
    include_security: bool = True
    include_git_workflow: bool = True
    include_do_not: bool = True
    max_lines: int = 150


class AgentsMdFile(BaseModel):
    """Generated AGENTS.md file."""
    content: str
    generated_at: datetime
    source_hash: str
    line_count: int
    sections: list[str]


class AgentsMdService:
    """
    Generate and validate AGENTS.md files.

    Implements ADR-029 Static AGENTS.md layer:
    - Generates from project configuration
    - Enforces ≤150 line limit
    - Validates forbidden content
    """

    def __init__(
        self,
        project_repo,
        file_analyzer,
    ):
        self.project_repo = project_repo
        self.file_analyzer = file_analyzer

    async def generate(
        self,
        project_id: UUID,
        config: Optional[AgentsMdConfig] = None,
    ) -> AgentsMdFile:
        """
        Generate AGENTS.md from project analysis.

        Args:
            project_id: Project UUID
            config: Generation configuration

        Returns:
            AgentsMdFile with content and metadata
        """
        config = config or AgentsMdConfig()
        sections = []
        section_names = []

        # Header
        project = await self.project_repo.get(project_id)
        header = f"# AGENTS.md - {project.name}\n"

        # Quick Start
        if config.include_quick_start:
            quick_start = await self._generate_quick_start(project_id)
            if quick_start:
                sections.append(quick_start)
                section_names.append("Quick Start")

        # Architecture
        if config.include_architecture:
            arch = await self._generate_architecture(project_id)
            if arch:
                sections.append(arch)
                section_names.append("Architecture")

        # Current Stage (static snapshot)
        stage = await self._generate_current_stage(project_id)
        if stage:
            sections.append(stage)
            section_names.append("Current Stage")

        # Conventions
        if config.include_conventions:
            conv = await self._generate_conventions(project_id)
            if conv:
                sections.append(conv)
                section_names.append("Conventions")

        # Security
        if config.include_security:
            sec = await self._generate_security(project_id)
            if sec:
                sections.append(sec)
                section_names.append("Security")

        # Git Workflow
        if config.include_git_workflow:
            git = await self._generate_git_workflow(project_id)
            if git:
                sections.append(git)
                section_names.append("Git Workflow")

        # DO NOT
        if config.include_do_not:
            dont = await self._generate_do_not(project_id)
            if dont:
                sections.append(dont)
                section_names.append("DO NOT")

        # Combine
        content = header + "\n".join(sections)

        # Enforce line limit
        line_count = content.count('\n') + 1
        if line_count > config.max_lines:
            content = self._truncate_to_limit(content, config.max_lines)
            line_count = config.max_lines

        return AgentsMdFile(
            content=content,
            generated_at=datetime.utcnow(),
            source_hash=hashlib.sha256(content.encode()).hexdigest(),
            line_count=line_count,
            sections=section_names,
        )

    async def _generate_quick_start(self, project_id: UUID) -> str:
        """Generate Quick Start section from docker-compose/package.json."""
        commands = []

        # Check for docker-compose
        if await self.file_analyzer.exists(project_id, "docker-compose.yml"):
            commands.append("- Full stack: `docker compose up -d`")

        # Check for backend
        if await self.file_analyzer.exists(project_id, "backend/requirements.txt"):
            commands.append("- Backend only: `cd backend && pytest`")
        elif await self.file_analyzer.exists(project_id, "backend/pyproject.toml"):
            commands.append("- Backend only: `cd backend && poetry run pytest`")

        # Check for frontend
        if await self.file_analyzer.exists(project_id, "frontend/package.json"):
            commands.append("- Frontend only: `cd frontend && npm run dev`")
        elif await self.file_analyzer.exists(project_id, "frontend/web/package.json"):
            commands.append("- Frontend only: `cd frontend/web && npm run dev`")

        if not commands:
            return ""

        return f"""## Quick Start
{chr(10).join(commands)}
"""

    async def _generate_architecture(self, project_id: UUID) -> str:
        """Generate Architecture section (brief overview)."""
        # Default template - will be customized per project
        return """## Architecture
See `/docs/02-design/` for detailed architecture documentation.
"""

    async def _generate_current_stage(self, project_id: UUID) -> str:
        """Generate Current Stage section (static snapshot)."""
        # This is a STATIC snapshot, not dynamic
        return """## Current Stage
Check project dashboard for current SDLC stage and gate status.
"""

    async def _generate_conventions(self, project_id: UUID) -> str:
        """Generate Conventions section from config files."""
        conventions = []

        # Python conventions
        if await self.file_analyzer.exists(project_id, "ruff.toml"):
            conventions.append("- Python: ruff + mypy strict mode")
        elif await self.file_analyzer.exists(project_id, "pyproject.toml"):
            conventions.append("- Python: See pyproject.toml for linting config")

        # TypeScript conventions
        if await self.file_analyzer.exists(project_id, "tsconfig.json"):
            conventions.append("- TypeScript: strict mode enabled")

        # Naming conventions (default)
        conventions.append("- Files: snake_case (Python), camelCase/PascalCase (TypeScript)")
        conventions.append("- Tests: 95%+ coverage required")

        return f"""## Conventions
{chr(10).join(conventions)}
"""

    async def _generate_security(self, project_id: UUID) -> str:
        """Generate Security section."""
        return """## Security
- OWASP ASVS L2 compliance required
- No hardcoded secrets (use environment variables)
- Input validation on all API endpoints
- SQL injection prevention via ORM
"""

    async def _generate_git_workflow(self, project_id: UUID) -> str:
        """Generate Git Workflow section."""
        return """## Git Workflow
- Branch: `feature/{ticket}-{description}`
- Commit: `feat|fix|chore(scope): message`
- PR: Must pass quality gates before merge
"""

    async def _generate_do_not(self, project_id: UUID) -> str:
        """Generate DO NOT section."""
        rules = [
            "- Add mocks or placeholders (Zero Mock Policy)",
            "- Skip tests for 'quick fixes'",
            "- Hardcode secrets or credentials",
            "- Use `// TODO` without ticket reference",
        ]

        # Check for AGPL containment
        if await self.file_analyzer.exists(project_id, "docker-compose.yml"):
            docker_content = await self.file_analyzer.read(project_id, "docker-compose.yml")
            if "minio" in docker_content.lower() or "grafana" in docker_content.lower():
                rules.append("- Import AGPL libraries (MinIO SDK, Grafana SDK) - use network-only")

        return f"""## DO NOT
{chr(10).join(rules)}
"""

    def _truncate_to_limit(self, content: str, max_lines: int) -> str:
        """Truncate content to max lines while preserving structure."""
        lines = content.split('\n')
        if len(lines) <= max_lines:
            return content

        # Keep header and truncate body
        truncated = lines[:max_lines - 1]
        truncated.append("\n<!-- Truncated to 150 lines. See docs for full details. -->")
        return '\n'.join(truncated)
```

### Day 3: AGENTS.md Validator (6 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `AgentsMdValidator` class | Backend | 2h | P0 | ⏳ |
| Forbidden content detection | Backend | 2h | P0 | ⏳ |
| Section structure validation | Backend | 2h | P0 | ⏳ |
| Unit tests (8 tests) | Backend | 2h | P0 | ⏳ |

**Implementation:**

```python
# backend/app/services/agents_md_validator.py
import re
from typing import List, Optional
from pydantic import BaseModel


class ValidationError(BaseModel):
    """Validation error."""
    severity: str  # "error" or "warning"
    message: str
    line_number: Optional[int] = None


class ValidationResult(BaseModel):
    """Validation result."""
    valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    line_count: int
    sections_found: List[str]


class AgentsMdValidator:
    """
    Validate AGENTS.md structure and content.

    Checks:
    - Line limit (≤150)
    - Forbidden content (secrets, credentials)
    - Required sections (recommended)
    - Markdown structure
    """

    # Patterns for forbidden content
    SECRET_PATTERNS = [
        r'(?i)api[_-]?key\s*[=:]\s*["\'][^"\']+["\']',
        r'(?i)password\s*[=:]\s*["\'][^"\']+["\']',
        r'(?i)secret\s*[=:]\s*["\'][^"\']+["\']',
        r'sk-[a-zA-Z0-9]{20,}',  # OpenAI-style keys
        r'ghp_[a-zA-Z0-9]{36}',  # GitHub PAT
        r'aws_[a-z_]+\s*=\s*["\'][A-Z0-9/+]{20,}["\']',  # AWS keys
    ]

    RECOMMENDED_SECTIONS = [
        "Quick Start",
        "Architecture",
        "Conventions",
        "Security",
        "DO NOT",
    ]

    def validate(self, content: str) -> ValidationResult:
        """
        Validate AGENTS.md content.

        Args:
            content: AGENTS.md file content

        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []
        lines = content.split('\n')
        line_count = len(lines)

        # Check line limit
        if line_count > 150:
            warnings.append(ValidationError(
                severity="warning",
                message=f"File exceeds recommended 150 lines ({line_count} lines)",
            ))

        # Check for forbidden content
        for i, line in enumerate(lines, 1):
            for pattern in self.SECRET_PATTERNS:
                if re.search(pattern, line):
                    errors.append(ValidationError(
                        severity="error",
                        message="Potential secret or credential detected",
                        line_number=i,
                    ))
                    break

        # Check for required sections
        sections_found = self._find_sections(content)
        for section in self.RECOMMENDED_SECTIONS:
            if section not in sections_found:
                warnings.append(ValidationError(
                    severity="warning",
                    message=f"Missing recommended section: {section}",
                ))

        # Check markdown structure
        structure_errors = self._validate_structure(content)
        errors.extend(structure_errors)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            line_count=line_count,
            sections_found=sections_found,
        )

    def _find_sections(self, content: str) -> List[str]:
        """Find all ## sections in content."""
        sections = []
        for match in re.finditer(r'^##?\s+(.+)$', content, re.MULTILINE):
            section_name = match.group(1).strip()
            sections.append(section_name)
        return sections

    def _validate_structure(self, content: str) -> List[ValidationError]:
        """Validate markdown structure."""
        errors = []

        # Check for title
        if not content.strip().startswith('#'):
            errors.append(ValidationError(
                severity="error",
                message="AGENTS.md must start with a title (# heading)",
                line_number=1,
            ))

        return errors
```

### Day 4-5: CLI Integration (8 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Add `sdlc agents init` command | Backend | 3h | P0 | ⏳ |
| Add `sdlc agents validate` command | Backend | 2h | P0 | ⏳ |
| Add `sdlc agents lint` command | Backend | 2h | P1 | ⏳ |
| CLI help and documentation | Backend | 1h | P0 | ⏳ |
| Integration tests (6 tests) | Backend | 3h | P0 | ⏳ |

**CLI Commands:**

```bash
# Generate AGENTS.md
$ sdlc agents init
✅ Generated AGENTS.md (142 lines)
   Sections: Quick Start, Architecture, Conventions, Security, DO NOT

# Validate existing AGENTS.md
$ sdlc agents validate
✅ AGENTS.md is valid
   📊 Lines: 142/150
   📋 Sections: 5 found
   ⚠️ Warning: Consider adding "Git Workflow" section

# Lint and auto-fix
$ sdlc agents lint --fix
🔧 Fixed 2 issues:
   - Trimmed trailing whitespace (line 45)
   - Added missing newline at end of file
```

### Day 6-7: Context Overlay Service (8 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `ContextOverlayService` | Backend | 4h | P1 | ⏳ |
| PR comment formatter | Backend | 3h | P1 | ⏳ |
| CLI context output | Backend | 2h | P1 | ⏳ |
| Unit tests (8 tests) | Backend | 3h | P0 | ⏳ |

**Implementation:**

```python
# backend/app/services/context_overlay_service.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


class SprintContext(BaseModel):
    """Sprint context for overlay."""
    id: Optional[UUID] = None
    number: Optional[int] = None
    goal: Optional[str] = None
    velocity: Optional[float] = None
    days_remaining: Optional[int] = None


class Constraint(BaseModel):
    """Active constraint."""
    type: str  # "strict_mode", "security_review", "agpl", "incident"
    severity: str  # "info", "warning", "error"
    message: str
    affected_files: List[str] = []


class ContextOverlay(BaseModel):
    """Dynamic context overlay (NOT committed to git)."""
    project_id: UUID
    generated_at: datetime
    stage_name: Optional[str] = None
    gate_status: Optional[str] = None
    sprint: Optional[SprintContext] = None
    constraints: List[Constraint] = []
    strict_mode: bool = False


class ContextOverlayService:
    """
    Generate dynamic context overlays.

    Implements ADR-029 Dynamic Overlay layer:
    - NOT committed to git
    - Delivered via PR comments, CLI, VS Code
    - Contains runtime constraints and context
    """

    def __init__(
        self,
        project_repo,
        gate_service,
        sprint_service,
        security_service,
    ):
        self.project_repo = project_repo
        self.gate_service = gate_service
        self.sprint_service = sprint_service
        self.security_service = security_service

    async def get_overlay(
        self,
        project_id: UUID,
    ) -> ContextOverlay:
        """
        Generate context overlay for project.

        Sources:
        - Current SDLC stage and gate
        - Active sprint context
        - Security constraints
        - Incident constraints
        """
        constraints = []

        # Get stage and gate
        stage = await self.gate_service.get_current_stage(project_id)
        gate_status = await self.gate_service.get_latest_gate_status(project_id)

        # Check strict mode (post-G3)
        strict_mode = False
        if gate_status and "G3" in gate_status and "PASSED" in gate_status:
            strict_mode = True
            constraints.append(Constraint(
                type="strict_mode",
                severity="warning",
                message="Post-G3: Only bug fixes allowed",
            ))

        # Get sprint context
        sprint = await self.sprint_service.get_active_sprint(project_id)
        sprint_context = None
        if sprint:
            sprint_context = SprintContext(
                id=sprint.id,
                number=sprint.number,
                goal=sprint.goal,
                velocity=sprint.velocity,
                days_remaining=sprint.days_remaining,
            )

        # Get security constraints
        security_issues = await self.security_service.get_active_issues(project_id)
        for issue in security_issues:
            constraints.append(Constraint(
                type="security_review",
                severity="error",
                message=f"Security issue: {issue.title}",
                affected_files=issue.affected_files,
            ))

        # AGPL containment (always active)
        constraints.append(Constraint(
            type="agpl",
            severity="info",
            message="AGPL: MinIO/Grafana network-only (no SDK imports)",
        ))

        return ContextOverlay(
            project_id=project_id,
            generated_at=datetime.utcnow(),
            stage_name=stage.name if stage else None,
            gate_status=gate_status,
            sprint=sprint_context,
            constraints=constraints,
            strict_mode=strict_mode,
        )

    def format_pr_comment(self, overlay: ContextOverlay) -> str:
        """
        Format overlay as PR comment.

        Uses structured HTML comment markers for parsing.
        """
        timestamp = overlay.generated_at.strftime('%b %d, %Y %H:%M UTC')

        # Constraints section
        constraints_text = ""
        for c in overlay.constraints:
            icon = {"info": "ℹ️", "warning": "⚠️", "error": "🔴"}.get(c.severity, "•")
            constraints_text += f"- {icon} **{c.type.replace('_', ' ').title()}**: {c.message}\n"
            if c.affected_files:
                for f in c.affected_files:
                    constraints_text += f"  - `{f}`\n"

        # Sprint section
        sprint_text = "N/A"
        if overlay.sprint:
            sprint_text = f"Sprint {overlay.sprint.number}"
            if overlay.sprint.goal:
                sprint_text += f" - {overlay.sprint.goal}"

        return f"""<!-- SDLC-CONTEXT-START -->
## 🎯 SDLC Context ({timestamp})

**Stage**: {overlay.stage_name or 'Unknown'} | **Gate**: {overlay.gate_status or 'N/A'} | **Sprint**: {sprint_text}

### Active Constraints
{constraints_text if constraints_text else "- None"}

---
*Generated by SDLC Orchestrator - [Dashboard](#)*
<!-- SDLC-CONTEXT-END -->"""

    def format_cli_output(self, overlay: ContextOverlay) -> str:
        """Format overlay for CLI output."""
        lines = [
            f"📍 Stage: {overlay.stage_name or 'Unknown'}",
            f"🚪 Gate: {overlay.gate_status or 'N/A'}",
            f"{'🔒 STRICT MODE' if overlay.strict_mode else ''}",
            "",
            "📋 Active Constraints:",
        ]

        for c in overlay.constraints:
            icon = {"info": "ℹ️", "warning": "⚠️", "error": "🔴"}.get(c.severity, "•")
            lines.append(f"  {icon} {c.message}")

        return "\n".join(lines)
```

### Day 8-9: Framework Deprecation (4 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Update SASE-Artifacts README | PM | 2h | P1 | ⏳ |
| Mark MTS/BRS/LPS as DEPRECATED | PM | 1h | P1 | ⏳ |
| Create migration guide | PM | 2h | P1 | ⏳ |
| Archive existing artifacts | PM | 1h | P1 | ⏳ |

**Migration Document:**

```markdown
# SASE Artifact Migration: MTS/BRS/LPS → AGENTS.md

## Summary
Per ADR-029, the following artifacts are DEPRECATED:
- MentorScript (MTS) → AGENTS.md "Conventions" section
- BriefingScript (BRS) → GitHub Issue template + AGENTS.md
- LoopScript (LPS) → AI coders generate own plans

## Migration Steps
1. Run `sdlc agents init` to generate AGENTS.md
2. Copy relevant conventions from MTS to AGENTS.md
3. Convert BRS to GitHub Issue template
4. Archive LPS files (historical reference only)

## Artifacts KEPT (Unchanged)
- CRP (Clarification Request Pack) - governance evidence
- MRP (Merge Readiness Pack) - governance evidence
- VCR (Verification Completion Report) - governance evidence
```

### Day 10: Testing & Documentation (4 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| End-to-end tests (4 tests) | Backend | 3h | P0 | ⏳ |
| API documentation update | Backend | 2h | P0 | ⏳ |
| Sprint 80 completion report | PM | 2h | P0 | ⏳ |
| Handoff to Sprint 81 | PM | 1h | P0 | ⏳ |

---

## 🔗 API Endpoints

```yaml
# Sprint 80 New Endpoints

# AGENTS.md Generator
POST /api/v1/projects/{project_id}/agents-md/generate:
  summary: Generate AGENTS.md from project configuration
  tags: [AGENTS.md]
  request:
    include_quick_start: boolean
    include_architecture: boolean
    max_lines: integer (default: 150)
  response:
    content: string
    line_count: integer
    sections: array[string]

# AGENTS.md Validator
POST /api/v1/agents-md/validate:
  summary: Validate AGENTS.md content
  tags: [AGENTS.md]
  request:
    content: string
  response:
    valid: boolean
    errors: array[ValidationError]
    warnings: array[ValidationError]

# Context Overlay
GET /api/v1/projects/{project_id}/context-overlay:
  summary: Get dynamic context overlay
  tags: [Context]
  response:
    stage_name: string
    gate_status: string
    constraints: array[Constraint]
    strict_mode: boolean

# Format for PR Comment
GET /api/v1/projects/{project_id}/context-overlay/pr-comment:
  summary: Get context overlay formatted as PR comment
  tags: [Context]
  response:
    comment: string (markdown)
```

---

## 🔒 Definition of Done

### Code Complete

- [ ] `AgentsMdService` with all generators
- [ ] `AgentsMdValidator` with forbidden content detection
- [ ] CLI commands: `sdlc agents init|validate|lint`
- [ ] `ContextOverlayService` with PR comment formatter
- [ ] Framework README updated (MTS/BRS/LPS deprecated)

### Tests

- [ ] Unit tests: 34+ new tests
- [ ] Integration tests: 6 tests (CLI, API)
- [ ] E2E tests: 4 tests (generate → validate → commit flow)
- [ ] Total coverage: 90%+

### Documentation

- [ ] ADR-029 CTO approved
- [ ] API documentation (OpenAPI)
- [ ] CLI help text
- [ ] Migration guide (MTS/BRS/LPS → AGENTS.md)

### Review

- [ ] Code review by Tech Lead
- [ ] CTO approval on ADR-029
- [ ] PR merged to main
- [ ] Staging deployment verified

---

## 📊 Metrics & Success Criteria

| Metric | Target | Notes |
|--------|--------|-------|
| AGENTS.md generation time | <2s | For typical project |
| Validation time | <500ms | For 150-line file |
| Test coverage | 90%+ | generators + validators |
| CLI usability | <5 commands | Complete workflow |

---

## 📝 SDLC 5.1.3 Compliance

| Pillar | Sprint 80 Implementation |
|--------|--------------------------|
| P5 (SASE Integration) | AGENTS.md replaces MTS/BRS/LPS |
| P4 (Quality Gates) | Context overlay enforces constraints |
| P7 (Documentation) | Migration guide + API docs |

---

## 🚀 Handoff to Sprint 81

### Expected Completion (Sprint 80)

- ✅ AGENTS.md Generator Service
- ✅ CLI integration (`sdlc agents`)
- ✅ Context Overlay Service
- ✅ MTS/BRS/LPS deprecated

### Sprint 81 Focus (Feb 17-28)

- ⏳ GitHub Check Run integration (post overlay)
- ⏳ VS Code Extension context panel
- ⏳ PR webhook → auto-post overlay
- ⏳ Multi-repo AGENTS.md management

---

## 🔴 Dependencies on Other Teams

| Dependency | Team | Status | Blocker? |
|------------|------|--------|----------|
| ADR-029 CTO Approval | CTO | ✅ APPROVED | ❌ Resolved |
| Evidence Vault asymmetric signing | Backend | ⏳ Sprint 79 | ❌ No |
| GitHub Check Run | Backend | ⏳ Sprint 79 | ❌ No |

---

## 📅 Daily Standup Schedule

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Feb 3-4 | AGENTS.md Generator | `AgentsMdService` complete |
| Feb 5 | Validator | `AgentsMdValidator` complete |
| Feb 6-7 | CLI Integration | `sdlc agents` commands |
| Feb 10-11 | Context Overlay | `ContextOverlayService` |
| Feb 12-13 | Framework Update | MTS/BRS/LPS deprecated |
| Feb 14 | Testing & Docs | Sprint completion |

---

**SDLC 5.1.3 | Sprint 80 | Stage 04 (BUILD)**

*G-Sprint Approval Required Before Sprint Start*
