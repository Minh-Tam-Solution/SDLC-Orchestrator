# Submodule Crisis Recovery Plan
## SDLC-Enterprise-Framework Submodule Failure Scenarios

**Version:** 1.0.0  
**Date:** December 9, 2025  
**Owner:** DevOps Lead + CTO  
**Status:** ✅ MANDATORY - Week 1 Prerequisite

---

## EXECUTIVE SUMMARY

This document provides step-by-step recovery procedures for submodule failure scenarios. **All team members must be familiar with these procedures** before Week 2 execution begins.

**Critical Principle:** Framework submodule failures should **NEVER** block main repo development. Recovery procedures must be executable within **<10 minutes**.

---

## FAILURE SCENARIOS

### Scenario 1: Submodule Pointer Out of Sync

**Symptoms:**
- `git submodule status` shows `-` or `+` prefix
- CI/CD fails with "submodule not initialized"
- Local clone shows "fatal: reference is not a tree"

**Root Cause:**
- Framework repo updated, but main repo submodule pointer not updated
- Force push to Framework main branch
- Submodule commit hash doesn't exist in Framework repo

**Recovery Procedure:**

```bash
# Step 1: Check current state
cd SDLC-Orchestrator
git submodule status

# Step 2: Identify correct commit
cd SDLC-Enterprise-Framework
git fetch origin
git log --oneline origin/main | head -5

# Step 3: Update submodule pointer
cd ..
git submodule update --remote SDLC-Enterprise-Framework
git add SDLC-Enterprise-Framework
git commit -m "fix: Update Framework submodule pointer to latest"

# Step 4: Verify
git submodule status
# Should show: 00d728d... (no prefix)
```

**Prevention:**
- Always use `git submodule update --remote` after Framework changes
- Never force-push to Framework main branch
- CI/CD gate checks submodule sync status

**Time to Recovery:** <5 minutes

---

### Scenario 2: Framework Repository Unavailable

**Symptoms:**
- `git submodule update` fails with "fatal: repository not found"
- CI/CD fails with "could not read submodule"
- Network timeout accessing Framework repo

**Root Cause:**
- GitHub outage
- Framework repo deleted/renamed
- Network connectivity issues
- Authentication failure

**Recovery Procedure:**

#### Option A: Use Local Cache (If Available)

```bash
# Step 1: Check if local cache exists
cd SDLC-Orchestrator
ls -la .git/modules/SDLC-Enterprise-Framework/

# Step 2: Use cached version
git submodule update --init --reference .git/modules/SDLC-Enterprise-Framework

# Step 3: Continue development (read-only)
# Note: Cannot push to Framework, but main repo works
```

#### Option B: Temporary Fallback (Emergency Only)

```bash
# Step 1: Remove submodule temporarily
cd SDLC-Orchestrator
git submodule deinit SDLC-Enterprise-Framework
git rm SDLC-Enterprise-Framework

# Step 2: Add Framework as tracked directory (temporary)
# Copy from backup or local cache
cp -r /backup/SDLC-Enterprise-Framework ./SDLC-Enterprise-Framework
git add SDLC-Enterprise-Framework
git commit -m "emergency: Temporarily use tracked Framework directory"

# Step 3: Restore submodule after Framework repo available
# (See Scenario 3: Restore Submodule)
```

**Prevention:**
- Local backup of Framework repo (weekly)
- Mirror Framework repo to secondary location
- Monitor Framework repo availability (health check)

**Time to Recovery:** <10 minutes (Option A), <30 minutes (Option B)

---

### Scenario 3: Submodule Directory Corrupted

**Symptoms:**
- `cd SDLC-Enterprise-Framework` fails
- `git submodule status` shows error
- Files missing or corrupted in submodule directory

**Root Cause:**
- Disk corruption
- Accidental deletion
- File system errors

**Recovery Procedure:**

```bash
# Step 1: Remove corrupted submodule
cd SDLC-Orchestrator
rm -rf SDLC-Enterprise-Framework
rm -rf .git/modules/SDLC-Enterprise-Framework

# Step 2: Re-initialize submodule
git submodule init SDLC-Enterprise-Framework
git submodule update SDLC-Enterprise-Framework

# Step 3: Verify
cd SDLC-Enterprise-Framework
git status
# Should show: "On branch main" or "HEAD detached at 00d728d"

# Step 4: Checkout correct commit
git checkout main
git pull origin main
cd ..
git submodule update --remote SDLC-Enterprise-Framework
```

