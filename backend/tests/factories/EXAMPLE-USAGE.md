# Test Factories - Example Usage

**SDLC 5.2.0 Compliance** - Test-Driven Development
**Framework**: Test Strategy 2026
**Date**: January 28, 2026

---

## Purpose

This document demonstrates how to use test factories in SDLC Orchestrator tests. All examples follow the **Factory Pattern** from `.claude/skills/testing-patterns` and the **TDD Iron Law** from `.claude/skills/test-driven-development`.

---

## Quick Start

```python
from tests.factories import (
    get_mock_user,
    get_mock_project,
    get_mock_gate,
    get_mock_evidence,
    get_mock_policy,
    get_mock_codegen_spec,
)

# Basic usage
user = get_mock_user()
project = get_mock_project()
gate = get_mock_gate()

# With overrides
cto = get_mock_user({"role": "cto", "is_platform_admin": True})
approved_gate = get_mock_gate({"status": "APPROVED"})
```

---

## Example 1: Unit Test with Factories

```python
# backend/tests/services/test_gate_service.py

import pytest
from app.services.gate_service import GateService
from tests.factories import get_mock_gate, get_mock_user, get_mock_project


class TestGateService:
    """Unit tests for GateService"""

    @pytest.fixture
    def service(self):
        """Fixture: GateService instance"""
        return GateService()

    def test_create_gate_with_valid_data(self, service):
        """
        RED → GREEN → REFACTOR

        Test: GateService.create_gate() creates gate with valid data
        """
        # Arrange (using factories)
        user = get_mock_user({"role": "engineering_manager"})
        project = get_mock_project({"owner_id": user["id"]})
        gate_data = {
            "gate_name": "Authentication - G1",
            "gate_type": "G1_DESIGN_READY",
            "stage": "WHAT",
            "project_id": project["id"],
            "created_by": user["id"],
        }

        # Act
        gate = service.create_gate(gate_data)

        # Assert
        assert gate.id is not None
        assert gate.status == "DRAFT"
        assert gate.gate_name == "Authentication - G1"
        assert gate.project_id == project["id"]

    def test_approve_gate_updates_status_and_notifies(self, service):
        """
        RED → GREEN → REFACTOR

        Test: GateService.approve() updates status and sends notification
        """
        # Arrange
        cto = get_mock_user({"role": "cto"})
        gate = get_mock_gate({
            "status": "PENDING_APPROVAL",
            "created_by": get_mock_user()["id"],
        })

        # Act
        service.approve(gate, approved_by=cto["id"])

        # Assert
        assert gate["status"] == "APPROVED"
        assert gate["approved_at"] is not None
        # Verify notification sent (mock or real service)
```

---

## Example 2: Integration Test with Real Services

```python
# backend/tests/integration/test_gate_api.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.factories import get_mock_gate_create_data, get_mock_user


class TestGateAPI:
    """Integration tests for Gate API endpoints"""

    @pytest.fixture
    def client(self):
        """Use REAL services (PostgreSQL, Redis, OPA, MinIO in Docker)"""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Authenticated user headers"""
        user = get_mock_user({"role": "engineering_manager"})
        # Create JWT token with user data
        token = create_test_jwt_token(user_id=user["id"], role=user["role"])
        return {"Authorization": f"Bearer {token}"}

    def test_create_gate_api_success(self, client, auth_headers):
        """
        Integration: POST /api/v1/gates creates gate

        Test uses real PostgreSQL database (Docker Compose)
        """
        # Arrange
        gate_data = get_mock_gate_create_data({
            "gate_name": "Test Gate - G1",
        })

        # Act
        response = client.post(
            "/api/v1/gates",
            json=gate_data,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 201
        assert response.json()["status"] == "DRAFT"
        assert "id" in response.json()

    def test_approve_gate_api_requires_authorization(self, client):
        """
        Integration: POST /api/v1/gates/{id}/approve requires auth
        """
        # Arrange
        gate_id = "non-existent-id"

        # Act
        response = client.post(f"/api/v1/gates/{gate_id}/approve")

        # Assert
        assert response.status_code == 401
```

