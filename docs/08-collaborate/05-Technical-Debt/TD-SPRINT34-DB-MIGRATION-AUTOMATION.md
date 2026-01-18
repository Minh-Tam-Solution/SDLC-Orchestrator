# Technical Debt: Fix Staging Database Migration Automation

**Ticket ID**: TD-SPRINT34-001
**Created**: December 16, 2025 (Sprint 33 Day 2)
**Priority**: P3 (Medium - Workaround Exists)
**Owner**: Backend Lead + DevOps Lead
**Sprint**: Sprint 34 (Post-Beta Launch)
**Estimated Effort**: 4-6 hours
**Status**: 🔴 **OPEN**

---

## Problem Statement

During Sprint 33 Day 2 staging deployment, Alembic database migrations execute successfully (`alembic upgrade head`) but **create zero tables** in the PostgreSQL database. This blocks automated smoke test execution and requires manual database schema setup.

### Impact

- ❌ Cannot run automated smoke tests in staging environment
- ❌ Manual schema setup required for each fresh deployment
- ❌ Slows down CI/CD pipeline validation
- ⚠️ Risk of schema drift between environments

**Workaround**: Manual schema export/import or use production docker-compose with port remapping.

---

## Reproduction Steps

### Environment

**Docker Compose**: `docker-compose.staging.yml`
**Database**: PostgreSQL 15.5 (sdlc-staging-postgres container)
**Backend**: FastAPI + SQLAlchemy 2.0 + Alembic 1.12+
**Date**: December 16, 2025

### Steps to Reproduce

```bash
# 1. Start fresh staging environment
docker compose -f docker-compose.staging.yml --env-file .env.staging down -v
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d

# 2. Wait for services to be healthy (30 seconds)
sleep 30

# 3. Check database is empty
docker exec sdlc-staging-postgres psql -U sdlc_staging_user \
  -d sdlc_orchestrator_staging -c "\dt"
# Expected: "Did not find any relations."

# 4. Run migrations
docker exec sdlc-staging-backend alembic upgrade head

# 5. Observe migration logs (looks successful)
# Output shows:
# INFO  [alembic.runtime.migration] Running upgrade  -> dce31118ffb7, Initial schema - 24 tables
# INFO  [alembic.runtime.migration] Running upgrade dce31118ffb7 -> a502ce0d23a7, ...
# ... (13 more migrations)

# 6. Check database again
docker exec sdlc-staging-postgres psql -U sdlc_staging_user \
  -d sdlc_orchestrator_staging -c "\dt"
# Expected: 24 tables (users, projects, gates, etc.)
# Actual: "Did not find any relations."  ❌

# 7. Check alembic version
docker exec sdlc-staging-backend alembic current
# Output: (empty - no current version)
```

---

## Expected Behavior

1. `alembic upgrade head` creates all 24 tables from migrations
2. `\dt` shows tables: users, projects, gates, evidence, etc.
3. `alembic current` shows latest migration hash (e.g., `k6f7g8h9i0j1`)
4. Backend health check `/health/ready` returns all dependencies healthy
5. Smoke tests can execute (users can be created, gates evaluated, etc.)

---

## Actual Behavior

1. ✅ `alembic upgrade head` runs without errors
2. ✅ Migration logs show all 13 migrations executing
3. ❌ `\dt` shows "Did not find any relations" (0 tables)
4. ❌ `alembic current` shows empty (no version tracked)
5. ❌ Smoke tests blocked (cannot create users, no tables exist)

---

## Error Logs & Evidence

