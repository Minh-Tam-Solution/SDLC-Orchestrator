# Sprint 21: Compliance Scanner & AI Integration

**Version**: 1.0.0
**Date**: November 29, 2025
**Status**: PLANNED
**Authority**: CTO + Backend Lead + CPO
**Foundation**: SDLC 5.1.3.1 Enforcement Requirements
**Framework**: SDLC 5.1.3 Complete Lifecycle
**Week**: 11 of 13 (Dec 2-6, 2025)

---

## Sprint Overview

**Sprint Goal**: Implement automated compliance scanning to detect SDLC violations and integrate AI-powered recommendations with Ollama.

**Duration**: 5 days
**Team**: Backend Lead (80%), AI Engineer (100%), Frontend Lead (20%)
**Priority**: P0 - Critical (Governance Enforcement Core Feature)

---

## Context: Why Compliance Scanner?

From user feedback (Nov 29, 2025):
> "SDLC Orchestrator sẽ phải định kỳ quét toàn bộ project repo (codebase) để phát hiện sai lệch so với chuẩn SDLC hoặc chuẩn mà owner hoặc PJM thiết lập ban đầu khi hình thành dự án"

### Problems with Manual Enforcement

```yaml
Current State (Manual):
  ❌ CPO/CTO must manually check each stage for evidence
  ❌ Teams can skip stages when leadership is busy
  ❌ No automated detection of policy violations
  ❌ Audit trail maintained in spreadsheets
  ❌ Cannot scale beyond 5-10 projects

Platform Solution:
  ✅ Scheduled scans detect violations automatically
  ✅ Policy-as-Code (OPA) enforces rules consistently
  ✅ AI generates fix recommendations
  ✅ Immutable audit logs in database
  ✅ Scales to 100+ projects
```

---

## Day 1: Compliance Scanner Core

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 1.1 | Create ComplianceScanner service | backend/app/services/compliance_scanner.py | 3h | BE |
| 1.2 | Define SDLC 5.1.3.1 policy rules | backend/app/policies/sdlc-4.9.1.rego | 2h | BE |
| 1.3 | Create compliance_scans table | alembic/versions/xxx_compliance_scans.py | 1h | BE |
| 1.4 | Add scan results model | backend/app/models/compliance_scan.py | 1h | BE |

### Deliverables

**compliance_scanner.py**:
```python
"""
Compliance Scanner Service - SDLC 5.1.3.1 Violation Detection

This service periodically scans projects to detect violations of SDLC standards.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import Project, Gate, GateEvidence
from app.services.opa_service import OPAService
from app.services.github_service import GitHubService

class ComplianceScanner:
    """
    Scan projects for SDLC 5.1.3.1 compliance violations.

    Features:
    - Documentation structure validation
    - Stage sequence enforcement
    - Evidence completeness checks
    - Custom policy rule evaluation
    """

    def __init__(self, db: Session, opa_service: OPAService):
        self.db = db
        self.opa = opa_service

    async def scan_project(self, project_id: str) -> ComplianceScanResult:
        """
        Perform full compliance scan on a project.

        Returns:
            ComplianceScanResult with violations, warnings, and score
        """
        violations = []
        warnings = []

        # 1. Check documentation structure
        doc_violations = await self._check_documentation_structure(project_id)
        violations.extend(doc_violations)

        # 2. Check stage sequence (no skipped stages)
        stage_violations = await self._check_stage_sequence(project_id)
        violations.extend(stage_violations)

        # 3. Check evidence completeness per gate
        evidence_violations = await self._check_evidence_completeness(project_id)
        violations.extend(evidence_violations)

        # 4. Evaluate custom policies via OPA
        policy_violations = await self._evaluate_custom_policies(project_id)
        violations.extend(policy_violations)

        # Calculate compliance score
        score = self._calculate_score(violations, warnings)

        return ComplianceScanResult(
            project_id=project_id,
            violations=violations,
            warnings=warnings,
            compliance_score=score,
            scanned_at=datetime.utcnow()
        )

    async def _check_documentation_structure(self, project_id: str) -> List[Violation]:
        """Check if /docs folder follows SDLC 5.1.3.1 structure."""
        # Expected structure: 00-Project-Foundation, 01-Planning-Analysis, etc.
        pass

    async def _check_stage_sequence(self, project_id: str) -> List[Violation]:
        """Ensure stages are not skipped (G0 -> G1 -> G2 -> ...)."""
        pass

    async def _check_evidence_completeness(self, project_id: str) -> List[Violation]:
        """Check each gate has required evidence files."""
        pass
```

