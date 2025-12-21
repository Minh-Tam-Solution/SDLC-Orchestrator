# AI Detection Service - API Specification

**SDLC Stage**: 04 - BUILD
**Sprint**: 42 - AI Detection & Validation Pipeline
**Framework**: SDLC 5.1.1
**Version**: 1.0.0
**Status**: Production Ready

---

## OpenAPI Specification

```yaml
openapi: 3.0.3
info:
  title: AI Detection API
  description: API for detecting AI-generated Pull Requests
  version: 1.0.0
  contact:
    name: SDLC Orchestrator Team
    email: support@sdlc.com

servers:
  - url: https://api.sdlc.com/api/v1
    description: Production
  - url: https://staging.api.sdlc.com/api/v1
    description: Staging

security:
  - BearerAuth: []

paths:
  /ai-detection/status:
    get:
      summary: Get detection service status
      description: Returns current detection configuration and status
      operationId: getDetectionStatus
      tags:
        - AI Detection
      responses:
        '200':
          description: Service status
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DetectionStatusResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'

  /ai-detection/shadow-mode:
    get:
      summary: Get shadow mode configuration
      description: Returns shadow mode status and settings
      operationId: getShadowMode
      tags:
        - AI Detection
      responses:
        '200':
          description: Shadow mode configuration
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ShadowModeResponse'

  /ai-detection/analyze:
    post:
      summary: Analyze PR for AI content
      description: Analyzes a Pull Request for AI-generated content
      operationId: analyzePR
      tags:
        - AI Detection
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PRAnalysisRequest'
      responses:
        '200':
          description: Analysis result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PRAnalysisResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'

  /ai-detection/tools:
    get:
      summary: Get supported AI tools
      description: Returns list of AI tools that can be detected
      operationId: getSupportedTools
      tags:
        - AI Detection
      responses:
        '200':
          description: List of supported tools
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SupportedToolsResponse'

  /ai-detection/circuit-breakers:
    get:
      summary: Get circuit breaker status
      description: Returns status of all circuit breakers
      operationId: getCircuitBreakers
      tags:
        - Circuit Breaker
      responses:
        '200':
          description: Circuit breaker status
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CircuitBreakersResponse'

  /ai-detection/circuit-breakers/{breakerName}/reset:
    post:
      summary: Reset circuit breaker
      description: Resets a circuit breaker to closed state
      operationId: resetCircuitBreaker
      tags:
        - Circuit Breaker
      parameters:
        - name: breakerName
          in: path
          required: true
          schema:
            type: string
            enum: [github_api, external_ai]
      responses:
        '200':
          description: Reset successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CircuitBreakerResetResponse'
        '404':
          description: Circuit breaker not found

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    DetectionStatusResponse:
      type: object
      required:
        - service
        - version
        - detection_threshold
        - strategies
        - weights
        - shadow_mode
      properties:
        service:
          type: string
          example: "GitHubAIDetectionService"
        version:
          type: string
          example: "1.0.0"
        detection_threshold:
          type: number
          format: float
          minimum: 0.0
          maximum: 1.0
          example: 0.5
        strategies:
          type: array
          items:
            type: string
          example: ["metadata", "commit", "pattern"]
        weights:
          type: object
          additionalProperties:
            type: number
          example:
            metadata: 0.4
            commit: 0.4
            pattern: 0.2
        shadow_mode:
          $ref: '#/components/schemas/ShadowModeConfig'

    ShadowModeConfig:
      type: object
      properties:
        enabled:
          type: boolean
          example: true
        sample_rate:
          type: number
          format: float
          minimum: 0.0
          maximum: 1.0
          example: 1.0
        log_level:
          type: string
          enum: [DEBUG, INFO, WARNING]
          example: "INFO"
        collect_metrics:
          type: boolean
          example: true

    ShadowModeResponse:
      type: object
      properties:
        status:
          type: string
          enum: [enabled, disabled]
          example: "enabled"
        config:
          $ref: '#/components/schemas/ShadowModeConfig'
        description:
          type: string
          example: "Shadow mode logs detection results for production validation without blocking or modifying PRs."

    PRAnalysisRequest:
      type: object
      required:
        - pr_id
        - title
      properties:
        pr_id:
          type: string
          description: PR identifier (e.g., "owner/repo#123")
          example: "owner/repo#123"
        title:
          type: string
          description: PR title
          example: "feat: implement user authentication"
        body:
          type: string
          nullable: true
          description: PR body/description
          example: "Generated using Cursor AI."
        commits:
          type: array
          items:
            $ref: '#/components/schemas/CommitObject'
          description: List of commit objects
        diff:
          type: string
          nullable: true
          description: Unified diff content
          example: "def authenticate(user, password):\n    pass"

    CommitObject:
      type: object
      properties:
        commit:
          type: object
          properties:
            message:
              type: string
              example: "[cursor] add login endpoint"
            sha:
              type: string
              example: "abc123def456"

    PRAnalysisResponse:
      type: object
      required:
        - pr_id
        - is_ai_generated
        - confidence
        - detection_method
        - detection_duration_ms
      properties:
        pr_id:
          type: string
          example: "owner/repo#123"
        is_ai_generated:
          type: boolean
          description: Whether AI was detected
          example: true
        confidence:
          type: number
          format: float
          minimum: 0.0
          maximum: 1.0
          description: Detection confidence score
          example: 0.76
        detected_tool:
          type: string
          nullable: true
          enum: [cursor, copilot, claude_code, chatgpt, windsurf, cody, tabnine]
          description: Detected AI tool (null if not detected)
          example: "cursor"
        detection_method:
          type: string
          enum: [metadata, commit_message, pattern_analysis, combined]
          description: Method used for detection
          example: "combined"
        detection_duration_ms:
          type: integer
          description: Detection duration in milliseconds
          example: 1
        individual_confidences:
          type: object
          additionalProperties:
            type: number
          description: Confidence scores per strategy
          example:
            metadata: 0.9
            commit: 0.9
            pattern: 0.0
        weighted_confidence:
          type: number
          format: float
          description: Weighted confidence score
          example: 0.76
        detection_threshold:
          type: number
          format: float
          description: Threshold used for detection
          example: 0.5

    SupportedToolsResponse:
      type: object
      properties:
        tools:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
                example: "cursor"
              name:
                type: string
                example: "Cursor"
        count:
          type: integer
          example: 7

    CircuitBreakersResponse:
      type: object
      properties:
        circuit_breakers:
          type: object
          additionalProperties:
            $ref: '#/components/schemas/CircuitBreakerStats'
        description:
          type: string
          example: "Circuit breakers protect against cascading failures when external services are unavailable."

    CircuitBreakerStats:
      type: object
      properties:
        name:
          type: string
          example: "github_api"
        config:
          type: object
          properties:
            failure_threshold:
              type: integer
              example: 5
            recovery_timeout:
              type: number
              format: float
              example: 30.0
            success_threshold:
              type: integer
              example: 3
            enabled:
              type: boolean
              example: true
        stats:
          type: object
          properties:
            state:
              type: string
              enum: [closed, open, half_open]
              example: "closed"
            failure_count:
              type: integer
              example: 0
            success_count:
              type: integer
              example: 0
            total_requests:
              type: integer
              example: 0
            total_failures:
              type: integer
              example: 0
            total_successes:
              type: integer
              example: 0
            total_rejections:
              type: integer
              example: 0
            uptime_seconds:
              type: number
              format: float
              example: 3600.5

    CircuitBreakerResetResponse:
      type: object
      properties:
        message:
          type: string
          example: "Circuit breaker 'github_api' reset to CLOSED state"
        stats:
          $ref: '#/components/schemas/CircuitBreakerStats'

    Error:
      type: object
      properties:
        detail:
          type: string
          example: "Invalid request"

  responses:
    BadRequest:
      description: Bad request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

tags:
  - name: AI Detection
    description: AI detection endpoints
  - name: Circuit Breaker
    description: Circuit breaker management
```

