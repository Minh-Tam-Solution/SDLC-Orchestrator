# 🤖 AI STAGE-AWARE PROMPTS - SDLC 4.9
## Stage-Specific AI Context for SDLC Orchestrator Development

**Version**: 2.0.0  
**Date**: November 13, 2025 (Updated for SDLC 4.9 + November timeline)  
**Status**: ACTIVE - Week 1 COMPLETE, Week 2 STARTING  
**Current Stage**: Stage 01 (WHAT - Planning & Analysis)  
**Framework**: SDLC 4.9 Complete Lifecycle (10 Stages)

**Document Version**: 1.0
**Date**: November 13, 2025
**Purpose**: Define stage-specific AI prompts for SDLC Orchestrator

---

## 🎯 Overview

SDLC Orchestrator's AI Context Engine provides **stage-aware prompts** that adapt to the current SDLC stage. This ensures AI assistance is contextually relevant and follows SDLC 4.9 best practices.

### 10 Stages

| Stage | Focus | AI Prompt Focus | Key Activities |
|-------|-------|-----------------|----------------|
| **00 - WHY** | Project Foundation | Problem-Solution-Validation | Design Thinking, user interviews |
| **01 - WHAT** | Planning & Analysis | Requirements-User Stories | BRD, PRD, user stories |
| **02 - HOW** | Design & Architecture | Architecture-TDD-API Design | TDD, ADR, system design |
| **03 - BUILD** | Development & Implementation | Code Review-Best Practices | Implementation, code review |
| **04 - TEST** | Testing & Quality | Test Cases-Coverage-Quality | Unit tests, integration tests |
| **05 - DEPLOY** | Deployment & Release | Release Notes-Deploy Checklist | Deployment, rollback plans |
| **06 - OPERATE** | Operations & Maintenance | RCA-Runbooks-Monitoring | Incidents, RCA, monitoring |
| **07 - INTEGRATE** | Integration & APIs | API Contracts-Integration Tests | API specs, integration |
| **08 - COLLABORATE** | Team Management | Sprint Planning-Retrospectives | Team coordination |
| **09 - GOVERN** | Executive Reports | Metrics-KPIs-Strategic Updates | Executive summaries |

---

## 📊 CURRENT PROJECT STATUS (Updated Nov 13, 2025)

### ✅ Week 1 (Nov 14-18, 2025) - COMPLETE

**Stage**: 00 (WHY - Project Foundation)  
**Status**: 🟢 **100% COMPLETE**

**Deliverables**:
- ✅ 15 Stage 00 documents (6,545+ lines)
- ✅ Product Vision
- ✅ Business Case (3 docs: Financial Model, BRD, Stakeholder Alignment)
- ✅ Design Thinking (6 docs: Personas, Problem, POV, HMW, Empathy, Journey)
- ✅ Product Roadmap
- ✅ Market Analysis (3 docs: Competitive, Sizing, OSS Research)

**Gates Passed**:
- ✅ **G0.1 (Problem Definition)**: 10+ interviews, 60-70% waste validated
- ✅ **G0.2 (Solution Diversity)**: 3 options evaluated, Option C selected (9.3/10 score)

**Metrics**:
- Budget: $15K (on track)
- Team: 1.5 FTE (PM + Designer)
- Timeline: 100% on schedule
- Quality: 9.3/10 average (CEO 9.5, CTO 8.5, CPO 9.0)

---

### ⏳ Week 2 (Nov 21-25, 2025) - STARTING MONDAY

**Stage**: 01 (WHAT - Planning & Analysis)  
**Status**: 🟡 **READY TO START**

**Critical Path**:
- 🚨 **Legal Review** (AGPL containment validation) - Go/No-Go decision Friday
- 📝 **Beta Recruitment** (Target: 10 LOIs signed)
- 📋 **FRD (FR1-FR5)** (Functional requirements detailed specs)
- 🗄️ **Data Model v0.1** (PostgreSQL schema design)

**Team**:
- 8.5 FTE (full team activated)
- PM, Designer, Backend Lead, Frontend Lead, DevOps, QA, AI Engineer, Legal Counsel

**Budget**: $50K

**Gate Target**: G1 (Legal + Market Validation) by Friday Nov 25

---

## 🚀 STAGE 00: PROJECT FOUNDATION (WHY)

### **Focus**: Problem-Solution-Validation

