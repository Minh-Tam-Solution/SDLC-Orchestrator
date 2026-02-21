# SPRINT-41: AI Safety Foundation
## SDLC 6.1.0 Complete Lifecycle - BUILD Phase | AI Safety First (Q1 2026)

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-41 |
| **Epic** | EP-01: Idea & Stalled Project Flow + EP-02: AI Safety Layer v1 |
| **Duration** | 2 weeks (Jan 6-17, 2026) |
| **Status** | PLANNED |
| **Team** | 2 Backend + 2 Frontend + 1 DevOps + 1 QA |
| **Framework** | SDLC 6.1.0 + SASE Level 2 |
| **CTO Approval** | December 20, 2025 |

---

## SASE Artifact Linkage

| Artifact | Status | Location |
|----------|--------|----------|
| **BriefingScript** | ✅ Approved | [BRS-2026-001](../../05-SASE-Artifacts/BRS-2026-001-AI-SAFETY.yaml) |
| **MentorScript** | ✅ Active | [MTS-AI-SAFETY](../../05-SASE-Artifacts/MTS-AI-SAFETY.md) |
| **LoopScript** | ⏳ Agent generates | Per task |
| **MRP** | ⏳ Per PR | Evidence Vault |
| **VCR** | ⏳ Per approval | Evidence Vault |

---

## Executive Summary

Sprint 41 đánh dấu khởi đầu Q1 2026 "AI Safety First" với 2 track song song:
1. **Foundation Setup** - Telemetry, analytics instrumentation, AI Safety Layer schema
2. **Design Partner Sourcing** - Outreach 20 candidates, prepare workshop materials

**Roadmap Reference**: [Product-Roadmap-2026-Software3.0.md](../../00-foundation/04-Roadmap/Product-Roadmap-2026-Software3.0.md)
**CTO Approval**: [Q1Q2-2026-ROADMAP-CTO-APPROVED.md](../../09-govern/04-Strategic-Updates/2025-12-20-Q1Q2-2026-ROADMAP-CTO-APPROVED.md)

---

## Sprint Goals

### Primary Objectives

| # | Objective | Epic | Priority |
|---|-----------|------|----------|
| 1 | Setup product analytics (Mixpanel/Amplitude) | EP-01/EP-02 | P0 |
| 2 | Create `ai_code_events` collection schema | EP-02 | P0 |
| 3 | Design AI PR detection hooks (GitHub) | EP-02 | P0 |
| 4 | Source 20 Design Partner candidates | EP-03 | P0 |
| 5 | Create workshop deck "AI Safety for Engineering Teams" | EP-03 | P1 |

### Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Analytics events tracking | ≥10 key events | Mixpanel/Amplitude dashboard |
| `ai_code_events` schema | Approved by DBA | ADR document |
| PR detection accuracy | ≥90% (test dataset) | Unit tests |
| Partner candidates | 20 qualified leads | CRM/Notion |
| Workshop deck | v1.0 complete | Google Slides |

---

## Week 1: Foundation & Schema (Jan 6-10)

### Day 1-2: Product Analytics Instrumentation

**BriefingScript Reference**: BRS-2026-001-TASK-01

**Objective**: Setup telemetry pipeline for DAU/WAU, AI usage, gate pass rates.

**Tasks**:

1. **Choose Analytics Provider**
   ```yaml
   Decision: Mixpanel vs Amplitude
   Criteria:
     - Cost: Free tier sufficient for 6 months
     - Features: Event tracking, funnels, cohorts
     - Privacy: GDPR-compliant, EU data residency option
   
   Recommendation: Mixpanel (better free tier, easier setup)
   ```

2. **Backend Event Service**
   ```python
   # backend/app/services/analytics_service.py
   from mixpanel import Mixpanel

   class AnalyticsService:
       def __init__(self):
           self.mp = Mixpanel(settings.MIXPANEL_TOKEN)
       
       async def track_event(
           self,
           user_id: str,
           event_name: str,
           properties: dict = None
       ):
           """Track user event to Mixpanel."""
           self.mp.track(user_id, event_name, properties or {})
       
       async def track_ai_safety_event(
           self,
           user_id: str,
           pr_id: str,
           ai_tool: str,
           validation_result: str,
           duration_ms: int
       ):
           """Track AI Safety Layer event."""
           self.track_event(user_id, "ai_safety_validation", {
               "pr_id": pr_id,
               "ai_tool": ai_tool,
               "result": validation_result,
               "duration_ms": duration_ms
           })
   ```

