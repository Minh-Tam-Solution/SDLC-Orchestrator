# Sprint 73: Staging Deployment Checklist
**Teams Integration - Production Readiness Validation**

**Sprint:** 73 - Teams Integration
**Date:** February 10, 2026
**Status:** ⏳ READY FOR STAGING
**Authority:** DevOps + Backend Lead + CTO Approved

---

## 🎯 Deployment Objectives

**Primary Goals:**
1. Validate data migration script on staging
2. Test auto-gate creation for new projects
3. Verify frontend Teams integration
4. Identify production blockers
5. Create rollback plan

**Success Criteria:**
- ✅ Migration completes without errors
- ✅ All users have organization_id
- ✅ All projects have team_id + 5 gates
- ✅ Frontend Teams features work correctly
- ✅ No data loss or corruption

---

## 📋 Pre-Deployment Checklist

### 1. Code Readiness
- [x] Frontend build passes (npm run build)
- [x] Backend tests pass (pytest)
- [x] Linting passes (ruff, ESLint)
- [x] Git branch up-to-date with main
- [x] All commits have CTO approval

### 2. Database Preparation
- [ ] Staging database backup created
- [ ] Backup verified and downloadable
- [ ] Database connection string configured
- [ ] Alembic migration history checked

### 3. Environment Configuration
- [ ] Staging environment variables updated
- [ ] API keys and secrets rotated
- [ ] CORS settings allow staging domain
- [ ] Redis cache cleared

### 4. Monitoring Setup
- [ ] Grafana dashboards configured
- [ ] Prometheus metrics endpoint active
- [ ] Error logging (Sentry) configured
- [ ] OnCall alerts configured

---

## 🚀 Deployment Steps

### Phase 1: Backend Deployment (30 min)

#### Step 1.1: Database Backup (5 min)
```bash
# Connect to staging database
ssh staging-db-server

# Create backup with timestamp
timestamp=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U postgres -d sdlc_orchestrator_staging > \
  /backups/pre_s73_migration_${timestamp}.sql

# Verify backup size (should be >100MB for production-like data)
ls -lh /backups/pre_s73_migration_${timestamp}.sql

# Upload backup to S3
aws s3 cp /backups/pre_s73_migration_${timestamp}.sql \
  s3://nqh-backups/sdlc-orchestrator/staging/

# Record backup location
echo "Backup: s3://nqh-backups/sdlc-orchestrator/staging/pre_s73_migration_${timestamp}.sql"
```

**Verification:**
- [ ] Backup file exists
- [ ] Backup size reasonable (>100MB)
- [ ] S3 upload confirmed
- [ ] Backup location documented

---

#### Step 1.2: Deploy Backend Code (10 min)
```bash
# SSH to staging server
ssh staging-backend-server

# Pull latest code
cd /opt/sdlc-orchestrator/backend
git fetch origin
git checkout main
git pull origin main

# Verify Sprint 73 code present
git log --oneline -5
# Should show:
# - feat(sprint73): Teams data migration script
# - feat(sprint73): Auto-create default gates
# - feat(sprint73): Add team statistics to Dashboard

# Install dependencies (if needed)
pip install -r requirements.txt

# Restart backend service
sudo systemctl restart sdlc-orchestrator-backend
sudo systemctl status sdlc-orchestrator-backend

# Check logs for startup errors
tail -f /var/log/sdlc-orchestrator/backend.log
```

**Verification:**
- [ ] Code deployed successfully
- [ ] Service started without errors
- [ ] API health check passes (GET /health)
- [ ] No errors in logs

---

#### Step 1.3: Run Migration (DRY RUN) (5 min)
```bash
# Run migration in dry-run mode to preview changes
cd /opt/sdlc-orchestrator/backend
alembic upgrade head --sql > /tmp/s73_migration_preview.sql

# Review SQL statements
cat /tmp/s73_migration_preview.sql

# Expected output:
# - CREATE organization "Nhat Quang Holding"
# - CREATE team "Unassigned Projects"
# - UPDATE users SET organization_id = ...
# - UPDATE projects SET team_id = ...
# - INSERT INTO gates (5 per project)
```

**Verification:**
- [ ] SQL preview looks correct
- [ ] No unexpected DROP or DELETE statements
- [ ] Organization/team creation statements present
- [ ] User/project UPDATE statements present

---

