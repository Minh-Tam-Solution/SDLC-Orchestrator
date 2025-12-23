"""
Unit Tests for Override Service

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
Test Override Service business logic including:
- Override request creation
- Approval/rejection flow
- Queue management
- Expiry handling
- Audit logging

Test Coverage Target: 95%+
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.analytics import AICodeEvent
from app.models.override import (
    OverrideAuditAction,
    OverrideAuditLog,
    OverrideStatus,
    OverrideType,
    ValidationOverride,
)
from app.models.user import User
from app.services.override_service import (
    APPROVER_ROLES,
    MIN_REASON_LENGTH,
    OVERRIDE_EXPIRY_DAYS,
    OverrideNotFoundError,
    OverridePermissionError,
    OverrideService,
    OverrideValidationError,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_db():
    """Create mock async database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """Create mock developer user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "developer@example.com"
    user.name = "Test Developer"
    user.is_superuser = False
    user.role_names = ["dev"]
    return user


@pytest.fixture
def mock_admin_user():
    """Create mock admin user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "admin@example.com"
    user.name = "Admin User"
    user.is_superuser = True
    user.role_names = ["admin"]
    return user


@pytest.fixture
def mock_manager_user():
    """Create mock manager user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "manager@example.com"
    user.name = "Manager User"
    user.is_superuser = False
    user.role_names = ["manager"]
    return user


@pytest.fixture
def mock_ai_code_event():
    """Create mock failed AI code event."""
    event = MagicMock(spec=AICodeEvent)
    event.id = uuid4()
    event.project_id = uuid4()
    event.pr_id = "123"
    event.validation_result = "failed"
    event.violations = [
        {"validator": "sast", "message": "SQL injection detected"},
        {"validator": "policy_guards", "message": "Unsafe AI pattern"},
    ]
    return event


@pytest.fixture
def mock_pending_override(mock_ai_code_event, mock_user):
    """Create mock pending override."""
    override = MagicMock(spec=ValidationOverride)
    override.id = uuid4()
    override.event_id = mock_ai_code_event.id
    override.project_id = mock_ai_code_event.project_id
    override.override_type = OverrideType.FALSE_POSITIVE
    override.reason = "This is a test file that is excluded from production." * 3
    override.status = OverrideStatus.PENDING
    override.requested_by_id = mock_user.id
    override.requested_by = mock_user
    override.requested_at = datetime.utcnow()
    override.expires_at = datetime.utcnow() + timedelta(days=7)
    override.is_expired = False
    override.resolved_by_id = None
    override.resolved_by = None
    override.resolved_at = None
    override.resolution_comment = None
    override.pr_number = "123"
    override.pr_title = "PR #123"
    override.failed_validators = '["sast", "policy_guards"]'
    override.post_merge_review_required = False
    override.created_at = datetime.utcnow()
    override.event = mock_ai_code_event
    return override


# =============================================================================
# Override Request Creation Tests
# =============================================================================


class TestCreateOverrideRequest:
    """Tests for override request creation."""

    @pytest.mark.asyncio
    async def test_create_request_success(self, mock_db, mock_user, mock_ai_code_event):
        """Test successful override request creation."""
        # Setup
        mock_db.execute.side_effect = [
            # First call: fetch event
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_ai_code_event)),
            # Second call: check existing pending
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        ]

        service = OverrideService(mock_db)
        reason = "This is a false positive. " * 5  # > 50 chars

        # Execute
        result = await service.create_override_request(
            event_id=mock_ai_code_event.id,
            override_type=OverrideType.FALSE_POSITIVE,
            reason=reason,
            requested_by=mock_user,
        )

        # Verify
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_request_reason_too_short(self, mock_db, mock_user, mock_ai_code_event):
        """Test validation error for short reason."""
        service = OverrideService(mock_db)

        with pytest.raises(OverrideValidationError) as exc_info:
            await service.create_override_request(
                event_id=mock_ai_code_event.id,
                override_type=OverrideType.FALSE_POSITIVE,
                reason="Too short",
                requested_by=mock_user,
            )

        assert "at least" in str(exc_info.value)
        assert str(MIN_REASON_LENGTH) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_request_event_not_found(self, mock_db, mock_user):
        """Test error when event not found."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        service = OverrideService(mock_db)

        with pytest.raises(OverrideNotFoundError):
            await service.create_override_request(
                event_id=uuid4(),
                override_type=OverrideType.FALSE_POSITIVE,
                reason="This is a valid reason that is long enough." * 2,
                requested_by=mock_user,
            )

    @pytest.mark.asyncio
    async def test_create_request_event_not_failed(self, mock_db, mock_user, mock_ai_code_event):
        """Test error when event is not failed."""
        mock_ai_code_event.validation_result = "passed"
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_ai_code_event)
        )

        service = OverrideService(mock_db)

        with pytest.raises(OverrideValidationError) as exc_info:
            await service.create_override_request(
                event_id=mock_ai_code_event.id,
                override_type=OverrideType.FALSE_POSITIVE,
                reason="This is a valid reason that is long enough." * 2,
                requested_by=mock_user,
            )

        assert "failed or warning" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_request_duplicate_pending(
        self, mock_db, mock_user, mock_ai_code_event, mock_pending_override
    ):
        """Test error when pending override already exists."""
        mock_db.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_ai_code_event)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_pending_override)),
        ]

        service = OverrideService(mock_db)

        with pytest.raises(OverrideValidationError) as exc_info:
            await service.create_override_request(
                event_id=mock_ai_code_event.id,
                override_type=OverrideType.FALSE_POSITIVE,
                reason="This is a valid reason that is long enough." * 2,
                requested_by=mock_user,
            )

        assert "already pending" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_emergency_override_requires_review(
        self, mock_db, mock_user, mock_ai_code_event
    ):
        """Test emergency override sets post_merge_review_required."""
        mock_db.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_ai_code_event)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        ]

        service = OverrideService(mock_db)

        await service.create_override_request(
            event_id=mock_ai_code_event.id,
            override_type=OverrideType.EMERGENCY,
            reason="Critical hotfix required for production outage." * 2,
            requested_by=mock_user,
        )

        # Verify override was added with post_merge_review_required
        add_call = mock_db.add.call_args_list[0]
        override = add_call[0][0]
        assert override.post_merge_review_required is True


