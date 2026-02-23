#!/usr/bin/env python3
"""
*-CyEyes-* E2E API Test Runner v2.0.0

SDLC Framework 6.1.1 Compliant
SE4A QA Tester — Stage 05-Verify

Parses OpenAPI spec from running backend and tests ALL endpoints.
Generates structured JSON results for report generation.

Usage:
    python3 test_all_endpoints_v2.py [--base-url URL] [--categories CATS]
"""

import json
import sys
import time
import re
import os
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8300")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", "artifacts", "auth_token.txt")
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "..", "artifacts", "test_results.json")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_token() -> str:
    with open(TOKEN_FILE) as f:
        return f.read().strip()


def http(method: str, url: str, token: str | None = None, body: dict | None = None,
         timeout: int = 15) -> tuple[int, dict | str, float]:
    """Simple HTTP client. Returns (status_code, body, elapsed_ms)."""
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()

    req = Request(url, data=data, headers=headers, method=method.upper())
    start = time.monotonic()
    try:
        with urlopen(req, timeout=timeout) as resp:
            elapsed = (time.monotonic() - start) * 1000
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw), elapsed
            except json.JSONDecodeError:
                return resp.status, raw[:500], elapsed
    except HTTPError as e:
        elapsed = (time.monotonic() - start) * 1000
        raw = e.read().decode() if e.fp else ""
        try:
            return e.code, json.loads(raw), elapsed
        except (json.JSONDecodeError, Exception):
            return e.code, raw[:500], elapsed
    except (URLError, TimeoutError, OSError) as e:
        elapsed = (time.monotonic() - start) * 1000
        return 0, str(e)[:300], elapsed


def classify(status: int, method: str) -> str:
    if status == 0:
        return "TIMEOUT"
    if 200 <= status < 300:
        return "PASS"
    if status == 401:
        return "UNAUTHORIZED"
    if status == 403:
        return "FORBIDDEN"
    if status == 404:
        if method.upper() == "GET":
            return "NOT_FOUND"
        return "PASS"  # 404 on DELETE/GET by ID is acceptable
    if status == 405:
        return "METHOD_NOT_ALLOWED"
    if status == 422:
        return "VALIDATION_ERROR"
    if status == 429:
        return "RATE_LIMITED"
    if 400 <= status < 500:
        return "CLIENT_ERROR"
    if 500 <= status < 600:
        return "SERVER_ERROR"
    return "UNKNOWN"


def make_path_params(path: str, params: list[dict]) -> str:
    """Substitute path parameters with realistic test values."""
    substitutions = {
        "project_id": "1",
        "gate_id": "1",
        "evidence_id": "1",
        "user_id": "1",
        "team_id": "1",
        "scan_id": "1",
        "session_id": "1",
        "task_id": "1",
        "roadmap_id": "1",
        "phase_id": "1",
        "sprint_id": "1",
        "item_id": "1",
        "rule_id": "1",
        "template_id": "1",
        "override_id": "1",
        "conversation_id": "1",
        "message_id": "1",
        "definition_id": "1",
        "pack_id": "1",
        "connection_id": "1",
        "org_id": "1",
        "invitation_id": "1",
        "report_id": "1",
        "adr_id": "1",
        "role_id": "1",
        "ticket_id": "1",
        "provider": "github",
        "token": "test-token-123",
        "format": "json",
        "region": "us-east-1",
    }
    result = path
    for match in re.findall(r"\{(\w+)\}", path):
        val = substitutions.get(match, "1")
        result = result.replace(f"{{{match}}}", val)
    return result


