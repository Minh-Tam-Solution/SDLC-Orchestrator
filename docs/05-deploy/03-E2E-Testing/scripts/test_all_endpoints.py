#!/usr/bin/env python3
"""
E2E API Test Script - SDLC 6.0.2

This script tests all API endpoints defined in Stage 03 OpenAPI specification.
Reference: RFC-SDLC-602-E2E-API-TESTING

Usage:
    python test_all_endpoints.py --base-url http://localhost:8000 --auth-token $TOKEN
"""

import argparse
import json
import requests
from datetime import datetime
from pathlib import Path


def load_openapi_spec(spec_path: str) -> dict:
    """Load OpenAPI specification from Stage 03."""
    with open(spec_path, "r") as f:
        return json.load(f)


def test_endpoint(base_url: str, method: str, path: str, auth_token: str | None) -> dict:
    """Test a single endpoint."""
    url = f"{base_url}{path}"
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    try:
        response = requests.request(method, url, headers=headers, timeout=30)
        return {
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "response_time_ms": response.elapsed.total_seconds() * 1000,
        }
    except Exception as e:
        return {
            "method": method,
            "path": path,
            "status_code": 0,
            "success": False,
            "error": str(e),
        }


def main():
    parser = argparse.ArgumentParser(description="E2E API Test Script")
    parser.add_argument("--base-url", required=True, help="API base URL")
    parser.add_argument("--auth-token", help="Bearer token for authentication")
    parser.add_argument("--openapi", default="../../03-integrate/01-api-contracts/openapi.json")
    parser.add_argument("--output", default="../reports/test_results.json")
    args = parser.parse_args()

    print(f"E2E API Testing - {datetime.now().isoformat()}")
    print(f"Base URL: {args.base_url}")

    # Load OpenAPI spec
    spec = load_openapi_spec(args.openapi)

    results = []
    passed = 0
    failed = 0

    # Test each endpoint
    for path, methods in spec.get("paths", {}).items():
        for method in ["get", "post", "put", "patch", "delete"]:
            if method in methods:
                result = test_endpoint(args.base_url, method.upper(), path, args.auth_token)
                results.append(result)
                if result["success"]:
                    passed += 1
                    print(f"  ✅ {method.upper()} {path}")
                else:
                    failed += 1
                    print(f"  ❌ {method.upper()} {path}")

    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "base_url": args.base_url,
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "pass_rate": (passed / len(results) * 100) if results else 0,
        "results": results,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults: {passed}/{len(results)} passed ({output['pass_rate']:.1f}%)")
    print(f"Report saved to: {args.output}")


if __name__ == "__main__":
    main()
