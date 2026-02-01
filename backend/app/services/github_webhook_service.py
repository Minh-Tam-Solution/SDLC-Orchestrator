"""
GitHub Webhook Service - Sprint 129.5

Service for handling GitHub webhook events with idempotency and background processing.

Key Features:
- HMAC-SHA256 signature validation
- Redis-based idempotency (24h TTL)
- Background job queueing (Celery)
- Event-specific handlers (push, pull_request, installation)
- PR status check posting
- PR comment posting (compliance violations)

Security:
- Webhook signature validation (X-Hub-Signature-256)
- Idempotency via X-GitHub-Delivery header
- No sensitive data logged

Reference: SPRINT-129.5-GITHUB-WEBHOOKS.md
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"

# Idempotency TTL (24 hours in seconds)
IDEMPOTENCY_TTL = 86400


# ============================================================================
# Enums
# ============================================================================

class WebhookEventType(str, Enum):
    """Supported GitHub webhook event types."""
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    INSTALLATION = "installation"
    PING = "ping"


class PullRequestAction(str, Enum):
    """Pull request webhook actions that trigger processing."""
    OPENED = "opened"
    SYNCHRONIZE = "synchronize"
    REOPENED = "reopened"
    CLOSED = "closed"


class CheckStatus(str, Enum):
    """GitHub check status values."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"


# ============================================================================
# Pydantic Models
# ============================================================================

class WebhookPayload(BaseModel):
    """Parsed webhook payload."""
    event_type: str
    delivery_id: str
    installation_id: Optional[int] = None
    action: Optional[str] = None
    repository: Optional[Dict[str, Any]] = None
    sender: Optional[Dict[str, Any]] = None
    raw_payload: Dict[str, Any]


class PushEventData(BaseModel):
    """Parsed push event data."""
    ref: str
    before: str
    after: str
    repository_full_name: str
    repository_id: int
    pusher_name: str
    commits: List[Dict[str, Any]]
    head_commit: Optional[Dict[str, Any]] = None


class PullRequestEventData(BaseModel):
    """Parsed pull request event data."""
    action: str
    pr_number: int
    pr_title: str
    pr_body: Optional[str] = None
    head_sha: str
    head_ref: str
    base_ref: str
    repository_full_name: str
    repository_id: int
    sender_login: str
    is_draft: bool = False


class ComplianceResult(BaseModel):
    """Compliance check result for PR status."""
    score: int  # 0-100
    violations_count: int
    violations: List[Dict[str, Any]]
    gate_status: str  # passed, failed, warning


