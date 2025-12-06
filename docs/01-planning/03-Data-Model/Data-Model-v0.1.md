# Data Model v0.1 - PostgreSQL Schema Design

**Version**: 1.0.0
**Date**: November 29, 2025
**Status**: IMPLEMENTED - Production Ready
**Authority**: Backend Lead + CTO + Database Architect
**Foundation**: Functional Requirements Document (FR1-FR5)
**Framework**: SDLC 4.9 Complete Lifecycle

> **UPDATE (Nov 29, 2025)**: Schema implemented with 24 tables (down from 25 design).
> `evidence_integrity_checks` merged into `gate_evidence` for simplicity.
> Actual column names aligned with SQLAlchemy model implementation.

---

## Executive Summary

**Purpose**: Define the complete PostgreSQL database schema supporting all 5 functional requirements (FR1-FR5).

**Scope**:
- 25 core tables (users, gates, evidence, policies, AI usage)
- Relationships and constraints (foreign keys, indexes)
- Data types and validation rules
- Migration strategy (Alembic)

**Design Principles**:
1. **Normalization**: 3NF (Third Normal Form) for data integrity
2. **Performance**: Strategic indexes for <200ms query response (p95)
3. **Auditability**: 100% operations logged (created_at, updated_at, deleted_at)
4. **Scalability**: Support 1,000 gates/day, 10,000 evidence files
5. **Security**: Row-level security (RLS) for multi-tenancy

---

## Entity-Relationship Diagram (ERD)

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     CORE ENTITIES                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │  Users   │───▶│ Projects │◀───│  Gates   │───▶│ Evidence │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│       │               │               │               │         │
│       │               │               │               │         │
│       ▼               ▼               ▼               ▼         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │  Roles   │    │  Stages  │    │ Approvals│    │ Integrity│ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                   POLICY ENGINE                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐ │
│  │ Policies │───▶│ Policy Tests │    │ Policy Evaluations   │ │
│  └──────────┘    └──────────────┘    └──────────────────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    AI ENGINE                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────────┐  │
│  │ AI Providers │───▶│ AI Requests  │───▶│ AI Usage Logs  │  │
│  └──────────────┘    └──────────────┘    └────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Detailed ERD (Mermaid Format)

```mermaid
erDiagram
    USERS ||--o{ USER_ROLES : has
    USERS ||--o{ PROJECTS : owns
    USERS ||--o{ GATES : creates
    USERS ||--o{ GATE_APPROVALS : approves

    PROJECTS ||--o{ GATES : contains
    PROJECTS ||--o{ PROJECT_MEMBERS : has
    PROJECTS ||--o{ CUSTOM_POLICIES : uses

    GATES ||--o{ GATE_EVIDENCE : requires
    GATES ||--o{ GATE_APPROVALS : needs
    GATES ||--o{ POLICY_EVALUATIONS : evaluated_by
    GATES ||--o{ STAGE_TRANSITIONS : triggers

    GATE_EVIDENCE ||--o{ EVIDENCE_INTEGRITY_CHECKS : verified_by
    GATE_EVIDENCE ||--o{ AI_EVIDENCE_DRAFTS : generates

    POLICIES ||--o{ CUSTOM_POLICIES : customized_as
    POLICIES ||--o{ POLICY_TESTS : tested_by
    POLICIES ||--o{ POLICY_EVALUATIONS : executes

    AI_PROVIDERS ||--o{ AI_REQUESTS : handles
    AI_REQUESTS ||--o{ AI_USAGE_LOGS : logs

    ROLES ||--o{ USER_ROLES : assigned_to
```

---

## Core Tables

### 1. Users Table

**Purpose**: Authentication and user profile management

**Table Name**: `users`

```sql
CREATE TABLE users (
    -- Primary Key
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Authentication
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, -- bcrypt hash
    email_verified BOOLEAN DEFAULT FALSE,
    email_verified_at TIMESTAMPTZ,

    -- OAuth (optional)
    oauth_provider VARCHAR(50), -- 'github', 'google', 'microsoft'
    oauth_id VARCHAR(255),
    oauth_access_token TEXT, -- Encrypted

    -- MFA (for C-Suite)
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255), -- TOTP secret, encrypted
    mfa_backup_codes TEXT[], -- Encrypted array

    -- Profile
    full_name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    locale VARCHAR(10) DEFAULT 'en',

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    last_login_ip INET,

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ, -- Soft delete

    -- Indexes
    CONSTRAINT users_email_unique UNIQUE (email),
    CONSTRAINT users_oauth_unique UNIQUE (oauth_provider, oauth_id)
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_oauth ON users(oauth_provider, oauth_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_active ON users(is_active) WHERE deleted_at IS NULL;
```

**Acceptance Criteria**:
- AC1: Support 10,000 users (initial scale)
- AC2: Email lookup <10ms (indexed)
- AC3: Password hash: bcrypt rounds 12+
- AC4: MFA secret: AES-256 encrypted at rest

---

### 2. Roles Table

**Purpose**: Role-Based Access Control (RBAC)

**Table Name**: `roles`