# =============================================================================
# Approval/Rejection Tests
# =============================================================================


class TestApproveOverride:
    """Tests for override approval."""

    @pytest.mark.asyncio
    async def test_approve_success(self, mock_db, mock_admin_user, mock_pending_override):
        """Test successful override approval."""
        mock_db.execute.side_effect = [
            # Get override
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_pending_override)),
            # Update AICodeEvent
            MagicMock(),
        ]

        service = OverrideService(mock_db)

        result = await service.approve_override(
            override_id=mock_pending_override.id,
            approver=mock_admin_user,
            comment="Approved after code review.",
        )

        assert mock_pending_override.status == OverrideStatus.APPROVED
        assert mock_pending_override.resolved_by_id == mock_admin_user.id
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_approve_permission_denied(self, mock_db, mock_user, mock_pending_override):
        """Test approval denied for non-admin user."""
        service = OverrideService(mock_db)

        with pytest.raises(OverridePermissionError):
            await service.approve_override(
                override_id=mock_pending_override.id,
                approver=mock_user,
            )

    @pytest.mark.asyncio
    async def test_approve_override_not_found(self, mock_db, mock_admin_user):
        """Test approval when override not found."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        service = OverrideService(mock_db)

        with pytest.raises(OverrideNotFoundError):
            await service.approve_override(
                override_id=uuid4(),
                approver=mock_admin_user,
            )

    @pytest.mark.asyncio
    async def test_approve_already_resolved(self, mock_db, mock_admin_user, mock_pending_override):
        """Test approval when already resolved."""
        mock_pending_override.status = OverrideStatus.APPROVED
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_pending_override)
        )

        service = OverrideService(mock_db)

        with pytest.raises(OverrideValidationError) as exc_info:
            await service.approve_override(
                override_id=mock_pending_override.id,
                approver=mock_admin_user,
            )

        assert "Cannot approve" in str(exc_info.value)


class TestRejectOverride:
    """Tests for override rejection."""

    @pytest.mark.asyncio
    async def test_reject_success(self, mock_db, mock_admin_user, mock_pending_override):
        """Test successful override rejection."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_pending_override)
        )

        service = OverrideService(mock_db)

        result = await service.reject_override(
            override_id=mock_pending_override.id,
            rejector=mock_admin_user,
            reason="Security vulnerability must be fixed.",
        )

        assert mock_pending_override.status == OverrideStatus.REJECTED
        assert mock_pending_override.resolved_by_id == mock_admin_user.id
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_reject_reason_too_short(self, mock_db, mock_admin_user, mock_pending_override):
        """Test rejection requires valid reason."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_pending_override)
        )

        service = OverrideService(mock_db)

        with pytest.raises(OverrideValidationError) as exc_info:
            await service.reject_override(
                override_id=mock_pending_override.id,
                rejector=mock_admin_user,
                reason="No",
            )

        assert "at least 10" in str(exc_info.value)


class TestCancelOverride:
    """Tests for override cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_by_requester(self, mock_db, mock_user, mock_pending_override):
        """Test cancellation by requester."""
        mock_pending_override.requested_by_id = mock_user.id
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_pending_override)
        )

        service = OverrideService(mock_db)

        result = await service.cancel_override(
            override_id=mock_pending_override.id,
            user=mock_user,
        )

        assert mock_pending_override.status == OverrideStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_by_admin(self, mock_db, mock_admin_user, mock_pending_override):
        """Test admin can cancel any override."""
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_pending_override)
        )

        service = OverrideService(mock_db)

        result = await service.cancel_override(
            override_id=mock_pending_override.id,
            user=mock_admin_user,
        )

        assert mock_pending_override.status == OverrideStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_permission_denied(self, mock_db, mock_pending_override):
        """Test non-requester non-admin cannot cancel."""
        other_user = MagicMock(spec=User)
        other_user.id = uuid4()
        other_user.is_superuser = False
        other_user.role_names = ["dev"]

        mock_pending_override.requested_by_id = uuid4()  # Different user
        mock_db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_pending_override)
        )

        service = OverrideService(mock_db)

        with pytest.raises(OverridePermissionError):
            await service.cancel_override(
                override_id=mock_pending_override.id,
                user=other_user,
            )


