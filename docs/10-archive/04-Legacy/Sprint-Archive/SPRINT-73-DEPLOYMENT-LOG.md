# Sprint 73 Staging Deployment Log

**Date:** February 10, 2026
**Sprint:** 73 - Teams Integration
**Environment:** Staging → Production
**Authority:** DevOps + Backend Lead + CTO

---

## 📋 Pre-Deployment Verification

### Code Readiness
- [x] Git working tree clean (23 commits ahead of origin/main)
- [x] Migration file exists: `alembic/versions/s73_teams_data_migration.py` (15KB)
- [x] E2E tests exist: `frontend/web/e2e/teams.spec.ts` (27KB)
- [x] Integration tests exist: `backend/tests/integration/test_sprint73_teams_integration.py`
- [x] All Sprint 73 code committed (8 commits total)

### Files Created/Modified
- ✅ `backend/app/services/gate_auto_creation_service.py` (549 lines)
- ✅ `backend/app/api/routes/projects.py` (modified - team_id support)
- ✅ `backend/alembic/versions/s73_teams_data_migration.py` (447 lines)
- ✅ `frontend/web/src/components/projects/CreateProjectDialog.tsx` (team selector)
- ✅ `frontend/web/src/pages/ProjectsPage.tsx` (team filter)
- ✅ `frontend/web/src/pages/DashboardPage.tsx` (team stats)
- ✅ `frontend/web/e2e/teams.spec.ts` (600 lines)
- ✅ `backend/tests/integration/test_sprint73_teams_integration.py` (700 lines)

---

## 🚀 Phase 1: Backend Deployment (Staging)

### Step 1.1: Database Backup ⏳

**Start Time:** _____________
**End Time:** _____________

**Commands:**
```bash
# Connect to staging database server
ssh staging-db-server

# Create timestamped backup
timestamp=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U postgres -d sdlc_orchestrator_staging > \
  /backups/pre_s73_migration_${timestamp}.sql

# Verify backup
ls -lh /backups/pre_s73_migration_${timestamp}.sql

# Upload to S3
aws s3 cp /backups/pre_s73_migration_${timestamp}.sql \
  s3://nqh-backups/sdlc-orchestrator/staging/
```

**Checklist:**
- [ ] SSH connection successful
- [ ] Backup created successfully
- [ ] Backup size: __________ MB (expected: >100MB)
- [ ] S3 upload successful
- [ ] Backup URL recorded: __________________________________________

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### Step 1.2: Deploy Backend Code ⏳

**Start Time:** _____________
**End Time:** _____________

**Commands:**
```bash
# SSH to staging backend server
ssh staging-backend-server

# Navigate to backend directory
cd /opt/sdlc-orchestrator/backend

# Pull latest code
git fetch origin
git checkout main
git pull origin main

# Verify Sprint 73 commits
git log --oneline -10 | grep -i "sprint.*73\|s73\|teams"

# Install dependencies (if requirements.txt changed)
pip install -r requirements.txt

# Restart backend service
sudo systemctl restart sdlc-orchestrator-backend

# Check service status
sudo systemctl status sdlc-orchestrator-backend

# Monitor logs for startup errors
tail -n 50 /var/log/sdlc-orchestrator/backend.log
```

**Checklist:**
- [ ] Git pull successful
- [ ] Sprint 73 commits visible in log
- [ ] Dependencies installed (if needed)
- [ ] Service restarted successfully
- [ ] Service status: Active (running)
- [ ] No errors in logs
- [ ] API health check: `curl http://localhost:8000/health`

**Commits Found:**
_____________________________________________________________________________
_____________________________________________________________________________

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### Step 1.3: Migration Dry Run ⏳

**Start Time:** _____________
**End Time:** _____________

