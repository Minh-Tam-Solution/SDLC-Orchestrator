# MinIO Object Lock (WORM) Configuration Guide

**Version:** 1.0.0
**Date:** January 19, 2026
**Status:** ACTIVE - Sprint 82 (Pre-Launch Hardening)
**Authority:** DevOps Lead + CTO Approved
**Framework:** SDLC 6.0.6 P7 (Documentation Permanence, RFC-001)
**Compliance:** SEC 17a-4, FINRA 4511, GDPR Art. 17

---

## Overview

This guide covers configuring MinIO Object Lock for the SDLC Orchestrator Evidence Vault. Object Lock provides Write-Once-Read-Many (WORM) compliance, ensuring evidence cannot be modified or deleted during the retention period.

### Why Object Lock?

| Requirement | Solution |
|-------------|----------|
| Evidence immutability | Objects locked for retention period |
| Audit compliance | SEC 17a-4, FINRA 4511 compliant |
| 7-year retention | Legal hold + governance mode |
| GDPR compatibility | Anonymization allowed via metadata |

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| MinIO Server | RELEASE.2024-01-01+ | Object Lock support |
| MinIO Client (mc) | Latest | For configuration |
| TLS Enabled | Required | For production |
| Versioning | Auto-enabled | Required for Object Lock |

---

## Part 1: Enable Object Lock on Bucket

### Step 1: Create Bucket with Object Lock Enabled

Object Lock must be enabled at bucket creation time and cannot be added later.

```bash
# Create bucket with Object Lock
mc mb myminio/sdlc-evidence --with-lock

# Verify Object Lock status
mc stat myminio/sdlc-evidence
# Should show: Object Lock: Enabled
```

### Step 2: Configure Default Retention Policy

```bash
# Set default retention: 7 years (2555 days) in GOVERNANCE mode
mc retention set --default GOVERNANCE "2555d" myminio/sdlc-evidence

# Verify retention policy
mc retention info --default myminio/sdlc-evidence
# Output: GOVERNANCE mode, 2555 days retention
```

### Retention Modes

| Mode | Can Delete? | Can Override? | Use Case |
|------|-------------|---------------|----------|
| **GOVERNANCE** | With special permission | Yes, with `s3:BypassGovernanceRetention` | Standard compliance |
| **COMPLIANCE** | No, never | No | Legal/regulatory (SEC 17a-4) |

**Recommendation:** Use GOVERNANCE mode for flexibility, restrict bypass permission.

---

## Part 2: Object-Level Retention

### Uploading with Retention

```bash
# Upload with specific retention period
mc cp evidence.pdf myminio/sdlc-evidence/project-123/evidence.pdf \
  --retention-mode governance \
  --retention-duration 7y

# Upload with retention until specific date
mc cp evidence.pdf myminio/sdlc-evidence/project-123/evidence.pdf \
  --retention-mode governance \
  --retention-retain-until "2033-01-19T00:00:00Z"
```

### Legal Hold

Legal hold prevents deletion regardless of retention mode:

```bash
# Enable legal hold (e.g., for ongoing investigation)
mc legalhold set myminio/sdlc-evidence/project-123/evidence.pdf

# Check legal hold status
mc legalhold info myminio/sdlc-evidence/project-123/evidence.pdf

# Remove legal hold (when investigation complete)
mc legalhold clear myminio/sdlc-evidence/project-123/evidence.pdf
```

---

## Part 3: Backend Integration

### MinIO Service Update

Update `minio_service.py` to use Object Lock:

```python
# backend/app/services/minio_service.py

import hashlib
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import requests
from app.core.config import settings


class MinIOService:
    """
    MinIO Evidence Vault service with Object Lock (WORM) support.

    Sprint 82 Enhancement:
    - Object Lock for WORM compliance
    - 7-year default retention
    - Legal hold support

    AGPL-Safe: Network-only access via S3 API.
    """

    def __init__(self):
        self.endpoint = settings.MINIO_ENDPOINT
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.bucket = settings.EVIDENCE_BUCKET
        self.retention_days = settings.EVIDENCE_RETENTION_DAYS  # 2555 = ~7 years

    async def upload_evidence(
        self,
        project_id: UUID,
        file_content: bytes,
        file_name: str,
        content_type: str = "application/octet-stream",
        retention_mode: str = "GOVERNANCE",
        legal_hold: bool = False,
    ) -> dict:
        """
        Upload evidence with Object Lock protection.

        Args:
            project_id: Project UUID
            file_content: File bytes
            file_name: Original file name
            content_type: MIME type
            retention_mode: "GOVERNANCE" or "COMPLIANCE"
            legal_hold: Enable legal hold

        Returns:
            dict with path, sha256, version_id, retention_until
        """
        # Calculate SHA256
        sha256 = hashlib.sha256(file_content).hexdigest()

        # Generate object path
        object_path = f"evidence/{project_id}/{sha256}/{file_name}"

        # Calculate retention date
        retention_until = datetime.utcnow() + timedelta(days=self.retention_days)

        # Upload with Object Lock headers
        headers = {
            "Content-Type": content_type,
            "x-amz-object-lock-mode": retention_mode,
            "x-amz-object-lock-retain-until-date": retention_until.isoformat() + "Z",
        }

        if legal_hold:
            headers["x-amz-object-lock-legal-hold"] = "ON"

        # Use S3 API (AGPL-safe network-only access)
        response = requests.put(
            f"{self.endpoint}/{self.bucket}/{object_path}",
            data=file_content,
            headers=headers,
            auth=(self.access_key, self.secret_key),
            timeout=30,
        )
        response.raise_for_status()

        return {
            "path": f"s3://{self.bucket}/{object_path}",
            "sha256": sha256,
            "version_id": response.headers.get("x-amz-version-id"),
            "retention_until": retention_until.isoformat(),
            "retention_mode": retention_mode,
            "legal_hold": legal_hold,
            "size_bytes": len(file_content),
        }

    async def set_legal_hold(
        self,
        object_path: str,
        enabled: bool = True,
    ) -> bool:
        """
        Enable/disable legal hold on evidence.

        Use for:
        - Ongoing investigations
        - Litigation hold
        - Regulatory inquiries

        Args:
            object_path: Full S3 path
            enabled: True to enable, False to disable

        Returns:
            True if successful
        """
        # Extract bucket and key from path
        # s3://bucket/key -> bucket, key
        path_parts = object_path.replace("s3://", "").split("/", 1)
        bucket = path_parts[0]
        key = path_parts[1]

        response = requests.put(
            f"{self.endpoint}/{bucket}/{key}?legal-hold",
            data=f'<LegalHold><Status>{"ON" if enabled else "OFF"}</Status></LegalHold>',
            headers={"Content-Type": "application/xml"},
            auth=(self.access_key, self.secret_key),
            timeout=10,
        )

        return response.status_code == 200

    async def get_retention_info(self, object_path: str) -> dict:
        """Get retention and legal hold status for object."""
        path_parts = object_path.replace("s3://", "").split("/", 1)
        bucket = path_parts[0]
        key = path_parts[1]

        # Get object lock configuration
        response = requests.get(
            f"{self.endpoint}/{bucket}/{key}?retention",
            auth=(self.access_key, self.secret_key),
            timeout=10,
        )

        # Parse response
        # (In production, use proper XML parsing)
        return {
            "has_retention": response.status_code == 200,
            "retention_response": response.text if response.status_code == 200 else None,
        }
```

### Configuration Settings

Add to `config.py`:

```python
# backend/app/core/config.py

class Settings(BaseSettings):
    # ... existing settings ...

    # MinIO Object Lock Configuration (Sprint 82)
    EVIDENCE_RETENTION_DAYS: int = 2555  # ~7 years
    EVIDENCE_RETENTION_MODE: str = "GOVERNANCE"  # or "COMPLIANCE"
    EVIDENCE_LEGAL_HOLD_DEFAULT: bool = False
```

---

## Part 4: Docker Compose Configuration

### Development Environment

```yaml
# docker-compose.yml
services:
  minio:
    image: minio/minio:RELEASE.2024-01-01T00-00-00Z
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

volumes:
  minio_data:
```

### Initialization Script

```bash
#!/bin/bash
# scripts/init-minio.sh

# Wait for MinIO to start
until curl -s http://localhost:9000/minio/health/live; do
  echo "Waiting for MinIO..."
  sleep 2
done

# Configure mc alias
mc alias set myminio http://localhost:9000 minioadmin minioadmin

# Create evidence bucket with Object Lock
mc mb myminio/sdlc-evidence --with-lock --ignore-existing

# Set default retention policy (7 years)
mc retention set --default GOVERNANCE "2555d" myminio/sdlc-evidence

# Create manifest bucket with Object Lock
mc mb myminio/sdlc-manifests --with-lock --ignore-existing
mc retention set --default GOVERNANCE "2555d" myminio/sdlc-manifests

echo "MinIO buckets configured with Object Lock"
```

---

## Part 5: Production Deployment

### Kubernetes Configuration

```yaml
# k8s/minio-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: minio-object-lock-config
  namespace: sdlc-orchestrator
data:
  MINIO_OBJECT_LOCK_ENABLED: "true"
  EVIDENCE_RETENTION_DAYS: "2555"
  EVIDENCE_RETENTION_MODE: "GOVERNANCE"
```

### Initialization Job

```yaml
# k8s/minio-init-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: minio-init-buckets
  namespace: sdlc-orchestrator
spec:
  template:
    spec:
      containers:
      - name: init
        image: minio/mc:latest
        command:
        - /bin/sh
        - -c
        - |
          mc alias set myminio $MINIO_ENDPOINT $MINIO_ACCESS_KEY $MINIO_SECRET_KEY
          mc mb myminio/sdlc-evidence --with-lock --ignore-existing
          mc retention set --default GOVERNANCE "2555d" myminio/sdlc-evidence
          mc mb myminio/sdlc-manifests --with-lock --ignore-existing
          mc retention set --default GOVERNANCE "2555d" myminio/sdlc-manifests
        envFrom:
        - secretRef:
            name: minio-credentials
      restartPolicy: OnFailure
```