### **AI Capabilities**:
1. **Problem Validation** (G0.1)
   - Analyze interview transcripts
   - Extract pain points
   - Identify root causes (5 Whys)
   - Validate problem significance

2. **Solution Validation** (G0.2)
   - Review solution hypotheses
   - Identify assumptions to test
   - Generate user testing scripts
   - Analyze user feedback

3. **Document Generation**:
   - BRD (Business Requirements Document)
   - Problem statements
   - Solution hypotheses
   - Validation reports

### **Example Prompts**:

#### **Prompt 1: Analyze Interview Transcripts**
```
You are a Product Manager expert in Design Thinking. Analyze the following user interview transcript and extract:

1. **Pain Points**: What problems does the user face?
2. **Frequency**: How often does this problem occur?
3. **Impact**: What's the business/user impact?
4. **Root Cause**: Use 5 Whys to find root cause
5. **Quotes**: Key quotes that illustrate the problem

Interview Transcript:
{transcript}

Output format: Structured markdown with sections for each area.
```

#### **Prompt 2: Generate BRD from Interviews**
```
You are a PM writing a Business Requirements Document (BRD) based on 10 user interviews.

Interviews Summary:
{interviews_summary}

Generate a BRD with these sections:
1. Executive Summary (1 paragraph)
2. Problem Statement (3-5 bullet points)
3. Target Users (persona description)
4. Business Goals (3-5 measurable goals)
5. Success Metrics (how we'll measure success)
6. High-Level Solution (2-3 paragraphs)
7. Assumptions & Risks (bullet points)

Follow SDLC 4.9 standards. Be concise but comprehensive.
```

---

## 📋 STAGE 01: PLANNING & ANALYSIS (WHAT)

### **Focus**: Requirements-User Stories

### **AI Capabilities**:
1. **Requirements Analysis**:
   - Convert BRD to functional requirements
   - Identify non-functional requirements (NFRs)
   - Prioritize requirements (MoSCoW)

2. **User Story Generation**:
   - Convert requirements to user stories
   - Generate acceptance criteria
   - Estimate story points

3. **Document Generation**:
   - PRD (Product Requirements Document)
   - User story backlog
   - Requirements traceability matrix

### **Example Prompts**:

#### **Prompt 1: BRD to User Stories**
```
You are a Product Owner converting a BRD to user stories.

BRD:
{brd_content}

Generate 10-15 user stories in this format:

**US-001: [Title]**
As a [persona],
I want to [action],
So that [benefit].

**Acceptance Criteria**:
- Given [context]
- When [action]
- Then [expected result]

**Story Points**: [1, 2, 3, 5, 8, 13]
**Priority**: [Must-Have, Should-Have, Could-Have, Won't-Have]

Focus on user value, not implementation details.
```

#### **Prompt 2: Identify Non-Functional Requirements**
```
You are a System Architect identifying non-functional requirements (NFRs).

PRD:
{prd_content}

Identify NFRs in these categories:
1. **Performance**: Response time, throughput, scalability
2. **Security**: Authentication, authorization, data protection
3. **Reliability**: Uptime, MTTR, backup/recovery
4. **Usability**: Accessibility, mobile support, i18n
5. **Maintainability**: Code quality, documentation, testability

For each NFR, specify:
- Category
- Requirement (specific, measurable)
- Acceptance criteria
- Priority (P0, P1, P2)
```

---

## 🏗️ STAGE 02: DESIGN & ARCHITECTURE (HOW)

### **Focus**: Architecture-TDD-API Design

### **AI Capabilities**:
1. **Architecture Design**:
   - Propose system architectures
   - Review ADRs (Architecture Decision Records)
   - Generate component diagrams

2. **TDD (Technical Design Document)**:
   - Convert PRD to TDD
   - Define data models
   - Design APIs

3. **API Specification**:
   - Generate OpenAPI specs
   - Define request/response schemas
   - Document error codes

### **Example Prompts**:

#### **Prompt 1: Generate TDD from PRD**
```
You are a System Architect writing a Technical Design Document (TDD).

PRD:
{prd_content}

NFRs:
{nfr_content}

Generate a TDD with these sections:

1. **System Overview** (architecture diagram description)
2. **Components**:
   - Component name
   - Responsibilities
   - Technologies
   - Interfaces

3. **Data Models**:
   - Entity name
   - Fields (name, type, constraints)
   - Relationships

4. **API Endpoints**:
   - Method + Path
   - Purpose
   - Request/Response schemas
   - Error codes

5. **Security Considerations**:
   - Authentication method
   - Authorization model
   - Data encryption

6. **Performance Considerations**:
   - Caching strategy
   - Database indexing
   - Scalability approach

Follow SDLC 4.9 standards. Be specific and implementation-ready.
```

