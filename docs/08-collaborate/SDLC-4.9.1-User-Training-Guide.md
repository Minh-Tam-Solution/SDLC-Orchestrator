# SDLC Orchestrator - User Training Guide
## Apply SDLC 5.1.3.1 Framework Through the Platform

**Version**: 1.0.0
**Date**: November 29, 2025
**Status**: ACTIVE - USER TRAINING DOCUMENT
**Authority**: CPO + CTO Approved
**Platform**: SDLC Orchestrator - Project Governance Tool

---

## Mục Tiêu Tài Liệu

Tài liệu này hướng dẫn bạn **sử dụng SDLC Orchestrator** để **áp dụng SDLC 5.1.3.1 Framework** vào dự án phần mềm của bạn.

**Sau khi hoàn thành, bạn sẽ:**
- Hiểu cách SDLC Orchestrator enforce 10-stage lifecycle
- Biết cách tạo project và invite team members
- Biết cách submit evidence và request gate approvals
- Hiểu role-based collaboration trong platform

---

## 1. Tại Sao Cần SDLC Orchestrator?

### 1.1 Vấn Đề Với Manual SDLC Enforcement

Khi áp dụng SDLC 5.1.3.1 **manual** (không có tool), team cần:

```yaml
Manual Oversight Required:

  CPO/CTO phải manually:
    - Check mỗi stage có đủ evidence không
    - Đảm bảo team không skip stages
    - Track ai approve cái gì khi nào
    - Enforce role-based approvals
    - Maintain audit trail trong spreadsheet

  Problems:
    ❌ Human error: Quên check, bỏ sót stages
    ❌ Time consuming: Leadership spend 30-40% time oversight
    ❌ No enforcement: Team có thể bypass khi leadership busy
    ❌ Audit gaps: Spreadsheet không đủ detail cho compliance
    ❌ Scale issue: Không quản lý được 10+ projects
```

### 1.2 SDLC Orchestrator - Automated Enforcement

```yaml
Platform Solves:

  ✅ Auto-enforcement: Platform block actions khi rules violated
  ✅ Zero human oversight needed: Rules built into system
  ✅ Scalable: 100+ projects, same enforcement quality
  ✅ Complete audit: Every action logged automatically
  ✅ Role-based: System validates before accepting

  Leadership time saved: 30-40% → 5%
  Compliance confidence: 70% → 99%
```

### 1.3 So Sánh Manual vs Platform

| Aspect | Manual (NQH hiện tại) | SDLC Orchestrator |
|--------|----------------------|-------------------|
| Stage enforcement | CPO/CTO manually check | Platform auto-blocks |
| Evidence tracking | Spreadsheet/Drive | Centralized in platform |
| Role validation | Manager verifies | System validates |
| Audit trail | Manual logging | Automatic, immutable |
| Skip prevention | Trust-based | System-enforced |
| Scale | 3-5 projects max | 100+ projects |
| Human oversight | 30-40% leadership time | 5% (exceptions only) |

---

## 2. SDLC Orchestrator Enforce SDLC 5.1.3.1 Như Thế Nào?

### 1.1 Platform Không Cho Phép Bỏ Qua

SDLC Orchestrator được thiết kế để **enforce** - không chỉ **suggest** - SDLC 5.1.3.1:

```yaml
Enforcement Rules:

  1. Sequential Stages:
     - Bạn KHÔNG THỂ bắt đầu Stage 04 (BUILD) nếu Stage 02 (HOW) chưa pass
     - Platform block hành động nếu gate trước chưa approved

  2. Evidence Required:
     - Mỗi gate yêu cầu evidence cụ thể
     - Không có evidence = Không thể request approval

  3. Role-Based Approvals:
     - Developer KHÔNG THỂ tự approve gate của mình
     - Chỉ người có đúng role mới có thể approve

  4. Audit Trail:
     - Mọi hành động được log
     - Không thể xóa hoặc sửa đổi history
```

### 1.2 10-Stage Workflow Trong Platform

