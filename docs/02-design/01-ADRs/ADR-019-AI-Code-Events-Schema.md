# ADR-019: AI Code Events Schema
## Architecture Decision Record - AI Safety Layer Foundation

**Status**: ✅ **APPROVED**
**Date**: January 6, 2026
**Author**: Backend Team + CTO
**Deciders**: CTO, Backend Lead, DBA
**Framework**: SDLC 6.1.0
**Epic**: EP-02 AI Safety Layer v1
**Sprint**: Sprint 41 - AI Safety Foundation

---

## Context

EP-02 AI Safety Layer v1 requires comprehensive logging of all AI-generated code events for:
1. **Audit Trail** - Full evidence of AI tool usage, validation results, policy decisions
2. **Compliance** - HIPAA/SOC 2 requirement for AI code traceability
3. **Analytics** - Track AI adoption, validation success rates, policy effectiveness
4. **Evidence Vault** - Integration with existing evidence collection system

### Current State

**Existing Evidence Infrastructure**:
- Evidence Vault (MinIO S3) - stores file artifacts
- `evidence` table - metadata for manual evidence uploads
- `audit_logs` table - user action logs
- No AI-specific event tracking

### Requirements

**Functional Requirements (FR)**:
- **FR-AI-001**: Track all AI-generated PRs (auto-detected or manually tagged)
- **FR-AI-002**: Record validation pipeline execution and results
- **FR-AI-003**: Store policy evaluation outcomes (pass/fail/override)
- **FR-AI-004**: Link to Evidence Vault artifacts (diffs, test results)
- **FR-AI-005**: Support VCR (Validation Code Review) override workflow

**Non-Functional Requirements (NFR)**:
- **NFR-AI-001**: Query performance <100ms p95 for dashboard views
- **NFR-AI-002**: Schema extensible for future AI tools/validators
- **NFR-AI-003**: GDPR-compliant (no raw prompts, only hashes)
- **NFR-AI-004**: Retention policy: 2 years active, 5 years archive

---

## Decision

Create a **new dedicated table** `ai_code_events` instead of extending existing schemas.

### Rationale

**Why New Table (Not Extend Existing)**:
1. ✅ **Separation of Concerns** - AI events have unique lifecycle vs manual evidence
2. ✅ **Schema Flexibility** - AI-specific fields (tool, model, confidence) don't fit existing tables
3. ✅ **Performance** - Avoid polluting high-traffic `audit_logs` with heavy AI metadata
4. ✅ **Data Retention** - Different retention policy (2yr vs 7yr for audit logs)
5. ✅ **Query Optimization** - AI-specific indexes without affecting existing queries

**Alternative Considered**:
- **JSONB column in `evidence` table** ❌ Rejected - poor queryability, no type safety
- **Separate microservice DB** ❌ Rejected - adds complexity, cross-DB joins expensive
- **Event sourcing system** ❌ Rejected - overkill for v1, defer to v2

---

## Schema Design

### Database Model

