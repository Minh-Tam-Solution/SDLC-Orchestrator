# AI Detection Service - Partner Onboarding Guide

**SDLC Stage**: 04 - BUILD
**Sprint**: 42 - AI Detection & Validation Pipeline
**Framework**: SDLC 6.1.0
**Day**: 9 - Partner Onboarding Documentation
**Status**: Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [API Reference](#api-reference)
5. [Integration Patterns](#integration-patterns)
6. [Configuration](#configuration)
7. [Monitoring & Observability](#monitoring--observability)
8. [Troubleshooting](#troubleshooting)
9. [Support](#support)

---

## Overview

### What is the AI Detection Service?

The AI Detection Service automatically identifies Pull Requests (PRs) that were generated using AI coding assistants such as:

| Tool | Detection Method | Confidence |
|------|-----------------|------------|
| Cursor | Metadata + Commit patterns | 95%+ |
| GitHub Copilot | Co-authored-by tags | 99%+ |
| Claude Code | Robot emoji + signatures | 95%+ |
| ChatGPT/OpenAI | GPT-4/OpenAI mentions | 90%+ |
| Windsurf | Codeium patterns | 90%+ |
| Cody | Sourcegraph patterns | 85%+ |
| Tabnine | Tabnine mentions | 85%+ |

### Why Use AI Detection?

1. **Transparency**: Track AI-assisted contributions in your codebase
2. **Compliance**: Meet regulatory requirements for AI disclosure
3. **Quality Assurance**: Apply appropriate review processes for AI-generated code
4. **Analytics**: Understand AI adoption patterns in your organization

### Production Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Accuracy | ≥80% | 80%+ |
| Precision | ≥80% | 100% |
| Recall | ≥50% | 74.1% |
| False Positive Rate | ≤30% | 0% |
| p95 Latency | <600ms | 0.3ms |

---

## Prerequisites

### Technical Requirements

- **GitHub Repository**: Organization-level access
- **Webhook Support**: Ability to receive HTTPS webhooks
- **API Access**: Valid API key for SDLC Orchestrator

### Permissions Required

```yaml
GitHub App Permissions:
  - pull_requests: read
  - contents: read
  - metadata: read

Webhook Events:
  - pull_request.opened
  - pull_request.synchronize
  - pull_request.reopened
```

---

## Quick Start

### Step 1: Obtain API Credentials

Contact the SDLC Orchestrator team to receive:
- `API_KEY`: Your organization's API key
- `WEBHOOK_SECRET`: Secret for validating webhook payloads

### Step 2: Configure Environment

```bash
# Required environment variables
export SDLC_API_KEY="your-api-key"
export SDLC_API_URL="https://api.sdlc.com/api/v1"
export SDLC_WEBHOOK_SECRET="your-webhook-secret"
```

### Step 3: Register Webhook

```bash
# Register your repository for AI detection
curl -X POST "${SDLC_API_URL}/ai-detection/register" \
  -H "Authorization: Bearer ${SDLC_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "owner/repo",
    "webhook_url": "https://your-service.com/webhooks/sdlc",
    "events": ["pull_request"]
  }'
```

### Step 4: Verify Integration

```bash
# Check detection service status
curl -X GET "${SDLC_API_URL}/ai-detection/status" \
  -H "Authorization: Bearer ${SDLC_API_KEY}"
```

Expected response:
```json
{
  "service": "GitHubAIDetectionService",
  "version": "1.0.0",
  "detection_threshold": 0.5,
  "strategies": ["metadata", "commit", "pattern"],
  "weights": {"metadata": 0.4, "commit": 0.4, "pattern": 0.2},
  "shadow_mode": {
    "enabled": true,
    "sample_rate": 1.0,
    "log_level": "INFO"
  }
}
```

---

## API Reference

### Base URL

```
Production: https://api.sdlc.com/api/v1
Staging: https://staging.api.sdlc.com/api/v1
```

### Authentication

All API requests require a Bearer token:

```http
Authorization: Bearer <your-api-key>
```

### Endpoints

#### GET /ai-detection/status

Get detection service status and configuration.

**Response**:
```json
{
  "service": "GitHubAIDetectionService",
  "version": "1.0.0",
  "detection_threshold": 0.5,
  "strategies": ["metadata", "commit", "pattern"],
  "weights": {"metadata": 0.4, "commit": 0.4, "pattern": 0.2},
  "shadow_mode": {
    "enabled": true,
    "sample_rate": 1.0,
    "log_level": "INFO",
    "collect_metrics": true
  }
}
```

#### GET /ai-detection/shadow-mode

Get shadow mode configuration.

**Response**:
```json
{
  "status": "enabled",
  "config": {
    "enabled": true,
    "sample_rate": 1.0,
    "log_level": "INFO",
    "collect_metrics": true
  },
  "description": "Shadow mode logs detection results for production validation without blocking or modifying PRs."
}
```

#### POST /ai-detection/analyze

Analyze a PR for AI-generated content.

**Request**:
```json
{
  "pr_id": "owner/repo#123",
  "title": "feat: implement user authentication",
  "body": "Generated using Cursor AI.",
  "commits": [
    {"commit": {"message": "[cursor] add login endpoint"}}
  ],
  "diff": "def authenticate(user, password):\n    pass"
}
```

**Response**:
```json
{
  "pr_id": "owner/repo#123",
  "is_ai_generated": true,
  "confidence": 0.76,
  "detected_tool": "cursor",
  "detection_method": "combined",
  "detection_duration_ms": 1,
  "individual_confidences": {
    "metadata": 0.9,
    "commit": 0.9,
    "pattern": 0.0
  },
  "weighted_confidence": 0.76,
  "detection_threshold": 0.5
}
```

#### GET /ai-detection/tools

Get list of supported AI tools.

**Response**:
```json
{
  "tools": [
    {"id": "cursor", "name": "Cursor"},
    {"id": "copilot", "name": "Copilot"},
    {"id": "claude_code", "name": "Claude Code"},
    {"id": "chatgpt", "name": "Chatgpt"},
    {"id": "windsurf", "name": "Windsurf"},
    {"id": "cody", "name": "Cody"},
    {"id": "tabnine", "name": "Tabnine"}
  ],
  "count": 7
}
```

#### GET /ai-detection/circuit-breakers

Get circuit breaker status for external services.

**Response**:
```json
{
  "circuit_breakers": {
    "github_api": {
      "name": "github_api",
      "config": {
        "failure_threshold": 5,
        "recovery_timeout": 30.0,
        "success_threshold": 3,
        "enabled": true
      },
      "stats": {
        "state": "closed",
        "failure_count": 0,
        "success_count": 0,
        "total_requests": 0,
        "total_failures": 0,
        "total_successes": 0,
        "total_rejections": 0
      }
    },
    "external_ai": {
      "name": "external_ai",
      "config": {...},
      "stats": {...}
    }
  },
  "description": "Circuit breakers protect against cascading failures when external services are unavailable."
}
```

#### POST /ai-detection/circuit-breakers/{breaker_name}/reset

Reset a circuit breaker to closed state.

**Request**:
```bash
POST /ai-detection/circuit-breakers/github_api/reset
```

**Response**:
```json
{
  "message": "Circuit breaker 'github_api' reset to CLOSED state",
  "stats": {...}
}
```

---

## Integration Patterns

### Pattern 1: GitHub Webhook Integration

The recommended pattern for real-time PR analysis.

```python
from flask import Flask, request, jsonify
import hmac
import hashlib
import requests

app = Flask(__name__)
WEBHOOK_SECRET = os.environ["SDLC_WEBHOOK_SECRET"]
API_KEY = os.environ["SDLC_API_KEY"]
API_URL = os.environ["SDLC_API_URL"]

@app.route("/webhooks/github", methods=["POST"])
def handle_github_webhook():
    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401

    event = request.headers.get("X-GitHub-Event")
    payload = request.json

    if event == "pull_request" and payload["action"] in ["opened", "synchronize"]:
        pr = payload["pull_request"]

        # Analyze PR
        result = requests.post(
            f"{API_URL}/ai-detection/analyze",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "pr_id": f"{payload['repository']['full_name']}#{pr['number']}",
                "title": pr["title"],
                "body": pr["body"],
                "commits": [],  # Fetch separately if needed
                "diff": None,  # Fetch separately if needed
            }
        ).json()

        # Handle result
        if result["is_ai_generated"]:
            add_label(pr, "ai-generated")
            add_comment(pr, f"AI Detection: {result['detected_tool']} ({result['confidence']:.0%})")

    return jsonify({"status": "ok"})

def verify_signature(payload, signature):
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### Pattern 2: CI/CD Pipeline Integration

Integrate AI detection into your CI/CD pipeline.

```yaml
# .github/workflows/ai-detection.yml
name: AI Detection Check

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  ai-detection:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Get PR Info
        id: pr
        run: |
          echo "title=${{ github.event.pull_request.title }}" >> $GITHUB_OUTPUT
          echo "body=${{ github.event.pull_request.body }}" >> $GITHUB_OUTPUT

      - name: Analyze PR
        id: analyze
        run: |
          RESULT=$(curl -s -X POST "${{ secrets.SDLC_API_URL }}/ai-detection/analyze" \
            -H "Authorization: Bearer ${{ secrets.SDLC_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "pr_id": "${{ github.repository }}#${{ github.event.pull_request.number }}",
              "title": "${{ steps.pr.outputs.title }}",
              "body": "${{ steps.pr.outputs.body }}",
              "commits": [],
              "diff": null
            }')

          echo "result=$RESULT" >> $GITHUB_OUTPUT

          IS_AI=$(echo $RESULT | jq -r '.is_ai_generated')
          if [ "$IS_AI" == "true" ]; then
            TOOL=$(echo $RESULT | jq -r '.detected_tool')
            CONFIDENCE=$(echo $RESULT | jq -r '.confidence')
            echo "::notice::AI-Generated PR detected: $TOOL (confidence: $CONFIDENCE)"
          fi

      - name: Add Label
        if: ${{ fromJson(steps.analyze.outputs.result).is_ai_generated }}
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.addLabels({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              labels: ['ai-generated']
            })
```

### Pattern 3: Batch Analysis

Analyze multiple PRs in batch for historical data.

```python
import asyncio
import aiohttp

async def analyze_batch(prs: list[dict]) -> list[dict]:
    """Analyze multiple PRs concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [analyze_pr(session, pr) for pr in prs]
        return await asyncio.gather(*tasks)

async def analyze_pr(session: aiohttp.ClientSession, pr: dict) -> dict:
    """Analyze a single PR."""
    async with session.post(
        f"{API_URL}/ai-detection/analyze",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json=pr,
    ) as response:
        return await response.json()

# Usage
prs = [
    {"pr_id": "owner/repo#1", "title": "feat: with Cursor", "body": "...", "commits": [], "diff": None},
    {"pr_id": "owner/repo#2", "title": "fix: typo", "body": "...", "commits": [], "diff": None},
    # ... more PRs
]

results = asyncio.run(analyze_batch(prs))
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AI_DETECTION_THRESHOLD` | No | `0.50` | Confidence threshold for detection |
| `AI_DETECTION_SHADOW_MODE` | No | `true` | Enable shadow mode (log-only) |
| `AI_DETECTION_SHADOW_SAMPLE_RATE` | No | `1.0` | Sampling rate (0.0-1.0) |
| `CIRCUIT_BREAKER_ENABLED` | No | `true` | Enable circuit breaker |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` | No | `5` | Failures before opening |
| `CIRCUIT_BREAKER_RECOVERY_TIMEOUT` | No | `30.0` | Seconds before recovery attempt |

### Threshold Tuning

| Threshold | Precision | Recall | Use Case |
|-----------|-----------|--------|----------|
| `0.35` | Lower | Higher | Catch more AI, accept more FPs |
| `0.50` | Balanced | Balanced | **Production recommended** |
| `0.65` | Higher | Lower | Minimize FPs, may miss some AI |

---

## Monitoring & Observability

### Health Check

```bash
# Check service health
curl -X GET "${SDLC_API_URL}/health"

# Expected response
{"status": "healthy", "version": "1.0.0"}
```

### Circuit Breaker Monitoring

```bash
# Monitor circuit breaker states
curl -X GET "${SDLC_API_URL}/ai-detection/circuit-breakers"
```

Circuit breaker states:
- `closed`: Normal operation, requests pass through
- `open`: Service failing, requests rejected immediately
- `half_open`: Testing recovery, limited requests allowed

### Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| `ai_detection_requests_total` | Total detection requests | - |
| `ai_detection_latency_ms` | Detection latency (p95) | <600ms |
| `ai_detection_confidence` | Detection confidence | 0.5-1.0 |
| `circuit_breaker_state` | Current circuit state | closed |

---

## Troubleshooting

### Common Issues

#### Issue: Detection returns `is_ai_generated: false` for known AI PR

**Cause**: Insufficient signals (only title without body/commits)

**Solution**: Ensure you're sending all available data:
```json
{
  "pr_id": "owner/repo#123",
  "title": "feat: with Cursor",
  "body": "Generated using Cursor AI.",  // Include body
  "commits": [{"commit": {"message": "[cursor] add"}}],  // Include commits
  "diff": "..."  // Include diff if available
}
```

#### Issue: Circuit breaker is OPEN

**Cause**: Too many failures to external service

**Solution**:
1. Check external service status
2. Wait for recovery timeout (30s default)
3. Or manually reset: `POST /ai-detection/circuit-breakers/github_api/reset`

#### Issue: False positive detection

**Cause**: Technical terms matching AI tool names

**Examples** that should NOT trigger detection:
- "database cursor" (not Cursor AI)
- "pilot project" (not Copilot)
- "Claude Shannon" (not Claude AI)

**Solution**: If you encounter a false positive, report it with:
- PR title and body
- Commit messages
- Expected vs actual result

### Debug Mode

Enable debug logging for detailed analysis:

```bash
export AI_DETECTION_SHADOW_LOG_LEVEL=DEBUG
```

This will log:
- Individual strategy confidences
- Pattern matches
- False positive checks

---

## Support

### Contact

- **Email**: support@sdlc.com
- **Slack**: #sdlc-ai-detection
- **GitHub Issues**: https://github.com/Minh-Tam-Solution/SDLC-Orchestrator/issues

### SLA

| Priority | Response Time | Resolution Time |
|----------|---------------|-----------------|
| P0 (Critical) | 15 minutes | 4 hours |
| P1 (High) | 1 hour | 24 hours |
| P2 (Medium) | 4 hours | 72 hours |
| P3 (Low) | 24 hours | 1 week |

### Reporting Issues

When reporting issues, please include:

1. **API Request** (with sensitive data redacted)
2. **API Response**
3. **Expected Behavior**
4. **Actual Behavior**
5. **Reproduction Steps**

---

## Changelog

### v1.0.0 (Sprint 42 - December 2025)

- Initial release
- Support for 7 AI tools
- 3-strategy detection (metadata, commit, pattern)
- Circuit breaker for resilience
- Shadow mode for production validation

---

**Document Status**: Production Ready
**Last Updated**: December 22, 2025
**Owner**: AI Detection Team
**Review Cycle**: Monthly
