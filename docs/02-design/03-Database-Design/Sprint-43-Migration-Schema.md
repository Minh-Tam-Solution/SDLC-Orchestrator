# Sprint 43 Database Migration Schema
## Policy Guards & Evidence Timeline

---

**Document Information**

| Field | Value |
|-------|-------|
| **Document ID** | DBS-043-001 |
| **Version** | 1.0.0 |
| **Status** | DRAFT |
| **Created** | 2025-12-22 |
| **Author** | Backend Lead |
| **Sprint** | 43 |
| **Migration ID** | 043_policy_guards_evidence |

---

## 1. Overview

This document defines the database schema migrations required for Sprint 43:
- Policy Packs and Rules (OPA integration)
- Evidence Events and Overrides
- Policy Evaluations history

---

## 2. New Tables

### 2.1 policy_packs

Stores policy pack configuration per project.

```sql
-- Migration: 043_01_create_policy_packs.py

CREATE TABLE policy_packs (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Keys
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Policy Pack Definition
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    version VARCHAR(20) NOT NULL CHECK (version ~ '^\d+\.\d+\.\d+$'),
    tier VARCHAR(20) NOT NULL CHECK (tier IN ('lite', 'standard', 'professional', 'enterprise')),

    -- Validator Configuration (JSONB)
    validators JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- Schema: [{ "name": "lint", "enabled": true, "blocking": true, "config": {} }]

    -- Coverage Settings
    coverage_threshold INTEGER NOT NULL DEFAULT 80 CHECK (coverage_threshold >= 0 AND coverage_threshold <= 100),
    coverage_blocking BOOLEAN NOT NULL DEFAULT FALSE,

    -- Architecture Rules (JSONB arrays)
    forbidden_imports JSONB NOT NULL DEFAULT '[]'::jsonb,
    required_patterns JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_policy_packs_project UNIQUE (project_id)
);

-- Indexes
CREATE INDEX idx_policy_packs_project_id ON policy_packs(project_id);
CREATE INDEX idx_policy_packs_tier ON policy_packs(tier);
CREATE INDEX idx_policy_packs_created_at ON policy_packs(created_at);

-- Trigger for updated_at
CREATE TRIGGER trg_policy_packs_updated_at
    BEFORE UPDATE ON policy_packs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE policy_packs IS 'Policy pack configuration per project for AI Safety validation';
COMMENT ON COLUMN policy_packs.validators IS 'List of validator configurations (lint, test, coverage, sast, policy_guards)';
COMMENT ON COLUMN policy_packs.forbidden_imports IS 'List of import patterns to block (e.g., ["app.legacy", "deprecated"])';
```

### 2.2 policy_rules

Stores individual OPA policy rules.

```sql
-- Migration: 043_02_create_policy_rules.py

CREATE TABLE policy_rules (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key
    policy_pack_id UUID NOT NULL REFERENCES policy_packs(id) ON DELETE CASCADE,

    -- Policy Definition
    policy_id VARCHAR(100) NOT NULL,  -- e.g., "no-hardcoded-secrets"
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    rego_policy TEXT NOT NULL,  -- Rego policy code
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    blocking BOOLEAN NOT NULL DEFAULT TRUE,
    message_template TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_policy_rules_pack_policy_id UNIQUE (policy_pack_id, policy_id),
    CONSTRAINT chk_policy_id_format CHECK (policy_id ~ '^[a-z0-9-]+$'),
    CONSTRAINT chk_rego_policy_min_length CHECK (length(rego_policy) >= 50)
);

-- Indexes
CREATE INDEX idx_policy_rules_pack_id ON policy_rules(policy_pack_id);
CREATE INDEX idx_policy_rules_severity ON policy_rules(severity);
CREATE INDEX idx_policy_rules_enabled ON policy_rules(enabled);
CREATE INDEX idx_policy_rules_tags ON policy_rules USING GIN (tags);

-- Trigger for updated_at
CREATE TRIGGER trg_policy_rules_updated_at
    BEFORE UPDATE ON policy_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE policy_rules IS 'Individual OPA Rego policy rules within a policy pack';
COMMENT ON COLUMN policy_rules.rego_policy IS 'Complete Rego policy code for OPA evaluation';
COMMENT ON COLUMN policy_rules.message_template IS 'Error message template with {file}, {line} placeholders';
```

