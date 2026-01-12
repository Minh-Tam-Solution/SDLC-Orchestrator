# OpenCode Setup Instructions - ACTUAL (CLI Tool, NOT Server)

**Date**: January 12, 2026
**Owner**: Backend Lead
**Discovery**: OpenCode is a CLI/TUI tool (like Claude Code), NOT an API server
**OpenCode Location**: `/home/nqh/shared/opencode`

---

## 🚨 IMPORTANT DISCOVERY

**ADR-026 Assumption**: We assumed OpenCode has "Server Mode" for API integration (based on expert analysis).

**Reality**: OpenCode is a **CLI/TUI tool** (Terminal UI) similar to Claude Code, NOT an HTTP API server.

**Implications**:
- ❌ No REST API endpoints (`/api/v1/feature`, `/health`)
- ❌ No Docker server mode setup
- ✅ Interactive terminal interface (like `cursor`, `claude code`)
- ✅ Client/server architecture exists BUT for remote control of CLI (mobile app → desktop CLI)
- ✅ Architecture: TypeScript/Bun monorepo with packages

---

## 🔍 What OpenCode Actually Is

Based on `/home/nqh/shared/opencode`:

**Type**: AI-powered CLI coding agent (TUI interface)
**Language**: TypeScript (Bun runtime)
**Architecture**: Monorepo with multiple packages
**Similar To**: Claude Code, Cursor (AI coding assistants)

**Key Features** (from README):
- 100% open source (MIT license)
- Provider-agnostic (Claude, OpenAI, Google, local models)
- Built-in LSP support
- Terminal UI focused (built by neovim users)
- Client/server architecture (for remote control)

**Built-in Agents**:
- **build** - Full access agent for development work
- **plan** - Read-only agent for analysis/exploration
- **general** - Subagent for complex searches (invoked via `@general`)

---

## ✅ Correct Setup Steps (CLI Installation)

### Step 1: Install OpenCode CLI (5-10 minutes)

Since repository is already cloned at `/home/nqh/shared/opencode`, we can:

**Option A: Install via Package Manager (Recommended)**
```bash
# Using Homebrew (recommended, always up to date)
brew install anomalyco/tap/opencode

# Verify installation
opencode --version
which opencode
```

**Option B: Build from Source**
```bash
cd /home/nqh/shared/opencode

# Install Bun (if not already installed)
curl -fsSL https://bun.sh/install | bash

# Install dependencies
bun install

# Build OpenCode
bun run dev

# OR use the package directly
cd packages/opencode
bun src/index.ts
```

**Option C: Use Install Script**
```bash
curl -fsSL https://opencode.ai/install | bash

# Or with custom directory
OPENCODE_INSTALL_DIR=/usr/local/bin curl -fsSL https://opencode.ai/install | bash
```

---

### Step 2: Configure OpenCode (5 minutes)

**Set Up API Keys** (for AI providers):
```bash
# Configure OpenCode (interactive setup)
opencode config

# OR set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
# OR use OpenCode Zen (recommended by OpenCode team)
```

**Check Configuration**:
```bash
# View current config
opencode config --list

# Test OpenCode
opencode --help
```

---

### Step 3: Run First Interactive Session (10-15 minutes)

**Start OpenCode**:
```bash
cd /home/nqh/shared/opencode-test-project
mkdir -p /home/nqh/shared/opencode-test-project
cd /home/nqh/shared/opencode-test-project

# Start OpenCode CLI
opencode
```

**Interactive Commands** (inside OpenCode TUI):
```
# Task 1: Simple function
> Create a Python function that adds two numbers

# Task 2: FastAPI CRUD (as in ADR-026)
> Create a FastAPI endpoint for user CRUD operations with:
- POST /users (create user: name, email)
- GET /users/{user_id}
- PUT /users/{user_id}
- DELETE /users/{user_id}
- Use Pydantic models
- Return proper status codes (201, 200, 404)
- In-memory storage (no database)
```

**Expected Behavior**:
- OpenCode will generate code files directly
- Files created in current directory
- Interactive TUI for approving changes
- Can switch between agents (Tab key: build ↔ plan)

---

## 📊 Evaluation Metrics (Adjusted for CLI Tool)

### Quality Assessment

**Syntax (Gate 1)**:
```bash
# After OpenCode generates code
python -m py_compile *.py
ruff check *.py
mypy *.py
```

**Functionality (Gate 2)**:
```bash
# Test generated FastAPI code
uvicorn main:app --reload

# Test endpoints
curl -X POST http://localhost:8000/users -d '{"name":"John","email":"john@example.com"}'
curl http://localhost:8000/users/1
```

**Latency (Target: <30s)**:
```bash
# Measure time to generate
time opencode < task1-prompt.txt
```

**Code Quality (Gate 4)**:
- Review generated code manually
- Check for best practices
- Verify error handling
- Assess maintainability

---

## 🔄 Revised ADR-026 Implications

### CRITICAL FINDING

**Original ADR-026 Assumption**:
> "OpenCode Server Mode: HTTP API for external tool integration with self-healing loop (auto-fix failing tests, max 3 retries)"

**Reality Check**:
- ❌ No "Server Mode" HTTP API exists (as of January 2026)
- ❌ Cannot integrate via REST endpoints
- ✅ OpenCode IS a CLI tool (competitor to Claude Code/Cursor)
- ✅ Client/server architecture exists for remote control (mobile → CLI)

### Integration Scenarios (Revised)