# ============================================================================
# Signature Validation
# ============================================================================

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook signature (HMAC-SHA256).

    Uses constant-time comparison to prevent timing attacks.

    Args:
        payload: Raw webhook payload bytes
        signature: X-Hub-Signature-256 header value (format: "sha256=<hex>")
        secret: Webhook secret configured in GitHub App

    Returns:
        True if signature is valid, False otherwise

    Example:
        >>> payload = b'{"action": "opened"}'
        >>> signature = "sha256=abc123..."
        >>> secret = "my-webhook-secret"
        >>> verify_webhook_signature(payload, signature, secret)
        True
    """
    if not signature or not signature.startswith("sha256="):
        logger.warning("Invalid signature format: missing sha256= prefix")
        return False

    try:
        # Compute expected signature
        expected_signature = "sha256=" + hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison (prevents timing attacks)
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


# ============================================================================
# Idempotency Check (Redis)
# ============================================================================

class WebhookIdempotencyService:
    """
    Redis-based idempotency service for webhook deduplication.

    Stores X-GitHub-Delivery header to prevent duplicate processing.
    """

    def __init__(self, redis_client=None):
        """
        Initialize idempotency service.

        Args:
            redis_client: Redis client instance (optional, uses default if not provided)
        """
        self._redis = redis_client

    @property
    def redis(self):
        """Lazy load Redis client."""
        if self._redis is None:
            from app.core.redis import get_redis_client
            self._redis = get_redis_client()
        return self._redis

    def is_duplicate(self, delivery_id: str) -> bool:
        """
        Check if webhook has already been processed.

        Args:
            delivery_id: X-GitHub-Delivery header value

        Returns:
            True if duplicate (already processed), False if new
        """
        if not delivery_id:
            logger.warning("No delivery_id provided, cannot check idempotency")
            return False

        key = f"webhook:delivery:{delivery_id}"

        try:
            # Check if key exists
            exists = self.redis.exists(key)
            return bool(exists)
        except Exception as e:
            logger.error(f"Redis error checking idempotency: {e}")
            # On Redis error, allow processing (fail-open for availability)
            return False

    def mark_processed(self, delivery_id: str, event_type: str) -> bool:
        """
        Mark webhook as processed.

        Args:
            delivery_id: X-GitHub-Delivery header value
            event_type: GitHub event type

        Returns:
            True if marked successfully, False if already exists
        """
        if not delivery_id:
            return False

        key = f"webhook:delivery:{delivery_id}"
        value = json.dumps({
            "event_type": event_type,
            "processed_at": datetime.utcnow().isoformat()
        })

        try:
            # SET with NX (only if not exists) and EX (expiry)
            result = self.redis.set(key, value, ex=IDEMPOTENCY_TTL, nx=True)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis error marking processed: {e}")
            return False


# Global idempotency service instance
_idempotency_service: Optional[WebhookIdempotencyService] = None


def get_idempotency_service() -> WebhookIdempotencyService:
    """Get or create idempotency service singleton."""
    global _idempotency_service
    if _idempotency_service is None:
        _idempotency_service = WebhookIdempotencyService()
    return _idempotency_service


# ============================================================================
# Payload Parsing
# ============================================================================

def parse_webhook_payload(
    event_type: str,
    delivery_id: str,
    payload: Dict[str, Any]
) -> WebhookPayload:
    """
    Parse raw webhook payload into structured format.

    Args:
        event_type: X-GitHub-Event header value
        delivery_id: X-GitHub-Delivery header value
        payload: Parsed JSON payload

    Returns:
        WebhookPayload with extracted fields
    """
    installation = payload.get("installation", {})
    repository = payload.get("repository")
    sender = payload.get("sender")

    return WebhookPayload(
        event_type=event_type,
        delivery_id=delivery_id,
        installation_id=installation.get("id") if installation else None,
        action=payload.get("action"),
        repository=repository,
        sender=sender,
        raw_payload=payload
    )


def parse_push_event(payload: Dict[str, Any]) -> PushEventData:
    """
    Parse push event payload.

    Args:
        payload: Raw push event payload

    Returns:
        PushEventData with extracted fields

    Raises:
        ValueError: If required fields are missing
    """
    repository = payload.get("repository", {})

    if not repository:
        raise ValueError("Push event missing repository field")

    return PushEventData(
        ref=payload.get("ref", ""),
        before=payload.get("before", ""),
        after=payload.get("after", ""),
        repository_full_name=repository.get("full_name", ""),
        repository_id=repository.get("id", 0),
        pusher_name=payload.get("pusher", {}).get("name", "unknown"),
        commits=payload.get("commits", []),
        head_commit=payload.get("head_commit")
    )


def parse_pull_request_event(payload: Dict[str, Any]) -> PullRequestEventData:
    """
    Parse pull_request event payload.

    Args:
        payload: Raw pull_request event payload

    Returns:
        PullRequestEventData with extracted fields

    Raises:
        ValueError: If required fields are missing
    """
    pull_request = payload.get("pull_request", {})
    repository = payload.get("repository", {})
    sender = payload.get("sender", {})

    if not pull_request:
        raise ValueError("Pull request event missing pull_request field")

    head = pull_request.get("head", {})
    base = pull_request.get("base", {})

    return PullRequestEventData(
        action=payload.get("action", ""),
        pr_number=pull_request.get("number", 0),
        pr_title=pull_request.get("title", ""),
        pr_body=pull_request.get("body"),
        head_sha=head.get("sha", ""),
        head_ref=head.get("ref", ""),
        base_ref=base.get("ref", ""),
        repository_full_name=repository.get("full_name", ""),
        repository_id=repository.get("id", 0),
        sender_login=sender.get("login", "unknown"),
        is_draft=pull_request.get("draft", False)
    )


# ============================================================================
# GitHub API: Status Checks
# ============================================================================

async def post_commit_status(
    token: str,
    repo_full_name: str,
    commit_sha: str,
    state: CheckStatus,
    description: str,
    target_url: Optional[str] = None,
    context: str = "SDLC Orchestrator / Compliance"
) -> Dict[str, Any]:
    """
    Post commit status check to GitHub.

    Args:
        token: GitHub installation access token
        repo_full_name: Repository full name (owner/repo)
        commit_sha: Commit SHA to update
        state: Check state (pending, success, failure, error)
        description: Status description (max 140 chars)
        target_url: URL to compliance report (optional)
        context: Status context identifier

    Returns:
        GitHub API response

    Raises:
        httpx.HTTPError: If API request fails

    Example:
        >>> await post_commit_status(
        ...     token="ghs_xxx",
        ...     repo_full_name="owner/repo",
        ...     commit_sha="abc123",
        ...     state=CheckStatus.SUCCESS,
        ...     description="SDLC compliance: 100% (0 violations)"
        ... )
    """
    # Truncate description to 140 chars (GitHub limit)
    if len(description) > 140:
        description = description[:137] + "..."

    payload = {
        "state": state.value,
        "description": description,
        "context": context
    }

    if target_url:
        payload["target_url"] = target_url

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GITHUB_API_BASE_URL}/repos/{repo_full_name}/statuses/{commit_sha}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": GITHUB_API_VERSION
            },
            json=payload,
            timeout=30.0
        )

        response.raise_for_status()
        logger.info(f"Posted status {state.value} to {repo_full_name}@{commit_sha[:7]}")
        return response.json()


async def post_pr_comment(
    token: str,
    repo_full_name: str,
    pr_number: int,
    body: str
) -> Dict[str, Any]:
    """
    Post comment on a pull request.

    Args:
        token: GitHub installation access token
        repo_full_name: Repository full name (owner/repo)
        pr_number: Pull request number
        body: Comment body (Markdown supported)

    Returns:
        GitHub API response

    Raises:
        httpx.HTTPError: If API request fails
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GITHUB_API_BASE_URL}/repos/{repo_full_name}/issues/{pr_number}/comments",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": GITHUB_API_VERSION
            },
            json={"body": body},
            timeout=30.0
        )

        response.raise_for_status()
        logger.info(f"Posted comment to {repo_full_name}#{pr_number}")
        return response.json()


