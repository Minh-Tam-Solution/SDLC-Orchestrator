"""
=========================================================================
Authentication Schemas - Request/Response Models
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Week 3 Day 3 API Implementation
Authority: Backend Lead + CTO Approved
Foundation: OpenAPI 3.0, Pydantic v2
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Authentication request/response models
- OAuth callback schemas
- Token management schemas
- User profile schemas

Validation:
- Email format validation
- Password strength requirements (min 8 chars)
- Token format validation

Zero Mock Policy: Production-ready Pydantic models
=========================================================================
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# =========================================================================
# Enums (BUG #8 Fix: User Role)
# =========================================================================


class UserRole(str, Enum):
    """
    User role enumeration for RBAC.

    SDLC Orchestrator Roles (14 total):
        C-Suite (5 roles):
            - CEO: Chief Executive Officer (all permissions)
            - CTO: Chief Technology Officer (technical decisions)
            - CPO: Chief Product Officer (product strategy)
            - CIO: Chief Information Officer (IT infrastructure)
            - CFO: Chief Financial Officer (budget approval)

        Engineering (6 roles):
            - EM: Engineering Manager (team oversight)
            - TL: Tech Lead (architecture decisions)
            - DEV: Developer (code implementation)
            - QA: QA Engineer (testing, quality gates)
            - DEVOPS: DevOps Engineer (deployment, infrastructure)
            - SECURITY: Security Engineer (security review)

        Product & Business (3 roles):
            - PM: Product Manager (requirements, roadmap)
            - BA: Business Analyst (data analysis)
            - DESIGNER: UI/UX Designer (design artifacts)
    """
    CEO = "ceo"
    CTO = "cto"
    CPO = "cpo"
    CIO = "cio"
    CFO = "cfo"
    EM = "em"
    TL = "tl"
    PM = "pm"
    DEV = "dev"
    QA = "qa"
    DEVOPS = "devops"
    SECURITY = "security"
    BA = "ba"
    DESIGNER = "designer"


# =========================================================================
# Authentication Request/Response Schemas
# =========================================================================


class RegisterRequest(BaseModel):
    """
    User registration request with email and password.

    Request Body:
        {
            "email": "user@example.com",
            "password": "SecurePassword123!",
            "full_name": "Nguyễn Văn A"
        }

    Validation:
        - Email: Must be valid email format
        - Password: Minimum 8 characters (OWASP recommendation)
        - Full name: Optional, 1-100 characters

    Security:
        - Password hashed with bcrypt (cost=12)
        - Email stored lowercase
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (min 8 chars, recommended: 12+ with mixed case, numbers, symbols)"
    )
    full_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User full name (optional)"
    )
    role: UserRole = Field(
        UserRole.DEV,
        description="User role (default: dev)"
    )  # BUG #8 Fix