### 2.3 evidence_events

Stores all AI detection events.

```sql
-- Migration: 043_03_create_evidence_events.py

CREATE TABLE evidence_events (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Keys
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- PR Information
    pr_number INTEGER NOT NULL,
    pr_title VARCHAR(500),
    pr_author VARCHAR(100),
    pr_url VARCHAR(500),

    -- Detection Results
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ai_tool VARCHAR(50),  -- cursor, copilot, claude, chatgpt, windsurf, cody, tabnine, other, null
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    detection_method VARCHAR(50) NOT NULL,  -- metadata, commit, pattern, combined

    -- Strategy Scores (for audit)
    strategy_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Schema: { "metadata": 0.8, "commit": 0.7, "pattern": 0.3 }

    -- Validation Results
    validation_status VARCHAR(20) NOT NULL CHECK (validation_status IN ('pending', 'passed', 'failed', 'skipped', 'error')),
    validation_results JSONB,
    -- Schema: [{ "validator": "lint", "status": "passed", "duration_ms": 45, "details": {} }]
    validation_duration_ms INTEGER,

    -- Evidence Data (immutable, for audit)
    evidence_data JSONB NOT NULL,
    -- Schema: { "title": "...", "body": "...", "commits": [...], "matched_patterns": [...] }
    evidence_hash VARCHAR(64) NOT NULL,  -- SHA256 of evidence_data

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()

    -- Note: No updated_at - evidence is immutable
);

-- Indexes
CREATE INDEX idx_evidence_events_project_id ON evidence_events(project_id);
CREATE INDEX idx_evidence_events_pr_number ON evidence_events(project_id, pr_number);
CREATE INDEX idx_evidence_events_ai_tool ON evidence_events(ai_tool);
CREATE INDEX idx_evidence_events_confidence ON evidence_events(confidence);
CREATE INDEX idx_evidence_events_validation_status ON evidence_events(validation_status);
CREATE INDEX idx_evidence_events_detected_at ON evidence_events(detected_at DESC);
CREATE INDEX idx_evidence_events_created_at ON evidence_events(created_at DESC);

-- Partial index for AI-detected events
CREATE INDEX idx_evidence_events_ai_detected ON evidence_events(project_id, detected_at DESC)
    WHERE ai_tool IS NOT NULL;

-- Comments
COMMENT ON TABLE evidence_events IS 'Immutable record of all AI detection events for audit trail';
COMMENT ON COLUMN evidence_events.evidence_hash IS 'SHA256 hash of evidence_data for integrity verification';
COMMENT ON COLUMN evidence_events.strategy_scores IS 'Individual scores from each detection strategy';
```

### 2.4 evidence_overrides

Stores override requests and decisions.

```sql
-- Migration: 043_04_create_evidence_overrides.py

CREATE TABLE evidence_overrides (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Keys
    evidence_event_id UUID NOT NULL REFERENCES evidence_events(id) ON DELETE CASCADE,
    requested_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    decided_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Override Request
    override_type VARCHAR(30) NOT NULL CHECK (override_type IN ('false_positive', 'approved_risk', 'emergency')),
    reason TEXT NOT NULL CHECK (length(reason) >= 50),

    -- Decision
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    decision_reason TEXT,
    decided_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_evidence_overrides_event_id ON evidence_overrides(evidence_event_id);
CREATE INDEX idx_evidence_overrides_status ON evidence_overrides(status);
CREATE INDEX idx_evidence_overrides_requested_by ON evidence_overrides(requested_by);
CREATE INDEX idx_evidence_overrides_decided_by ON evidence_overrides(decided_by);
CREATE INDEX idx_evidence_overrides_created_at ON evidence_overrides(created_at DESC);

-- Partial index for pending overrides
CREATE INDEX idx_evidence_overrides_pending ON evidence_overrides(created_at DESC)
    WHERE status = 'pending';

-- Trigger for updated_at
CREATE TRIGGER trg_evidence_overrides_updated_at
    BEFORE UPDATE ON evidence_overrides
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE evidence_overrides IS 'Override requests and decisions for blocked AI PRs';
COMMENT ON COLUMN evidence_overrides.override_type IS 'Type of override: false_positive, approved_risk, or emergency';
```

