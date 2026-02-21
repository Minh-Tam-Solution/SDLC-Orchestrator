---
sdlc_version: "6.1.0"
document_type: "Security Questionnaire"
status: "APPROVED"
sprint: "188"
spec_id: "SEC-QST-001"
tier: "ENTERPRISE"
stage: "09 - Govern"
---

# SDLC Orchestrator — Enterprise Security Questionnaire

**Version**: 1.0.0
**Status**: APPROVED
**Created**: February 2026
**Sprint**: 188 — GA Launch
**Audience**: Enterprise buyers, procurement teams, InfoSec reviewers, RFP respondents
**Owner**: CTO + Security Lead

This document provides pre-filled answers to the 50 most common enterprise security and compliance questions asked during vendor evaluation. Distribute under NDA for enterprise pipeline deals.

---

## 1. Authentication & Access Control

**Q1. What authentication methods are supported?**
SAML 2.0 (via ENTERPRISE SSO — Sprint 183), Azure Active Directory OAuth 2.0, Google Workspace OAuth 2.0, GitHub OAuth 2.0. JWT tokens (15-minute access + 7-day refresh rotation). TOTP-based MFA enforced for all PROFESSIONAL and ENTERPRISE users.

**Q2. Does the platform support Single Sign-On (SSO)?**
Yes. ENTERPRISE tier supports SAML 2.0 and Azure AD OAuth 2.0 PKCE with Just-in-Time (JIT) user provisioning. IdP groups are mapped to Orchestrator RBAC roles automatically on first login. Configuration endpoint: `POST /api/v1/enterprise/sso/configure`.

**Q3. Is multi-factor authentication (MFA) enforced?**
MFA is enforced for PROFESSIONAL and ENTERPRISE tiers (TOTP via Google Authenticator or any RFC 6238-compliant app). LITE and STANDARD tiers: MFA is available but optional. Admin-level accounts always require MFA regardless of tier.

**Q4. What is the password policy?**
Minimum 12 characters, bcrypt hash (cost factor 12), password reuse blocked for last 5 passwords. Breach detection via HaveIBeenPwned API (email-only check, no plaintext sent). Password rotation recommended every 90 days; forced for admin accounts.

**Q5. How is role-based access control (RBAC) implemented?**
13 predefined roles: Owner, Admin, CTO, CPO, CEO, PM, Tech Lead, Senior Dev, Dev, QA, DevOps, Security Lead, DPO. Row-level security (PostgreSQL RLS policies) ensures users can only access records belonging to their organisation. API scopes: `read:gates`, `write:evidence`, `admin:policies`, `manage:users`.

**Q6. Is there session management and automatic timeout?**
JWT access tokens expire after 15 minutes. Refresh tokens expire after 7 days. Refresh tokens are rotated on use (refresh token rotation). Token blacklist maintained in Redis for immediate revocation. Session timeout warning at 13 minutes with automatic renewal option.

**Q7. Can user access be revoked immediately?**
Yes. Admin endpoint `POST /api/v1/admin/users/{id}/revoke-sessions` invalidates all active tokens immediately by writing to the Redis token blacklist. Takes effect within the next token validation cycle (<1 second).

---

## 2. Data Security & Privacy

**Q8. Where is data stored?**
Primary database: PostgreSQL 15.5 (Singapore region). Evidence files (binary artifacts): MinIO S3-compatible object storage, region-configurable per project (VN / EU / US). ENTERPRISE customers may specify their required data region at project creation. See ADR-063 for data residency details.

**Q9. Is data encrypted at rest?**
Yes. PostgreSQL: AES-256 via `pgcrypto` extension for sensitive columns (email, IP addresses, PII fields). MinIO evidence storage: AES-256 server-side encryption (SSE-S3). Database disk: AES-256 volume encryption on all cloud instances. Encryption keys managed via HashiCorp Vault with 90-day rotation.

**Q10. Is data encrypted in transit?**
Yes. All external traffic: TLS 1.3 enforced (TLS 1.2 as fallback, TLS 1.0/1.1 disabled). Internal service-to-service: mutual TLS. Certificate management: Let's Encrypt (auto-renewal) for public endpoints, private CA for internal services. HSTS header enforced: `max-age=31536000; includeSubDomains`.

**Q11. What is the data retention policy?**
- User data: retained while account is active + 30 days post-cancellation
- Evidence files: retained for project lifetime + 90 days post-project-deletion
- Audit logs: 90-day immutable retention (append-only PostgreSQL table, no UPDATE/DELETE)
- LITE inactive accounts: hibernated at 30 days, purged at 90 days (GDPR Art.17 erasure on request)
- Backups: daily, 30-day retention, encrypted, stored in separate region

