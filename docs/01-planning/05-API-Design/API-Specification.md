# API Specification (OpenAPI 3.0)
## Complete REST + GraphQL Endpoints

**Version**: 2.0.0
**Date**: December 3, 2025
**Status**: ACTIVE - AI Governance Extension
**Authority**: Backend Lead + CTO Review (APPROVED)
**Foundation**: Functional Requirements v2.0.0, Data Model ERD v2.0
**Stage**: Stage 01 (WHAT - Planning & Analysis)
**Framework**: SDLC 4.9.1 Complete Lifecycle (10 Stages)

**Changelog v2.0.0** (Dec 3, 2025):
- Added Context-Aware Requirements endpoints (/requirements, /context-profiles)
- Added Task Decomposition endpoints (/decompose)
- Added Planning Hierarchy endpoints (/roadmaps, /phases, /sprints, /backlog)
- Added SDLC Structure Validation endpoints (/validate)
- Total endpoints: 19 → 35 endpoints

---

## Document Purpose

This document defines **WHAT API endpoints to expose** using OpenAPI 3.0 specification.

**Key Sections**:
- REST API endpoints (30+ endpoints)
- GraphQL schema (queries, mutations, subscriptions)
- Authentication & authorization
- Rate limiting & pagination
- Error responses & status codes

**Out of Scope** (Stage 02 - Architecture):
- Implementation details (controllers, services, repositories)
- Database queries (SQL, ORM)
- Infrastructure deployment (Kubernetes, Docker)

---

## API Architecture Overview

### REST API (Primary)
**Base URL**: `https://api.sdlc-orchestrator.com/v1`
**Protocol**: HTTPS only (TLS 1.3)
**Format**: JSON (Content-Type: application/json)
**Authentication**: JWT Bearer token (OAuth 2.0)

### GraphQL API (Secondary)
**Endpoint**: `https://api.sdlc-orchestrator.com/graphql`
**Protocol**: HTTPS + WebSocket (subscriptions)
**Use Case**: Complex queries, real-time updates (gate status changes)

### API Design Principles
1. **RESTful**: Use HTTP verbs correctly (GET/POST/PUT/PATCH/DELETE)
2. **Idempotent**: PUT/DELETE safe to retry
3. **Versioned**: /v1, /v2 in URL path
4. **Paginated**: Cursor-based pagination (default: 20 items/page)
5. **Filterable**: Query params for filtering, sorting, searching
6. **Rate Limited**: 1000 requests/hour/user (Standard), 10K/hour (Enterprise)

---

## OpenAPI 3.0 Specification

