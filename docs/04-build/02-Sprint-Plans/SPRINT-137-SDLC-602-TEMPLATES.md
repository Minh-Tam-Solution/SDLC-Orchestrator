# Sprint 137: SDLC 6.0.5 Templates & Orchestrator Integration

**Sprint ID**: SPRINT-137
**Duration**: February 8-21, 2026 (2 weeks)
**Theme**: RFC-SDLC-602 Implementation - E2E API Testing Templates
**Priority**: P0 (Blocks March Launch)
**Team**: BFlow Platform Team + SDLC Orchestrator Team
**Framework**: SDLC 6.0.5

---

## 1. Executive Summary

### Context
- **RFC Approved**: RFC-SDLC-602-E2E-API-TESTING (CTO Score: 9.2/10)
- **Case Study**: SOP Generator E2E Testing (58 endpoints, 84.5% pass rate)
- **Gap Identified**: No standardized E2E testing workflow, Stage 03↔05 cross-reference

### Sprint Goal
Implement 5 Framework templates and SDLC Orchestrator integration for E2E API testing workflow.

---

## 2. Sprint Backlog

### Week 1 (Feb 8-14): Framework Templates

#### 2.1 Template 1: E2E API Testing Workflow (P0)
**Location**: `SDLC-Enterprise-Framework/03-Templates-Tools/1-AI-Tools/testing/e2e-api-testing-workflow.md`

**Content Requirements**:
```yaml
Phases:
  Phase 0: API Documentation Check (Stage 03)
    - Verify COMPLETE-API-ENDPOINT-REFERENCE.md exists
    - Locate openapi.json in Stage 03 (SSOT - CTO requirement)
    - Create API reference if missing

  Phase 1: Setup & Authentication (Stage 05)
    - Create SDLC folder structure
    - Locate test credentials
    - Authenticate and save token

  Phase 2: Test Execution
    - Parse OpenAPI specification (link to Stage 03)
    - Generate automated test script
    - Execute all endpoints
    - Capture responses

  Phase 3: Report Generation
    - Generate E2E-API-REPORT-{DATE}.md
    - Include executive summary, detailed results
    - Document failed endpoints with root cause

  Phase 4: Stage 03 Update
    - Update API Reference with findings
    - Add real examples from tests
    - Document validation rules

  Phase 5: Cross-Reference (NEW - CTO requirement)
    - Link Stage 03 → Stage 05 reports
    - Update README.md with links
    - Validate bidirectional traceability

Stage Transition Notes (CTO Condition #2):
  - Stage 03 → 05: API docs MUST exist before testing begins
  - Stage 05 → 03: Test findings update API documentation
  - Circular dependency: Both stages reference each other
```

**Acceptance Criteria**:
- [ ] 6-phase workflow documented
- [ ] Stage transition notes included
- [ ] Compatible with e2e-api-testing skill v1.1.0

---

#### 2.2 Template 2: API Documentation Structure (P0)
**Location**: `SDLC-Enterprise-Framework/03-Templates-Tools/3-Manual-Templates/integration/API-DOCUMENTATION-TEMPLATE.md`

**Content Requirements**:
```markdown
# Complete API Endpoint Reference

## Summary
| Category | Count | Coverage | Test Report Link |
|----------|-------|----------|------------------|

## Endpoints by Category

### 1. Authentication
| # | Method | Endpoint | Auth | Description | Test Status |
|---|--------|----------|------|-------------|-------------|

## Detailed Endpoints

### Endpoint: POST /api/v1/example
- **Description**: ...
- **Authentication**: Required/Optional
- **Request Schema**: {...}
- **Response Schema**: {...}
- **Example Request**: curl command
- **Example Response**: JSON
- **Validation Rules**: enums, patterns, required fields
- **Test Report**: Link to Stage 05 E2E report
- **Last Tested**: Date
```

**Acceptance Criteria**:
- [ ] Summary table with test report links
- [ ] Per-endpoint test status
- [ ] Cross-reference to Stage 05

