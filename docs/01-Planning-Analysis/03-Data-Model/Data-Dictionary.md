# Data Dictionary
## Complete Field Definitions (16 Tables)

**Version**: 1.0.0
**Date**: January 13, 2025
**Status**: ACTIVE - DRAFT
**Authority**: Backend Lead + CTO Review (PENDING)
**Foundation**: Data Model ERD v1.0, Database Schema v1.0
**Stage**: Stage 01 (WHAT - Planning & Analysis)
**Framework**: SDLC 4.9 Complete Lifecycle (10 Stages)

---

## Document Purpose

This document defines **WHAT each database field means** with data types, constraints, examples, and business rules.

---

## Table 1: users

| Field | Type | Required | Constraints | Description | Example |
|-------|------|----------|-------------|-------------|---------|
| id | UUID | Yes | PRIMARY KEY | Unique user identifier (auto-generated) | `550e8400-e29b-41d4-a716-446655440000` |
| email | VARCHAR(255) | Yes | UNIQUE, NOT NULL | User email address (login credential) | `john.doe@techcorp.com` |
| password_hash | VARCHAR(255) | Yes | NOT NULL | bcrypt hash of password (never store plaintext) | `$2b$12$KIXxJ3...` |
| role | VARCHAR(20) | Yes | NOT NULL, CHECK | User role (C-Suite: ceo/cto/cpo/cio/cfo, Engineering: em/pm/dev_lead/qa_lead/security_lead/devops_lead/data_lead, Admin: admin) | `cto`, `em`, `admin` |
| team_id | UUID | Yes | NOT NULL, FOREIGN KEY(teams.id) | Team membership | `7f3e8400-...` |
| full_name | VARCHAR(255) | No | - | User's full name | `John Doe` |
| avatar_url | VARCHAR(500) | No | - | Profile picture URL (Gravatar, uploaded image) | `https://...` |
| job_title | VARCHAR(100) | No | - | Official job title | `Chief Technology Officer`, `Engineering Manager` |
| department | VARCHAR(50) | No | - | Department affiliation | `Engineering`, `Product`, `Operations` |
| created_at | TIMESTAMP | Yes | NOT NULL, DEFAULT NOW() | Account creation timestamp | `2025-01-13 10:00:00` |
| updated_at | TIMESTAMP | Yes | NOT NULL, DEFAULT NOW() | Last profile update | `2025-01-13 11:30:00` |
| last_login_at | TIMESTAMP | No | - | Last successful login | `2025-01-13 09:45:00` |
| is_active | BOOLEAN | Yes | NOT NULL, DEFAULT TRUE | Account status (deactivated users cannot log in) | `true` |
| email_verified | BOOLEAN | Yes | NOT NULL, DEFAULT FALSE | Email verification status (2FA, security) | `false` |

---

## Table 2: organizations

| Field | Type | Required | Constraints | Description | Example |
|-------|------|----------|-------------|-------------|---------|
| id | UUID | Yes | PRIMARY KEY | Unique organization identifier | `550e8400-...` |
| org_name | VARCHAR(255) | Yes | NOT NULL | Organization name | `TechCorp Inc.` |
| subscription_tier | VARCHAR(20) | Yes | NOT NULL, CHECK(free/pro/enterprise) | Subscription plan (determines limits) | `enterprise` |
| max_projects | INT | Yes | NOT NULL, DEFAULT 10 | Maximum projects allowed (enforced by application) | `1000` (enterprise) |
| max_users | INT | Yes | NOT NULL, DEFAULT 50 | Maximum users allowed | `1000` (enterprise) |
| created_at | TIMESTAMP | Yes | NOT NULL, DEFAULT NOW() | Organization registration | `2025-01-01 00:00:00` |
| updated_at | TIMESTAMP | Yes | NOT NULL, DEFAULT NOW() | Last org settings update | `2025-01-13 10:00:00` |

---

## Table 3: gate_approvals (SDLC 4.9 - 10 Stages)

