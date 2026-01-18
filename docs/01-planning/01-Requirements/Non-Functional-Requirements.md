# Non-Functional Requirements (NFR)
## Quality Attributes and System Constraints

**Version**: 3.1.0
**Date**: December 23, 2025
**Status**: ACTIVE - AI Safety + Governance + Codegen Quality Gates
**Authority**: CTO + DevOps Lead Review (APPROVED)
**Foundation**: FRD v3.1.0, Product Vision 4.0.0
**Stage**: Stage 01 (WHAT - Planning & Analysis)
**Framework**: SDLC 5.1.1 Complete Lifecycle

**Changelog v3.1.0** (Dec 23, 2025):
- Added NFR29-NFR35: EP-06 Codegen Quality Gates performance requirements
- NFR29: Codegen Generation Latency (<30s per module, multi-provider)
- NFR30: 4-Gate Quality Pipeline Latency (<30s total validation)
- NFR31: Validation Loop Orchestration (max_retries=3, state persistence)
- NFR32: Evidence State Machine (8 states, <100ms transitions)
- NFR33: Codegen Observability (7 Prometheus metrics)
- NFR34: Context Alignment Performance (5 CTX checks <15s)
- NFR35: Escalation SLA (24 hours, queue monitoring)
- References: [Quality-Gates-Codegen-Specification.md](../../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)

**Changelog v3.0.0** (Dec 21, 2025):
- Updated framework to SDLC 5.1.1
- Added NFR22-NFR25: AI Safety Layer performance requirements
- Added NFR26-NFR28: Migration Engine scalability (1M+ LOC)
- Updated foundation references

**Changelog v2.0.0** (Dec 3, 2025):
- Added NFR18: AI Task Decomposition Performance
- Added NFR19: Planning Hierarchy Query Performance
- Added NFR20: Context-Aware Requirements Engine Performance
- Added NFR21: SDLC Structure Validation Performance
- Updated NFR Traceability to include FR6-FR9

---

## Document Purpose

This document defines **WHAT quality attributes the system must meet**, not HOW to achieve them (Stage 02 scope).

**Key Categories**:
- Performance (response time, throughput)
- Scalability (concurrent users, data volume)
- Security (encryption, authentication, authorization)
- Availability (uptime SLA, disaster recovery)
- Usability (time to first value, learning curve)
- Maintainability (code quality, technical debt)
- Compliance (SOC 2, GDPR, data retention)

---

## NFR Summary Table

| Category | NFRs | Priority | Impact |
|----------|------|----------|--------|
| Performance | NFR1-NFR3 | P0 | User experience |
| Scalability | NFR4-NFR6 | P0 | Growth support |
| Security | NFR7-NFR10 | P0 | Trust, compliance |
| Availability | NFR11-NFR12 | P0 | SLA, reliability |
| Usability | NFR13-NFR14 | P1 | Adoption rate |
| Compliance | NFR15-NFR17 | P0 | Legal, SOC 2 |
| AI Governance | NFR18-NFR21 | P0 | AI quality, CEO value *(v2.0)* |
| **EP-06 Codegen** | **NFR29-NFR35** | **P0** | **Quality Gates, Validation Loop** *(v3.1)* |

---

## NFR1: API Response Time

**Requirement**: API responses must be <200ms (p95) for read operations, <500ms (p95) for write operations.

**Measurements**:
- GET requests: <200ms p95 (e.g., /api/v1/gates/{id})
- POST requests: <500ms p95 (e.g., /api/v1/gates/evaluate)
- Complex queries: <1s p95 (e.g., dashboard metrics aggregation)

**Acceptance Criteria**:
```gherkin
Given production load (100 concurrent users)
When user requests gate status (GET /api/v1/gates/123)
Then response time is <200ms for 95% of requests
And response time is <500ms for 99% of requests
```

**Trade-offs**: Faster response may require caching (Redis), increased infrastructure cost.

---

## NFR2: Gate Evaluation Performance

**Requirement**: Gate evaluation must complete <500ms (p95) for 10 policy packs.

