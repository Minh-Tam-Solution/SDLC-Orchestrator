# OpenCode Level 0 Evaluation - Week 1-2 Setup

**Issue Type**: Task
**Priority**: Medium
**Timeline**: Week 1-2 (Jan 12-17, 2026)
**Budget**: $0 (observation only)
**Owners**: Backend Lead (implementation), Architect (monitoring)
**Related**: [ADR-026-OpenCode-Integration-Strategy.md](../../02-design/01-ADRs/ADR-026-OpenCode-Integration-Strategy.md)

---

## Context

As part of Q1 2026 observation phase, we need to setup local OpenCode environment and run initial evaluation to assess its potential as Layer 5 AI Coder integration.

**Strategic Goal**: Decide by April 2026 whether to proceed with Level 1 Pilot ($30K)

---

## Objectives (Week 1-2) - REVISED

- [x] ✅ ADR-026 created and approved (Jan 12, 2026)
- [x] ✅ OpenCode repository cloned to /home/nqh/shared/opencode (Jan 12, 2026)
- [x] 🚨 Critical discovery: OpenCode is CLI/TUI tool (NOT API server) - Jan 12, 2026
- [ ] ⏳ Star OpenCode GitHub repo, enable notifications (Architect)
- [ ] ⏳ Install OpenCode CLI - `brew install anomalyco/tap/opencode` (Backend Lead)
- [ ] ⏳ Run first sample task via CLI (Task 1: FastAPI CRUD) (Backend Lead)
- [ ] ⏳ Document findings + integration options assessment (Backend Lead)
- [ ] 🚨 CTO Checkpoint: 4 integration options decision (Jan 17 @ 3pm)

---

## Tasks

### Task 1: GitHub Monitoring Setup (Architect)
**Owner**: Architect
**Deadline**: Jan 13, 2026 (Monday)
**Estimated Time**: 15 minutes

**Steps**:
1. Go to https://github.com/anomalyco/opencode
2. Click "Star" button (top-right corner)
3. Click "Watch" → "All Activity" to enable notifications
4. Create monitoring spreadsheet with columns:
   - Date
   - Stars count
   - Commits this week
   - Open critical issues (P0/P1)
   - API changes (yes/no)
   - Notes

**Success Criteria**:
- ✅ Repo starred
- ✅ Notifications enabled
- ✅ Monitoring spreadsheet created

---

### Task 2: Local OpenCode Setup (Backend Lead)
**Owner**: Backend Lead
**Deadline**: Jan 15, 2026 (Wednesday)
**Estimated Time**: 2-3 hours

**Prerequisites**:
- Docker installed and running
- Git client installed
- Python 3.11+ installed (for testing generated code)

**Steps**:

1. **Clone OpenCode repository**:
```bash
cd ~/projects  # or your preferred location
git clone https://github.com/anomalyco/opencode.git
cd opencode
```

2. **Review documentation**:
```bash
# Read README.md
cat README.md

# Check available Docker configurations
ls -la docker*
cat docker-compose.yml  # if exists
```

3. **Start OpenCode in Server Mode**:
```bash
# Option A: Using Docker Compose (if available)
docker-compose up -d

# Option B: Using Docker directly
docker run -d \
  --name opencode-server \
  -p 8080:8080 \
  -e OPENCODE_MODE=server \
  anomalyco/opencode:latest

# Check logs
docker logs -f opencode-server
```

4. **Verify OpenCode is running**:
```bash
# Test health endpoint
curl http://localhost:8080/health

# Expected response:
# {"status": "ok", "version": "x.y.z"}
```

5. **Test basic API call**:
```bash
# Test /api/v1/feature endpoint (if available)
curl -X POST http://localhost:8080/api/v1/feature \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a simple Python function that adds two numbers",
    "workflow": "feature"
  }'
```

**Success Criteria**:
- ✅ OpenCode Docker container running
- ✅ Health endpoint responds with 200 OK
- ✅ Basic API call returns generated code
- ✅ Setup documented (commands, issues encountered, workarounds)

**Expected Blockers**:
- Missing Docker image → Check OpenCode releases, build from source if needed
- Port conflict (8080 in use) → Use different port: `-p 8081:8080`
- API documentation missing → Inspect source code, check examples/

---

### Task 3: Run First Sample Task (Backend Lead)
**Owner**: Backend Lead
**Deadline**: Jan 17, 2026 (Friday)
**Estimated Time**: 1-2 hours

**Sample Task 1: Simple CRUD API Endpoint (FastAPI)**

**Input Specification**:
```json
{
  "task": "Create a FastAPI endpoint for user CRUD operations with the following requirements:\n- POST /users - Create new user (accepts: name, email)\n- GET /users/{user_id} - Get user by ID\n- PUT /users/{user_id} - Update user\n- DELETE /users/{user_id} - Delete user\n- Use Pydantic models for validation\n- Return proper HTTP status codes (201, 200, 404)\n- No database required, use in-memory list",
  "workflow": "feature",
  "language": "python",
  "framework": "fastapi"
}
```

**Steps**:

1. **Run OpenCode generation**:
```bash
# Via API
curl -X POST http://localhost:8080/api/v1/feature \
  -H "Content-Type: application/json" \
  -d @task1-spec.json \
  > task1-output.json

# Measure generation time
time curl -X POST http://localhost:8080/api/v1/feature \
  -H "Content-Type: application/json" \
  -d @task1-spec.json
```

2. **Extract generated code**:
```bash
# Parse JSON output
cat task1-output.json | jq -r '.code' > task1-generated.py

# OR if multi-file
cat task1-output.json | jq -r '.files'
```

