#!/usr/bin/env python3
"""
Test GitHub Device Flow endpoints.

This script tests the newly added GitHub Device Flow endpoints:
1. POST /auth/github/device - Initiate device flow
2. POST /auth/github/token - Poll for token

Usage:
    python test_device_flow.py
"""

import requests
import time

API_URL = "http://localhost:8000/api/v1"


def test_device_flow():
    """Test the complete GitHub Device Flow."""
    print("=" * 60)
    print("Testing GitHub Device Flow Endpoints")
    print("=" * 60)

    # Step 1: Initiate device flow
    print("\n1. Initiating device flow...")
    response = requests.post(f"{API_URL}/auth/github/device")

    if response.status_code != 200:
        print(f"❌ Device flow initiation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    device_data = response.json()
    print("✅ Device flow initiated successfully")
    print(f"   User code: {device_data['user_code']}")
    print(f"   Verification URI: {device_data['verification_uri']}")
    print(f"   Expires in: {device_data['expires_in']} seconds")
    print(f"   Polling interval: {device_data['interval']} seconds")

    # Step 2: Test polling (should get authorization_pending)
    print("\n2. Testing token polling (expect authorization_pending)...")
    response = requests.post(
        f"{API_URL}/auth/github/token",
        json={"device_code": device_data["device_code"]},
    )

    if response.status_code == 400:
        error_data = response.json()
        if error_data.get("error") == "authorization_pending":
            print("✅ Polling endpoint working correctly")
            print("   Status: authorization_pending (user hasn't authorized yet)")
            return True
        else:
            print(f"❌ Unexpected error: {error_data}")
            return False
    else:
        print(f"❌ Unexpected status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False


if __name__ == "__main__":
    try:
        # Test health endpoint first
        print("\n0. Checking backend health...")
        response = requests.get(f"{API_URL}/auth/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print("❌ Backend health check failed")
            print(f"Make sure the backend is running on {API_URL}")
            exit(1)

        # Run device flow test
        success = test_device_flow()

        print("\n" + "=" * 60)
        if success:
            print("✅ All tests passed!")
            print("=" * 60)
        else:
            print("❌ Some tests failed")
            print("=" * 60)
            exit(1)

    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to backend at {API_URL}")
        print("Make sure the backend is running:")
        print("  cd backend")
        print("  docker-compose up")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        exit(1)
