# AI Detection Service - Integration Guide

**SDLC Stage**: 04 - BUILD
**Sprint**: 42 - AI Detection & Validation Pipeline
**Framework**: SDLC 6.1.0
**Day**: 10 - Partner Integration Guide
**Status**: Production Ready

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Integration Scenarios](#integration-scenarios)
3. [GitHub App Setup](#github-app-setup)
4. [Webhook Configuration](#webhook-configuration)
5. [Sample Implementations](#sample-implementations)
6. [Testing Your Integration](#testing-your-integration)
7. [Production Checklist](#production-checklist)
8. [Performance Optimization](#performance-optimization)

---

## Architecture Overview

### System Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   GitHub PR     │────▶│   Your App      │────▶│  AI Detection   │
│   (Webhook)     │     │   (Middleware)  │     │    Service      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  PR Labels/     │     │  Shadow Mode    │
                        │  Comments       │     │  Logging        │
                        └─────────────────┘     └─────────────────┘
```

### Detection Pipeline

```
┌────────────┐    ┌────────────┐    ┌────────────┐
│  Metadata  │    │   Commit   │    │  Pattern   │
│  Detector  │    │  Detector  │    │  Detector  │
│   (40%)    │    │   (40%)    │    │   (20%)    │
└─────┬──────┘    └─────┬──────┘    └─────┬──────┘
      │                 │                 │
      └────────────────┬┘─────────────────┘
                       ▼
              ┌─────────────────┐
              │  Weighted Vote  │
              │   Algorithm     │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │  Detection      │
              │  Result         │
              └─────────────────┘
```

---

## Integration Scenarios

### Scenario 1: Label AI-Generated PRs

**Goal**: Automatically add `ai-generated` label to PRs

**Implementation**:
```python
async def handle_pr_opened(pr_data: dict) -> None:
    """Handle PR opened event."""
    result = await analyze_pr(pr_data)

    if result["is_ai_generated"]:
        await add_label(
            pr_data["repo"],
            pr_data["number"],
            "ai-generated"
        )
        await add_comment(
            pr_data["repo"],
            pr_data["number"],
            f"🤖 AI-generated PR detected: {result['detected_tool']} "
            f"(confidence: {result['confidence']:.0%})"
        )
```

### Scenario 2: Require Additional Review

**Goal**: Require extra reviewer for AI-generated PRs

**Implementation**:
```python
async def handle_pr_opened(pr_data: dict) -> None:
    """Handle PR opened event with review requirements."""
    result = await analyze_pr(pr_data)

    if result["is_ai_generated"] and result["confidence"] > 0.7:
        # Require senior reviewer for high-confidence AI PRs
        await request_review(
            pr_data["repo"],
            pr_data["number"],
            reviewers=["senior-dev-1", "senior-dev-2"]
        )
        await add_comment(
            pr_data["repo"],
            pr_data["number"],
            "⚠️ This PR was detected as AI-generated with high confidence. "
            "Additional review from a senior developer is required."
        )
```

### Scenario 3: Block Merge Until Acknowledged

**Goal**: Require explicit acknowledgment for AI PRs

**Implementation**:
```python
async def handle_pr_opened(pr_data: dict) -> None:
    """Block AI PRs until acknowledged."""
    result = await analyze_pr(pr_data)

    if result["is_ai_generated"]:
        # Create pending check
        await create_check_run(
            pr_data["repo"],
            pr_data["head_sha"],
            name="AI Disclosure",
            status="pending",
            output={
                "title": "AI-Generated PR - Acknowledgment Required",
                "summary": f"This PR was detected as AI-generated "
                           f"({result['detected_tool']}, {result['confidence']:.0%}).\n\n"
                           "Please acknowledge by commenting `/ai-acknowledged`."
            }
        )

async def handle_comment(comment_data: dict) -> None:
    """Handle acknowledgment comment."""
    if "/ai-acknowledged" in comment_data["body"]:
        await update_check_run(
            comment_data["repo"],
            check_run_id,
            status="completed",
            conclusion="success",
            output={
                "title": "AI Disclosure Acknowledged",
                "summary": f"Acknowledged by @{comment_data['user']}"
            }
        )
```

### Scenario 4: Analytics Dashboard

**Goal**: Track AI adoption metrics

**Implementation**:
```python
async def collect_metrics(pr_data: dict) -> None:
    """Collect AI detection metrics."""
    result = await analyze_pr(pr_data)

    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "repo": pr_data["repo"],
        "pr_number": pr_data["number"],
        "author": pr_data["author"],
        "is_ai_generated": result["is_ai_generated"],
        "detected_tool": result["detected_tool"],
        "confidence": result["confidence"],
        "detection_duration_ms": result["detection_duration_ms"],
    }

    # Store in your analytics database
    await analytics_db.insert("ai_detection_metrics", metrics)

    # Update aggregated stats
    await update_org_stats(
        pr_data["org"],
        ai_pr_count=1 if result["is_ai_generated"] else 0,
        total_pr_count=1
    )
```

---

## GitHub App Setup

### Step 1: Create GitHub App

1. Go to **Settings** → **Developer settings** → **GitHub Apps** → **New GitHub App**

2. Configure app settings:
```yaml
GitHub App name: AI Detection Bot
Homepage URL: https://your-company.com/ai-detection
Webhook URL: https://your-service.com/webhooks/github
Webhook secret: <generate-secure-secret>

Permissions:
  Repository permissions:
    - Contents: Read
    - Metadata: Read
    - Pull requests: Read & Write
    - Checks: Read & Write (optional)

  Subscribe to events:
    - Pull request
    - Pull request review comment (optional)
```

3. Generate and download private key

### Step 2: Install App

1. Go to app settings → **Install App**
2. Select organization/repositories
3. Authorize requested permissions

### Step 3: Configure Authentication

```python
import jwt
import time
import requests

class GitHubAppAuth:
    def __init__(self, app_id: str, private_key: str):
        self.app_id = app_id
        self.private_key = private_key

    def get_jwt(self) -> str:
        """Generate JWT for GitHub App authentication."""
        now = int(time.time())
        payload = {
            "iat": now - 60,  # Issued at time (60 seconds ago)
            "exp": now + 600,  # Expires in 10 minutes
            "iss": self.app_id,
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")

    def get_installation_token(self, installation_id: int) -> str:
        """Get installation access token."""
        jwt_token = self.get_jwt()
        response = requests.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        response.raise_for_status()
        return response.json()["token"]
```

---

## Webhook Configuration

### Webhook Handler

```python
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib

app = FastAPI()
WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"]
AI_DETECTION_API_KEY = os.environ["AI_DETECTION_API_KEY"]
AI_DETECTION_URL = os.environ["AI_DETECTION_URL"]

@app.post("/webhooks/github")
async def github_webhook(request: Request):
    """Handle GitHub webhook events."""
    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256")
    body = await request.body()

    if not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse event
    event = request.headers.get("X-GitHub-Event")
    payload = await request.json()

    # Route to handler
    if event == "pull_request":
        await handle_pull_request(payload)
    elif event == "pull_request_review_comment":
        await handle_pr_comment(payload)

    return {"status": "ok"}

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature:
        return False

    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)

async def handle_pull_request(payload: dict):
    """Handle pull_request events."""
    action = payload["action"]

    if action not in ["opened", "synchronize", "reopened"]:
        return

    pr = payload["pull_request"]
    repo = payload["repository"]["full_name"]

    # Fetch commits
    commits = await fetch_pr_commits(repo, pr["number"])

    # Fetch diff (optional, for pattern detection)
    diff = await fetch_pr_diff(repo, pr["number"])

    # Analyze PR
    result = await analyze_pr({
        "pr_id": f"{repo}#{pr['number']}",
        "title": pr["title"],
        "body": pr["body"],
        "commits": commits,
        "diff": diff,
    })

    # Handle result
    if result["is_ai_generated"]:
        await add_label(repo, pr["number"], "ai-generated")
        await post_detection_comment(repo, pr["number"], result)
```

### Webhook Event Payloads

**Pull Request Opened**:
```json
{
  "action": "opened",
  "number": 123,
  "pull_request": {
    "number": 123,
    "title": "feat: implement feature with Cursor",
    "body": "Generated using Cursor AI.",
    "head": {
      "sha": "abc123def456"
    },
    "user": {
      "login": "developer"
    }
  },
  "repository": {
    "full_name": "owner/repo"
  },
  "installation": {
    "id": 12345678
  }
}
```

---

## Sample Implementations

### Complete FastAPI Implementation

```python
# app.py
import os
import httpx
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
import hmac
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Detection Webhook Handler")

# Configuration
WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"]
AI_API_KEY = os.environ["AI_DETECTION_API_KEY"]
AI_API_URL = os.environ.get("AI_DETECTION_URL", "https://api.sdlc.com/api/v1")
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]


class AIDetectionResult(BaseModel):
    pr_id: str
    is_ai_generated: bool
    confidence: float
    detected_tool: str | None
    detection_method: str
    detection_duration_ms: int


async def analyze_pr(pr_data: dict) -> AIDetectionResult:
    """Call AI Detection API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AI_API_URL}/ai-detection/analyze",
            headers={"Authorization": f"Bearer {AI_API_KEY}"},
            json=pr_data,
            timeout=30.0,
        )
        response.raise_for_status()
        return AIDetectionResult(**response.json())


async def add_label(repo: str, pr_number: int, label: str) -> None:
    """Add label to PR."""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
            },
            json={"labels": [label]},
        )


async def add_comment(repo: str, pr_number: int, body: str) -> None:
    """Add comment to PR."""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
            },
            json={"body": body},
        )


async def fetch_pr_commits(repo: str, pr_number: int) -> list:
    """Fetch PR commits from GitHub."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{repo}/pulls/{pr_number}/commits",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
            },
        )
        response.raise_for_status()
        return response.json()


async def process_pr(payload: dict) -> None:
    """Process PR for AI detection."""
    pr = payload["pull_request"]
    repo = payload["repository"]["full_name"]
    pr_number = pr["number"]

    logger.info(f"Processing PR: {repo}#{pr_number}")

    try:
        # Fetch commits
        commits = await fetch_pr_commits(repo, pr_number)

        # Analyze PR
        result = await analyze_pr({
            "pr_id": f"{repo}#{pr_number}",
            "title": pr["title"],
            "body": pr.get("body") or "",
            "commits": commits,
            "diff": None,  # Optional
        })

        logger.info(
            f"Detection result: is_ai={result.is_ai_generated}, "
            f"tool={result.detected_tool}, confidence={result.confidence:.2%}"
        )

        # Handle AI-generated PRs
        if result.is_ai_generated:
            await add_label(repo, pr_number, "ai-generated")

            comment = (
                f"## 🤖 AI-Generated PR Detected\n\n"
                f"| Metric | Value |\n"
                f"|--------|-------|\n"
                f"| Tool | {result.detected_tool or 'Unknown'} |\n"
                f"| Confidence | {result.confidence:.0%} |\n"
                f"| Detection Method | {result.detection_method} |\n"
                f"| Analysis Time | {result.detection_duration_ms}ms |\n\n"
                f"*This is an automated message from the AI Detection Service.*"
            )
            await add_comment(repo, pr_number, comment)

    except Exception as e:
        logger.error(f"Error processing PR {repo}#{pr_number}: {e}")


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature:
        return False

    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@app.post("/webhooks/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle GitHub webhook events."""
    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256")
    body = await request.body()

    if not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse event
    event = request.headers.get("X-GitHub-Event")
    payload = await request.json()

    # Handle pull_request events
    if event == "pull_request":
        action = payload.get("action")
        if action in ["opened", "synchronize", "reopened"]:
            # Process in background to respond quickly
            background_tasks.add_task(process_pr, payload)

    return {"status": "ok", "event": event}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```txt
# requirements.txt
fastapi>=0.104.0
uvicorn>=0.24.0
httpx>=0.25.0
pydantic>=2.0.0
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  webhook-handler:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - AI_DETECTION_API_KEY=${AI_DETECTION_API_KEY}
      - AI_DETECTION_URL=https://api.sdlc.com/api/v1
    restart: unless-stopped
```

---

## Testing Your Integration

### Test Dataset

Use these sample PRs to test your integration:

**AI-Generated PRs** (should be detected):

```python
ai_test_cases = [
    {
        "pr_id": "test/repo#1",
        "title": "feat: implement with Cursor",
        "body": "Generated using Cursor AI.",
        "commits": [{"commit": {"message": "[cursor] add feature"}}],
        "expected": {"is_ai_generated": True, "tool": "cursor"}
    },
    {
        "pr_id": "test/repo#2",
        "title": "feat: add authentication",
        "body": "",
        "commits": [{"commit": {"message": "Co-authored-by: GitHub Copilot <noreply@github.com>"}}],
        "expected": {"is_ai_generated": True, "tool": "copilot"}
    },
    {
        "pr_id": "test/repo#3",
        "title": "feat: API implementation",
        "body": "🤖 Generated with Claude Code",
        "commits": [],
        "expected": {"is_ai_generated": True, "tool": "claude_code"}
    },
]
```

**Human PRs** (should NOT be detected):

```python
human_test_cases = [
    {
        "pr_id": "test/repo#10",
        "title": "fix: database cursor leak",
        "body": "Fixed cursor leak in connection pool.",
        "commits": [{"commit": {"message": "fix cursor leak"}}],
        "expected": {"is_ai_generated": False}
    },
    {
        "pr_id": "test/repo#11",
        "title": "feat: pilot project setup",
        "body": "Initial pilot project configuration.",
        "commits": [],
        "expected": {"is_ai_generated": False}
    },
    {
        "pr_id": "test/repo#12",
        "title": "docs: Claude Shannon theory",
        "body": "Documentation about information theory.",
        "commits": [],
        "expected": {"is_ai_generated": False}
    },
]
```

### Test Script

```python
# test_integration.py
import asyncio
import httpx

AI_API_URL = "https://api.sdlc.com/api/v1"
AI_API_KEY = "your-api-key"

async def test_detection(pr_data: dict, expected: dict) -> bool:
    """Test a single PR detection."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AI_API_URL}/ai-detection/analyze",
            headers={"Authorization": f"Bearer {AI_API_KEY}"},
            json=pr_data,
        )
        result = response.json()

    passed = result["is_ai_generated"] == expected["is_ai_generated"]

    if passed and expected.get("tool"):
        passed = result.get("detected_tool") == expected["tool"]

    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {pr_data['pr_id']} - "
          f"Expected: {expected}, Got: is_ai={result['is_ai_generated']}, "
          f"tool={result.get('detected_tool')}")

    return passed

async def main():
    """Run all tests."""
    all_tests = ai_test_cases + human_test_cases
    results = []

    for test in all_tests:
        pr_data = {k: v for k, v in test.items() if k != "expected"}
        passed = await test_detection(pr_data, test["expected"])
        results.append(passed)

    passed = sum(results)
    total = len(results)
    print(f"\nResults: {passed}/{total} tests passed ({passed/total:.0%})")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Production Checklist

### Pre-Production

- [ ] **API Key**: Obtained and stored securely
- [ ] **Webhook Secret**: Generated and configured
- [ ] **GitHub App**: Installed on target repositories
- [ ] **Webhook URL**: HTTPS endpoint accessible
- [ ] **Signature Verification**: Implemented and tested
- [ ] **Error Handling**: Graceful degradation implemented
- [ ] **Logging**: Structured logging configured
- [ ] **Monitoring**: Health checks and alerts set up

### Post-Production

- [ ] **Shadow Mode**: Verify logging without user impact
- [ ] **Metrics**: Track detection rate and accuracy
- [ ] **Alerts**: Set up for circuit breaker OPEN
- [ ] **Runbook**: Document incident response procedures
- [ ] **Rollback Plan**: Document how to disable integration

---

## Performance Optimization

### Async Processing

Process webhooks asynchronously to respond quickly:

```python
@app.post("/webhooks/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    # Verify and parse (fast)
    ...

    # Process in background (slow)
    background_tasks.add_task(process_pr, payload)

    # Respond immediately
    return {"status": "accepted"}
```

### Caching

Cache detection results for repeated webhooks:

```python
from cachetools import TTLCache

# Cache results for 5 minutes
detection_cache = TTLCache(maxsize=1000, ttl=300)

async def analyze_pr_cached(pr_data: dict) -> AIDetectionResult:
    cache_key = f"{pr_data['pr_id']}:{pr_data['title']}"

    if cache_key in detection_cache:
        return detection_cache[cache_key]

    result = await analyze_pr(pr_data)
    detection_cache[cache_key] = result
    return result
```

### Connection Pooling

Use connection pooling for HTTP clients:

```python
# Global client with connection pooling
http_client = httpx.AsyncClient(
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    timeout=30.0,
)

async def analyze_pr(pr_data: dict) -> AIDetectionResult:
    response = await http_client.post(
        f"{AI_API_URL}/ai-detection/analyze",
        headers={"Authorization": f"Bearer {AI_API_KEY}"},
        json=pr_data,
    )
    return AIDetectionResult(**response.json())
```

---

**Document Status**: Production Ready
**Last Updated**: December 22, 2025
**Owner**: AI Detection Team
**Next Review**: January 2026