class RegisterResponse(BaseModel):
    """
    User registration response after successful signup.

    Response Body:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "full_name": "Nguyễn Văn A",
            "role": "dev",
            "is_active": true,
            "created_at": "2025-12-27T10:30:00Z",
            "message": "Registration successful. You can now login."
        }
    """

    id: UUID = Field(..., description="User UUID")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="User full name")  # BUG #2 Fix
    role: UserRole = Field(..., description="User role")  # BUG #8 Fix
    is_active: bool = Field(..., description="User active status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    message: str = Field(
        default="Registration successful. You can now login.",
        description="Success message"
    )

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """
    Login request with email and password.

    Request Body:
        {
            "email": "nguyen.van.anh@mtc.com.vn",
            "password": "SecurePassword123!"
        }

    Validation:
        - Email: Must be valid email format
        - Password: No validation here (hashed in DB)
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password (plain text)")


class TokenResponse(BaseModel):
    """
    JWT token response after successful login.

    Response Body:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 3600
        }

    Usage:
        Authorization: Bearer <access_token>
    """

    access_token: str = Field(..., description="JWT access token (1 hour expiry)")
    refresh_token: str = Field(..., description="JWT refresh token (30 days expiry)")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(
        default=3600, description="Access token expiry in seconds (3600 = 1 hour)"
    )


class RefreshTokenRequest(BaseModel):
    """
    Refresh token request to get new access token.

    Request Body:
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    """

    refresh_token: str = Field(..., description="JWT refresh token")


class LogoutRequest(BaseModel):
    """
    Logout request to revoke refresh token.

    Request Body:
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    """

    refresh_token: str = Field(..., description="JWT refresh token to revoke")


# =========================================================================
# OAuth Schemas
# =========================================================================


class OAuthAuthorizeResponse(BaseModel):
    """
    OAuth authorization URL response.

    Response Body:
        {
            "authorization_url": "https://github.com/login/oauth/authorize?...",
            "state": "random-state-string"
        }
    """

    authorization_url: str = Field(..., description="OAuth provider authorization URL")
    state: str = Field(..., description="CSRF protection state parameter")


class OAuthCallbackRequest(BaseModel):
    """
    OAuth callback request from provider (GitHub, Google, Microsoft).

    Request Body:
        {
            "code": "abc123def456",
            "state": "random-state-string"
        }

    Flow:
        1. User clicks "Login with GitHub"
        2. Redirected to GitHub OAuth page
        3. User approves access
        4. GitHub redirects to /auth/oauth/github/callback?code=...&state=...
        5. Backend exchanges code for access token
        6. Backend creates user account (if not exists)
        7. Backend returns JWT tokens
    """

    code: str = Field(..., description="OAuth authorization code from provider")
    state: str = Field(..., description="CSRF protection state parameter")
    code_verifier: Optional[str] = Field(None, description="PKCE code verifier (Google only)")


class OAuthProvider(BaseModel):
    """
    OAuth provider information.

    Response Body:
        {
            "provider_id": "550e8400-e29b-41d4-a716-446655440000",
            "provider_name": "github",
            "oauth_user_id": "123456789",
            "email": "nguyen.van.anh@gmail.com",
            "linked_at": "2025-11-28T10:30:00Z"
        }
    """

    provider_id: UUID = Field(..., description="OAuth account UUID")
    provider_name: str = Field(..., description="OAuth provider (github, google, microsoft)")
    oauth_user_id: str = Field(..., description="User ID from OAuth provider")
    email: Optional[str] = Field(None, description="Email from OAuth provider")
    linked_at: datetime = Field(..., description="OAuth link timestamp")


# =========================================================================
# User Profile Schemas
# =========================================================================


class UserProfile(BaseModel):
    """
    User profile response (authenticated user).

    Response Body:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "nguyen.van.anh@mtc.com.vn",
            "name": "Nguyễn Văn Anh",
            "is_active": true,
            "is_superuser": false,
            "is_platform_admin": false,
            "roles": ["Engineering Manager", "CTO"],
            "oauth_providers": ["github", "google"],
            "created_at": "2025-10-01T08:00:00Z",
            "last_login_at": "2025-11-28T10:30:00Z"
        }

    Sprint 88: Platform Admin Privacy Fix
        - is_platform_admin: Platform admins manage system operations but CANNOT access customer data
        - is_superuser: DEPRECATED - legacy field, use is_platform_admin for privacy checks
    """

    id: UUID = Field(..., description="User UUID")
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    is_active: bool = Field(..., description="User active status")
    is_superuser: bool = Field(default=False, description="Superuser flag (DEPRECATED - use is_platform_admin)")
    is_platform_admin: bool = Field(default=False, description="Platform admin flag - manages system operations, CANNOT access customer data (Sprint 88)")
    roles: List[str] = Field(default_factory=list, description="List of role names")
    oauth_providers: List[str] = Field(
        default_factory=list, description="List of linked OAuth providers"
    )
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        from_attributes = True  # Pydantic v2: Enable ORM mode


# =========================================================================
# API Key Schemas
# =========================================================================


class APIKeyCreateRequest(BaseModel):
    """
    API key creation request (for CI/CD integrations).

    Request Body:
        {
            "name": "GitHub Actions - Production Deploy",
            "expires_in_days": 90
        }
    """

    name: str = Field(..., min_length=1, max_length=255, description="API key name")
    expires_in_days: Optional[int] = Field(
        None, ge=1, le=365, description="Expiry in days (max 365)"
    )


class APIKeyResponse(BaseModel):
    """
    API key response after creation.

    Response Body:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "api_key": "sdlc_live_abc123def456...",
            "name": "GitHub Actions - Production Deploy",
            "created_at": "2025-11-28T10:30:00Z",
            "expires_at": "2026-02-26T10:30:00Z"
        }

    Warning:
        The `api_key` field is only shown ONCE during creation.
        Store it securely - it cannot be retrieved later.
    """

    id: UUID = Field(..., description="API key UUID")
    api_key: str = Field(..., description="Full API key (shown ONCE)")
    name: str = Field(..., description="API key name")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiry timestamp")


class APIKeyInfo(BaseModel):
    """
    API key information (without revealing the key).

    Response Body:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "GitHub Actions - Production Deploy",
            "key_prefix": "sdlc_live_abc1...",
            "created_at": "2025-11-28T10:30:00Z",
            "expires_at": "2026-02-26T10:30:00Z",
            "last_used_at": "2025-11-28T15:45:00Z",
            "is_active": true
        }
    """

    id: UUID = Field(..., description="API key UUID")
    name: str = Field(..., description="API key name")
    key_prefix: str = Field(..., description="API key prefix (first 20 chars)")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiry timestamp")
    last_used_at: Optional[datetime] = Field(None, description="Last used timestamp")
    is_active: bool = Field(..., description="Active status")

    class Config:
        from_attributes = True  # Pydantic v2: Enable ORM mode


# =========================================================================
# Password Reset Schemas (Sprint 60)
# =========================================================================


class ForgotPasswordRequest(BaseModel):
    """
    Forgot password request to initiate password reset.

    Request Body:
        {
            "email": "user@example.com"
        }

    Flow:
        1. User submits email address
        2. System generates reset token
        3. System sends email with reset link
        4. Always returns 200 (email enumeration protection)

    Security:
        - Always returns success (prevents email enumeration)
        - Rate limited: 3 requests/email/hour
    """

    email: EmailStr = Field(..., description="User email address")


class ForgotPasswordResponse(BaseModel):
    """
    Response after forgot password request.

    Always returns success message regardless of whether email exists.
    This prevents email enumeration attacks.

    Response Body:
        {
            "message": "If an account with this email exists, you will receive a password reset link.",
            "email": "user@example.com"
        }
    """

    message: str = Field(
        default="If an account with this email exists, you will receive a password reset link.",
        description="Generic success message (email enumeration protection)"
    )
    email: EmailStr = Field(..., description="Submitted email address")


class VerifyResetTokenRequest(BaseModel):
    """
    Request to verify password reset token validity.

    Query Parameters:
        token: Reset token from email link

    Usage:
        GET /auth/verify-reset-token?token=abc123...
    """

    token: str = Field(..., min_length=32, description="Password reset token from email")


class VerifyResetTokenResponse(BaseModel):
    """
    Response after verifying reset token.

    Response Body (valid token):
        {
            "valid": true,
            "email": "user@example.com",
            "expires_at": "2025-12-29T15:00:00Z"
        }

    Response Body (invalid/expired token):
        {
            "valid": false,
            "email": null,
            "expires_at": null,
            "error": "Token has expired"
        }
    """

    valid: bool = Field(..., description="Whether token is valid and not expired")
    email: Optional[EmailStr] = Field(None, description="Email address associated with token")
    expires_at: Optional[datetime] = Field(None, description="Token expiry timestamp")
    error: Optional[str] = Field(None, description="Error message if token is invalid")


class ResetPasswordRequest(BaseModel):
    """
    Request to reset password using valid token.

    Request Body:
        {
            "token": "abc123...",
            "new_password": "NewSecurePassword123!"
        }

    Validation:
        - Token: Must be valid and not expired
        - Password: Minimum 8 characters (OWASP recommendation)

    Security:
        - Token marked as used after successful reset
        - All existing sessions revoked
        - Password hashed with bcrypt (cost=12)
    """

    token: str = Field(..., min_length=32, description="Password reset token from email")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (min 8 chars, recommended: 12+ with mixed case, numbers, symbols)"
    )


class ResetPasswordResponse(BaseModel):
    """
    Response after successful password reset.

    Response Body:
        {
            "message": "Password has been reset successfully. You can now login with your new password.",
            "email": "user@example.com"
        }

    Errors:
        - 400 Bad Request: Invalid or expired token
        - 422 Unprocessable Entity: Password too short
    """

    message: str = Field(
        default="Password has been reset successfully. You can now login with your new password.",
        description="Success message"
    )
    email: EmailStr = Field(..., description="Email address of the user")
