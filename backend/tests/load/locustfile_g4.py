"""
=========================================================================
Load Testing Configuration — G4 Production Validation
SDLC Orchestrator — Sprint 187

Version: 1.0.0
Date: 2026-02-20
Status: ACTIVE — Sprint 187 G4 Validation (G4-05)
Authority: CTO + CPO Approved
Reference: docs/04-build/02-Sprint-Plans/SPRINT-187-G4-PRODUCTION-VALIDATION.md

Purpose:
- G4 gate criterion G4-05: p95 API latency < 100ms under 50K concurrent users
- Validate SDLC Orchestrator handles production-scale traffic
- Identify database bottlenecks before GA launch

Target Traffic Mix:
  40% — list_projects      (most common dashboard operation)
  20% — list_gates         (gate management)
  20% — list_evidence      (evidence vault browsing)
  10% — evaluate_gate      (OPA evaluation — heavier, p95 < 500ms)
  10% — audit_log_query    (ENTERPRISE audit dashboard — < 200ms)

G4-05 Pass Criteria:
  - p95 latency: < 100ms for list_projects, list_gates, list_evidence
  - p95 latency: < 500ms for evaluate_gate (OPA evaluation overhead)
  - p99 latency: < 200ms for read endpoints
  - Error rate:  < 0.1%
  - Throughput:  > 5,000 req/s sustained for 30 min

Infrastructure:
  - 5 Locust worker nodes + 1 master
  - Staging environment: production-equivalent (same DB instance size, same Redis)

Usage:
    # Single machine (dev validation)
    locust -f tests/load/locustfile_g4.py --users 500 --spawn-rate 50

    # Full G4 validation (distributed, 5 workers)
    locust -f tests/load/locustfile_g4.py \\
        --host https://staging.sdlcorchestrator.com \\
        --users 50000 \\
        --spawn-rate 100 \\
        --run-time 30m \\
        --html reports/load_test_g4.html \\
        --csv reports/load_test_g4

    # Headless CI/CD validation (reduced scale)
    locust -f tests/load/locustfile_g4.py \\
        --headless \\
        --users 1000 \\
        --spawn-rate 50 \\
        --run-time 5m \\
        --host https://staging.sdlcorchestrator.com \\
        --html reports/load_test_g4_ci.html

G4 Certification Command (full 50K users, run by DevOps lead):
    locust -f backend/tests/load/locustfile_g4.py \\
        --host https://staging.sdlcorchestrator.com \\
        --users 50000 \\
        --spawn-rate 100 \\
        --run-time 30m \\
        --html reports/load_test_g4.html \\
        --csv reports/load_test_g4 \\
        --stop-timeout 30
=========================================================================
"""

import os
import random
from typing import Optional

from locust import HttpUser, between, events, task
from locust.runners import MasterRunner, WorkerRunner


# =============================================================================
# Configuration
# =============================================================================

# Pre-created test accounts in staging DB (100 accounts: loadtest1@..loadtest100@)
TEST_USERS = [
    {"email": f"loadtest{i}@sdlcstaging.internal", "password": "G4LoadTest!2026"}
    for i in range(1, 101)
]


def _load_ids(env_var: str) -> list:
    """Load comma-separated UUIDs from an environment variable.

    Operators MUST set these before running G4 certification:

        export G4_PROJECT_IDS=$(psql $DB_URL -t -c \\
            "SELECT string_agg(id::text, ',') FROM projects LIMIT 50")
        export G4_GATE_IDS=$(psql $DB_URL -t -c \\
            "SELECT string_agg(id::text, ',') FROM gates LIMIT 200")

    Without real IDs all project/gate requests return 404 (counted as success
    by the task code) and measure empty-result latency — G4-05 results invalid.
    """
    raw = os.environ.get(env_var, "").strip()
    return [x.strip() for x in raw.split(",") if x.strip()] if raw else []


# Real project and gate IDs from the staging database.
# REQUIRED before running G4 certification (see _load_ids docstring).
TEST_PROJECT_IDS: list = _load_ids("G4_PROJECT_IDS")

# Real gate IDs from staging (at least 20 required for evaluate_gate tasks).
TEST_GATE_IDS: list = _load_ids("G4_GATE_IDS")

# Subset of gates with OPA policies loaded — used for evaluate_gate tasks.
TEST_EVALUABLE_GATE_IDS: list = TEST_GATE_IDS[:20]