```sql
CREATE TABLE roles (
    -- Primary Key
    role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Role Definition
    role_name VARCHAR(50) NOT NULL UNIQUE, -- 'admin', 'engineering_manager', 'approver_cto', 'developer', 'viewer'
    display_name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Permissions (JSON)
    permissions JSONB NOT NULL DEFAULT '{}',
    -- Example: {"gates": ["create", "read", "update"], "evidence": ["upload", "read"]}

    -- Hierarchy
    is_system_role BOOLEAN DEFAULT FALSE, -- System roles cannot be deleted
    parent_role_id UUID REFERENCES roles(role_id),

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_roles_name ON roles(role_name) WHERE deleted_at IS NULL;
CREATE INDEX idx_roles_system ON roles(is_system_role) WHERE deleted_at IS NULL;
```

**Sample Data** (System Roles):
```sql
INSERT INTO roles (role_name, display_name, description, is_system_role, permissions) VALUES
('admin', 'Administrator', 'Full system access', TRUE, '{"*": ["*"]}'),
('engineering_manager', 'Engineering Manager', 'Create gates, submit for review', TRUE, '{"gates": ["create", "read", "update", "submit"], "evidence": ["upload", "read"]}'),
('approver_cto', 'CTO (Approver)', 'Approve/reject gates', TRUE, '{"gates": ["read", "approve", "reject"], "evidence": ["read"]}'),
('developer', 'Developer', 'View gates, upload evidence', TRUE, '{"gates": ["read"], "evidence": ["upload", "read"]}'),
('viewer', 'Viewer (Auditor)', 'Read-only access', TRUE, '{"gates": ["read"], "evidence": ["read"]}');
```

---

### 3. User Roles Table (Junction)

**Purpose**: Many-to-many relationship between users and roles

**Table Name**: `user_roles`

```sql
CREATE TABLE user_roles (
    -- Composite Primary Key
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,

    -- Scope (optional: project-level roles)
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE, -- NULL = global role

    -- Audit
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assigned_by UUID REFERENCES users(user_id),

    PRIMARY KEY (user_id, role_id, COALESCE(project_id, '00000000-0000-0000-0000-000000000000'))
);

-- Indexes
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);
CREATE INDEX idx_user_roles_project ON user_roles(project_id) WHERE project_id IS NOT NULL;
```

---

### 4. Projects Table

**Purpose**: Project/workspace isolation

**Table Name**: `projects`

```sql
CREATE TABLE projects (
    -- Primary Key
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Project Info
    project_name VARCHAR(255) NOT NULL,
    project_slug VARCHAR(100) NOT NULL UNIQUE, -- URL-friendly: 'sdlc-orchestrator-mvp'
    description TEXT,

    -- Owner
    owner_user_id UUID NOT NULL REFERENCES users(user_id),

    -- SDLC Stage
    current_stage VARCHAR(20) NOT NULL DEFAULT 'WHY',
    -- 'WHY', 'WHAT', 'HOW', 'BUILD', 'TEST', 'DEPLOY', 'OPERATE', 'INTEGRATE', 'COLLABORATE', 'GOVERN'

    -- Timeline
    start_date DATE,
    target_end_date DATE,
    actual_end_date DATE,

    -- Settings (JSON)
    settings JSONB DEFAULT '{}',
    -- Example: {"github_repo": "org/repo", "slack_channel": "#engineering"}

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_archived BOOLEAN DEFAULT FALSE,

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,

    CONSTRAINT projects_slug_unique UNIQUE (project_slug)
);

-- Indexes
CREATE INDEX idx_projects_owner ON projects(owner_user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_slug ON projects(project_slug) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_active ON projects(is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_stage ON projects(current_stage) WHERE deleted_at IS NULL;
```

---

### 5. Project Members Table (Junction)

**Purpose**: Multi-user project access

**Table Name**: `project_members`

```sql
CREATE TABLE project_members (
    -- Composite Primary Key
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Member Role (project-specific)
    role VARCHAR(50) NOT NULL, -- 'owner', 'member', 'viewer'

    -- Audit
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    invited_by UUID REFERENCES users(user_id),

    PRIMARY KEY (project_id, user_id)
);

-- Indexes
CREATE INDEX idx_project_members_project ON project_members(project_id);
CREATE INDEX idx_project_members_user ON project_members(user_id);
```

---

### 6. Gates Table

**Purpose**: Quality gate instances (FR1)

**Table Name**: `gates`

```sql
CREATE TABLE gates (
    -- Primary Key
    gate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Gate Info
    gate_name VARCHAR(255) NOT NULL,
    gate_type VARCHAR(50) NOT NULL, -- 'G0_1_DESIGN_THINKING', 'G0_2_SOLUTION_DIVERSITY', 'G1_DESIGN_READY', etc.
    stage VARCHAR(20) NOT NULL, -- 'WHY', 'WHAT', 'HOW', 'BUILD', 'TEST', 'DEPLOY', 'OPERATE', etc.

    -- Project
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,

    -- Creator
    created_by UUID NOT NULL REFERENCES users(user_id),

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    -- 'DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED'

    -- Exit Criteria (JSON array from policy pack)
    exit_criteria JSONB NOT NULL DEFAULT '[]',
    -- Example: [{"id": "G1-EC1", "description": "TDD tests written", "required": true}]

    -- Metadata (JSON)
    metadata JSONB DEFAULT '{}',
    -- Example: {"feature_name": "User Auth", "priority": "P0", "target_sprint": 2}

    -- GitHub Integration
    github_branch VARCHAR(255), -- 'build/user-auth'
    github_pr_number INTEGER,

    -- Policy Evaluation
    last_policy_check_at TIMESTAMPTZ,
    last_policy_result JSONB, -- OPA response

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submitted_at TIMESTAMPTZ, -- When submitted for review
    approved_at TIMESTAMPTZ, -- When all approvers approved
    rejected_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_gates_project ON gates(project_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_gates_status ON gates(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_gates_type ON gates(gate_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_gates_stage ON gates(stage) WHERE deleted_at IS NULL;
CREATE INDEX idx_gates_created_by ON gates(created_by) WHERE deleted_at IS NULL;
CREATE INDEX idx_gates_github_branch ON gates(github_branch) WHERE deleted_at IS NULL;
```

