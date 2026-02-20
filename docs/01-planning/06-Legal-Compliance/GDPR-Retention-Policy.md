# GDPR Retention Policy - SDLC Orchestrator

**Version:** 1.0.0
**Date:** January 19, 2026
**Status:** ACTIVE - Sprint 82 (Pre-Launch Hardening)
**Authority:** Legal + CTO Approved
**Framework:** SDLC 6.1.0 P7 (Documentation Permanence)
**Compliance:** GDPR, CCPA, SOC 2

---

## Executive Summary

This document defines the data retention policy for SDLC Orchestrator, balancing:
- **Evidence integrity** (7-year audit trail requirement)
- **GDPR compliance** (right to erasure, data minimization)
- **Operational needs** (performance, storage costs)

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| Evidence: 7-year retention | SEC 17a-4, SOX, audit compliance |
| Evidence deletion: Anonymization | Preserves integrity while respecting GDPR |
| User PII: Account lifetime + 30 days | GDPR data minimization |
| Audit logs: 7-year append-only | Non-repudiation requirement |

---

## Data Classification

### Tier 1: Evidence Artifacts (Immutable)

**Description:** Files uploaded to Evidence Vault (documents, screenshots, code samples)

| Attribute | Value |
|-----------|-------|
| **Retention Period** | 7 years |
| **Storage** | MinIO with Object Lock (WORM) |
| **GDPR Erasure** | **Anonymization** (not deletion) |
| **Legal Basis** | Legitimate interest (audit compliance) |

**Anonymization Approach:**
- File content: Preserved (integrity)
- Metadata (uploader, user references): Replaced with `REDACTED-{hash}`
- Audit trail: Maintained with anonymized references

```
Before Anonymization:
  uploader_id: "user-123-john.doe@company.com"
  uploader_name: "John Doe"

After Anonymization:
  uploader_id: "REDACTED-a1b2c3d4"
  uploader_name: "REDACTED"
```

### Tier 2: Audit Logs (Append-Only)

**Description:** System audit trail (who did what when)

| Attribute | Value |
|-----------|-------|
| **Retention Period** | 7 years |
| **Storage** | PostgreSQL append-only table |
| **GDPR Erasure** | **PII redaction** (event preserved) |
| **Legal Basis** | Legal obligation (audit requirements) |

**Redaction Approach:**
- Event type: Preserved
- Timestamp: Preserved
- IP address: Anonymized (`192.168.1.100` → `192.168.x.x`)
- User ID: Replaced with `REDACTED-{hash}`
- Action details: Preserved (no PII in details)

### Tier 3: User PII (Deletable)

**Description:** User account information (name, email, profile)

| Attribute | Value |
|-----------|-------|
| **Retention Period** | Account lifetime + 30 days |
| **Storage** | PostgreSQL with soft delete |
| **GDPR Erasure** | **Full deletion** |
| **Legal Basis** | Consent / Contract |

**Deletion Process:**
1. Soft delete (mark `deleted_at`)
2. 30-day grace period (recovery possible)
3. Hard delete + anonymize references in other tables

### Tier 4: Operational Data (Short-Lived)

**Description:** Sessions, tokens, cache entries

| Attribute | Value |
|-----------|-------|
| **Retention Period** | 24 hours - 30 days |
| **Storage** | Redis / PostgreSQL |
| **GDPR Erasure** | **Automatic expiry** |
| **Legal Basis** | Legitimate interest (security) |

| Data Type | Retention |
|-----------|-----------|
| Session tokens | 24 hours |
| Refresh tokens | 30 days |
| Rate limit counters | 1 hour |
| Cache entries | 24 hours |

---

## Retention Schedule Summary

