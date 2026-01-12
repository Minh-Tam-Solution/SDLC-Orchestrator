# Vibecode CLI Requirements Summary - Q2/H2 2026

**Document ID**: VIBECODE-CLI-REQ-2026-001
**Version**: 1.0.0
**Date**: January 17, 2026
**Status**: DRAFT (awaiting CTO approval)
**Owner**: PM/PO
**Budget**: $90,000 (reallocated from OpenCode evaluation abort)

---

## 📋 EXECUTIVE SUMMARY

### Context

On January 12, 2026, the **OpenCode integration evaluation was aborted** after 4 hours of discovery revealed strategic misalignment:
- OpenCode is a CLI/TUI tool (competitor to Claude Code, Cursor)
- No HTTP API for integration (ADR-026 assumption invalid)
- Integration would require $50K-$80K fork + custom API layer

**Decision**: Reallocate $90K to **Vibecode CLI** (our core differentiator for Vietnamese SME market)

### Vision

**Vibecode CLI** is an **IR-based deterministic code generator** designed for **Vietnamese SMEs**, enabling them to build enterprise-grade software with:
- Vietnamese domain-specific templates (E-commerce, HRM, CRM)
- 4-Gate Quality Pipeline validation (Syntax → Security → Context → Tests)
- Evidence-based audit trail for compliance (ISO 9001, GDPR)
- Integration with SDLC Orchestrator for governance

### Budget Allocation

| Period | Phase | Budget | Focus |
|--------|-------|--------|-------|
| **Q2 2026** | Level 1 Enhancements | $30,000 | Core IR Processor + Vietnamese templates |
| **H2 2026** | Level 2-3 Optimizations | $60,000 | Multi-provider + Vietnam pilot (5 customers) |
| **TOTAL** | - | **$90,000** | Full productization |

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Code Generation Success Rate | >80% | Generated code passes 4-Gate pipeline |
| Vietnamese Template Coverage | 3+ domains | E-commerce, HRM, CRM templates available |
| Time to Generate | <60s | p95 latency (vs 2-4h manual coding) |
| Customer Satisfaction | ≥4/5 | Post-pilot survey (5 founding customers) |
| Vietnam SME Pilot | 5 customers | Paying customers by Q4 2026 |

---

## 🎯 STRATEGIC POSITIONING

### Market Opportunity

**Target**: Vietnamese SME companies (10-50 employees)
- 250,000+ SMEs in Vietnam (2024 data)
- 60% lack internal software development capability
- $2.5B software outsourcing market (growing 15% YoY)

**Problem**: Vietnamese SMEs struggle with:
- High cost of custom software development ($50-$100K per project)
- Language barrier (most tools are English-first)
- Lack of technical expertise (no in-house developers)
- Compliance requirements (Vietnam-specific regulations)

**Solution**: Vibecode CLI enables **citizen developers** to generate production-ready code from Vietnamese specifications

### Competitive Landscape

| Competitor | Strength | Weakness | Vibecode CLI Advantage |
|------------|----------|----------|------------------------|
| **GitHub Copilot** | Large model, good code completion | English-first, no Vietnamese domain knowledge | Vietnamese templates + domain expertise |
| **Cursor/Claude Code** | IDE integration, chat interface | Generic (not SME-focused), no governance | 4-Gate Quality Pipeline + Evidence Vault |
| **OpenCode** | Open source, free | CLI only, no HTTP API, no Vietnamese support | API-first, Vietnamese-first, governance-ready |
| **ChatGPT Code Interpreter** | General purpose, easy to use | No specialization, no audit trail | Deterministic IR, full traceability |

**Key Differentiators**:
1. ✅ **Vietnamese-first** (templates, documentation, support)
2. ✅ **Domain-specific** (E-commerce, HRM, CRM templates)
3. ✅ **Deterministic** (IR-based generation, not probabilistic)
4. ✅ **Governance-ready** (4-Gate pipeline, Evidence Vault)
5. ✅ **SME-focused** (affordable, easy to use, no coding required)

---

## 📐 ARCHITECTURE OVERVIEW

