"""
Unit Tests for Team Invitation Service

Tests for business logic, security features, and error handling.

Coverage:
- Token security functions (generate, hash, verify)
- Rate limiting (Redis-based)
- Core service functions (send, get, accept, decline, resend)
- Error cases and edge cases

Reference: ADR-043-Team-Invitation-System-Architecture.md
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.team_invitation import InvitationStatus, TeamInvitation
from app.schemas.invitation import InvitationCreate
from app.services import invitation_service


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session"""
    mock = MagicMock(spec=Session)

    # Configure add() to set id if not set
    def add_side_effect(obj):
        if hasattr(obj, 'id') and obj.id is None:
            obj.id = uuid4()

    # Configure refresh() to set created_at and updated_at
    def refresh_side_effect(obj):
        if hasattr(obj, 'created_at') and obj.created_at is None:
            obj.created_at = datetime.utcnow()
        if hasattr(obj, 'updated_at') and obj.updated_at is None:
            obj.updated_at = datetime.utcnow()

    mock.add.side_effect = add_side_effect
    mock.refresh.side_effect = refresh_side_effect
    return mock


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch("app.services.invitation_service.redis_client") as mock:
        yield mock


@pytest.fixture
def sample_team(mock_db):
    """Sample team for testing"""
    team = MagicMock()
    team.id = uuid4()
    team.name = "Test Team"
    team.organization = MagicMock()
    team.organization.name = "Test Organization"
    mock_db.query.return_value.filter.return_value.first.return_value = team
    return team


@pytest.fixture
def sample_user(mock_db):
    """Sample user for testing"""
    user = MagicMock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.display_name = "Test User"
    user.username = "testuser"
    return user


@pytest.fixture
def sample_invitation_data():
    """Sample invitation creation data"""
    return InvitationCreate(
        email="invitee@example.com",
        role="member",
        message="Welcome to the team!",
    )


# ============================================================================
# Token Security Tests
# ============================================================================

class TestTokenSecurity:
    """Test token generation, hashing, and verification"""

    def test_generate_invitation_token_length(self):
        """Generated token should be 43 characters (256-bit entropy)"""
        token = invitation_service.generate_invitation_token()
        assert len(token) == 43

    def test_generate_invitation_token_uniqueness(self):
        """Generated tokens should be unique (cryptographically random)"""
        tokens = [invitation_service.generate_invitation_token() for _ in range(100)]
        assert len(set(tokens)) == 100

    def test_hash_token_sha256(self):
        """Token hash should be SHA256 (64 hex characters)"""
        token = "abc123"
        token_hash = invitation_service.hash_token(token)

        assert len(token_hash) == 64
        assert all(c in "0123456789abcdef" for c in token_hash)

        # Verify it matches Python's hashlib.sha256
        expected_hash = hashlib.sha256(token.encode()).hexdigest()
        assert token_hash == expected_hash

    def test_hash_token_deterministic(self):
        """Same token should always produce same hash"""
        token = "test_token_123"
        hash1 = invitation_service.hash_token(token)
        hash2 = invitation_service.hash_token(token)

        assert hash1 == hash2

    def test_verify_token_valid(self):
        """Valid token should verify successfully"""
        token = "abc123"
        token_hash = invitation_service.hash_token(token)

        assert invitation_service.verify_token(token, token_hash) is True

    def test_verify_token_invalid(self):
        """Invalid token should fail verification"""
        token = "abc123"
        wrong_token = "xyz789"
        token_hash = invitation_service.hash_token(token)

        assert invitation_service.verify_token(wrong_token, token_hash) is False

    def test_verify_token_constant_time(self):
        """Token verification should use constant-time comparison"""
        # This test verifies that hmac.compare_digest is used
        # by checking the function implementation
        import inspect
        source = inspect.getsource(invitation_service.verify_token)
        assert "hmac.compare_digest" in source


# ============================================================================
# Rate Limiting Tests
# ============================================================================

