"""
=========================================================================
User Model - Authentication & Authorization
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Week 3 Architecture Design
Authority: Backend Lead + CTO Approved
Foundation: Data Model v0.1 (9.8/10 quality), OWASP ASVS Level 2
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- User authentication (OAuth 2.0, email/password, MFA)
- Role-based access control (RBAC)
- Multi-tenancy support (project-level isolation)
- API key management (SHA256 hashed)

Security Standards:
- OWASP ASVS Level 2 compliant
- AES-256 encryption (passwords, MFA secrets)
- SHA-256 hashing (API keys, refresh tokens)
- JWT token management (1-hour access, 30-day refresh)

Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base

# Many-to-Many association table: users <-> roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE")),
    extend_existing=True,  # Allow table redefinition during test imports
)


class User(Base):
    """
    User model for authentication and authorization.

    Fields:
        - id: UUID primary key
        - organization_id: Parent organization (Sprint 70)
        - email: Unique email address (lowercase, validated)
        - password_hash: bcrypt hash (cost=12, 72-byte output)
        - full_name: Full name (optional, from OAuth providers) [BUG #2 Fix]
        - avatar_url: Profile picture URL (optional, from OAuth)
        - role: User role (ceo, cto, pm, dev, qa, etc.) [BUG #8 Fix]
        - is_active: Account status (True by default, False = suspended)
        - is_superuser: Admin flag (CTO, CEO only) [DEPRECATED - use is_platform_admin]
        - is_platform_admin: Platform admin flag - manages system, CANNOT access customer data (Sprint 88)
        - mfa_enabled: MFA enrollment status
        - mfa_secret: TOTP secret (encrypted, 32-byte base32)
        - backup_codes: One-time recovery codes (10 codes, hashed)
        - mfa_setup_deadline: Deadline for completing MFA setup (7-day grace, ADR-027)
        - is_mfa_exempt: User exempt from MFA requirement (admin override, ADR-027)
        - last_login: Last successful login timestamp
        - failed_login_count: Consecutive failed login attempts (ADR-027)
        - locked_until: Account lockout expiry timestamp (ADR-027)
        - deleted_at: Soft delete timestamp (NULL = active, NOT NULL = deleted)
        - deleted_by: Foreign key to User who performed deletion (for audit)
        - created_at: Account creation timestamp
        - updated_at: Last update timestamp

    Relationships:
        - roles: Many-to-Many with Role model
        - oauth_accounts: One-to-Many with OAuthAccount model
        - api_keys: One-to-Many with APIKey model
        - audit_logs: One-to-Many with AuditLog model

    Indexes:
        - email (unique, B-tree) - Fast user lookup by email
        - created_at (B-tree) - Recent user queries
        - is_active (B-tree) - Active user filtering

    Security:
        - Password: bcrypt with cost=12 (250ms hash time)
        - MFA secret: AES-256 encrypted in database
        - Backup codes: SHA-256 hashed (not plaintext)
    """

    __tablename__ = "users"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Organization (Sprint 70 - Teams Foundation)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent organization (NULL during migration or for unassigned users)"
    )

    # Authentication
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth-only users

    # Profile
    full_name = Column(String(255), nullable=True)  # BUG #2 Fix: Renamed from 'name'
    avatar_url = Column(String(512), nullable=True)
    role = Column(
        String(50),
        nullable=False,
        default="dev",
        server_default="dev",
        index=True,
        comment="User role: ceo, cto, cpo, cio, cfo, em, tl, pm, dev, qa, devops, security, ba, designer"
    )  # BUG #8 Fix: Added role column

    # Account Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_platform_admin = Column(
        Boolean,
        default=False,
        nullable=False,
        server_default='false',
        index=True,
        comment='Platform admin - manages system operations, CANNOT access customer data (Sprint 88)'
    )

    # Multi-Factor Authentication (MFA)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)  # Encrypted TOTP secret
    backup_codes = Column(String(1024), nullable=True)  # JSON array of hashed codes

    # MFA Enforcement (ADR-027 Phase 1 - mfa_required)
    mfa_setup_deadline = Column(
        DateTime(timezone=True),
        nullable=True,
        comment='Deadline for completing MFA setup when mfa_required is enabled (7-day grace period)'
    )
    is_mfa_exempt = Column(
        Boolean,
        default=False,
        nullable=False,
        server_default='false',
        comment='User is exempt from MFA requirement (admin override)'
    )

    # Session Management
    last_login = Column(DateTime, nullable=True)

    # Login Lockout (ADR-027 Phase 1 - max_login_attempts)
    failed_login_count = Column(
        postgresql.INTEGER,
        default=0,
        nullable=False,
        server_default='0',
        comment='Number of consecutive failed login attempts'
    )
    locked_until = Column(
        DateTime(timezone=True),
        nullable=True,
        comment='Account locked until this timestamp (NULL = not locked)'
    )

    # Soft Delete (Sprint 40 - Admin Panel CRUD)
    deleted_at = Column(DateTime, nullable=True, index=True)  # Soft delete timestamp
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Admin who deleted

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    # Organization & Team Relationships (Sprint 70 - Teams Foundation)
    organization = relationship("Organization", back_populates="users")
    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")

    # Project Relationships
    owned_projects = relationship("Project", back_populates="owner", foreign_keys="[Project.owner_id]")
    project_memberships = relationship("ProjectMember", back_populates="user", foreign_keys="[ProjectMember.user_id]")

    # Gate Relationships
    created_gates = relationship("Gate", back_populates="creator", foreign_keys="[Gate.created_by]")
    gate_approvals = relationship("GateApproval", back_populates="approver")

    # Evidence Relationships
    uploaded_evidence = relationship("GateEvidence", back_populates="uploader")

    # AI Relationships
    ai_requests = relationship("AIRequest", back_populates="user")

    # Policy Relationships
    custom_policies = relationship("CustomPolicy", back_populates="creator")

    # Support Relationships
    stage_transitions = relationship("StageTransition", back_populates="user")
    webhooks = relationship("Webhook", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

    # Usage Tracking Relationships (Sprint 24)
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    usage_events = relationship("UsageEvent", back_populates="user", cascade="all, delete-orphan")

    # Analytics Relationships (Sprint 41)
    analytics_events = relationship("AnalyticsEvent", back_populates="user", cascade="all, delete-orphan")
    ai_code_events = relationship(
        "AICodeEvent", back_populates="user",
        foreign_keys="[AICodeEvent.user_id]", cascade="all, delete-orphan"
    )

    # Override Relationships (Sprint 43)
    override_requests = relationship(
        "ValidationOverride", back_populates="requested_by",
        foreign_keys="[ValidationOverride.requested_by_id]"
    )

    # Pilot Tracking Relationships (Sprint 49)
    pilot_participant = relationship(
        "PilotParticipant", back_populates="user",
        uselist=False, cascade="all, delete-orphan"
    )

    # Subscription & Payment Relationships (Sprint 58)
    subscription = relationship(
        "Subscription", back_populates="user",
        uselist=False, cascade="all, delete-orphan"
    )
    payments = relationship(
        "PaymentHistory", back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, roles={[r.name for r in self.roles]})>"

    @property
    def role_names(self) -> list[str]:
        """Get list of role names (e.g., ['em', 'pm'])"""
        return [role.name for role in self.roles]

    @property
    def is_c_suite(self) -> bool:
        """Check if user is C-Suite (CEO, CTO, CPO, CIO, CFO)"""
        c_suite_roles = {"ceo", "cto", "cpo", "cio", "cfo"}
        return bool(set(self.role_names) & c_suite_roles)

    @property
    def requires_mfa(self) -> bool:
        """Check if user must have MFA enabled (C-Suite mandatory)"""
        return self.is_c_suite


class Role(Base):
    """
    Role model for RBAC (Role-Based Access Control).

    SDLC Orchestrator Roles (13 total):
        C-Suite (5 roles):
            - ceo: Chief Executive Officer (all permissions)
            - cto: Chief Technology Officer (technical decisions)
            - cpo: Chief Product Officer (product strategy)
            - cio: Chief Information Officer (IT infrastructure)
            - cfo: Chief Financial Officer (budget approval)

        Engineering (6 roles):
            - em: Engineering Manager (team oversight)
            - tl: Tech Lead (architecture decisions)
            - dev: Developer (code implementation)
            - qa: QA Engineer (testing, quality gates)
            - devops: DevOps Engineer (deployment, infrastructure)
            - security: Security Engineer (security review)

        Product & Business (2 roles):
            - pm: Product Manager (requirements, roadmap)
            - ba: Business Analyst (data analysis)

    Fields:
        - id: UUID primary key
        - name: Role name (lowercase, snake_case, e.g., 'em', 'cto')
        - display_name: Human-readable name (e.g., 'Engineering Manager')
        - description: Role description and permissions
        - is_active: Role status (True by default)
        - created_at: Role creation timestamp

    Relationships:
        - users: Many-to-Many with User model
        - permissions: Many-to-Many with Permission model (future)

    Indexes:
        - name (unique, B-tree) - Fast role lookup by name
    """

    __tablename__ = "roles"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Role Identity
    name = Column(String(50), unique=True, index=True, nullable=False)  # e.g., 'em', 'cto'
    display_name = Column(String(100), nullable=False)  # e.g., 'Engineering Manager'
    description = Column(String(500), nullable=True)

    # Role Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")

    def __repr__(self) -> str:
        return f"<Role(name={self.name}, display_name={self.display_name})>"


class OAuthAccount(Base):
    """
    OAuth Account model for SSO (GitHub, Google, Microsoft).

    Fields:
        - id: UUID primary key
        - user_id: Foreign key to User
        - provider: OAuth provider name ('github', 'google', 'microsoft')
        - provider_account_id: User ID from OAuth provider
        - access_token: OAuth access token (encrypted)
        - refresh_token: OAuth refresh token (encrypted)
        - expires_at: Token expiry timestamp
        - created_at: Account linking timestamp
        - updated_at: Last token refresh timestamp

    Relationships:
        - user: Many-to-One with User model

    Indexes:
        - user_id (B-tree) - Fast user lookup
        - provider + provider_account_id (unique composite) - Prevent duplicate accounts

    Security:
        - Tokens encrypted at-rest (AES-256)
        - Never logged or exposed in API responses
    """

    __tablename__ = "oauth_accounts"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # User Relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # OAuth Provider
    provider = Column(String(50), nullable=False)  # 'github', 'google', 'microsoft'
    provider_account_id = Column(String(255), nullable=False)  # User ID from provider

    # OAuth Tokens (encrypted)
    access_token = Column(String(512), nullable=False)
    refresh_token = Column(String(512), nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="oauth_accounts")

    def __repr__(self) -> str:
        return f"<OAuthAccount(user_id={self.user_id}, provider={self.provider})>"


class APIKey(Base):
    """
    API Key model for CI/CD and third-party integrations.

    Fields:
        - id: UUID primary key
        - user_id: Foreign key to User
        - name: User-friendly name (e.g., 'GitHub Actions')
        - key_hash: SHA-256 hash of API key (not plaintext)
        - prefix: First 8 characters of key (for UI display)
        - last_used_at: Last usage timestamp
        - expires_at: Expiry timestamp (optional)
        - is_active: Key status (True by default, False = revoked)
        - created_at: Key creation timestamp

    Relationships:
        - user: Many-to-One with User model

    Indexes:
        - user_id (B-tree) - Fast user lookup
        - key_hash (unique, B-tree) - Fast key validation
        - is_active (B-tree) - Active key filtering

    Security:
        - Key format: sdlc_live_<32-byte-base64> (e.g., sdlc_live_abc123...)
        - Hash: SHA-256 (256-bit output, collision-resistant)
        - Shown ONCE: On creation, user must save it
    """

    __tablename__ = "api_keys"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # User Relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # API Key Identity
    name = Column(String(100), nullable=False)  # User-friendly name
    key_hash = Column(String(64), unique=True, index=True, nullable=False)  # SHA-256 hash
    prefix = Column(String(30), nullable=False)  # First 20 chars (for UI display, e.g., sdlc_live_xxxx...)

    # Usage Tracking
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Optional expiry

    # Key Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<APIKey(name={self.name}, prefix={self.prefix}, user_id={self.user_id})>"


class RefreshToken(Base):
    """
    Refresh Token model for session management.

    Fields:
        - id: UUID primary key
        - user_id: Foreign key to User
        - token_hash: SHA-256 hash of refresh token
        - expires_at: Token expiry timestamp (30 days from issue)
        - is_revoked: Revocation status (False by default, True = blacklisted)
        - created_at: Token issue timestamp

    Relationships:
        - user: Many-to-One with User model

    Indexes:
        - user_id (B-tree) - Fast user lookup
        - token_hash (unique, B-tree) - Fast token validation
        - expires_at (B-tree) - Expired token cleanup

    Security:
        - Token format: <64-byte-base64> (random, not guessable)
        - Hash: SHA-256 (store hash, not plaintext)
        - Revocation: Blacklist in Redis (immediate effect)
        - Expiry: 30 days (auto-cleanup expired tokens)
    """

    __tablename__ = "refresh_tokens"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # User Relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Refresh Token
    token_hash = Column(String(64), unique=True, index=True, nullable=False)  # SHA-256 hash
    expires_at = Column(DateTime, nullable=False, index=True)

    # Revocation
    is_revoked = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken(user_id={self.user_id}, expires_at={self.expires_at}, is_revoked={self.is_revoked})>"


class PasswordResetToken(Base):
    """
    Password Reset Token model for secure password recovery.

    Sprint 60 - December 29, 2025
    OWASP Compliant Password Reset Flow

    Fields:
        - id: UUID primary key
        - user_id: Foreign key to User
        - token_hash: SHA-256 hash of reset token (never store plaintext)
        - expires_at: Token expiry timestamp (1 hour from issue)
        - used_at: Timestamp when token was used (NULL if unused)
        - created_at: Token creation timestamp
        - ip_address: IP address that requested the token (for audit)
        - user_agent: Browser user agent (for audit)

    Relationships:
        - user: Many-to-One with User model

    Indexes:
        - user_id (B-tree) - Fast user lookup
        - token_hash (unique, B-tree) - Fast token validation
        - expires_at (B-tree) - Expired token cleanup

    Security:
        - Token: 64-byte URL-safe base64 (cryptographically random)
        - Hash: SHA-256 (store hash, not plaintext)
        - Single-use: Marked as used after password reset
        - Short expiry: 1 hour (prevents replay attacks)
        - Rate limited: 3 requests/email/hour, 10 requests/IP/hour
    """

    __tablename__ = "password_reset_tokens"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # User Relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Reset Token
    token_hash = Column(String(128), unique=True, index=True, nullable=False)  # SHA-256 hash (64 hex chars)
    expires_at = Column(DateTime, nullable=False, index=True)

    # Usage Tracking
    used_at = Column(DateTime, nullable=True)  # NULL = unused, timestamp = used

    # Audit Information
    ip_address = Column(postgresql.INET(), nullable=True)  # PostgreSQL INET type
    user_agent = Column(String(512), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="password_reset_tokens")

    def __repr__(self) -> str:
        return f"<PasswordResetToken(user_id={self.user_id}, expires_at={self.expires_at}, used={self.used_at is not None})>"

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        # Handle both offset-naive and offset-aware datetimes
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return self.used_at is None and expires > now

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        # Handle both offset-naive and offset-aware datetimes
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return expires <= now

    @property
    def is_used(self) -> bool:
        """Check if token has been used."""
        return self.used_at is not None
