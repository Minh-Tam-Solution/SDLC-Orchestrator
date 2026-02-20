# API Developer Guide
## SDLC Orchestrator - Comprehensive API Documentation

**Version**: 1.0.0
**Date**: November 18, 2025
**Status**: ACTIVE - Week 4 Day 1 (Architecture Documentation)
**Authority**: Backend Lead + CTO Approved
**Foundation**: Week 3 Day 1-4 Implementation (23 Endpoints)
**Framework**: SDLC 6.1.0

---

## Document Purpose

This guide provides **practical API documentation for developers** building integrations with the SDLC Orchestrator platform.

**Key Sections**:
- **Quick Start** - Get your first API call working in 5 minutes
- **Authentication** - JWT token management, OAuth flows
- **API Reference** - Complete endpoint documentation with examples
- **Error Handling** - Error codes, retry strategies, debugging
- **Best Practices** - Rate limiting, pagination, performance optimization
- **SDKs & Tools** - Code examples in Python, JavaScript, cURL

**Audience**:
- Backend developers integrating SDLC Orchestrator
- Frontend developers building custom UIs
- DevOps engineers automating workflows
- QA engineers writing integration tests

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [API Reference](#api-reference)
   - [Authentication Endpoints](#authentication-endpoints)
   - [Gates Endpoints](#gates-endpoints)
   - [Evidence Endpoints](#evidence-endpoints)
   - [Policies Endpoints](#policies-endpoints)
4. [Error Handling](#error-handling)
5. [Rate Limiting & Pagination](#rate-limiting--pagination)
6. [SDKs & Code Examples](#sdks--code-examples)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Get Your API Credentials

**Development Environment**:
```bash
# Local development (Docker)
BASE_URL="http://localhost:8000"
EMAIL="test@example.com"
PASSWORD="password123"
```

**Production Environment**:
```bash
# Production (HTTPS required)
BASE_URL="https://api.sdlc-orchestrator.com"
EMAIL="your-email@company.com"
PASSWORD="your-secure-password"
```

### 2. Login & Get Access Token

```bash
# Login (POST /api/v1/auth/login)
curl -X POST "${BASE_URL}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "25e9ed25-c232-4ce3-a3ea-5458a85a915b",
    "email": "test@example.com",
    "full_name": "Test User",
    "is_active": true,
    "is_verified": true
  }
}
```

### 3. Make Your First Authenticated Request

```bash
# Get current user info (GET /api/v1/auth/me)
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET "${BASE_URL}/api/v1/auth/me" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Response** (200 OK):
```json
{
  "id": "25e9ed25-c232-4ce3-a3ea-5458a85a915b",
  "email": "test@example.com",
  "full_name": "Test User",
  "is_active": true,
  "is_verified": true,
  "created_at": "2025-11-18T10:00:00Z"
}
```

✅ **Success!** You've made your first API call to SDLC Orchestrator.

---

## Authentication

### JWT Token Authentication

**SDLC Orchestrator uses JWT Bearer tokens** for authentication.

**Token Lifecycle**:
- **Access Token**: 60 minutes TTL (short-lived, for API requests)
- **Refresh Token**: 30 days TTL (long-lived, for renewing access tokens)

### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Database

    Client->>API: POST /auth/login (email, password)
    API->>Database: Validate credentials (bcrypt)
    Database-->>API: User found, password valid
    API->>API: Generate JWT tokens (access + refresh)
    API-->>Client: 200 OK (access_token, refresh_token)

    Note over Client: Store tokens securely

    Client->>API: GET /auth/me (Authorization: Bearer <token>)
    API->>API: Verify JWT signature (HS256)
    API->>Database: Get user by ID from JWT payload
    Database-->>API: User data
    API-->>Client: 200 OK (user object)

    Note over Client: Access token expires after 60 min

    Client->>API: POST /auth/refresh (refresh_token)
    API->>Database: Validate refresh token
    Database-->>API: Refresh token valid
    API->>API: Generate new access token
    API-->>Client: 200 OK (new access_token)
```

### Token Storage Best Practices

**Frontend (Web)**:
```javascript
// ✅ GOOD: Use secure httpOnly cookies
// Server sets: Set-Cookie: access_token=...; HttpOnly; Secure; SameSite=Strict

// ⚠️ ACCEPTABLE: Use memory storage (lost on page refresh)
let accessToken = null;

// ❌ BAD: localStorage (vulnerable to XSS)
// localStorage.setItem('access_token', token); // DON'T DO THIS
```

**Backend/CLI**:
```python
# ✅ GOOD: Use environment variables or secure config files
import os

ACCESS_TOKEN = os.getenv("SDLC_ACCESS_TOKEN")

# ✅ GOOD: Use system keyring (macOS Keychain, Windows Credential Manager)
import keyring

keyring.set_password("sdlc-orchestrator", "access_token", token)
token = keyring.get_password("sdlc-orchestrator", "access_token")
```

### Token Refresh Strategy

**Automatic Refresh** (Recommended):
```python
import requests
import time

class SDLCClient:
    def __init__(self, base_url, email, password):
        self.base_url = base_url
        self.email = email
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0

    def login(self):
        """Login and get tokens."""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": self.email, "password": self.password}
        )
        response.raise_for_status()
        data = response.json()

        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.token_expires_at = time.time() + data["expires_in"]

    def refresh_access_token(self):
        """Refresh access token using refresh token."""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )
        response.raise_for_status()
        data = response.json()

        self.access_token = data["access_token"]
        self.token_expires_at = time.time() + data["expires_in"]

    def get_headers(self):
        """Get authorization headers, refreshing token if needed."""
        # Refresh token if it expires in < 5 minutes
        if time.time() >= self.token_expires_at - 300:
            self.refresh_access_token()

        return {"Authorization": f"Bearer {self.access_token}"}

    def get(self, path):
        """Make authenticated GET request."""
        response = requests.get(
            f"{self.base_url}{path}",
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()

# Usage
client = SDLCClient("http://localhost:8000", "test@example.com", "password123")
client.login()

# Automatically refreshes token if needed
user = client.get("/api/v1/auth/me")
print(user)
```

---

## API Reference

### Base URL

| Environment | Base URL |
|-------------|----------|
| **Local Development** | `http://localhost:8000` |
| **Staging** | `https://api-staging.sdlc-orchestrator.com` |
| **Production** | `https://api.sdlc-orchestrator.com` |

### API Versioning

All endpoints are prefixed with `/api/v1/`.

**Example**: `GET /api/v1/auth/me`

**Future Versions**:
- Breaking changes will introduce new versions (`/api/v2/`)
- Old versions will be supported for 12 months after deprecation notice

---

## Authentication Endpoints

### POST /api/v1/auth/login

**Description**: Authenticate user and receive JWT tokens.

**Request**:
```http
POST /api/v1/auth/login HTTP/1.1
Content-Type: application/json

{
  "email": "nguyen.van.anh@mtc.com.vn",
  "password": "password123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjMzNjE1ODksImlhdCI6MTc2MzM1Nzk4OSwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjI1ZTllZDI1LWMyMzItNGNlMy1hM2VhLTU0NThhODVhOTE1YiJ9.iSvPYlbrbXRouf3SCLqimqtvZlU8CivJh3A7yLTvgQ4",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjU5NDk5ODksImlhdCI6MTc2MzM1Nzk4OSwic3ViIjoiMjVlOWVkMjUtYzIzMi00Y2UzLWEzZWEtNTQ1OGE4NWE5MTViIiwidHlwZSI6InJlZnJlc2gifQ.yV2WMgOmMIrlGnQD7UzsOIiBz7-zsOMp1mfX4k0q_S0",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "25e9ed25-c232-4ce3-a3ea-5458a85a915b",
    "email": "nguyen.van.anh@mtc.com.vn",
    "full_name": "Nguyen Van Anh",
    "is_active": true,
    "is_verified": true,
    "created_at": "2025-11-18T10:00:00Z"
  }
}
```

**Error Responses**:

| Status | Error Code | Description |
|--------|------------|-------------|
| 400 | `VALIDATION_ERROR` | Missing email or password |
| 401 | `INVALID_CREDENTIALS` | Wrong email or password |
| 403 | `ACCOUNT_DISABLED` | User account is inactive |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many login attempts |

**Example Error** (401 Unauthorized):
```json
{
  "detail": "Invalid credentials"
}
```

**Code Examples**:

<details>
<summary>cURL</summary>

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nguyen.van.anh@mtc.com.vn",
    "password": "password123"
  }'
```
</details>

<details>
<summary>Python (requests)</summary>

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={
        "email": "nguyen.van.anh@mtc.com.vn",
        "password": "password123"
    }
)

if response.status_code == 200:
    data = response.json()
    access_token = data["access_token"]
    print(f"Login successful! Token: {access_token[:20]}...")
else:
    print(f"Login failed: {response.json()}")
```
</details>

<details>
<summary>JavaScript (fetch)</summary>

```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'nguyen.van.anh@mtc.com.vn',
    password: 'password123'
  })
});

if (response.ok) {
  const data = await response.json();
  const accessToken = data.access_token;
  console.log('Login successful!', accessToken.substring(0, 20) + '...');
} else {
  const error = await response.json();
  console.error('Login failed:', error);
}
```
</details>

---

### GET /api/v1/auth/me

**Description**: Get current authenticated user information.

**Authentication**: Required (Bearer token)

**Request**:
```http
GET /api/v1/auth/me HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "id": "25e9ed25-c232-4ce3-a3ea-5458a85a915b",
  "email": "nguyen.van.anh@mtc.com.vn",
  "full_name": "Nguyen Van Anh",
  "is_active": true,
  "is_verified": true,
  "created_at": "2025-11-18T10:00:00Z"
}
```

**Error Responses**:

| Status | Error Code | Description |
|--------|------------|-------------|
| 401 | `MISSING_TOKEN` | Authorization header missing |
| 401 | `INVALID_TOKEN` | Token is invalid or expired |
| 404 | `USER_NOT_FOUND` | User no longer exists |

**Code Examples**:

<details>
<summary>cURL</summary>

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer ${TOKEN}"
```
</details>

<details>
<summary>Python (requests)</summary>

```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(
    "http://localhost:8000/api/v1/auth/me",
    headers=headers
)

if response.status_code == 200:
    user = response.json()
    print(f"Logged in as: {user['full_name']} ({user['email']})")
else:
    print(f"Error: {response.json()}")
```
</details>

---

### POST /api/v1/auth/refresh

**Description**: Refresh access token using refresh token.

**Request**:
```http
POST /api/v1/auth/refresh HTTP/1.1
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Error Responses**:

| Status | Error Code | Description |
|--------|------------|-------------|
| 401 | `INVALID_REFRESH_TOKEN` | Refresh token is invalid or expired |
| 404 | `TOKEN_NOT_FOUND` | Refresh token not found in database |

---

### POST /api/v1/auth/logout

**Description**: Logout user and invalidate refresh token.

**Authentication**: Required (Bearer token)

**Request**:
```http
POST /api/v1/auth/logout HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "message": "Successfully logged out"
}
```

---

### GET /api/v1/auth/health

**Description**: Health check for authentication service.

**Authentication**: Not required

**Request**:
```http
GET /api/v1/auth/health HTTP/1.1
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "authentication",
  "timestamp": "2025-11-18T10:00:00Z"
}
```

---

## Gates Endpoints

### GET /api/v1/gates

**Description**: List all quality gates (with optional filtering).

**Authentication**: Required (Bearer token)

**Query Parameters**:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `stage` | string | No | Filter by SDLC stage | `WHAT`, `BUILD`, `SHIP` |
| `status` | string | No | Filter by gate status | `PENDING`, `PASSED`, `BLOCKED` |
| `limit` | integer | No | Max results (default: 20, max: 100) | `50` |
| `offset` | integer | No | Pagination offset | `0` |

**Request**:
```http
GET /api/v1/gates?stage=WHAT&status=PENDING HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "gates": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "gate_number": "G1",
      "gate_name": "Requirements Approved",
      "stage": "WHAT",
      "description": "Functional requirements reviewed and approved by stakeholders",
      "status": "PENDING",
      "created_by": "25e9ed25-c232-4ce3-a3ea-5458a85a915b",
      "created_at": "2025-11-18T10:00:00Z",
      "updated_at": "2025-11-18T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

**Code Examples**:

<details>
<summary>cURL</summary>

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET "http://localhost:8000/api/v1/gates?stage=WHAT&status=PENDING" \
  -H "Authorization: Bearer ${TOKEN}"
```
</details>

<details>
<summary>Python (requests)</summary>

```python
import requests

headers = {"Authorization": f"Bearer {access_token}"}

response = requests.get(
    "http://localhost:8000/api/v1/gates",
    headers=headers,
    params={
        "stage": "WHAT",
        "status": "PENDING",
        "limit": 50
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"Found {data['total']} gates")
    for gate in data['gates']:
        print(f"  - {gate['gate_number']}: {gate['gate_name']} ({gate['status']})")
```
</details>

---

### GET /api/v1/gates/{gate_id}

**Description**: Get gate by ID.

**Authentication**: Required (Bearer token)

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `gate_id` | UUID | Yes | Gate UUID |

**Request**:
```http
GET /api/v1/gates/a1b2c3d4-e5f6-7890-abcd-ef1234567890 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "gate_number": "G1",
  "gate_name": "Requirements Approved",
  "stage": "WHAT",
  "description": "Functional requirements reviewed and approved by stakeholders",
  "status": "PENDING",
  "created_by": "25e9ed25-c232-4ce3-a3ea-5458a85a915b",
  "created_at": "2025-11-18T10:00:00Z",
  "updated_at": "2025-11-18T10:00:00Z"
}
```

**Error Responses**:

| Status | Error Code | Description |
|--------|------------|-------------|
| 404 | `GATE_NOT_FOUND` | Gate with given ID not found |

---

### POST /api/v1/gates

**Description**: Create a new quality gate.

**Authentication**: Required (Bearer token)

**Request Body**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `gate_number` | string | Yes | Gate identifier (G0.1-G9) | `"G1"` |
| `gate_name` | string | Yes | Human-readable gate name | `"Requirements Approved"` |
| `stage` | string | Yes | SDLC stage | `"WHAT"` |
| `description` | string | No | Gate description | `"FRD approved by stakeholders"` |

**Request**:
```http
POST /api/v1/gates HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "gate_number": "G1",
  "gate_name": "Requirements Approved",
  "stage": "WHAT",
  "description": "Functional requirements reviewed and approved by stakeholders"
}
```

**Response** (201 Created):
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "gate_number": "G1",
  "gate_name": "Requirements Approved",
  "stage": "WHAT",
  "description": "Functional requirements reviewed and approved by stakeholders",
  "status": "PENDING",
  "created_by": "25e9ed25-c232-4ce3-a3ea-5458a85a915b",
  "created_at": "2025-11-18T10:00:00Z",
  "updated_at": "2025-11-18T10:00:00Z"
}
```

**Error Responses**:

| Status | Error Code | Description |
|--------|------------|-------------|
| 400 | `VALIDATION_ERROR` | Missing required fields |
| 409 | `GATE_ALREADY_EXISTS` | Gate with same gate_number already exists |

---

### PUT /api/v1/gates/{gate_id}

**Description**: Update gate (status, description).

**Authentication**: Required (Bearer token)

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `gate_id` | UUID | Yes | Gate UUID |

**Request Body** (all fields optional):

| Field | Type | Description |
|-------|------|-------------|
| `gate_name` | string | Updated gate name |
| `description` | string | Updated description |
| `status` | string | Updated status (`PENDING`, `PASSED`, `BLOCKED`) |

**Request**:
```http
PUT /api/v1/gates/a1b2c3d4-e5f6-7890-abcd-ef1234567890 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "status": "PASSED"
}
```

**Response** (200 OK):
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "gate_number": "G1",
  "gate_name": "Requirements Approved",
  "stage": "WHAT",
  "description": "Functional requirements reviewed and approved by stakeholders",
  "status": "PASSED",
  "created_by": "25e9ed25-c232-4ce3-a3ea-5458a85a915b",
  "created_at": "2025-11-18T10:00:00Z",
  "updated_at": "2025-11-18T11:00:00Z"
}
```

---

### DELETE /api/v1/gates/{gate_id}

**Description**: Delete gate (soft delete).

**Authentication**: Required (Bearer token)

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `gate_id` | UUID | Yes | Gate UUID |

**Request**:
```http
DELETE /api/v1/gates/a1b2c3d4-e5f6-7890-abcd-ef1234567890 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "message": "Gate deleted successfully",
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### GET /api/v1/gates/health

**Description**: Health check for gates service.

**Authentication**: Not required

**Request**:
```http
GET /api/v1/gates/health HTTP/1.1
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "gates",
  "timestamp": "2025-11-18T10:00:00Z"
}
```

---

## Evidence Endpoints

### GET /api/v1/evidence

**Description**: List evidence files (with filtering).

**Authentication**: Required (Bearer token)

**Query Parameters**:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `gate_id` | UUID | No | Filter by gate | `a1b2c3d4-...` |
| `limit` | integer | No | Max results (default: 20) | `50` |
| `offset` | integer | No | Pagination offset | `0` |

**Request**:
```http
GET /api/v1/evidence?gate_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "evidence": [
    {
      "id": "e1f2g3h4-i5j6-7890-klmn-op1234567890",
      "gate_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "file_name": "functional-requirements-v1.0.pdf",
      "file_path": "s3://evidence-vault/2025/11/18/e1f2g3h4.pdf",
      "file_size_bytes": 2048576,
      "file_hash": "a3c7f1e9d2b4...",
      "uploaded_by": "25e9ed25-c232-4ce3-a3ea-5458a85a915b",
      "created_at": "2025-11-18T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

### POST /api/v1/evidence

**Description**: Upload evidence file to S3 (MinIO).

**Authentication**: Required (Bearer token)

**Request** (multipart/form-data):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | File to upload (max 10MB) |
| `gate_id` | UUID | No | Associated gate |

**Request**:
```http
POST /api/v1/evidence HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="requirements.pdf"
Content-Type: application/pdf

[Binary file data]
------WebKitFormBoundary
Content-Disposition: form-data; name="gate_id"

a1b2c3d4-e5f6-7890-abcd-ef1234567890
------WebKitFormBoundary--
```

**Response** (201 Created):
```json
{
  "id": "e1f2g3h4-i5j6-7890-klmn-op1234567890",
  "gate_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "file_name": "requirements.pdf",
  "file_path": "s3://evidence-vault/2025/11/18/e1f2g3h4.pdf",
  "file_size_bytes": 2048576,
  "file_hash": "a3c7f1e9d2b4...",
  "uploaded_by": "25e9ed25-c232-4ce3-a3ea-5458a85a915b",
  "created_at": "2025-11-18T10:00:00Z"
}
```

**Code Examples**:

<details>
<summary>cURL</summary>

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
GATE_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"

curl -X POST http://localhost:8000/api/v1/evidence \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@/path/to/requirements.pdf" \
  -F "gate_id=${GATE_ID}"
```
</details>

<details>
<summary>Python (requests)</summary>

```python
import requests

headers = {"Authorization": f"Bearer {access_token}"}

files = {
    "file": ("requirements.pdf", open("requirements.pdf", "rb"), "application/pdf")
}

data = {
    "gate_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}

response = requests.post(
    "http://localhost:8000/api/v1/evidence",
    headers=headers,
    files=files,
    data=data
)

if response.status_code == 201:
    evidence = response.json()
    print(f"File uploaded: {evidence['file_name']} ({evidence['file_size_bytes']} bytes)")
```
</details>

---

### DELETE /api/v1/evidence/{evidence_id}

**Description**: Delete evidence file.

**Authentication**: Required (Bearer token)

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | UUID | Yes | Evidence UUID |

**Request**:
```http
DELETE /api/v1/evidence/e1f2g3h4-i5j6-7890-klmn-op1234567890 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "message": "Evidence deleted successfully",
  "id": "e1f2g3h4-i5j6-7890-klmn-op1234567890"
}
```

---

### GET /api/v1/evidence/health

**Description**: Health check for evidence service.

**Request**:
```http
GET /api/v1/evidence/health HTTP/1.1
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "evidence",
  "timestamp": "2025-11-18T10:00:00Z"
}
```

---

## Policies Endpoints

### GET /api/v1/policies

**Description**: List OPA policies.

**Authentication**: Required (Bearer token)

**Query Parameters**:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `stage` | string | No | Filter by SDLC stage | `WHAT`, `BUILD` |
| `is_active` | boolean | No | Filter by active status | `true` |
| `limit` | integer | No | Max results (default: 20) | `50` |

**Request**:
```http
GET /api/v1/policies?stage=WHAT&is_active=true HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "policies": [
    {
      "id": "p1q2r3s4-t5u6-7890-vwxy-z1234567890",
      "policy_name": "FRD Completeness Check",
      "policy_code": "FRD_COMPLETENESS",
      "stage": "WHAT",
      "description": "Validates that FRD has all required sections",
      "rego_code": "package sdlc.what.frd_completeness\ndefault allow = false\nallow { input.complete == true }",
      "severity": "ERROR",
      "is_active": true,
      "version": "1.0.0",
      "created_at": "2025-11-18T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

### GET /api/v1/policies/health

**Description**: Health check for policies service.

**Request**:
```http
GET /api/v1/policies/health HTTP/1.1
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "policies",
  "timestamp": "2025-11-18T10:00:00Z"
}
```

---

## Error Handling

### Standard Error Response Format

All API errors follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

**Example** (404 Not Found):
```json
{
  "detail": "Gate not found"
}
```

### HTTP Status Codes

| Status Code | Meaning | When to Use |
|-------------|---------|-------------|
| **200** | OK | Successful GET/PUT/PATCH request |
| **201** | Created | Successful POST request (resource created) |
| **204** | No Content | Successful DELETE request |
| **400** | Bad Request | Invalid request body, missing required fields |
| **401** | Unauthorized | Missing or invalid authentication token |
| **403** | Forbidden | Valid token but insufficient permissions |
| **404** | Not Found | Resource doesn't exist |
| **409** | Conflict | Resource already exists (duplicate key) |
| **413** | Payload Too Large | File upload exceeds 10MB limit |
| **429** | Too Many Requests | Rate limit exceeded |
| **500** | Internal Server Error | Server error (logged for investigation) |
| **502** | Bad Gateway | Upstream service (OPA, MinIO) unavailable |
| **503** | Service Unavailable | Server maintenance, temporary downtime |

### Retry Strategy

**Idempotent Requests** (GET, PUT, DELETE):
- Safe to retry on network errors
- Use exponential backoff (1s, 2s, 4s, 8s, 16s)

**Non-Idempotent Requests** (POST):
- Avoid retrying (may create duplicate resources)
- Use idempotency keys for safe retries (future feature)

**Example Retry Logic** (Python):
```python
import requests
import time

def api_request_with_retry(url, method="GET", max_retries=5, **kwargs):
    """Make API request with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, **kwargs)

            # Don't retry client errors (4xx)
            if 400 <= response.status_code < 500:
                response.raise_for_status()

            # Retry server errors (5xx) and rate limits (429)
            if response.status_code >= 500 or response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Retry {attempt+1}/{max_retries} after {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    response.raise_for_status()

            return response

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Network error, retry {attempt+1}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise e

    return None

# Usage
response = api_request_with_retry(
    "http://localhost:8000/api/v1/auth/me",
    headers={"Authorization": f"Bearer {token}"}
)
```

---

## Rate Limiting & Pagination

### Rate Limiting

**SDLC Orchestrator does NOT currently enforce rate limiting** (as of Week 4 Day 1).

**Future Implementation** (Week 8-10):
- **Rate Limit**: 1000 requests/hour/user
- **Rate Limit Headers**:
  - `X-RateLimit-Limit`: Max requests allowed per hour
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

**Rate Limit Exceeded Response** (429):
```json
{
  "detail": "Rate limit exceeded. Try again in 3600 seconds."
}
```

### Pagination

**Current Implementation**: Offset-based pagination

**Query Parameters**:
- `limit`: Max results per page (default: 20, max: 100)
- `offset`: Number of records to skip (default: 0)

**Example**:
```bash
# Page 1 (records 0-19)
GET /api/v1/gates?limit=20&offset=0

# Page 2 (records 20-39)
GET /api/v1/gates?limit=20&offset=20

# Page 3 (records 40-59)
GET /api/v1/gates?limit=20&offset=40
```

**Response**:
```json
{
  "gates": [...],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

**Pagination Helper** (Python):
```python
def get_all_gates(client, stage=None):
    """Fetch all gates using pagination."""
    all_gates = []
    offset = 0
    limit = 100

    while True:
        response = client.get(
            "/api/v1/gates",
            params={"stage": stage, "limit": limit, "offset": offset}
        )
        data = response.json()

        all_gates.extend(data["gates"])

        if len(data["gates"]) < limit:
            break  # No more pages

        offset += limit

    return all_gates
```

---

## SDKs & Code Examples

### Python SDK

```python
# File: sdlc_client.py
import requests
import time
from typing import Optional, Dict, List

class SDLCClient:
    """SDLC Orchestrator Python SDK."""

    def __init__(self, base_url: str, email: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0

    def login(self):
        """Login and get tokens."""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": self.email, "password": self.password}
        )
        response.raise_for_status()
        data = response.json()

        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.token_expires_at = time.time() + data["expires_in"]

        return data["user"]

    def refresh_access_token(self):
        """Refresh access token."""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )
        response.raise_for_status()
        data = response.json()

        self.access_token = data["access_token"]
        self.token_expires_at = time.time() + data["expires_in"]

    def get_headers(self):
        """Get headers with auto-refresh."""
        if time.time() >= self.token_expires_at - 300:
            self.refresh_access_token()

        return {"Authorization": f"Bearer {self.access_token}"}

    def get(self, path: str, params: Optional[Dict] = None):
        """Make GET request."""
        response = requests.get(
            f"{self.base_url}{path}",
            headers=self.get_headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()

    def post(self, path: str, json: Optional[Dict] = None):
        """Make POST request."""
        response = requests.post(
            f"{self.base_url}{path}",
            headers=self.get_headers(),
            json=json
        )
        response.raise_for_status()
        return response.json()

    def put(self, path: str, json: Optional[Dict] = None):
        """Make PUT request."""
        response = requests.put(
            f"{self.base_url}{path}",
            headers=self.get_headers(),
            json=json
        )
        response.raise_for_status()
        return response.json()

    def delete(self, path: str):
        """Make DELETE request."""
        response = requests.delete(
            f"{self.base_url}{path}",
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()

    # ========== High-level API methods ==========

    def get_current_user(self):
        """Get current user info."""
        return self.get("/api/v1/auth/me")

    def list_gates(self, stage: Optional[str] = None, status: Optional[str] = None):
        """List gates."""
        params = {}
        if stage:
            params["stage"] = stage
        if status:
            params["status"] = status

        return self.get("/api/v1/gates", params=params)

    def get_gate(self, gate_id: str):
        """Get gate by ID."""
        return self.get(f"/api/v1/gates/{gate_id}")

    def create_gate(self, gate_number: str, gate_name: str, stage: str, description: Optional[str] = None):
        """Create new gate."""
        data = {
            "gate_number": gate_number,
            "gate_name": gate_name,
            "stage": stage
        }
        if description:
            data["description"] = description

        return self.post("/api/v1/gates", json=data)

    def update_gate(self, gate_id: str, **kwargs):
        """Update gate."""
        return self.put(f"/api/v1/gates/{gate_id}", json=kwargs)

    def delete_gate(self, gate_id: str):
        """Delete gate."""
        return self.delete(f"/api/v1/gates/{gate_id}")

# Usage Example
if __name__ == "__main__":
    # Initialize client
    client = SDLCClient(
        base_url="http://localhost:8000",
        email="test@example.com",
        password="password123"
    )

    # Login
    user = client.login()
    print(f"✅ Logged in as: {user['full_name']} ({user['email']})")

    # List gates
    gates_response = client.list_gates(stage="WHAT", status="PENDING")
    print(f"\n📋 Found {gates_response['total']} gates:")
    for gate in gates_response['gates']:
        print(f"  - {gate['gate_number']}: {gate['gate_name']} ({gate['status']})")

    # Create new gate
    new_gate = client.create_gate(
        gate_number="G2",
        gate_name="Architecture Approved",
        stage="HOW",
        description="System architecture reviewed and approved"
    )
    print(f"\n✅ Created gate: {new_gate['gate_number']} - {new_gate['gate_name']}")

    # Update gate status
    updated_gate = client.update_gate(new_gate['id'], status="PASSED")
    print(f"✅ Updated gate status to: {updated_gate['status']}")
```

---

## Best Practices

### 1. Always Use HTTPS in Production

```python
# ❌ DON'T use HTTP in production
base_url = "http://api.sdlc-orchestrator.com"  # Insecure!

# ✅ DO use HTTPS
base_url = "https://api.sdlc-orchestrator.com"  # Secure
```

### 2. Store Tokens Securely

```python
# ❌ DON'T hardcode tokens
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # Bad!

# ✅ DO use environment variables
import os
access_token = os.getenv("SDLC_ACCESS_TOKEN")

# ✅ DO use system keyring
import keyring
access_token = keyring.get_password("sdlc-orchestrator", "access_token")
```

### 3. Handle Token Expiration Gracefully

```python
# ✅ Auto-refresh tokens before they expire
if time.time() >= token_expires_at - 300:  # 5 min buffer
    client.refresh_access_token()
```

### 4. Use Pagination for Large Datasets

```python
# ❌ DON'T fetch all records at once
gates = client.get("/api/v1/gates?limit=10000")  # May timeout!

# ✅ DO use pagination
offset = 0
limit = 100
all_gates = []

while True:
    response = client.get(f"/api/v1/gates?limit={limit}&offset={offset}")
    all_gates.extend(response["gates"])

    if len(response["gates"]) < limit:
        break

    offset += limit
```

### 5. Implement Retry Logic for Resilience

```python
# ✅ Retry on server errors (5xx) and rate limits (429)
import time
import requests

for attempt in range(5):
    try:
        response = requests.get(url, headers=headers)

        if response.status_code >= 500 or response.status_code == 429:
            wait_time = 2 ** attempt  # Exponential backoff
            time.sleep(wait_time)
            continue

        response.raise_for_status()
        break
    except requests.exceptions.RequestException as e:
        if attempt == 4:
            raise e
        time.sleep(2 ** attempt)
```

---

## Troubleshooting

### Common Errors

#### 401 Unauthorized - Missing or Invalid Token

**Problem**: API returns `401 Unauthorized` with `"detail": "Not authenticated"`

**Solution**:
1. Check that you're sending the `Authorization` header:
   ```bash
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. Verify token hasn't expired (60 min TTL):
   ```python
   import jwt

   # Decode token (don't verify signature for debugging)
   decoded = jwt.decode(token, options={"verify_signature": False})
   print(f"Token expires at: {decoded['exp']}")
   print(f"Current time: {time.time()}")
   ```

3. Refresh token if expired:
   ```python
   client.refresh_access_token()
   ```

#### 404 Not Found - Resource Doesn't Exist

**Problem**: API returns `404 Not Found` with `"detail": "Gate not found"`

**Solution**:
1. Verify resource ID is correct (valid UUID):
   ```python
   import uuid

   try:
       uuid.UUID(gate_id)
   except ValueError:
       print("Invalid UUID!")
   ```

2. Check resource exists:
   ```bash
   # List all gates
   curl -X GET http://localhost:8000/api/v1/gates \
     -H "Authorization: Bearer ${TOKEN}"
   ```

#### 413 Payload Too Large - File Upload Exceeds Limit

**Problem**: Uploading evidence file fails with `413 Payload Too Large`

**Solution**:
1. Check file size (max 10MB):
   ```python
   import os

   file_size = os.path.getsize("requirements.pdf")
   if file_size > 10 * 1024 * 1024:
       print("File too large! Max 10MB")
   ```

2. Compress PDF or upload to external storage (Google Drive, Dropbox)

---

## OpenAPI Specification

**Interactive API Documentation** (Swagger UI):
- **Local**: http://localhost:8000/docs
- **Production**: https://api.sdlc-orchestrator.com/docs

**ReDoc Documentation**:
- **Local**: http://localhost:8000/redoc
- **Production**: https://api.sdlc-orchestrator.com/redoc

**OpenAPI JSON**:
- **Local**: http://localhost:8000/openapi.json
- **Production**: https://api.sdlc-orchestrator.com/openapi.json

---

## Support & Resources

### Documentation
- **API Reference**: https://docs.sdlc-orchestrator.com/api
- **Architecture Diagrams**: [C4-ARCHITECTURE-DIAGRAMS.md](../02-System-Architecture/C4-ARCHITECTURE-DIAGRAMS.md)
- **Deployment Guide**: *(Coming in Week 4 Day 1-2)*

### Community
- **GitHub Issues**: https://github.com/sdlc-orchestrator/issues
- **Slack Community**: https://sdlc-orchestrator.slack.com
- **Email Support**: api-support@sdlc-orchestrator.com

### Status & Monitoring
- **System Status**: https://status.sdlc-orchestrator.com
- **API Uptime**: 99.9% SLA (Enterprise tier)

---

**Last Updated**: November 18, 2025
**Owner**: Backend Lead + CTO
**Status**: ✅ ACTIVE (Week 4 Day 1)

---

**End of API Developer Guide v1.0.0**