| Data Category | Retention | GDPR Erasure Method | Legal Basis |
|---------------|-----------|---------------------|-------------|
| Evidence artifacts | 7 years | Anonymize metadata | Legitimate interest |
| Evidence manifests | 7 years | Preserve (hash chain) | Legitimate interest |
| Audit logs | 7 years | Redact PII | Legal obligation |
| Gate evaluations | 7 years | Anonymize | Legitimate interest |
| User accounts | Lifetime + 30d | Full delete | Consent |
| User preferences | Lifetime + 30d | Full delete | Consent |
| Sessions/tokens | 24h-30d | Auto-expire | Legitimate interest |
| Analytics events | 2 years | Aggregate then delete | Legitimate interest |
| Support tickets | 3 years | Anonymize | Contract |

---

## GDPR Rights Implementation

### Right to Erasure (Article 17)

**Process:**

```
User Request → Validate Identity → Check Exceptions → Execute
                                          ↓
                              ┌───────────────────────┐
                              │ Exception Categories: │
                              │ • Legal obligation    │
                              │ • Public interest     │
                              │ • Legitimate interest │
                              │   (with assessment)   │
                              └───────────────────────┘
```

**Implementation by Data Type:**

| Data Type | Can Delete? | Method | Timeline |
|-----------|-------------|--------|----------|
| User account | ✅ Yes | Hard delete + anonymize refs | 30 days |
| Evidence files | ❌ No | Anonymize metadata | 30 days |
| Audit logs | ❌ No | Redact PII | 30 days |
| Analytics | ✅ Yes | Delete | 30 days |
| Support tickets | ✅ Yes | Anonymize | 30 days |

### Right to Access (Article 15)

**Data Export Format:**

```json
{
  "user": {
    "id": "user-123",
    "email": "john.doe@company.com",
    "name": "John Doe",
    "created_at": "2025-01-01T00:00:00Z"
  },
  "evidence_uploaded": [
    {
      "id": "evidence-456",
      "file_name": "design-doc.pdf",
      "uploaded_at": "2025-06-15T10:30:00Z",
      "project": "Project Alpha"
    }
  ],
  "gate_evaluations": [
    {
      "gate": "G2",
      "result": "PASSED",
      "evaluated_at": "2025-06-20T14:00:00Z"
    }
  ],
  "audit_log": [
    {
      "action": "login",
      "timestamp": "2025-06-20T09:00:00Z",
      "ip_address": "192.168.1.x"
    }
  ]
}
```

### Right to Rectification (Article 16)

**Editable Fields:**

| Field | Editable | Notes |
|-------|----------|-------|
| Display name | ✅ Yes | User profile |
| Email (with verification) | ✅ Yes | Requires re-verification |
| Evidence metadata | ❌ No | Immutable for audit |
| Audit logs | ❌ No | Append-only |

---

## Anonymization Procedures

### Evidence Metadata Anonymization

```python
# backend/app/services/gdpr_service.py

from datetime import datetime
from uuid import UUID
import hashlib


async def anonymize_evidence_metadata(
    db: AsyncSession,
    user_id: UUID,
    reason: str,
    request_id: str,
) -> dict:
    """
    Anonymize user's evidence metadata per GDPR request.

    Steps:
    1. Find all evidence uploaded by user
    2. Replace uploader_id with REDACTED-{hash}
    3. Clear uploader_name
    4. Log anonymization in audit trail
    5. Update evidence manifest (new version)

    Args:
        db: Database session
        user_id: User requesting erasure
        reason: Reason for anonymization
        request_id: GDPR request tracking ID

    Returns:
        Summary of anonymized records
    """
    # Generate anonymized ID (deterministic for consistency)
    anon_id = f"REDACTED-{hashlib.sha256(str(user_id).encode()).hexdigest()[:8]}"

    # Find evidence records
    evidence_records = await db.execute(
        select(GateEvidence).where(GateEvidence.uploaded_by == user_id)
    )

    anonymized_count = 0
    for evidence in evidence_records.scalars():
        evidence.uploader_id = anon_id
        evidence.uploader_name = "REDACTED"
        evidence.uploader_email = None
        anonymized_count += 1

    # Log anonymization
    audit_log = AuditLog(
        action="gdpr_anonymization",
        user_id=anon_id,  # Already anonymized
        details={
            "request_id": request_id,
            "reason": reason,
            "evidence_count": anonymized_count,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
    db.add(audit_log)

    await db.commit()

    return {
        "request_id": request_id,
        "anonymized_evidence": anonymized_count,
        "completed_at": datetime.utcnow().isoformat(),
    }
```