```python
# backend/app/models/ai_code_event.py
from sqlalchemy import Column, String, DateTime, JSON, Enum, ForeignKey, Integer, Float, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum
from uuid import uuid4
from datetime import datetime

class AIToolType(str, enum.Enum):
    """AI coding tools detection enum."""
    CURSOR = "cursor"
    COPILOT = "copilot"
    CLAUDE_CODE = "claude_code"
    CHATGPT = "chatgpt"
    WINDSURF = "windsurf"
    CODY = "cody"
    TABNINE = "tabnine"
    OTHER = "other"
    MANUAL_TAG = "manual_tag"  # User-marked as AI-generated

class ValidationStatus(str, enum.Enum):
    """Validation pipeline status enum."""
    PENDING = "pending"        # Queued for validation
    RUNNING = "running"        # Validators executing
    PASSED = "passed"          # All validators passed
    FAILED = "failed"          # At least one blocking validator failed
    PARTIAL_PASS = "partial_pass"  # Some non-blocking validators failed
    OVERRIDDEN = "overridden"  # VCR approved despite failures
    ERROR = "error"            # Pipeline error (not validation failure)

class AICodeEvent(Base):
    """
    AI Code Event - Evidence record for AI-generated code.

    Lifecycle:
    1. PR detected as AI-generated (auto or manual)
    2. Event created with PENDING status
    3. Validation pipeline triggered
    4. Validators run, results aggregated
    5. Policy engine evaluates pass/fail
    6. Status updated to PASSED/FAILED
    7. (Optional) VCR override if FAILED
    8. Evidence stored in Vault

    Retention:
    - Active: 2 years from created_at
    - Archive: Move to cold storage after 2 years
    - Delete: After 5 years total (compliance requirement)
    """
    __tablename__ = "ai_code_events"

    # =========================================================================
    # Primary Key & Timestamps
    # =========================================================================
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # =========================================================================
    # PR Information (Source of AI Code)
    # =========================================================================
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    pr_number = Column(String(50), nullable=False)  # e.g., "123" (GitHub PR number)
    pr_url = Column(String(500))                     # Full URL to PR
    pr_title = Column(String(500))
    pr_author = Column(String(100))                  # GitHub username
    pr_branch = Column(String(255))                  # Source branch name
    pr_base_branch = Column(String(255))             # Target branch (usually main/master)
    pr_created_at = Column(DateTime)                 # When PR was opened
    pr_merged_at = Column(DateTime, nullable=True)   # NULL if not merged yet

    # =========================================================================
    # AI Tool Detection
    # =========================================================================
    ai_tool = Column(Enum(AIToolType), nullable=False, index=True)
    ai_model = Column(String(100))                   # e.g., "gpt-4-turbo", "claude-3-opus"
    ai_model_version = Column(String(50))            # e.g., "0125" for GPT-4
    detection_method = Column(String(50), nullable=False)  # "metadata", "commit_msg", "manual", "api"
    detection_confidence = Column(Float)             # 0.0 - 1.0 (NULL for manual tags)
    detection_evidence = Column(JSONB)               # JSON with detection details

    # Example detection_evidence:
    # {
    #   "markers_found": ["cursor", "AI-generated"],
    #   "commit_messages": ["feat: add login with Cursor AI"],
    #   "pr_description_keywords": ["generated by Cursor"],
    #   "committer_email": "cursor@anthropic.com"
    # }

    # =========================================================================
    # Code Change Metrics
    # =========================================================================
    files_changed = Column(JSONB)                    # List of file paths
    files_changed_count = Column(Integer)
    lines_added = Column(Integer)
    lines_removed = Column(Integer)
    lines_total = Column(Integer)                    # lines_added + lines_removed
    commits_count = Column(Integer)

    # Example files_changed:
    # [
    #   {
    #     "path": "src/auth/login.ts",
    #     "additions": 45,
    #     "deletions": 12,
    #     "changes": 57
    #   }
    # ]

    # =========================================================================
    # Validation Pipeline Results
    # =========================================================================
    validation_status = Column(
        Enum(ValidationStatus),
        default=ValidationStatus.PENDING,
        nullable=False,
        index=True
    )
    validation_started_at = Column(DateTime)
    validation_completed_at = Column(DateTime)
    validation_duration_ms = Column(Integer)         # Total pipeline duration

    validators_run = Column(JSONB)                   # List of validators executed
    validators_passed = Column(JSONB)                # List of passed validators
    validators_failed = Column(JSONB)                # List of failed validators

    # Example validators_run:
    # [
    #   {
    #     "name": "eslint",
    #     "status": "passed",
    #     "duration_ms": 1234,
    #     "errors": 0,
    #     "warnings": 2
    #   },
    #   {
    #     "name": "pytest",
    #     "status": "failed",
    #     "duration_ms": 5678,
    #     "tests_run": 150,
    #     "tests_failed": 3,
    #     "failure_details": ["test_login_invalid_password", ...]
    #   }
    # ]

    # =========================================================================
    # Policy Evaluation Results
    # =========================================================================
    policy_pack_id = Column(UUID(as_uuid=True), ForeignKey("policy_packs.id"), nullable=True)
    policy_results = Column(JSONB)                   # Per-policy pass/fail
    blocking_policies_failed = Column(JSONB)         # List of failed mandatory policies
    non_blocking_policies_failed = Column(JSONB)     # List of failed optional policies

    # Example policy_results:
    # {
    #   "no_ai_in_auth": {"status": "failed", "severity": "critical"},
    #   "require_tests": {"status": "passed"},
    #   "min_coverage_80": {"status": "failed", "severity": "high", "actual": 65}
    # }

    # =========================================================================
    # VCR (Validation Code Review) Override
    # =========================================================================
    override_approved = Column(Boolean, default=False, nullable=False)
    override_reason = Column(Text)                   # Justification for override
    override_approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    override_approved_at = Column(DateTime, nullable=True)
    override_ticket_url = Column(String(500))        # Link to Jira/Linear ticket

    # =========================================================================
    # Evidence Vault Links
    # =========================================================================
    evidence_vault_path = Column(String(500))        # S3 path to evidence bundle
    evidence_artifacts = Column(JSONB)               # List of stored artifacts

    # Example evidence_artifacts:
    # [
    #   {"type": "diff", "path": "s3://evidence/pr-123-diff.patch", "size_bytes": 12345},
    #   {"type": "test_results", "path": "s3://evidence/pr-123-pytest.xml", "size_bytes": 6789},
    #   {"type": "coverage", "path": "s3://evidence/pr-123-coverage.html", "size_bytes": 45678}
    # ]

    # =========================================================================
    # Security & Privacy
    # =========================================================================
    prompt_hash = Column(String(64))                 # SHA-256 of AI prompt (redacted, not stored)
    prompt_redacted_preview = Column(Text)           # First 100 chars (PII removed)
    contains_secrets = Column(Boolean, default=False) # Flagged by secret scanner

    # =========================================================================
    # Metadata
    # =========================================================================
    tags = Column(JSONB)                             # Custom tags (e.g., ["refactoring", "bug-fix"])
    notes = Column(Text)                             # Additional context

    # =========================================================================
    # Relationships
    # =========================================================================
    project = relationship("Project", back_populates="ai_code_events")
    policy_pack = relationship("PolicyPack")
    override_approver = relationship("User", foreign_keys=[override_approved_by])
```