```yaml
Khi bạn tạo project trong SDLC Orchestrator:

  Project → 10 Stages được tạo tự động:

  Stage 00 (WHY)       → Gate G0.1 + G0.2 → Evidence required
  Stage 01 (WHAT)      → Gate G1          → Evidence required
  Stage 02 (HOW)       → Gate G2          → Evidence required
  Stage 04 (BUILD)     → Gate G3          → Evidence required
  Stage 05 (TEST)      → Gate G4          → Evidence required
  Stage 06 (DEPLOY)    → Gate G5          → Evidence required
  Stage 07 (OPERATE)   → Gate G6          → Evidence required
  Stage 03 (INTEGRATE) → Gate G7          → Evidence required
  Stage 08 (COLLABORATE)→ Gate G8         → Evidence required
  Stage 09 (GOVERN)    → Gate G9          → Evidence required

  Dashboard hiển thị: Current Stage, Gate Status, Progress %
```

---

## 2. Bắt Đầu: Tạo Account và Project

### 2.1 Đăng Ký / Đăng Nhập

**Option 1: GitHub OAuth (Khuyến nghị)**
```
1. Vào https://sdlc-orchestrator.io
2. Click "Continue with GitHub"
3. Authorize SDLC Orchestrator app
4. Done - Bạn đã login với GitHub account
   → GitHub token được lưu, có thể sync repos ngay
```

**Option 2: Email/Password**
```
1. Vào https://sdlc-orchestrator.io
2. Click "Sign Up"
3. Nhập email và password
4. Verify email
5. Login
   → Nếu muốn sync GitHub repos, vào Settings → Connect GitHub
```

### 2.2 Tạo Project Mới

```
Dashboard → Click "New Project"

Form:
  - Project Name: "NQH-Bot Platform v3.0"
  - Description: "Workforce management platform for NQH"
  - Template: "SDLC 5.1.3.1 Standard" (default)

Click "Create"

Result:
  → Bạn trở thành Owner
  → 10 Stages được tạo tự động
  → Project ở Stage 00 (WHY)
```

### 2.3 Invite Team Members

```
Project → Settings → Members → "Invite Member"

Search:
  - By email: taidt@mtsolution.com.vn
  - By GitHub: @taidang

Select Role:
  - Admin     → CTO/Technical Lead (approve G2, G3, G5-G7)
  - Maintainer → Dev Lead/QA Lead (approve G3-G6)
  - Developer → Team members (submit evidence, request approval)
  - Viewer    → Stakeholders (view only)

Click "Send Invitation"

Result:
  → User nhận email invitation
  → Accept → Gia nhập project với role đã chọn
```

---

## 3. Stage 00 (WHY): Foundation

### 3.1 Mục Tiêu Stage

SDLC 5.1.3.1 yêu cầu bắt đầu với **WHY** - tại sao làm dự án này?

Platform enforce:
- Phải có Problem Statement
- Phải có stakeholder analysis
- Phải có solution options
- CPO/Owner phải approve trước khi chuyển sang WHAT

### 3.2 Cách Thực Hiện Trong Platform

**Step 1: Upload Problem Statement**
```
Project → Stage 00 (WHY) → Gate G0.1 → "Upload Evidence"

Evidence Type: "Document"
File: problem-statement.md hoặc problem-statement.pdf

Required Sections (Platform validates):
  □ Problem description
  □ Affected users
  □ Current pain points
  □ Success metrics

Click "Upload"
```

**Step 2: Upload Solution Options**
```
Project → Stage 00 (WHY) → Gate G0.2 → "Upload Evidence"

Evidence Type: "Document"
File: solution-options.md

Required Sections:
  □ Minimum 3 solution options
  □ Pros/Cons for each
  □ Recommended option with rationale

Click "Upload"
```

**Step 3: Request Approval**
```
Gate G0.1 → "Request Approval"
  Select Approver: Owner hoặc CPO
  Add Notes: "Ready for review"

Gate G0.2 → "Request Approval"
  Select Approver: Owner hoặc CPO

Result:
  → Approver nhận notification
  → Review evidence
  → Approve hoặc Request Changes
```

**Step 4: Gate Passed**
```
When both G0.1 and G0.2 approved:
  → Stage 00 marked as COMPLETE
  → Stage 01 (WHAT) unlocked
  → Progress: 10%
```

---

## 4. Stage 01-02: WHAT và HOW

### 4.1 Stage 01 (WHAT): Planning

**Evidence Required:**
- Functional Requirements Document (FRD)
- User Stories
- Acceptance Criteria
- Sprint Plan

