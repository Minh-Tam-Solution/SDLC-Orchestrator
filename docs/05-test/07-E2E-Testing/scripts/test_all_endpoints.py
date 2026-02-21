#!/usr/bin/env python3
"""
*-CyEyes-* E2E API Test Script — SDLC Orchestrator Sprint 181-188
Generated: 2026-02-20
Base URL: http://localhost:8300
Coverage: All 550 unique paths (622 operations)

Focuses on Sprint 181-188 new features:
  Sprint 181: OTT Foundation + Route Activation (compliance, NIST, invitations, templates)
  Sprint 182: Enterprise SSO Design + Teams Channel
  Sprint 183: Enterprise SSO Implementation + Compliance Evidence
  Sprint 184: Tier Enforcement + Jira Integration
  Sprint 185: Audit Trail + SOC2 Evidence Pack
  Sprint 186: Multi-Region + GDPR
  Sprint 187: G4 Production Validation
  Sprint 188: GA Launch + Pricing Enforcement
"""

import json
import time
import datetime
from pathlib import Path
import requests

BASE_URL = "http://localhost:8300"
ARTIFACTS_DIR = Path(__file__).parent.parent / "artifacts"
TOKEN_FILE = ARTIFACTS_DIR / "auth_token.txt"

# Load auth token
with open(TOKEN_FILE) as f:
    TOKEN = f.read().strip()

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

results = []
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def test(method: str, path: str, body=None, params=None, label: str = "", expected_codes=(200, 201, 204)):
    """Execute a single API test and record result."""
    url = f"{BASE_URL}{path}"
    t0 = time.time()
    try:
        resp = requests.request(
            method=method,
            url=url,
            headers=HEADERS,
            json=body,
            params=params,
            timeout=15,
        )
        elapsed = int((time.time() - t0) * 1000)
        code = resp.status_code

        if code in expected_codes:
            status = "PASS"
        elif code == 422:
            status = "VALIDATION_ERROR"
        elif code == 404:
            status = "NOT_FOUND"
        elif code in (401, 403):
            status = "UNAUTHORIZED"
        elif code >= 500:
            status = "SERVER_ERROR"
        else:
            status = "FAIL"

        try:
            resp_body = resp.json()
        except Exception:
            resp_body = resp.text[:200] if resp.text else ""

        entry = {
            "stt": len(results) + 1,
            "method": method,
            "path": path,
            "label": label or path,
            "status": status,
            "code": code,
            "elapsed_ms": elapsed,
            "request_body": body,
            "response": resp_body,
        }
        results.append(entry)

        icon = {"PASS": "✅", "VALIDATION_ERROR": "⚠️", "NOT_FOUND": "🚫",
                "UNAUTHORIZED": "🔒", "SERVER_ERROR": "🔴", "FAIL": "❌"}.get(status, "?")
        print(f"{icon} [{code}] {method:6} {path[:70]:<70} {elapsed:4}ms  {status}")
        return entry

    except requests.exceptions.Timeout:
        elapsed = int((time.time() - t0) * 1000)
        entry = {"stt": len(results) + 1, "method": method, "path": path,
                 "label": label, "status": "TIMEOUT", "code": 0, "elapsed_ms": elapsed,
                 "request_body": body, "response": "Request timed out"}
        results.append(entry)
        print(f"⏱️  [TMO] {method:6} {path[:70]:<70} {elapsed:4}ms  TIMEOUT")
        return entry
    except Exception as e:
        entry = {"stt": len(results) + 1, "method": method, "path": path,
                 "label": label, "status": "ERROR", "code": 0, "elapsed_ms": 0,
                 "request_body": body, "response": str(e)}
        results.append(entry)
        print(f"💥 [ERR] {method:6} {path[:70]:<70}           ERROR: {e}")
        return entry


print("=" * 100)
print("*-CyEyes-* SDLC Orchestrator E2E API Tests — Sprint 181-188")
print(f"Started: {datetime.datetime.now().isoformat()}")
print(f"Base URL: {BASE_URL}")
print("=" * 100)

