"""
Unit Tests for GitHub Webhook Service - Sprint 129.5 Day 1

Tests webhook signature validation, idempotency, and event handling.

Test Suite Structure:
- TestSignatureValidation: 2 tests (valid + invalid HMAC)
- TestIdempotencyService: 2 tests (new + duplicate delivery)
- TestPayloadParsing: 2 tests (push + pull_request events)
- TestEventHandlers: 2 tests (installation + unknown events)

Total: 8 unit tests (Day 1 requirement)

Reference: SPRINT-129.5-GITHUB-WEBHOOKS.md
"""

import hashlib
import hmac
import json
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from app.services.github_webhook_service import (
    verify_webhook_signature,
    WebhookIdempotencyService,
    parse_webhook_payload,
    parse_push_event,
    parse_pull_request_event,
    handle_push_event,
    handle_pull_request_event,
    handle_installation_event,
    process_webhook,
    WebhookPayload,
    CheckStatus,
    format_compliance_comment,
    ComplianceResult,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def webhook_secret():
    """Test webhook secret."""
    return "test-webhook-secret-123"


@pytest.fixture
def sample_push_payload():
    """Sample push event payload."""
    return {
        "ref": "refs/heads/main",
        "before": "0000000000000000000000000000000000000000",
        "after": "abc123def456789012345678901234567890abcd",
        "repository": {
            "id": 12345,
            "name": "test-repo",
            "full_name": "owner/test-repo",
            "owner": {"login": "owner"}
        },
        "pusher": {"name": "test-user"},
        "commits": [
            {
                "id": "abc123",
                "message": "Fix bug in authentication",
                "timestamp": "2026-01-31T10:00:00Z",
                "author": {"name": "Test User"}
            }
        ],
        "head_commit": {
            "id": "abc123",
            "message": "Fix bug in authentication"
        },
        "installation": {"id": 99999}
    }


@pytest.fixture
def sample_pr_payload():
    """Sample pull_request event payload."""
    return {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "number": 42,
            "title": "Add new feature",
            "body": "This PR adds a new feature",
            "state": "open",
            "draft": False,
            "head": {
                "sha": "abc123def456",
                "ref": "feature/new-feature"
            },
            "base": {
                "ref": "main"
            }
        },
        "repository": {
            "id": 12345,
            "name": "test-repo",
            "full_name": "owner/test-repo"
        },
        "sender": {"login": "contributor"},
        "installation": {"id": 99999}
    }


@pytest.fixture
def sample_installation_payload():
    """Sample installation event payload."""
    return {
        "action": "created",
        "installation": {
            "id": 99999,
            "account": {
                "login": "test-org",
                "type": "Organization"
            }
        },
        "sender": {"login": "admin-user"}
    }


# ============================================================================
# Test 1-2: Signature Validation
# ============================================================================

class TestSignatureValidation:
    """Tests for webhook signature validation (HMAC-SHA256)."""

    def test_valid_signature(self, webhook_secret):
        """
        Test 1: Valid HMAC-SHA256 signature is accepted.

        Verifies that a correctly computed signature passes validation.
        """
        payload = b'{"action": "opened", "number": 42}'

        # Compute valid signature
        expected_sig = "sha256=" + hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = verify_webhook_signature(payload, expected_sig, webhook_secret)
        assert result is True

    def test_invalid_signature(self, webhook_secret):
        """
        Test 2: Invalid HMAC-SHA256 signature is rejected.

        Verifies that tampered or incorrect signatures are rejected.
        """
        payload = b'{"action": "opened", "number": 42}'
        invalid_signature = "sha256=invalid_signature_here_abc123"

        result = verify_webhook_signature(payload, invalid_signature, webhook_secret)
        assert result is False

    def test_missing_sha256_prefix(self, webhook_secret):
        """
        Test 2b: Signature without sha256= prefix is rejected.
        """
        payload = b'{"action": "opened"}'
        # Signature without prefix
        signature_without_prefix = hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = verify_webhook_signature(payload, signature_without_prefix, webhook_secret)
        assert result is False

    def test_empty_signature(self, webhook_secret):
        """
        Test 2c: Empty signature is rejected.
        """
        payload = b'{"action": "opened"}'
        result = verify_webhook_signature(payload, "", webhook_secret)
        assert result is False


# ============================================================================
# Test 3-4: Idempotency Service
# ============================================================================