def format_compliance_comment(result: ComplianceResult, report_url: Optional[str] = None) -> str:
    """
    Format compliance result as Markdown comment.

    Args:
        result: Compliance check result
        report_url: URL to full compliance report

    Returns:
        Markdown-formatted comment body
    """
    # Header with score
    if result.score >= 90:
        status_emoji = "✅"
        status_text = "Passed"
    elif result.score >= 70:
        status_emoji = "⚠️"
        status_text = "Warning"
    else:
        status_emoji = "❌"
        status_text = "Failed"

    lines = [
        f"## {status_emoji} SDLC Compliance Report",
        "",
        f"**Score**: {result.score}% | **Status**: {status_text} | **Violations**: {result.violations_count}",
        ""
    ]

    # Group violations by gate
    if result.violations:
        violations_by_gate: Dict[str, List[Dict[str, Any]]] = {}
        for v in result.violations:
            gate = v.get("gate", "Unknown")
            if gate not in violations_by_gate:
                violations_by_gate[gate] = []
            violations_by_gate[gate].append(v)

        for gate, violations in sorted(violations_by_gate.items()):
            severity_emoji = "❌" if any(v.get("severity") == "HIGH" for v in violations) else "⚠️"
            lines.append(f"<details>")
            lines.append(f"<summary>{severity_emoji} {gate} Violations ({len(violations)})</summary>")
            lines.append("")
            lines.append("| Severity | Rule | File | Line |")
            lines.append("|----------|------|------|------|")

            for v in violations:
                severity = v.get("severity", "MEDIUM")
                rule = v.get("rule", "Unknown rule")
                file = v.get("file", "-")
                line = v.get("line", "-")
                lines.append(f"| {severity} | {rule} | {file} | {line} |")

            lines.append("")
            lines.append("</details>")
            lines.append("")

    # Footer with link
    lines.append("---")
    if report_url:
        lines.append(f"**View full report**: [{report_url}]({report_url})")
    lines.append("")
    lines.append("*Generated by [SDLC Orchestrator](https://sdlc.nhatquangholding.com)*")

    return "\n".join(lines)


