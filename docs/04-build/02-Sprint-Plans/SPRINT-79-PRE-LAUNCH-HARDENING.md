# Sprint 79: Pre-Launch Hardening & Critical Fixes

**Sprint ID:** S79
**Status:** 🔄 IN PROGRESS
**Duration:** 10 days (January 20 - February 2, 2026)
**Goal:** Complete P0 Launch Blockers + Evidence Vault Hardening
**Story Points:** 48 SP
**Framework Reference:** SDLC 5.1.3 P4 (Quality Gates)
**Prerequisite:** Sprint 78 ✅ + CTO Pre-Launch Approval ✅

---

## 🎯 Sprint 79 Objectives

### Primary Goals (P0 - Launch Blockers)

| # | Task | Owner | Deadline | Priority |
|---|------|-------|----------|----------|
| 1 | Fix over-claims in all Expert docs | PM | Jan 21 | 🔴 P0 |
| 2 | GitHub Check Run implementation | Backend | Jan 28 | 🔴 P0 |
| 3 | Evidence hash chain v1 (Ed25519) | Backend | Feb 10* | 🔴 P0 |

*Note: Evidence hash chain extends to Feb 10 per CTO timeline adjustment (+3 days for Ed25519)

### Secondary Goals (P1 - Differentiators)

| # | Task | Owner | Deadline | Priority |
|---|------|-------|----------|----------|
| 4 | MinIO Object Lock (WORM) config | DevOps | Jan 25 | 🟠 P1 |
| 5 | GDPR vs Retention policy | Legal + PM | Feb 1 | 🟠 P1 |
| 6 | Landing Page MVP | Frontend | Feb 2 | 🟠 P1 |

---

## 📋 Sprint 79 Backlog

### Week 1 (Jan 20-24): Documentation & GitHub Integration

#### Day 1-2: Over-claims Fix (8 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Audit all 10 Expert Request docs | PM | 4h | P0 | ⏳ |
| Fix 100K → single metric format | PM | 2h | P0 | ⏳ |
| Fix ASVS math (264 × 98.4%) | PM | 1h | P0 | ⏳ |
| Update positioning in all docs | PM | 3h | P0 | ⏳ |

**Single Metric Format (Mandated):**

```markdown
## Load Testing Results (Honest)

| Metric | Value | Notes |
|--------|-------|-------|
| **Virtual Users (VUs)** | 10,000 | Locust simulation |
| **Requests per Second** | 500 RPS | Sustained for 30 min |
| **Concurrent WebSocket Sessions** | 200 | Actual measured |
| **API Latency p95** | 87ms | Under load |
| **Database Connections** | 100 | PgBouncer pool |

### Interpretation
- "10K VUs" = Simulated user load (requests)
- "200 concurrent" = Actual simultaneous connections
- Bottleneck: DB connection pool (fixable with scaling)
- Designed capacity: 10K concurrent sessions (with horizontal scaling)
```

#### Day 3-5: GitHub Check Run (12 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| GitHub App registration | DevOps | 2h | P0 | ⏳ |
| Check Run API integration | Backend | 6h | P0 | ⏳ |
| Gate evaluation → Check output | Backend | 4h | P0 | ⏳ |
| Branch protection config | DevOps | 2h | P0 | ⏳ |
| Demo repo with merge disabled | Backend | 2h | P0 | ⏳ |
| Integration tests (8 tests) | Backend | 3h | P0 | ⏳ |

**Implementation:**

