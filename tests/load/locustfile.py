"""
=========================================================================
Locust Load Testing - SDLC Orchestrator API
Week 5 Day 2 - Performance & Load Testing

Purpose:
- Load test 23 API endpoints (4 routers: auth, gates, evidence, policies)
- Simulate 100K concurrent users (target)
- Measure p50/p95/p99 latency (target: <100ms p95)
- Identify bottlenecks (database, Redis, API)

Test Configuration:
- Users: 100,000 (100K concurrent)
- Spawn rate: 1000 users/second (100 seconds ramp-up)
- Duration: 30 minutes sustained load
- Host: http://localhost:8000

Test Scenarios (Weighted by Real Usage):
1. Authentication Flow (30% of traffic):
   - Login (15%)
   - Token refresh (10%)
   - Get user profile (5%)

2. Gates Management (40% of traffic):
   - List gates (20%)
   - Get gate details (10%)
   - Create gate (5%)
   - Update gate (3%)
   - Delete gate (2%)

3. Evidence Vault (20% of traffic):
   - List evidence (10%)
   - Upload evidence (5%)
   - Get evidence details (3%)
   - Download evidence (2%)

4. Policies Management (10% of traffic):
   - List policies (5%)
   - Get policy details (3%)
   - Create policy (1%)
   - Update policy (1%)

Performance Targets (SDLC 4.9 Requirements):
- p50 latency: <50ms
- p95 latency: <100ms ⭐ CRITICAL
- p99 latency: <200ms
- Error rate: <0.1%
- Throughput: >1000 req/s

OWASP ASVS Compliance:
- V11.1.4: Load testing validates scalability
- V11.1.5: Performance monitoring integrated
=========================================================================
"""

import random
import time
from typing import Dict, List

from locust import HttpUser, between, task