# ============================================================================
# Event Handlers
# ============================================================================

async def handle_push_event(
    payload: WebhookPayload,
    db_session=None
) -> Dict[str, Any]:
    """
    Handle push webhook event.

    Triggers gap analysis for the pushed branch.

    Args:
        payload: Parsed webhook payload
        db_session: Optional database session

    Returns:
        Processing result

    Flow:
    1. Parse push event data
    2. Find linked project by repository ID
    3. Enqueue gap analysis job
    4. Return job ID for tracking
    """
    try:
        push_data = parse_push_event(payload.raw_payload)

        # Skip if deleting branch (after = 0000000...)
        if push_data.after == "0" * 40:
            logger.info(f"Ignoring branch deletion: {push_data.ref}")
            return {
                "status": "skipped",
                "reason": "branch_deleted",
                "ref": push_data.ref
            }

        # Extract branch name from ref (refs/heads/main -> main)
        branch = push_data.ref.replace("refs/heads/", "")

        logger.info(
            f"Push event: {push_data.repository_full_name}@{branch} "
            f"({len(push_data.commits)} commits by {push_data.pusher_name})"
        )

        # TODO: Find linked project and enqueue gap analysis job
        # This will be implemented when connecting to the job system
        # job_id = enqueue_gap_analysis(
        #     repository_id=push_data.repository_id,
        #     branch=branch,
        #     commit_sha=push_data.after
        # )

        return {
            "status": "accepted",
            "event": "push",
            "repository": push_data.repository_full_name,
            "branch": branch,
            "commits_count": len(push_data.commits),
            "head_sha": push_data.after
            # "job_id": job_id  # Will be added when job system integrated
        }

    except ValueError as e:
        logger.error(f"Failed to parse push event: {e}")
        return {
            "status": "error",
            "event": "push",
            "error": str(e)
        }


async def handle_pull_request_event(
    payload: WebhookPayload,
    db_session=None
) -> Dict[str, Any]:
    """
    Handle pull_request webhook event.

    Triggers gate evaluation and posts status check.

    Args:
        payload: Parsed webhook payload
        db_session: Optional database session

    Returns:
        Processing result

    Flow:
    1. Parse PR event data
    2. Check if action requires processing (opened, synchronize, reopened)
    3. Find linked project by repository ID
    4. Enqueue gate evaluation job
    5. Post "pending" status check immediately
    6. Return job ID for tracking
    """
    try:
        pr_data = parse_pull_request_event(payload.raw_payload)

        # Only process certain actions
        processable_actions = [
            PullRequestAction.OPENED.value,
            PullRequestAction.SYNCHRONIZE.value,
            PullRequestAction.REOPENED.value
        ]

        if pr_data.action not in processable_actions:
            logger.info(f"Skipping PR action: {pr_data.action}")
            return {
                "status": "skipped",
                "reason": f"action_{pr_data.action}_not_processable",
                "pr_number": pr_data.pr_number
            }

        # Skip draft PRs
        if pr_data.is_draft:
            logger.info(f"Skipping draft PR: #{pr_data.pr_number}")
            return {
                "status": "skipped",
                "reason": "draft_pr",
                "pr_number": pr_data.pr_number
            }

        logger.info(
            f"PR event: {pr_data.repository_full_name}#{pr_data.pr_number} "
            f"({pr_data.action}) - {pr_data.pr_title}"
        )

        # TODO: Post pending status and enqueue gate evaluation
        # token = await get_installation_token(payload.installation_id)
        # await post_commit_status(
        #     token=token,
        #     repo_full_name=pr_data.repository_full_name,
        #     commit_sha=pr_data.head_sha,
        #     state=CheckStatus.PENDING,
        #     description="Running SDLC compliance check..."
        # )
        #
        # job_id = enqueue_gate_evaluation(
        #     repository_id=pr_data.repository_id,
        #     pr_number=pr_data.pr_number,
        #     head_sha=pr_data.head_sha
        # )

        return {
            "status": "accepted",
            "event": "pull_request",
            "action": pr_data.action,
            "repository": pr_data.repository_full_name,
            "pr_number": pr_data.pr_number,
            "head_sha": pr_data.head_sha
            # "job_id": job_id  # Will be added when job system integrated
        }

    except ValueError as e:
        logger.error(f"Failed to parse pull_request event: {e}")
        return {
            "status": "error",
            "event": "pull_request",
            "error": str(e)
        }


