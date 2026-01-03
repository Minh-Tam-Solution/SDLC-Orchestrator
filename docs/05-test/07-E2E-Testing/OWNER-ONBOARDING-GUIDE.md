# Owner Onboarding Guide - SDLC Orchestrator

## Overview

This guide documents the onboarding flow for the first project owner on SDLC Orchestrator.

**Test Date**: December 29, 2025
**Sprint**: 60 - i18n Localization + OAuth Fix
**Status**: Ready for Testing

---

## Prerequisites

### Platform State
- Database reset with clean start seed data
- Platform Admin account active: `admin@sdlc-orchestrator.io` / `Admin@123`
- No existing projects or users (except admin)

### First Owner Details
- **Email**: dangtt1971@gmail.com
- **Project**: Endior Translator
- **Local Path**: `/Users/dttai/Documents/Python/Endior Translator/`
- **Authentication**: GitHub OAuth or Email Registration

---

## Onboarding Flow

### Step 1: Access Platform

1. Navigate to https://sdlc.nhatquangholding.com
2. Click "Get Started" or "Login"

### Step 2: Register/Login

#### Option A: GitHub OAuth (Recommended)
1. Click "Continue with GitHub" button
2. Authorize SDLC Orchestrator on GitHub
3. Wait for redirect back to dashboard

#### Option B: Email Registration
1. Click "Create an account"
2. Enter email: `dangtt1971@gmail.com`
3. Enter name: `Endior` (or full name)
4. Create password (min 12 characters)
5. Submit registration
6. Check email for verification (if enabled)
7. Login with credentials

### Step 3: Create First Project

1. After login, click "Create Project" or "New Project"
2. Fill project details:
   - **Name**: Endior Translator
   - **Description**: AI-powered translation application for Vietnamese-English
   - **Repository URL**: (optional - link GitHub repo if available)
   - **Tier**: STANDARD (recommended for SME projects)
3. Click "Create Project"

### Step 4: Configure Project

1. Set SDLC stage: 03-BUILD (Development phase)
2. Configure gates based on SDLC 5.1.2 framework:
   - G0.1: Problem Definition (if applicable)
   - G0.2: Solution Diversity (if applicable)
   - G1: Requirements Approval
   - G2: Architecture Approval
   - G3: Code Review Approval
3. Invite team members (optional)

### Step 5: Upload Evidence

1. Navigate to project gate
2. Click "Upload Evidence"
3. Select evidence type:
   - DOCUMENT: Requirements, Architecture docs
   - CODE: Source files, tests
   - LINK: External resources
4. Upload files from local project:
   - `/Users/dttai/Documents/Python/Endior Translator/`

---

## Expected Results

After successful onboarding:

| Item | Expected State |
|------|----------------|
| User Account | Active, role: Owner |
| Project | Created, stage: BUILD |
| Gates | Configured per SDLC tier |
| Evidence | Ready for upload |

---

## Troubleshooting

### OAuth "Invalid State Parameter" Error
**Issue**: Error when returning from GitHub OAuth in Incognito mode
**Fix**: This was fixed in Sprint 60 by changing from `sessionStorage` to `localStorage`
**Status**: RESOLVED

### Login Fails After Registration
**Check**:
1. Email verification completed (if enabled)
2. Correct password entered
3. Account is active in database

### Project Creation Fails
**Check**:
1. User has Owner role permissions
2. All required fields filled
3. Backend service healthy: `docker compose ps backend`

---

## Database Verification

Run these queries to verify onboarding state:

```sql
-- Check users
SELECT email, name, is_active, created_at FROM users;

-- Check projects
SELECT name, stage, tier, owner_id, created_at FROM projects;

-- Check project members
SELECT u.email, pm.role, p.name as project
FROM project_members pm
JOIN users u ON pm.user_id = u.id
JOIN projects p ON pm.project_id = p.id;
```

---

## Reset for Re-testing

To reset database and start fresh:

```bash
./scripts/reset-database.sh
```

This will:
1. Drop and recreate database
2. Run all migrations
3. Apply clean start seed data (admin only)

---

## Related Documents

- [CLEAN-START-SEED-DATA.sql](./CLEAN-START-SEED-DATA.sql) - Database seed script
- [CURRENT-SPRINT.md](../../04-build/02-Sprint-Plans/CURRENT-SPRINT.md) - Sprint 60 details
- [ADR-024-Frontend-Architecture.md](../../02-design/01-ADRs/ADR-024-Frontend-Architecture-Dual-vs-Monolithic.md) - Dual frontend architecture

---

**Last Updated**: December 29, 2025
**Author**: AI Assistant (Claude)
**Status**: Ready for Manual Testing