**Q12. How is GDPR compliance handled?**
Full GDPR implementation per ADR-063 and FR-045:
- Art.15 (Right of Access): `GET /api/v1/gdpr/me/data-export` — summary view
- Art.20 (Data Portability): `GET /api/v1/gdpr/me/data-export/full` — full JSON export
- Art.17 (Right to Erasure): `POST /api/v1/gdpr/dsar` with `request_type=erasure` — 30-day SLA
- Art.7 (Consent): `POST/PUT /api/v1/gdpr/consent` — granular per-purpose consent management
- DPO contact: Accessible via platform UI and `GET /api/v1/gdpr/dsar` (DPO role required for review)

**Q13. Do you comply with CCPA (California Consumer Privacy Act)?**
Yes. CCPA rights are fulfilled via the same GDPR-compliant DSAR infrastructure. California users may submit data access, deletion, and opt-out requests via the same endpoints. No sale of personal data to third parties.

**Q14. What personal data is collected?**
Email address, full name, IP address (masked in logs after 30 days), session metadata, usage telemetry (feature interactions, no content). Evidence file content is stored but not processed by Orchestrator systems (it is user-owned data). Agent message content is retained per user session.

**Q15. Can we use our own encryption keys (BYOK)?**
BYOK is on the roadmap for Q3 2026 (Sprint 192+). Currently, encryption keys are Orchestrator-managed via HashiCorp Vault. ENTERPRISE customers may request a dedicated Vault namespace. Contact `security@sdlcorchestrator.com` for early access.

---

## 3. Infrastructure & Operations

**Q16. Where is the platform hosted?**
Primary: AWS Singapore (ap-southeast-1). EU data residency: AWS Frankfurt (eu-central-1) available for ENTERPRISE. CDN: Cloudflare (DDoS protection + WAF). Database: AWS RDS PostgreSQL (Multi-AZ, automated failover). Storage: AWS S3-compatible MinIO (replicated across AZs).

**Q17. What is the uptime SLA?**
- ENTERPRISE: 99.9% monthly uptime SLA (≤8.7 hours downtime/year). 4-hour P1 response, 24-hour resolution target.
- PROFESSIONAL: 99.5% best-effort. No contractual SLA.
- LITE/STANDARD: No SLA (community best-effort).
SLA credits: 10% of monthly fee per hour of downtime beyond SLA.

**Q18. What is the disaster recovery plan?**
RTO (Recovery Time Objective): 4 hours. RPO (Recovery Point Objective): 1 hour. Daily automated snapshots to a separate AWS region. Multi-AZ PostgreSQL with 1-minute failover. Runbook: `docs/09-govern/08-Operations/DISASTER-RECOVERY-RUNBOOK.md`. Last DR test: Sprint 187.

**Q19. Is there a penetration test report available?**
Yes. External penetration test conducted in Sprint 187 (February 2026). Report available under NDA to ENTERPRISE prospects. Zero P0/P1 findings at GA. All findings disclosed and remediated within 30 days. Contact `security@sdlcorchestrator.com`.

**Q20. What is the vulnerability management process?**
- SAST: Semgrep with OWASP Top 10 rules on every commit (GitHub Actions)
- Dependency scan: Grype (critical/high CVEs block merge)
- License scan: Syft (AGPL contamination detection)
- CVE response: Critical (<24h), High (<7 days), Medium (<30 days)
- SBOM: Automatically generated per release, available on request

**Q21. How are security patches applied?**
Critical OS patches: applied within 24 hours via automated patching (AWS Systems Manager Patch Manager). Application dependency patches: via Dependabot PRs reviewed by Security Lead. Zero-downtime rolling deployments via Kubernetes. Patch notification sent to ENTERPRISE customers 48 hours in advance (except emergency patches).

**Q22. Do you have a security incident response plan?**
Yes. Documented in `docs/09-govern/08-Operations/INCIDENT-RESPONSE-RUNBOOK.md`. Severity classification: P0 (data breach), P1 (service outage), P2 (degraded performance). P0 notification: within 24 hours to affected ENTERPRISE customers (GDPR Art.33 72-hour DPA notification included). Security contact: `security@sdlcorchestrator.com`.

---

## 4. Compliance & Certifications

**Q23. Are you SOC2 Type II certified?**
SOC2 evidence pack generated and available (Sprint 185). Independent auditor review scheduled Q2 2026. Full SOC2 Type II report targeted Q3 2026. SOC2 evidence pack available to ENTERPRISE prospects under NDA. Maps to Trust Service Criteria: Security, Availability, Confidentiality.

**Q24. Do you support HIPAA compliance?**
HIPAA evidence pack available for ENTERPRISE tier. Business Associate Agreement (BAA) template available. PHI access logging enforced when `compliance_type=HIPAA_AUDIT` evidence is stored. PHI data handling is customer-managed (Orchestrator is the governance layer, not a PHI processor). Full HIPAA BAA execution required for healthcare enterprise customers.

