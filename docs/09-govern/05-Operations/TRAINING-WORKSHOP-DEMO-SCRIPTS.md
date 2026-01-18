# Training Workshop Demo Scripts
## Hands-On Lab Instructions for Instructors

**Document Version:** 1.0.0
**Status:** READY FOR USE
**Workshop Date:** Dec 10-11, 2025
**Duration:** 3 labs × 10 minutes = 30 minutes total
**Audience:** 9 developers (2 sessions)

---

## 🎯 OVERVIEW

**Purpose:** Provide step-by-step demo scripts for instructors to guide hands-on labs during the 90-minute training workshop.

**Lab Structure:**
- **Lab 1:** Clone with Submodule (10 min) - After Session 1
- **Lab 2:** Update Framework After Pull (10 min) - After Session 2
- **Lab 3:** Two-Step Commit Workflow (10 min) - After Session 2

**Instructor Role:**
- Live demo on projector (5 min)
- Students follow along (5 min)
- Q&A and troubleshooting (built into timing)

---

## 🔧 TECHNICAL SETUP (Before Workshop)

### **Instructor Machine Preparation**

**Terminal Setup:**
```bash
# Open 2 terminal windows side-by-side
# Terminal 1: For live demos
# Terminal 2: For showing git status/logs

# Increase font size for visibility
# Recommended: 18-20pt font (readable from back of room)

# Use clear terminal theme
# Recommended: Light background (better for projector)
```

**Repository Cleanup (Start Fresh Each Session):**
```bash
# Remove existing clone (if any)
cd ~/Desktop
rm -rf SDLC-Orchestrator-DEMO

# Verify clean state
ls -la ~/Desktop | grep SDLC
# Should show: No SDLC-Orchestrator directory
```

**GitHub Access:**
```bash
# Verify SSH key or HTTPS credentials working
ssh -T git@github.com
# Should show: "Hi [username]! You've successfully authenticated"

# OR for HTTPS:
git config --global credential.helper cache
# Cache credentials for 15 minutes
```

**Student Environment Verification:**
```bash
# Before lab starts, ask students to verify:
git --version
# Minimum: git 2.20+ (for submodule improvements)

ssh -T git@github.com
# OR configure HTTPS credentials

cd ~/Desktop
# Students should work in consistent location
```

---

## 📝 LAB 1: CLONE WITH SUBMODULE (10 MIN)

**Timing Breakdown:**
- 00:00-05:00 Instructor demo
- 05:00-09:00 Students follow along
- 09:00-10:00 Q&A and troubleshooting

**Learning Objective:** Students can clone SDLC Orchestrator with Framework submodule initialized in one command.

---

### **INSTRUCTOR DEMO SCRIPT**

**Step 1: Show Wrong Way (Common Mistake)**

```bash
# Terminal 1 (Instructor narrates while typing)

# "Let me show you the WRONG way first - what happens if you forget --recurse-submodules"

cd ~/Desktop

git clone https://github.com/Minh-Tam-Solution/SDLC-Orchestrator SDLC-Orchestrator-WRONG

cd SDLC-Orchestrator-WRONG

# "Let's check if Framework is there"
ls -la SDLC-Enterprise-Framework/

# Expected output: Empty directory or just .git file
# Instructor points out: "See? Framework directory is EMPTY!"

# "Let's confirm with git submodule status"
git submodule status

# Expected output: "-abc1234 SDLC-Enterprise-Framework (uninitialized)"
# Instructor explains: The "-" prefix means UNINITIALIZED

# "If you try to build now, it will FAIL because Framework templates are missing"
# This is the #1 submodule mistake!
```

**Step 2: Show Correct Way (Option B - Recommended)**

```bash
# Terminal 1 (Instructor continues)

# "Now let's do it the RIGHT way - Option B (recommended)"

cd ~/Desktop

git clone --recurse-submodules https://github.com/Minh-Tam-Solution/SDLC-Orchestrator SDLC-Orchestrator-CORRECT

cd SDLC-Orchestrator-CORRECT

# "Notice the --recurse-submodules flag? This initializes Framework automatically"

# "Let's verify Framework is populated"
ls -la SDLC-Enterprise-Framework/

# Expected output: Directories like 00-Why, 01-What, 02-How, etc.
# Instructor counts: "See? We have all 11 SDLC 5.1.3 folders!"

# "Let's confirm with git submodule status"
git submodule status

# Expected output: " abc1234 SDLC-Enterprise-Framework (heads/main)"
# Instructor explains: No prefix = CLEAN, ready to use

# "Framework is now fully initialized - ready for development!"
```

