# Week 1 Training Workshop Schedule
## SDLC-Enterprise-Framework Submodule Operations

**Document Version:** 1.0.0
**Status:** SCHEDULED - MANDATORY ATTENDANCE
**Authority:** CTO MANDATED
**Workshop Date:** December 10-11, 2025
**Duration:** 90 minutes
**Attendance Requirement:** 100% (9/9 developers)

---

## 🎯 WORKSHOP OVERVIEW

**Purpose:** Train all team members on git submodule operations for SDLC-Enterprise-Framework

**Non-Negotiable Requirement:**
- **100% attendance** (9/9 developers)
- **4/5 passing score** on certification quiz
- **Completion by Dec 11 EOD** (before Week 2 execution)

**CTO Authorization Dependency:**
- Week 2 work BLOCKED until training evidence submitted
- Evidence deadline: Dec 11 EOD
- CTO verification: Dec 12 morning
- Week 2 start: Dec 12 afternoon (if approved)

---

## 📅 WORKSHOP SCHEDULE

### **Session 1: December 10, 2025 - 10:00 AM - 11:30 AM**

**Location:** Conference Room A (or Zoom: https://zoom.us/j/XXXXXXX)

**Attendees (Group 1 - 5 developers):**
1. [ ] Backend Lead
2. [ ] Frontend Lead
3. [ ] Full-Stack Dev 1
4. [ ] Full-Stack Dev 2
5. [ ] QA Lead

**Agenda:**
- 10:00-10:30: Session 1 - Submodule Basics (30 min)
- 10:30-11:00: Session 2 - Daily Operations (30 min)
- 11:00-11:15: Session 3 - Crisis Recovery (15 min)
- 11:15-11:30: Certification Quiz (15 min)

---

### **Session 2: December 11, 2025 - 2:00 PM - 3:30 PM**

**Location:** Conference Room B (or Zoom: https://zoom.us/j/YYYYYYY)

**Attendees (Group 2 - 4 developers):**
6. [ ] DevOps Lead
7. [ ] Junior Dev 1
8. [ ] Junior Dev 2
9. [ ] PM/PO

**Agenda:**
- 2:00-2:30: Session 1 - Submodule Basics (30 min)
- 2:30-3:00: Session 2 - Daily Operations (30 min)
- 3:00-3:15: Session 3 - Crisis Recovery (15 min)
- 3:15-3:30: Certification Quiz (15 min)

---

## 📚 TRAINING MATERIALS

**Primary Document:**
- `docs/09-govern/05-Operations/SUBMODULE-TEAM-TRAINING.md` (643 lines)

**Hands-On Labs:**
1. Lab 1: Clone and Verify (5 min)
2. Lab 2: Update Framework (5 min)
3. Lab 3: Add Framework Content (10 min)

**Certification Quiz:**
- 5 questions (multiple choice)
- Passing score: 4/5 (80% accuracy)
- Unlimited retakes allowed (must pass by Dec 11 EOD)

---

## 🎓 CERTIFICATION QUIZ

### **Question 1: Cloning with Submodule**

Your manager asks you to clone SDLC Orchestrator. Which command is correct?

A) `git clone https://github.com/Minh-Tam-Solution/SDLC-Orchestrator`

B) `git clone --recurse-submodules https://github.com/Minh-Tam-Solution/SDLC-Orchestrator`

C) `git clone https://github.com/Minh-Tam-Solution/SDLC-Orchestrator && git submodule init`

D) Both B and C are correct

**Correct Answer:** D

---

### **Question 2: Framework-First Principle**

PM asks you to add "AI-powered BRD generator" feature. What is the CORRECT approach?

A) Add API endpoint to Orchestrator backend, hard-code BRD template in Python

B) Add BRD template to Framework (SDLC-Enterprise-Framework), then build Orchestrator automation

C) Build Orchestrator feature first, migrate to Framework later if needed

D) Framework-First doesn't apply to AI features, go ahead with Orchestrator

**Correct Answer:** B

---

### **Question 3: Updating Framework After Pull**

After `git pull origin main`, you notice Framework files are outdated. What should you do?

A) Delete SDLC-Enterprise-Framework/ and re-clone main repo

B) Run `git submodule update --init --recursive`

C) Run `cd SDLC-Enterprise-Framework && git pull origin main`

D) Ignore it, Framework updates are optional

**Correct Answer:** B

---

### **Question 4: Working on Framework Changes**

You need to add SASE MRP template to Framework. What is the correct workflow?

A) Edit in `SDLC-Orchestrator/SDLC-Enterprise-Framework/`, commit to main repo

