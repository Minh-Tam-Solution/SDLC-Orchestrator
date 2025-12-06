# Database Schema (SQL Migrations)
## PostgreSQL 15.5 Schema Definitions

**Version**: 2.0.0
**Date**: December 3, 2025
**Status**: ACTIVE - AI Governance Extension
**Authority**: Backend Lead + CTO Review (APPROVED)
**Foundation**: Data Model ERD v2.0 (with AI Governance)
**Stage**: Stage 01 (WHAT - Planning & Analysis)

**Changelog v2.0.0** (Dec 3, 2025):
- Added Migration 006: AI Governance Tables (stage_requirements, requirement_overrides)
- Added Migration 007: Task Decomposition Tables (decomposed_tasks, decomposition_sessions)
- Added Migration 008: Planning Hierarchy Tables (roadmaps, phases, sprints, backlog_items)
- Updated table count: 16 → 25 tables

---

## Document Purpose

This document defines **WHAT database schema to create** using SQL migration scripts (Alembic/Flyway format).

**Key Sections**:
- Schema creation (25 tables - extended for AI Governance)
- Indexes (30+ for performance)
- Foreign keys (data integrity)
- Partitioning (audit_logs by month)
- Initial seed data (C-Suite roles, pre-built policies)
- AI Governance tables (context-aware requirements, task decomposition, planning hierarchy)

---

## Migration 001: Create Core Tables (Users, Teams, Organizations)

```sql
-- Migration: 001_create_core_tables.sql
-- Description: Create users, teams, organizations tables
-- Author: Backend Lead
-- Date: 2025-01-13

-- Table: organizations
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_name VARCHAR(255) NOT NULL,
  subscription_tier VARCHAR(20) NOT NULL CHECK (subscription_tier IN ('free', 'pro', 'enterprise')),
  max_projects INT NOT NULL DEFAULT 10,
  max_users INT NOT NULL DEFAULT 50,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_organizations_subscription_tier ON organizations(subscription_tier);

-- Table: teams
CREATE TABLE teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_name VARCHAR(255) NOT NULL,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_teams_organization_id ON teams(organization_id);

-- Table: users (with C-Suite roles)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL CHECK (role IN (
    -- C-Suite Leadership
    'ceo', 'cto', 'cpo', 'cio', 'cfo',
    -- Engineering Team
    'em', 'pm', 'dev_lead', 'qa_lead', 'security_lead', 'devops_lead', 'data_lead',
    -- Admin
    'admin'
  )),
  team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  full_name VARCHAR(255),
  avatar_url VARCHAR(500),
  job_title VARCHAR(100),
  department VARCHAR(50),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  last_login_at TIMESTAMP,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  email_verified BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_team_id ON users(team_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_department ON users(department);

-- Seed data: Admin user
INSERT INTO organizations (org_name, subscription_tier, max_projects, max_users)
VALUES ('System', 'enterprise', 1000, 1000);

INSERT INTO teams (team_name, organization_id)
VALUES ('Admin Team', (SELECT id FROM organizations WHERE org_name = 'System'));

INSERT INTO users (email, password_hash, role, team_id, full_name, job_title, department)
VALUES (
  'admin@sdlc-orchestrator.com',
  '$2b$12$...',  -- bcrypt hash (to be replaced in production)
  'admin',
  (SELECT id FROM teams WHERE team_name = 'Admin Team'),
  'System Administrator',
  'Admin',
  'Operations'
);
```

---

## Migration 002: Create Project & Gate Tables