**Step 3: Show Alternative Way (Option C)**

```bash
# Terminal 1 (Instructor shows two-step alternative)

# "There's also Option C - two-step process (more explicit)"

cd ~/Desktop
rm -rf SDLC-Orchestrator-ALT

# Step 1: Clone main repo (WITHOUT submodules)
git clone https://github.com/Minh-Tam-Solution/SDLC-Orchestrator SDLC-Orchestrator-ALT

cd SDLC-Orchestrator-ALT

# "At this point, Framework is empty (same as wrong way)"
ls SDLC-Enterprise-Framework/
# Empty!

# Step 2: Initialize submodule manually
git submodule init
git submodule update

# "Now Framework is populated"
ls -la SDLC-Enterprise-Framework/
# Populated!

# "Both Option B and Option C work - Option B is faster (one command)"
```

**Step 4: Comparison Summary (Terminal 2)**

```bash
# Terminal 2 (Instructor shows side-by-side comparison)

# "Let me summarize the three approaches"

# Terminal 2 splits into 3 panes (tmux or separate windows)

# Pane 1: WRONG
cd ~/Desktop/SDLC-Orchestrator-WRONG
git submodule status
# Output: -abc1234 SDLC-Enterprise-Framework (uninitialized)

# Pane 2: CORRECT (Option B)
cd ~/Desktop/SDLC-Orchestrator-CORRECT
git submodule status
# Output:  abc1234 SDLC-Enterprise-Framework (heads/main)

# Pane 3: ALTERNATIVE (Option C)
cd ~/Desktop/SDLC-Orchestrator-ALT
git submodule status
# Output:  abc1234 SDLC-Enterprise-Framework (heads/main)

# Instructor points out: "Option B and C have SAME result - clean submodule!"
```

---

### **STUDENT HANDS-ON (5 MIN)**

**Instructor Instructions to Students:**

> "Now it's your turn! Please follow these steps on your machine:"
>
> **Step 1:** Open terminal and navigate to Desktop
> ```bash
> cd ~/Desktop
> ```
>
> **Step 2:** Clone with submodule initialization (Option B - recommended)
> ```bash
> git clone --recurse-submodules https://github.com/Minh-Tam-Solution/SDLC-Orchestrator
> ```
>
> **Step 3:** Verify submodule initialized
> ```bash
> cd SDLC-Orchestrator
> git submodule status
> ```
> Expected output: ` abc1234 SDLC-Enterprise-Framework (heads/main)`
> (No "-" prefix = initialized correctly)
>
> **Step 4:** Verify Framework files present
> ```bash
> ls SDLC-Enterprise-Framework/
> ```
> Expected output: 00-Why, 01-What, 02-How, ..., 10-SASE-Artifacts
>
> **Success Criteria:** You should see 11 folders in Framework directory!

**Common Issues & Troubleshooting:**

| Issue | Symptom | Fix |
|-------|---------|-----|
| **SSH key not configured** | `Permission denied (publickey)` | Use HTTPS: `git clone --recurse-submodules https://...` |
| **Framework empty** | `ls SDLC-Enterprise-Framework/` shows empty | Run `git submodule update --init --recursive` |
| **Submodule shows "-" prefix** | `git submodule status` shows `-abc1234` | Same as above - run submodule update |
| **Network timeout** | Clone hangs at "Receiving objects" | Wait 30s, retry with `--depth 1` flag |

**Instructor Monitors Progress:**
- Walk around room, check student screens
- Look for "-" prefix in `git submodule status` (indicates failure)
- Help students with SSH/HTTPS authentication issues

---

## 📝 LAB 2: UPDATE FRAMEWORK AFTER PULL (10 MIN)

**Timing Breakdown:**
- 00:00-05:00 Instructor demo
- 05:00-09:00 Students follow along
- 09:00-10:00 Q&A and troubleshooting

**Learning Objective:** Students understand that `git pull` does NOT update submodules automatically, and can fix outdated Framework.

---

### **INSTRUCTOR DEMO SCRIPT**

**Step 1: Simulate Outdated Framework (Setup)**

