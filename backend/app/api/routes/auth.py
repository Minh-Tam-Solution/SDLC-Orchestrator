"""
=========================================================================
Authentication Router - Registration, Login, Token Refresh, Logout
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.1.0
Date: December 27, 2025
Status: ACTIVE - Sprint 58 Registration + VNPay
Authority: Backend Lead + CTO Approved
Foundation: FastAPI, JWT Authentication, OWASP ASVS Level 2
Framework: SDLC 5.1.2 Universal Framework

Purpose:
- User registration (email/password)
- User authentication endpoints
- JWT token management (access + refresh)
- OAuth 2.0 integration (GitHub, Google, Microsoft)
- User profile management

Endpoints:
- POST /auth/register - User registration (Sprint 58)
- POST /auth/login - Email/password login
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Revoke refresh token
- GET /auth/me - Get current user profile
- GET /auth/oauth/{provider}/authorize - OAuth authorization URL
- POST /auth/oauth/{provider}/callback - OAuth callback handler

Security:
- Password hashing (bcrypt, cost=12)
- Password verification (bcrypt)
- JWT token generation (HS256)
- Token expiry enforcement (1h access, 30d refresh)
- Refresh token revocation (blacklist)
- Email uniqueness validation

Zero Mock Policy: Production-ready authentication implementation
=========================================================================
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_current_user
from app.core.config import settings
from app.core.cookies import (
    REFRESH_TOKEN_COOKIE_NAME,
    clear_auth_cookies,
    set_access_token_cookie,
    set_auth_cookies,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_password_reset_token,
    get_password_hash,
    hash_api_key,
    hash_reset_token,
    verify_password,
)
from app.db.session import get_db
from app.models.user import PasswordResetToken, RefreshToken, User
from app.services.settings_service import SettingsService, get_settings_service
from app.schemas.auth import (
    DeviceTokenRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutRequest,
    OAuthAuthorizeResponse,
    OAuthCallbackRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    TokenResponse,
    UserProfile,
    VerifyResetTokenResponse,
)
from app.services.audit_service import AuditAction, AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    register_data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings_service: SettingsService = Depends(get_settings_service),
) -> RegisterResponse:
    """
    Register a new user with email and password.

    Request Body:
        {
            "email": "user@example.com",
            "password": "SecurePassword123!",
            "full_name": "Nguyễn Văn A"
        }

    Response (201 Created):
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "name": "Nguyễn Văn A",
            "is_active": true,
            "created_at": "2025-12-27T10:30:00Z",
            "message": "Registration successful. You can now login."
        }

    Errors:
        - 400 Bad Request: Email already registered
        - 422 Unprocessable Entity: Invalid email format or password too short

    Flow:
        1. Validate email uniqueness
        2. Hash password with bcrypt (cost=12)
        3. Create user record
        4. Return user info with success message

    Security:
        - Password hashed with bcrypt (cost=12)
        - Email stored lowercase and trimmed
        - No email verification in V1 (per plan v2.2)

    Rate Limiting (per plan v2.2 Section 3.4):
        - 10 requests/minute per IP
        - 3 accounts/day per IP
    """
    # Initialize audit service
    audit_service = AuditService(db)

    # Normalize email (lowercase, trimmed)
    email = register_data.email.lower().strip()

    # ADR-027: Validate password meets minimum length requirement
    from app.utils.password_validator import validate_password_strength
    await validate_password_strength(register_data.password, settings_service)

    try:
        # Check if email already exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # Audit failed registration attempt
            await audit_service.log(
                action=AuditAction.USER_LOGIN_FAILED,  # Reusing existing action type
                details={
                    "email": email,
                    "failure_reason": "email_already_registered",
                    "action": "registration",
                },
                request=request,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Hash password with bcrypt (CPU-intensive — run in threadpool to avoid blocking)
        from starlette.concurrency import run_in_threadpool
        password_hash = await run_in_threadpool(get_password_hash, register_data.password)

        # Create new user
        new_user = User(
            email=email,
            password_hash=password_hash,
            full_name=register_data.full_name,
            is_active=True,  # No email verification in V1
        )
        db.add(new_user)

        await db.commit()
        await db.refresh(new_user)

        # Audit successful registration
        await audit_service.log(
            action=AuditAction.USER_CREATED,
            user_id=new_user.id,
            resource_type="user",
            resource_id=new_user.id,
            details={
                "email": new_user.email,
                "registration_method": "email",
            },
            request=request,
        )

        return RegisterResponse(
            id=new_user.id,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            message="Registration successful. You can now login.",
        )
    except SQLAlchemyOperationalError as exc:
        logger.error("Database unavailable in register: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable",
            headers={"Retry-After": "30"},
        )


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    login_data: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings_service: "SettingsService" = Depends(get_settings_service),
) -> TokenResponse:
    """
    Login with email and password.

    Sprint 63: Sets httpOnly cookies + returns tokens in body (dual mode).

    Request Body:
        {
            "email": "nguyen.van.anh@mtc.com.vn",
            "password": "SecurePassword123!"
        }

    Response (200 OK):
        Body: {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 3600
        }
        Cookies:
            - sdlc_access_token (httpOnly, 15 min)
            - sdlc_refresh_token (httpOnly, 7 days)

    Errors:
        - 401 Unauthorized: Invalid email or password
        - 403 Forbidden: User account is inactive

    Flow:
        1. Validate email/password
        2. Generate access token (15 min cookie, 1 hour body for legacy)
        3. Generate refresh token (7 days cookie, 30 days body for legacy)
        4. Store refresh token in database
        5. Set httpOnly cookies (Sprint 63)
        6. Update last_login_at timestamp
        7. Return tokens in body (backward compatibility)
    """
    # Initialize audit service
    audit_service = AuditService(db)

    try:
        # Find user by email
        result = await db.execute(select(User).where(User.email == login_data.email))
        user = result.scalar_one_or_none()

        # ADR-027: Check if account is locked (max_login_attempts)
        if user and user.locked_until:
            # Check if lockout period has expired (30 minutes auto-unlock)
            if datetime.now(timezone.utc) < user.locked_until:
                # Still locked - reject login
                await audit_service.log(
                    action=AuditAction.USER_LOGIN_FAILED,
                    user_id=user.id,
                    resource_type="user",
                    resource_id=user.id,
                    details={
                        "email": login_data.email,
                        "failure_reason": "account_locked",
                        "locked_until": user.locked_until.isoformat(),
                    },
                    request=request,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Account locked due to too many failed login attempts. Try again after {user.locked_until.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                )
            else:
                # Lockout expired - auto-unlock account
                user.failed_login_count = 0
                user.locked_until = None
                await db.commit()

        # Verify user exists and password is correct (bcrypt is CPU-intensive)
        from starlette.concurrency import run_in_threadpool
        if not user or not await run_in_threadpool(verify_password, login_data.password, user.password_hash):
            # ADR-027: Increment failed login counter if user exists
            if user:
                # Get max_login_attempts from settings (default: 5)
                max_attempts = await settings_service.get_max_login_attempts()

                user.failed_login_count += 1

                # Check if max attempts reached
                if user.failed_login_count >= max_attempts:
                    # Lock account for 30 minutes
                    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
                    await db.commit()

                    # Audit account lockout
                    await audit_service.log(
                        action=AuditAction.USER_LOGIN_FAILED,
                        user_id=user.id,
                        resource_type="user",
                        resource_id=user.id,
                        details={
                            "email": login_data.email,
                            "failure_reason": "max_attempts_exceeded",
                            "failed_login_count": user.failed_login_count,
                            "locked_until": user.locked_until.isoformat(),
                        },
                        request=request,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Account locked due to {max_attempts} failed login attempts. Try again after 30 minutes.",
                    )
                else:
                    # Not locked yet, just increment counter
                    await db.commit()

            # Audit failed login attempt
            await audit_service.log(
                action=AuditAction.USER_LOGIN_FAILED,
                details={
                    "email": login_data.email,
                    "failure_reason": "invalid_credentials",
                },
                request=request,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Check if user is active
        if not user.is_active:
            # Audit failed login (inactive account)
            await audit_service.log(
                action=AuditAction.USER_LOGIN_FAILED,
                user_id=user.id,
                resource_type="user",
                resource_id=user.id,
                details={
                    "email": login_data.email,
                    "failure_reason": "account_inactive",
                },
                request=request,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        # Generate JWT tokens (ADR-027: session_timeout from DB setting)
        access_token = await create_access_token(
            subject=str(user.id),
            settings_service=settings_service
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        # Store refresh token in database (for revocation support)
        # Hash the token with SHA-256 (64 chars) to fit database column
        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_api_key(refresh_token),  # SHA-256 hash (64 chars)
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        db.add(db_refresh_token)

        # Update last login timestamp
        user.last_login = datetime.utcnow()

        # ADR-027: Reset failed login counter on successful login
        user.failed_login_count = 0
        user.locked_until = None

        await db.commit()

        # Audit successful login
        await audit_service.log(
            action=AuditAction.USER_LOGIN,
            user_id=user.id,
            resource_type="user",
            resource_id=user.id,
            details={
                "email": user.email,
                "login_method": "password",
            },
            request=request,
        )

        # Sprint 63: Set httpOnly cookies for XSS protection
        set_auth_cookies(response, access_token, refresh_token)

        # Return tokens in body for backward compatibility (Vite dashboard)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        )
    except SQLAlchemyOperationalError as exc:
        logger.error("Database unavailable in login: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable",
            headers={"Retry-After": "30"},
        )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_access_token(
    response: Response,
    refresh_data: Optional[RefreshTokenRequest] = None,
    db: AsyncSession = Depends(get_db),
    refresh_token_cookie: Optional[str] = Cookie(None, alias=REFRESH_TOKEN_COOKIE_NAME),
    settings_service: SettingsService = Depends(get_settings_service),
) -> TokenResponse:
    """
    Refresh access token using refresh token.

    Sprint 63 Dual Mode: Accepts refresh token from cookie OR body.

    Request (Option A - Cookie - Sprint 63 preferred):
        Cookie: sdlc_refresh_token=eyJ...

    Request (Option B - Body - Legacy):
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }

    Response (200 OK):
        Body: {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 3600
        }
        Cookie: sdlc_access_token (new token)

    Errors:
        - 401 Unauthorized: Invalid or expired refresh token
        - 401 Unauthorized: Refresh token revoked

    Flow:
        1. Get refresh token from cookie OR body (priority: cookie)
        2. Decode and validate refresh token
        3. Check token type is "refresh"
        4. Verify token exists in database (not revoked)
        5. Generate new access token
        6. Set new access token cookie (Sprint 63)
        7. Return new tokens in body (backward compatibility)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
    )

    # Sprint 63: Get refresh token from cookie (priority) or body
    refresh_token: Optional[str] = None
    if refresh_token_cookie:
        refresh_token = refresh_token_cookie
    elif refresh_data and refresh_data.refresh_token:
        refresh_token = refresh_data.refresh_token

    if not refresh_token:
        raise credentials_exception

    try:
        # Decode refresh token
        payload = decode_token(refresh_token)

        # Extract user ID
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Token type must be "refresh"
        token_type: Optional[str] = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type (expected 'refresh')",
            )

    except Exception:
        raise credentials_exception

    # Check if refresh token exists in database (and not revoked)
    # Hash the token to match database storage
    token_hash = hash_api_key(refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == UUID(user_id),
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
        )
    )
    db_refresh_token = result.scalar_one_or_none()

    if not db_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or has been revoked",
        )

    # Check if refresh token is expired
    if db_refresh_token.expires_at and db_refresh_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    # Fetch user
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exception

    # Generate new access token (ADR-027: session_timeout from DB setting)
    access_token = await create_access_token(
        subject=str(user.id),
        settings_service=settings_service
    )

    # Sprint 63: Set new access token cookie
    set_access_token_cookie(response, access_token)

    # Return tokens in body for backward compatibility
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    logout_data: Optional[LogoutRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    refresh_token_cookie: Optional[str] = Cookie(None, alias=REFRESH_TOKEN_COOKIE_NAME),
) -> None:
    """
    Logout and revoke refresh token.

    Sprint 63 Dual Mode: Accepts refresh token from cookie OR body.

    Request (Option A - Cookie - Sprint 63):
        Cookie: sdlc_refresh_token=eyJ...

    Request (Option B - Body - Legacy):
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }

    Response (204 No Content):
        Clear-Cookie: sdlc_access_token
        Clear-Cookie: sdlc_refresh_token
        (empty body)

    Errors:
        - 401 Unauthorized: Invalid access token
        - 404 Not Found: Refresh token not found (only if body provided)

    Flow:
        1. Validate access token (current_user dependency)
        2. Get refresh token from cookie OR body
        3. Find and revoke refresh token in database
        4. Clear cookies (Sprint 63)
        5. Return 204 No Content
    """
    # Sprint 63: Get refresh token from cookie (priority) or body
    refresh_token: Optional[str] = None
    if refresh_token_cookie:
        refresh_token = refresh_token_cookie
    elif logout_data and logout_data.refresh_token:
        refresh_token = logout_data.refresh_token

    # If we have a refresh token, try to revoke it
    if refresh_token:
        # Hash the token to match database storage
        token_hash = hash_api_key(refresh_token)
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == current_user.id,
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked == False,
            )
        )
        db_refresh_token = result.scalar_one_or_none()

        if db_refresh_token:
            # Revoke refresh token
            db_refresh_token.is_revoked = True
            await db.commit()

    # Sprint 63: Clear httpOnly cookies
    clear_auth_cookies(response)

    # Audit logout
    audit_service = AuditService(db)
    await audit_service.log(
        action=AuditAction.USER_LOGOUT,
        user_id=current_user.id,
        resource_type="user",
        resource_id=current_user.id,
        details={"email": current_user.email},
        request=request,
    )

    # Return 204 No Content
    return None