#### Step 1.4: Run Migration (ACTUAL) (10 min)
```bash
# Run migration for real
cd /opt/sdlc-orchestrator/backend
alembic upgrade head

# Monitor output for errors
# Expected output:
# S73-T12: Creating default organization...
#   ✓ Created default organization: uuid-1234
# S73-T13: Migrating users to default organization...
#   ✓ Migrated 50 users to default organization
# S73-T14: Creating 'Unassigned' team...
#   ✓ Created 'Unassigned' team: uuid-5678
# S73-T15: Migrating projects to 'Unassigned' team...
#   ✓ Migrated 25 projects to 'Unassigned' team
#   ✓ Added 50 users as team members
# S73-T16: Backfilling gates for existing projects...
#   ✓ Created 125 gates for 25 projects
# S73-T17: Verifying migration...
# === Migration Verification ===
# Users without organization_id: 0 (expected: 0)
# Projects without team_id: 0 (expected: 0)
# Projects without gates: 0 (expected: 0)
# ✅ Migration completed successfully!

# Record migration output
alembic upgrade head 2>&1 | tee /tmp/s73_migration_output.log
```

**Verification:**
- [ ] Migration completed without errors
- [ ] All verification checks passed (0/0/0)
- [ ] Organization created
- [ ] Team created
- [ ] Users migrated
- [ ] Projects migrated
- [ ] Gates backfilled

---

### Phase 2: Frontend Deployment (15 min)

#### Step 2.1: Build Frontend (5 min)
```bash
# On local machine or CI/CD
cd /path/to/SDLC-Orchestrator/frontend/web

# Install dependencies
npm install

# Build for production
npm run build

# Verify build output
ls -lh dist/
# Should see index.html, assets/, etc.

# Check build size (<5MB for good performance)
du -sh dist/
```

**Verification:**
- [ ] Build completes without errors
- [ ] No TypeScript errors
- [ ] No ESLint errors
- [ ] Build size reasonable (<5MB)

---

#### Step 2.2: Deploy Frontend (5 min)
```bash
# Upload to staging server
rsync -avz --delete dist/ staging-frontend-server:/var/www/sdlc-orchestrator/

# SSH to frontend server
ssh staging-frontend-server

# Verify files deployed
ls -la /var/www/sdlc-orchestrator/

# Restart web server (if needed)
sudo systemctl restart nginx
sudo systemctl status nginx

# Clear CloudFlare cache (if using CDN)
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

**Verification:**
- [ ] Files deployed successfully
- [ ] Nginx restarted without errors
- [ ] Static files accessible
- [ ] CDN cache cleared

---

#### Step 2.3: Verify Frontend Load (5 min)
```bash
# Test frontend loads
curl -I https://staging.sdlc-orchestrator.nhatquangholding.com

# Expected:
# HTTP/2 200
# content-type: text/html
# cache-control: public, max-age=0

# Check browser console for errors
# Open: https://staging.sdlc-orchestrator.nhatquangholding.com
# F12 → Console tab
# Should be no errors
```

**Verification:**
- [ ] Frontend loads (HTTP 200)
- [ ] No JavaScript errors in console
- [ ] Assets load correctly (CSS, JS, images)
- [ ] Favicon loads

---

### Phase 3: Smoke Tests (30 min)

#### Test 1: Login & Dashboard (5 min)
```
URL: https://staging.sdlc-orchestrator.nhatquangholding.com/login

Steps:
1. Navigate to login page
2. Login with test user (test@nhatquangholding.com / Test@123)
3. Verify redirect to dashboard
4. Check dashboard statistics:
   - Total Projects: Should show count
   - Total Teams: Should show 1 (Unassigned)
   - Active Gates: Should show count
   - Pending Approvals: Should show count
   - Pass Rate: Should show percentage

Expected:
✅ Login successful
✅ Dashboard loads <2s
✅ All stat cards display correctly
✅ Total Teams card shows "1" (Unassigned team)
✅ Clicking Total Teams navigates to /teams
```

**Verification:**
- [ ] Login works
- [ ] Dashboard loads
- [ ] Team statistics visible
- [ ] Navigation works

---

#### Test 2: Teams List Page (5 min)
```
URL: https://staging.sdlc-orchestrator.nhatquangholding.com/teams