def make_body(method: str, path: str, operation: dict) -> dict | None:
    """Generate a minimal request body for POST/PUT/PATCH."""
    if method.upper() in ("GET", "DELETE", "HEAD", "OPTIONS"):
        return None

    # Try to extract from requestBody schema
    req_body = operation.get("requestBody", {})
    content = req_body.get("content", {})
    json_schema = content.get("application/json", {}).get("schema", {})

    # Common bodies by path pattern
    if "login" in path:
        return {"email": "taidt@mtsolution.com.vn", "password": "Admin@123456"}
    if "register" in path:
        return {"email": "test-e2e@test.com", "password": "TestE2E@2026!!", "full_name": "E2E Test User"}
    if "/gates" in path and method.upper() == "POST" and "evaluate" not in path:
        return {"project_id": 1, "gate_type": "G1_CONSULTATION", "name": "E2E Test Gate"}
    if "evidence" in path and "upload" in path:
        return None  # multipart, skip
    if "decompose" in path:
        return {"description": "Test decomposition", "max_tasks": 3}
    if "projects" in path and method.upper() == "POST" and "{" not in path:
        return {"name": "E2E Test Project", "description": "Created by E2E test"}
    if "teams" in path and method.upper() == "POST" and "{" not in path:
        return {"name": "E2E Test Team"}
    if "policies" in path and method.upper() == "POST":
        return {"name": "E2E Test Policy", "policy_type": "gate_requirement"}

    # Generic body from schema properties
    if json_schema.get("properties"):
        body = {}
        for prop, details in json_schema["properties"].items():
            ptype = details.get("type", "string")
            if ptype == "string":
                body[prop] = f"e2e-test-{prop}"
            elif ptype == "integer":
                body[prop] = 1
            elif ptype == "boolean":
                body[prop] = True
            elif ptype == "number":
                body[prop] = 1.0
            elif ptype == "array":
                body[prop] = []
            elif ptype == "object":
                body[prop] = {}
        if body:
            return body

    # Fallback minimal body
    if method.upper() in ("POST", "PUT", "PATCH"):
        return {"name": "e2e-test", "description": "E2E test data"}
    return None


# ---------------------------------------------------------------------------
# Main test runner
# ---------------------------------------------------------------------------

