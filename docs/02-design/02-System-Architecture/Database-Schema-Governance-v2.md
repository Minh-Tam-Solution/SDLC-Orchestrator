# Database Schema Design - Governance System v2.0
## SPEC-0001/0002 Automation Layer (14 Tables)

**Version**: 2.0.0
**Date**: January 28, 2026
**Status**: DESIGN (Pre-Implementation)
**Owner**: Backend Lead
**Authority**: CTO Approval Required
**Sprint**: Sprint 118 Preparation (D1 Deliverable)
**Foundation**: SPEC-0001 (Anti-Vibecoding), SPEC-0002 (Specification Standard)

---

## 📋 **Document Purpose**

This document defines the database schema for automating **SPEC-0001** (Anti-Vibecoding Quality Assurance) and **SPEC-0002** (Framework 6.0.5 Specification Standard) in SDLC Orchestrator.

**Deliverable**: D1 from [SPRINT-118-TRACK-2-PLAN.md](../../04-build/02-Sprint-Plans/SPRINT-118-TRACK-2-PLAN.md)

**Scope**:
- **14 new tables** (governance_specifications, spec_versions, etc.)
- **ERD diagram** showing relationships to existing 33 tables
- **DDL statements** (SQL CREATE TABLE)
- **Index strategy** for query optimization
- **Migration plan** (Alembic version sequence)
- **Data retention policies**

**Constraints**:
- ✅ Zero downtime migrations
- ✅ Compatible with existing 33-table schema
- ✅ PostgreSQL 15.5+ (pgvector, btree_gin extensions)
- ✅ Foreign keys to existing tables: users, projects, gates, gate_evidence
- ✅ Performance target: <50ms p95 for all queries

---

## 🗄️ **Schema Overview - 14 New Tables**