---

## Request/Response Examples

### Analyze PR - Cursor Detection

**Request**:
```bash
curl -X POST "https://api.sdlc.com/api/v1/ai-detection/analyze" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "pr_id": "owner/repo#123",
    "title": "feat(auth): implement OAuth2 flow with Cursor",
    "body": "Generated using Cursor AI assistant.",
    "commits": [
      {"commit": {"message": "[cursor] add oauth endpoints"}},
      {"commit": {"message": "[cursor] implement token refresh"}}
    ],
    "diff": "def oauth_callback():\n    pass"
  }'
```

**Response** (200 OK):
```json
{
  "pr_id": "owner/repo#123",
  "is_ai_generated": true,
  "confidence": 0.76,
  "detected_tool": "cursor",
  "detection_method": "combined",
  "detection_duration_ms": 1,
  "individual_confidences": {
    "metadata": 1.0,
    "commit": 0.9,
    "pattern": 0.0
  },
  "weighted_confidence": 0.76,
  "detection_threshold": 0.5
}
```

### Analyze PR - Human Written

**Request**:
```bash
curl -X POST "https://api.sdlc.com/api/v1/ai-detection/analyze" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "pr_id": "owner/repo#456",
    "title": "fix: resolve race condition in cache",
    "body": "Added asyncio.Lock() for thread safety.",
    "commits": [
      {"commit": {"message": "fix: add lock to cache"}}
    ],
    "diff": "async with self._cache_lock:\n    pass"
  }'
```

