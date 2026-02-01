# Technical Specification Template (SDLC 6.0.0)

**File naming**: `SPEC-XXXX-[kebab-case-title].md`
**Location**: `docs/02-design/14-Technical-Specs/`

---

## YAML Frontmatter (Required - Section 8 Standard)

```yaml
---
# Required Fields (9/9) - SDLC 6.0.0 Section 8
spec_id: SPEC-XXXX
title: "[Specification Title]"
version: 1.0.0
status: DRAFT  # DRAFT | REVIEW | CTO_APPROVED | ACTIVE | DEPRECATED
stage: 02-design
tier: PROFESSIONAL  # LITE | STANDARD | PROFESSIONAL | ENTERPRISE
author: "[Name]"
created: YYYY-MM-DD
updated: YYYY-MM-DD

# Context Management (AGENTS.md 4-Zone Model)
context_zone: Semi-Static  # Specs typically Semi-Static (updated per sprint)
update_frequency: Per Sprint  # Daily | Weekly | Per Sprint | Quarterly

# Optional Fields
sprint: XXX
priority: P1  # P0 (Critical) | P1 (High) | P2 (Medium)
dependencies:
  - SPEC-YYYY (Prerequisite spec)
related_adrs:
  - ADR-XXX (Related architecture decision)
related_sprints:
  - SPRINT-XXX
supersedes: null  # SPEC-YYYY if replacing
tags:
  - architecture
  - backend
  - frontend
---
```

---

## Technical Spec Structure (BDD Format)

### 1. Overview

**Purpose**: [What problem does this solve?]