class TestIdempotencyService:
    """Tests for Redis-based webhook idempotency."""

    def test_new_delivery_not_duplicate(self):
        """
        Test 3: New delivery_id is not marked as duplicate.

        First occurrence of a delivery_id should return False (not duplicate).
        """
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 0  # Key doesn't exist

        service = WebhookIdempotencyService(redis_client=mock_redis)
        result = service.is_duplicate("new-delivery-123")

        assert result is False
        mock_redis.exists.assert_called_once_with("webhook:delivery:new-delivery-123")

    def test_duplicate_delivery_detected(self):
        """
        Test 4: Duplicate delivery_id is detected.

        Second occurrence of the same delivery_id should return True.
        """
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 1  # Key exists

        service = WebhookIdempotencyService(redis_client=mock_redis)
        result = service.is_duplicate("existing-delivery-456")

        assert result is True
        mock_redis.exists.assert_called_once_with("webhook:delivery:existing-delivery-456")

    def test_mark_processed_success(self):
        """
        Test 4b: mark_processed stores delivery_id in Redis.
        """
        mock_redis = MagicMock()
        mock_redis.set.return_value = True  # SET NX succeeded

        service = WebhookIdempotencyService(redis_client=mock_redis)
        result = service.mark_processed("delivery-789", "push")

        assert result is True
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "webhook:delivery:delivery-789"
        assert "push" in call_args[0][1]  # Event type in value

    def test_mark_processed_already_exists(self):
        """
        Test 4c: mark_processed returns False if already processed.
        """
        mock_redis = MagicMock()
        mock_redis.set.return_value = False  # SET NX failed (key exists)

        service = WebhookIdempotencyService(redis_client=mock_redis)
        result = service.mark_processed("already-processed", "push")

        assert result is False


# ============================================================================
# Test 5-6: Payload Parsing
# ============================================================================

class TestPayloadParsing:
    """Tests for webhook payload parsing."""

    def test_parse_push_event(self, sample_push_payload):
        """
        Test 5: Push event payload is correctly parsed.

        Extracts repository, branch, commit, and pusher info.
        """
        result = parse_push_event(sample_push_payload)

        assert result.ref == "refs/heads/main"
        assert result.repository_full_name == "owner/test-repo"
        assert result.repository_id == 12345
        assert result.pusher_name == "test-user"
        assert len(result.commits) == 1
        assert result.head_commit["message"] == "Fix bug in authentication"
        assert result.after == "abc123def456789012345678901234567890abcd"

    def test_parse_pull_request_event(self, sample_pr_payload):
        """
        Test 6: Pull request event payload is correctly parsed.

        Extracts PR number, action, title, and commit info.
        """
        result = parse_pull_request_event(sample_pr_payload)

        assert result.action == "opened"
        assert result.pr_number == 42
        assert result.pr_title == "Add new feature"
        assert result.head_sha == "abc123def456"
        assert result.head_ref == "feature/new-feature"
        assert result.base_ref == "main"
        assert result.repository_full_name == "owner/test-repo"
        assert result.sender_login == "contributor"
        assert result.is_draft is False

    def test_parse_webhook_payload(self, sample_push_payload):
        """
        Test 6b: Generic webhook payload parsing.
        """
        result = parse_webhook_payload(
            event_type="push",
            delivery_id="delivery-123",
            payload=sample_push_payload
        )

        assert result.event_type == "push"
        assert result.delivery_id == "delivery-123"
        assert result.installation_id == 99999
        assert result.repository["full_name"] == "owner/test-repo"


# ============================================================================
# Test 7-8: Event Handlers
# ============================================================================

class TestEventHandlers:
    """Tests for event-specific handlers."""

    @pytest.mark.asyncio
    async def test_installation_event_created(self, sample_installation_payload):
        """
        Test 7: Installation created event is handled correctly.
        """
        payload = WebhookPayload(
            event_type="installation",
            delivery_id="delivery-install",
            installation_id=99999,
            action="created",
            repository=None,
            sender={"login": "admin-user"},
            raw_payload=sample_installation_payload
        )

        result = await handle_installation_event(payload)

        assert result["status"] == "acknowledged"
        assert result["action"] == "created"
        assert result["installation_id"] == 99999
        assert result["account"] == "test-org"

    @pytest.mark.asyncio
    async def test_unknown_event_ignored(self):
        """
        Test 8: Unknown event types are logged and ignored.
        """
        # Test the main process_webhook function with unknown event
        with patch(
            'app.services.github_webhook_service.get_idempotency_service'
        ) as mock_idempotency:
            mock_service = MagicMock()
            mock_service.is_duplicate.return_value = False
            mock_idempotency.return_value = mock_service

            result = await process_webhook(
                event_type="unknown_event_type",
                delivery_id="delivery-unknown",
                payload={"action": "test"}
            )

            assert result["status"] == "ignored"
            assert result["event"] == "unknown_event_type"
            assert result["reason"] == "unsupported_event"

    @pytest.mark.asyncio
    async def test_push_event_handler(self, sample_push_payload):
        """
        Test 7b: Push event triggers gap analysis (accepted).
        """
        payload = WebhookPayload(
            event_type="push",
            delivery_id="delivery-push",
            installation_id=99999,
            action=None,
            repository=sample_push_payload["repository"],
            sender=None,
            raw_payload=sample_push_payload
        )

        result = await handle_push_event(payload)

        assert result["status"] == "accepted"
        assert result["event"] == "push"
        assert result["repository"] == "owner/test-repo"
        assert result["branch"] == "main"
        assert result["commits_count"] == 1

    @pytest.mark.asyncio
    async def test_pull_request_event_handler(self, sample_pr_payload):
        """
        Test 8b: Pull request event triggers gate evaluation.
        """
        payload = WebhookPayload(
            event_type="pull_request",
            delivery_id="delivery-pr",
            installation_id=99999,
            action="opened",
            repository=sample_pr_payload["repository"],
            sender=sample_pr_payload["sender"],
            raw_payload=sample_pr_payload
        )

        result = await handle_pull_request_event(payload)

        assert result["status"] == "accepted"
        assert result["event"] == "pull_request"
        assert result["action"] == "opened"
        assert result["pr_number"] == 42
        assert result["head_sha"] == "abc123def456"