### 5-Layer Software 3.0 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 5: AI CODERS (External - We Orchestrate)                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │   Cursor    │ │ Claude Code │ │   Copilot   │ │  OpenCode │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
│         ↑               ↑               ↑              ↑        │
│         └───────────────┴───────────────┴──────────────┘        │
│                    Governance API + Quality Gates               │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 4: VIBECODE CLI (Our Innovation - Q2/H2 2026)             │
│  • IR Processor Service (Spec → Intermediate Representation)   │
│  • Vietnamese Domain Templates (E-commerce, HRM, CRM)           │
│  • 4-Gate Quality Pipeline (Syntax → Security → Context → Test) │
│  • Multi-Provider Gateway (Ollama → Claude → DeepCode)          │
│  • Evidence State Machine (8 states, immutable audit)           │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 3: SDLC ORCHESTRATOR (Governance Layer)                   │
│  • Gate Engine API (OPA-powered Policy-as-Code)                 │
│  • Evidence Vault API (S3 + SHA256 integrity)                   │
│  • SASE Artifacts (BRS, MRP, VCR for traceability)              │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 2: INTEGRATION (Thin Adapters)                            │
│  • opa_service.py → OPA REST API (policy validation)           │
│  • minio_service.py → MinIO S3 API (evidence storage)          │
│  • ollama_service.py → Ollama REST API (AI provider)           │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 1: INFRASTRUCTURE (OSS Components)                        │
│  • Ollama (api.nhatquangholding.com) - Primary AI provider      │
│  • MinIO (AGPL v3) - Evidence storage (network-only)            │
│  • OPA (Apache-2.0) - Policy evaluation engine                  │
│  • PostgreSQL 15.5 - Database (project metadata)                │
└─────────────────────────────────────────────────────────────────┘
```

**Vibecode CLI Position**: **Layer 4** (EP-06 Codegen Engine)
- Sits ABOVE SDLC Orchestrator governance layer
- Uses Orchestrator's Evidence Vault + 4-Gate pipeline
- Provides deterministic code generation (vs probabilistic AI coders)

### IR (Intermediate Representation) Approach

**Why IR?**
- ✅ **Deterministic**: Same spec → Same code (reproducible)
- ✅ **Traceable**: Spec → IR → Code (full audit trail)
- ✅ **Governable**: IR can be validated before code generation
- ✅ **Template-driven**: Domain-specific templates (not generic prompts)

**IR Flow**:
```
Vietnamese Spec (YAML)
    ↓
Spec Parser (validate structure)
    ↓
IR Generator (domain-specific transformation)
    ↓
IR Validator (semantic validation)
    ↓
Code Generator (template instantiation)
    ↓
4-Gate Quality Pipeline (Syntax → Security → Context → Tests)
    ↓
Generated Code (production-ready)
```

---

## 🚀 LEVEL 1 ENHANCEMENTS (Q2 2026 - $30K)

### Timeline: Q2 2026 (April - June)

**Duration**: 12 weeks (3 sprints x 4 weeks)
**Budget**: $30,000
**Team**: 2 Backend + 1 Frontend + PM/PO
**Outcome**: Vibecode CLI MVP (beta release)

### Sprint 1 (Weeks 1-4): IR Processor Service

**Goal**: Build core IR processing engine

**Deliverables**:
1. **Spec Parser** (Vietnamese YAML → AST)
   - YAML schema validation (100+ rules)
   - Vietnamese keyword support (e.g., `chức_năng`, `điều_kiện`, `kết_quả`)
   - Error messages in Vietnamese

2. **IR Generator** (AST → Intermediate Representation)
   - Domain-agnostic IR schema (JSON format)
   - Support for: entities, fields, relationships, business rules, workflows
   - Validation: referential integrity, circular dependency detection

3. **IR Validator** (Semantic Validation)
   - Business rule validation (e.g., "discount cannot exceed price")
   - Data type consistency (e.g., "phone number must be string")
   - Performance validation (e.g., "N+1 query detection")

**Success Criteria**:
- Parse 10 sample Vietnamese specs (100% success rate)
- Generate valid IR for 3 domains (E-commerce, HRM, CRM)
- Validation catches 90%+ semantic errors

**Budget**: $10,000

---

### Sprint 2 (Weeks 5-8): Vietnamese Domain Templates

**Goal**: Create production-ready templates for 3 domains

**Deliverables**:

#### Template 1: E-commerce (Thương mại điện tử)
**Scope**: Basic online store
- Entities: Product, Category, Cart, Order, Customer, Payment
- Features: Product listing, cart management, checkout, order tracking
- Business Rules: Inventory management, pricing rules, discount calculation
- Output: FastAPI (backend) + React (frontend) + PostgreSQL (database)

**Example Vietnamese Spec**:
```yaml
chức_năng: Quản lý sản phẩm
mô_tả: Hệ thống quản lý sản phẩm cho cửa hàng trực tuyến
thực_thể:
  - tên: SảnPhẩm
    thuộc_tính:
      - tên: tên_sản_phẩm
        kiểu: chuỗi
        bắt_buộc: có
      - tên: giá_bán
        kiểu: số
        điều_kiện: giá_bán > 0