class TestRateLimiting:
    """Test rate limiting for teams and emails"""

    def test_check_team_rate_limit_first_request(self, mock_redis):
        """First request should set expiry"""
        mock_redis.incr.return_value = 1
        team_id = uuid4()

        # Should not raise exception
        invitation_service.check_team_rate_limit(team_id)

        # Verify expiry was set
        assert mock_redis.incr.called
        assert mock_redis.expire.called
        assert mock_redis.expire.call_args[0][1] == 3600  # 1 hour

    def test_check_team_rate_limit_within_limit(self, mock_redis):
        """Requests within limit should succeed"""
        mock_redis.incr.return_value = 25  # Less than 50
        team_id = uuid4()

        # Should not raise exception
        invitation_service.check_team_rate_limit(team_id)

    def test_check_team_rate_limit_exceeded(self, mock_redis):
        """Requests exceeding limit should raise 429"""
        mock_redis.incr.return_value = 51  # Exceeds 50/hour
        team_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.check_team_rate_limit(team_id)

        assert exc_info.value.status_code == 429
        assert "rate_limit_exceeded" in str(exc_info.value.detail)

    def test_check_email_rate_limit_first_request(self, mock_redis):
        """First email request should set expiry"""
        mock_redis.incr.return_value = 1
        email = "test@example.com"

        # Should not raise exception
        invitation_service.check_email_rate_limit(email)

        # Verify expiry was set
        assert mock_redis.incr.called
        assert mock_redis.expire.called
        assert mock_redis.expire.call_args[0][1] == 86400  # 24 hours

    def test_check_email_rate_limit_within_limit(self, mock_redis):
        """Email requests within limit should succeed"""
        mock_redis.incr.return_value = 2  # Less than 3
        email = "test@example.com"

        # Should not raise exception
        invitation_service.check_email_rate_limit(email)

    def test_check_email_rate_limit_exceeded(self, mock_redis):
        """Email requests exceeding limit should raise 429"""
        mock_redis.incr.return_value = 4  # Exceeds 3/day
        email = "test@example.com"

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.check_email_rate_limit(email)

        assert exc_info.value.status_code == 429
        assert "rate_limit_exceeded" in str(exc_info.value.detail)

    def test_rate_limit_no_redis(self, mock_redis):
        """Rate limiting should skip if Redis not available"""
        with patch("app.services.invitation_service.redis_client", None):
            team_id = uuid4()
            email = "test@example.com"

            # Should not raise exception even without Redis
            invitation_service.check_team_rate_limit(team_id)
            invitation_service.check_email_rate_limit(email)


# ============================================================================
# Send Invitation Tests
# ============================================================================

class TestSendInvitation:
    """Test invitation sending with rate limiting and validation"""

    def test_send_invitation_success(
        self,
        mock_db,
        mock_redis,
        sample_team,
        sample_user,
        sample_invitation_data,
    ):
        """Successful invitation send"""
        mock_redis.incr.return_value = 1

        # Mock no existing invitation
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_team,  # Team exists
            None,  # No existing invitation
            sample_user,  # Inviter user
        ]

        response, raw_token = invitation_service.send_invitation(
            team_id=sample_team.id,
            data=sample_invitation_data,
            invited_by_user_id=sample_user.id,
            db=mock_db,
        )

        # Verify token is returned
        assert len(raw_token) == 43

        # Verify response
        assert response.invited_email == sample_invitation_data.email
        assert response.role == sample_invitation_data.role
        assert response.status == InvitationStatus.PENDING

        # Verify database add/commit called
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_send_invitation_team_not_found(
        self,
        mock_db,
        mock_redis,
        sample_user,
        sample_invitation_data,
    ):
        """Invitation send should fail if team not found"""
        mock_redis.incr.return_value = 1

        # Mock team not found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.send_invitation(
                team_id=uuid4(),
                data=sample_invitation_data,
                invited_by_user_id=sample_user.id,
                db=mock_db,
            )

        assert exc_info.value.status_code == 404
        assert "Team not found" in str(exc_info.value.detail)

    def test_send_invitation_duplicate_pending(
        self,
        mock_db,
        mock_redis,
        sample_team,
        sample_user,
        sample_invitation_data,
    ):
        """Duplicate pending invitation should fail with 409"""
        mock_redis.incr.return_value = 1

        # Mock existing pending invitation
        existing_invitation = TeamInvitation(
            id=uuid4(),
            team_id=sample_team.id,
            invited_email=sample_invitation_data.email,
            status=InvitationStatus.PENDING,
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_team,  # Team exists
            existing_invitation,  # Existing invitation found
        ]

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.send_invitation(
                team_id=sample_team.id,
                data=sample_invitation_data,
                invited_by_user_id=sample_user.id,
                db=mock_db,
            )

        assert exc_info.value.status_code == 409
        assert "invitation_exists" in str(exc_info.value.detail)

    def test_send_invitation_rate_limit_exceeded(
        self,
        mock_db,
        mock_redis,
        sample_team,
        sample_user,
        sample_invitation_data,
    ):
        """Rate limit exceeded should fail with 429"""
        mock_redis.incr.return_value = 51  # Exceeds limit

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.send_invitation(
                team_id=sample_team.id,
                data=sample_invitation_data,
                invited_by_user_id=sample_user.id,
                db=mock_db,
            )

        assert exc_info.value.status_code == 429

    def test_send_invitation_token_hashed(
        self,
        mock_db,
        mock_redis,
        sample_team,
        sample_user,
        sample_invitation_data,
    ):
        """Token should be hashed before storage (never store raw)"""
        mock_redis.incr.return_value = 1

        # Mock no existing invitation
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_team,
            None,
            sample_user,
        ]

        response, raw_token = invitation_service.send_invitation(
            team_id=sample_team.id,
            data=sample_invitation_data,
            invited_by_user_id=sample_user.id,
            db=mock_db,
        )

        # Verify invitation was created with hashed token
        invitation_call = mock_db.add.call_args[0][0]
        assert isinstance(invitation_call, TeamInvitation)
        assert len(invitation_call.invitation_token_hash) == 64  # SHA256 hash
        assert invitation_call.invitation_token_hash != raw_token  # NOT raw token


