# Sprint 174: Anthropic Best Practices Integration — CORRECTED Implementation Plan
## Methodology First, Tool Second (SDLC 6.1.0 Compliance)

**Date**: February 16, 2026  
**Sprint**: 174 (Feb 17-28, 2026)  
**Revised By**: CTO Nguyen Quoc Huy  
**Principle**: **SDLC Framework (methodology) → SDLC Orchestrator (automation)**

---

## 🚨 Why This Revision Is Necessary

**Original Plan Flaw**: Implemented Orchestrator features (CLAUDE.md, prompt caching, MCP) BEFORE defining Framework methodology.

**Consequence**: Tool-driven development instead of methodology-driven development.

**Framework-First Principle** (SDLC 6.1.0 Section 3.2):
> "Every capability in SDLC Orchestrator must first exist as a documented pattern in SDLC Enterprise Framework. The Framework is the source of truth; the Orchestrator is the automation layer."

---

## ✅ CORRECTED Implementation Sequence

### **PHASE 1: Framework Enhancements** (Days 1-3) — METHODOLOGY LAYER
*Define patterns BEFORE building tools*

#### Day 1: CLAUDE.md Methodology Documentation
**File**: `SDLC-Enterprise-Framework/03-AI-GOVERNANCE/07-CLAUDE-MD-STANDARD.md`