**Prevention:**
- Regular backups of `.git/modules/`
- Health check script (daily)
- Disk monitoring alerts

**Time to Recovery:** <10 minutes

---

## ROLLBACK PLAN

### Rollback to Tracked Directory (Last Resort)

**When to Use:**
- All recovery procedures failed
- Framework repo permanently unavailable
- Submodule causing critical blocker

**Procedure:**

```bash
# Step 1: Remove submodule
cd SDLC-Orchestrator
git submodule deinit -f SDLC-Enterprise-Framework
git rm -f SDLC-Enterprise-Framework
rm -rf .git/modules/SDLC-Enterprise-Framework

# Step 2: Add Framework as tracked directory
# Use backup or clone fresh
git clone https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework.git SDLC-Enterprise-Framework
rm -rf SDLC-Enterprise-Framework/.git
git add SDLC-Enterprise-Framework
git commit -m "rollback: Revert to tracked Framework directory"

# Step 3: Update .gitignore
# Remove: SDLC-Enterprise-Framework/
# Add comment: # Framework now tracked (rollback from submodule)

# Step 4: Update documentation
# Mark as temporary measure
# Plan submodule restoration after Framework repo available
```

**Time to Rollback:** <15 minutes

**Restoration Plan:**
- After Framework repo available, convert back to submodule
- Follow "Submodule Conversion" procedure (Week 1)

---

## MONITORING & ALERTS

### Health Check Script

**Location:** `scripts/check-submodule-health.sh`

```bash
#!/bin/bash
# Submodule Health Check Script

REPO_DIR="/home/nqh/shared/SDLC-Orchestrator"
SUBMODULE_DIR="$REPO_DIR/SDLC-Enterprise-Framework"

# Check 1: Submodule exists
if [ ! -d "$SUBMODULE_DIR" ]; then
    echo "ERROR: Submodule directory missing"
    exit 1
fi

# Check 2: Submodule initialized
cd "$REPO_DIR"
if ! git submodule status | grep -q "SDLC-Enterprise-Framework"; then
    echo "ERROR: Submodule not initialized"
    exit 1
fi

# Check 3: Framework repo accessible
cd "$SUBMODULE_DIR"
if ! git fetch origin --dry-run > /dev/null 2>&1; then
    echo "WARNING: Framework repo not accessible"
    exit 2
fi

# Check 4: Submodule pointer valid
cd "$REPO_DIR"
STATUS=$(git submodule status | grep SDLC-Enterprise-Framework)
if echo "$STATUS" | grep -q "^[+-]"; then
    echo "WARNING: Submodule pointer out of sync"
    exit 2
fi

echo "OK: Submodule health check passed"
exit 0
```

**Cron Schedule:** Daily at 2 AM

**Alert Thresholds:**
- ERROR: Page DevOps Lead immediately
- WARNING: Log to monitoring system, notify on-call

---

## ESCALATION PATH

| Level | Issue | Contact | SLA |
|-------|-------|---------|-----|
| **L1** | Submodule out of sync | DevOps Lead | <1 hour |
| **L2** | Framework repo unavailable | CTO + DevOps Lead | <4 hours |
| **L3** | Submodule corruption | CTO + DevOps Lead | <8 hours |
| **L4** | Rollback required | CTO + CEO | <24 hours |

---

## TESTING PROCEDURES

### Monthly Disaster Recovery Drill

**Schedule:** First Monday of each month

**Procedure:**
1. Simulate Scenario 1 (out of sync)
2. Execute recovery procedure
3. Measure time to recovery
4. Document lessons learned

**Success Criteria:**
- Recovery time <10 minutes
- Zero data loss
- All team members trained

---

## RELATED DOCUMENTS

- [Submodule Workflow Guide](../../04-build/03-Setup-Guides/GIT-SUBMODULE-WORKFLOW.md)
- [Framework-First Principle](../../00-foundation/01-Vision/Product-Vision.md)
- [Incident Response Runbook](../01-Runbooks/INCIDENT-RESPONSE-RUNBOOK.md)

---

**Last Updated:** December 9, 2025  
**Next Review:** January 9, 2026  
**Owner:** DevOps Lead + CTO