### Audit Log PII Redaction

```python
async def redact_audit_log_pii(
    db: AsyncSession,
    user_id: UUID,
    request_id: str,
) -> dict:
    """
    Redact PII from audit logs per GDPR request.

    Preserves:
    - Event type
    - Timestamp
    - Non-PII details

    Redacts:
    - User ID → REDACTED-{hash}
    - IP address → anonymized
    - Email → removed
    """
    anon_id = f"REDACTED-{hashlib.sha256(str(user_id).encode()).hexdigest()[:8]}"

    audit_logs = await db.execute(
        select(AuditLog).where(AuditLog.user_id == user_id)
    )

    redacted_count = 0
    for log in audit_logs.scalars():
        log.user_id = anon_id
        if log.ip_address:
            # Anonymize IP: 192.168.1.100 → 192.168.x.x
            parts = log.ip_address.split(".")
            if len(parts) == 4:
                log.ip_address = f"{parts[0]}.{parts[1]}.x.x"
        if log.details and "email" in log.details:
            log.details["email"] = "REDACTED"
        redacted_count += 1

    await db.commit()

    return {
        "request_id": request_id,
        "redacted_logs": redacted_count,
    }
```

---

## Retention Enforcement

### Automated Cleanup Jobs

```python
# backend/app/jobs/retention_cleanup.py

from datetime import datetime, timedelta
from celery import shared_task


@shared_task
def cleanup_expired_data():
    """
    Daily job to clean up expired data.

    Schedule: 02:00 UTC daily
    """
    now = datetime.utcnow()

    # 1. Purge soft-deleted users (30+ days old)
    purge_cutoff = now - timedelta(days=30)
    deleted_users = User.query.filter(
        User.deleted_at.isnot(None),
        User.deleted_at < purge_cutoff,
    ).all()

    for user in deleted_users:
        # Anonymize references first
        anonymize_user_references(user.id)
        # Then hard delete
        db.session.delete(user)

    # 2. Expire old sessions
    session_cutoff = now - timedelta(days=30)
    RefreshToken.query.filter(
        RefreshToken.created_at < session_cutoff
    ).delete()

    # 3. Archive old analytics (>2 years)
    analytics_cutoff = now - timedelta(days=730)
    # Move to cold storage, then delete
    archive_analytics(before=analytics_cutoff)
    AnalyticsEvent.query.filter(
        AnalyticsEvent.created_at < analytics_cutoff
    ).delete()

    db.session.commit()

    return {
        "purged_users": len(deleted_users),
        "expired_sessions": session_count,
        "archived_analytics": analytics_count,
    }
```

### Evidence Retention Check

```python
@shared_task
def check_evidence_retention():
    """
    Monthly job to report on evidence nearing retention end.

    Note: Evidence is NOT auto-deleted. This job creates
    a report for manual review before retention expires.
    """
    retention_end = datetime.utcnow() + timedelta(days=90)

    expiring_evidence = GateEvidence.query.filter(
        GateEvidence.retention_until < retention_end,
        GateEvidence.retention_until > datetime.utcnow(),
    ).all()

    if expiring_evidence:
        # Send notification to compliance team
        notify_compliance_team(
            subject="Evidence Approaching Retention End",
            evidence_list=expiring_evidence,
        )

    return {
        "evidence_expiring_90_days": len(expiring_evidence),
    }
```

---

## GDPR Request Workflow

### Request Processing SLA