**sdlc-4.9.1.rego**:
```rego
package sdlc.compliance

# Documentation structure rules
default doc_structure_valid = false

doc_structure_valid {
    input.docs["00-Project-Foundation"]
    input.docs["01-Planning-Analysis"]
    input.docs["02-Design-Architecture"]
}

# Violation: Missing required stage folder
violation["Missing 00-Project-Foundation folder"] {
    not input.docs["00-Project-Foundation"]
}

violation["Missing 01-Planning-Analysis folder"] {
    not input.docs["01-Planning-Analysis"]
}

# Stage sequence rules
default stage_sequence_valid = false

stage_sequence_valid {
    gate_g0_passed
    gate_g1_passed
    gate_g2_passed
}

gate_g0_passed {
    input.gates["G0.1"].status == "approved"
    input.gates["G0.2"].status == "approved"
}

# Evidence completeness rules
violation[msg] {
    gate := input.gates[gate_id]
    gate.status == "pending_approval"
    count(gate.evidence) < gate.required_evidence_count
    msg := sprintf("Gate %s has insufficient evidence (%d/%d)", [gate_id, count(gate.evidence), gate.required_evidence_count])
}
```

### Success Criteria
- [ ] ComplianceScanner service created
- [ ] 10+ SDLC 5.1.3.1 rules defined in Rego
- [ ] Database schema for scan results
- [ ] Unit tests for scanner logic

---

