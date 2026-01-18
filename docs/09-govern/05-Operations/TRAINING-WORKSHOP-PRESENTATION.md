# Training Workshop Presentation
## SDLC-Enterprise-Framework Submodule Operations

**Duration:** 90 minutes
**Format:** Instructor-led with hands-on labs
**Audience:** All 9 developers (100% attendance required)
**Delivery:** Dec 10-11, 2025

---

## 🎯 SLIDE 1: WELCOME & OVERVIEW (2 min)

**Title Slide:**
```
SDLC-Enterprise-Framework Submodule Training
Git Submodule Operations Workshop

Duration: 90 minutes
Certification: 5-question quiz (4/5 passing score)
Hands-On: 3 practical labs

CTO Mandated - 100% Attendance Required
```

**Instructor Welcome:**
> "Good morning/afternoon team! Welcome to the SDLC-Enterprise-Framework Submodule Training.
>
> Today we'll learn how to work with git submodules - a critical skill for SE 3.0 Track 1 execution.
>
> This is a **hands-on workshop** - you'll clone, update, and commit to the Framework submodule by the end of today.
>
> **Important:** Week 2 work is BLOCKED until 100% of team is certified (4/5 quiz score). So let's make this count!"

---

## 📚 SESSION 1: SUBMODULE BASICS (30 min)

### SLIDE 2: What is a Git Submodule? (5 min)

**Visual Diagram:**
```
┌─────────────────────────────────────────────────┐
│ SDLC-Orchestrator (Main Repo)                  │
│ https://github.com/.../SDLC-Orchestrator       │
│                                                  │
│ ├── backend/                                    │
│ ├── frontend/                                   │
│ ├── docs/                                       │
│ └── SDLC-Enterprise-Framework/ ← SUBMODULE     │
│     │                                           │
│     └── Separate Git Repo:                     │
│         https://github.com/.../               │
│         SDLC-Enterprise-Framework              │
│                                                  │
│         ├── 00-Why/                             │
│         ├── 01-What/                            │
│         ├── 02-How/                             │
│         └── ... (10 SDLC 5.1.3 stages)         │
└─────────────────────────────────────────────────┘
```

**Key Points:**
- Git submodule = **repository inside repository**
- Framework has **own git history** (separate from main repo)
- Main repo tracks **specific commit** of Framework
- Changes to Framework require **two commits** (Framework + main repo)

**Analogy:**
> "Think of it like a book with an appendix. The appendix (Framework) is written separately and can be updated independently, but the main book (Orchestrator) references a specific version of it."

**Show in Terminal:**
```bash
# Show .gitmodules file
cat .gitmodules

# Show submodule status
git submodule status

# Show Framework has separate git
ls -la SDLC-Enterprise-Framework/.git
```

---

### SLIDE 3: Why Submodule for Framework? (5 min)

**Framework-First Principle Recap:**

```
┌───────────────────────────────────────────────┐
│ LAYER 1: Framework (Methodology)             │
│ - Tools-agnostic templates                   │
│ - SDLC 5.1.3 methodology                     │
│ - Works with ANY tool (Claude, GPT-4, etc)   │
│ - Survives even if Orchestrator replaced     │
└───────────────────────────────────────────────┘
                    ↓
┌───────────────────────────────────────────────┐
│ LAYER 2: Orchestrator (Automation)           │
│ - Tool-specific implementation               │
│ - Reads templates from Framework submodule   │
│ - Automates Framework methodology            │
└───────────────────────────────────────────────┘
```

**Why This Matters:**

**Before (Tracked Directory):**
❌ Framework changes pollute main repo commit history
❌ Cannot version Framework independently
❌ Hard to share Framework across projects (NQH, BFlow, MTEP)

**After (Submodule):**
✅ Clean separation (Framework commits isolated)
✅ Independent versioning (Framework v5.1.0, Orchestrator v1.0.0)
✅ Easy to share Framework across 5+ NQH projects
✅ Framework survives even if Orchestrator replaced