**Option 1: CLI Wrapper Integration** (Low complexity)
- SDLC Orchestrator spawns `opencode` CLI subprocess
- Pass prompts via stdin/file
- Capture generated code from filesystem
- **Pros**: No OpenCode modification needed
- **Cons**: Limited control, no retry loop, hard to sandbox

**Option 2: Fork OpenCode + Add API Layer** (High complexity)
- Fork OpenCode repository
- Add HTTP API server package (Express/Fastapi)
- Expose code generation as REST endpoints
- **Pros**: Full control, retry loop, sandboxing
- **Cons**: Maintenance burden, diverges from upstream

**Option 3: Use OpenCode as Layer 5 (External Tool)** (ADR-026 as-is)
- Position OpenCode as external AI coder (like Cursor/Claude Code)
- SDLC Orchestrator reviews OpenCode-generated PRs via 4-Gate pipeline
- **Pros**: Minimal integration, preserve provider-agnostic architecture
- **Cons**: No direct control over generation process

---

## 🚨 RECOMMENDED NEXT STEPS

### Immediate (Week 1-2)

**1. Test OpenCode CLI** (Backend Lead - Jan 13-15)
```bash
# Install OpenCode
brew install anomalyco/tap/opencode

# Run 5-sample benchmark manually
cd /home/nqh/shared/opencode-evaluation
opencode

# Interactive prompts:
- Task 1: FastAPI CRUD (as in ADR-026)
- Task 2: React component with state
- Task 3: Multi-file auth flow
- Task 4: Bug fix with tests
- Task 5: Performance optimization
```

**2. Document Actual Architecture** (Backend Lead - Jan 16)
- Review `/home/nqh/shared/opencode/packages/` structure
- Identify core generation logic
- Check for API extensibility points
- Document findings in Week 1-2 report

**3. Escalate to CTO** (PM/PO - Jan 17 @ 3pm)
- Present discovery: OpenCode is CLI tool, not API server
- Discuss integration options (CLI wrapper vs Fork vs External tool)
- Re-evaluate ADR-026 Level 1 feasibility ($30K pilot scope)

---

## 📋 Revised Week 1-2 Report Template

```markdown
# OpenCode Level 0 - Week 1-2 Report (REVISED)

**Date**: January 17, 2026
**Evaluator**: Backend Lead
**Status**: Week 1-2 Complete

## CRITICAL DISCOVERY

**Assumption**: OpenCode has "Server Mode" HTTP API
**Reality**: OpenCode is a CLI/TUI tool (like Claude Code)

### Architecture (Actual)

- **Type**: AI coding agent (CLI/TUI interface)
- **Language**: TypeScript (Bun runtime)
- **License**: MIT (commercially friendly)
- **Repository Structure**: Monorepo (`packages/opencode`, `packages/console`, etc.)
- **Built-in Agents**: build (full access), plan (read-only), general (subagent)
- **Client/Server**: For remote control (mobile → CLI), NOT HTTP API

### Integration Implications

| Scenario | Feasibility | Effort | ADR-026 Alignment |
|----------|-------------|--------|-------------------|
| CLI Wrapper | ✅ Low | 2-4 weeks | Partial (no retry loop) |
| Fork + API Layer | ⚠️ High | 8-12 weeks | Full (custom API) |
| External Tool (Layer 5) | ✅ Low | 0 weeks | Full (as-is) |

## Sample Task 1: FastAPI CRUD (CLI-based)

| Metric | Result | Notes |
|--------|--------|-------|
| **Generation** |
| Latency | Xs | Interactive CLI (no batch mode) |
| Status | ✅/❌ | Manual approval required |
| **Quality** |
| Syntax | ✅/❌ | Python AST validates? |
| Functionality | X/4 endpoints | POST, GET, PUT, DELETE |
| Security | ✅/❌ | Pydantic validation present? |
| Code Quality | X/5 | Readability, maintainability |

## Recommendation for CTO

**Preliminary Assessment**: [PROMISING / BLOCKED / PIVOT_NEEDED]

**Options**:
1. **Continue as CLI Tool** (Level 0 only, no pilot integration)
   - Use OpenCode as external AI coder (like Cursor)
   - SDLC Orchestrator reviews OpenCode-generated PRs
   - Budget: $0 (no integration, observation only)

2. **Fork + Custom API** (Level 1 modified)
   - Fork OpenCode, add HTTP API layer
   - Requires significant engineering effort (8-12 weeks)
   - Budget: $50K-$80K (not $30K as planned)

3. **Abort OpenCode Integration** (Exit Level 0)
   - Focus on Vibecode CLI (IR-based codegen)
   - Allocate $30K budget to EP-06 enhancements
   - OpenCode remains competitor, not integration target

**Recommended**: [Option 1 / Option 2 / Option 3]
**Rationale**: [2-3 sentences]
```

---

## 📞 Support

**Escalation**:
- CTO: Strategic decision on integration path
- Architect: Architecture review of OpenCode internals
- PM/PO: ADR-026 revision process

**Documentation**:
- OpenCode Official: https://opencode.ai/docs
- OpenCode GitHub: https://github.com/anomalyco/opencode
- ADR-026: [ADR-026-OpenCode-Integration-Strategy.md](../../02-design/01-ADRs/ADR-026-OpenCode-Integration-Strategy.md)

---

**Last Updated**: January 12, 2026
**Next Review**: January 17, 2026 (Friday 3pm Checkpoint - CRITICAL DECISION)