```bash
# Terminal 1 (Instructor sets up scenario)

cd ~/Desktop/SDLC-Orchestrator-CORRECT

# "Let me simulate what happens when Framework is outdated"

# Step 1: Check current submodule commit
git submodule status
# Output:  abc1234 SDLC-Enterprise-Framework (heads/main)
# Instructor notes: "Current Framework commit: abc1234"

# Step 2: Manually checkout older Framework commit (simulate outdated)
cd SDLC-Enterprise-Framework
git log --oneline -5
# Shows recent commits

git checkout HEAD~2
# Go back 2 commits (simulate outdated)

cd ..
git submodule status
# Output: +def5678 SDLC-Enterprise-Framework (heads/main)
# Instructor points out: "See the '+' prefix? Framework is MODIFIED (outdated)"
```

**Step 2: Show Wrong Way (Common Mistake)**

```bash
# Terminal 1 (Instructor demonstrates mistake)

# "What if a teammate just did 'git pull' on main repo?"

# Simulate: Another developer updates main repo's submodule pointer
# (In reality, instructor just shows `git pull` doesn't sync Framework)

git pull origin main

# "Let's check Framework status"
git submodule status
# Output: +def5678 SDLC-Enterprise-Framework (still outdated!)

# Instructor explains: "See? 'git pull' updated main repo, but Framework is STILL outdated!"
# This is Crisis Scenario 1 from training!

ls SDLC-Enterprise-Framework/
# Files are from old commit (missing recent templates)
```

**Step 3: Show Correct Way (Crisis Recovery)**

```bash
# Terminal 1 (Instructor shows fix)

# "Here's how to fix it - the magic command:"

git submodule update --init --recursive

# "Let's verify Framework is now synced"
git submodule status
# Output:  abc1234 SDLC-Enterprise-Framework (heads/main)
# Instructor points out: "No '+' prefix anymore - CLEAN!"

# "Framework is now synced to the commit tracked by main repo"

cd SDLC-Enterprise-Framework
git log --oneline -1
# Shows current commit matches main repo's pointer

cd ..
```

**Step 4: Show Daily Workflow (Best Practice)**

```bash
# Terminal 1 (Instructor shows recommended workflow)

# "Here's the daily workflow you should follow EVERY TIME you pull:"

# Create alias for convenience (optional)
git config --global alias.pullall '!git pull && git submodule update --init --recursive'

# "Now you can use:"
git pullall

# "This updates BOTH main repo AND Framework submodule!"

# Alternative (without alias):
git pull origin main && git submodule update --init --recursive

# "Get in the habit of ALWAYS running submodule update after pull"
```

**Step 5: Explain Wrong Approach (Direct Pull in Framework)**

```bash
# Terminal 1 (Instructor shows what NOT to do)

# "What if you do 'git pull' INSIDE Framework directory?"

cd SDLC-Enterprise-Framework
git checkout main
git pull origin main

# "Let's check main repo status"
cd ..
git submodule status
# Output: +xyz9876 SDLC-Enterprise-Framework (modified)

# Instructor explains:
# "See the '+' prefix? Framework is now AHEAD of main repo's pointer!"
# "This creates a version mismatch - your teammates will be confused"

git status
# Shows: modified:   SDLC-Enterprise-Framework (new commits)

# "This is WRONG approach - main repo tracks SPECIFIC commit, not 'latest'"

# Fix: Revert to tracked commit
git submodule update --init --recursive
```

---

### **STUDENT HANDS-ON (5 MIN)**

**Instructor Instructions to Students:**

