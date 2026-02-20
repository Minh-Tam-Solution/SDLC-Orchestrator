"""
Enterprise SSO API routes — Sprint 183.

6 endpoints per API Spec v3.7.0 Section 12:
    POST   /api/v1/enterprise/sso/configure        — Create/update SSO config (ENTERPRISE)
    GET    /api/v1/enterprise/sso/saml/metadata    — SP metadata XML (public)
    POST   /api/v1/enterprise/sso/saml/login       — Initiate SAML login
    POST   /api/v1/enterprise/sso/saml/callback    — SAML ACS callback (IdP → SP)
    GET    /api/v1/enterprise/sso/azure-ad/login   — Initiate Azure AD PKCE login
    GET    /api/v1/enterprise/sso/azure-ad/callback — Azure AD OAuth2 callback
    POST   /api/v1/enterprise/sso/logout           — Delete SSO session

Security:
    - configure: JWT required + ENTERPRISE tier gate (HTTP 402 if tier < enterprise)
    - saml/metadata: PUBLIC (no auth — IT admin downloads for IdP registration)
    - saml/login, azure-ad/login: JWT required
    - saml/callback, azure-ad/callback: NO JWT (IdP/Azure AD posts directly)
    - logout: JWT required

ADR-061 compliance:
    D-2: ACS URL = /api/v1/enterprise/sso/saml/callback
    D-3: JIT provisioning from SAML NameID / OIDC email claim
    D-5: SHA256(id_token) only — raw id_token never stored or returned

Sprint 183 — ADR-061 implementation.
"""

from __future__ import annotations

import logging
import os
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, require_enterprise_tier
from app.db.session import get_db
from app.models.user import User
from app.schemas.enterprise_sso import (
    SsoConfigCreate,
    SsoConfigResponse,
    SsoLoginInitiateRequest,
    SsoLoginResponse,
    SsoLogoutRequest,
    SsoSessionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/enterprise/sso",
    tags=["Enterprise SSO"],
)

# Dashboard redirect URL after successful SSO login (configurable via ENV)
_SSO_SUCCESS_REDIRECT = os.getenv(
    "SSO_SUCCESS_REDIRECT_URL", "/dashboard?sso=success"
)
_SSO_ERROR_REDIRECT = os.getenv(
    "SSO_ERROR_REDIRECT_URL", "/login?error=sso_failed"
)


# ──────────────────────────────────────────────────────────────────────────────
# POST /configure — Create or update SSO configuration
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/configure",
    response_model=SsoConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Configure enterprise SSO for an organization",
    description=(
        "Create or replace the SSO configuration for an organization. "
        "Requires ENTERPRISE tier (HTTP 402 if tier < enterprise). "
        "Raises 409 if a config for (org, provider) already exists — use PUT to update."
    ),
    dependencies=[Depends(require_enterprise_tier)],
)
async def configure_sso(
    config: SsoConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SsoConfigResponse:
    """
    Create or update SSO configuration for an organization.

    Args:
        config: SSO configuration payload (provider, IdP fields, role_mapping).
        db:     Async database session.

    Returns:
        Persisted SsoConfigResponse.

    Raises:
        HTTP 402: ENTERPRISE tier required.
        HTTP 409: Config already exists for (organization_id, provider).
    """
    from app.models.enterprise_sso import EnterpriseSsoConfig

    # Check for existing config (uq_sso_config_org_provider constraint)
    stmt = select(EnterpriseSsoConfig).where(
        EnterpriseSsoConfig.organization_id == config.organization_id,
        EnterpriseSsoConfig.provider == config.provider,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"SSO config for provider '{config.provider}' already exists for this "
                f"organization. Delete the existing config before creating a new one, "
                f"or update it via PATCH."
            ),
        )

    sso_config = EnterpriseSsoConfig(
        organization_id=config.organization_id,
        provider=config.provider,
        is_enabled=config.is_enabled,
        idp_entity_id=config.idp_entity_id,
        idp_sso_url=config.idp_sso_url,
        idp_x509_cert=config.idp_x509_cert,
        sp_entity_id=config.sp_entity_id,
        tenant_id=config.tenant_id,
        client_id=config.client_id,
        role_mapping=config.role_mapping or {},
    )
    db.add(sso_config)
    await db.commit()
    await db.refresh(sso_config)

    logger.info(
        "enterprise_sso: configured provider=%s org=%s by user=%s",
        config.provider,
        config.organization_id,
        current_user.id,
    )
    return SsoConfigResponse.model_validate(sso_config)


