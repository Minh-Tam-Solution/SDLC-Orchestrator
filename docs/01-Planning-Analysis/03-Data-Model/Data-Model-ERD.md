# Data Model & Entity-Relationship Diagram
## Database Schema and Relationships

**Version**: 1.0.0
**Date**: January 13, 2025
**Status**: ACTIVE - DRAFT
**Authority**: CTO + Backend Lead Review (PENDING)
**Foundation**: FRD v1.0, User Stories v1.0
**Stage**: Stage 01 (WHAT - Planning & Analysis)

---

## Document Purpose

This document defines **WHAT data to store**, not HOW to implement database (Stage 02 scope).

**Key Sections**:
- Entity-Relationship Diagram (ERD)
- Table schemas (columns, data types, constraints)
- Relationships (1:1, 1:N, N:M)
- Indexes (performance optimization)
- Data dictionary (field definitions)

---

## ERD Overview (16 Core Tables)

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   users     │──────▶│   teams     │──────▶│organizations│
└─────────────┘       └─────────────┘       └─────────────┘
       │
       │ 1:N
       ▼
┌─────────────┐  N:M  ┌─────────────┐  1:N  ┌─────────────┐
│  projects   │◀─────▶│project_users│──────▶│   gates     │
└─────────────┘       └─────────────┘       └─────────────┘
       │                                            │
       │ 1:N                                        │ 1:N
       ▼                                            ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  features   │       │gate_evals   │       │  policies   │
└─────────────┘       └─────────────┘       └─────────────┘
       │                     │                      │
       │ 1:N                 │ 1:N                  │ 1:N
       ▼                     ▼                      ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  evidence   │       │policy_results│      │policy_versions│
└─────────────┘       └─────────────┘       └─────────────┘
       │                                            │
       │ 1:N                                        │ 1:N
       ▼                                            ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ audit_logs  │       │gate_approvals│      │integrations │
└─────────────┘       └─────────────┘       └─────────────┘
                             │
                             │ N:1
                             ▼
                      ┌─────────────┐
                      │ai_contexts  │
                      └─────────────┘