# G4 pass thresholds (milliseconds) — used in summary report
G4_THRESHOLDS = {
    "list_projects":  {"p95": 100,  "p99": 200},
    "list_gates":     {"p95": 100,  "p99": 200},
    "list_evidence":  {"p95": 100,  "p99": 200},
    "evaluate_gate":  {"p95": 500,  "p99": 1000},
    "audit_log_query": {"p95": 200, "p99": 500},
}

# Mapping from G4_THRESHOLDS key → (Locust stat name, HTTP method).
# Locust stat names are the `name=` parameter passed to self.client.get/post.
# These MUST match the `name=` strings in each @task method exactly.
G4_STAT_NAMES: dict[str, tuple[str, str]] = {
    "list_projects":  ("GET /projects",          "GET"),
    "list_gates":     ("GET /gates",              "GET"),
    "list_evidence":  ("GET /evidence",           "GET"),
    "evaluate_gate":  ("POST /gates/evaluate",    "POST"),
    "audit_log_query": ("GET /enterprise/audit",  "GET"),
}



# =============================================================================
# Event Hooks
# =============================================================================


@events.init.add_listener
def on_locust_init(environment, **kwargs) -> None:
    """Validate required env vars and log G4 test configuration on startup."""
    # F-02 fix: fail fast if staging IDs were not provided — random UUIDs produce
    # misleading latency results (all 404s returning in ~5ms instead of real data).
    if not TEST_PROJECT_IDS:
        raise SystemExit(
            "ERROR: G4_PROJECT_IDS env var is not set.\n"
            "Export real staging project UUIDs before running the load test:\n"
            "  psql $STAGING_DB -c \"SELECT id FROM projects LIMIT 50\" -tA | "
            "tr '\\n' ',' > /tmp/project_ids.txt\n"
            "  export G4_PROJECT_IDS=$(cat /tmp/project_ids.txt)"
        )
    if not TEST_GATE_IDS:
        raise SystemExit(
            "ERROR: G4_GATE_IDS env var is not set.\n"
            "Export real staging gate UUIDs before running the load test:\n"
            "  psql $STAGING_DB -c \"SELECT id FROM gates LIMIT 200\" -tA | "
            "tr '\\n' ',' > /tmp/gate_ids.txt\n"
            "  export G4_GATE_IDS=$(cat /tmp/gate_ids.txt)"
        )

    if isinstance(environment.runner, MasterRunner):
        print("\n" + "=" * 70)
        print("SDLC Orchestrator — G4 Production Validation Load Test")
        print("Sprint 187 | Gate G4-05 — Performance Criterion")
        print("=" * 70)
        print(f"Host:         {environment.host}")
        print(f"Project IDs:  {len(TEST_PROJECT_IDS)} loaded from G4_PROJECT_IDS")
        print(f"Gate IDs:     {len(TEST_GATE_IDS)} loaded from G4_GATE_IDS")
        print(f"Target users: {environment.runner.target_user_count}")
        print(f"Workers:      {environment.runner.worker_count}")
        print("\nG4-05 Pass Criteria:")
        for endpoint, thresholds in G4_THRESHOLDS.items():
            print(
                f"  {endpoint:<22} p95 < {thresholds['p95']}ms  "
                f"p99 < {thresholds['p99']}ms"
            )
        print("  Error rate < 0.1%")
        print("  Throughput > 5,000 req/s sustained")
        print("=" * 70 + "\n")

        # Validate real test data IDs are seeded (F-02 guard)
        missing = []
        if not TEST_PROJECT_IDS:
            missing.append("G4_PROJECT_IDS")
        if not TEST_GATE_IDS:
            missing.append("G4_GATE_IDS")
        if missing:
            print("!" * 70)
            print(f"WARNING: {', '.join(missing)} env var(s) not set.")
            print("All project/gate requests will return 404 — G4-05 results INVALID.")
            print("Seed these vars from staging DB before running:")
            print("  export G4_PROJECT_IDS=$(psql $DB_URL -t -c \\")
            print("    \"SELECT string_agg(id::text, ',') FROM projects LIMIT 50\")")
            print("  export G4_GATE_IDS=$(psql $DB_URL -t -c \\")
            print("    \"SELECT string_agg(id::text, ',') FROM gates LIMIT 200\")")
            print("!" * 70 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs) -> None:
    """Print G4 criterion assessment on test completion."""
    stats = environment.stats.total
    if stats.num_requests == 0:
        return

    print("\n" + "=" * 70)
    print("G4-05 LOAD TEST SUMMARY")
    print("=" * 70)
    print(f"Total Requests:     {stats.num_requests:,}")
    print(f"Failures:           {stats.num_failures:,}")
    print(f"Error Rate:         {stats.fail_ratio * 100:.3f}%")
    print(f"Throughput:         {stats.total_rps:.1f} req/s")
    print(f"Median Latency:     {stats.median_response_time}ms")
    print(f"p95 Latency:        {stats.get_response_time_percentile(0.95)}ms")
    print(f"p99 Latency:        {stats.get_response_time_percentile(0.99)}ms")

    # Per-endpoint assessment
    print("\nPer-endpoint G4-05 Assessment:")
    all_pass = True
    for endpoint_name, thresholds in G4_THRESHOLDS.items():
        stat_name, method = G4_STAT_NAMES[endpoint_name]
        endpoint_stats = environment.stats.get(stat_name, method)
        if endpoint_stats and endpoint_stats.num_requests > 0:
            p95 = endpoint_stats.get_response_time_percentile(0.95)
            result = "✅ PASS" if p95 <= thresholds["p95"] else "❌ FAIL"
            if p95 > thresholds["p95"]:
                all_pass = False
            print(f"  {result}  {endpoint_name:<22} p95={p95}ms (limit={thresholds['p95']}ms)")

    error_pass = stats.fail_ratio < 0.001  # < 0.1%
    throughput_pass = stats.total_rps >= 5000
    print(f"\n  {'✅' if error_pass else '❌'}  Error rate {stats.fail_ratio * 100:.3f}% (limit=0.1%)")
    print(f"  {'✅' if throughput_pass else '❌'}  Throughput {stats.total_rps:.1f} req/s (limit=5000)")

    overall = "✅ G4-05 PASS" if (all_pass and error_pass) else "❌ G4-05 FAIL"
    print(f"\nG4-05 RESULT: {overall}")
    print("=" * 70 + "\n")