**Commands:**
```bash
# Generate SQL preview (dry run)
cd /opt/sdlc-orchestrator/backend
alembic upgrade head --sql > /tmp/s73_migration_preview.sql

# Review SQL statements
cat /tmp/s73_migration_preview.sql | head -100

# Check for expected operations
grep -i "CREATE.*organization" /tmp/s73_migration_preview.sql
grep -i "CREATE.*team" /tmp/s73_migration_preview.sql
grep -i "UPDATE.*users.*organization_id" /tmp/s73_migration_preview.sql
grep -i "UPDATE.*projects.*team_id" /tmp/s73_migration_preview.sql
grep -i "INSERT.*gates" /tmp/s73_migration_preview.sql
```

**Checklist:**
- [ ] SQL preview generated successfully
- [ ] Organization creation statement found
- [ ] Team creation statement found
- [ ] User update statement found (SET organization_id)
- [ ] Project update statement found (SET team_id)
- [ ] Gate insert statements found (5 per project)
- [ ] No DROP or DELETE statements (except in downgrade)
- [ ] SQL looks safe to execute

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### Step 1.4: Run Migration (ACTUAL) ⏳

**Start Time:** _____________
**End Time:** _____________

**Commands:**
```bash
# Run actual migration
cd /opt/sdlc-orchestrator/backend
alembic upgrade head 2>&1 | tee /tmp/s73_migration_output.log

# View migration output
cat /tmp/s73_migration_output.log
```

**Expected Output:**
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

**Actual Results:**
- Users migrated: __________
- Projects migrated: __________
- Team members added: __________
- Gates created: __________

**Checklist:**
- [ ] Migration completed without errors
- [ ] Verification: 0 users without organization_id
- [ ] Verification: 0 projects without team_id
- [ ] Verification: 0 projects without gates
- [ ] Default organization created (Nhat Quang Holding)
- [ ] Unassigned team created
- [ ] Migration log saved to /tmp/s73_migration_output.log

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

## 🎨 Phase 2: Frontend Deployment (Staging)

### Step 2.1: Build Frontend ⏳

**Start Time:** _____________
**End Time:** _____________

**Commands:**
```bash
# On local machine or CI/CD server
cd /path/to/SDLC-Orchestrator/frontend/web

# Install dependencies (if needed)
npm install

# Run linting
npm run lint

# Build for production
npm run build

# Verify build output
ls -lh dist/
du -sh dist/
```

**Checklist:**
- [ ] npm install successful
- [ ] Linting passed (0 errors)
- [ ] Build completed successfully
- [ ] Build size: __________ MB (expected: <5MB)
- [ ] dist/ directory contains index.html
- [ ] dist/assets/ contains JS and CSS files

**Build Output:**
_____________________________________________________________________________
_____________________________________________________________________________

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### Step 2.2: Deploy Frontend Files ⏳

**Start Time:** _____________
**End Time:** _____________

**Commands:**
```bash
# Upload to staging server
rsync -avz --delete dist/ staging-frontend-server:/var/www/sdlc-orchestrator/

# SSH to frontend server
ssh staging-frontend-server

# Verify files deployed
ls -la /var/www/sdlc-orchestrator/
ls -la /var/www/sdlc-orchestrator/assets/

# Restart nginx
sudo systemctl restart nginx
sudo systemctl status nginx

# Test nginx config
sudo nginx -t
```

**Checklist:**
- [ ] rsync completed successfully
- [ ] Files visible in /var/www/sdlc-orchestrator/
- [ ] Nginx config test passed
- [ ] Nginx restarted successfully
- [ ] Nginx status: Active (running)

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### Step 2.3: Verify Frontend Load ⏳

**Start Time:** _____________
**End Time:** _____________

**Commands:**
```bash
# Test frontend loads (staging URL)
curl -I https://staging.sdlc-orchestrator.nhatquangholding.com

# Check for HTTP 200
# Check content-type: text/html
```

**Browser Test:**
1. Open: https://staging.sdlc-orchestrator.nhatquangholding.com
2. Open DevTools (F12) → Console tab
3. Check for JavaScript errors
4. Verify page loads correctly

