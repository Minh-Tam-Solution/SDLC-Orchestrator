"""
=========================================================================
Support Models - Audit, Webhooks, Notifications, Stage Transitions
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Week 3 Architecture Design
Authority: Backend Lead + CTO Approved
Foundation: Data Model v0.1 (9.8/10 quality)
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Stage transition tracking (WHY → WHAT → BUILD... progression)
- GitHub/GitLab webhook integration (PR auto-collection)
- Audit log (100% operation logging for compliance)
- Notification system (Email, Slack alerts)

Components:
- StageTransition: SDLC stage progression tracking
- Webhook: GitHub/GitLab integration for evidence auto-upload
- AuditLog: System-wide audit trail (500K logs Year 1 capacity)
- Notification: Email/Slack notification queue

Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class StageTransition(Base):
    """
    Stage Transition model for SDLC stage progression tracking.

    Purpose:
        - Track stage transitions (WHY → WHAT → BUILD...)
        - Audit trail for stage progression
        - Gate-triggered transitions

    SDLC 4.9 Stages:
        WHY → WHAT → HOW → BUILD → TEST → DEPLOY → OPERATE → INTEGRATE → COLLABORATE → GOVERN

    Fields:
        - id: UUID primary key
        - gate_id: Foreign key to Gate (which gate triggered this transition)
        - from_stage: Previous stage ('WHY', 'WHAT', etc.)
        - to_stage: New stage ('WHAT', 'BUILD', etc.)
        - transitioned_by: Foreign key to User (who triggered transition)
        - transitioned_at: Transition timestamp
        - notes: Transition notes
        - created_at: Record creation timestamp

    Relationships:
        - gate: Many-to-One with Gate model
        - user: Many-to-One with User model

    Indexes:
        - gate_id (B-tree) - Fast gate transition lookup
        - transitioned_at (B-tree) - Recent transitions queries

    Usage Example:
        transition = StageTransition(
            gate_id=gate.id,
            from_stage='WHAT',
            to_stage='BUILD',
            transitioned_by=user.id,
            transitioned_at=datetime.utcnow(),
            notes='Gate G1 approved - moving to BUILD stage'
        )
    """

    __tablename__ = "stage_transitions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Gate Relationship
    gate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("gates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Stage Transition
    from_stage = Column(String(20), nullable=False)  # 'WHY', 'WHAT', etc.
    to_stage = Column(String(20), nullable=False)  # 'WHAT', 'BUILD', etc.

    # Transition Metadata
    transitioned_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    transitioned_at = Column(DateTime, nullable=False, index=True)
    notes = Column(Text, nullable=True)

    # Audit Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    gate = relationship("Gate", back_populates="stage_transitions")
    user = relationship("User", back_populates="stage_transitions")

    def __repr__(self) -> str:
        return f"<StageTransition(gate_id={self.gate_id}, {self.from_stage} → {self.to_stage})>"


class Webhook(Base):
    """
    Webhook model for GitHub/GitLab integration.

    Purpose:
        - GitHub PR auto-collection (webhook triggers on PR merge)
        - Evidence auto-upload (commits, PRs, deployments)
        - Event-driven gate updates

    Supported Events:
        - pull_request.merged: PR merged event
        - push: Code pushed to branch
        - deployment: Deployment event
        - release.published: Release published

    Fields:
        - id: UUID primary key
        - project_id: Foreign key to Project
        - webhook_url: Webhook URL (unique, secret)
        - webhook_secret: HMAC secret for signature verification
        - provider: Webhook provider ('github', 'gitlab', 'bitbucket')
        - events: JSONB array of subscribed events
        - is_active: Webhook status (True = enabled)
        - last_triggered_at: Last webhook trigger timestamp
        - created_by: Foreign key to User (creator)
        - created_at: Webhook creation timestamp
        - updated_at: Last update timestamp

    Relationships:
        - project: Many-to-One with Project model
        - creator: Many-to-One with User model

    Indexes:
        - project_id (B-tree) - Fast project webhook lookup
        - webhook_url (unique, B-tree) - Fast webhook URL lookup
        - is_active (B-tree) - Active webhook filtering

    Usage Example:
        webhook = Webhook(
            project_id=project.id,
            webhook_url='https://sdlc.example.com/webhooks/abc123',
            webhook_secret='secret123',
            provider='github',
            events=['pull_request.merged', 'deployment'],
            created_by=user.id
        )
    """

    __tablename__ = "webhooks"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Project Relationship
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Webhook Configuration
    webhook_url = Column(String(512), unique=True, index=True, nullable=False)
    webhook_secret = Column(String(255), nullable=False)  # HMAC secret

    # Provider
    provider = Column(String(50), nullable=False)  # 'github', 'gitlab', 'bitbucket'

    # Subscribed Events
    events = Column(
        JSONB, nullable=False, default=list
    )  # ['pull_request.merged', 'deployment']

    # Webhook Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_triggered_at = Column(DateTime, nullable=True)

    # Creator
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Audit Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    project = relationship("Project", back_populates="webhooks")
    creator = relationship("User", back_populates="webhooks")

    def __repr__(self) -> str:
        return f"<Webhook(project_id={self.project_id}, provider={self.provider})>"


class AuditLog(Base):
    """
    Audit Log model for system-wide audit trail.

    Purpose:
        - 100% operation logging (compliance, security)
        - User action tracking (who did what when)
        - Security event monitoring (failed logins, permission changes)

    Logged Actions:
        - USER_LOGIN: User login event
        - USER_LOGOUT: User logout event
        - GATE_CREATED: Gate created
        - GATE_APPROVED: Gate approved
        - GATE_REJECTED: Gate rejected
        - EVIDENCE_UPLOADED: Evidence file uploaded
        - POLICY_EVALUATED: Policy evaluation executed
        - PERMISSION_CHANGED: User permission changed

    Fields:
        - id: UUID primary key
        - user_id: Foreign key to User (actor, nullable for system events)
        - action: Action type ('USER_LOGIN', 'GATE_CREATED', etc.)
        - resource_type: Resource type ('user', 'gate', 'evidence', etc.)
        - resource_id: Resource UUID
        - details: JSONB additional details
        - ip_address: Client IP address
        - user_agent: Client user agent
        - created_at: Event timestamp

    Relationships:
        - user: Many-to-One with User model

    Indexes:
        - user_id (B-tree) - Fast user audit lookup
        - action (B-tree) - Action type filtering
        - resource_type + resource_id (composite) - Resource audit lookup
        - created_at (B-tree) - Recent events queries

    Usage Example:
        log = AuditLog(
            user_id=user.id,
            action='GATE_APPROVED',
            resource_type='gate',
            resource_id=gate.id,
            details={'gate_name': 'G1 Design Ready', 'approver_role': 'CTO'},
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0...'
        )
    """

    __tablename__ = "audit_logs"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # User Relationship (nullable for system events)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Action
    action = Column(String(50), nullable=False, index=True)  # 'USER_LOGIN', 'GATE_CREATED', etc.

    # Resource
    resource_type = Column(String(50), nullable=True, index=True)  # 'user', 'gate', 'evidence'
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    target_name = Column(String(255), nullable=True)  # Human-readable target name for display

    # Details
    details = Column(JSONB, nullable=False, default=dict)  # Additional context

    # Client Information
    ip_address = Column(INET, nullable=True)
    user_agent = Column(String(512), nullable=True)

    # Audit Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog(action={self.action}, user_id={self.user_id}, resource_type={self.resource_type})>"


class SystemSetting(Base):
    """
    System Setting model for platform configuration.

    Purpose:
        - Store system-wide configuration (session timeout, limits, features)
        - Runtime configuration without redeployment
        - Audit trail for setting changes (who changed what when)
        - Version control for rollback capability (CTO requirement)

    Categories:
        - security: Session timeout, MFA, password policy
        - limits: Max projects, max file size, retention periods
        - features: Feature flags (AI Council, etc.)
        - notifications: Email/Slack settings

    Fields:
        - key: Setting key (primary key, e.g., 'session_timeout_minutes')
        - value: JSONB value (flexible for different types)
        - version: Version number for rollback capability
        - previous_value: Previous value for rollback
        - category: Setting category ('security', 'limits', 'features')
        - description: Human-readable description
        - updated_at: Last update timestamp
        - updated_by: Foreign key to User (who made the change)

    Indexes:
        - category (B-tree) - Category filtering
        - updated_at (B-tree) - Recent changes queries

    Usage Example:
        setting = SystemSetting(
            key='session_timeout_minutes',
            value=30,
            category='security',
            description='Session timeout in minutes'
        )

    ADR Reference: ADR-017 Admin Panel Architecture
    CTO Condition: Version field for rollback capability (Dec 16, 2025)
    """

    __tablename__ = "system_settings"

    # Primary Key
    key = Column(String(100), primary_key=True)

    # Value (JSONB for flexibility)
    value = Column(JSONB, nullable=False)

    # Version control for rollback (CTO requirement)
    version = Column(Integer, nullable=False, default=1)
    previous_value = Column(JSONB, nullable=True)

    # Metadata
    category = Column(String(50), nullable=False, default="general")
    description = Column(Text, nullable=True)

    # Audit
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    updater = relationship("User", backref="system_settings_updated")

    def __repr__(self) -> str:
        return f"<SystemSetting(key={self.key}, category={self.category}, version={self.version})>"


class Notification(Base):
    """
    Notification model for email/Slack notifications.

    Purpose:
        - Email notifications (gate approved, policy failed, etc.)
        - Slack notifications (real-time alerts)
        - Notification queue management

    Notification Types:
        - GATE_APPROVAL_REQUEST: Gate submitted for approval
        - GATE_APPROVED: Gate approved
        - GATE_REJECTED: Gate rejected with comments
        - POLICY_FAILED: Policy evaluation failed
        - EVIDENCE_UPLOADED: New evidence uploaded
        - BUDGET_ALERT: AI budget threshold reached (80%, 90%, 100%)

    Fields:
        - id: UUID primary key
        - user_id: Foreign key to User (recipient)
        - notification_type: Notification type ('GATE_APPROVAL_REQUEST', etc.)
        - title: Notification title
        - message: Notification message body
        - channel: Notification channel ('email', 'slack', 'in_app')
        - status: Notification status ('PENDING', 'SENT', 'FAILED')
        - sent_at: Sent timestamp
        - error_message: Error details if failed
        - created_at: Notification creation timestamp

    Relationships:
        - user: Many-to-One with User model

    Indexes:
        - user_id (B-tree) - Fast user notification lookup
        - status (B-tree) - Pending notification filtering
        - created_at (B-tree) - Recent notifications queries

    Usage Example:
        notification = Notification(
            user_id=cto_user.id,
            notification_type='GATE_APPROVAL_REQUEST',
            title='Gate G1 Design Ready - Approval Required',
            message='E-commerce Platform v2.0 Gate G1 requires your approval.',
            channel='email',
            status='PENDING'
        )
    """

    __tablename__ = "notifications"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # User Relationship
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Notification Type
    notification_type = Column(
        String(50), nullable=False
    )  # 'GATE_APPROVAL_REQUEST', 'GATE_APPROVED', etc.

    # Notification Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Channel
    channel = Column(String(20), nullable=False, default="in_app")  # 'email', 'slack', 'in_app', 'teams'

    # Priority (Sprint 22 - Notifications Enhancement)
    priority = Column(
        String(20), nullable=False, default="medium"
    )  # 'critical', 'high', 'medium', 'low'

    # Project Reference (Sprint 22 - Notifications Enhancement)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Extra Data (Sprint 22 - Additional context)
    # Note: 'metadata' is reserved in SQLAlchemy, using 'extra_data' instead
    extra_data = Column(JSONB, nullable=True, default=dict)

    # Read Status (Sprint 22 - In-app notifications)
    is_read = Column(Boolean, nullable=False, default=False, index=True)

    # Status
    status = Column(
        String(20), nullable=False, default="PENDING", index=True
    )  # 'PENDING', 'SENT', 'FAILED'
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Audit Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="notifications")
    project = relationship("Project", backref="notifications")

    def __repr__(self) -> str:
        return f"<Notification(user_id={self.user_id}, notification_type={self.notification_type}, status={self.status})>"