---

### 7. Gate Approvals Table

**Purpose**: Multi-approval workflow (FR1)

**Table Name**: `gate_approvals`

```sql
CREATE TABLE gate_approvals (
    -- Primary Key
    approval_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Gate
    gate_id UUID NOT NULL REFERENCES gates(gate_id) ON DELETE CASCADE,

    -- Approver
    approver_role VARCHAR(50) NOT NULL, -- 'CTO', 'CPO', 'CEO', 'CFO', 'CIO'
    approver_user_id UUID NOT NULL REFERENCES users(user_id),

    -- Decision
    decision VARCHAR(20) NOT NULL, -- 'APPROVE', 'REJECT'
    comment TEXT, -- Required for REJECT

    -- Audit
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint: one approval per role per gate
    CONSTRAINT gate_approvals_unique UNIQUE (gate_id, approver_role)
);

-- Indexes
CREATE INDEX idx_gate_approvals_gate ON gate_approvals(gate_id);
CREATE INDEX idx_gate_approvals_approver ON gate_approvals(approver_user_id);
CREATE INDEX idx_gate_approvals_decision ON gate_approvals(decision);
```

---

### 8. Gate Evidence Table

**Purpose**: Evidence files for gates (FR2)

**Table Name**: `gate_evidence`

> **UPDATED (Nov 29, 2025)**: Actual implementation uses `s3_key`, `s3_bucket`, `file_type` instead of `file_path`, `mime_type`.

```sql
CREATE TABLE gate_evidence (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Gate
    gate_id UUID NOT NULL REFERENCES gates(id) ON DELETE CASCADE,

    -- Evidence Type
    evidence_type VARCHAR(50) NOT NULL,
    -- 'DESIGN_DOCUMENT', 'CODE_REVIEW', 'TEST_RESULTS', 'ARCHITECTURE_DIAGRAM', 'RUNBOOK', 'GITHUB_PR', etc.

    -- File Info (ACTUAL IMPLEMENTATION)
    file_name VARCHAR(255) NOT NULL,
    s3_key TEXT NOT NULL,           -- MinIO path: 'bflow/gate-1/evidence-1.pdf'
    s3_bucket VARCHAR(100) NOT NULL DEFAULT 'evidence-vault',
    file_size BIGINT NOT NULL,
    file_type VARCHAR(100),         -- MIME type: 'application/pdf', 'image/png'

    -- Integrity (SHA256)
    sha256_hash VARCHAR(64) NOT NULL, -- 256 bits = 64 hex chars

    -- Uploader
    uploaded_by UUID NOT NULL REFERENCES users(id),

    -- Description
    description TEXT,

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_gate_evidence_gate ON gate_evidence(gate_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_gate_evidence_type ON gate_evidence(evidence_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_gate_evidence_sha256 ON gate_evidence(sha256_hash) WHERE deleted_at IS NULL;
CREATE INDEX idx_gate_evidence_uploader ON gate_evidence(uploaded_by) WHERE deleted_at IS NULL;

-- Unique constraint: no duplicate SHA256 hashes per gate
CREATE UNIQUE INDEX idx_gate_evidence_sha256_unique ON gate_evidence(gate_id, sha256_hash) WHERE deleted_at IS NULL;
```

---

### 9. Evidence Integrity Checks Table

> **DEPRECATED (Nov 29, 2025)**: This table was merged into `gate_evidence.sha256_hash` for simplicity.
> Integrity verification is done on-demand by comparing stored SHA256 with recalculated hash.

**Purpose**: Audit trail for integrity verification (FR2)

**Status**: NOT IMPLEMENTED - Merged into gate_evidence

~~**Table Name**: `evidence_integrity_checks`~~

```sql
-- DEPRECATED: Merged into gate_evidence.sha256_hash
-- Integrity verification done on-demand:
-- 1. Fetch file from MinIO
-- 2. Calculate SHA256
-- 3. Compare with gate_evidence.sha256_hash
-- 4. Log to audit_logs if tampering detected
```

---

### 10. Policies Table

**Purpose**: Policy pack library (FR5)

**Table Name**: `policies`

```sql
CREATE TABLE policies (
    -- Primary Key
    policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Policy Info
    policy_code VARCHAR(50) NOT NULL UNIQUE, -- 'G1-CODE-REVIEW', 'G2-TEST-COVERAGE'
    policy_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Gate Association
    gate_type VARCHAR(50) NOT NULL, -- 'G1_DESIGN_READY', 'G2_BUILD_READY', etc.
    stage VARCHAR(20) NOT NULL, -- 'WHAT', 'BUILD', 'TEST', etc.

    -- Severity
    severity VARCHAR(20) NOT NULL, -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'

    -- Rego Code
    rego_code TEXT NOT NULL, -- OPA Rego policy code
    rego_version VARCHAR(20) NOT NULL DEFAULT '1.0.0', -- Semantic versioning

    -- Parameters (JSON schema for customization)
    parameters_schema JSONB DEFAULT '{}',
    -- Example: {"min_reviewers": {"type": "integer", "default": 2, "min": 1, "max": 10}}

    -- Test Cases
    test_cases JSONB DEFAULT '[]',
    -- Example: [{"name": "Multiple reviewers", "input": {...}, "expected": {"allowed": true}}]

    -- Documentation
    documentation_url TEXT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_system_policy BOOLEAN DEFAULT FALSE, -- System policies cannot be deleted

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deprecated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_policies_code ON policies(policy_code) WHERE deleted_at IS NULL;
CREATE INDEX idx_policies_gate_type ON policies(gate_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_policies_stage ON policies(stage) WHERE deleted_at IS NULL;
CREATE INDEX idx_policies_active ON policies(is_active) WHERE deleted_at IS NULL;
```