---

#### 2.3 Template 3: Stage Cross-Reference Matrix (P0)
**Location**: `SDLC-Enterprise-Framework/02-Core-Methodology/Stage-Cross-Reference/STAGE-03-05-CROSS-REFERENCE.md`

**Renamed**: Per CTO Condition #3 (was "Stage 03/05 Cross-Reference Guidelines")

**Content Requirements**:
```yaml
Stage Cross-Reference Matrix:

  Stage 03 → Stage 05 Links:
    docs/03-Integration-APIs/:
      - 02-API-Specifications/
          - COMPLETE-API-ENDPOINT-REFERENCE.md  # Links to test report
          - openapi.json                        # SSOT (single location)
      - README.md                               # Links to both docs

    docs/05-Testing-Quality/:
      - 03-E2E-Testing/
          - reports/E2E-API-REPORT-{DATE}.md    # Links to API ref
          - scripts/test_all_endpoints.py
          - artifacts/                          # Symlink to Stage 03 openapi.json

  SSOT Principle (CTO Condition #5):
    Primary Location: docs/03-Integration-APIs/02-API-Specifications/openapi.json
    Stage 05 Access: Symlink or relative path reference (NOT duplicate)
    Reason: Database is SSOT, files follow same principle

  Cross-Reference Requirements:
    1. API Reference MUST link to E2E test report
    2. Test report MUST link to API Reference
    3. Both MUST be linked from README.md
    4. OpenAPI spec stored ONCE in Stage 03

  Future Extensions:
    - Stage 01 ↔ 02 (Requirements → Design)
    - Stage 02 ↔ 04 (Design → Implementation)
    - Stage 04 ↔ 05 (Implementation → Testing)
```

**Acceptance Criteria**:
- [ ] Renamed to "Matrix" (future-proof)
- [ ] SSOT principle documented
- [ ] No duplicate openapi.json

---

#### 2.4 Template 4: Security Testing Checklist (P0)
**Location**: `SDLC-Enterprise-Framework/03-Templates-Tools/1-AI-Tools/testing/security-testing-checklist.md`