### 2.5 policy_evaluations

Stores policy evaluation history for analytics.

```sql
-- Migration: 043_05_create_policy_evaluations.py

CREATE TABLE policy_evaluations (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Keys
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    policy_pack_id UUID REFERENCES policy_packs(id) ON DELETE SET NULL,
    evidence_event_id UUID REFERENCES evidence_events(id) ON DELETE SET NULL,

    -- PR Information
    pr_number INTEGER NOT NULL,

    -- Evaluation Results
    total_policies INTEGER NOT NULL,
    passed_count INTEGER NOT NULL,
    failed_count INTEGER NOT NULL,
    blocked BOOLEAN NOT NULL,
    results JSONB NOT NULL,
    -- Schema: [{ "policy_id": "...", "passed": true, "severity": "high", "message": null }]

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_ms INTEGER NOT NULL,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_policy_evaluations_project_id ON policy_evaluations(project_id);
CREATE INDEX idx_policy_evaluations_pr ON policy_evaluations(project_id, pr_number);
CREATE INDEX idx_policy_evaluations_policy_pack_id ON policy_evaluations(policy_pack_id);
CREATE INDEX idx_policy_evaluations_blocked ON policy_evaluations(blocked);
CREATE INDEX idx_policy_evaluations_created_at ON policy_evaluations(created_at DESC);

-- Comments
COMMENT ON TABLE policy_evaluations IS 'History of policy evaluations for analytics and debugging';
```

---

## 3. Alembic Migration Files

### 3.1 Migration Template

```python
# backend/alembic/versions/043_01_create_policy_packs.py

"""Create policy_packs table

Revision ID: 043_01
Revises: 042_xx  # Previous migration
Create Date: 2026-02-03 09:00:00.000000

Sprint: 43 - Policy Guards & Evidence UI
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '043_01'
down_revision = '042_xx'  # Update with actual previous revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create policy_packs table
    op.create_table(
        'policy_packs',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', UUID(), nullable=False),
        sa.Column('created_by', UUID(), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('tier', sa.String(20), nullable=False),
        sa.Column('validators', JSONB(), server_default='[]', nullable=False),
        sa.Column('coverage_threshold', sa.Integer(), server_default='80', nullable=False),
        sa.Column('coverage_blocking', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('forbidden_imports', JSONB(), server_default='[]', nullable=False),
        sa.Column('required_patterns', JSONB(), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('project_id', name='uq_policy_packs_project'),
        sa.CheckConstraint("tier IN ('lite', 'standard', 'professional', 'enterprise')", name='chk_policy_packs_tier'),
        sa.CheckConstraint("version ~ '^\\d+\\.\\d+\\.\\d+$'", name='chk_policy_packs_version'),
        sa.CheckConstraint('coverage_threshold >= 0 AND coverage_threshold <= 100', name='chk_policy_packs_coverage'),
    )

    # Create indexes
    op.create_index('idx_policy_packs_project_id', 'policy_packs', ['project_id'])
    op.create_index('idx_policy_packs_tier', 'policy_packs', ['tier'])
    op.create_index('idx_policy_packs_created_at', 'policy_packs', ['created_at'])

    # Create updated_at trigger
    op.execute("""
        CREATE TRIGGER trg_policy_packs_updated_at
            BEFORE UPDATE ON policy_packs
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    op.execute('DROP TRIGGER IF EXISTS trg_policy_packs_updated_at ON policy_packs')
    op.drop_table('policy_packs')
```

### 3.2 Full Migration Script