# ──────────────────────────────────────────────────────────────────────────────
# GET /saml/metadata — SP metadata XML (public)
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/saml/metadata",
    summary="Get SAML SP metadata XML",
    description=(
        "Returns the Service Provider metadata XML for a given organization. "
        "IT administrators download this and upload it to their IdP (Okta, Azure AD, etc.). "
        "No authentication required — publicly accessible by design."
    ),
    responses={
        200: {"content": {"application/xml": {}}},
        404: {"description": "No SAML config found for this organization"},
    },
)
async def saml_metadata(
    organization_id: UUID = Query(..., description="Organization UUID"),
    db: AsyncSession = Depends(get_db),
) -> PlainTextResponse:
    """
    Return SP metadata XML for IdP registration.

    Public endpoint — no authentication required.
    Rate limited by RateLimiterMiddleware (200 req/min per IP, inherited from app).

    Args:
        organization_id: Organization UUID query parameter.
        db:              Async database session.

    Returns:
        XML response with SP metadata.

    Raises:
        HTTP 404: No SAML SSO config found for this organization.
        HTTP 503: python3-saml not installed or metadata generation error.
    """
    from app.models.enterprise_sso import EnterpriseSsoConfig
    from app.services.sso.saml_service import SAMLConfigError, SAMLService

    stmt = select(EnterpriseSsoConfig).where(
        EnterpriseSsoConfig.organization_id == organization_id,
        EnterpriseSsoConfig.provider == "saml",
        EnterpriseSsoConfig.is_enabled.is_(True),
    )
    result = await db.execute(stmt)
    sso_config = result.scalar_one_or_none()

    if not sso_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active SAML config found for organization {organization_id}",
        )

    try:
        svc = SAMLService(sso_config)
        metadata_xml = svc.get_metadata()
    except SAMLConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"SAML metadata generation failed: {exc}",
        )

    return PlainTextResponse(
        content=metadata_xml,
        media_type="application/xml",
    )


# ──────────────────────────────────────────────────────────────────────────────
# POST /saml/login — Initiate SAML SP-initiated login
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/saml/login",
    response_model=SsoLoginResponse,
    summary="Initiate SAML SP-initiated login",
    description=(
        "Returns the IdP redirect URL for SP-initiated SAML flow. "
        "The caller must redirect the user's browser to redirect_url."
    ),
)
async def saml_login(
    body: SsoLoginInitiateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SsoLoginResponse:
    """
    Initiate SAML SP-initiated login flow.

    Returns the IdP redirect URL. The client application must redirect
    the browser to this URL to begin the SAML exchange.

    Args:
        body:         Contains organization_id.
        request:      FastAPI Request (used to build request_data for python3-saml).
        db:           Async database session.
        current_user: Authenticated user (may be pre-existing session or unauthenticated).

    Returns:
        SsoLoginResponse with redirect_url pointing to IdP.

    Raises:
        HTTP 404: No active SAML config for this organization.
        HTTP 503: SAML library error.
    """
    from app.models.enterprise_sso import EnterpriseSsoConfig
    from app.services.sso.saml_service import SAMLConfigError, SAMLError, SAMLService

    stmt = select(EnterpriseSsoConfig).where(
        EnterpriseSsoConfig.organization_id == body.organization_id,
        EnterpriseSsoConfig.provider == "saml",
        EnterpriseSsoConfig.is_enabled.is_(True),
    )
    result = await db.execute(stmt)
    sso_config = result.scalar_one_or_none()

    if not sso_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active SAML config for organization {body.organization_id}",
        )

    # Build python3-saml request_data from FastAPI Request
    request_data = _build_saml_request_data(request)

    try:
        svc = SAMLService(sso_config)
        redirect_url = svc.initiate_login(request_data)
    except (SAMLConfigError, SAMLError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"SAML login initiation failed: {exc}",
        )

    logger.info(
        "enterprise_sso: saml login initiated org=%s user=%s",
        body.organization_id,
        current_user.id,
    )
    return SsoLoginResponse(redirect_url=redirect_url, provider="saml")