B) Edit in `SDLC-Orchestrator/SDLC-Enterprise-Framework/`, commit to Framework repo, then update main repo pointer

C) Clone Framework repo separately, commit there, then update main repo submodule

D) Both B and C are correct

**Correct Answer:** D

---

### **Question 5: Crisis Recovery**

After `git pull`, you see error: `fatal: reference is not a tree: abc1234`. What is the problem?

A) Framework repository is unavailable (GitHub outage)

B) Submodule pointer out of sync (run `git submodule update`)

C) Framework commit abc1234 doesn't exist (force-pushed or deleted)

D) Your local Framework has uncommitted changes

**Correct Answer:** C

---

## 📊 ATTENDANCE TRACKING

### **Group 1 (Dec 10, 10:00 AM)**

| Name | Role | Attended | Quiz Score | Status | Retake Date |
|------|------|----------|------------|--------|-------------|
| [Name 1] | Backend Lead | [ ] | __/5 | ⏳ Pending | N/A |
| [Name 2] | Frontend Lead | [ ] | __/5 | ⏳ Pending | N/A |
| [Name 3] | Full-Stack Dev 1 | [ ] | __/5 | ⏳ Pending | N/A |
| [Name 4] | Full-Stack Dev 2 | [ ] | __/5 | ⏳ Pending | N/A |
| [Name 5] | QA Lead | [ ] | __/5 | ⏳ Pending | N/A |

---

### **Group 2 (Dec 11, 2:00 PM)**

| Name | Role | Attended | Quiz Score | Status | Retake Date |
|------|------|----------|------------|--------|-------------|
| [Name 6] | DevOps Lead | [ ] | __/5 | ⏳ Pending | N/A |
| [Name 7] | Junior Dev 1 | [ ] | __/5 | ⏳ Pending | N/A |
| [Name 8] | Junior Dev 2 | [ ] | __/5 | ⏳ Pending | N/A |
| [Name 9] | PM/PO | [ ] | __/5 | ⏳ Pending | N/A |

---

## ✅ COMPLETION CHECKLIST

### **Workshop Preparation (Dec 9, 2025)**

- [x] Create workshop schedule
- [ ] Send calendar invites to all 9 developers
- [ ] Reserve Conference Room A (Dec 10, 10am-11:30am)
- [ ] Reserve Conference Room B (Dec 11, 2pm-3:30pm)
- [ ] Prepare Zoom links (if remote attendance needed)
- [ ] Print quiz forms (9 copies)
- [ ] Prepare hands-on lab environment (Docker + git)

---

### **Workshop Delivery (Dec 10-11, 2025)**

**Session 1 (Dec 10, 10am):**
- [ ] Record attendance (5/5 developers present)
- [ ] Deliver 3 training sessions (basics, operations, crisis)
- [ ] Supervise 3 hands-on labs
- [ ] Administer certification quiz
- [ ] Grade quizzes (4/5 passing threshold)
- [ ] Schedule retakes if needed (same day or Dec 11)

**Session 2 (Dec 11, 2pm):**
- [ ] Record attendance (4/4 developers present)
- [ ] Deliver 3 training sessions
- [ ] Supervise 3 hands-on labs
- [ ] Administer certification quiz
- [ ] Grade quizzes (4/5 passing threshold)
- [ ] Schedule retakes if needed (Dec 11 evening)

---

### **Evidence Submission (Dec 11 EOD)**

- [ ] **Attendance Report**
  - Total attendance: __/9 (100% required)
  - Group 1: __/5
  - Group 2: __/4

- [ ] **Quiz Results**
  - Pass rate: __/9 (100% required by Dec 11 EOD)
  - Average score: __/5
  - Retakes completed: __

- [ ] **Hands-On Labs**
  - Lab 1 completion: __/9
  - Lab 2 completion: __/9
  - Lab 3 completion: __/9

- [ ] **Supporting Evidence**
  - Attendance sheets (signed by attendees)
  - Quiz answer sheets (graded, scored)
  - Lab completion screenshots (9 developers)

---

### **CTO Submission (Dec 11 EOD)**

**Deliverables to CTO:**

1. **Training Evidence Report**
   - File: `docs/09-govern/05-Operations/WEEK-1-TRAINING-EVIDENCE-REPORT.md`
   - Content: Attendance, quiz scores, lab results

2. **Attendance Sheets**
   - Scanned copies (PDF)
   - Signed by all attendees

3. **Quiz Results**
   - Individual scores (anonymized)
   - Pass rate summary

**Submission Method:**
- Email to CTO: cto@company.com
- Subject: "SE 3.0 Week 1 Training Evidence - Dec 11, 2025"
- Attachments: Evidence report + attendance sheets + quiz results