@router.get("/me", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """
    Get current authenticated user profile.

    Headers:
        Authorization: Bearer <access_token>

    Response (200 OK):
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

    Errors:
        - 401 Unauthorized: Invalid or expired access token
        - 403 Forbidden: User account is inactive

    Flow:
        1. Validate access token (get_current_active_user dependency)
        2. Fetch user roles from database
        3. Fetch linked OAuth providers
        4. Return user profile
    """
    # Fetch user roles (Sprint 159.1 Fix: Return uppercase short names for frontend compatibility)
    # Frontend expects: ["CTO", "CPO", "CEO"] not ["Chief Technology Officer", ...]
    role_names = [role.name.upper() for role in current_user.roles]

    # Fetch OAuth providers
    oauth_providers = [oauth.provider for oauth in current_user.oauth_accounts]

    # ADR-065 D3: Fetch org memberships and compute effective_tier
    from app.models.organization import Organization, UserOrganization
    from app.schemas.auth import UserOrganizationInfo
    from sqlalchemy import select as sa_select

    org_memberships: list[UserOrganizationInfo] = []
    effective_tier = "free"

    # Superuser/platform_admin → always enterprise (ADR-065 D2)
    if current_user.is_superuser or current_user.is_platform_admin:
        effective_tier = "enterprise"

    # Query org memberships
    org_result = await db.execute(
        sa_select(
            Organization.id,
            Organization.name,
            Organization.slug,
            Organization.plan,
            UserOrganization.role,
            UserOrganization.joined_at,
        ).where(
            UserOrganization.user_id == current_user.id,
            UserOrganization.organization_id == Organization.id,
        )
    )
    org_rows = org_result.all()

    # ADR-065 D4: expanded TIER_RANK covering all ADR-059 plan strings
    tier_rank = {
        "enterprise": 4,
        "pro": 3, "professional": 3,
        "starter": 2, "standard": 2, "founder": 2,
        "free": 1, "lite": 1,
    }
    best_rank = 0
    is_admin = current_user.is_superuser or current_user.is_platform_admin

    for row in org_rows:
        org_memberships.append(UserOrganizationInfo(
            id=row[0],
            name=row[1],
            slug=row[2],
            plan=row[3] or "free",
            role=row[4] or "member",
            joined_at=row[5],
        ))
        plan = row[3] or "free"
        rank = tier_rank.get(plan, 1)
        if rank > best_rank:
            best_rank = rank
            if not is_admin:
                effective_tier = plan

    # No-op: effective_tier defaults to "free" already

    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        is_platform_admin=current_user.is_platform_admin,
        roles=role_names,
        oauth_providers=oauth_providers,
        effective_tier=effective_tier,
        organizations=org_memberships,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login,
    )