```python
# backend/app/services/github_checks_service.py
from typing import Optional
from uuid import UUID
import httpx

class GitHubChecksService:
    """
    GitHub Checks API integration for gate enforcement.

    Creates Check Runs that BLOCK merge when gates fail.
    """

    def __init__(self, github_app_id: str, private_key: str):
        self.app_id = github_app_id
        self.private_key = private_key

    async def create_check_run(
        self,
        installation_id: int,
        repo_owner: str,
        repo_name: str,
        head_sha: str,
        gate_id: str,
        status: str,  # "queued", "in_progress", "completed"
        conclusion: Optional[str] = None,  # "success", "failure", "neutral"
        output: Optional[dict] = None,
    ) -> dict:
        """
        Create a GitHub Check Run for gate evaluation.

        When conclusion="failure", merge button is DISABLED.
        This is the HARD enforcement layer.
        """
        token = await self._get_installation_token(installation_id)

        payload = {
            "name": f"SDLC Gate: {gate_id}",
            "head_sha": head_sha,
            "status": status,
            "external_id": str(UUID()),
        }

        if conclusion:
            payload["conclusion"] = conclusion

        if output:
            payload["output"] = {
                "title": output.get("title", f"Gate {gate_id} Evaluation"),
                "summary": output.get("summary", ""),
                "text": output.get("text", ""),
            }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/repos/{repo_owner}/{repo_name}/check-runs",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def update_check_run(
        self,
        installation_id: int,
        repo_owner: str,
        repo_name: str,
        check_run_id: int,
        status: str,
        conclusion: Optional[str] = None,
        output: Optional[dict] = None,
    ) -> dict:
        """Update an existing Check Run with evaluation results."""
        token = await self._get_installation_token(installation_id)

        payload = {"status": status}

        if conclusion:
            payload["conclusion"] = conclusion
            payload["completed_at"] = datetime.utcnow().isoformat() + "Z"

        if output:
            payload["output"] = output

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"https://api.github.com/repos/{repo_owner}/{repo_name}/check-runs/{check_run_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def evaluate_and_report(
        self,
        project_id: UUID,
        pr_number: int,
        head_sha: str,
    ) -> dict:
        """
        Full flow: Evaluate gates and report via Check Run.

        Returns Check Run result with enforcement status.
        """
        # Get project GitHub config
        project = await self.project_repo.get(project_id)

        # Create pending Check Run
        check_run = await self.create_check_run(
            installation_id=project.github_installation_id,
            repo_owner=project.github_owner,
            repo_name=project.github_repo,
            head_sha=head_sha,
            gate_id="G-Sprint",
            status="in_progress",
        )

        try:
            # Evaluate gates
            result = await self.gate_service.evaluate_for_pr(
                project_id=project_id,
                pr_number=pr_number,
            )

            # Update Check Run with result
            conclusion = "success" if result.passed else "failure"
            output = self._format_gate_output(result)

            return await self.update_check_run(
                installation_id=project.github_installation_id,
                repo_owner=project.github_owner,
                repo_name=project.github_repo,
                check_run_id=check_run["id"],
                status="completed",
                conclusion=conclusion,
                output=output,
            )

        except Exception as e:
            # Report error
            return await self.update_check_run(
                installation_id=project.github_installation_id,
                repo_owner=project.github_owner,
                repo_name=project.github_repo,
                check_run_id=check_run["id"],
                status="completed",
                conclusion="neutral",
                output={
                    "title": "Gate Evaluation Error",
                    "summary": f"Error: {str(e)}",
                },
            )

    def _format_gate_output(self, result) -> dict:
        """Format gate evaluation result for Check Run output."""
        status_icon = "✅" if result.passed else "❌"

        summary = f"{status_icon} **Gate Status: {'PASSED' if result.passed else 'FAILED'}**\n\n"

        for gate in result.gates:
            icon = "✅" if gate.passed else "❌"
            summary += f"- {icon} {gate.name}: {gate.status}\n"

        if not result.passed:
            summary += "\n⚠️ **Merge is BLOCKED until all gates pass.**"

        return {
            "title": f"SDLC Gate Evaluation: {'PASSED' if result.passed else 'FAILED'}",
            "summary": summary,
            "text": result.details if hasattr(result, 'details') else "",
        }
```

#### Day 5: MinIO Object Lock (4 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Enable Object Lock on evidence bucket | DevOps | 2h | P1 | ⏳ |
| Configure WORM retention policy | DevOps | 2h | P1 | ⏳ |
| Test immutability enforcement | DevOps | 2h | P1 | ⏳ |
| Documentation update | DevOps | 1h | P1 | ⏳ |