```
┌─────────────────────────────────────────────────────────────────┐
│               GOVERNANCE SYSTEM LAYER (NEW v2.0)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │          SPECIFICATION MANAGEMENT (7 tables)            │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  ┌───────────────────────────┐                          │   │
│  │  │ governance_specifications │ (SPEC-0001, SPEC-0002)   │   │
│  │  └───────────────────────────┘                          │   │
│  │             │ 1:N                                        │   │
│  │             ├──────┬──────┬──────┬──────┬──────┐        │   │
│  │             ▼      ▼      ▼      ▼      ▼      ▼        │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │ spec_versions (version history)                 │    │   │
│  │  │ spec_frontmatter_metadata (YAML storage)        │    │   │
│  │  │ spec_functional_requirements (FR-001 to FR-008) │    │   │
│  │  │ spec_acceptance_criteria (AC-001 to AC-012)     │    │   │
│  │  │ spec_implementation_phases (Phase 0-4)          │    │   │
│  │  │ spec_cross_references (inter-spec deps)         │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │       ANTI-VIBECODING SYSTEM (7 tables)                 │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  ┌───────────────────────────┐                          │   │
│  │  │   vibecoding_signals      │ (5 signals: Intent, Own, │   │
│  │  │                           │  Context, AI, Historical) │   │
│  │  └───────────────────────────┘                          │   │
│  │             │ N:1 to governance_submissions             │   │
│  │             ▼                                            │   │
│  │  ┌───────────────────────────┐                          │   │
│  │  │vibecoding_index_history   │ (time-series index)      │   │
│  │  └───────────────────────────┘                          │   │
│  │             │ N:1 to projects                           │   │
│  │             ▼                                            │   │
│  │  ┌───────────────────────────┐                          │   │
│  │  │progressive_routing_rules  │ (Green/Yellow/Orange/Red)│   │
│  │  └───────────────────────────┘                          │   │
│  │             │ 1:1 per zone                              │   │
│  │             ▼                                            │   │
│  │  ┌───────────────────────────┐                          │   │
│  │  │ kill_switch_triggers      │ (3 triggers: rejection,  │   │
│  │  │                           │  latency, CVEs)          │   │
│  │  └───────────────────────────┘                          │   │
│  │             │ 1:N events                                │   │
│  │             ▼                                            │   │
│  │  ┌───────────────────────────┐                          │   │
│  │  │  kill_switch_events       │ (activation log)         │   │
│  │  └───────────────────────────┘                          │   │
│  │                                                          │   │
│  │  ┌───────────────────────────┐                          │   │
│  │  │tier_specific_requirements │ (LITE/STD/PRO/ENT rules) │   │
│  │  └───────────────────────────┘                          │   │
│  │                                                          │   │
│  │  ┌───────────────────────────┐                          │   │
│  │  │ spec_validation_results   │ (validation output)      │   │
│  │  └───────────────────────────┘                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Relationships to Existing 30 Tables:                          │
│  • governance_specifications → users (owner_id FK)             │
│  • vibecoding_index_history → projects (project_id FK)         │
│  • spec_validation_results → gate_evidence (evidence_id FK)    │
│  • kill_switch_events → users (triggered_by_user_id FK)        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 **Table Definitions (14 New Tables)**

### **Group 1: Specification Management (7 tables)**

---

#### **Table 1: governance_specifications**

**Purpose**: Store SPEC-0001, SPEC-0002, and future specifications metadata.

**Schema**:
```sql
CREATE TABLE governance_specifications (
  -- Primary Key
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Specification Identity (from YAML frontmatter)
  spec_id               VARCHAR(20) UNIQUE NOT NULL, -- "SPEC-0001", "SPEC-0002"
  title                 VARCHAR(255) NOT NULL,
  version               VARCHAR(20) NOT NULL, -- Semantic versioning "1.0.0"
  status                VARCHAR(20) NOT NULL CHECK (status IN (
                          'DRAFT', 'REVIEW', 'APPROVED', 'ACTIVE', 'DEPRECATED'
                        )),

  -- Tier Applicability (array field)
  tier                  VARCHAR(20)[] NOT NULL, -- ['LITE', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE']

  -- Pillar/Section Classification
  pillar                TEXT[] NOT NULL, -- ['Pillar 7 - Quality Assurance System']

  -- Ownership
  owner_id              UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  owner_label           VARCHAR(255), -- "CTO + Quality Lead"

  -- Cross-References
  related_adrs          TEXT[], -- ['ADR-035-Governance-System-Design']
  related_specs         TEXT[], -- ['SPEC-0002', 'SPEC-0003']

  -- Framework Context
  framework_version     VARCHAR(20) NOT NULL DEFAULT '6.0.5', -- "SDLC 6.0.5"
  machine_readable_spec TEXT, -- URL to YAML control file

  -- Content Storage
  content_markdown      TEXT NOT NULL, -- Full specification markdown
  content_hash          VARCHAR(64) NOT NULL, -- SHA256 for integrity check

  -- Metadata
  tags                  TEXT[], -- ['anti-vibecoding', 'quality-assurance']
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  last_validated_at     TIMESTAMP WITH TIME ZONE,

  -- Audit Trail
  created_by_user_id    UUID NOT NULL REFERENCES users(id),
  updated_by_user_id    UUID REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_governance_specs_spec_id ON governance_specifications(spec_id);
CREATE INDEX idx_governance_specs_status ON governance_specifications(status);
CREATE INDEX idx_governance_specs_owner ON governance_specifications(owner_id);
CREATE INDEX idx_governance_specs_framework_version ON governance_specifications(framework_version);
CREATE INDEX idx_governance_specs_tags ON governance_specifications USING GIN(tags);

-- Full-text search on title + content
CREATE INDEX idx_governance_specs_fts ON governance_specifications
  USING GIN(to_tsvector('english', title || ' ' || content_markdown));

-- Comments
COMMENT ON TABLE governance_specifications IS 'SPEC-0001, SPEC-0002 metadata and content storage';
COMMENT ON COLUMN governance_specifications.spec_id IS 'Unique spec identifier from YAML frontmatter';
COMMENT ON COLUMN governance_specifications.content_hash IS 'SHA256 hash for integrity verification';
```

**Key Features**:
- ✅ Stores YAML frontmatter fields (spec_id, title, version, status, tier, pillar)
- ✅ Full markdown content stored with SHA256 integrity check
- ✅ Full-text search index for title + content
- ✅ GIN index on tags for fast tag-based queries
- ✅ Foreign key to users for ownership tracking

---

#### **Table 2: spec_versions**

**Purpose**: Version history and changelog for specifications.

**Schema**:
```sql
CREATE TABLE spec_versions (
  -- Primary Key
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Specification Reference
  spec_id               VARCHAR(20) NOT NULL, -- "SPEC-0001"
  governance_spec_id    UUID NOT NULL REFERENCES governance_specifications(id) ON DELETE CASCADE,

  -- Version Information
  version               VARCHAR(20) NOT NULL, -- "1.0.0", "1.1.0", "2.0.0"
  version_date          DATE NOT NULL,

  -- Change Tracking
  changelog             TEXT NOT NULL, -- Markdown formatted changelog
  breaking_changes      BOOLEAN NOT NULL DEFAULT false,
  deprecated_features   TEXT[], -- List of deprecated features

  -- Content Snapshot
  content_markdown      TEXT NOT NULL, -- Full spec at this version
  content_hash          VARCHAR(64) NOT NULL, -- SHA256 hash

  -- Metadata
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  created_by_user_id    UUID NOT NULL REFERENCES users(id),

  -- Unique constraint: one version per spec
  UNIQUE(spec_id, version)
);

-- Indexes
CREATE INDEX idx_spec_versions_spec_id ON spec_versions(spec_id);
CREATE INDEX idx_spec_versions_governance_spec ON spec_versions(governance_spec_id);
CREATE INDEX idx_spec_versions_version ON spec_versions(spec_id, version);
CREATE INDEX idx_spec_versions_date ON spec_versions(version_date DESC);

-- Comments
COMMENT ON TABLE spec_versions IS 'Version history for specifications';
COMMENT ON COLUMN spec_versions.breaking_changes IS 'Indicates if this version has breaking changes';
```

**Key Features**:
- ✅ Full version history with changelog
- ✅ Breaking change flag for migration warnings
- ✅ Content snapshot at each version
- ✅ Chronological query optimization (version_date DESC index)

---

#### **Table 3: spec_frontmatter_metadata**

**Purpose**: Store parsed YAML frontmatter key-value pairs for querying.

**Schema**:
```sql
CREATE TABLE spec_frontmatter_metadata (
  -- Primary Key
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Specification Reference
  governance_spec_id    UUID NOT NULL REFERENCES governance_specifications(id) ON DELETE CASCADE,
  spec_id               VARCHAR(20) NOT NULL,

  -- YAML Frontmatter Fields (JSON storage for flexibility)
  frontmatter_json      JSONB NOT NULL,

  -- Key Required Fields (extracted for fast queries)
  spec_id_value         VARCHAR(20) NOT NULL, -- From frontmatter
  title_value           VARCHAR(255) NOT NULL,
  version_value         VARCHAR(20) NOT NULL,
  status_value          VARCHAR(20) NOT NULL,
  tier_value            TEXT[] NOT NULL,
  pillar_value          TEXT[] NOT NULL,
  owner_value           VARCHAR(255) NOT NULL,
  last_updated_value    DATE NOT NULL,

  -- Validation
  schema_version        VARCHAR(20) NOT NULL DEFAULT '1.0', -- JSON Schema version
  validation_status     VARCHAR(20) NOT NULL CHECK (validation_status IN ('VALID', 'INVALID')),
  validation_errors     JSONB, -- Array of validation errors if INVALID

  -- Metadata
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_frontmatter_governance_spec ON spec_frontmatter_metadata(governance_spec_id);
CREATE INDEX idx_frontmatter_spec_id ON spec_frontmatter_metadata(spec_id);
CREATE INDEX idx_frontmatter_status ON spec_frontmatter_metadata(status_value);
CREATE INDEX idx_frontmatter_validation ON spec_frontmatter_metadata(validation_status);

-- GIN index on JSONB for fast key-value queries
CREATE INDEX idx_frontmatter_json ON spec_frontmatter_metadata USING GIN(frontmatter_json);

-- Comments
COMMENT ON TABLE spec_frontmatter_metadata IS 'Parsed YAML frontmatter for fast querying';
COMMENT ON COLUMN spec_frontmatter_metadata.frontmatter_json IS 'Full YAML frontmatter as JSONB';
COMMENT ON COLUMN spec_frontmatter_metadata.validation_errors IS 'JSON Schema validation errors (if any)';
```

**Key Features**:
- ✅ JSONB storage for flexible frontmatter fields
- ✅ Extracted key fields for fast queries (no JSON traversal needed)
- ✅ GIN index on JSONB for complex queries
- ✅ Validation status tracking with error details

---

#### **Table 4: spec_functional_requirements**

**Purpose**: Store functional requirements (FR-001 to FR-008) from specifications.

**Schema**:
```sql
CREATE TABLE spec_functional_requirements (
  -- Primary Key
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Specification Reference
  governance_spec_id    UUID NOT NULL REFERENCES governance_specifications(id) ON DELETE CASCADE,
  spec_id               VARCHAR(20) NOT NULL,

  -- Requirement Identity
  requirement_id        VARCHAR(20) NOT NULL, -- "FR-001", "FR-002"
  requirement_title     VARCHAR(255) NOT NULL,
  requirement_order     INTEGER NOT NULL, -- Display order (1, 2, 3...)

  -- BDD Format (GIVEN-WHEN-THEN)
  given_conditions      TEXT NOT NULL, -- "GIVEN user submits code"
  when_actions          TEXT NOT NULL, -- "WHEN Vibecoding Index calculated"
  then_outcomes         TEXT NOT NULL, -- "THEN index MUST be 0-100"

  -- Requirement Details
  description           TEXT NOT NULL,
  tier_applicability    TEXT[] NOT NULL, -- ['PROFESSIONAL', 'ENTERPRISE']
  priority              VARCHAR(20) CHECK (priority IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),

  -- Implementation Status
  implementation_status VARCHAR(20) NOT NULL DEFAULT 'NOT_STARTED' CHECK (implementation_status IN (
                          'NOT_STARTED', 'IN_PROGRESS', 'IMPLEMENTED', 'VERIFIED', 'DEFERRED'
                        )),
  implemented_in_version VARCHAR(20), -- "1.0.0"

  -- Metadata
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  -- Unique constraint
  UNIQUE(spec_id, requirement_id)
);

-- Indexes
CREATE INDEX idx_func_requirements_spec ON spec_functional_requirements(governance_spec_id);
CREATE INDEX idx_func_requirements_spec_id ON spec_functional_requirements(spec_id);
CREATE INDEX idx_func_requirements_status ON spec_functional_requirements(implementation_status);
CREATE INDEX idx_func_requirements_order ON spec_functional_requirements(spec_id, requirement_order);

-- Comments
COMMENT ON TABLE spec_functional_requirements IS 'Functional requirements (FR-001 to FR-008) from specs';
COMMENT ON COLUMN spec_functional_requirements.given_conditions IS 'BDD GIVEN clause';
COMMENT ON COLUMN spec_functional_requirements.when_actions IS 'BDD WHEN clause';
COMMENT ON COLUMN spec_functional_requirements.then_outcomes IS 'BDD THEN clause';
```

**Key Features**:
- ✅ BDD format storage (GIVEN-WHEN-THEN)
- ✅ Implementation status tracking
- ✅ Tier-specific applicability
- ✅ Display order for UI rendering

---

#### **Table 5: spec_acceptance_criteria**

**Purpose**: Store acceptance criteria (AC-001 to AC-012) with test methods.

**Schema**:
```sql
CREATE TABLE spec_acceptance_criteria (
  -- Primary Key
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Specification Reference
  governance_spec_id    UUID NOT NULL REFERENCES governance_specifications(id) ON DELETE CASCADE,
  spec_id               VARCHAR(20) NOT NULL,

  -- Acceptance Criteria Identity
  ac_id                 VARCHAR(20) NOT NULL, -- "AC-001", "AC-002"
  ac_title              VARCHAR(255) NOT NULL,
  ac_order              INTEGER NOT NULL, -- Display order

  -- Criteria Definition
  criteria_description  TEXT NOT NULL,
  success_conditions    TEXT[] NOT NULL, -- Array of success conditions

  -- Testing
  test_method           VARCHAR(50) NOT NULL CHECK (test_method IN (
                          'AUTOMATED', 'MANUAL', 'INSPECTION', 'ANALYSIS', 'DEMONSTRATION'
                        )),
  test_procedure        TEXT, -- Step-by-step test procedure
  test_result           VARCHAR(20) CHECK (test_result IN ('PASS', 'FAIL', 'NOT_TESTED')),

  -- Evidence
  evidence_required     BOOLEAN NOT NULL DEFAULT true,
  evidence_type         VARCHAR(50), -- "UNIT_TEST", "INTEGRATION_TEST", "SCREENSHOT"

  -- Tier Applicability
  tier_applicability    TEXT[] NOT NULL,

  -- Metadata
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  last_tested_at        TIMESTAMP WITH TIME ZONE,

  -- Unique constraint
  UNIQUE(spec_id, ac_id)
);

-- Indexes
CREATE INDEX idx_ac_spec ON spec_acceptance_criteria(governance_spec_id);
CREATE INDEX idx_ac_spec_id ON spec_acceptance_criteria(spec_id);
CREATE INDEX idx_ac_test_method ON spec_acceptance_criteria(test_method);
CREATE INDEX idx_ac_test_result ON spec_acceptance_criteria(test_result);
CREATE INDEX idx_ac_order ON spec_acceptance_criteria(spec_id, ac_order);

-- Comments
COMMENT ON TABLE spec_acceptance_criteria IS 'Acceptance criteria (AC-001 to AC-012) with test methods';
COMMENT ON COLUMN spec_acceptance_criteria.test_method IS 'How to test this acceptance criterion';
COMMENT ON COLUMN spec_acceptance_criteria.test_result IS 'Latest test result';
```

**Key Features**:
- ✅ Test method categorization (AUTOMATED, MANUAL, etc.)
- ✅ Test result tracking (PASS/FAIL)
- ✅ Evidence requirements
- ✅ Last tested timestamp

---

#### **Table 6: spec_implementation_phases**

**Purpose**: Track implementation phases (Phase 0 to Phase 4) progress.

**Schema**:
```sql
CREATE TABLE spec_implementation_phases (
  -- Primary Key
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Specification Reference
  governance_spec_id    UUID NOT NULL REFERENCES governance_specifications(id) ON DELETE CASCADE,
  spec_id               VARCHAR(20) NOT NULL,

  -- Phase Identity
  phase_number          INTEGER NOT NULL CHECK (phase_number >= 0 AND phase_number <= 10),
  phase_name            VARCHAR(100) NOT NULL, -- "Phase 0: POC", "Phase 1: Foundation"
  phase_order           INTEGER NOT NULL, -- Display order

  -- Phase Details
  phase_description     TEXT NOT NULL,
  phase_deliverables    TEXT[] NOT NULL, -- Array of deliverable descriptions
  phase_duration        VARCHAR(50), -- "2 weeks", "1 sprint"

  -- Progress Tracking
  status                VARCHAR(20) NOT NULL DEFAULT 'NOT_STARTED' CHECK (status IN (
                          'NOT_STARTED', 'IN_PROGRESS', 'BLOCKED', 'COMPLETE', 'DEFERRED'
                        )),
  progress_percentage   INTEGER CHECK (progress_percentage >= 0 AND progress_percentage <= 100),

  -- Dates
  start_date            DATE,
  target_end_date       DATE,
  actual_end_date       DATE,

  -- Dependencies
  depends_on_phases     INTEGER[], -- Array of phase_number dependencies
  blocking_issues       TEXT, -- Description of blockers (if status = BLOCKED)

  -- Metadata
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  -- Unique constraint
  UNIQUE(spec_id, phase_number)
);

-- Indexes
CREATE INDEX idx_phases_spec ON spec_implementation_phases(governance_spec_id);
CREATE INDEX idx_phases_spec_id ON spec_implementation_phases(spec_id);
CREATE INDEX idx_phases_status ON spec_implementation_phases(status);
CREATE INDEX idx_phases_order ON spec_implementation_phases(spec_id, phase_order);
CREATE INDEX idx_phases_dates ON spec_implementation_phases(start_date, target_end_date);

-- Comments
COMMENT ON TABLE spec_implementation_phases IS 'Implementation phases (Phase 0-4) progress tracking';
COMMENT ON COLUMN spec_implementation_phases.depends_on_phases IS 'Array of prerequisite phase numbers';
COMMENT ON COLUMN spec_implementation_phases.blocking_issues IS 'Description of blockers (if status = BLOCKED)';
```

**Key Features**:
- ✅ Phase dependency tracking
- ✅ Progress percentage
- ✅ Date tracking (start, target, actual)
- ✅ Blocking issue documentation

---

#### **Table 7: spec_cross_references**

**Purpose**: Track inter-specification dependencies and references.

**Schema**:
```sql
CREATE TABLE spec_cross_references (
  -- Primary Key
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Source Specification
  source_spec_id        VARCHAR(20) NOT NULL, -- "SPEC-0001"
  source_governance_id  UUID NOT NULL REFERENCES governance_specifications(id) ON DELETE CASCADE,

  -- Target Specification
  target_spec_id        VARCHAR(20) NOT NULL, -- "SPEC-0002"
  target_governance_id  UUID REFERENCES governance_specifications(id) ON DELETE CASCADE,

  -- Reference Type
  reference_type        VARCHAR(50) NOT NULL CHECK (reference_type IN (
                          'DEPENDS_ON',        -- Source depends on target
                          'EXTENDS',           -- Source extends target
                          'IMPLEMENTS',        -- Source implements target
                          'SUPERSEDES',        -- Source supersedes target
                          'RELATED_TO',        -- General relationship
                          'CONFLICTS_WITH'     -- Incompatible specifications
                        )),

  -- Reference Details
  description           TEXT, -- Why this reference exists
  section_reference     VARCHAR(100), -- "Section 3.2" or "FR-005"

  -- Validation
  is_valid              BOOLEAN NOT NULL DEFAULT true, -- False if target is DEPRECATED
  validation_message    TEXT, -- Error if is_valid = false

  -- Metadata
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  created_by_user_id    UUID NOT NULL REFERENCES users(id),

  -- Prevent duplicate references
  UNIQUE(source_spec_id, target_spec_id, reference_type)
);

-- Indexes
CREATE INDEX idx_cross_ref_source ON spec_cross_references(source_spec_id);
CREATE INDEX idx_cross_ref_target ON spec_cross_references(target_spec_id);
CREATE INDEX idx_cross_ref_type ON spec_cross_references(reference_type);
CREATE INDEX idx_cross_ref_valid ON spec_cross_references(is_valid);

-- Comments
COMMENT ON TABLE spec_cross_references IS 'Inter-specification dependencies and references';
COMMENT ON COLUMN spec_cross_references.reference_type IS 'Type of relationship between specs';
COMMENT ON COLUMN spec_cross_references.is_valid IS 'False if target spec is deprecated or missing';
```

**Key Features**:
- ✅ 6 reference types (DEPENDS_ON, EXTENDS, IMPLEMENTS, etc.)
- ✅ Validation status for broken references
- ✅ Section-level references
- ✅ Bidirectional relationship queries

---

### **Group 2: Anti-Vibecoding System (7 tables)**

---

#### **Table 8: vibecoding_signals**

**Purpose**: Store 5 signal values for Vibecoding Index calculation.

**Schema**:
```sql
CREATE TABLE vibecoding_signals (
  -- Primary Key
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Submission Reference (links to governance_submissions if exists, else gate_evidence)
  submission_id         UUID, -- NULL if calculated before submission created
  project_id            UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

  -- Gate Evidence Reference (for gate-based submissions)
  gate_evidence_id      UUID REFERENCES gate_evidence(id) ON DELETE SET NULL,

  -- Signal 1: Intent Clarity Score (weight: 0.30)
  intent_clarity_score  DECIMAL(5,2) NOT NULL CHECK (intent_clarity_score >= 0 AND intent_clarity_score <= 100),
  intent_evidence_type  VARCHAR(50) DEFAULT 'REQUIREMENT_ANALYSIS',
  intent_threshold      VARCHAR(20), -- 'RED', 'ORANGE', 'YELLOW', 'GREEN'

  -- Signal 2: Code Ownership Confidence (weight: 0.25)
  ownership_confidence  DECIMAL(5,2) NOT NULL CHECK (ownership_confidence >= 0 AND ownership_confidence <= 100),
  ownership_evidence_type VARCHAR(50) DEFAULT 'OWNERSHIP_DOCUMENTATION',
  ownership_threshold   VARCHAR(20),

  -- Signal 3: Context Completeness (weight: 0.20)
  context_completeness  DECIMAL(5,2) NOT NULL CHECK (context_completeness >= 0 AND context_completeness <= 100),
  context_evidence_type VARCHAR(50) DEFAULT 'CONTEXT_DOCUMENTATION',
  context_threshold     VARCHAR(20),

  -- Signal 4: AI Attestation Rate (weight: 0.15)
  ai_attestation_rate   DECIMAL(5,2) NOT NULL CHECK (ai_attestation_rate >= 0 AND ai_attestation_rate <= 100),
  ai_evidence_type      VARCHAR(50) DEFAULT 'CODE_CONTRIBUTION_METADATA',
  ai_threshold          VARCHAR(20),

  -- Signal 5: Historical Rejection Rate (weight: 0.10)
  rejection_rate        DECIMAL(5,2) NOT NULL CHECK (rejection_rate >= 0 AND rejection_rate <= 100),
  rejection_evidence_type VARCHAR(50) DEFAULT 'CODE_REVIEW_OUTCOME',
  rejection_threshold   VARCHAR(20),

  -- Overall Vibecoding Index (0-100, higher = riskier)
  vibecoding_index      DECIMAL(5,2) NOT NULL CHECK (vibecoding_index >= 0 AND vibecoding_index <= 100),

  -- Calculation Metadata
  calculation_formula   TEXT NOT NULL DEFAULT '100 - (intent*0.30 + ownership*0.25 + context*0.20 + attestation*0.15 + (100-rejection)*0.10)',
  calculation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  -- Metadata
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  created_by_user_id    UUID REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_signals_submission ON vibecoding_signals(submission_id);
CREATE INDEX idx_signals_project ON vibecoding_signals(project_id);
CREATE INDEX idx_signals_gate_evidence ON vibecoding_signals(gate_evidence_id);
CREATE INDEX idx_signals_index ON vibecoding_signals(vibecoding_index);
CREATE INDEX idx_signals_timestamp ON vibecoding_signals(calculation_timestamp DESC);

-- Comments
COMMENT ON TABLE vibecoding_signals IS '5 signal values for Vibecoding Index calculation';
COMMENT ON COLUMN vibecoding_signals.vibecoding_index IS 'Calculated index (0-100), higher = riskier';
COMMENT ON COLUMN vibecoding_signals.intent_clarity_score IS 'Signal 1: Requirement clarity (0-100)';
```

**Key Features**:
- ✅ All 5 signals stored with evidence types
- ✅ Threshold classification (RED/ORANGE/YELLOW/GREEN)
- ✅ Calculated vibecoding_index stored for fast queries
- ✅ Time-series query optimization (timestamp DESC index)

---

#### **Table 9: vibecoding_index_history**

**Purpose**: Time-series storage of Vibecoding Index per project/submission.

**Schema**:
```sql
CREATE TABLE vibecoding_index_history (
  -- Primary Key
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- References
  project_id            UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  submission_id         UUID, -- NULL if calculated before submission
  vibecoding_signal_id  UUID NOT NULL REFERENCES vibecoding_signals(id) ON DELETE CASCADE,

  -- Index Value
  index_value           DECIMAL(5,2) NOT NULL CHECK (index_value >= 0 AND index_value <= 100),

  -- Routing Zone (calculated from index_value)
  routing_zone          VARCHAR(20) NOT NULL CHECK (routing_zone IN ('GREEN', 'YELLOW', 'ORANGE', 'RED')),
  routing_action        VARCHAR(50) NOT NULL, -- 'AUTO_MERGE', 'HUMAN_REVIEW_REQUIRED', etc.

  -- Context
  calculation_context   JSONB, -- Additional context (PR number, branch, commit SHA)

  -- Timestamp
  calculated_at         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  -- Metadata
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_index_history_project ON vibecoding_index_history(project_id);
CREATE INDEX idx_index_history_submission ON vibecoding_index_history(submission_id);
CREATE INDEX idx_index_history_signal ON vibecoding_index_history(vibecoding_signal_id);
CREATE INDEX idx_index_history_zone ON vibecoding_index_history(routing_zone);
CREATE INDEX idx_index_history_calculated_at ON vibecoding_index_history(calculated_at DESC);

-- Time-series partitioning (optional for large datasets)
-- CREATE INDEX idx_index_history_project_time ON vibecoding_index_history(project_id, calculated_at DESC);

-- Comments
COMMENT ON TABLE vibecoding_index_history IS 'Time-series Vibecoding Index per project';
COMMENT ON COLUMN vibecoding_index_history.routing_zone IS 'GREEN (<20), YELLOW (20-40), ORANGE (40-60), RED (>=60)';
COMMENT ON COLUMN vibecoding_index_history.calculation_context IS 'JSONB with PR number, branch, commit SHA';
```

**Key Features**:
- ✅ Time-series storage for trend analysis
- ✅ Routing zone pre-calculated for fast filtering
- ✅ JSONB context for flexible metadata
- ✅ Partitioning-ready for scale (by project_id + calculated_at)

---

#### **Table 10: progressive_routing_rules**

**Purpose**: Store routing rules for 4 zones (Green/Yellow/Orange/Red).

**Schema**:
```sql
CREATE TABLE progressive_routing_rules (
  -- Primary Key
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Zone Identity
  zone                  VARCHAR(20) UNIQUE NOT NULL CHECK (zone IN ('GREEN', 'YELLOW', 'ORANGE', 'RED')),
  zone_label            VARCHAR(100) NOT NULL, -- "Low Risk (< 20)"

  -- Threshold Range
  index_min             DECIMAL(5,2) NOT NULL CHECK (index_min >= 0),
  index_max             DECIMAL(5,2) CHECK (index_max <= 100),

  -- Routing Action
  routing_action        VARCHAR(50) NOT NULL CHECK (routing_action IN (
                          'AUTO_MERGE', 'HUMAN_REVIEW_REQUIRED', 'SENIOR_REVIEW_REQUIRED', 'BLOCK_OR_COUNCIL'
                        )),

  -- Conditions (stored as JSONB array)
  conditions            JSONB NOT NULL, -- [{"type": "ci_checks_pass"}, {"type": "approvals", "count": 1}]

  -- Tier Applicability
  tier                  TEXT[] NOT NULL DEFAULT ARRAY['PROFESSIONAL', 'ENTERPRISE'],
  enforcement_mode      JSONB NOT NULL, -- {"PROFESSIONAL": "WARNING", "ENTERPRISE": "SOFT"}

  -- Metadata
  description           TEXT,
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_routing_rules_zone ON progressive_routing_rules(zone);
CREATE INDEX idx_routing_rules_action ON progressive_routing_rules(routing_action);

-- Seed Data (from SPEC-0001 AVC-002)
INSERT INTO progressive_routing_rules (zone, zone_label, index_min, index_max, routing_action, conditions, description) VALUES
  ('GREEN', 'Low Risk (< 20)', 0, 19.99, 'AUTO_MERGE',
   '[{"type": "ci_checks_pass"}, {"type": "approvals", "count": 1, "automated_ok": true}, {"type": "no_security_vulnerabilities"}]',
   'Auto-merge allowed with basic checks'),

  ('YELLOW', 'Medium Risk (20-40)', 20, 39.99, 'HUMAN_REVIEW_REQUIRED',
   '[{"type": "human_reviews", "count": 2}, {"type": "security_scan_pass"}, {"type": "test_coverage", "threshold": 80}]',
   '2+ human code reviews required'),

  ('ORANGE', 'High Risk (40-60)', 40, 59.99, 'SENIOR_REVIEW_REQUIRED',
   '[{"type": "senior_engineer_review"}, {"type": "security_lead_signoff"}, {"type": "test_coverage", "threshold": 90}, {"type": "ai_output_validation"}]',
   'Senior engineer and security lead approval required'),

  ('RED', 'Critical Risk (>= 60)', 60, 100, 'BLOCK_OR_COUNCIL',
   '[{"type": "block_by_default_soft_mode"}, {"type": "escalate_to_ai_council"}, {"type": "cto_override_required_full_mode"}, {"type": "mandatory_human_rewrite_if_rejected"}]',
   'PR blocked by default, requires council escalation');

-- Comments
COMMENT ON TABLE progressive_routing_rules IS 'Routing rules for 4 zones (Green/Yellow/Orange/Red)';
COMMENT ON COLUMN progressive_routing_rules.conditions IS 'JSONB array of conditions for this zone';
COMMENT ON COLUMN progressive_routing_rules.enforcement_mode IS 'JSONB: {"PROFESSIONAL": "WARNING", "ENTERPRISE": "SOFT"}';
```

**Key Features**:
- ✅ Pre-seeded with SPEC-0001 AVC-002 rules
- ✅ JSONB conditions for flexible rule definitions
- ✅ Tier-specific enforcement modes
- ✅ Index range for zone determination

---

#### **Table 11: kill_switch_triggers**

**Purpose**: Define 3 kill switch triggers (rejection rate, latency, CVEs).

**Schema**:
```sql
CREATE TABLE kill_switch_triggers (
  -- Primary Key
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Trigger Identity
  trigger_id            VARCHAR(20) UNIQUE NOT NULL, -- "KST-001", "KST-002", "KST-003"
  trigger_name          VARCHAR(100) NOT NULL,

  -- Trigger Metric
  metric                VARCHAR(50) NOT NULL CHECK (metric IN ('REJECTION_RATE', 'LATENCY_P95', 'SECURITY_SCAN_FAILURES')),

  -- Threshold Conditions
  threshold_value       DECIMAL(10,2) NOT NULL, -- 80 for rejection_rate, 500 for latency, 5 for CVEs
  threshold_operator    VARCHAR(10) NOT NULL CHECK (threshold_operator IN ('>', '<', '>=', '<=', '=')),
  threshold_unit        VARCHAR(20), -- '%', 'ms', 'count'

  -- Duration Window
  duration_minutes      INTEGER, -- 30 for rejection, 15 for latency, NULL for CVEs (immediate)
  duration_description  VARCHAR(100), -- "30 consecutive minutes", "15 consecutive minutes", "Any occurrence"

  -- Action on Trigger
  action                VARCHAR(100) NOT NULL, -- "Disable AI codegen for 24h", "Fallback to rule-based"

  -- Tier Applicability
  tier                  TEXT[] NOT NULL DEFAULT ARRAY['ENTERPRISE'],
  enforcement_mode      VARCHAR(20) NOT NULL DEFAULT 'FULL',

  -- Recovery Conditions (JSONB array)
  recovery_conditions   JSONB NOT NULL, -- [{"type": "cto_approval"}, {"type": "root_cause_analysis"}]

  -- Metadata
  is_active             BOOLEAN NOT NULL DEFAULT true,
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_kill_switch_triggers_metric ON kill_switch_triggers(metric);
CREATE INDEX idx_kill_switch_triggers_active ON kill_switch_triggers(is_active);

-- Seed Data (from SPEC-0001 AVC-003)
INSERT INTO kill_switch_triggers (trigger_id, trigger_name, metric, threshold_value, threshold_operator, threshold_unit, duration_minutes, duration_description, action, recovery_conditions) VALUES
  ('KST-001', 'High Rejection Rate', 'REJECTION_RATE', 80, '>', '%', 30, '30 consecutive minutes', 'Disable AI codegen for 24h',
   '[{"type": "cto_approval"}, {"type": "root_cause_analysis"}, {"type": "fix_deployed_and_validated"}, {"type": "gradual_reenable", "steps": ["10%", "50%", "100%"]}]'),

  ('KST-002', 'High Latency', 'LATENCY_P95', 500, '>', 'ms', 15, '15 consecutive minutes', 'Fallback to rule-based',
   '[{"type": "cto_approval"}, {"type": "performance_fix_deployed"}]'),

  ('KST-003', 'Critical Security Vulnerabilities', 'SECURITY_SCAN_FAILURES', 5, '>', 'count', NULL, 'Any occurrence', 'Immediate disable + alert CTO',
   '[{"type": "cto_approval"}, {"type": "security_fix_deployed"}, {"type": "security_scan_clean"}]');

-- Comments
COMMENT ON TABLE kill_switch_triggers IS '3 kill switch triggers from SPEC-0001 AVC-003';
COMMENT ON COLUMN kill_switch_triggers.duration_minutes IS 'NULL = immediate trigger (no window)';
COMMENT ON COLUMN kill_switch_triggers.recovery_conditions IS 'JSONB array of conditions to re-enable after kill switch';
```

**Key Features**:
- ✅ Pre-seeded with SPEC-0001 AVC-003 triggers
- ✅ Flexible threshold conditions (>, <, >=, <=, =)
- ✅ Duration window for time-based triggers
- ✅ JSONB recovery conditions

---

#### **Table 12: kill_switch_events**

**Purpose**: Log kill switch activation events (1-year retention).

**Schema**:
```sql
CREATE TABLE kill_switch_events (
  -- Primary Key
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Trigger Reference
  trigger_id            VARCHAR(20) NOT NULL, -- "KST-001"
  kill_switch_trigger_id UUID NOT NULL REFERENCES kill_switch_triggers(id) ON DELETE RESTRICT,

  -- Event Details
  event_type            VARCHAR(20) NOT NULL CHECK (event_type IN ('ACTIVATED', 'DEACTIVATED', 'RECOVERY')),
  triggered_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  -- Trigger Metrics (at activation time)
  metric_name           VARCHAR(50) NOT NULL,
  metric_value          DECIMAL(10,2) NOT NULL, -- Actual value that triggered
  threshold_value       DECIMAL(10,2) NOT NULL, -- Threshold from trigger definition

  -- Context
  affected_projects     UUID[], -- Array of project IDs affected
  project_count         INTEGER,

  -- Actions Taken
  action_taken          VARCHAR(255) NOT NULL, -- "Disabled AI codegen for 24h"
  notification_sent     BOOLEAN NOT NULL DEFAULT true,
  notified_users        UUID[], -- Array of user IDs notified (CEO, CTO)

  -- Recovery
  recovered_at          TIMESTAMP WITH TIME ZONE,
  recovery_reason       TEXT, -- Root cause analysis summary
  recovery_approved_by  UUID REFERENCES users(id), -- CTO/CEO

  -- Evidence
  evidence_json         JSONB, -- Detailed evidence (metrics, logs, screenshots)
  evidence_retention    INTERVAL NOT NULL DEFAULT INTERVAL '1 year',

  -- Metadata
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  triggered_by_system   BOOLEAN NOT NULL DEFAULT true, -- false if manual trigger
  triggered_by_user_id  UUID REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_kill_switch_events_trigger ON kill_switch_events(kill_switch_trigger_id);
CREATE INDEX idx_kill_switch_events_type ON kill_switch_events(event_type);
CREATE INDEX idx_kill_switch_events_triggered_at ON kill_switch_events(triggered_at DESC);
CREATE INDEX idx_kill_switch_events_recovery ON kill_switch_events(recovered_at DESC) WHERE recovered_at IS NOT NULL;

-- Partitioning by triggered_at (for 1-year retention policy)
-- CREATE INDEX idx_kill_switch_events_retention ON kill_switch_events(triggered_at)
--   WHERE triggered_at < NOW() - INTERVAL '1 year'; -- Partition candidates for cleanup

-- Comments
COMMENT ON TABLE kill_switch_events IS 'Kill switch activation log (1-year retention)';
COMMENT ON COLUMN kill_switch_events.evidence_json IS 'Detailed evidence at activation time';
COMMENT ON COLUMN kill_switch_events.evidence_retention IS '1 year retention per SPEC-0001';
```

**Key Features**:
- ✅ Event type tracking (ACTIVATED, DEACTIVATED, RECOVERY)
- ✅ Metric snapshot at trigger time
- ✅ Notification tracking (who was notified)
- ✅ Evidence storage with retention policy
- ✅ Partitioning-ready for 1-year retention

---

#### **Table 13: tier_specific_requirements**

**Purpose**: Store tier-specific requirements (LITE/STANDARD/PROFESSIONAL/ENTERPRISE).

**Schema**:
```sql
CREATE TABLE tier_specific_requirements (
  -- Primary Key
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Specification Reference
  governance_spec_id    UUID NOT NULL REFERENCES governance_specifications(id) ON DELETE CASCADE,
  spec_id               VARCHAR(20) NOT NULL,

  -- Requirement Identity
  requirement_id        VARCHAR(50) NOT NULL, -- "AVC-001", "FR-001", custom ID
  requirement_title     VARCHAR(255) NOT NULL,

  -- Tier Configuration
  tier                  VARCHAR(20) NOT NULL CHECK (tier IN ('LITE', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE')),
  applicability         VARCHAR(20) NOT NULL CHECK (applicability IN (
                          'REQUIRED', 'RECOMMENDED', 'OPTIONAL', 'NOT_APPLICABLE'
                        )),

  -- Enforcement Mode (for this tier)
  enforcement_mode      VARCHAR(20) CHECK (enforcement_mode IN ('OFF', 'WARNING', 'SOFT', 'FULL')),

  -- Requirement Details
  description           TEXT NOT NULL,
  configuration_params  JSONB, -- Tier-specific parameters (thresholds, limits)

  -- Implementation Notes
  implementation_notes  TEXT, -- How this requirement differs by tier

  -- Metadata
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  -- Unique constraint: one requirement per tier
  UNIQUE(spec_id, requirement_id, tier)
);

-- Indexes
CREATE INDEX idx_tier_reqs_spec ON tier_specific_requirements(governance_spec_id);
CREATE INDEX idx_tier_reqs_spec_id ON tier_specific_requirements(spec_id);
CREATE INDEX idx_tier_reqs_tier ON tier_specific_requirements(tier);
CREATE INDEX idx_tier_reqs_applicability ON tier_specific_requirements(tier, applicability);
CREATE INDEX idx_tier_reqs_enforcement ON tier_specific_requirements(enforcement_mode);

-- GIN index on JSONB params
CREATE INDEX idx_tier_reqs_params ON tier_specific_requirements USING GIN(configuration_params);

-- Comments
COMMENT ON TABLE tier_specific_requirements IS 'Tier-specific requirements (LITE/STD/PRO/ENT)';
COMMENT ON COLUMN tier_specific_requirements.applicability IS 'REQUIRED, RECOMMENDED, OPTIONAL, NOT_APPLICABLE';
COMMENT ON COLUMN tier_specific_requirements.configuration_params IS 'JSONB with tier-specific parameters';
```

**Key Features**:
- ✅ 4-tier support (LITE/STANDARD/PROFESSIONAL/ENTERPRISE)
- ✅ Applicability classification (REQUIRED/RECOMMENDED/OPTIONAL)
- ✅ Enforcement mode per tier
- ✅ JSONB configuration for flexible parameters

---

#### **Table 14: spec_validation_results**

**Purpose**: Store automated validation results (25/25 checks from POC).

**Schema**:
```sql
CREATE TABLE spec_validation_results (
  -- Primary Key
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Specification Reference
  governance_spec_id    UUID NOT NULL REFERENCES governance_specifications(id) ON DELETE CASCADE,
  spec_id               VARCHAR(20) NOT NULL,

  -- Validation Run
  validation_run_id     UUID NOT NULL, -- Groups multiple validations in one run
  validation_timestamp  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  -- Validation Type
  validation_type       VARCHAR(50) NOT NULL CHECK (validation_type IN (
                          'YAML_FRONTMATTER',     -- AC-001
                          'BDD_FORMAT',           -- AC-002
                          'TIER_SECTIONS',        -- AC-003
                          'ACCEPTANCE_CRITERIA',  -- AC-004
                          'CROSS_REFERENCES',     -- AC-005
                          'IMPLEMENTATION_PLAN',  -- AC-006
                          'DESIGN_DECISIONS'      -- AC-007
                        )),

  -- Results
  status                VARCHAR(20) NOT NULL CHECK (status IN ('PASS', 'FAIL', 'WARNING', 'SKIPPED')),
  checks_total          INTEGER NOT NULL, -- Total checks performed
  checks_passed         INTEGER NOT NULL, -- Checks that passed
  checks_failed         INTEGER NOT NULL, -- Checks that failed

  -- Errors (if FAIL)
  validation_errors     JSONB, -- Array of error objects
  error_summary         TEXT, -- Human-readable summary

  -- Evidence
  gate_evidence_id      UUID REFERENCES gate_evidence(id) ON DELETE SET NULL,
  evidence_file_path    TEXT, -- Path to validation report file

  -- Metadata
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  validated_by_user_id  UUID REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_validation_results_spec ON spec_validation_results(governance_spec_id);
CREATE INDEX idx_validation_results_spec_id ON spec_validation_results(spec_id);
CREATE INDEX idx_validation_results_run ON spec_validation_results(validation_run_id);
CREATE INDEX idx_validation_results_type ON spec_validation_results(validation_type);
CREATE INDEX idx_validation_results_status ON spec_validation_results(status);
CREATE INDEX idx_validation_results_timestamp ON spec_validation_results(validation_timestamp DESC);

-- GIN index on errors JSONB
CREATE INDEX idx_validation_results_errors ON spec_validation_results USING GIN(validation_errors);

-- Comments
COMMENT ON TABLE spec_validation_results IS 'Automated validation results (25/25 checks)';
COMMENT ON COLUMN spec_validation_results.validation_run_id IS 'Groups multiple validation checks in one run';
COMMENT ON COLUMN spec_validation_results.validation_errors IS 'JSONB array of error details';
```

**Key Features**:
- ✅ 7 validation types (AC-001 to AC-007)
- ✅ Detailed check counts (total, passed, failed)
- ✅ JSONB error storage with GIN index
- ✅ Evidence linking for audit trail
- ✅ Validation run grouping

---

## 🔗 **Relationships to Existing 30 Tables**

### **Foreign Key Constraints**

```sql
-- governance_specifications → users (owner)
ALTER TABLE governance_specifications
  ADD CONSTRAINT fk_gov_spec_owner
  FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE RESTRICT;

-- vibecoding_signals → projects
ALTER TABLE vibecoding_signals
  ADD CONSTRAINT fk_signals_project
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

-- vibecoding_signals → gate_evidence (optional)
ALTER TABLE vibecoding_signals
  ADD CONSTRAINT fk_signals_gate_evidence
  FOREIGN KEY (gate_evidence_id) REFERENCES gate_evidence(id) ON DELETE SET NULL;

-- spec_validation_results → gate_evidence (optional)
ALTER TABLE spec_validation_results
  ADD CONSTRAINT fk_validation_gate_evidence
  FOREIGN KEY (gate_evidence_id) REFERENCES gate_evidence(id) ON DELETE SET NULL;

-- kill_switch_events → users (triggered_by, approved_by)
ALTER TABLE kill_switch_events
  ADD CONSTRAINT fk_kill_switch_triggered_by
  FOREIGN KEY (triggered_by_user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE kill_switch_events
  ADD CONSTRAINT fk_kill_switch_approved_by
  FOREIGN KEY (recovery_approved_by) REFERENCES users(id) ON DELETE SET NULL;
```

**Relationship Summary**:
- **governance_specifications** → **users** (owner_id) - Who owns this spec
- **vibecoding_signals** → **projects** (project_id) - Which project is being evaluated
- **vibecoding_signals** → **gate_evidence** (gate_evidence_id) - Link to gate submission
- **vibecoding_index_history** → **projects** (project_id) - Time-series per project
- **spec_validation_results** → **gate_evidence** (gate_evidence_id) - Validation evidence
- **kill_switch_events** → **users** (triggered_by, approved_by) - Who triggered/approved

---

## 📈 **ERD Diagram (14 New Tables + Existing 30)**

```
┌─────────────────────────────────────────────────────────────────┐
│                  EXISTING 30 TABLES (from Data-Model-ERD.md)    │
├─────────────────────────────────────────────────────────────────┤
│  Authentication: users, roles, user_roles, oauth_accounts,      │
│                  refresh_tokens, api_keys (6 tables)            │
│                                                                  │
│  Project: projects, project_members, webhooks (3 tables)        │
│                                                                  │
│  Gate Engine: gates, gate_approvals, gate_evidence,             │
│               policy_evaluations, stage_transitions (5 tables)  │
│                                                                  │
│  Policy: policies, policy_tests, custom_policies (3 tables)     │
│                                                                  │
│  AI Engine: ai_providers, ai_requests, ai_usage_logs,           │
│             ai_evidence_drafts (4 tables)                       │
│                                                                  │
│  System: audit_logs, notifications (2 tables)                   │
│                                                                  │
│  EP-06: ir_modules, codegen_generations, codegen_attempts,      │
│         codegen_escalations, codegen_evidence, vcr_requests     │
│         (6 tables)                                               │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Foreign Keys
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               NEW 14 TABLES (Governance System v2.0)            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Specification Management (7):                                  │
│  • governance_specifications ────→ users (owner_id)             │
│  • spec_versions                                                │
│  • spec_frontmatter_metadata                                    │
│  • spec_functional_requirements                                 │
│  • spec_acceptance_criteria                                     │
│  • spec_implementation_phases                                   │
│  • spec_cross_references                                        │
│                                                                  │
│  Anti-Vibecoding System (7):                                    │
│  • vibecoding_signals ────→ projects (project_id)               │
│                      └────→ gate_evidence (gate_evidence_id)    │
│  • vibecoding_index_history ────→ projects (project_id)         │
│  • progressive_routing_rules (seeded with 4 zones)              │
│  • kill_switch_triggers (seeded with 3 triggers)                │
│  • kill_switch_events ────→ users (triggered_by, approved_by)   │
│  • tier_specific_requirements                                   │
│  • spec_validation_results ────→ gate_evidence (evidence_id)    │
│                                                                  │
│  Total: 44 tables (30 existing + 14 new)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 **Migration Strategy**

### **Alembic Migration Sequence**

**Prerequisites**:
- PostgreSQL 15.5+
- Existing 33-table schema deployed
- `alembic` migration framework configured

**Migration Plan** (3 phases):

#### **Phase 1: Specification Management Tables (7 tables)**
**File**: `backend/alembic/versions/001_add_governance_spec_tables.py`

```python
"""Add governance specification tables

Revision ID: 001_gov_spec
Revises: <latest_existing_revision>
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ... SQL CREATE TABLE statements for tables 1-7
```

**Estimated Time**: 2 minutes (DDL only, no data)

---

#### **Phase 2: Anti-Vibecoding Tables (7 tables)**
**File**: `backend/alembic/versions/002_add_vibecoding_tables.py`

```python
"""Add anti-vibecoding system tables

Revision ID: 002_vibecoding
Revises: 001_gov_spec
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ... SQL CREATE TABLE statements for tables 8-14
# ... INSERT seed data for progressive_routing_rules (4 zones)
# ... INSERT seed data for kill_switch_triggers (3 triggers)
```

**Estimated Time**: 3 minutes (DDL + seed data)

---

#### **Phase 3: Indexes and Foreign Keys**
**File**: `backend/alembic/versions/003_add_governance_indexes_fks.py`

```python
"""Add indexes and foreign keys for governance tables

Revision ID: 003_gov_indexes
Revises: 002_vibecoding
Create Date: 2026-02-10

"""
from alembic import op

# ... CREATE INDEX statements (50+ indexes)
# ... ALTER TABLE ADD CONSTRAINT statements (10+ foreign keys)
```

**Estimated Time**: 5 minutes (index creation can be slow on large datasets)

---

### **Zero-Downtime Migration Steps**

1. **Pre-Migration**:
   - Backup database (PostgreSQL `pg_dump`)
   - Test migration on staging replica
   - Prepare rollback script

2. **Migration Execution**:
   ```bash
   # Apply migrations (production)
   alembic upgrade head
   ```

3. **Validation**:
   ```bash
   # Verify all 14 tables exist
   psql -c "\dt governance_*"
   psql -c "\dt vibecoding_*"
   psql -c "\dt spec_*"
   psql -c "\dt kill_switch_*"
   psql -c "\dt tier_specific_*"
   psql -c "\dt progressive_routing_*"

   # Verify foreign keys
   psql -c "\d+ governance_specifications"
   ```

4. **Rollback Plan** (if migration fails):
   ```bash
   # Rollback to previous revision
   alembic downgrade -1
   ```

5. **Post-Migration**:
   - Run `ANALYZE` on new tables (PostgreSQL statistics)
   - Monitor query performance (p95 latency target: <50ms)
   - Verify seed data loaded (4 routing rules, 3 kill switch triggers)

---

## 📊 **Index Strategy**

### **Performance Optimization**

**Primary Indexes** (created automatically with PRIMARY KEY, UNIQUE):
- All `id` columns (UUID PRIMARY KEY)
- All UNIQUE constraints (spec_id, zone, trigger_id, etc.)

**Secondary Indexes** (explicitly created):

**1. Foreign Key Indexes** (fast JOIN queries):
```sql
-- governance_specifications
CREATE INDEX idx_governance_specs_owner ON governance_specifications(owner_id);

-- vibecoding_signals
CREATE INDEX idx_signals_project ON vibecoding_signals(project_id);
CREATE INDEX idx_signals_gate_evidence ON vibecoding_signals(gate_evidence_id);

-- vibecoding_index_history
CREATE INDEX idx_index_history_project ON vibecoding_index_history(project_id);
CREATE INDEX idx_index_history_signal ON vibecoding_index_history(vibecoding_signal_id);

-- spec_validation_results
CREATE INDEX idx_validation_results_gate_evidence ON spec_validation_results(gate_evidence_id);
```

**2. Time-Series Indexes** (fast chronological queries):
```sql
-- Latest first (DESC) for dashboards
CREATE INDEX idx_index_history_calculated_at ON vibecoding_index_history(calculated_at DESC);
CREATE INDEX idx_validation_results_timestamp ON spec_validation_results(validation_timestamp DESC);
CREATE INDEX idx_kill_switch_events_triggered_at ON kill_switch_events(triggered_at DESC);
CREATE INDEX idx_spec_versions_date ON spec_versions(version_date DESC);
```

**3. Enum/Status Indexes** (fast filtering):
```sql
CREATE INDEX idx_governance_specs_status ON governance_specifications(status);
CREATE INDEX idx_func_requirements_status ON spec_functional_requirements(implementation_status);
CREATE INDEX idx_phases_status ON spec_implementation_phases(status);
CREATE INDEX idx_index_history_zone ON vibecoding_index_history(routing_zone);
CREATE INDEX idx_validation_results_status ON spec_validation_results(status);
```

**4. GIN Indexes** (JSONB, arrays, full-text search):
```sql
-- JSONB columns
CREATE INDEX idx_frontmatter_json ON spec_frontmatter_metadata USING GIN(frontmatter_json);
CREATE INDEX idx_validation_results_errors ON spec_validation_results USING GIN(validation_errors);
CREATE INDEX idx_tier_reqs_params ON tier_specific_requirements USING GIN(configuration_params);

-- Array columns
CREATE INDEX idx_governance_specs_tags ON governance_specifications USING GIN(tags);

-- Full-text search
CREATE INDEX idx_governance_specs_fts ON governance_specifications
  USING GIN(to_tsvector('english', title || ' ' || content_markdown));
```

**5. Composite Indexes** (common query patterns):
```sql
-- Spec + requirement lookup
CREATE INDEX idx_func_requirements_order ON spec_functional_requirements(spec_id, requirement_order);
CREATE INDEX idx_ac_order ON spec_acceptance_criteria(spec_id, ac_order);
CREATE INDEX idx_phases_order ON spec_implementation_phases(spec_id, phase_order);

-- Tier + applicability filtering
CREATE INDEX idx_tier_reqs_applicability ON tier_specific_requirements(tier, applicability);

-- Project + time-series (partitioning-ready)
-- CREATE INDEX idx_index_history_project_time ON vibecoding_index_history(project_id, calculated_at DESC);
```

### **Index Maintenance**

**Monitoring**:
```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public' AND tablename LIKE '%governance%' OR tablename LIKE '%vibecoding%'
ORDER BY idx_scan DESC;

-- Check index size
SELECT schemaname, tablename, indexname, pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

**Maintenance Schedule**:
- **Daily**: Auto-vacuum (PostgreSQL default)
- **Weekly**: `ANALYZE` on all governance tables
- **Monthly**: `REINDEX CONCURRENTLY` if index bloat detected

---

## 📦 **Data Retention Policies**

### **Retention Rules**

| Table | Retention Period | Rationale | Cleanup Strategy |
|-------|------------------|-----------|------------------|
| **governance_specifications** | Indefinite | Specifications never deleted, only deprecated | Mark status='DEPRECATED' |
| **spec_versions** | Indefinite | Version history preserved | No cleanup |
| **spec_frontmatter_metadata** | Indefinite | Linked to specs | No cleanup |
| **spec_functional_requirements** | Indefinite | Requirements preserved | No cleanup |
| **spec_acceptance_criteria** | Indefinite | Test history preserved | No cleanup |
| **spec_implementation_phases** | Indefinite | Progress tracking | No cleanup |
| **spec_cross_references** | Indefinite | Dependency tracking | No cleanup |
| **vibecoding_signals** | 90 days | Per SPEC-0001 evidence retention | `DELETE WHERE calculation_timestamp < NOW() - INTERVAL '90 days'` |
| **vibecoding_index_history** | 90 days | Time-series data (90-day trend window) | `DELETE WHERE calculated_at < NOW() - INTERVAL '90 days'` |
| **progressive_routing_rules** | Indefinite | Configuration data | No cleanup |
| **kill_switch_triggers** | Indefinite | Configuration data | No cleanup |
| **kill_switch_events** | 1 year | Per SPEC-0001 evidence retention | `DELETE WHERE triggered_at < NOW() - INTERVAL '1 year'` |
| **tier_specific_requirements** | Indefinite | Tier configurations | No cleanup |
| **spec_validation_results** | 90 days | Validation history (recent trend) | `DELETE WHERE validation_timestamp < NOW() - INTERVAL '90 days'` |

### **Cleanup Automation**

**Alembic Maintenance Migration**:
```python
"""Periodic cleanup governance tables

Revision ID: 999_cleanup_governance
Revises: <latest>
Create Date: Monthly (automated)

"""
from alembic import op

def upgrade():
    # vibecoding_signals (90 days)
    op.execute("""
        DELETE FROM vibecoding_signals
        WHERE calculation_timestamp < NOW() - INTERVAL '90 days'
    """)

    # vibecoding_index_history (90 days)
    op.execute("""
        DELETE FROM vibecoding_index_history
        WHERE calculated_at < NOW() - INTERVAL '90 days'
    """)

    # kill_switch_events (1 year)
    op.execute("""
        DELETE FROM kill_switch_events
        WHERE triggered_at < NOW() - INTERVAL '1 year'
    """)

    # spec_validation_results (90 days)
    op.execute("""
        DELETE FROM spec_validation_results
        WHERE validation_timestamp < NOW() - INTERVAL '90 days'
    """)

def downgrade():
    pass  # No rollback for cleanup
```

**Scheduling**: Run as monthly cron job (1st day of month, 02:00 UTC)

---

## 🔍 **Query Patterns & Performance**

### **Common Query Examples**

**Q1: Get latest Vibecoding Index for a project**
```sql
-- Target: <10ms p95
SELECT
  vih.index_value,
  vih.routing_zone,
  vih.routing_action,
  vih.calculated_at
FROM vibecoding_index_history vih
WHERE vih.project_id = :project_id
ORDER BY vih.calculated_at DESC
LIMIT 1;

-- Index used: idx_index_history_project, idx_index_history_calculated_at
```

**Q2: Get all functional requirements for a spec**
```sql
-- Target: <20ms p95
SELECT
  requirement_id,
  requirement_title,
  given_conditions,
  when_actions,
  then_outcomes,
  implementation_status
FROM spec_functional_requirements
WHERE spec_id = :spec_id
ORDER BY requirement_order ASC;

-- Index used: idx_func_requirements_spec_id, idx_func_requirements_order
```

**Q3: Check if kill switch is active**
```sql
-- Target: <50ms p95
SELECT
  kse.event_type,
  kse.triggered_at,
  kse.recovered_at,
  kst.trigger_name,
  kst.action
FROM kill_switch_events kse
JOIN kill_switch_triggers kst ON kse.kill_switch_trigger_id = kst.id
WHERE kse.event_type = 'ACTIVATED'
  AND kse.recovered_at IS NULL
ORDER BY kse.triggered_at DESC
LIMIT 1;

-- Index used: idx_kill_switch_events_type, idx_kill_switch_events_triggered_at
```

**Q4: Get tier-specific requirements for a project**
```sql
-- Target: <30ms p95
SELECT
  requirement_id,
  requirement_title,
  applicability,
  enforcement_mode,
  description
FROM tier_specific_requirements
WHERE spec_id = :spec_id
  AND tier = :tier  -- 'PROFESSIONAL' or 'ENTERPRISE'
  AND applicability IN ('REQUIRED', 'RECOMMENDED')
ORDER BY applicability DESC, requirement_id ASC;

-- Index used: idx_tier_reqs_spec_id, idx_tier_reqs_applicability
```

**Q5: Full-text search across specifications**
```sql
-- Target: <100ms p95
SELECT
  spec_id,
  title,
  version,
  status,
  ts_rank(to_tsvector('english', title || ' ' || content_markdown),
          plainto_tsquery('english', :search_query)) AS rank
FROM governance_specifications
WHERE to_tsvector('english', title || ' ' || content_markdown)
      @@ plainto_tsquery('english', :search_query)
ORDER BY rank DESC
LIMIT 20;

-- Index used: idx_governance_specs_fts (GIN index)
```

### **Performance Benchmarks**

**Target Latencies** (from SPRINT-118-TRACK-2-PLAN.md):
- Simple SELECT: <10ms p95
- JOIN (2 tables): <50ms p95
- Aggregate (1M rows): <500ms p95 (not applicable yet, dataset small)

**Initial Dataset Estimates**:
- governance_specifications: 2 rows (SPEC-0001, SPEC-0002) → ~20 rows (by SDLC 7.0)
- spec_functional_requirements: 16 rows (8 per spec) → ~160 rows
- spec_acceptance_criteria: 24 rows (12 per spec) → ~240 rows
- vibecoding_signals: ~100/day → ~9,000 rows (90-day retention)
- vibecoding_index_history: ~100/day → ~9,000 rows (90-day retention)
- kill_switch_events: ~1/month → ~12/year

**Scaling Considerations**:
- Time-series tables (vibecoding_index_history) may require partitioning at 1M+ rows
- Full-text search (governance_specifications) may require pg_trgm extension for fuzzy matching at 100+ specs

---

## ✅ **Schema Validation Checklist**

### **Pre-Implementation Review**

- [ ] **All 14 tables defined** with PRIMARY KEY, NOT NULL constraints
- [ ] **Foreign keys** to existing 33 tables (users, projects, gate_evidence)
- [ ] **50+ indexes** for query optimization (FK, time-series, enum, GIN, FTS)
- [ ] **JSONB fields** for flexible metadata (frontmatter, conditions, evidence)
- [ ] **Seed data** prepared for progressive_routing_rules (4 zones) and kill_switch_triggers (3 triggers)
- [ ] **Data retention policies** defined (90 days, 1 year, indefinite)
- [ ] **Migration scripts** drafted (3-phase Alembic migrations)
- [ ] **Rollback plan** tested on staging replica
- [ ] **Performance targets** validated (<50ms p95 for all queries)
- [ ] **CTO approval** obtained before implementation

---

## 🔄 **Next Steps (D2: API Architecture)**

After CTO approval of this schema design, proceed to:

**D2: API Architecture Design** (12 endpoints, OpenAPI 3.0)
- `POST /api/v1/governance/specs/validate`
- `POST /api/v1/governance/vibecoding/calculate`
- `GET /api/v1/governance/vibecoding/{submission_id}`
- ... (9 more endpoints)

**Document**: `docs/01-planning/05-API-Design/API-Specification-Governance-v2.md`

---

## 📝 **Changelog**

### v2.0.0 (January 28, 2026)
- Initial database schema design for SPEC-0001/0002 automation
- 14 new tables across 2 groups (Specification Management, Anti-Vibecoding)
- 50+ indexes for query optimization
- 3-phase Alembic migration plan
- Data retention policies (90 days, 1 year)
- Zero-downtime migration strategy
- Performance targets (<50ms p95)

---

**Document Status**: ✅ **DESIGN COMPLETE - AWAITING CTO APPROVAL**

**Next Action**: CTO review (January 29, 2026)

**Implementation**: Sprint 118 Day 1-2 (February 10-11, 2026)

---

*Database Schema Design - Governance System v2.0*
*14 Tables for SPEC-0001/0002 Automation*
*Production-ready design with zero-downtime migration*