# =============================================================================
# OAuth 2.0 Endpoints (Sprint 59)
# =============================================================================


@router.get(
    "/oauth/{provider}/authorize",
    response_model=OAuthAuthorizeResponse,
    status_code=status.HTTP_200_OK,
)
async def oauth_authorize(
    provider: str,
    redirect_uri: str = None,
) -> OAuthAuthorizeResponse:
    """
    Get OAuth authorization URL for the specified provider.

    Path Parameters:
        - provider: OAuth provider ('github' or 'google')

    Query Parameters:
        - redirect_uri: Optional custom redirect URI (default: OAUTH_REDIRECT_URL)

    Response (200 OK):
        {
            "authorization_url": "https://github.com/login/oauth/authorize?...",
            "state": "random-state-string"
        }

    Errors:
        - 400 Bad Request: Invalid provider or provider not configured

    Flow:
        1. Generate state for CSRF protection
        2. Store state in Redis (10 min TTL)
        3. Build authorization URL
        4. Return URL and state
    """
    from app.services.oauth_service import oauth_service

    # Validate provider
    valid_providers = ["github", "google"]
    if provider not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OAuth provider. Valid options: {', '.join(valid_providers)}",
        )

    # Check if provider is configured
    if provider == "github" and not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub OAuth is not configured",
        )
    if provider == "google" and not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth is not configured",
        )

    # Use provider-specific redirect URI if not provided
    if provider == "github":
        final_redirect_uri = redirect_uri or settings.GITHUB_OAUTH_REDIRECT_URL
    else:
        final_redirect_uri = redirect_uri or settings.OAUTH_REDIRECT_URL

    # Generate base state (CSRF protection), then wrap provider metadata into an encoded state.
    # IMPORTANT: the provider redirect must receive the SAME state value we return to the frontend.
    import json
    import base64

    raw_state = oauth_service.generate_state()

    # For Google (PKCE), generate the verifier and persist it in the encoded state.
    code_verifier = oauth_service.generate_code_verifier() if provider == "google" else None

    state_data = {
        "provider": provider,
        "redirect_uri": final_redirect_uri,
        "code_verifier": code_verifier,
    }

    encoded_state = base64.urlsafe_b64encode(
        json.dumps({"state": raw_state, "data": state_data}).encode()
    ).decode()

    # Build authorization URL based on provider using encoded_state
    if provider == "github":
        authorization_url = oauth_service.get_github_auth_url(
            state=encoded_state,
            redirect_uri=final_redirect_uri,
        )
    else:  # google
        authorization_url = oauth_service.get_google_auth_url(
            state=encoded_state,
            redirect_uri=final_redirect_uri,
            code_verifier=code_verifier,
        )

    return OAuthAuthorizeResponse(
        authorization_url=authorization_url,
        state=encoded_state,
    )