**Content**:
```markdown
# CLAUDE.md Standard for AI-Assisted Development
## Framework Version 6.0.5

### Purpose
CLAUDE.md is the canonical context document for AI coding assistants (Claude Code, Cursor, Copilot). It enables:
- Zero-to-productive onboarding (<10 minutes)
- Consistent AI guidance across team members
- Progressive disclosure (4 layers: Quickstart → Patterns → Architecture → Deep Dive)

### Three-Tier Structure

#### TIER 1: LITE (Startups, <10 team members)
**File**: `CLAUDE.md` (500-1,000 lines)
- Project overview + tech stack
- Quick start commands (dev/test/deploy)
- Top 5 architecture decisions
- Top 10 common tasks with file paths
- Emergency contacts

**Validation**: AI assistant can run dev server + find 3 key files in <5 min

#### TIER 2: PRO (SMBs, 10-100 team members)  
**File**: `CLAUDE.md` (1,500-3,000 lines)
- LITE content +
- Module-specific zones (6-10 modules)
- Common debugging patterns
- Test execution commands per module
- Onboarding checklist (5-7 tasks)

**Validation**: AI assistant can implement a small feature (<50 LOC) in <15 min

#### TIER 3: ENTERPRISE (Enterprises, 100+ team members)
**Files**: `CLAUDE.md` (2,000 lines) + `docs/CLAUDE/*.md` (10+ files)
- PRO content +
- Separate docs per major system (Gateway, Auth, Payment, Reporting)
- Cross-system dependencies
- Compliance checklists (SOC2, HIPAA, GDPR)
- Runbook library (20+ scenarios)

**Validation**: AI assistant can navigate 500K+ LOC codebase and locate root cause of production incident in <20 min

### Anthropic Validation
**Source**: Anthropic PDF (Data Infrastructure team, p. 2)
> "When new data scientists join the team, they're directed to use Claude Code to navigate their massive codebase. Claude Code reads their Claude.md files (documentation), identifies relevant files for specific tasks, explains data pipeline dependencies, and helps newcomers understand which upstream sources feed into dashboards. This replaces traditional data catalogs and discoverability tools."

**Learning**: CLAUDE.md must be:
1. **Living documentation** (updated every sprint)
2. **Progressive disclosure** (not a 10,000-line dump)
3. **Action-oriented** (file paths + commands, not philosophies)

### Integration with SDLC Orchestrator
Once this Framework standard exists, SDLC Orchestrator will:
1. Provide `CLAUDE.md` templates via `sdlcctl project init --tier=[lite|pro|enterprise]`
2. Validate CLAUDE.md structure via Quality Gate G1 (Consultation)
3. Auto-update CLAUDE.md sections from Evidence Vault metadata

### Success Metrics
- **Onboarding time reduction**: 50% (4 hours → 2 hours avg)
- **AI assistant accuracy**: >90% on "find file for task X" queries
- **Developer satisfaction**: >80% report "CLAUDE.md is my first reference"

### Next Steps
1. ✅ Document standard in Framework (this file)
2. ⏭️ Implement templates in Orchestrator (`backend/sdlcctl/templates/claude-md/`)
3. ⏭️ Add Quality Gate validation rule (`policy-packs/rego/claude-md-validation.rego`)
```

**Output**: Framework standard created FIRST

---

#### Day 2: Autonomous Codegen Methodology
**File**: `SDLC-Enterprise-Framework/03-AI-GOVERNANCE/08-AUTONOMOUS-CODEGEN-PATTERNS.md`

**Content**:
```markdown
# Autonomous Codegen with Quality Gates
## Framework Version 6.0.5

### Problem Statement
Traditional autonomous coding agents (e.g., Devin, AutoGPT, SWE-Agent) have **60-80% feature waste** because they lack Quality Gates. Code is generated without:
- Legal clearance (AGPL contamination risk)
- Security validation (vulnerabilities shipped to prod)
- Architectural alignment (technical debt accumulates)
- Evidence traceability (no audit trail)

### Anthropic's Two-Agent Pattern
**Source**: `anthropics/claude-quickstarts/autonomous-coding/`

**Architecture**:
1. **Initializer Agent** (Session 1):
   - Reads `app_spec.txt` (PRD)
   - Generates `feature_list.json` (200 test cases)
   - Sets up project structure + git
   - **Duration**: 10-20 minutes (one-time)

2. **Coding Agent** (Sessions 2+):
   - Picks up where previous session left off
   - Implements features one by one
   - Marks tests as passing in `feature_list.json`
   - Auto-continues between sessions (3s delay)
   - **Duration**: 5-10 minutes per feature

**Key Insight**: Progress persistence via `feature_list.json` + git commits enables **resumable** autonomous coding across multiple sessions.

### SDLC Enhancement: 4-Gate Quality Pipeline
**Improvement over Anthropic**: Add Quality Gates to catch issues BEFORE merge.

| Stage | Anthropic Pattern | SDLC Enhancement |
|-------|-------------------|------------------|
| **Spec → Features** | app_spec.txt → feature_list.json | Gate G1: Legal + Stakeholder review on spec |
| **Feature → Implementation** | Coding agent writes code | Gate G2: SAST + Security scan on generated code |
| **Implementation → Tests** | Agent marks tests passing | Gate G3: Coverage + Integration tests mandatory |
| **Tests → Merge** | Git commit | Gate G4: Human architect review (for changes >500 LOC) |

**Architecture Diagram**:
```
┌─────────────┐
│ app_spec.txt│──── Gate G1 (Legal + Stakeholder) ────┐
└─────────────┘                                         │
                                                        ▼
┌─────────────────────┐                         ┌──────────────┐
│ feature_list.json   │◄──── Initializer ───────│ APPROVED     │
│ (200 test cases)    │       Agent             └──────────────┘
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Feature #1          │──── Gate G2 (SAST) ────┐
│ (generated code)    │                         │
└─────────────────────┘                         ▼
         │                              ┌──────────────┐
         ├───── Gate G3 (Tests) ────────│ PASS         │
         │                              └──────────────┘
         ▼                                       │
┌─────────────────────┐                         │
│ Feature #2          │────────────────┐        │
│ (generated code)    │                │        │
└─────────────────────┘                │        ▼
         │                              │  ┌──────────────┐
         ▼                              ├──│ Gate G4      │
    ... Loop continues until           │  │ (Human Review)│
    all 200 features complete          │  └──────────────┘
                                        │         │
                                        │         ▼
                                        │  ┌──────────────┐
                                        └──│ MERGED       │
                                           └──────────────┘
```

### Security Model
**Anthropic**: Bash command allowlist (security.py)
```python
ALLOWED_COMMANDS = [
    "cd", "ls", "cat", "git", "touch", "mkdir", "mv", "cp", "rm",
    "npm", "python", "pip", "pytest", "node"
]
```

**SDLC Enhancement**: OPA policies + Evidence Vault
- Every bash command logged to Evidence Vault
- OPA policy evaluates risk (CRITICAL/HIGH/MEDIUM/LOW)
- CRITICAL commands (rm -rf, chmod 777) require human approval
- Command history available for compliance audit

### Integration with EP-06 Codegen
**Current state**: EP-06 generates code from IR (Intermediate Representation)
**Sprint 175 target**: Add autonomous loop on top of EP-06

```python
# Pseudo-code for Sprint 175
async def autonomous_codegen_loop(spec_file: Path, max_iterations: int = 100):
    # Step 1: Initializer agent (Gate G1)
    ir = await generate_ir_from_spec(spec_file)
    await submit_to_gate_g1(ir, stakeholders=["legal", "architect"])
    
    # Step 2: Coding agent loop
    iteration = 0
    while iteration < max_iterations:
        feature = ir.get_next_unimplemented_feature()
        if not feature:
            break
            
        # Generate code
        code = await ep06_codegen(feature)
        
        # Gate G2: SAST
        sast_result = await run_semgrep(code)
        if sast_result.has_critical_issues():
            await escalate_to_security_team(sast_result)
            continue
            
        # Gate G3: Tests
        test_result = await run_tests(code)
        if not test_result.passed():
            await refine_with_test_feedback(code, test_result)
            continue
            
        # Mark feature as complete
        ir.mark_feature_complete(feature.id)
        await git_commit(f"feat: {feature.name}")
        
        iteration += 1
    
    # Step 3: Gate G4 (human review if >500 LOC)
    if ir.total_loc() > 500:
        await create_merge_request_with_mrp()
    else:
        await auto_merge()
```

### Success Metrics
- **Feature waste reduction**: 60% → 30% (via Quality Gates)
- **Security vulnerability rate**: <2% of generated code has SAST issues
- **Human review burden**: Only triggered for >500 LOC changes (20% of features)
- **Time to first feature**: <30 minutes (from spec to deployed code)

### Risk Mitigation
| Risk | Mitigation |
|------|-----------|
| **Agent generates AGPL code** | Gate G1 blocks specs requesting AGPL libraries |
| **Agent bypasses tests** | Gate G3 enforces 80% coverage minimum |
| **Agent accumulates tech debt** | Gate G4: Human architect reviews large changes |
| **Agent costs spiral** | Prompt caching reduces cost by 8x |

### Rollout Plan
- **Sprint 174**: Document methodology (this file) + create ADR-055
- **Sprint 175**: Implement initializer agent with Gate G1 integration
- **Sprint 176**: Implement coding agent loop with Gates G2/G3
- **Sprint 177**: Full E2E test + pilot with internal projects

### Next Steps
1. ✅ Document methodology in Framework (this file)
2. ⏭️ Create ADR-055 in Orchestrator with architecture diagrams
3. ⏭️ Implement sprint-by-sprint (175-177)
```

**Output**: Autonomous codegen **methodology** documented BEFORE implementation

---

#### Day 3: MRP (Merge-Readiness Package) Methodology
**File**: `SDLC-Enterprise-Framework/02-Core-Methodology/07-MRP-TEMPLATE.md`

**Content**:
```markdown
# MRP: Merge-Readiness Package Template
## Framework Version 6.0.5

### Purpose
MRP (Merge-Readiness Package) is the artifact that proves a feature is ready for production. It replaces ad-hoc PR descriptions with structured evidence.

**Anthropic Inspiration**: Data Science team (PDF p. 11)
> "The team asks Claude Code to summarize completed work sessions and update documentation automatically."

**SDLC Innovation**: Extend session summaries → comprehensive merge package.

### MRP Structure (5 Sections)

#### Section 1: Change Summary
**What changed**: 3-5 bullet points, <100 words total
**Why it changed**: Link to Gate G1 approval (consultation evidence)
**Impact scope**: List of affected systems/APIs/tables

```markdown
### Change Summary
- Added prompt caching to EP-06 codegen API
- Integrated Redis cache with Anthropic cache_control
- Reduced codegen cost by 8x ($0.016 → $0.002 per request)

**Gate G1 Approval**: [Evidence ID: EVD-12345]
**Impact Scope**: 
  - Systems: EP-06 Codegen Service
  - APIs: `POST /api/v1/codegen/generate`
  - Dependencies: Redis 7.2+ required
```

#### Section 2: Evidence Vault References
**Required Evidence** (Gate-specific):
- Gate G1: Legal clearance + stakeholder sign-off
- Gate G2: SAST report (Semgrep) + dependency audit
- Gate G3: Test coverage report (>90%) + E2E test recordings
- Gate G4: Architect review notes + performance benchmarks

```markdown
### Evidence Vault References
| Gate | Evidence ID | Type | Status | Link |
|------|-------------|------|--------|------|
| G1 | EVD-12345 | Legal Clearance | APPROVED | [View] |
| G2 | EVD-12346 | Semgrep Report | PASS (0 critical) | [View] |
| G3 | EVD-12347 | Test Coverage | 94.2% | [View] |
| G4 | EVD-12348 | Perf Benchmark | Latency -200ms | [View] |
```

#### Section 3: Rollback Plan
**Rollback trigger**: Define failure conditions
**Rollback steps**: 1-2-3 instructions (executable by on-call engineer)
**Data migration**: If schema changed, document rollback migration

```markdown
### Rollback Plan
**Trigger**: Cache hit rate <50% OR latency increase >100ms

**Steps**:
1. `kubectl rollback deployment/codegen-service --to-revision=42`
2. `redis-cli -h redis.sdlc.svc -p 6379 FLUSHDB` (clear corrupted cache)
3. Monitor: `curl https://api.sdlc.dev/health` should return 200

**Data Migration**: N/A (cache-only, no persistent schema change)
```

#### Section 4: Testing Evidence
**Unit tests**: Coverage % + key test names
**Integration tests**: List of E2E scenarios + recordings
**Manual QA**: Screenshots/videos of critical flows

```markdown
### Testing Evidence
**Unit Tests**: 94.2% coverage (272 tests pass, 0 fail)
- `test_context_cache_hit_rate()` — validates 85% cache hit
- `test_cache_key_collision_prevention()` — ensures unique keys
- `test_redis_connection_retry()` — validates resilience

**Integration Tests**: 12 E2E scenarios (all pass)
- Scenario 1: Fresh codegen request (cache miss) → 1200ms
- Scenario 2: Repeated request (cache hit) → 180ms (-85% latency)

**Manual QA**: Video recording of EP-06 codegen workflow
[Screen recording: codegen-cache-demo.mp4]
```

#### Section 5: Deployment Notes
**Config changes**: New env vars, feature flags
**Deployment order**: If multi-service, document sequence
**Post-deployment validation**: Health check commands

```markdown
### Deployment Notes
**New Environment Variables**:
- `REDIS_CACHE_URL=redis://redis.sdlc.svc:6379/2`
- `PROMPT_CACHE_TTL_SECONDS=3600`

**Deployment Order**:
1. Deploy Redis cache (if not exists): `helm install redis bitnami/redis`
2. Deploy codegen-service: `kubectl apply -f k8s/codegen-service.yaml`
3. Run smoke test: `sdlcctl cache stats` should return non-zero hit count

**Post-Deployment Validation**:
```bash
# Check cache is operational
redis-cli -h redis.sdlc.svc PING
# Expected: PONG

# Check codegen service health
curl https://api.sdlc.dev/api/v1/codegen/health
# Expected: {"status": "healthy", "cache": "connected"}
```
```

### MRP Generation Workflow

#### Manual Generation (Sprint 174 baseline)
Engineer writes MRP in Markdown during PR creation.

#### Semi-Automated (Sprint 175 target)
```bash
sdlcctl mrp generate \
  --pr-number=1234 \
  --auto-evidence  # Pulls evidence from Vault
  --auto-tests     # Scrapes test reports
  --template=standard
```

Output: 80% pre-filled MRP, engineer reviews + adds rollback plan.

#### Fully Automated (Sprint 177 target)
Claude Code generates MRP from Evidence Vault + git history:
```bash
sdlcctl mrp auto-generate --pr-number=1234
```

AI assistant:
1. Reads PR commits + Evidence Vault
2. Generates Change Summary from commit messages
3. Links Evidence IDs from Gate approvals
4. Creates rollback plan from deployment history
5. Embeds test coverage reports
6. Outputs MRP draft for human approval

### Integration with Quality Gates
**Gate G4 requirement**: MRP must exist and be complete before merge approval.

**OPA Policy**:
```rego
package sdlc.gates.g4

deny[msg] {
  not input.mrp_exists
  msg := "Gate G4 BLOCKED: MRP (Merge-Readiness Package) not found. Run: sdlcctl mrp generate"
}

deny[msg] {
  input.mrp_exists
  not input.mrp_sections_complete
  msg := "Gate G4 BLOCKED: MRP incomplete. Missing sections: [ROLLBACK_PLAN, TESTING_EVIDENCE]"
}
```

### Success Metrics
- **MRP completion rate**: 100% of PRs >100 LOC have MRP
- **Rollback success rate**: >95% (clear instructions prevent mistakes)
- **Merge confidence**: Team survey shows >90% feel "confident merging with MRP"

### Next Steps
1. ✅ Document MRP template in Framework (this file)
2. ⏭️ Implement `sdlcctl mrp generate` command in Orchestrator
3. ⏭️ Add Gate G4 OPA policy requiring MRP
4. ⏭️ Train team on MRP workflow (Sprint 174 kickoff)
```

**Output**: MRP **methodology** documented BEFORE CLI implementation

---

### **PHASE 2: Orchestrator — CLAUDE.md Implementation** (Days 4-5) — AUTOMATION LAYER
*Now that Framework standard exists, implement in tool*

#### Day 4: Create CLAUDE.md for SDLC Orchestrator (PRO Tier)
**File**: `SDLC-Orchestrator/CLAUDE.md`

**Action**: Extend existing CLAUDE.md (currently 150 lines) → 2,000 lines (PRO tier)

**New sections to add** (following Framework standard from Day 1):

1. **Module Zone: Gate Engine API**
```markdown
## Module: Gate Engine API
**Purpose**: Quality Gate lifecycle management (DRAFT → EVALUATED → APPROVED/REJECTED)

**Key Files**:
- `backend/app/api/v1/endpoints/gates.py` — Gate CRUD endpoints
- `backend/app/services/gate_service.py` — Business logic
- `backend/app/services/opa_service.py` — Policy evaluation
- `backend/app/models/gate.py` — SQLAlchemy model

**State Machine**:
```
DRAFT ──submit──> EVALUATED ──approve──> APPROVED
                      │
                      └─reject──> REJECTED
                      │
                      └─stale (24h)──> EVALUATED_STALE
```

**Common Tasks**:
1. **Create new gate**:
   ```bash
   curl -X POST https://api.sdlc.dev/api/v1/gates \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"project_id": 1, "gate_type": "G1_CONSULTATION"}'
   ```

2. **Submit for evaluation**:
   ```bash
   curl -X POST https://api.sdlc.dev/api/v1/gates/{gate_id}/submit
   ```

3. **Check OPA policy result**:
   ```bash
   curl https://api.sdlc.dev/api/v1/gates/{gate_id}/policy-result
   ```

**Debugging**:
- **Issue**: BaseHTTPMiddleware hangs on FastAPI 0.100+
  - **Fix**: Downgrade to FastAPI 0.99 OR use pure ASGI middleware
  - **Root cause**: Starlette event loop conflict
  
- **Issue**: Redis mock failures in tests
  - **Fix**: Use `fakeredis` instead of `unittest.mock`
  - **Example**: See `tests/unit/test_gate_service.py:45`

**Tests**:
```bash
# Unit tests
DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
  python -m pytest tests/unit/test_gate_service.py -v

# E2E tests (full governance loop)
python -m pytest tests/e2e/test_governance_loop_e2e.py::test_g1_to_g4_flow -v
```

**Dependencies**:
- Upstream: PostgreSQL 15.5 (port 15432), Redis 7.2 (port 6395)
- Downstream: OPA 0.58 (port 8185), Evidence Vault (MinIO)
```

2. **Module Zone: Evidence Vault API** (similar structure)
3. **Module Zone: AI Context Engine** (similar structure)
4. **Module Zone: EP-06 Codegen Pipeline** (similar structure)
5. **Module Zone: SAST Integration** (similar structure)
6. **Module Zone: Frontend Dashboard** (similar structure)

**Verification**: AI assistant can navigate to any module's key files using CLAUDE.md alone (test with: "Find the file that handles Gate G2 security validation")

---

#### Day 5: Update SDLC Framework CLAUDE.md
**File**: `SDLC-Enterprise-Framework/CLAUDE.md`

**Action**: Create CLAUDE.md for Framework repo (LITE tier, since Framework is documentation-only)

**Content** (500-1,000 lines):
- Framework structure overview (7 pillars)
- How to navigate to specific methodology docs
- How to add new Framework content
- Quality Gate descriptions (G1-G4)
- AI Governance principles summary

---

### **PHASE 3: ADR Revision** (Day 6) — DOCUMENTATION LAYER
*Align ADR with actual Anthropic findings*

#### Day 6: Revise ADR-054
**File**: `docs/02-design/01-ADRs/ADR-054-Anthropic-Claude-Code-Best-Practices.md`

**Changes**:

1. **Add "Source Analysis" section** (after Status, before Context):
```markdown
## Source Analysis

### Primary Sources
1. **Anthropic Internal PDF**: "How Anthropic teams use Claude Code" (23 pages, 10 teams)
   - Data Infrastructure (p. 2-3): CLAUDE.md for onboarding
   - Product Development (p. 4-5): Multi-file editing
   - Security Engineering (p. 6-7): Screenshot-driven debugging
   - Inference (p. 8-9): Plain text workflows
   - Data Science (p. 10-11): End-of-session documentation
   - API (p. 12-13): Codebase navigation
   - Growth Marketing (p. 14-15): Non-technical user enablement
   - Product Design (p. 16-17): Rapid prototyping
   - RL Engineering (p. 18-19): Algorithm scaffolding
   - Legal (p. 20-21): Compliance validation

2. **GitHub Repository**: `anthropics/claude-quickstarts` (5 examples)
   - `agents/` (300 LOC): MCP connection management (stdio + SSE)
   - `autonomous-coding/` (500 LOC): Two-agent pattern + feature_list.json
   - `browser-use-demo/` (2,000 LOC): Playwright browser automation
   - `browser-use-demo/tests/` (300 LOC): Async integration testing
   - `agent_demo.ipynb` (200 LOC): Multi-tool ecosystem

3. **BFlow Analysis**: `BFLOW-CLAUDE-CODE-PRACTICES-NOTIFICATION-MAR2026.md` (9 items)
   - 6 items for Orchestrator (CLAUDE.md, Code Review, Test Gen, Studies, Browser E2E)
   - 3 items for Framework (CLAUDE.md Standard, AI Review, AI Governance)

### Analysis Methodology
- **CTO deep-dive**: 3 days (Feb 13-16, 2026)
- **Cross-referencing**: Validated patterns across all 3 sources
- **Prioritization**: RICE scoring (Reach × Impact × Confidence / Effort)
- **Sequencing**: Framework-first approach (methodology → tool)
```

2. **Restructure Pattern Sections**:
   - Clearly separate "Anthropic practices" from "SDLC innovations inspired by Anthropic"
   - Label Extended Thinking Pre-Flight and Progressive Disclosure as "inspired by" (not direct from Anthropic)

3. **Add cross-references**:
   - Link to CTO analysis: `docs/04-build/02-Sprint-Plans/CTO-ANTHROPIC-ANALYSIS-SPRINT-174.md`
   - Link to Framework standards created in Days 1-3

---

### **PHASE 4: Prompt Caching Implementation** (Days 7-8) — INFRASTRUCTURE LAYER
*Cost optimization infrastructure*

#### Day 7: Create Context Cache Service
**File**: `backend/app/services/context_cache_service.py`

**Implementation**:
```python
"""
Context caching service for Anthropic prompt caching.
Reduces EP-06 codegen costs by 8x via Redis-backed cache.

Based on:
- Framework: SDLC-Enterprise-Framework/03-AI-GOVERNANCE/06-PROMPT-CACHING-PATTERNS.md (if exists)
- Anthropic Docs: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
"""

import hashlib
import json
from typing import Dict, Any, Optional
from redis import Redis
from anthropic import Anthropic
from anthropic.types import CacheControlEphemeralParam

class SDLCContextCache:
    """
    Manages prompt caching for SDLC Orchestrator.
    
    Architecture:
    - L1 Cache: Redis (TTL 1 hour, fast lookups)
    - L2 Cache: Anthropic cache_control (TTL 5 minutes, API-level)
    """
    
    def __init__(self, redis_client: Redis, anthropic_client: Anthropic):
        self.redis = redis_client
        self.anthropic = anthropic_client
        self.cache_ttl = 3600  # 1 hour
        
    def generate_cache_key(self, context: Dict[str, Any]) -> str:
        """
        Generate deterministic cache key from context.
        
        Context includes:
        - CLAUDE.md content (or hash if >10KB)
        - Project structure (file tree)
        - Recent git commits (last 5)
        - Active feature flags
        """
        cache_input = json.dumps(context, sort_keys=True)
        return f"sdlc:context:v1:{hashlib.sha256(cache_input.encode()).hexdigest()}"
        
    async def get_cached_context(self, cache_key: str) -> Optional[str]:
        """Retrieve cached context from Redis."""
        cached = await self.redis.get(cache_key)
        if cached:
            return cached.decode('utf-8')
        return None
        
    async def cache_context(self, cache_key: str, context: str):
        """Store context in Redis with TTL."""
        await self.redis.setex(cache_key, self.cache_ttl, context.encode('utf-8'))
        
    def build_cached_prompt(self, system_prompt: str, use_anthropic_cache: bool = True):
        """
        Build prompt with Anthropic cache_control.
        
        Example:
        ```python
        system_prompt = [
            {"type": "text", "text": "You are SDLC Orchestrator..."},
            {
                "type": "text",
                "text": "<CODEBASE_CONTEXT>...</CODEBASE_CONTEXT>",
                "cache_control": {"type": "ephemeral"}  # Cache this!
            }
        ]
        ```
        """
        if not use_anthropic_cache:
            return system_prompt
            
        # Split prompt into cacheable (large/static) + dynamic (small)
        # Cacheable: CLAUDE.md, project structure
        # Dynamic: current task description
        
        return [
            {"type": "text", "text": system_prompt},
            {"type": "text", "text": "", "cache_control": {"type": "ephemeral"}}
        ]
```

**Tests**: `tests/unit/test_context_cache_service.py` (100 LOC)

---

#### Day 8: Integrate Caching into Codegen Service
**Files**:
- `backend/app/services/codegen/codegen_service.py` — Add caching
- `backend/sdlcctl/sdlcctl/commands/cache.py` — CLI for cache management
- `backend/sdlcctl/sdlcctl/cli.py` — Register cache commands

**Verification**:
```bash
# Clear cache
sdlcctl cache clear

# Generate code (cache miss, ~1500ms)
sdlcctl codegen generate --spec=spec.yaml

# Generate again (cache hit, ~300ms, -80%)
sdlcctl codegen generate --spec=spec.yaml

# Check stats
sdlcctl cache stats
# Output:
# Cache hit rate: 87.3%
# Total requests: 1,247
# Cache hits: 1,089
# Avg latency (hit): 285ms
# Avg latency (miss): 1,420ms
```

---

### **PHASE 5: MCP Service Upgrade** (Day 9) — INTEGRATION LAYER
*Align with Anthropic's AsyncExitStack pattern*

#### Day 9: Refactor MCP Service
**File**: `backend/app/services/mcp_service.py`

**Changes**:
1. Add `AsyncExitStack` for connection lifecycle management (from `agents/utils/connections.py`)
2. Ensure SSE transport support (alongside existing stdio)
3. Add integration tests for both transports

**Before** (current):
```python
# Simplified current implementation
class MCPService:
    async def connect_stdio(self, command: str, args: List[str]):
        # Manual connection management
        self.process = await asyncio.create_subprocess_exec(command, *args)
```

**After** (Day 9):
```python
from contextlib import AsyncExitStack

class MCPService:
    def __init__(self):
        self.stack = AsyncExitStack()
        
    async def connect_stdio(self, command: str, args: List[str]):
        # AsyncExitStack manages cleanup automatically
        connection = await self.stack.enter_async_context(
            MCPConnectionStdio(command=command, args=args)
        )
        return connection
        
    async def connect_sse(self, url: str, headers: Dict[str, str]):
        # SSE transport (new!)
        connection = await self.stack.enter_async_context(
            MCPConnectionSSE(url=url, headers=headers)
        )
        return connection
```

**Tests**: `tests/integration/test_mcp_service.py` (150 LOC)

---

### **PHASE 6: New ADRs + Prototypes** (Day 10) — EXPANSION LAYER
*Document future work*

#### Day 10 Morning: ADR-055 (Autonomous Codegen)
**File**: `docs/02-design/01-ADRs/ADR-055-Autonomous-Codegen-4-Gate-Validation.md`

**Content** (based on Framework doc from Day 2):
- Architecture comparison: Anthropic vs SDLC
- Integration with EP-06 Codegen Pipeline
- Sprint 175-177 implementation roadmap

#### Day 10 Afternoon: Browser Agent Prototype
**File**: `backend/app/services/browser_agent_service.py`

**Scope**: Basic Playwright integration (100 LOC prototype)
- Connect to Chromium
- Execute simple actions (navigate, click, screenshot)
- NOT full browser-use-demo (that's Sprint 176)

---

### **PHASE 7: Cleanup** (Day 10 End) — FINALIZATION LAYER

#### Update CURRENT-SPRINT.md
**File**: `docs/04-build/02-Sprint-Plans/CURRENT-SPRINT.md`

**Changes**:
- Remove stale Sprint 170 content
- Add clean Sprint 174 summary with links to:
  - Framework standards (Days 1-3)
  - CLAUDE.md (Days 4-5)
  - ADR-054 (revised, Day 6)
  - Prompt caching (Days 7-8)

#### Update ADR-054 Status
Change status from `DRAFT` → `APPROVED`

---

## Verification Checklist

### Framework-First Compliance
- [ ] **Day 1-3**: Framework standards created BEFORE Orchestrator implementation
- [ ] **Day 4-5**: Orchestrator CLAUDE.md follows Framework standard from Day 1
- [ ] **Day 6**: ADR-054 references Framework standards (not vice versa)
- [ ] **Day 7-8**: Prompt caching implementation follows Framework patterns (if exists)
- [ ] **Day 9**: MCP service upgrade documented in Framework first (if not, create retroactive doc)
- [ ] **Day 10**: ADR-055 references Framework autonomous codegen doc from Day 2

### Technical Validation
- [ ] CLAUDE.md has 6 module-specific zones with real file paths
- [ ] AI assistant can navigate to Gate G2 security validation files using CLAUDE.md alone
- [ ] Prompt caching: Cache hit rate >85% on 1000 test requests
- [ ] MCP service: Both stdio + SSE transports tested
- [ ] ADR-055 created with architecture comparison table
- [ ] Browser agent service: Basic Playwright integration working (navigate + screenshot)
- [ ] All existing tests pass: `python -m pytest tests/ -v`

### Documentation Quality
- [ ] Framework standards (Days 1-3) are production-ready (can be used by external adopters)
- [ ] CLAUDE.md is `TIER 2: PRO` level (1,500-3,000 lines)
- [ ] ADR-054 clearly distinguishes "Anthropic patterns" vs "SDLC innovations"
- [ ] CURRENT-SPRINT.md is clean and up-to-date

---

## Key Differences from Original Plan

| Aspect | Original Plan | Corrected Plan |
|--------|--------------|----------------|
| **Sequencing** | Tool → Methodology | ✅ Methodology → Tool |
| **Framework Work** | Day 10 (end) | ✅ Days 1-3 (start) |
| **CLAUDE.md** | Orchestrator-only | ✅ Framework standard + Orchestrator impl |
| **ADR-055** | Standalone doc | ✅ Based on Framework doc from Day 2 |
| **Validation** | Code works | ✅ Framework compliance + code works |

---

## Dependencies

### Infrastructure
- [ ] Redis running on port 6395 (for prompt caching)
- [ ] Anthropic API key with `cache_control` support
- [ ] Playwright + Chromium Docker image (for browser agent)

### Repositories
- [ ] `SDLC-Enterprise-Framework` submodule checked out at `main`
- [ ] `SDLC-Orchestrator` on Sprint 174 branch

### Team Alignment
- [ ] CTO approval on methodology-first sequencing ✅ (this doc)
- [ ] Framework reviewers assigned (for Days 1-3 PRs)
- [ ] Orchestrator reviewers assigned (for Days 4-10 PRs)

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Framework PRs block Orchestrator work** | HIGH | Days 1-3 Framework PRs must be reviewed same-day |
| **CLAUDE.md scope creep** (>3,000 lines) | MEDIUM | Timebox to 2,000 lines, defer extra content to Sprint 175 |
| **Prompt caching savings <85%** | MEDIUM | If <70%, escalate to Anthropic support; if 70-85%, acceptable |
| **MCP refactor breaks existing integrations** | HIGH | Run full E2E test suite on Day 9; rollback if failures |

---

## Success Metrics (Sprint 174)

### Framework Metrics
- [ ] 3 new Framework docs created (CLAUDE.md Standard, Autonomous Codegen, MRP)
- [ ] Framework docs used by ≥1 external team (soft launch cohort)

### Orchestrator Metrics
- [ ] CLAUDE.md onboarding time: 4 hours → 2 hours (50% reduction)
- [ ] Prompt caching hit rate: >85%
- [ ] Prompt caching cost reduction: $0.016 → $0.002 per request (87.5% savings)
- [ ] MCP service: 0 connection failures in 1000 test connections

### Team Metrics
- [ ] Developer satisfaction: Survey shows >80% find CLAUDE.md helpful
- [ ] Sprint 174 velocity: 90% of planned stories completed
- [ ] Zero production incidents from Sprint 174 changes

---

## Next Steps (Post-Sprint 174)

### Sprint 175
- [ ] BFlow pilots Code Review Automation + Test Generation
- [ ] Implement initializer agent (autonomous codegen Phase 1)
- [ ] Full MRP CLI implementation (`sdlcctl mrp generate`)

### Sprint 176
- [ ] Full Browser E2E implementation (Playwright across all projects)
- [ ] Implement coding agent loop (autonomous codegen Phase 2)

### Sprint 177
- [ ] Autonomous codegen E2E testing + pilot
- [ ] Public release of Framework 6.1.0 with Anthropic patterns
- [ ] Soft launch SDLC Orchestrator with autonomous codegen

---

**CTO Approval**: ✅ Nguyen Quoc Huy  
**Framework-First Compliance**: ✅ VERIFIED  
**Ready for Sprint 174 Kickoff**: ✅ YES  
**Date**: February 16, 2026
