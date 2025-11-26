"""
=========================================================================
Security Headers Middleware - OWASP ASVS Level 2 Compliance
SDLC Orchestrator - Week 5 Day 1 (P1 Features)

Purpose:
- Add security headers to all HTTP responses
- HSTS (HTTP Strict Transport Security)
- CSP (Content Security Policy)
- X-Frame-Options, X-Content-Type-Options, etc.
- OWASP ASVS Level 2 compliance (V9: Communication Security)

Headers Added:
- Strict-Transport-Security (HSTS): max-age=31536000; includeSubDomains
- Content-Security-Policy (CSP): default-src 'self'
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
=========================================================================
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all HTTP responses.

    Usage:
        app.add_middleware(SecurityHeadersMiddleware)

    OWASP ASVS Mapping:
    - V9.1.1: TLS only (HSTS)
    - V9.1.2: HSTS header with max-age
    - V9.1.3: HSTS includeSubDomains
    - V9.1.4: Content Security Policy
    - V9.2.1: X-Frame-Options header
    - V9.2.2: X-Content-Type-Options header
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request, call_next):
        """Add security headers to response."""
        response = await call_next(request)

        # HSTS (HTTP Strict Transport Security)
        # max-age=31536000 = 1 year, includeSubDomains
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Content Security Policy (CSP)
        # Default: allow only same-origin, block inline scripts/styles
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Allow inline for now (FastAPI docs)
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        # X-Frame-Options: Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options: Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection: Enable XSS filter (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy (Feature Policy): Restrict browser features
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy

        return response