Steps:
1. Navigate to Teams page
2. Verify "Unassigned Projects" team visible
3. Click on "Unassigned Projects" team
4. Verify team detail page loads
5. Check team members list (should show all users)
6. Check team projects (should show all existing projects)

Expected:
✅ Teams list loads
✅ "Unassigned Projects" team visible
✅ Team detail page shows members
✅ Team detail page shows projects
✅ All migrated users appear as team members
```

**Verification:**
- [ ] Teams page loads
- [ ] Unassigned team visible
- [ ] Team members list correct
- [ ] Projects assigned to team

---

#### Test 3: Create New Project with Auto-Gates (10 min)
```
URL: https://staging.sdlc-orchestrator.nhatquangholding.com/projects

Steps:
1. Navigate to Projects page
2. Click "Create Project" button
3. Fill in form:
   - Name: "Test Sprint 73 Auto-Gates"
   - Description: "Testing auto-gate creation feature"
   - Team: Select "Unassigned Projects"
   - Policy Pack: Standard
4. Click "Create Project"
5. Wait for project creation
6. Navigate to project detail page
7. Click on "Gates" tab
8. Verify 5 gates created:
   - Planning Review (Stage 01-PLAN)
   - Design Review (Stage 02-DESIGN)
   - Code Review (Stage 03-BUILD)
   - Test Review (Stage 05-TEST)
   - Deploy Approval (Stage 06-DEPLOY)
9. Verify all gates in DRAFT status

Expected:
✅ Project created successfully
✅ 5 gates auto-created (gates_created: 5 in response)
✅ All gates in DRAFT status
✅ Gate names: "{project name} - {gate name}"
✅ Exit criteria pre-configured
```

**Verification:**
- [ ] Project creation works
- [ ] 5 gates auto-created
- [ ] Gates visible in UI
- [ ] Gate names correct
- [ ] Exit criteria present

---

#### Test 4: Team Filter on Projects (5 min)
```
URL: https://staging.sdlc-orchestrator.nhatquangholding.com/projects

Steps:
1. Navigate to Projects page
2. Use team filter dropdown
3. Select "Unassigned Projects"
4. Verify only Unassigned team projects shown
5. Select "No Team"
6. Verify empty state or projects without team
7. Select "All Teams"
8. Verify all projects shown

Expected:
✅ Team filter dropdown works
✅ Filtering by team works correctly
✅ "No Team" option works
✅ "All Teams" shows all projects
✅ Filter badge shows active filter
```

**Verification:**
- [ ] Team filter works
- [ ] Projects filtered correctly
- [ ] No team option works
- [ ] All teams option works

---

#### Test 5: Migration Data Verification (5 min)
```
Database Query:

Steps:
1. SSH to staging database server
2. Connect to PostgreSQL
3. Run verification queries

Queries:
-- Check users have organization_id
SELECT COUNT(*) as users_without_org
FROM users
WHERE organization_id IS NULL AND deleted_at IS NULL;
-- Expected: 0

-- Check projects have team_id
SELECT COUNT(*) as projects_without_team
FROM projects
WHERE team_id IS NULL AND deleted_at IS NULL;
-- Expected: 0

-- Check projects have gates
SELECT p.id, p.name, COUNT(g.id) as gate_count
FROM projects p
LEFT JOIN gates g ON p.id = g.project_id
WHERE p.deleted_at IS NULL
GROUP BY p.id, p.name
HAVING COUNT(g.id) < 5;
-- Expected: 0 rows (all projects should have ≥5 gates)

-- Check organization exists
SELECT * FROM organizations WHERE slug = 'nhat-quang-holding';
-- Expected: 1 row

-- Check team exists
SELECT * FROM teams WHERE slug = 'unassigned';
-- Expected: 1 row

-- Check team members count
SELECT COUNT(*) as team_members
FROM team_members
WHERE team_id = (SELECT id FROM teams WHERE slug = 'unassigned');
-- Expected: Total user count
```

**Verification:**
- [ ] All users have organization_id
- [ ] All projects have team_id
- [ ] All projects have ≥5 gates
- [ ] Default organization exists
- [ ] Unassigned team exists
- [ ] Team members added

---

## 🐛 Issue Tracking

### Known Issues
| ID | Issue | Severity | Status | Workaround |
|----|-------|----------|--------|------------|
| S73-001 | Team selector empty on first load | Low | ⏳ | Refresh page |
| S73-002 | Dashboard team stat shows 0 | Medium | ⏳ | Cache issue |

### Issues Found During Staging
_Document any new issues found during staging deployment_

| ID | Issue | Severity | Status | Assigned To |
|----|-------|----------|--------|-------------|
| | | | | |

---

## 🔄 Rollback Plan

### Scenario 1: Migration Failed (During Migration)
```bash
# Stop migration if errors occur
# Migration is transactional, will auto-rollback