---

## Example 3: E2E Test with Playwright

```typescript
// frontend/web/tests/e2e/gate-creation.spec.ts

import { test, expect } from '@playwright/test';

test('Engineering Manager creates gate and CTO approves', async ({ page }) => {
  // Login as Engineering Manager
  await page.goto('/login');
  await page.fill('[name="email"]', 'em@example.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('[type="submit"]');

  // Create gate (using factory-like data)
  await page.click('text=Create Gate');
  await page.fill('[name="gate_name"]', 'Authentication - G1');
  await page.selectOption('[name="gate_type"]', 'G1_DESIGN_READY');
  await page.fill('[name="description"]', 'Design Ready gate for authentication');
  await page.click('text=Create');

  // Verify gate created
  await expect(page.locator('text=Authentication - G1')).toBeVisible();
  await expect(page.locator('text=Status: DRAFT')).toBeVisible();

  // Logout and login as CTO
  await page.click('text=Logout');
  await page.fill('[name="email"]', 'cto@example.com');
  await page.fill('[name="password"]', 'cto_password');
  await page.click('[type="submit"]');

  // Approve gate
  await page.click('text=Authentication - G1');
  await page.click('text=Approve');

  // Verify gate approved
  await expect(page.locator('text=Status: APPROVED')).toBeVisible();
});
```

---

## Example 4: Framework Compliance Test

```python
# backend/tests/compliance/test_framework_compliance.py

import pytest
from pathlib import Path
import yaml
from app.services.gate_service import GateService
from tests.factories import get_mock_gate


class TestSDLC520Compliance:
    """
    Verify SDLC Orchestrator implements SDLC 5.2.0 framework correctly.
    """

    @pytest.fixture
    def framework_gates(self):
        """Load gate definitions from framework submodule"""
        framework_path = Path("SDLC-Enterprise-Framework/03-Templates-Tools/Gate-Templates/")
        gates = {}
        for yaml_file in framework_path.glob("*.yaml"):
            with open(yaml_file) as f:
                gate_data = yaml.safe_load(f)
                gates[gate_data["gate_id"]] = gate_data
        return gates

    def test_g1_gate_matches_framework(self, framework_gates):
        """
        Verify G1 Design Ready gate matches framework definition
        """
        # Get G1 from framework
        framework_g1 = framework_gates["G1"]

        # Get G1 from Orchestrator (using factory)
        orchestrator_g1 = get_mock_gate({
            "gate_type": "G1_DESIGN_READY",
            "stage": "WHAT",
        })

        # Compare exit criteria
        framework_criteria = set(framework_g1["exit_criteria"])
        orchestrator_criteria = set(orchestrator_g1["exit_criteria"])

        # Assert
        assert framework_criteria == orchestrator_criteria, \
            f"G1 exit criteria mismatch. Framework: {framework_criteria}, Orchestrator: {orchestrator_criteria}"
```

---

## Example 5: Load Test with Factories

```python
# tests/load/locustfile.py

from locust import HttpUser, task, between
from tests.factories import get_mock_gate_create_data, get_mock_user_login_data


class SDLCOrchestratorUser(HttpUser):
    """Simulate user behavior for load testing"""

    wait_time = between(1, 5)
    host = "https://staging.sdlc-orchestrator.com"

    def on_start(self):
        """Login before test (using factory)"""
        login_data = get_mock_user_login_data({
            "email": f"loadtest{self.user_id}@example.com",
            "password": "loadtest_password",
        })

        response = self.client.post("/api/v1/auth/login", json=login_data)
        self.token = response.json()["access_token"]

    @task(2)
    def create_gate(self):
        """POST /api/v1/gates (using factory)"""
        gate_data = get_mock_gate_create_data({
            "gate_name": f"Load Test Gate {self.user_id}",
        })

        self.client.post(
            "/api/v1/gates",
            json=gate_data,
            headers={"Authorization": f"Bearer {self.token}"},
            name="Create Gate",
        )
```