**Checklist:**
- [ ] curl returns HTTP 200
- [ ] Content-Type: text/html
- [ ] Browser loads page successfully
- [ ] No JavaScript errors in console
- [ ] CSS styles applied correctly
- [ ] Images/icons load correctly
- [ ] Page load time: __________ seconds (expected: <2s)

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

## 🧪 Phase 3: Smoke Tests (Staging)

### Test 1: Login & Dashboard ⏳

**Start Time:** _____________
**End Time:** _____________

**Test Steps:**
1. Navigate to: https://staging.sdlc-orchestrator.nhatquangholding.com/login
2. Login with: test@nhatquangholding.com / Test@123
3. Verify redirect to /dashboard
4. Check dashboard statistics:
   - Total Projects: __________
   - **Total Teams: __________ (expected: 1)** ← NEW
   - Active Gates: __________
   - Pending Approvals: __________
   - Pass Rate: __________%

**Checklist:**
- [ ] Login successful
- [ ] Redirect to dashboard
- [ ] Dashboard loads <2s
- [ ] All stat cards visible
- [ ] **Total Teams card shows correct count**
- [ ] Clicking "Total Teams" navigates to /teams

**Screenshot:** (Optional)
_____________________________________________________________________________

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### Test 2: Teams List Page ⏳

**Start Time:** _____________
**End Time:** _____________

**Test Steps:**
1. Navigate to: https://staging.sdlc-orchestrator.nhatquangholding.com/teams
2. Verify "Unassigned Projects" team visible
3. Click on "Unassigned Projects" team
4. Check team detail page:
   - Team members count: __________
   - Team projects count: __________

**Checklist:**
- [ ] Teams page loads successfully
- [ ] "Unassigned Projects" team visible
- [ ] Team detail page loads
- [ ] Team members list shows all migrated users
- [ ] Team projects list shows all migrated projects
- [ ] Team member roles displayed correctly

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### Test 3: Create Project with Auto-Gates (BUG #7) ⏳

**Start Time:** _____________
**End Time:** _____________

**Test Steps:**
1. Navigate to: https://staging.sdlc-orchestrator.nhatquangholding.com/projects
2. Click "Create Project"
3. Fill form:
   - Name: "Test Sprint 73 Auto-Gates"
   - Description: "Testing auto-gate creation"
   - Team: Select "Unassigned Projects"
   - Policy Pack: Standard
4. Click "Create Project"
5. Navigate to project detail page
6. Click "Gates" tab
7. Verify gates created:
   - [ ] Planning Review (01-PLAN)
   - [ ] Design Review (02-DESIGN)
   - [ ] Code Review (03-BUILD)
   - [ ] Test Review (05-TEST)
   - [ ] Deploy Approval (06-DEPLOY)

