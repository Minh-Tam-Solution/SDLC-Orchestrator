# Git Submodule Team Training Program
## SDLC-Enterprise-Framework Submodule Operations

**Document Version:** 1.0.0
**Status:** ACTIVE - PRODUCTION
**Authority:** CTO MANDATED
**Effective Date:** December 9, 2025
**Training Duration:** 90 minutes
**Required Attendance:** 100% of engineering team (8.5 FTE)

---

## 🎯 TRAINING OBJECTIVES

By the end of this workshop, all team members will be able to:

1. ✅ Clone SDLC Orchestrator repository with Framework submodule (100% success rate)
2. ✅ Update Framework submodule to latest version (<2 min execution)
3. ✅ Work on Framework changes and push to remote (zero conflicts)
4. ✅ Diagnose and recover from 3 common submodule failure scenarios
5. ✅ Explain Framework-First Principle and apply it to feature development

**Non-Negotiable Requirement:** All team members MUST score 4/5+ on certification quiz.

---

## 📚 TRAINING AGENDA

### **Session 1: Submodule Basics (30 minutes)**

#### **1.1 What is Git Submodule?**

**Definition:**
Git submodule is a repository embedded inside another repository. It allows us to:
- Keep SDLC Framework (methodology) separate from SDLC Orchestrator (tool)
- Track specific versions of Framework in main repo
- Allow parallel development of Framework and Orchestrator

**Visual Diagram:**
```
SDLC-Orchestrator (Main Repo)
├── backend/
├── frontend/
├── docs/
└── SDLC-Enterprise-Framework/ ← SUBMODULE (separate git repo)
    ├── 00-Why/
    ├── 01-What/
    ├── 02-How/
    └── ... (10 SDLC 5.1.3 stages)
```

**Key Metadata Files:**
```yaml
.gitmodules:
  Purpose: Defines submodule configuration
  Content:
    [submodule "SDLC-Enterprise-Framework"]
      path = SDLC-Enterprise-Framework
      url = https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework

.git/modules/SDLC-Enterprise-Framework/:
  Purpose: Submodule's git directory (hidden)
  Contains: Submodule's commit history, branches, remotes
```

#### **1.2 Why Submodule for Framework?**

**Framework-First Principle:**
- **Framework** = Methodology layer (tools-agnostic, universal)
- **Orchestrator** = Automation layer (specific implementation)
- Framework survives even if Orchestrator is replaced

**Example:**
```yaml
Feature Request: "Add SASE artifact generator"

❌ WRONG Approach:
  - Add SASE generation API to Orchestrator backend
  - Hard-code templates in Python code
  - Framework has no documentation about SASE

✅ CORRECT Approach (Framework-First):
  - Add SASE methodology + templates to Framework (Track 1)
  - Document BRS, MRP, VCR artifacts in Framework
  - Then build Orchestrator automation (Track 2, conditional)
  - Result: Teams can use SASE manually even without Orchestrator
```

---

### **Session 2: Daily Operations (30 minutes)**

#### **2.1 Cloning SDLC Orchestrator**

**Scenario:** New developer joins team, needs to set up local environment.

**Step-by-Step:**
```bash
# Step 1: Clone main repo WITH submodule
git clone --recurse-submodules https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
cd SDLC-Orchestrator

# Step 2: Verify submodule initialized
git submodule status
# Expected output:
# abc1234... SDLC-Enterprise-Framework (heads/main)

# Step 3: Verify Framework files present
ls -la SDLC-Enterprise-Framework/
# Should show 10+ directories (00-Why, 01-What, etc.)

# Step 4: Verify Framework remote
cd SDLC-Enterprise-Framework
git remote -v
# Should show:
# origin  https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework (fetch)
# origin  https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework (push)
```