> "Now practice the update workflow on your machine:"
>
> **Step 1:** Simulate outdated Framework
> ```bash
> cd ~/Desktop/SDLC-Orchestrator/SDLC-Enterprise-Framework
> git checkout HEAD~1
> cd ..
> git submodule status
> ```
> Expected: `+abc1234` (+ prefix = modified/outdated)
>
> **Step 2:** Try wrong way (verify it doesn't work)
> ```bash
> git pull origin main
> git submodule status
> ```
> Expected: Still shows `+abc1234` (not fixed!)
>
> **Step 3:** Fix with correct command
> ```bash
> git submodule update --init --recursive
> git submodule status
> ```
> Expected: ` abc1234` (no prefix = clean!)
>
> **Step 4:** Create alias for daily workflow (optional)
> ```bash
> git config --global alias.pullall '!git pull && git submodule update --init --recursive'
> ```
> Test: `git pullall`

**Common Issues & Troubleshooting:**

| Issue | Symptom | Fix |
|-------|---------|-----|
| **Submodule still shows "+"** | After update, `+abc1234` persists | Run `git submodule update --force --recursive` |
| **Uncommitted changes warning** | Error: "Cannot checkout ... local changes" | Stash changes: `cd Framework && git stash` |
| **Network timeout** | Update hangs | Check internet connection, retry |

---

## 📝 LAB 3: TWO-STEP COMMIT WORKFLOW (10 MIN)

**Timing Breakdown:**
- 00:00-05:00 Instructor demo
- 05:00-09:00 Students follow along
- 09:00-10:00 Q&A and troubleshooting

**Learning Objective:** Students can make changes to Framework and update main repo's submodule pointer (two-step commit workflow).

---

### **INSTRUCTOR DEMO SCRIPT**

**Step 1: Make Change in Framework**

```bash
# Terminal 1 (Instructor demonstrates Framework change)

cd ~/Desktop/SDLC-Orchestrator-CORRECT

# "Let's say we need to add a new SASE template to Framework"

cd SDLC-Enterprise-Framework

# Verify we're on main branch
git branch
# Should show: * main

# Create new file (example: Add ACE template)
mkdir -p 03-Templates-Tools/SASE-Artifacts
cat > 03-Templates-Tools/SASE-Artifacts/04-ACE-Template.md << 'EOF'
# Accountability & Commitment Examination (ACE)

**Version:** 1.0.0
**Status:** TEMPLATE

## Purpose
Document team accountability and commitments for project delivery.

## Template Structure

### 1. Team Roster
- Role assignments
- Responsibilities
- Availability

### 2. Commitment Matrix
- Deliverable commitments
- Timeline commitments
- Quality commitments

### 3. Accountability Framework
- Who is accountable for what
- Escalation paths
- Decision rights

---

*Template created: Dec 10, 2025*
EOF

# "New ACE template created in Framework"
```

**Step 2: Commit to Framework Repo (FIRST COMMIT)**

```bash
# Terminal 1 (Still in Framework directory)

# "Step 1 of 2: Commit to Framework repo"

git status
# Shows: new file: 03-Templates-Tools/SASE-Artifacts/04-ACE-Template.md

git add 03-Templates-Tools/SASE-Artifacts/04-ACE-Template.md

git commit -m "feat(SDLC 5.1.0): Add ACE (Accountability & Commitment Examination) template

New SASE artifact template for SE 3.0 Track 1.

Related: SE 3.0 SASE Integration Plan"

# "Framework commit created!"

git log --oneline -1
# Shows new commit hash, e.g., abc9999

# Instructor notes: "This commit is LOCAL to Framework repo - teammates won't see it yet"
```

**Step 3: Push Framework Changes**

```bash
# Terminal 1 (Still in Framework directory)

# "Push Framework changes to remote"

git push origin main

# "Framework changes now visible to team!"

# Verify push succeeded
git log --oneline -1 origin/main
# Should match local commit
```

**Step 4: Update Main Repo Pointer (SECOND COMMIT)**

```bash
# Terminal 1 (Navigate back to main repo)

cd ..
# Now in main repo (SDLC-Orchestrator)

# "Step 2 of 2: Update main repo's submodule pointer"

git status
# Shows: modified:   SDLC-Enterprise-Framework (new commits)

# "See? Main repo detected Framework changed!"

git submodule status
# Shows: +abc9999 SDLC-Enterprise-Framework (modified)
# Instructor points out: "The '+' means Framework has new commits"

# Add submodule pointer update
git add SDLC-Enterprise-Framework

git commit -m "chore: Update Framework submodule - Add ACE template

Framework updated to include ACE (Accountability & Commitment Examination) template.

Framework commit: abc9999
Related: SE 3.0 SASE Integration Plan"

# "Main repo commit created!"
```

**Step 5: Push Main Repo Changes**

```bash
# Terminal 1 (Still in main repo)

# "Push main repo changes to remote"

git push origin main

# "Done! Both commits pushed - teammates will now see ACE template"

# Verify final state
git submodule status
# Shows:  abc9999 SDLC-Enterprise-Framework (heads/main)
# Instructor points out: "No '+' prefix - clean!"
```

**Step 6: Explain Two-Step Workflow (Diagram)**

```bash
# Terminal 2 (Instructor shows workflow diagram)

# "Let me visualize the two-step workflow:"

cat << 'EOF'

┌─────────────────────────────────────────────────────────────┐
│ TWO-STEP COMMIT WORKFLOW                                    │
└─────────────────────────────────────────────────────────────┘

Step 1: Commit to Framework Repo
┌──────────────────────────────────────┐
│ cd SDLC-Enterprise-Framework         │
│ git add <files>                      │
│ git commit -m "feat: Add ACE"        │
│ git push origin main                 │
│                                      │
│ Result: Framework commit abc9999     │
└──────────────────────────────────────┘
                 │
                 ▼
Step 2: Update Main Repo Pointer
┌──────────────────────────────────────┐
│ cd ..                                │
│ git add SDLC-Enterprise-Framework    │
│ git commit -m "chore: Update"        │
│ git push origin main                 │
│                                      │
│ Result: Main repo tracks abc9999     │
└──────────────────────────────────────┘

EOF
```

**Step 7: Show What Happens If You Skip Step 2**

```bash
# Terminal 1 (Instructor demonstrates mistake)

# "What if you forget Step 2? Let's see..."

cd SDLC-Enterprise-Framework

# Make another change
echo "## Additional Section" >> 03-Templates-Tools/SASE-Artifacts/04-ACE-Template.md

git add .
git commit -m "docs: Update ACE template"
git push origin main

# Skip Step 2 - don't update main repo pointer
cd ..

# "Let's see what happens when a teammate clones now"

cd ~/Desktop
rm -rf SDLC-Orchestrator-TEAMMATE
git clone --recurse-submodules https://github.com/Minh-Tam-Solution/SDLC-Orchestrator SDLC-Orchestrator-TEAMMATE

cd SDLC-Orchestrator-TEAMMATE/SDLC-Enterprise-Framework
cat 03-Templates-Tools/SASE-Artifacts/04-ACE-Template.md
# Instructor points out: "See? Teammate doesn't have 'Additional Section'!"
# Because main repo pointer wasn't updated!

# "This is why Step 2 is MANDATORY - always update main repo pointer!"
```

---

### **STUDENT HANDS-ON (5 MIN)**

**Instructor Instructions to Students:**

> "Practice the two-step workflow on your machine:"
>
> **Step 1:** Make change in Framework
> ```bash
> cd ~/Desktop/SDLC-Orchestrator/SDLC-Enterprise-Framework
> mkdir -p 03-Templates-Tools/SASE-Artifacts
> echo "# Test Template" > 03-Templates-Tools/SASE-Artifacts/TEST-$(date +%s).md
> ```
>
> **Step 2:** Commit to Framework repo
> ```bash
> git add .
> git commit -m "test: Add test template for training"
> git push origin main
> ```
> Note: Push may fail if no write access - that's OK for training!
>
> **Step 3:** Update main repo pointer
> ```bash
> cd ..
> git status
> ```
> Expected: `modified:   SDLC-Enterprise-Framework`
> ```bash
> git add SDLC-Enterprise-Framework
> git commit -m "chore: Update Framework submodule - test template"
> ```
>
> **Step 4:** Verify final state
> ```bash
> git submodule status
> ```
> Expected: ` abc1234` (no prefix = clean)

**Common Issues & Troubleshooting:**

| Issue | Symptom | Fix |
|-------|---------|-----|
| **Push to Framework fails** | `Permission denied` | Expected - students don't have write access (training only) |
| **Main repo shows modified** | After commit, still shows modified | Verify `git add SDLC-Enterprise-Framework` ran |
| **Submodule shows "+"** | After main commit, still `+abc1234` | Run `git submodule update` to sync |

**Instructor Clarification:**

> "In real work, you WILL have write access to Framework repo. For this training, push failures are expected - focus on understanding the two-step workflow concept!"

---

## 📊 LAB COMPLETION CHECKLIST

**After Each Lab, Instructor Verifies:**

**Lab 1 Checklist:**
- [ ] All students have SDLC-Orchestrator cloned
- [ ] `git submodule status` shows no "-" prefix (all initialized)
- [ ] Framework directory contains 11 folders (00-Why to 10-SASE-Artifacts)
- [ ] No students stuck on authentication issues

**Lab 2 Checklist:**
- [ ] All students successfully ran `git submodule update`
- [ ] Students understand `git pull` ≠ submodule update
- [ ] Students can identify "+" prefix in `git submodule status`
- [ ] Optional: Students created `pullall` alias

**Lab 3 Checklist:**
- [ ] All students understand two-step workflow concept
- [ ] Students can commit to Framework (even if push fails)
- [ ] Students can update main repo pointer
- [ ] Students understand why Step 2 is mandatory

---

## 🎯 POST-LAB Q&A TIPS

**Common Questions & Answers:**

**Q: "Why can't we just use 'git pull' in Framework directory?"**
A: "Because main repo tracks a SPECIFIC Framework commit (version lock). Pulling in Framework creates version mismatch - your teammates will be confused. Always use `git submodule update` to sync to tracked commit."

**Q: "What if I want to work on Framework changes for multiple days?"**
A: "Work in Framework directory as normal (commit locally). When ready to share, push Framework changes (Step 1) THEN update main repo pointer (Step 2). Don't skip Step 2!"

**Q: "Can I use feature branches in Framework?"**
A: "Yes! Work on Framework feature branch, then merge to main. After merge, update main repo pointer to new Framework commit. Same two-step workflow applies."

**Q: "What's the recovery time if Framework breaks?"**
A: "See Crisis Recovery Plan - all 3 scenarios have <10 min recovery. Most common (pointer out of sync) is <2 min: `git submodule update --init --recursive`"

**Q: "How do I know if Framework is outdated?"**
A: "Run `git submodule status`. Look for prefixes:
- `-` = uninitialized (need `git submodule init`)
- `+` = modified/outdated (need `git submodule update`)
- ` ` (no prefix) = clean, up-to-date"

---

## ✅ SUCCESS CRITERIA (Instructor Assessment)

**Lab 1 Success:**
- 9/9 students can clone with `--recurse-submodules` flag
- 9/9 students verify Framework initialized (no "-" prefix)
- <2 students need troubleshooting help

**Lab 2 Success:**
- 9/9 students understand `git pull` doesn't update Framework
- 9/9 students can run `git submodule update` successfully
- <3 students need troubleshooting help

**Lab 3 Success:**
- 9/9 students understand two-step commit workflow
- 7/9+ students can execute both steps (push failures OK)
- <4 students need troubleshooting help

**Overall Success:**
- 100% attendance (9/9 developers)
- 100% hands-on participation
- <30% need instructor intervention per lab

---

## 📋 INSTRUCTOR NOTES

**Timing Management:**
- If lab runs over 10 min, cut Q&A short (move to post-workshop Slack)
- If lab finishes early (<8 min), add bonus challenge (see below)
- Stay on schedule - quiz MUST start at 77-minute mark

**Bonus Challenges (If Time Permits):**

**Lab 1 Bonus:**
```bash
# Challenge: Clone with depth 1 (faster for large repos)
git clone --recurse-submodules --depth 1 https://...
```

**Lab 2 Bonus:**
```bash
# Challenge: Update to specific Framework commit
cd SDLC-Enterprise-Framework
git checkout abc1234
cd ..
git add SDLC-Enterprise-Framework
git commit -m "chore: Pin Framework to abc1234"
```

**Lab 3 Bonus:**
```bash
# Challenge: Work on Framework feature branch
cd SDLC-Enterprise-Framework
git checkout -b feature/my-template
# ... make changes
git commit -m "feat: Add template"
git push origin feature/my-template
# Create PR in Framework repo
```

**Troubleshooting Escalation:**
- 1-2 students stuck: Help individually (don't block others)
- 3+ students stuck: Pause lab, demo fix on projector
- 5+ students stuck: Issue with lab instructions (fix before next session)

---

**Document Owner:** PM/PO (Workshop Instructor)
**Created:** December 9, 2025
**Status:** READY FOR USE
**First Use:** Dec 10, 2025 (Session 1, 10:00 AM)

---

**Instructor Checklist (Print This):**
- [ ] Increase terminal font size (18-20pt)
- [ ] Clean Desktop (remove old DEMO directories)
- [ ] Test SSH/HTTPS authentication
- [ ] Prepare 2-terminal layout (side-by-side)
- [ ] Verify projector resolution (1920×1080 recommended)
- [ ] Print this demo script (3 pages)
- [ ] Announce: "Put phones on silent, laptops only"
- [ ] Set 10-minute timer for each lab

---

**Post-Workshop:**
- [ ] Collect lab completion stats (how many succeeded per lab)
- [ ] Document common issues for next session
- [ ] Share troubleshooting tips on Slack
- [ ] Update demo scripts if needed (for Session 2)