**Scope**: [What's included/excluded?]

**Target Audience**: [Who will use this?]

---

### 2. Functional Requirements (BDD Format)

#### FR-1: [Feature Name]
**Priority**: [P0 | P1 | P2]
**Tier**: [LITE | STANDARD | PROFESSIONAL | ENTERPRISE]

```gherkin
Feature: [Feature name]
  As a [user type]
  I want to [action]
  So that [benefit]

  Scenario: [Happy path]
    Given [precondition]
    And [additional context]
    When [action]
    And [additional action]
    Then [expected result]
    And [additional verification]
```

**Acceptance Criteria**:
- [ ] [Criterion 1]
- [ ] [Criterion 2]

**Vietnamese Business Logic** (if applicable):
```gherkin
  Scenario: Calculate BHXH contribution (Vietnamese social insurance)
    Given an employee with salary 30,000,000 VND
    And BHXH contribution rate is 21.5% (employer) + 10.5% (employee)
    When calculating monthly BHXH
    Then employer contribution should be 6,450,000 VND
    And employee contribution should be 3,150,000 VND
    And total BHXH should be 9,600,000 VND
```

---

#### FR-2: [Feature Name]
**Priority**: [P0 | P1 | P2]
**Tier**: [LITE | STANDARD | PROFESSIONAL | ENTERPRISE]

```gherkin
Feature: [Feature name]
  As a [user type]
  I want to [action]
  So that [benefit]

  Scenario: [Happy path]
    Given [precondition]
    When [action]
    Then [expected result]
```

**Acceptance Criteria**:
- [ ] [Criterion 1]
- [ ] [Criterion 2]

---

### 3. Non-Functional Requirements

#### NFR-1: Performance
```gherkin
GIVEN the system is under load
WHEN handling 1000 concurrent requests
THEN API p95 latency MUST be < 100ms
  AND database query time < 50ms
  AND frontend render time < 100ms
```

#### NFR-2: Security
```gherkin
GIVEN sensitive data is processed
WHEN implementing the feature
THEN OWASP ASVS Level 2 MUST be met (264/264)
  AND encryption at-rest MUST use AES-256
  AND encryption in-transit MUST use TLS 1.3
```

#### NFR-3: Scalability
```gherkin
GIVEN the platform grows to 10K+ projects
WHEN evaluating architecture
THEN the solution MUST support horizontal scaling
  AND database MUST handle 10M+ rows
  AND cache hit rate MUST be > 90%
```

---

### 4. API Specification

#### Endpoint 1: [Name]
```http
POST /api/v1/[resource]
Content-Type: application/json
Authorization: Bearer {token}

Request:
{
  "field1": "value1",
  "field2": 123
}

Response (200 OK):
{
  "id": "uuid",
  "status": "success",
  "data": { ... }
}

Response (400 Bad Request):
{
  "error": "validation_error",
  "details": [ ... ]
}
```

**BDD Test Scenarios**:
```gherkin
Scenario: Successful API call
  Given a valid authentication token
  And a valid request payload
  When POST /api/v1/[resource]
  Then status code should be 200
  And response should contain "id"
  And response time should be < 100ms
```

---

### 5. Data Model

#### Table: [table_name]
```sql
CREATE TABLE [table_name] (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  field1 VARCHAR(255) NOT NULL,
  field2 INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**Constraints**:
- [ ] Primary key: `id`
- [ ] Foreign keys: [list]
- [ ] Indexes: [list]
- [ ] Unique constraints: [list]

**BDD Validation**:
```gherkin
Scenario: Valid data insertion
  Given a [table_name] row with valid data
  When inserting into database
  Then row should be created successfully
  And constraints should be enforced
  And indexes should be updated
```

---

### 6. Security Considerations

**Authentication**:
```gherkin
GIVEN a user wants to access this feature
WHEN making an API request
THEN a valid JWT token MUST be present
  AND token expiry MUST be checked
  AND user permissions MUST be validated
```

**Authorization**:
```gherkin
GIVEN a user has role [role_name]
WHEN accessing [resource]
THEN RBAC policies MUST be enforced
  AND row-level security MUST filter data
  AND audit log MUST record access
```

**Data Protection**:
- [ ] Encryption at-rest: AES-256
- [ ] Encryption in-transit: TLS 1.3
- [ ] PII handling: [Strategy]

---

### 7. Testing Strategy

#### Unit Tests
```gherkin
GIVEN a [component] is implemented
WHEN running unit tests
THEN test coverage MUST be ≥ 95%
  AND all edge cases MUST be covered
  AND no mocks MUST be used (Zero Mock Policy)
```

#### Integration Tests
```gherkin
GIVEN the API is deployed
WHEN running integration tests
THEN all endpoints MUST return expected responses
  AND database transactions MUST be atomic
  AND external services MUST be tested with real instances
```

#### E2E Tests
```gherkin
GIVEN a user performs [workflow]
WHEN executing E2E tests
THEN the entire flow MUST complete successfully
  AND performance targets MUST be met
  AND user experience MUST be validated
```

---

### 8. Implementation Plan

**Phase 1: Backend** (X days, Y SP)
- [ ] Database schema migration
- [ ] API endpoints implementation
- [ ] Unit tests (95%+ coverage)

**Phase 2: Frontend** (X days, Y SP)
- [ ] UI components
- [ ] State management
- [ ] E2E tests

**Phase 3: Integration** (X days, Y SP)
- [ ] Backend-Frontend integration
- [ ] Performance testing
- [ ] Security audit

---

### 9. Dependencies

**Internal**:
- [ ] SPEC-YYYY: [Description]
- [ ] ADR-XXX: [Description]

**External**:
- [ ] [Library/Service name]: [Purpose]

---

### 10. References

**Internal Docs**:
- [ADR-XXX: Architecture Decision](link)
- [SPRINT-XXX: Implementation Plan](link)

**External Resources**:
- [External reference 1](url)
- [External reference 2](url)

---

### 11. Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | YYYY-MM-DD | [Name] | Initial specification |

---

**Spec Status**: DRAFT
**Created**: YYYY-MM-DD
**Author**: [Name]
**Next Review**: [Date]
**Approval Required**: CTO