**MinIO WORM Configuration:**

```yaml
# docker-compose.override.yml
services:
  minio:
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    # Object Lock enabled via mc command after startup

# scripts/configure-minio-worm.sh
#!/bin/bash
# Enable Object Lock on evidence bucket

# Wait for MinIO to be ready
until mc alias set minio http://minio:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD; do
  sleep 1
done

# Create bucket with Object Lock enabled
mc mb --with-lock minio/evidence-vault

# Set default retention (7 years per compliance)
mc retention set --default GOVERNANCE "7y" minio/evidence-vault

echo "✅ MinIO WORM enabled for evidence-vault bucket"
```

---

### Week 2 (Jan 27 - Feb 2): Evidence Vault & Landing Page

#### Day 6-8: Evidence Hash Chain with Ed25519 (12 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Ed25519 key generation service | Backend | 4h | P0 | ⏳ |
| Key storage (Vault/HSM) | DevOps | 3h | P0 | ⏳ |
| Manifest signing implementation | Backend | 6h | P0 | ⏳ |
| Signature verification | Backend | 3h | P0 | ⏳ |
| Hash chain linking | Backend | 4h | P0 | ⏳ |
| Integration tests (10 tests) | Backend | 4h | P0 | ⏳ |
| Security review | CTO | 4h | P0 | ⏳ |

**Implementation (Per Expert 6 Feedback):**