**Measurements**:
- Simple policy (1 rule): <50ms
- Complex policy (10+ rules): <200ms
- Full gate (10 policies): <500ms p95

**Acceptance Criteria**:
```gherkin
Given gate G1 with 10 policy packs
When system evaluates gate
Then evaluation completes <500ms for 95% of requests
And OPA evaluates 10K+ policies/sec (benchmark)
```

**Dependencies**: OPA performance (10K+ evals/sec documented)

---

## NFR3: Evidence Upload Performance

**Requirement**: Evidence upload must complete <2s for 10MB file.

**Measurements**:
- 1MB file: <500ms
- 5MB file: <1s
- 10MB file: <2s

**Acceptance Criteria**:
```gherkin
Given user uploads 10MB PDF
When upload to Evidence Vault
Then file uploaded + encrypted + virus-scanned in <2s
```

**Trade-offs**: Faster upload requires higher bandwidth (AWS S3 transfer acceleration).

---

## NFR4: Concurrent Users (Scalability)

**Requirement**: System must support 1,000 concurrent users (Year 3 target).

**Scaling Roadmap**:
- Year 1: 100 concurrent users (100 teams)
- Year 2: 500 concurrent users (454 teams)
- Year 3: 1,000 concurrent users (1,342 teams)

**Acceptance Criteria**:
```gherkin
Given 1,000 users logged in simultaneously
When all users access dashboard
Then system maintains <200ms response time (NFR1)
And no degradation in performance
```

**Architecture**: Auto-scaling (1-10 backend instances), load balancer (AWS ALB).

---

## NFR5: Data Volume (Scalability)

**Requirement**: System must handle 10TB total evidence storage (Year 3: 1,342 teams × 10GB/team).

**Storage Roadmap**:
- Year 1: 1TB (100 teams × 10GB)
- Year 2: 4.5TB (454 teams × 10GB)
- Year 3: 13TB (1,342 teams × 10GB)

**Acceptance Criteria**:
```gherkin
Given 10TB evidence stored in MinIO
When user searches evidence
Then search completes <200ms (NFR1)
And storage costs <$230/month (AWS S3 pricing: $23/TB)
```

**Cost Optimization**: MinIO self-hosted (free) vs AWS S3 ($23/TB/month).

---

## NFR6: Database Scalability

**Requirement**: PostgreSQL must handle 100M+ rows (Year 3 projection).

**Data Growth**:
- evidence table: 50M rows (1,342 teams × 10K evidence/team × 3 years)
- gates table: 10M rows (1,342 teams × 8 gates × 1K evaluations)
- audit_logs table: 100M rows (all user actions logged)

**Acceptance Criteria**:
```gherkin
Given PostgreSQL with 100M rows
When complex query (JOIN 3 tables)
Then query completes <1s (NFR1)
And no table scans (indexes enforced)
```

**Architecture**: Read replicas (2x), connection pooling (PgBouncer 1K connections).

---

## NFR7: Data Encryption

**Requirement**: All data encrypted at-rest (AES-256) and in-transit (TLS 1.3).

**Scope**:
- Evidence files: AES-256 (MinIO encryption)
- Database: AES-256 (PostgreSQL pgcrypto)
- API traffic: TLS 1.3 (HTTPS enforced)

**Acceptance Criteria**:
```gherkin
Given evidence file uploaded
Then file encrypted with AES-256 before storage
And encryption key rotated every 90 days
And decryption only with valid user authentication
```

**Compliance**: SOC 2 Type I requires encryption at-rest + in-transit.

---

## NFR8: Authentication & Authorization

**Requirement**: RBAC enforced with C-Suite + Engineering roles (Stage 00-09 SDLC Framework).

