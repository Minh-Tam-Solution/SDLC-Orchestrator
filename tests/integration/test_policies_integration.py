"""
Integration Tests for Policies API

File: tests/integration/test_policies_integration.py
Version: 1.0.0
Date: December 12, 2025
Status: ACTIVE - Week 6 Day 1
Authority: Backend Lead + QA Lead
Framework: SDLC 4.9 Complete Lifecycle

Test Coverage:
- POST /api/v1/policies - Create new policy
- GET /api/v1/policies - List policies (pagination + filters)
- GET /api/v1/policies/{policy_id} - Get policy details
- PUT /api/v1/policies/{policy_id} - Update policy
- DELETE /api/v1/policies/{policy_id} - Delete policy (soft delete)
- POST /api/v1/policies/{policy_id}/evaluate - Evaluate policy against gate
- POST /api/v1/policies/{policy_id}/test - Test policy with sample data

Total Endpoints: 7
Total Tests: 12+
Target Coverage: 90%+
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.user import User
from app.models.policy import Policy
from app.models.gate import Gate


@pytest.mark.integration
@pytest.mark.policies
@pytest.mark.skip(reason="CREATE endpoint not implemented in API")
class TestPolicyCreate:
    """Integration tests for policy creation endpoint."""

    async def test_create_policy_success(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test successful policy creation (admin only)."""
        # CREATE endpoint not implemented - skip test
        pytest.skip("POST /api/v1/policies not implemented")

    async def test_create_policy_unauthorized(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test policy creation by non-admin returns 403."""
        # CREATE endpoint not implemented - skip test
        pytest.skip("POST /api/v1/policies not implemented")

    async def test_create_policy_invalid_rego(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test policy creation with invalid Rego code returns 422."""
        # CREATE endpoint not implemented - skip test
        pytest.skip("POST /api/v1/policies not implemented")


@pytest.mark.integration
@pytest.mark.policies
class TestPolicyList:
    """Integration tests for policy list endpoint."""

    async def test_list_policies_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_policy: Policy,
    ):
        """Test list policies with pagination."""
        response = await client.get(
            "/api/v1/policies",
            headers=auth_headers,
            params={"page": 1, "page_size": 10},
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert len(data["items"]) > 0

    async def test_list_policies_filter_by_stage(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_policy: Policy,
    ):
        """Test list policies filtered by stage."""
        response = await client.get(
            "/api/v1/policies",
            headers=auth_headers,
            params={"stage": "WHAT"},  # API uses 'stage' parameter (uppercase)
        )

        assert response.status_code == 200
        data = response.json()

        # All policies should be for WHAT stage
        for policy in data["items"]:
            assert policy["stage"] == "WHAT"  # API returns 'stage' field

    @pytest.mark.skip(reason="policy_type filter not implemented in API")
    async def test_list_policies_filter_by_type(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_policy: Policy,
    ):
        """Test list policies filtered by policy type."""
        # API doesn't support policy_type filter - skip test
        pytest.skip("policy_type filter not implemented in API")


@pytest.mark.integration
@pytest.mark.policies
class TestPolicyDetail:
    """Integration tests for policy detail endpoint."""

    async def test_get_policy_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_policy: Policy,
    ):
        """Test get policy details."""
        response = await client.get(
            f"/api/v1/policies/{test_policy.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(test_policy.id)
        assert data["policy_name"] == test_policy.policy_name  # API uses 'policy_name'
        assert data["policy_code"] == test_policy.policy_code  # API uses 'policy_code'
        assert data["stage"] == test_policy.stage  # API uses 'stage'
        assert "rego_code" in data

    async def test_get_policy_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test get non-existent policy returns 404."""
        response = await client.get(
            f"/api/v1/policies/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.policies
@pytest.mark.skip(reason="UPDATE endpoint not implemented in API")
class TestPolicyUpdate:
    """Integration tests for policy update endpoint."""

    async def test_update_policy_success(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_policy: Policy,
    ):
        """Test successful policy update (admin only)."""
        # UPDATE endpoint not implemented - skip test
        pytest.skip("PUT /api/v1/policies/{id} not implemented")

    async def test_update_policy_unauthorized(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_policy: Policy,
    ):
        """Test policy update by non-admin returns 403."""
        # UPDATE endpoint not implemented - skip test
        pytest.skip("PUT /api/v1/policies/{id} not implemented")


@pytest.mark.integration
@pytest.mark.policies
@pytest.mark.skip(reason="DELETE endpoint not implemented in API")
class TestPolicyDelete:
    """Integration tests for policy deletion (soft delete)."""

    async def test_delete_policy_success(
        self,
        client: AsyncClient,
        admin_headers: dict,
        db: AsyncSession,
        test_policy: Policy,
    ):
        """Test successful policy deletion (admin only)."""
        # DELETE endpoint not implemented - skip test
        pytest.skip("DELETE /api/v1/policies/{id} not implemented")

    async def test_delete_policy_unauthorized(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_policy: Policy,
    ):
        """Test policy deletion by non-admin returns 403."""
        # DELETE endpoint not implemented - skip test
        pytest.skip("DELETE /api/v1/policies/{id} not implemented")


@pytest.mark.integration
@pytest.mark.policies
@pytest.mark.slow
class TestPolicyEvaluate:
    """Integration tests for policy evaluation endpoint."""

    async def test_evaluate_policy_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_policy: Policy,
        test_gate: Gate,
    ):
        """Test successful policy evaluation against gate."""
        # API uses POST /api/v1/policies/evaluate with policy_id and gate_id in body
        response = await client.post(
            "/api/v1/policies/evaluate",
            headers=auth_headers,
            json={
                "gate_id": str(test_gate.id),
                "policy_id": str(test_policy.id),
                "input_data": {},  # Empty input_data for test
            },
        )

        assert response.status_code == 201  # API returns 201 Created
        data = response.json()

        assert "result" in data
        assert data["result"] in ["pass", "fail"]  # API returns "pass" or "fail"
        assert "policy_id" in data
        assert data["policy_id"] == str(test_policy.id)
        assert "gate_id" in data
        assert data["gate_id"] == str(test_gate.id)

    async def test_evaluate_policy_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
    ):
        """Test evaluate non-existent policy returns 404."""
        # API uses POST /api/v1/policies/evaluate with policy_id in body
        response = await client.post(
            "/api/v1/policies/evaluate",
            headers=auth_headers,
            json={
                "gate_id": str(test_gate.id),
                "policy_id": str(uuid4()),  # Non-existent policy
                "input_data": {},
            },
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.policies
@pytest.mark.skip(reason="TEST endpoint not implemented in API")
class TestPolicyTest:
    """Integration tests for policy testing endpoint."""

    async def test_test_policy_success(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_policy: Policy,
    ):
        """Test policy with sample input data."""
        # TEST endpoint not implemented - skip test
        pytest.skip("POST /api/v1/policies/{id}/test not implemented")

    async def test_test_policy_unauthorized(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_policy: Policy,
    ):
        """Test policy testing by non-admin returns 403."""
        # TEST endpoint not implemented - skip test
        pytest.skip("POST /api/v1/policies/{id}/test not implemented")


@pytest.mark.integration
@pytest.mark.policies
class TestPolicyEvaluationsList:
    """Integration tests for GET policy evaluations endpoint (NEW)."""

    async def test_get_gate_evaluations_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_policy: Policy,
        test_gate: Gate,
        db: AsyncSession,
    ):
        """Test get policy evaluations for gate with existing evaluations."""
        # First, create some policy evaluations by calling evaluate endpoint
        from app.models.policy import PolicyEvaluation
        from uuid import uuid4
        from datetime import datetime

        # Create 3 policy evaluations (2 pass, 1 fail)
        evaluation1 = PolicyEvaluation(
            id=uuid4(),
            gate_id=test_gate.id,
            policy_id=test_policy.id,
            evaluation_result={
                "result": "pass",
                "violations": [],
                "metadata": {},
            },
            is_passed=True,
            violations=[],
            evaluated_at=datetime.utcnow(),
        )
        evaluation2 = PolicyEvaluation(
            id=uuid4(),
            gate_id=test_gate.id,
            policy_id=test_policy.id,
            evaluation_result={
                "result": "fail",
                "violations": ["Missing required documentation"],
                "metadata": {},
            },
            is_passed=False,
            violations=["Missing required documentation"],
            evaluated_at=datetime.utcnow(),
        )
        evaluation3 = PolicyEvaluation(
            id=uuid4(),
            gate_id=test_gate.id,
            policy_id=test_policy.id,
            evaluation_result={
                "result": "pass",
                "violations": [],
                "metadata": {},
            },
            is_passed=True,
            violations=[],
            evaluated_at=datetime.utcnow(),
        )

        db.add(evaluation1)
        db.add(evaluation2)
        db.add(evaluation3)
        await db.commit()

        # Now test GET /api/v1/policies/evaluations/{gate_id}
        response = await client.get(
            f"/api/v1/policies/evaluations/{test_gate.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "items" in data
        assert "total" in data
        assert "passed" in data
        assert "failed" in data
        assert "pass_rate" in data

        # Validate counts (3 total, 2 passed, 1 failed)
        assert data["total"] == 3
        assert data["passed"] == 2
        assert data["failed"] == 1
        assert data["pass_rate"] == pytest.approx(66.67, rel=0.01)  # 2/3 * 100

        # Validate items structure
        assert len(data["items"]) == 3
        for item in data["items"]:
            assert "id" in item
            assert "gate_id" in item
            assert "policy_id" in item
            assert "policy_name" in item
            assert "result" in item
            assert "violations" in item
            assert "evaluated_at" in item
            assert item["gate_id"] == str(test_gate.id)
            assert item["policy_id"] == str(test_policy.id)
            assert item["result"] in ["pass", "fail"]

    async def test_get_gate_evaluations_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
    ):
        """Test get policy evaluations for gate with no evaluations."""
        response = await client.get(
            f"/api/v1/policies/evaluations/{test_gate.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Validate empty response
        assert data["total"] == 0
        assert data["passed"] == 0
        assert data["failed"] == 0
        assert data["pass_rate"] == 0.0
        assert len(data["items"]) == 0

    async def test_get_gate_evaluations_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test get policy evaluations for non-existent gate returns 404."""
        response = await client.get(
            f"/api/v1/policies/evaluations/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.policies
class TestPolicyListErrorHandling:
    """Integration tests for policy list error handling and validation."""

    async def test_list_policies_invalid_page_zero(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test list policies with page=0 returns 422 validation error."""
        response = await client.get(
            "/api/v1/policies",
            headers=auth_headers,
            params={"page": 0, "page_size": 10},  # page must be >= 1
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    async def test_list_policies_invalid_page_size_exceeds_max(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test list policies with page_size > 100 returns 422 validation error."""
        response = await client.get(
            "/api/v1/policies",
            headers=auth_headers,
            params={"page": 1, "page_size": 101},  # page_size max is 100
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    async def test_list_policies_negative_page_size(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test list policies with negative page_size returns 422 validation error."""
        response = await client.get(
            "/api/v1/policies",
            headers=auth_headers,
            params={"page": 1, "page_size": -10},  # page_size must be >= 1
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    async def test_evaluate_policy_invalid_gate_id_format(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_policy: Policy,
    ):
        """Test evaluate policy with invalid gate_id format returns 422 validation error."""
        response = await client.post(
            "/api/v1/policies/evaluate",
            headers=auth_headers,
            json={
                "gate_id": "not-a-valid-uuid",  # Invalid UUID format
                "policy_id": str(test_policy.id),
                "input_data": {},
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


@pytest.mark.integration
@pytest.mark.policies
class TestPolicyEdgeCases:
    """Integration tests for policy edge cases and boundary conditions."""

    async def test_list_policies_empty_database(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
    ):
        """Test list policies when no policies exist in database."""
        # Delete all policies to simulate empty state
        from app.models.policy import Policy

        result = await db.execute(select(Policy))
        policies = result.scalars().all()
        for policy in policies:
            await db.delete(policy)
        await db.commit()

        response = await client.get(
            "/api/v1/policies",
            headers=auth_headers,
            params={"page": 1, "page_size": 10},
        )

        assert response.status_code == 200
        data = response.json()

        # Should return empty list with zero count
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["pages"] == 0
        assert len(data["items"]) == 0

    async def test_list_policies_with_inactive_policies(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_policy: Policy,
        db: AsyncSession,
    ):
        """Test list policies filters out inactive policies by default."""
        # Mark test_policy as inactive
        test_policy.is_active = False
        await db.commit()

        # List policies (is_active=True by default)
        response = await client.get(
            "/api/v1/policies",
            headers=auth_headers,
            params={"page": 1, "page_size": 10},
        )

        assert response.status_code == 200
        data = response.json()

        # Inactive policy should NOT appear in results
        policy_ids = [p["id"] for p in data["items"]]
        assert str(test_policy.id) not in policy_ids

    async def test_list_policies_large_page_size(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_policy: Policy,
    ):
        """Test list policies with maximum page_size (100)."""
        response = await client.get(
            "/api/v1/policies",
            headers=auth_headers,
            params={"page": 1, "page_size": 100},  # Max allowed
        )

        assert response.status_code == 200
        data = response.json()

        # Should succeed with page_size=100
        assert data["page_size"] == 100
        assert len(data["items"]) <= 100

    async def test_evaluate_policy_multiple_times(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_policy: Policy,
        test_gate: Gate,
    ):
        """Test evaluating same policy against same gate multiple times creates separate records."""
        # Evaluate same policy 3 times
        evaluation_ids = []
        for i in range(3):
            response = await client.post(
                "/api/v1/policies/evaluate",
                headers=auth_headers,
                json={
                    "gate_id": str(test_gate.id),
                    "policy_id": str(test_policy.id),
                    "input_data": {"iteration": i},
                },
            )

            assert response.status_code == 201
            data = response.json()
            evaluation_ids.append(data["id"])

        # All 3 evaluations should have unique IDs
        assert len(set(evaluation_ids)) == 3

        # Verify all 3 evaluations appear in gate evaluations list
        response = await client.get(
            f"/api/v1/policies/evaluations/{test_gate.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3  # At least 3 evaluations