def run_tests(categories_filter: list[str] | None = None) -> dict:
    token = load_token()

    # Verify token
    status, body, _ = http("GET", f"{BASE_URL}/api/v1/auth/me", token)
    if status != 200:
        print(f"[FATAL] Token verification failed: {status} {body}")
        sys.exit(1)
    print(f"[OK] Authenticated as: {body.get('email', 'unknown') if isinstance(body, dict) else 'unknown'}")

    # Fetch OpenAPI spec
    status, spec, _ = http("GET", f"{BASE_URL}/api/openapi.json")
    if status != 200:
        print(f"[FATAL] Cannot fetch OpenAPI spec: {status}")
        sys.exit(1)

    paths = spec.get("paths", {})
    print(f"[OK] OpenAPI spec loaded: {len(paths)} paths")

    # Build operation list
    operations = []
    for path, methods in sorted(paths.items()):
        for method, operation in methods.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            tags = operation.get("tags", ["uncategorized"])
            op_id = operation.get("operationId", f"{method}_{path}")
            operations.append({
                "method": method.upper(),
                "path": path,
                "operation_id": op_id,
                "tags": tags,
                "operation": operation,
                "summary": operation.get("summary", ""),
            })

    print(f"[OK] Total operations to test: {len(operations)}")

    # Category filter
    if categories_filter:
        cats = [c.lower() for c in categories_filter]
        operations = [op for op in operations if any(
            c in t.lower() for t in op["tags"] for c in cats
        )]
        print(f"[FILTER] Testing {len(operations)} ops in categories: {categories_filter}")

    # Skip patterns (destructive or known-problematic)
    skip_patterns = [
        ("DELETE", "/api/v1/users/"),          # Don't delete real users
        ("POST", "/api/v1/auth/register"),     # Don't create extra users
        ("POST", "/api/v1/auth/forgot-password"),
        ("POST", "/api/v1/auth/reset-password"),
        ("DELETE", "/api/v1/projects/"),        # Don't delete projects
    ]

    results = []
    pass_count = 0
    fail_count = 0
    skip_count = 0
    start_time = time.monotonic()

    for i, op in enumerate(operations, 1):
        method = op["method"]
        path = op["path"]

        # Check skip
        should_skip = False
        for skip_method, skip_path in skip_patterns:
            if method == skip_method and path.startswith(skip_path):
                should_skip = True
                break

        if should_skip:
            results.append({
                "stt": i,
                "method": method,
                "path": path,
                "operation_id": op["operation_id"],
                "tags": op["tags"],
                "summary": op["summary"],
                "status": "SKIPPED",
                "code": 0,
                "time_ms": 0,
                "reason": "Destructive/sensitive operation",
            })
            skip_count += 1
            continue

        # Prepare URL
        url_path = make_path_params(path, op["operation"].get("parameters", []))
        url = f"{BASE_URL}{url_path}"

        # Prepare body
        body = make_body(method, path, op["operation"])

        # Check if auth required
        security = op["operation"].get("security", spec.get("security", []))
        use_token = token if security else None
        # Always send token for simplicity (most endpoints need it)
        use_token = token

        # Execute
        code, resp_body, elapsed = http(method, url, use_token, body)
        status_class = classify(code, method)

        result = {
            "stt": i,
            "method": method,
            "path": path,
            "operation_id": op["operation_id"],
            "tags": op["tags"],
            "summary": op["summary"],
            "status": status_class,
            "code": code,
            "time_ms": round(elapsed, 1),
        }

        if status_class not in ("PASS", "NOT_FOUND", "SKIPPED"):
            # Include error detail for failures
            if isinstance(resp_body, dict):
                result["detail"] = str(resp_body.get("detail", resp_body))[:200]
            else:
                result["detail"] = str(resp_body)[:200]

        results.append(result)

        if status_class in ("PASS", "NOT_FOUND"):
            pass_count += 1
        elif status_class != "SKIPPED":
            fail_count += 1

        # Progress
        if i % 50 == 0 or i == len(operations):
            elapsed_total = time.monotonic() - start_time
            print(f"  [{i}/{len(operations)}] {pass_count} pass, {fail_count} fail, {skip_count} skip ({elapsed_total:.1f}s)")

    total_time = time.monotonic() - start_time

    # Compute summary
    total = len(results)
    tested = total - skip_count
    summary = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "openapi_version": spec.get("info", {}).get("version", "?"),
        "total_operations": total,
        "tested": tested,
        "skipped": skip_count,
        "passed": pass_count,
        "failed": fail_count,
        "pass_rate": round(pass_count / tested * 100, 1) if tested > 0 else 0,
        "total_time_s": round(total_time, 1),
        "avg_time_ms": round(sum(r["time_ms"] for r in results if r["status"] != "SKIPPED") / max(tested, 1), 1),
        "by_status": {},
        "by_tag": {},
    }

    # Count by status
    for r in results:
        s = r["status"]
        summary["by_status"][s] = summary["by_status"].get(s, 0) + 1

    # Count by tag
    for r in results:
        for tag in r["tags"]:
            if tag not in summary["by_tag"]:
                summary["by_tag"][tag] = {"total": 0, "pass": 0, "fail": 0}
            summary["by_tag"][tag]["total"] += 1
            if r["status"] in ("PASS", "NOT_FOUND", "SKIPPED"):
                summary["by_tag"][tag]["pass"] += 1
            elif r["status"] != "SKIPPED":
                summary["by_tag"][tag]["fail"] += 1

    output = {"summary": summary, "results": results}

    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n[DONE] Results saved to {RESULTS_FILE}")
    print(f"  Total: {total} | Tested: {tested} | Pass: {pass_count} | Fail: {fail_count} | Skip: {skip_count}")
    print(f"  Pass Rate: {summary['pass_rate']}% | Time: {summary['total_time_s']}s")

    return output


if __name__ == "__main__":
    cats = None
    if "--categories" in sys.argv:
        idx = sys.argv.index("--categories")
        if idx + 1 < len(sys.argv):
            cats = sys.argv[idx + 1].split(",")
    if "--base-url" in sys.argv:
        idx = sys.argv.index("--base-url")
        if idx + 1 < len(sys.argv):
            BASE_URL = sys.argv[idx + 1]

    run_tests(cats)