**Common Mistake:**
```bash
# ❌ WRONG - Cloning without --recurse-submodules
git clone https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
cd SDLC-Orchestrator
ls -la SDLC-Enterprise-Framework/
# Result: Empty directory! Framework not initialized.

# ✅ FIX - Initialize submodule manually
git submodule init
git submodule update
```

#### **2.2 Pulling Latest Changes**

**Scenario:** Another developer pushed Framework changes, you need to sync.

**Step-by-Step:**
```bash
# Step 1: Pull main repo changes
git pull origin main

# Step 2: Update submodule to match main repo pointer
git submodule update --init --recursive

# Step 3: Verify Framework files updated
cd SDLC-Enterprise-Framework
git log -1
# Should show latest Framework commit
```

**Automation Tip (Recommended):**
```bash
# Create post-merge hook to auto-update submodules
cat > .git/hooks/post-merge << 'EOF'
#!/bin/bash
git submodule update --init --recursive
EOF

chmod +x .git/hooks/post-merge
```

#### **2.3 Working on Framework Changes**

**Scenario:** SE 3.0 SASE Integration - you need to add BRS template to Framework.

**Step-by-Step:**
```bash
# Step 1: Navigate to Framework submodule
cd SDLC-Enterprise-Framework

# Step 2: Work on main branch (per CTO guidance)
git checkout main
git pull origin main

# Step 3: Create new SASE template
mkdir -p 03-Templates-Tools/SASE-Artifacts
cat > 03-Templates-Tools/SASE-Artifacts/BRS-Template.md << 'EOF'
# Business Requirements Specification (BRS)
## SASE Artifact Template

**Version:** 1.0.0
**Stage:** Stage 01 (WHAT - Planning & Analysis)
...
EOF

# Step 4: Commit to Framework repo
git add .
git commit -m "feat(SDLC 5.1.0): Add BRS template for SASE artifacts"
git push origin main

# Step 5: Return to main repo and update submodule pointer
cd ..
git submodule update --remote SDLC-Enterprise-Framework
git add SDLC-Enterprise-Framework
git commit -m "chore: Update Framework submodule - BRS template added"
git push origin main
```

**Key Principle:** Always commit to Framework FIRST, then update main repo pointer.

---

### **Session 3: Crisis Recovery (30 minutes)**

#### **3.1 Scenario 1: Submodule Pointer Out of Sync**

**When:** After `git pull`, Framework files missing or outdated.

**Recovery:**
```bash
# Symptom
ls -la SDLC-Enterprise-Framework/
# Shows old files or empty directory

# Diagnosis
git submodule status
# Shows "-" prefix = not initialized or wrong commit

# Recovery
git submodule update --init --recursive

# Verification
cd SDLC-Enterprise-Framework
git log -1
# Should match commit hash in main repo's .gitmodules
```

**Time to Recover:** <2 minutes

#### **3.2 Scenario 2: Framework Repository Unavailable**

**When:** GitHub outage, repo deleted, network failure.

**Recovery Option A (Wait for GitHub):**
```bash
# Step 1: Check GitHub status
curl https://status.github.com

# Step 2: Wait for recovery (typical <30 min)

# Step 3: Retry submodule init
git submodule update --init --recursive
```

**Recovery Option B (Emergency Rollback to Tracked Directory):**
```bash
# ONLY if Framework repo permanently lost + CTO approval

# Step 1: Checkout commit before submodule conversion
git checkout 769e7fd^

# Step 2: Extract Framework files
cp -r SDLC-Enterprise-Framework /tmp/framework-backup

# Step 3: Return to main
git checkout main

# Step 4: Remove submodule
git submodule deinit -f SDLC-Enterprise-Framework
git rm -f SDLC-Enterprise-Framework
rm -rf .git/modules/SDLC-Enterprise-Framework

# Step 5: Restore as tracked directory
cp -r /tmp/framework-backup SDLC-Enterprise-Framework
git add SDLC-Enterprise-Framework

# Step 6: Commit with CTO approval
git commit -m "emergency: Rollback Framework to tracked directory

Framework repo unavailable. Reverting to pre-submodule state.

CTO Approval Required: YES"

git push origin main
```

