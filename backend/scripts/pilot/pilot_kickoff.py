"""
Pilot Team Kickoff Management Script
Sprint 122 - Stabilization + Framework 6.1 Planning

Manages pilot team kickoff process:
- Team status tracking
- Kickoff meeting scheduling
- Training material distribution
- Feedback channel setup
- Success metrics collection

Usage:
    python pilot_kickoff.py --team alpha --action kickoff
    python pilot_kickoff.py --all --action status
    python pilot_kickoff.py --team beta --action feedback
"""

import argparse
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PilotStatus(str, Enum):
    """Pilot team status stages."""
    PENDING = "pending"
    ONBOARDED = "onboarded"
    KICKOFF_SCHEDULED = "kickoff_scheduled"
    KICKOFF_COMPLETE = "kickoff_complete"
    TRAINING_IN_PROGRESS = "training_in_progress"
    ACTIVE = "active"
    FEEDBACK_COLLECTED = "feedback_collected"
    GRADUATED = "graduated"


class FeedbackCategory(str, Enum):
    """Feedback categories for pilot teams."""
    USABILITY = "usability"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    GENERAL = "general"


@dataclass
class PilotTeam:
    """Pilot team configuration and status."""
    id: str
    name: str
    company: str
    tier: str
    contact_email: str
    contact_name: str
    status: PilotStatus = PilotStatus.PENDING
    onboarded_at: Optional[datetime] = None
    kickoff_scheduled_at: Optional[datetime] = None
    kickoff_completed_at: Optional[datetime] = None
    training_started_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    feedback_count: int = 0
    satisfaction_score: Optional[float] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class FeedbackItem:
    """Individual feedback item from pilot team."""
    id: str
    team_id: str
    category: FeedbackCategory
    title: str
    description: str
    severity: str  # low, medium, high, critical
    submitted_at: datetime
    submitted_by: str
    status: str = "open"  # open, acknowledged, in_progress, resolved, wont_fix
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None


@dataclass
class KickoffMeeting:
    """Kickoff meeting details."""
    id: str
    team_id: str
    scheduled_at: datetime
    duration_minutes: int = 60
    attendees: List[str] = field(default_factory=list)
    agenda: List[str] = field(default_factory=list)
    meeting_link: Optional[str] = None
    recording_link: Optional[str] = None
    notes: Optional[str] = None
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled


# Pilot team configurations
PILOT_TEAMS: Dict[str, PilotTeam] = {
    "alpha": PilotTeam(
        id="alpha",
        name="Alpha Team",
        company="NHQ Holdings",
        tier="ENTERPRISE",
        contact_email="cto@nhq.com",
        contact_name="Tai Nguyen",
        notes=["Internal flagship team", "Full feature validation", "High SLA requirements"]
    ),
    "beta": PilotTeam(
        id="beta",
        name="Beta Team",
        company="TechViet Solutions",
        tier="PROFESSIONAL",
        contact_email="lead@techviet.vn",
        contact_name="Minh Tran",
        notes=["Mid-size agency", "Multi-project governance", "Strong technical team"]
    ),
    "gamma": PilotTeam(
        id="gamma",
        name="Gamma Team",
        company="StartupHub VN",
        tier="STANDARD",
        contact_email="founder@startuphub.vn",
        contact_name="Linh Pham",
        notes=["Startup accelerator", "High-velocity teams", "Cost-conscious"]
    ),
    "delta": PilotTeam(
        id="delta",
        name="Delta Team",
        company="DataFlow Analytics",
        tier="PROFESSIONAL",
        contact_email="eng@dataflow.io",
        contact_name="Hung Le",
        notes=["Data engineering focus", "Compliance-heavy workflows", "Security priority"]
    ),
    "epsilon": PilotTeam(
        id="epsilon",
        name="Epsilon Team",
        company="MicroSaaS Studio",
        tier="LITE",
        contact_email="solo@microsaas.dev",
        contact_name="An Vo",
        notes=["Solo founder", "Minimal overhead", "Quick iteration cycles"]
    ),
}

# Standard kickoff agenda
KICKOFF_AGENDA = [
    "1. Welcome and introductions (5 min)",
    "2. SDLC Orchestrator overview and value proposition (10 min)",
    "3. Tier-specific features walkthrough (15 min)",
    "4. Dashboard tour and navigation (10 min)",
    "5. GitHub integration setup (10 min)",
    "6. Gates and evidence workflow demo (10 min)",
    "7. Q&A and feedback channels (10 min)",
    "8. Next steps and support contacts (5 min)",
]