```

**Key Relationships**:
- **C-Suite Approval Workflow**: users (CEO/CTO/CPO/CIO/CFO) → gate_approvals → gates
- **Multi-Approval Gates**: G0.2, G1, G2, G5, G9 require 2+ approvers (see Table 5a)
- **Stage Transitions**: gates → gate_approvals (all approvals = 'approved') → stage transition allowed

---

## Table 1: users

**Purpose**: User accounts and authentication.

**Schema**:
```sql
CREATE TABLE users (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email             VARCHAR(255) UNIQUE NOT NULL,
  password_hash     VARCHAR(255) NOT NULL, -- bcrypt hash
  role              VARCHAR(20) NOT NULL CHECK (role IN (
    -- C-Suite Leadership
    'ceo', 'cto', 'cpo', 'cio', 'cfo',
    -- Engineering Team
    'em', 'pm', 'dev_lead', 'qa_lead', 'security_lead', 'devops_lead', 'data_lead',
    -- Admin
    'admin'
  )),
  team_id           UUID NOT NULL REFERENCES teams(id),
  full_name         VARCHAR(255),
  avatar_url        VARCHAR(500),
  job_title         VARCHAR(100), -- e.g., "Chief Technology Officer", "Engineering Manager"
  department        VARCHAR(50), -- e.g., "Engineering", "Product", "Operations"
  created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMP NOT NULL DEFAULT NOW(),
  last_login_at     TIMESTAMP,
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,
  email_verified    BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_team_id ON users(team_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_department ON users(department);
```

**Relationships**:
- N:1 with teams (many users belong to one team)
- 1:N with audit_logs (one user has many audit logs)

**Constraints**:
- Email must be unique and valid format (validated in application layer)
- Role must be one of (SDLC 4.8 RBAC):
  - **C-Suite**: ceo, cto, cpo, cio, cfo
  - **Engineering**: em, pm, dev_lead, qa_lead, security_lead, devops_lead, data_lead
  - **Admin**: admin

---

## Table 2: teams

**Purpose**: Team/organization grouping.

**Schema**:
```sql
CREATE TABLE teams (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name              VARCHAR(255) NOT NULL,
  organization_id   UUID REFERENCES organizations(id),
  subscription_tier VARCHAR(20) NOT NULL CHECK (tier IN ('starter', 'growth', 'enterprise')),
  max_projects      INT NOT NULL DEFAULT 10,
  max_users         INT NOT NULL DEFAULT 50,
  storage_quota_gb  INT NOT NULL DEFAULT 10, -- Evidence Vault quota
  created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_teams_org_id ON teams(organization_id);
```

**Relationships**:
- 1:N with users (one team has many users)
- 1:N with projects (one team has many projects)
- N:1 with organizations (optional, for multi-team orgs)

**Business Rules**:
- Starter tier: 10 projects, 50 users, 10GB storage
- Growth tier: 50 projects, 200 users, 50GB storage
- Enterprise tier: Unlimited projects/users/storage

---

## Table 3: projects

**Purpose**: Projects (software products being developed).

**Schema**:
```sql
CREATE TABLE projects (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name              VARCHAR(255) NOT NULL,
  description       TEXT,
  team_id           UUID NOT NULL REFERENCES teams(id),
  created_by        UUID NOT NULL REFERENCES users(id),
  current_stage     VARCHAR(20) NOT NULL DEFAULT 'stage-00', -- stage-00 to stage-06
  status            VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'paused')),
  github_repo_url   VARCHAR(500),
  created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_projects_team_id ON projects(team_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_current_stage ON projects(current_stage);
```

**Relationships**:
- N:1 with teams (many projects belong to one team)
- 1:N with gates (one project has many gates)
- 1:N with features (one project has many features)
- N:M with users (project_users join table)

---

## Table 4: gates

**Purpose**: Gate definitions and current status.

**Schema**:
```sql
CREATE TABLE gates (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id        UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  gate_code         VARCHAR(20) NOT NULL, -- G0.1, G0.2, G1, G2, etc.
  gate_name         VARCHAR(255) NOT NULL, -- "Problem Definition", etc.
  stage             VARCHAR(20) NOT NULL, -- stage-00, stage-01, etc.
  status            VARCHAR(20) NOT NULL DEFAULT 'not_evaluated' CHECK (status IN ('not_evaluated', 'blocked', 'pending', 'passed')),
  is_blocking       BOOLEAN NOT NULL DEFAULT TRUE,
  last_evaluated_at TIMESTAMP,
  passed_at         TIMESTAMP,
  override_by       UUID REFERENCES users(id),
  override_reason   TEXT,
  override_expires  TIMESTAMP,
  created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMP NOT NULL DEFAULT NOW(),

  UNIQUE(project_id, gate_code)
);

CREATE INDEX idx_gates_project_id ON gates(project_id);
CREATE INDEX idx_gates_status ON gates(status);
CREATE INDEX idx_gates_stage ON gates(stage);
```

**Relationships**:
- N:1 with projects (many gates belong to one project)
- 1:N with gate_evaluations (one gate has many evaluations)
- 1:N with evidence (one gate has many evidence items)

**Business Rules**:
- Gate status: not_evaluated → pending → passed/blocked
- Override expires after 7 days (NFR, automated job)
- Override requires CTO role (RBAC check)

---

## Table 5: gate_evaluations

**Purpose**: History of gate evaluations.

**Schema**:
```sql
CREATE TABLE gate_evaluations (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gate_id           UUID NOT NULL REFERENCES gates(id) ON DELETE CASCADE,
  evaluated_by      UUID REFERENCES users(id),
  status            VARCHAR(20) NOT NULL CHECK (status IN ('blocked', 'pending', 'passed')),
  policies_checked  INT NOT NULL, -- Total number of policies evaluated
  policies_passed   INT NOT NULL, -- Number of policies that passed
  evaluation_time_ms INT NOT NULL, -- Performance tracking (NFR2)
  created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gate_evals_gate_id ON gate_evaluations(gate_id);
CREATE INDEX idx_gate_evals_created_at ON gate_evaluations(created_at DESC);
```

**Relationships**:
- N:1 with gates (many evaluations belong to one gate)
- 1:N with policy_results (one evaluation has many policy results)

**Performance**:
- Index on created_at DESC for recent evaluations query
- Partition by created_at (monthly) for large datasets (Year 3: 10M rows)

---

## Table 5a: gate_approvals

**Purpose**: Multi-approval workflow for quality gates (SDLC 4.8 Stages 00-09).

**Schema**:
```sql
CREATE TABLE gate_approvals (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gate_id           UUID NOT NULL REFERENCES gates(id) ON DELETE CASCADE,
  approver_id       UUID NOT NULL REFERENCES users(id),
  approver_role     VARCHAR(20) NOT NULL, -- ceo, cto, cpo, cio, cfo, etc.
  approval_status   VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
  approval_reason   TEXT, -- Required for rejection
  approved_at       TIMESTAMP,
  created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gate_approvals_gate_id ON gate_approvals(gate_id);
CREATE INDEX idx_gate_approvals_approver_id ON gate_approvals(approver_id);
CREATE INDEX idx_gate_approvals_status ON gate_approvals(approval_status);
```

**Relationships**:
- N:1 with gates (many approvals belong to one gate)
- N:1 with users (many approvals by one user)

**Business Rules** (SDLC 4.9 Complete Lifecycle - 10 Stages):
- **G0.1** (Problem Foundation): CPO + EM (2 approvals required)
- **G0.2** (Business Case): CEO + CPO (2 approvals required)
- **G1** (Requirements & Planning): CTO + CPO (2 approvals required)
- **G2** (Design & Architecture): CTO + Security Lead (2 approvals required)
- **G3** (Development): CTO + Dev Lead (2 approvals required)
- **G4** (Quality Assurance): CPO + QA Lead (2 approvals required)
- **G5** (Production Go-Live): CTO + CIO (2 approvals required)
- **G6** (Production Excellence): CIO + DevOps Lead (2 approvals required)
- **G7** (Systems Integration): CTO + Data Lead (2 approvals required)
- **G8** (Team Coordination): CPO + EM (2 approvals required)
- **G9** (Strategic Oversight): CEO + CFO (2 approvals required)

**Workflow**:
1. Gate evaluation passes (status = 'passed')
2. System creates gate_approvals records (status = 'pending') for required approvers
3. Approvers review and approve/reject
4. Gate transitions to next stage only when ALL required approvals = 'approved'

**Acceptance Criteria**:
```gherkin
Given gate G1 evaluation passes
When system creates approval workflow
Then 2 gate_approvals records created:
  - approver_role = 'cto', status = 'pending'
  - approver_role = 'cpo', status = 'pending'

Given CTO approves G1
When CPO also approves G1
Then gate status = 'approved'
And stage transition allowed (Stage 01 → Stage 02)

Given CTO approves G1
When CPO rejects G1 (approval_reason = "Missing NFR1-3 performance metrics")
Then gate status = 'blocked'
And stage transition NOT allowed
And EM receives notification with rejection reason
```

---

## Table 6: policies

**Purpose**: Policy pack definitions (Rego code).

**Schema**:
```sql
CREATE TABLE policies (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_code       VARCHAR(100) UNIQUE NOT NULL, -- policy-pack-user-interviews
  policy_name       VARCHAR(255) NOT NULL,
  description       TEXT,
  rego_code         TEXT NOT NULL, -- Rego policy logic
  stage             VARCHAR(20) NOT NULL, -- stage-00, stage-01, etc.
  category          VARCHAR(50), -- validation, security, performance, etc.
  is_pre_built      BOOLEAN NOT NULL DEFAULT FALSE, -- Pre-built vs custom
  created_by        UUID REFERENCES users(id),
  current_version   VARCHAR(20) NOT NULL DEFAULT '1.0.0', -- Semantic versioning
  created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_policies_stage ON policies(stage);
CREATE INDEX idx_policies_category ON policies(category);
CREATE INDEX idx_policies_is_pre_built ON policies(is_pre_built);
```

**Relationships**:
- 1:N with policy_versions (one policy has many versions)
- N:M with gates (via gate_policies join table)

**Business Rules**:
- Pre-built policies (is_pre_built=true) cannot be deleted
- Rego code validated before save (OPA syntax check)
- Policy versioning follows semantic versioning (1.0.0, 1.1.0, 2.0.0)

---

## Table 7: evidence

**Purpose**: Evidence files and metadata.

**Schema**:
```sql
CREATE TABLE evidence (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id        UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  gate_id           UUID REFERENCES gates(id),
  evidence_type     VARCHAR(50) NOT NULL CHECK (type IN ('manual_upload', 'slack_message', 'github_pr', 'github_issue', 'figma_file', 'zoom_transcript')),
  file_path         VARCHAR(500), -- MinIO S3 path
  file_size_bytes   BIGINT,
  file_mime_type    VARCHAR(100),
  source_url        VARCHAR(500), -- Original URL (Slack, GitHub, etc.)
  content_preview   TEXT, -- First 1000 chars for search
  uploaded_by       UUID REFERENCES users(id),
  created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
  indexed_at        TIMESTAMP -- Full-text search index timestamp
);

CREATE INDEX idx_evidence_project_id ON evidence(project_id);
CREATE INDEX idx_evidence_gate_id ON evidence(gate_id);
CREATE INDEX idx_evidence_type ON evidence(evidence_type);
CREATE INDEX idx_evidence_created_at ON evidence(created_at DESC);

-- Full-text search index (PostgreSQL pg_trgm)
CREATE INDEX idx_evidence_content_search ON evidence USING gin(to_tsvector('english', content_preview));
```

**Relationships**:
- N:1 with projects (many evidence belong to one project)
- N:1 with gates (many evidence belong to one gate, optional)
- N:1 with users (uploaded_by)

**Storage**:
- Files stored in MinIO (S3-compatible)
- file_path format: `evidence-vault/{team_id}/{project_id}/{gate_id}/{filename}`
- Max file size: 10MB (enforced in application layer)

**Performance**:
- Full-text search using PostgreSQL pg_trgm (trigram matching)
- Search query: `WHERE to_tsvector('english', content_preview) @@ plainto_tsquery('user interview')`

---

## Table 8: audit_logs

**Purpose**: Audit trail for compliance (SOC 2, GDPR).

**Schema**:
```sql
CREATE TABLE audit_logs (
  id                BIGSERIAL PRIMARY KEY, -- Bigserial for high-volume inserts
  user_id           UUID REFERENCES users(id),
  action            VARCHAR(50) NOT NULL, -- view, download, delete, override, etc.
  resource_type     VARCHAR(50) NOT NULL, -- evidence, gate, policy, user, etc.
  resource_id       UUID,
  ip_address        INET,
  user_agent        TEXT,
  metadata          JSONB, -- Additional context (e.g., override reason)
  created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_resource_type_id ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Partition by created_at (monthly) for performance
CREATE TABLE audit_logs_2025_01 PARTITION OF audit_logs
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

**Relationships**:
- N:1 with users (many logs belong to one user)

**Business Rules**:
- Append-only (no UPDATE/DELETE allowed)
- Retained 7 years (NFR17, compliance requirement)
- Partition by month for performance (Year 3: 100M rows)

**Performance**:
- Partitioning by month reduces query time (scan only relevant partition)
- Index on created_at DESC for recent logs query

---

## Table 9: integrations

**Purpose**: External integrations (Slack, GitHub, Figma, etc.).

**Schema**:
```sql
CREATE TABLE integrations (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id           UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  integration_type  VARCHAR(50) NOT NULL CHECK (type IN ('slack', 'github', 'jira', 'figma', 'zoom')),
  is_enabled        BOOLEAN NOT NULL DEFAULT TRUE,
  oauth_token       TEXT, -- Encrypted OAuth token
  config            JSONB, -- Integration-specific config (channels, repos, etc.)
  last_sync_at      TIMESTAMP,
  created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMP NOT NULL DEFAULT NOW(),

  UNIQUE(team_id, integration_type)
);

CREATE INDEX idx_integrations_team_id ON integrations(team_id);
CREATE INDEX idx_integrations_type ON integrations(integration_type);
```

**Relationships**:
- N:1 with teams (many integrations belong to one team)

**Security**:
- oauth_token encrypted with AES-256 (application layer)
- config JSONB stores integration-specific settings:
  - Slack: `{"channels": ["#product", "#design"], "keywords": ["user interview"]}`
  - GitHub: `{"repos": ["org/repo1", "org/repo2"], "events": ["pull_request", "issue"]}`

---

## Table 10: ai_contexts

**Purpose**: AI conversation history and context.

**Schema**:
```sql
CREATE TABLE ai_contexts (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id        UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id           UUID NOT NULL REFERENCES users(id),
  stage             VARCHAR(20) NOT NULL, -- stage-00, stage-01, etc.
  prompt            TEXT NOT NULL,
  response          TEXT NOT NULL,
  ai_provider       VARCHAR(20) NOT NULL CHECK (provider IN ('claude', 'gpt4o', 'gemini')),
  tokens_used       INT, -- Cost tracking
  response_time_ms  INT, -- Performance tracking
  created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ai_contexts_project_id ON ai_contexts(project_id);
CREATE INDEX idx_ai_contexts_user_id ON ai_contexts(user_id);
CREATE INDEX idx_ai_contexts_created_at ON ai_contexts(created_at DESC);
```

**Relationships**:
- N:1 with projects (many AI contexts belong to one project)
- N:1 with users (many AI contexts belong to one user)

**Business Rules**:
- Conversation history retained 30 days (auto-delete old records)
- tokens_used tracked for cost monitoring (target: <$350/month)

---

## Data Dictionary (Key Fields)

### Enumerated Types

**user.role**:
- `em`: Engineering Manager (60% of users)
- `cto`: CTO (30% of users)
- `pm`: Product Manager (10% of users)
- `admin`: System Admin (internal only)

**gate.status**:
- `not_evaluated`: Initial state (no evaluation yet)
- `pending`: Missing evidence (cannot determine pass/fail)
- `blocked`: Policy failed (cannot proceed)
- `passed`: All policies passed

**evidence.evidence_type**:
- `manual_upload`: User uploaded file (PDF, PNG, etc.)
- `slack_message`: Auto-collected from Slack
- `github_pr`: Auto-collected from GitHub PR
- `github_issue`: Auto-collected from GitHub issue
- `figma_file`: Auto-collected from Figma
- `zoom_transcript`: Auto-collected from Zoom recording

---

## Database Sizing (Year 3 Projections)

### Table Row Counts

| Table | Year 1 | Year 2 | Year 3 | Growth |
|-------|--------|--------|--------|--------|
| users | 500 | 2,000 | 7,000 | 14x |
| teams | 100 | 454 | 1,342 | 13x |
| projects | 300 | 1,362 | 4,026 | 13x |
| gates | 2,400 | 10,896 | 32,208 | 13x |
| gate_evaluations | 24K | 109K | 322K | 13x |
| evidence | 30K | 136K | 403K | 13x |
| audit_logs | 500K | 2.2M | 6.7M | 13x |
| ai_contexts | 10K | 45K | 134K | 13x |

**Total Database Size**:
- Year 1: ~500MB
- Year 2: ~2GB
- Year 3: ~6GB (database only, excluding evidence files in MinIO)

### MinIO Storage

| Year | Teams | Storage/Team | Total |
|------|-------|--------------|-------|
| Year 1 | 100 | 10GB | **1TB** |
| Year 2 | 454 | 10GB | **4.5TB** |
| Year 3 | 1,342 | 10GB | **13TB** |

**Cost** (if AWS S3): 13TB × $23/TB = $299/month (Year 3)
**Cost** (MinIO self-hosted): $0/month (infrastructure only: ~$100/month)

---

## Performance Optimizations

### Indexes

**Critical Indexes** (query <200ms, NFR1):
1. `idx_users_email` - Login query (millions/day)
2. `idx_gates_project_id` - Dashboard query (thousands/day)
3. `idx_evidence_content_search` - Full-text search (hundreds/day)
4. `idx_audit_logs_created_at` - Recent logs query (hundreds/day)

**Composite Indexes** (multi-column queries):
```sql
CREATE INDEX idx_gates_project_status ON gates(project_id, status);
CREATE INDEX idx_evidence_project_gate ON evidence(project_id, gate_id);
```

### Partitioning

**audit_logs** partitioned by month:
- Query recent logs (last 30 days) = scan 1 partition only
- Query old logs (7 years) = scan multiple partitions (slower, acceptable)

**gate_evaluations** partitioned by created_at (future optimization):
- Year 3: 322K rows → partition by quarter (80K rows/partition)

---

## Database Migrations Strategy

### Migration Tools
- **Alembic** (Python, SQLAlchemy ORM)
- Migrations versioned in Git (`/backend/migrations/`)

### Migration Example
```python
# migration: add_gate_override_fields.py (2025-01-20)
def upgrade():
    op.add_column('gates', sa.Column('override_by', sa.UUID()))
    op.add_column('gates', sa.Column('override_reason', sa.Text()))
    op.add_column('gates', sa.Column('override_expires', sa.TIMESTAMP()))

def downgrade():
    op.drop_column('gates', 'override_expires')
    op.drop_column('gates', 'override_reason')
    op.drop_column('gates', 'override_by')
```

### Migration Testing
- Test migrations on staging before production
- Backup database before migration (automated, RDS snapshots)
- Rollback plan (downgrade migration + restore backup)

---

## Document Control

**Version History**:
- v1.0.0 (January 13, 2025): Initial data model (15 tables)

**Related Documents**:
- [FRD](../01-Requirements/Functional-Requirements-Document.md)
- [NFR](../01-Requirements/Non-Functional-Requirements.md)

---

**End of Data Model v1.0.0**