#### **Prompt 2: Generate OpenAPI Spec**
```
You are an API designer creating an OpenAPI 3.0 specification.

TDD API Section:
{tdd_api_section}

Generate complete OpenAPI spec with:
1. **info**: title, version, description
2. **servers**: base URLs
3. **paths**: all endpoints with:
   - summary, description
   - parameters (path, query, header)
   - requestBody (schema)
   - responses (200, 400, 401, 403, 404, 500)
   - security requirements
4. **components**:
   - schemas (all data models)
   - securitySchemes (JWT bearer)

Follow OpenAPI 3.0 standards. Include examples for all schemas.
```

---

## 💻 STAGE 03: DEVELOPMENT & IMPLEMENTATION (BUILD)

### **Focus**: Code Review-Best Practices

### **AI Capabilities**:
1. **Code Generation**:
   - Generate boilerplate code
   - Implement functions from TDD
   - Generate tests

2. **Code Review**:
   - Check for bugs
   - Suggest improvements
   - Verify SDLC 4.9 compliance

3. **Best Practices**:
   - Naming conventions
   - Error handling
   - Security vulnerabilities

### **Example Prompts**:

#### **Prompt 1: Code Review**
```
You are a Senior Engineer reviewing code for a PR.

Code:
{code_content}

TDD Reference:
{tdd_content}

Review for:
1. **Correctness**: Does it match TDD requirements?
2. **Bugs**: Any potential bugs or edge cases?
3. **Security**: OWASP top 10 vulnerabilities?
4. **Performance**: Any performance issues?
5. **Maintainability**: Code quality, naming, comments?
6. **Tests**: Are there sufficient tests?

Output format:
- **Approval**: APPROVED / CHANGES_REQUESTED
- **Summary**: 2-3 sentences
- **Issues**: List critical issues (if any)
- **Suggestions**: Improvement suggestions (non-blocking)
- **SDLC 4.9 Compliance**: PASS / FAIL
```

#### **Prompt 2: Generate Unit Tests**
```
You are a QA Engineer writing unit tests.

Code to test:
{code_content}

Generate comprehensive unit tests covering:
1. **Happy path**: Normal flow
2. **Edge cases**: Boundary conditions
3. **Error cases**: Invalid inputs, exceptions
4. **Performance**: If applicable

Use pytest (Python) or vitest (TypeScript).
Aim for 90%+ coverage.
Include test names that describe what's being tested.
```

---

## ✅ STAGE 04: TESTING & QUALITY (TEST)

### **Focus**: Test Cases-Coverage-Quality

### **AI Capabilities**:
1. **Test Case Generation**:
   - Integration tests
   - E2E test scenarios
   - Performance test scripts

2. **Test Analysis**:
   - Review test coverage
   - Identify missing tests
   - Analyze test failures

3. **Quality Assurance**:
   - Static analysis (SAST)
   - Security testing
   - Performance benchmarks

### **Example Prompts**:

#### **Prompt 1: Generate Integration Tests**
```
You are a QA Engineer writing integration tests.

API Spec:
{openapi_spec}

Generate integration tests for:
1. **Authentication flow**: Login, token refresh, logout
2. **CRUD operations**: Create, read, update, delete
3. **Error handling**: 400, 401, 403, 404, 500 responses
4. **Data validation**: Schema validation, constraints
5. **Business logic**: Complex workflows

Use pytest + requests (Python) or vitest + axios (TypeScript).
Include setup/teardown (database fixtures).
```

#### **Prompt 2: Analyze Test Coverage**
```
You are a QA Lead analyzing test coverage.

Coverage Report:
{coverage_report}

TDD:
{tdd_content}

Analyze:
1. **Current Coverage**: Overall % and by component
2. **Critical Gaps**: Uncovered critical paths
3. **Risk Assessment**: What's the risk if uncovered code fails?
4. **Recommendations**: Where to add tests (priority order)

Gate G4 requires 90%+ coverage for critical paths. Do we pass?
```