---

### 11. Custom Policies Table

**Purpose**: Project-specific policy customizations (FR5)

**Table Name**: `custom_policies`

```sql
CREATE TABLE custom_policies (
    -- Primary Key
    custom_policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Base Policy
    base_policy_id UUID NOT NULL REFERENCES policies(policy_id),

    -- Project
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,

    -- Custom Info
    custom_name VARCHAR(255),

    -- Custom Parameters (JSON)
    parameters JSONB NOT NULL DEFAULT '{}',
    -- Example: {"min_reviewers": 3} (overrides base policy default 2)

    -- Generated Rego (parameterized)
    generated_rego TEXT, -- Rego code with custom parameters applied

    -- Creator
    created_by UUID NOT NULL REFERENCES users(user_id),

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_custom_policies_base ON custom_policies(base_policy_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_custom_policies_project ON custom_policies(project_id) WHERE deleted_at IS NULL;
```

---

### 12. Policy Evaluations Table

**Purpose**: Audit trail for OPA policy checks (FR1)

**Table Name**: `policy_evaluations`

```sql
CREATE TABLE policy_evaluations (
    -- Primary Key
    evaluation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Gate
    gate_id UUID NOT NULL REFERENCES gates(gate_id) ON DELETE CASCADE,

    -- Policy
    policy_id UUID REFERENCES policies(policy_id), -- NULL for custom policies
    custom_policy_id UUID REFERENCES custom_policies(custom_policy_id),

    -- OPA Request/Response
    input_document JSONB NOT NULL, -- Evidence + metadata sent to OPA
    output_decision JSONB NOT NULL, -- OPA response: {"allowed": false, "violations": [...]}

    -- Timing
    evaluation_duration_ms INTEGER, -- How long OPA took

    -- OPA Version
    opa_version VARCHAR(20),

    -- Audit
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_policy_evaluations_gate ON policy_evaluations(gate_id);
CREATE INDEX idx_policy_evaluations_policy ON policy_evaluations(policy_id);
CREATE INDEX idx_policy_evaluations_evaluated_at ON policy_evaluations(evaluated_at DESC);
```

---

### 13. Stage Transitions Table

**Purpose**: Audit trail for stage progression (FR1)

**Table Name**: `stage_transitions`

```sql
CREATE TABLE stage_transitions (
    -- Primary Key
    transition_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Project
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,

    -- Gate (that triggered transition)
    gate_id UUID NOT NULL REFERENCES gates(gate_id),

    -- Transition
    from_stage VARCHAR(20) NOT NULL, -- 'WHAT'
    to_stage VARCHAR(20) NOT NULL, -- 'BUILD'

    -- Triggered By
    triggered_by UUID NOT NULL REFERENCES users(user_id), -- Last approver

    -- Audit
    transitioned_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_stage_transitions_project ON stage_transitions(project_id);
CREATE INDEX idx_stage_transitions_gate ON stage_transitions(gate_id);
CREATE INDEX idx_stage_transitions_stages ON stage_transitions(from_stage, to_stage);
```

---

### 14. AI Providers Table

**Purpose**: Multi-provider AI configuration (FR3)

**Table Name**: `ai_providers`

```sql
CREATE TABLE ai_providers (
    -- Primary Key
    provider_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Provider Info
    provider_code VARCHAR(50) NOT NULL UNIQUE, -- 'CLAUDE', 'GPT4', 'GEMINI'
    provider_name VARCHAR(100) NOT NULL, -- 'Claude Sonnet 4.5', 'GPT-4o', 'Gemini 2.0 Flash'

    -- API Configuration
    api_endpoint TEXT NOT NULL,
    api_key_encrypted TEXT NOT NULL, -- AES-256 encrypted

    -- Model
    model_id VARCHAR(100) NOT NULL, -- 'claude-sonnet-4-5-20250929', 'gpt-4o', 'gemini-2.0-flash'

    -- Pricing (per 1M tokens)
    price_input_per_1m_usd DECIMAL(10, 6), -- $3.00
    price_output_per_1m_usd DECIMAL(10, 6), -- $15.00

    -- Rate Limits
    rate_limit_rpm INTEGER, -- Requests per minute (50 for Claude)
    rate_limit_tpm INTEGER, -- Tokens per minute (100,000 for Claude)

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ai_providers_code ON ai_providers(provider_code);
CREATE INDEX idx_ai_providers_active ON ai_providers(is_active);
```

---

### 15. AI Requests Table

**Purpose**: AI request routing and tracking (FR3)

**Table Name**: `ai_requests`