## Day 2: Scheduled Scans & Notification

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 2.1 | Create APScheduler job | backend/app/jobs/compliance_scan_job.py | 2h | BE |
| 2.2 | Add scan scheduling API | backend/app/api/v1/compliance.py | 2h | BE |
| 2.3 | Create notification service | backend/app/services/notification_service.py | 2h | BE |
| 2.4 | Add email/Slack templates | backend/app/templates/violations/*.html | 2h | BE |

### Deliverables

**compliance_scan_job.py**:
```python
"""
Scheduled Compliance Scan Job

Runs daily at 2:00 AM to scan all active projects.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.compliance_scanner import ComplianceScanner
from app.services.notification_service import NotificationService

async def run_daily_compliance_scan():
    """
    Scan all active projects and notify stakeholders of violations.
    """
    projects = await get_active_projects()

    for project in projects:
        result = await scanner.scan_project(project.id)

        if result.violations:
            # Notify project owner
            await notification_service.send_violation_alert(
                project=project,
                violations=result.violations,
                recipients=[project.owner, project.pm]
            )

        # Store scan result
        await store_scan_result(result)

    logger.info(f"Daily compliance scan completed: {len(projects)} projects scanned")
```

**compliance.py (API)**:
```python
@router.post("/scans")
async def trigger_scan(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ComplianceScanResponse:
    """
    Trigger immediate compliance scan for a project.

    Only project owner or admin can trigger scans.
    """
    scanner = ComplianceScanner(db)
    result = await scanner.scan_project(str(project_id))
    return ComplianceScanResponse.from_result(result)

@router.get("/scans/{project_id}/history")
async def get_scan_history(
    project_id: UUID,
    limit: int = 10
) -> List[ComplianceScanSummary]:
    """Get historical scan results for a project."""
    pass
```

### Success Criteria
- [ ] Daily scan job configured
- [ ] On-demand scan API working
- [ ] Email notifications sent for violations
- [ ] Slack webhook integration (optional)

---

## Day 3: Ollama AI Integration

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 3.1 | Create OllamaService | backend/app/services/ollama_service.py | 3h | AI |
| 3.2 | Implement AI recommendation | backend/app/services/ai_recommendation.py | 3h | AI |
| 3.3 | Add AI API endpoints | backend/app/api/v1/ai.py | 2h | AI |

### Deliverables

**ollama_service.py**:
```python
"""
Ollama AI Service - Stage-Aware Recommendations

Uses local Ollama (api.nhatquangholding.com) for 95% cost savings.
Fallback: Claude > GPT-4o > Gemini > Rule-based
"""
import httpx
from app.core.config import settings

class OllamaService:
    """
    AI service using Ollama for SDLC recommendations.

    Cost: $50/month vs $1000/month (Claude)
    Latency: <100ms vs 300ms
    Privacy: No external API calls
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL  # http://api.nhatquangholding.com:11434
        self.model = settings.OLLAMA_MODEL  # qwen2.5-coder:32b

    async def generate_recommendation(
        self,
        violation: Violation,
        context: Dict[str, Any]
    ) -> AIRecommendation:
        """
        Generate AI-powered fix recommendation for a violation.

        Args:
            violation: The detected compliance violation
            context: Project context (stage, files, history)

        Returns:
            AIRecommendation with fix steps and examples
        """
        prompt = self._build_prompt(violation, context)

        response = await self._call_ollama(prompt)

        return AIRecommendation(
            violation_id=violation.id,
            recommendation=response.content,
            confidence=response.confidence,
            fix_steps=self._parse_fix_steps(response),
            examples=self._extract_examples(response)
        )

    def _build_prompt(self, violation: Violation, context: Dict) -> str:
        """Build stage-aware prompt for the AI."""
        return f"""
You are an SDLC 5.1.3.1 compliance expert. A violation was detected in a software project.

## Violation Details
- Type: {violation.type}
- Severity: {violation.severity}
- Description: {violation.description}
- Location: {violation.location}

## Project Context
- Current Stage: {context['current_stage']}
- Project Type: {context['project_type']}
- Team Size: {context['team_size']}

## Task
Provide a clear, actionable recommendation to fix this violation. Include:
1. Root cause analysis (why this happened)
2. Step-by-step fix instructions
3. Example code/documentation if applicable
4. Prevention tips for the future

Keep the response concise and practical.
"""

    async def _call_ollama(self, prompt: str) -> OllamaResponse:
        """Make API call to Ollama service."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_ctx": 32768
                    }
                },
                timeout=30.0
            )
            response.raise_for_status()
            return OllamaResponse(**response.json())
```

**ai.py (API)**:
```python
@router.post("/recommendations")
async def get_ai_recommendation(
    request: AIRecommendationRequest,
    current_user: User = Depends(get_current_user)
) -> AIRecommendationResponse:
    """
    Get AI-powered recommendation for fixing a violation.

    Uses Ollama (primary) with fallback to Claude/GPT-4o.
    """
    service = AIRecommendationService()
    recommendation = await service.get_recommendation(
        violation_id=request.violation_id,
        context=request.context
    )
    return AIRecommendationResponse(recommendation=recommendation)

@router.get("/providers")
async def list_ai_providers() -> List[AIProviderStatus]:
    """List available AI providers with status and costs."""
    pass
```

### Success Criteria
- [ ] Ollama service connected to api.nhatquangholding.com
- [ ] AI recommendations generated for violations
- [ ] Fallback chain working (Ollama > Claude > GPT-4o)
- [ ] Response time <100ms (Ollama)

---

## Day 4: Compliance Dashboard UI

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 4.1 | Create ComplianceDashboard page | frontend/web/src/pages/CompliancePage.tsx | 3h | FE |
| 4.2 | Add ViolationCard component | components/compliance/ViolationCard.tsx | 2h | FE |
| 4.3 | Create ComplianceScore widget | components/compliance/ComplianceScore.tsx | 1h | FE |
| 4.4 | Add scan history view | CompliancePage.tsx | 2h | FE |

### Deliverables

**CompliancePage.tsx**:
```typescript
export default function CompliancePage() {
  const { projectId } = useParams()

  const { data: latestScan } = useQuery({
    queryKey: ['compliance', projectId, 'latest'],
    queryFn: () => api.compliance.getLatest(projectId),
  })

  const triggerScanMutation = useMutation({
    mutationFn: () => api.compliance.triggerScan(projectId),
  })

  return (
    <div className="space-y-6">
      {/* Compliance Score */}
      <ComplianceScore
        score={latestScan?.compliance_score || 0}
        lastScan={latestScan?.scanned_at}
      />

      {/* Actions */}
      <div className="flex gap-4">
        <Button onClick={() => triggerScanMutation.mutate()}>
          Run Scan Now
        </Button>
        <Button variant="outline">View History</Button>
      </div>

      {/* Violations List */}
      <Card>
        <CardHeader>
          <CardTitle>Violations ({latestScan?.violations.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {latestScan?.violations.map((violation) => (
            <ViolationCard
              key={violation.id}
              violation={violation}
              onGetRecommendation={handleGetRecommendation}
            />
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
```

### Success Criteria
- [ ] Compliance dashboard displays score
- [ ] Violations list with severity badges
- [ ] AI recommendation button per violation
- [ ] Scan history viewable

---

## Day 5: Testing & Documentation

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 5.1 | Write integration tests | tests/integration/test_compliance_scanner.py | 3h | BE |
| 5.2 | Write E2E tests | frontend/web/e2e/compliance.spec.ts | 2h | FE |
| 5.3 | Update API docs | docs/02-Design-Architecture/03-API-Design/openapi.yml | 1h | BE |
| 5.4 | Create Sprint 21 completion report | docs/03-Development-Implementation/01-Sprint-Plans/ | 1h | PM |

### Test Scenarios

```python
# tests/integration/test_compliance_scanner.py
class TestComplianceScanner:
    async def test_detect_missing_documentation(self, db, project):
        """Should detect when docs folder is missing."""
        scanner = ComplianceScanner(db)
        result = await scanner.scan_project(project.id)

        assert len(result.violations) > 0
        assert any(v.type == "MISSING_DOCUMENTATION" for v in result.violations)

    async def test_detect_skipped_stage(self, db, project):
        """Should detect when a stage is skipped."""
        # Create G2 gate without G1
        await create_gate(project.id, "G2")

        scanner = ComplianceScanner(db)
        result = await scanner.scan_project(project.id)

        assert any(v.type == "SKIPPED_STAGE" for v in result.violations)

    async def test_perfect_compliance(self, db, project):
        """Should return 100% score when fully compliant."""
        # Setup compliant project
        await setup_compliant_project(project.id)

        scanner = ComplianceScanner(db)
        result = await scanner.scan_project(project.id)

        assert result.compliance_score == 100
        assert len(result.violations) == 0
```

### Success Criteria
- [ ] 90%+ test coverage for scanner
- [ ] E2E test for compliance flow
- [ ] OpenAPI updated with new endpoints
- [ ] Sprint completion report written

---

## Database Schema

### compliance_scans Table

```sql
CREATE TABLE compliance_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    triggered_by UUID REFERENCES users(id),
    trigger_type VARCHAR(20) NOT NULL, -- 'scheduled', 'manual', 'webhook'

    compliance_score INTEGER NOT NULL CHECK (compliance_score >= 0 AND compliance_score <= 100),
    violations_count INTEGER NOT NULL DEFAULT 0,
    warnings_count INTEGER NOT NULL DEFAULT 0,

    violations JSONB DEFAULT '[]',
    warnings JSONB DEFAULT '[]',

    scanned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    duration_ms INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_compliance_scans_project ON compliance_scans(project_id);
CREATE INDEX idx_compliance_scans_date ON compliance_scans(scanned_at DESC);
```

---

## API Endpoints (New)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/compliance/scans | Trigger compliance scan |
| GET | /api/v1/compliance/scans/{project_id}/latest | Get latest scan result |
| GET | /api/v1/compliance/scans/{project_id}/history | Get scan history |
| POST | /api/v1/ai/recommendations | Get AI fix recommendation |
| GET | /api/v1/ai/providers | List AI provider status |

---

## Sprint Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Scan Accuracy | >95% | True positive rate |
| Scan Performance | <30s | Full project scan |
| AI Response Time | <100ms | Ollama recommendation |
| Test Coverage | 90%+ | Backend scanner |

---

## Definition of Done

- [ ] ComplianceScanner service complete
- [ ] 15+ SDLC 5.1.3.1 policy rules
- [ ] Scheduled daily scans working
- [ ] Ollama AI integration complete
- [ ] Compliance dashboard UI
- [ ] Email notifications for violations
- [ ] 90%+ test coverage
- [ ] API documentation updated
- [ ] No P0/P1 bugs

---

## Appendix A: Documentation Drift Detection (Doc-Code Sync)

### Why Documentation Drift Detection?

From user feedback (Nov 29, 2025):
> "tuy SDLC Framework quy định Document as Code, nhưng chúng ta cũng chưa có biện pháp nào để thực thi việc này... với người mới tiếp cận phương pháp của SDLC Framework của chúng ta, thì xác suất cao sẽ làm sai"

> "việc thiết kế, code, test không phải là tuyến tính mà vòng lặp đi lặp lại, khi có thay đổi thiết kế thì phải refactor hoặc code mới, khi bổ sung code khác với thiết kế thì phải quay lại cập nhật thiết kế"

### Problem Statement

```yaml
SDLC Framework Problem:
  Policy: "Document as Code" - docs must match implementation
  Reality: Manual enforcement only (owner with expertise)

What Happens:
  ❌ New team members don't know SDLC Framework rules
  ❌ AI Codex (Claude, Copilot) generates code without updating docs
  ❌ Design changes → Code refactored → Docs NOT updated
  ❌ Code differs from design → No one notices until audit
  ❌ Iterative workflow broken (Design ↔ Code ↔ Test loop)

Impact:
  - Documentation becomes stale (lies)
  - Compliance audits fail
  - Knowledge transfer broken
  - Technical debt accumulates silently
```

### Solution: Doc-Code Sync Scanner

```yaml
Scanner Types:

1. API Drift Detection:
   - Compare openapi.yml with actual endpoint implementations
   - Detect: Missing endpoints, wrong parameters, undocumented errors
   - Action: Block gate until API spec updated

2. Database Drift Detection:
   - Compare Data-Model-ERD.md with Alembic migrations
   - Detect: Missing tables, extra columns, wrong relationships
   - Action: Block gate until ERD updated

3. Architecture Drift Detection:
   - Compare System-Architecture-Document.md with actual services
   - Detect: New services not in diagram, deprecated services still in doc
   - Action: Create "Architecture Update Required" task

4. Security Drift Detection:
   - Compare Security-Baseline.md with actual implementations
   - Detect: Missing RBAC rules, undocumented auth flows
   - Action: Block gate + alert Security Lead

5. Test Coverage Drift:
   - Compare test files with documented test scenarios
   - Detect: Tests without documentation, documented tests not implemented
   - Action: Warning (not blocking)
```

### Implementation Design

**doc_code_sync_scanner.py**:
```python
"""
Documentation Drift Detection - Enforces Doc-as-Code Policy

Scans for differences between documentation and implementation.
Creates gate blockers when drift detected.
"""

class DocCodeSyncScanner:
    """
    Detect drift between documentation and code implementation.

    This is critical for SDLC 5.1.3.1 compliance because:
    1. New team members rely on docs to understand system
    2. AI Codex changes may not update docs
    3. Iterative development creates doc debt
    """

    def __init__(self, db: Session, github_service: GitHubService):
        self.db = db
        self.github = github_service

    async def scan_doc_code_sync(self, project_id: str) -> DocCodeSyncResult:
        """
        Compare documentation with actual implementation.

        Returns:
            DocCodeSyncResult with drift items and recommendations
        """
        drifts = []

        # 1. API Drift: openapi.yml vs actual endpoints
        api_drifts = await self._check_api_drift(project_id)
        drifts.extend(api_drifts)

        # 2. DB Drift: ERD vs Alembic migrations
        db_drifts = await self._check_database_drift(project_id)
        drifts.extend(db_drifts)

        # 3. Architecture Drift: SAD vs service files
        arch_drifts = await self._check_architecture_drift(project_id)
        drifts.extend(arch_drifts)

        # 4. Security Drift: Security baseline vs implementations
        sec_drifts = await self._check_security_drift(project_id)
        drifts.extend(sec_drifts)

        return DocCodeSyncResult(
            project_id=project_id,
            drifts=drifts,
            sync_score=self._calculate_sync_score(drifts),
            recommendations=await self._generate_recommendations(drifts)
        )

    async def _check_api_drift(self, project_id: str) -> List[DriftItem]:
        """
        Compare openapi.yml with actual FastAPI routes.

        Detects:
        - Endpoints in code but not in spec
        - Endpoints in spec but not in code
        - Parameter mismatches
        - Response schema differences
        """
        drifts = []

        # Get openapi.yml from repo
        spec_endpoints = await self._parse_openapi_spec(project_id)

        # Get actual endpoints from FastAPI
        actual_endpoints = await self._extract_fastapi_routes(project_id)

        # Compare
        for endpoint in actual_endpoints:
            if endpoint not in spec_endpoints:
                drifts.append(DriftItem(
                    type="API_NOT_DOCUMENTED",
                    severity="HIGH",
                    location=f"{endpoint.method} {endpoint.path}",
                    description=f"Endpoint implemented but not in openapi.yml",
                    recommendation="Add endpoint to docs/02-Design-Architecture/03-API-Design/openapi.yml"
                ))

        for endpoint in spec_endpoints:
            if endpoint not in actual_endpoints:
                drifts.append(DriftItem(
                    type="API_NOT_IMPLEMENTED",
                    severity="MEDIUM",
                    location=f"{endpoint.method} {endpoint.path}",
                    description=f"Endpoint in openapi.yml but not implemented",
                    recommendation="Either implement endpoint or remove from spec"
                ))

        return drifts

    async def _check_database_drift(self, project_id: str) -> List[DriftItem]:
        """
        Compare Data-Model-ERD.md with actual database schema.

        Detects:
        - Tables in DB but not in ERD
        - Columns in DB but not documented
        - Missing indexes documented but not created
        """
        pass  # Implementation

    async def _generate_recommendations(self, drifts: List[DriftItem]) -> List[str]:
        """Generate AI-powered recommendations using Ollama."""
        if not drifts:
            return ["Documentation is in sync with code. Great job!"]

        recommendations = []
        for drift in drifts[:5]:  # Top 5 priority items
            prompt = f"""
A documentation drift was detected in an SDLC 5.1.3.1 project:

Type: {drift.type}
Location: {drift.location}
Description: {drift.description}

Generate a specific, actionable recommendation to fix this drift.
Keep it concise (2-3 sentences).
"""
            rec = await self.ollama.generate(prompt)
            recommendations.append(rec)

        return recommendations
```

### Drift Types Table

| Drift Type | Severity | Gate Blocking | Auto-Fix Possible |
|------------|----------|---------------|-------------------|
| API_NOT_DOCUMENTED | HIGH | Yes | No (manual review needed) |
| API_NOT_IMPLEMENTED | MEDIUM | No | No |
| DB_TABLE_NOT_DOCUMENTED | HIGH | Yes | Partial (AI can suggest) |
| DB_COLUMN_MISMATCH | MEDIUM | No | No |
| ARCHITECTURE_SERVICE_MISSING | HIGH | Yes | No |
| SECURITY_RULE_UNDOCUMENTED | CRITICAL | Yes | No |
| TEST_SCENARIO_NOT_IMPLEMENTED | LOW | No | No |
| README_OUTDATED | LOW | No | Yes (AI can update) |

### AI Codex Tracking

```yaml
Why Track AI Codex:
  - AI tools (Claude, Copilot, Cursor) generate code quickly
  - Code changes may not reflect in documentation
  - Without tracking, drift accumulates silently

Detection Strategy:
  1. Monitor commit messages for AI indicators:
     - "🤖 Generated with Claude Code"
     - "Co-Authored-By: Claude"
     - "GitHub Copilot" in commit author

  2. Flag AI-generated commits for doc review:
     - Create automatic "Doc Review Required" task
     - Assign to PM or Tech Lead
     - Block next gate until reviewed

  3. Calculate AI-to-Doc ratio:
     - % of AI commits that updated docs
     - Target: >80% of AI commits should touch docs
```

### Integration with Gate System

```python
# Gate evaluation now includes doc-code sync check
async def evaluate_gate(gate_id: str) -> GateEvaluation:
    """
    Evaluate gate with documentation sync check.
    """
    # Standard policy checks
    policy_result = await opa_service.evaluate(gate_id)

    # Doc-code sync check (NEW)
    sync_result = await doc_code_scanner.scan_doc_code_sync(project_id)

    # Block if critical drift detected
    if any(d.severity == "CRITICAL" for d in sync_result.drifts):
        return GateEvaluation(
            status="BLOCKED",
            reason="Documentation drift detected. Code differs from design docs.",
            blockers=[
                f"{d.type}: {d.location}" for d in sync_result.drifts
                if d.severity in ("CRITICAL", "HIGH")
            ],
            recommendation="Update documentation to match implementation before proceeding."
        )

    return GateEvaluation(
        status=policy_result.status,
        warnings=[f"Doc drift: {d.type}" for d in sync_result.drifts if d.severity == "MEDIUM"]
    )
```

### Success Metrics for Doc-Code Sync

| Metric | Target | Measurement |
|--------|--------|-------------|
| Doc Sync Score | >90% | (Documented items / Total items) × 100 |
| AI Commit Doc Rate | >80% | AI commits with doc updates / Total AI commits |
| Drift Resolution Time | <24h | Time from detection to fix |
| False Positive Rate | <5% | False drift alerts / Total alerts |

---

## Appendix B: Iterative Workflow Enforcement

### The Problem with Linear Thinking

```yaml
Traditional SDLC (Wrong):
  Design → Code → Test → Deploy → Done

Reality (Correct):
  ┌─────────────────────────────────────┐
  │  Design → Code → Test               │
  │    ↑                ↓               │
  │    └──── Refactor ──┘               │
  │                                     │
  │  Code → Test → Bug Found            │
  │    ↑                ↓               │
  │    └─── Fix Design ─┘               │
  │                                     │
  │  Test → Fail → Update Requirements  │
  │    ↑                ↓               │
  │    └─── Re-Design ──┘               │
  └─────────────────────────────────────┘

Problem:
  ❌ People skip doc updates in iteration loops
  ❌ Design docs become stale after 2-3 iterations
  ❌ New team members read outdated docs
  ❌ Audit finds code ≠ docs = compliance failure
```

### Platform Enforcement

```yaml
Gate Workflow with Doc Enforcement:

1. Code Change Detected:
   - Developer pushes code
   - Platform scans for changes

2. Doc Impact Analysis:
   - Compare changes with affected docs
   - Identify which docs need updates
   - AI suggest specific updates needed

3. Create Mandatory Tasks:
   - "Update API Spec for /new-endpoint"
   - "Update ERD for new 'notifications' table"
   - "Update Security doc for new OAuth scope"

4. Block Gate Until Done:
   - Gate status: "BLOCKED - Documentation Required"
   - Show specific doc update tasks
   - Link to AI-generated draft updates

5. After Doc Update:
   - Re-scan for drift
   - If clean, unblock gate
   - Log in audit trail
```

### AI-Assisted Doc Updates

```python
async def suggest_doc_updates(
    code_changes: List[CodeChange],
    affected_docs: List[str]
) -> List[DocUpdateSuggestion]:
    """
    Use Ollama to generate documentation update suggestions.

    This helps developers (especially new ones) know exactly
    what to update and how.
    """
    suggestions = []

    for change in code_changes:
        prompt = f"""
A code change was made that may require documentation updates.

Code Change:
- File: {change.file_path}
- Type: {change.change_type}  # added, modified, deleted
- Summary: {change.summary}

Affected Documentation:
{', '.join(affected_docs)}

Generate specific, copy-paste-ready documentation updates.
Format: Markdown sections that can be directly added to docs.
"""
        suggestion = await ollama.generate(prompt)
        suggestions.append(DocUpdateSuggestion(
            change=change,
            affected_docs=affected_docs,
            suggested_content=suggestion,
            confidence=0.85
        ))

    return suggestions
```

---

## Appendix C: Anti-Documentation-Overload Protection

### The Problem: Documentation Theater

> "Cuối cùng thì document cũng không phải code, vì không có code đúng sẽ không có ứng dụng"

```yaml
Documentation Theater (Bad):
  ❌ Team writes 500 pages of docs, 0 lines of code
  ❌ Every small change requires 10-page design doc
  ❌ Analysis paralysis - "let me document this first"
  ❌ Docs become an excuse to delay actual work
  ❌ Perfect docs, broken product

Reality Check:
  ✅ Working software > comprehensive documentation (Agile Manifesto)
  ✅ Code is the ultimate source of truth
  ✅ Docs exist to SUPPORT code, not replace it
  ✅ Minimum viable documentation (MVD)
```

### Platform Safeguards Against Doc Overload

```yaml
1. Code-First Metrics:
   - Track code:doc ratio per sprint
   - Alert: "0 commits, 50 doc changes this week"
   - Target: 70% code, 30% docs (by commit count)

2. Time-Boxing Doc Updates:
   - Max 2 hours/week on doc updates (auto-reminder)
   - AI generates doc drafts (reduce manual effort)
   - "Good enough" docs > perfect docs

3. Gate Evaluation Priority:
   - Code working? → HIGH priority
   - Tests passing? → HIGH priority
   - Docs updated? → MEDIUM priority (warning, not blocker for minor drift)

4. Smart Blocking Rules:
   - CRITICAL drift (security, API contracts) → Block gate
   - MEDIUM drift (README, minor changes) → Warning only
   - LOW drift (comments, formatting) → Ignore
```

### Doc Effort Tracker

```python
class DocEffortTracker:
    """
    Track documentation effort to prevent doc theater.

    Goal: Ensure team spends most time on CODE, not docs.
    """

    async def check_doc_overload(self, project_id: str) -> DocOverloadWarning | None:
        """
        Detect if team is spending too much time on docs vs code.
        """
        # Get last 7 days activity
        commits = await self._get_recent_commits(project_id, days=7)

        code_commits = [c for c in commits if self._is_code_change(c)]
        doc_commits = [c for c in commits if self._is_doc_change(c)]

        # Calculate ratio
        total = len(code_commits) + len(doc_commits)
        if total == 0:
            return None

        doc_ratio = len(doc_commits) / total

        # Alert if docs > 50% of activity
        if doc_ratio > 0.5:
            return DocOverloadWarning(
                message=f"Documentation activity ({doc_ratio:.0%}) exceeds code activity. Consider focusing on implementation.",
                doc_commits=len(doc_commits),
                code_commits=len(code_commits),
                recommendation="Working software is the primary measure of progress. Docs should support code, not replace it."
            )

        # Alert if 0 code commits
        if len(code_commits) == 0 and len(doc_commits) > 5:
            return DocOverloadWarning(
                message="No code commits this week, but multiple doc changes. Is this intentional?",
                severity="HIGH",
                recommendation="Consider: Are docs blocking progress? Ship code first, polish docs later."
            )

        return None
```

### Balanced Approach: MVD (Minimum Viable Documentation)

```yaml
MVD Principle:
  "Write the minimum documentation needed to:
   1. Onboard a new team member
   2. Pass compliance audit
   3. Debug production issues"

What MUST be documented:
  ✅ API contracts (openapi.yml) - others depend on it
  ✅ Security decisions (auth flows, encryption) - audit requirement
  ✅ Architecture decisions (ADRs) - context for future
  ✅ Setup instructions (README) - onboarding

What can be LIGHT documentation:
  ⚡ Internal implementation details - code is the doc
  ⚡ Every function signature - IDE provides this
  ⚡ Step-by-step tutorials - link to external resources
  ⚡ Meeting notes - ephemeral, not worth maintaining

What should NOT be documented:
  ❌ Obvious code logic - "// increment i by 1"
  ❌ Temporary workarounds - fix them instead
  ❌ Personal preferences - not project knowledge
```

### Dashboard: Code vs Doc Health

```yaml
Dashboard Widget - "Development Balance":

┌─────────────────────────────────────────────┐
│  📊 This Week's Balance                     │
├─────────────────────────────────────────────┤
│  Code Commits:  ████████████████░░░░ 78%   │
│  Doc Changes:   ████░░░░░░░░░░░░░░░░ 22%   │
│                                             │
│  ✅ Healthy balance - Code-first approach   │
├─────────────────────────────────────────────┤
│  Sprint Progress:                           │
│  ✅ 12 features shipped                     │
│  ✅ 95% test coverage                       │
│  ⚠️ 3 docs need minor updates (non-blocking)│
└─────────────────────────────────────────────┘

Warning State (if doc_ratio > 50%):

┌─────────────────────────────────────────────┐
│  ⚠️ Documentation Overload Warning          │
├─────────────────────────────────────────────┤
│  Code Commits:  ████░░░░░░░░░░░░░░░░ 25%   │
│  Doc Changes:   ███████████████████░ 75%   │
│                                             │
│  "Working software > comprehensive docs"    │
│                                             │
│  Suggestion: Focus on shipping code.        │
│  Docs can be updated after feature works.   │
└─────────────────────────────────────────────┘
```

### The Golden Rule

```yaml
Priority Order (Non-Negotiable):

1. 🥇 Working Code (ship features)
2. 🥈 Passing Tests (prove it works)
3. 🥉 Updated Docs (help others understand)

Remember:
  - No amount of documentation can save broken code
  - Perfect docs with broken software = failed project
  - Ship first, document second (but DO document)
  - AI can help generate docs - use it!

Platform Enforcement:
  - Gates prioritize code+tests over docs
  - Doc drift = warning (usually), not blocker
  - Only CRITICAL doc issues (security, API contracts) block gates
  - Track doc:code ratio, alert on imbalance
```

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 5.1.3. Zero Mock Policy enforced.*

**Sprint 21 Focus**: "Automated Compliance - Platform that enforces, not just suggests"

**Key Innovation**: Doc-Code Sync Scanner - First-of-its-kind enforcement of "Document as Code" policy through automated drift detection and AI-assisted remediation.

**Balance Principle**: Working software > comprehensive documentation. Docs support code, not replace it.