**Real Example:**
> "SE 3.0 SASE templates will be added to Framework **first** (Track 1), then Orchestrator automation **later** (Track 2, conditional). This way, teams can use SASE manually even without Orchestrator."

---

### SLIDE 4: Framework-First in Practice (5 min)

**Example Workflow:**

**❌ WRONG Approach:**
```python
# backend/app/api/routes/sase.py
@router.post("/sase/briefing-script")
def generate_brs(request):
    # VIOLATION: Hard-coded template in Orchestrator
    template = """
    # BriefingScript (BRS)
    {problem}
    {solution}
    """
    return template.format(**request.dict())
```

**✅ CORRECT Approach (Framework-First):**

**Step 1: Add to Framework FIRST**
```bash
# In Framework repo
cat > 03-Templates-Tools/SASE-Artifacts/BRS-Template.md << 'EOF'
# BriefingScript (BRS)
## Problem Context
{problem}

## Solution Requirements
{solution}
EOF

git add .
git commit -m "feat: Add BRS template"
git push origin main
```

**Step 2: THEN automate in Orchestrator**
```python
# backend/app/api/routes/sase.py
from pathlib import Path

@router.post("/sase/briefing-script")
def generate_brs(request):
    # ✅ Read from Framework submodule
    template_path = Path("SDLC-Enterprise-Framework/03-Templates-Tools/SASE-Artifacts/BRS-Template.md")
    with open(template_path, "r") as f:
        template = f.read()
    return template.format(**request.dict())
```

**Key Takeaway:**
> "Methodology FIRST (Framework), Automation SECOND (Orchestrator). This is non-negotiable."

---

### SLIDE 5: Submodule Metadata Files (5 min)

**Two Key Files:**

**File 1: .gitmodules (Main Repo)**
```ini
[submodule "SDLC-Enterprise-Framework"]
    path = SDLC-Enterprise-Framework
    url = https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework
```

**Purpose:**
- Tells git where the submodule repo is located
- Defines submodule path in main repo
- Committed to main repo (tracked in version control)

**File 2: .git/modules/SDLC-Enterprise-Framework/ (Hidden)**
```
SDLC-Orchestrator/
└── .git/
    └── modules/
        └── SDLC-Enterprise-Framework/  ← Submodule's git directory
            ├── objects/
            ├── refs/
            └── config
```

**Purpose:**
- Contains submodule's full git history
- Separate from main repo's .git directory
- Allows submodule to have independent branches, commits

**Show in Terminal:**
```bash
# Show .gitmodules
cat .gitmodules

# Show submodule git directory exists
ls -la .git/modules/SDLC-Enterprise-Framework/
```

---

### SLIDE 6: Common Submodule States (10 min)

**State 1: Clean (✅ Good)**
```bash
$ git submodule status
 abc1234567890 SDLC-Enterprise-Framework (heads/main)
```
- First character: **space** = clean, no changes
- Commit hash matches main repo's expectation
- Framework on main branch

**State 2: Modified (-M prefix, ⚠️ Warning)**
```bash
$ git submodule status
+abc1234567890 SDLC-Enterprise-Framework (heads/main)
```
- **Plus sign** = Framework has uncommitted changes
- Or Framework checked out to different commit than main repo expects
- **Action:** Commit changes or run `git submodule update`

**State 3: Uninitialized (-prefix, ❌ Error)**
```bash
$ git submodule status
-abc1234567890 SDLC-Enterprise-Framework
```
- **Minus sign** = Submodule not initialized
- Framework directory empty or missing
- **Fix:** Run `git submodule init && git submodule update`

**Demo in Terminal:**
```bash
# Show clean state
git submodule status

# Create change to show modified state
cd SDLC-Enterprise-Framework
touch TEST.md
cd ..
git submodule status  # Shows "+"

# Clean up
cd SDLC-Enterprise-Framework
rm TEST.md
cd ..
git submodule status  # Back to clean
```