@router.post(
    "/oauth/{provider}/callback",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def oauth_callback(
    provider: str,
    callback_data: OAuthCallbackRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings_service: SettingsService = Depends(get_settings_service),
) -> TokenResponse:
    """
    Handle OAuth callback and exchange code for tokens.

    Path Parameters:
        - provider: OAuth provider ('github' or 'google')

    Request Body:
        {
            "code": "authorization_code_from_provider",
            "state": "encoded_state_from_authorize"
        }

    Response (200 OK):
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 3600
        }

    Errors:
        - 400 Bad Request: Invalid state or provider
        - 401 Unauthorized: OAuth exchange failed
        - 500 Internal Server Error: User creation failed

    Flow:
        1. Validate state parameter
        2. Exchange code for OAuth tokens
        3. Get user info from provider
        4. Find or create user
        5. Link OAuth account
        6. Generate JWT tokens
    """
    import json
    import base64
    from app.services.oauth_service import oauth_service
    from app.models.user import OAuthAccount

    # Validate provider
    valid_providers = ["github", "google"]
    if provider not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OAuth provider. Valid options: {', '.join(valid_providers)}",
        )

    # Decode and validate state
    try:
        state_json = base64.urlsafe_b64decode(callback_data.state.encode()).decode()
        state_data = json.loads(state_json)
        original_state = state_data.get("state")
        stored_data = state_data.get("data", {})

        if stored_data.get("provider") != provider:
            raise ValueError("Provider mismatch")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )

    redirect_uri = stored_data.get("redirect_uri", settings.OAUTH_REDIRECT_URL)
    code_verifier = stored_data.get("code_verifier")

    # Exchange code for tokens
    try:
        if provider == "github":
            oauth_tokens = await oauth_service.exchange_github_code(
                code=callback_data.code,
                redirect_uri=redirect_uri,
            )
            user_info = await oauth_service.get_github_user_info(
                access_token=oauth_tokens.access_token
            )
        else:  # google
            if not code_verifier:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Code verifier missing for Google OAuth",
                )
            oauth_tokens = await oauth_service.exchange_google_code(
                code=callback_data.code,
                redirect_uri=redirect_uri,
                code_verifier=code_verifier,
            )
            user_info = await oauth_service.get_google_user_info(
                access_token=oauth_tokens.access_token
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    # Initialize audit service
    audit_service = AuditService(db)

    # Find existing user by email
    email = user_info.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        # Create new user
        user = User(
            email=email,
            full_name=user_info.name,
            avatar_url=user_info.avatar_url,
            is_active=True,
            password_hash=None,  # OAuth-only user, no password
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Audit user creation
        await audit_service.log(
            action=AuditAction.USER_CREATED,
            user_id=user.id,
            resource_type="user",
            resource_id=user.id,
            details={
                "email": user.email,
                "registration_method": f"oauth_{provider}",
            },
            request=request,
        )

    # Check if OAuth account already linked
    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == user.id,
            OAuthAccount.provider == provider,
        )
    )
    oauth_account = result.scalar_one_or_none()

    if oauth_account:
        # Update existing OAuth account
        oauth_account.access_token = oauth_tokens.access_token
        oauth_account.refresh_token = oauth_tokens.refresh_token
        oauth_account.expires_at = (
            datetime.utcnow() + timedelta(seconds=oauth_tokens.expires_in)
            if oauth_tokens.expires_in
            else None
        )
    else:
        # Create new OAuth account link
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_account_id=user_info.provider_account_id,
            access_token=oauth_tokens.access_token,
            refresh_token=oauth_tokens.refresh_token,
            expires_at=(
                datetime.utcnow() + timedelta(seconds=oauth_tokens.expires_in)
                if oauth_tokens.expires_in
                else None
            ),
        )
        db.add(oauth_account)

    # Generate JWT tokens (ADR-027: session_timeout from DB setting)
    access_token = await create_access_token(
        subject=str(user.id),
        settings_service=settings_service
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    # Store refresh token in database
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_api_key(refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(db_refresh_token)

    # Update last login timestamp
    user.last_login = datetime.utcnow()

    await db.commit()

    # Audit OAuth login
    await audit_service.log(
        action=AuditAction.USER_LOGIN,
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        details={
            "email": user.email,
            "login_method": f"oauth_{provider}",
        },
        request=request,
    )

    # Sprint 63: Set httpOnly cookies (XSS protection)
    # Cookies are set in addition to returning tokens in body for backward compatibility
    set_auth_cookies(response, access_token, refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
    )


@router.post(
    "/github/device",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def github_device_flow_init() -> dict:
    """
    Initiate GitHub OAuth Device Flow (for CLI/Desktop apps).

    This endpoint is designed for applications that cannot easily handle
    browser redirects (like CLI tools, VS Code extensions, desktop apps).

    Response (200 OK):
        {
            "device_code": "3584d83530557fdd1f46af8289938c8ef79f9dc5",
            "user_code": "WDJB-MJHT",
            "verification_uri": "https://github.com/login/device",
            "expires_in": 900,
            "interval": 5
        }

    Errors:
        - 400 Bad Request: GitHub device flow initiation failed
        - 500 Internal Server Error: Service unavailable

    Flow:
        1. Extension calls this endpoint to get device_code and user_code
        2. Extension shows user_code and verification_uri to user
        3. User visits https://github.com/login/device and enters user_code
        4. Extension polls POST /auth/github/token with device_code
        5. When user authorizes, token endpoint returns access_token
        6. Extension creates user session with access_token

    Usage:
        - VS Code Extension: Show user_code in notification, open browser
        - CLI: Print user_code and verification_uri, poll for token
        - Desktop App: Show dialog with user_code, poll for token

    Security:
        - device_code expires in 15 minutes (900 seconds)
        - user_code is 8 characters (format: XXXX-XXXX)
        - Polling interval should be respected to avoid rate limits
    """
    from app.services.oauth_service import oauth_service

    # Check if GitHub OAuth is configured
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub OAuth is not configured on this server",
        )

    try:
        device_flow_data = await oauth_service.initiate_github_device_flow()
        return device_flow_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except (ConnectionError, OSError) as e:
        logger.error("GitHub device flow service unavailable: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth service temporarily unavailable",
            headers={"Retry-After": "30"},
        )
    except Exception as e:
        logger.error("GitHub device flow error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate GitHub device flow",
        )


@router.post(
    "/github/token",
    status_code=status.HTTP_200_OK,
)
async def github_device_flow_poll(
    device_request: DeviceTokenRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings_service: SettingsService = Depends(get_settings_service),
):
    """
    Poll for GitHub device authorization completion.

    Request Body:
        {
            "device_code": "3584d83530557fdd1f46af8289938c8ef79f9dc5"
        }

    Response (200 OK - when authorized):
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 28800
        }

    Response (400 Bad Request - polling states):
        {
            "detail": "error:authorization_pending"  # User hasn't authorized yet
        }
        {
            "detail": "error:slow_down"  # Polling too fast
        }
        {
            "detail": "error:expired_token"  # Device code expired
        }
        {
            "detail": "error:access_denied"  # User denied authorization
        }

    Errors:
        - 400 Bad Request: Missing device_code
        - 400 Bad Request: Polling error (see detail for error code)
        - 500 Internal Server Error: User creation failed

    Polling Logic:
        1. Poll every `interval` seconds (from device flow response)
        2. If "authorization_pending": Continue polling
        3. If "slow_down": Increase interval by 5 seconds
        4. If "expired_token" or "access_denied": Stop polling, show error
        5. If success (200 OK with tokens): Stop polling, store tokens

    Flow:
        1. Extension polls this endpoint with device_code
        2. Backend calls GitHub to check if user authorized
        3. If authorized: Create/link user, return JWT tokens
        4. If not yet: Return authorization_pending (400)
        5. Extension continues polling until success or error
    """
    from app.services.oauth_service import oauth_service
    from app.models.user import OAuthAccount
    from fastapi.responses import JSONResponse

    # Initialize audit service
    audit_service = AuditService(db)

    try:
        # Poll GitHub for device authorization
        oauth_tokens = await oauth_service.poll_github_device_token(device_request.device_code)

        # Get user info from GitHub
        user_info = await oauth_service.get_github_user_info(oauth_tokens.access_token)

        # Find existing user by email
        email = user_info.email.lower().strip()
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            # Create new user
            user = User(
                email=email,
                full_name=user_info.name,
                avatar_url=user_info.avatar_url,
                is_active=True,
                password_hash=None,  # OAuth-only user
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            # Audit user creation
            await audit_service.log(
                action=AuditAction.USER_CREATED,
                user_id=user.id,
                resource_type="user",
                resource_id=user.id,
                details={
                    "email": user.email,
                    "registration_method": "oauth_github_device",
                },
                request=request,
            )

        # Check if OAuth account already linked
        result = await db.execute(
            select(OAuthAccount).where(
                OAuthAccount.user_id == user.id,
                OAuthAccount.provider == "github",
            )
        )
        oauth_account = result.scalar_one_or_none()

        if oauth_account:
            # Update existing OAuth account
            oauth_account.access_token = oauth_tokens.access_token
            oauth_account.refresh_token = oauth_tokens.refresh_token
            oauth_account.expires_at = (
                datetime.utcnow() + timedelta(seconds=oauth_tokens.expires_in)
                if oauth_tokens.expires_in
                else None
            )
        else:
            # Create new OAuth account link
            oauth_account = OAuthAccount(
                user_id=user.id,
                provider="github",
                provider_account_id=user_info.provider_account_id,
                access_token=oauth_tokens.access_token,
                refresh_token=oauth_tokens.refresh_token,
                expires_at=(
                    datetime.utcnow() + timedelta(seconds=oauth_tokens.expires_in)
                    if oauth_tokens.expires_in
                    else None
                ),
            )
            db.add(oauth_account)

        # Generate JWT tokens
        access_token = await create_access_token(
            subject=str(user.id),
            settings_service=settings_service
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        # Store refresh token in database
        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_api_key(refresh_token),
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        db.add(db_refresh_token)

        # Update last login timestamp
        user.last_login = datetime.utcnow()

        await db.commit()

        # Audit OAuth login
        await audit_service.log(
            action=AuditAction.USER_LOGIN,
            user_id=user.id,
            resource_type="user",
            resource_id=user.id,
            details={
                "email": user.email,
                "login_method": "oauth_github_device",
            },
            request=request,
        )

        # Set httpOnly cookies for XSS protection
        if response:
            set_auth_cookies(response, access_token, refresh_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        )

    except ValueError as e:
        error_message = str(e)

        # Check if this is a polling error (authorization_pending, slow_down, etc.)
        if error_message.startswith("error:"):
            error_code = error_message.replace("error:", "")
            # Return error in the format Extension expects: {"error": "code"}
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": error_code},
            )

        # Other ValueError (e.g., user info retrieval failed)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )

    except (ConnectionError, OSError) as e:
        logger.error("GitHub device token poll service unavailable: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
            headers={"Retry-After": "30"},
        )
    except Exception as e:
        logger.error("GitHub device token poll error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process GitHub device authorization",
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def auth_health_check() -> dict:
    """
    Authentication service health check.

    Response (200 OK):
        {
            "status": "healthy",
            "service": "authentication",
            "version": "1.0.0"
        }

    Usage:
        - Kubernetes liveness probe
        - Monitoring/alerting systems
        - CI/CD health validation
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "version": settings.APP_VERSION,
    }


# =============================================================================
# Password Reset Endpoints (Sprint 60)
# =============================================================================


@router.post("/forgot-password", response_model=ForgotPasswordResponse, status_code=status.HTTP_200_OK)
async def forgot_password(
    forgot_data: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ForgotPasswordResponse:
    """
    Initiate password reset by sending reset link to email.

    Request Body:
        {
            "email": "user@example.com"
        }

    Response (200 OK - always, for email enumeration protection):
        {
            "message": "If an account with this email exists, you will receive a password reset link.",
            "email": "user@example.com"
        }

    Flow:
        1. Look up user by email
        2. If user exists and is active:
           a. Generate secure reset token (64-byte URL-safe)
           b. Store SHA-256 hash in database (1-hour expiry)
           c. Send email with reset link
        3. Always return 200 OK (prevents email enumeration)

    Security:
        - Always returns success (prevents email enumeration attacks)
        - Token is SHA-256 hashed before storage
        - Token expires in 1 hour
        - Rate limited: 3 requests/email/hour (recommended)
    """
    audit_service = AuditService(db)
    email = forgot_data.email.lower().strip()

    # Look up user by email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Always return the same response (email enumeration protection)
    response = ForgotPasswordResponse(
        message="If an account with this email exists, you will receive a password reset link.",
        email=email,
    )

    # If user doesn't exist or is inactive, log and return (don't reveal info)
    if not user or not user.is_active:
        await audit_service.log(
            action=AuditAction.USER_LOGIN_FAILED,  # Reusing for audit
            details={
                "email": email,
                "action": "forgot_password",
                "failure_reason": "user_not_found_or_inactive",
            },
            request=request,
        )
        return response

    # Check if user has a password (OAuth-only users can't reset password)
    if not user.password_hash:
        await audit_service.log(
            action=AuditAction.USER_LOGIN_FAILED,
            user_id=user.id,
            details={
                "email": email,
                "action": "forgot_password",
                "failure_reason": "oauth_only_user",
            },
            request=request,
        )
        return response

    # Generate reset token
    token, token_hash = generate_password_reset_token()

    # Get client IP and user agent for audit
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:512]

    # Invalidate any existing unused tokens for this user
    await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=datetime.utcnow())  # Mark as "used" to invalidate (naive datetime to match column)
    )

    # Create new password reset token (1-hour expiry)
    # Using naive datetime to match PasswordResetToken.expires_at column type
    expires_at = datetime.utcnow() + timedelta(hours=1)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    db.add(reset_token)
    await db.commit()

    # Send password reset email in background thread (non-blocking)
    import threading

    # Capture values needed for email (avoid accessing db objects in thread)
    user_email = user.email
    user_name = user.full_name
    frontend_url = getattr(settings, "FRONTEND_URL", "https://sdlc.nhatquangholding.com")
    reset_url = f"{frontend_url}/reset-password?token={token}"

    def send_email_sync():
        """Sync function to send email in background thread."""
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            smtp_host = getattr(settings, "SMTP_HOST", None)
            smtp_port = int(getattr(settings, "SMTP_PORT", 587))
            smtp_user = getattr(settings, "SMTP_USER", None)
            smtp_password = getattr(settings, "SMTP_PASSWORD", None)
            smtp_use_tls = getattr(settings, "SMTP_USE_TLS", True)
            from_email = getattr(settings, "SMTP_FROM_EMAIL", "noreply@sdlc-orchestrator.com")
            from_name = getattr(settings, "SMTP_FROM_NAME", "SDLC Orchestrator")

            if not smtp_host or not smtp_user:
                print(f"\n{'='*60}")
                print(f"[PASSWORD RESET] Email: {user_email}")
                print(f"[PASSWORD RESET] Link: {reset_url}")
                print(f"{'='*60}\n")
                return

            # Build email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Reset Your Password - SDLC Orchestrator"
            msg["From"] = f"{from_name} <{from_email}>"
            msg["To"] = user_email

            text_content = f"Hello {user_name or user_email},\n\nClick to reset: {reset_url}\n\nExpires in 1 hour."
            html_content = f'<p>Hello {user_name or user_email},</p><p><a href="{reset_url}">Reset Password</a></p><p>Expires in 1 hour.</p>'

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                if smtp_use_tls:
                    server.starttls()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.sendmail(from_email, user_email, msg.as_string())
            logger.info(f"Password reset email sent to {user_email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user_email}: {e}")

    email_thread = threading.Thread(target=send_email_sync, daemon=True)
    email_thread.start()
    logger.info(f"Password reset email queued for {email}")

    # Audit successful password reset request
    await audit_service.log(
        action=AuditAction.USER_UPDATED,  # Reusing for password reset
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        details={
            "email": email,
            "action": "forgot_password",
            "token_id": str(reset_token.id),
        },
        request=request,
    )

    return response


@router.get("/verify-reset-token", response_model=VerifyResetTokenResponse, status_code=status.HTTP_200_OK)
async def verify_reset_token(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> VerifyResetTokenResponse:
    """
    Verify password reset token validity.

    Query Parameters:
        token: Password reset token from email link

    Response (200 OK - valid token):
        {
            "valid": true,
            "email": "user@example.com",
            "expires_at": "2025-12-29T15:00:00Z"
        }

    Response (200 OK - invalid/expired token):
        {
            "valid": false,
            "email": null,
            "expires_at": null,
            "error": "Token has expired"
        }

    Usage:
        Frontend calls this when user clicks reset link to check if token is valid
        before showing the password reset form.
    """
    # Hash the token to look up in database
    token_hash = hash_reset_token(token)

    # Find the reset token
    result = await db.execute(
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == token_hash)
    )
    reset_token = result.scalar_one_or_none()

    # Token not found
    if not reset_token:
        return VerifyResetTokenResponse(
            valid=False,
            email=None,
            expires_at=None,
            error="Invalid or expired token",
        )

    # Token already used
    if reset_token.is_used:
        return VerifyResetTokenResponse(
            valid=False,
            email=None,
            expires_at=None,
            error="Token has already been used",
        )

    # Token expired - debug logging
    from datetime import timezone as tz
    now_utc = datetime.now(tz.utc)
    expires = reset_token.expires_at
    if expires.tzinfo is None:
        expires_aware = expires.replace(tzinfo=tz.utc)
    else:
        expires_aware = expires
    print(f"[DEBUG] Token expires_at: {reset_token.expires_at} (raw)")
    print(f"[DEBUG] Token expires_aware: {expires_aware}")
    print(f"[DEBUG] Now UTC: {now_utc}")
    print(f"[DEBUG] is_expired result: {reset_token.is_expired}")
    print(f"[DEBUG] expires_aware <= now_utc: {expires_aware <= now_utc}")

    if reset_token.is_expired:
        return VerifyResetTokenResponse(
            valid=False,
            email=None,
            expires_at=None,
            error="Token has expired",
        )

    # Get user email
    result = await db.execute(select(User).where(User.id == reset_token.user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        return VerifyResetTokenResponse(
            valid=False,
            email=None,
            expires_at=None,
            error="User account not found or inactive",
        )

    return VerifyResetTokenResponse(
        valid=True,
        email=user.email,
        expires_at=reset_token.expires_at,
        error=None,
    )


@router.post("/reset-password", response_model=ResetPasswordResponse, status_code=status.HTTP_200_OK)
async def reset_password(
    reset_data: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ResetPasswordResponse:
    """
    Reset password using valid token.

    Request Body:
        {
            "token": "abc123...",
            "new_password": "NewSecurePassword123!"
        }

    Response (200 OK):
        {
            "message": "Password has been reset successfully. You can now login with your new password.",
            "email": "user@example.com"
        }

    Errors:
        - 400 Bad Request: Invalid, expired, or already used token
        - 422 Unprocessable Entity: Password too short

    Flow:
        1. Validate reset token
        2. Check token is not expired or used
        3. Update user password (bcrypt hash)
        4. Mark token as used
        5. Revoke all existing sessions (refresh tokens)
        6. Return success message

    Security:
        - Token marked as used immediately after password reset
        - All existing sessions revoked (security best practice)
        - Password hashed with bcrypt (cost=12)
    """
    audit_service = AuditService(db)

    # Hash the token to look up in database
    token_hash = hash_reset_token(reset_data.token)

    try:
        # Find the reset token
        result = await db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hash)
        )
        reset_token = result.scalar_one_or_none()

        # Token not found
        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token",
            )

        # Token already used
        if reset_token.is_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has already been used",
            )

        # Token expired
        if reset_token.is_expired:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has expired",
            )

        # Get user
        result = await db.execute(select(User).where(User.id == reset_token.user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account not found or inactive",
            )

        # Hash new password (CPU-intensive — run in threadpool to avoid blocking)
        from starlette.concurrency import run_in_threadpool
        new_password_hash = await run_in_threadpool(get_password_hash, reset_data.new_password)

        # Update user password
        user.password_hash = new_password_hash
        user.updated_at = datetime.utcnow()

        # Mark token as used (naive datetime to match column type)
        reset_token.used_at = datetime.utcnow()

        # Revoke all existing refresh tokens (security: logout all sessions)
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user.id,
                RefreshToken.is_revoked == False,
            )
            .values(is_revoked=True)
        )

        await db.commit()

        # Audit successful password reset
        await audit_service.log(
            action=AuditAction.USER_UPDATED,
            user_id=user.id,
            resource_type="user",
            resource_id=user.id,
            details={
                "email": user.email,
                "action": "password_reset",
                "token_id": str(reset_token.id),
                "sessions_revoked": True,
            },
            request=request,
        )

        return ResetPasswordResponse(
            message="Password has been reset successfully. You can now login with your new password.",
            email=user.email,
        )
    except SQLAlchemyOperationalError as exc:
        logger.error("Database unavailable in reset-password: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable",
            headers={"Retry-After": "30"},
        )


async def _send_password_reset_email(user: User, token: str, request: Request) -> None:
    """
    Send password reset email to user.

    Args:
        user: User object
        token: Plain text reset token (not hashed)
        request: HTTP request for building reset URL

    Note:
        Uses SMTP if configured, otherwise logs the reset link.
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    # Build reset URL
    # Use frontend URL from settings or construct from request
    frontend_url = getattr(settings, "FRONTEND_URL", "https://sdlc.nhatquangholding.com")
    reset_url = f"{frontend_url}/reset-password?token={token}"

    # Check if SMTP is configured
    smtp_host = getattr(settings, "SMTP_HOST", None)
    smtp_port = getattr(settings, "SMTP_PORT", 587)
    smtp_user = getattr(settings, "SMTP_USER", None)
    smtp_password = getattr(settings, "SMTP_PASSWORD", None)
    smtp_use_tls = getattr(settings, "SMTP_USE_TLS", True)
    from_email = getattr(settings, "SMTP_FROM_EMAIL", "noreply@sdlc-orchestrator.com")
    from_name = getattr(settings, "SMTP_FROM_NAME", "SDLC Orchestrator")

    if not smtp_host or not smtp_user:
        # SMTP not configured - print the reset link for testing (visible in docker logs)
        print(f"\n{'='*60}")
        print(f"[PASSWORD RESET] Email: {user.email}")
        print(f"[PASSWORD RESET] Link: {reset_url}")
        print(f"{'='*60}\n")
        logger.warning(f"[SMTP not configured] Password reset link for {user.email}: {reset_url}")
        return

    # Build email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset Your Password - SDLC Orchestrator"
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = user.email

    # Plain text version
    text_content = f"""
Hello {user.full_name or user.email},

You requested to reset your password for SDLC Orchestrator.

Click the link below to reset your password (valid for 1 hour):

{reset_url}

If you did not request this password reset, please ignore this email.
Your password will remain unchanged.

---
SDLC Orchestrator
https://sdlc.nhatquangholding.com
"""

    # HTML version
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #3b82f6; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
        .content {{ background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
        .button {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        .button:hover {{ background: #2563eb; }}
        .footer {{ background: #f3f4f6; padding: 15px; font-size: 12px; color: #6b7280; border-radius: 0 0 8px 8px; text-align: center; }}
        .warning {{ color: #9ca3af; font-size: 13px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0; font-size: 24px;">Reset Your Password</h1>
        </div>
        <div class="content">
            <p>Hello {user.full_name or user.email},</p>
            <p>You requested to reset your password for SDLC Orchestrator.</p>
            <p>Click the button below to reset your password:</p>
            <p style="text-align: center;">
                <a href="{reset_url}" class="button">Reset Password</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background: #e5e7eb; padding: 10px; border-radius: 4px; font-size: 12px;">
                {reset_url}
            </p>
            <p class="warning">
                This link will expire in 1 hour.<br>
                If you did not request this password reset, please ignore this email.
            </p>
        </div>
        <div class="footer">
            <p>&copy; 2025 SDLC Orchestrator. All rights reserved.</p>
            <p><a href="https://sdlc.nhatquangholding.com">https://sdlc.nhatquangholding.com</a></p>
        </div>
    </div>
</body>
</html>
"""

    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    # Send email
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_use_tls:
                server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.sendmail(from_email, user.email, msg.as_string())
        logger.info(f"Password reset email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")
        raise