### Alembic Migration Output

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> dce31118ffb7, Initial schema - 24 tables
INFO  [alembic.runtime.migration] Running upgrade dce31118ffb7 -> a502ce0d23a7, =========================================================================
INFO  [alembic.runtime.migration] Running upgrade a502ce0d23a7 -> f8a9b2c3d4e5, add_github_fields_to_projects
INFO  [alembic.runtime.migration] Running upgrade a502ce0d23a7 -> b7c8d9e0f1a2, Add compliance_scans and compliance_violations tables
INFO  [alembic.runtime.migration] Running upgrade b7c8d9e0f1a2 -> c8d9e0f1a2b3, Add scan_jobs table for persistent job queue
INFO  [alembic.runtime.migration] Running upgrade c8d9e0f1a2b3, f8a9b2c3d4e5 -> d9e0f1a2b3c4, Merge compliance and github branches
INFO  [alembic.runtime.migration] Running upgrade d9e0f1a2b3c4 -> e0f1a2b3c4d5, Add notification enhancement fields
INFO  [alembic.runtime.migration] Running upgrade e0f1a2b3c4d5 -> f1a2b3c4d5e6, Add performance optimization indexes
INFO  [alembic.runtime.migration] Running upgrade f1a2b3c4d5e6 -> g2b3c4d5e6f7, Add MTEP Platform and pilot team accounts
INFO  [alembic.runtime.migration] Running upgrade g2b3c4d5e6f7 -> h3c4d5e6f7g8, Add pilot feedback tables
INFO  [alembic.runtime.migration] Running upgrade h3c4d5e6f7g8 -> i4d5e6f7g8h9, Add usage tracking tables
INFO  [alembic.runtime.migration] Running upgrade i4d5e6f7g8h9 -> j5e6f7g8h9i0, Add SDLC 5.1.3 validation tables
INFO  [alembic.runtime.migration] Running upgrade j5e6f7g8h9i0 -> k6f7g8h9i0j1, Add Gate G3 performance indexes
```

**Status**: Logs indicate success, but no tables created.

### Backend Runtime Error (scan_jobs Missing)

```
sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError)
<class 'asyncpg.exceptions.UndefinedTableError'>: relation "scan_jobs" does not exist

[SQL: SELECT scan_jobs.id, scan_jobs.project_id, ... FROM scan_jobs
WHERE scan_jobs.status = $1::VARCHAR AND scan_jobs.started_at < $2::TIMESTAMP]
```

**Context**: Backend scheduler tries to query scan_jobs table at startup (compliance job queue processing). Table doesn't exist because migrations didn't actually create it.

---

## Hypotheses (Root Cause)

### Hypothesis 1: Database Connection String Mismatch

**Theory**: Alembic connects to a different database than the backend expects.

**Evidence**:
- Backend env var: `DATABASE_URL=postgresql+asyncpg://sdlc_staging_user:${POSTGRES_PASSWORD}@postgres:5432/sdlc_orchestrator_staging`
- Alembic config: `alembic.ini` might use different URL
- Docker network: Backend uses `postgres:5432` (Docker DNS), alembic might use `localhost:5450` (host mapping)

**Test**:
```bash
docker exec sdlc-staging-backend env | grep DATABASE_URL
docker exec sdlc-staging-backend cat alembic.ini | grep sqlalchemy.url
```

**Resolution**: Ensure both use same connection string.

---

### Hypothesis 2: Transaction Rollback

**Theory**: Alembic commits migrations in a transaction that gets rolled back.

**Evidence**:
- Migrations execute (logs show "Running upgrade")
- No error messages (would show rollback if failed)
- Tables not persisted (transaction never committed?)

**Test**:
```bash
# Check if alembic_version table exists
docker exec sdlc-staging-postgres psql -U sdlc_staging_user \
  -d sdlc_orchestrator_staging -c "SELECT * FROM alembic_version;"
# If table exists but is empty → transaction issue
# If table doesn't exist → connection issue
```

**Resolution**: Add verbose logging to migrations, check for implicit rollback.

---

### Hypothesis 3: Schema Permissions

**Theory**: `sdlc_staging_user` lacks CREATE TABLE permissions on public schema.

**Evidence**:
- Schema was manually reset: `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`
- GRANT command used: `GRANT ALL ON SCHEMA public TO sdlc_staging_user;`
- Might need additional table-level permissions

**Test**:
```bash
# Check user permissions
docker exec sdlc-staging-postgres psql -U sdlc_staging_user \
  -d sdlc_orchestrator_staging -c "\dp"

# Try creating table manually
docker exec sdlc-staging-postgres psql -U sdlc_staging_user \
  -d sdlc_orchestrator_staging -c "CREATE TABLE test (id INT);"
```

**Resolution**: Grant explicit CREATE permission if manual table creation fails.

---

## Investigation Plan

### Phase 1: Verify Connection (30 min)

1. Check backend DATABASE_URL env var
2. Check alembic.ini sqlalchemy.url
3. Verify both point to same database
4. Test connection with psql using both URLs

### Phase 2: Transaction Analysis (1 hour)