```sql
-- Migration: 002_create_project_gate_tables.sql

-- Table: projects
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_name VARCHAR(255) NOT NULL,
  project_code VARCHAR(100) UNIQUE NOT NULL,
  description TEXT,
  current_stage VARCHAR(20) NOT NULL DEFAULT 'stage-00' CHECK (stage IN (
    'stage-00', 'stage-01', 'stage-02', 'stage-03', 'stage-04',
    'stage-05', 'stage-06', 'stage-07', 'stage-08', 'stage-09'
  )),
  team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_projects_team_id ON projects(team_id);
CREATE INDEX idx_projects_current_stage ON projects(current_stage);
CREATE INDEX idx_projects_created_by ON projects(created_by);

-- Table: gates
CREATE TABLE gates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  gate_code VARCHAR(20) NOT NULL,  -- G0.1, G0.2, G1, G2, etc.
  gate_name VARCHAR(255) NOT NULL,
  stage VARCHAR(20) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'not_evaluated' CHECK (status IN (
    'not_evaluated', 'pending', 'blocked', 'passed', 'override'
  )),
  override_reason TEXT,
  override_by UUID REFERENCES users(id),
  override_at TIMESTAMP,
  override_expires_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  evaluated_at TIMESTAMP
);

CREATE INDEX idx_gates_project_id ON gates(project_id);
CREATE INDEX idx_gates_status ON gates(status);
CREATE INDEX idx_gates_stage ON gates(stage);

-- Table: gate_approvals (multi-approval workflow)
CREATE TABLE gate_approvals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gate_id UUID NOT NULL REFERENCES gates(id) ON DELETE CASCADE,
  approver_id UUID NOT NULL REFERENCES users(id),
  approver_role VARCHAR(20) NOT NULL,
  approval_status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
  approval_reason TEXT,
  approved_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gate_approvals_gate_id ON gate_approvals(gate_id);
CREATE INDEX idx_gate_approvals_approver_id ON gate_approvals(approver_id);
CREATE INDEX idx_gate_approvals_status ON gate_approvals(approval_status);
```

---

## Migration 003: Create Evidence & Policy Tables

```sql
-- Migration: 003_create_evidence_policy_tables.sql

-- Enable PostgreSQL extensions for full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Table: evidence
CREATE TABLE evidence (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  gate_id UUID REFERENCES gates(id),
  evidence_type VARCHAR(50) NOT NULL CHECK (type IN (
    'manual_upload', 'slack_message', 'github_pr', 'github_issue', 'figma_file', 'zoom_transcript'
  )),
  file_path VARCHAR(500),
  file_size_bytes BIGINT,
  file_mime_type VARCHAR(100),
  source_url VARCHAR(500),
  content_preview TEXT,
  uploaded_by UUID REFERENCES users(id),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  indexed_at TIMESTAMP
);

CREATE INDEX idx_evidence_project_id ON evidence(project_id);
CREATE INDEX idx_evidence_gate_id ON evidence(gate_id);
CREATE INDEX idx_evidence_type ON evidence(evidence_type);
CREATE INDEX idx_evidence_uploaded_by ON evidence(uploaded_by);

-- Full-text search index (PostgreSQL pg_trgm)
CREATE INDEX idx_evidence_content_search ON evidence USING gin(to_tsvector('english', content_preview));

-- Table: policies
CREATE TABLE policies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_code VARCHAR(100) UNIQUE NOT NULL,
  policy_name VARCHAR(255) NOT NULL,
  description TEXT,
  rego_code TEXT NOT NULL,
  stage VARCHAR(20) NOT NULL,
  category VARCHAR(50),
  is_pre_built BOOLEAN NOT NULL DEFAULT FALSE,
  created_by UUID REFERENCES users(id),
  current_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_policies_stage ON policies(stage);
CREATE INDEX idx_policies_category ON policies(category);
CREATE INDEX idx_policies_is_pre_built ON policies(is_pre_built);

-- Seed data: Pre-built policy packs (Stage 00)
INSERT INTO policies (policy_code, policy_name, description, rego_code, stage, category, is_pre_built)
VALUES
  (
    'policy-pack-user-interviews',
    'User Interviews (3+ required)',
    'Validates that 3+ user interviews conducted (Stage 00, G0.1)',
    'package policy_pack_user_interviews
default allow = false
allow {
  count(input.evidence) >= 3
  input.evidence[_].type == "user_interview"
}
deny[msg] {
  count(input.evidence) < 3
  msg := sprintf("Insufficient user interviews. Found: %d, Required: 3+", [count(input.evidence)])
}',
    'stage-00',
    'validation',
    true
  ),
  (
    'policy-pack-problem-statement',
    'Problem Statement Validated',
    'Validates that problem statement exists and pain level >=7/10 (Stage 00, G0.1)',
    'package policy_pack_problem_statement
default allow = false
allow {
  input.problem_statement != ""
  input.pain_level >= 7
}
deny[msg] {
  input.problem_statement == ""
  msg := "Problem statement missing. Please document validated problem."
}',
    'stage-00',
    'validation',
    true
  );
```

---

## Migration 004: Create Audit Log (Partitioned by Month)