---

## 📋 CALENDAR INVITES

### **Invite 1: Group 1 Workshop**

```
Subject: [MANDATORY] SE 3.0 Submodule Training - Group 1
Date: December 10, 2025
Time: 10:00 AM - 11:30 AM (90 min)
Location: Conference Room A / Zoom: https://zoom.us/j/XXXXXXX

Attendees:
- Backend Lead
- Frontend Lead
- Full-Stack Dev 1
- Full-Stack Dev 2
- QA Lead

Organizer: PM/PO

Description:
This is a MANDATORY training workshop on SDLC-Enterprise-Framework submodule operations.

Agenda:
- 10:00-10:30: Submodule Basics (what, why, structure)
- 10:30-11:00: Daily Operations (clone, pull, commit workflow)
- 11:00-11:15: Crisis Recovery (3 failure scenarios)
- 11:15-11:30: Certification Quiz (5 questions, 4/5 passing)

Requirements:
- 100% attendance required (CTO mandated)
- Bring laptop with git installed
- Complete 3 hands-on labs during workshop
- Pass certification quiz (4/5 minimum score)

Materials:
- Training guide: docs/09-govern/05-Operations/SUBMODULE-TEAM-TRAINING.md
- Crisis recovery plan: docs/09-govern/05-Operations/SUBMODULE-CRISIS-RECOVERY-PLAN.md

Important:
- Week 2 work BLOCKED until training evidence submitted to CTO
- Retakes available if quiz score <4/5 (must pass by Dec 11 EOD)
- Questions? Contact PM/PO before Dec 10 morning

See you there!
```

---

### **Invite 2: Group 2 Workshop**

```
Subject: [MANDATORY] SE 3.0 Submodule Training - Group 2
Date: December 11, 2025
Time: 2:00 PM - 3:30 PM (90 min)
Location: Conference Room B / Zoom: https://zoom.us/j/YYYYYYY

Attendees:
- DevOps Lead
- Junior Dev 1
- Junior Dev 2
- PM/PO

Organizer: PM/PO

Description:
This is a MANDATORY training workshop on SDLC-Enterprise-Framework submodule operations.

Agenda:
- 2:00-2:30: Submodule Basics (what, why, structure)
- 2:30-3:00: Daily Operations (clone, pull, commit workflow)
- 3:00-3:15: Crisis Recovery (3 failure scenarios)
- 3:15-3:30: Certification Quiz (5 questions, 4/5 passing)

Requirements:
- 100% attendance required (CTO mandated)
- Bring laptop with git installed
- Complete 3 hands-on labs during workshop
- Pass certification quiz (4/5 minimum score)

Materials:
- Training guide: docs/09-govern/05-Operations/SUBMODULE-TEAM-TRAINING.md
- Crisis recovery plan: docs/09-govern/05-Operations/SUBMODULE-CRISIS-RECOVERY-PLAN.md

Important:
- Week 2 work BLOCKED until training evidence submitted to CTO
- Retakes available if quiz score <4/5 (must pass by Dec 11 EOD)
- This is the LAST training session before evidence submission deadline
- Questions? Contact PM/PO before Dec 11 morning

See you there!
```

---

## 🔧 HANDS-ON LAB SETUP

### **Lab Environment Requirements**

**Each Developer's Laptop:**
```bash
# Verify git installed
git --version
# Required: git 2.30+ (submodule support)

# Verify Docker installed (for testing)
docker --version
# Required: Docker 20.10+

# Verify network access
ping github.com
# Required: Internet connectivity to clone repos
```

**Lab Repositories:**
```bash
# Main repo (with submodule)
https://github.com/Minh-Tam-Solution/SDLC-Orchestrator

# Framework repo (submodule)
https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework
```

---

### **Lab 1: Clone and Verify (5 min)**

**Objective:** Clone SDLC Orchestrator with Framework submodule

**Instructions:**
```bash
# Step 1: Clone with submodule (choose ONE method)

# Method A: Single command (recommended)
git clone --recurse-submodules https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
cd SDLC-Orchestrator

# Method B: Two commands (alternative)
git clone https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
cd SDLC-Orchestrator
git submodule init
git submodule update

# Step 2: Verify submodule status
git submodule status
# Expected output: Shows Framework commit hash + path

# Step 3: Count Framework directories
ls -1 SDLC-Enterprise-Framework/ | wc -l
# Expected: 10+ directories (00-Why, 01-What, etc.)

# Step 4: Verify Framework remote
cd SDLC-Enterprise-Framework
git remote -v
# Expected: github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework
```

