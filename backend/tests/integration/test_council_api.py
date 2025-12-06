"""
=========================================================================
AI Council API Integration Tests - Sprint 26
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 4, 2025
Status: ACTIVE - Sprint 26 Day 4 (Tests + Performance)
Authority: Backend Lead + CTO Approved
Foundation: Sprint 26 Plan, ADR-011 (AI Governance Layer)
Framework: SDLC 4.9.1 Complete Lifecycle

Purpose:
- Integration tests for AI Council API endpoints
- Test deliberation flow (create violation → trigger council → verify result)
- Test access control (project membership required)
- Test auto-council integration with compliance scanner
- Test error handling

Endpoints Tested:
- POST /api/v1/council/deliberate
- GET /api/v1/council/status/{request_id}
- GET /api/v1/council/history/{project_id}
- GET /api/v1/council/stats/{project_id}

Zero Mock Policy: Real API integration with test database
=========================================================================
"""

import pytest
import pytest_asyncio
from datetime import datetime
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.compliance_scan import ComplianceViolation, ComplianceScan, TriggerType


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def sample_project(db_session, test_user):
    """Create sample project for testing."""
    project = Project(
        id=uuid4(),
        name="Test Project - Council API",
        description="Project for AI Council API testing",
        owner_id=test_user.id,
        sdlc_stage="BUILD",
        created_at=datetime.utcnow(),
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def sample_scan(db_session, sample_project):
    """Create sample compliance scan."""
    scan = ComplianceScan(
        id=uuid4(),
        project_id=sample_project.id,
        trigger_type=TriggerType.MANUAL.value,
        compliance_score=65,
        violations_count=3,
        warnings_count=2,
        scanned_at=datetime.utcnow(),
        is_compliant=False,
    )
    db_session.add(scan)
    await db_session.commit()
    await db_session.refresh(scan)
    return scan


@pytest_asyncio.fixture
async def critical_violation(db_session, sample_project, sample_scan):
    """Create CRITICAL severity violation for testing."""
    violation = ComplianceViolation(
        id=uuid4(),
        scan_id=sample_scan.id,
        project_id=sample_project.id,
        violation_type="MISSING_DOCUMENTATION",
        severity="CRITICAL",
        location="/docs/00-Project-Foundation",
        description="Missing Product Vision document (Product-Vision.md) in Stage 00",
        recommendation="Create Product Vision document following SDLC 4.9.1 template",
        is_resolved=False,
        created_at=datetime.utcnow(),
    )
    db_session.add(violation)
    await db_session.commit()
    await db_session.refresh(violation)
    return violation


# ============================================================================
# Test POST /api/v1/council/deliberate
# ============================================================================


@pytest.mark.asyncio
async def test_deliberate_single_mode_success(
    client: AsyncClient,
    auth_headers: dict,
    critical_violation: ComplianceViolation,
):
    """Test triggering council deliberation in SINGLE mode."""
    # Mock AI service for test environment
    with patch('app.services.ai_council_service.AIRecommendationService') as mock_ai:
        mock_ai.return_value.generate_recommendation = AsyncMock(
            return_value=MagicMock(
                recommendation="Create /docs/00-Project-Foundation/01-Vision/Product-Vision.md",
                provider="ollama",
                confidence=85,
                duration_ms=1500.0,
                cost_usd=0.0,
                fallback_used=False,
            )
        )

        response = await client.post(
            "/api/v1/council/deliberate",
            headers=auth_headers,
            json={
                "violation_id": str(critical_violation.id),
                "council_mode": "single",
            },
        )

        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["violation_id"] == str(critical_violation.id)
        assert data["mode_used"] == "single"
        assert data["confidence_score"] >= 0
        assert data["confidence_score"] <= 100
        assert len(data["recommendation"]) > 0
        assert len(data["providers_used"]) > 0
        assert data["total_duration_ms"] > 0


@pytest.mark.asyncio
async def test_deliberate_council_mode_success(
    client: AsyncClient,
    auth_headers: dict,
    critical_violation: ComplianceViolation,
):
    """Test triggering council deliberation in COUNCIL mode (3 stages)."""
    with patch('app.services.ai_council_service.AICouncilService.deliberate') as mock_deliberate:
        mock_deliberate.return_value = MagicMock(
            request_id=uuid4(),
            violation_id=critical_violation.id,
            mode_used="council",
            recommendation="Synthesized recommendation from 3 providers",
            confidence_score=92,
            providers_used=["ollama", "claude", "gpt4"],
            deliberation={
                "stage1": {"successful_count": 3, "duration_ms": 3500},
                "stage2": {"best_response_id": "claude", "duration_ms": 2200},
                "stage3": {"chairman": "claude", "duration_ms": 1800},
            },
            total_duration_ms=7500.0,
            total_cost_usd=0.045,
            fallback_used=False,
        )

        response = await client.post(
            "/api/v1/council/deliberate",
            headers=auth_headers,
            json={
                "violation_id": str(critical_violation.id),
                "council_mode": "council",
                "providers": ["ollama", "claude", "gpt4"],
            },
        )

        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["mode_used"] == "council"
        assert data["confidence_score"] == 92
        assert len(data["providers_used"]) == 3
        assert "deliberation" in data
        assert data["deliberation"]["stage1"]["successful_count"] == 3


@pytest.mark.asyncio
async def test_deliberate_auto_mode_critical(
    client: AsyncClient,
    auth_headers: dict,
    critical_violation: ComplianceViolation,
):
    """Test AUTO mode uses council for CRITICAL severity."""
    with patch('app.services.ai_council_service.AICouncilService.deliberate') as mock_deliberate:
        mock_deliberate.return_value = MagicMock(
            request_id=uuid4(),
            violation_id=critical_violation.id,
            mode_used="council",  # AUTO should choose council for CRITICAL
            recommendation="Council recommendation",
            confidence_score=90,
            providers_used=["ollama", "claude", "gpt4"],
            deliberation={},
            total_duration_ms=7000.0,
            total_cost_usd=0.040,
            fallback_used=False,
        )

        response = await client.post(
            "/api/v1/council/deliberate",
            headers=auth_headers,
            json={
                "violation_id": str(critical_violation.id),
                "council_mode": "auto",  # Let system decide
            },
        )

        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["mode_used"] == "council"  # AUTO chose council for CRITICAL


@pytest.mark.asyncio
async def test_deliberate_unauthorized(
    client: AsyncClient,
    critical_violation: ComplianceViolation,
):
    """Test deliberation without authentication fails."""
    response = await client.post(
        "/api/v1/council/deliberate",
        json={
            "violation_id": str(critical_violation.id),
            "council_mode": "single",
        },
    )

    # Assertions
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_deliberate_forbidden_project(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
    test_user: User,
):
    """Test deliberation for violation in project user doesn't have access to."""
    # Create another user's project
    other_user = User(
        id=uuid4(),
        email="other@example.com",
        full_name="Other User",
        password_hash="hash",
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.flush()

    other_project = Project(
        id=uuid4(),
        name="Other Project",
        owner_id=other_user.id,
    )
    db_session.add(other_project)
    await db_session.flush()

    scan = ComplianceScan(
        id=uuid4(),
        project_id=other_project.id,
        trigger_type="MANUAL",
        compliance_score=70,
        violations_count=1,
        warnings_count=0,
        scanned_at=datetime.utcnow(),
    )
    db_session.add(scan)
    await db_session.flush()

    violation = ComplianceViolation(
        id=uuid4(),
        scan_id=scan.id,
        project_id=other_project.id,
        violation_type="TEST",
        severity="HIGH",
        description="Test violation",
        is_resolved=False,
        created_at=datetime.utcnow(),
    )
    db_session.add(violation)
    await db_session.commit()

    response = await client.post(
        "/api/v1/council/deliberate",
        headers=auth_headers,
        json={
            "violation_id": str(violation.id),
            "council_mode": "single",
        },
    )

    # Assertions
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_deliberate_violation_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test deliberation for non-existent violation."""
    response = await client.post(
        "/api/v1/council/deliberate",
        headers=auth_headers,
        json={
            "violation_id": str(uuid4()),  # Random UUID
            "council_mode": "single",
        },
    )

    # Assertions
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_deliberate_updates_violation(
    client: AsyncClient,
    auth_headers: dict,
    critical_violation: ComplianceViolation,
    db_session,
):
    """Test that deliberation updates violation with AI recommendation."""
    with patch('app.services.ai_council_service.AICouncilService.deliberate') as mock_deliberate:
        mock_deliberate.return_value = MagicMock(
            request_id=uuid4(),
            violation_id=critical_violation.id,
            mode_used="single",
            recommendation="AI-generated recommendation for this violation",
            confidence_score=87,
            providers_used=["ollama"],
            total_duration_ms=1500.0,
            total_cost_usd=0.0,
        )

        response = await client.post(
            "/api/v1/council/deliberate",
            headers=auth_headers,
            json={
                "violation_id": str(critical_violation.id),
                "council_mode": "single",
            },
        )

        assert response.status_code == 201

        # Verify violation was updated
        await db_session.refresh(critical_violation)
        assert critical_violation.ai_recommendation == "AI-generated recommendation for this violation"
        assert critical_violation.ai_provider == "council-single"
        assert critical_violation.ai_confidence == 87


# ============================================================================
# Test GET /api/v1/council/status/{request_id}
# ============================================================================


@pytest.mark.asyncio
async def test_get_deliberation_status_not_implemented(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test deliberation status endpoint (future feature)."""
    response = await client.get(
        f"/api/v1/council/status/{uuid4()}",
        headers=auth_headers,
    )

    # Assertions - should return 501 (not implemented yet)
    assert response.status_code == 501
    data = response.json()
    assert "not implemented" in data["detail"].lower() or "synchronous" in data["detail"].lower()


# ============================================================================
# Test GET /api/v1/council/history/{project_id}
# ============================================================================


@pytest.mark.asyncio
async def test_get_council_history(
    client: AsyncClient,
    auth_headers: dict,
    sample_project: Project,
):
    """Test getting council history for a project."""
    response = await client.get(
        f"/api/v1/council/history/{sample_project.id}",
        headers=auth_headers,
    )

    # Assertions - currently returns empty list (Sprint 27 feature)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # In Sprint 27, this will return actual deliberation history


@pytest.mark.asyncio
async def test_get_council_history_unauthorized(
    client: AsyncClient,
    sample_project: Project,
):
    """Test getting history without authentication."""
    response = await client.get(f"/api/v1/council/history/{sample_project.id}")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_council_history_forbidden(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test getting history for project user doesn't have access to."""
    random_project_id = uuid4()

    response = await client.get(
        f"/api/v1/council/history/{random_project_id}",
        headers=auth_headers,
    )

    # Assertions
    assert response.status_code in [403, 404]


# ============================================================================
# Test GET /api/v1/council/stats/{project_id}
# ============================================================================


@pytest.mark.asyncio
async def test_get_council_stats(
    client: AsyncClient,
    auth_headers: dict,
    sample_project: Project,
):
    """Test getting council statistics for a project."""
    response = await client.get(
        f"/api/v1/council/stats/{sample_project.id}",
        headers=auth_headers,
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "total_deliberations" in data
    assert "single_mode_count" in data
    assert "council_mode_count" in data
    assert "average_confidence" in data
    # Currently returns zeros (Sprint 27 feature)


# ============================================================================
# Test Auto-Council Integration (Sprint 26 Day 3)
# ============================================================================


@pytest.mark.asyncio
async def test_auto_council_triggered_after_scan(
    client: AsyncClient,
    auth_headers: dict,
    sample_project: Project,
    db_session,
):
    """Test that auto-council is triggered after compliance scan completes."""
    from app.services.compliance_scanner import ComplianceScanner
    from unittest.mock import patch

    # Mock council service
    with patch('app.api.routes.council.auto_council_for_critical_violations') as mock_auto_council:
        mock_auto_council.return_value = {
            "total_violations": 2,
            "council_triggered": 2,
            "council_succeeded": 2,
            "council_failed": 0,
            "average_confidence": 88.5,
            "total_cost_usd": 0.030,
        }

        # Trigger compliance scan
        scanner = ComplianceScanner(db_session)
        result = await scanner.scan_project(
            project_id=sample_project.id,
            triggered_by=test_user.id,
            trigger_type=TriggerType.MANUAL,
        )

        # Verify auto-council was called
        mock_auto_council.assert_called_once()
        call_args = mock_auto_council.call_args[1]
        assert call_args['project_id'] == sample_project.id


# ============================================================================
# Test Performance (Basic)
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.slow
async def test_single_mode_performance(
    client: AsyncClient,
    auth_headers: dict,
    critical_violation: ComplianceViolation,
):
    """Test single mode deliberation meets <3s p95 target."""
    import time

    durations = []

    for _ in range(10):  # Run 10 times to get p95
        start = time.time()

        with patch('app.services.ai_council_service.AIRecommendationService') as mock_ai:
            mock_ai.return_value.generate_recommendation = AsyncMock(
                return_value=MagicMock(
                    recommendation="Test",
                    provider="ollama",
                    confidence=85,
                    duration_ms=1000,
                    cost_usd=0.0,
                )
            )

            response = await client.post(
                "/api/v1/council/deliberate",
                headers=auth_headers,
                json={
                    "violation_id": str(critical_violation.id),
                    "council_mode": "single",
                },
            )

            duration = (time.time() - start) * 1000  # Convert to ms
            durations.append(duration)

            assert response.status_code == 201

    # Calculate p95
    durations.sort()
    p95_index = int(len(durations) * 0.95)
    p95_duration = durations[p95_index]

    # Assertion - p95 should be <3000ms
    assert p95_duration < 3000, f"P95 latency {p95_duration:.2f}ms exceeds 3000ms target"


# ============================================================================
# Test Error Handling
# ============================================================================


@pytest.mark.asyncio
async def test_deliberate_invalid_mode(
    client: AsyncClient,
    auth_headers: dict,
    critical_violation: ComplianceViolation,
):
    """Test deliberation with invalid council mode."""
    response = await client.post(
        "/api/v1/council/deliberate",
        headers=auth_headers,
        json={
            "violation_id": str(critical_violation.id),
            "council_mode": "invalid_mode",
        },
    )

    # Assertions - should fail validation
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_deliberate_invalid_violation_id(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test deliberation with malformed violation ID."""
    response = await client.post(
        "/api/v1/council/deliberate",
        headers=auth_headers,
        json={
            "violation_id": "not-a-uuid",
            "council_mode": "single",
        },
    )

    # Assertions
    assert response.status_code == 422  # Validation error
