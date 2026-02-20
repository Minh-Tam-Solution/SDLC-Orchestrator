# Sprint 82: Pre-Launch Hardening - Evidence Hash Chain

**Sprint ID:** S82
**Status:** DRAFT - Pending Sprint 81 Completion
**Duration:** 10 days (March 3-14, 2026)
**Goal:** Implement tamper-evident Evidence Vault + Complete GitHub App setup + MinIO Object Lock
**Story Points:** 38 SP
**Framework Reference:** SDLC 6.1.0 P4 (Quality Gates) + P7 (Documentation Permanence)
**Prerequisite:** Sprint 81 ✅ COMPLETE
**Launch Gate:** Go/No-Go Review Feb 28, 2026

---

## CTO Priority Reference (Pre-Launch Hardening Plan)

| Priority | Task | Sprint 82 Scope | Original Deadline |
|----------|------|-----------------|-------------------|
| **P0** | Evidence hash chain v1 | ✅ Primary focus | Feb 10 (+5 days buffer) |
| **P0** | GitHub Check Run (Advisory→Blocking) | ✅ Secondary focus | Jan 28 |
| **P1** | MinIO Object Lock config | ✅ Included | Jan 25 |
| **P1** | GDPR vs Retention policy documentation | ✅ Included | Feb 1 |
| **P2** | PostgreSQL RLS policies | ✅ Foundation | Feb 20 |

---

## 🎯 Sprint 82 Objectives

### Primary Goals (P0 - LAUNCH BLOCKERS)

1. **Evidence Hash Chain v1** - Tamper-evident manifest with hash chain linking
2. **GitHub App Registration** - Complete DevOps setup from Sprint 81 blockers
3. **Check Run Enforcement Mode** - Upgrade from Advisory to Blocking mode

### Secondary Goals (P1 - SCALE BLOCKERS)

4. **MinIO Object Lock** - WORM compliance for Evidence Vault
5. **GDPR Retention Policy** - Legal compliance documentation
6. **Rate Limiting** - PR webhook rate limiting (10 Check Runs/min/repo)

### Foundation (P2)

7. **PostgreSQL RLS Foundation** - Design + first policy implementation

---

## 📋 Sprint 82 Backlog

### Day 1-4: Evidence Hash Chain v1 (16 SP)

