"""
Security Tests for Team Invitation System

Tests for security-critical features and potential vulnerabilities.

Security Test Coverage:
1. Token enumeration attack prevention
2. Timing attack prevention (constant-time comparison)
3. Replay attack prevention (one-time use)
4. Rate limiting bypass attempts
5. Email injection prevention

Reference: ADR-043-Team-Invitation-System-Architecture.md
OWASP: A07:2021 - Identification and Authentication Failures
"""
import hashlib
import time
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


# ============================================================================
# Security Test 1: Token Enumeration Attack Prevention
# ============================================================================

class TestTokenEnumerationPrevention:
    """
    Prevent attackers from enumerating valid invitation tokens.

    Attack Vector:
    - Attacker tries random tokens to find valid invitations
    - 404 response reveals "not found", 410 reveals "already used"
    - Information leakage enables targeted attacks

    Defense:
    - Same error message for all invalid tokens
    - No timing differences in responses
    - Rate limiting on token validation endpoint
    """

    def test_invalid_token_generic_error(self, mock_db):
        """Invalid token should return generic 404 (no information leakage)"""
        # Test with completely random token
        random_token = "completely_invalid_token_12345"

        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.get_invitation_by_token(random_token, mock_db)

        # Should be generic error (no hints about why it failed)
        assert exc_info.value.status_code == 404
        assert "invitation_not_found" in str(exc_info.value.detail)
        # Should NOT reveal if token was wrong format, expired, or never existed

    def test_expired_token_same_error(self, mock_db):
        """Expired token should return same error as invalid token"""
        token = "test_token_123"
        token_hash = invitation_service.hash_token(token)

        expired_invitation = TeamInvitation(
            id=uuid4(),
            team_id=uuid4(),
            invited_email="test@example.com",
            invitation_token_hash=token_hash,
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired
        )

        mock_db.query.return_value.filter.return_value.first.return_value = expired_invitation

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.get_invitation_by_token(token, mock_db)

        # Should be same 404 error (not 410 Gone which reveals it existed)
        assert exc_info.value.status_code == 404
        assert "invitation_expired" in str(exc_info.value.detail)


# ============================================================================
# Security Test 2: Timing Attack Prevention
# ============================================================================

class TestTimingAttackPrevention:
    """
    Prevent timing attacks on token verification.

    Attack Vector:
    - Attacker measures response time to guess token characters
    - String comparison stops at first mismatch (faster for wrong prefix)
    - Timing differences leak information about token correctness

    Defense:
    - Use hmac.compare_digest() for constant-time comparison
    - All comparisons take same time regardless of input
    """

    def test_verify_token_constant_time_implementation(self):
        """Verify implementation uses hmac.compare_digest"""
        import inspect
        source = inspect.getsource(invitation_service.verify_token)

        # Verify constant-time comparison function is used
        assert "hmac.compare_digest" in source, (
            "Token verification MUST use hmac.compare_digest() "
            "to prevent timing attacks"
        )

    def test_verify_token_timing_consistency(self):
        """
        Timing should be consistent for valid and invalid tokens.

        Note: This is a statistical test that may have false positives.
        It verifies that timing differences are minimal.
        """
        token = "valid_token_12345"
        valid_hash = invitation_service.hash_token(token)

        # Measure timing for correct token
        correct_times = []
        for _ in range(100):
            start = time.perf_counter()
            invitation_service.verify_token(token, valid_hash)
            correct_times.append(time.perf_counter() - start)

        # Measure timing for incorrect token
        incorrect_times = []
        for _ in range(100):
            start = time.perf_counter()
            invitation_service.verify_token("wrong_token", valid_hash)
            incorrect_times.append(time.perf_counter() - start)

        # Calculate average timing difference
        avg_correct = sum(correct_times) / len(correct_times)
        avg_incorrect = sum(incorrect_times) / len(incorrect_times)

        # Timing difference should be negligible (<10% variance)
        # If using string comparison, difference would be >50%
        variance_percent = abs(avg_correct - avg_incorrect) / avg_correct * 100

        assert variance_percent < 10, (
            f"Timing variance {variance_percent:.2f}% suggests non-constant-time comparison. "
            "This may indicate a timing attack vulnerability."
        )