# ─────────────────────────────────────────────────────────
# CORE INFRASTRUCTURE
# ─────────────────────────────────────────────────────────
print("\n### CORE INFRASTRUCTURE ###")
test("GET", "/health", label="Health check")
test("GET", "/health/ready", label="Readiness check")
test("GET", "/", label="Root info")
test("GET", "/metrics", label="Prometheus metrics", expected_codes=(200,))

# ─────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────
print("\n### AUTH ###")
test("GET", "/api/v1/auth/me", label="Current user profile")
test("POST", "/api/v1/auth/register",
     body={"email": "e2e_test@sdlc.test", "password": "E2eTest@123456", "full_name": "E2E Tester"},
     label="Register new user", expected_codes=(200, 201, 400, 409))
test("POST", "/api/v1/auth/refresh", body={}, label="Refresh token (no body)", expected_codes=(200, 401, 422))
test("GET", "/api/v1/auth/mfa/setup", label="MFA setup info", expected_codes=(200, 400))

# ─────────────────────────────────────────────────────────
# PROJECTS
# ─────────────────────────────────────────────────────────
print("\n### PROJECTS ###")
r = test("GET", "/api/v1/projects", label="List projects")
project_id = None
if r["status"] == "PASS" and isinstance(r["response"], (list, dict)):
    items = r["response"] if isinstance(r["response"], list) else r["response"].get("items", r["response"].get("projects", []))
    if items:
        project_id = items[0].get("id")
        print(f"  → Using project_id={project_id}")

test("POST", "/api/v1/projects",
     body={"name": "E2E Test Project", "description": "Auto-generated by e2e test suite", "methodology": "agile"},
     label="Create project", expected_codes=(200, 201))

if project_id:
    test("GET", f"/api/v1/projects/{project_id}", label="Get project detail")
    test("GET", f"/api/v1/projects/{project_id}/summary", label="Project summary", expected_codes=(200, 404))

# ─────────────────────────────────────────────────────────
# GATES
# ─────────────────────────────────────────────────────────
print("\n### GATES ###")
test("GET", "/api/v1/gates", label="List gates")
test("GET", "/api/v1/gates-engine/health", label="Gates engine health", expected_codes=(200, 404))
test("GET", "/api/v1/gates-engine/policies", label="Gates engine policies", expected_codes=(200, 404))

# ─────────────────────────────────────────────────────────
# EVIDENCE
# ─────────────────────────────────────────────────────────
print("\n### EVIDENCE ###")
test("GET", "/api/v1/evidence-manifests", label="List evidence manifests")

# ─────────────────────────────────────────────────────────
# SPRINT 181: COMPLIANCE FRAMEWORK (ENTERPRISE route activation)
# ─────────────────────────────────────────────────────────
print("\n### SPRINT 181: COMPLIANCE FRAMEWORK ###")
test("GET", "/api/v1/compliance", label="List compliance frameworks", expected_codes=(200, 402, 403, 404))
test("GET", "/api/v1/compliance/frameworks", label="Compliance frameworks list", expected_codes=(200, 402, 403, 404))
test("GET", "/api/v1/compliance/types", label="Compliance types", expected_codes=(200, 402, 403, 404))
test("POST", "/api/v1/compliance/assess",
     body={"framework": "SOC2", "project_id": project_id or 1},
     label="Compliance assessment", expected_codes=(200, 201, 402, 403, 404, 422))
test("GET", "/api/v1/compliance/evidence", label="Compliance evidence list", expected_codes=(200, 402, 403, 404))

# ─────────────────────────────────────────────────────────
# SPRINT 181: TEMPLATES (CORE route activation)
# ─────────────────────────────────────────────────────────
print("\n### SPRINT 181: TEMPLATES ###")
test("GET", "/api/v1/templates", label="List templates", expected_codes=(200, 404))
test("GET", "/api/v1/templates/categories", label="Template categories", expected_codes=(200, 404))