### Indexes for Performance

```sql
-- Primary lookup patterns (NFR-AI-001: <100ms p95)

-- 1. List AI events by project (dashboard view)
CREATE INDEX idx_ai_code_events_project_created
ON ai_code_events(project_id, created_at DESC);

-- 2. Filter by validation status (pending/failed PRs)
CREATE INDEX idx_ai_code_events_status
ON ai_code_events(validation_status, created_at DESC);

-- 3. Filter by AI tool (analytics by tool type)
CREATE INDEX idx_ai_code_events_ai_tool
ON ai_code_events(ai_tool, created_at DESC);

-- 4. Find events needing override (VCR workflow)
CREATE INDEX idx_ai_code_events_override
ON ai_code_events(override_approved, validation_status)
WHERE validation_status = 'failed';

-- 5. Timeline view (Evidence UI)
CREATE INDEX idx_ai_code_events_timeline
ON ai_code_events(project_id, validation_started_at DESC)
WHERE validation_started_at IS NOT NULL;

-- 6. Policy pack effectiveness (analytics)
CREATE INDEX idx_ai_code_events_policy_pack
ON ai_code_events(policy_pack_id, validation_status);

-- 7. JSONB search on files changed (architecture checks)
CREATE INDEX idx_ai_code_events_files_gin
ON ai_code_events USING gin(files_changed jsonb_path_ops);
```

### Alembic Migration