**Approvers:** Owner, CPO, PM

**Trong Platform:**
```
Stage 01 → Gate G1 → Upload Evidence:
  - functional-requirements.md
  - user-stories.md
  - sprint-plan.md

Request Approval → CPO/PM reviews → Approved/Request Changes
```

### 4.2 Stage 02 (HOW): Design

**Evidence Required:**
- Architecture Document
- API Specification
- Database Schema
- Security Review

**Approvers:** Owner, CTO, Admin

**Trong Platform:**
```
Stage 02 → Gate G2 → Upload Evidence:
  - architecture.md
  - openapi.yml
  - db-schema.sql
  - security-review.md

Request Approval → CTO/Admin reviews → Approved/Request Changes
```

---

## 5. Stage 04 (BUILD) và TEST

### 5.1 Stage 04 (BUILD): Development

**Evidence Required:**
- Code committed to repository
- Unit tests (80%+ coverage)
- Code review approved
- CI/CD pass

**Approvers:** CTO, Dev Lead, Admin

**Trong Platform:**
```
Stage 03 → Gate G3 → Upload Evidence:

Evidence Type: "GitHub Link"
  URL: github.com/org/repo/pull/123
  → Platform fetches: PR status, review status, CI status

Evidence Type: "Test Report"
  File: coverage-report.xml
  → Platform parses: Coverage %, pass/fail count

Evidence Type: "Screenshot"
  File: ci-cd-pass.png
  → Visual proof of CI/CD green

Request Approval → Dev Lead reviews → Approved/Request Changes
```

### 5.2 Stage 05 (TEST): Quality Assurance

**Evidence Required:**
- Test Report (Unit + Integration + E2E)
- Bug Report
- UAT Sign-off
- Performance Test Results

**Approvers:** QA Lead

**Trong Platform:**
```
Stage 04 → Gate G4 → Upload Evidence:
  - test-report.xml (JUnit format)
  - bug-report.md
  - uat-signoff.pdf
  - performance-results.json

Platform validates:
  □ Coverage ≥ 80%
  □ Zero P0 bugs
  □ UAT satisfaction ≥ 8/10
  □ Performance targets met

Request Approval → QA Lead reviews
```

---

## 6. Stage 06 (DEPLOY) và OPERATE

### 6.1 Stage 06 (DEPLOY): Go-Live

**Evidence Required:**
- Deployment Plan
- Rollback Procedure (tested)
- Pre-deployment Checklist
- War Room Setup

**Approvers:** DevOps Lead

**Trong Platform:**
```
Stage 05 → Gate G5 → Upload Evidence:
  - deployment-plan.md
  - rollback-test-results.md (must show <5 min RTO)
  - checklist-completed.pdf (50+ items)
  - war-room-schedule.md

Request Approval → DevOps Lead reviews
```

### 6.2 Stage 07 (OPERATE): Production

**Evidence Required:**
- Runbook
- Monitoring Setup (screenshots)
- On-call Schedule
- Incident Response Plan

**Approvers:** DevOps Lead

**Trong Platform:**
```
Stage 06 → Gate G6 → Upload Evidence:
  - runbook.md
  - grafana-dashboard.png
  - on-call-schedule.png
  - incident-response.md

Request Approval → DevOps Lead reviews
```

---

## 7. Stage 03 (INTEGRATE), COLLABORATE, GOVERN

### 7.1 Stage 03 (INTEGRATE)

**Evidence:** Integration tests, API contracts, data validation
**Approvers:** CTO, Data Lead

### 7.2 Stage 08 (COLLABORATE)

**Evidence:** Team review notes, knowledge transfer docs
**Approvers:** CPO, PM

### 7.3 Stage 09 (GOVERN)

**Evidence:** Executive summary, compliance report, final sign-off
**Approvers:** Owner, CEO

```
Stage 09 → Gate G9 → ALL gates passed

Project Status: COMPLETE
Progress: 100%

Audit Trail: Complete history of who did what when
```

---

## 8. Dashboard và Monitoring