3. **Frontend Analytics Hook**
   ```typescript
   // frontend/web/src/hooks/useAnalytics.ts
   import mixpanel from 'mixpanel-browser';
   
   export const useAnalytics = () => {
     const trackEvent = (name: string, properties?: Record<string, any>) => {
       mixpanel.track(name, {
         ...properties,
         timestamp: new Date().toISOString(),
         page: window.location.pathname,
       });
     };
     
     const trackPageView = (pageName: string) => {
       trackEvent('page_view', { page_name: pageName });
     };
     
     return { trackEvent, trackPageView };
   };
   ```

4. **Key Events to Track (10 minimum)**
   ```yaml
   Core Events:
     - user_login
     - user_logout
     - project_created
     - project_viewed
     - idea_submitted (EP-01)
     - stalled_project_analyzed (EP-01)
     - ai_pr_detected (EP-02)
     - ai_safety_validation (EP-02)
     - policy_pack_applied
     - gate_passed
   ```

**Deliverables**:
- [ ] Mixpanel project created with API keys
- [ ] AnalyticsService implemented
- [ ] Frontend hook created
- [ ] 10 key events instrumented
- [ ] Environment variables configured

**Assignee**: Backend Dev 1 + Frontend Dev 1
**Estimated**: 2 days

---

### Day 3-4: AI Code Events Schema

**BriefingScript Reference**: BRS-2026-001-TASK-02

**Objective**: Create `ai_code_events` collection for Evidence Vault.

**Tasks**:

1. **Schema Design (ADR)**
   ```markdown
   # ADR-019: AI Code Events Schema
   
   ## Context
   EP-02 requires logging all AI-generated code events for audit trail.
   
   ## Decision
   Create new collection `ai_code_events` (not extend existing schemas).
   
   ## Schema
   ```

2. **Database Model**
   ```python
   # backend/app/models/ai_code_event.py
   from sqlalchemy import Column, String, DateTime, JSON, Enum, ForeignKey
   from sqlalchemy.dialects.postgresql import UUID, JSONB
   from app.db.base_class import Base
   import enum
   
   class AIToolType(str, enum.Enum):
       CURSOR = "cursor"
       COPILOT = "copilot"
       CLAUDE_CODE = "claude_code"
       CHATGPT = "chatgpt"
       OTHER = "other"
       MANUAL_TAG = "manual_tag"
   
   class ValidationStatus(str, enum.Enum):
       PENDING = "pending"
       PASSED = "passed"
       FAILED = "failed"
       OVERRIDDEN = "overridden"
   
   class AICodeEvent(Base):
       __tablename__ = "ai_code_events"
       
       id = Column(UUID, primary_key=True, default=uuid4)
       created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
       updated_at = Column(DateTime, onupdate=datetime.utcnow)
       
       # PR Information
       project_id = Column(UUID, ForeignKey("projects.id"), nullable=False)
       pr_number = Column(String(50), nullable=False)
       pr_url = Column(String(500))
       pr_title = Column(String(500))
       pr_author = Column(String(100))
       
       # AI Tool Detection
       ai_tool = Column(Enum(AIToolType), nullable=False)
       ai_model = Column(String(100))  # e.g., "gpt-4", "claude-3"
       detection_method = Column(String(50))  # "metadata", "commit_msg", "manual"
       detection_confidence = Column(Float)  # 0.0 - 1.0
       
       # Validation Results
       validation_status = Column(Enum(ValidationStatus), default=ValidationStatus.PENDING)
       validators_run = Column(JSONB)  # List of validators executed
       validation_started_at = Column(DateTime)
       validation_completed_at = Column(DateTime)
       validation_duration_ms = Column(Integer)
       
       # Policy Results
       policy_pack_id = Column(UUID, ForeignKey("policy_packs.id"))
       policy_results = Column(JSONB)  # {policy_name: pass/fail, ...}
       blocking_policies = Column(JSONB)  # List of failed mandatory policies
       
       # Override (VCR)
       override_approved = Column(Boolean, default=False)
       override_reason = Column(Text)
       override_approved_by = Column(UUID, ForeignKey("users.id"))
       override_approved_at = Column(DateTime)
       
       # Evidence Trail
       prompt_hash = Column(String(64))  # SHA-256 of prompt (redacted)
       files_changed = Column(JSONB)  # List of files
       lines_added = Column(Integer)
       lines_removed = Column(Integer)
       
       # Relationships
       project = relationship("Project", back_populates="ai_code_events")
       policy_pack = relationship("PolicyPack")
       override_approver = relationship("User")
   ```