```

#### Template 2: HRM (Quản lý nhân sự)
**Scope**: Basic HR management system
- Entities: Employee, Department, Position, Leave Request, Payroll
- Features: Employee directory, leave management, payroll calculation, attendance tracking
- Business Rules: Leave balance calculation, overtime rules, salary structure
- Output: FastAPI (backend) + React (frontend) + PostgreSQL (database)

#### Template 3: CRM (Quản lý quan hệ khách hàng)
**Scope**: Basic customer relationship management
- Entities: Customer, Lead, Opportunity, Contact, Task
- Features: Lead tracking, sales pipeline, contact management, task scheduling
- Business Rules: Lead scoring, opportunity stage progression, task assignment
- Output: FastAPI (backend) + React (frontend) + PostgreSQL (database)

**Success Criteria**:
- 3 templates available (E-commerce, HRM, CRM)
- Each template generates working MVP (100% functional)
- Vietnamese documentation complete (setup guide, API docs)

**Budget**: $12,000

---

### Sprint 3 (Weeks 9-12): 4-Gate Quality Pipeline

**Goal**: Integrate Vibecode CLI with SDLC Orchestrator's 4-Gate pipeline

**Deliverables**:

#### Gate 1: Syntax Validation (<5s)
- Python: `ast.parse()` + `ruff` linter
- TypeScript: `tsc --noEmit` compiler check
- SQL: `sqlfluff` linter
- Exit code validation: 0 = pass, non-zero = fail

#### Gate 2: Security Validation (<10s)
- SAST: Semgrep with AI-specific rules
- Dependency scan: Check for known vulnerabilities
- Secrets detection: No hardcoded credentials
- OWASP Top 10 validation

#### Gate 3: Context Validation (<10s)
- File existence: All imports resolve
- API contract: OpenAPI schema validation
- Database schema: Migration scripts valid
- Cross-reference: No broken links

#### Gate 4: Test Validation (<60s)
- Unit tests: `pytest` execution (if tests exist)
- Coverage: ≥80% target (optional)
- Integration tests: API contract tests
- E2E tests: Critical user journey (optional)

**4-Gate Workflow**:
```
Generated Code
    ↓
Gate 1: Syntax → PASS/FAIL
    ↓
Gate 2: Security → PASS/FAIL
    ↓
Gate 3: Context → PASS/FAIL
    ↓
Gate 4: Tests → PASS/FAIL
    ↓
Evidence Vault (store results + SHA256 hash)
    ↓
MRP Generated (Merge-Readiness Pack)
```

**Success Criteria**:
- 4 gates implemented and integrated
- Generated code passes all 4 gates (>80% success rate)
- Evidence stored in MinIO (SHA256 integrity)
- MRP auto-generated (5 evidence types)

**Budget**: $8,000

---

## 🎯 LEVEL 2-3 OPTIMIZATIONS (H2 2026 - $60K)

### Timeline: H2 2026 (July - December)

**Duration**: 24 weeks (2 phases x 12 weeks)
**Budget**: $60,000
**Team**: 2 Backend + 1 Frontend + 1 DevOps + PM/PO
**Outcome**: Production-ready Vibecode CLI + Vietnam pilot (5 customers)

### Level 2: Multi-Provider Codegen (Weeks 13-24) - $30K

**Goal**: Improve generation quality and reliability

**Deliverables**:

#### 1. Multi-Provider Gateway
- **Primary**: Ollama (api.nhatquangholding.com)
  - Model: `qwen3-coder:30b` (~50 tok/s, 256K context)
  - Cost: $50/month (flat rate)
  - Latency: <15s (p95)

- **Fallback 1**: Claude (Anthropic API)
  - Model: `claude-sonnet-4-5-20250929`
  - Cost: $1000/month (metered)
  - Latency: <25s (p95)
  - Trigger: Ollama timeout (>30s) or error

- **Fallback 2**: DeepCode (Vietnam AI provider - TBD)
  - Model: `deepcode-v1` (Vietnamese-optimized)
  - Cost: TBD (negotiating partnership)
  - Latency: <20s (p95)
  - Trigger: Claude quota exceeded

**Provider Selection Logic**:
```python
def select_provider(spec, context):
    if spec.complexity < 100 lines:
        return "ollama"  # Fast, cheap
    elif spec.language == "vietnamese" and context.domain in ["ecommerce", "hrm", "crm"]:
        return "ollama"  # Domain templates optimized for Ollama
    elif spec.complexity > 500 lines:
        return "claude"  # Better for complex specs
    else:
        return "ollama"  # Default