---

## Part 6: GDPR Compliance with Object Lock

### The Challenge

GDPR requires "right to erasure" (Art. 17), but Object Lock prevents deletion.

### Solution: Anonymization

Instead of deleting evidence, anonymize personal data:

```python
async def anonymize_evidence_metadata(
    self,
    object_path: str,
    anonymized_fields: dict,
) -> bool:
    """
    Anonymize metadata while preserving evidence integrity.

    GDPR Art. 17 Compliance:
    - Evidence file remains (for audit trail)
    - Personal data in metadata is replaced with "REDACTED-{hash}"
    - Original uploader reference anonymized

    Args:
        object_path: S3 path to evidence
        anonymized_fields: {field: "REDACTED-xxx"} mapping

    Returns:
        True if successful
    """
    # Copy object to new version with anonymized metadata
    # Original version still protected by Object Lock
    # New version has anonymized metadata
    pass  # Implementation depends on versioning strategy
```

### Data Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    Evidence Lifecycle                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Upload ──→ Object Lock (7 years) ──→ Retention Expires ──→ Delete │
│     │                                                            │
│     │   GDPR Request?                                           │
│     ▼                                                            │
│  Anonymize Metadata                                              │
│  (Personal data → REDACTED)                                      │
│                                                                  │
│  Evidence file: PRESERVED (audit integrity)                      │
│  User identity: REDACTED (GDPR compliant)                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 7: Monitoring & Alerting

### Key Metrics

| Metric | Alert Threshold | Action |
|--------|-----------------|--------|
| `minio_bucket_usage_bytes` | >80% capacity | Expand storage |
| `minio_object_lock_failures` | >0 | Investigate immediately |
| `minio_objects_nearing_expiry` | Report daily | Audit before deletion |
| `minio_legal_hold_count` | Track | Document holds |

### Prometheus Metrics

```yaml
# prometheus/minio-alerts.yaml
groups:
- name: minio-object-lock
  rules:
  - alert: MinIOObjectLockFailure
    expr: increase(minio_s3_requests_error_total{api="PutObjectRetention"}[5m]) > 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "MinIO Object Lock operation failed"

  - alert: MinIOCapacityWarning
    expr: minio_bucket_usage_total_bytes / minio_bucket_quota_bytes > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "MinIO bucket approaching capacity limit"
```

---

## Part 8: Verification Checklist

### Pre-Production

- [ ] Object Lock enabled on evidence bucket
- [ ] Default retention policy set (GOVERNANCE, 2555 days)
- [ ] Versioning enabled (auto with Object Lock)
- [ ] TLS enabled for MinIO endpoint
- [ ] Access keys rotated and stored in Vault

### Post-Production

- [ ] Test upload with Object Lock headers
- [ ] Verify cannot delete locked object (should fail)
- [ ] Test legal hold enable/disable
- [ ] Verify retention date on uploaded objects
- [ ] Monitor Object Lock metrics

### Compliance Verification

```bash
# Verify bucket has Object Lock
mc stat myminio/sdlc-evidence | grep "Object Lock"

# Verify default retention
mc retention info --default myminio/sdlc-evidence

# Test deletion fails on locked object
mc rm myminio/sdlc-evidence/test-object.pdf
# Expected: ERROR: Object locked, cannot delete

# Verify object retention
mc stat myminio/sdlc-evidence/project-123/evidence.pdf
# Should show retention mode and date
```

---

## Appendix A: Retention Periods by Regulation

| Regulation | Required Period | Recommended Setting |
|------------|-----------------|---------------------|
| SEC 17a-4 | 6 years | 7 years (buffer) |
| FINRA 4511 | 6 years | 7 years |
| SOX | 7 years | 7 years |
| GDPR | "No longer than necessary" | 7 years (with anonymization) |
| HIPAA | 6 years | 7 years |

---

## Appendix B: Emergency Procedures

### Removing Object Lock (GOVERNANCE mode only)

Only users with `s3:BypassGovernanceRetention` permission can bypass:

```bash
# Bypass governance retention (EMERGENCY ONLY - requires audit)
mc rm myminio/sdlc-evidence/object.pdf --bypass-governance-retention

# This action is logged and should trigger an alert
```

### Legal Hold Override

Legal hold can only be removed by authorized personnel:

```bash
# Remove legal hold (requires audit approval)
mc legalhold clear myminio/sdlc-evidence/project-123/evidence.pdf

# Document reason in audit log
```

---

## References

- [MinIO Object Lock Guide](https://min.io/docs/minio/linux/administration/object-management/object-retention.html)
- [AWS S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)
- [SEC Rule 17a-4](https://www.sec.gov/rules/interp/34-47806.htm)
- [GDPR Article 17](https://gdpr-info.eu/art-17-gdpr/)

---

**Document Status:** ✅ APPROVED
**Last Updated:** January 19, 2026
**Owner:** DevOps Lead
**Review:** CTO + Legal
