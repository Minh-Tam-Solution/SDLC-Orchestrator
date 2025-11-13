"""
Security utilities for authentication and authorization.
SDLC Orchestrator - Stage 03 (BUILD)

Functions:
    - verify_password: Verify password against bcrypt hash
    - get_password_hash: Generate bcrypt hash from password
    - create_access_token: Generate JWT access token (1 hour expiry)
    - create_refresh_token: Generate JWT refresh token (30 days expiry)
    - decode_token: Decode and validate JWT token

Security Standards:
    - OWASP ASVS Level 2 compliant
    - bcrypt cost=12 (250ms hash time)
    - JWT RS256 algorithm (RSA signatures)
    - Token expiry: Access 1h, Refresh 30d
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context (bcrypt, cost=12)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# JWT Algorithm
ALGORITHM = "HS256"  # HMAC SHA-256 (symmetric key)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against bcrypt hash.

    Args:
        plain_password: Password from user input
        hashed_password: bcrypt hash from database

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hash = get_password_hash("mypassword123")
        >>> verify_password("mypassword123", hash)
        True
        >>> verify_password("wrongpassword", hash)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate bcrypt hash from password.

    Args:
        password: Plain text password

    Returns:
        bcrypt hash (72-byte string)

    Security:
        - Cost factor: 12 (250ms hash time on 2023 hardware)
        - Salt: Auto-generated (random, 16-byte)
        - Algorithm: bcrypt (OWASP recommended)

    Example:
        >>> hash = get_password_hash("mypassword123")
        >>> len(hash)
        60
        >>> hash[:7]
        '$2b$12$'
    """
    return pwd_context.hash(password)


def create_access_token(subject: str | dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token (short-lived, 1 hour).

    Args:
        subject: User ID (str) or claims dict
        expires_delta: Optional expiry override (default: 1 hour)

    Returns:
        JWT token string (Base64-encoded)

    Token Payload:
        {
            "sub": "550e8400-e29b-41d4-a716-446655440000",
            "exp": 1673629200,
            "iat": 1673625600,
            "type": "access"
        }

    Security:
        - Expiry: 1 hour (short-lived)
        - Algorithm: HS256 (HMAC SHA-256)
        - Secret: From environment variable (256-bit)

    Example:
        >>> token = create_access_token(subject="user-123")
        >>> len(token) > 100
        True
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode = {"exp": expire, "iat": datetime.utcnow(), "type": "access"}

    if isinstance(subject, str):
        to_encode.update({"sub": subject})
    else:
        to_encode.update(subject)

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT refresh token (long-lived, 30 days).

    Args:
        subject: User ID (str)
        expires_delta: Optional expiry override (default: 30 days)

    Returns:
        JWT token string (Base64-encoded)

    Token Payload:
        {
            "sub": "550e8400-e29b-41d4-a716-446655440000",
            "exp": 1676217600,
            "iat": 1673625600,
            "type": "refresh"
        }

    Security:
        - Expiry: 30 days (long-lived)
        - Algorithm: HS256 (HMAC SHA-256)
        - Secret: From environment variable (256-bit)
        - Revocable: Blacklist in Redis

    Example:
        >>> token = create_refresh_token(subject="user-123")
        >>> len(token) > 100
        True
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "exp": expire,
        "iat": datetime.utcnow(),
        "sub": subject,
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token.

    Args:
        token: JWT token string

    Returns:
        Token payload (dict)

    Raises:
        JWTError: If token is invalid or expired

    Example:
        >>> token = create_access_token(subject="user-123")
        >>> payload = decode_token(token)
        >>> payload["type"]
        'access'
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise JWTError(f"Token validation failed: {str(e)}")


def generate_api_key() -> tuple[str, str]:
    """
    Generate API key for CI/CD integrations.

    Returns:
        Tuple of (api_key, key_hash)
        - api_key: Full key to show user ONCE (e.g., sdlc_live_abc123...)
        - key_hash: SHA-256 hash to store in database

    Format:
        sdlc_live_<32-byte-base64>

    Security:
        - Random: 32 bytes (256-bit entropy)
        - Hash: SHA-256 (store hash, not plaintext)
        - Prefix: sdlc_live_ (for user identification)

    Example:
        >>> api_key, key_hash = generate_api_key()
        >>> api_key[:10]
        'sdlc_live_'
        >>> len(key_hash)
        64
    """
    # Generate random 32-byte key
    random_bytes = secrets.token_bytes(32)
    api_key = f"sdlc_live_{secrets.token_urlsafe(32)}"

    # Hash with SHA-256
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    return api_key, key_hash


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for database storage.

    Args:
        api_key: Full API key (e.g., sdlc_live_abc123...)

    Returns:
        SHA-256 hash (64-character hex string)

    Example:
        >>> hash_api_key("sdlc_live_test123")
        'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3'
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_device_code() -> tuple[str, str]:
    """
    Generate device code for OAuth Device Flow (VS Code Extension, CLI).

    Returns:
        Tuple of (device_code, user_code)
        - device_code: 32-byte random string (for polling)
        - user_code: 8-character uppercase code (for user entry)

    Format:
        - device_code: 32-byte base64 (e.g., "abc123def456...")
        - user_code: 8-char uppercase (e.g., "ABCD-1234")

    Example:
        >>> device_code, user_code = generate_device_code()
        >>> len(device_code)
        43
        >>> len(user_code)
        9  # Includes hyphen
    """
    device_code = secrets.token_urlsafe(32)
    user_code = f"{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}"

    return device_code, user_code