```

#### 2. N-Version Programming Support
- Generate 2-3 code variants (using different providers)
- Present side-by-side comparison to user
- User selects best variant (or hybrid combination)
- Store selection rationale in Evidence Vault

#### 3. Validation Loop Orchestrator
- **max_retries**: 3 (configurable)
- **Feedback loop**: Gate failure → Extract error → Re-generate with fix
- **Deterministic feedback**: Parse gate error → Convert to IR constraint
- **Escalation**: If 3 retries fail → Human review (VCR workflow)

**Success Criteria**:
- Multi-provider fallback working (100% availability)
- Generation quality improved (>90% 4-Gate pass rate)
- Average cost <$5 per generation (95% Ollama usage)

**Budget**: $20,000

---

#### 4. Evidence-Based Audit Trail
- **8-State Evidence Lifecycle**:
  ```
  generated → validating → passed/failed → retrying (if failed)
  → escalated (if max_retries) → evidence_locked → awaiting_vcr
  → merged/aborted
  ```

- **Evidence Storage** (MinIO S3):
  - Spec YAML (input)
  - Generated IR (intermediate)
  - Generated code (output)
  - 4-Gate results (validation evidence)
  - MRP bundle (merge-readiness pack)
  - VCR decision (approval record)

- **Immutable Audit Trail**:
  - SHA256 hash for all evidence
  - Version control (Git integration)
  - Timestamp + author for all changes

**Success Criteria**:
- 100% evidence captured (no missing audit trail)
- Evidence Vault integration complete
- SASE artifacts (BRS/MRP/VCR) auto-generated

**Budget**: $10,000

---

### Level 3: Vietnam SME Pilot (Weeks 25-36) - $30K

**Goal**: Validate product-market fit with 5 founding customers

**Deliverables**:

#### 1. Founding Customer Recruitment (Weeks 25-26)
- **Target**: 5 Vietnamese SMEs (10-50 employees)
- **Criteria**:
  - Active software development need (new project starting)
  - Budget: $10K-$50K per project
  - Willing to use beta product (with support)
  - Vietnamese-speaking team (no English requirement)

- **Recruitment Channels**:
  - NQH network (existing customers + partners)
  - Vietnam Chamber of Commerce (SME directory)
  - Tech community events (Hanoi + Ho Chi Minh City)

**Budget**: $5,000 (marketing + events)

---

#### 2. Pilot Onboarding (Weeks 27-28)
- **Onboarding Workshop** (4 hours per customer)
  - Introduction to Vibecode CLI (Vietnamese)
  - Hands-on lab: Generate first application (E-commerce sample)
  - Q&A + troubleshooting

- **Support Package**:
  - Dedicated Slack channel (Vietnamese support)
  - 1-hour weekly check-in (video call)
  - Priority bug fixes (24-hour SLA)

**Budget**: $5,000 (PM/PO time + support infrastructure)

---

#### 3. Pilot Execution (Weeks 29-34)
- **Each Customer Project**:
  - Week 1-2: Spec writing workshop (convert requirements → Vietnamese YAML)
  - Week 3-4: Code generation + 4-Gate validation
  - Week 5: Deployment + training
  - Week 6: Retrospective + feedback collection

- **Success Metrics**:
  - Code generation success rate: >80%
  - Customer satisfaction: ≥4/5
  - Time to deploy: <6 weeks (vs 12-16 weeks traditional development)
  - Cost savings: ≥50% (vs outsourcing)

**Budget**: $15,000 (PM/PO + Backend support time)

---

#### 4. Pilot Retrospective (Weeks 35-36)
- **Data Collection**:
  - Customer satisfaction survey (5-point scale)
  - Time-to-deploy measurement (vs baseline)
  - Cost analysis (Vibecode CLI vs outsourcing)
  - Defect rate (bugs per 1000 lines of code)

- **Outcomes**:
  - Case studies (3 success stories)
  - Product-market fit validation (go/no-go for GA launch)
  - Pricing model refinement ($X per generation, $Y per month subscription)
  - Roadmap for Q1 2027 (based on customer feedback)

**Budget**: $5,000 (PM/PO + Analyst time)

---

## 📊 SUCCESS METRICS & KPIs

### Q2 2026 Level 1 Targets

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Code Generation Success Rate** | N/A | >80% | Generated code passes 4-Gate pipeline |
| **Vietnamese Template Coverage** | 0 | 3 domains | E-commerce, HRM, CRM available |
| **Time to Generate** | 2-4h manual | <60s | p95 latency from spec → code |
| **4-Gate Pass Rate** | N/A | >70% | First-time pass without retry |
| **IR Validator Accuracy** | N/A | >90% | Semantic errors caught before generation |

### H2 2026 Level 2-3 Targets

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Multi-Provider Availability** | N/A | 100% | Uptime with fallback |
| **Average Cost per Generation** | N/A | <$5 | 95% Ollama, 5% Claude fallback |
| **Evidence Capture Rate** | N/A | 100% | All generations stored in Evidence Vault |
| **Customer Satisfaction** | N/A | ≥4/5 | Post-pilot survey (5 founding customers) |
| **Time to Deploy** | 12-16 weeks | <6 weeks | Spec → production (50% reduction) |
| **Cost Savings** | $50K outsourcing | $25K Vibecode | ≥50% savings for SME customers |

---

## 💰 BUDGET BREAKDOWN

### Q2 2026 Level 1 ($30K)

| Sprint | Focus | Duration | Budget | Team |
|--------|-------|----------|--------|------|
| Sprint 1 | IR Processor Service | 4 weeks | $10,000 | 2 Backend + PM/PO |
| Sprint 2 | Vietnamese Domain Templates | 4 weeks | $12,000 | 2 Backend + 1 Frontend + PM/PO |
| Sprint 3 | 4-Gate Quality Pipeline | 4 weeks | $8,000 | 2 Backend + PM/PO |
| **TOTAL** | **Q2 2026** | **12 weeks** | **$30,000** | **Avg 3-4 FTE** |

### H2 2026 Level 2-3 ($60K)

| Phase | Focus | Duration | Budget | Team |
|-------|-------|----------|--------|------|
| Level 2 | Multi-Provider + Evidence Audit | 12 weeks | $30,000 | 2 Backend + 1 Frontend + PM/PO |
| Level 3 | Vietnam SME Pilot (5 customers) | 12 weeks | $30,000 | PM/PO + Backend support |
| **TOTAL** | **H2 2026** | **24 weeks** | **$60,000** | **Avg 3-4 FTE** |

### Total Investment ($90K)

| Period | Budget | Outcome |
|--------|--------|---------|
| Q2 2026 | $30,000 | Vibecode CLI MVP (beta release) |
| H2 2026 | $60,000 | Production-ready + 5 customer pilot |
| **TOTAL** | **$90,000** | **Product-market fit validated** |

---

## 🚧 RISKS & MITIGATION

| Risk | Likelihood | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| **Vietnamese template quality** | MEDIUM | HIGH | Hire Vietnamese domain expert (E-commerce/HRM/CRM) | PM/PO |
| **IR schema complexity** | HIGH | MEDIUM | Start simple (80/20 rule), iterate based on pilot | Architect |
| **Ollama model capability** | MEDIUM | HIGH | Multi-provider fallback (Claude, DeepCode) | Backend Lead |
| **SME customer recruitment** | MEDIUM | HIGH | Leverage NQH network, offer pilot discount | PM/PO |
| **Vietnam market timing** | LOW | MEDIUM | Q4 2026 pilot allows Q1 2027 GA launch | CTO |

---

## 📅 TIMELINE OVERVIEW

```
Q2 2026 (Apr-Jun): Level 1 MVP
├── Sprint 1 (Weeks 1-4): IR Processor Service
├── Sprint 2 (Weeks 5-8): Vietnamese Domain Templates
└── Sprint 3 (Weeks 9-12): 4-Gate Quality Pipeline

