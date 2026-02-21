"""
==========================================================================
UsageAlertService — Sprint 188 Overage Alert Emails
SDLC Orchestrator — Tier Enforcement Layer

Purpose:
- Detect when users cross 80% of their tier limits across 4 dimensions:
    1. projects      (max_projects)
    2. storage_mb    (max_storage_mb)
    3. gates/month   (max_gates_per_month)
    4. team_members  (max_team_members)
- Send a single warning email per metric per day (Redis dedup, 23h TTL)
- Provide a background sweep to alert all ACTIVE LITE/STANDARD users

Architecture:
- Stateless — no persistent objects; call check_and_send_overage_alerts()
- Deduplication: Redis key `usage_alert:{user_id}:{metric}:{iso_date}` TTL 23h
  Falls back to an in-process LRU dict when Redis is unavailable (best-effort,
  process-local only — acceptable for a low-traffic alert path)
- Email: uses send_email() from email_service.py (Gmail SMTP / SendGrid)
  If neither is configured, warning is logged with a clear comment so the
  on-call engineer knows exactly where to wire the real email.
- Fail-open on Redis and email errors: a failed alert never raises to the caller

Metrics → TIER_LIMITS key mapping:
    "projects"          → "max_projects"         (UsageService: project_count)
    "storage_mb"        → "max_storage_mb"        (UsageService: storage_mb)
    "gates_this_month"  → "max_gates_per_month"   (UsageService: gates_this_month)
    "team_members"      → "max_team_members"       (UsageService: team_members)

SDLC 6.1.0 — Sprint 188 P0 Deliverable
Authority: CTO + Backend Lead Approved
==========================================================================
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.usage_limits import TIER_LIMITS
from app.services.email_service import FROM_EMAIL, FROM_NAME, send_email
from app.services.usage_service import UsageService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Threshold at which we fire the overage alert (80 %)
ALERT_THRESHOLD = 0.80

# Redis TTL for dedup key (23 hours in seconds — gives a small window for
# retry within the same calendar day after a transient failure)
_DEDUP_TTL_SECONDS = 23 * 3600

# Upgrade call-to-action URL embedded in every alert email
UPGRADE_URL = "https://app.sdlcorchestrator.com/pricing"

# Map internal metric names (as returned by UsageService.get_all) to
# the corresponding TIER_LIMITS key and a human-readable display label.
_METRIC_META: dict[str, dict[str, str]] = {
    "project_count": {
        "limit_key": "max_projects",
        "label": "Projects",
    },
    "storage_mb": {
        "limit_key": "max_storage_mb",
        "label": "Storage",
    },
    "gates_this_month": {
        "limit_key": "max_gates_per_month",
        "label": "Gates (this month)",
    },
    "team_members": {
        "limit_key": "max_team_members",
        "label": "Team Members",
    },
}

# In-process fallback dedup store (process-local; used when Redis unavailable)
# Key: "{user_id}:{metric}:{iso_date}", Value: True
_local_dedup: dict[str, bool] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def check_and_send_overage_alerts(
    user: Any,
    db: AsyncSession,
) -> list[dict[str, Any]]:
    """
    Evaluate the user's current resource consumption and send alert emails
    for any metric that has crossed 80 % of its tier limit.

    Each unique (user, metric, calendar-day) combination is alerted at most
    once per 23 hours thanks to a Redis dedup key.  If Redis is unavailable
    the dedup falls back to an in-process dict (best-effort, process-local).

    Args:
        user: SQLAlchemy User ORM instance with at least:
              - id (UUID)
              - email (str)
              - full_name (str | None)
              - effective_tier (str property)
              - is_active (bool)
        db:   Open AsyncSession (caller-managed transaction scope)

    Returns:
        List of result dicts, one per checked metric:
        [
            {
                "metric": "storage_mb",
                "current": 88.4,
                "max": 100,
                "pct": 88.4,
                "alerted": True,   # email was sent (or attempted)
                "skipped_dedup": False,
            },
            ...
        ]

    Example:
        results = await check_and_send_overage_alerts(user, db)
        triggered = [r for r in results if r["alerted"]]
    """
    # Resolve tier — effective_tier is a property on the User model (Sprint 58+)
    raw_tier: str = getattr(user, "effective_tier", "lite") or "lite"
    tier = raw_tier.lower().strip()
    limits: dict[str, int | float] = TIER_LIMITS.get(tier, TIER_LIMITS["lite"])

    # Fetch all four usage dimensions in one call
    usage: dict[str, int | float] = await UsageService.get_all(db, user.id)

    today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    results: list[dict[str, Any]] = []

    for metric_name, meta in _METRIC_META.items():
        limit_key = meta["limit_key"]
        label = meta["label"]

        max_val: int | float = limits.get(limit_key, -1)
        current: int | float = usage.get(metric_name, 0)

        # -1 means unlimited for this tier → skip
        if max_val < 0:
            logger.debug(
                "UsageAlertService: metric=%s tier=%s unlimited → skipping user=%s",
                metric_name, tier, user.id,
            )
            continue

        pct: float = (float(current) / float(max_val)) * 100.0 if max_val > 0 else 0.0

        result: dict[str, Any] = {
            "metric": metric_name,
            "current": current,
            "max": max_val,
            "pct": round(pct, 1),
            "alerted": False,
            "skipped_dedup": False,
        }

        if pct < ALERT_THRESHOLD * 100:
            # Below threshold — no action needed
            results.append(result)
            continue

        # ----------------------------------------------------------------
        # Deduplication check — skip if already alerted today
        # ----------------------------------------------------------------
        dedup_key = f"usage_alert:{user.id}:{metric_name}:{today_iso}"
        already_sent = await _dedup_check(dedup_key)
        if already_sent:
            logger.debug(
                "UsageAlertService: dedup hit key=%s user=%s → suppressing",
                dedup_key, user.id,
            )
            result["skipped_dedup"] = True
            results.append(result)
            continue

        # ----------------------------------------------------------------
        # Build and send the alert email
        # ----------------------------------------------------------------
        html_body = _build_alert_html(
            user_display_name=getattr(user, "full_name", None) or user.email,
            label=label,
            current=current,
            max_val=max_val,
            pct=pct,
            tier=tier,
        )
        subject = f"Action Required: You're at {pct:.0f}% of your {label} limit"

        email_sent = _attempt_send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_body,
        )

        if email_sent:
            # Record dedup key so we don't send again today
            await _dedup_mark(dedup_key, ttl=_DEDUP_TTL_SECONDS)
            result["alerted"] = True
            logger.info(
                "UsageAlertService: alert sent user=%s metric=%s pct=%.1f tier=%s",
                user.id, metric_name, pct, tier,
            )
        else:
            # Email failure — do NOT set dedup key; allow retry on next sweep
            logger.warning(
                "UsageAlertService: email delivery failed user=%s metric=%s — will retry",
                user.id, metric_name,
            )

        results.append(result)

    return results


async def run_usage_alerts_for_all_users(db: AsyncSession) -> dict[str, Any]:
    """
    Background sweep: find all ACTIVE LITE/STANDARD users and call
    check_and_send_overage_alerts for each.

    Intended to be called by a scheduled job (e.g. APScheduler, Celery beat,
    or a FastAPI background task triggered from a cron endpoint).

    LITE and STANDARD tiers are the only ones with finite limits that
    meaningfully trigger overage alerts:
        - LITE:     1 project, 100 MB, 4 gates/month, 1 member
        - STANDARD: 15 projects, 50 GB, unlimited gates, 30 members
    PRO / ENTERPRISE have very high or unlimited limits; FOUNDER overlaps
    with STANDARD and is included for completeness.

    Args:
        db: Open AsyncSession (caller-managed)

    Returns:
        Summary dict:
        {
            "users_checked": 12,
            "alerts_sent": 3,
            "errors": 0,
        }
    """
    from app.models.subscription import Subscription, SubscriptionStatus
    from app.models.user import User

    # Tiers that have restrictive finite limits — adjust list if tier taxonomy changes
    _ALERTED_TIERS = ("lite", "standard", "founder", "starter")

    # Join users → subscriptions to filter by active plan + user is_active
    stmt = (
        select(User)
        .join(Subscription, Subscription.user_id == User.id, isouter=True)
        .where(
            User.is_active.is_(True),
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.plan.in_(_ALERTED_TIERS),
        )
        .distinct()
    )

    result = await db.execute(stmt)
    users = result.scalars().all()

    users_checked = 0
    alerts_sent = 0
    errors = 0

    for user in users:
        try:
            alert_results = await check_and_send_overage_alerts(user, db)
            users_checked += 1
            alerts_sent += sum(1 for r in alert_results if r.get("alerted"))
        except Exception as exc:  # noqa: BLE001
            errors += 1
            logger.error(
                "UsageAlertService: sweep error for user=%s: %s",
                getattr(user, "id", "unknown"), exc,
            )

    logger.info(
        "UsageAlertService: sweep complete checked=%d alerts_sent=%d errors=%d",
        users_checked, alerts_sent, errors,
    )
    return {
        "users_checked": users_checked,
        "alerts_sent": alerts_sent,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Private helpers — email
# ---------------------------------------------------------------------------


def _attempt_send_email(
    to_email: str,
    subject: str,
    html_content: str,
) -> bool:
    """
    Call send_email() from email_service and return True on success.

    Any exception is caught and logged — alert failures must never crash
    the background sweep or the route handler that triggered the check.

    If no email provider is configured (sandbox mode / missing env vars),
    email_service.send_email() logs a warning internally.  We treat that
    as a soft-success (returns True) so the dedup key is still written and
    we don't spam logs on every sweep run in a no-email-config dev env.

    WIRING NOTE:
    -----------
    To connect a real email provider, set one of these env vars:
        EMAIL_PROVIDER=gmail  + GMAIL_EMAIL + GMAIL_APP_PASSWORD
        EMAIL_PROVIDER=sendgrid + SENDGRID_API_KEY
    See backend/app/services/email_service.py for full configuration.

    Args:
        to_email:     Recipient address
        subject:      Email subject line
        html_content: HTML body

    Returns:
        True if the send call completed without raising; False on exception.
    """
    try:
        send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            from_email=FROM_EMAIL,
            from_name=FROM_NAME,
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "UsageAlertService: send_email raised for %s: %s",
            to_email, exc,
        )
        return False


def _build_alert_html(
    user_display_name: str,
    label: str,
    current: int | float,
    max_val: int | float,
    pct: float,
    tier: str,
) -> str:
    """
    Render the HTML overage alert email body.

    Args:
        user_display_name: First name or email for greeting
        label:             Human-readable metric name (e.g. "Storage")
        current:           Current consumption value
        max_val:           Tier limit value
        pct:               Percentage consumed (0–100)
        tier:              Canonical tier string (e.g. "lite")

    Returns:
        Fully-formed HTML string safe to embed in a MIMEText part.
    """
    # HTML-escape user-controlled strings to prevent injection
    safe_name = _html_escape(user_display_name)
    safe_label = _html_escape(label)
    safe_tier = _html_escape(tier.upper())

    # Format current/max with units where appropriate
    if label == "Storage":
        current_display = f"{current:.1f} MB"
        max_display = f"{max_val:.0f} MB"
    else:
        current_display = str(int(current))
        max_display = str(int(max_val))

    # Colour the progress bar: orange at 80–99 %, red at 100 %
    bar_colour = "#dc3545" if pct >= 100.0 else "#fd7e14"
    bar_width = min(int(pct), 100)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Usage Alert — SDLC Orchestrator</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
             line-height: 1.6; color: #212529; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="background: #fff; border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden;">

    <!-- Header -->
    <div style="background: #fd7e14; color: #fff; padding: 28px 24px; text-align: center;">
      <h1 style="margin: 0; font-size: 24px; font-weight: 600;">Usage Alert</h1>
      <p style="margin: 8px 0 0; font-size: 14px; opacity: 0.9;">SDLC Orchestrator — {safe_tier} Plan</p>
    </div>

    <!-- Body -->
    <div style="padding: 32px 24px;">
      <p style="font-size: 16px; margin: 0 0 20px;">Hi {safe_name},</p>

      <p style="font-size: 16px; margin: 0 0 20px;">
        You are currently using <strong>{pct:.0f}%</strong> of your
        <strong>{safe_label}</strong> limit on the <strong>{safe_tier}</strong> plan.
        Consider upgrading before you reach the ceiling to avoid service disruption.
      </p>

      <!-- Usage card -->
      <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 20px; margin: 0 0 24px;">
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="font-size: 14px; color: #495057; padding: 4px 0; width: 50%;">Metric</td>
            <td style="font-size: 14px; font-weight: 600; text-align: right;">{safe_label}</td>
          </tr>
          <tr>
            <td style="font-size: 14px; color: #495057; padding: 4px 0;">Current usage</td>
            <td style="font-size: 14px; font-weight: 600; text-align: right;">{current_display}</td>
          </tr>
          <tr>
            <td style="font-size: 14px; color: #495057; padding: 4px 0;">Plan limit</td>
            <td style="font-size: 14px; font-weight: 600; text-align: right;">{max_display}</td>
          </tr>
          <tr>
            <td style="font-size: 14px; color: #495057; padding: 4px 0;">Used</td>
            <td style="font-size: 14px; font-weight: 700; color: {bar_colour}; text-align: right;">{pct:.1f}%</td>
          </tr>
        </table>

        <!-- Progress bar -->
        <div style="margin-top: 14px; background: #e9ecef; border-radius: 4px; height: 10px;">
          <div style="width: {bar_width}%; background: {bar_colour}; border-radius: 4px; height: 10px;"></div>
        </div>
      </div>

      <!-- CTA -->
      <div style="text-align: center; margin: 28px 0;">
        <a href="{UPGRADE_URL}"
           style="display: inline-block; background: #0066cc; color: #fff;
                  padding: 14px 32px; text-decoration: none; border-radius: 6px;
                  font-size: 16px; font-weight: 600;">
          Upgrade My Plan
        </a>
      </div>

      <p style="font-size: 13px; color: #6c757d; margin: 0 0 8px;">
        Or copy and paste this URL into your browser:<br>
        <a href="{UPGRADE_URL}" style="color: #0066cc; word-break: break-all;">{UPGRADE_URL}</a>
      </p>
    </div>

    <!-- Footer -->
    <div style="background: #f8f9fa; padding: 20px 24px; text-align: center; border-top: 1px solid #dee2e6;">
      <p style="margin: 0 0 6px; font-size: 13px; color: #6c757d;">
        Sent by <strong>SDLC Orchestrator</strong>
      </p>
      <p style="margin: 0; font-size: 11px; color: #adb5bd;">
        This is an automated notification. Please do not reply to this message.
      </p>
    </div>
  </div>

  <div style="text-align: center; padding: 20px 0; color: #adb5bd; font-size: 11px;">
    SDLC Orchestrator — Operating System for Software 3.0<br>
    &copy; 2026 SDLC Orchestrator. All rights reserved.
  </div>
</body>
</html>"""