```sql
-- Migration: 004_create_audit_logs_partitioned.sql

-- Table: audit_logs (partitioned by month for scalability)
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  action VARCHAR(50) NOT NULL,  -- upload, download, delete, override, approve, reject
  resource_type VARCHAR(50) NOT NULL,  -- evidence, gate, policy, user
  resource_id UUID,
  metadata JSONB,  -- Additional context (IP address, user agent, etc.)
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Create partitions for Year 2025 (monthly)
CREATE TABLE audit_logs_2025_01 PARTITION OF audit_logs
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE audit_logs_2025_02 PARTITION OF audit_logs
  FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

CREATE TABLE audit_logs_2025_03 PARTITION OF audit_logs
  FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');

-- Continue creating partitions up to 2025-12...

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
```

---

## Migration 005: Create Integration Tables

```sql
-- Migration: 005_create_integration_tables.sql

-- Table: integrations
CREATE TABLE integrations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  integration_type VARCHAR(50) NOT NULL CHECK (type IN (
    'slack', 'github', 'figma', 'zoom', 'jira', 'linear'
  )),
  oauth_token TEXT,  -- Encrypted OAuth token
  oauth_refresh_token TEXT,
  config JSONB,  -- Integration-specific config (channel IDs, repo URLs, etc.)
  status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'error')),
  last_sync_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_integrations_team_id ON integrations(team_id);
CREATE INDEX idx_integrations_type ON integrations(integration_type);
CREATE INDEX idx_integrations_status ON integrations(status);
```

---

## Migration 006: AI Governance - Context-Aware Requirements

*(Added in v2.0.0 - December 3, 2025)*

```sql
-- Migration: 006_create_context_aware_requirements.sql
-- Description: Context-aware stage requirements with 3-tier classification
-- Author: Backend Lead + AI Governance Team
-- Date: 2025-12-03

-- Table: project_context_profiles (5 context dimensions)
CREATE TABLE project_context_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

  -- Context Dimensions
  project_scale VARCHAR(20) NOT NULL CHECK (project_scale IN ('startup', 'scaleup', 'enterprise')),
  team_structure VARCHAR(20) NOT NULL CHECK (team_structure IN ('solo', 'small', 'medium', 'large', 'distributed')),
  industry VARCHAR(50) NOT NULL, -- fintech, healthcare, edtech, ecommerce, etc.
  risk_profile VARCHAR(20) NOT NULL CHECK (risk_profile IN ('low', 'medium', 'high', 'critical')),
  dev_practices VARCHAR(30) NOT NULL CHECK (dev_practices IN ('waterfall', 'agile', 'hybrid', 'continuous')),

  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

  CONSTRAINT unique_project_profile UNIQUE (project_id)
);

CREATE INDEX idx_context_profiles_project ON project_context_profiles(project_id);
CREATE INDEX idx_context_profiles_scale ON project_context_profiles(project_scale);
CREATE INDEX idx_context_profiles_risk ON project_context_profiles(risk_profile);

-- Table: stage_requirements (base requirements per stage)
CREATE TABLE stage_requirements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  stage VARCHAR(20) NOT NULL,  -- stage-00 through stage-09
  requirement_code VARCHAR(50) NOT NULL,  -- FR-01.01, NFR-02.03, etc.
  requirement_name VARCHAR(255) NOT NULL,
  description TEXT,
  default_tier VARCHAR(20) NOT NULL CHECK (default_tier IN ('mandatory', 'recommended', 'optional')),
  category VARCHAR(50),  -- validation, security, performance, compliance

  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

  CONSTRAINT unique_stage_requirement UNIQUE (stage, requirement_code)
);

CREATE INDEX idx_stage_requirements_stage ON stage_requirements(stage);
CREATE INDEX idx_stage_requirements_tier ON stage_requirements(default_tier);

-- Table: context_rules (dynamic tier classification rules)
CREATE TABLE context_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  requirement_id UUID NOT NULL REFERENCES stage_requirements(id) ON DELETE CASCADE,

  -- Rule conditions (JSON for flexibility)
  condition_expression JSONB NOT NULL,
  -- Example: {"project_scale": "enterprise", "risk_profile": "high"}

  resulting_tier VARCHAR(20) NOT NULL CHECK (resulting_tier IN ('mandatory', 'recommended', 'optional')),
  priority INT NOT NULL DEFAULT 0,  -- Higher priority rules evaluated first

  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_context_rules_requirement ON context_rules(requirement_id);
CREATE INDEX idx_context_rules_tier ON context_rules(resulting_tier);

-- Table: requirement_overrides (user overrides with audit)
CREATE TABLE requirement_overrides (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  requirement_id UUID NOT NULL REFERENCES stage_requirements(id) ON DELETE CASCADE,

  original_tier VARCHAR(20) NOT NULL,
  new_tier VARCHAR(20) NOT NULL CHECK (new_tier IN ('mandatory', 'recommended', 'optional')),
  override_reason TEXT NOT NULL,

  overridden_by UUID NOT NULL REFERENCES users(id),
  approved_by UUID REFERENCES users(id),  -- Required for mandatory → optional
  approval_status VARCHAR(20) DEFAULT 'pending' CHECK (approval_status IN ('pending', 'approved', 'rejected')),

  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMP,  -- Optional expiration

  CONSTRAINT unique_project_requirement_override UNIQUE (project_id, requirement_id)
);

CREATE INDEX idx_overrides_project ON requirement_overrides(project_id);
CREATE INDEX idx_overrides_requirement ON requirement_overrides(requirement_id);
CREATE INDEX idx_overrides_status ON requirement_overrides(approval_status);

-- Seed: Default stage requirements (Stage 00 - WHY)
INSERT INTO stage_requirements (stage, requirement_code, requirement_name, description, default_tier, category)
VALUES
  ('stage-00', 'FR-00.01', 'Problem Statement Document', 'Documented validated problem with pain level ≥7/10', 'mandatory', 'validation'),
  ('stage-00', 'FR-00.02', 'User Interview Evidence', 'Minimum 3 user interviews conducted', 'mandatory', 'validation'),
  ('stage-00', 'FR-00.03', 'Market Research Report', 'TAM/SAM/SOM analysis completed', 'recommended', 'validation'),
  ('stage-00', 'FR-00.04', 'Competitive Analysis', 'Analysis of 5+ competitors', 'optional', 'validation'),
  ('stage-00', 'FR-00.05', 'Solution Hypothesis', 'Documented solution approach', 'mandatory', 'validation');
```

