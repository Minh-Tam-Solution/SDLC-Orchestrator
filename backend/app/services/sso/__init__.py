"""
Enterprise SSO service package — Sprint 183.

Provides SAML 2.0 (python3-saml MIT) and Azure AD OIDC (msal MIT) SSO
implementations per ADR-061 locked decisions.

Modules:
    saml_service   — SAML 2.0 SP: login, ACS callback, SP metadata, logout
    azure_ad_service — Azure AD PKCE flow: login, callback, JWKS validation, logout
"""