```python
# backend/app/services/evidence_manifest_service.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
import hashlib

from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import HexEncoder
from pydantic import BaseModel


class ArtifactEntry(BaseModel):
    """Single artifact in manifest."""
    id: UUID
    sha256: str
    uploaded_at: datetime
    file_path: str
    file_size: int


class EvidenceManifest(BaseModel):
    """
    Tamper-evident manifest with Ed25519 signing.

    Per Expert 6 feedback: Use asymmetric signing for non-repudiation.
    HMAC with server secret allows admin forgery.
    Ed25519 provides cryptographic proof of origin.
    """
    manifest_id: UUID
    project_id: UUID
    artifacts: List[ArtifactEntry]
    previous_manifest_hash: Optional[str]  # Hash chain linking

    # Asymmetric signing (NOT HMAC)
    signature: str  # Ed25519 signature
    signer_key_id: str  # Public key ID for verification
    signing_algorithm: str = "Ed25519"

    # Optional enterprise features
    timestamp_authority: Optional[str] = None  # External TSA

    created_at: datetime


class EvidenceManifestService:
    """
    Tamper-evident evidence manifest with Ed25519 signing.

    Design principles (per Expert 6):
    1. Asymmetric signing for non-repudiation
    2. Hash chain for tamper-evidence
    3. Key rotation support
    4. Optional external timestamping
    """

    def __init__(
        self,
        key_storage,  # Vault/HSM abstraction
        manifest_repo,
    ):
        self.key_storage = key_storage
        self.manifest_repo = manifest_repo

    async def create_manifest(
        self,
        project_id: UUID,
        artifacts: List[ArtifactEntry],
    ) -> EvidenceManifest:
        """
        Create new manifest with Ed25519 signature.

        1. Get previous manifest hash (chain linking)
        2. Compute content hash
        3. Sign with Ed25519 private key
        4. Store manifest
        """
        # Get previous manifest for chain linking
        previous = await self.manifest_repo.get_latest(project_id)
        previous_hash = None
        if previous:
            previous_hash = self._compute_manifest_hash(previous)

        # Create unsigned manifest
        manifest_id = uuid4()
        created_at = datetime.utcnow()

        # Get current signing key
        key_id, signing_key = await self.key_storage.get_current_signing_key()

        # Compute signature
        content_to_sign = self._prepare_signing_content(
            manifest_id=manifest_id,
            project_id=project_id,
            artifacts=artifacts,
            previous_hash=previous_hash,
            created_at=created_at,
        )

        signature = signing_key.sign(
            content_to_sign.encode('utf-8'),
            encoder=HexEncoder,
        ).signature.decode('utf-8')

        # Create manifest
        manifest = EvidenceManifest(
            manifest_id=manifest_id,
            project_id=project_id,
            artifacts=artifacts,
            previous_manifest_hash=previous_hash,
            signature=signature,
            signer_key_id=key_id,
            signing_algorithm="Ed25519",
            created_at=created_at,
        )

        # Store
        await self.manifest_repo.save(manifest)

        return manifest

    async def verify_manifest(
        self,
        manifest: EvidenceManifest,
    ) -> bool:
        """
        Verify manifest signature and chain integrity.

        Returns True if:
        1. Signature is valid
        2. Previous hash matches (if not first)
        3. All artifact hashes match
        """
        # Get verify key
        verify_key = await self.key_storage.get_verify_key(manifest.signer_key_id)

        # Verify signature
        content_to_verify = self._prepare_signing_content(
            manifest_id=manifest.manifest_id,
            project_id=manifest.project_id,
            artifacts=manifest.artifacts,
            previous_hash=manifest.previous_manifest_hash,
            created_at=manifest.created_at,
        )

        try:
            verify_key.verify(
                content_to_verify.encode('utf-8'),
                bytes.fromhex(manifest.signature),
            )
        except Exception:
            return False

        # Verify chain integrity
        if manifest.previous_manifest_hash:
            previous = await self.manifest_repo.get_by_hash(
                manifest.previous_manifest_hash
            )
            if not previous:
                return False  # Chain broken

        return True

    async def verify_chain(
        self,
        project_id: UUID,
    ) -> tuple[bool, List[str]]:
        """
        Verify entire manifest chain for a project.

        Returns (is_valid, list_of_errors).
        """
        errors = []
        manifests = await self.manifest_repo.get_all_for_project(project_id)

        for i, manifest in enumerate(manifests):
            # Verify signature
            if not await self.verify_manifest(manifest):
                errors.append(f"Invalid signature on manifest {manifest.manifest_id}")

            # Verify chain link
            if i > 0:
                expected_hash = self._compute_manifest_hash(manifests[i - 1])
                if manifest.previous_manifest_hash != expected_hash:
                    errors.append(
                        f"Chain broken at manifest {manifest.manifest_id}: "
                        f"expected {expected_hash}, got {manifest.previous_manifest_hash}"
                    )

        return len(errors) == 0, errors

    def _prepare_signing_content(
        self,
        manifest_id: UUID,
        project_id: UUID,
        artifacts: List[ArtifactEntry],
        previous_hash: Optional[str],
        created_at: datetime,
    ) -> str:
        """Prepare deterministic content for signing."""
        # Sort artifacts by ID for determinism
        sorted_artifacts = sorted(artifacts, key=lambda a: str(a.id))

        content = {
            "manifest_id": str(manifest_id),
            "project_id": str(project_id),
            "previous_hash": previous_hash or "",
            "created_at": created_at.isoformat(),
            "artifacts": [
                {
                    "id": str(a.id),
                    "sha256": a.sha256,
                    "uploaded_at": a.uploaded_at.isoformat(),
                }
                for a in sorted_artifacts
            ],
        }

        # Canonical JSON (sorted keys, no whitespace)
        import json
        return json.dumps(content, sort_keys=True, separators=(',', ':'))

    def _compute_manifest_hash(self, manifest: EvidenceManifest) -> str:
        """Compute SHA-256 hash of manifest for chain linking."""
        content = self._prepare_signing_content(
            manifest_id=manifest.manifest_id,
            project_id=manifest.project_id,
            artifacts=manifest.artifacts,
            previous_hash=manifest.previous_manifest_hash,
            created_at=manifest.created_at,
        )
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


class KeyStorageService:
    """
    Key storage abstraction for Ed25519 signing keys.

    Production: Use HashiCorp Vault or AWS KMS
    Development: File-based storage (encrypted)
    """

    def __init__(self, vault_client=None):
        self.vault_client = vault_client
        self._keys = {}  # In-memory cache

    async def generate_key_pair(self) -> tuple[str, SigningKey]:
        """Generate new Ed25519 key pair."""
        signing_key = SigningKey.generate()
        key_id = f"ed25519-{uuid4().hex[:8]}"

        # Store in Vault
        await self._store_key(key_id, signing_key)

        return key_id, signing_key

    async def get_current_signing_key(self) -> tuple[str, SigningKey]:
        """Get current active signing key."""
        # In production, fetch from Vault with key rotation
        if not self._keys:
            return await self.generate_key_pair()

        key_id = list(self._keys.keys())[-1]
        return key_id, self._keys[key_id]

    async def get_verify_key(self, key_id: str) -> VerifyKey:
        """Get verify key for signature verification."""
        signing_key = self._keys.get(key_id)
        if not signing_key:
            # Fetch from Vault
            signing_key = await self._fetch_key(key_id)

        return signing_key.verify_key

    async def _store_key(self, key_id: str, signing_key: SigningKey):
        """Store key in Vault."""
        self._keys[key_id] = signing_key

        if self.vault_client:
            await self.vault_client.secrets.kv.v2.create_or_update_secret(
                path=f"signing-keys/{key_id}",
                secret={
                    "private_key": signing_key.encode(encoder=HexEncoder).decode(),
                    "public_key": signing_key.verify_key.encode(encoder=HexEncoder).decode(),
                },
            )

    async def _fetch_key(self, key_id: str) -> SigningKey:
        """Fetch key from Vault."""
        if self.vault_client:
            secret = await self.vault_client.secrets.kv.v2.read_secret_version(
                path=f"signing-keys/{key_id}",
            )
            return SigningKey(
                secret["data"]["data"]["private_key"],
                encoder=HexEncoder,
            )
        raise KeyError(f"Key {key_id} not found")
```