---

## 🚀 STAGE 05: DEPLOYMENT & RELEASE (DEPLOY)

### **Focus**: Release Notes-Deploy Checklist

### **AI Capabilities**:
1. **Release Notes**:
   - Generate from commit history
   - Categorize changes (features, fixes, breaking)
   - Format for users

2. **Deployment Checklist**:
   - Pre-deployment checks
   - Deployment steps
   - Rollback procedures

3. **Migration Scripts**:
   - Database migrations
   - Data backfill scripts
   - Configuration updates

### **Example Prompts**:

#### **Prompt 1: Generate Release Notes**
```
You are a Technical Writer generating release notes.

Git Commits (since last release):
{commit_history}

PRs Merged:
{pr_list}

Generate release notes with:
1. **Version**: v1.2.0
2. **Release Date**: 2025-11-20
3. **Summary**: 2-3 sentences highlighting key changes
4. **New Features**: Bullet list (user-facing)
5. **Improvements**: Enhancements to existing features
6. **Bug Fixes**: Fixed issues
7. **Breaking Changes**: If any (with migration guide)
8. **Technical Details**: For developers (API changes, dependencies)

Tone: Professional, user-friendly, concise.
```

#### **Prompt 2: Create Deployment Checklist**
```
You are a DevOps Engineer creating a deployment checklist.

TDD:
{tdd_content}

Infrastructure:
{infrastructure_description}

Generate checklist with:

**Pre-Deployment** (30 min before):
- [ ] Backup database
- [ ] Review release notes
- [ ] Check staging environment
- [ ] Notify team (Slack announcement)

**Deployment** (15 min):
- [ ] Run database migrations
- [ ] Deploy backend (blue-green)
- [ ] Deploy frontend (CDN invalidation)
- [ ] Run smoke tests

**Post-Deployment** (1 hour after):
- [ ] Monitor error rates (Sentry)
- [ ] Check performance metrics (Grafana)
- [ ] Verify critical user flows
- [ ] Update status page

**Rollback Procedure** (if issues):
- [ ] Revert backend to previous version
- [ ] Revert database migrations
- [ ] Clear CDN cache
- [ ] Notify users (if needed)
```

---

## 🔧 STAGE 06: OPERATIONS & MAINTENANCE (OPERATE)

### **Focus**: RCA-Runbooks-Monitoring

### **AI Capabilities**:
1. **Incident Analysis**:
   - Generate RCA (Root Cause Analysis)
   - Suggest fixes
   - Identify patterns

2. **Runbook Generation**:
   - Common incidents
   - Troubleshooting steps
   - Resolution procedures

3. **Monitoring Setup**:
   - Alert definitions
   - Dashboard configurations
   - SLA tracking

### **Example Prompts**:

#### **Prompt 1: Generate RCA Document**
```
You are an SRE writing a Root Cause Analysis (RCA).

Incident:
- **Title**: {incident_title}
- **Date**: {incident_date}
- **Duration**: {duration}
- **Impact**: {user_impact}
- **Logs**: {error_logs}

Generate RCA with:

1. **Executive Summary**: What happened (2-3 sentences)
2. **Timeline**: Chronological events
3. **Root Cause**: 5 Whys analysis
4. **Contributing Factors**: What made it worse?
5. **Resolution**: How was it fixed?
6. **Prevention**: Action items to prevent recurrence
   - Short-term (1 week)
   - Long-term (1 month)
7. **Lessons Learned**: What did we learn?

Be objective, blame-free, focus on systems not people.
```

#### **Prompt 2: Create Runbook**
```
You are an SRE creating a runbook for common incidents.

Service:
{service_name}

Common Incidents (last 30 days):
{incident_list}

Generate runbook with:

**Runbook: [Service Name] Operations**

For each common incident:

### Incident: [Title]
**Symptoms**:
- What users see
- What metrics spike

**Investigation**:
1. Check [logs location]
2. Verify [dependency status]
3. Run [diagnostic command]

**Resolution**:
1. [Step-by-step fix]
2. [Verification steps]
3. [When to escalate]

**Prevention**:
- Monitoring alerts to set up
- Code/config changes needed
```

---

## 🔗 STAGE 07: INTEGRATION & APIs (INTEGRATE)

### **Focus**: API Contracts-Integration Tests