```sql
CREATE TABLE ai_requests (
    -- Primary Key
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Gate (optional: AI can be used outside gates)
    gate_id UUID REFERENCES gates(gate_id),

    -- User
    user_id UUID NOT NULL REFERENCES users(user_id),

    -- Provider
    provider_id UUID NOT NULL REFERENCES ai_providers(provider_id),

    -- Request Type
    evidence_type VARCHAR(50), -- 'TDD_TESTS', 'API_CONTRACTS', 'RUNBOOK', etc.
    stage VARCHAR(20), -- 'WHAT', 'BUILD', 'OPERATE', etc.

    -- Prompt
    prompt_template TEXT NOT NULL, -- Stage-aware prompt template
    prompt_input JSONB NOT NULL, -- User-provided input (user story, architecture doc, etc.)
    prompt_final TEXT NOT NULL, -- Final prompt sent to AI (template + input)

    -- Response
    response_content TEXT, -- Generated code/text
    response_tokens_input INTEGER,
    response_tokens_output INTEGER,
    response_tokens_total INTEGER,

    -- Cost
    cost_usd DECIMAL(10, 6), -- Calculated from tokens * pricing

    -- Temperature
    temperature DECIMAL(3, 2) DEFAULT 0.2, -- 0.0 - 1.0

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    -- 'PENDING', 'SUCCESS', 'FAILED', 'RATE_LIMITED'
    error_message TEXT,

    -- Timing
    request_duration_ms INTEGER,

    -- Audit
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_ai_requests_gate ON ai_requests(gate_id);
CREATE INDEX idx_ai_requests_user ON ai_requests(user_id);
CREATE INDEX idx_ai_requests_provider ON ai_requests(provider_id);
CREATE INDEX idx_ai_requests_status ON ai_requests(status);
CREATE INDEX idx_ai_requests_requested_at ON ai_requests(requested_at DESC);
```

---

### 16. AI Usage Logs Table

**Purpose**: Cost tracking and budget monitoring (FR3)

**Table Name**: `ai_usage_logs`

```sql
CREATE TABLE ai_usage_logs (
    -- Primary Key
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Request
    request_id UUID NOT NULL REFERENCES ai_requests(request_id) ON DELETE CASCADE,

    -- Aggregation Keys
    project_id UUID REFERENCES projects(project_id),
    gate_id UUID REFERENCES gates(gate_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    provider_id UUID NOT NULL REFERENCES ai_providers(provider_id),

    -- Usage
    tokens_input INTEGER NOT NULL,
    tokens_output INTEGER NOT NULL,
    tokens_total INTEGER NOT NULL,
    cost_usd DECIMAL(10, 6) NOT NULL,

    -- Time Window (for budget tracking)
    usage_date DATE NOT NULL, -- For daily aggregation
    usage_month VARCHAR(7) NOT NULL, -- 'YYYY-MM' for monthly budget

    -- Audit
    logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ai_usage_logs_request ON ai_usage_logs(request_id);
CREATE INDEX idx_ai_usage_logs_project ON ai_usage_logs(project_id);
CREATE INDEX idx_ai_usage_logs_gate ON ai_usage_logs(gate_id);
CREATE INDEX idx_ai_usage_logs_user ON ai_usage_logs(user_id);
CREATE INDEX idx_ai_usage_logs_provider ON ai_usage_logs(provider_id);
CREATE INDEX idx_ai_usage_logs_month ON ai_usage_logs(usage_month);

-- Aggregate index for monthly cost rollup
CREATE INDEX idx_ai_usage_logs_monthly_cost ON ai_usage_logs(usage_month, provider_id)
INCLUDE (cost_usd);
```

---

### 17. AI Evidence Drafts Table

**Purpose**: Store AI-generated evidence before upload (FR3)

**Table Name**: `ai_evidence_drafts`

```sql
CREATE TABLE ai_evidence_drafts (
    -- Primary Key
    draft_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Gate
    gate_id UUID NOT NULL REFERENCES gates(gate_id) ON DELETE CASCADE,

    -- AI Request
    request_id UUID NOT NULL REFERENCES ai_requests(request_id),

    -- Evidence Type
    evidence_type VARCHAR(50) NOT NULL, -- 'TDD_TESTS', 'API_CONTRACTS', etc.

    -- Generated Content
    generated_content TEXT NOT NULL, -- Code or markdown

    -- User Edits (optional)
    edited_content TEXT, -- User-modified version

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    -- 'DRAFT', 'UPLOADED' (converted to gate_evidence), 'DISCARDED'

    -- Creator
    created_by UUID NOT NULL REFERENCES users(user_id),

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    uploaded_at TIMESTAMPTZ, -- When converted to gate_evidence
    deleted_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_ai_evidence_drafts_gate ON ai_evidence_drafts(gate_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ai_evidence_drafts_request ON ai_evidence_drafts(request_id);
CREATE INDEX idx_ai_evidence_drafts_status ON ai_evidence_drafts(status) WHERE deleted_at IS NULL;
```

---

## Supporting Tables

### 18. Refresh Tokens Table

**Purpose**: JWT refresh token management

**Table Name**: `refresh_tokens`

```sql
CREATE TABLE refresh_tokens (
    -- Primary Key
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Token
    token_hash VARCHAR(255) NOT NULL UNIQUE, -- SHA256 hash of token

    -- Expiry
    expires_at TIMESTAMPTZ NOT NULL,

    -- Revocation
    is_revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMPTZ,

    -- Device Info
    user_agent TEXT,
    ip_address INET,

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id) WHERE is_revoked = FALSE;
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash) WHERE is_revoked = FALSE;
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at) WHERE is_revoked = FALSE;

-- Cleanup expired tokens (run daily via cron)
CREATE INDEX idx_refresh_tokens_cleanup ON refresh_tokens(expires_at)
WHERE is_revoked = FALSE AND expires_at < NOW();
```