# ============================================================================
# Get Invitation Tests
# ============================================================================

class TestGetInvitation:
    """Test getting invitation details by token"""

    def test_get_invitation_valid_token(self, mock_db, sample_team):
        """Valid token should return invitation details"""
        token = "test_token_123"
        token_hash = invitation_service.hash_token(token)

        invitation = TeamInvitation(
            id=uuid4(),
            team_id=sample_team.id,
            invited_email="test@example.com",
            invitation_token_hash=token_hash,
            role="member",
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=7),
            invited_by=uuid4(),
            created_at=datetime.utcnow(),
        )

        # Mock inviter user
        mock_inviter = MagicMock()
        mock_inviter.id = invitation.invited_by
        mock_inviter.username = "inviter"
        mock_inviter.display_name = "Inviter"

        # Mock database query
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            invitation,  # Invitation found
            sample_team,  # Team found
            mock_inviter,  # Inviter found
        ]

        details = invitation_service.get_invitation_by_token(token, mock_db)

        assert details.invited_email == invitation.invited_email
        assert details.role == invitation.role
        assert details.status == invitation.status

    def test_get_invitation_invalid_token(self, mock_db):
        """Invalid token should fail with 404"""
        token = "invalid_token"

        # Mock invitation not found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.get_invitation_by_token(token, mock_db)

        assert exc_info.value.status_code == 404
        assert "invitation_not_found" in str(exc_info.value.detail)

    def test_get_invitation_already_used(self, mock_db):
        """Already used invitation should fail with 410"""
        token = "test_token_123"
        token_hash = invitation_service.hash_token(token)

        invitation = TeamInvitation(
            id=uuid4(),
            team_id=uuid4(),
            invited_email="test@example.com",
            invitation_token_hash=token_hash,
            status=InvitationStatus.ACCEPTED,  # Already accepted
        )

        mock_db.query.return_value.filter.return_value.first.return_value = invitation

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.get_invitation_by_token(token, mock_db)

        assert exc_info.value.status_code == 410
        assert "invitation_already_used" in str(exc_info.value.detail)

    def test_get_invitation_expired(self, mock_db):
        """Expired invitation should fail with 404"""
        token = "test_token_123"
        token_hash = invitation_service.hash_token(token)

        invitation = TeamInvitation(
            id=uuid4(),
            team_id=uuid4(),
            invited_email="test@example.com",
            invitation_token_hash=token_hash,
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired
        )

        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = invitation

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.get_invitation_by_token(token, mock_db)

        assert exc_info.value.status_code == 404
        assert "invitation_expired" in str(exc_info.value.detail)


# ============================================================================
# Accept Invitation Tests
# ============================================================================