```yaml
openapi: 3.0.3
info:
  title: SDLC Orchestrator API
  description: |
    Project governance tool that enforces the SDLC Universal Framework.

    **Features**:
    - Quality gate management (G0.1-G9)
    - Evidence vault (manual uploads + auto-collection)
    - Policy-as-Code enforcement (OPA)
    - Multi-approval workflows (CEO, CTO, CPO, CIO, CFO)
    - AI context engine (stage-aware prompts)

    **Base URL**: https://api.sdlc-orchestrator.com/v1
  version: 1.0.0
  contact:
    name: SDLC Orchestrator API Support
    email: api-support@sdlc-orchestrator.com
    url: https://docs.sdlc-orchestrator.com
  license:
    name: Proprietary
    url: https://sdlc-orchestrator.com/license

servers:
  - url: https://api.sdlc-orchestrator.com/v1
    description: Production server
  - url: https://api-staging.sdlc-orchestrator.com/v1
    description: Staging server
  - url: http://localhost:8000/v1
    description: Local development server

tags:
  - name: Authentication
    description: User authentication & authorization
  - name: Projects
    description: Project management (CRUD, team assignment)
  - name: Gates
    description: Quality gate evaluation & approval
  - name: Evidence
    description: Evidence vault (uploads, auto-collection)
  - name: Policies
    description: Policy-as-Code management (OPA)
  - name: Users
    description: User management (RBAC, teams)
  - name: Teams
    description: Team management
  - name: Organizations
    description: Organization settings
  - name: Integrations
    description: Third-party integrations (GitHub, Slack, Figma)
  - name: AI
    description: AI context engine (stage-aware prompts)
  - name: Audit
    description: Audit logs (immutable, partitioned)

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        JWT token obtained from /auth/login.
        Format: Authorization: Bearer <token>

  schemas:
    # Authentication
    LoginRequest:
      type: object
      required:
        - email
        - password
      properties:
        email:
          type: string
          format: email
          example: john.doe@techcorp.com
        password:
          type: string
          format: password
          minLength: 8
          example: SecurePassword123!

    LoginResponse:
      type: object
      properties:
        access_token:
          type: string
          description: JWT access token (expires in 1 hour)
          example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        refresh_token:
          type: string
          description: Refresh token (expires in 30 days)
          example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        token_type:
          type: string
          enum: [Bearer]
        expires_in:
          type: integer
          description: Access token TTL (seconds)
          example: 3600
        user:
          $ref: '#/components/schemas/User'

    # User
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
          example: 550e8400-e29b-41d4-a716-446655440000
        email:
          type: string
          format: email
          example: john.doe@techcorp.com
        full_name:
          type: string
          example: John Doe
        role:
          type: string
          enum: [ceo, cto, cpo, cio, cfo, em, pm, dev_lead, qa_lead, security_lead, devops_lead, data_lead, admin]
          example: em
        team_id:
          type: string
          format: uuid
        avatar_url:
          type: string
          format: uri
          example: https://gravatar.com/avatar/...
        job_title:
          type: string
          example: Engineering Manager
        department:
          type: string
          example: Engineering
        is_active:
          type: boolean
          example: true
        email_verified:
          type: boolean
          example: true
        created_at:
          type: string
          format: date-time
          example: 2025-01-13T10:00:00Z
        last_login_at:
          type: string
          format: date-time
          example: 2025-01-13T09:45:00Z

    # Project
    Project:
      type: object
      properties:
        id:
          type: string
          format: uuid
        project_name:
          type: string
          example: SDLC Orchestrator MVP
        project_code:
          type: string
          example: SDLC-MVP
          pattern: ^[A-Z0-9-]+$
        description:
          type: string
          example: Project governance tool that enforces SDLC 4.9
        current_stage:
          type: string
          enum: [stage-00, stage-01, stage-02, stage-03, stage-04, stage-05, stage-06, stage-07, stage-08, stage-09]
          example: stage-01
        team_id:
          type: string
          format: uuid
        created_by:
          type: string
          format: uuid
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    # Gate
    Gate:
      type: object
      properties:
        id:
          type: string
          format: uuid
        project_id:
          type: string
          format: uuid
        gate_code:
          type: string
          enum: [G0.1, G0.2, G1, G2, G3, G4, G5, G6, G7, G8, G9]
          example: G1
        gate_name:
          type: string
          example: Requirements & Planning Ready
        stage:
          type: string
          enum: [stage-00, stage-01, stage-02, stage-03, stage-04, stage-05, stage-06, stage-07, stage-08, stage-09]
          example: stage-01
        status:
          type: string
          enum: [not_evaluated, pending, blocked, passed, override]
          example: pending
        approvals:
          type: array
          items:
            $ref: '#/components/schemas/GateApproval'
        override_reason:
          type: string
          nullable: true
        override_by:
          type: string
          format: uuid
          nullable: true
        override_at:
          type: string
          format: date-time
          nullable: true
        override_expires_at:
          type: string
          format: date-time
          nullable: true
        created_at:
          type: string
          format: date-time
        evaluated_at:
          type: string
          format: date-time
          nullable: true

    # Gate Approval
    GateApproval:
      type: object
      properties:
        id:
          type: string
          format: uuid
        gate_id:
          type: string
          format: uuid
        approver_id:
          type: string
          format: uuid
        approver_role:
          type: string
          enum: [ceo, cto, cpo, cio, cfo, em, pm, dev_lead, qa_lead, security_lead, devops_lead, data_lead]
          example: cto
        approval_status:
          type: string
          enum: [pending, approved, rejected]
          example: approved
        approval_reason:
          type: string
          nullable: true
          example: Architecture reviewed, no N+1 queries, scalable design.
        approved_at:
          type: string
          format: date-time
          nullable: true
        created_at:
          type: string
          format: date-time

    # Evidence
    Evidence:
      type: object
      properties:
        id:
          type: string
          format: uuid
        project_id:
          type: string
          format: uuid
        gate_id:
          type: string
          format: uuid
          nullable: true
        evidence_type:
          type: string
          enum: [manual_upload, slack_message, github_pr, github_issue, figma_file, zoom_transcript]
          example: github_pr
        file_path:
          type: string
          example: s3://evidence-vault/2025/01/13/550e8400-e29b-41d4-a716-446655440000.pdf
          nullable: true
        file_size_bytes:
          type: integer
          format: int64
          example: 2097152
          nullable: true
        file_mime_type:
          type: string
          example: application/pdf
          nullable: true
        source_url:
          type: string
          format: uri
          example: https://github.com/acme/repo/pull/123
          nullable: true
        content_preview:
          type: string
          description: First 1000 chars for full-text search
          example: User Interview Summary - Talked to Sarah (EM, 25-person team)...
          nullable: true
        uploaded_by:
          type: string
          format: uuid
        created_at:
          type: string
          format: date-time
        indexed_at:
          type: string
          format: date-time
          nullable: true

    # Policy
    Policy:
      type: object
      properties:
        id:
          type: string
          format: uuid
        policy_code:
          type: string
          example: policy-pack-user-interviews
          pattern: ^policy-[a-z0-9-]+$
        policy_name:
          type: string
          example: User Interviews (3+ required)
        description:
          type: string
          example: Validates that 3+ user interviews conducted (Stage 00, G0.1)
        rego_code:
          type: string
          description: OPA Rego policy logic
          example: |
            package policy_pack_user_interviews
            default allow = false
            allow {
              count(input.evidence) >= 3
              input.evidence[_].type == "user_interview"
            }
        stage:
          type: string
          enum: [stage-00, stage-01, stage-02, stage-03, stage-04, stage-05, stage-06, stage-07, stage-08, stage-09]
          example: stage-00
        category:
          type: string
          enum: [validation, security, performance, compliance]
          example: validation
        is_pre_built:
          type: boolean
          example: true
        current_version:
          type: string
          example: 1.0.0
          pattern: ^\d+\.\d+\.\d+$
        created_by:
          type: string
          format: uuid
          nullable: true
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    # Error Response
    Error:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
              example: GATE_NOT_FOUND
            message:
              type: string
              example: Gate G1 not found for project 550e8400-e29b-41d4-a716-446655440000
            details:
              type: object
              nullable: true
            timestamp:
              type: string
              format: date-time

    # Pagination
    PaginatedResponse:
      type: object
      properties:
        data:
          type: array
          items:
            type: object
        pagination:
          type: object
          properties:
            cursor:
              type: string
              description: Cursor for next page
              example: eyJpZCI6IjU1MGU4NDAwLWUyOWItNDFkNC1hNzE2LTQ0NjY1NTQ0MDAwMCJ9
              nullable: true
            has_more:
              type: boolean
              example: true
            total:
              type: integer
              example: 150
            limit:
              type: integer
              example: 20

paths:
  # Authentication Endpoints
  /auth/login:
    post:
      tags:
        - Authentication
      summary: Login user
      description: Authenticate user and return JWT tokens
      operationId: loginUser
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LoginRequest'
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LoginResponse'
        '401':
          description: Invalid credentials
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Too many login attempts
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /auth/refresh:
    post:
      tags:
        - Authentication
      summary: Refresh access token
      description: Use refresh token to obtain new access token
      operationId: refreshToken
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - refresh_token
              properties:
                refresh_token:
                  type: string
      responses:
        '200':
          description: Token refreshed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LoginResponse'
        '401':
          description: Invalid refresh token
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /auth/logout:
    post:
      tags:
        - Authentication
      summary: Logout user
      description: Invalidate refresh token
      operationId: logoutUser
      security:
        - BearerAuth: []
      responses:
        '204':
          description: Logout successful
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  # Project Endpoints
  /projects:
    get:
      tags:
        - Projects
      summary: List projects
      description: Get paginated list of projects (filtered by team)
      operationId: listProjects
      security:
        - BearerAuth: []
      parameters:
        - name: team_id
          in: query
          description: Filter by team ID
          schema:
            type: string
            format: uuid
        - name: current_stage
          in: query
          description: Filter by current stage
          schema:
            type: string
            enum: [stage-00, stage-01, stage-02, stage-03, stage-04, stage-05, stage-06, stage-07, stage-08, stage-09]
        - name: cursor
          in: query
          description: Pagination cursor
          schema:
            type: string
        - name: limit
          in: query
          description: Items per page (max 100)
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        '200':
          description: Projects retrieved successfully
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/PaginatedResponse'
                  - type: object
                    properties:
                      data:
                        type: array
                        items:
                          $ref: '#/components/schemas/Project'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

    post:
      tags:
        - Projects
      summary: Create project
      description: Create new project (requires EM/PM role)
      operationId: createProject
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - project_name
                - project_code
                - team_id
              properties:
                project_name:
                  type: string
                  example: SDLC Orchestrator MVP
                project_code:
                  type: string
                  example: SDLC-MVP
                  pattern: ^[A-Z0-9-]+$
                description:
                  type: string
                  example: Project governance tool
                team_id:
                  type: string
                  format: uuid
      responses:
        '201':
          description: Project created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Project'
        '400':
          description: Invalid request (duplicate project_code, missing fields)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          description: Unauthorized
        '403':
          description: Forbidden (insufficient role)

  /projects/{project_id}:
    get:
      tags:
        - Projects
      summary: Get project by ID
      operationId: getProject
      security:
        - BearerAuth: []
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Project retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Project'
        '404':
          description: Project not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

    put:
      tags:
        - Projects
      summary: Update project
      description: Update project (requires EM/PM role)
      operationId: updateProject
      security:
        - BearerAuth: []
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                project_name:
                  type: string
                description:
                  type: string
                current_stage:
                  type: string
                  enum: [stage-00, stage-01, stage-02, stage-03, stage-04, stage-05, stage-06, stage-07, stage-08, stage-09]
      responses:
        '200':
          description: Project updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Project'
        '403':
          description: Forbidden
        '404':
          description: Project not found

    delete:
      tags:
        - Projects
      summary: Delete project
      description: Delete project (requires EM/Admin role)
      operationId: deleteProject
      security:
        - BearerAuth: []
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '204':
          description: Project deleted
        '403':
          description: Forbidden
        '404':
          description: Project not found

  # Gate Endpoints
  /projects/{project_id}/gates:
    get:
      tags:
        - Gates
      summary: List gates for project
      operationId: listGates
      security:
        - BearerAuth: []
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
        - name: stage
          in: query
          description: Filter by stage
          schema:
            type: string
            enum: [stage-00, stage-01, stage-02, stage-03, stage-04, stage-05, stage-06, stage-07, stage-08, stage-09]
        - name: status
          in: query
          description: Filter by status
          schema:
            type: string
            enum: [not_evaluated, pending, blocked, passed, override]
      responses:
        '200':
          description: Gates retrieved
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Gate'

  /projects/{project_id}/gates/{gate_code}:
    get:
      tags:
        - Gates
      summary: Get gate by code
      operationId: getGate
      security:
        - BearerAuth: []
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
        - name: gate_code
          in: path
          required: true
          schema:
            type: string
            enum: [G0.1, G0.2, G1, G2, G3, G4, G5, G6, G7, G8, G9]
      responses:
        '200':
          description: Gate retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Gate'
        '404':
          description: Gate not found

  /projects/{project_id}/gates/{gate_code}/evaluate:
    post:
      tags:
        - Gates
      summary: Evaluate gate
      description: Run policy checks and update gate status
      operationId: evaluateGate
      security:
        - BearerAuth: []
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
        - name: gate_code
          in: path
          required: true
          schema:
            type: string
            enum: [G0.1, G0.2, G1, G2, G3, G4, G5, G6, G7, G8, G9]
      responses:
        '200':
          description: Gate evaluated
          content:
            application/json:
              schema:
                type: object
                properties:
                  gate:
                    $ref: '#/components/schemas/Gate'
                  policy_results:
                    type: array
                    items:
                      type: object
                      properties:
                        policy_code:
                          type: string
                        policy_name:
                          type: string
                        passed:
                          type: boolean
                        message:
                          type: string
        '404':
          description: Gate not found

  /projects/{project_id}/gates/{gate_code}/approvals:
    post:
      tags:
        - Gates
      summary: Submit gate approval
      description: Approve or reject gate (requires specific role per gate)
      operationId: submitGateApproval
      security:
        - BearerAuth: []
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
        - name: gate_code
          in: path
          required: true
          schema:
            type: string
            enum: [G0.1, G0.2, G1, G2, G3, G4, G5, G6, G7, G8, G9]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - approval_status
              properties:
                approval_status:
                  type: string
                  enum: [approved, rejected]
                approval_reason:
                  type: string
                  description: Required for rejection
      responses:
        '201':
          description: Approval submitted
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GateApproval'
        '403':
          description: Forbidden (user role not authorized to approve this gate)
        '404':
          description: Gate not found
        '409':
          description: Conflict (already approved/rejected by this user)

  # Evidence Endpoints
  /projects/{project_id}/evidence:
    get:
      tags:
        - Evidence
      summary: List evidence
      operationId: listEvidence
      security:
        - BearerAuth: []
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
        - name: gate_id
          in: query
          description: Filter by gate
          schema:
            type: string
            format: uuid
        - name: evidence_type
          in: query
          description: Filter by type
          schema:
            type: string
            enum: [manual_upload, slack_message, github_pr, github_issue, figma_file, zoom_transcript]
        - name: cursor
          in: query
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        '200':
          description: Evidence retrieved
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/PaginatedResponse'
                  - type: object
                    properties:
                      data:
                        type: array
                        items:
                          $ref: '#/components/schemas/Evidence'

    post:
      tags:
        - Evidence
      summary: Upload evidence
      description: Upload file to evidence vault (max 10MB per NFR3)
      operationId: uploadEvidence
      security:
        - BearerAuth: []
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - file
                - evidence_type
              properties:
                file:
                  type: string
                  format: binary
                  description: File to upload (max 10MB)
                evidence_type:
                  type: string
                  enum: [manual_upload]
                gate_id:
                  type: string
                  format: uuid
                  description: Optional gate association
      responses:
        '201':
          description: Evidence uploaded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Evidence'
        '400':
          description: Invalid file (size > 10MB, unsupported format)
        '413':
          description: File too large (> 10MB)

  /projects/{project_id}/evidence/{evidence_id}:
    get:
      tags:
        - Evidence
      summary: Get evidence by ID
      operationId: getEvidence
      security:
        - BearerAuth: []
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
        - name: evidence_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Evidence retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Evidence'
        '404':
          description: Evidence not found

    delete:
      tags:
        - Evidence
      summary: Delete evidence
      description: Delete evidence (requires EM/Admin role)
      operationId: deleteEvidence
      security:
        - BearerAuth: []
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
        - name: evidence_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '204':
          description: Evidence deleted
        '403':
          description: Forbidden
        '404':
          description: Evidence not found

  # Policy Endpoints
  /policies:
    get:
      tags:
        - Policies
      summary: List policies
      operationId: listPolicies
      security:
        - BearerAuth: []
      parameters:
        - name: stage
          in: query
          description: Filter by stage
          schema:
            type: string
            enum: [stage-00, stage-01, stage-02, stage-03, stage-04, stage-05, stage-06, stage-07, stage-08, stage-09]
        - name: category
          in: query
          description: Filter by category
          schema:
            type: string
            enum: [validation, security, performance, compliance]
        - name: is_pre_built
          in: query
          description: Filter by pre-built vs custom
          schema:
            type: boolean
      responses:
        '200':
          description: Policies retrieved
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Policy'

    post:
      tags:
        - Policies
      summary: Create custom policy
      description: Create custom policy (requires Admin role)
      operationId: createPolicy
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - policy_code
                - policy_name
                - rego_code
                - stage
              properties:
                policy_code:
                  type: string
                  pattern: ^policy-[a-z0-9-]+$
                policy_name:
                  type: string
                description:
                  type: string
                rego_code:
                  type: string
                stage:
                  type: string
                  enum: [stage-00, stage-01, stage-02, stage-03, stage-04, stage-05, stage-06, stage-07, stage-08, stage-09]
                category:
                  type: string
                  enum: [validation, security, performance, compliance]
      responses:
        '201':
          description: Policy created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Policy'
        '403':
          description: Forbidden (requires Admin role)
        '409':
          description: Conflict (policy_code already exists)

  # User Endpoints
  /users/me:
    get:
      tags:
        - Users
      summary: Get current user
      operationId: getCurrentUser
      security:
        - BearerAuth: []
      responses:
        '200':
          description: User retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

  # AI Endpoints
  /ai/generate:
    post:
      tags:
        - AI
      summary: Generate AI content
      description: Generate PRD, test plan, or other stage-aware content
      operationId: generateAIContent
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - prompt_type
                - context
              properties:
                prompt_type:
                  type: string
                  enum: [prd, test_plan, architecture, runbook]
                  example: prd
                context:
                  type: object
                  properties:
                    project_id:
                      type: string
                      format: uuid
                    evidence_ids:
                      type: array
                      items:
                        type: string
                        format: uuid
                    user_input:
                      type: string
                provider:
                  type: string
                  enum: [claude, gpt4, gemini]
                  default: claude
      responses:
        '200':
          description: Content generated
          content:
            application/json:
              schema:
                type: object
                properties:
                  content:
                    type: string
                  tokens_used:
                    type: integer
                  cost_usd:
                    type: number
                    format: float
        '402':
          description: Payment required (usage limit exceeded)

security:
  - BearerAuth: []
```