### 8.1 Project Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│ Project: NQH-Bot Platform v3.0                                  │
│ Current Stage: 03 (BUILD)           Progress: 35%              │
├─────────────────────────────────────────────────────────────────┤
│ Gates Status:                                                   │
│   G0.1 ✅ Approved (Nov 20, CPO)                                │
│   G0.2 ✅ Approved (Nov 21, CPO)                                │
│   G1   ✅ Approved (Nov 23, PM)                                 │
│   G2   ✅ Approved (Nov 25, CTO)                                │
│   G3   ⏳ In Progress (3/5 evidence uploaded)                  │
│   G4-G9 🔒 Locked                                              │
├─────────────────────────────────────────────────────────────────┤
│ Team: 8 members                                                 │
│   Owner: Tai Dang                                               │
│   Admin: Hiep Dinh (CTO)                                        │
│   Maintainer: Endior (Dev Lead), Hang (Remote Lead)             │
│   Developer: 4 devs                                             │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Notifications

```
Platform gửi notifications khi:
  - Approval requested → Approver nhận email/Slack
  - Gate approved → Team nhận notification
  - Request changes → Submitter nhận feedback
  - Stage completed → All members notified
```

---

## 9. Best Practices

### 9.1 Evidence Quality

```yaml
❌ BAD Evidence:
  - Screenshot không rõ ràng
  - Document chưa hoàn chỉnh
  - Test report fake

✅ GOOD Evidence:
  - Clear screenshots với annotations
  - Complete documents với all sections
  - Real test results từ CI/CD

Platform tip: Upload early, iterate based on feedback
```

### 9.2 Collaboration

```yaml
❌ One-person-does-all:
  - Developer tự submit và tự approve
  - Platform blocks: "Cannot approve own submission"

✅ Team collaboration:
  - Developer submits evidence
  - Dev Lead reviews và approves
  - Different roles for different stages

Platform enforces: Separation of duties
```

### 9.3 Regular Check-ins

```yaml
Recommended Workflow:

  Daily: Update evidence, check gate status
  Weekly: Team sync on stage progress
  Per-Gate: Request approval khi evidence complete
  Per-Stage: Celebrate completion, plan next stage
```

---

## 10. Troubleshooting

### Q: Không thể approve gate?

```
Check:
  1. Role: Bạn có đúng role không? (Dev không approve được G3)
  2. Evidence: Đã upload đủ required evidence chưa?
  3. Previous gate: Gate trước đã pass chưa?

Solution: Contact Owner để check permissions
```

### Q: Gate bị reject?

```
1. Xem feedback từ approver
2. Update evidence theo feedback
3. Re-upload evidence mới
4. Request approval lại

Platform keeps history: Tất cả versions được lưu
```

### Q: Muốn skip một stage?

```
Platform policy: KHÔNG cho phép skip stages

Lý do:
  - SDLC 5.1.3.1 requires sequential completion
  - Each stage builds on previous
  - Skip = Technical debt

Exception: Owner có thể "Force Pass" với documented reason
  → Audit log records việc này
  → Không khuyến khích
```

---

## 11. Support

```yaml
Documentation:
  - In-app help: Click (?) icon
  - User Guide: /docs trong platform
  - SDLC 5.1.3.1 Framework: /docs/10-Archive/SDLC-Enterprise-Framework/

Contact:
  - Platform Support: support@sdlc-orchestrator.io
  - Slack: #sdlc-orchestrator-support
  - Issues: github.com/sdlc-orchestrator/issues
```

---

## Summary: SDLC Orchestrator + SDLC 5.1.3.1

```yaml
SDLC 5.1.3.1 Framework định nghĩa:
  - 10 Stages (WHY → GOVERN)
  - Quality Gates (G0-G9)
  - Role-based Approvals
  - Evidence Requirements

SDLC Orchestrator enforce:
  - Sequential stage progression (không skip)
  - Evidence validation (không fake)
  - Role-based access (đúng người đúng việc)
  - Full audit trail (accountability)

Kết quả:
  - Team follow SDLC 5.1.3.1 đúng cách
  - Quality được đảm bảo ở mỗi stage
  - Collaboration được enforce
  - Full traceability cho audit
```

---

**Last Updated**: November 29, 2025
**Status**: USER TRAINING DOCUMENT
**Platform Version**: 1.0.0

---

*Tài liệu này hướng dẫn sử dụng SDLC Orchestrator để áp dụng SDLC 5.1.3.1 Framework. Platform enforce workflow, bạn focus vào quality.*
