# Sprint 73 Local Testing Guide

**Purpose:** Test migration script locally before production deployment
**Environment:** Docker Compose (PostgreSQL + Backend + Frontend)
**Timeline:** 30 minutes

---

## 🐳 Step 1: Start Local Environment (5 min)

```bash
# Navigate to project root
cd /home/nqh/shared/SDLC-Orchestrator

# Start Docker Compose (PostgreSQL, Redis, Backend, Frontend)
docker-compose up -d

# Wait for services to be ready
docker-compose ps

# Expected:
# - postgres: Up (port 5432)
# - redis: Up (port 6379)
# - backend: Up (port 8000)
# - frontend: Up (port 3000)

# Check backend logs
docker-compose logs -f backend
```

**Checklist:**
- [ ] All containers running?
- [ ] Backend started without errors?
- [ ] Database connection successful?

---

## 📊 Step 2: Check Database State (Before Migration)

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d sdlc_orchestrator

# Check current state
SELECT COUNT(*) as total_users FROM users WHERE deleted_at IS NULL;
SELECT COUNT(*) as users_without_org FROM users WHERE organization_id IS NULL AND deleted_at IS NULL;
SELECT COUNT(*) as total_projects FROM projects WHERE deleted_at IS NULL;
SELECT COUNT(*) as projects_without_team FROM projects WHERE team_id IS NULL AND deleted_at IS NULL;

# Check gates count
SELECT COUNT(*) as total_gates FROM gates;

# Check projects without gates
SELECT p.id, p.name, COUNT(g.id) as gate_count
FROM projects p
LEFT JOIN gates g ON p.id = g.project_id
WHERE p.deleted_at IS NULL
GROUP BY p.id, p.name
HAVING COUNT(g.id) = 0;

\q
```

**Record baseline:**
- Total users: __________
- Users without org: __________
- Total projects: __________
- Projects without team: __________
- Total gates (before): __________
- Projects without gates: __________

---

## 🔄 Step 3: Run Migration (Dry Run)

```bash
# Exec into backend container
docker-compose exec backend bash

# Generate SQL preview
cd /app
alembic upgrade head --sql > /tmp/s73_migration_preview.sql

# Review SQL
cat /tmp/s73_migration_preview.sql | head -100

# Check for expected operations
echo "=== Organization creation ==="
grep -i "INSERT.*organizations" /tmp/s73_migration_preview.sql | head -5

echo "=== Team creation ==="
grep -i "INSERT.*teams" /tmp/s73_migration_preview.sql | head -5

echo "=== User migration ==="
grep -i "UPDATE.*users.*organization_id" /tmp/s73_migration_preview.sql | head -5

echo "=== Project migration ==="
grep -i "UPDATE.*projects.*team_id" /tmp/s73_migration_preview.sql | head -5

echo "=== Gate backfill ==="
grep -i "INSERT.*gates" /tmp/s73_migration_preview.sql | head -10

exit
```

**Checklist:**
- [ ] SQL preview generated?
- [ ] Organization INSERT found?
- [ ] Team INSERT found?
- [ ] User UPDATE found?
- [ ] Project UPDATE found?
- [ ] Gate INSERT found (5 per project)?
- [ ] No unexpected DROP/DELETE?

---

## ⚙️ Step 4: Run Migration (Actual)

```bash
# Exec into backend container
docker-compose exec backend bash

# Run migration
cd /app
alembic upgrade head 2>&1 | tee /tmp/s73_migration_output.log

# View output
cat /tmp/s73_migration_output.log
```

**Expected output:**
```
S73-T12: Creating default organization...
  ✓ Created default organization: <uuid>

S73-T13: Migrating users to default organization...
  ✓ Migrated <N> users to default organization

S73-T14: Creating 'Unassigned' team...
  ✓ Created 'Unassigned' team: <uuid>

S73-T15: Migrating projects to 'Unassigned' team...
  ✓ Migrated <N> projects to 'Unassigned' team
  ✓ Added <N> users as team members

S73-T16: Backfilling gates for existing projects...
  ✓ Created <N> gates for <M> projects

S73-T17: Verifying migration...
=== Migration Verification ===
Users without organization_id: 0 (expected: 0)
Projects without team_id: 0 (expected: 0)
Projects without gates: 0 (expected: 0)

✅ Migration completed successfully!
```

**Record results:**
- Users migrated: __________
- Projects migrated: __________
- Team members added: __________
- Gates created: __________
- Migration status: Success / Failed

---

## ✅ Step 5: Verify Migration Results

```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d sdlc_orchestrator

# Verify users have organization_id
SELECT COUNT(*) as users_without_org
FROM users
WHERE organization_id IS NULL AND deleted_at IS NULL;
-- Expected: 0

# Verify projects have team_id
SELECT COUNT(*) as projects_without_team
FROM projects
WHERE team_id IS NULL AND deleted_at IS NULL;
-- Expected: 0