**Q&A Time (2 min):**
> "Any questions about submodule basics before we move to daily operations?"

---

## 🛠️ SESSION 2: DAILY OPERATIONS (30 min)

### SLIDE 7: Cloning with Submodule (5 min)

**Scenario:** New developer joins team, needs to clone SDLC Orchestrator.

**Method A: Single Command (Recommended)**
```bash
git clone --recurse-submodules https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
cd SDLC-Orchestrator
```

**Method B: Two Commands (Alternative)**
```bash
git clone https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
cd SDLC-Orchestrator
git submodule init
git submodule update
```

**Common Mistake:**
```bash
# ❌ WRONG - Cloning without --recurse-submodules
git clone https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
cd SDLC-Orchestrator
ls -la SDLC-Enterprise-Framework/
# Result: Empty directory! Framework not initialized.
```

**Verification Steps:**
```bash
# 1. Check submodule initialized
git submodule status
# Should show: abc1234... SDLC-Enterprise-Framework (heads/main)

# 2. Check Framework files present
ls -la SDLC-Enterprise-Framework/
# Should show 10+ directories

# 3. Check Framework remote
cd SDLC-Enterprise-Framework
git remote -v
# Should show Framework repo URL, NOT Orchestrator URL
```

**Demo Time:** Live clone demo (5 min)

---

### SLIDE 8: Updating Framework After Pull (5 min)

**Scenario:** Another developer pushed Framework changes, you need to sync.

**Workflow:**
```bash
# Step 1: Pull main repo changes
cd /path/to/SDLC-Orchestrator
git pull origin main

# Step 2: Update submodule to match main repo pointer
git submodule update --init --recursive

# Step 3: Verify Framework updated
cd SDLC-Enterprise-Framework
git log -1 --oneline
# Should show latest Framework commit

cd ..
```

**Why Two Steps?**
> "`git pull` updates main repo only. Submodule still points to old commit until you run `git submodule update`."

**Automation Tip:**
```bash
# Create post-merge hook to auto-update submodules
cat > .git/hooks/post-merge << 'EOF'
#!/bin/bash
git submodule update --init --recursive
EOF

chmod +x .git/hooks/post-merge
```

**Common Mistake:**
```bash
# ❌ WRONG - Pulling Framework directly
cd SDLC-Enterprise-Framework
git pull origin main  # Pulls LATEST, not the commit main repo expects

# ✅ CORRECT - Update submodule via main repo
cd ..
git submodule update --init --recursive  # Syncs to commit main repo expects
```

---

### SLIDE 9: Working on Framework Changes (10 min)

**Scenario:** SE 3.0 SASE Integration - you need to add BRS template to Framework.

**Step-by-Step Workflow:**

**Step 1: Navigate to Framework submodule**
```bash
cd SDLC-Enterprise-Framework
```

**Step 2: Ensure on main branch**
```bash
git checkout main
git pull origin main
```

**Step 3: Create SASE template**
```bash
mkdir -p 03-Templates-Tools/SASE-Artifacts

cat > 03-Templates-Tools/SASE-Artifacts/BRS-Template.md << 'EOF'
# BriefingScript (BRS)
## SASE Artifact Template

**Version:** 1.0.0
**Stage:** Stage 01 (WHAT - Planning & Analysis)

---

## 1. Problem Context (WHY)
{problem_description}

## 2. Solution Requirements (WHAT)
{solution_requirements}

## 3. Expected Deliverables
{deliverables}
EOF
```

**Step 4: Commit to Framework repo**
```bash
git add .
git commit -m "feat(SDLC 5.1.0): Add BRS template for SASE artifacts"
git push origin main
```

**Step 5: Return to main repo and update submodule pointer**
```bash
cd ..
git submodule update --remote SDLC-Enterprise-Framework
git add SDLC-Enterprise-Framework
git commit -m "chore: Update Framework submodule - BRS template added"
git push origin main
```