---

## Factory Pattern Benefits

### ✅ **DO** (With Factories)

```python
# Reusable, consistent, DRY
user = get_mock_user()
cto = get_mock_user({"role": "cto"})
dev = get_mock_user({"role": "developer"})
```

### ❌ **DON'T** (Hardcoded)

```python
# Duplicated, inconsistent, WET
user1 = {
    "id": "user-123",
    "email": "test@example.com",
    "role": "developer",
    # Missing fields!
}

user2 = {
    "id": "user-456",
    "email": "cto@example.com",
    "role": "cto",
    "is_platform_admin": True,
    # Different structure!
}
```

---

## Best Practices

1. **ALWAYS use factories** (no hardcoded test data)
2. **Override only what you need** (use defaults for the rest)
3. **Keep factories simple** (no complex logic in factories)
4. **One factory per model** (user_factory, project_factory, etc.)
5. **Factories return dicts** (not model instances, for flexibility)
6. **Use descriptive overrides** (make intent clear)

---

## Anti-Patterns to Avoid

### ❌ Testing Mock Behavior

```python
# BAD - Testing the mock, not the code
mock_service = Mock()
mock_service.create_gate.return_value = {"id": "123"}

result = mock_service.create_gate(data)
assert mock_service.create_gate.called  # Testing mock!
```

### ✅ Testing Real Behavior

```python
# GOOD - Testing actual code with factory data
gate_data = get_mock_gate_create_data()
result = gate_service.create_gate(gate_data)

assert result.id is not None  # Testing real logic!
assert result.status == "DRAFT"
```

---

## TDD Workflow with Factories

### Step 1: RED - Write Failing Test

```python
def test_create_gate_with_valid_data(service):
    """RED: Not implemented yet"""
    gate_data = get_mock_gate_create_data()  # Use factory
    gate = service.create_gate(gate_data)

    assert gate.id is not None  # WILL FAIL (method doesn't exist)
```

### Step 2: Run Test (Watch it Fail)

```bash
$ pytest backend/tests/services/test_gate_service.py::test_create_gate_with_valid_data

# EXPECTED OUTPUT:
# FAIL: AttributeError: 'GateService' object has no attribute 'create_gate'
```

### Step 3: GREEN - Minimal Implementation

```python
class GateService:
    def create_gate(self, data: Dict) -> Gate:
        return Gate(id=str(uuid4()), **data)  # Minimal code to pass
```

### Step 4: Run Test (Watch it Pass)

```bash
$ pytest backend/tests/services/test_gate_service.py::test_create_gate_with_valid_data

# EXPECTED OUTPUT:
# PASS
```

### Step 5: REFACTOR (Keep Tests Green)

```python
class GateService:
    def create_gate(self, data: Dict) -> Gate:
        # Extract ID generation, add validation, etc.
        gate = Gate(
            id=str(uuid4()),
            status="DRAFT",
            **data
        )
        self.db.add(gate)
        self.db.commit()
        return gate
```

---

## References

- **Test Strategy**: [docs/05-test/00-TEST-STRATEGY-2026.md](../../docs/05-test/00-TEST-STRATEGY-2026.md)
- **Remediation Plan**: [docs/05-test/REMEDIATION-PLAN-GOLIVE-2026.md](../../docs/05-test/REMEDIATION-PLAN-GOLIVE-2026.md)
- **TDD Skill**: [.claude/skills/test-driven-development](/.claude/skills/test-driven-development/SKILL.md)
- **Testing Patterns Skill**: [.claude/skills/testing-patterns](/.claude/skills/testing-patterns/SKILL.md)

---

**Last Updated**: January 28, 2026
**Sprint**: 107 (Foundation & Infrastructure)
**Framework**: SDLC 5.2.0 (7-Pillar + AI Governance Principles)