```python
# backend/alembic/versions/019_add_ai_code_events_table.py
"""add ai_code_events table

Revision ID: 019_ai_code_events
Revises: 018_previous_migration
Create Date: 2026-01-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '019_ai_code_events'
down_revision = '018_previous_migration'
branch_labels = None
depends_on = None

def upgrade():
    # Create enum types
    op.execute("""
        CREATE TYPE aitooltype AS ENUM (
            'cursor', 'copilot', 'claude_code', 'chatgpt',
            'windsurf', 'cody', 'tabnine', 'other', 'manual_tag'
        );
    """)

    op.execute("""
        CREATE TYPE validationstatus AS ENUM (
            'pending', 'running', 'passed', 'failed',
            'partial_pass', 'overridden', 'error'
        );
    """)

    # Create table
    op.create_table(
        'ai_code_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),

        # PR info
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pr_number', sa.String(50), nullable=False),
        sa.Column('pr_url', sa.String(500)),
        sa.Column('pr_title', sa.String(500)),
        sa.Column('pr_author', sa.String(100)),
        sa.Column('pr_branch', sa.String(255)),
        sa.Column('pr_base_branch', sa.String(255)),
        sa.Column('pr_created_at', sa.DateTime()),
        sa.Column('pr_merged_at', sa.DateTime()),

        # AI detection
        sa.Column('ai_tool', sa.Enum('aitooltype', name='aitooltype'), nullable=False),
        sa.Column('ai_model', sa.String(100)),
        sa.Column('ai_model_version', sa.String(50)),
        sa.Column('detection_method', sa.String(50), nullable=False),
        sa.Column('detection_confidence', sa.Float()),
        sa.Column('detection_evidence', postgresql.JSONB()),

        # Code metrics
        sa.Column('files_changed', postgresql.JSONB()),
        sa.Column('files_changed_count', sa.Integer()),
        sa.Column('lines_added', sa.Integer()),
        sa.Column('lines_removed', sa.Integer()),
        sa.Column('lines_total', sa.Integer()),
        sa.Column('commits_count', sa.Integer()),

        # Validation
        sa.Column('validation_status', sa.Enum('validationstatus', name='validationstatus'), nullable=False),
        sa.Column('validation_started_at', sa.DateTime()),
        sa.Column('validation_completed_at', sa.DateTime()),
        sa.Column('validation_duration_ms', sa.Integer()),
        sa.Column('validators_run', postgresql.JSONB()),
        sa.Column('validators_passed', postgresql.JSONB()),
        sa.Column('validators_failed', postgresql.JSONB()),

        # Policy
        sa.Column('policy_pack_id', postgresql.UUID(as_uuid=True)),
        sa.Column('policy_results', postgresql.JSONB()),
        sa.Column('blocking_policies_failed', postgresql.JSONB()),
        sa.Column('non_blocking_policies_failed', postgresql.JSONB()),

        # VCR override
        sa.Column('override_approved', sa.Boolean(), default=False, nullable=False),
        sa.Column('override_reason', sa.Text()),
        sa.Column('override_approved_by', postgresql.UUID(as_uuid=True)),
        sa.Column('override_approved_at', sa.DateTime()),
        sa.Column('override_ticket_url', sa.String(500)),

        # Evidence
        sa.Column('evidence_vault_path', sa.String(500)),
        sa.Column('evidence_artifacts', postgresql.JSONB()),

        # Security
        sa.Column('prompt_hash', sa.String(64)),
        sa.Column('prompt_redacted_preview', sa.Text()),
        sa.Column('contains_secrets', sa.Boolean(), default=False),

        # Metadata
        sa.Column('tags', postgresql.JSONB()),
        sa.Column('notes', sa.Text()),

        # Foreign keys
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['policy_pack_id'], ['policy_packs.id']),
        sa.ForeignKeyConstraint(['override_approved_by'], ['users.id']),
    )

    # Create indexes
    op.create_index('idx_ai_code_events_project_created', 'ai_code_events', ['project_id', sa.text('created_at DESC')])
    op.create_index('idx_ai_code_events_status', 'ai_code_events', ['validation_status', sa.text('created_at DESC')])
    op.create_index('idx_ai_code_events_ai_tool', 'ai_code_events', ['ai_tool', sa.text('created_at DESC')])
    op.create_index('idx_ai_code_events_override', 'ai_code_events', ['override_approved', 'validation_status'],
                    postgresql_where=sa.text("validation_status = 'failed'"))
    op.create_index('idx_ai_code_events_timeline', 'ai_code_events', ['project_id', sa.text('validation_started_at DESC')],
                    postgresql_where=sa.text("validation_started_at IS NOT NULL"))
    op.create_index('idx_ai_code_events_policy_pack', 'ai_code_events', ['policy_pack_id', 'validation_status'])
    op.execute("CREATE INDEX idx_ai_code_events_files_gin ON ai_code_events USING gin(files_changed jsonb_path_ops)")

def downgrade():
    op.drop_table('ai_code_events')
    op.execute('DROP TYPE validationstatus')
    op.execute('DROP TYPE aitooltype')
```

---

## Consequences

### Positive