**Roles & Permissions**:
| Role | View Projects | Override Gates | Approve Budgets | View Audit Logs | Manage Users | Approve Stage Transition |
|------|--------------|----------------|-----------------|-----------------|--------------|-------------------------|
| **C-Suite Leadership** |
| CEO | All | ✅ (Emergency) | ✅ | ✅ | ✅ | ✅ (All Gates) |
| CTO | All | ✅ | ❌ | ✅ | ❌ | ✅ (G2, G3, G5, G6) |
| CPO | All | ❌ | ❌ | ✅ | ❌ | ✅ (G0.1, G0.2, G1, G4) |
| CIO | All | ❌ | ❌ | ✅ | ✅ | ✅ (G5, G6 - Operations) |
| CFO | All | ❌ | ✅ | ✅ | ❌ | ✅ (Budget Gates) |
| **Engineering Team** |
| EM | Own only | ❌ | ❌ | ❌ | ❌ | ❌ |
| PM | Assigned | ❌ | ❌ | ❌ | ❌ | ❌ |
| Dev Lead | Assigned | ❌ | ❌ | ❌ | ❌ | ❌ |
| QA Lead | Assigned | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Admin** |
| Admin | All | ✅ | ✅ | ✅ | ✅ | ✅ (All Gates) |

**Gate Approval Matrix (SDLC 5.1.3 Complete Lifecycle - 10 Stages)**:
| Gate | Stage | Approver(s) Required | Rationale |
|------|-------|---------------------|-----------|
| G0.1 | Stage 00 (WHY - Problem Foundation) | CPO + EM | Problem validated (5+ users) |
| G0.2 | Stage 00 (WHY - Business Case) | CEO + CPO | Strategic alignment ($4.7M+ value) |
| G1 | Stage 01 (WHAT - Requirements & Planning) | CTO + CPO | Scope defined (100+ ideas → Top 3) |
| G2 | Stage 02 (HOW - Design & Architecture) | CTO + Security Lead | API contracts validated, security reviewed |
| G3 | Stage 04 (BUILD - Development| | CTO + Dev Lead | Code quality (80%+ coverage, CI/CD passing) |
| G4 | Stage 05 (TEST - Quality Assurance| | CPO + QA Lead | UAT ≥8.5/10, zero P0 bugs, coverage ≥80% |
| G5 | Stage 06 (DEPLOY - Production Go-Live| | CTO + CIO | Pre-checks passed, rollback <5min, war room 24/7 |
| G6 | Stage 07 (OPERATE - Production Excellence| | CIO + DevOps Lead | Uptime ≥99.9%, P0 response <15min, monitoring ≥95% |
| G7 | Stage 03 (INTEGRATE - Systems Integration| | CTO + Data Lead | API contracts validated, integration tests ≥90% |
| G8 | Stage 08 (COLLABORATE - Team Coordination) | CPO + EM | Documentation ≥90%, velocity stable ±20% |
| G9 | Stage 09 (GOVERN - Strategic Oversight) | CEO + CFO | Zero violations, budget ±10%, stakeholder ≥8/10 |

**Acceptance Criteria**:
```gherkin
Given user role = EM
When user attempts to override gate
Then API returns 403 Forbidden
And audit log records unauthorized attempt

Given user role = CTO
When user overrides gate G2 (Architecture)
Then override succeeds
And audit log records: user_id, gate_id, reason, timestamp
And CPO receives notification (approval required for stage transition)

Given user role = CEO
When user approves emergency gate override
Then override succeeds (all gates)
And audit log marked as "EMERGENCY_OVERRIDE"
And all C-Suite notified via Slack
```

**Implementation**:
- JWT tokens (exp 1 hour), refresh tokens (exp 7 days)
- Role hierarchy: CEO > CTO/CPO/CIO/CFO > Admin > EM/PM/Dev Lead/QA Lead
- Multi-approval workflow: Gates G0.2, G1, G2 require 2+ approvers (e.g., G1 = CTO + CPO)

---

## NFR9: Audit Logging

**Requirement**: All user actions logged (who, what, when, where).

**Logged Actions**:
- Evidence access (view, download, delete)
- Gate overrides (manual approval)
- User management (create, update, delete)
- Policy pack changes (create, update, version)

**Acceptance Criteria**:
```gherkin
Given user downloads evidence
Then audit log entry created:
  - user_id, action="download", evidence_id, timestamp, ip_address
And audit log immutable (cannot be deleted/modified)
And audit log retained 7 years (SOC 2 compliance)
```

**Storage**: PostgreSQL audit_logs table (append-only).

---

## NFR10: Vulnerability Scanning

**Requirement**: All uploaded files virus-scanned (ClamAV) before storage.

**Scope**:
- Evidence uploads (PDFs, images, docs)
- Reject infected files (quarantine + notify admin)

**Acceptance Criteria**:
```gherkin
Given user uploads infected PDF (test virus: EICAR)
When file uploaded
Then ClamAV detects virus
And upload rejected with error "File contains virus"
And admin notified via Slack
```

**SLA**: Scan completes <1s for 10MB file (ClamAV benchmark).

---

## NFR11: Uptime SLA

**Requirement**: 99.9% uptime SLA (8.76 hours downtime/year).

**Calculation**:
- 99.9% = 365 days × 24 hours × 0.001 = 8.76 hours/year
- Planned maintenance: 4 hours/year (quarterly, off-peak)
- Unplanned outage budget: 4.76 hours/year

**Acceptance Criteria**:
```gherkin
Given production deployment
When measured over 365 days
Then uptime ≥99.9%
And downtime <8.76 hours/year
```

**Architecture**: Multi-AZ (AWS us-east-1a + us-east-1b), auto-scaling, health checks.

---

## NFR12: Disaster Recovery

**Requirement**: RTO <1 hour, RPO <5 minutes.

**Definitions**:
- RTO (Recovery Time Objective): Time to restore service after failure
- RPO (Recovery Point Objective): Max data loss in case of failure

**Acceptance Criteria**:
```gherkin
Given database failure (primary instance down)
When failover to read replica
Then service restored <1 hour (RTO)
And data loss <5 minutes (RPO = last backup)
```

**Implementation**: PostgreSQL streaming replication (lag <5s), automated failover.

---

## NFR13: Time to First Value

**Requirement**: Users achieve first value <1 hour (from signup to first gate check).

**Onboarding Steps**:
1. Signup (5 min)
2. Dashboard tour (10 min)
3. GitHub integration setup (15 min)
4. First gate check (30 min)
Total: 60 min

**Acceptance Criteria**:
```gherkin
Given new user signup
When user follows onboarding flow
Then user completes first gate check <1 hour
And user receives value (gate status = PASSED or BLOCKED with actionable feedback)
```

**Optimization**: Pre-built policy packs (no setup), guided onboarding wizard.

---

## NFR14: System Usability Scale (SUS)

**Requirement**: SUS score >70 (above average usability).

**Measurement**:
- SUS survey (10 questions, 1-5 scale)
- Target: >70/100 (above average)
- Baseline: 68 (industry average for B2B SaaS)

**Acceptance Criteria**:
```gherkin
Given 10 beta users complete SUS survey
When scores aggregated
Then average SUS score >70
And no critical usability issues (score <50)
```

**Testing**: Beta Week 11 (10 teams × 2 users = 20 SUS surveys).

---

## NFR15: SOC 2 Type I Compliance

**Requirement**: Achieve SOC 2 Type I certification by Week 12 (MVP launch).

**Controls Required** (Trust Service Criteria):
- CC6.1: Logical access controls (RBAC, NFR8)
- CC6.6: Encryption (AES-256, NFR7)
- CC7.2: System monitoring (Prometheus + Grafana)
- CC7.3: Audit logging (NFR9)

**Acceptance Criteria**:
```gherkin
Given SOC 2 Type I audit (Week 12)
When auditor reviews controls
Then all controls pass audit
And SOC 2 Type I report issued
```

**Timeline**: 6 months (start Week 12, complete Month 6).

---

## NFR16: GDPR Compliance

**Requirement**: GDPR-compliant (EU data protection regulation).

**Key Requirements**:
- Right to access: Users can export their data
- Right to deletion: Users can delete account + data (30-day retention)
- Data minimization: Only collect necessary data
- Consent: Users opt-in to data collection

**Acceptance Criteria**:
```gherkin
Given EU user requests data deletion
When user clicks "Delete Account"
Then all user data deleted within 30 days
And audit log shows deletion timestamp
And deletion confirmation email sent
```

**Scope**: EU users only (10% of Year 1 customers).

---

## NFR17: Data Retention

**Requirement**: Evidence retained 7 years (SOC 2 + legal compliance).

**Retention Policy**:
- Evidence: 7 years (active + archived)
- Audit logs: 7 years (immutable)
- User data: 30 days after account deletion
- Backups: 90 days (rotating)

**Acceptance Criteria**:
```gherkin
Given evidence uploaded 2025-01-13
When 2032-01-13 (7 years later)
Then evidence auto-archived (moved to cold storage)
And evidence still accessible (retrieval <1 hour)
```

**Cost Optimization**: Glacier storage ($1/TB/month vs S3 $23/TB/month).

---

## NFR18: AI Task Decomposition Performance

*(Added in v2.0.0 - December 3, 2025)*

**Requirement**: AI task decomposition must complete <2 minutes end-to-end with CEO-level quality.

**Measurements**:
- Context gathering: <5 seconds
- AI API call (Ollama primary): <90 seconds
- Response parsing: <5 seconds
- Total end-to-end: <2 minutes

**Acceptance Criteria**:
```gherkin
Given user story with 5 acceptance criteria
When user clicks "AI Decompose"
Then decomposition completes <2 minutes
And generated tasks have estimates and acceptance criteria
And completeness score ≥80%
```

**Fallback Chain**: Ollama (<100ms latency) → Claude (300ms) → GPT-4o (250ms) → Rule-based (50ms)

---

## NFR19: Planning Hierarchy Query Performance

*(Added in v2.0.0 - December 3, 2025)*

**Requirement**: Full traceability chain query (Task → Sprint → Phase → Roadmap → Vision) must complete <1s.

**Measurements**:
- Single level navigation: <100ms
- Full chain query (4 levels): <1s
- Aggregate metrics: <500ms

**Acceptance Criteria**:
```gherkin
Given backlog item with full chain
When user clicks "View Traceability"
Then full chain displayed <1 second
And alignment score calculated
And contributing objectives highlighted
```

**Database Optimization**: Recursive CTE with indexed foreign keys.

---

## NFR20: Context-Aware Requirements Engine Performance

*(Added in v2.0.0 - December 3, 2025)*

**Requirement**: Requirements classification must complete <500ms (p95) for all stage requirements.

**Measurements**:
- Single requirement classification: <50ms
- Full stage requirements (50+ items): <500ms
- Override workflow: <200ms

**Acceptance Criteria**:
```gherkin
Given project with 5 context dimensions configured
When user opens stage requirements view
Then requirements classified <500ms
And color-coded tiers displayed
And override links visible for eligible users
```

**Caching**: Requirements cached with 5-minute TTL, invalidated on profile change.

---

## NFR21: SDLC Structure Validation Performance

*(Added in v2.0.0 - December 3, 2025)*

**Requirement**: SDLC structure validation must complete <10 seconds for large projects.

**Measurements**:
- Small project (Level 0-1): <2 seconds
- Medium project (Level 0-2): <5 seconds
- Large project (Level 0-3): <10 seconds

**Acceptance Criteria**:
```gherkin
Given large project with 100+ files
When user runs `sdlc-validate --strict`
Then validation completes <10 seconds
And compliance score calculated
And violations listed with fix suggestions
```

**CI/CD Integration**: Pre-commit hook with <5 second timeout.

---

## NFR29: Codegen Generation Latency (EP-06)

*(Added in v3.1.0 - December 23, 2025)*

**Requirement**: Code generation must complete <30 seconds per IR module (p95) with multi-provider fallback.

**Measurements**:
- Simple module (1 entity): <10 seconds
- Complex module (5+ entities with relations): <20 seconds
- Full project (50 modules batch): <5 minutes total
- Provider fallback: <5 seconds per provider switch

**Acceptance Criteria**:
```gherkin
Given IR module with 3 entities
When user clicks "Generate Code"
Then generation completes <30 seconds (p95)
And provider used is logged with latency
And cost tracked per generation
```

**Provider Latency Targets**:
| Provider | Target Latency | Fallback Order |
|----------|---------------|----------------|
| Ollama (qwen2.5-coder:32b) | <15 seconds | Primary |
| Claude (Anthropic) | <25 seconds | Secondary |
| DeepCode (Q2 2026) | TBD | Tertiary |

**Technical Spec**: [Quality-Gates-Codegen-Specification.md §3.2](../../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)

---

## NFR30: 4-Gate Quality Pipeline Latency (EP-06)

*(Added in v3.1.0 - December 23, 2025)*

**Requirement**: 4-Gate quality validation must complete <30 seconds total for generated code.

**Measurements per Gate**:
| Gate | Validation | Target Latency | Cumulative |
|------|------------|----------------|------------|
| Gate 1 | Syntax (ast.parse, ruff) | <5 seconds | 5s |
| Gate 2 | Security (Semgrep SAST) | <10 seconds | 15s |
| Gate 3 | Context (5 CTX checks) | <10 seconds | 25s |
| Gate 4 | Tests (unit only, Dockerized) | <60 seconds | 85s* |

*Gate 4 runs async, not blocking evidence creation if skipped.

**Acceptance Criteria**:
```gherkin
Given generated code from IR module
When system runs quality pipeline
Then Gate 1-3 completes <25 seconds total
And Gate 4 completes <60 seconds (if enabled)
And gate results include Vietnamese error messages
```

**Technical Spec**: [Quality-Gates-Codegen-Specification.md §2](../../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)

---

## NFR31: Validation Loop Orchestration (EP-06)

*(Added in v3.1.0 - December 23, 2025)*

**Requirement**: Validation loop must support configurable retries with state persistence across service restarts.

**Configuration**:
```yaml
CODEGEN_MAX_RETRIES: 3              # Configurable
CODEGEN_ESCALATION_SLA_HOURS: 24    # Configurable
CODEGEN_ESCALATION_CHANNEL: council # council | human | abort
```

**Acceptance Criteria**:
```gherkin
Given generation fails Gate 2 (security)
When system retries generation
Then retry uses deterministic feedback
And attempt_number incremented
And state persisted to database

Given max_retries exceeded (attempt > 3)
When escalation triggered
Then escalation ticket created
And council/human notified within SLA
```

**State Persistence**:
- Loop state survives service restart
- Each attempt logged with full context
- Feedback deterministic (no AI randomness)

**Technical Spec**: [Quality-Gates-Codegen-Specification.md §3.1](../../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)

---

## NFR32: Evidence State Machine (EP-06)

*(Added in v3.1.0 - December 23, 2025)*

**Requirement**: Evidence state transitions must complete <100ms with full audit trail.

**8 States**:
```
generated → validating → retrying → escalated → evidence_locked → awaiting_vcr → merged/aborted
```

**Acceptance Criteria**:
```gherkin
Given evidence in 'validating' state
When all gates pass
Then state transitions to 'evidence_locked' <100ms
And transition logged with timestamp and actor
And evidence hash computed and locked

Given evidence in 'evidence_locked' state
When VCR workflow initiated
Then state transitions to 'awaiting_vcr' <100ms
And evidence immutable (no modifications allowed)
```

**Database Schema**:
```sql
CREATE TABLE codegen_evidence (
    id UUID PRIMARY KEY,
    state VARCHAR(20) NOT NULL,
    state_transitions JSONB, -- Array of {from, to, timestamp, actor}
    locked_hash VARCHAR(64),
    locked_at TIMESTAMP
);
```

**Technical Spec**: [Quality-Gates-Codegen-Specification.md §3.4](../../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)

---

## NFR33: Codegen Observability (EP-06)

*(Added in v3.1.0 - December 23, 2025)*

**Requirement**: 7 Prometheus metrics must be exposed for codegen monitoring.

**Required Metrics**:
| Metric | Type | Labels | Alert Threshold |
|--------|------|--------|-----------------|
| `codegen_attempts_total` | Counter | provider, status | - |
| `codegen_retry_count` | Histogram | provider | p95 > 2 |
| `codegen_gate_failures_total` | Counter | gate, reason | >10/hour |
| `codegen_latency_seconds` | Histogram | provider, mode | p95 > 60s |
| `codegen_evidence_state` | Gauge | state | escalated > 5 |
| `codegen_escalation_queue_size` | Gauge | channel | >5 |
| `codegen_provider_cost_usd` | Counter | provider | >$100/day |

**Acceptance Criteria**:
```gherkin
Given codegen service running
When Prometheus scrapes /metrics
Then all 7 metrics available
And metrics labeled correctly
And Grafana dashboard shows 3+ panels

Given escalation queue > 5
When alert rule evaluates
Then PagerDuty/Slack notification sent
```

**Technical Spec**: [Quality-Gates-Codegen-Specification.md §3.5](../../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)

---

## NFR34: Context Alignment Performance (EP-06)

*(Added in v3.1.0 - December 23, 2025)*

**Requirement**: 5 Context Alignment Checks (CTX-01 to CTX-05) must complete <15 seconds total.

**CTX Checks**:
| Check | Description | Target Latency |
|-------|-------------|----------------|
| CTX-01 | IR Module Coverage | <2 seconds |
| CTX-02 | Entity-Schema Consistency | <3 seconds |
| CTX-03 | Route-Module Binding | <3 seconds |
| CTX-04 | Reference Existence | <3 seconds |
| CTX-05 | API Shape vs IR | <4 seconds |

**Acceptance Criteria**:
```gherkin
Given generated code with 10 entity references
When Gate 3 context validation runs
Then all 5 CTX checks complete <15 seconds
And alignment score calculated (0-100%)
And failures include Vietnamese remediation suggestions
```

**Alignment Score Threshold**: ≥80% required for Gate 3 PASS

**Technical Spec**: [Quality-Gates-Codegen-Specification.md §3.2.4](../../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)

---

## NFR35: Escalation SLA (EP-06)

*(Added in v3.1.0 - December 23, 2025)*

**Requirement**: Escalation handling must complete within 24-hour SLA with queue monitoring.

**Escalation Channels**:
| Channel | Target | SLA | Notification |
|---------|--------|-----|--------------|
| council | AI Council | 4 hours | Async processing |
| human | Slack/PagerDuty | 24 hours | Real-time alert |
| abort | None | Immediate | Evidence marked ABORTED |

**Acceptance Criteria**:
```gherkin
Given escalation ticket created
When 24 hours elapsed without resolution
Then ticket auto-escalated to CTO
And warning email sent to PM
And evidence state remains 'escalated'

Given council escalation
When multi-agent deliberation completes
Then decision logged (approve/reject/modify)
And evidence state updated accordingly
And audit trail includes reasoning
```

**Queue Monitoring**:
- Alert: `codegen_escalation_queue_size > 5`
- Dashboard: Escalation aging chart
- SLA Breach: Auto-escalate to CTO

**Technical Spec**: [Quality-Gates-Codegen-Specification.md §3.1.2](../../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)

---

## NFR Traceability to Functional Requirements

| NFR | Related FR | Rationale |
|-----|------------|-----------|
| NFR1-NFR3 | FR1-FR6 | Performance critical for gate checks, AI, dashboard |
| NFR4-NFR6 | All FRs | Scalability supports growth (100 → 1,000 teams) |
| NFR7-NFR10 | FR2 | Security protects Evidence Vault data |
| NFR11-NFR12 | All FRs | Availability ensures 99.9% uptime SLA |
| NFR13-NFR14 | FR4-FR5 | Usability drives adoption (Feature Adoption Rate 70%+) |
| NFR15-NFR17 | FR2 | Compliance enables Enterprise sales (SOC 2) |
| NFR18 | FR7 | AI Task Decomposition must match CEO-level quality *(v2.0)* |
| NFR19 | FR8 | Planning Hierarchy enables full traceability *(v2.0)* |
| NFR20 | FR6 | Context-Aware Requirements dynamically classify *(v2.0)* |
| NFR21 | FR9 | SDLC Structure Validator enforces compliance *(v2.0)* |
| **NFR29** | **FR41** | **Codegen Generation Latency <30s per module** *(v3.1)* |
| **NFR30** | **FR42** | **4-Gate Quality Pipeline <30s total** *(v3.1)* |
| **NFR31** | **FR43** | **Validation Loop max_retries=3, state persistence** *(v3.1)* |
| **NFR32** | **FR44** | **Evidence State Machine 8 states, <100ms transitions** *(v3.1)* |
| **NFR33** | **FR45** | **Codegen Observability 7 Prometheus metrics** *(v3.1)* |
| **NFR34** | **FR42.3** | **Context Alignment 5 CTX checks <15s** *(v3.1)* |
| **NFR35** | **FR43.3** | **Escalation SLA 24 hours, queue monitoring** *(v3.1)* |

---

## Testing Strategy (NFRs)

### Performance Testing
- **Load testing**: Simulate 1,000 concurrent users (JMeter, Locust)
- **Stress testing**: Find breaking point (max concurrent users)
- **Benchmarking**: OPA 10K+ evals/sec, PostgreSQL 100K+ rows/sec

### Security Testing
- **Penetration testing**: Week 12 (external firm, $10K budget)
- **Vulnerability scanning**: ClamAV, Dependabot, Snyk
- **RBAC testing**: Verify EM cannot override gates (403 Forbidden)

### Availability Testing
- **Chaos engineering**: Simulate failures (Chaos Monkey)
- **Disaster recovery drill**: Test RTO <1 hour, RPO <5 min

### Usability Testing
- **SUS survey**: Beta Week 11 (10 teams × 2 users = 20 surveys)
- **Time to First Value**: Track onboarding duration (target <1 hour)

---

## Document Control

**Version History**:
- v3.1.0 (December 23, 2025): Added NFR29-NFR35 for EP-06 Codegen Quality Gates (28 requirements total)
- v3.0.0 (December 21, 2025): SDLC 5.1.1 update, EP-02/04/05/06 NFRs added
- v2.0.0 (December 3, 2025): Added NFR18-NFR21 for AI Governance (21 requirements total)
- v1.0.0 (November 13, 2025): Initial NFR (17 requirements)

**Review Schedule**:
- CTO Review: Week 2 ✅ APPROVED
- DevOps Lead Review: Week 2 ✅ APPROVED
- Security Review: Week 2 ✅ APPROVED

**Related Documents**:
- [Functional Requirements Document](./Functional-Requirements-Document.md) (v3.1.0)
- [Product Roadmap](../../00-foundation/04-Roadmap/Product-Roadmap.md) (v5.0.0)
- [Product Vision](../../00-foundation/01-Vision/Product-Vision.md) (v4.0.0)
- [EP-04 SDLC Structure Enforcement](../02-Epics/EP-04-SDLC-Structure-Enforcement.md)
- [EP-05 Enterprise Migration](../02-Epics/EP-05-ENTERPRISE-SDLC-MIGRATION.md)
- [EP-06 IR-Based Codegen Engine](../02-Epics/EP-06-IR-Based-Codegen-Engine.md)
- **[Quality-Gates-Codegen-Specification.md](../../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)** *(NEW v3.1)*

---

**Document**: SDLC-Orchestrator-Non-Functional-Requirements
**Framework**: SDLC 5.1.1 Stage 01 (WHAT) - Planning & Analysis
**Component**: Quality Attributes and System Constraints
**Review**: Quarterly with CTO + DevOps Lead
**Last Updated**: December 23, 2025

*"Define quality before you build quality."*