# ============================================================================
# Additional Tests: PR Comment Formatting
# ============================================================================

class TestComplianceFormatting:
    """Tests for compliance report formatting."""

    def test_format_compliance_comment_success(self):
        """Format compliance comment for passing score."""
        result = ComplianceResult(
            score=95,
            violations_count=0,
            violations=[],
            gate_status="passed"
        )

        comment = format_compliance_comment(result)

        assert "✅" in comment
        assert "95%" in comment
        assert "Passed" in comment
        assert "0" in comment  # violations count

    def test_format_compliance_comment_failure(self):
        """Format compliance comment with violations."""
        result = ComplianceResult(
            score=60,
            violations_count=3,
            violations=[
                {"gate": "G1", "severity": "HIGH", "rule": "Missing PRD", "file": "-", "line": "-"},
                {"gate": "G2", "severity": "MEDIUM", "rule": "Incomplete ADR", "file": "docs/adr.md", "line": "10"},
                {"gate": "G2", "severity": "LOW", "rule": "Formatting", "file": "docs/api.md", "line": "45"},
            ],
            gate_status="failed"
        )

        comment = format_compliance_comment(result, report_url="https://sdlc.example.com/report/123")

        assert "❌" in comment
        assert "60%" in comment
        assert "Failed" in comment
        assert "3" in comment  # violations count
        assert "G1 Violations" in comment
        assert "G2 Violations" in comment
        assert "Missing PRD" in comment
        assert "https://sdlc.example.com/report/123" in comment


# ============================================================================
# Integration Test: Full Webhook Flow
# ============================================================================

class TestWebhookFlow:
    """Integration tests for complete webhook processing flow."""

    @pytest.mark.asyncio
    async def test_full_push_webhook_flow(self, sample_push_payload, webhook_secret):
        """
        Integration: Complete push webhook flow.

        1. Validate signature
        2. Check idempotency
        3. Parse payload
        4. Handle event
        5. Mark processed
        """
        payload_bytes = json.dumps(sample_push_payload).encode()
        signature = "sha256=" + hmac.new(
            webhook_secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        # Step 1: Validate signature
        assert verify_webhook_signature(payload_bytes, signature, webhook_secret) is True

        # Steps 2-5: Process webhook
        with patch(
            'app.services.github_webhook_service.get_idempotency_service'
        ) as mock_idempotency:
            mock_service = MagicMock()
            mock_service.is_duplicate.return_value = False
            mock_service.mark_processed.return_value = True
            mock_idempotency.return_value = mock_service

            result = await process_webhook(
                event_type="push",
                delivery_id="delivery-full-flow",
                payload=sample_push_payload
            )

            assert result["status"] == "accepted"
            assert result["event"] == "push"

            # Verify idempotency was checked and marked
            mock_service.is_duplicate.assert_called_once_with("delivery-full-flow")
            mock_service.mark_processed.assert_called_once()

    @pytest.mark.asyncio
    async def test_duplicate_webhook_skipped(self, sample_push_payload):
        """
        Integration: Duplicate webhook is detected and skipped.
        """
        with patch(
            'app.services.github_webhook_service.get_idempotency_service'
        ) as mock_idempotency:
            mock_service = MagicMock()
            mock_service.is_duplicate.return_value = True  # Already processed
            mock_idempotency.return_value = mock_service

            result = await process_webhook(
                event_type="push",
                delivery_id="delivery-duplicate",
                payload=sample_push_payload
            )

            assert result["status"] == "duplicate"
            assert result["delivery_id"] == "delivery-duplicate"
            assert "already processed" in result["message"].lower()