3. **Alembic Migration**
   ```bash
   alembic revision --autogenerate -m "add_ai_code_events_table"
   alembic upgrade head
   ```

4. **Indexes for Performance**
   ```sql
   CREATE INDEX idx_ai_code_events_project_id ON ai_code_events(project_id);
   CREATE INDEX idx_ai_code_events_created_at ON ai_code_events(created_at);
   CREATE INDEX idx_ai_code_events_validation_status ON ai_code_events(validation_status);
   CREATE INDEX idx_ai_code_events_ai_tool ON ai_code_events(ai_tool);
   ```

**Deliverables**:
- [ ] ADR-019 documented and approved
- [ ] AICodeEvent model created
- [ ] Alembic migration generated
- [ ] Indexes created
- [ ] Unit tests for model

**Assignee**: Backend Lead + DBA Review
**Estimated**: 2 days

---

### Day 5: GitHub PR Detection Design

**BriefingScript Reference**: BRS-2026-001-TASK-03

**Objective**: Design hooks to detect AI-generated PRs from GitHub.

**Tasks**:

1. **Detection Strategies**
   ```yaml
   Strategy 1 - Metadata Analysis:
     - Check PR description for AI tool markers
     - Parse commit messages for "Copilot", "Cursor", etc.
     - Check for known AI signature patterns
     Accuracy: ~70%
   
   Strategy 2 - GitHub API Integration:
     - Use GitHub Copilot API metadata (if available)
     - Check committer email patterns
     - Analyze diff patterns typical of AI
     Accuracy: ~85%
   
   Strategy 3 - Manual Tagging:
     - User marks PR as AI-generated
     - Required for non-GitHub AI tools
     - Fallback option
     Accuracy: 100% (user input)
   
   Recommendation: Combine all 3 strategies with weighted confidence
   ```

2. **Detection Service Interface**
   ```python
   # backend/app/services/ai_detection_service.py
   from abc import ABC, abstractmethod
   
   class AIDetectionResult:
       is_ai_generated: bool
       confidence: float  # 0.0 - 1.0
       detected_tool: AIToolType
       detected_model: Optional[str]
       detection_method: str
       evidence: dict
   
   class AIDetectionService(ABC):
       @abstractmethod
       async def detect(
           self,
           pr_data: dict,
           commits: List[dict],
           diff: str
       ) -> AIDetectionResult:
           pass
   
   class GitHubAIDetectionService(AIDetectionService):
       async def detect(self, pr_data, commits, diff) -> AIDetectionResult:
           # Combine multiple detection strategies
           metadata_result = await self._check_metadata(pr_data)
           commit_result = await self._check_commits(commits)
           pattern_result = await self._check_patterns(diff)
           
           # Weighted average confidence
           confidence = self._calculate_confidence(
               metadata_result, commit_result, pattern_result
           )
           
           return AIDetectionResult(
               is_ai_generated=confidence > 0.5,
               confidence=confidence,
               detected_tool=self._determine_tool(metadata_result, commit_result),
               detection_method="combined",
               evidence={...}
           )
   ```

3. **GitHub Webhook Handler**
   ```python
   # backend/app/api/routes/webhooks/github.py
   @router.post("/github/pr")
   async def handle_github_pr_webhook(
       request: Request,
       db: Session = Depends(get_db)
   ):
       payload = await request.json()
       
       if payload["action"] in ["opened", "synchronize"]:
           pr_data = payload["pull_request"]
           
           # Detect AI generation
           detection = await ai_detection_service.detect(
               pr_data=pr_data,
               commits=await fetch_commits(pr_data),
               diff=await fetch_diff(pr_data)
           )
           
           if detection.is_ai_generated:
               # Create AI code event
               event = await ai_code_event_service.create(
                   project_id=...,
                   pr_number=pr_data["number"],
                   ai_tool=detection.detected_tool,
                   detection_confidence=detection.confidence
               )
               
               # Trigger validation pipeline
               await validation_pipeline.queue(event.id)
   ```