**Time to Recover:** 5-10 minutes
**CTO Approval:** MANDATORY

#### **3.3 Scenario 3: Submodule Commit Missing**

**When:** Framework repo force-pushed, commit deleted.

**Recovery:**
```bash
# Symptom
git submodule update
# Error: fatal: reference is not a tree: <commit-hash>

# Diagnosis
cd SDLC-Enterprise-Framework
git fetch --all
git log --oneline -20
# Commit hash from main repo not found

# Recovery
git checkout <nearest-available-commit>
cd ..
git add SDLC-Enterprise-Framework
git commit -m "fix: Update Framework submodule to nearest available commit

Previous commit <old-hash> not found in Framework repo.
Updated to <new-hash>.

Investigation required: Why was commit lost?"

git push origin main
```

**Time to Recover:** 3-5 minutes
**Post-Recovery Action:** Mandatory investigation

---

## 📝 CERTIFICATION QUIZ

**Passing Score:** 4/5 correct answers
**Time Limit:** 10 minutes
**Retakes:** Unlimited (must pass before end of Week 1)

### **Question 1: Cloning with Submodule**

Your manager asks you to clone SDLC Orchestrator. Which command is correct?

A) `git clone https://github.com/Minh-Tam-Solution/SDLC-Orchestrator`

B) `git clone --recurse-submodules https://github.com/Minh-Tam-Solution/SDLC-Orchestrator`

C) `git clone https://github.com/Minh-Tam-Solution/SDLC-Orchestrator && git submodule init`

D) Both B and C are correct

**Correct Answer:** D

**Explanation:**
- Option B clones with submodule initialization in one command (preferred)
- Option C clones first, then initializes submodule manually (also works)
- Option A is WRONG - submodule won't be initialized, Framework directory empty

---

### **Question 2: Framework-First Principle**

PM asks you to add "AI-powered BRD generator" feature. What is the CORRECT approach?

A) Add API endpoint to Orchestrator backend, hard-code BRD template in Python

B) Add BRD template to Framework (SDLC-Enterprise-Framework), then build Orchestrator automation

C) Build Orchestrator feature first, migrate to Framework later if needed

D) Framework-First doesn't apply to AI features, go ahead with Orchestrator

**Correct Answer:** B

**Explanation:**
- Framework-First Principle: Methodology BEFORE automation
- BRD template is methodology (belongs in Framework)
- Orchestrator automation is optional (Track 2, conditional on Track 1)
- Result: Teams can use BRD manually even without Orchestrator AI

---

### **Question 3: Updating Framework After Pull**

After `git pull origin main`, you notice Framework files are outdated. What should you do?

A) Delete SDLC-Enterprise-Framework/ and re-clone main repo

B) Run `git submodule update --init --recursive`

C) Run `cd SDLC-Enterprise-Framework && git pull origin main`

D) Ignore it, Framework updates are optional

**Correct Answer:** B

**Explanation:**
- `git pull` updates main repo, not submodule
- `git submodule update --init --recursive` syncs submodule to commit hash tracked in main repo
- Option C is WRONG - pulls latest Framework, not the commit hash tracked in main repo (can cause version mismatch)
- Option A is inefficient and unnecessary

---

### **Question 4: Working on Framework Changes**

You need to add SASE MRP template to Framework. What is the correct workflow?

A) Edit in `SDLC-Orchestrator/SDLC-Enterprise-Framework/`, commit to main repo

B) Edit in `SDLC-Orchestrator/SDLC-Enterprise-Framework/`, commit to Framework repo, then update main repo pointer

C) Clone Framework repo separately, commit there, then update main repo submodule

D) Both B and C are correct

**Correct Answer:** D

