# Beta Pilot Onboarding Guide

## SDLC Orchestrator - Internal Beta Program

**Version**: 1.0.0
**Date**: December 2025
**Status**: ACTIVE - Beta Pilot
**Audience**: Pilot Team Members

---

## Welcome to SDLC Orchestrator Beta!

Congratulations on being selected for the SDLC Orchestrator internal beta program! This guide will help you get started quickly and make the most of the platform.

---

## Quick Start (5 Minutes)

### Step 1: Access the Platform

| Environment | URL | Status |
|-------------|-----|--------|
| **Staging** | http://localhost:3000 | Active |
| **API Docs** | http://localhost:8000/api/docs | Active |
| **Grafana** | http://localhost:3001 | Active |

### Step 2: Login

1. Navigate to http://localhost:3000/login
2. Enter your credentials:
   - **Email**: Your company email (e.g., `yourname@bflow.vn`)
   - **Password**: `Admin@123` (default for pilot accounts)
3. Click "Sign In"

### Step 3: Explore Your Dashboard

After login, you'll see:
- **Project Overview**: Your assigned projects and their status
- **Gate Status**: Current quality gates and compliance scores
- **Recent Activity**: Latest updates from your team

---

## Platform Features

### 1. Projects Management

**View Projects**
- Navigate to "Projects" in the sidebar
- See all projects you have access to
- Filter by status: Active, Completed, Archived

**Project Details**
- Click on a project to view details
- See project description, team members, and gates
- Track compliance score and risk level

### 2. Quality Gates

**Understanding Gates**
Gates are checkpoints that ensure quality at each SDLC stage:

| Stage | Gates | Purpose |
|-------|-------|---------|
| Stage 00 | G0.1, G0.2 | Problem Definition |
| Stage 01 | G1.1, G1.2 | Requirements & Planning |
| Stage 02 | G2.1, G2.2 | Design & Architecture |
| Stage 03 | G3.1, G3.2 | Development & Implementation |

**Gate Status**
- **Pending**: Awaiting review
- **Approved**: Passed all criteria
- **Rejected**: Needs revision
- **In Review**: Currently being evaluated

### 3. Evidence Vault

**Uploading Evidence**
1. Navigate to a specific gate
2. Click "Upload Evidence"
3. Select file(s) to upload
4. Add description and tags
5. Submit for review

**Supported File Types**
- Documents: PDF, DOCX, MD
- Images: PNG, JPG, SVG
- Code: ZIP archives
- Max file size: 50MB

### 4. Compliance Dashboard

**View Compliance Score**
- Overall score (0-100%)
- Score breakdown by category
- Trend over time

**Understanding Scores**
| Score Range | Status | Action |
|-------------|--------|--------|
| 90-100% | Excellent | Maintain |
| 70-89% | Good | Minor improvements |
| 50-69% | Fair | Review required |
| 0-49% | Critical | Immediate action |

---

## Pilot Team Projects

Your team has been assigned to one of these pilot projects:

| Project | Lead | Focus Area |
|---------|------|------------|
| BFlow Workflow Automation v3.0 | CTO | Workflow automation |
| NQH E-commerce Phase 2 | CPO | E-commerce platform |
| MTC Internal Tool | PM | Internal tooling |
| MTEP Platform | EM | Enterprise platform |

---

## Daily Workflow

### Morning (5 mins)
1. Check dashboard for notifications
2. Review any pending gate approvals
3. Check compliance score changes

### During Development
1. Document evidence as you work
2. Upload artifacts to relevant gates
3. Tag team members for reviews

### End of Day (5 mins)
1. Update gate progress
2. Submit any pending evidence
3. Review team notifications

---

## Common Tasks

### Task 1: Submit Gate Evidence

```
1. Go to Projects → Select Project → Gates
2. Click on the gate you want to update
3. Click "Add Evidence" button
4. Upload file and add description
5. Click "Submit"
```

### Task 2: Request Gate Approval

```
1. Ensure all required evidence is uploaded
2. Click "Request Approval" on the gate
3. Select approvers from your team
4. Add any notes or comments
5. Submit request
```

### Task 3: View Compliance Report

```
1. Go to Compliance in sidebar
2. Select date range
3. View score breakdown
4. Export report if needed (PDF/CSV)
```

---

## API Access (For Developers)

### Authentication

```bash
# Get access token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "your-password"}'
```

### Example API Calls

```bash
# List projects
curl http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get project details
curl http://localhost:8000/api/v1/projects/{project_id} \
  -H "Authorization: Bearer YOUR_TOKEN"

# List gates for a project
curl http://localhost:8000/api/v1/gates?project_id={project_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### API Documentation

Full API documentation available at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json

---

## Feedback & Support

### Providing Feedback

We value your input! Please share:
- **Bugs**: Issues you encounter
- **Feature Requests**: Ideas for improvement
- **UX Feedback**: Usability concerns

### Feedback Channels

| Channel | Purpose | Response Time |
|---------|---------|---------------|
| GitHub Issues | Bug reports | 24 hours |
| Slack #sdlc-pilot | Quick questions | 4 hours |
| Email | Detailed feedback | 48 hours |

### Bug Report Template

```markdown
**Summary**: Brief description of the issue

**Steps to Reproduce**:
1. Step 1
2. Step 2
3. ...

**Expected Behavior**: What should happen

**Actual Behavior**: What actually happens

**Screenshots**: If applicable

**Environment**:
- Browser: Chrome/Firefox/Safari
- OS: macOS/Windows/Linux
```

---

## FAQ

### Q: I forgot my password
**A**: Click "Forgot Password" on the login page, or contact admin@sdlc-orchestrator.io

### Q: I can't see my project
**A**: Check that you're logged in with the correct email. Contact your team lead if issue persists.

### Q: How do I add team members?
**A**: Project owners can add members via Project Settings → Team Members → Add Member

### Q: What file formats are supported for evidence?
**A**: PDF, DOCX, MD, PNG, JPG, SVG, ZIP (max 50MB per file)

### Q: How is compliance score calculated?
**A**: Score is based on: gate completion (40%), evidence quality (30%), policy adherence (30%)

### Q: Can I export my data?
**A**: Yes, go to Settings → Export Data to download your project data in JSON/CSV format

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Quick search |
| `Ctrl/Cmd + N` | New project |
| `Ctrl/Cmd + U` | Upload evidence |
| `Ctrl/Cmd + /` | Show shortcuts |
| `Esc` | Close modal |

---

## Resources

- **User Guide**: docs/USER-GUIDE.md
- **API Reference**: http://localhost:8000/api/docs
- **Architecture**: docs/02-Design-Architecture/System-Architecture-Document.md
- **Security**: docs/02-Design-Architecture/Security-Baseline.md

---

## Contact

| Role | Contact | Availability |
|------|---------|--------------|
| **Technical Support** | support@sdlc-orchestrator.io | Mon-Fri 9am-6pm |
| **Product Team** | product@sdlc-orchestrator.io | Mon-Fri 9am-6pm |
| **Emergency** | oncall@sdlc-orchestrator.io | 24/7 |

---

**Thank you for participating in our beta program!**

Your feedback will help shape the future of SDLC Orchestrator.

---

*Document Version: 1.0.0 | Last Updated: December 2025*