**Checklist:**
- [ ] Project created successfully
- [ ] **5 gates auto-created (BUG #7 verified)**
- [ ] All gates in DRAFT status
- [ ] Gate names format: "{Project Name} - {Gate Name}"
- [ ] Exit criteria pre-configured for each gate
- [ ] Gates visible in UI

**Project ID:** __________
**Gates Created:** __________

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### Test 4: Team Filter on Projects ⏳

**Start Time:** _____________
**End Time:** _____________

**Test Steps:**
1. Navigate to: https://staging.sdlc-orchestrator.nhatquangholding.com/projects
2. Locate team filter dropdown
3. Select "Unassigned Projects"
4. Verify projects filtered
5. Select "All Teams"
6. Verify all projects shown

**Checklist:**
- [ ] Team filter dropdown visible
- [ ] Filtering by "Unassigned Projects" works
- [ ] Only team projects shown when filtered
- [ ] "All Teams" shows all projects
- [ ] Filter badge/indicator visible when active
- [ ] Team badge visible on project cards

**Projects visible (Unassigned filter):** __________
**Projects visible (All Teams):** __________

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### Test 5: Migration Data Verification (Database) ⏳

**Start Time:** _____________
**End Time:** _____________

**Commands:**
```bash
# SSH to staging database
ssh staging-db-server

# Connect to PostgreSQL
psql -h localhost -U postgres -d sdlc_orchestrator_staging

# Run verification queries
SELECT COUNT(*) as users_without_org
FROM users
WHERE organization_id IS NULL AND deleted_at IS NULL;

SELECT COUNT(*) as projects_without_team
FROM projects
WHERE team_id IS NULL AND deleted_at IS NULL;

SELECT p.id, p.name, COUNT(g.id) as gate_count
FROM projects p
LEFT JOIN gates g ON p.id = g.project_id
WHERE p.deleted_at IS NULL
GROUP BY p.id, p.name
HAVING COUNT(g.id) < 5;

SELECT * FROM organizations WHERE slug = 'nhat-quang-holding';

SELECT * FROM teams WHERE slug = 'unassigned';

SELECT COUNT(*) as team_members
FROM team_members
WHERE team_id = (SELECT id FROM teams WHERE slug = 'unassigned');
```

**Results:**
- Users without organization_id: __________ (expected: 0)
- Projects without team_id: __________ (expected: 0)
- Projects with <5 gates: __________ (expected: 0)
- Default organization exists: [ ] Yes [ ] No
- Unassigned team exists: [ ] Yes [ ] No
- Team members count: __________ (expected: equal to user count)

**Checklist:**
- [ ] 0 users without organization_id
- [ ] 0 projects without team_id
- [ ] 0 projects with <5 gates
- [ ] Default organization "Nhat Quang Holding" exists
- [ ] Unassigned team exists
- [ ] All users added as team members

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

## ✅ Staging Deployment Sign-Off

### DevOps Engineer
- [ ] Database backup verified
- [ ] Migration completed successfully
- [ ] Backend deployed and running
- [ ] Frontend deployed and accessible
- [ ] All smoke tests passed

**Name:** ________________
**Date:** ________________
**Status:** [ ] PASS [ ] FAIL
**Blockers:** _____________________________________________________________

---

### Backend Lead
- [ ] Migration verification: 0/0/0 (perfect)
- [ ] BUG #7 verified (5 gates auto-created)
- [ ] API endpoints working
- [ ] No errors in logs

**Name:** ________________
**Date:** ________________
**Status:** [ ] PASS [ ] FAIL
**Blockers:** _____________________________________________________________

---

### Frontend Lead
- [ ] Frontend deployed successfully
- [ ] Teams features working
- [ ] Team filter working
- [ ] Dashboard team stats visible
- [ ] No JavaScript errors

**Name:** ________________
**Date:** ________________
**Status:** [ ] PASS [ ] FAIL
**Blockers:** _____________________________________________________________

---

### CTO Approval
- [ ] All smoke tests passed
- [ ] BUG #7 verified
- [ ] Migration verified
- [ ] Performance acceptable
- [ ] Ready for E2E tests

**Name:** ________________
**Date:** ________________
**Status:** [ ] APPROVED [ ] REJECTED
**Decision:** _____________________________________________________________

---

## 🎯 Next Steps

**After Staging Success:**
1. [ ] Run E2E tests against staging
2. [ ] Run integration tests
3. [ ] Fix any issues found
4. [ ] Schedule production deployment
5. [ ] Execute production deployment (same steps)

**Timeline:**
- Staging deployment: __________ minutes (budget: 75 min)
- E2E tests: __________ minutes
- Production deployment: __________ minutes (budget: 75 min)

---

## 📝 Issues Encountered

| Issue | Severity | Resolution | Time Lost |
|-------|----------|------------|-----------|
|       |          |            |           |
|       |          |            |           |
|       |          |            |           |

---

**Deployment Status:** [ ] IN PROGRESS [ ] COMPLETE [ ] FAILED [ ] ROLLED BACK
**Total Time:** __________ minutes
**Final Status:** _____________________________________________________________
