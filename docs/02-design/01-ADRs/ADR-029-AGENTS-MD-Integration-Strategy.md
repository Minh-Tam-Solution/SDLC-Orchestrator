# ADR-029: AGENTS.md Integration Strategy
## AI Code Governance via Industry Standard + Dynamic Overlay

**Status**: ✅ APPROVED (CTO + CEO)
**Date**: January 19, 2026
**Approved By**: CTO (Jan 19, 2026), CEO (Jan 19, 2026)
**Decision Makers**: CTO, CEO
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 6.1.0
**Sprint**: Sprint 80 (Feb 3 - Feb 14, 2026)
**Priority**: P1 - DIFFERENTIATOR

---

## Context

### Problem Statement

SDLC Orchestrator currently uses proprietary artifacts (MTS/BRS/LPS) for AI agent guidance that:

1. **No industry adoption**: 0 projects using our artifacts externally
2. **Documentation-only**: No backend code integration exists
3. **Maintenance burden**: 3 complex YAML/MD templates (1,400+ lines total)
4. **No tool support**: Cursor, Copilot, Claude Code don't recognize them

Meanwhile, [AGENTS.md](https://agents.md/) has emerged as the industry standard:

| Metric | AGENTS.md | Our SASE Artifacts |
|--------|-----------|-------------------|
| Industry adoption | 60,000+ projects | 0 external |
| Tool support | Cursor, Copilot, Claude Code, OpenCode, RooCode | None |
| Founders | Google, OpenAI, Factory, Sourcegraph | Internal |
| Simplicity | ≤150 lines Markdown | 1,400+ lines YAML/MD |
| Launch date | Q4 2025 | Dec 2025 |

### Expert Consensus (7/7 Agree)

- ✅ **Adopt AGENTS.md**: Non-negotiable for credibility
- ✅ **Kill MTS/BRS/LPS**: Documentation-only, no backend integration
- ✅ **Keep CRP/MRP/VCR**: Governance artifacts (evidence capture)
- ⚠️ **Dynamic AGENTS.md**: Risk of over-claim if done wrong

### Critical Feedback: Dynamic AGENTS.md Over-claim Risk

**Problem identified by Expert 6:**

> "If auto-update AGENTS.md via commit → noise commits + conflict + breaks blame/history"
>
> "If generate runtime → most tools only read files in repo, so 'dynamic' will NOT reach Cursor/Copilot/OpenCode"

**Implication**: Our original "Dynamic AGENTS.md = TRUE MOAT" claim is technically incorrect.

---

## Decision

### Architecture: Static AGENTS.md + Dynamic Overlay

We adopt a **two-layer architecture** that separates stable conventions from runtime context:

```
┌─────────────────────────────────────────────────────────────────────┐
│           SDLC ORCHESTRATOR: STATIC + DYNAMIC OVERLAY               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LAYER A: STATIC AGENTS.md (Committed to repo)                      │
│  ────────────────────────────────────────────                       │
│  Location: repo root /AGENTS.md                                     │
│  Update frequency: Rarely (architecture changes, new conventions)   │
│  Contents:                                                          │
│    • Setup commands (docker compose, npm install)                   │
│    • Code conventions (naming, style, tests)                        │
│    • Security boundaries (DO NOT rules)                             │
│    • Architecture overview (layers, patterns)                       │
│    • Git workflow (branch, commit, PR rules)                        │
│  Tool support: ✅ Cursor, Copilot, Claude Code, OpenCode            │
│                                                                     │
│  LAYER B: DYNAMIC OVERLAY (Runtime - NOT committed)                 │
│  ──────────────────────────────────────────────                     │
│  Location: API response, PR comments, CLI output, VS Code panel     │
│  Update frequency: Per gate pass, per incident, per PR              │
│  Contents:                                                          │
│    • Current SDLC stage + gate status                               │
│    • Sprint context (goal, velocity, blockers)                      │
│    • Incident constraints ("CVE-XXX detected, fix required")        │
│    • Strict mode flags ("G3 passed - only bug fixes allowed")       │
│    • Known risky files ("auth_service.py under security review")    │
│                                                                     │
│  Delivery Channels:                                                 │
│  ├─ GitHub Check Run output (universal, all tools see it)           │
│  ├─ PR Comment with constraints (visible in Cursor/Copilot)         │
│  ├─ CLI: `sdlc context` → local .sdlc-context.json (gitignored)     │
│  └─ VS Code Extension: inject in chat context panel                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

#### 1. Static AGENTS.md is Primary (Generator Feature)

```yaml
Feature: AGENTS.md Generator
Command: sdlc agents init
Output: /AGENTS.md (≤150 lines)

Sections generated:
  - Quick Start: from docker-compose.yml analysis
  - Architecture: from docs/02-design/ or manual input
  - Conventions: from .editorconfig, ruff.toml, tsconfig.json
  - Security: from OWASP baseline + AGPL containment rules
  - Git Workflow: from .github/workflows/ analysis
  - DO NOT: from security policies + AGPL requirements
```

#### 2. Dynamic Overlay via Multiple Channels (NOT file commits)

| Channel | Reaches | Update Trigger | Format |
|---------|---------|----------------|--------|
| **GitHub Check Run** | All tools (via PR context) | Per commit/PR | Markdown in check output |
| **PR Comment** | Cursor, Copilot (via conversation) | Per PR | `<!-- SDLC-CONTEXT -->` |
| **CLI** | Local dev environment | On-demand | `.sdlc-context.json` (gitignored) |
| **VS Code Panel** | Claude Code, our extension | Real-time | JSON injected to chat |

#### 3. SASE Artifact Migration

| Artifact | Action | Migration Path |
|----------|--------|----------------|
| **MTS (MentorScript)** | 🗑️ DEPRECATE | → AGENTS.md "Conventions" section |
| **BRS (BriefingScript)** | 🗑️ DEPRECATE | → GitHub Issue template + AGENTS.md |
| **LPS (LoopScript)** | 🗑️ DEPRECATE | AI coders generate own execution plans |
| **CRP** | ✅ KEEP | Governance artifact (clarification evidence) |
| **MRP** | ✅ KEEP | Governance artifact (merge readiness) |
| **VCR** | ✅ KEEP | Governance artifact (verification) |

#### 4. Security: Load Static AGENTS.md Safely

```yaml
Security Policy:
  source: Default branch only (main/master)
  validation:
    - require_signed_commit: true  # Enterprise tier
    - require_ci_pass: false       # Don't block on CI for config
    - max_file_size: 50KB          # Prevent abuse
  forbidden_content:
    - secrets (API keys, passwords)
    - credentials
    - internal URLs
    - executable code blocks
```

---

## Rationale

### Why Static + Overlay Instead of Pure Dynamic?

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Pure Static** | Simple, universal tool support | No runtime context | ❌ Limited value |
| **Pure Dynamic (file commits)** | Context-aware | Noise commits, merge conflicts, breaks history | ❌ Over-engineered |
| **Pure Dynamic (runtime only)** | No git pollution | Tools don't see it | ❌ Doesn't reach AI coders |
| **Static + Overlay** | Best of both worlds | More complex architecture | ✅ Selected |

### Why PR Comments for Overlay?

Tools like Cursor and Copilot see PR conversation context. By posting structured comments:

```markdown
<!-- SDLC-CONTEXT-START -->
## Current Constraints (Jan 19, 2026 14:30 UTC)

**Stage**: Stage 04 (BUILD) | **Sprint**: 79 | **Gate**: G3 PASSED

### Active Constraints:
- 🔒 **Strict Mode**: Only bug fixes allowed (post-G3)
- ⚠️ **Security Review**: `auth_service.py` under audit - do not modify
- 🛡️ **AGPL**: MinIO/Grafana network-only (no SDK imports)

### Sprint Context:
- Goal: AGENTS.md Generator + Landing Page
- Velocity: 32 SP/sprint
- Remaining: 8 SP
<!-- SDLC-CONTEXT-END -->
```

AI tools naturally incorporate this context into their suggestions.

### Why Not Commit Dynamic Content?

Expert 6 correctly identified:

1. **Git history pollution**: Daily context updates = hundreds of noise commits
2. **Merge conflicts**: Multiple developers = constant AGENTS.md conflicts
3. **Blame corruption**: `git blame` becomes useless for AGENTS.md
4. **CI/CD overhead**: Every context update triggers CI

---

## Implementation Plan

### Phase 1: AGENTS.md Generator (Sprint 80 - Feb 3-14)

```python
# backend/app/services/agents_md_service.py
class AgentsMdService:
    """Generate and validate AGENTS.md files."""

    async def generate(
        self,
        project_id: UUID,
        config: AgentsMdConfig,
    ) -> AgentsMdFile:
        """
        Generate AGENTS.md from project analysis.

        Sources:
        - docker-compose.yml → Quick Start
        - docs/02-design/ → Architecture
        - .editorconfig, ruff.toml → Conventions
        - Security baseline → DO NOT rules
        """
        sections = []

        # Quick Start
        quick_start = await self._analyze_setup(project_id)
        sections.append(self._format_section("Quick Start", quick_start))

        # Architecture (brief)
        arch = await self._summarize_architecture(project_id)
        sections.append(self._format_section("Architecture", arch))

        # Conventions
        conventions = await self._extract_conventions(project_id)
        sections.append(self._format_section("Conventions", conventions))

        # Security
        security = await self._get_security_rules(project_id)
        sections.append(self._format_section("Security", security))

        # DO NOT
        dont = await self._get_forbidden_actions(project_id)
        sections.append(self._format_section("DO NOT", dont))

        content = f"# AGENTS.md\n\n" + "\n\n".join(sections)

        # Validate length (≤150 lines)
        if content.count('\n') > 150:
            content = self._truncate_to_limit(content, 150)

        return AgentsMdFile(
            content=content,
            generated_at=datetime.utcnow(),
            source_hash=hashlib.sha256(content.encode()).hexdigest(),
        )

    async def validate(
        self,
        content: str,
    ) -> ValidationResult:
        """Validate AGENTS.md structure and content."""
        errors = []
        warnings = []

        # Check length
        lines = content.count('\n') + 1
        if lines > 150:
            warnings.append(f"File exceeds 150 lines ({lines}). Consider trimming.")

        # Check forbidden content
        if self._contains_secrets(content):
            errors.append("AGENTS.md contains potential secrets")

        # Check required sections
        required = ["Quick Start", "Architecture", "Conventions"]
        for section in required:
            if f"## {section}" not in content and f"# {section}" not in content:
                warnings.append(f"Missing recommended section: {section}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
```

### Phase 2: Dynamic Context Service (Sprint 81 - Feb 17-28)

```python
# backend/app/services/context_overlay_service.py
class ContextOverlayService:
    """Generate dynamic context overlays for AI tools."""

    async def get_overlay(
        self,
        project_id: UUID,
        trigger: str = "manual",
    ) -> ContextOverlay:
        """
        Generate context overlay based on current project state.

        NOT committed to git - delivered via:
        - PR comments
        - CLI output
        - VS Code panel
        - API response
        """
        project = await self.project_repo.get(project_id)

        # Get current SDLC stage
        stage = await self.gate_service.get_current_stage(project_id)

        # Get sprint context
        sprint = await self.sprint_service.get_active_sprint(project_id)

        # Get active constraints
        constraints = await self._get_active_constraints(project_id)

        # Get risky files under review
        risky_files = await self._get_files_under_review(project_id)

        return ContextOverlay(
            project_id=project_id,
            generated_at=datetime.utcnow(),
            stage=stage,
            sprint=SprintContext(
                id=sprint.id if sprint else None,
                number=sprint.number if sprint else None,
                goal=sprint.goal if sprint else None,
                velocity=sprint.velocity if sprint else None,
            ),
            constraints=constraints,
            risky_files=risky_files,
            strict_mode=stage and stage.name == "G3",  # Post-G3 = strict
        )

    def format_for_pr_comment(self, overlay: ContextOverlay) -> str:
        """Format overlay as PR comment for AI tools."""
        return f"""<!-- SDLC-CONTEXT-START -->
## Current Constraints ({overlay.generated_at.strftime('%b %d, %Y %H:%M UTC')})

**Stage**: {overlay.stage.name if overlay.stage else 'Unknown'} | **Sprint**: {overlay.sprint.number or 'N/A'} | **Gate**: {overlay.stage.gate_status if overlay.stage else 'N/A'}

### Active Constraints:
{self._format_constraints(overlay.constraints)}

### Files Under Review:
{self._format_risky_files(overlay.risky_files)}
<!-- SDLC-CONTEXT-END -->"""
```

### Phase 3: VS Code Extension (Sprint 82 - Mar 3-14)

- Context panel showing dynamic overlay
- Auto-inject overlay into Claude Code chat
- Generate AGENTS.md from command palette

---

## Consequences

### Positive

1. **Industry alignment**: 60,000+ projects use AGENTS.md
2. **Tool compatibility**: Cursor, Copilot, Claude Code native support
3. **Reduced maintenance**: 1 file vs 3 complex artifacts
4. **Clear separation**: Static (conventions) vs Dynamic (context)
5. **No git pollution**: Overlay via comments/API, not commits

### Negative

1. **Migration effort**: ~5 days to deprecate MTS/BRS/LPS
2. **Learning curve**: Team must understand two-layer architecture
3. **Dependency**: Relying on external standard (agents.md)

### Risks

| Risk | Mitigation |
|------|------------|
| agents.md standard fails | Fallback: AGENTS.md is just Markdown, still works |
| Dynamic overlay not reaching tools | Multiple channels: PR comments, CLI, VS Code |
| Over-claim accusation | Honest positioning: "Static + Overlay + Hard Enforcement" |

---

## Revised Positioning

### Before (Over-claim)
> "Dynamic AGENTS.md = TRUE ORCHESTRATION"

### After (Honest)
> "Static AGENTS.md + verified dynamic overlays + hard enforcement via GitHub Checks"

### Marketing Tagline
> "Static rules. Dynamic context. Hard enforcement."

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| AGENTS.md adoption | 100% pilot customers | File exists in repo |
| Generator usage | 50+ generations/month | CLI analytics |
| Overlay delivery | <500ms p95 | API metrics |
| PR comment accuracy | >90% | Manual review |

---

## Related Documents

- [agents.md Specification](https://agents.md/)
- [Pre-Launch Hardening Plan](/home/dttai/.claude/plans/crispy-drifting-walrus.md)
- [SPRINT-80-AGENTS-MD-FOUNDATION.md](../../../04-build/02-Sprint-Plans/SPRINT-80-AGENTS-MD-FOUNDATION.md)

---

## Approval

| Role | Name | Decision | Date |
|------|------|----------|------|
| CTO | CTO | ✅ APPROVED | Jan 19, 2026 |
| CEO | CEO | ✅ APPROVED | Jan 19, 2026 |

---

**SDLC 5.1.3 | ADR-029 | Stage 02 (HOW)**