H2 2026 (Jul-Dec): Level 2-3 Production
├── Level 2 (Weeks 13-24): Multi-Provider + Evidence Audit
└── Level 3 (Weeks 25-36): Vietnam SME Pilot (5 customers)
    ├── Weeks 25-26: Customer recruitment
    ├── Weeks 27-28: Onboarding workshops
    ├── Weeks 29-34: Pilot execution
    └── Weeks 35-36: Retrospective + case studies

Q1 2027 (Jan-Mar): GA Launch (dependent on pilot success)
```

---

## 🎯 GO/NO-GO DECISION CRITERIA

### Q2 2026 End (Jun 30) - Level 1 Checkpoint

**Criteria for "GO" to Level 2-3**:
- ✅ IR Processor generates valid IR for 3 domains (100% success)
- ✅ 3 Vietnamese templates available (E-commerce, HRM, CRM)
- ✅ 4-Gate pipeline integrated (>70% first-time pass rate)
- ✅ MVP demo ready (working E-commerce app generated from spec)
- ✅ CTO approval for $60K Level 2-3 budget

**Criteria for "NO-GO" (pause or pivot)**:
- ❌ IR schema too complex (>6 months to production)
- ❌ Template quality poor (<50% 4-Gate pass rate)
- ❌ Ollama model insufficient (fallback costs >$500/month)

### Q4 2026 End (Dec 31) - Level 2-3 Checkpoint

**Criteria for "GO" to GA Launch (Q1 2027)**:
- ✅ 5 founding customers completed pilot
- ✅ Customer satisfaction ≥4/5 (average across 5 customers)
- ✅ Time to deploy <6 weeks demonstrated (vs 12-16 weeks baseline)
- ✅ Cost savings ≥50% demonstrated (vs outsourcing)
- ✅ Case studies available (3 success stories)
- ✅ Pricing model validated ($X per generation or $Y per month)

**Criteria for "NO-GO" (refine or abandon)**:
- ❌ <3 customers completed pilot (recruitment failed)
- ❌ Customer satisfaction <3/5 (poor product-market fit)
- ❌ No cost savings demonstrated (not competitive with outsourcing)

---

## 📚 REFERENCES

### 1. OpenCode Abort Decision
- Path: `docs/99-archive/OpenCode-Evaluation-Aborted-Jan12-2026/SUMMARY.md`
- Budget reallocated: $90K → Vibecode CLI

### 2. SDLC 5.1.0 SASE Framework
- Path: `docs/09-govern/04-Strategic-Updates/SE3.0-SASE-Integration-Plan-APPROVED.md`
- Agentic artifacts (BRS/MRP/VCR) will be used for Vibecode CLI governance

### 3. System Architecture Document
- Path: `docs/02-design/02-System-Architecture/System-Architecture-Document.md`
- 5-layer architecture (Vibecode CLI = Layer 4)

### 4. Product Roadmap
- Path: `docs/00-foundation/04-Roadmap/Product-Roadmap.md`
- Vibecode CLI entries: Q2 2026 ($30K), H2 2026 ($60K)

---

## 📞 STAKEHOLDERS

| Role | Name | Responsibility | Decision Authority |
|------|------|----------------|-------------------|
| **CTO** | - | Strategic approval, architecture review | Final approval for $90K budget |
| **PM/PO** | - | Requirements, roadmap, pilot execution | Day-to-day decisions |
| **Architect** | - | IR schema design, 4-Gate integration | Technical design |
| **Backend Lead** | - | IR Processor, Multi-Provider Gateway | Implementation |
| **Frontend Lead** | - | Vietnamese UI, template visualization | Implementation |
| **DevOps** | - | Ollama infrastructure, Evidence Vault | Infrastructure |

---

## ✅ APPROVAL & NEXT STEPS

### Document Status

**Status**: DRAFT (awaiting CTO approval)
**Review Date**: January 17, 2026 (Friday standup)
**Approval Authority**: CTO

### Approval Checklist

- [ ] **Budget approved**: $90K allocation (Q2 $30K + H2 $60K)
- [ ] **Q2 2026 sprint plan approved**: IR Processor → Templates → 4-Gate
- [ ] **H2 2026 pilot plan approved**: Multi-Provider → Pilot (5 customers)
- [ ] **Team assignment**: 2 Backend + 1 Frontend + PM/PO (starting Q2)
- [ ] **Go/No-Go criteria approved**: Q2 checkpoint + Q4 checkpoint

### Next Actions (After CTO Approval)

1. **Week 6 (Jan 20-24)**: Update Product-Roadmap.md with Vibecode CLI sprints
2. **Q1 2026 (Feb-Mar)**: Prepare detailed sprint plans (Sprint 1-3)
3. **Q2 2026 Start (Apr 1)**: Kickoff Sprint 1 (IR Processor Service)

---

**Document Prepared By**: PM/PO
**Date**: January 17, 2026
**Version**: 1.0.0 (DRAFT)
**Next Review**: CTO Standup (Jan 17, 2026 @ 3pm)

---

*This requirements summary is part of the $90K budget reallocation from OpenCode evaluation abort*
*Reference: OpenCode-Evaluation-Aborted-Jan12-2026 (docs/99-archive/)*