**Q25. Do you support NIST AI RMF compliance?**
Yes, ENTERPRISE tier only. Four NIST AI RMF functions implemented: `GOVERN`, `MAP`, `MEASURE`, `MANAGE` via dedicated API routes (`/api/v1/nist/govern`, etc.). NIST AI RMF Gap Assessment available as a professional service ($6,000, 2-3 weeks).

**Q26. ISO 27001 controls mapping?**
ISO 27001 Annex A controls are mapped to existing Evidence Vault categories (Sprint 185). Compliance dashboard shows ISO 27001 readiness percentage. Full ISO 27001 certification is on the Q4 2026 roadmap.

**Q27. What security frameworks does the platform follow?**
OWASP ASVS Level 2 (264/264 requirements, verified Sprint 187). NIST Cybersecurity Framework (Identify, Protect, Detect, Respond, Recover). GDPR (Art.6, Art.15, Art.17, Art.20 implemented). NIST AI Risk Management Framework (ENTERPRISE tier).

---

## 5. Network & API Security

**Q28. How are APIs secured?**
JWT Bearer token authentication on all endpoints. Rate limiting: global (100 req/min per IP), per-user (1,000 req/hour), per-endpoint (varies). CSRF protection on all state-mutating endpoints. API versioning: `/api/v1/` prefix. OpenAPI 3.0 specification maintained (1,629 lines, 91 endpoints). All inputs validated via Pydantic with strict mode.

**Q29. Is there an IP allowlist feature?**
IP allowlist for ENTERPRISE tier: configurable via `POST /api/v1/enterprise/sso/configure` — `allowed_ip_ranges` field (CIDR notation). Webhook IPs: configurable per integration (Jira, Teams, Slack). Not available for LITE/STANDARD.

**Q30. Are there DDoS protections?**
Cloudflare WAF + DDoS protection (included). AWS Shield Standard (free, included). Rate limiting middleware in application layer (Redis-backed, per-IP and per-user). Burst protection: 10x normal rate for up to 5 seconds, then hard block.

**Q31. Is there an audit log for API access?**
Yes. Immutable audit log table (`audit_logs`): append-only (PostgreSQL trigger prevents UPDATE/DELETE). Records: user_id, action, endpoint, IP address, timestamp, request/response status. 90-day retention. Exportable via `GET /api/v1/enterprise/audit` (ENTERPRISE, DPO role). Available as CSV, JSON, or PDF.

**Q32. Do you support mutual TLS (mTLS) for API clients?**
mTLS is supported for ENTERPRISE webhook integrations (Jira, Teams callbacks). Enterprise API clients may request client certificate provisioning. Contact `enterprise@sdlcorchestrator.com` for setup.

---

## 6. Third-Party Integrations & Supply Chain

**Q33. What third-party services are used?**
- **Cloudflare**: CDN + WAF (required)
- **AWS**: Compute + storage (required)
- **Anthropic (Claude)**: Fallback AI provider (optional, no PII sent in prompts by default)
- **OPA (Open Policy Agent)**: Policy evaluation (self-hosted, no third-party calls)
- **MinIO**: Object storage (self-hosted on AWS)
- **HashiCorp Vault**: Secrets management (self-hosted)
- **Prometheus + Grafana**: Monitoring (self-hosted)
- **Semgrep**: SAST scanning (CLI-only, no data leaves the platform)

**Q34. How are third-party dependencies managed?**
SBOM (Software Bill of Materials) generated per release via Syft. Dependency vulnerabilities scanned via Grype (blocks merge on critical/high CVEs). License compliance: Syft detects AGPL/GPL contamination (CI/CD gate). All AGPL components (MinIO, Grafana) accessed via network-only API — no code imports (ADR containment policy). Quarterly dependency review by CTO.

**Q35. Do you do background checks on employees with data access?**
Yes. All employees with production database access undergo background checks (Vietnamese national standard + international Criminal Record Check for non-VN nationals). Access is role-based with least privilege. Production access logs reviewed weekly.

---

## 7. Business Continuity

**Q36. What is your company's size and location?**
Minh Tam Solution (MTS), Ho Chi Minh City, Vietnam. Founded 2023. 8-15 FTE team (engineering + product + operations). 5 founding enterprise customers (Vietnam Series B, fintech sector). Contact: `enterprise@sdlcorchestrator.com`, CPO: `taidt@mtsolution.com.vn`.

**Q37. What is the key-person risk mitigation?**
Full source code hosted on private GitHub repository with 3 maintainer accounts. Documentation (SDLC 6.1.0 Framework) published as open-source submodule. Architecture decisions documented in 63 ADRs. Run-book operations documented for all P0/P1 incidents. Infrastructure fully IaC (Terraform) — reproducible by any qualified engineer.