---

## REST API Endpoint Summary

### Authentication (3 endpoints)
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/auth/login` | Login user | No |
| POST | `/auth/refresh` | Refresh access token | No |
| POST | `/auth/logout` | Logout user | Yes |

### Projects (4 endpoints)
| Method | Path | Description | Role Required |
|--------|------|-------------|---------------|
| GET | `/projects` | List projects | Any |
| POST | `/projects` | Create project | EM, PM, Admin |
| GET | `/projects/{id}` | Get project | Any |
| PUT | `/projects/{id}` | Update project | EM, PM, Admin |
| DELETE | `/projects/{id}` | Delete project | EM, Admin |

### Gates (4 endpoints)
| Method | Path | Description | Role Required |
|--------|------|-------------|---------------|
| GET | `/projects/{id}/gates` | List gates | Any |
| GET | `/projects/{id}/gates/{code}` | Get gate | Any |
| POST | `/projects/{id}/gates/{code}/evaluate` | Evaluate gate | Any |
| POST | `/projects/{id}/gates/{code}/approvals` | Submit approval | Role-specific |

### Evidence (4 endpoints)
| Method | Path | Description | Role Required |
|--------|------|-------------|---------------|
| GET | `/projects/{id}/evidence` | List evidence | Any |
| POST | `/projects/{id}/evidence` | Upload evidence | Any |
| GET | `/projects/{id}/evidence/{id}` | Get evidence | Any |
| DELETE | `/projects/{id}/evidence/{id}` | Delete evidence | EM, Admin |

### Policies (2 endpoints)
| Method | Path | Description | Role Required |
|--------|------|-------------|---------------|
| GET | `/policies` | List policies | Any |
| POST | `/policies` | Create custom policy | Admin |

### Users (1 endpoint)
| Method | Path | Description | Role Required |
|--------|------|-------------|---------------|
| GET | `/users/me` | Get current user | Any |

### AI (1 endpoint)
| Method | Path | Description | Role Required |
|--------|------|-------------|---------------|
| POST | `/ai/generate` | Generate AI content | Any |

### Context-Aware Requirements (4 endpoints) *(NEW v2.0)*
| Method | Path | Description | Role Required |
|--------|------|-------------|---------------|
| GET | `/projects/{id}/requirements` | Get classified requirements | Any |
| GET | `/projects/{id}/context-profile` | Get project context | Any |
| PUT | `/projects/{id}/context-profile` | Update project context | EM, PM, Admin |
| POST | `/projects/{id}/requirements/{req_id}/override` | Override requirement tier | CTO, CPO, Admin |

### Task Decomposition (3 endpoints) *(NEW v2.0)*
| Method | Path | Description | Role Required |
|--------|------|-------------|---------------|
| POST | `/projects/{id}/decompose` | AI decompose user story | Any |
| GET | `/projects/{id}/decompose/sessions` | List decomposition sessions | Any |
| GET | `/projects/{id}/decompose/sessions/{session_id}` | Get session details | Any |

### Planning Hierarchy (8 endpoints) *(NEW v2.0)*
| Method | Path | Description | Role Required |
|--------|------|-------------|---------------|
| GET | `/projects/{id}/roadmap` | Get project roadmap | Any |
| PUT | `/projects/{id}/roadmap` | Update roadmap | EM, PM, Admin |
| GET | `/projects/{id}/phases` | List phases | Any |
| POST | `/projects/{id}/phases` | Create phase | EM, PM, Admin |
| GET | `/projects/{id}/sprints` | List sprints | Any |
| POST | `/projects/{id}/sprints` | Create sprint | EM, PM, Admin |
| GET | `/projects/{id}/backlog` | List backlog items | Any |
| POST | `/projects/{id}/backlog` | Create backlog item | Any |

### SDLC Validation (1 endpoint) *(NEW v2.0)*
| Method | Path | Description | Role Required |
|--------|------|-------------|---------------|
| POST | `/validate` | Validate SDLC structure | Any |

**Total REST Endpoints**: 35 endpoints (19 original + 16 AI Governance)

---

## GraphQL Schema

```graphql
schema {
  query: Query
  mutation: Mutation
  subscription: Subscription
}