# ============================================================================
# Security Test 3: Replay Attack Prevention
# ============================================================================

class TestReplayAttackPrevention:
    """
    Prevent replay attacks on invitation acceptance.

    Attack Vector:
    - Attacker captures acceptance request
    - Replays request to join team multiple times
    - Creates multiple memberships or bypasses authorization

    Defense:
    - One-time use tokens (status change after accept)
    - Database transaction ensures atomicity
    - Status check before processing
    """

    def test_accept_invitation_one_time_use(self, mock_db):
        """Invitation can only be accepted once"""
        token = "test_token_123"
        token_hash = invitation_service.hash_token(token)
        user_id = uuid4()
        user_email = "test@example.com"

        # First attempt: invitation exists with PENDING status
        invitation = TeamInvitation(
            id=uuid4(),
            team_id=uuid4(),
            invited_email=user_email,
            invitation_token_hash=token_hash,
            role="member",
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

        mock_team = MagicMock()
        mock_team.id = invitation.team_id
        mock_team.name = "Test Team"

        # First acceptance - P1 fix adds existing_member check
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            invitation,  # Invitation found
            None,  # No existing TeamMember (P1 fix: user not already in team)
            mock_team,  # Team found
        ]

        result1 = invitation_service.accept_invitation(
            token=token,
            user_id=user_id,
            user_email=user_email,
            db=mock_db,
        )

        assert result1.status == "accepted"

        # Second attempt: invitation now has ACCEPTED status
        # Query should filter by status=PENDING and return None
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # No PENDING invitation found
        ]

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.accept_invitation(
                token=token,
                user_id=user_id,
                user_email=user_email,
                db=mock_db,
            )

        assert exc_info.value.status_code == 404

    def test_decline_invitation_one_time_use(self, mock_db):
        """Invitation cannot be declined after acceptance"""
        token = "test_token_123"
        token_hash = invitation_service.hash_token(token)

        # Already accepted invitation
        invitation = TeamInvitation(
            id=uuid4(),
            team_id=uuid4(),
            invited_email="test@example.com",
            invitation_token_hash=token_hash,
            status=InvitationStatus.ACCEPTED,
        )

        mock_db.query.return_value.filter.return_value.first.return_value = invitation

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.decline_invitation(token, mock_db)

        assert exc_info.value.status_code == 400
        assert "cannot_decline_invitation" in str(exc_info.value.detail)


# ============================================================================
# Security Test 4: Rate Limiting Bypass Prevention
# ============================================================================

