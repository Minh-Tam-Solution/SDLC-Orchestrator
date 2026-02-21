# Beta Team Onboarding Guide

**Version**: 1.0.0
**Date**: November 27, 2025
**Status**: ACTIVE - Week 13 Production Launch
**Authority**: PM + CPO
**Framework**: SDLC 6.1.0
**Target Audience**: Internal MTS/NQH Beta Teams (5-8 teams)

---

## Welcome to SDLC Orchestrator Beta!

Congratulations on being selected as a **beta team** for SDLC Orchestrator - the first governance-first platform built on SDLC 6.1.0 methodology.

Your feedback will help us refine the product before public release.

---

## Quick Start (5 Minutes)

### Step 1: Access the Platform

**URL**: https://app.sdlc-orchestrator.com (or http://localhost:3000 for local)

**Login Options**:
- Email + Password (provided by admin)
- GitHub OAuth (recommended)
- Google OAuth
- Microsoft OAuth

### Step 2: First Login

1. Navigate to the login page
2. Enter your credentials or click OAuth provider
3. Complete MFA setup (optional but recommended)
4. You'll be redirected to the Dashboard

### Step 3: Connect GitHub Repository (Recommended)

1. Click "Connect GitHub" in the onboarding wizard
2. Authorize SDLC Orchestrator to access your repositories (read-only)
3. Select a repository from the list
4. The system will automatically:
   - Analyze your repository structure
   - Detect project type (FastAPI, React, Node, etc.)
   - Recommend a policy pack (Lite/Standard/Enterprise)
   - Map folders to SDLC 6.1.0 stages
   - Create your first project

**Alternative**: You can also create a project manually without GitHub connection.

### Step 4: Create Your First Project (Manual)

1. Click "Projects" in the sidebar
2. Click "New Project" button
3. Fill in:
   - **Name**: Your project name
   - **Description**: Brief description
   - **Repository URL**: GitHub repo (optional)
4. Click "Create"

### Step 5: Set Up Your First Gate

1. Go to your project
2. Click "Gates" tab
3. Click "New Gate"
4. Select gate type:
   - G0.1: Problem Definition
   - G0.2: Solution Diversity
   - G1: Legal + Market Validation
   - G2: Design Ready
5. Click "Create Gate"

### Step 6: Submit Evidence

1. Go to your gate
2. Click "Upload Evidence"
3. Select files (documents, images, code)
4. Add description
5. Click "Submit"

---

## Core Features

### 1. Dashboard

The dashboard provides an overview of:
- Active projects count
- Pending gates
- Recent activities
- Gate pass rate

### 2. Projects

Projects are the top-level container for your work:
- Create unlimited projects
- Invite team members
- Track progress across gates

### 3. Gates

Gates are quality checkpoints:
- 10 gate types (G0.1 to G6)
- Evidence collection
- Approval workflow
- Automatic notifications

### 4. Evidence Vault

Secure storage for your evidence:
- SHA256 integrity verification
- Audit trail
- Search by metadata
- Export functionality

### 5. Policy Engine

Automated policy evaluation:
- 110+ pre-built policies
- Custom policy support
- Real-time validation
- OPA (Open Policy Agent) powered

---

## SDLC 6.1.0 Gate Overview

| Gate | Stage | Purpose | Evidence Required |
|------|-------|---------|-------------------|
| G0.1 | WHY | Problem Definition | User interviews, market research |
| G0.2 | WHY | Solution Diversity | Solution comparison matrix |
| G1 | WHAT | Legal + Market | Legal brief, LOIs, competition analysis |
| G2 | HOW | Design Ready | Architecture docs, API spec, security plan |
| G3 | BUILD | Ship Ready | Working code, tests, documentation |
| G4 | TEST | Verified | Test results, security audit |
| G5 | LAUNCH | Production Ready | Deployment plan, runbooks |
| G6 | OPERATE | Internal Validation | Usage metrics, NPS scores |

---

## Beta Program Expectations

### What We Need From You

1. **Daily Usage**: Use the platform for your actual projects
2. **Feedback**: Report bugs, suggest features
3. **Documentation**: Note any confusing areas
4. **NPS Survey**: Weekly survey (2 minutes)