class TestAcceptInvitation:
    """Test invitation acceptance with security checks"""

    def test_accept_invitation_success(self, mock_db, sample_team):
        """Successful invitation acceptance"""
        token = "test_token_123"
        token_hash = invitation_service.hash_token(token)
        user_id = uuid4()
        user_email = "test@example.com"

        invitation = TeamInvitation(
            id=uuid4(),
            team_id=sample_team.id,
            invited_email=user_email,
            invitation_token_hash=token_hash,
            role="member",
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

        # Mock database query - P1 fix adds existing_member check
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            invitation,  # Invitation found
            None,  # No existing TeamMember (P1 fix: user not already in team)
            sample_team,  # Team found
        ]

        result = invitation_service.accept_invitation(
            token=token,
            user_id=user_id,
            user_email=user_email,
            db=mock_db,
        )

        assert result.status == "accepted"
        assert result.team_id == sample_team.id
        assert result.role == "member"
        assert mock_db.commit.called

    def test_accept_invitation_email_mismatch(self, mock_db):
        """Email mismatch should fail with 403"""
        token = "test_token_123"
        token_hash = invitation_service.hash_token(token)

        invitation = TeamInvitation(
            id=uuid4(),
            team_id=uuid4(),
            invited_email="invitee@example.com",
            invitation_token_hash=token_hash,
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

        mock_db.query.return_value.filter.return_value.first.return_value = invitation

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.accept_invitation(
                token=token,
                user_id=uuid4(),
                user_email="wrong@example.com",  # Mismatched email
                db=mock_db,
            )

        assert exc_info.value.status_code == 403
        assert "email_mismatch" in str(exc_info.value.detail)

    def test_accept_invitation_already_accepted(self, mock_db):
        """Already accepted invitation should fail with 404"""
        token = "test_token_123"
        token_hash = invitation_service.hash_token(token)

        invitation = TeamInvitation(
            id=uuid4(),
            team_id=uuid4(),
            invited_email="test@example.com",
            invitation_token_hash=token_hash,
            status=InvitationStatus.ACCEPTED,  # Already accepted
        )

        # Mock returns None because query filters by status=PENDING
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.accept_invitation(
                token=token,
                user_id=uuid4(),
                user_email="test@example.com",
                db=mock_db,
            )

        assert exc_info.value.status_code == 404


# ============================================================================
# Decline Invitation Tests
# ============================================================================

class TestDeclineInvitation:
    """Test invitation decline"""

    def test_decline_invitation_success(self, mock_db):
        """Successful invitation decline"""
        token = "test_token_123"
        token_hash = invitation_service.hash_token(token)

        invitation = TeamInvitation(
            id=uuid4(),
            team_id=uuid4(),
            invited_email="test@example.com",
            invitation_token_hash=token_hash,
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow(),
            invited_by=uuid4(),
        )

        mock_db.query.return_value.filter.return_value.first.return_value = invitation

        result = invitation_service.decline_invitation(token, mock_db)

        assert result.status == "declined"
        assert result.declined_at is not None
        assert mock_db.commit.called

    def test_decline_invitation_already_accepted(self, mock_db):
        """Cannot decline already accepted invitation"""
        token = "test_token_123"
        token_hash = invitation_service.hash_token(token)

        invitation = TeamInvitation(
            id=uuid4(),
            team_id=uuid4(),
            invited_email="test@example.com",
            invitation_token_hash=token_hash,
            status=InvitationStatus.ACCEPTED,  # Already accepted
        )

        mock_db.query.return_value.filter.return_value.first.return_value = invitation

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.decline_invitation(token, mock_db)

        assert exc_info.value.status_code == 400
        assert "cannot_decline_invitation" in str(exc_info.value.detail)


# ============================================================================
# Resend Invitation Tests
# ============================================================================

class TestResendInvitation:
    """Test invitation resend with rate limiting"""

    def test_resend_invitation_success(self, mock_db):
        """Successful invitation resend"""
        invitation_id = uuid4()

        invitation = TeamInvitation(
            id=invitation_id,
            team_id=uuid4(),
            invited_email="test@example.com",
            invitation_token_hash="old_hash",
            status=InvitationStatus.PENDING,
            resend_count=0,
            last_resent_at=None,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

        mock_db.query.return_value.filter.return_value.first.return_value = invitation

        result, new_token = invitation_service.resend_invitation(invitation_id, mock_db)

        # Verify new token generated
        assert len(new_token) == 43

        # Verify response
        assert result.resend_count == 1
        assert result.last_resent_at is not None
        assert mock_db.commit.called

    def test_resend_invitation_limit_exceeded(self, mock_db):
        """Resend limit exceeded should fail with 429"""
        invitation = TeamInvitation(
            id=uuid4(),
            team_id=uuid4(),
            invited_email="test@example.com",
            invitation_token_hash="hash",
            status=InvitationStatus.PENDING,
            resend_count=3,  # At limit
        )

        mock_db.query.return_value.filter.return_value.first.return_value = invitation

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.resend_invitation(invitation.id, mock_db)

        assert exc_info.value.status_code == 429
        assert "resend_limit_exceeded" in str(exc_info.value.detail)

    def test_resend_invitation_cooldown_active(self, mock_db):
        """Cooldown period should prevent immediate resend"""
        invitation = TeamInvitation(
            id=uuid4(),
            team_id=uuid4(),
            invited_email="test@example.com",
            invitation_token_hash="hash",
            status=InvitationStatus.PENDING,
            resend_count=1,
            last_resent_at=datetime.utcnow() - timedelta(minutes=2),  # 2 minutes ago
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

        mock_db.query.return_value.filter.return_value.first.return_value = invitation

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.resend_invitation(invitation.id, mock_db)

        assert exc_info.value.status_code == 429
        assert "resend_cooldown_active" in str(exc_info.value.detail)