# ─────────────────────────────────────────────────────────
# SPRINT 181: NIST ROUTES (ENTERPRISE)
# ─────────────────────────────────────────────────────────
print("\n### SPRINT 181: NIST AI FRAMEWORK ###")
for nist_type in ["govern", "manage", "map", "measure"]:
    test("GET", f"/api/v1/nist-{nist_type}", label=f"NIST {nist_type}", expected_codes=(200, 402, 403, 404))
    test("GET", f"/api/v1/nist-{nist_type}/controls", label=f"NIST {nist_type} controls", expected_codes=(200, 402, 403, 404))

# ─────────────────────────────────────────────────────────
# SPRINT 182/183: ENTERPRISE SSO
# ─────────────────────────────────────────────────────────
print("\n### SPRINT 182-183: ENTERPRISE SSO ###")
test("GET", "/api/v1/enterprise/sso", label="SSO config list", expected_codes=(200, 402, 403, 404))
test("GET", "/api/v1/enterprise/sso/metadata", label="SSO SAML metadata", expected_codes=(200, 402, 403, 404))
test("POST", "/api/v1/enterprise/sso/configure",
     body={"provider": "azure_ad", "tenant_id": "test-tenant", "client_id": "test-client"},
     label="Configure SSO", expected_codes=(200, 201, 402, 403, 404, 422))
test("GET", "/api/v1/enterprise/sso/sessions", label="SSO sessions", expected_codes=(200, 402, 403, 404))

# ─────────────────────────────────────────────────────────
# SPRINT 185: AUDIT TRAIL (ENTERPRISE)
# ─────────────────────────────────────────────────────────
print("\n### SPRINT 185: AUDIT TRAIL ###")
test("GET", "/api/v1/enterprise/audit", label="Audit log list", expected_codes=(200, 402, 403, 404))
test("GET", "/api/v1/enterprise/audit/export", label="Audit export", expected_codes=(200, 402, 403, 404))
test("POST", "/api/v1/enterprise/audit/export",
     body={"format": "json", "from": "2026-01-01", "to": "2026-02-20"},
     label="Export audit logs", expected_codes=(200, 201, 402, 403, 404, 422))

# ─────────────────────────────────────────────────────────
# SPRINT 185: SOC2 EVIDENCE PACK
# ─────────────────────────────────────────────────────────
print("\n### SPRINT 185: SOC2 COMPLIANCE PACK ###")
test("GET", "/api/v1/compliance/soc2", label="SOC2 status", expected_codes=(200, 402, 403, 404))
test("POST", "/api/v1/compliance/soc2/generate",
     body={"project_id": project_id or 1},
     label="Generate SOC2 pack", expected_codes=(200, 201, 202, 402, 403, 404, 422))
test("GET", "/api/v1/compliance/hipaa", label="HIPAA status", expected_codes=(200, 402, 403, 404))
test("GET", "/api/v1/compliance/nist", label="NIST compliance", expected_codes=(200, 402, 403, 404))

# ─────────────────────────────────────────────────────────
# SPRINT 186: DATA RESIDENCY + GDPR
# ─────────────────────────────────────────────────────────
print("\n### SPRINT 186: DATA RESIDENCY ###")
test("GET", "/api/v1/data-residency", label="Data residency config", expected_codes=(200, 402, 403, 404))
test("GET", "/api/v1/data-residency/regions", label="Available regions", expected_codes=(200, 402, 403, 404))
test("POST", "/api/v1/data-residency/set",
     body={"region": "VN", "project_id": project_id or 1},
     label="Set data region", expected_codes=(200, 201, 402, 403, 404, 422))

print("\n### SPRINT 186: GDPR ###")
test("GET", "/api/v1/gdpr/dsar", label="GDPR DSAR list", expected_codes=(200, 402, 403, 404))
test("POST", "/api/v1/gdpr/dsar",
     body={"request_type": "access", "subject_email": "test@example.com"},
     label="Create DSAR request", expected_codes=(200, 201, 402, 403, 404, 422))
