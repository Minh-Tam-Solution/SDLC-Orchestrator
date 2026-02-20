# SE 3.0 Submodule Workflow Workshop
## Team Training Material - Week 1 Prerequisite

**Date:** December 9, 2025  
**Duration:** 30 minutes  
**Audience:** All Engineering Team Members  
**Prerequisites:** Basic Git knowledge

---

## WORKSHOP OBJECTIVES

By the end of this workshop, participants will:
1. ✅ Understand Framework-First Principle
2. ✅ Know how to clone repo with submodules
3. ✅ Know how to work with Framework submodule
4. ✅ Know how to update submodule pointers
5. ✅ Know when to escalate submodule issues

---

## ATTENDANCE TRACKING

**Workshop Date:** _______________  
**Workshop Time:** _______________  
**Instructor:** _______________

| Name | Role | Attendance | Quiz Score | Notes |
|------|------|------------|------------|-------|
| | | ✅ / ❌ | /5 | |
| | | ✅ / ❌ | /5 | |
| | | ✅ / ❌ | /5 | |

**Minimum Attendance:** 80% of team  
**Minimum Quiz Score:** 4/5 (80%)

---

## WORKSHOP CONTENT

### Part 1: Framework-First Principle (5 min)

**Key Concept:**
> Framework = Universal methodology (works with ANY tools)  
> Orchestrator = Automation tool (optional, accelerates adoption)

**Rule:**
- ✅ Framework changes go to `SDLC-Enterprise-Framework/` submodule
- ❌ Framework changes should NEVER go to main repo
- ✅ Orchestrator changes go to main repo
- ✅ Framework changes are tool-agnostic (Claude, GPT-4, Gemini, Ollama)

**Example:**
```yaml
✅ CORRECT:
  - Add SASE template to: SDLC-Enterprise-Framework/03-Templates-Tools/
  - Commit to Framework repo
  - Update main repo submodule pointer

❌ WRONG:
  - Add SASE template to: docs/03-Templates-Tools/ (main repo)
  - This violates Framework-First Principle
```

---

### Part 2: Cloning with Submodules (5 min)

**Option 1: Clone with Submodules (Recommended)**
```bash
git clone --recurse-submodules https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
cd SDLC-Orchestrator
# Framework submodule automatically initialized
```

**Option 2: Clone Then Init**
```bash
git clone https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
cd SDLC-Orchestrator
git submodule init
git submodule update
```

**Verification:**
```bash
git submodule status
# Should show: 00d728d... SDLC-Enterprise-Framework (heads/main)
```

---

### Part 3: Working with Framework Submodule (10 min)

**Scenario A: Reading Framework Content**
```bash
# Navigate to Framework
cd SDLC-Enterprise-Framework

# Read files (read-only is fine)
cat 02-Core-Methodology/README.md

# Return to main repo
cd ..
```

**Scenario B: Making Framework Changes**
```bash
# Navigate to Framework
cd SDLC-Enterprise-Framework

# Checkout main branch (per CTO Q4 guidance)
git checkout main
git pull origin main

# Make changes (e.g., add SASE template)
mkdir -p 03-Templates-Tools/SASE-Artifacts
# ... create files ...

# Commit to Framework repo
git add .
git commit -m "feat(SDLC 6.1.0): Add SASE artifact templates"
git push origin main

# Return to main repo
cd ..

# Update main repo submodule pointer
git submodule update --remote SDLC-Enterprise-Framework
git add SDLC-Enterprise-Framework
git commit -m "chore: Update Framework submodule - SASE templates"
git push origin main
```

**Scenario C: Updating Framework to Latest**
```bash
# Pull latest Framework changes
cd SDLC-Orchestrator
git pull origin main
git submodule update --remote --merge
```

---

### Part 4: Common Pitfalls (5 min)