### What You Get

1. **Early Access**: Shape the product before release
2. **Priority Support**: Direct Slack channel
3. **Influence**: Feature requests prioritized
4. **Recognition**: Beta team credits in launch

### Feedback Channels

| Channel | Purpose | Response Time |
|---------|---------|---------------|
| Slack #sdlc-beta | Questions, bugs | <2 hours |
| GitHub Issues | Bug reports | <24 hours |
| Weekly Survey | Feature requests | Weekly review |
| Email support@sdlc-orchestrator.com | Urgent issues | <4 hours |

---

## Common Workflows

### Workflow 1: Starting a New Feature

```
1. Create Project
2. Set up G0.1 (Problem Definition) gate
3. Conduct user interviews
4. Upload interview notes as evidence
5. Submit for gate approval
6. Once approved, proceed to G0.2
7. Continue through gates...
```

### Workflow 2: Existing Project Migration

```
1. Create Project (link existing GitHub repo)
2. Import existing documentation as evidence
3. Set up appropriate gate (based on current stage)
4. Upload relevant artifacts
5. Request gate review
```

### Workflow 3: Gate Review Process

```
1. Reviewer receives notification
2. Review evidence in Evidence Vault
3. Check policy evaluation results
4. Approve / Request Changes / Reject
5. Submitter notified of decision
```

---

## Troubleshooting

### Issue: Can't Login

**Solution**:
1. Check email/password correct
2. Try "Forgot Password" link
3. Clear browser cache
4. Try different OAuth provider
5. Contact support if persists

### Issue: File Upload Fails

**Solution**:
1. Check file size (<50MB)
2. Check file type supported
3. Check network connection
4. Try different browser
5. Contact support if persists

### Issue: Gate Evaluation Pending

**Solution**:
1. Check all required evidence uploaded
2. Check policy requirements met
3. Contact reviewer via Slack
4. Check for system notifications

---

## API Access (Advanced)

For teams wanting to integrate via API:

### Authentication

```bash
# Login to get token
curl -X POST https://api.sdlc-orchestrator.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"your-password"}'

# Response contains access_token
```

### Create Project

```bash
curl -X POST https://api.sdlc-orchestrator.com/api/v1/projects \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Project","description":"Description"}'
```

### Full API Documentation

- Swagger UI: https://api.sdlc-orchestrator.com/docs
- ReDoc: https://api.sdlc-orchestrator.com/redoc
- OpenAPI Spec: https://api.sdlc-orchestrator.com/openapi.json

---

## Support Contacts

| Role | Name | Contact |
|------|------|---------|
| Product Manager | TBD | Slack: @pm |
| Technical Lead | TBD | Slack: @tech-lead |
| Support | Support Team | support@sdlc-orchestrator.com |

### Escalation Path

1. **Level 1**: Slack #sdlc-beta (respond <2h)
2. **Level 2**: Direct message to PM (respond <4h)
3. **Level 3**: Email CTO/CPO (respond <24h)

---

## Beta Timeline

| Week | Activity |
|------|----------|
| Week 1 | Onboarding, first project setup |
| Week 2 | Active usage, initial feedback |
| Week 3 | Feature requests collection |
| Week 4 | Final survey, graduation to GA |

---

## FAQ

**Q: Is my data secure?**
A: Yes. All data is encrypted at rest (AES-256) and in transit (TLS 1.3). We follow SOC 2 Type I controls.

**Q: Can I invite external collaborators?**
A: Beta is internal only. External access will be available at GA.

**Q: What happens to my data after beta?**
A: All data is preserved. You'll continue using the same account.

**Q: How do I request a new feature?**
A: Submit via Slack #sdlc-beta or weekly survey.

**Q: Is there a mobile app?**
A: Not yet. The web app is responsive and works on mobile browsers.

---

## Acknowledgments

Thank you for participating in the SDLC Orchestrator beta program!

Your feedback is invaluable in building the first governance-first platform on SDLC 6.1.0.

---

*This document is part of the SDLC 6.1.0 Complete Lifecycle documentation.*

**Generated**: November 27, 2025
**Version**: 1.0.0
**Next Update**: After Week 1 feedback