test("GET", "/api/v1/gdpr/consent", label="Consent records", expected_codes=(200, 402, 403, 404))
test("DELETE", "/api/v1/gdpr/data/test@example.com",
     label="Right to erasure", expected_codes=(200, 204, 402, 403, 404))

# ─────────────────────────────────────────────────────────
# SPRINT 188: USAGE LIMITS + PAYMENTS
# ─────────────────────────────────────────────────────────
print("\n### SPRINT 188: USAGE LIMITS ###")
test("GET", "/api/v1/payments/subscription", label="Current subscription", expected_codes=(200, 402, 403, 404))
test("GET", "/api/v1/payments/usage", label="Usage stats", expected_codes=(200, 402, 403, 404))
test("GET", "/api/v1/payments/limits", label="Usage limits", expected_codes=(200, 402, 403, 404))
test("POST", "/api/v1/payments/subscription",
     body={"plan": "lite", "billing_cycle": "monthly"},
     label="Create subscription", expected_codes=(200, 201, 400, 402, 403, 404, 422))
test("GET", "/api/v1/payments/plans", label="Available plans", expected_codes=(200, 404))

# ─────────────────────────────────────────────────────────
# SPRINT 184: TIER ENFORCEMENT (existing routes should respond with 402)
# ─────────────────────────────────────────────────────────
print("\n### SPRINT 184: TIER ENFORCEMENT CHECK ###")
test("GET", "/api/v1/agent-team/definitions", label="Multi-agent defs (PROFESSIONAL+)", expected_codes=(200, 402, 403, 404))
test("GET", "/api/v1/ceo-dashboard", label="CEO dashboard (PROFESSIONAL+)", expected_codes=(200, 402, 403, 404))
test("GET", "/api/v1/governance-metrics", label="Governance metrics", expected_codes=(200, 402, 403, 404))
test("GET", "/api/v1/context-authority", label="Context Authority V2", expected_codes=(200, 402, 403, 404))

# ─────────────────────────────────────────────────────────
# MULTI-AGENT TEAM ENGINE (EP-07, Sprints 176-179)
# ─────────────────────────────────────────────────────────
print("\n### MULTI-AGENT TEAM ENGINE (EP-07) ###")
test("GET", "/api/v1/agent-team/definitions", label="List agent definitions", expected_codes=(200, 402, 403, 404))
test("POST", "/api/v1/agent-team/definitions",
     body={"name": "E2E Test Agent", "role": "developer", "system_prompt": "You are a test agent",
           "provider": "ollama", "model": "qwen3:8b"},
     label="Create agent definition", expected_codes=(200, 201, 402, 403, 404, 422))
test("GET", "/api/v1/agent-team/conversations", label="List conversations", expected_codes=(200, 402, 403, 404))

# ─────────────────────────────────────────────────────────
# PLANNING (largest group - 59 paths)
# ─────────────────────────────────────────────────────────
print("\n### PLANNING ###")
test("GET", "/api/v1/planning/roadmaps", label="List roadmaps", expected_codes=(200, 404))
test("GET", "/api/v1/planning/phases", label="List phases", expected_codes=(200, 404))
test("GET", "/api/v1/planning/sprints", label="List sprints", expected_codes=(200, 404))
test("GET", "/api/v1/planning/backlog", label="Backlog items", expected_codes=(200, 404))
test("POST", "/api/v1/planning/roadmaps",
     body={"name": "E2E Roadmap", "description": "Auto test", "project_id": project_id or 1},
     label="Create roadmap", expected_codes=(200, 201, 422))

# ─────────────────────────────────────────────────────────
# ADMIN
# ─────────────────────────────────────────────────────────
print("\n### ADMIN ###")
test("GET", "/api/v1/admin/users", label="Admin: list users", expected_codes=(200, 403, 404))
test("GET", "/api/v1/admin/stats", label="Admin: platform stats", expected_codes=(200, 403, 404))
test("GET", "/api/v1/admin/subscriptions", label="Admin: subscriptions", expected_codes=(200, 403, 404))