1. Enable SQLAlchemy echo (verbose SQL logging)
2. Run single migration with `alembic upgrade +1`
3. Check if alembic_version table exists
4. Query alembic_version for current revision
5. Look for ROLLBACK statements in logs

### Phase 3: Permissions Check (30 min)

1. List user permissions on public schema
2. Attempt manual table creation
3. Check table ownership after migration
4. Grant explicit permissions if needed

### Phase 4: Alembic Debugging (1 hour)

1. Run alembic with verbose logging: `alembic -x verbose=true upgrade head`
2. Check migration history: `alembic history`
3. Try offline SQL generation: `alembic upgrade head --sql > migrations.sql`
4. Review generated SQL for issues

---

## Workarounds (Immediate)

### Workaround 1: Manual Schema Export/Import ⭐ **RECOMMENDED**

```bash
# 1. Export schema from working production environment
docker exec sdlc-postgres pg_dump -U sdlc_user -d sdlc_orchestrator \
  --schema-only --no-owner --no-acl > /tmp/schema.sql

# 2. Import to staging
cat /tmp/schema.sql | docker exec -i sdlc-staging-postgres \
  psql -U sdlc_staging_user -d sdlc_orchestrator_staging

# 3. Mark alembic as current
docker exec sdlc-staging-backend alembic stamp head

# 4. Verify tables exist
docker exec sdlc-staging-postgres psql -U sdlc_staging_user \
  -d sdlc_orchestrator_staging -c "\dt" | wc -l
# Expected: 24+ tables
```

**Time**: 15 minutes
**Risk**: Low (read-only export from production)

---

### Workaround 2: Use Production Docker Compose

```bash
# 1. Copy production compose
cp docker-compose.yml docker-compose.staging-v2.yml

# 2. Remap conflicting ports (9093 → 9094, etc.)
sed -i 's/9093:9093/9094:9093/g' docker-compose.staging-v2.yml

# 3. Use staging env vars
docker compose -f docker-compose.staging-v2.yml \
  --env-file .env.staging up -d

# 4. Verify migrations run correctly
docker exec <backend-container> alembic current
# Expected: k6f7g8h9i0j1 (latest migration)
```

**Time**: 30 minutes
**Risk**: Medium (need to remap multiple ports, test thoroughly)

---

## Success Criteria (Definition of Done)

1. ✅ `alembic upgrade head` creates all 24 tables in staging database
2. ✅ `\dt` shows expected tables (users, projects, gates, evidence, etc.)
3. ✅ `alembic current` shows latest migration version
4. ✅ Backend health check `/health/ready` returns all dependencies healthy
5. ✅ Smoke test 1 (Authentication) can create user and login successfully
6. ✅ Process documented in runbook for future deployments
7. ✅ CI/CD pipeline updated to verify migrations in staging

---

## References

**Sprint 33 Documents**:
- [Day 2 Status Report](../../09-govern/01-CTO-Reports/2025-12-16-CTO-SPRINT-33-DAY2-STATUS.md)
- [Day 2 Smoke Tests](../../06-deploy/01-Deployment-Strategy/SPRINT-33-DAY2-SMOKE-TESTS.md)

**Git Commits**:
- [0aa0f13](https://github.com/Minh-Tam-Solution/SDLC-Orchestrator/commit/0aa0f13) - Day 2 infrastructure complete

**Related Files**:
- `backend/alembic/alembic.ini` - Alembic configuration
- `backend/alembic/env.py` - Migration environment setup
- `backend/app/core/config.py` - Database connection settings
- `docker-compose.staging.yml` - Staging service definitions

---

## Owner Assignment

**Primary**: Backend Lead (Alembic + SQLAlchemy expertise)
**Secondary**: DevOps Lead (Docker + PostgreSQL permissions)
**Reviewer**: CTO (Final approval on fix approach)

**Target Sprint**: Sprint 34 (Week of Dec 23-27, 2025)
**Estimated Effort**: 4-6 hours (investigation + fix + testing + documentation)

---

## Notes

- This issue does NOT block beta launch (manual workaround available)
- Production environment works correctly (migrations create tables as expected)
- Issue is specific to staging docker-compose.staging.yml configuration
- Similar issue might affect other fresh deployments (dev, testing, QA)

**Created**: December 16, 2025
**Last Updated**: December 16, 2025
**Status**: 🔴 **OPEN** - Awaiting Sprint 34 assignment