class SDLCOrchestratorUser(HttpUser):
    """
    Simulated user for SDLC Orchestrator API load testing.

    User Behavior:
    - Login once at spawn (setup)
    - Perform weighted tasks based on real usage patterns
    - Wait 1-3 seconds between requests (realistic user behavior)
    """

    # Wait time between tasks (1-3 seconds)
    wait_time = between(1, 3)

    # API base path
    api_base = "/api/v1"

    # User state
    access_token: str = ""
    refresh_token: str = ""
    user_id: str = ""
    project_id: str = ""
    gate_id: str = ""
    evidence_id: str = ""
    policy_id: str = ""

    def on_start(self):
        """
        Setup: Login user and get access token.

        Called once when user spawns.
        """
        self.login()

    def login(self):
        """
        Login user and get JWT access token.

        POST /api/v1/auth/login
        """
        response = self.client.post(
            f"{self.api_base}/auth/login",
            json={
                "email": "nguyen.van.anh@mtc.com.vn",
                "password": "SecurePassword123!",
            },
            name="/auth/login",
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token", "")
            self.refresh_token = data.get("refresh_token", "")

            # Decode JWT to get user_id (simple base64 decode of payload)
            # Format: header.payload.signature
            # Payload contains: {"sub": "user_id", ...}
            try:
                import base64
                import json

                payload = self.access_token.split(".")[1]
                # Add padding if needed
                payload += "=" * (4 - len(payload) % 4)
                decoded = base64.urlsafe_b64decode(payload)
                token_data = json.loads(decoded)
                self.user_id = token_data.get("sub", "")
            except Exception:
                # If decode fails, use default user_id
                self.user_id = "25e9ed25-c232-4ce3-a3ea-5458a85a915b"

    def get_headers(self) -> Dict[str, str]:
        """
        Get request headers with Authorization token.

        Returns:
            Dict with Authorization header
        """
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    # ========================================================================
    # AUTHENTICATION TASKS (30% of traffic)
    # ========================================================================

    @task(15)
    def auth_login(self):
        """
        Login user (15% of traffic).

        POST /api/v1/auth/login
        """
        self.client.post(
            f"{self.api_base}/auth/login",
            json={
                "email": "nguyen.van.anh@mtc.com.vn",
                "password": "SecurePassword123!",
            },
            name="/auth/login",
        )

    @task(10)
    def auth_refresh(self):
        """
        Refresh access token (10% of traffic).

        POST /api/v1/auth/refresh
        """
        self.client.post(
            f"{self.api_base}/auth/refresh",
            json={"refresh_token": self.refresh_token},
            name="/auth/refresh",
        )

    @task(5)
    def auth_get_me(self):
        """
        Get current user profile (5% of traffic).

        GET /api/v1/auth/me
        """
        self.client.get(
            f"{self.api_base}/auth/me",
            headers=self.get_headers(),
            name="/auth/me",
        )

    # ========================================================================
    # GATES MANAGEMENT TASKS (40% of traffic)
    # ========================================================================

    @task(20)
    def gates_list(self):
        """
        List all gates (20% of traffic).

        GET /api/v1/gates?limit=50&offset=0
        """
        response = self.client.get(
            f"{self.api_base}/gates?limit=50&offset=0",
            headers=self.get_headers(),
            name="/gates (list)",
        )

        # Extract first gate_id for detail requests
        if response.status_code == 200:
            data = response.json()
            if data.get("gates") and len(data["gates"]) > 0:
                self.gate_id = data["gates"][0].get("id", "")

    @task(10)
    def gates_get(self):
        """
        Get gate details (10% of traffic).

        GET /api/v1/gates/{gate_id}
        """
        # Use stored gate_id or create placeholder
        gate_id = self.gate_id or "550e8400-e29b-41d4-a716-446655440000"

        self.client.get(
            f"{self.api_base}/gates/{gate_id}",
            headers=self.get_headers(),
            name="/gates/{id} (get)",
        )

    @task(5)
    def gates_create(self):
        """
        Create new gate (5% of traffic).

        POST /api/v1/gates
        """
        response = self.client.post(
            f"{self.api_base}/gates",
            headers=self.get_headers(),
            json={
                "project_id": "550e8400-e29b-41d4-a716-446655440001",
                "gate_type": random.choice(["G0.1", "G0.2", "G1", "G2", "G3", "G4"]),
                "status": "pending",
                "title": f"Load Test Gate {random.randint(1, 100000)}",
                "description": "Auto-generated gate for load testing",
            },
            name="/gates (create)",
        )

        # Store created gate_id for future requests
        if response.status_code == 201:
            data = response.json()
            self.gate_id = data.get("id", "")

    @task(3)
    def gates_update(self):
        """
        Update gate (3% of traffic).

        PUT /api/v1/gates/{gate_id}
        """
        gate_id = self.gate_id or "550e8400-e29b-41d4-a716-446655440000"

        self.client.put(
            f"{self.api_base}/gates/{gate_id}",
            headers=self.get_headers(),
            json={
                "status": random.choice(["pending", "approved", "rejected"]),
                "description": "Updated via load test",
            },
            name="/gates/{id} (update)",
        )

    @task(2)
    def gates_delete(self):
        """
        Delete gate (2% of traffic).

        DELETE /api/v1/gates/{gate_id}
        """
        gate_id = self.gate_id or "550e8400-e29b-41d4-a716-446655440000"

        self.client.delete(
            f"{self.api_base}/gates/{gate_id}",
            headers=self.get_headers(),
            name="/gates/{id} (delete)",
        )

    # ========================================================================
    # EVIDENCE VAULT TASKS (20% of traffic)
    # ========================================================================

    @task(10)
    def evidence_list(self):
        """
        List all evidence (10% of traffic).

        GET /api/v1/evidence?limit=50&offset=0
        """
        response = self.client.get(
            f"{self.api_base}/evidence?limit=50&offset=0",
            headers=self.get_headers(),
            name="/evidence (list)",
        )

        # Extract first evidence_id for detail requests
        if response.status_code == 200:
            data = response.json()
            if data.get("evidence") and len(data["evidence"]) > 0:
                self.evidence_id = data["evidence"][0].get("id", "")

    @task(5)
    def evidence_create(self):
        """
        Upload evidence file (5% of traffic).

        POST /api/v1/evidence
        """
        # Simulate file upload with small JSON payload
        response = self.client.post(
            f"{self.api_base}/evidence",
            headers=self.get_headers(),
            json={
                "gate_id": self.gate_id or "550e8400-e29b-41d4-a716-446655440000",
                "file_name": f"load_test_{random.randint(1, 100000)}.pdf",
                "file_type": "application/pdf",
                "file_size": random.randint(1000, 10000000),  # 1KB - 10MB
                "description": "Load test evidence file",
            },
            name="/evidence (upload)",
        )

        # Store created evidence_id
        if response.status_code == 201:
            data = response.json()
            self.evidence_id = data.get("id", "")

    @task(3)
    def evidence_get(self):
        """
        Get evidence details (3% of traffic).

        GET /api/v1/evidence/{evidence_id}
        """
        evidence_id = self.evidence_id or "550e8400-e29b-41d4-a716-446655440002"

        self.client.get(
            f"{self.api_base}/evidence/{evidence_id}",
            headers=self.get_headers(),
            name="/evidence/{id} (get)",
        )

    @task(2)
    def evidence_download(self):
        """
        Download evidence file (2% of traffic).

        GET /api/v1/evidence/{evidence_id}/download
        """
        evidence_id = self.evidence_id or "550e8400-e29b-41d4-a716-446655440002"

        self.client.get(
            f"{self.api_base}/evidence/{evidence_id}/download",
            headers=self.get_headers(),
            name="/evidence/{id}/download",
        )

    # ========================================================================
    # POLICIES MANAGEMENT TASKS (10% of traffic)
    # ========================================================================

    @task(5)
    def policies_list(self):
        """
        List all policies (5% of traffic).

        GET /api/v1/policies?limit=50&offset=0
        """
        response = self.client.get(
            f"{self.api_base}/policies?limit=50&offset=0",
            headers=self.get_headers(),
            name="/policies (list)",
        )

        # Extract first policy_id for detail requests
        if response.status_code == 200:
            data = response.json()
            if data.get("policies") and len(data["policies"]) > 0:
                self.policy_id = data["policies"][0].get("id", "")

    @task(3)
    def policies_get(self):
        """
        Get policy details (3% of traffic).

        GET /api/v1/policies/{policy_id}
        """
        policy_id = self.policy_id or "550e8400-e29b-41d4-a716-446655440003"

        self.client.get(
            f"{self.api_base}/policies/{policy_id}",
            headers=self.get_headers(),
            name="/policies/{id} (get)",
        )

    @task(1)
    def policies_create(self):
        """
        Create new policy (1% of traffic).

        POST /api/v1/policies
        """
        response = self.client.post(
            f"{self.api_base}/policies",
            headers=self.get_headers(),
            json={
                "name": f"Load Test Policy {random.randint(1, 100000)}",
                "description": "Auto-generated policy for load testing",
                "gate_type": random.choice(["G0.1", "G0.2", "G1", "G2", "G3", "G4"]),
                "policy_content": {
                    "package": "sdlc.gates",
                    "rules": [
                        {
                            "name": "test_rule",
                            "condition": "input.test == true",
                            "result": "approved",
                        }
                    ],
                },
            },
            name="/policies (create)",
        )

        # Store created policy_id
        if response.status_code == 201:
            data = response.json()
            self.policy_id = data.get("id", "")

    @task(1)
    def policies_update(self):
        """
        Update policy (1% of traffic).

        PUT /api/v1/policies/{policy_id}
        """
        policy_id = self.policy_id or "550e8400-e29b-41d4-a716-446655440003"

        self.client.put(
            f"{self.api_base}/policies/{policy_id}",
            headers=self.get_headers(),
            json={
                "description": "Updated via load test",
                "policy_content": {
                    "package": "sdlc.gates.updated",
                    "rules": [
                        {
                            "name": "updated_rule",
                            "condition": "input.updated == true",
                            "result": "approved",
                        }
                    ],
                },
            },
            name="/policies/{id} (update)",
        )


class AdminUser(HttpUser):
    """
    Admin user with heavier write operations.

    Admin tasks (5% of total traffic):
    - Create/update/delete gates
    - Create/update policies
    - Bulk operations
    """

    wait_time = between(2, 5)
    api_base = "/api/v1"
    access_token: str = ""
    weight = 1  # 5% of users are admins

    def on_start(self):
        """Login as admin."""
        response = self.client.post(
            f"{self.api_base}/auth/login",
            json={
                "email": "admin@sdlc-orchestrator.com",
                "password": "AdminSecure456!",
            },
            name="/auth/login (admin)",
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token", "")

    def get_headers(self) -> Dict[str, str]:
        """Get admin headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    @task(3)
    def admin_create_gates(self):
        """Admin: Create multiple gates."""
        for _ in range(5):
            self.client.post(
                f"{self.api_base}/gates",
                headers=self.get_headers(),
                json={
                    "project_id": "550e8400-e29b-41d4-a716-446655440001",
                    "gate_type": random.choice(
                        ["G0.1", "G0.2", "G1", "G2", "G3", "G4"]
                    ),
                    "status": "pending",
                    "title": f"Admin Gate {random.randint(1, 100000)}",
                    "description": "Admin-created gate",
                },
                name="/gates (admin create)",
            )

    @task(2)
    def admin_create_policies(self):
        """Admin: Create new policies."""
        self.client.post(
            f"{self.api_base}/policies",
            headers=self.get_headers(),
            json={
                "name": f"Admin Policy {random.randint(1, 100000)}",
                "description": "Admin-created policy",
                "gate_type": random.choice(["G0.1", "G0.2", "G1", "G2", "G3", "G4"]),
                "policy_content": {
                    "package": "sdlc.gates.admin",
                    "rules": [
                        {
                            "name": "admin_rule",
                            "condition": "input.admin == true",
                            "result": "approved",
                        }
                    ],
                },
            },
            name="/policies (admin create)",
        )


# ============================================================================
# LOAD TEST CONFIGURATION
# ============================================================================

"""
How to run this load test:

1. Start backend server:
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000

2. Run load test (Web UI):
   locust -f tests/load/locustfile.py --host http://localhost:8000

   Then open: http://localhost:8089
   Configure:
   - Users: 100000
   - Spawn rate: 1000
   - Host: http://localhost:8000

3. Run load test (Headless):
   locust -f tests/load/locustfile.py \
     --host http://localhost:8000 \
     --users 100000 \
     --spawn-rate 1000 \
     --run-time 30m \
     --headless \
     --csv=reports/load_test \
     --html=reports/load_test_report.html

4. Monitor results:
   - Real-time: http://localhost:8089
   - CSV: reports/load_test_stats.csv
   - HTML: reports/load_test_report.html

Performance Targets (SDLC 4.9):
✅ p50 latency: <50ms
✅ p95 latency: <100ms ⭐ CRITICAL
✅ p99 latency: <200ms
✅ Error rate: <0.1%
✅ Throughput: >1000 req/s

OWASP ASVS Compliance:
✅ V11.1.4: Load testing validates scalability
✅ V11.1.5: Performance monitoring integrated
"""