---

## Migration 007: AI Governance - Task Decomposition

*(Added in v2.0.0 - December 3, 2025)*

```sql
-- Migration: 007_create_task_decomposition.sql
-- Description: AI-powered user story decomposition tracking
-- Author: Backend Lead + AI Governance Team
-- Date: 2025-12-03

-- Table: decomposition_sessions (AI decomposition audit)
CREATE TABLE decomposition_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_story_id UUID,  -- Optional link to external story

  -- Input
  original_story TEXT NOT NULL,
  context_data JSONB,  -- Project context, dependencies, etc.

  -- AI Processing
  ai_provider VARCHAR(20) NOT NULL CHECK (ai_provider IN ('ollama', 'claude', 'gpt4', 'rule_based')),
  model_version VARCHAR(50),
  prompt_template VARCHAR(100),

  -- Output
  decomposition_result JSONB NOT NULL,  -- Array of tasks
  completeness_score DECIMAL(5,2),  -- 0-100%
  tokens_used INT,
  cost_usd DECIMAL(10,4),
  processing_time_ms INT,

  -- Status
  status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'approved', 'rejected')),
  error_message TEXT,

  created_by UUID NOT NULL REFERENCES users(id),
  reviewed_by UUID REFERENCES users(id),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMP
);

CREATE INDEX idx_decomp_sessions_project ON decomposition_sessions(project_id);
CREATE INDEX idx_decomp_sessions_status ON decomposition_sessions(status);
CREATE INDEX idx_decomp_sessions_provider ON decomposition_sessions(ai_provider);
CREATE INDEX idx_decomp_sessions_created_by ON decomposition_sessions(created_by);

-- Table: decomposed_tasks (individual tasks from decomposition)
CREATE TABLE decomposed_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES decomposition_sessions(id) ON DELETE CASCADE,

  -- Task details
  task_title VARCHAR(255) NOT NULL,
  task_description TEXT,
  task_type VARCHAR(30) NOT NULL CHECK (task_type IN ('development', 'testing', 'documentation', 'review', 'deployment', 'research')),

  -- Estimates
  estimated_hours DECIMAL(5,2),
  complexity VARCHAR(20) CHECK (complexity IN ('trivial', 'simple', 'medium', 'complex', 'very_complex')),

  -- Dependencies
  depends_on_task_ids UUID[],  -- Array of task IDs

  -- Acceptance criteria
  acceptance_criteria JSONB,  -- Array of criteria

  -- Tracking
  sequence_order INT NOT NULL,
  is_approved BOOLEAN DEFAULT FALSE,
  approved_by UUID REFERENCES users(id),

  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_decomposed_tasks_session ON decomposed_tasks(session_id);
CREATE INDEX idx_decomposed_tasks_type ON decomposed_tasks(task_type);
CREATE INDEX idx_decomposed_tasks_approved ON decomposed_tasks(is_approved);
```