**Response** (200 OK):
```json
{
  "pr_id": "owner/repo#456",
  "is_ai_generated": false,
  "confidence": 0.0,
  "detected_tool": null,
  "detection_method": "combined",
  "detection_duration_ms": 1,
  "individual_confidences": {
    "metadata": 0.0,
    "commit": 0.0,
    "pattern": 0.0
  },
  "weighted_confidence": 0.0,
  "detection_threshold": 0.5
}
```

### Analyze PR - Co-authored-by Detection

**Request**:
```bash
curl -X POST "https://api.sdlc.com/api/v1/ai-detection/analyze" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "pr_id": "owner/repo#789",
    "title": "feat: add user registration",
    "body": "Registration flow implementation.",
    "commits": [
      {"commit": {"message": "feat: add registration\n\nCo-authored-by: GitHub Copilot <noreply@github.com>"}}
    ],
    "diff": ""
  }'
```

**Response** (200 OK):
```json
{
  "pr_id": "owner/repo#789",
  "is_ai_generated": true,
  "confidence": 0.64,
  "detected_tool": "copilot",
  "detection_method": "combined",
  "detection_duration_ms": 1,
  "individual_confidences": {
    "metadata": 0.0,
    "commit": 1.0,
    "pattern": 0.0
  },
  "weighted_confidence": 0.64,
  "detection_threshold": 0.5
}
```

---

## Rate Limiting

| Tier | Requests/Minute | Requests/Hour |
|------|-----------------|---------------|
| Free | 60 | 1,000 |
| Pro | 300 | 10,000 |
| Enterprise | Unlimited | Unlimited |

Rate limit headers:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1703232000
```

---

## Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| 400 | Bad Request | Check request body format |
| 401 | Unauthorized | Check API key |
| 404 | Not Found | Check endpoint URL |
| 429 | Rate Limited | Wait and retry |
| 500 | Internal Error | Contact support |
| 503 | Service Unavailable | Circuit breaker open, retry later |

---

## SDK Support

### Python SDK (Coming Soon)

```python
from sdlc import AIDetectionClient

client = AIDetectionClient(api_key="your-api-key")

# Analyze PR
result = client.analyze_pr(
    pr_id="owner/repo#123",
    title="feat: with Cursor",
    body="Cursor AI.",
    commits=[{"commit": {"message": "[cursor] add"}}]
)

print(f"AI Generated: {result.is_ai_generated}")
print(f"Tool: {result.detected_tool}")
print(f"Confidence: {result.confidence:.0%}")
```

### JavaScript SDK (Coming Soon)

```javascript
import { AIDetectionClient } from '@sdlc/ai-detection';

const client = new AIDetectionClient({ apiKey: 'your-api-key' });

// Analyze PR
const result = await client.analyzePR({
  prId: 'owner/repo#123',
  title: 'feat: with Cursor',
  body: 'Cursor AI.',
  commits: [{ commit: { message: '[cursor] add' } }]
});

console.log(`AI Generated: ${result.isAiGenerated}`);
console.log(`Tool: ${result.detectedTool}`);
console.log(`Confidence: ${(result.confidence * 100).toFixed(0)}%`);
```

---

**Document Status**: Production Ready
**Last Updated**: December 22, 2025
**Owner**: AI Detection Team