**Explanation:**
- Framework is a separate git repository
- Changes must be committed to Framework repo (NOT main repo)
- Option B: Work in submodule directory, commit to Framework, update pointer (recommended)
- Option C: Work in separate clone, then update submodule pointer (also valid)
- Option A is WRONG - commits to main repo, not Framework repo

---

### **Question 5: Crisis Recovery**

After `git pull`, you see error: `fatal: reference is not a tree: abc1234`. What is the problem?

A) Framework repository is unavailable (GitHub outage)

B) Submodule pointer out of sync (run `git submodule update`)

C) Framework commit abc1234 doesn't exist (force-pushed or deleted)

D) Your local Framework has uncommitted changes

**Correct Answer:** C

**Explanation:**
- Error "reference is not a tree" = commit hash doesn't exist in repo
- Common cause: Framework repo force-pushed, commit deleted
- Recovery: Checkout nearest available commit, update main repo pointer
- Option A would show "unable to access" error
- Option B would show "-" prefix in `git submodule status`
- Option D would show "M" prefix in `git submodule status`

---

## 📊 TRAINING METRICS

### **Attendance Tracking**

| Name | Role | Attended | Quiz Score | Status |
|------|------|----------|------------|--------|
| [Name 1] | Backend Lead | ✅ Yes | 5/5 | ✅ Certified |
| [Name 2] | Frontend Lead | ✅ Yes | 4/5 | ✅ Certified |
| [Name 3] | Full-Stack Dev | ✅ Yes | 5/5 | ✅ Certified |
| [Name 4] | Full-Stack Dev | ✅ Yes | 4/5 | ✅ Certified |
| [Name 5] | QA Lead | ✅ Yes | 5/5 | ✅ Certified |
| [Name 6] | DevOps Lead | ✅ Yes | 5/5 | ✅ Certified |
| [Name 7] | Junior Dev | ✅ Yes | 3/5 | ⏳ Retake Required |
| [Name 8] | Junior Dev | ✅ Yes | 4/5 | ✅ Certified |
| [Name 9] | PM/PO | ✅ Yes | 5/5 | ✅ Certified |

**Overall Stats:**
- Attendance: 9/9 (100%)
- Pass Rate: 8/9 (89% - 1 retake pending)
- Average Score: 4.56/5
- Training Date: December 9, 2025
- Training Duration: 90 minutes
- Trainer: CTO + DevOps Lead

### **Certification Requirements**

**To be certified, team members must:**
1. ✅ Attend full 90-minute workshop (100% attendance)
2. ✅ Score 4/5+ on certification quiz (80%+ accuracy)
3. ✅ Complete hands-on lab (clone, pull, update, commit)
4. ✅ Demonstrate crisis recovery (1/3 scenarios)

**Retake Policy:**
- Unlimited retakes allowed
- Must pass before end of Week 1 (December 13, 2025)
- 1-on-1 coaching available for those who score <4/5

---

## 🔧 HANDS-ON LAB

### **Lab 1: Clone and Verify (5 minutes)**

**Objective:** Clone SDLC Orchestrator with Framework submodule.

**Tasks:**
```bash
# 1. Clone with submodule
git clone --recurse-submodules https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
cd SDLC-Orchestrator

# 2. Verify submodule status
git submodule status
# Expected: abc1234... SDLC-Enterprise-Framework (heads/main)

# 3. Count Framework directories
ls -1 SDLC-Enterprise-Framework/ | wc -l
# Expected: 10+ directories

# 4. Verify Framework remote
cd SDLC-Enterprise-Framework && git remote -v
# Expected: github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework
```

**Success Criteria:** All 4 commands execute without errors.

---

### **Lab 2: Update Framework (5 minutes)**

**Objective:** Pull latest Framework changes.

**Tasks:**
```bash
# 1. Pull main repo
git pull origin main

# 2. Update submodule
git submodule update --init --recursive

# 3. Verify Framework updated
cd SDLC-Enterprise-Framework
git log -1 --oneline
# Should show latest Framework commit

# 4. Return to main repo
cd ..
```