---

### 19. Audit Logs Table

**Purpose**: System-wide audit trail (compliance)

**Table Name**: `audit_logs`

```sql
CREATE TABLE audit_logs (
    -- Primary Key
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event
    event_type VARCHAR(50) NOT NULL,
    -- 'USER_LOGIN', 'GATE_CREATED', 'GATE_APPROVED', 'EVIDENCE_UPLOADED', 'POLICY_UPDATED', etc.

    -- Actor
    user_id UUID REFERENCES users(user_id),

    -- Resource
    resource_type VARCHAR(50), -- 'gate', 'evidence', 'policy', 'user'
    resource_id UUID,

    -- Details (JSON)
    event_data JSONB DEFAULT '{}',
    -- Example: {"gate_id": "...", "old_status": "DRAFT", "new_status": "APPROVED"}

    -- Request Context
    request_id VARCHAR(100), -- Trace ID from OpenTelemetry
    ip_address INET,
    user_agent TEXT,

    -- Audit
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_occurred_at ON audit_logs(occurred_at DESC);

-- Partitioning by month (for performance at scale)
-- CREATE TABLE audit_logs_2025_11 PARTITION OF audit_logs
-- FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
```

---

### 20. Webhooks Table

**Purpose**: GitHub webhook event log

**Table Name**: `webhooks`

```sql
CREATE TABLE webhooks (
    -- Primary Key
    webhook_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source
    source VARCHAR(50) NOT NULL, -- 'github', 'gitlab', 'bitbucket'

    -- Event Type
    event_type VARCHAR(100) NOT NULL, -- 'pull_request.merged', 'push', 'issue.created'

    -- Payload
    payload JSONB NOT NULL, -- Full webhook payload

    -- Processing
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    error_message TEXT,

    -- Idempotency
    external_event_id VARCHAR(255), -- GitHub delivery ID

    -- Audit
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_webhooks_source ON webhooks(source);
CREATE INDEX idx_webhooks_event_type ON webhooks(event_type);
CREATE INDEX idx_webhooks_processed ON webhooks(processed, received_at) WHERE processed = FALSE;
CREATE INDEX idx_webhooks_external_id ON webhooks(source, external_event_id);
```

---

### 21. Notifications Table

**Purpose**: User notification queue (email, Slack)

**Table Name**: `notifications`

```sql
CREATE TABLE notifications (
    -- Primary Key
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Recipient
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Channel
    channel VARCHAR(20) NOT NULL, -- 'EMAIL', 'SLACK', 'IN_APP'

    -- Content
    notification_type VARCHAR(50) NOT NULL,
    -- 'GATE_SUBMITTED', 'GATE_APPROVED', 'GATE_REJECTED', 'MENTION', etc.
    subject VARCHAR(255),
    body TEXT NOT NULL,

    -- Related Resource
    resource_type VARCHAR(50), -- 'gate', 'evidence', 'project'
    resource_id UUID,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    -- 'PENDING', 'SENT', 'FAILED'
    sent_at TIMESTAMPTZ,
    error_message TEXT,

    -- In-App Status
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read) WHERE channel = 'IN_APP';
CREATE INDEX idx_notifications_status ON notifications(status, created_at) WHERE status = 'PENDING';
CREATE INDEX idx_notifications_resource ON notifications(resource_type, resource_id);
```

---

## Data Dictionary Summary

> **UPDATED (Nov 29, 2025)**: Reflects actual implementation with 24 tables.
> Added `oauth_accounts`, `api_keys`, `policy_tests` tables.
> Removed `evidence_integrity_checks` (merged into gate_evidence).

| # | Table Name | Primary Key | Foreign Keys | Purpose | Row Estimate (Year 1) | Status |
|---|------------|-------------|--------------|---------|----------------------|--------|
| 1 | `users` | id | - | User accounts | 10,000 | ✅ Implemented |
| 2 | `roles` | id | - | RBAC roles | 13 | ✅ Implemented |
| 3 | `user_roles` | (composite) | user_id, role_id | User-role mapping | 15,000 | ✅ Implemented |
| 4 | `projects` | id | owner_id | Projects/workspaces | 1,000 | ✅ Implemented |
| 5 | `project_members` | id | project_id, user_id | Project membership | 5,000 | ✅ Implemented |
| 6 | `gates` | id | project_id, created_by | Quality gates | 50,000 | ✅ Implemented |
| 7 | `gate_approvals` | id | gate_id, approver_id | Approvals | 100,000 | ✅ Implemented |
| 8 | `gate_evidence` | id | gate_id, uploaded_by | Evidence files | 200,000 | ✅ Implemented |
| 9 | ~~`evidence_integrity_checks`~~ | - | - | ~~Integrity audits~~ | - | ❌ DEPRECATED |
| 10 | `policies` | id | - | Policy library | 110 | ✅ Implemented |
| 11 | `custom_policies` | id | base_policy_id, project_id | Custom policies | 500 | ✅ Implemented |
| 12 | `policy_evaluations` | id | gate_id, policy_id | Policy check logs | 250,000 | ✅ Implemented |
| 13 | `policy_tests` | id | policy_id | Policy test cases | 550 | ✅ **NEW** |
| 14 | `stage_transitions` | id | project_id, gate_id | Stage progression | 10,000 | ✅ Implemented |
| 15 | `ai_providers` | id | - | AI provider config | 4 | ✅ Implemented |
| 16 | `ai_requests` | id | provider_id, user_id | AI requests | 100,000 | ✅ Implemented |
| 17 | `ai_usage_logs` | id | request_id, project_id | AI cost tracking | 100,000 | ✅ Implemented |
| 18 | `ai_evidence_drafts` | id | gate_id, request_id | AI drafts | 50,000 | ✅ Implemented |
| 19 | `refresh_tokens` | id | user_id | JWT refresh tokens | 15,000 | ✅ Implemented |
| 20 | `oauth_accounts` | id | user_id | OAuth connections | 5,000 | ✅ **NEW** |
| 21 | `api_keys` | id | user_id | API keys | 2,000 | ✅ **NEW** |
| 22 | `audit_logs` | id | user_id | Audit trail | 500,000 | ✅ Implemented |
| 23 | `webhooks` | id | project_id | Webhook events | 100,000 | ✅ Implemented |
| 24 | `notifications` | id | user_id | Notifications | 200,000 | ✅ Implemented |