# ──────────────────────────────────────────────────────────────────────────────
# POST /saml/callback — SAML ACS callback (IdP → SP)
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/saml/callback",
    summary="SAML ACS callback — process assertion from IdP",
    description=(
        "Assertion Consumer Service endpoint. The IdP posts a SAML Response here "
        "after the user authenticates. No JWT required (IdP cannot send auth headers). "
        "On success: JIT provisions user, creates SsoSession, redirects to dashboard."
    ),
    include_in_schema=False,  # Hide from Swagger — IdP-facing, not developer-facing
)
async def saml_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """
    Process SAML ACS callback from Identity Provider.

    This endpoint is called directly by the IdP after authentication.
    No JWT authentication — IdP posts form data with SAMLResponse.

    Pipeline:
    1. Extract organization_id from RelayState
    2. Load EnterpriseSsoConfig for (org, provider='saml')
    3. Validate SAML assertion (signature, timestamps, NameID)
    4. JIT provision user + create SsoSession
    5. Redirect to dashboard

    Args:
        request: FastAPI Request (contains SAMLResponse form field + RelayState).
        db:      Async database session.

    Returns:
        RedirectResponse → dashboard or error page.
    """
    from app.models.enterprise_sso import EnterpriseSsoConfig
    from app.services.sso.saml_service import SAMLConfigError, SAMLError, SAMLService

    # Build python3-saml request_data from POST body.
    # post_data must be populated with the full form payload (SAMLResponse, RelayState)
    # before passing to OneLogin_Saml2_Auth.process_response().
    form_data = await request.form()
    request_data = _build_saml_request_data(request)
    request_data["post_data"] = dict(form_data)

    # Extract organization_id from RelayState (set during SP-initiated login)
    relay_state: str = form_data.get("RelayState", "")
    organization_id = _extract_org_from_relay_state(relay_state)

    if not organization_id:
        logger.warning(
            "enterprise_sso: saml_callback missing or invalid RelayState=%s",
            relay_state,
        )
        return RedirectResponse(
            url=f"{_SSO_ERROR_REDIRECT}&reason=invalid_relay_state",
            status_code=status.HTTP_302_FOUND,
        )

    stmt = select(EnterpriseSsoConfig).where(
        EnterpriseSsoConfig.organization_id == organization_id,
        EnterpriseSsoConfig.provider == "saml",
        EnterpriseSsoConfig.is_enabled.is_(True),
    )
    result = await db.execute(stmt)
    sso_config = result.scalar_one_or_none()

    if not sso_config:
        logger.warning(
            "enterprise_sso: saml_callback no config org=%s", organization_id
        )
        return RedirectResponse(
            url=f"{_SSO_ERROR_REDIRECT}&reason=no_sso_config",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        svc = SAMLService(sso_config)
        user, session = await svc.process_callback(request_data, db)
    except SAMLError as exc:
        logger.warning(
            "enterprise_sso: saml_callback validation failed org=%s error=%s",
            organization_id,
            str(exc),
        )
        return RedirectResponse(
            url=f"{_SSO_ERROR_REDIRECT}&reason=saml_invalid",
            status_code=status.HTTP_302_FOUND,
        )
    except SAMLConfigError as exc:
        logger.error(
            "enterprise_sso: saml_callback config error org=%s error=%s",
            organization_id,
            str(exc),
        )
        return RedirectResponse(
            url=f"{_SSO_ERROR_REDIRECT}&reason=config_error",
            status_code=status.HTTP_302_FOUND,
        )

    logger.info(
        "enterprise_sso: saml_callback success user=%s org=%s session=%s",
        user.id,
        organization_id,
        session.id,
    )
    return RedirectResponse(
        url=f"{_SSO_SUCCESS_REDIRECT}&session_id={session.id}",
        status_code=status.HTTP_302_FOUND,
    )


# ──────────────────────────────────────────────────────────────────────────────
# GET /azure-ad/login — Initiate Azure AD PKCE login
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/azure-ad/login",
    response_model=SsoLoginResponse,
    summary="Initiate Azure AD PKCE login",
    description=(
        "Returns the Azure AD authorization URL with PKCE S256 code_challenge. "
        "The caller must redirect the browser to redirect_url. "
        "Stores (code_verifier, state) in Redis with 5-min TTL."
    ),
)
async def azure_ad_login(
    request: Request,
    organization_id: UUID = Query(..., description="Organization UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SsoLoginResponse:
    """
    Initiate Azure AD Authorization Code + PKCE S256 flow.

    Generates PKCE code_verifier and CSRF state token.
    Stores both in Redis (key: sso:pkce:{state}) with 5-min TTL.
    Returns the Azure AD authorization URL for browser redirect.

    Args:
        organization_id: Organization UUID query parameter.
        db:              Async database session.
        current_user:    Authenticated user initiating the SSO flow.

    Returns:
        SsoLoginResponse with redirect_url (Azure AD) and state (CSRF token).

    Raises:
        HTTP 404: No active Azure AD config for this organization.
        HTTP 503: Azure AD service error.
    """
    from app.models.enterprise_sso import EnterpriseSsoConfig
    from app.services.sso.azure_ad_service import AzureADConfigError, AzureADService
    from app.utils.redis import get_redis_client

    stmt = select(EnterpriseSsoConfig).where(
        EnterpriseSsoConfig.organization_id == organization_id,
        EnterpriseSsoConfig.provider == "azure_ad",
        EnterpriseSsoConfig.is_enabled.is_(True),
    )
    result = await db.execute(stmt)
    sso_config = result.scalar_one_or_none()

    if not sso_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active Azure AD config for organization {organization_id}",
        )

    # Compute absolute redirect_uri from the incoming request host.
    # Azure AD requires an absolute URL matching the app registration
    # (relative paths cause AADSTS50011: redirect_uri mismatch).
    _callback_path = "/api/v1/enterprise/sso/azure-ad/callback"
    redirect_uri = str(request.base_url).rstrip("/") + _callback_path

    try:
        svc = AzureADService(sso_config)
        auth_url, code_verifier, state = svc.initiate_login(redirect_uri=redirect_uri)
    except AzureADConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Azure AD login initiation failed: {exc}",
        )

    # Store PKCE state in Redis: key = sso:pkce:{state}, value = {verifier, org_id, redirect_uri}
    # redirect_uri stored so token exchange uses the same absolute URI (RFC 6749 §4.1.3).
    # TTL = 300s (5 minutes) per ADR-061 D-1
    try:
        redis = await get_redis_client()
        import json
        pkce_data = json.dumps({
            "code_verifier": code_verifier,
            "organization_id": str(organization_id),
            "redirect_uri": redirect_uri,
        })
        await redis.setex(f"sso:pkce:{state}", 300, pkce_data)
    except Exception as exc:
        logger.error(
            "enterprise_sso: azure_ad_login redis store failed state=%s error=%s",
            state,
            str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SSO state storage unavailable — try again",
        )

    logger.info(
        "enterprise_sso: azure_ad login initiated org=%s user=%s",
        organization_id,
        current_user.id,
    )
    return SsoLoginResponse(
        redirect_url=auth_url,
        provider="azure_ad",
        state=state,
    )


