# Implementation Phases - Governance System v2.0
## Sprint 118 (Feb 10-21, 2026) - 10-Day Implementation Plan

**Version**: 2.0.0
**Status**: APPROVED
**Owner**: Tech Lead + EM
**Created**: 2026-01-28
**Sprint**: 118 Track 2 - D5
**Related Specs**: SPEC-0001 (Anti-Vibecoding), SPEC-0002 (Specification Standard)
**Framework**: SDLC 6.0.6
**Team Size**: 8.5 FTE (Backend: 2, Frontend: 2, QA: 2, DevOps: 1, EM: 0.5, Tech Lead: 1)

---

## 📋 Table of Contents

1. [Sprint Overview](#sprint-overview)
2. [Phase 0: Pre-Sprint Preparation](#phase-0-pre-sprint-preparation)
3. [Phase 1: Database Migration](#phase-1-database-migration)
4. [Phase 2: Backend Services](#phase-2-backend-services)
5. [Phase 3: API Endpoints](#phase-3-api-endpoints)
6. [Phase 4: Frontend UI](#phase-4-frontend-ui)
7. [Phase 5: Testing & QA](#phase-5-testing--qa)
8. [Phase 6: Integration & Performance](#phase-6-integration--performance)
9. [Phase 7: Security & Compliance](#phase-7-security--compliance)
10. [Phase 8: Documentation & Training](#phase-8-documentation--training)
11. [Phase 9: Deployment & Validation](#phase-9-deployment--validation)
12. [Daily Schedule](#daily-schedule)
13. [Risk Mitigation](#risk-mitigation)
14. [Rollback Strategy](#rollback-strategy)
15. [Success Criteria](#success-criteria)

---

## 1. Sprint Overview

### 1.1 Sprint Goals

```yaml
Primary Goal: Ship Governance v2.0 with Anti-Vibecoding + Specification Standard

Key Deliverables:
  ✅ 14 new database tables (governance system)
  ✅ 12 new REST API endpoints (governance management)
  ✅ 6 new frontend features (vibecoding UI, spec validator)
  ✅ ~500 automated tests (95%+ coverage)
  ✅ Documentation complete (API docs, user guides)
  ✅ Production deployment ready

Business Value:
  - Enable Vietnamese SME code quality governance
  - Reduce AI-generated code rejection from 70% → <30%
  - Automated routing (Green → auto-merge, Red → block)
  - Kill switch for quality protection
  - Multi-currency subscription tracking (8 currencies)
```

### 1.2 Team Allocation

```yaml
Backend Team (2 FTE):
  Lead: Backend Lead
  Member: Senior Backend Engineer
  Focus:
    - Database migrations (14 tables, 50+ indexes)
    - Business logic (vibecoding service, specification service)
    - API endpoints (12 governance endpoints)
    - Unit tests (300+ tests, 95%+ coverage)

Frontend Team (2 FTE):
  Lead: Frontend Lead
  Member: Senior Frontend Engineer
  Focus:
    - UI components (vibecoding cards, spec validator)
    - State management (TanStack Query + Zustand)
    - Integration with 12 new API endpoints
    - Unit tests (120+ tests, 90%+ coverage)

QA Team (2 FTE):
  Lead: QA Lead
  Member: QA Engineer
  Focus:
    - Integration tests (150+ tests, 90%+ coverage)
    - E2E tests (10 critical user journeys)
    - Performance tests (<100ms p95 API latency)
    - Security tests (Semgrep, Trivy)
    - Manual testing (10 scenarios)

DevOps Team (1 FTE):
  Lead: DevOps Lead
  Focus:
    - Docker Compose setup (PostgreSQL, Redis, OPA, MinIO)
    - CI/CD pipeline updates (GitHub Actions)
    - Database migration automation (Alembic)
    - Monitoring setup (Prometheus, Grafana)
    - Deployment scripts (blue-green deployment)

Engineering Manager (0.5 FTE):
  Focus:
    - Daily standups (15 min)
    - Blocker resolution
    - Stakeholder communication
    - Risk management

Tech Lead (1 FTE):
  Focus:
    - Architecture decisions
    - Code reviews (all PRs)
    - Technical guidance
    - Integration oversight
    - CTO Gate preparation
```

### 1.3 Timeline Overview

```
Phase 0: Pre-Sprint (Feb 7-9, 3 days)
  ⏸️  Environment setup, dependency installation

Phase 1-2: Foundation (Feb 10-11, 2 days)
  🔧 Database migrations + Backend services

Phase 3-4: Features (Feb 12-14, 3 days)
  ⚡ API endpoints + Frontend UI

Phase 5-6: Quality (Feb 17-18, 2 days)
  ✅ Testing + Performance optimization

Phase 7-8: Polish (Feb 19-20, 2 days)
  🔒 Security + Documentation

Phase 9: Deploy (Feb 21, 1 day)
  🚀 Production deployment + CTO Gate

CTO Gate: Feb 21 (End of Day)
  👨‍💼 Review all deliverables, approve for production
```

---

## 2. Phase 0: Pre-Sprint Preparation (Feb 7-9, 3 days)

**Goal**: Ensure all team members have working development environments before Sprint 118 Day 1.

### 2.1 Environment Setup

**Backend Team**:
```bash
# Day 1 (Feb 7): Python environment
pyenv install 3.11.7
pyenv local 3.11.7
pip install -r backend/requirements.txt
pip install -r backend/requirements-test.txt

# Verify installation
python --version  # Should be 3.11.7
pytest --version  # Should be 7.4.0+
ruff --version    # Should be 0.1.6+

# Day 2 (Feb 8): Docker services
docker-compose up -d postgres redis opa minio
sleep 10  # Wait for services

# Verify services
psql -h localhost -U test -d sdlc_test -c "SELECT 1;"
redis-cli ping
curl http://localhost:8181/health
curl http://localhost:9000/minio/health/live

# Day 3 (Feb 9): Database initialization
cd backend
alembic upgrade head  # Apply existing migrations
pytest tests/unit --exitfirst  # Verify tests pass
```

**Frontend Team**:
```bash
# Day 1 (Feb 7): Node.js environment
nvm install 20
nvm use 20
cd frontend
npm ci  # Install dependencies (use ci for reproducible builds)

# Verify installation
node --version  # Should be 20.x
npm --version   # Should be 10.x
npx vite --version  # Should be 5.0+

# Day 2 (Feb 8): Backend API connection
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local
npm run dev  # Start dev server
# Open http://localhost:3000, verify API connection

# Day 3 (Feb 9): Run tests
npm run test  # Unit tests
npm run test:e2e  # E2E tests (requires backend running)
```

**QA Team**:
```bash
# Day 1 (Feb 7): Test frameworks
pip install pytest pytest-asyncio pytest-cov
npm install -g @playwright/test
npx playwright install --with-deps  # Install browsers

# Day 2 (Feb 8): Test environment verification
pytest backend/tests/unit --collect-only  # List all tests
npm run test --list  # List frontend tests
npx playwright test --list  # List E2E tests

# Day 3 (Feb 9): Baseline test run
pytest backend/tests/unit  # Should all pass
npm run test  # Should all pass
# E2E tests will be written during sprint
```

**DevOps Team**:
```bash
# Day 1 (Feb 7): Infrastructure tools
brew install terraform kubectl helm  # macOS
# OR
sudo apt install terraform kubectl  # Ubuntu

# Verify installations
terraform --version  # 1.6.0+
kubectl version --client  # 1.28+

# Day 2 (Feb 8): CI/CD setup
gh auth login  # GitHub CLI
gh workflow list  # Verify GitHub Actions access

# Day 3 (Feb 9): Monitoring setup
docker-compose up -d prometheus grafana
# Open http://localhost:3001 (Grafana)
# Import dashboards from dashboards/ folder
```

### 2.2 Pre-Sprint Checklist

```yaml
Backend Team:
  ☐ Python 3.11.7 installed and verified
  ☐ All dependencies installed (requirements.txt)
  ☐ Docker services running (PostgreSQL, Redis, OPA, MinIO)
  ☐ Database initialized (alembic upgrade head)
  ☐ Existing unit tests passing (100%)
  ☐ IDE configured (VS Code extensions)

Frontend Team:
  ☐ Node.js 20 installed and verified
  ☐ All dependencies installed (npm ci)
  ☐ Backend API connection working
  ☐ Dev server running (npm run dev)
  ☐ Existing unit tests passing (100%)
  ☐ IDE configured (VS Code extensions)

QA Team:
  ☐ Test frameworks installed (pytest, Playwright)
  ☐ Browsers installed (Chromium, Firefox, WebKit)
  ☐ Test environment verified
  ☐ Baseline test run successful
  ☐ Test data generators ready (factories)

DevOps Team:
  ☐ Infrastructure tools installed (Terraform, kubectl)
  ☐ CI/CD access verified (GitHub Actions)
  ☐ Monitoring stack running (Prometheus, Grafana)
  ☐ Docker Compose working (all services)
  ☐ Deployment scripts ready

All Teams:
  ☐ SDLC-Orchestrator repo cloned and updated
  ☐ SDLC-Enterprise-Framework submodule initialized
  ☐ CLAUDE.md and AGENTS.md reviewed
  ☐ Sprint 118 plan reviewed (this document)
  ☐ Daily standup time confirmed (9:00 AM ICT)
  ☐ Communication channels ready (Slack, GitHub)
```

---

## 3. Phase 1: Database Migration (Feb 10, Day 1)

**Duration**: 1 day
**Owner**: Backend Lead + DevOps Lead
**Dependencies**: Phase 0 complete

### 3.1 Objectives

```yaml
Goals:
  ✅ Create 14 new tables (governance system)
  ✅ Create 50+ indexes (FK, time-series, GIN, composite)
  ✅ Insert seed data (routing rules, kill switch triggers)
  ✅ Verify foreign keys to existing 30 tables
  ✅ Zero downtime (concurrent index creation)
  ✅ Rollback tested (<5 minutes)

Success Criteria:
  - All 14 tables created successfully
  - All 50+ indexes created successfully
  - Seed data inserted (4 routing rules, 3 kill switch triggers)
  - Database migration time < 10 minutes
  - All existing tests still passing (0 regressions)
```

### 3.2 Implementation Steps

**Morning (9:00-12:00): Alembic Migrations**

```bash
# Step 1: Generate Phase 1 migration (7 specification tables)
cd backend
alembic revision --autogenerate -m "Add governance v2 specification tables"

# Review generated migration file
# Location: alembic/versions/XXXXXX_add_governance_v2_specification_tables.py

# Expected tables:
#   - governance_specifications
#   - spec_versions
#   - spec_frontmatter_metadata
#   - spec_functional_requirements
#   - spec_acceptance_criteria
#   - spec_implementation_phases
#   - spec_cross_references

# Step 2: Manual review (CRITICAL - prevent data loss)
# Check for:
#   ❌ DROP TABLE statements (should be NONE for new tables)
#   ❌ ALTER TABLE on existing tables (should be minimal)
#   ✅ CREATE TABLE statements (should be 7)
#   ✅ Foreign keys to existing tables (users, projects)

# Step 3: Dry-run migration on test database
alembic upgrade head --sql > migration_phase1.sql
less migration_phase1.sql  # Manual review

# Step 4: Apply migration to test database
alembic upgrade head

# Step 5: Verify tables created
psql -h localhost -U test -d sdlc_test -c "\dt governance_*"
# Expected: 7 tables listed

# Step 6: Run all existing tests (verify no regressions)
pytest tests/unit tests/integration --exitfirst
# All tests should PASS
```

**Afternoon (13:00-16:00): Phase 2 Migration (7 vibecoding tables + seed data)**

```bash
# Step 7: Generate Phase 2 migration
alembic revision --autogenerate -m "Add governance v2 vibecoding tables and seed data"

# Expected tables:
#   - vibecoding_signals
#   - vibecoding_index_history
#   - progressive_routing_rules
#   - kill_switch_triggers
#   - kill_switch_events
#   - tier_specific_requirements
#   - spec_validation_results

# Step 8: Add seed data to migration
# Edit migration file manually:
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    # ... table creation code (auto-generated)

    # Insert seed data: Progressive routing rules
    routing_rules = table('progressive_routing_rules',
        column('zone', sa.String),
        column('threshold_min', sa.Integer),
        column('threshold_max', sa.Integer),
        column('action', sa.String),
        column('description', sa.String)
    )

    op.bulk_insert(routing_rules, [
        {'zone': 'GREEN', 'threshold_min': 0, 'threshold_max': 20,
         'action': 'AUTO_MERGE', 'description': 'Automatic merge approved'},
        {'zone': 'YELLOW', 'threshold_min': 20, 'threshold_max': 40,
         'action': 'HUMAN_REVIEW_REQUIRED', 'description': 'Requires human review'},
        {'zone': 'ORANGE', 'threshold_min': 40, 'threshold_max': 60,
         'action': 'SENIOR_REVIEW_REQUIRED', 'description': 'Requires senior review'},
        {'zone': 'RED', 'threshold_min': 60, 'threshold_max': 100,
         'action': 'BLOCK_OR_COUNCIL', 'description': 'Blocked or requires council'},
    ])

    # Insert seed data: Kill switch triggers
    kill_switch_triggers = table('kill_switch_triggers',
        column('metric', sa.String),
        column('threshold', sa.String),
        column('duration', sa.String),
        column('action', sa.String),
        column('severity', sa.String)
    )

    op.bulk_insert(kill_switch_triggers, [
        {'metric': 'rejection_rate', 'threshold': '> 80%', 'duration': '30 minutes',
         'action': 'Disable AI codegen for 24h', 'severity': 'HIGH'},
        {'metric': 'latency_p95', 'threshold': '> 500ms', 'duration': '15 minutes',
         'action': 'Fallback to rule-based', 'severity': 'MEDIUM'},
        {'metric': 'security_scan_failures', 'threshold': '> 5 critical CVEs', 'duration': 'Any occurrence',
         'action': 'Immediate disable + alert CTO', 'severity': 'CRITICAL'},
    ])

# Step 9: Apply Phase 2 migration
alembic upgrade head

# Step 10: Verify seed data
psql -h localhost -U test -d sdlc_test -c "SELECT * FROM progressive_routing_rules;"
# Expected: 4 rows (GREEN, YELLOW, ORANGE, RED)

psql -h localhost -U test -d sdlc_test -c "SELECT * FROM kill_switch_triggers;"
# Expected: 3 rows (rejection_rate, latency_p95, security_scan_failures)
```

**Late Afternoon (16:00-18:00): Phase 3 Migration (50+ indexes)**

```bash
# Step 11: Generate Phase 3 migration (indexes only)
alembic revision -m "Add governance v2 indexes"

# Manual migration file (auto-generate doesn't handle all index types well):
from alembic import op

def upgrade():
    # Foreign key indexes (28 indexes)
    op.create_index('idx_governance_specs_spec_id', 'governance_specifications', ['spec_id'])
    op.create_index('idx_spec_versions_spec_id', 'spec_versions', ['specification_id'])
    # ... (28 total FK indexes)

    # Time-series indexes (8 indexes)
    op.create_index('idx_vibecoding_signals_created_at', 'vibecoding_signals', ['created_at'])
    op.create_index('idx_vibecoding_index_history_calculated_at', 'vibecoding_index_history', ['calculated_at'])
    # ... (8 total time-series indexes)

    # GIN indexes for JSONB/arrays/full-text (10 indexes)
    op.execute("CREATE INDEX idx_spec_frontmatter_metadata_jsonb ON spec_frontmatter_metadata USING GIN (metadata)")
    op.execute("CREATE INDEX idx_spec_frontmatter_tier_array ON spec_frontmatter_metadata USING GIN (tier)")
    # ... (10 total GIN indexes)

    # Composite indexes (6 indexes)
    op.create_index('idx_vibecoding_signals_submission_project', 'vibecoding_signals', ['submission_id', 'project_id'])
    # ... (6 total composite indexes)

# Step 12: Use CONCURRENT index creation (PostgreSQL)
# Edit migration to use concurrent (prevents table locking):
def upgrade():
    # Add this for all indexes:
    op.execute("CREATE INDEX CONCURRENTLY idx_... ON table (...)")

# Step 13: Apply Phase 3 migration (may take 2-4 hours for large tables)
alembic upgrade head

# Monitor progress:
psql -h localhost -U test -d sdlc_test -c "SELECT * FROM pg_stat_progress_create_index;"

# Step 14: Verify all indexes created
psql -h localhost -U test -d sdlc_test -c "SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public' AND tablename LIKE 'governance_%' OR tablename LIKE 'vibecoding_%' OR tablename LIKE 'spec_%' ORDER BY tablename;"
# Expected: 50+ indexes listed
```

### 3.3 Testing & Validation

```bash
# Test 1: Verify table count
psql -h localhost -U test -d sdlc_test -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'governance_%' OR table_name LIKE 'vibecoding_%' OR table_name LIKE 'spec_%';"
# Expected: 14 tables

# Test 2: Verify foreign keys
psql -h localhost -U test -d sdlc_test -c "SELECT conname, conrelid::regclass, confrelid::regclass FROM pg_constraint WHERE contype = 'f' AND conname LIKE 'fk_governance_%';"
# Expected: 28+ foreign keys

# Test 3: Verify seed data
psql -h localhost -U test -d sdlc_test -c "SELECT COUNT(*) FROM progressive_routing_rules;"
# Expected: 4

psql -h localhost -U test -d sdlc_test -c "SELECT COUNT(*) FROM kill_switch_triggers;"
# Expected: 3

# Test 4: Run all existing tests (regression check)
pytest tests/unit tests/integration
# Expected: All PASS (0 failures)

# Test 5: Performance test (simple queries)
psql -h localhost -U test -d sdlc_test -c "EXPLAIN ANALYZE SELECT * FROM governance_specifications WHERE spec_id = 'SPEC-0001';"
# Expected: Index scan, <10ms execution time
```

### 3.4 Rollback Plan

```bash
# If migration fails or causes issues:

# Option 1: Rollback last migration
alembic downgrade -1

# Option 2: Rollback to specific version (before Phase 1)
alembic downgrade <previous_version_id>

# Option 3: Drop all new tables (LAST RESORT)
psql -h localhost -U test -d sdlc_test -c "
DROP TABLE IF EXISTS spec_validation_results CASCADE;
DROP TABLE IF EXISTS tier_specific_requirements CASCADE;
DROP TABLE IF EXISTS kill_switch_events CASCADE;
DROP TABLE IF EXISTS kill_switch_triggers CASCADE;
DROP TABLE IF EXISTS progressive_routing_rules CASCADE;
DROP TABLE IF EXISTS vibecoding_index_history CASCADE;
DROP TABLE IF EXISTS vibecoding_signals CASCADE;
DROP TABLE IF EXISTS spec_cross_references CASCADE;
DROP TABLE IF EXISTS spec_implementation_phases CASCADE;
DROP TABLE IF EXISTS spec_acceptance_criteria CASCADE;
DROP TABLE IF EXISTS spec_functional_requirements CASCADE;
DROP TABLE IF EXISTS spec_frontmatter_metadata CASCADE;
DROP TABLE IF EXISTS spec_versions CASCADE;
DROP TABLE IF EXISTS governance_specifications CASCADE;
"

# After rollback, verify existing tables intact:
pytest tests/unit tests/integration
# Should all PASS
```

### 3.5 Phase 1 Deliverables

```yaml
✅ 14 new tables created:
  - Group 1 (7 spec tables)
  - Group 2 (7 vibecoding tables)

✅ 50+ indexes created:
  - 28 FK indexes
  - 8 time-series indexes
  - 10 GIN indexes (JSONB, arrays, full-text)
  - 6 composite indexes

✅ Seed data inserted:
  - 4 progressive routing rules (GREEN/YELLOW/ORANGE/RED)
  - 3 kill switch triggers (rejection_rate, latency_p95, security_scan_failures)

✅ Validation complete:
  - All tables created successfully
  - All foreign keys verified
  - All indexes verified
  - Performance tests passing (<10ms simple queries)
  - No regressions (existing tests passing)

✅ Rollback tested:
  - Rollback script ready
  - Rollback time < 5 minutes
```

---

## 4. Phase 2: Backend Services (Feb 11, Day 2)

**Duration**: 1 day
**Owner**: Backend Team (2 FTE)
**Dependencies**: Phase 1 complete (database tables ready)

### 4.1 Objectives

```yaml
Goals:
  ✅ Implement VibecodingService (5-signal calculation)
  ✅ Implement SpecificationService (YAML validation)
  ✅ Implement KillSwitchService (3 trigger checks)
  ✅ Unit tests for all services (95%+ coverage)
  ✅ Integration tests for OPA policies
  ✅ Performance benchmarks (<100ms p95)

Success Criteria:
  - All 3 services implemented with 0 mocks (real DB, Redis, OPA)
  - 100+ unit tests written and passing
  - 95%+ code coverage (pytest-cov)
  - All services meet performance targets
  - Code review approved (Tech Lead + 1 reviewer)
```

### 4.2 Implementation Steps

**Morning (9:00-12:00): VibecodingService**

```python
# File: backend/app/services/vibecoding_service.py
from typing import Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.governance import VibecodingSignal, VibecodingIndexHistory, KillSwitchEvent
import structlog

log = structlog.get_logger()

class VibecodingService:
    """
    Service for calculating vibecoding index and progressive routing.

    5 Signals:
      1. Intent Clarity (30% weight)
      2. Code Ownership (25% weight)
      3. Context Completeness (20% weight)
      4. AI Attestation (15% weight)
      5. Historical Rejection Rate (10% weight)

    Routing Zones:
      - GREEN (0-20): AUTO_MERGE
      - YELLOW (20-40): HUMAN_REVIEW_REQUIRED
      - ORANGE (40-60): SENIOR_REVIEW_REQUIRED
      - RED (60-100): BLOCK_OR_COUNCIL
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_index(
        self,
        submission_id: str,
        project_id: str,
        intent_clarity: int,
        code_ownership: int,
        context_completeness: int,
        ai_attestation: bool,
        rejection_rate: float
    ) -> Dict:
        """
        Calculate vibecoding index using 5 weighted signals.

        Args:
            submission_id: Unique submission ID (SUB-XXXXXX)
            project_id: Project ID (PRJ-XXXXXX)
            intent_clarity: Intent clarity score (0-100)
            code_ownership: Code ownership score (0-100)
            context_completeness: Context completeness score (0-100)
            ai_attestation: Whether AI attestation provided (True/False)
            rejection_rate: Historical rejection rate (0.0-1.0)

        Returns:
            Dict with keys: score, zone, routing, signals

        Formula:
            score = (100 - intent_clarity) * 0.30 +
                    (100 - code_ownership) * 0.25 +
                    (100 - context_completeness) * 0.20 +
                    (0 if ai_attestation else 100) * 0.15 +
                    (rejection_rate * 100) * 0.10
        """
        # Calculate weighted score
        intent_penalty = (100 - intent_clarity) * 0.30
        ownership_penalty = (100 - code_ownership) * 0.25
        context_penalty = (100 - context_completeness) * 0.20
        attestation_penalty = 0 if ai_attestation else (100 * 0.15)
        rejection_penalty = (rejection_rate * 100) * 0.10

        score = (
            intent_penalty +
            ownership_penalty +
            context_penalty +
            attestation_penalty +
            rejection_penalty
        )

        # Determine zone and routing
        if score < 20:
            zone = "GREEN"
            routing = "AUTO_MERGE"
        elif score < 40:
            zone = "YELLOW"
            routing = "HUMAN_REVIEW_REQUIRED"
        elif score < 60:
            zone = "ORANGE"
            routing = "SENIOR_REVIEW_REQUIRED"
        else:
            zone = "RED"
            routing = "BLOCK_OR_COUNCIL"

        # Store signal
        signal = VibecodingSignal(
            submission_id=submission_id,
            project_id=project_id,
            intent_clarity=intent_clarity,
            code_ownership=code_ownership,
            context_completeness=context_completeness,
            ai_attestation=ai_attestation,
            rejection_rate=rejection_rate,
            signal_metadata={
                "intent_penalty": intent_penalty,
                "ownership_penalty": ownership_penalty,
                "context_penalty": context_penalty,
                "attestation_penalty": attestation_penalty,
                "rejection_penalty": rejection_penalty
            }
        )
        self.db.add(signal)

        # Store index history
        index_history = VibecodingIndexHistory(
            submission_id=submission_id,
            project_id=project_id,
            score=score,
            zone=zone,
            routing=routing,
            calculated_at=datetime.utcnow()
        )
        self.db.add(index_history)

        await self.db.commit()

        log.info(
            "vibecoding_index_calculated",
            submission_id=submission_id,
            score=score,
            zone=zone,
            routing=routing
        )

        return {
            "submission_id": submission_id,
            "project_id": project_id,
            "score": round(score, 2),
            "zone": zone,
            "routing": routing,
            "signals": {
                "intent_clarity": intent_clarity,
                "code_ownership": code_ownership,
                "context_completeness": context_completeness,
                "ai_attestation": ai_attestation,
                "rejection_rate": rejection_rate
            },
            "calculated_at": datetime.utcnow().isoformat()
        }

    async def check_kill_switch(self, project_id: str) -> Dict:
        """
        Check if kill switch should be triggered for a project.

        3 Triggers:
          1. Rejection rate > 80% for 30 minutes
          2. Latency p95 > 500ms for 15 minutes
          3. Security scan failures > 5 critical CVEs

        Args:
            project_id: Project ID to check

        Returns:
            Dict with keys: triggered, trigger_type, action, severity
        """
        # Check trigger 1: Rejection rate
        thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)

        rejection_query = select(
            func.count(VibecodingSignal.id).label("total"),
            func.sum(
                func.cast(VibecodingSignal.rejection_rate > 0.80, sa.Integer)
            ).label("rejected")
        ).where(
            VibecodingSignal.project_id == project_id,
            VibecodingSignal.created_at >= thirty_minutes_ago
        )

        result = await self.db.execute(rejection_query)
        row = result.one()

        if row.total > 0:
            rejection_rate_30min = row.rejected / row.total

            if rejection_rate_30min > 0.80:
                # Trigger kill switch
                event = KillSwitchEvent(
                    project_id=project_id,
                    trigger_type="rejection_rate",
                    threshold="80%",
                    actual_value=f"{rejection_rate_30min * 100:.1f}%",
                    duration="30 minutes",
                    action="Disable AI codegen for 24h",
                    severity="HIGH",
                    triggered_by="system",
                    metadata={
                        "rejected_count": row.rejected,
                        "total_submissions": row.total,
                        "time_window": "30m"
                    }
                )
                self.db.add(event)
                await self.db.commit()

                log.warning(
                    "kill_switch_triggered",
                    project_id=project_id,
                    trigger_type="rejection_rate",
                    actual_value=f"{rejection_rate_30min * 100:.1f}%"
                )

                return {
                    "triggered": True,
                    "trigger_type": "rejection_rate",
                    "threshold": "80%",
                    "actual_value": f"{rejection_rate_30min * 100:.1f}%",
                    "duration": "30 minutes",
                    "action": "Disable AI codegen for 24h",
                    "severity": "HIGH"
                }

        # Check trigger 2: Latency (TODO: Implement latency monitoring)
        # Check trigger 3: Security (TODO: Implement CVE monitoring)

        return {
            "triggered": False,
            "trigger_type": None,
            "action": None,
            "severity": None
        }
```

**Unit Tests for VibecodingService**:

```python
# File: backend/tests/unit/services/test_vibecoding_service.py
import pytest
from datetime import datetime, timedelta
from app.services.vibecoding_service import VibecodingService

@pytest.mark.asyncio
class TestVibecodingService:

    async def test_calculate_index_green_zone(self, db_session):
        """Score < 20 should route to AUTO_MERGE"""
        service = VibecodingService(db_session)

        result = await service.calculate_index(
            submission_id="SUB-000001",
            project_id="PRJ-000001",
            intent_clarity=90,
            code_ownership=85,
            context_completeness=95,
            ai_attestation=True,
            rejection_rate=0.05
        )

        assert result["score"] < 20
        assert result["zone"] == "GREEN"
        assert result["routing"] == "AUTO_MERGE"

    async def test_calculate_index_5_signal_weights(self, db_session):
        """Verify weighted calculation formula"""
        service = VibecodingService(db_session)

        # Known values: intent=80, ownership=70, context=90, attestation=True, rejection=0.10
        # Expected: (20*0.30) + (30*0.25) + (10*0.20) + (0*0.15) + (10*0.10) = 16.5
        result = await service.calculate_index(
            submission_id="SUB-000002",
            project_id="PRJ-000001",
            intent_clarity=80,
            code_ownership=70,
            context_completeness=90,
            ai_attestation=True,
            rejection_rate=0.10
        )

        assert result["score"] == pytest.approx(16.5, rel=1e-2)

    async def test_check_kill_switch_triggered(self, db_session):
        """Rejection rate > 80% for 30 minutes should trigger kill switch"""
        service = VibecodingService(db_session)

        # Simulate 30 submissions with 85% rejection
        for i in range(30):
            await service.calculate_index(
                submission_id=f"SUB-{i:06d}",
                project_id="PRJ-000001",
                intent_clarity=30,
                code_ownership=25,
                context_completeness=40,
                ai_attestation=False,
                rejection_rate=0.85 if i < 25 else 0.10  # 25/30 = 83%
            )

        result = await service.check_kill_switch(project_id="PRJ-000001")

        assert result["triggered"] is True
        assert result["trigger_type"] == "rejection_rate"
        assert result["severity"] == "HIGH"
```

**Afternoon (13:00-16:00): SpecificationService**

```python
# File: backend/app/services/specification_service.py
import yaml
import jsonschema
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.governance import Specification, SpecFrontmatterMetadata
import structlog

log = structlog.get_logger()

class SpecificationService:
    """
    Service for validating YAML frontmatter and managing specifications.

    SPEC-0002 Compliance:
      - YAML frontmatter with 8 required fields
      - JSON Schema validation
      - Tier-specific sections
      - BDD format for functional requirements
    """

    FRONTMATTER_SCHEMA = {
        "type": "object",
        "properties": {
            "spec_id": {"type": "string", "pattern": "^SPEC-\\d{4}$"},
            "title": {"type": "string", "minLength": 10, "maxLength": 200},
            "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
            "status": {"type": "string", "enum": ["DRAFT", "APPROVED", "DEPRECATED"]},
            "tier": {
                "type": "array",
                "items": {"enum": ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"]},
                "minItems": 1
            },
            "pillar": {"type": "integer", "minimum": 1, "maximum": 7},
            "owner": {"type": "string", "minLength": 2},
            "last_updated": {"type": "string", "format": "date"}
        },
        "required": ["spec_id", "title", "version", "status", "tier", "pillar", "owner", "last_updated"]
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_yaml_frontmatter(self, yaml_content: str) -> Dict:
        """
        Validate YAML frontmatter against SPEC-0002 schema.

        Args:
            yaml_content: YAML string with frontmatter

        Returns:
            Dict with keys: valid, spec_id, errors

        Raises:
            ValueError: If YAML parsing fails
        """
        try:
            # Parse YAML (safe load only, never use yaml.load)
            frontmatter = yaml.safe_load(yaml_content)

            if not isinstance(frontmatter, dict):
                return {
                    "valid": False,
                    "spec_id": None,
                    "errors": [{"field": "root", "message": "YAML must be a dictionary"}]
                }

            # Validate against JSON Schema
            try:
                jsonschema.validate(instance=frontmatter, schema=self.FRONTMATTER_SCHEMA)

                log.info(
                    "spec_validation_success",
                    spec_id=frontmatter.get("spec_id"),
                    tier=frontmatter.get("tier")
                )

                return {
                    "valid": True,
                    "spec_id": frontmatter["spec_id"],
                    "title": frontmatter["title"],
                    "version": frontmatter["version"],
                    "tier": frontmatter["tier"],
                    "errors": []
                }

            except jsonschema.ValidationError as e:
                return {
                    "valid": False,
                    "spec_id": frontmatter.get("spec_id"),
                    "errors": [{"field": e.path[0] if e.path else "root", "message": e.message}]
                }

        except yaml.YAMLError as e:
            return {
                "valid": False,
                "spec_id": None,
                "errors": [{"field": "yaml", "message": f"YAML parsing error: {str(e)}"}]
            }

    async def get_tier_specific_requirements(
        self,
        spec_id: str,
        tier: str
    ) -> List[Dict]:
        """
        Get tier-specific requirements for a specification.

        Args:
            spec_id: Specification ID (SPEC-XXXX)
            tier: Tier level (LITE, STANDARD, PROFESSIONAL, ENTERPRISE)

        Returns:
            List of requirements applicable to the tier
        """
        # TODO: Implement tier-specific requirement filtering
        # For now, return all requirements (MVP)
        pass
```

**Late Afternoon (16:00-18:00): Unit Tests + Integration Tests**

```python
# Unit tests for SpecificationService (30+ tests)
# Integration tests with OPA (10+ tests)
# Performance benchmarks (pytest-benchmark)

# Run all tests:
pytest tests/unit/services/ --cov=app/services --cov-report=term-missing --cov-fail-under=95
```

### 4.3 Phase 2 Deliverables

```yaml
✅ Services Implemented:
  - VibecodingService (500+ LOC)
    - calculate_index() - 5-signal calculation
    - check_kill_switch() - 3 trigger checks
    - determine_routing() - Progressive routing logic

  - SpecificationService (300+ LOC)
    - validate_yaml_frontmatter() - SPEC-0002 compliance
    - get_tier_specific_requirements() - Tier filtering

  - KillSwitchService (200+ LOC)
    - check_all_triggers() - Unified trigger checking
    - record_event() - Event logging

✅ Unit Tests:
  - 100+ tests written
  - 95%+ code coverage
  - 0 mocks (real DB, Redis, OPA)
  - All tests passing

✅ Performance:
  - calculate_index(): <50ms p95
  - validate_yaml_frontmatter(): <30ms p95
  - check_kill_switch(): <100ms p95

✅ Code Review:
  - Tech Lead approved
  - 1 additional reviewer approved
  - 0 unresolved comments
```

---

## 5. Phase 3: API Endpoints (Feb 12-13, Day 3-4)

**Duration**: 2 days
**Owner**: Backend Team (2 FTE)
**Dependencies**: Phase 2 complete (services ready)

### 5.1 Objectives

```yaml
Goals:
  ✅ Implement 12 REST API endpoints (3 groups)
  ✅ OpenAPI 3.0 documentation (auto-generated)
  ✅ Request/response validation (Pydantic schemas)
  ✅ Authentication (JWT) + Authorization (RBAC)
  ✅ Rate limiting (Redis-based, 100 req/min per user)
  ✅ Caching (Redis, 15min/1h/24h TTL)
  ✅ Integration tests (90%+ coverage)
  ✅ API latency <100ms p95

Success Criteria:
  - All 12 endpoints implemented and tested
  - 0 security vulnerabilities (Semgrep scan passing)
  - Rate limiting working (429 after 100 requests)
  - Caching hit rate >80%
  - Postman collection created (for manual testing)
  - Code review approved
```

### 5.2 Implementation Schedule

**Day 3 (Feb 12): Specification Management (4 endpoints)**

```python
# File: backend/app/api/v1/governance.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.specification_service import SpecificationService
from app.schemas.governance import (
    SpecValidationRequest,
    SpecValidationResponse,
    SpecMetadataResponse
)
from app.api.dependencies import get_current_user, rate_limit

router = APIRouter(prefix="/governance", tags=["governance"])

@router.post("/specs/validate", response_model=SpecValidationResponse)
@rate_limit(limit=100, window=60)  # 100 req/min
async def validate_spec(
    request: SpecValidationRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Validate YAML frontmatter against SPEC-0002 standard.

    Checks:
      - YAML syntax valid
      - All required fields present
      - spec_id format (SPEC-XXXX)
      - version format (X.Y.Z)
      - tier values (LITE/STANDARD/PROFESSIONAL/ENTERPRISE)
      - pillar range (1-7)

    Rate Limit: 100 requests/minute per user

    Returns:
      - valid: boolean
      - spec_id: string (if valid)
      - errors: list of validation errors
    """
    service = SpecificationService(db)
    result = await service.validate_yaml_frontmatter(request.yaml_content)

    return SpecValidationResponse(**result)

@router.get("/specs/{spec_id}", response_model=SpecMetadataResponse)
@rate_limit(limit=100, window=60)
async def get_spec_metadata(
    spec_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Retrieve specification metadata by spec_id.

    Cache: Redis, 1 hour TTL

    Returns:
      - spec_id, title, version, status, tier, pillar, owner
    """
    # Check cache first
    cache_key = f"spec:metadata:{spec_id}"
    cached = await redis.get(cache_key)
    if cached:
        return SpecMetadataResponse(**json.loads(cached))

    # Query database
    spec = await db.get(Specification, spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Specification not found")

    response = SpecMetadataResponse(
        spec_id=spec.spec_id,
        title=spec.title,
        version=spec.version,
        status=spec.status,
        tier=spec.tier,
        pillar=spec.pillar,
        owner=spec.owner
    )

    # Cache for 1 hour
    await redis.setex(cache_key, 3600, response.json())

    return response

@router.get("/specs/{spec_id}/requirements")
@rate_limit(limit=100, window=60)
async def get_spec_requirements(
    spec_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List functional requirements for a specification.

    Returns:
      - Array of requirements (FR-001 to FR-008)
    """
    # Implementation...
    pass

@router.get("/specs/{spec_id}/acceptance-criteria")
@rate_limit(limit=100, window=60)
async def get_spec_acceptance_criteria(
    spec_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List acceptance criteria for a specification.

    Returns:
      - Array of acceptance criteria (AC-001 to AC-012)
    """
    # Implementation...
    pass
```

**Day 4 (Feb 13): Vibecoding System (5 endpoints) + Tier Management (3 endpoints)**

```python
@router.post("/vibecoding/calculate")
@rate_limit(limit=100, window=60)
async def calculate_vibecoding_index(
    request: VibecodingIndexRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Calculate vibecoding index for a code submission.

    5 Signals:
      - Intent Clarity (30%)
      - Code Ownership (25%)
      - Context Completeness (20%)
      - AI Attestation (15%)
      - Historical Rejection Rate (10%)

    Routing Zones:
      - GREEN (0-20): AUTO_MERGE
      - YELLOW (20-40): HUMAN_REVIEW_REQUIRED
      - ORANGE (40-60): SENIOR_REVIEW_REQUIRED
      - RED (60-100): BLOCK_OR_COUNCIL

    Cache: Redis, 15 minutes TTL

    Returns:
      - score (0-100)
      - zone (GREEN/YELLOW/ORANGE/RED)
      - routing decision
      - signal breakdown
    """
    service = VibecodingService(db)

    result = await service.calculate_index(
        submission_id=request.submission_id,
        project_id=request.project_id,
        intent_clarity=request.intent_clarity,
        code_ownership=request.code_ownership,
        context_completeness=request.context_completeness,
        ai_attestation=request.ai_attestation,
        rejection_rate=request.rejection_rate
    )

    # Cache for 15 minutes
    cache_key = f"vibecoding:index:{request.submission_id}"
    await redis.setex(cache_key, 900, json.dumps(result))

    return result

@router.get("/vibecoding/{submission_id}")
@rate_limit(limit=100, window=60)
async def get_vibecoding_index(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get vibecoding index history for a submission.

    Cache: Redis, 15 minutes TTL

    Returns:
      - Latest vibecoding index
      - Historical scores (last 7 days)
    """
    # Check cache
    cache_key = f"vibecoding:index:{submission_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Query database
    # ...

@router.post("/vibecoding/route")
@rate_limit(limit=100, window=60)
async def progressive_routing_decision(
    request: RoutingRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Determine progressive routing decision based on vibecoding index.

    Uses OPA policy evaluation.

    Returns:
      - routing decision
      - required reviewers
      - SLA (time limit for review)
    """
    # Implementation with OPA integration
    pass

@router.get("/vibecoding/signals/{submission_id}")
@rate_limit(limit=100, window=60)
async def get_vibecoding_signals(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get 5-signal breakdown for a submission.

    Returns:
      - Intent Clarity score + weight
      - Code Ownership score + weight
      - Context Completeness score + weight
      - AI Attestation + weight
      - Historical Rejection Rate + weight
    """
    # Implementation...
    pass

@router.post("/vibecoding/kill-switch/check")
@rate_limit(limit=100, window=60)
async def check_kill_switch(
    request: KillSwitchCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Check if kill switch should be triggered for a project.

    3 Triggers:
      1. Rejection rate > 80% for 30 minutes
      2. Latency p95 > 500ms for 15 minutes
      3. Security scan failures > 5 critical CVEs

    Cache: Redis, 5 minutes TTL (critical real-time data)

    Returns:
      - triggered (boolean)
      - trigger_type (rejection_rate/latency/security)
      - action (disable AI codegen, fallback to rule-based, etc.)
      - severity (LOW/MEDIUM/HIGH/CRITICAL)
    """
    service = VibecodingService(db)
    result = await service.check_kill_switch(project_id=request.project_id)

    # Cache for 5 minutes
    cache_key = f"killswitch:state:{request.project_id}"
    await redis.setex(cache_key, 300, json.dumps(result))

    return result

# Tier Management Endpoints (3)
@router.get("/tiers/{project_id}")
@router.get("/tiers/{tier}/requirements")
@router.post("/tiers/{project_id}/upgrade")
```

### 5.3 Authentication & Authorization

```python
# File: backend/app/api/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings
from app.models.users import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validate JWT token and return current user.

    Raises:
        HTTPException: 401 if token invalid or expired
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return user

def require_role(required_role: str):
    """
    Dependency to check if user has required role.

    Usage:
        @router.post("/admin-only", dependencies=[Depends(require_role("admin"))])
    """
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role"
            )
        return current_user
    return role_checker
```

### 5.4 Rate Limiting

```python
# File: backend/app/api/dependencies.py (continued)
import redis.asyncio as redis
from functools import wraps
from fastapi import Request, HTTPException, status

redis_client = redis.from_url(settings.REDIS_URL)

def rate_limit(limit: int = 100, window: int = 60):
    """
    Rate limiting decorator using Redis sliding window.

    Args:
        limit: Number of requests allowed
        window: Time window in seconds

    Usage:
        @rate_limit(limit=100, window=60)  # 100 req/min
        async def my_endpoint(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            current_user: User = kwargs.get("current_user")

            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required for rate limiting"
                )

            # Redis key: ratelimit:{user_id}:{endpoint}:{window}
            key = f"ratelimit:{current_user.id}:{request.url.path}:{window}"

            # Increment counter
            count = await redis_client.incr(key)

            if count == 1:
                # First request in window, set expiry
                await redis_client.expire(key, window)

            if count > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Max {limit} requests per {window}s.",
                    headers={"Retry-After": str(window)}
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
```

### 5.5 Phase 3 Deliverables

```yaml
✅ API Endpoints (12 total):
  Group 1 - Specification Management (4):
    - POST /api/v1/governance/specs/validate
    - GET /api/v1/governance/specs/{spec_id}
    - GET /api/v1/governance/specs/{spec_id}/requirements
    - GET /api/v1/governance/specs/{spec_id}/acceptance-criteria

  Group 2 - Vibecoding System (5):
    - POST /api/v1/governance/vibecoding/calculate
    - GET /api/v1/governance/vibecoding/{submission_id}
    - POST /api/v1/governance/vibecoding/route
    - GET /api/v1/governance/vibecoding/signals/{submission_id}
    - POST /api/v1/governance/vibecoding/kill-switch/check

  Group 3 - Tier Management (3):
    - GET /api/v1/governance/tiers/{project_id}
    - GET /api/v1/governance/tiers/{tier}/requirements
    - POST /api/v1/governance/tiers/{project_id}/upgrade

✅ Security:
  - JWT authentication implemented
  - RBAC authorization (13 roles)
  - Rate limiting (100 req/min per user)
  - Input validation (Pydantic schemas)
  - SQL injection prevention (SQLAlchemy ORM)

✅ Caching:
  - Redis caching implemented (3 TTL strategies)
  - Cache hit rate >80% (tested)
  - Cache invalidation on updates

✅ Documentation:
  - OpenAPI 3.0 auto-generated (FastAPI)
  - Postman collection created
  - cURL examples for all endpoints

✅ Testing:
  - 50+ integration tests
  - 90%+ API coverage
  - Rate limiting tested (429 response)
  - Authentication tested (401, 403 responses)

✅ Performance:
  - All endpoints <100ms p95
  - Rate limiting <2ms overhead
  - Cache retrieval <5ms
```

---

## 6. Phase 4: Frontend UI (Feb 14-17, Day 5-8)

**Duration**: 4 days
**Owner**: Frontend Team (2 FTE)
**Dependencies**: Phase 3 complete (API endpoints ready)

### 6.1 Objectives

```yaml
Goals:
  ✅ Implement 6 UI features (vibecoding, spec validator, kill switch)
  ✅ Integrate with 12 new API endpoints
  ✅ State management (TanStack Query + Zustand)
  ✅ UI components (shadcn/ui)
  ✅ Bilingual support (EN/VI, 40+ i18n keys)
  ✅ Unit tests (120+ tests, 90%+ coverage)
  ✅ Dashboard load <1s p95

Success Criteria:
  - All 6 features functional and tested
  - 0 console errors in production build
  - Lighthouse score >90
  - Accessibility WCAG 2.1 AA compliance
  - E2E tests passing (10 scenarios)
  - Code review approved
```

### 6.2 Implementation Schedule

**Day 5 (Feb 14): Vibecoding Index Card**

```typescript
// File: frontend/src/features/governance/VibecodingIndexCard.tsx
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useVibecodingIndex } from '@/services/governanceApi'

interface VibecodingIndexCardProps {
  submissionId: string
}

export function VibecodingIndexCard({ submissionId }: VibecodingIndexCardProps) {
  const { data, isLoading, error } = useVibecodingIndex(submissionId)

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorAlert error={error} />

  const { score, zone, routing, signals } = data

  const zoneColor = {
    GREEN: 'bg-green-100 text-green-800',
    YELLOW: 'bg-yellow-100 text-yellow-800',
    ORANGE: 'bg-orange-100 text-orange-800',
    RED: 'bg-red-100 text-red-800',
  }[zone]

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Vibecoding Index</h3>
        <Badge className={zoneColor}>{zone}</Badge>
      </div>

      <div className="text-4xl font-bold mb-2">{score}</div>
      <div className="text-sm text-muted-foreground mb-6">{routing}</div>

      <div className="space-y-4">
        <SignalBar
          label="Intent Clarity"
          value={signals.intent_clarity}
          weight="30%"
        />
        <SignalBar
          label="Code Ownership"
          value={signals.code_ownership}
          weight="25%"
        />
        <SignalBar
          label="Context Completeness"
          value={signals.context_completeness}
          weight="20%"
        />
        <SignalBar
          label="AI Attestation"
          value={signals.ai_attestation ? 100 : 0}
          weight="15%"
        />
        <SignalBar
          label="Rejection Rate"
          value={(1 - signals.rejection_rate) * 100}
          weight="10%"
        />
      </div>
    </Card>
  )
}

function SignalBar({ label, value, weight }: SignalBarProps) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span>{label}</span>
        <span className="text-muted-foreground">
          {value}/100 ({weight})
        </span>
      </div>
      <Progress value={value} className="h-2" />
    </div>
  )
}
```

**Day 6 (Feb 15): Specification Validator**

```typescript
// File: frontend/src/features/governance/SpecificationValidator.tsx
import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useValidateSpec } from '@/services/governanceApi'

export function SpecificationValidator() {
  const [yamlContent, setYamlContent] = useState('')
  const validateMutation = useValidateSpec()

  const handleValidate = () => {
    validateMutation.mutate({ yaml_content: yamlContent })
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">YAML Frontmatter Validator</h3>

      <Textarea
        placeholder="Paste your YAML frontmatter here..."
        value={yamlContent}
        onChange={(e) => setYamlContent(e.target.value)}
        rows={12}
        className="font-mono text-sm mb-4"
      />

      <Button onClick={handleValidate} disabled={validateMutation.isPending}>
        {validateMutation.isPending ? 'Validating...' : 'Validate'}
      </Button>

      {validateMutation.data && (
        <div className="mt-4">
          {validateMutation.data.valid ? (
            <Alert variant="success">
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                Valid! Spec ID: {validateMutation.data.spec_id}
              </AlertDescription>
            </Alert>
          ) : (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <p className="font-semibold mb-2">Validation Errors:</p>
                <ul className="list-disc pl-4">
                  {validateMutation.data.errors.map((error, i) => (
                    <li key={i}>
                      <span className="font-mono text-xs">{error.field}</span>:{' '}
                      {error.message}
                    </li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}
    </Card>
  )
}
```

**Day 7 (Feb 17): Kill Switch Dashboard + Tier Management**

**Day 8 (Feb 17): Testing + Polish**

```typescript
// Unit tests for all components (120+ tests)
// E2E tests with Playwright (10 scenarios)
```

### 6.3 Phase 4 Deliverables

```yaml
✅ UI Features (6):
  1. Vibecoding Index Card
  2. Vibecoding Signal Breakdown
  3. Specification Validator
  4. Kill Switch Dashboard
  5. Tier Management Panel
  6. Progressive Routing Visualization

✅ Integration:
  - 12 API endpoints integrated
  - TanStack Query for server state
  - Zustand for client state
  - Error handling + retry logic

✅ Bilingual Support (EN/VI):
  - 40+ i18n keys translated
  - Language switcher component
  - RTL support (future-ready)

✅ Testing:
  - 120+ unit tests (Vitest)
  - 10 E2E tests (Playwright)
  - 90%+ component coverage

✅ Performance:
  - Dashboard load <1s p95
  - Component render <100ms
  - Lighthouse score >90
```

---

## 7. Phase 5-9: Summary (Abbreviated)

### Phase 5: Testing & QA (Feb 18, 1 day)
- **Owner**: QA Team
- **Deliverables**: 500+ automated tests running, manual testing complete

### Phase 6: Integration & Performance (Feb 18, 1 day)
- **Owner**: Tech Lead + DevOps Lead
- **Deliverables**: All services integrated, performance targets met

### Phase 7: Security & Compliance (Feb 19, 1 day)
- **Owner**: Security Lead + QA Lead
- **Deliverables**: Semgrep scan passing, OWASP ASVS L2 validated

### Phase 8: Documentation & Training (Feb 20, 1 day)
- **Owner**: Tech Lead + EM
- **Deliverables**: User guides, API docs, training materials

### Phase 9: Deployment & Validation (Feb 21, 1 day)
- **Owner**: DevOps Lead + Tech Lead
- **Deliverables**: Production deployment, CTO gate approval

---

## 12. Daily Schedule

### Daily Standup (9:00-9:15 AM ICT)

```yaml
Format:
  1. Quick round-robin (2 min per person):
     - What I did yesterday
     - What I'm doing today
     - Blockers (if any)

  2. Blocker resolution (5 min):
     - EM + Tech Lead address blockers
     - Assign action items

  3. Daily goal alignment (2 min):
     - Verify everyone aligned on sprint goals
     - Highlight dependencies

Location: Zoom call + #sdlc-orchestrator-daily Slack channel
```

### Daily Code Review (4:00-5:00 PM ICT)

```yaml
Format:
  - All PRs from the day reviewed
  - Tech Lead + 1 additional reviewer required
  - Max 2 hours for review (no blocking overnight)

Checklist:
  ✅ Zero Mock Policy compliance (no mocks in tests)
  ✅ Performance targets met (benchmarks passing)
  ✅ Test coverage ≥95% (backend), ≥90% (frontend)
  ✅ Security scan passing (Semgrep)
  ✅ AGPL containment (no minio/grafana imports)
  ✅ Code style (ruff, eslint passing)
  ✅ Documentation updated (if API changes)
```

### Daily Deployment (5:00-6:00 PM ICT)

```yaml
Process:
  1. Merge approved PRs to main (5:00-5:15 PM)
  2. CI/CD pipeline runs (5:15-5:35 PM):
     - Unit tests
     - Integration tests
     - Security scan
     - Build Docker images
     - Deploy to staging

  3. Staging smoke tests (5:35-5:50 PM):
     - Health check endpoints
     - Critical user journey E2E test
     - Database migration verification

  4. Production deployment (if staging passes):
     - Blue-green deployment
     - Gradual rollout (10% → 50% → 100%)
     - Monitor for 30 minutes post-deploy

  5. Rollback if issues detected (< 5 minutes)
```

---

## 13. Risk Mitigation

### Risk 1: Database Migration Failure

```yaml
Risk:
  Database migration fails in production, causing downtime

Probability: MEDIUM
Impact: HIGH (production downtime)

Mitigation:
  - Dry-run migrations on staging before production
  - Concurrent index creation (no table locking)
  - Rollback script tested and ready
  - Database backup before migration

Contingency:
  - Rollback migration within 5 minutes
  - Switch to read-only mode while fixing
  - Notify users via status page
```

### Risk 2: API Performance Degradation

```yaml
Risk:
  New API endpoints slow down existing endpoints

Probability: LOW
Impact: MEDIUM (user experience degradation)

Mitigation:
  - Load testing with 100 concurrent users
  - Performance benchmarks in CI/CD
  - Database query optimization (indexes)
  - Redis caching for hot paths

Contingency:
  - Enable feature flags (disable new endpoints)
  - Scale horizontally (add more API pods)
  - Investigate slow queries (pg_stat_statements)
```

### Risk 3: Integration Issues with OPA/MinIO

```yaml
Risk:
  OPA policies or MinIO storage integration fails

Probability: LOW
Impact: MEDIUM (vibecoding/evidence upload fails)

Mitigation:
  - Integration tests with real OPA/MinIO (no mocks)
  - Docker Compose for local testing
  - Health check endpoints for dependencies
  - Retry logic with exponential backoff

Contingency:
  - Fallback to rule-based routing (no OPA)
  - Fallback to local disk storage (no MinIO)
  - Alert DevOps team immediately
```

### Risk 4: Frontend-Backend API Mismatch

```yaml
Risk:
  Frontend expects different API response format

Probability: MEDIUM
Impact: LOW (UI errors, but non-blocking)

Mitigation:
  - OpenAPI 3.0 contract-first development
  - Pydantic schema validation (backend)
  - Zod schema validation (frontend)
  - Integration tests for all 12 endpoints

Contingency:
  - Quick fix deployment (< 1 hour)
  - Fallback UI with error message
  - Document breaking changes in CHANGELOG
```

---

## 14. Rollback Strategy

### Rollback Triggers

```yaml
Automatic Rollback (CI/CD):
  - Smoke tests fail after deployment
  - Health check endpoints return 500
  - Error rate >5% for 5 minutes
  - API latency p95 >500ms for 5 minutes

Manual Rollback (DevOps decision):
  - Critical bug discovered
  - CTO requests rollback
  - Customer-facing issue (loss of revenue)
```

### Rollback Procedure

```bash
# Step 1: Initiate rollback (< 1 minute)
kubectl rollout undo deployment/backend  # Instant rollback to previous version

# Step 2: Verify rollback successful (2 minutes)
kubectl rollout status deployment/backend
curl https://api.sdlc-orchestrator.com/health  # Should return 200

# Step 3: Rollback database migration (if needed, 2 minutes)
alembic downgrade -1  # Rollback last migration

# Step 4: Clear Redis cache (1 minute)
redis-cli FLUSHDB

# Step 5: Notify team (Slack alert)
# "Rollback complete. Version rolled back from X.Y.Z to X.Y.W. Investigating root cause."

Total Time: < 5 minutes
```

### Post-Rollback Actions

```yaml
Immediate (0-2 hours):
  - Root cause analysis (RCA) started
  - Hot fix branch created
  - Incident report drafted

Short-term (2-24 hours):
  - Fix implemented and tested
  - Code review expedited
  - Deploy fix to staging
  - Re-deploy to production (with extra monitoring)

Long-term (1-7 days):
  - RCA completed and documented
  - Post-mortem meeting (blameless)
  - Process improvements identified
  - Update runbooks
```

---

## 15. Success Criteria

### Sprint 118 Definition of Done

```yaml
Code Complete:
  ✅ All 14 tables created and seeded
  ✅ All 12 API endpoints implemented and tested
  ✅ All 6 UI features functional
  ✅ 500+ automated tests passing (95%+ coverage)
  ✅ 0 P0/P1 bugs in production

Performance Verified:
  ✅ API latency <100ms p95 (load tested with 100 users)
  ✅ Database queries <50ms p95
  ✅ Dashboard load <1s p95
  ✅ Redis cache hit rate >80%

Security Validated:
  ✅ Semgrep scan passing (0 HIGH/CRITICAL issues)
  ✅ Trivy container scan passing
  ✅ OWASP ASVS L2 compliance (264/264)
  ✅ AGPL containment verified (no SDK imports)

Documentation Complete:
  ✅ API documentation (OpenAPI 3.0)
  ✅ User guides (vibecoding, spec validator)
  ✅ Runbooks (deployment, rollback, incident response)
  ✅ ADRs updated (if architectural changes)

CTO Gate Review Approved:
  ✅ Tech Lead presents deliverables
  ✅ CTO reviews code quality
  ✅ CTO approves production deployment
  ✅ Sign-off documented (CTO signature)
```

### CTO Gate Checklist (Feb 21)

```yaml
Architecture Review:
  ☐ 5-layer architecture maintained
  ☐ AGPL containment verified (network-only MinIO/Grafana)
  ☐ Zero Mock Policy compliance (all tests use real services)
  ☐ Battle-tested patterns applied (BFlow, NQH-Bot, MTEP)

Code Quality Review:
  ☐ 95%+ test coverage (backend)
  ☐ 90%+ test coverage (frontend)
  ☐ All tests passing (500+ tests)
  ☐ No code smells (SonarQube scan)

Performance Review:
  ☐ API latency <100ms p95 (load test report)
  ☐ Database queries optimized (<50ms p95)
  ☐ Caching strategy working (>80% hit rate)
  ☐ No memory leaks (profiling report)

Security Review:
  ☐ Semgrep scan passing (0 HIGH/CRITICAL)
  ☐ Trivy scan passing (0 HIGH/CRITICAL CVEs)
  ☐ JWT authentication working
  ☐ RBAC authorization working (13 roles)
  ☐ Rate limiting working (429 after 100 req/min)

Documentation Review:
  ☐ API docs complete (OpenAPI 3.0)
  ☐ User guides complete (screenshots + examples)
  ☐ Runbooks complete (deployment, rollback)
  ☐ ADRs updated (if architectural changes)

Deployment Review:
  ☐ Staging deployment successful
  ☐ Smoke tests passing
  ☐ Rollback tested (<5 min)
  ☐ Monitoring alerts configured

CTO Decision:
  ☐ APPROVED - Deploy to production
  ☐ CONDITIONALLY APPROVED - Fix X, Y, Z first
  ☐ REJECTED - Major issues, postpone deployment
```

---

## 16. Appendix: Team Contact Info

```yaml
Backend Team:
  Backend Lead: backend-lead@example.com (Slack: @backend-lead)
  Senior Backend Engineer: backend-eng@example.com (Slack: @backend-eng)

Frontend Team:
  Frontend Lead: frontend-lead@example.com (Slack: @frontend-lead)
  Senior Frontend Engineer: frontend-eng@example.com (Slack: @frontend-eng)

QA Team:
  QA Lead: qa-lead@example.com (Slack: @qa-lead)
  QA Engineer: qa-eng@example.com (Slack: @qa-eng)

DevOps Team:
  DevOps Lead: devops-lead@example.com (Slack: @devops-lead)

Leadership:
  Tech Lead: tech-lead@example.com (Slack: @tech-lead)
  Engineering Manager: em@example.com (Slack: @em)
  CTO: cto@example.com (Slack: @cto)

Slack Channels:
  #sdlc-orchestrator-dev (development discussion)
  #sdlc-orchestrator-daily (daily standups)
  #sdlc-orchestrator-ops (operations, incidents)
  #sdlc-orchestrator-pr-reviews (code review notifications)

GitHub:
  Repo: https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
  Project Board: https://github.com/orgs/Minh-Tam-Solution/projects/5
  Issues: https://github.com/Minh-Tam-Solution/SDLC-Orchestrator/issues
```

---

**D5 Status**: ✅ COMPLETE
**Document Version**: 2.0.0
**Sprint Duration**: 10 days (Feb 10-21, 2026)
**Team Size**: 8.5 FTE
**Total Deliverables**: 14 tables, 12 APIs, 6 UI features, 500+ tests
**Next Deliverable**: D6 - Architecture Diagrams (Feb 6-7)

---

**Sprint 118 Track 2 Progress**:
- ✅ D1: Database Schema Governance v2 (14 tables)
- ✅ D2: API Specification Governance v2 (12 endpoints)
- ✅ D3: Technical Dependencies (87 packages)
- ✅ D4: Testing Strategy (~500 tests, 95%+ coverage)
- ✅ D5: Implementation Phases (10-day sprint plan)
- ⏳ D6: Architecture Diagrams (5 diagrams)