1. ✅ **Type Safety** - Pydantic schemas + SQLAlchemy enums prevent invalid data
2. ✅ **Query Performance** - Dedicated indexes optimize AI event queries
3. ✅ **Schema Flexibility** - JSONB columns allow evolution without migrations
4. ✅ **Audit Compliance** - Full evidence trail for HIPAA/SOC 2
5. ✅ **Analytics Ready** - Rich metadata for AI adoption insights

### Negative

1. ⚠️ **Storage Growth** - JSONB columns can become large (mitigated by 2-year retention)
2. ⚠️ **Schema Duplication** - Some fields overlap with `evidence` table (accepted trade-off)
3. ⚠️ **Migration Complexity** - New enums require careful PostgreSQL version management

### Neutral

1. 📊 **Learning Curve** - Team needs to understand JSONB query syntax
2. 📊 **Monitoring** - New table requires dedicated observability (Prometheus metrics)

---

## Implementation Plan

### Phase 1: Schema Deployment (Sprint 41, Week 1)
- [ ] DBA review of schema design (Jan 8)
- [ ] Alembic migration tested on staging (Jan 9)
- [ ] Migration deployed to production (Jan 10)
- [ ] Smoke test: Insert 10 sample events (Jan 10)

### Phase 2: Service Integration (Sprint 41-42)
- [ ] `AICodeEventService` CRUD operations (Sprint 41)
- [ ] GitHub webhook integration (Sprint 42)
- [ ] Validation pipeline updates (Sprint 42)

### Phase 3: UI Integration (Sprint 43)
- [ ] Evidence Timeline UI (Feb 3-7)
- [ ] VCR Override dialog (Feb 10-14)

---

## Alternatives Considered

### Alternative 1: Event Sourcing with Kafka
**Description**: Stream AI events to Kafka, materialize views in PostgreSQL.

**Pros**:
- ✅ Scalable for high-volume events
- ✅ Real-time analytics

**Cons**:
- ❌ Operational complexity (Kafka cluster)
- ❌ Cross-system queries difficult
- ❌ Overkill for current scale (<1000 events/day)

**Decision**: Rejected for v1, revisit at 10K+ events/day.

---

### Alternative 2: NoSQL (MongoDB)
**Description**: Store AI events in MongoDB for schema flexibility.

**Pros**:
- ✅ Schema-less evolution
- ✅ Native JSON storage

**Cons**:
- ❌ Weak joins with existing PostgreSQL data
- ❌ Transaction guarantees weaker than Postgres
- ❌ Team expertise in PostgreSQL, not MongoDB

**Decision**: Rejected. PostgreSQL JSONB provides 90% of flexibility with better integration.

---

### Alternative 3: Extend `evidence` Table
**Description**: Add `event_type` enum and JSONB column to existing `evidence` table.

**Pros**:
- ✅ Reuse existing infrastructure
- ✅ No new table

**Cons**:
- ❌ Poor queryability (WHERE event_type = 'ai_code')
- ❌ Schema bloat (100+ fields in single table)
- ❌ Index pollution (indexes slow down all evidence operations)

**Decision**: Rejected. Violates single responsibility principle.

---

## References

### Internal Documents
- [EP-02: AI Safety Layer v1](../../00-foundation/04-Roadmap/Product-Roadmap-2026-Software3.0.md)
- [Sprint 41: AI Safety Foundation](../../04-build/02-Sprint-Plans/SPRINT-41-AI-SAFETY-FOUNDATION.md)
- [Evidence Vault Architecture](../02-System-Architecture/System-Architecture-Document.md#evidence-vault)

### External Standards
- [OWASP ASVS Level 2](https://owasp.org/www-project-application-security-verification-standard/)
- [PostgreSQL JSONB Performance](https://www.postgresql.org/docs/current/datatype-json.html)
- [GDPR Privacy by Design](https://gdpr-info.eu/art-25-gdpr/)

---

## Approval Signatures

| Role | Name | Status | Date |
|------|------|--------|------|
| **Backend Lead** | TBD | ✅ APPROVED | Jan 6, 2026 |
| **DBA** | TBD | ⏳ PENDING | - |
| **CTO** | Mr. Tai | ✅ APPROVED | Jan 6, 2026 |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 6, 2026 | Backend Team | Initial schema design |

---

*ADR Version: 1.0.0 | Created: January 6, 2026 | Framework: SDLC 5.1.3*