**Key Principle:**
> "Always commit to Framework FIRST, then update main repo pointer. Never skip the second step!"

**Visual Flow:**
```
Framework Repo Commits         Main Repo Commits
─────────────────────         ─────────────────
commit abc1234
"Add BRS template"
      ↓
                             commit def5678
                             "Update Framework submodule"
                             (points to abc1234)
```

---

### SLIDE 10: Framework-Only Work (5 min)

**Scenario:** PM/PO needs to update Framework docs (no Orchestrator code change).

**Quick Workflow:**
```bash
# Work directly in Framework submodule
cd SDLC-Enterprise-Framework

# Make changes
nano 03-Templates-Tools/SASE-Artifacts/BRS-Template.md

# Commit to Framework repo
git add .
git commit -m "docs: Improve BRS template with examples"
git push origin main

# Update main repo pointer
cd ..
git submodule update --remote SDLC-Enterprise-Framework
git add SDLC-Enterprise-Framework
git commit -m "chore: Update Framework submodule - BRS improvements"
git push origin main
```

**When to Use:**
- Updating Framework documentation
- Adding new Framework templates
- Fixing Framework typos

**When NOT to Use:**
- Changing Orchestrator backend code (work in main repo)
- Updating Orchestrator frontend (work in main repo)

---

### SLIDE 11: Hands-On Lab 1 - Clone and Verify (5 min)

**🔬 LAB INSTRUCTIONS:**

**Objective:** Clone SDLC Orchestrator with Framework submodule

**Tasks:**
1. Clone repo with `--recurse-submodules` flag
2. Verify submodule status
3. Count Framework directories (should be 10+)
4. Verify Framework remote URL

**Commands:**
```bash
# Clone (choose Method A or B from Slide 7)
git clone --recurse-submodules https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
cd SDLC-Orchestrator

# Verify
git submodule status
ls -1 SDLC-Enterprise-Framework/ | wc -l
cd SDLC-Enterprise-Framework && git remote -v
```

**Success Criteria:**
- [ ] Submodule status shows no errors
- [ ] Framework has 10+ directories
- [ ] Framework remote is github.com/.../SDLC-Enterprise-Framework

**Time Limit:** 5 minutes

**Instructor Support:** Circulate to help anyone stuck

---

## 🚨 SESSION 3: CRISIS RECOVERY (15 min)

### SLIDE 12: Crisis Scenario 1 - Pointer Out of Sync (5 min)

**Symptom:**
```bash
$ git pull origin main
$ ls SDLC-Enterprise-Framework/
# Directory empty or showing old files!
```

**Diagnosis:**
```bash
$ git submodule status
-abc1234567890 SDLC-Enterprise-Framework
# Minus sign = not initialized
```

**Recovery:**
```bash
git submodule update --init --recursive
```

**Verification:**
```bash
ls -la SDLC-Enterprise-Framework/
# Should show 10+ directories

git submodule status
# Should show clean state (no "-" prefix)
```

**Time to Recover:** <2 minutes

**Demo:** Live recovery simulation

---

### SLIDE 13: Crisis Scenario 2 - Repo Unavailable (5 min)

**Symptom:**
```bash
$ git clone --recurse-submodules https://github.com/.../SDLC-Orchestrator
# Error: fatal: unable to access SDLC-Enterprise-Framework
# (GitHub outage, repo deleted, network failure)
```

**Recovery Option A: Wait for GitHub**
```bash
# Check GitHub status
curl https://status.github.com

# Wait for recovery (typical <30 min)

# Retry clone
git clone --recurse-submodules https://github.com/.../SDLC-Orchestrator
```

**Recovery Option B: Emergency Rollback (REQUIRES CTO APPROVAL)**
```bash
# ONLY if Framework repo permanently lost

# Step 1: Checkout commit before submodule conversion
git checkout 769e7fd^

# Step 2: Extract Framework files
cp -r SDLC-Enterprise-Framework /tmp/framework-backup

# Step 3: Rollback to tracked directory
# (See Crisis Recovery Plan for full procedure)
```

