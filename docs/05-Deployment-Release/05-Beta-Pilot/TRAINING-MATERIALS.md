# SDLC Orchestrator Training Materials

## Beta Pilot Training Program

**Version**: 1.0.0
**Date**: December 2025
**Status**: ACTIVE - Beta Pilot
**Audience**: Pilot Team Members (5-8 teams)

---

## Table of Contents

1. [Quick Reference Cards](#quick-reference-cards)
2. [Video Tutorial Scripts](#video-tutorial-scripts)
3. [Hands-On Exercises](#hands-on-exercises)
4. [Assessment Checklist](#assessment-checklist)
5. [Common Workflows](#common-workflows)

---

## Quick Reference Cards

### Card 1: Authentication & First Login

```
┌─────────────────────────────────────────────────────────────┐
│  🔐 AUTHENTICATION QUICK REFERENCE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LOGIN URL: http://localhost:3000/login                     │
│                                                             │
│  FIRST TIME LOGIN:                                          │
│  1. Enter email from welcome email                          │
│  2. Enter temporary password                                │
│  3. Change password (12+ chars, 1 uppercase, 1 number)      │
│  4. Complete profile                                        │
│                                                             │
│  OAUTH OPTIONS:                                             │
│  • GitHub (recommended for developers)                      │
│  • Google (enterprise accounts)                             │
│                                                             │
│  FORGOT PASSWORD:                                           │
│  1. Click "Forgot Password"                                 │
│  2. Enter email                                             │
│  3. Check inbox for reset link                              │
│  4. Link expires in 24 hours                                │
│                                                             │
│  NEED HELP? #sdlc-pilot-support on Slack                   │
└─────────────────────────────────────────────────────────────┘
```

### Card 2: Dashboard Navigation

```
┌─────────────────────────────────────────────────────────────┐
│  📊 DASHBOARD QUICK REFERENCE                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MAIN NAVIGATION:                                           │
│  ┌─────────┐                                                │
│  │ 🏠 Home │ → Overview, recent activity                    │
│  │ 📁 Proj │ → Your projects list                          │
│  │ 🚪 Gate │ → Gate status and evaluations                 │
│  │ 📎 Evid │ → Evidence vault                              │
│  │ 📋 Comp │ → Compliance dashboard                        │
│  │ ⚙️ Sett │ → Account settings                            │
│  └─────────┘                                                │
│                                                             │
│  PROJECT CARD:                                              │
│  ┌────────────────────────────┐                             │
│  │ Project Name         [→]  │ ← Click to view details     │
│  │ Stage: 02 - Design        │                             │
│  │ ████████░░ 80%           │ ← Gate progress              │
│  │ 3 pending | 2 approved   │ ← Gate status                │
│  └────────────────────────────┘                             │
│                                                             │
│  KEYBOARD SHORTCUTS:                                        │
│  • Cmd/Ctrl + K → Quick search                             │
│  • G + P → Go to Projects                                   │
│  • G + G → Go to Gates                                      │
│  • G + E → Go to Evidence                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Card 3: Gate Evaluation

```
┌─────────────────────────────────────────────────────────────┐
│  🚪 GATE EVALUATION QUICK REFERENCE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  GATE STATUSES:                                             │
│  • 🟢 APPROVED  - Gate passed, proceed to next stage       │
│  • 🟡 PENDING   - Awaiting evidence or review              │
│  • 🔴 BLOCKED   - Missing requirements, action needed      │
│  • ⚪ NOT STARTED - Future gate                            │
│                                                             │
│  TO REQUEST EVALUATION:                                     │
│  1. Navigate to gate details page                          │
│  2. Review exit criteria checklist                         │
│  3. Upload required evidence                               │
│  4. Click "Request Evaluation"                             │
│  5. Wait for reviewer notification                         │
│                                                             │
│  EVALUATION CRITERIA:                                       │
│  • Minimum score: 80% (configurable)                       │
│  • All MUST-HAVE items required                            │
│  • Evidence integrity verified (SHA256)                    │
│                                                             │
│  COMMON GATES:                                              │
│  Stage 00: G0.1 Problem Validation, G0.2 Solution Diversity│
│  Stage 01: G1.1 Requirements Complete, G1.2 Tech Feasible  │
│  Stage 02: G2.1 Architecture Review, G2.2 Security Base    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Card 4: Evidence Upload

```
┌─────────────────────────────────────────────────────────────┐
│  📎 EVIDENCE UPLOAD QUICK REFERENCE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SUPPORTED FORMATS:                                         │
│  • Documents: PDF, DOCX, MD, TXT                           │
│  • Images: PNG, JPG, GIF (screenshots)                     │
│  • Data: JSON, YAML, CSV                                   │
│  • Archives: ZIP (for multiple files)                      │
│                                                             │
│  MAX FILE SIZE: 50MB per file                              │
│                                                             │
│  UPLOAD METHODS:                                            │
│  1. Web Dashboard:                                          │
│     Gate Details → "Upload Evidence" → Select files        │
│                                                             │
│  2. API:                                                    │
│     POST /api/v1/evidence/upload                           │
│     Content-Type: multipart/form-data                      │
│                                                             │
│  3. VS Code Extension (coming soon):                       │
│     Cmd+Shift+E → Select file → Submit                     │
│                                                             │
│  EVIDENCE REQUIREMENTS:                                     │
│  • Title: Descriptive name (required)                      │
│  • Description: What this evidence proves                  │
│  • Gate: Which gate this supports                          │
│  • Tags: Optional categorization                           │
│                                                             │
│  VERIFICATION:                                              │
│  • SHA256 hash calculated automatically                    │
│  • Immutable once uploaded                                 │
│  • Audit trail maintained                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Card 5: Compliance Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  📋 COMPLIANCE DASHBOARD QUICK REFERENCE                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  COMPLIANCE SCORE:                                          │
│  • 90-100%: 🟢 Excellent - All requirements met            │
│  • 70-89%:  🟡 Good - Minor issues to address              │
│  • 50-69%:  🟠 Needs Work - Action required                │
│  • <50%:    🔴 Critical - Immediate attention              │
│                                                             │
│  DASHBOARD SECTIONS:                                        │
│  ┌─────────────────────────────────────────┐                │
│  │ Overall Score     │ Trend Chart        │                │
│  ├───────────────────┼────────────────────┤                │
│  │ Violations List   │ AI Provider Status │                │
│  └─────────────────────────────────────────┘                │
│                                                             │
│  VIOLATION PRIORITIES:                                      │
│  • P0 Critical: Security, legal, data integrity            │
│  • P1 High: Process compliance, gate requirements          │
│  • P2 Medium: Best practices, documentation                │
│  • P3 Low: Style, optional improvements                    │
│                                                             │
│  ACTIONS:                                                   │
│  • "Trigger Scan" - Run manual compliance check            │
│  • "View Details" - See violation specifics                │
│  • "Resolve" - Mark violation as fixed                     │
│  • "Export" - Download compliance report                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Video Tutorial Scripts

### Video 1: Getting Started (5 minutes)

**Title**: Welcome to SDLC Orchestrator

**Script**:

```
[0:00-0:30] INTRO
"Welcome to SDLC Orchestrator, the governance-first platform that helps
your team build better software by enforcing quality gates and collecting
evidence throughout your development lifecycle.

In this tutorial, we'll walk through your first login, dashboard overview,
and basic navigation."

[0:30-1:30] FIRST LOGIN
"Let's start by logging in. Open your browser and go to the login URL
from your welcome email.

Enter your email address and temporary password. You'll be prompted to
change your password - choose something secure with at least 12 characters.

Alternatively, you can use OAuth to sign in with GitHub or Google.
This is recommended for developers as it enables GitHub integration."

[1:30-3:00] DASHBOARD OVERVIEW
"Once logged in, you'll see the main dashboard. Let's explore:

- The left sidebar shows main navigation: Home, Projects, Gates, Evidence,
  Compliance, and Settings.

- The home screen shows your recent activity and quick stats.

- Project cards display your active projects with gate progress indicators.

- The top bar has quick search (Cmd+K) and your profile menu."

[3:00-4:30] NAVIGATION
"Let's look at keyboard shortcuts to speed up your workflow:

- Press G then P to go to Projects
- Press G then G to go to Gates
- Press G then E to go to Evidence

Use Cmd+K or Ctrl+K for quick search across all projects and gates."

[4:30-5:00] WRAP UP
"That's it for getting started! In the next video, we'll dive deeper
into gate evaluations and evidence uploads.

If you have questions, reach out on Slack #sdlc-pilot-support or
email support@sdlc-orchestrator.io."
```

### Video 2: Working with Gates (7 minutes)

**Title**: Understanding Gates and Evaluations

**Script**:

```
[0:00-0:45] INTRO
"Gates are the core of SDLC Orchestrator. They act as quality checkpoints
throughout your development lifecycle, ensuring your team follows proven
practices before moving to the next stage.

In this tutorial, you'll learn how gates work, how to request evaluations,
and how to resolve blocked gates."

[0:45-2:00] GATE OVERVIEW
"Navigate to Gates using the sidebar or press G then G.

You'll see all gates for your projects organized by stage:
- Stage 00: Problem Definition gates
- Stage 01: Planning gates
- Stage 02: Design gates
- And so on through Stage 10

Each gate shows:
- Status: Approved, Pending, Blocked, or Not Started
- Exit criteria: What's required to pass
- Evidence: Documents uploaded to support the gate"

[2:00-4:00] REQUESTING EVALUATION
"Let's request an evaluation for a pending gate.

1. Click on the gate card to open details
2. Review the exit criteria checklist
3. Ensure you have uploaded all required evidence
4. Click 'Request Evaluation'

The system will:
- Validate evidence completeness
- Run policy checks against your submissions
- Calculate a compliance score
- Notify designated reviewers

You'll receive a notification when the evaluation is complete."

[4:00-5:30] HANDLING BLOCKED GATES
"If a gate is blocked, don't panic. Here's how to resolve it:

1. Open the blocked gate details
2. Review the 'Blocking Issues' section
3. Each issue shows:
   - What's missing or non-compliant
   - Suggested remediation
   - Priority level

4. Address each issue by uploading evidence or making changes
5. Re-request evaluation once issues are resolved

Common blocking reasons:
- Missing required evidence
- Policy violations
- Incomplete documentation
- Failed automated checks"

[5:30-6:30] GATE BEST PRACTICES
"Some tips for smooth gate passages:

1. Start early - don't wait until the end of a stage
2. Use templates - we provide templates for common evidence
3. Check policies first - understand requirements before starting work
4. Communicate - use comments to discuss with reviewers
5. Track progress - the dashboard shows gate health over time"

[6:30-7:00] WRAP UP
"You now understand how gates work in SDLC Orchestrator.

Next, we'll cover evidence management in detail.

Questions? #sdlc-pilot-support on Slack."
```

### Video 3: Evidence Management (6 minutes)

**Title**: Uploading and Managing Evidence

**Script**:

```
[0:00-0:30] INTRO
"Evidence is the proof that your team has met gate requirements.
SDLC Orchestrator provides a secure Evidence Vault with SHA256
integrity verification and full audit trails.

Let's learn how to upload, organize, and manage your evidence."

[0:30-2:00] UPLOADING EVIDENCE
"Navigate to Evidence in the sidebar or press G then E.

To upload:
1. Click 'Upload Evidence'
2. Drag and drop files or click to browse
3. Fill in the metadata form:
   - Title: A descriptive name
   - Description: What this evidence proves
   - Gate: Which gate this supports
   - Tags: Optional categorization

4. Click 'Upload'

Supported formats include PDF, DOCX, images, and data files.
Maximum size is 50MB per file."

[2:00-3:30] EVIDENCE INTEGRITY
"Every piece of evidence gets a SHA256 hash calculated at upload time.

This ensures:
- Tamper detection: Any modification is detected
- Audit compliance: Proof of authenticity for auditors
- Traceability: Full history of who uploaded what and when

You can verify integrity anytime by clicking 'Verify' on any evidence item.

The system also maintains an immutable audit log of all evidence actions."

[3:30-5:00] ORGANIZING EVIDENCE
"As your project grows, organization becomes important.

Use these features:
- Tags: Create consistent tags like 'security', 'design', 'testing'
- Filters: Filter by gate, stage, type, or date
- Search: Full-text search across titles and descriptions
- Bulk actions: Select multiple items for tagging or moving

Pro tip: Establish team conventions for naming and tagging early.
For example:
- '[Stage]-[Gate]-[Description]'
- 'S02-G2.1-Architecture-Diagram-v2'"

[5:00-5:45] API ACCESS
"For automation, use the Evidence API:

Upload:
POST /api/v1/evidence/upload
- multipart/form-data with file and metadata

List:
GET /api/v1/evidence
- Query parameters for filtering

Verify:
GET /api/v1/evidence/{id}/verify
- Returns integrity check result

See the API documentation for full details."

[5:45-6:00] WRAP UP
"You're now ready to manage evidence effectively.

Next video covers the Compliance Dashboard.

Questions? #sdlc-pilot-support on Slack."
```

---

## Hands-On Exercises

### Exercise 1: First Login & Profile Setup (10 minutes)

**Objective**: Complete initial login and configure your profile.

**Steps**:

1. **Login**
   - Open http://localhost:3000/login
   - Enter credentials from welcome email
   - Change password when prompted

2. **Complete Profile**
   - Navigate to Settings > Profile
   - Upload a profile picture
   - Set your display name
   - Configure notification preferences

3. **Connect GitHub (Optional)**
   - Go to Settings > Integrations
   - Click "Connect GitHub"
   - Authorize the OAuth app
   - Select repositories to sync

**Verification Checklist**:
- [ ] Successfully logged in
- [ ] Password changed
- [ ] Profile picture uploaded
- [ ] Display name set
- [ ] Notification preferences configured
- [ ] GitHub connected (optional)

---

### Exercise 2: Navigate Your First Project (15 minutes)

**Objective**: Explore a project's gates and understand stage progression.

**Steps**:

1. **Open Project**
   - Go to Projects
   - Click on your assigned pilot project
   - Review the project overview

2. **Explore Stages**
   - Click through each stage tab (00-10)
   - Note which gates exist in each stage
   - Identify current stage based on gate statuses

3. **View Gate Details**
   - Open a gate marked as "Pending"
   - Read the exit criteria
   - Note what evidence is required
   - Check if any evidence exists

4. **Review Evidence**
   - Click on any existing evidence
   - Read the description
   - Click "Verify" to check integrity

**Questions to Answer**:
1. What stage is your project currently in?
2. How many gates are approved vs pending?
3. What evidence is missing for the next gate?

---

### Exercise 3: Upload Your First Evidence (20 minutes)

**Objective**: Upload evidence and link it to a gate.

**Steps**:

1. **Prepare Evidence**
   - Create a simple document (e.g., meeting notes in Markdown)
   - Or use a screenshot of your project planning

2. **Upload**
   - Navigate to Evidence > Upload
   - Select your file
   - Fill in metadata:
     - Title: "Exercise 3 - Sample Evidence"
     - Description: "Test evidence upload for training"
     - Gate: Select a pending gate
     - Tags: "training", "exercise"

3. **Verify Upload**
   - Find your evidence in the list
   - Click to view details
   - Verify the SHA256 hash is present
   - Check the audit log shows your upload

4. **Link to Gate**
   - Go to the gate you selected
   - Confirm your evidence appears in the gate's evidence list

**Verification Checklist**:
- [ ] Evidence uploaded successfully
- [ ] Metadata complete and accurate
- [ ] SHA256 hash visible
- [ ] Evidence linked to gate
- [ ] Audit log entry present

---

### Exercise 4: Request Gate Evaluation (25 minutes)

**Objective**: Complete a gate evaluation request workflow.

**Steps**:

1. **Select a Gate**
   - Choose a gate with status "Pending"
   - Ensure it has at least one evidence item

2. **Review Exit Criteria**
   - Read each requirement carefully
   - Check off items you have evidence for
   - Note any gaps

3. **Upload Missing Evidence** (if needed)
   - Create placeholder documents for training
   - Upload and link to the gate

4. **Request Evaluation**
   - Click "Request Evaluation"
   - Add a comment explaining your submission
   - Submit the request

5. **Check Status**
   - Refresh the page
   - Note the status change to "Under Review"
   - Check notifications for updates

**Expected Outcome**:
- Gate status changes to "Under Review"
- Notification sent to reviewers
- Your activity logged in audit trail

---

### Exercise 5: Use the Compliance Dashboard (15 minutes)

**Objective**: Navigate the compliance dashboard and understand scores.

**Steps**:

1. **Open Compliance**
   - Navigate to Compliance in sidebar
   - View overall compliance score

2. **Explore Charts**
   - Look at the Compliance Score Trend chart
   - Identify any dips or improvements over time

3. **Review Violations**
   - Click on any violation in the list
   - Read the details and remediation suggestions
   - Understand the priority level

4. **Trigger a Scan**
   - Click "Trigger Scan" button
   - Wait for scan to complete
   - Note any changes in score

5. **Export Report**
   - Click "Export" to download compliance report
   - Review the PDF/CSV output

**Questions to Answer**:
1. What is your project's current compliance score?
2. Are there any P0 or P1 violations?
3. What's the trend direction over the last week?

---

## Assessment Checklist

### Self-Assessment: Ready for Production Use

Complete this checklist to verify you're ready to use SDLC Orchestrator effectively:

#### Authentication & Access
- [ ] I can log in successfully
- [ ] I have changed my password from the temporary one
- [ ] I know how to use OAuth login (if applicable)
- [ ] I know where to find my API tokens

#### Navigation
- [ ] I can navigate to all main sections (Projects, Gates, Evidence, Compliance)
- [ ] I know keyboard shortcuts for quick navigation
- [ ] I can use the quick search feature

#### Gates
- [ ] I understand what gates are and their purpose
- [ ] I can view gate details and exit criteria
- [ ] I know the different gate statuses
- [ ] I can request a gate evaluation
- [ ] I understand how to resolve blocked gates

#### Evidence
- [ ] I can upload evidence files
- [ ] I understand evidence metadata (title, description, tags)
- [ ] I know how to link evidence to gates
- [ ] I can verify evidence integrity
- [ ] I understand the audit trail

#### Compliance
- [ ] I can read the compliance score
- [ ] I understand violation priorities (P0-P3)
- [ ] I can trigger a compliance scan
- [ ] I can export compliance reports

#### Support
- [ ] I know how to submit feedback
- [ ] I know the Slack support channel
- [ ] I know the support email address
- [ ] I know when office hours are held

---

## Common Workflows

### Workflow 1: Starting a New Project Stage

```
1. Review current stage gates
   └── All gates should be APPROVED

2. Create stage kick-off document
   └── Upload as evidence for next stage

3. Review next stage requirements
   └── Gates > Select stage > View exit criteria

4. Plan evidence collection
   └── Create tasks for each required evidence

5. Begin stage work
   └── Update project status in dashboard
```

### Workflow 2: Preparing for Gate Evaluation

```
1. Review gate exit criteria
   └── Gates > Select gate > Exit Criteria tab

2. Gather required evidence
   └── Documents, screenshots, data exports

3. Upload evidence
   └── Evidence > Upload > Link to gate

4. Self-check compliance
   └── Compliance > Trigger Scan

5. Request evaluation
   └── Gates > Select gate > Request Evaluation

6. Monitor status
   └── Notifications + Gate details page
```

### Workflow 3: Resolving a Blocked Gate

```
1. Review blocking issues
   └── Gates > Blocked gate > Blocking Issues

2. Prioritize by severity
   └── P0 > P1 > P2 > P3

3. Address each issue
   └── Upload missing evidence OR fix violations

4. Verify fixes
   └── Compliance > Trigger Scan

5. Re-request evaluation
   └── Gates > Request Evaluation
```

### Workflow 4: Daily Standup Check

```
1. Check dashboard (30 seconds)
   └── Home > Recent activity + stats

2. Review gate status (1 minute)
   └── Any blocked gates? New approvals?

3. Check compliance score (30 seconds)
   └── Compliance > Score trend

4. Check notifications (30 seconds)
   └── Any pending reviews? Feedback?

5. Update team (during standup)
   └── "Gate X approved, working on evidence for Y"
```

---

## Additional Resources

### Documentation Links
- **Onboarding Guide**: [BETA-PILOT-ONBOARDING-GUIDE.md](./BETA-PILOT-ONBOARDING-GUIDE.md)
- **Support Channels**: [SUPPORT-CHANNELS-CONFIG.md](./SUPPORT-CHANNELS-CONFIG.md)
- **API Documentation**: http://localhost:8000/docs

### Support Contacts
- **Slack**: #sdlc-pilot-support
- **Email**: support@sdlc-orchestrator.io
- **Office Hours**: Thursdays 3-4pm (GMT+7)

### Feedback
- **In-App**: Click feedback button (bottom-right)
- **API**: POST /api/v1/feedback
- **GitHub**: sdlc-orchestrator/pilot-feedback

---

**Last Updated**: December 2025
**Owner**: Training & Enablement Team
**Status**: ACTIVE - Beta Pilot