**Pitfall 1: Forgetting to Update Submodule Pointer**
```bash
# ❌ WRONG: Push Framework changes, forget main repo
cd SDLC-Enterprise-Framework
git push origin main
cd ..
# Forgot: git submodule update --remote

# ✅ CORRECT: Always update main repo after Framework push
cd SDLC-Enterprise-Framework
git push origin main
cd ..
git submodule update --remote SDLC-Enterprise-Framework
git add SDLC-Enterprise-Framework
git commit -m "chore: Update Framework submodule"
```

**Pitfall 2: Making Framework Changes in Main Repo**
```bash
# ❌ WRONG: Add Framework file to main repo
mkdir -p docs/SDLC-Enterprise-Framework/03-Templates-Tools/
# This violates Framework-First Principle

# ✅ CORRECT: Add to submodule
cd SDLC-Enterprise-Framework
mkdir -p 03-Templates-Tools/
# ... create files ...
```

**Pitfall 3: Not Initializing Submodule After Clone**
```bash
# ❌ WRONG: Clone without submodules, then try to use Framework
git clone https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
cd SDLC-Enterprise-Framework
# Error: directory empty

# ✅ CORRECT: Initialize submodules
git submodule init
git submodule update
```

---

### Part 5: Escalation (5 min)

**When to Escalate:**
- Submodule pointer out of sync (after trying recovery)
- Framework repo unavailable (after 10 min)
- Submodule directory corrupted
- Any submodule issue blocking development

**Escalation Path:**
1. **L1:** DevOps Lead (<1 hour)
2. **L2:** CTO + DevOps Lead (<4 hours)
3. **L3:** CTO + CEO (<24 hours)

**Reference:** [Submodule Crisis Recovery Plan](../../07-operate/02-Incident-Response/SUBMODULE-CRISIS-RECOVERY.md)

---

## QUIZ (5 Questions)

**Instructions:** Answer each question. Minimum score: 4/5 (80%)

### Question 1: Framework-First Principle
Where should SASE artifact templates be added?
- [ ] A. `docs/03-Templates-Tools/` (main repo)
- [ ] B. `SDLC-Enterprise-Framework/03-Templates-Tools/` (submodule) ✅
- [ ] C. Either location is fine

### Question 2: Cloning Repository
What command clones repo with submodules?
- [ ] A. `git clone https://...`
- [ ] B. `git clone --recurse-submodules https://...` ✅
- [ ] C. `git clone --submodule https://...`

### Question 3: Updating Submodule Pointer
After pushing Framework changes, what's the next step?
- [ ] A. Nothing, Framework push is enough
- [ ] B. Update main repo submodule pointer ✅
- [ ] C. Re-clone the repository

### Question 4: Framework Changes Location
Can Framework changes be made in main repo?
- [ ] A. Yes, if it's faster
- [ ] B. No, violates Framework-First Principle ✅
- [ ] C. Only for emergency fixes

### Question 5: Submodule Health Check
What command checks submodule status?
- [ ] A. `git status`
- [ ] B. `git submodule status` ✅
- [ ] C. `git submodule list`

**Answer Key:** B, B, B, B, B

---

## POST-WORKSHOP VALIDATION

**Validation Checklist:**
- [ ] All team members attended (80%+ attendance)
- [ ] All team members scored 4/5+ on quiz
- [ ] Common pitfalls documented
- [ ] Escalation path understood

**Next Steps:**
- Practice submodule workflow on test branch
- Report any issues to DevOps Lead
- Reference [Submodule Crisis Recovery Plan](../../07-operate/02-Incident-Response/SUBMODULE-CRISIS-RECOVERY.md)

---

**Workshop Materials:**
- [Framework-First Principle](../../00-foundation/01-Vision/Product-Vision.md)
- [Submodule Workflow Guide](../../04-build/03-Setup-Guides/GIT-SUBMODULE-WORKFLOW.md)
- [Crisis Recovery Plan](../../07-operate/02-Incident-Response/SUBMODULE-CRISIS-RECOVERY.md)

---

**Last Updated:** December 9, 2025  
**Next Review:** January 9, 2026  
**Owner:** DevOps Lead + PM/PO


