"""
Usage Tracking Service - Sprint 24 Day 4

Service for tracking and analyzing user activity:
- Session management
- Event tracking
- Feature usage aggregation
- Pilot metrics calculation
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage_tracking import (
    UserSession,
    UsageEvent,
    FeatureUsage,
    PilotMetrics,
    EventType,
)


class UsageTrackingService:
    """Service for tracking user activity and generating analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Session Management
    # =========================================================================

    async def start_session(
        self,
        user_id: UUID,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> UserSession:
        """
        Start a new user session.

        Args:
            user_id: ID of the user
            user_agent: Browser user agent string
            ip_address: Client IP address

        Returns:
            Created UserSession
        """
        # Parse user agent for device info
        device_info = self._parse_user_agent(user_agent)

        session = UserSession(
            user_id=user_id,
            session_token=secrets.token_urlsafe(32),
            started_at=datetime.utcnow(),
            is_active=True,
            user_agent=user_agent,
            ip_address=ip_address,
            device_type=device_info.get("device_type"),
            browser=device_info.get("browser"),
            os=device_info.get("os"),
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        # Track session start event
        await self.track_event(
            user_id=user_id,
            session_id=session.id,
            event_type=EventType.SESSION_START,
            event_name="session_started",
        )

        return session

    async def end_session(self, session_id: UUID) -> Optional[UserSession]:
        """
        End a user session.

        Args:
            session_id: ID of the session to end

        Returns:
            Updated UserSession or None if not found
        """
        result = await self.db.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        now = datetime.utcnow()
        session.ended_at = now
        session.is_active = False
        session.duration_seconds = int((now - session.started_at).total_seconds())

        await self.db.commit()
        await self.db.refresh(session)

        # Track session end event
        await self.track_event(
            user_id=session.user_id,
            session_id=session.id,
            event_type=EventType.SESSION_END,
            event_name="session_ended",
            metadata={"duration_seconds": session.duration_seconds},
        )

        return session

    async def get_active_session(self, user_id: UUID) -> Optional[UserSession]:
        """Get the active session for a user."""
        result = await self.db.execute(
            select(UserSession).where(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
            ).order_by(UserSession.started_at.desc())
        )
        return result.scalar_one_or_none()

    # =========================================================================
    # Event Tracking
    # =========================================================================

    async def track_event(
        self,
        user_id: UUID,
        event_type: EventType | str,
        event_name: str,
        session_id: Optional[UUID] = None,
        page_url: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        metadata: Optional[dict] = None,
        duration_ms: Optional[int] = None,
    ) -> UsageEvent:
        """
        Track a usage event.

        Args:
            user_id: ID of the user
            event_type: Type of event (from EventType enum)
            event_name: Name of the event
            session_id: Associated session ID
            page_url: URL where event occurred
            resource_type: Type of resource being accessed
            resource_id: ID of the resource
            metadata: Additional event data
            duration_ms: Duration of action in milliseconds

        Returns:
            Created UsageEvent
        """
        event_type_str = event_type.value if isinstance(event_type, EventType) else event_type

        event = UsageEvent(
            user_id=user_id,
            session_id=session_id,
            event_type=event_type_str,
            event_name=event_name,
            timestamp=datetime.utcnow(),
            page_url=page_url,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata,
            duration_ms=duration_ms,
        )

        self.db.add(event)

        # Update session event count if session exists
        if session_id:
            result = await self.db.execute(
                select(UserSession).where(UserSession.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                session.events_count = (session.events_count or 0) + 1
                if event_type_str == EventType.PAGE_VIEW.value:
                    session.page_views_count = (session.page_views_count or 0) + 1

        await self.db.commit()
        await self.db.refresh(event)

        return event

    async def track_page_view(
        self,
        user_id: UUID,
        page_url: str,
        session_id: Optional[UUID] = None,
        referrer_url: Optional[str] = None,
    ) -> UsageEvent:
        """Track a page view event."""
        return await self.track_event(
            user_id=user_id,
            session_id=session_id,
            event_type=EventType.PAGE_VIEW,
            event_name="page_viewed",
            page_url=page_url,
            metadata={"referrer": referrer_url} if referrer_url else None,
        )

    async def track_feature_use(
        self,
        user_id: UUID,
        feature_name: str,
        session_id: Optional[UUID] = None,
        success: bool = True,
        duration_ms: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> UsageEvent:
        """Track feature usage."""
        event_metadata = metadata or {}
        event_metadata["success"] = success

        return await self.track_event(
            user_id=user_id,
            session_id=session_id,
            event_type=EventType.FEATURE_USE,
            event_name=feature_name,
            duration_ms=duration_ms,
            metadata=event_metadata,
        )

    # =========================================================================
    # Analytics & Aggregation
    # =========================================================================

    async def get_user_activity(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[UsageEvent]:
        """Get recent activity for a user."""
        query = select(UsageEvent).where(UsageEvent.user_id == user_id)

        if start_date:
            query = query.where(UsageEvent.timestamp >= start_date)
        if end_date:
            query = query.where(UsageEvent.timestamp <= end_date)

        query = query.order_by(UsageEvent.timestamp.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_feature_usage_stats(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """Get aggregated feature usage statistics."""
        # Count events by type
        result = await self.db.execute(
            select(
                UsageEvent.event_name,
                func.count(UsageEvent.id).label("count"),
                func.count(distinct(UsageEvent.user_id)).label("unique_users"),
                func.avg(UsageEvent.duration_ms).label("avg_duration"),
            )
            .where(
                UsageEvent.timestamp >= start_date,
                UsageEvent.timestamp <= end_date,
                UsageEvent.event_type == EventType.FEATURE_USE.value,
            )
            .group_by(UsageEvent.event_name)
        )

        features = {}
        for row in result.all():
            features[row.event_name] = {
                "total_uses": row.count,
                "unique_users": row.unique_users,
                "avg_duration_ms": int(row.avg_duration) if row.avg_duration else None,
            }

        return features

    async def calculate_pilot_metrics(self, date: datetime) -> PilotMetrics:
        """
        Calculate pilot metrics for a specific date.

        Args:
            date: Date to calculate metrics for

        Returns:
            PilotMetrics for the date
        """
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # Check if metrics already exist for this date
        existing = await self.db.execute(
            select(PilotMetrics).where(
                func.date(PilotMetrics.date) == start_of_day.date()
            )
        )
        metrics = existing.scalar_one_or_none()

        if not metrics:
            metrics = PilotMetrics(date=start_of_day)
            self.db.add(metrics)

        # Calculate user metrics
        from app.models.user import User

        total_users = await self.db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        metrics.total_users = total_users.scalar() or 0

        active_users = await self.db.execute(
            select(func.count(distinct(UsageEvent.user_id))).where(
                UsageEvent.timestamp >= start_of_day,
                UsageEvent.timestamp < end_of_day,
            )
        )
        metrics.active_users = active_users.scalar() or 0

        # Session metrics
        sessions = await self.db.execute(
            select(
                func.count(UserSession.id),
                func.avg(UserSession.duration_seconds),
            ).where(
                UserSession.started_at >= start_of_day,
                UserSession.started_at < end_of_day,
            )
        )
        session_row = sessions.one()
        metrics.total_sessions = session_row[0] or 0
        metrics.avg_session_duration = int(session_row[1]) if session_row[1] else 0

        # Page views
        page_views = await self.db.execute(
            select(func.count(UsageEvent.id)).where(
                UsageEvent.timestamp >= start_of_day,
                UsageEvent.timestamp < end_of_day,
                UsageEvent.event_type == EventType.PAGE_VIEW.value,
            )
        )
        metrics.total_page_views = page_views.scalar() or 0

        # Feature adoption - users using specific features
        for feature, field in [
            (EventType.GATE_VIEW.value, "users_using_gates"),
            (EventType.EVIDENCE_UPLOAD.value, "users_using_evidence"),
            (EventType.COMPLIANCE_VIEW.value, "users_using_compliance"),
        ]:
            count = await self.db.execute(
                select(func.count(distinct(UsageEvent.user_id))).where(
                    UsageEvent.timestamp >= start_of_day,
                    UsageEvent.timestamp < end_of_day,
                    UsageEvent.event_type == feature,
                )
            )
            setattr(metrics, field, count.scalar() or 0)

        # Gate metrics
        gate_evals = await self.db.execute(
            select(func.count(UsageEvent.id)).where(
                UsageEvent.timestamp >= start_of_day,
                UsageEvent.timestamp < end_of_day,
                UsageEvent.event_type == EventType.GATE_EVALUATE.value,
            )
        )
        metrics.gates_evaluated = gate_evals.scalar() or 0

        # Evidence metrics
        evidence_uploads = await self.db.execute(
            select(func.count(UsageEvent.id)).where(
                UsageEvent.timestamp >= start_of_day,
                UsageEvent.timestamp < end_of_day,
                UsageEvent.event_type == EventType.EVIDENCE_UPLOAD.value,
            )
        )
        metrics.evidence_uploaded = evidence_uploads.scalar() or 0

        # Compliance scans
        compliance_scans = await self.db.execute(
            select(func.count(UsageEvent.id)).where(
                UsageEvent.timestamp >= start_of_day,
                UsageEvent.timestamp < end_of_day,
                UsageEvent.event_type == EventType.COMPLIANCE_SCAN.value,
            )
        )
        metrics.compliance_scans = compliance_scans.scalar() or 0

        # Feedback metrics
        from app.models.feedback import PilotFeedback, FeedbackType

        feedback_count = await self.db.execute(
            select(func.count(PilotFeedback.id)).where(
                PilotFeedback.created_at >= start_of_day,
                PilotFeedback.created_at < end_of_day,
            )
        )
        metrics.feedback_submitted = feedback_count.scalar() or 0

        bugs = await self.db.execute(
            select(func.count(PilotFeedback.id)).where(
                PilotFeedback.created_at >= start_of_day,
                PilotFeedback.created_at < end_of_day,
                PilotFeedback.type == FeedbackType.BUG,
            )
        )
        metrics.bugs_reported = bugs.scalar() or 0

        feature_requests = await self.db.execute(
            select(func.count(PilotFeedback.id)).where(
                PilotFeedback.created_at >= start_of_day,
                PilotFeedback.created_at < end_of_day,
                PilotFeedback.type == FeedbackType.FEATURE_REQUEST,
            )
        )
        metrics.features_requested = feature_requests.scalar() or 0

        await self.db.commit()
        await self.db.refresh(metrics)

        return metrics

    async def get_pilot_metrics_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[PilotMetrics]:
        """Get pilot metrics for a date range."""
        result = await self.db.execute(
            select(PilotMetrics)
            .where(
                PilotMetrics.date >= start_date,
                PilotMetrics.date <= end_date,
            )
            .order_by(PilotMetrics.date)
        )
        return list(result.scalars().all())

    async def get_engagement_summary(self) -> dict:
        """Get current engagement summary for dashboard."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        # Today's active users
        today_active = await self.db.execute(
            select(func.count(distinct(UsageEvent.user_id))).where(
                UsageEvent.timestamp >= today_start
            )
        )

        # This week's active users
        week_active = await self.db.execute(
            select(func.count(distinct(UsageEvent.user_id))).where(
                UsageEvent.timestamp >= week_start
            )
        )

        # Total sessions today
        today_sessions = await self.db.execute(
            select(func.count(UserSession.id)).where(
                UserSession.started_at >= today_start
            )
        )

        # Average session duration (last 7 days)
        avg_duration = await self.db.execute(
            select(func.avg(UserSession.duration_seconds)).where(
                UserSession.started_at >= week_start,
                UserSession.duration_seconds.isnot(None),
            )
        )

        # Most used features (last 7 days)
        top_features = await self.db.execute(
            select(
                UsageEvent.event_name,
                func.count(UsageEvent.id).label("count"),
            )
            .where(
                UsageEvent.timestamp >= week_start,
                UsageEvent.event_type == EventType.FEATURE_USE.value,
            )
            .group_by(UsageEvent.event_name)
            .order_by(func.count(UsageEvent.id).desc())
            .limit(5)
        )

        return {
            "today_active_users": today_active.scalar() or 0,
            "week_active_users": week_active.scalar() or 0,
            "today_sessions": today_sessions.scalar() or 0,
            "avg_session_duration_seconds": int(avg_duration.scalar() or 0),
            "top_features": [
                {"name": row.event_name, "count": row.count}
                for row in top_features.all()
            ],
        }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _parse_user_agent(self, user_agent: Optional[str]) -> dict:
        """Parse user agent string for device info."""
        if not user_agent:
            return {}

        result = {
            "device_type": "desktop",
            "browser": "unknown",
            "os": "unknown",
        }

        ua_lower = user_agent.lower()

        # Device type
        if "mobile" in ua_lower or "android" in ua_lower:
            result["device_type"] = "mobile"
        elif "tablet" in ua_lower or "ipad" in ua_lower:
            result["device_type"] = "tablet"

        # Browser
        if "chrome" in ua_lower and "edg" not in ua_lower:
            result["browser"] = "Chrome"
        elif "firefox" in ua_lower:
            result["browser"] = "Firefox"
        elif "safari" in ua_lower and "chrome" not in ua_lower:
            result["browser"] = "Safari"
        elif "edg" in ua_lower:
            result["browser"] = "Edge"

        # OS
        if "windows" in ua_lower:
            result["os"] = "Windows"
        elif "mac os" in ua_lower or "macos" in ua_lower:
            result["os"] = "macOS"
        elif "linux" in ua_lower:
            result["os"] = "Linux"
        elif "android" in ua_lower:
            result["os"] = "Android"
        elif "ios" in ua_lower or "iphone" in ua_lower:
            result["os"] = "iOS"

        return result


async def get_usage_tracking_service(db: AsyncSession) -> UsageTrackingService:
    """Factory function for UsageTrackingService."""
    return UsageTrackingService(db)