```python
# backend/alembic/versions/043_00_policy_guards_evidence.py

"""Sprint 43: Policy Guards and Evidence Timeline

Revision ID: 043_00
Revises: 042_xx
Create Date: 2026-02-03 09:00:00.000000

Sprint: 43 - Policy Guards & Evidence UI

Tables created:
- policy_packs: Policy pack configuration per project
- policy_rules: Individual OPA Rego policy rules
- evidence_events: AI detection events (immutable)
- evidence_overrides: Override requests and decisions
- policy_evaluations: Policy evaluation history
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '043_00'
down_revision = '042_xx'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # 1. policy_packs
    # =========================================================================
    op.create_table(
        'policy_packs',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', UUID(), nullable=False),
        sa.Column('created_by', UUID(), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('tier', sa.String(20), nullable=False),
        sa.Column('validators', JSONB(), server_default='[]', nullable=False),
        sa.Column('coverage_threshold', sa.Integer(), server_default='80', nullable=False),
        sa.Column('coverage_blocking', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('forbidden_imports', JSONB(), server_default='[]', nullable=False),
        sa.Column('required_patterns', JSONB(), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('project_id', name='uq_policy_packs_project'),
    )
    op.create_index('idx_policy_packs_project_id', 'policy_packs', ['project_id'])

    # =========================================================================
    # 2. policy_rules
    # =========================================================================
    op.create_table(
        'policy_rules',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('policy_pack_id', UUID(), nullable=False),
        sa.Column('policy_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('rego_policy', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('blocking', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('message_template', sa.Text(), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('tags', JSONB(), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['policy_pack_id'], ['policy_packs.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('policy_pack_id', 'policy_id', name='uq_policy_rules_pack_policy_id'),
    )
    op.create_index('idx_policy_rules_pack_id', 'policy_rules', ['policy_pack_id'])
    op.create_index('idx_policy_rules_severity', 'policy_rules', ['severity'])

    # =========================================================================
    # 3. evidence_events
    # =========================================================================
    op.create_table(
        'evidence_events',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', UUID(), nullable=False),
        sa.Column('pr_number', sa.Integer(), nullable=False),
        sa.Column('pr_title', sa.String(500), nullable=True),
        sa.Column('pr_author', sa.String(100), nullable=True),
        sa.Column('pr_url', sa.String(500), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ai_tool', sa.String(50), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('detection_method', sa.String(50), nullable=False),
        sa.Column('strategy_scores', JSONB(), server_default='{}', nullable=False),
        sa.Column('validation_status', sa.String(20), nullable=False),
        sa.Column('validation_results', JSONB(), nullable=True),
        sa.Column('validation_duration_ms', sa.Integer(), nullable=True),
        sa.Column('evidence_data', JSONB(), nullable=False),
        sa.Column('evidence_hash', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_evidence_events_project_id', 'evidence_events', ['project_id'])
    op.create_index('idx_evidence_events_pr', 'evidence_events', ['project_id', 'pr_number'])
    op.create_index('idx_evidence_events_detected_at', 'evidence_events', ['detected_at'])

    # =========================================================================
    # 4. evidence_overrides
    # =========================================================================
    op.create_table(
        'evidence_overrides',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('evidence_event_id', UUID(), nullable=False),
        sa.Column('requested_by', UUID(), nullable=False),
        sa.Column('decided_by', UUID(), nullable=True),
        sa.Column('override_type', sa.String(30), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['evidence_event_id'], ['evidence_events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['decided_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_evidence_overrides_event_id', 'evidence_overrides', ['evidence_event_id'])
    op.create_index('idx_evidence_overrides_status', 'evidence_overrides', ['status'])

    # =========================================================================
    # 5. policy_evaluations
    # =========================================================================
    op.create_table(
        'policy_evaluations',
        sa.Column('id', UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', UUID(), nullable=False),
        sa.Column('policy_pack_id', UUID(), nullable=True),
        sa.Column('evidence_event_id', UUID(), nullable=True),
        sa.Column('pr_number', sa.Integer(), nullable=False),
        sa.Column('total_policies', sa.Integer(), nullable=False),
        sa.Column('passed_count', sa.Integer(), nullable=False),
        sa.Column('failed_count', sa.Integer(), nullable=False),
        sa.Column('blocked', sa.Boolean(), nullable=False),
        sa.Column('results', JSONB(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['policy_pack_id'], ['policy_packs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['evidence_event_id'], ['evidence_events.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_policy_evaluations_project_id', 'policy_evaluations', ['project_id'])
    op.create_index('idx_policy_evaluations_created_at', 'policy_evaluations', ['created_at'])


def downgrade() -> None:
    op.drop_table('policy_evaluations')
    op.drop_table('evidence_overrides')
    op.drop_table('evidence_events')
    op.drop_table('policy_rules')
    op.drop_table('policy_packs')
```