# If migration completed but data looks wrong:
# 1. Stop backend service
sudo systemctl stop sdlc-orchestrator-backend

# 2. Restore database from backup
psql -h localhost -U postgres -d sdlc_orchestrator_staging < \
  /backups/pre_s73_migration_${timestamp}.sql

# 3. Verify data restored
psql -h localhost -U postgres -d sdlc_orchestrator_staging -c \
  "SELECT COUNT(*) FROM users WHERE organization_id IS NULL;"
# Should show original count (before migration)

# 4. Restart backend with old code
git checkout <commit_before_s73>
sudo systemctl restart sdlc-orchestrator-backend
```

### Scenario 2: Frontend Issues (After Deployment)
```bash
# Rollback frontend to previous version
cd /var/www/sdlc-orchestrator/
cp -r ../sdlc-orchestrator.backup/* .

# Restart nginx
sudo systemctl restart nginx

# Clear CDN cache
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

### Scenario 3: Critical Production Bug
```bash
# Run migration downgrade
cd /opt/sdlc-orchestrator/backend
alembic downgrade -1

# This will:
# - Remove team_id from projects
# - Remove organization_id from users
# - Delete team memberships
# - Delete auto-created gates
# - Delete Unassigned team
# - Delete default organization

# Verify rollback
psql -h localhost -U postgres -d sdlc_orchestrator_staging -c \
  "SELECT COUNT(*) FROM organizations WHERE slug = 'nhat-quang-holding';"
# Expected: 0 (organization deleted)
```

---

## 📊 Post-Deployment Validation

### Performance Checks
```bash
# API latency check
curl -w "@curl-format.txt" -o /dev/null -s \
  https://staging-api.sdlc-orchestrator.nhatquangholding.com/health

# Expected: <100ms total_time

# Dashboard load time
curl -w "@curl-format.txt" -o /dev/null -s \
  https://staging.sdlc-orchestrator.nhatquangholding.com/

# Expected: <1s total_time
```

### Monitoring Checks
- [ ] Grafana dashboards show metrics
- [ ] Prometheus scraping backend
- [ ] Error rate <1% (first hour)
- [ ] No memory leaks (steady state)
- [ ] No database connection leaks

### Security Checks
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] CORS allows only staging domain
- [ ] API keys rotated
- [ ] No secrets in frontend bundle

---

## ✅ Sign-Off

### DevOps Engineer
- [ ] Database backup verified
- [ ] Migration completed successfully
- [ ] Monitoring configured
- [ ] Rollback plan tested

**Name:** ________________
**Date:** ________________
**Signature:** ________________

### Backend Lead
- [ ] Code deployed correctly
- [ ] Migration script verified
- [ ] API endpoints working
- [ ] No errors in logs

**Name:** ________________
**Date:** ________________
**Signature:** ________________

### Frontend Lead
- [ ] Frontend deployed correctly
- [ ] Teams features working
- [ ] No JavaScript errors
- [ ] Performance acceptable

**Name:** ________________
**Date:** ________________
**Signature:** ________________

### CTO Approval
- [ ] All smoke tests passed
- [ ] No critical issues found
- [ ] Performance metrics acceptable
- [ ] Ready for E2E test writing

**Name:** ________________
**Date:** ________________
**Signature:** ________________

---

## 📝 Next Steps

After staging deployment success:

1. **E2E Tests** (6 SP)
   - Write Playwright tests for Teams workflows
   - Test against staging environment
   - Verify permission boundaries

2. **Backend Integration Tests** (4 SP)
   - Write pytest tests for team access control
   - Test gate approval with team roles
   - Test team deletion cascade

3. **Production Deployment** (3 SP)
   - Schedule production maintenance window
   - Run migration on production database
   - Deploy to production servers
   - Monitor for 24 hours

---

**Status:** ⏳ READY FOR EXECUTION
**Next Action:** Execute Phase 1 (Backend Deployment)
**Timeline:** 75 minutes total deployment time