| Field | Type | Required | Constraints | Description | Example |
|-------|------|----------|-------------|-------------|---------|
| id | UUID | Yes | PRIMARY KEY | Unique approval record identifier | `550e8400-...` |
| gate_id | UUID | Yes | NOT NULL, FOREIGN KEY(gates.id) ON DELETE CASCADE | Gate being approved | `7f3e8400-...` |
| approver_id | UUID | Yes | NOT NULL, FOREIGN KEY(users.id) | User granting approval (CEO/CTO/CPO/CIO/CFO/etc.) | `8a4f9500-...` |
| approver_role | VARCHAR(20) | Yes | NOT NULL | Role of approver (ceo/cto/cpo/cio/cfo/em/pm/dev_lead/qa_lead/security_lead/devops_lead/data_lead) | `cto`, `cpo` |
| approval_status | VARCHAR(20) | Yes | NOT NULL, CHECK(pending/approved/rejected) | Approval decision | `approved` |
| approval_reason | TEXT | No | - | Reason for approval/rejection (required for rejection) | `Missing NFR1-3 performance metrics` |
| approved_at | TIMESTAMP | No | - | Timestamp of approval/rejection decision | `2025-01-13 15:30:00` |
| created_at | TIMESTAMP | Yes | NOT NULL, DEFAULT NOW() | Approval request created | `2025-01-13 14:00:00` |

**Business Rules (SDLC 4.9 Gate Matrix)**:
- G0.1 (Problem Foundation): CPO + EM (2 approvals)
- G0.2 (Business Case): CEO + CPO (2 approvals)
- G1 (Requirements & Planning): CTO + CPO (2 approvals)
- G2 (Design & Architecture): CTO + Security Lead (2 approvals)
- G3 (Development): CTO + Dev Lead (2 approvals)
- G4 (Quality Assurance): CPO + QA Lead (2 approvals)
- G5 (Production Go-Live): CTO + CIO (2 approvals)
- G6 (Production Excellence): CIO + DevOps Lead (2 approvals)
- G7 (Systems Integration): CTO + Data Lead (2 approvals)
- G8 (Team Coordination): CPO + EM (2 approvals)
- G9 (Strategic Oversight): CEO + CFO (2 approvals)

---

## Table 4: gates

| Field | Type | Required | Constraints | Description | Example |
|-------|------|----------|-------------|-------------|---------|
| gate_code | VARCHAR(20) | Yes | NOT NULL | Gate identifier (G0.1, G0.2, G1, G2, G3, G4, G5, G6, G7, G8, G9) | `G1`, `G2` |
| stage | VARCHAR(20) | Yes | NOT NULL, CHECK(stage-00 to stage-09) | SDLC 4.9 stage (stage-00 to stage-09) | `stage-01` |
| status | VARCHAR(20) | Yes | NOT NULL, DEFAULT not_evaluated, CHECK(not_evaluated/pending/blocked/passed/override) | Gate evaluation status | `passed`, `blocked` |
| override_reason | TEXT | No | - | Reason for manual override (CTO/CEO only) | `Legal review delayed, proceeding with internal risk assessment` |
| override_expires_at | TIMESTAMP | No | - | Override expiration (default: +7 days from override_at) | `2025-01-20 10:00:00` |

---

## Table 5: evidence

| Field | Type | Required | Constraints | Description | Example |
|-------|------|----------|-------------|-------------|---------|
| evidence_type | VARCHAR(50) | Yes | NOT NULL, CHECK(manual_upload/slack_message/github_pr/github_issue/figma_file/zoom_transcript) | Evidence source type | `slack_message`, `github_pr` |
| file_path | VARCHAR(500) | No | - | MinIO S3 path (for uploaded files) | `s3://evidence-vault/2025/01/13/{UUID}.pdf` |
| file_size_bytes | BIGINT | No | - | File size (for uploads, max 10MB per NFR3) | `2097152` (2MB) |
| file_mime_type | VARCHAR(100) | No | - | MIME type (for virus scanning) | `application/pdf`, `image/png` |
| source_url | VARCHAR(500) | No | - | Original URL (Slack message link, GitHub PR link, Figma file link) | `https://acme.slack.com/archives/C01.../p1673614200` |
| content_preview | TEXT | No | - | First 1000 chars for full-text search (PostgreSQL pg_trgm) | `User Interview Summary: Talked to Sarah...` |

---

## Table 6: policies