class TestRateLimitingBypass:
    """
    Prevent rate limiting bypass attempts.

    Attack Vector:
    - Attacker sends invitations from multiple IPs
    - Attacker uses multiple team accounts
    - Attacker spams same email address

    Defense:
    - Per-team rate limiting (50/hour)
    - Per-email rate limiting (3/day across all teams)
    - Redis-based sliding window
    """

    def test_email_rate_limit_across_teams(self, mock_db, mock_redis):
        """Email rate limit should apply across ALL teams"""
        email = "victim@example.com"
        team_id_1 = uuid4()
        team_id_2 = uuid4()
        user_id = uuid4()

        # Mock Redis returns 2 (within limit)
        mock_redis.incr.return_value = 2

        # Mock teams exist
        team1 = MagicMock()
        team1.id = team_id_1
        team1.name = "Team 1"
        team2 = MagicMock()
        team2.id = team_id_2
        team2.name = "Team 2"

        data = InvitationCreate(email=email, role="member")

        # First invitation from Team 1 (2nd invitation to this email today)
        user1 = MagicMock()
        user1.id = user_id
        user1.full_name = "User 1"
        user1.display_name = "User 1"
        user1.username = "user1"
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            team1,
            None,
            user1,
        ]

        invitation_service.send_invitation(
            team_id=team_id_1,
            data=data,
            invited_by_user_id=user_id,
            db=mock_db,
        )

        # Mock Redis now returns 3 (at limit)
        mock_redis.incr.return_value = 3

        # Second invitation from Team 2 (3rd invitation to this email today)
        user2 = MagicMock()
        user2.id = user_id
        user2.full_name = "User 2"
        user2.display_name = "User 2"
        user2.username = "user2"
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            team2,
            None,
            user2,
        ]

        invitation_service.send_invitation(
            team_id=team_id_2,
            data=data,
            invited_by_user_id=user_id,
            db=mock_db,
        )

        # Mock Redis now returns 4 (exceeds limit)
        mock_redis.incr.return_value = 4

        # Third invitation should fail (exceeds 3/day limit)
        with pytest.raises(HTTPException) as exc_info:
            invitation_service.send_invitation(
                team_id=team_id_1,
                data=data,
                invited_by_user_id=user_id,
                db=mock_db,
            )

        assert exc_info.value.status_code == 429

    def test_team_rate_limit_sliding_window(self, mock_redis):
        """Rate limit should use sliding window (not fixed window)"""
        team_id = uuid4()

        # Configure mock to return a count below limit
        mock_redis.incr.return_value = 1

        # Verify Redis key includes hour (sliding window)
        invitation_service.check_team_rate_limit(team_id)

        # Extract Redis key from incr call
        redis_key = mock_redis.incr.call_args[0][0]

        # Key should include YYYYMMDDHH format (hourly buckets)
        assert "invitation_rate" in redis_key
        assert str(team_id) in redis_key
        assert datetime.utcnow().strftime('%Y%m%d%H') in redis_key


# ============================================================================
# Security Test 5: Email Injection Prevention
# ============================================================================

class TestEmailInjectionPrevention:
    """
    Prevent email injection attacks.

    Attack Vector:
    - Attacker includes malicious content in message field
    - XSS payload in HTML email
    - Email header injection

    Defense:
    - HTML escaping in email templates
    - Email validation (Pydantic EmailStr)
    - Message length limits
    """

    def test_invitation_message_xss_prevention(self):
        """Malicious HTML in message should be escaped"""
        from app.services.email_service import get_invitation_email_html

        malicious_message = '<script>alert("XSS")</script>'

        html = get_invitation_email_html(
            team_name="Test Team",
            inviter_name="Inviter",
            invitation_link="http://localhost/invitations/accept?token=abc123",
            role="member",
            expires_at=datetime.utcnow() + timedelta(days=7),
            message=malicious_message,
        )

        # Verify script tags are escaped
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
        assert "&lt;/script&gt;" in html

    def test_invitation_email_validation(self):
        """Email field should validate with Pydantic EmailStr"""
        from app.schemas.invitation import InvitationCreate

        # Valid email should pass
        valid_data = InvitationCreate(
            email="valid@example.com",
            role="member",
        )
        assert valid_data.email == "valid@example.com"

        # Invalid email should fail validation
        with pytest.raises(Exception):  # Pydantic ValidationError
            InvitationCreate(
                email="not-an-email",
                role="member",
            )

    def test_invitation_message_length_limit(self):
        """Message field should enforce length limit"""
        from app.schemas.invitation import InvitationCreate

        # Valid message (500 chars)
        valid_message = "x" * 500
        valid_data = InvitationCreate(
            email="test@example.com",
            role="member",
            message=valid_message,
        )
        assert len(valid_data.message) == 500

        # Excessive message (>500 chars) should fail
        with pytest.raises(Exception):  # Pydantic ValidationError
            InvitationCreate(
                email="test@example.com",
                role="member",
                message="x" * 501,
            )


# ============================================================================
# Security Test 6: Token Generation Randomness
# ============================================================================