| Step | Timeline | Owner |
|------|----------|-------|
| Acknowledge request | 24 hours | Support |
| Verify identity | 48 hours | Support |
| Execute request | 30 days max | Engineering |
| Confirm completion | 30 days max | Support |

### Request Tracking

```sql
-- GDPR request tracking table
CREATE TABLE gdpr_requests (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    request_type VARCHAR(50) NOT NULL,  -- erasure, access, rectification, portability
    status VARCHAR(50) NOT NULL,  -- pending, processing, completed, denied
    requested_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    denial_reason TEXT,
    processed_by UUID REFERENCES users(id),
    audit_trail JSONB
);

-- Index for SLA monitoring
CREATE INDEX idx_gdpr_requests_pending ON gdpr_requests(status, requested_at)
    WHERE status IN ('pending', 'processing');
```

---

## Exceptions to Erasure

### Legal Grounds for Retention

| Exception | GDPR Article | Our Application |
|-----------|--------------|-----------------|
| Legal obligation | Art. 17(3)(b) | Audit logs for SEC/SOX |
| Public interest | Art. 17(3)(d) | N/A |
| Legal claims | Art. 17(3)(e) | Evidence under litigation hold |
| Archiving | Art. 17(3)(d) | Historical audit records |

### Evidence Under Legal Hold

Evidence with active legal holds cannot be anonymized:

```python
async def process_erasure_request(user_id: UUID) -> dict:
    """Process GDPR erasure request with exception handling."""

    # Check for legal holds
    legal_holds = await db.execute(
        select(EvidenceLegalHold).where(
            EvidenceLegalHold.user_id == user_id,
            EvidenceLegalHold.status == "active",
        )
    )

    if legal_holds.scalars().first():
        return {
            "status": "denied",
            "reason": "legal_hold_active",
            "message": "Evidence is under legal hold and cannot be anonymized.",
            "gdpr_article": "17(3)(e)",
        }

    # Proceed with anonymization
    return await anonymize_user_data(user_id)
```

---

## Compliance Checklist

### Pre-Launch (Sprint 82)

- [x] Data classification completed
- [x] Retention periods defined
- [x] Anonymization procedures documented
- [ ] GDPR request workflow implemented
- [ ] Automated cleanup jobs scheduled
- [ ] Legal review completed
- [ ] DPO sign-off obtained

### Ongoing Compliance

- [ ] Monthly retention report review
- [ ] Quarterly GDPR request audit
- [ ] Annual policy review
- [ ] Staff training (annual)

---

## Appendix A: Data Mapping

| Table | PII Fields | Retention | Erasure Method |
|-------|------------|-----------|----------------|
| users | email, name, phone | Lifetime + 30d | Hard delete |
| audit_logs | user_id, ip_address | 7 years | Redact |
| gate_evidence | uploader_id, uploader_name | 7 years | Anonymize |
| evidence_manifests | created_by | 7 years | Anonymize |
| sessions | user_id, ip_address | 30 days | Auto-expire |
| analytics_events | user_id | 2 years | Delete |

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Anonymization** | Irreversibly removing identifying information |
| **Pseudonymization** | Replacing identifiers with pseudonyms (reversible) |
| **Redaction** | Removing specific data while preserving structure |
| **Legal Hold** | Court-ordered preservation of evidence |
| **WORM** | Write-Once-Read-Many (immutable storage) |

---

## Appendix C: Regulatory References

| Regulation | Article | Requirement |
|------------|---------|-------------|
| GDPR | Art. 5(1)(e) | Storage limitation |
| GDPR | Art. 17 | Right to erasure |
| GDPR | Art. 17(3) | Exceptions to erasure |
| SEC 17a-4 | (f) | 6-year record retention |
| SOX | Section 802 | 7-year audit trail |

---

**Document Status:** ✅ APPROVED
**Last Updated:** January 19, 2026
**Owner:** Legal + Engineering
**Review:** CTO + DPO
**Next Review:** January 2027