**Q38. Do you have cyber liability insurance?**
Cyber liability insurance procurement in progress (targeted Q2 2026 before large enterprise contracts). Currently self-insured. ENTERPRISE contracts include SLA credit provisions.

---

## 8. Data Portability & Exit Rights

**Q39. Can we export all our data if we leave?**
Yes. Multiple export mechanisms:
- `GET /api/v1/gdpr/me/data-export/full` (Art.20 — JSON format, per user)
- `GET /api/v1/enterprise/audit` (full audit log export — CSV/JSON/PDF)
- Evidence files: direct S3 download via signed URLs (MinIO)
- Full database export: available on request within 30 days of contract termination
No lock-in: exported data formats are open standards (JSON, CSV, XML, SARIF).

**Q40. What happens to data after contract termination?**
User data deleted within 30 days of account cancellation. Evidence files deleted within 90 days. Audit logs retained for 90 days post-termination (legal hold override available). Backup data purged after 30 days. DPA requires written confirmation of deletion within 14 days of purge.

---

## 9. AI-Specific Security

**Q41. How is AI-generated output governed?**
4-Gate Quality Pipeline on all AI outputs: Gate 1 (Syntax), Gate 2 (Security/SAST), Gate 3 (Context), Gate 4 (Tests). Maximum retry limit of 3 before escalation to human review. All AI outputs stored in Evidence Vault with full audit trail. AI provider fallback chain: Ollama (primary, on-premise) → Claude (external, fallback) → Rule-based (deterministic fallback).

**Q42. Is any user data sent to external AI providers?**
By default, the primary AI provider is Ollama running on-premise (no data leaves your network). Claude (Anthropic) is used only as a fallback provider and only receives task-specific prompts — no user PII, no evidence file contents, no audit log data. Customers may disable Claude fallback and operate fully on-premise.

**Q43. How is prompt injection prevented?**
12 injection-pattern regex rules in `input_sanitizer.py` (Sprint 179). OTT/webhook content (Telegram, Teams) is sanitized before reaching agent prompts. Shell command injection: 8 deny regex patterns in `shell_guard.py` + path traversal detection. Agent output: credential scrubbing (6 patterns) before display/storage (Sprint 179, ADR-058).

**Q44. Are agent delegation depths limited?**
Yes. Maximum delegation depth enforced to prevent infinite agent chains (Nanobot N2 pattern, ADR-056). Parent-child conversation inheritance tracked with budget circuit breakers. Agent budget limits configurable per conversation.

---

## 10. Vendor Evaluation Specifics

**Q45. Can we get a security questionnaire in Excel/Word format?**
Contact `enterprise@sdlcorchestrator.com`. We maintain completed versions of SIG-Lite, CAIQ (CSA), and custom formats. This document can be exported as PDF or DOCX on request.

**Q46. Is a third-party security audit report available?**
Yes. External penetration test report from Sprint 187 (February 2026) available under NDA. OWASP ASVS Level 2 self-assessment: 264/264 requirements met. Independent SOC2 Type II audit in progress (targeted Q3 2026).

**Q47. Do you participate in a bug bounty program?**
Coordinated vulnerability disclosure program active. Contact: `security@sdlcorchestrator.com`. Responsible disclosure policy: 90-day embargo, public acknowledgement, no legal action for good-faith researchers. Formal bug bounty program (HackerOne) planned Q3 2026.

**Q48. What is your SLA for security vulnerability patching?**
- Critical (CVSS 9.0+): Patch within 24 hours, notification within 4 hours
- High (CVSS 7.0-8.9): Patch within 7 days
- Medium (CVSS 4.0-6.9): Patch within 30 days
- Low: Next scheduled release cycle

**Q49. Can we do our own penetration test?**
Yes, with advance notice (minimum 5 business days) and signed Rules of Engagement. Contact `security@sdlcorchestrator.com`. ENTERPRISE customers may conduct quarterly tests. Testing must be scoped to the customer's own tenant only.

**Q50. Whom should we contact for security escalations?**
- Security inquiries: `security@sdlcorchestrator.com`
- Enterprise sales/DPA: `enterprise@sdlcorchestrator.com`
- CPO (product + pricing): `taidt@mtsolution.com.vn`
- P0 incidents (ENTERPRISE SLA): Dedicated CSM + `oncall@sdlcorchestrator.com` (4-hour response SLA)

---

## Document Control

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Approved by | CTO + Security Lead |
| Last review | February 2026 |
| Next review | August 2026 |
| Distribution | Enterprise prospects under NDA only |
| Classification | CONFIDENTIAL |

---

*SDLC Orchestrator — Enterprise AI Governance Platform. Questions? `enterprise@sdlcorchestrator.com`*