async def handle_installation_event(
    payload: WebhookPayload,
    db_session=None
) -> Dict[str, Any]:
    """
    Handle installation webhook event.

    Manages GitHub App install/uninstall/suspend/unsuspend events.

    Args:
        payload: Parsed webhook payload
        db_session: Optional database session

    Returns:
        Processing result
    """
    action = payload.action
    installation_id = payload.installation_id
    account = payload.raw_payload.get("installation", {}).get("account", {})
    account_login = account.get("login", "unknown")

    logger.info(f"Installation event: {action} for {account_login} (id: {installation_id})")

    if action == "created":
        # New installation - record will be created when user links a repo
        return {
            "status": "acknowledged",
            "action": "created",
            "installation_id": installation_id,
            "account": account_login
        }

    elif action == "deleted":
        # Uninstall - mark installation and unlink projects
        # TODO: Update database when db_session available
        return {
            "status": "acknowledged",
            "action": "deleted",
            "installation_id": installation_id,
            "account": account_login
        }

    elif action in ("suspend", "unsuspend"):
        # Suspend/unsuspend - update installation status
        return {
            "status": "acknowledged",
            "action": action,
            "installation_id": installation_id,
            "account": account_login
        }

    else:
        return {
            "status": "ignored",
            "action": action,
            "reason": "unknown_action"
        }


# ============================================================================
# Main Webhook Handler
# ============================================================================

async def process_webhook(
    event_type: str,
    delivery_id: str,
    payload: Dict[str, Any],
    db_session=None
) -> Dict[str, Any]:
    """
    Main webhook processing function.

    Orchestrates validation, idempotency check, and event handling.

    Args:
        event_type: X-GitHub-Event header value
        delivery_id: X-GitHub-Delivery header value
        payload: Parsed JSON payload
        db_session: Optional database session

    Returns:
        Processing result with status and event details

    Flow:
    1. Check idempotency (skip if duplicate)
    2. Parse payload
    3. Route to event-specific handler
    4. Mark as processed
    5. Return result
    """
    # Check idempotency
    idempotency_service = get_idempotency_service()

    if idempotency_service.is_duplicate(delivery_id):
        logger.info(f"Duplicate webhook: {delivery_id} (event: {event_type})")
        return {
            "status": "duplicate",
            "delivery_id": delivery_id,
            "message": "Webhook already processed"
        }

    # Parse payload
    webhook_payload = parse_webhook_payload(event_type, delivery_id, payload)

    # Route to handler
    result: Dict[str, Any]

    if event_type == WebhookEventType.PUSH.value:
        result = await handle_push_event(webhook_payload, db_session)

    elif event_type == WebhookEventType.PULL_REQUEST.value:
        result = await handle_pull_request_event(webhook_payload, db_session)

    elif event_type == WebhookEventType.INSTALLATION.value:
        result = await handle_installation_event(webhook_payload, db_session)

    elif event_type == WebhookEventType.PING.value:
        logger.info("Received ping event")
        result = {"status": "pong", "event": "ping"}

    else:
        logger.info(f"Ignoring unsupported event: {event_type}")
        result = {
            "status": "ignored",
            "event": event_type,
            "reason": "unsupported_event"
        }

    # Mark as processed (only for non-duplicate, non-ignored events)
    if result.get("status") not in ("duplicate", "ignored"):
        idempotency_service.mark_processed(delivery_id, event_type)

    return result