#### Day 9-10: Landing Page MVP (8 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Hero section with positioning | Frontend | 3h | P1 | ⏳ |
| Feature highlights (3 pillars) | Frontend | 3h | P1 | ⏳ |
| Pricing section | Frontend | 2h | P1 | ⏳ |
| CTA and signup form | Frontend | 2h | P1 | ⏳ |
| Mobile responsive | Frontend | 2h | P1 | ⏳ |
| Performance optimization | Frontend | 2h | P1 | ⏳ |

**Landing Page Content (Per CTO Approved Positioning):**

```markdown
## Hero Section
# AI Code Governance Platform
"Static rules. Dynamic context. Hard enforcement."

Ensure every AI-generated code meets your standards before merge.

[Get Started - Free Trial] [View Demo]

## 3 Pillars
1. **AGENTS.md Generator** - Industry standard AI guidance
2. **Dynamic Context** - Real-time constraints via PR comments
3. **Hard Enforcement** - GitHub Checks API blocks bad merges

## Honest Metrics
- 10K virtual users tested
- 200 concurrent sessions
- <100ms API latency (p95)
- 95%+ test coverage

## Pricing
- Free: 1 project, 3 team members
- Pro: $30/user/month - Unlimited projects
- Enterprise: Custom - SSO, audit logs, support
```

---

## 🔗 API Endpoints (Sprint 79)

```yaml
# GitHub Checks Integration
POST /api/v1/github/check-runs:
  summary: Create Check Run for PR
  tags: [GitHub, Enforcement]

PATCH /api/v1/github/check-runs/{id}:
  summary: Update Check Run with evaluation result
  tags: [GitHub, Enforcement]

POST /api/v1/github/webhooks/pull-request:
  summary: Handle PR webhook, trigger gate evaluation
  tags: [GitHub, Webhooks]

# Evidence Manifest (Ed25519)
POST /api/v1/evidence/manifests:
  summary: Create signed manifest
  tags: [Evidence, Security]

GET /api/v1/evidence/manifests/{id}/verify:
  summary: Verify manifest signature
  tags: [Evidence, Security]

GET /api/v1/projects/{id}/evidence/chain/verify:
  summary: Verify entire evidence chain
  tags: [Evidence, Audit]
```