# Verify projects have gates (at least 5)
SELECT p.id, p.name, COUNT(g.id) as gate_count
FROM projects p
LEFT JOIN gates g ON p.id = g.project_id
WHERE p.deleted_at IS NULL
GROUP BY p.id, p.name
HAVING COUNT(g.id) < 5;
-- Expected: 0 rows

# Check default organization
SELECT * FROM organizations WHERE slug = 'nhat-quang-holding';
-- Expected: 1 row

# Check unassigned team
SELECT * FROM teams WHERE slug = 'unassigned';
-- Expected: 1 row

# Check team members
SELECT COUNT(*) FROM team_members
WHERE team_id = (SELECT id FROM teams WHERE slug = 'unassigned');
-- Expected: Equal to user count

\q
```

**Verification results:**
- Users without org: __________ (must be 0)
- Projects without team: __________ (must be 0)
- Projects with <5 gates: __________ (must be 0)
- Default org exists: Yes / No
- Unassigned team exists: Yes / No
- Team members count: __________

---

## 🧪 Step 6: Test Auto-Gate Creation (BUG #7)

```bash
# Get access token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@sdlc-orchestrator.io", "password": "Admin@123"}' \
  | jq -r .access_token)

# Create new project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Local Test Project",
    "description": "Testing auto-gate creation",
    "slug": "local-test-s73"
  }' | jq .

# Expected response:
# {
#   "id": "...",
#   "name": "Local Test Project",
#   "gates_created": 5,  <-- CRITICAL
#   ...
# }

# Verify gates created
PROJECT_ID="<id-from-above>"
curl http://localhost:8000/api/v1/projects/${PROJECT_ID}/gates \
  -H "Authorization: Bearer $TOKEN" | jq '. | length'

# Expected: 5
```

**BUG #7 Verification:**
- [ ] New project returns `gates_created: 5`?
- [ ] Project actually has 5 gates?
- [ ] Gate names correct (Planning, Design, Code, Test, Deploy)?
- [ ] All gates in DRAFT status?
- [ ] Exit criteria pre-configured?

---

## 🎨 Step 7: Test Frontend (Optional)

```bash
# Frontend should be accessible at http://localhost:3000
# Open browser: http://localhost:3000

# Test:
# 1. Login page loads
# 2. Can login
# 3. Dashboard shows "Total Teams" stat
# 4. Teams page shows "Unassigned Projects"
# 5. Projects page has team filter
# 6. Can create project with team selector
```

---

## 🔄 Step 8: Test Migration Rollback

```bash
# Test downgrade (rollback migration)
docker-compose exec backend bash

cd /app
alembic downgrade -1

# Expected:
# - Removes team_id from projects
# - Removes organization_id from users
# - Deletes team memberships
# - Deletes auto-created gates
# - Deletes Unassigned team
# - Deletes default organization

# Verify rollback
docker-compose exec postgres psql -U postgres -d sdlc_orchestrator

SELECT COUNT(*) FROM organizations WHERE slug = 'nhat-quang-holding';
-- Expected: 0

SELECT COUNT(*) FROM teams WHERE slug = 'unassigned';
-- Expected: 0

SELECT COUNT(*) FROM users WHERE organization_id IS NOT NULL;
-- Expected: 0

\q

# Re-run migration (test idempotency)
alembic upgrade head

# Should complete successfully again
exit
```

**Rollback test:**
- [ ] Downgrade successful?
- [ ] Organization deleted?
- [ ] Team deleted?
- [ ] User organization_id cleared?
- [ ] Re-upgrade successful?

---

## 📊 Local Testing Results

```
=== SPRINT 73 LOCAL TESTING RESULTS ===
Date: January 18, 2026
Tester: __________

✅ Migration dry run: PASS / FAIL
✅ Migration execution: PASS / FAIL
✅ Data verification (0/0/0): PASS / FAIL
✅ Auto-gate creation (BUG #7): PASS / FAIL
✅ Migration rollback: PASS / FAIL
✅ Migration re-run (idempotency): PASS / FAIL

Overall Status: READY FOR PRODUCTION / NEEDS FIX

Issues Found:
_____________________________________________________________________________
_____________________________________________________________________________

Blockers:
_____________________________________________________________________________
_____________________________________________________________________________
```

---

## ✅ Sign-Off

If all local tests PASS, you are ready for production deployment.

**Backend Lead Approval:**
- [ ] Migration tested locally
- [ ] 0/0/0 verification passed
- [ ] BUG #7 verified (5 gates auto-created)
- [ ] Rollback tested successfully
- [ ] Ready for production

**Name:** ________________
**Date:** ________________
**Signature:** ✅ APPROVED FOR PRODUCTION

---

## 🚀 Next Step

After successful local testing:
1. Stop local Docker: `docker-compose down`
2. Proceed with **Production Deployment**
3. Reference: `SPRINT-73-PRODUCTION-DEPLOYMENT.md`

---

**Status:** ⏳ LOCAL TESTING IN PROGRESS
**Next:** Production Deployment (30 min)