# =============================================================================
# Queue Management Tests
# =============================================================================


class TestPendingQueue:
    """Tests for pending queue retrieval."""

    @pytest.mark.asyncio
    async def test_get_pending_queue(self, mock_db, mock_pending_override):
        """Test getting pending override queue."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_pending_override]

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        service = OverrideService(mock_db)

        overrides, total = await service.get_pending_queue(limit=50)

        assert len(overrides) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_get_pending_queue_with_project_filter(self, mock_db):
        """Test queue filtering by project."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_db.execute.side_effect = [mock_result, mock_count_result]

        service = OverrideService(mock_db)
        project_id = uuid4()

        overrides, total = await service.get_pending_queue(project_id=project_id)

        assert len(overrides) == 0
        assert total == 0


# =============================================================================
# Expiry Management Tests
# =============================================================================


class TestExpiryManagement:
    """Tests for override expiry handling."""

    @pytest.mark.asyncio
    async def test_expire_old_requests(self, mock_db, mock_pending_override):
        """Test expiring old override requests."""
        # Set override as expired
        mock_pending_override.expires_at = datetime.utcnow() - timedelta(days=1)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_pending_override]
        mock_db.execute.return_value = mock_result

        service = OverrideService(mock_db)

        expired_count = await service.expire_old_requests()

        assert expired_count == 1
        assert mock_pending_override.status == OverrideStatus.EXPIRED
        assert mock_pending_override.is_expired is True

    @pytest.mark.asyncio
    async def test_expire_no_expired_requests(self, mock_db):
        """Test no expiry when no expired requests."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = OverrideService(mock_db)

        expired_count = await service.expire_old_requests()

        assert expired_count == 0


# =============================================================================
# Statistics Tests
# =============================================================================


class TestOverrideStats:
    """Tests for override statistics."""

    @pytest.mark.asyncio
    async def test_get_override_stats(self, mock_db):
        """Test getting override statistics."""
        # Mock total count
        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 100

        # Mock status breakdown
        mock_status_result = MagicMock()
        mock_status_result.all.return_value = [
            MagicMock(status=OverrideStatus.APPROVED, count=70),
            MagicMock(status=OverrideStatus.REJECTED, count=20),
            MagicMock(status=OverrideStatus.PENDING, count=10),
        ]

        # Mock type breakdown
        mock_type_result = MagicMock()
        mock_type_result.all.return_value = [
            MagicMock(override_type=OverrideType.FALSE_POSITIVE, count=50),
            MagicMock(override_type=OverrideType.APPROVED_RISK, count=40),
            MagicMock(override_type=OverrideType.EMERGENCY, count=10),
        ]

        mock_db.execute.side_effect = [
            mock_total_result,
            mock_status_result,
            mock_type_result,
        ]

        service = OverrideService(mock_db)

        stats = await service.get_override_stats(days=30)

        assert stats["total"] == 100
        assert stats["approval_rate"] == pytest.approx(77.78, rel=0.1)
        assert stats["pending"] == 10


# =============================================================================
# Role Checking Tests
# =============================================================================


class TestRoleChecking:
    """Tests for approver role checking."""

    def test_has_approver_role_admin(self, mock_admin_user):
        """Test admin has approver role."""
        from app.services.override_service import OverrideService

        service = OverrideService(MagicMock())
        assert service._has_approver_role(mock_admin_user) is True

    def test_has_approver_role_manager(self, mock_manager_user):
        """Test manager has approver role."""
        service = OverrideService(MagicMock())
        assert service._has_approver_role(mock_manager_user) is True

    def test_has_approver_role_developer(self, mock_user):
        """Test developer does not have approver role."""
        service = OverrideService(MagicMock())
        assert service._has_approver_role(mock_user) is False

    def test_has_approver_role_superuser(self):
        """Test superuser always has approver role."""
        user = MagicMock(spec=User)
        user.is_superuser = True
        user.role_names = []

        service = OverrideService(MagicMock())
        assert service._has_approver_role(user) is True


# =============================================================================
# Constants Tests
# =============================================================================


class TestConstants:
    """Tests for service constants."""

    def test_override_expiry_days(self):
        """Test expiry days constant."""
        assert OVERRIDE_EXPIRY_DAYS == 7

    def test_min_reason_length(self):
        """Test minimum reason length."""
        assert MIN_REASON_LENGTH == 50

    def test_approver_roles(self):
        """Test approver roles set."""
        assert "admin" in APPROVER_ROLES
        assert "manager" in APPROVER_ROLES
        assert "security" in APPROVER_ROLES
        assert "cto" in APPROVER_ROLES
        assert "ceo" in APPROVER_ROLES
        assert "dev" not in APPROVER_ROLES