**Deliverables**:
- [ ] Detection strategies documented
- [ ] AIDetectionService interface defined
- [ ] GitHubAIDetectionService skeleton
- [ ] Webhook handler skeleton
- [ ] Test dataset of 50 PRs (25 AI, 25 human)

**Assignee**: Backend Dev 2 + DevOps
**Estimated**: 1 day

---

## Week 2: Design Partner Program (Jan 13-17)

### Day 6-7: Partner Sourcing & Qualification

**BriefingScript Reference**: BRS-2026-001-TASK-04

**Objective**: Source 20 qualified Design Partner candidates.

**Tasks**:

1. **Target Partner Profile**
   ```yaml
   Ideal Partner:
     Company Size: 10-200 engineers
     Codebase: ≥100K LOC
     AI Usage: Heavy (Cursor/Copilot/Claude daily)
     Pain Points:
       - Architecture drift from AI code
       - Compliance gaps
       - No audit trail for AI changes
     Decision Maker: CTO, VP Engineering, Eng Manager
     
   Disqualifiers:
     - < 10 engineers (too small)
     - No active AI usage
     - Competitors
   ```

2. **Sourcing Channels**
   ```yaml
   Channel 1 - Network (Target: 8 candidates):
     - MTS client referrals
     - NQH partner network
     - Personal LinkedIn outreach
   
   Channel 2 - Communities (Target: 6 candidates):
     - VN tech Slack/Discord communities
     - AI developer communities
     - Tech conferences attendees list
   
   Channel 3 - Cold Outreach (Target: 6 candidates):
     - LinkedIn Sales Navigator
     - GitHub trending repo maintainers
     - Tech company engineering blogs
   ```

3. **Qualification Criteria Scorecard**
   ```yaml
   Scoring (Max 100 points):
     AI Usage (30 points):
       - Daily Copilot/Cursor: 30
       - Weekly: 20
       - Occasional: 10
       - None: 0
     
     Team Size (20 points):
       - 50-200 engineers: 20
       - 20-50: 15
       - 10-20: 10
       - <10: 5
     
     Pain Clarity (25 points):
       - Explicit architecture drift: 25
       - Compliance concerns: 20
       - General quality issues: 10
       - No clear pain: 0
     
     Decision Authority (25 points):
       - CTO/VP Eng: 25
       - Eng Manager: 15
       - Senior Dev: 5
   
   Qualified: ≥60 points
   Priority: ≥80 points
   ```

4. **Outreach Template**
   ```markdown
   Subject: Partnership opportunity - AI Safety for your engineering team
   
   Hi [Name],
   
   I noticed [Company] is actively using AI coding tools. 
   We're building the governance layer for AI-generated code and looking 
   for 10 design partners to shape the product.
   
   What you get:
   - 6-9 months free access
   - Direct influence on roadmap
   - Dedicated support channel
   - Grandfathered pricing at GA
   
   Would you have 30 mins next week for a quick chat?
   
   Best,
   [Name]
   ```

**Deliverables**:
- [ ] 20 qualified candidates in pipeline
- [ ] Scorecard completed for each
- [ ] 10 initial outreach emails sent
- [ ] 5 discovery calls scheduled

**Assignee**: Product Team + Customer Success
**Estimated**: 2 days

---

### Day 8-9: Workshop Deck Creation

**BriefingScript Reference**: BRS-2026-001-TASK-05

**Objective**: Create 90-minute workshop deck "AI Safety for Engineering Teams".

**Tasks**:

1. **Workshop Outline**
   ```yaml
   Duration: 90 minutes
   
   Part 1 - The Problem (20 min):
     - AI coding tools adoption curve
     - Hidden risks of AI-generated code
     - Real examples of architecture drift
     - Compliance gaps (audit trail, evidence)
   
   Part 2 - AI Safety Framework (25 min):
     - What is AI Safety Layer?
     - Detection → Validation → Policy → Evidence
     - Demo: AI PR flow through Orchestrator
     - 3 Killer Capabilities showcase
   
   Part 3 - Implementation Path (20 min):
     - Getting started (5 min setup)
     - Policy Pack configuration
     - Team onboarding guide
     - Integration with existing workflow
   
   Part 4 - Interactive Q&A (25 min):
     - Open discussion
     - Use case exploration
     - Partnership benefits
     - Next steps
   ```