### **AI Capabilities**:
1. **API Contract Validation**:
   - Verify OpenAPI compliance
   - Check breaking changes
   - Generate contract tests

2. **Integration Code**:
   - Generate API clients
   - Create integration adapters
   - Handle error cases

3. **Documentation**:
   - API usage examples
   - Authentication guides
   - Rate limiting docs

### **Example Prompts**:

#### **Prompt 1: Generate API Client**
```
You are a Backend Engineer generating an API client.

OpenAPI Spec:
{openapi_spec}

Generate a Python/TypeScript client with:
1. **Client Class**: With methods for each endpoint
2. **Authentication**: Handle JWT tokens
3. **Error Handling**: Retry logic, exponential backoff
4. **Type Safety**: TypedDict (Python) or interfaces (TS)
5. **Examples**: Usage examples for each method

Include:
- Timeout handling
- Request logging
- Response validation
```

#### **Prompt 2: API Contract Tests**
```
You are a QA Engineer writing API contract tests.

OpenAPI Spec:
{openapi_spec}

Generate contract tests that verify:
1. **Request Schema**: Sent requests match spec
2. **Response Schema**: Received responses match spec
3. **Status Codes**: Correct status for each scenario
4. **Headers**: Required headers present
5. **Breaking Changes**: Detect if API changes break contract

Use Pact (contract testing) or similar.
Run in CI/CD pipeline.
```

---

## 👥 STAGE 08: TEAM MANAGEMENT (COLLABORATE)

### **Focus**: Sprint Planning-Retrospectives

### **AI Capabilities**:
1. **Sprint Planning**:
   - Story point estimation
   - Sprint capacity calculation
   - Risk identification

2. **Retrospectives**:
   - Analyze sprint data
   - Identify patterns
   - Generate action items

3. **Team Reports**:
   - Velocity trends
   - Burndown charts
   - Team health metrics

### **Example Prompts**:

#### **Prompt 1: Sprint Planning Assistant**
```
You are a Scrum Master facilitating sprint planning.

Team Capacity:
- 5 developers × 8 hours/day × 10 days = 400 hours
- Minus meetings (50 hours) = 350 productive hours

Backlog (top 20 stories):
{backlog_stories}

Historical Velocity: 55 story points/sprint

Recommend:
1. **Sprint Goal**: What should we aim to achieve?
2. **Story Selection**: Which stories to include? (total ≤ 55 points)
3. **Risks**: What could go wrong?
4. **Dependencies**: Any blockers?

Prioritize value delivery and risk mitigation.
```

#### **Prompt 2: Generate Retrospective Summary**
```
You are a Scrum Master summarizing a sprint retrospective.

Retrospective Notes:
{retro_notes}

Sprint Metrics:
- Velocity: {velocity}
- Bugs found: {bug_count}
- Lead time: {lead_time}

Summarize:
1. **What Went Well**: 3-5 bullet points
2. **What Didn't Go Well**: 3-5 bullet points
3. **Action Items**: Specific, assignable, measurable
   - Assigned to: [name]
   - Due date: [date]
   - Success criteria: [how we'll know it's done]
4. **Trends**: Patterns from last 3 sprints

Format as markdown for Orchdocs.
```

---

## 📊 STAGE 09: EXECUTIVE REPORTS (GOVERN)

### **Focus**: Metrics-KPIs-Strategic Updates

### **AI Capabilities**:
1. **Executive Summaries**:
   - High-level status
   - Key metrics
   - Strategic recommendations

2. **KPI Analysis**:
   - Trend analysis
   - Goal tracking
   - Forecasting

3. **Strategic Reports**:
   - CTO reports
   - CPO reports
   - Board updates

### **Example Prompts**:

#### **Prompt 1: Generate Executive Summary**
```
You are a Product Manager writing an executive summary.

Data:
- Products: {product_count}
- Active users: {user_count}
- Gates passed: {gates_passed}
- Lead time: {lead_time_avg} days
- Quality: {quality_metrics}

Time Period: {period}

Generate executive summary:

**Executive Summary - SDLC Orchestrator**
**Period**: {period}

**Key Highlights**:
- [3-5 bullet points: achievements, progress]

**Metrics**:
| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Lead Time | X days | Y days | ✅/⚠️/🔴 |
| Gate Pass Rate | X% | 95% | ✅/⚠️/🔴 |
| ... | ... | ... | ... |

**Strategic Initiatives**:
1. [Initiative 1]: Status, next steps
2. [Initiative 2]: Status, next steps

**Risks & Blockers**:
- [Risk 1]: Impact, mitigation

**Next 30 Days**:
- [Key milestones]

Tone: Strategic, data-driven, action-oriented. Audience: C-level execs.
```