**Time to Recover:** 5-10 minutes

**CTO Approval:** MANDATORY for Option B

---

### SLIDE 14: Crisis Scenario 3 - Commit Missing (5 min)

**Symptom:**
```bash
$ git submodule update
fatal: reference is not a tree: abc1234567890
# Framework commit doesn't exist in repo (force-pushed or deleted)
```

**Recovery:**
```bash
# Step 1: Go to Framework repo
cd SDLC-Enterprise-Framework

# Step 2: Fetch all refs
git fetch --all

# Step 3: Find nearest available commit
git log --oneline -20

# Step 4: Checkout nearest commit
git checkout <nearest-commit-hash>

# Step 5: Update main repo pointer
cd ..
git add SDLC-Enterprise-Framework
git commit -m "fix: Update Framework submodule to nearest available commit"
git push origin main
```

**Time to Recover:** 3-5 minutes

**Post-Recovery:** MANDATORY investigation (why was commit lost?)

---

## 🎓 CERTIFICATION QUIZ (15 min)

### SLIDE 15: Quiz Instructions (2 min)

**Quiz Format:**
- 5 multiple choice questions
- 15 minutes time limit
- 4/5 passing score (80% accuracy)
- Unlimited retakes (must pass by Dec 11 EOD)

**Quiz Rules:**
- Closed book (no looking at notes)
- Individual work (no collaboration)
- Mark answers on quiz form
- Submit to instructor when done

**Passing Criteria:**
- Score 4/5+ → ✅ Certified for Week 2 work
- Score <4/5 → ⏳ Retake required (same day or Dec 11)

**Ready? Let's begin!**

---

### SLIDE 16-20: Quiz Questions (Display one at a time)

**(See TRAINING-WORKSHOP-QUIZ-ANSWER-KEY.md for detailed questions)**

**Question 1:** Cloning command
**Question 2:** Framework-First Principle
**Question 3:** Updating Framework after pull
**Question 4:** Working on Framework changes
**Question 5:** Crisis recovery

---

## 🎯 SLIDE 21: WRAP-UP & NEXT STEPS (3 min)

**What We Learned Today:**
- ✅ Git submodule basics (what, why, structure)
- ✅ Daily operations (clone, pull, commit workflow)
- ✅ Crisis recovery (3 failure scenarios)
- ✅ Framework-First Principle (methodology → automation)

**Hands-On Labs Completed:**
- ✅ Lab 1: Clone and Verify
- ✅ Lab 2: Update Framework (if time permits)
- ✅ Lab 3: Add Framework Content (if time permits)

**Certification Status:**
- Quiz graded by instructor (10 min)
- Results announced today
- Retakes scheduled if needed

**Next Steps:**
- ✅ Passed (4/5+): Certified for Week 2 work
- ⏳ Retake (<4/5): Study materials + retake by Dec 11 EOD

**Resources:**
- Training guide: `docs/09-govern/05-Operations/SUBMODULE-TEAM-TRAINING.md`
- Crisis recovery: `docs/09-govern/05-Operations/SUBMODULE-CRISIS-RECOVERY-PLAN.md`
- Quick reference card: (in training guide)

---

## 🙏 SLIDE 22: THANK YOU (1 min)

**Title:**
```
Thank You for Attending!

Week 2 work depends on 100% team certification.
Let's make SE 3.0 Track 1 a success together!

Questions? Ask instructor or PM/PO anytime.
```

**Closing Remarks:**
> "Thank you all for your time and attention today!
>
> Remember: Framework-First is non-negotiable. Methodology before automation. Templates in Framework, automation in Orchestrator.
>
> You're now equipped to work with git submodules. Use the crisis recovery plan if you hit any issues.
>
> Week 2 starts Dec 12 after CTO verification. Let's build something great together!
>
> Questions?"

---