**Content Requirements** (CTO Condition #1 - ALL 10 items):
```yaml
OWASP API Security Top 10 (2023) Checklist:

  1. API1:2023 - Broken Object Level Authorization (BOLA/IDOR):
     Test: Change user IDs in requests
     Expected: 403 Forbidden for other users' resources
     Tools: Burp Suite, custom scripts

  2. API2:2023 - Broken Authentication:
     Test: JWT weakness, token expiration, logout
     Expected: Proper token invalidation
     Tools: jwt_tool, Burp JWT plugin

  3. API3:2023 - Broken Object Property Level Authorization:
     Test: Access restricted properties
     Expected: Hidden fields not exposed
     Tools: Burp, response comparison

  4. API4:2023 - Unrestricted Resource Consumption:
     Test: Rate limiting, large payloads
     Expected: 429 Too Many Requests
     Tools: Locust, custom scripts

  5. API5:2023 - Broken Function Level Authorization:
     Test: Access admin endpoints as regular user
     Expected: 403 Forbidden
     Tools: Burp, permission matrix

  6. API6:2023 - Unrestricted Access to Sensitive Business Flows:
     Test: Abuse business logic (mass creation, enumeration)
     Expected: Rate limits, CAPTCHA triggers
     Tools: Custom scripts

  7. API7:2023 - Server-Side Request Forgery (SSRF):
     Test: URL parameters pointing to internal services
     Expected: Block internal URLs, validate schemes
     Tools: Burp Collaborator, ffuf

  8. API8:2023 - Security Misconfiguration:
     Test: Debug mode, default credentials, CORS
     Expected: Proper security headers, no debug info
     Tools: SecurityHeaders.com, Burp

  9. API9:2023 - Improper Inventory Management:
     Test: Old API versions, undocumented endpoints
     Expected: Only documented endpoints accessible
     Tools: Swagger diff, endpoint enumeration

  10. API10:2023 - Unsafe Consumption of APIs:
      Test: Third-party API responses (injection, validation)
      Expected: Validate all external inputs
      Tools: Custom fuzzing, mock servers

Security Testing Modes (from e2e-api-testing skill):
  - IDOR Testing (API1)
  - Authentication Testing (API2)
  - Injection Testing - SQL, Command (API7)
  - GraphQL-specific Testing
  - 403/401 Bypass Attempts (API5)
```

**Acceptance Criteria**:
- [ ] ALL 10 OWASP items documented
- [ ] Each item has: Test, Expected, Tools
- [ ] Integrated with e2e-api-testing skill modes

---

#### 2.5 Template 5: Testing Artifacts Structure (P0)
**Location**: `SDLC-Enterprise-Framework/02-Core-Methodology/Folder-Structure/TESTING-ARTIFACTS-STRUCTURE.md`

**Content Requirements**:
```
<PROJECT_ROOT>/docs/
├── 03-Integration-APIs/
│   └── 02-API-Specifications/
│       ├── COMPLETE-API-ENDPOINT-REFERENCE.md  # Stage 03 SSOT
│       ├── openapi.json                        # Single source
│       └── README.md                           # Links to Stage 05

└── 05-Testing-Quality/
    ├── 03-E2E-Testing/
    │   ├── reports/                    # Test reports
    │   │   └── E2E-API-REPORT-{DATE}.md
    │   ├── scripts/                    # Test scripts
    │   │   └── test_all_endpoints.py
    │   ├── artifacts/                  # Runtime artifacts
    │   │   ├── auth_token.txt          # Ephemeral (gitignored)
    │   │   └── test_results_{timestamp}.json
    │   ├── changelogs/
    │   │   └── CHANGELOG-{DATE}.md
    │   └── README.md                   # Links to Stage 03
    │
    ├── 04-Integration-Testing/
    │   ├── reports/
    │   └── scripts/
    │
    └── 05-Security-Testing/            # NEW
        ├── owasp-top10/
        │   └── SECURITY-REPORT-{DATE}.md
        └── scripts/

Gitignore Patterns:
  - docs/05-Testing-Quality/*/artifacts/auth_token.txt
  - docs/05-Testing-Quality/*/artifacts/*.json
  - !docs/05-Testing-Quality/*/artifacts/README.md
```

**Acceptance Criteria**:
- [ ] Stage 03 as SSOT for openapi.json
- [ ] Security testing folder added
- [ ] Gitignore patterns documented

---

### Week 2 (Feb 15-21): SDLC Orchestrator Integration

#### 2.6 Evidence Schema Update (P0 - CTO Condition #6)
**Location**: Backend SPEC-0016 compliance

**New Artifact Types**:
```python
class EvidenceArtifactType(str, Enum):
    # Existing types...

    # NEW - RFC-SDLC-602
    E2E_TESTING_REPORT = "e2e_testing_report"
    API_DOCUMENTATION_REFERENCE = "api_documentation_reference"
    SECURITY_TESTING_RESULTS = "security_testing_results"
    STAGE_CROSS_REFERENCE = "stage_cross_reference"
```

**New Validation Rules**:
```python
VALIDATION_RULES = {
    "e2e_testing_report": {
        "required_fields": ["total_endpoints", "pass_rate", "api_reference_link"],
        "file_pattern": r"E2E-API-REPORT-\d{4}-\d{2}-\d{2}\.md",
        "stage": "05-TESTING"
    },
    "stage_cross_reference": {
        "required_links": ["stage_03_path", "stage_05_path"],
        "bidirectional": True
    }
}
```

**Files to Modify**:
- `backend/app/models/evidence.py` - Add new artifact types
- `backend/app/services/evidence_service.py` - Add validation rules
- `backend/app/api/v1/endpoints/evidence.py` - Update endpoints

**Acceptance Criteria**:
- [ ] 4 new artifact types registered
- [ ] Validation rules implemented
- [ ] Stage cross-reference validation working

---

#### 2.7 OPA Policy Updates (P0 - CTO Condition #4)
**Location**: `backend/opa/policies/`

**New Policies**:
```rego
# e2e_testing_compliance.rego
package sdlc.e2e_testing

# Require E2E report before Stage 05 → 06 transition
default allow_stage_transition = false

allow_stage_transition {
    input.from_stage == "05-TESTING"
    input.to_stage == "06-DEPLOY"
    has_e2e_report
    e2e_pass_rate >= 80
}

has_e2e_report {
    some report in input.evidence
    report.artifact_type == "e2e_testing_report"
}

e2e_pass_rate = rate {
    some report in input.evidence
    report.artifact_type == "e2e_testing_report"
    rate := report.metadata.pass_rate
}

# stage_cross_reference.rego
package sdlc.cross_reference

# Require Stage 03 ↔ 05 bidirectional links
default cross_reference_valid = false

cross_reference_valid {
    has_stage_03_link
    has_stage_05_link
}
```

**Files to Create**:
- `backend/opa/policies/e2e_testing_compliance.rego`
- `backend/opa/policies/stage_cross_reference.rego`

**Acceptance Criteria**:
- [ ] E2E report required for Stage 05 → 06
- [ ] Cross-reference validation policy
- [ ] Pass rate threshold configurable

---

#### 2.8 sdlcctl CLI Updates (P0 - CTO Condition #4)
**Location**: `backend/sdlcctl/`

**New Commands**:
```bash
# Validate E2E testing artifacts
sdlcctl validate-e2e \
  --project-path /path/to/project \
  --min-pass-rate 80

# Validate stage cross-references
sdlcctl validate-cross-reference \
  --stage-03 docs/03-Integration-APIs \
  --stage-05 docs/05-Testing-Quality

# Generate E2E report from test results
sdlcctl generate-e2e-report \
  --results test_results.json \
  --output docs/05-Testing-Quality/03-E2E-Testing/reports/
```

**Files to Modify**:
- `backend/sdlcctl/sdlcctl/commands/validate.py` - Add e2e subcommand
- `backend/sdlcctl/sdlcctl/commands/generate.py` - Add report generation

**Acceptance Criteria**:
- [ ] validate-e2e command working
- [ ] validate-cross-reference command working
- [ ] generate-e2e-report command working

---

## 3. Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| RFC-SDLC-602 Approval | External | ✅ Approved (Feb 2, 2026) |
| SOP Generator Case Study | Reference | ✅ Complete |
| e2e-api-testing skill v1.1.0 | Tool | ✅ Available |
| Sprint 136 SSOT Implementation | Internal | ✅ Complete |

---

## 4. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Template adoption friction | Medium | High | Include real examples from SOP Generator |
| Evidence schema migration | Low | Medium | Backwards-compatible changes only |
| OPA policy conflicts | Low | High | Test in staging before production |

---

## 5. Success Criteria

### Framework Templates (Week 1)
- [ ] All 5 templates created and reviewed
- [ ] OWASP Top 10 complete (10/10 items)
- [ ] SSOT principle enforced (no duplicate files)
- [ ] Stage transition notes included

### Orchestrator Integration (Week 2)
- [ ] 4 new evidence artifact types registered
- [ ] OPA policies deployed to staging
- [ ] sdlcctl commands documented
- [ ] E2E validation passing on SOP Generator

### Overall Sprint 137
- [ ] All CTO conditions met (6/6)
- [ ] Ready for Sprint 138 validation

---

## 6. Definition of Done

1. ✅ All 5 templates committed to SDLC-Enterprise-Framework
2. ✅ Evidence schema updated in backend
3. ✅ OPA policies deployed
4. ✅ sdlcctl commands implemented
5. ✅ Documentation updated
6. ✅ Tested on SOP Generator (pilot project)
7. ✅ CTO review passed

---

**Sprint Status**: ⏳ NOT STARTED
**Planned Start**: February 8, 2026
**Target Completion**: February 21, 2026