---

## Migration 008: AI Governance - Planning Hierarchy

*(Added in v2.0.0 - December 3, 2025)*

```sql
-- Migration: 008_create_planning_hierarchy.sql
-- Description: 4-level planning hierarchy (Roadmap → Phase → Sprint → Backlog)
-- Author: Backend Lead + AI Governance Team
-- Date: 2025-12-03

-- Table: roadmaps (Level 1 - Strategic Vision)
CREATE TABLE roadmaps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

  -- Roadmap details
  roadmap_name VARCHAR(255) NOT NULL,
  version VARCHAR(20) NOT NULL,  -- v1.0.0, v2.0.0, etc.
  vision_statement TEXT NOT NULL,

  -- Timeline
  start_date DATE NOT NULL,
  target_end_date DATE NOT NULL,

  -- Status
  status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'completed', 'archived')),

  -- Objectives (OKRs)
  objectives JSONB,  -- Array of {objective, key_results[]}

  created_by UUID NOT NULL REFERENCES users(id),
  approved_by UUID REFERENCES users(id),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_roadmaps_project ON roadmaps(project_id);
CREATE INDEX idx_roadmaps_status ON roadmaps(status);

-- Table: phases (Level 2 - Quarterly/Monthly Milestones)
CREATE TABLE phases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  roadmap_id UUID NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,

  -- Phase details
  phase_name VARCHAR(255) NOT NULL,
  phase_number INT NOT NULL,  -- PHASE-01, PHASE-02, etc.
  description TEXT,

  -- Scope
  theme VARCHAR(100),  -- "MVP Core Features", "Security Hardening", etc.
  success_criteria JSONB,  -- Array of measurable criteria

  -- Timeline
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,

  -- Status
  status VARCHAR(20) NOT NULL DEFAULT 'planned' CHECK (status IN ('planned', 'in_progress', 'completed', 'blocked', 'cancelled')),
  progress_percentage DECIMAL(5,2) DEFAULT 0,

  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_phases_roadmap ON phases(roadmap_id);
CREATE INDEX idx_phases_status ON phases(status);
CREATE INDEX idx_phases_number ON phases(phase_number);

-- Table: sprints (Level 3 - Weekly Iterations)
CREATE TABLE sprints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phase_id UUID NOT NULL REFERENCES phases(id) ON DELETE CASCADE,

  -- Sprint details
  sprint_name VARCHAR(255) NOT NULL,
  sprint_number INT NOT NULL,  -- SPRINT-01, SPRINT-02, etc.
  goal TEXT,

  -- Timeline
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  duration_days INT NOT NULL DEFAULT 7,

  -- Capacity
  planned_story_points INT,
  completed_story_points INT DEFAULT 0,
  velocity DECIMAL(5,2),

  -- Status
  status VARCHAR(20) NOT NULL DEFAULT 'planned' CHECK (status IN ('planned', 'active', 'completed', 'cancelled')),

  -- Retrospective
  retrospective JSONB,  -- {what_went_well[], what_needs_improvement[], action_items[]}

  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sprints_phase ON sprints(phase_id);
CREATE INDEX idx_sprints_status ON sprints(status);
CREATE INDEX idx_sprints_dates ON sprints(start_date, end_date);

-- Table: backlog_items (Level 4 - Daily Tasks)
CREATE TABLE backlog_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sprint_id UUID REFERENCES sprints(id) ON DELETE SET NULL,  -- Can be unassigned
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

  -- Item details
  item_type VARCHAR(20) NOT NULL CHECK (item_type IN ('epic', 'story', 'task', 'bug', 'spike', 'chore')),
  title VARCHAR(255) NOT NULL,
  description TEXT,

  -- Hierarchy
  parent_item_id UUID REFERENCES backlog_items(id),  -- For epic → story → task

  -- Estimation
  story_points INT,
  estimated_hours DECIMAL(5,2),
  actual_hours DECIMAL(5,2),

  -- Priority & Status
  priority VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK (priority IN ('critical', 'high', 'medium', 'low')),
  status VARCHAR(20) NOT NULL DEFAULT 'backlog' CHECK (status IN ('backlog', 'ready', 'in_progress', 'in_review', 'done', 'blocked', 'cancelled')),

  -- Assignment
  assignee_id UUID REFERENCES users(id),
  reviewer_id UUID REFERENCES users(id),

  -- Traceability
  linked_decomposition_task_id UUID REFERENCES decomposed_tasks(id),
  linked_requirement_id UUID REFERENCES stage_requirements(id),

  -- Labels & Tags
  labels JSONB,  -- Array of labels

  created_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMP
);

CREATE INDEX idx_backlog_sprint ON backlog_items(sprint_id);
CREATE INDEX idx_backlog_project ON backlog_items(project_id);
CREATE INDEX idx_backlog_type ON backlog_items(item_type);
CREATE INDEX idx_backlog_status ON backlog_items(status);
CREATE INDEX idx_backlog_priority ON backlog_items(priority);
CREATE INDEX idx_backlog_assignee ON backlog_items(assignee_id);
CREATE INDEX idx_backlog_parent ON backlog_items(parent_item_id);

-- Recursive CTE index for traceability queries
CREATE INDEX idx_backlog_traceability ON backlog_items(linked_decomposition_task_id, linked_requirement_id);
```