## 📊 INSTRUCTOR NOTES

### Timing Breakdown (90 min total)

```
00:00-02:00  Welcome & Overview (Slide 1)
02:00-07:00  What is Git Submodule? (Slide 2)
07:00-12:00  Why Submodule for Framework? (Slide 3)
12:00-17:00  Framework-First in Practice (Slide 4)
17:00-22:00  Submodule Metadata Files (Slide 5)
22:00-32:00  Common Submodule States (Slide 6)

32:00-37:00  Cloning with Submodule (Slide 7)
37:00-42:00  Updating Framework After Pull (Slide 8)
42:00-52:00  Working on Framework Changes (Slide 9)
52:00-57:00  Framework-Only Work (Slide 10)
57:00-62:00  Hands-On Lab 1 (Slide 11)

62:00-67:00  Crisis Scenario 1 (Slide 12)
67:00-72:00  Crisis Scenario 2 (Slide 13)
72:00-77:00  Crisis Scenario 3 (Slide 14)

77:00-79:00  Quiz Instructions (Slide 15)
79:00-92:00  Quiz Questions (Slides 16-20, 15 min total)

92:00-95:00  Wrap-Up (Slide 21)
95:00-96:00  Thank You (Slide 22)

Total: 96 minutes (allows 6 min buffer for Q&A)
```

### Key Teaching Points

**Session 1 (Basics):**
- Emphasize: Submodule = separate repo, not folder
- Show: .gitmodules file + .git/modules/ directory
- Demo: git submodule status states (clean, modified, uninitialized)

**Session 2 (Operations):**
- Emphasize: Framework-First = methodology before automation
- Show: Two-step workflow (commit Framework → update main repo)
- Demo: Live clone + commit workflow

**Session 3 (Crisis):**
- Emphasize: All scenarios recoverable in <10 min
- Show: Crisis Recovery Plan document
- Demo: At least one crisis simulation live

### Common Student Questions

**Q: "Why not just copy Framework files into main repo?"**
A: "Because we'd lose independent versioning and ability to share Framework across 5 NQH projects. Submodule keeps Framework separate and reusable."

**Q: "What if I forget to update main repo pointer after Framework commit?"**
A: "Other team members won't see your Framework changes. Always do both steps: commit Framework → update main repo."

**Q: "Can I work on a feature branch in Framework?"**
A: "Per CTO guidance, we work directly on `main` branch for SE 3.0. No feature branches for now."

**Q: "What if GitHub is down during my work?"**
A: "You can still work locally. Commit when GitHub recovers. See Crisis Scenario 2 for full procedure."

---

## 🛠️ TECHNICAL SETUP CHECKLIST

**Before Workshop:**
- [ ] Test internet connectivity (clone repos)
- [ ] Test Zoom link (if remote session)
- [ ] Load presentation (this file)
- [ ] Open terminal for live demos
- [ ] Have Crisis Recovery Plan document ready
- [ ] Print quiz forms (9 copies)
- [ ] Prepare attendance sheet

**During Workshop:**
- [ ] Share screen (presentation + terminal)
- [ ] Record attendance
- [ ] Demo each command live (don't just show slides)
- [ ] Circulate during hands-on labs
- [ ] Answer questions as they arise
- [ ] Administer quiz at 77-minute mark

**After Workshop:**
- [ ] Grade quizzes (4/5 passing threshold)
- [ ] Announce results
- [ ] Schedule retakes if needed
- [ ] Submit evidence to CTO

---

**Document Owner:** PM/PO (Workshop Instructor)
**Created:** December 9, 2025
**Status:** READY FOR DELIVERY
**First Session:** Dec 10, 2025, 10:00 AM

---

**Instructor Notes:**
> "Keep energy high - this is hands-on, not lecture."
> "Demo everything live - students learn by seeing, not just reading."
> "Crisis recovery demos are critical - show real failures + real fixes."
> "Quiz is certification gate - be fair but rigorous (4/5 threshold)."