**Problem Statement:**
- Current Evidence Vault only has SHA256 per-file hash
- No hash chain linking artifacts (can't detect deletions)
- No signed manifest for audit
- Files can be deleted (not immutable)

**Solution: Tamper-Evident Manifest**

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `EvidenceManifest` model | Backend | 3h | P0 | ⏳ |
| Create `EvidenceManifestService` | Backend | 4h | P0 | ⏳ |
| Implement hash chain (previous_hash linking) | Backend | 4h | P0 | ⏳ |
| HMAC-SHA256 manifest signing | Backend | 3h | P0 | ⏳ |
| Database migration for manifests table | Backend | 2h | P0 | ⏳ |
| Update `MinIOService` to call manifest on upload | Backend | 2h | P0 | ⏳ |
| Manifest verification endpoint | Backend | 3h | P0 | ⏳ |
| Unit tests (15 tests) | Backend | 4h | P0 | ⏳ |
| Integration tests (8 tests) | QA | 3h | P0 | ⏳ |

**Technical Design:**

```python
# backend/app/models/evidence_manifest.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class EvidenceManifest(Base):
    """
    Tamper-evident manifest for Evidence Vault.

    Design:
    1. Each artifact gets SHA256 hash stored in manifest entry
    2. Manifest includes previous_manifest_hash (chain)
    3. Manifest is signed with server key (HMAC-SHA256)
    4. Stored in manifests table (append-only design)

    Chain verification:
    - manifest_n.previous_hash == SHA256(manifest_n-1)
    - Any tampering breaks the chain
    """
    __tablename__ = "evidence_manifests"

    id = Column(PGUUID(as_uuid=True), primary_key=True)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    # Hash chain
    manifest_hash = Column(String(64), nullable=False, unique=True)  # SHA256 of this manifest
    previous_manifest_hash = Column(String(64), nullable=True)  # Links to previous (NULL for first)

    # Artifacts in this manifest
    artifacts = Column(JSONB, nullable=False)  # [{artifact_id, sha256, path, size, uploaded_at}]

    # Signing
    signature = Column(String(128), nullable=False)  # HMAC-SHA256 with server secret

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="evidence_manifests")


# backend/app/services/evidence_manifest_service.py
import hashlib
import hmac
import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.evidence_manifest import EvidenceManifest


class ArtifactEntry:
    """Single artifact entry in manifest."""
    artifact_id: UUID
    sha256: str
    path: str
    size: int
    uploaded_at: datetime


class EvidenceManifestService:
    """
    Tamper-evident manifest service for Evidence Vault.

    Flow:
    1. On artifact upload → add_artifact()
    2. Periodically (or on batch) → create_manifest()
    3. On audit → verify_chain()
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._secret_key = settings.EVIDENCE_MANIFEST_SECRET_KEY

    async def create_manifest(
        self,
        project_id: UUID,
        artifacts: List[ArtifactEntry],
        created_by: Optional[UUID] = None,
    ) -> EvidenceManifest:
        """
        Create new manifest with hash chain.

        Args:
            project_id: Project owning the evidence
            artifacts: List of artifacts to include
            created_by: User creating manifest (optional)

        Returns:
            Created manifest with computed hashes
        """
        # Get previous manifest
        previous = await self._get_latest_manifest(project_id)
        previous_hash = previous.manifest_hash if previous else None

        # Build manifest content
        manifest_id = uuid4()
        artifacts_json = [
            {
                "artifact_id": str(a.artifact_id),
                "sha256": a.sha256,
                "path": a.path,
                "size": a.size,
                "uploaded_at": a.uploaded_at.isoformat(),
            }
            for a in artifacts
        ]

        # Compute manifest hash
        content_to_hash = json.dumps({
            "manifest_id": str(manifest_id),
            "project_id": str(project_id),
            "previous_hash": previous_hash,
            "artifacts": artifacts_json,
        }, sort_keys=True)

        manifest_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()

        # Sign manifest
        signature = self._sign_manifest(manifest_hash)

        # Create record
        manifest = EvidenceManifest(
            id=manifest_id,
            project_id=project_id,
            manifest_hash=manifest_hash,
            previous_manifest_hash=previous_hash,
            artifacts=artifacts_json,
            signature=signature,
            created_at=datetime.utcnow(),
            created_by=created_by,
        )

        self.db.add(manifest)
        await self.db.commit()
        await self.db.refresh(manifest)

        return manifest

    async def verify_chain(self, project_id: UUID) -> dict:
        """
        Verify entire hash chain for project.

        Returns:
            {
                "valid": bool,
                "manifests_checked": int,
                "broken_at": Optional[UUID],  # First broken manifest
                "error": Optional[str]
            }
        """
        stmt = (
            select(EvidenceManifest)
            .where(EvidenceManifest.project_id == project_id)
            .order_by(EvidenceManifest.created_at.asc())
        )
        result = await self.db.execute(stmt)
        manifests = result.scalars().all()

        if not manifests:
            return {"valid": True, "manifests_checked": 0}

        for i, manifest in enumerate(manifests):
            # Verify signature
            expected_sig = self._sign_manifest(manifest.manifest_hash)
            if manifest.signature != expected_sig:
                return {
                    "valid": False,
                    "manifests_checked": i + 1,
                    "broken_at": manifest.id,
                    "error": f"Invalid signature on manifest {manifest.id}",
                }

            # Verify chain link (except first)
            if i > 0:
                expected_previous = manifests[i - 1].manifest_hash
                if manifest.previous_manifest_hash != expected_previous:
                    return {
                        "valid": False,
                        "manifests_checked": i + 1,
                        "broken_at": manifest.id,
                        "error": f"Chain broken at manifest {manifest.id}",
                    }

        return {
            "valid": True,
            "manifests_checked": len(manifests),
        }

    def _sign_manifest(self, manifest_hash: str) -> str:
        """Sign manifest hash with HMAC-SHA256."""
        return hmac.new(
            self._secret_key.encode(),
            manifest_hash.encode(),
            hashlib.sha256,
        ).hexdigest()

    async def _get_latest_manifest(
        self, project_id: UUID
    ) -> Optional[EvidenceManifest]:
        """Get most recent manifest for project."""
        stmt = (
            select(EvidenceManifest)
            .where(EvidenceManifest.project_id == project_id)
            .order_by(EvidenceManifest.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
```

**Database Migration:**

```python
# backend/alembic/versions/s82_001_evidence_manifests.py
"""
Create evidence_manifests table for tamper-evident audit trail.

Sprint 82 - Evidence Hash Chain v1
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 's82_001_evidence_manifests'
down_revision = 's81_xxx'  # Previous migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'evidence_manifests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('manifest_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('previous_manifest_hash', sa.String(64), nullable=True),
        sa.Column('artifacts', postgresql.JSONB, nullable=False),
        sa.Column('signature', sa.String(128), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )

    # Indexes
    op.create_index('ix_evidence_manifests_project_id', 'evidence_manifests', ['project_id'])
    op.create_index('ix_evidence_manifests_created_at', 'evidence_manifests', ['created_at'])
    op.create_index('ix_evidence_manifests_previous_hash', 'evidence_manifests', ['previous_manifest_hash'])


def downgrade() -> None:
    op.drop_table('evidence_manifests')
```

**API Endpoints:**

```yaml
# New endpoints for Evidence Manifest
POST /api/v1/evidence/{project_id}/manifests:
  summary: Create new evidence manifest
  tags: [Evidence]
  request_body:
    artifact_ids: array[UUID]  # Artifacts to include
  response:
    manifest_id: UUID
    manifest_hash: string
    artifacts_count: int

GET /api/v1/evidence/{project_id}/manifests:
  summary: List evidence manifests
  tags: [Evidence]
  query_params:
    limit: int (default: 20)
    offset: int (default: 0)
  response:
    items: array[Manifest]
    total: int

GET /api/v1/evidence/{project_id}/manifests/verify:
  summary: Verify hash chain integrity
  tags: [Evidence]
  response:
    valid: boolean
    manifests_checked: int
    broken_at: UUID (optional)
    error: string (optional)

GET /api/v1/evidence/{project_id}/manifests/{manifest_id}:
  summary: Get specific manifest
  tags: [Evidence]
  response:
    id: UUID
    manifest_hash: string
    previous_manifest_hash: string
    artifacts: array
    signature: string
    created_at: datetime
```

---

### Day 5-6: GitHub App Production Setup (6 SP)

**Pre-Sprint Blocker Resolution:**

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Register GitHub App in production | DevOps | 2h | P0 | ⏳ |
| Generate and store private key in Vault | DevOps | 1h | P0 | ⏳ |
| Configure webhook URL | DevOps | 1h | P0 | ⏳ |
| Test App installation flow | DevOps | 2h | P0 | ⏳ |
| Update staging environment | DevOps | 2h | P0 | ⏳ |
| Documentation for self-hosted setup | PM | 2h | P1 | ⏳ |

**GitHub App Configuration:**

```yaml
# GitHub App Settings
Name: SDLC Orchestrator
Description: AI Dev Governance Platform - Quality Gate Enforcement
Homepage URL: https://sdlc.nhatquangholding.com
Callback URL: https://sdlc.nhatquangholding.com/auth/github/callback
Webhook URL: https://sdlc.nhatquangholding.com/api/v1/webhooks/github
Webhook Secret: [HashiCorp Vault - github/webhook_secret]

Permissions:
  Repository:
    - checks: write
    - contents: read
    - metadata: read
    - pull_requests: read

Events:
  - pull_request
  - check_run

Post-Installation Setup URL: https://sdlc.nhatquangholding.com/setup/github
```

---

### Day 7: Check Run Blocking Mode (4 SP)

**Upgrade from Advisory to Enforcement:**

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Add `blocking_mode` config per project | Backend | 2h | P0 | ⏳ |
| Update conclusion logic (failure → blocks) | Backend | 2h | P0 | ⏳ |
| Add bypass label (`sdlc-bypass`) | Backend | 1h | P1 | ⏳ |
| Update documentation | PM | 1h | P0 | ⏳ |
| Integration tests | QA | 2h | P0 | ⏳ |

**Check Run Enforcement Modes:**

```python
# backend/app/services/github_check_run_service.py (enhancement)

class CheckRunMode(str, Enum):
    """Check Run enforcement modes."""
    ADVISORY = "advisory"      # Posts Check Run but doesn't block
    BLOCKING = "blocking"      # Blocks merge if gates fail
    STRICT = "strict"          # Blocks merge + requires approval for bypass


async def create_check_run(
    self,
    project_id: UUID,
    repo_owner: str,
    repo_name: str,
    head_sha: str,
    mode: CheckRunMode = CheckRunMode.ADVISORY,
) -> dict:
    """
    Create Check Run with configurable enforcement.

    Modes:
    - ADVISORY: conclusion="neutral" always (informational)
    - BLOCKING: conclusion="failure" if gates fail (blocks merge)
    - STRICT: conclusion="action_required" if gates fail (requires review)
    """
    # ... existing logic ...

    # Determine conclusion based on mode
    if mode == CheckRunMode.ADVISORY:
        conclusion = "neutral"  # Never blocks
    elif mode == CheckRunMode.BLOCKING:
        conclusion = "success" if gate_result.passed else "failure"
    elif mode == CheckRunMode.STRICT:
        if not gate_result.passed:
            conclusion = "action_required"
        elif overlay.strict_mode:
            conclusion = "action_required"  # Requires explicit approval
        else:
            conclusion = "success"

    # Check for bypass label
    if await self._has_bypass_label(repo_owner, repo_name, pr_number):
        conclusion = "neutral"
        output.summary += "\n\n⚠️ **Bypass label applied** - Gate enforcement skipped"

    # ... complete check run ...
```

---

### Day 8: MinIO Object Lock (4 SP)

**WORM Compliance for Evidence:**

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Configure Object Lock on evidence bucket | DevOps | 2h | P0 | ⏳ |
| Update MinIOService to use retention mode | Backend | 2h | P0 | ⏳ |
| Test immutability (cannot delete) | QA | 2h | P0 | ⏳ |
| Document retention policy | PM | 1h | P0 | ⏳ |

**MinIO Object Lock Configuration:**

```yaml
# MinIO bucket configuration
Bucket: sdlc-evidence
Object Lock: ENABLED
Default Retention:
  Mode: GOVERNANCE  # Can be overridden with special permission
  Days: 2555  # ~7 years (GDPR compliance)

# Alternative: COMPLIANCE mode (cannot be overridden)
# Use for highly regulated environments
```

**Code Enhancement:**

```python
# backend/app/services/minio_service.py (enhancement)

async def upload_evidence(
    self,
    project_id: UUID,
    file_content: bytes,
    filename: str,
    metadata: dict,
) -> str:
    """
    Upload evidence with Object Lock retention.

    WORM compliance:
    - Object cannot be deleted during retention period
    - Retention set to 7 years (configurable)
    """
    object_name = f"evidence/{project_id}/{uuid4()}/{filename}"

    # Calculate retention until date
    retention_until = datetime.utcnow() + timedelta(days=settings.EVIDENCE_RETENTION_DAYS)

    # Upload with retention
    response = requests.put(
        f"{self.endpoint}/{self.bucket}/{object_name}",
        data=file_content,
        headers={
            "Content-Type": "application/octet-stream",
            "x-amz-object-lock-mode": "GOVERNANCE",
            "x-amz-object-lock-retain-until-date": retention_until.isoformat() + "Z",
            **self._auth_headers(),
        },
    )
    response.raise_for_status()

    return f"s3://{self.bucket}/{object_name}"
```

---

### Day 9: GDPR Retention Policy Documentation (2 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Write GDPR-Retention-Policy.md | Legal + PM | 3h | P1 | ⏳ |
| Review with legal counsel | PM | 2h | P1 | ⏳ |
| Update data classification docs | PM | 1h | P1 | ⏳ |

**GDPR vs Retention Resolution:**

```markdown
# GDPR-Retention-Policy.md

## Data Classification for GDPR Compliance

| Data Type | Retention | GDPR Erasure | Storage | Method |
|-----------|-----------|--------------|---------|--------|
| Evidence Artifacts | 7 years | Anonymize, don't delete | MinIO WORM | Object Lock |
| Audit Logs | 7 years | Redact PII only | Append-only table | PostgreSQL |
| User PII | Account lifetime | Full delete | Soft delete then purge | PostgreSQL |
| Code Snippets | 7 years | Already de-identified | MinIO | Object Lock |

## Anonymization Strategy

When GDPR erasure is requested:
1. Replace user_id with "REDACTED-{random}" in evidence metadata
2. Keep audit event but remove identifying info
3. Preserve evidence integrity while respecting GDPR
4. Maintain hash chain validity (hash includes anonymized data)

## Implementation

- `POST /api/v1/users/{user_id}/anonymize` - Trigger GDPR anonymization
- Affects: audit_logs, evidence metadata, comments
- Does NOT affect: evidence files (anonymized metadata only)
```

---

### Day 10: PostgreSQL RLS Foundation (4 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Design RLS policy strategy | Backend | 2h | P2 | ⏳ |
| Implement RLS for `teams` table | Backend | 2h | P2 | ⏳ |
| Test tenant isolation | QA | 2h | P2 | ⏳ |
| Document RLS approach | PM | 1h | P2 | ⏳ |

**RLS Policy Design:**

```sql
-- backend/alembic/versions/s82_002_rls_foundation.py

-- Enable RLS on teams table
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;

-- Create policy for team isolation
CREATE POLICY team_member_access ON teams
    FOR ALL
    USING (
        organization_id IN (
            SELECT organization_id
            FROM team_members
            WHERE user_id = current_setting('app.current_user_id')::uuid
        )
    );

-- Application must set user context
-- SET app.current_user_id = 'user-uuid-here';
```

---

## 🔒 Definition of Done

### Code Complete

- [ ] `EvidenceManifest` model + migration
- [ ] `EvidenceManifestService` with hash chain
- [ ] Manifest API endpoints (create, list, verify)
- [ ] Check Run blocking mode
- [ ] MinIO Object Lock configuration
- [ ] RLS policy for teams table

### Tests

- [ ] Evidence manifest unit tests (15 tests)
- [ ] Hash chain verification tests (8 tests)
- [ ] Check Run blocking mode tests (6 tests)
- [ ] MinIO Object Lock integration tests (4 tests)
- [ ] RLS policy tests (4 tests)
- [ ] Total coverage: 90%+

### Documentation

- [ ] GDPR-Retention-Policy.md
- [ ] Evidence Vault Tamper-Evident Design.md
- [ ] GitHub App Setup Guide
- [ ] API documentation updated

### Review

- [ ] CTO security review (hash chain design)
- [ ] Legal review (GDPR policy)
- [ ] Code review by Tech Lead
- [ ] PR merged to main
- [ ] Staging deployment verified

---

## 📊 Success Criteria (Go/No-Go Feb 28)

| Metric | Target | Verification |
|--------|--------|--------------|
| Hash chain valid | 100% | `GET /evidence/{id}/manifests/verify` returns valid=true |
| Cannot delete evidence | ✅ | MinIO Object Lock prevents deletion |
| Check Run blocks merge | ✅ | PR with failed gates cannot merge |
| GDPR policy documented | ✅ | Legal sign-off |
| GitHub App working | ✅ | Check Run posts on PR |

---

## 🔗 Dependencies

| Dependency | Team | Status | Blocker? |
|------------|------|--------|----------|
| Sprint 81 Complete | Backend | ✅ Complete | ❌ Resolved |
| GitHub App credentials | DevOps | ⏳ Pending | ⚠️ Yes |
| MinIO admin access | DevOps | ⏳ Pending | ⚠️ Yes |
| Legal counsel review | Legal | ⏳ Scheduled | ⚠️ For GDPR doc |

---

## ⚠️ Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Hash chain performance | Medium | Medium | Batch manifests, async creation |
| MinIO Object Lock misconfiguration | Low | High | Test in staging, document rollback |
| GDPR anonymization complexity | Medium | Medium | Clear data classification |
| RLS policy slowdown | Low | Medium | Benchmark queries, add indexes |

---

## 📅 Daily Standup Schedule

| Day | Focus | Deliverable |
|-----|-------|-------------|
| **Mar 3-4** | Evidence Manifest Model | Model + migration + basic service |
| **Mar 5-6** | Hash Chain + API | Chain verification + endpoints |
| **Mar 7** | GitHub App Setup | Production registration + Vault |
| **Mar 10** | Check Run Blocking | Enforcement mode upgrade |
| **Mar 11** | MinIO Object Lock | WORM configuration |
| **Mar 12** | GDPR Documentation | Policy document + review |
| **Mar 13** | RLS Foundation | Teams table policy |
| **Mar 14** | Testing & Verification | E2E tests, Go/No-Go prep |

---

## 🚀 Handoff to Sprint 83

### Expected Completion (Sprint 82)

- ✅ Evidence hash chain v1 (tamper-evident)
- ✅ GitHub App production ready
- ✅ Check Run blocking mode
- ✅ MinIO Object Lock enabled
- ✅ GDPR retention policy documented
- ✅ RLS foundation (teams table)

### Sprint 83 Focus (March 17-28)

- ⏳ Dynamic Context Injector (gate-triggered AGENTS.md updates)
- ⏳ Multi-repo AGENTS.md management dashboard
- ⏳ Analytics dashboard (overlay usage metrics)
- ⏳ RLS expansion (all tenant tables)

---

## 📎 References

- [CTO Pre-Launch Hardening Plan](../../09-govern/05-Knowledge-Transfer/01-Expert-Request/crispy-drifting-walrus.md)
- [Sprint 81 Complete](./SPRINT-81-AGENTS-MD-INTEGRATION.md)
- [Evidence Vault Design](../../02-design/14-Technical-Specs/Evidence-Vault-Tamper-Evident-Design.md)
- [MinIO Object Lock Docs](https://min.io/docs/minio/linux/administration/object-management/object-retention.html)

---

**Sprint 82 Plan Version:** 1.0.0
**Created:** January 19, 2026
**Author:** Backend Lead
**Status:** DRAFT - Pending Sprint 81 Close
**Go/No-Go Review:** February 28, 2026

---

**SDLC 6.1.0 | Sprint 82 | Stage 04 (BUILD)**

*Pre-Launch Hardening - "Credibility is our most valuable asset. We cannot afford to lose it on day one." - CTO*