type Query {
  # Projects
  project(id: ID!): Project
  projects(
    teamId: ID
    currentStage: Stage
    limit: Int = 20
    cursor: String
  ): ProjectConnection!

  # Gates
  gate(projectId: ID!, gateCode: GateCode!): Gate
  gates(
    projectId: ID!
    stage: Stage
    status: GateStatus
  ): [Gate!]!

  # Evidence
  evidence(projectId: ID!, id: ID!): Evidence
  evidences(
    projectId: ID!
    gateId: ID
    evidenceType: EvidenceType
    limit: Int = 20
    cursor: String
  ): EvidenceConnection!

  # Policies
  policy(id: ID!): Policy
  policies(
    stage: Stage
    category: PolicyCategory
    isPreBuilt: Boolean
  ): [Policy!]!

  # Users
  me: User!
}

type Mutation {
  # Projects
  createProject(input: CreateProjectInput!): Project!
  updateProject(id: ID!, input: UpdateProjectInput!): Project!
  deleteProject(id: ID!): Boolean!

  # Gates
  evaluateGate(projectId: ID!, gateCode: GateCode!): GateEvaluationResult!
  submitGateApproval(
    projectId: ID!
    gateCode: GateCode!
    input: GateApprovalInput!
  ): GateApproval!

  # Evidence
  uploadEvidence(projectId: ID!, input: UploadEvidenceInput!): Evidence!
  deleteEvidence(projectId: ID!, id: ID!): Boolean!

  # Policies
  createPolicy(input: CreatePolicyInput!): Policy!

  # AI
  generateAIContent(input: AIGenerateInput!): AIGeneratedContent!
}