**Total Tables**: 24 (implemented), 1 deprecated
**Total Estimated Rows (Year 1)**: ~1.9 million

### Seed Data Statistics (Nov 29, 2025)

| Entity | Count | Source |
|--------|-------|--------|
| System Roles | 13 | CEO, CTO, CPO, EM, TL, DEV, QA, DevOps, Security, PM, BA, CIO, CFO |
| Users | 12 | 1 admin + 11 NQH team members |
| Projects | 4 | BFlow, NQH-Bot, SDLC-Orchestrator, SDLC-Enterprise-Framework |
| Gates | 26 | 22 APPROVED, 1 PENDING, 3 DRAFT |
| Evidence Files | 46 | Distributed across all gates |
| Project Memberships | 35 | Team assignments |
| AI Providers | 4 | Ollama (primary), Claude, GPT-4o, Gemini |

---

## Database Configuration

### PostgreSQL Version

**Target**: PostgreSQL 15.5+

**Rationale**:
- JSON performance improvements (JSONB indexing)
- Row-level security (RLS) for multi-tenancy
- Partitioning support (for audit_logs at scale)

---

### Connection Pooling

**Tool**: PgBouncer or SQLAlchemy pool

**Configuration**:
```python
# backend/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/sdlc_orchestrator"

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Min connections
    max_overflow=30,  # Max connections (total 50)
    pool_timeout=30,  # Wait 30s for connection
    pool_recycle=3600,  # Recycle connections every 1 hour
)
```

---

### Migrations

**Tool**: Alembic

**Directory Structure**:
```
backend/alembic/
├── env.py
├── script.py.mako
└── versions/
    ├── 001_create_users_table.py
    ├── 002_create_roles_table.py
    ├── 003_create_projects_table.py
    ├── 004_create_gates_table.py
    └── ...
```

**Initial Migration** (all tables):
```bash
# Generate migration
alembic revision --autogenerate -m "Initial schema - 21 tables"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

### Backup Strategy

**Frequency**: Daily (3 AM UTC)

**Retention**: 90 days

**Tool**: `pg_dump` + MinIO storage

**Script**:
```bash
#!/bin/bash
# backup-postgres.sh

DATE=$(date +%Y-%m-%d)
BACKUP_FILE="sdlc-orchestrator-${DATE}.sql.gz"

# Dump database
pg_dump -h localhost -U postgres sdlc_orchestrator | gzip > /tmp/${BACKUP_FILE}

# Upload to MinIO
mc cp /tmp/${BACKUP_FILE} minio/backups/postgresql/${BACKUP_FILE}

# Cleanup local file
rm /tmp/${BACKUP_FILE}

# Delete backups older than 90 days
mc rm --recursive --older-than=90d minio/backups/postgresql/
```

---

## Performance Optimization

### Index Strategy

**Rationale**: Support <200ms query response (p95) per CFR2

**Coverage**:
- **Primary Keys**: All tables (B-tree index)
- **Foreign Keys**: All FK columns (join optimization)
- **Status Fields**: `is_active`, `status`, `deleted_at` (filtering)
- **Timestamps**: `created_at DESC`, `updated_at` (sorting)
- **Partial Indexes**: `WHERE deleted_at IS NULL` (soft delete filtering)

**Monitoring**:
```sql
-- Find missing indexes (queries waiting on seq scans)
SELECT schemaname, tablename, seq_scan, seq_tup_read,
       idx_scan, seq_tup_read / seq_scan AS avg_seq_tup
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 25;
```

---

### Query Optimization

**Techniques**:
1. **Eager Loading**: Use SQLAlchemy `joinedload()` to avoid N+1 queries
2. **Pagination**: Cursor-based (not offset) for large result sets
3. **Aggregation**: Use PostgreSQL aggregate functions (not Python loops)
4. **Materialized Views**: For expensive dashboard queries

**Example** (Gate dashboard query):
```python
# Bad: N+1 queries
gates = session.query(Gate).filter_by(project_id=project_id).all()
for gate in gates:
    approvals = gate.approvals  # Separate query per gate