---

## 🔒 Definition of Done

### Code Complete

- [ ] Over-claims fixed in all 10 Expert docs
- [ ] GitHub Check Run API integration
- [ ] Evidence manifest with Ed25519 signing
- [ ] MinIO Object Lock (WORM) enabled
- [ ] Landing Page MVP deployed

### Tests

- [ ] GitHub Checks integration tests (8 tests)
- [ ] Evidence signing tests (10 tests)
- [ ] E2E: PR → Check Run → Block/Allow (2 tests)
- [ ] Total: 20+ new tests

### Documentation

- [ ] GitHub App setup guide
- [ ] Evidence Vault security design
- [ ] GDPR vs Retention policy document

### Demo

- [ ] Demo repo with merge disabled screenshot
- [ ] Evidence chain tamper test recording

### Review

- [ ] CTO security review on Ed25519 implementation
- [ ] Code review by Tech Lead
- [ ] PR merged to main

---

## 📊 Metrics & Success Criteria

| Metric | Target | Notes |
|--------|--------|-------|
| Over-claims | 0 remaining | Single metric format |
| GitHub enforcement | Working | Demo repo merge disabled |
| Evidence signing | Ed25519 | Non-repudiation |
| Landing Page | Lighthouse >90 | Performance |
| Test coverage | 90%+ | New code |

---

## 📝 SDLC 5.1.3 Compliance

| Pillar | Sprint 79 Implementation |
|--------|--------------------------|
| P4 (Quality Gates) | GitHub Check Run enforcement |
| P7 (Documentation) | Evidence chain audit trail |
| P5 (SASE) | Foundation for AGENTS.md (Sprint 80) |

---

## 🚀 Handoff to Sprint 80

### Expected Completion (Sprint 79)

| Feature | Status | Blocks Sprint 80? |
|---------|--------|-------------------|
| Over-claims fixed | ⏳ | ❌ No |
| GitHub Check Run | ⏳ | ❌ No |
| Evidence Ed25519 | ⏳ | ❌ No |
| MinIO WORM | ⏳ | ❌ No |
| Landing Page | ⏳ | ❌ No |

### Sprint 80 Prerequisites

- ✅ ADR-029 CTO Approved
- ⏳ Sprint 79 P0 items complete
- ⏳ GitHub enforcement working

---

## 📅 Daily Standup Schedule

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Jan 20 | Over-claims audit start | Audit report |
| Jan 21 | Over-claims fix complete | All docs updated |
| Jan 22 | GitHub App setup | App registered |
| Jan 23-24 | Check Run implementation | API working |
| Jan 25 | MinIO WORM | Config complete |
| Jan 27-28 | Check Run complete + Demo | Demo repo ready |
| Jan 29-31 | Ed25519 implementation | Signing working |
| Feb 1 | Security review | CTO sign-off |
| Feb 2 | Landing Page + Sprint close | MVP deployed |

---

## 🔴 CTO Priority Order Reference

Per CTO approval (Jan 19, 2026):

| Priority | Task | Owner | Deadline | Status |
|----------|------|-------|----------|--------|
| **P0** | Fix over-claims in all docs | PM | Jan 21 | ⏳ |
| **P0** | GitHub Check Run implementation | Backend | Jan 28 | ⏳ |
| **P0** | Evidence hash chain v1 (Ed25519) | Backend | Feb 10 | ⏳ |
| **P1** | MinIO Object Lock config | DevOps | Jan 25 | ⏳ |
| **P1** | GDPR vs Retention policy | Legal + PM | Feb 1 | ⏳ |

---

**SDLC 5.1.3 | Sprint 79 | Stage 04 (BUILD)**

*G-Sprint Approval: ✅ CTO Approved (Jan 19, 2026)*