# Training materials by tier
TRAINING_MATERIALS = {
    "LITE": [
        "quickstart-guide-lite.pdf",
        "gates-overview.pdf",
        "evidence-basics.pdf",
    ],
    "STANDARD": [
        "quickstart-guide-standard.pdf",
        "gates-overview.pdf",
        "evidence-management.pdf",
        "github-integration.pdf",
        "vibecoding-index-guide.pdf",
    ],
    "PROFESSIONAL": [
        "quickstart-guide-professional.pdf",
        "gates-overview.pdf",
        "evidence-management.pdf",
        "github-integration.pdf",
        "vibecoding-index-guide.pdf",
        "custom-policies-guide.pdf",
        "api-integration-guide.pdf",
    ],
    "ENTERPRISE": [
        "quickstart-guide-enterprise.pdf",
        "gates-overview.pdf",
        "evidence-management.pdf",
        "github-integration.pdf",
        "vibecoding-index-guide.pdf",
        "custom-policies-guide.pdf",
        "api-integration-guide.pdf",
        "sso-configuration.pdf",
        "enterprise-admin-guide.pdf",
        "compliance-reporting.pdf",
    ],
}


class PilotKickoffManager:
    """Manages pilot team kickoff and feedback collection."""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.teams = PILOT_TEAMS.copy()
        self.feedback_items: List[FeedbackItem] = []
        self.meetings: Dict[str, KickoffMeeting] = {}

    async def get_team_status(self, team_id: str) -> Dict[str, Any]:
        """Get current status of a pilot team."""
        if team_id not in self.teams:
            raise ValueError(f"Unknown team: {team_id}")

        team = self.teams[team_id]

        return {
            "team_id": team.id,
            "name": team.name,
            "company": team.company,
            "tier": team.tier,
            "status": team.status.value,
            "contact": {
                "name": team.contact_name,
                "email": team.contact_email,
            },
            "timeline": {
                "onboarded_at": team.onboarded_at.isoformat() if team.onboarded_at else None,
                "kickoff_scheduled_at": team.kickoff_scheduled_at.isoformat() if team.kickoff_scheduled_at else None,
                "kickoff_completed_at": team.kickoff_completed_at.isoformat() if team.kickoff_completed_at else None,
                "training_started_at": team.training_started_at.isoformat() if team.training_started_at else None,
                "activated_at": team.activated_at.isoformat() if team.activated_at else None,
            },
            "metrics": {
                "feedback_count": team.feedback_count,
                "satisfaction_score": team.satisfaction_score,
            },
            "notes": team.notes,
        }

    async def get_all_teams_status(self) -> List[Dict[str, Any]]:
        """Get status of all pilot teams."""
        statuses = []
        for team_id in self.teams:
            status = await self.get_team_status(team_id)
            statuses.append(status)
        return statuses

    async def schedule_kickoff(
        self,
        team_id: str,
        scheduled_at: datetime,
        duration_minutes: int = 60,
        meeting_link: Optional[str] = None,
    ) -> KickoffMeeting:
        """Schedule a kickoff meeting for a team."""
        if team_id not in self.teams:
            raise ValueError(f"Unknown team: {team_id}")

        team = self.teams[team_id]

        meeting = KickoffMeeting(
            id=str(uuid4()),
            team_id=team_id,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            attendees=[team.contact_email, "support@sdlc-orchestrator.io"],
            agenda=KICKOFF_AGENDA.copy(),
            meeting_link=meeting_link or f"https://meet.sdlc-orchestrator.io/{team_id}-kickoff",
        )

        self.meetings[team_id] = meeting
        team.status = PilotStatus.KICKOFF_SCHEDULED
        team.kickoff_scheduled_at = scheduled_at

        logger.info(f"Scheduled kickoff for {team.name} at {scheduled_at}")
        return meeting

    async def complete_kickoff(self, team_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Mark kickoff meeting as complete."""
        if team_id not in self.teams:
            raise ValueError(f"Unknown team: {team_id}")

        team = self.teams[team_id]
        meeting = self.meetings.get(team_id)

        if meeting:
            meeting.status = "completed"
            meeting.notes = notes

        team.status = PilotStatus.KICKOFF_COMPLETE
        team.kickoff_completed_at = datetime.utcnow()

        logger.info(f"Kickoff completed for {team.name}")

        return {
            "team_id": team_id,
            "status": "kickoff_complete",
            "completed_at": team.kickoff_completed_at.isoformat(),
            "next_step": "Start training with provided materials",
        }

    async def start_training(self, team_id: str) -> Dict[str, Any]:
        """Start training phase for a team."""
        if team_id not in self.teams:
            raise ValueError(f"Unknown team: {team_id}")

        team = self.teams[team_id]
        team.status = PilotStatus.TRAINING_IN_PROGRESS
        team.training_started_at = datetime.utcnow()

        materials = TRAINING_MATERIALS.get(team.tier, TRAINING_MATERIALS["STANDARD"])

        logger.info(f"Training started for {team.name}")

        return {
            "team_id": team_id,
            "status": "training_in_progress",
            "started_at": team.training_started_at.isoformat(),
            "materials": materials,
            "tier": team.tier,
        }

    async def activate_team(self, team_id: str) -> Dict[str, Any]:
        """Activate a team for production use."""
        if team_id not in self.teams:
            raise ValueError(f"Unknown team: {team_id}")

        team = self.teams[team_id]
        team.status = PilotStatus.ACTIVE
        team.activated_at = datetime.utcnow()

        logger.info(f"Team {team.name} is now ACTIVE")

        return {
            "team_id": team_id,
            "status": "active",
            "activated_at": team.activated_at.isoformat(),
            "message": f"{team.name} is now active and can use all {team.tier} features",
        }

    async def collect_feedback(
        self,
        team_id: str,
        category: FeedbackCategory,
        title: str,
        description: str,
        severity: str = "medium",
        submitted_by: Optional[str] = None,
    ) -> FeedbackItem:
        """Collect feedback from a pilot team."""
        if team_id not in self.teams:
            raise ValueError(f"Unknown team: {team_id}")

        team = self.teams[team_id]

        feedback = FeedbackItem(
            id=str(uuid4()),
            team_id=team_id,
            category=category,
            title=title,
            description=description,
            severity=severity,
            submitted_at=datetime.utcnow(),
            submitted_by=submitted_by or team.contact_email,
        )

        self.feedback_items.append(feedback)
        team.feedback_count += 1

        logger.info(f"Feedback collected from {team.name}: {title}")

        return feedback

    async def get_feedback_summary(self, team_id: Optional[str] = None) -> Dict[str, Any]:
        """Get feedback summary, optionally filtered by team."""
        if team_id:
            items = [f for f in self.feedback_items if f.team_id == team_id]
        else:
            items = self.feedback_items

        # Categorize feedback
        by_category = {}
        by_severity = {}
        by_status = {}

        for item in items:
            # By category
            cat = item.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

            # By severity
            by_severity[item.severity] = by_severity.get(item.severity, 0) + 1

            # By status
            by_status[item.status] = by_status.get(item.status, 0) + 1

        return {
            "total_items": len(items),
            "by_category": by_category,
            "by_severity": by_severity,
            "by_status": by_status,
            "open_critical": len([f for f in items if f.severity == "critical" and f.status == "open"]),
            "open_high": len([f for f in items if f.severity == "high" and f.status == "open"]),
        }

    async def update_satisfaction_score(self, team_id: str, score: float) -> Dict[str, Any]:
        """Update satisfaction score for a team (1-10 scale)."""
        if team_id not in self.teams:
            raise ValueError(f"Unknown team: {team_id}")

        if not 1 <= score <= 10:
            raise ValueError("Score must be between 1 and 10")

        team = self.teams[team_id]
        team.satisfaction_score = score

        logger.info(f"Satisfaction score for {team.name}: {score}/10")

        return {
            "team_id": team_id,
            "satisfaction_score": score,
            "rating": "excellent" if score >= 8 else "good" if score >= 6 else "needs_improvement",
        }

    async def generate_pilot_report(self) -> Dict[str, Any]:
        """Generate comprehensive pilot program report."""
        teams_by_status = {}
        total_feedback = 0
        avg_satisfaction = 0
        satisfaction_count = 0

        for team in self.teams.values():
            status = team.status.value
            teams_by_status[status] = teams_by_status.get(status, 0) + 1
            total_feedback += team.feedback_count
            if team.satisfaction_score:
                avg_satisfaction += team.satisfaction_score
                satisfaction_count += 1

        if satisfaction_count > 0:
            avg_satisfaction = avg_satisfaction / satisfaction_count

        feedback_summary = await self.get_feedback_summary()

        return {
            "report_date": datetime.utcnow().isoformat(),
            "pilot_program": {
                "total_teams": len(self.teams),
                "teams_by_status": teams_by_status,
                "teams_by_tier": {
                    "ENTERPRISE": len([t for t in self.teams.values() if t.tier == "ENTERPRISE"]),
                    "PROFESSIONAL": len([t for t in self.teams.values() if t.tier == "PROFESSIONAL"]),
                    "STANDARD": len([t for t in self.teams.values() if t.tier == "STANDARD"]),
                    "LITE": len([t for t in self.teams.values() if t.tier == "LITE"]),
                },
            },
            "feedback": {
                "total_items": total_feedback,
                "summary": feedback_summary,
            },
            "satisfaction": {
                "average_score": round(avg_satisfaction, 2) if satisfaction_count > 0 else None,
                "teams_rated": satisfaction_count,
                "target": 8.0,
                "status": "on_track" if avg_satisfaction >= 8 else "needs_attention",
            },
            "next_actions": [
                "Complete kickoff meetings for remaining teams",
                "Collect Day 1 feedback from active teams",
                "Address critical/high severity feedback",
                "Prepare for March 1 launch",
            ],
        }

    async def send_kickoff_reminder(self, team_id: str) -> Dict[str, Any]:
        """Send kickoff meeting reminder to team."""
        if team_id not in self.teams:
            raise ValueError(f"Unknown team: {team_id}")

        team = self.teams[team_id]
        meeting = self.meetings.get(team_id)

        if not meeting:
            return {"error": "No kickoff meeting scheduled"}

        # In production, this would send actual email/slack notification
        logger.info(f"Sending kickoff reminder to {team.name}")

        return {
            "team_id": team_id,
            "reminder_sent": True,
            "sent_to": team.contact_email,
            "meeting_time": meeting.scheduled_at.isoformat(),
            "meeting_link": meeting.meeting_link,
        }


async def main():
    """Main entry point for pilot kickoff management."""
    parser = argparse.ArgumentParser(description="Pilot Team Kickoff Management")
    parser.add_argument("--team", type=str, help="Team ID (alpha, beta, gamma, delta, epsilon)")
    parser.add_argument("--all", action="store_true", help="Apply to all teams")
    parser.add_argument(
        "--action",
        type=str,
        choices=["status", "schedule", "complete", "train", "activate", "feedback", "report", "reminder"],
        default="status",
        help="Action to perform"
    )
    parser.add_argument("--schedule-date", type=str, help="Kickoff date (YYYY-MM-DD HH:MM)")
    parser.add_argument("--score", type=float, help="Satisfaction score (1-10)")
    parser.add_argument("--output", type=str, choices=["json", "text"], default="text")

    args = parser.parse_args()

    manager = PilotKickoffManager()

    try:
        if args.action == "status":
            if args.all:
                result = await manager.get_all_teams_status()
            elif args.team:
                result = await manager.get_team_status(args.team)
            else:
                result = await manager.get_all_teams_status()

        elif args.action == "schedule":
            if not args.team:
                raise ValueError("--team required for schedule action")
            schedule_date = datetime.strptime(args.schedule_date, "%Y-%m-%d %H:%M") if args.schedule_date else datetime.utcnow() + timedelta(days=1)
            result = await manager.schedule_kickoff(args.team, schedule_date)
            result = {
                "meeting_id": result.id,
                "team_id": result.team_id,
                "scheduled_at": result.scheduled_at.isoformat(),
                "meeting_link": result.meeting_link,
                "agenda": result.agenda,
            }

        elif args.action == "complete":
            if not args.team:
                raise ValueError("--team required for complete action")
            result = await manager.complete_kickoff(args.team)

        elif args.action == "train":
            if not args.team:
                raise ValueError("--team required for train action")
            result = await manager.start_training(args.team)

        elif args.action == "activate":
            if not args.team:
                raise ValueError("--team required for activate action")
            result = await manager.activate_team(args.team)

        elif args.action == "feedback":
            if args.team:
                result = await manager.get_feedback_summary(args.team)
            else:
                result = await manager.get_feedback_summary()

        elif args.action == "report":
            result = await manager.generate_pilot_report()

        elif args.action == "reminder":
            if not args.team:
                raise ValueError("--team required for reminder action")
            result = await manager.send_kickoff_reminder(args.team)

        else:
            raise ValueError(f"Unknown action: {args.action}")

        # Output result
        if args.output == "json":
            print(json.dumps(result, indent=2, default=str))
        else:
            print("\n" + "=" * 60)
            print(f"PILOT KICKOFF MANAGER - {args.action.upper()}")
            print("=" * 60)

            if isinstance(result, list):
                for item in result:
                    print(f"\n{item.get('name', item.get('team_id', 'Unknown'))}:")
                    for key, value in item.items():
                        if key not in ['name', 'team_id']:
                            print(f"  {key}: {value}")
            else:
                for key, value in result.items():
                    if isinstance(value, dict):
                        print(f"\n{key}:")
                        for k, v in value.items():
                            print(f"  {k}: {v}")
                    elif isinstance(value, list):
                        print(f"\n{key}:")
                        for item in value:
                            print(f"  - {item}")
                    else:
                        print(f"{key}: {value}")

            print("\n" + "=" * 60)

    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