| Field | Type | Required | Constraints | Description | Example |
|-------|------|----------|-------------|-------------|---------|
| policy_code | VARCHAR(100) | Yes | UNIQUE, NOT NULL | Unique policy identifier (kebab-case) | `policy-pack-user-interviews` |
| rego_code | TEXT | Yes | NOT NULL | Rego policy logic (OPA syntax) | `package policy_pack_user_interviews\ndefault allow = false\n...` |
| stage | VARCHAR(20) | Yes | NOT NULL | SDLC 4.9 stage (stage-00 to stage-09) | `stage-00`, `stage-01` |
| category | VARCHAR(50) | No | - | Policy category (validation, security, performance, etc.) | `validation`, `security` |
| is_pre_built | BOOLEAN | Yes | NOT NULL, DEFAULT FALSE | Pre-built vs custom policy (pre-built cannot be deleted) | `true` (100+ pre-built), `false` (custom) |
| current_version | VARCHAR(20) | Yes | NOT NULL, DEFAULT 1.0.0 | Semantic versioning (1.0.0, 1.1.0, 2.0.0) | `1.0.0` |

---

## Table 7: audit_logs (Partitioned by Month)

| Field | Type | Required | Constraints | Description | Example |
|-------|------|----------|-------------|-------------|---------|
| action | VARCHAR(50) | Yes | NOT NULL | User action (upload, download, delete, override, approve, reject) | `upload`, `override` |
| resource_type | VARCHAR(50) | Yes | NOT NULL | Resource type (evidence, gate, policy, user) | `evidence`, `gate` |
| resource_id | UUID | No | - | Resource identifier | `550e8400-...` |
| metadata | JSONB | No | - | Additional context (IP address, user agent, browser, etc.) | `{"ip": "192.168.1.100", "user_agent": "Chrome/120"}` |
| created_at | TIMESTAMP | Yes | NOT NULL, DEFAULT NOW(), PARTITION KEY | Audit timestamp (partitioned by month for scalability) | `2025-01-13 10:00:00` |

**Partitioning**:
- audit_logs_2025_01 (Jan 2025)
- audit_logs_2025_02 (Feb 2025)
- ... (monthly partitions for 7 years per NFR17)

---

## Table 8: integrations

| Field | Type | Required | Constraints | Description | Example |
|-------|------|----------|-------------|-------------|---------|
| integration_type | VARCHAR(50) | Yes | NOT NULL, CHECK(slack/github/figma/zoom/jira/linear) | Integration type | `slack`, `github` |
| oauth_token | TEXT | No | - | Encrypted OAuth access token (AES-256, NFR7) | `xoxb-...` (encrypted) |
| oauth_refresh_token | TEXT | No | - | Encrypted OAuth refresh token | `xoxr-...` (encrypted) |
| config | JSONB | No | - | Integration-specific config (Slack: channel IDs, GitHub: repo URLs, etc.) | `{"channels": ["#product-research"], "repos": ["org/repo"]}` |
| status | VARCHAR(20) | Yes | NOT NULL, DEFAULT active, CHECK(active/inactive/error) | Integration status | `active`, `error` |
| last_sync_at | TIMESTAMP | No | - | Last successful sync timestamp | `2025-01-13 09:00:00` |

---

## Data Sizing Summary (Year 3)

| Table | Rows (Year 3) | Storage | Partition Strategy |
|-------|--------------|---------|-------------------|
| users | 13,420 | 10MB | None |
| teams | 1,342 | 1MB | None |
| organizations | 670 | 0.5MB | None |
| projects | 6,710 | 50MB | None |
| gates | 53,680 | 200MB | None |
| gate_approvals | 107,360 | 300MB | None (may partition if >1M rows) |
| evidence | 67,100,000 | 500MB | None (large files in MinIO, not PostgreSQL) |
| policies | 1,000 | 10MB | None |
| audit_logs | 100,000,000 | 5GB | **Partitioned by month** (12 partitions/year) |
| integrations | 4,026 | 20MB | None |
| **TOTAL** | **167M rows** | **6GB** | 1 partitioned table |

---

## References

- [Data Model ERD](./Data-Model-ERD.md)
- [Database Schema](./Database-Schema.md)
- [Non-Functional Requirements](../01-Requirements/Non-Functional-Requirements.md)

---

**Last Updated**: 2025-01-13
**Owner**: Backend Lead + CTO
**Status**: 🟡 DRAFT (PENDING REVIEW)

---

**End of Data Dictionary v1.0.0**