3. **Manual Code Review**:
   - Does it follow FastAPI best practices?
   - Are Pydantic models correctly defined?
   - Are HTTP status codes correct (201, 200, 404)?
   - Does it handle edge cases (missing user ID, duplicate email)?
   - Is code formatted (PEP 8 compliant)?

4. **Test Generated Code**:
```bash
# Install dependencies
pip install fastapi uvicorn pydantic

# Run generated code
uvicorn task1-generated:app --reload

# Test endpoints
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

curl http://localhost:8000/users/1

# Expected: 200 OK with user data
```

5. **Quality Assessment**:
   - **Syntax**: Does code run without syntax errors? (✅/❌)
   - **Functionality**: Do all endpoints work as specified? (✅/❌)
   - **Security**: Any security issues (SQL injection, XSS)? (✅/❌)
   - **Code Quality**: Is code readable, maintainable? (Score: 1-5)
   - **Latency**: Generation time (seconds)

**Success Criteria**:
- ✅ Code generated successfully (no server errors)
- ✅ Generated code runs without syntax errors
- ✅ At least 3/4 endpoints working correctly
- ✅ Quality assessment documented
- ✅ Generation latency <60s

**Deliverables**:
- `task1-spec.json` - Input specification
- `task1-output.json` - Raw OpenCode output
- `task1-generated.py` - Extracted code
- `task1-assessment.md` - Quality review (template below)

---

### Task 4: Document Findings (Backend Lead)
**Owner**: Backend Lead
**Deadline**: Jan 17, 2026 (Friday, 5pm)
**Estimated Time**: 30 minutes

**Create**: `docs/04-build/03-Issues/OpenCode-Week1-2-Report.md`

**Template**:
```markdown
# OpenCode Level 0 - Week 1-2 Report

**Date**: Jan 17, 2026
**Evaluator**: [Your Name]
**Status**: Week 1-2 Complete

## Setup Results

| Item | Status | Notes |
|------|--------|-------|
| GitHub monitoring | ✅/❌ | Stars: X, Commits: Y/week |
| Docker setup | ✅/❌ | Version: X.Y.Z, Port: 8080 |
| Health check | ✅/❌ | Response time: Xms |
| API test | ✅/❌ | Endpoint: /api/v1/feature |

## Sample Task 1: Simple CRUD API

| Metric | Result | Notes |
|--------|--------|-------|
| **Generation** |
| Latency | Xs | Target: <30s |
| Status | ✅/❌ | Success / Error |
| **Quality** |
| Syntax | ✅/❌ | Runs without errors? |
| Functionality | X/4 endpoints | POST, GET, PUT, DELETE |
| Security | ✅/❌ | Issues found? |
| Code Quality | X/5 | Readability, maintainability |
| **4-Gate Proxy** |
| Syntax (ast.parse) | ✅/❌ | Python AST validates? |
| Security (manual) | ✅/❌ | No obvious vulnerabilities? |
| Tests (manual) | ✅/❌ | Endpoints work as expected? |

## Observations

**Strengths**:
- [List what worked well]

**Weaknesses**:
- [List issues encountered]

**Blockers**:
- [List any blockers]

## Next Steps (Week 3-6)

- [ ] Run Task 2: React component with state
- [ ] Run Task 3: Multi-file auth flow
- [ ] Compare OpenCode vs manual coding time
- [ ] Update monitoring spreadsheet (week 2 data)

## Recommendation

**Preliminary Assessment**: [PROMISING / NEEDS_IMPROVEMENT / BLOCKED]

**Rationale**: [1-2 sentences]
```

**Success Criteria**:
- ✅ Report created and committed to Git
- ✅ All sections filled (no placeholders)
- ✅ Preliminary assessment provided

---

## Acceptance Criteria (Week 1-2)

- [x] ✅ ADR-026 created and approved
- [ ] ⏳ GitHub monitoring active (starred, notifications on)
- [ ] ⏳ OpenCode Docker container running locally
- [ ] ⏳ First sample task executed (Task 1: CRUD API)
- [ ] ⏳ Week 1-2 report documented
- [ ] ⏳ No blockers preventing Week 3-6 work

---

## Checkpoint: Friday Jan 17, 2026 @ 3pm

**Attendees**: CTO, Backend Lead, Architect

**Agenda**:
1. Demo: Show OpenCode running locally
2. Review: Task 1 quality assessment
3. Discuss: Any blockers or concerns
4. Decide: Proceed with Week 3-6 (Tasks 2-5) or adjust plan

**Expected Outcome**:
- GO: Proceed with 5-sample benchmark (Week 3-6)
- ADJUST: Modify sample tasks or evaluation criteria
- BLOCK: Escalate technical issues, revisit in 2 weeks

---

## Resources

**Documentation**:
- [ADR-026: OpenCode Integration Strategy](../../02-design/01-ADRs/ADR-026-OpenCode-Integration-Strategy.md)
- [CURRENT-SPRINT.md](../02-Sprint-Plans/CURRENT-SPRINT.md) - Q1 2026 Observation Phase

**OpenCode Repository**:
- GitHub: https://github.com/anomalyco/opencode
- Docs: https://github.com/anomalyco/opencode/tree/main/docs (if available)
- Issues: https://github.com/anomalyco/opencode/issues

**Internal Contacts**:
- CTO: Strategic decisions, budget approval
- Architect: Architecture review, monitoring
- Backend Lead: Implementation, testing

---

## Notes

- This is **observation only**, not production integration
- Budget: $0 (no external API costs, local Docker only)
- No changes to SDLC Orchestrator codebase required
- Work can be done independently without blocking other sprints

---

**Issue Status**: 🔄 IN PROGRESS (Week 1/12)
**Next Update**: Friday Jan 17, 2026 @ 3pm (Checkpoint)