def _html_escape(text: str) -> str:
    """Escape HTML special characters to prevent injection in email templates."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


# ---------------------------------------------------------------------------
# Private helpers — Redis dedup
# ---------------------------------------------------------------------------


async def _dedup_check(key: str) -> bool:
    """
    Return True if the dedup key already exists (alert was already sent today).

    Tries Redis first; falls back to the in-process dict on any Redis error.

    Args:
        key: Redis key string (usage_alert:{user_id}:{metric}:{iso_date})

    Returns:
        True if key exists (skip alert), False if key absent (send alert).
    """
    try:
        from app.utils.redis import get_redis_client

        redis = await get_redis_client()
        exists: bool = bool(await redis.exists(key))
        return exists
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "UsageAlertService: Redis dedup_check failed key=%s: %s — using local fallback",
            key, exc,
        )
        return _local_dedup.get(key, False)


async def _dedup_mark(key: str, ttl: int) -> None:
    """
    Set the dedup key with a TTL so the same alert is not sent again today.

    Tries Redis; falls back to in-process dict on failure.

    Args:
        key: Redis key string
        ttl: Time-to-live in seconds (23 hours = 82800)
    """
    try:
        from app.utils.redis import get_redis_client

        redis = await get_redis_client()
        await redis.set(key, "1", ex=ttl, nx=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "UsageAlertService: Redis dedup_mark failed key=%s: %s — using local fallback",
            key, exc,
        )
        # Best-effort in-process dedup for the lifetime of this process
        _local_dedup[key] = True
        # Prevent unbounded growth: evict oldest entries when cache exceeds 10 000 keys
        if len(_local_dedup) > 10_000:
            oldest_keys = list(_local_dedup.keys())[: len(_local_dedup) - 8_000]
            for k in oldest_keys:
                _local_dedup.pop(k, None)