# Good: Single query with join
gates = session.query(Gate).options(
    joinedload(Gate.approvals)
).filter_by(project_id=project_id).all()
```

---

### JSONB Indexing

**Use Case**: Search policy metadata, evidence metadata

**Index Types**:
```sql
-- GIN index for JSONB containment queries
CREATE INDEX idx_gates_metadata_gin ON gates USING GIN (metadata);

-- Query: Find gates with specific metadata
SELECT * FROM gates
WHERE metadata @> '{"priority": "P0"}';

-- GIN index for JSONB key existence
CREATE INDEX idx_gates_exit_criteria_gin ON gates USING GIN (exit_criteria);

-- Query: Find gates with specific exit criterion
SELECT * FROM gates
WHERE exit_criteria @> '[{"id": "G1-EC1"}]';
```

---

## Security Considerations

### Sensitive Data Encryption

**Fields Requiring Encryption**:
- `users.password_hash` → bcrypt (12 rounds)
- `users.mfa_secret` → AES-256
- `users.oauth_access_token` → AES-256
- `ai_providers.api_key_encrypted` → AES-256

**Implementation** (SQLAlchemy):
```python
from cryptography.fernet import Fernet
from sqlalchemy import TypeDecorator, String

class EncryptedString(TypeDecorator):
    impl = String

    def process_bind_param(self, value, dialect):
        if value is not None:
            fernet = Fernet(ENCRYPTION_KEY)
            return fernet.encrypt(value.encode()).decode()
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            fernet = Fernet(ENCRYPTION_KEY)
            return fernet.decrypt(value.encode()).decode()
        return value
```

---

### Row-Level Security (RLS)

**Use Case**: Multi-tenancy (users see only their projects)

**PostgreSQL RLS Policies**:
```sql
-- Enable RLS on projects table
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see projects they are members of
CREATE POLICY project_member_access ON projects
FOR SELECT
USING (
    project_id IN (
        SELECT project_id
        FROM project_members
        WHERE user_id = current_setting('app.user_id')::UUID
    )
);

-- Set user context (from FastAPI middleware)
SET app.user_id = 'uuid-of-current-user';
```

---

### SQL Injection Prevention

**Tools**: SQLAlchemy ORM (parameterized queries)

**Example**:
```python
# Bad: SQL injection vulnerable
user_id = request.query_params.get('user_id')
query = f"SELECT * FROM users WHERE user_id = '{user_id}'"  # NEVER DO THIS

# Good: Parameterized query
user_id = request.query_params.get('user_id')
user = session.query(User).filter_by(user_id=user_id).first()
```

---

## Acceptance Criteria (Data Model v0.1)

**Gate G1 Exit Criteria**:
- ✅ AC1: All 21 core tables defined with SQL DDL
- ✅ AC2: All foreign key relationships documented (ERD)
- ✅ AC3: All indexes specified for <200ms query performance
- ✅ AC4: Sensitive fields identified for encryption (4 fields)
- ✅ AC5: Migration strategy defined (Alembic)
- ✅ AC6: Backup strategy defined (daily pg_dump → MinIO)

**Non-Functional**:
- ✅ AC7: Support 1,000 gates/day (50,000 gates/year)
- ✅ AC8: Support 10,000 evidence files (200,000/year)
- ✅ AC9: Database size <100 GB (Year 1 estimate: 10 GB)
- ✅ AC10: Query response <200ms (p95) with proper indexes

---

## Next Steps (Week 3-4)

### 1. Implement SQLAlchemy Models (Week 3)
- Create Python classes for all 21 tables
- Define relationships (`relationship()`, `backref()`)
- Add validation (Pydantic integration)

### 2. Write Alembic Migrations (Week 3)
- Initial migration: Create all 21 tables
- Seed migration: Insert system roles, policies, AI providers

### 3. Integration Testing (Week 3)
- Test all CRUD operations
- Test foreign key constraints
- Test soft delete behavior

### 4. Performance Testing (Week 4)
- Load test: 1,000 concurrent queries
- Benchmark: Gate dashboard query (<200ms)
- Optimize: Add missing indexes based on query plans

---

## References

- [Functional Requirements Document](../Functional-Requirements/Functional-Requirements-Document.md) - FR1-FR5
- [Product Roadmap](../../00-Project-Foundation/04-Roadmap/Product-Roadmap.md) - Week 2 timeline
- [PostgreSQL Documentation](https://www.postgresql.org/docs/15/) - Version 15.5
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/) - ORM framework
- [Alembic Documentation](https://alembic.sqlalchemy.org/) - Migration tool

---

**End of Data Model v1.0**

**Status**: ✅ IMPLEMENTED - Production Ready
**Date**: November 29, 2025 (Updated from v0.1 Nov 21)
**Gate G1**: ✅ PASSED (Nov 25, 2025)
**Gate G2**: ✅ PASSED (Dec 9, 2025)
**Gate G3**: ✅ PASSED (Jan 27, 2026)
**Approvals**: Backend Lead ✅, CTO ✅, Database Architect ✅

### Implementation Notes

**Migration Files**:
- `dce31118ffb7_initial_schema_24_tables.py` - Initial schema (24 tables)
- `a502ce0d23a7_seed_data_realistic_mtc_nqh_examples.py` - NQH Portfolio seed data
- `f8a9b2c3d4e5_add_github_fields_to_projects.py` - GitHub integration fields

**Database**: PostgreSQL 15.5 (Docker container: `sdlc-prod-postgres`)
**ORM**: SQLAlchemy 2.0 (async mode)
**Migrations**: Alembic 1.12+