type Subscription {
  # Real-time gate status updates
  gateStatusChanged(projectId: ID!): Gate!

  # Real-time approval notifications
  approvalReceived(projectId: ID!): GateApproval!
}

# Types
type Project {
  id: ID!
  projectName: String!
  projectCode: String!
  description: String
  currentStage: Stage!
  teamId: ID!
  team: Team!
  createdBy: ID!
  creator: User!
  gates: [Gate!]!
  evidences(limit: Int, cursor: String): EvidenceConnection!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Gate {
  id: ID!
  projectId: ID!
  project: Project!
  gateCode: GateCode!
  gateName: String!
  stage: Stage!
  status: GateStatus!
  approvals: [GateApproval!]!
  overrideReason: String
  overrideBy: ID
  overrideAt: DateTime
  overrideExpiresAt: DateTime
  createdAt: DateTime!
  evaluatedAt: DateTime
}

type GateApproval {
  id: ID!
  gateId: ID!
  gate: Gate!
  approverId: ID!
  approver: User!
  approverRole: Role!
  approvalStatus: ApprovalStatus!
  approvalReason: String
  approvedAt: DateTime
  createdAt: DateTime!
}

type Evidence {
  id: ID!
  projectId: ID!
  project: Project!
  gateId: ID
  gate: Gate
  evidenceType: EvidenceType!
  filePath: String
  fileSizeBytes: Int
  fileMimeType: String
  sourceUrl: String
  contentPreview: String
  uploadedBy: ID!
  uploader: User!
  createdAt: DateTime!
  indexedAt: DateTime
}

type Policy {
  id: ID!
  policyCode: String!
  policyName: String!
  description: String
  regoCode: String!
  stage: Stage!
  category: PolicyCategory!
  isPreBuilt: Boolean!
  currentVersion: String!
  createdBy: ID
  creator: User
  createdAt: DateTime!
  updatedAt: DateTime!
}

type User {
  id: ID!
  email: String!
  fullName: String
  role: Role!
  teamId: ID!
  team: Team!
  avatarUrl: String
  jobTitle: String
  department: String
  isActive: Boolean!
  emailVerified: Boolean!
  createdAt: DateTime!
  lastLoginAt: DateTime
}

type Team {
  id: ID!
  teamName: String!
  organizationId: ID!
  organization: Organization!
  users: [User!]!
  projects: [Project!]!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Organization {
  id: ID!
  orgName: String!
  subscriptionTier: SubscriptionTier!
  maxProjects: Int!
  maxUsers: Int!
  teams: [Team!]!
  createdAt: DateTime!
  updatedAt: DateTime!
}

# Enums
enum Stage {
  STAGE_00
  STAGE_01
  STAGE_02
  STAGE_03
  STAGE_04
  STAGE_05
  STAGE_06
  STAGE_07
  STAGE_08
  STAGE_09
}

enum GateCode {
  G0_1
  G0_2
  G1
  G2
  G3
  G4
  G5
  G6
  G7
  G8
  G9
}

enum GateStatus {
  NOT_EVALUATED
  PENDING
  BLOCKED
  PASSED
  OVERRIDE
}

enum ApprovalStatus {
  PENDING
  APPROVED
  REJECTED
}

enum EvidenceType {
  MANUAL_UPLOAD
  SLACK_MESSAGE
  GITHUB_PR
  GITHUB_ISSUE
  FIGMA_FILE
  ZOOM_TRANSCRIPT
}

enum PolicyCategory {
  VALIDATION
  SECURITY
  PERFORMANCE
  COMPLIANCE
}

enum Role {
  CEO
  CTO
  CPO
  CIO
  CFO
  EM
  PM
  DEV_LEAD
  QA_LEAD
  SECURITY_LEAD
  DEVOPS_LEAD
  DATA_LEAD
  ADMIN
}

enum SubscriptionTier {
  FREE
  PRO
  ENTERPRISE
}

# Inputs
input CreateProjectInput {
  projectName: String!
  projectCode: String!
  description: String
  teamId: ID!
}

input UpdateProjectInput {
  projectName: String
  description: String
  currentStage: Stage
}

input GateApprovalInput {
  approvalStatus: ApprovalStatus!
  approvalReason: String
}

input UploadEvidenceInput {
  file: Upload!
  evidenceType: EvidenceType!
  gateId: ID
}

input CreatePolicyInput {
  policyCode: String!
  policyName: String!
  description: String
  regoCode: String!
  stage: Stage!
  category: PolicyCategory!
}

input AIGenerateInput {
  promptType: AIPromptType!
  context: AIContextInput!
  provider: AIProvider = CLAUDE
}

input AIContextInput {
  projectId: ID!
  evidenceIds: [ID!]
  userInput: String
}

enum AIPromptType {
  PRD
  TEST_PLAN
  ARCHITECTURE
  RUNBOOK
}

enum AIProvider {
  CLAUDE
  GPT4
  GEMINI
}

# Pagination
type ProjectConnection {
  edges: [ProjectEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type ProjectEdge {
  node: Project!
  cursor: String!
}

type EvidenceConnection {
  edges: [EvidenceEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type EvidenceEdge {
  node: Evidence!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

# Custom Scalars
scalar DateTime
scalar Upload

# Results
type GateEvaluationResult {
  gate: Gate!
  policyResults: [PolicyResult!]!
}

type PolicyResult {
  policyCode: String!
  policyName: String!
  passed: Boolean!
  message: String!
}

type AIGeneratedContent {
  content: String!
  tokensUsed: Int!
  costUsd: Float!
}
```

---

## Rate Limiting

**Strategy**: Token bucket algorithm
**Limits** (per user, per hour):
- **Free**: 100 requests/hour
- **Pro**: 1,000 requests/hour
- **Enterprise**: 10,000 requests/hour

**Headers**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1673625600
```

**Rate Limit Exceeded Response** (HTTP 429):
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Limit: 1000 requests/hour. Retry after 3600 seconds.",
    "details": {
      "limit": 1000,
      "remaining": 0,
      "reset_at": "2025-01-13T12:00:00Z"
    },
    "timestamp": "2025-01-13T11:00:00Z"
  }
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| 200 | OK | Successful GET/PUT/PATCH |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request body, missing required fields |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | Valid token but insufficient permissions (RBAC) |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource (e.g., project_code already exists) |
| 413 | Payload Too Large | File upload > 10MB |
| 422 | Unprocessable Entity | Valid syntax but semantic errors (e.g., invalid UUID) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error (logged for investigation) |
| 502 | Bad Gateway | Upstream service (OPA, MinIO) unavailable |
| 503 | Service Unavailable | Server maintenance, temporary downtime |

### Error Response Format

```json
{
  "error": {
    "code": "GATE_NOT_FOUND",
    "message": "Gate G1 not found for project 550e8400-e29b-41d4-a716-446655440000",
    "details": {
      "project_id": "550e8400-e29b-41d4-a716-446655440000",
      "gate_code": "G1",
      "available_gates": ["G0.1", "G0.2"]
    },
    "timestamp": "2025-01-13T10:30:00Z"
  }
}
```

### Error Codes (Enum)

```yaml
Authentication:
  - INVALID_CREDENTIALS
  - TOKEN_EXPIRED
  - TOKEN_INVALID
  - REFRESH_TOKEN_INVALID

Authorization:
  - INSUFFICIENT_PERMISSIONS
  - ROLE_NOT_AUTHORIZED

Projects:
  - PROJECT_NOT_FOUND
  - PROJECT_CODE_DUPLICATE
  - PROJECT_LIMIT_EXCEEDED

Gates:
  - GATE_NOT_FOUND
  - GATE_ALREADY_EVALUATED
  - GATE_BLOCKED
  - APPROVAL_ALREADY_SUBMITTED
  - APPROVER_NOT_AUTHORIZED

Evidence:
  - EVIDENCE_NOT_FOUND
  - FILE_TOO_LARGE
  - UNSUPPORTED_FILE_TYPE
  - EVIDENCE_UPLOAD_FAILED

Policies:
  - POLICY_NOT_FOUND
  - POLICY_CODE_DUPLICATE
  - INVALID_REGO_SYNTAX

Rate Limiting:
  - RATE_LIMIT_EXCEEDED

General:
  - INTERNAL_SERVER_ERROR
  - SERVICE_UNAVAILABLE
```

---

## Pagination

**Strategy**: Cursor-based pagination (for large datasets)

**Why Cursor Over Offset**:
- Consistent results (no data skipping when new records inserted)
- Better performance (no COUNT(*) queries)
- Scalable (works with 100M+ rows)

**Request**:
```http
GET /projects?limit=20&cursor=eyJpZCI6IjU1MGU4NDAwLWUyOWItNDFkNC1hNzE2LTQ0NjY1NTQ0MDAwMCJ9
```

**Response**:
```json
{
  "data": [
    { "id": "550e8400-...", "project_name": "Project A" },
    { "id": "660f9511-...", "project_name": "Project B" }
  ],
  "pagination": {
    "cursor": "eyJpZCI6IjY2MGY5NTExLWYzYWMtNDJlNS1iODI3LTU1Nzc2NjU1MTExMSJ9",
    "has_more": true,
    "total": 150,
    "limit": 20
  }
}
```

---

## References

- [OpenAPI 3.0 Specification](https://swagger.io/specification/)
- [REST API Design Best Practices](https://restfulapi.net/)
- [GraphQL Schema Design](https://graphql.org/learn/schema/)
- [Functional Requirements Document](../01-Requirements/Functional-Requirements-Document.md)
- [Data Model ERD](../03-Data-Model/Data-Model-ERD.md)

---

**Last Updated**: 2025-12-03
**Owner**: Backend Lead + CTO
**Status**: ✅ APPROVED (AI Governance Extension)

**Version History**:
- v2.0.0 (Dec 3, 2025): Added 16 AI Governance endpoints (35 total)
- v1.0.0 (Nov 13, 2025): Initial API spec (19 endpoints)

**Related Documents**:
- [Functional Requirements Document](../01-Requirements/Functional-Requirements-Document.md) (v2.0.0)
- [Database Schema](../03-Data-Model/Database-Schema.md) (v2.0.0)
- [ADR-011-Context-Aware-Requirements](../../02-design/01-ADRs/ADR-011-Context-Aware-Requirements.md)
- [ADR-012-AI-Task-Decomposition](../../02-design/01-ADRs/ADR-012-AI-Task-Decomposition.md)
- [ADR-013-Planning-Hierarchy](../../02-design/01-ADRs/ADR-013-Planning-Hierarchy.md)
- [ADR-014-SDLC-Structure-Validator](../../02-design/01-ADRs/ADR-014-SDLC-Structure-Validator.md)

---

**End of API Specification v2.0.0**