---

## 4. SQLAlchemy Models

```python
# backend/app/models/policy_pack.py

from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DateTime, Float, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class PolicyPack(Base):
    __tablename__ = "policy_packs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    version = Column(String(20), nullable=False)
    tier = Column(String(20), nullable=False)

    validators = Column(JSONB, nullable=False, default=list)
    coverage_threshold = Column(Integer, nullable=False, default=80)
    coverage_blocking = Column(Boolean, nullable=False, default=False)
    forbidden_imports = Column(JSONB, nullable=False, default=list)
    required_patterns = Column(JSONB, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="policy_pack")
    creator = relationship("User", foreign_keys=[created_by])
    rules = relationship("PolicyRule", back_populates="policy_pack", cascade="all, delete-orphan")


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_pack_id = Column(UUID(as_uuid=True), ForeignKey("policy_packs.id", ondelete="CASCADE"), nullable=False)

    policy_id = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    rego_policy = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)
    blocking = Column(Boolean, nullable=False, default=True)
    message_template = Column(Text, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    tags = Column(JSONB, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    policy_pack = relationship("PolicyPack", back_populates="rules")

    __table_args__ = (
        CheckConstraint("severity IN ('critical', 'high', 'medium', 'low', 'info')"),
    )


class EvidenceEvent(Base):
    __tablename__ = "evidence_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    pr_number = Column(Integer, nullable=False)
    pr_title = Column(String(500), nullable=True)
    pr_author = Column(String(100), nullable=True)
    pr_url = Column(String(500), nullable=True)

    detected_at = Column(DateTime(timezone=True), nullable=False)
    ai_tool = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=False)
    detection_method = Column(String(50), nullable=False)
    strategy_scores = Column(JSONB, nullable=False, default=dict)

    validation_status = Column(String(20), nullable=False)
    validation_results = Column(JSONB, nullable=True)
    validation_duration_ms = Column(Integer, nullable=True)

    evidence_data = Column(JSONB, nullable=False)
    evidence_hash = Column(String(64), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="evidence_events")
    overrides = relationship("EvidenceOverride", back_populates="evidence_event", cascade="all, delete-orphan")


class EvidenceOverride(Base):
    __tablename__ = "evidence_overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_event_id = Column(UUID(as_uuid=True), ForeignKey("evidence_events.id", ondelete="CASCADE"), nullable=False)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    decided_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    override_type = Column(String(30), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    decision_reason = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    evidence_event = relationship("EvidenceEvent", back_populates="overrides")
    requester = relationship("User", foreign_keys=[requested_by])
    decider = relationship("User", foreign_keys=[decided_by])
```

---

## 5. Data Migration

### 5.1 Seed Default Policy Packs

```python
# backend/app/db/seed/seed_default_policies.py

DEFAULT_POLICIES = [
    {
        "policy_id": "no-hardcoded-secrets",
        "name": "No Hardcoded Secrets",
        "description": "Detects hardcoded passwords, API keys, and secrets in AI-generated code",
        "severity": "critical",
        "blocking": True,
        "rego_policy": """...""",  # See Policy-Guards-Design.md
        "message_template": "Hardcoded secret detected in {file} at line {line}",
        "tags": ["security", "secrets"],
    },
    {
        "policy_id": "architecture-boundaries",
        "name": "Architecture Boundaries",
        "description": "Enforces layer separation (presentation -> business -> data)",
        "severity": "high",
        "blocking": True,
        "rego_policy": """...""",
        "message_template": "Architecture violation: {message}",
        "tags": ["architecture", "layers"],
    },
    # ... more default policies
]
```

---

## 6. Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-22 | Backend Lead | Initial schema design |

---

**Approvals**

| Role | Name | Date | Status |
|------|------|------|--------|
| CTO | | | PENDING |
| DBA | | | PENDING |
| Backend Lead | | | PENDING |