---

## Data Sizing Projections (Year 3)

| Table | Rows (Year 3) | Storage | Notes |
|-------|--------------|---------|-------|
| users | 13,420 | 10MB | 1,342 teams × 10 users/team |
| teams | 1,342 | 1MB | 1,342 teams |
| organizations | 670 | 0.5MB | 1,342 teams / 2 teams per org |
| projects | 6,710 | 50MB | 1,342 teams × 5 projects/team |
| gates | 53,680 | 200MB | 6,710 projects × 8 gates |
| gate_approvals | 107,360 | 300MB | 53,680 gates × 2 approvals (avg) |
| evidence | 67,100,000 | 500MB | 6,710 projects × 10K evidence/project |
| policies | 1,000 | 10MB | 100 pre-built + 900 custom |
| audit_logs | 100,000,000 | 5GB | All user actions logged |
| integrations | 4,026 | 20MB | 1,342 teams × 3 integrations/team |
| **AI Governance Tables** *(v2.0)* | | | |
| project_context_profiles | 6,710 | 5MB | 1 per project |
| stage_requirements | 500 | 2MB | 50 per stage × 10 stages |
| context_rules | 2,500 | 5MB | 5 rules per requirement |
| requirement_overrides | 33,550 | 10MB | 5% of project-requirements |
| decomposition_sessions | 335,500 | 100MB | 50 stories/project/year |
| decomposed_tasks | 1,677,500 | 200MB | 5 tasks/session |
| roadmaps | 6,710 | 5MB | 1 per project |
| phases | 26,840 | 10MB | 4 phases/roadmap |
| sprints | 348,920 | 50MB | 13 sprints/phase |
| backlog_items | 3,489,200 | 500MB | 10 items/sprint |
| **TOTAL** | **172M rows** | **7GB** | PostgreSQL only (MinIO: 13TB) |

---

## Performance Optimizations

1. **Indexes**: 20+ indexes for common queries (<200ms, NFR1)
2. **Partitioning**: audit_logs by month (Year 3: 558K rows/partition vs 6.7M total)
3. **Full-Text Search**: pg_trgm extension (trigram matching, typo tolerance)
4. **Foreign Keys**: CASCADE for data integrity (delete project → cascade delete gates/evidence)
5. **Connection Pooling**: PgBouncer (1K connections, NFR6)
6. **Read Replicas**: 2x read replicas (NFR12: 99.9% uptime)

---

## References

- [Data Model ERD](./Data-Model-ERD.md)
- [Non-Functional Requirements](../01-Requirements/Non-Functional-Requirements.md) (v2.0.0)
- [ADR-011-Context-Aware-Requirements](../../02-Design-Architecture/01-System-Architecture/Architecture-Decisions/ADR-011-Context-Aware-Requirements.md)
- [ADR-012-AI-Task-Decomposition](../../02-Design-Architecture/01-System-Architecture/Architecture-Decisions/ADR-012-AI-Task-Decomposition.md)
- [ADR-013-Planning-Hierarchy](../../02-Design-Architecture/01-System-Architecture/Architecture-Decisions/ADR-013-Planning-Hierarchy.md)

---

**Last Updated**: 2025-12-03
**Owner**: Backend Lead + CTO
**Status**: ✅ APPROVED (AI Governance Extension)

**Version History**:
- v2.0.0 (Dec 3, 2025): Added Migrations 006-008 for AI Governance (25 tables)
- v1.0.0 (Jan 13, 2025): Initial schema (16 tables)

---

**End of Database Schema v2.0.0**