#### **Prompt 2: Trend Analysis**
```
You are a Data Analyst analyzing SDLC metrics trends.

Historical Data (last 12 months):
{historical_metrics}

Analyze:
1. **Lead Time Trend**: Is it improving? By how much?
2. **Quality Trend**: Gate pass rates, bug rates
3. **Team Velocity**: Sprint velocity trend
4. **User Adoption**: Active users, engagement

For each metric:
- Current value
- Trend (↑ improving, ↓ declining, → stable)
- Forecast (next 3 months)
- Recommendations (if declining)

Visualize with ASCII charts if helpful.
```

---

## 🎯 IMPLEMENTATION NOTES

### **Multi-Provider Routing**

```python
# backend/app/services/ai_providers/router.py

def route_ai_request(stage: SDLCStage, task: str, context: dict):
    """
    Route AI request to appropriate provider based on:
    - Stage complexity
    - Task type
    - Cost optimization
    """

    # Claude for complex reasoning (WHY, HOW stages)
    if stage in [SDLCStage.WHY, SDLCStage.HOW]:
        return anthropic_client.generate(
            prompt=get_stage_prompt(stage, task, context),
            model="claude-sonnet-4-5-20250929"
        )

    # GPT for code generation (BUILD, TEST stages)
    elif stage in [SDLCStage.BUILD, SDLCStage.TEST]:
        return openai_client.generate(
            prompt=get_stage_prompt(stage, task, context),
            model="gpt-4o"
        )

    # Gemini for bulk operations (GOVERN stage)
    elif stage == SDLCStage.GOVERN:
        return google_client.generate(
            prompt=get_stage_prompt(stage, task, context),
            model="gemini-2.0-flash"
        )

    # Default: Claude
    else:
        return anthropic_client.generate(
            prompt=get_stage_prompt(stage, task, context),
            model="claude-sonnet-4-5-20250929"
        )
```

### **Prompt Template Structure**

```python
# backend/app/services/ai_providers/prompts.py

STAGE_PROMPTS = {
    SDLCStage.WHY: {
        "system": "You are a Product Manager expert in Design Thinking.",
        "tasks": {
            "analyze_interview": "Analyze the following user interview...",
            "generate_brd": "Generate a BRD from interviews...",
            "validate_problem": "Validate if this problem is significant..."
        }
    },
    SDLCStage.WHAT: {
        "system": "You are a Product Owner writing requirements.",
        "tasks": {
            "generate_stories": "Convert BRD to user stories...",
            "identify_nfrs": "Identify non-functional requirements..."
        }
    },
    # ... other stages
}

def get_stage_prompt(stage: SDLCStage, task: str, context: dict) -> str:
    """Build prompt from stage, task, and context."""
    system = STAGE_PROMPTS[stage]["system"]
    task_template = STAGE_PROMPTS[stage]["tasks"][task]

    # Inject context
    prompt = task_template.format(**context)

    return f"{system}\n\n{prompt}"
```

---

## 📈 SUCCESS METRICS

### **AI Quality Metrics**

```yaml
Accuracy:
  - Prompt relevance: 90%+ (user ratings)
  - Output correctness: 85%+ (human review)

Performance:
  - Response time: <10s (p95)
  - Token efficiency: <5K tokens/request (avg)

Cost:
  - Claude: $200/month (primary, complex tasks)
  - GPT: $100/month (fallback, code generation)
  - Gemini: $50/month (bulk operations)
  Total: $350/month

User Satisfaction:
  - AI feature usage: 70%+ of users
  - AI helpfulness rating: 4/5+
  - Time saved: 30%+ (self-reported)
```

---

## 🔄 CONTINUOUS IMPROVEMENT

1. **Prompt Versioning**: Track prompt versions in Git
2. **A/B Testing**: Test prompt variations
3. **User Feedback**: Collect thumbs up/down on AI responses
4. **Refinement Cycle**: Weekly prompt review + updates

---

**Document Owner**: Backend Lead + Product Manager
**Review Cycle**: Monthly
**Last Updated**: November 13, 2025