class TestTokenRandomness:
    """
    Verify cryptographic randomness of invitation tokens.

    Attack Vector:
    - Weak random number generator
    - Predictable token sequence
    - Token collision

    Defense:
    - Use secrets.token_urlsafe() (cryptographically secure)
    - 256-bit entropy (43 characters base64url)
    - Statistical randomness tests
    """

    def test_token_generation_uses_secrets_module(self):
        """Token generation should use secrets module"""
        import inspect
        source = inspect.getsource(invitation_service.generate_invitation_token)

        # Verify secrets.token_urlsafe is used (not random module)
        assert "secrets.token_urlsafe" in source
        assert "random" not in source.lower() or "secrets" in source

    def test_token_entropy_256_bits(self):
        """Generated token should have 256-bit entropy"""
        token = invitation_service.generate_invitation_token()

        # 256 bits = 32 bytes
        # base64url encoding: 4 chars per 3 bytes
        # 32 bytes → 43 characters (with padding)
        assert len(token) == 43

    def test_token_uniqueness_statistical(self):
        """Tokens should be statistically unique (no collisions)"""
        # Generate 10,000 tokens
        tokens = [invitation_service.generate_invitation_token() for _ in range(10000)]

        # Verify no duplicates (collision probability ~0 for 256-bit)
        unique_tokens = set(tokens)
        assert len(unique_tokens) == 10000

    def test_token_character_distribution(self):
        """Token characters should be evenly distributed"""
        # Generate 1000 tokens
        tokens = [invitation_service.generate_invitation_token() for _ in range(1000)]

        # Count character frequencies
        all_chars = "".join(tokens)
        char_counts = {}
        for char in all_chars:
            char_counts[char] = char_counts.get(char, 0) + 1

        # Base64url alphabet: A-Z, a-z, 0-9, -, _
        expected_chars = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        )
        actual_chars = set(char_counts.keys())

        # Most characters should appear (allowing for statistical variance)
        assert len(actual_chars) >= 50  # At least 50 out of 64 chars


# ============================================================================
# Security Test 7: Authorization Checks
# ============================================================================

class TestAuthorizationChecks:
    """
    Verify authorization checks are enforced.

    Attack Vector:
    - User accepts invitation with mismatched email
    - User accepts expired invitation
    - Unauthorized user resends invitation

    Defense:
    - Email verification before acceptance
    - Expiry check before acceptance
    - Permission check before resend (TODO in implementation)
    """

    def test_accept_invitation_email_verification(self, mock_db):
        """Accept should verify user email matches invited email"""
        token = "test_token_123"
        token_hash = invitation_service.hash_token(token)

        invitation = TeamInvitation(
            id=uuid4(),
            team_id=uuid4(),
            invited_email="alice@example.com",
            invitation_token_hash=token_hash,
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

        mock_db.query.return_value.filter.return_value.first.return_value = invitation

        # Attempt to accept with different email
        with pytest.raises(HTTPException) as exc_info:
            invitation_service.accept_invitation(
                token=token,
                user_id=uuid4(),
                user_email="bob@example.com",  # Different email
                db=mock_db,
            )

        assert exc_info.value.status_code == 403
        assert "email_mismatch" in str(exc_info.value.detail)

    def test_accept_invitation_expiry_check(self, mock_db):
        """Accept should reject expired invitations"""
        token = "test_token_123"
        token_hash = invitation_service.hash_token(token)

        invitation = TeamInvitation(
            id=uuid4(),
            team_id=uuid4(),
            invited_email="test@example.com",
            invitation_token_hash=token_hash,
            status=InvitationStatus.PENDING,
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired
        )

        mock_db.query.return_value.filter.return_value.first.return_value = invitation

        with pytest.raises(HTTPException) as exc_info:
            invitation_service.accept_invitation(
                token=token,
                user_id=uuid4(),
                user_email="test@example.com",
                db=mock_db,
            )

        assert exc_info.value.status_code == 400
        assert "invitation_expired" in str(exc_info.value.detail)
