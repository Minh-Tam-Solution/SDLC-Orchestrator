# Fernet Key Rotation Runbook

**Version**: 1.0.0
**Status**: ACTIVE
**Date**: February 20, 2026
**Authority**: CTO Approved (Sprint 185 CTO Condition #4)
**Classification**: CONFIDENTIAL — Operations Only
**Audience**: Backend Lead, DevOps Lead, Security Lead

---

## Overview

SDLC Orchestrator encrypts Jira API tokens at-rest using [Fernet](https://cryptography.io/en/latest/fernet/) symmetric encryption (AES-128-CBC + HMAC-SHA256). The key is resolved from:

1. `FERNET_KEY` environment variable (explicit Fernet key, preferred)
2. Fallback: `hashlib.sha256(SECRET_KEY).digest()` → base64-urlsafe-encode (Sprint 185 F-03 fix)

**Source**: [`backend/app/models/jira_connection.py:58–72`](../../../backend/app/models/jira_connection.py)

Affected table: `jira_connections.api_token_enc`

---

## When to Rotate

Rotate the Fernet key when any of the following occur:

| Trigger | Priority | SLA |
|---------|----------|-----|
| Security incident (key suspected compromised) | P0 | ≤ 4 hours |
| Engineer with key access leaves the company | P1 | ≤ 24 hours |
| Quarterly scheduled rotation (SOC2 CC6.7) | P2 | Within sprint |
| `SECRET_KEY` rotation (affects fallback derivation) | P1 | ≤ 4 hours post `SECRET_KEY` rotation |
| First ENTERPRISE customer onboarding | P1 | Before onboarding call |

---

## Pre-Rotation Checklist

- [ ] Maintenance window scheduled (off-peak hours: 02:00–04:00 ICT)
- [ ] Database backup taken and verified (`pg_dump sdlc_orchestrator`)
- [ ] Number of affected rows confirmed: `SELECT COUNT(*) FROM jira_connections;`
- [ ] Rollback tested in staging environment
- [ ] All team members with production access notified (Slack #ops-alerts)
- [ ] HashiCorp Vault access confirmed for the rotating engineer

---

## Step 1 — Generate New Fernet Key

```bash
# In a secure, ephemeral shell (never log to CI/CD)
python3 -c "
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print('NEW_FERNET_KEY:', key.decode())
"
```

> **CRITICAL**: Record the output securely in 1Password / HashiCorp Vault. Do NOT paste into Slack, email, or commit to git.

---

## Step 2 — Store Old Key as Fallback

Before overwriting the Vault secret, record the current key value for the re-encryption script:

```bash
# Retrieve current key from Vault
OLD_KEY=$(vault kv get -field=FERNET_KEY secret/sdlc-orchestrator/production)
echo "Old key length: ${#OLD_KEY} chars (should be 44)"
```

---

## Step 3 — Re-encrypt All `api_token_enc` Rows

Run the following script **in production** (or a direct DB connection with the same environment):

```python
#!/usr/bin/env python3
"""
fernet_reencrypt.py — Re-encrypt jira_connections.api_token_enc
Sprint 186 / SOC2 CC6.7 key rotation support.

USAGE:
  OLD_FERNET_KEY=<old_base64_key> NEW_FERNET_KEY=<new_base64_key> \
    python3 fernet_reencrypt.py --dry-run        # preview, no DB writes
  OLD_FERNET_KEY=<old_base64_key> NEW_FERNET_KEY=<new_base64_key> \
    python3 fernet_reencrypt.py --apply          # commit changes

SAFETY:
  - Wraps all writes in a single transaction; any failure rolls back.
  - Verifies decrypt(new_encrypt(decrypt(old_ciphertext))) == plaintext
    before committing (round-trip check).
  - Logs row count and any per-row failures (plaintext never logged).
"""

import os
import sys
import argparse
import logging
from cryptography.fernet import Fernet, InvalidToken

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("fernet_reencrypt")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    old_key = os.environ.get("OLD_FERNET_KEY")
    new_key = os.environ.get("NEW_FERNET_KEY")
    db_url = os.environ.get("DATABASE_URL")

    if not old_key or not new_key:
        log.error("OLD_FERNET_KEY and NEW_FERNET_KEY must be set")
        sys.exit(1)
    if not db_url:
        log.error("DATABASE_URL must be set")
        sys.exit(1)

    old_fernet = Fernet(old_key.encode())
    new_fernet = Fernet(new_key.encode())

    import psycopg2
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    cur.execute("SELECT id, api_token_enc FROM jira_connections ORDER BY id")
    rows = cur.fetchall()
    log.info("Found %d row(s) in jira_connections", len(rows))

    updates: list[tuple[str, str]] = []
    errors = 0

    for row_id, old_ciphertext in rows:
        try:
            plaintext = old_fernet.decrypt(old_ciphertext.encode())
        except InvalidToken:
            log.error("Row %s: decrypt failed with OLD_FERNET_KEY (skip)", row_id)
            errors += 1
            continue

        new_ciphertext = new_fernet.encrypt(plaintext).decode()

        # Round-trip verification
        try:
            verified = new_fernet.decrypt(new_ciphertext.encode())
            assert verified == plaintext, "Round-trip mismatch"
        except Exception as exc:
            log.error("Row %s: round-trip check failed: %s", row_id, exc)
            errors += 1
            continue

        updates.append((new_ciphertext, str(row_id)))
        log.info("Row %s: re-encrypted OK", row_id)

    if errors:
        log.error("%d row(s) had errors — aborting", errors)
        conn.rollback()
        conn.close()
        sys.exit(1)

    if args.dry_run:
        log.info("DRY RUN: %d row(s) would be updated. No changes written.", len(updates))
        conn.close()
        return

    # Apply updates in a single transaction
    for new_ciphertext, row_id in updates:
        cur.execute(
            "UPDATE jira_connections SET api_token_enc = %s, updated_at = NOW() WHERE id = %s",
            (new_ciphertext, row_id),
        )

    conn.commit()
    log.info("COMMITTED: %d row(s) re-encrypted successfully.", len(updates))
    conn.close()


if __name__ == "__main__":
    main()
```

**Dry-run first (mandatory)**:
```bash
OLD_FERNET_KEY="<old_key>" \
NEW_FERNET_KEY="<new_key>" \
DATABASE_URL="postgresql://..." \
  python3 fernet_reencrypt.py --dry-run
```

Expected output: `INFO DRY RUN: N row(s) would be updated. No changes written.`

**Apply (only after dry-run succeeds)**:
```bash
OLD_FERNET_KEY="<old_key>" \
NEW_FERNET_KEY="<new_key>" \
DATABASE_URL="postgresql://..." \
  python3 fernet_reencrypt.py --apply
```

---

## Step 4 — Verify Re-encryption

```sql
-- Spot-check: confirm updated_at was bumped for all rows
SELECT id, updated_at
FROM jira_connections
ORDER BY updated_at DESC
LIMIT 5;
```

Then verify at application level:
```bash
# In the running container with the NEW key already active
curl -X POST https://api.sdlcorchestrator.com/api/v1/integrations/jira/test \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"organization_id": "<first_org_id>"}'
# Expected: {"connected": true}
```

---

## Step 5 — Rotate the Secret in HashiCorp Vault

```bash
vault kv put secret/sdlc-orchestrator/production \
  FERNET_KEY="<new_key>"

# Confirm
vault kv get secret/sdlc-orchestrator/production
```

---

## Step 6 — Deploy / Restart Application

The new `FERNET_KEY` must be injected into the running process. Kubernetes:

```bash
kubectl rollout restart deployment/sdlc-orchestrator-backend -n production
kubectl rollout status deployment/sdlc-orchestrator-backend -n production
```

Docker Compose (staging):
```bash
docker compose down backend && docker compose up -d backend
```

---

## Step 7 — Post-Rotation Validation

```bash
# Health check
curl https://api.sdlcorchestrator.com/api/v1/health
# Expected: {"status": "healthy"}

# Evidence of rotation for SOC2 audit trail
# Columns corrected per AuditLog model (Sprint 186 F-07):
#   event_type  — NOT NULL (required)
#   action      — human-readable verb
#   resource_type / resource_id — what was affected
#   actor_id    — UUID of the operator (NOT 'created_by')
#   detail      — JSONB column (NOT 'details')
psql "$DATABASE_URL" -c "
INSERT INTO audit_logs (event_type, action, resource_type, resource_id, actor_id, detail)
VALUES (
  'KEY_ROTATION',
  'fernet_key_rotated',
  'system',
  'fernet_encryption_key',
  '00000000-0000-0000-0000-000000000000',
  '{\"rotation_date\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"rows_reencrypted\": 0}'::jsonb
);
"
```

---

## Rollback Procedure

If the application fails to decrypt after the new key is deployed:

1. **Restore old key in Vault**:
   ```bash
   vault kv put secret/sdlc-orchestrator/production FERNET_KEY="<old_key>"
   ```

2. **Restart application** (Step 6 above with old key)

3. **Verify** (Step 7 above)

4. The `api_token_enc` column still contains the old ciphertext if the `--apply` step had not yet committed. If it committed but the application is broken, re-run `fernet_reencrypt.py --apply` with `OLD_FERNET_KEY=<new_key>` and `NEW_FERNET_KEY=<old_key>` to reverse.

> **Note**: The `fernet_reencrypt.py --apply` commit and the Vault secret rotation are independent steps. Always re-encrypt the DB rows **before** pushing the new key to Vault + restarting.

---

## Fallback Key Derivation (Legacy Path)

If `FERNET_KEY` is **not** set, the key is derived as:

```python
import base64, hashlib
raw = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
key = base64.urlsafe_b64encode(raw)
```

**Warning**: Sprint 185 F-03 changed this derivation (was zero-padding, now SHA-256). Any rows encrypted under the old zero-padding derivation (before Sprint 185 deploy) must be re-encrypted. Run `fernet_reencrypt.py` with `OLD_FERNET_KEY` set to the zero-padded derived key:

```python
# Compute old (zero-padding) derived key for rows encrypted before Sprint 185
import base64
old_key = base64.urlsafe_b64encode(
    settings.SECRET_KEY.encode().ljust(32, b"\x00")[:32]
)
print(old_key.decode())
```

Use this as `OLD_FERNET_KEY` when migrating pre-Sprint-185 tokens.

---

## Audit Trail

Log each rotation in the Security Register (`docs/09-govern/11-Decisions/`):

| Date | Trigger | Rows Rotated | Engineer | Approved By |
|------|---------|--------------|----------|-------------|
| 2026-02-20 | Sprint 186 P1 mandate + ENTERPRISE onboarding prep | 0 (no connections yet) | TBD | CTO |

---

## Related Documents

- [ADR-056 — Multi-Agent Team Engine](../../02-design/ADR-056-Multi-Agent-Team-Engine.md) (Jira integration tier: PROFESSIONAL+)
- [Sprint 185 Close](../../04-build/02-Sprint-Plans/SPRINT-185-CLOSE.md) — F-03 key derivation fix context
- [Sprint 186 Plan](../../04-build/02-Sprint-Plans/SPRINT-186-MULTI-REGION-DATA-RESIDENCY.md) — CTO P1 carry-forward

---

*Runbook Status: APPROVED — Sprint 186 P1 Mandate*
*Next Review: Q2 2026 (quarterly SOC2 audit) or on any Fernet-related incident*