# ──────────────────────────────────────────────────────────────────────────────
# GET /azure-ad/callback — Azure AD OAuth2 callback
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/azure-ad/callback",
    summary="Azure AD OAuth2 callback",
    description=(
        "Azure AD redirects to this endpoint with ?code=...&state=... "
        "after the user authenticates. No JWT required. "
        "Validates state, exchanges code for id_token, JIT provisions user, "
        "creates SsoSession, redirects to dashboard."
    ),
    include_in_schema=False,  # IdP-facing endpoint — hide from Swagger
)
async def azure_ad_callback(
    code: str = Query(default=None, description="Authorization code from Azure AD"),
    state: str = Query(default=None, description="CSRF state token"),
    error: str = Query(default=None, description="Error code from Azure AD"),
    error_description: str = Query(default=None, description="Error description"),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """
    Process Azure AD OAuth2 callback.

    Azure AD redirects here after authentication with:
    - ?code=<auth_code>&state=<state>  on success
    - ?error=<err>&error_description=<desc>  on failure

    Pipeline:
    1. Check for Azure AD error response
    2. Validate required parameters (code, state)
    3. Look up PKCE data in Redis by state
    4. Load EnterpriseSsoConfig for organization from Redis PKCE data
    5. Exchange code + code_verifier for id_token
    6. Validate id_token JWT
    7. JIT provision user + create SsoSession
    8. Redirect to dashboard

    Args:
        code:              Authorization code from Azure AD.
        state:             CSRF state token (must match Redis stored state).
        error:             Azure AD error code (if auth failed on IdP side).
        error_description: Azure AD error description.
        db:                Async database session.

    Returns:
        RedirectResponse → dashboard or error page.
    """
    import json

    from app.models.enterprise_sso import EnterpriseSsoConfig
    from app.services.sso.azure_ad_service import AzureADConfigError, AzureADError, AzureADService
    from app.utils.redis import get_redis_client

    # Handle Azure AD error response (user denied consent, etc.)
    if error:
        logger.warning(
            "enterprise_sso: azure_ad_callback error=%s desc=%s",
            error,
            error_description,
        )
        return RedirectResponse(
            url=f"{_SSO_ERROR_REDIRECT}&reason={error}",
            status_code=status.HTTP_302_FOUND,
        )

    # Validate required parameters
    if not code or not state:
        logger.warning("enterprise_sso: azure_ad_callback missing code or state")
        return RedirectResponse(
            url=f"{_SSO_ERROR_REDIRECT}&reason=missing_params",
            status_code=status.HTTP_302_FOUND,
        )

    # Retrieve and validate PKCE data from Redis
    try:
        redis = await get_redis_client()
        redis_key = f"sso:pkce:{state}"
        pkce_raw = await redis.get(redis_key)
        if not pkce_raw:
            logger.warning(
                "enterprise_sso: azure_ad_callback state not found or expired state=%s",
                state,
            )
            return RedirectResponse(
                url=f"{_SSO_ERROR_REDIRECT}&reason=state_expired",
                status_code=status.HTTP_302_FOUND,
            )
        # Delete state immediately after retrieval (single-use)
        await redis.delete(redis_key)
        pkce_data = json.loads(pkce_raw)
    except Exception as exc:
        logger.error(
            "enterprise_sso: azure_ad_callback redis error state=%s error=%s",
            state,
            str(exc),
        )
        return RedirectResponse(
            url=f"{_SSO_ERROR_REDIRECT}&reason=state_error",
            status_code=status.HTTP_302_FOUND,
        )

    code_verifier = pkce_data.get("code_verifier", "")
    organization_id_str = pkce_data.get("organization_id", "")
    # redirect_uri stored at login time — must match authorization request exactly (RFC 6749 §4.1.3)
    stored_redirect_uri: str | None = pkce_data.get("redirect_uri")

    if not code_verifier or not organization_id_str:
        logger.warning(
            "enterprise_sso: azure_ad_callback corrupt pkce_data state=%s", state
        )
        return RedirectResponse(
            url=f"{_SSO_ERROR_REDIRECT}&reason=corrupt_state",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        organization_id = UUID(organization_id_str)
    except ValueError:
        return RedirectResponse(
            url=f"{_SSO_ERROR_REDIRECT}&reason=invalid_org",
            status_code=status.HTTP_302_FOUND,
        )

    # Load SSO config
    stmt = select(EnterpriseSsoConfig).where(
        EnterpriseSsoConfig.organization_id == organization_id,
        EnterpriseSsoConfig.provider == "azure_ad",
        EnterpriseSsoConfig.is_enabled.is_(True),
    )
    result = await db.execute(stmt)
    sso_config = result.scalar_one_or_none()

    if not sso_config:
        logger.warning(
            "enterprise_sso: azure_ad_callback no config org=%s", organization_id
        )
        return RedirectResponse(
            url=f"{_SSO_ERROR_REDIRECT}&reason=no_sso_config",
            status_code=status.HTTP_302_FOUND,
        )

    # Exchange code + PKCE verifier → id_token, validate, JIT provision
    # Pass stored_redirect_uri so token endpoint receives the identical absolute URI
    # used in the authorization request (Azure AD enforces exact match).
    try:
        svc = AzureADService(sso_config)
        user, session = await svc.process_callback(
            code=code,
            state=state,
            code_verifier=code_verifier,
            db=db,
            redirect_uri=stored_redirect_uri,
        )
    except AzureADError as exc:
        logger.warning(
            "enterprise_sso: azure_ad_callback token exchange failed org=%s error=%s",
            organization_id,
            str(exc),
        )
        return RedirectResponse(
            url=f"{_SSO_ERROR_REDIRECT}&reason=token_invalid",
            status_code=status.HTTP_302_FOUND,
        )
    except AzureADConfigError as exc:
        logger.error(
            "enterprise_sso: azure_ad_callback config error org=%s error=%s",
            organization_id,
            str(exc),
        )
        return RedirectResponse(
            url=f"{_SSO_ERROR_REDIRECT}&reason=config_error",
            status_code=status.HTTP_302_FOUND,
        )

    logger.info(
        "enterprise_sso: azure_ad_callback success user=%s org=%s session=%s",
        user.id,
        organization_id,
        session.id,
    )
    return RedirectResponse(
        url=f"{_SSO_SUCCESS_REDIRECT}&session_id={session.id}",
        status_code=status.HTTP_302_FOUND,
    )


# ──────────────────────────────────────────────────────────────────────────────
# POST /logout — Delete SSO session
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out of SSO session",
    description=(
        "Delete the active SsoSession for the given session_id. "
        "Only the session owner can delete their own session."
    ),
)
async def sso_logout(
    body: SsoLogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """
    Delete an SSO session (logout).

    Only the session owner can delete their own session.
    Returns HTTP 204 No Content on success.

    Args:
        body:         Contains session_id to invalidate.
        db:           Async database session.
        current_user: Authenticated user (must own the session).

    Returns:
        HTTP 204 No Content.

    Raises:
        HTTP 404: Session not found.
        HTTP 403: Session belongs to a different user.
    """
    from app.models.enterprise_sso import SsoSession

    stmt = select(SsoSession).where(SsoSession.id == body.session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SSO session {body.session_id} not found",
        )

    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete another user's SSO session",
        )

    await db.delete(session)
    await db.commit()

    logger.info(
        "enterprise_sso: logout session=%s user=%s",
        body.session_id,
        current_user.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────────────────────
# Private helpers
# ──────────────────────────────────────────────────────────────────────────────

def _build_saml_request_data(request: Request) -> dict[str, Any]:
    """
    Build python3-saml request_data dict from FastAPI Request.

    python3-saml expects a dict with keys:
        http_host, script_name, server_port, get_data, post_data, https

    Args:
        request: FastAPI Request object.

    Returns:
        dict compatible with OneLogin_Saml2_Auth constructor.
    """
    host = request.headers.get("host", "")
    # Detect HTTPS from X-Forwarded-Proto or scheme
    is_https = (
        request.headers.get("x-forwarded-proto", "").lower() == "https"
        or request.url.scheme == "https"
    )
    return {
        "http_host": host,
        "script_name": request.url.path,
        "server_port": request.url.port or (443 if is_https else 80),
        "get_data": dict(request.query_params),
        # post_data is populated asynchronously via saml_callback; synchronous here
        "post_data": {},
        "https": "on" if is_https else "off",
    }


def _extract_org_from_relay_state(relay_state: str) -> UUID | None:
    """
    Extract organization_id UUID from RelayState parameter.

    Convention: RelayState = "<organization_id>" (plain UUID string).
    Returns None if not a valid UUID.

    Args:
        relay_state: RelayState value from SAML POST.

    Returns:
        UUID if valid, None otherwise.
    """
    try:
        return UUID(relay_state.strip())
    except (ValueError, AttributeError):
        return None