**Success Criteria:** Framework files match latest Framework repo commit.

---

### **Lab 3: Add Framework Content (10 minutes)**

**Objective:** Add new file to Framework and update main repo.

**Tasks:**
```bash
# 1. Navigate to Framework
cd SDLC-Enterprise-Framework

# 2. Create test file
echo "# Test Document" > TEST.md
git add TEST.md
git commit -m "test: Add test document for training lab"

# 3. Push to Framework repo
git push origin main

# 4. Update main repo pointer
cd ..
git submodule update --remote SDLC-Enterprise-Framework
git add SDLC-Enterprise-Framework
git commit -m "chore: Update Framework - training lab test"
git push origin main

# 5. Cleanup (delete test file)
cd SDLC-Enterprise-Framework
git rm TEST.md
git commit -m "chore: Remove training lab test file"
git push origin main
cd ..
git submodule update --remote SDLC-Enterprise-Framework
git add SDLC-Enterprise-Framework
git commit -m "chore: Cleanup training lab test"
git push origin main
```

**Success Criteria:** Test file appears in Framework repo, then removed cleanly.

---

## 📚 REFERENCE MATERIALS

### **Quick Reference Card**

```yaml
Common Commands:

Clone with submodule:
  git clone --recurse-submodules <repo-url>

Initialize submodule (if cloned without --recurse-submodules):
  git submodule init
  git submodule update

Update submodule after pull:
  git submodule update --init --recursive

Check submodule status:
  git submodule status

Work on Framework:
  cd SDLC-Enterprise-Framework
  git checkout main
  git pull origin main
  # ... make changes
  git commit -m "..."
  git push origin main
  cd ..
  git submodule update --remote SDLC-Enterprise-Framework
  git add SDLC-Enterprise-Framework
  git commit -m "chore: Update Framework submodule"
  git push origin main

Crisis Recovery:
  See: docs/09-govern/05-Operations/SUBMODULE-CRISIS-RECOVERY-PLAN.md
```

### **Additional Resources**

- **Git Submodule Documentation:** https://git-scm.com/book/en/v2/Git-Tools-Submodules
- **Crisis Recovery Plan:** [SUBMODULE-CRISIS-RECOVERY-PLAN.md](SUBMODULE-CRISIS-RECOVERY-PLAN.md)
- **Framework-First Principle:** [CLAUDE.md](../../CLAUDE.md) (lines 101-193)
- **SE 3.0 SASE Integration:** [2025-12-08-SE-3.0-SASE-INTEGRATION-APPROVED.md](../00-Executive-Summaries/2025-12-08-SE-3.0-SASE-INTEGRATION-APPROVED.md)

---

## ✅ POST-TRAINING CHECKLIST

**Team Lead Responsibilities:**
- [ ] Schedule 90-minute training workshop
- [ ] Record attendance (100% required)
- [ ] Administer certification quiz
- [ ] Grade quiz (4/5+ passing score)
- [ ] Supervise hands-on labs
- [ ] Issue certifications
- [ ] Schedule retakes for those who scored <4/5
- [ ] Submit training report to CTO

**Individual Responsibilities:**
- [ ] Attend full workshop
- [ ] Complete certification quiz (4/5+ required)
- [ ] Finish all 3 hands-on labs
- [ ] Demonstrate crisis recovery (1 scenario)
- [ ] Bookmark reference materials
- [ ] Report any issues to Team Lead

---

**Document Owner:** CTO + DevOps Lead
**Last Updated:** December 9, 2025
**Next Review:** After Week 1 (December 13, 2025)

---

**CTO Notes:**
> "Training is non-negotiable. Submodule failures cost us hours. Invest 90 minutes now, save weeks later."
> "4/5 quiz score = you understand enough to not break production. Retake until you pass."