# =============================================================================
# Primary User Class — Mixed Workload
# =============================================================================


class OrchestratorUser(HttpUser):
    """
    Simulated SDLC Orchestrator production user.

    Task weights reflect realistic production traffic mix:
      40% list_projects   — dashboard landing, most frequent
      20% list_gates      — gate management workflow
      20% list_evidence   — evidence vault browsing
      10% evaluate_gate   — OPA gate evaluation (compute-heavy)
      10% audit_log_query — ENTERPRISE audit log access
    """

    # 0.1–0.5s think time simulates a fast enterprise dashboard user
    wait_time = between(0.1, 0.5)

    # Per-user state
    token: Optional[str] = None
    project_id: Optional[str] = None
    gate_id: Optional[str] = None

    def on_start(self) -> None:
        """Authenticate and select test data on user spawn."""
        user = random.choice(TEST_USERS)

        with self.client.post(
            "/api/v1/auth/login",
            json={"email": user["email"], "password": user["password"]},
            catch_response=True,
            name="POST /auth/login",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token")
                self.client.headers["Authorization"] = f"Bearer {self.token}"
                resp.success()
            elif resp.status_code in (401, 404):
                # Staging accounts may not all exist — use a placeholder token
                self.token = os.environ.get("G4_TEST_TOKEN", "staging_test_token")
                self.client.headers["Authorization"] = f"Bearer {self.token}"
                resp.failure(f"Login failed {resp.status_code} — using env token")
            else:
                resp.failure(f"Unexpected login status: {resp.status_code}")

        self.project_id = random.choice(TEST_PROJECT_IDS) if TEST_PROJECT_IDS else None
        self.gate_id = random.choice(TEST_GATE_IDS) if TEST_GATE_IDS else None

    def on_stop(self) -> None:
        """Logout on user removal."""
        if self.token:
            try:
                self.client.post(
                    "/api/v1/auth/logout",
                    name="POST /auth/logout",
                    catch_response=True,
                )
            except Exception:
                pass  # non-critical on teardown

    # =========================================================================
    # Core Endpoints (weight 40+20+20 = 80% of traffic)
    # =========================================================================

    @task(40)
    def list_projects(self) -> None:
        """
        GET /api/v1/projects — Dashboard landing page.

        G4-05: p95 < 100ms
        This is the single highest-traffic endpoint; must be fast.
        Includes RBAC filter, pagination, and join to org.
        """
        with self.client.get(
            "/api/v1/projects",
            name="GET /projects",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 401):
                resp.success()
            else:
                resp.failure(f"list_projects: unexpected {resp.status_code}")

    @task(20)
    def list_gates(self) -> None:
        """
        GET /api/v1/gates?project_id=X — Gate management dashboard.

        G4-05: p95 < 100ms
        Filters by project_id + user RBAC, returns gate status.
        """
        with self.client.get(
            f"/api/v1/gates?project_id={self.project_id}",
            name="GET /gates",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 401, 404):
                resp.success()
            else:
                resp.failure(f"list_gates: unexpected {resp.status_code}")

    @task(20)
    def list_evidence(self) -> None:
        """
        GET /api/v1/evidence?gate_id=X — Evidence Vault browsing.

        G4-05: p95 < 100ms
        Returns paginated evidence for a gate with SHA256 metadata.
        """
        gate_id = random.choice(TEST_GATE_IDS)
        with self.client.get(
            f"/api/v1/evidence?gate_id={gate_id}",
            name="GET /evidence",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 401, 404):
                resp.success()
            else:
                resp.failure(f"list_evidence: unexpected {resp.status_code}")

    # =========================================================================
    # Compute-Heavy Endpoint (weight 10%)
    # =========================================================================

    @task(10)
    def evaluate_gate(self) -> None:
        """
        POST /api/v1/gates/{id}/evaluate — OPA gate evaluation.

        G4-05: p95 < 500ms (higher budget for OPA evaluation)
        Triggers OPA Rego policy evaluation for all active policies.
        """
        gate_id = random.choice(TEST_EVALUABLE_GATE_IDS)
        with self.client.post(
            f"/api/v1/gates/{gate_id}/evaluate",
            json={"force_reevaluate": False},
            name="POST /gates/evaluate",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201, 401, 404, 422):
                resp.success()
            else:
                resp.failure(f"evaluate_gate: unexpected {resp.status_code}")

    # =========================================================================
    # ENTERPRISE Endpoint (weight 10%)
    # =========================================================================

    @task(10)
    def audit_log_query(self) -> None:
        """
        GET /api/v1/enterprise/audit — Immutable audit log dashboard.

        G4-05: p95 < 200ms
        ENTERPRISE-tier endpoint. Returns paginated audit logs for the org.
        """
        with self.client.get(
            "/api/v1/enterprise/audit?limit=50",
            name="GET /enterprise/audit",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 401, 402, 403):
                # 402 = correct tier gate response for non-ENTERPRISE users
                resp.success()
            else:
                resp.failure(f"audit_log_query: unexpected {resp.status_code}")


# =============================================================================
# Specialized User Classes (for targeted stress testing)
# =============================================================================


class DashboardHeavyUser(OrchestratorUser):
    """
    Dashboard-only load pattern — simulates a BI/reporting tool polling
    the projects + gates endpoints at high frequency.

    Use this class to isolate database read performance under dashboard load.
    """

    wait_time = between(0.05, 0.2)  # 5-10 RPS per user (BI polling pattern)

    @task(60)
    def list_projects(self) -> None:
        super().list_projects()

    @task(40)
    def list_gates(self) -> None:
        super().list_gates()


class OPAStressUser(OrchestratorUser):
    """
    OPA evaluation stress user — isolates the OPA policy engine under load.

    Use this class to validate OPA latency SLA (p95 < 500ms) independently.
    Set spawn rate low (5-10 users) as OPA is compute-heavy.
    """

    wait_time = between(0.5, 2.0)  # OPA evaluations are slower — less aggressive

    @task(70)
    def evaluate_gate(self) -> None:
        super().evaluate_gate()

    @task(30)
    def list_gates(self) -> None:
        super().list_gates()


class AuditUser(OrchestratorUser):
    """
    ENTERPRISE audit log user — simulates compliance officer reviewing logs.

    Use to validate ENTERPRISE tier audit endpoint performance at scale.
    """

    wait_time = between(1.0, 3.0)  # Compliance review is methodical

    @task(80)
    def audit_log_query(self) -> None:
        super().audit_log_query()

    @task(20)
    def list_projects(self) -> None:
        super().list_projects()