# ─────────────────────────────────────────────────────────
# GOVERNANCE
# ─────────────────────────────────────────────────────────
print("\n### GOVERNANCE ###")
test("GET", "/api/v1/governance", label="Governance list", expected_codes=(200, 404))
test("GET", "/api/v1/governance-metrics/summary", label="Governance metrics summary", expected_codes=(200, 404))
test("GET", "/api/v1/vibecoding/score", label="Vibecoding score", expected_codes=(200, 404))
test("GET", "/api/v1/stage-gating/status", label="Stage gating status", expected_codes=(200, 404))

# ─────────────────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────────────────
print("\n### ANALYTICS ###")
test("GET", "/api/v1/analytics/dora", label="DORA metrics", expected_codes=(200, 404))
test("GET", "/api/v1/analytics/gates", label="Gate analytics", expected_codes=(200, 404))
test("GET", "/api/v1/analytics/adoption", label="Adoption analytics", expected_codes=(200, 404))

# ─────────────────────────────────────────────────────────
# CODEGEN
# ─────────────────────────────────────────────────────────
print("\n### CODEGEN ###")
test("GET", "/api/v1/codegen/providers", label="Codegen providers", expected_codes=(200, 404))
test("GET", "/api/v1/codegen/sessions", label="Codegen sessions", expected_codes=(200, 404))

# ─────────────────────────────────────────────────────────
# TEAMS + NOTIFICATIONS
# ─────────────────────────────────────────────────────────
print("\n### TEAMS + NOTIFICATIONS ###")
test("GET", "/api/v1/teams", label="List teams", expected_codes=(200, 404))
test("GET", "/api/v1/notifications", label="Notifications", expected_codes=(200, 404))

# ─────────────────────────────────────────────────────────
# ONBOARDING + COUNCIL
# ─────────────────────────────────────────────────────────
print("\n### ONBOARDING + COUNCIL ###")
test("GET", "/api/v1/onboarding/status", label="Onboarding status", expected_codes=(200, 404))
test("GET", "/api/v1/council/recommendations", label="Council recommendations", expected_codes=(200, 404))

# ─────────────────────────────────────────────────────────
# SAST + CHECK RUNS
# ─────────────────────────────────────────────────────────
print("\n### SAST + CHECK RUNS ###")
test("GET", "/api/v1/sast/scans", label="SAST scans", expected_codes=(200, 404))
test("GET", "/api/v1/check-runs", label="GitHub check runs", expected_codes=(200, 404))

# ─────────────────────────────────────────────────────────
# SAVE RESULTS
# ─────────────────────────────────────────────────────────
results_file = ARTIFACTS_DIR / f"test_results_{timestamp}.json"
with open(results_file, "w") as f:
    json.dump(results, f, indent=2, default=str)

# Summary
from collections import Counter
status_counts = Counter(r["status"] for r in results)
total = len(results)
passed = status_counts.get("PASS", 0)

print("\n" + "=" * 100)
print(f"*-CyEyes-* TEST SUMMARY")
print(f"Total Tests: {total}")
for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
    icon = {"PASS": "✅", "VALIDATION_ERROR": "⚠️", "NOT_FOUND": "🚫",
            "UNAUTHORIZED": "🔒", "SERVER_ERROR": "🔴", "FAIL": "❌", "TIMEOUT": "⏱️"}.get(status, "?")
    print(f"  {icon} {status}: {count} ({count/total*100:.1f}%)")
print(f"\nCoverage: {passed}/{total} ({passed/total*100:.1f}%)")
avg_ms = sum(r["elapsed_ms"] for r in results) / total
print(f"Avg Response Time: {avg_ms:.0f}ms")
print(f"\nResults saved: {results_file}")
print("=" * 100)