**Success Criteria:**
- [ ] Submodule initialized (no errors)
- [ ] Framework files present (10+ directories)
- [ ] Framework remote correct (not Orchestrator remote)

---

### **Lab 2: Update Framework (5 min)**

**Objective:** Pull latest Framework changes

**Instructions:**
```bash
# Step 1: Navigate to main repo
cd /path/to/SDLC-Orchestrator

# Step 2: Pull main repo changes
git pull origin main

# Step 3: Update submodule to match main repo pointer
git submodule update --init --recursive

# Step 4: Verify Framework updated
cd SDLC-Enterprise-Framework
git log -1 --oneline
# Should show latest Framework commit

# Step 5: Return to main repo
cd ..
```

**Success Criteria:**
- [ ] Framework files match latest commit
- [ ] No "detached HEAD" warnings
- [ ] Submodule status shows no errors

---

### **Lab 3: Add Framework Content (10 min)**

**Objective:** Add new file to Framework and update main repo

**Instructions:**
```bash
# Step 1: Navigate to Framework
cd SDLC-Enterprise-Framework

# Step 2: Create test file (for training only)
echo "# Test Document - Training Lab 3" > TRAINING-LAB-TEST.md
git add TRAINING-LAB-TEST.md
git commit -m "test: Add training lab test file"

# Step 3: Push to Framework repo
git push origin main

# Step 4: Update main repo pointer
cd ..
git submodule update --remote SDLC-Enterprise-Framework
git add SDLC-Enterprise-Framework
git commit -m "chore: Update Framework - training lab test"
git push origin main

# Step 5: Cleanup (delete test file)
cd SDLC-Enterprise-Framework
git rm TRAINING-LAB-TEST.md
git commit -m "chore: Remove training lab test file"
git push origin main
cd ..
git submodule update --remote SDLC-Enterprise-Framework
git add SDLC-Enterprise-Framework
git commit -m "chore: Cleanup training lab test"
git push origin main
```

**Success Criteria:**
- [ ] Test file appears in Framework repo
- [ ] Main repo submodule pointer updated
- [ ] Test file cleanly removed
- [ ] No merge conflicts

---

## 📧 POST-WORKSHOP COMMUNICATION

### **Email to Team (After Workshop)**

```
Subject: SE 3.0 Submodule Training - Quiz Results & Next Steps

Hi Team,

Thank you for attending the SE 3.0 Submodule Training workshop today!

Results:
- Attendance: [X/9] (100% required)
- Average Quiz Score: [X.X/5]
- Pass Rate: [X/9] (100% required by Dec 11 EOD)

Next Steps:

For those who passed (4/5+):
✅ Congratulations! You're certified for Week 2 work.
✅ Reference materials: docs/09-govern/05-Operations/SUBMODULE-TEAM-TRAINING.md

For those who need retakes (<4/5):
⏳ Retake scheduled: [Date/Time]
⏳ Study materials: [Link to training guide]
⏳ Deadline: Dec 11 EOD (before CTO evidence submission)

Important Reminders:
- Week 2 work BLOCKED until all 9 developers certified
- Training evidence submitted to CTO: Dec 11 EOD
- CTO verification: Dec 12 morning
- Week 2 start: Dec 12 afternoon (if approved)

Questions?
Reply to this email or Slack me anytime.

Best regards,
PM/PO
```

---

## ✅ SUCCESS CRITERIA

**Training Workshop Success:**
- [ ] 100% attendance (9/9 developers)
- [ ] 100% pass rate (9/9 score 4/5+ on quiz)
- [ ] 100% lab completion (all 3 labs completed by all 9 developers)
- [ ] Evidence submitted to CTO by Dec 11 EOD
- [ ] CTO approval received by Dec 12 morning

**Certification Criteria (Per Developer):**
- [ ] Attended full 90-minute workshop
- [ ] Completed all 3 hands-on labs
- [ ] Scored 4/5+ on certification quiz
- [ ] Can clone repo with `--recurse-submodules`
- [ ] Can update submodule after `git pull`
- [ ] Can commit to Framework and update main repo pointer

---

**Document Owner:** PM/PO + CTO
**Created:** December 9, 2025
**Status:** SCHEDULED - AWAITING EXECUTION
**Next Update:** Dec 11 EOD (evidence submission)

---

**PM/PO Notes:**
> "Training workshop scheduled for Dec 10-11 (2 sessions, 90 min each)."
> "100% attendance required (9/9 developers)."
> "Evidence submission deadline: Dec 11 EOD."
> "Week 2 work BLOCKED until CTO approval (Dec 12 morning)."