2. **Key Slides (Minimum 25 slides)**
   ```yaml
   Opening (3 slides):
     1. Title: "AI Safety for Engineering Teams"
     2. Agenda
     3. About SDLC Orchestrator
   
   Problem (7 slides):
     4. AI tool adoption stats
     5. "Move fast, break architecture"
     6. Case study: Architecture drift
     7. Case study: Missing evidence
     8. Case study: Compliance gap
     9. The governance gap
     10. Cost of AI chaos
   
   Solution (8 slides):
     11. Introducing AI Safety Layer
     12. How it works (flow diagram)
     13. Detection: Know what's AI
     14. Validation: Check before merge
     15. Policy: Enforce your standards
     16. Evidence: Audit everything
     17. Demo screenshot 1
     18. Demo screenshot 2
   
   Implementation (4 slides):
     19. 5-minute setup
     20. Policy Pack configuration
     21. Team workflow
     22. Success metrics
   
   Partnership (3 slides):
     23. Design Partner benefits
     24. Timeline & expectations
     25. Q&A / Contact
   ```

**Deliverables**:
- [ ] Google Slides deck v1.0 (25+ slides)
- [ ] Speaker notes for each slide
- [ ] Demo script (5 min)
- [ ] Handout PDF

**Assignee**: Product Team + Frontend Dev 2 (for demo prep)
**Estimated**: 2 days

---

### Day 10: Sprint 41 Retrospective

**Tasks**:

1. **Retro Meeting** (1 hour)
   ```yaml
   Format: Start/Stop/Continue
   Participants: All sprint team members
   Facilitator: Scrum Master
   ```

2. **Metrics Review**
   ```yaml
   Analytics:
     - Events instrumented: X/10
     - Mixpanel setup: Complete/Partial/Blocked
   
   Schema:
     - ADR approved: Yes/No
     - Migration tested: Yes/No
   
   Detection:
     - Test accuracy: X%
     - Detection service: Complete/Partial
   
   Partners:
     - Candidates sourced: X/20
     - Calls scheduled: X/5
   
   Workshop:
     - Deck version: X.0
     - Demo ready: Yes/No
   ```

3. **Burndown Review**
   - Velocity points completed
   - Carryover items
   - Blockers encountered

**Deliverables**:
- [ ] Retro notes documented
- [ ] Action items assigned
- [ ] Sprint 42 backlog refined

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Mixpanel quota limit | Medium | Low | Monitor usage, upgrade plan if needed |
| Schema migration issues | High | Low | Test on staging first, rollback plan |
| Low partner response rate | Medium | Medium | Increase outreach volume, diversify channels |
| Workshop demo not ready | Medium | Low | Prepare fallback mockups |

---

## Dependencies

| Dependency | Owner | Status | Impact if Delayed |
|------------|-------|--------|-------------------|
| Mixpanel API keys | DevOps | ⏳ Pending | Block Day 1-2 |
| ADR-019 DBA review | DBA | ⏳ Pending | Block Day 3-4 |
| GitHub App credentials | DevOps | ✅ Ready | - |
| Partner contact list | Product | ⏳ Pending | Block Day 6-7 |

---

## Team Allocation

| Role | Name | Focus Areas | Capacity |
|------|------|-------------|----------|
| Backend Lead | TBD | Schema, Detection Service | 100% |
| Backend Dev 1 | TBD | Analytics Service | 100% |
| Backend Dev 2 | TBD | Webhook Handler | 100% |
| Frontend Dev 1 | TBD | Analytics Hook | 50% |
| Frontend Dev 2 | TBD | Demo Prep | 50% |
| DevOps | TBD | Infrastructure | 50% |
| Product | TBD | Partner Sourcing, Workshop | 100% |
| QA | TBD | Test Dataset, Validation | 100% |

---

## Definition of Done (Sprint Level)

- [ ] All P0 tasks completed
- [ ] Code reviewed and merged
- [ ] Tests passing (≥80% coverage)
- [ ] Documentation updated
- [ ] No P0/P1 bugs open
- [ ] MRP submitted for all merged PRs
- [ ] Retro completed

---

## Next Sprint Preview

**Sprint 42** (Jan 20 - Jan 31, 2026): AI Detection Implementation
- Implement full AI detection service
- Create validation pipeline skeleton
- Onboard first 2-3 Design Partners
- Conduct first workshop session

---

*Document Version: 1.0.0 | Created: December 20, 2025 | Framework: SDLC 6.1.0*
