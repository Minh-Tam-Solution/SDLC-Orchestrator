"""
=========================================================================
Password Validation Utility - ADR-027 Phase 1
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: 2026-01-14
Status: ACTIVE - Sprint N+1 (ADR-027 Phase 1)
Authority: Backend Lead + CTO Approved
Foundation: Pydantic v2, SettingsService
Framework: SDLC 5.1.2 Universal Framework

Purpose:
Dynamic password validation based on password_min_length setting from database.

ADR-027 Phase 1: password_min_length implementation
Zero Mock Policy: Real validation using database setting (not hardcoded)

Usage:
    from app.utils.password_validator import validate_password_strength

    # In route handler:
    await validate_password_strength(password, settings_service)
    # Raises HTTPException if password too short
=========================================================================
"""

from fastapi import HTTPException, status


async def validate_password_strength(
    password: str,
    settings_service: "SettingsService",
) -> None:
    """
    Validate password meets minimum length requirement from database setting.

    ADR-027 Phase 1: Dynamic password validation

    Args:
        password: Plain text password to validate
        settings_service: SettingsService instance to read min_length setting

    Raises:
        HTTPException(400): If password is too short

    Example:
        >>> from app.services.settings_service import SettingsService
        >>> settings_svc = SettingsService(db)
        >>> await validate_password_strength("short", settings_svc)
        HTTPException: Password must be at least 8 characters long

        >>> await validate_password_strength("Admin@123", settings_svc)
        None  # Valid (9 chars >= 8 min)
    """
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required",
        )

    # Get minimum password length from database setting (default: 12)
    min_length = await settings_service.get_password_min_length()

    if len(password) < min_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {min_length} characters long",
        )

    # Password meets minimum length requirement
    return None


def get_password_requirements_message(min_length: int) -> str:
    """
    Get user-friendly message about password requirements.

    Args:
        min_length: Minimum password length from settings

    Returns:
        Human-readable requirements message

    Example:
        >>> get_password_requirements_message(12)
        "Password must be at least 12 characters long. Recommended: use mixed case, numbers, and symbols."
    """
    return (
        f"Password must be at least {min_length} characters long. "
        f"Recommended: use mixed case, numbers, and symbols."
    )
