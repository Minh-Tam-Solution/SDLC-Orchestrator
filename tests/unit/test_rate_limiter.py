"""
Unit tests for Rate Limiter Middleware
SDLC Orchestrator - Week 5 Day 1 (P1 Features)
"""

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.middleware.rate_limiter import RateLimiterMiddleware


@pytest.mark.asyncio
async def test_get_ip_address():
    """Test IP address extraction from request."""
    middleware = RateLimiterMiddleware(app=None)
    
    # Mock request with X-Forwarded-For header
    class MockClient:
        host = "192.168.1.1"
    
    class MockRequest:
        def __init__(self):
            self.client = MockClient()
            self.headers = {"X-Forwarded-For": "203.0.113.42, 192.168.1.1"}
    
    request = MockRequest()
    ip = middleware._get_ip_address(request)
    assert ip == "203.0.113.42"
    
    # Test X-Real-IP header
    request.headers = {"X-Real-IP": "198.51.100.42"}
    ip = middleware._get_ip_address(request)
    assert ip == "198.51.100.42"
    
    # Test direct client IP (fallback)
    request.headers = {}
    ip = middleware._get_ip_address(request)
    assert ip == "192.168.1.1"


@pytest.mark.asyncio
async def test_get_user_id_no_token():
    """Test user ID extraction when no token provided."""
    middleware = RateLimiterMiddleware(app=None)
    
    class MockRequest:
        headers = {}
    
    request = MockRequest()
    user_id = middleware._get_user_id(request)
    assert user_id is None


# Integration tests will be added in test_api_endpoints_simple.py

