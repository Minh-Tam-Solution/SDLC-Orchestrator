# AGENTS.md Technical Design Document
## Sprint 80 - Static Generator + Dynamic Overlay Architecture

---

**Document Information**

| Field | Value |
|-------|-------|
| **Document ID** | TDS-080-001 |
| **Version** | 1.0.0 |
| **Status** | DRAFT → CTO REVIEW |
| **Created** | January 19, 2026 |
| **Author** | Backend Lead |
| **Sprint** | 80 (Feb 3-14, 2026) |
| **Epic** | EP-07: AGENTS.md Integration |
| **ADR Reference** | ADR-029 |
| **Framework** | SDLC 6.1.0 |

---

## 1. Overview

### 1.1 Purpose

This document provides the technical design for implementing AGENTS.md integration in SDLC Orchestrator, based on CTO-approved ADR-029. The implementation follows a **two-layer architecture**:

1. **Static AGENTS.md**: Committed to repo, read by AI coding tools
2. **Dynamic Overlay**: Runtime context delivered via PR comments, CLI, API

### 1.2 Scope

**In Scope:**
- AGENTS.md Generator Service
- AGENTS.md Validator/Linter
- Context Overlay Service
- CLI commands (`sdlc agents init/validate/lint`)
- API endpoints (4 new endpoints)
- PR comment integration
- Database schema (2 new tables)

**Out of Scope (Sprint 81+):**
- VS Code Extension integration
- GitHub Check Run overlay injection
- Multi-repo AGENTS.md management
- AGENTS.md version history

### 1.3 Expert Feedback Integration

| Feedback | Implementation |
|----------|----------------|
| "Dynamic via commits = git pollution" | ✅ Overlay via PR comments, NOT commits |
| "150-line limit for AI context windows" | ✅ Enforced in generator |
| "No secrets in AGENTS.md" | ✅ Validator with secret patterns |
| "Static + Dynamic separation" | ✅ Two-layer architecture |

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SDLC Orchestrator                                   │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                          API Layer                                          │ │
│  │  ┌─────────────────┐  ┌───────────────────┐  ┌─────────────────────────┐   │ │
│  │  │  /agents-md/    │  │  /context-overlay │  │  CLI: sdlc agents       │   │ │
│  │  │  generate       │  │  get              │  │  init | validate | lint │   │ │
│  │  │  validate       │  │  pr-comment       │  │                         │   │ │
│  │  └────────┬────────┘  └────────┬──────────┘  └───────────┬─────────────┘   │ │
│  └───────────│────────────────────│──────────────────────────│────────────────┘ │
│              │                    │                          │                   │
│  ┌───────────▼────────────────────▼──────────────────────────▼────────────────┐ │
│  │                        Service Layer                                        │ │
│  │                                                                              │ │
│  │  ┌─────────────────────┐   ┌─────────────────────┐   ┌──────────────────┐  │ │
│  │  │  AgentsMdService    │   │ ContextOverlayService│   │ AgentsMdValidator│  │ │
│  │  │  ─────────────────  │   │ ────────────────────│   │ ────────────────  │  │ │
│  │  │  • generate()       │   │ • get_overlay()     │   │ • validate()     │  │ │
│  │  │  • _quick_start()   │   │ • format_pr_comment()│  │ • _find_secrets()│  │ │
│  │  │  • _architecture()  │   │ • format_cli()      │   │ • _check_struct()│  │ │
│  │  │  • _conventions()   │   │ • format_check_run()│   │ • _check_length()│  │ │
│  │  │  • _security()      │   └──────────┬──────────┘   └────────┬─────────┘  │ │
│  │  │  • _do_not()        │              │                       │             │ │
│  │  └──────────┬──────────┘              │                       │             │ │
│  │             │                         │                       │             │ │
│  └─────────────│─────────────────────────│───────────────────────│─────────────┘ │
│                │                         │                       │               │
│  ┌─────────────▼─────────────────────────▼───────────────────────▼─────────────┐ │
│  │                        Data Access Layer                                     │ │
│  │                                                                              │ │
│  │  ┌─────────────────────┐   ┌─────────────────────┐   ┌──────────────────┐  │ │
│  │  │  FileAnalyzer       │   │  GateService        │   │  SprintService   │  │ │
│  │  │  (repo file access) │   │  (stage/gate data)  │   │  (sprint data)   │  │ │
│  │  └─────────────────────┘   └─────────────────────┘   └──────────────────┘  │ │
│  │                                                                              │ │
│  │  ┌─────────────────────┐   ┌─────────────────────┐                          │ │
│  │  │  AgentsMdRepo       │   │  ContextOverlayRepo │                          │ │
│  │  │  (PostgreSQL)       │   │  (PostgreSQL)       │                          │ │
│  │  └─────────────────────┘   └─────────────────────┘                          │ │
│  └──────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘

External Integrations:
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  GitHub API     │   │  Project Repo   │   │  AI Coding Tools│
│  (PR comments)  │   │  (file read)    │   │  (consume AGENTS)│
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

### 2.2 Data Flow

```
AGENTS.md Generation Flow:
───────────────────────────

1. User runs: sdlc agents init
        │
        ▼
2. CLI calls: POST /api/v1/projects/{id}/agents-md/generate
        │
        ▼
3. AgentsMdService.generate():
        │
        ├── FileAnalyzer.analyze_project_structure()
        │     ├── Check docker-compose.yml exists
        │     ├── Check package.json / requirements.txt
        │     ├── Check tsconfig.json / pyproject.toml
        │     └── Check .github/workflows/
        │
        ├── Generate sections:
        │     ├── _generate_quick_start() → Setup commands
        │     ├── _generate_architecture() → Brief overview
        │     ├── _generate_conventions() → From config files
        │     ├── _generate_security() → OWASP + AGPL rules
        │     ├── _generate_git_workflow() → Branch/commit rules
        │     └── _generate_do_not() → Forbidden actions
        │
        ├── Combine sections (enforce ≤150 lines)
        │
        └── AgentsMdValidator.validate() → Check structure/secrets
                │
                ▼
4. Return AgentsMdFile to CLI
        │
        ▼
5. CLI writes AGENTS.md to repo root
        │
        ▼
6. User commits: git add AGENTS.md && git commit


Context Overlay Flow:
─────────────────────

1. PR created/updated on GitHub
        │
        ▼
2. Webhook → POST /api/v1/webhooks/github
        │
        ▼
3. ContextOverlayService.get_overlay(project_id):
        │
        ├── GateService.get_current_stage() → SDLC stage
        │
        ├── GateService.get_latest_gate_status() → G0.1, G3, etc
        │
        ├── SprintService.get_active_sprint() → Sprint context
        │
        ├── SecurityService.get_active_issues() → Constraints
        │
        └── Build ContextOverlay object
                │
                ▼
4. ContextOverlayService.format_pr_comment(overlay)
        │
        ▼
5. GitHubService.post_pr_comment(pr_number, comment)
        │
        ▼
6. AI tools (Cursor, Copilot) see comment in PR context
```

### 2.3 Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| **AgentsMdService** | Generate AGENTS.md from project analysis |
| **AgentsMdValidator** | Validate structure, length, forbidden content |
| **ContextOverlayService** | Generate runtime context overlays |
| **FileAnalyzer** | Analyze project files (docker-compose, config) |
| **AgentsMdRepository** | CRUD for agents_md_files table |
| **ContextOverlayRepository** | CRUD for context_overlays table |

---

## 3. Database Schema

### 3.1 New Tables

```sql
-- Alembic migration: s80_agents_md_tables.py

-- Table: agents_md_files
-- Stores generated AGENTS.md history per project
CREATE TABLE agents_md_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Content
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,  -- SHA256
    line_count INTEGER NOT NULL,
    sections JSONB NOT NULL,  -- ["Quick Start", "Architecture", ...]

    -- Generation metadata
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generated_by UUID REFERENCES users(id),
    generator_version VARCHAR(20) NOT NULL,  -- "1.0.0"
    source_analysis JSONB,  -- Files analyzed, configs found

    -- Validation
    validation_status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, valid, invalid
    validation_errors JSONB,
    validation_warnings JSONB,

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_line_count CHECK (line_count > 0 AND line_count <= 200),
    CONSTRAINT chk_validation_status CHECK (validation_status IN ('pending', 'valid', 'invalid'))
);

-- Indexes
CREATE INDEX idx_agents_md_files_project_id ON agents_md_files(project_id);
CREATE INDEX idx_agents_md_files_generated_at ON agents_md_files(generated_at DESC);
CREATE INDEX idx_agents_md_files_content_hash ON agents_md_files(content_hash);

-- Latest file per project view
CREATE VIEW v_latest_agents_md AS
SELECT DISTINCT ON (project_id)
    id, project_id, content, content_hash, line_count, sections,
    generated_at, generator_version, validation_status
FROM agents_md_files
ORDER BY project_id, generated_at DESC;


-- Table: context_overlays
-- Stores generated context overlays for audit
CREATE TABLE context_overlays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Context data
    stage_name VARCHAR(50),
    gate_status VARCHAR(50),
    sprint_id UUID REFERENCES sprints(id),
    sprint_number INTEGER,
    sprint_goal TEXT,

    -- Constraints (stored as JSONB array)
    constraints JSONB NOT NULL DEFAULT '[]',
    -- Example: [{"type": "strict_mode", "severity": "warning", "message": "..."}]

    -- Flags
    strict_mode BOOLEAN NOT NULL DEFAULT FALSE,

    -- Delivery tracking
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    trigger_type VARCHAR(30) NOT NULL,  -- pr_webhook, cli, api, scheduled
    trigger_ref VARCHAR(255),  -- PR number, CLI session, etc

    -- Delivery channels used
    delivered_to_pr BOOLEAN DEFAULT FALSE,
    delivered_to_check_run BOOLEAN DEFAULT FALSE,
    pr_comment_id BIGINT,  -- GitHub comment ID if delivered
    check_run_id BIGINT,   -- GitHub check run ID if delivered

    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_trigger_type CHECK (trigger_type IN ('pr_webhook', 'cli', 'api', 'scheduled', 'manual'))
);

-- Indexes
CREATE INDEX idx_context_overlays_project_id ON context_overlays(project_id);
CREATE INDEX idx_context_overlays_generated_at ON context_overlays(generated_at DESC);
CREATE INDEX idx_context_overlays_trigger ON context_overlays(trigger_type, trigger_ref);
CREATE INDEX idx_context_overlays_pr ON context_overlays(pr_comment_id) WHERE pr_comment_id IS NOT NULL;
```

### 3.2 Entity Relationship

```
┌───────────────────┐       ┌───────────────────┐
│    projects       │       │    sprints        │
│    ─────────      │       │    ───────        │
│    id (PK)        │◄──────│    project_id (FK)│
│    name           │       │    number         │
│    ...            │       │    goal           │
└───────────────────┘       └───────────────────┘
         │                           │
         │                           │
         ▼                           ▼
┌───────────────────┐       ┌───────────────────┐
│ agents_md_files   │       │ context_overlays  │
│ ───────────────── │       │ ─────────────────│
│ id (PK)           │       │ id (PK)          │
│ project_id (FK)   │       │ project_id (FK)  │
│ content           │       │ sprint_id (FK)   │
│ content_hash      │       │ stage_name       │
│ line_count        │       │ constraints      │
│ sections          │       │ strict_mode      │
│ generated_at      │       │ generated_at     │
│ validation_status │       │ trigger_type     │
└───────────────────┘       └───────────────────┘
```

---

## 4. API Specification

### 4.1 Endpoints

```yaml
# OpenAPI 3.0 Specification

paths:
  /api/v1/projects/{project_id}/agents-md/generate:
    post:
      summary: Generate AGENTS.md from project configuration
      tags: [AGENTS.md]
      operationId: generateAgentsMd
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: false
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AgentsMdConfig'
      responses:
        '200':
          description: AGENTS.md generated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentsMdFile'
        '400':
          description: Invalid configuration
        '404':
          description: Project not found

  /api/v1/agents-md/validate:
    post:
      summary: Validate AGENTS.md content
      tags: [AGENTS.md]
      operationId: validateAgentsMd
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                content:
                  type: string
                  description: AGENTS.md file content
              required: [content]
      responses:
        '200':
          description: Validation result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ValidationResult'

  /api/v1/projects/{project_id}/context-overlay:
    get:
      summary: Get current context overlay for project
      tags: [Context]
      operationId: getContextOverlay
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Current context overlay
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ContextOverlay'

  /api/v1/projects/{project_id}/context-overlay/pr-comment:
    get:
      summary: Get context overlay formatted as PR comment
      tags: [Context]
      operationId: getContextOverlayAsPrComment
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: PR comment markdown
          content:
            application/json:
              schema:
                type: object
                properties:
                  comment:
                    type: string
                    description: Markdown formatted PR comment

components:
  schemas:
    AgentsMdConfig:
      type: object
      properties:
        include_quick_start:
          type: boolean
          default: true
        include_architecture:
          type: boolean
          default: true
        include_conventions:
          type: boolean
          default: true
        include_security:
          type: boolean
          default: true
        include_git_workflow:
          type: boolean
          default: true
        include_do_not:
          type: boolean
          default: true
        max_lines:
          type: integer
          default: 150
          minimum: 50
          maximum: 200

    AgentsMdFile:
      type: object
      properties:
        id:
          type: string
          format: uuid
        content:
          type: string
        content_hash:
          type: string
        line_count:
          type: integer
        sections:
          type: array
          items:
            type: string
        generated_at:
          type: string
          format: date-time
        validation_status:
          type: string
          enum: [pending, valid, invalid]

    ValidationResult:
      type: object
      properties:
        valid:
          type: boolean
        errors:
          type: array
          items:
            $ref: '#/components/schemas/ValidationError'
        warnings:
          type: array
          items:
            $ref: '#/components/schemas/ValidationError'
        line_count:
          type: integer
        sections_found:
          type: array
          items:
            type: string

    ValidationError:
      type: object
      properties:
        severity:
          type: string
          enum: [error, warning]
        message:
          type: string
        line_number:
          type: integer
          nullable: true

    ContextOverlay:
      type: object
      properties:
        project_id:
          type: string
          format: uuid
        generated_at:
          type: string
          format: date-time
        stage_name:
          type: string
          nullable: true
        gate_status:
          type: string
          nullable: true
        sprint:
          $ref: '#/components/schemas/SprintContext'
        constraints:
          type: array
          items:
            $ref: '#/components/schemas/Constraint'
        strict_mode:
          type: boolean

    SprintContext:
      type: object
      properties:
        id:
          type: string
          format: uuid
          nullable: true
        number:
          type: integer
          nullable: true
        goal:
          type: string
          nullable: true
        velocity:
          type: number
          nullable: true
        days_remaining:
          type: integer
          nullable: true

    Constraint:
      type: object
      properties:
        type:
          type: string
          enum: [strict_mode, security_review, agpl, incident, custom]
        severity:
          type: string
          enum: [info, warning, error]
        message:
          type: string
        affected_files:
          type: array
          items:
            type: string
```

### 4.2 Request/Response Examples

**Generate AGENTS.md:**

```bash
POST /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/agents-md/generate
Content-Type: application/json

{
  "include_quick_start": true,
  "include_architecture": true,
  "include_conventions": true,
  "include_security": true,
  "include_git_workflow": true,
  "include_do_not": true,
  "max_lines": 150
}
```

```json
// Response 200 OK
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "content": "# AGENTS.md - SDLC Orchestrator\n\n## Quick Start\n- Full stack: `docker compose up -d`\n...",
  "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "line_count": 142,
  "sections": ["Quick Start", "Architecture", "Conventions", "Security", "Git Workflow", "DO NOT"],
  "generated_at": "2026-02-03T10:00:00Z",
  "validation_status": "valid"
}
```

**Validate AGENTS.md:**

```bash
POST /api/v1/agents-md/validate
Content-Type: application/json

{
  "content": "# AGENTS.md\n\n## Quick Start\napi_key=sk-abc123\n..."
}
```

```json
// Response 200 OK
{
  "valid": false,
  "errors": [
    {
      "severity": "error",
      "message": "Potential secret or credential detected",
      "line_number": 4
    }
  ],
  "warnings": [
    {
      "severity": "warning",
      "message": "Missing recommended section: Security"
    }
  ],
  "line_count": 45,
  "sections_found": ["Quick Start"]
}
```

**Get Context Overlay:**

```bash
GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/context-overlay
```

```json
// Response 200 OK
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "generated_at": "2026-02-03T10:00:00Z",
  "stage_name": "Stage 04 (BUILD)",
  "gate_status": "G3 PASSED",
  "sprint": {
    "id": "8f14e45f-ceea-46ed-a8a1-5b0c8f5c7e8a",
    "number": 80,
    "goal": "AGENTS.md Generator + Landing Page",
    "velocity": 32,
    "days_remaining": 8
  },
  "constraints": [
    {
      "type": "strict_mode",
      "severity": "warning",
      "message": "Post-G3: Only bug fixes allowed",
      "affected_files": []
    },
    {
      "type": "agpl",
      "severity": "info",
      "message": "AGPL: MinIO/Grafana network-only (no SDK imports)",
      "affected_files": []
    }
  ],
  "strict_mode": true
}
```

---

## 5. Service Implementation

### 5.1 AgentsMdService

```python
# backend/app/services/agents_md_service.py

from datetime import datetime
from typing import Optional
from uuid import UUID
import hashlib

from pydantic import BaseModel, Field

from app.repositories.agents_md_repository import AgentsMdRepository
from app.services.file_analyzer import FileAnalyzer
from app.services.agents_md_validator import AgentsMdValidator


class AgentsMdConfig(BaseModel):
    """Configuration for AGENTS.md generation."""
    include_quick_start: bool = True
    include_architecture: bool = True
    include_conventions: bool = True
    include_security: bool = True
    include_git_workflow: bool = True
    include_do_not: bool = True
    max_lines: int = Field(default=150, ge=50, le=200)


class AgentsMdFile(BaseModel):
    """Generated AGENTS.md file."""
    id: Optional[UUID] = None
    content: str
    content_hash: str
    line_count: int
    sections: list[str]
    generated_at: datetime
    generator_version: str = "1.0.0"
    validation_status: str = "pending"
    validation_errors: list[dict] = []
    validation_warnings: list[dict] = []


class AgentsMdService:
    """
    Generate and manage AGENTS.md files.

    Implements ADR-029 Static AGENTS.md layer:
    - Generates from project configuration analysis
    - Enforces ≤150 line limit (configurable)
    - Validates forbidden content (secrets, credentials)
    - Stores generation history for audit

    Usage:
        service = AgentsMdService(repo, file_analyzer, validator)
        agents_md = await service.generate(project_id, config)
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        repository: AgentsMdRepository,
        file_analyzer: FileAnalyzer,
        validator: AgentsMdValidator,
    ):
        self.repository = repository
        self.file_analyzer = file_analyzer
        self.validator = validator

    async def generate(
        self,
        project_id: UUID,
        config: Optional[AgentsMdConfig] = None,
        user_id: Optional[UUID] = None,
    ) -> AgentsMdFile:
        """
        Generate AGENTS.md from project configuration analysis.

        Args:
            project_id: Project UUID
            config: Generation configuration (optional)
            user_id: User generating the file (for audit)

        Returns:
            AgentsMdFile with content and metadata

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        config = config or AgentsMdConfig()
        sections = []
        section_names = []
        source_analysis = {}

        # Get project info
        project = await self.repository.get_project(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project {project_id} not found")

        # Header
        header = f"# AGENTS.md - {project.name}\n"

        # Analyze project structure
        analysis = await self.file_analyzer.analyze_project(project_id)
        source_analysis = analysis.to_dict()

        # Quick Start
        if config.include_quick_start:
            quick_start = await self._generate_quick_start(project_id, analysis)
            if quick_start:
                sections.append(quick_start)
                section_names.append("Quick Start")

        # Architecture
        if config.include_architecture:
            arch = await self._generate_architecture(project_id, analysis)
            if arch:
                sections.append(arch)
                section_names.append("Architecture")

        # Current Stage (static snapshot)
        stage = await self._generate_current_stage(project_id)
        if stage:
            sections.append(stage)
            section_names.append("Current Stage")

        # Conventions
        if config.include_conventions:
            conv = await self._generate_conventions(project_id, analysis)
            if conv:
                sections.append(conv)
                section_names.append("Conventions")

        # Security
        if config.include_security:
            sec = await self._generate_security(project_id, analysis)
            if sec:
                sections.append(sec)
                section_names.append("Security")

        # Git Workflow
        if config.include_git_workflow:
            git = await self._generate_git_workflow(project_id, analysis)
            if git:
                sections.append(git)
                section_names.append("Git Workflow")

        # DO NOT
        if config.include_do_not:
            dont = await self._generate_do_not(project_id, analysis)
            if dont:
                sections.append(dont)
                section_names.append("DO NOT")

        # Combine sections
        content = header + "\n".join(sections)

        # Enforce line limit
        line_count = content.count('\n') + 1
        if line_count > config.max_lines:
            content = self._truncate_to_limit(content, config.max_lines)
            line_count = config.max_lines

        # Calculate hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Validate
        validation = self.validator.validate(content)

        # Create result
        agents_md = AgentsMdFile(
            content=content,
            content_hash=content_hash,
            line_count=line_count,
            sections=section_names,
            generated_at=datetime.utcnow(),
            generator_version=self.VERSION,
            validation_status="valid" if validation.valid else "invalid",
            validation_errors=[e.dict() for e in validation.errors],
            validation_warnings=[w.dict() for w in validation.warnings],
        )

        # Save to database for audit
        saved = await self.repository.create(
            project_id=project_id,
            content=content,
            content_hash=content_hash,
            line_count=line_count,
            sections=section_names,
            generator_version=self.VERSION,
            source_analysis=source_analysis,
            validation_status=agents_md.validation_status,
            validation_errors=agents_md.validation_errors,
            validation_warnings=agents_md.validation_warnings,
            generated_by=user_id,
        )

        agents_md.id = saved.id
        return agents_md

    async def _generate_quick_start(
        self,
        project_id: UUID,
        analysis: "ProjectAnalysis",
    ) -> str:
        """Generate Quick Start section from project structure."""
        commands = []

        # Docker Compose
        if analysis.has_docker_compose:
            commands.append("- Full stack: `docker compose up -d`")

        # Backend
        if analysis.backend_type == "python":
            if analysis.has_poetry:
                commands.append("- Backend only: `cd backend && poetry run pytest`")
            elif analysis.has_requirements:
                commands.append("- Backend only: `cd backend && pytest`")
        elif analysis.backend_type == "node":
            commands.append("- Backend only: `cd backend && npm test`")

        # Frontend
        if analysis.frontend_type == "react":
            if analysis.frontend_path:
                commands.append(f"- Frontend only: `cd {analysis.frontend_path} && npm run dev`")

        if not commands:
            return ""

        return f"""## Quick Start
{chr(10).join(commands)}
"""

    async def _generate_architecture(
        self,
        project_id: UUID,
        analysis: "ProjectAnalysis",
    ) -> str:
        """Generate Architecture section (brief overview)."""
        layers = []

        if analysis.has_docker_compose:
            layers.append("Infrastructure: Docker Compose")
        if analysis.backend_type:
            layers.append(f"Backend: {analysis.backend_type.title()}")
        if analysis.frontend_type:
            layers.append(f"Frontend: {analysis.frontend_type.title()}")
        if analysis.has_database:
            layers.append(f"Database: {analysis.database_type or 'PostgreSQL'}")

        if not layers:
            return """## Architecture
See `/docs/02-design/` for detailed architecture documentation.
"""

        return f"""## Architecture
{chr(10).join(f"- {l}" for l in layers)}
See `/docs/02-design/` for detailed architecture documentation.
"""

    async def _generate_current_stage(self, project_id: UUID) -> str:
        """Generate Current Stage section (static snapshot note)."""
        return """## Current Stage
Check project dashboard for current SDLC stage and gate status.
Dynamic context is delivered via PR comments (not in this file).
"""

    async def _generate_conventions(
        self,
        project_id: UUID,
        analysis: "ProjectAnalysis",
    ) -> str:
        """Generate Conventions section from config files."""
        conventions = []

        # Python conventions
        if analysis.backend_type == "python":
            if analysis.has_ruff:
                conventions.append("- Python: ruff + mypy strict mode")
            elif analysis.has_flake8:
                conventions.append("- Python: flake8 + mypy")
            else:
                conventions.append("- Python: See pyproject.toml for linting config")

        # TypeScript conventions
        if analysis.has_tsconfig:
            conventions.append("- TypeScript: strict mode enabled")

        # Naming conventions (default SDLC 6.1.0)
        conventions.append("- Files: snake_case (Python ≤50 chars), camelCase/PascalCase (TypeScript)")
        conventions.append("- Tests: 95%+ coverage required")

        return f"""## Conventions
{chr(10).join(conventions)}
"""

    async def _generate_security(
        self,
        project_id: UUID,
        analysis: "ProjectAnalysis",
    ) -> str:
        """Generate Security section."""
        rules = [
            "- OWASP ASVS L2 compliance required",
            "- No hardcoded secrets (use environment variables)",
            "- Input validation on all API endpoints",
            "- SQL injection prevention via ORM",
        ]

        # AGPL containment if using MinIO/Grafana
        if analysis.has_minio or analysis.has_grafana:
            rules.append("- AGPL: MinIO/Grafana network-only (NO SDK imports)")

        return f"""## Security
{chr(10).join(rules)}
"""

    async def _generate_git_workflow(
        self,
        project_id: UUID,
        analysis: "ProjectAnalysis",
    ) -> str:
        """Generate Git Workflow section."""
        return """## Git Workflow
- Branch: `feature/{ticket}-{description}`
- Commit: `feat|fix|chore(scope): message`
- PR: Must pass quality gates before merge
"""

    async def _generate_do_not(
        self,
        project_id: UUID,
        analysis: "ProjectAnalysis",
    ) -> str:
        """Generate DO NOT section."""
        rules = [
            "- Add mocks or placeholders (Zero Mock Policy)",
            "- Skip tests for 'quick fixes'",
            "- Hardcode secrets or credentials",
            "- Use `// TODO` without ticket reference",
        ]

        # AGPL containment
        if analysis.has_minio or analysis.has_grafana:
            rules.append("- Import AGPL libraries (MinIO SDK, Grafana SDK)")

        return f"""## DO NOT
{chr(10).join(rules)}
"""

    def _truncate_to_limit(self, content: str, max_lines: int) -> str:
        """Truncate content to max lines while preserving structure."""
        lines = content.split('\n')
        if len(lines) <= max_lines:
            return content

        # Keep content and add truncation notice
        truncated = lines[:max_lines - 2]
        truncated.append("")
        truncated.append("<!-- Truncated to fit AI context window. See docs for full details. -->")
        return '\n'.join(truncated)
```

### 5.2 AgentsMdValidator

```python
# backend/app/services/agents_md_validator.py

import re
from typing import List, Optional
from pydantic import BaseModel


class ValidationError(BaseModel):
    """Validation error or warning."""
    severity: str  # "error" or "warning"
    message: str
    line_number: Optional[int] = None


class ValidationResult(BaseModel):
    """Validation result."""
    valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    line_count: int
    sections_found: List[str]


class AgentsMdValidator:
    """
    Validate AGENTS.md structure and content.

    Implements ADR-029 validation requirements:
    - Line limit enforcement (≤150 recommended, ≤200 max)
    - Forbidden content detection (secrets, credentials)
    - Required section recommendations
    - Markdown structure validation

    Usage:
        validator = AgentsMdValidator()
        result = validator.validate(content)
        if not result.valid:
            print(f"Errors: {result.errors}")
    """

    # Patterns for forbidden content (secrets)
    SECRET_PATTERNS = [
        # API keys with values
        r'(?i)api[_-]?key\s*[=:]\s*["\'][^"\']{8,}["\']',
        r'(?i)password\s*[=:]\s*["\'][^"\']+["\']',
        r'(?i)secret\s*[=:]\s*["\'][^"\']+["\']',
        r'(?i)token\s*[=:]\s*["\'][^"\']{20,}["\']',

        # Known API key formats
        r'sk-[a-zA-Z0-9]{20,}',  # OpenAI
        r'ghp_[a-zA-Z0-9]{36}',  # GitHub PAT
        r'gho_[a-zA-Z0-9]{36}',  # GitHub OAuth
        r'AKIA[A-Z0-9]{16}',     # AWS Access Key
        r'aws_secret_access_key\s*=\s*["\'][A-Za-z0-9/+=]{40}["\']',  # AWS Secret

        # Private keys
        r'-----BEGIN.*PRIVATE KEY-----',
        r'-----BEGIN RSA PRIVATE KEY-----',

        # Connection strings with passwords
        r'(?i)://[^:]+:[^@]{8,}@',  # user:password@host
    ]

    RECOMMENDED_SECTIONS = [
        "Quick Start",
        "Architecture",
        "Conventions",
        "Security",
        "DO NOT",
    ]

    OPTIONAL_SECTIONS = [
        "Git Workflow",
        "Current Stage",
        "Testing",
    ]

    MAX_RECOMMENDED_LINES = 150
    MAX_ALLOWED_LINES = 200

    def validate(self, content: str) -> ValidationResult:
        """
        Validate AGENTS.md content.

        Args:
            content: AGENTS.md file content

        Returns:
            ValidationResult with errors and warnings
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []
        lines = content.split('\n')
        line_count = len(lines)

        # Check line limits
        if line_count > self.MAX_ALLOWED_LINES:
            errors.append(ValidationError(
                severity="error",
                message=f"File exceeds maximum {self.MAX_ALLOWED_LINES} lines ({line_count} lines)",
            ))
        elif line_count > self.MAX_RECOMMENDED_LINES:
            warnings.append(ValidationError(
                severity="warning",
                message=f"File exceeds recommended {self.MAX_RECOMMENDED_LINES} lines ({line_count} lines). Consider trimming.",
            ))

        # Check for forbidden content (secrets)
        secret_errors = self._check_secrets(lines)
        errors.extend(secret_errors)

        # Check for required sections
        sections_found = self._find_sections(content)
        for section in self.RECOMMENDED_SECTIONS:
            if section not in sections_found:
                warnings.append(ValidationError(
                    severity="warning",
                    message=f"Missing recommended section: {section}",
                ))

        # Check markdown structure
        structure_errors = self._validate_structure(content, lines)
        errors.extend(structure_errors)

        # Check for executable code blocks (potential risk)
        code_warnings = self._check_code_blocks(lines)
        warnings.extend(code_warnings)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            line_count=line_count,
            sections_found=sections_found,
        )

    def _check_secrets(self, lines: List[str]) -> List[ValidationError]:
        """Check for potential secrets in content."""
        errors = []

        for i, line in enumerate(lines, 1):
            for pattern in self.SECRET_PATTERNS:
                if re.search(pattern, line):
                    # Skip if it's a pattern example (starts with #)
                    if line.strip().startswith('#') or '`' in line:
                        continue

                    errors.append(ValidationError(
                        severity="error",
                        message="Potential secret or credential detected. Remove before committing.",
                        line_number=i,
                    ))
                    break  # One error per line is enough

        return errors

    def _find_sections(self, content: str) -> List[str]:
        """Find all ## or # sections in content."""
        sections = []
        for match in re.finditer(r'^##?\s+(.+)$', content, re.MULTILINE):
            section_name = match.group(1).strip()
            # Clean up section name (remove emoji, etc)
            section_name = re.sub(r'^[^\w\s]+\s*', '', section_name)
            sections.append(section_name)
        return sections

    def _validate_structure(
        self,
        content: str,
        lines: List[str],
    ) -> List[ValidationError]:
        """Validate markdown structure."""
        errors = []

        # Check for title
        if not content.strip().startswith('#'):
            errors.append(ValidationError(
                severity="error",
                message="AGENTS.md must start with a title (# heading)",
                line_number=1,
            ))

        # Check for AGENTS.md in title
        first_line = lines[0] if lines else ""
        if "AGENTS" not in first_line.upper():
            errors.append(ValidationError(
                severity="error",
                message="Title should include 'AGENTS.md'",
                line_number=1,
            ))

        return errors

    def _check_code_blocks(self, lines: List[str]) -> List[ValidationError]:
        """Check for potentially risky code blocks."""
        warnings = []
        in_code_block = False
        code_block_start = 0

        for i, line in enumerate(lines, 1):
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_block_start = i

                    # Check for executable languages
                    lang = line.strip()[3:].lower()
                    if lang in ['bash', 'sh', 'shell', 'cmd', 'powershell']:
                        # Only warn if it looks like it could modify system
                        pass  # Normal for setup commands
                else:
                    in_code_block = False

        return warnings

    def lint(self, content: str) -> tuple[str, List[str]]:
        """
        Lint and auto-fix AGENTS.md content.

        Args:
            content: AGENTS.md content

        Returns:
            Tuple of (fixed_content, list of fixes applied)
        """
        fixes = []
        lines = content.split('\n')

        # Fix trailing whitespace
        for i, line in enumerate(lines):
            if line.rstrip() != line:
                lines[i] = line.rstrip()
                fixes.append(f"Trimmed trailing whitespace (line {i+1})")

        # Ensure single newline at end
        while lines and lines[-1] == '':
            lines.pop()
            fixes.append("Removed extra blank line at end")
        lines.append('')  # Single newline at end

        # Ensure blank line between sections
        for i in range(1, len(lines)):
            if lines[i].startswith('#') and lines[i-1].strip() != '':
                lines.insert(i, '')
                fixes.append(f"Added blank line before heading (line {i+1})")

        return '\n'.join(lines), fixes
```

### 5.3 ContextOverlayService

```python
# backend/app/services/context_overlay_service.py

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.repositories.context_overlay_repository import ContextOverlayRepository
from app.services.gate_service import GateService
from app.services.sprint_service import SprintService
from app.services.security_service import SecurityService


class SprintContext(BaseModel):
    """Sprint context for overlay."""
    id: Optional[UUID] = None
    number: Optional[int] = None
    goal: Optional[str] = None
    velocity: Optional[float] = None
    days_remaining: Optional[int] = None


class Constraint(BaseModel):
    """Active constraint affecting development."""
    type: str  # strict_mode, security_review, agpl, incident, custom
    severity: str  # info, warning, error
    message: str
    affected_files: List[str] = []


class ContextOverlay(BaseModel):
    """
    Dynamic context overlay (NOT committed to git).

    Delivered via:
    - PR comments
    - CLI output
    - VS Code panel
    - API response
    """
    id: Optional[UUID] = None
    project_id: UUID
    generated_at: datetime
    stage_name: Optional[str] = None
    gate_status: Optional[str] = None
    sprint: Optional[SprintContext] = None
    constraints: List[Constraint] = []
    strict_mode: bool = False


class ContextOverlayService:
    """
    Generate dynamic context overlays for AI coding tools.

    Implements ADR-029 Dynamic Overlay layer:
    - NOT committed to git (delivered at runtime)
    - Contains current SDLC stage, sprint, and constraints
    - Formatted for PR comments, CLI, VS Code, API

    Sources:
    - GateService: Current stage and gate status
    - SprintService: Active sprint context
    - SecurityService: Security-related constraints
    - IncidentService: Active incident constraints
    """

    def __init__(
        self,
        repository: ContextOverlayRepository,
        gate_service: GateService,
        sprint_service: SprintService,
        security_service: SecurityService,
    ):
        self.repository = repository
        self.gate_service = gate_service
        self.sprint_service = sprint_service
        self.security_service = security_service

    async def get_overlay(
        self,
        project_id: UUID,
        trigger_type: str = "api",
        trigger_ref: Optional[str] = None,
    ) -> ContextOverlay:
        """
        Generate context overlay for project.

        Args:
            project_id: Project UUID
            trigger_type: What triggered the overlay (pr_webhook, cli, api, scheduled)
            trigger_ref: Reference for trigger (PR number, CLI session ID)

        Returns:
            ContextOverlay with current project context
        """
        constraints: List[Constraint] = []

        # Get current stage and gate
        stage = await self.gate_service.get_current_stage(project_id)
        gate_status = await self.gate_service.get_latest_gate_status(project_id)

        # Determine strict mode (post-G3)
        strict_mode = False
        if gate_status:
            gate_name = gate_status.get("gate_name", "")
            gate_passed = gate_status.get("passed", False)

            if "G3" in gate_name and gate_passed:
                strict_mode = True
                constraints.append(Constraint(
                    type="strict_mode",
                    severity="warning",
                    message="Post-G3: Only bug fixes allowed. Feature work blocked.",
                ))

        # Get active sprint
        sprint = await self.sprint_service.get_active_sprint(project_id)
        sprint_context = None
        if sprint:
            sprint_context = SprintContext(
                id=sprint.id,
                number=sprint.number,
                goal=sprint.goal,
                velocity=sprint.velocity,
                days_remaining=self._calculate_days_remaining(sprint),
            )

        # Get security constraints
        security_issues = await self.security_service.get_active_issues(project_id)
        for issue in security_issues:
            constraints.append(Constraint(
                type="security_review",
                severity="error" if issue.severity == "critical" else "warning",
                message=f"Security: {issue.title}",
                affected_files=issue.affected_files or [],
            ))

        # AGPL containment (always active for projects with MinIO/Grafana)
        project_config = await self.repository.get_project_config(project_id)
        if project_config.get("has_agpl_deps", False):
            constraints.append(Constraint(
                type="agpl",
                severity="info",
                message="AGPL: MinIO/Grafana network-only access (no SDK imports)",
            ))

        # Build overlay
        overlay = ContextOverlay(
            project_id=project_id,
            generated_at=datetime.utcnow(),
            stage_name=stage.name if stage else None,
            gate_status=gate_status.get("gate_name") if gate_status else None,
            sprint=sprint_context,
            constraints=constraints,
            strict_mode=strict_mode,
        )

        # Save for audit
        saved = await self.repository.create(
            project_id=project_id,
            stage_name=overlay.stage_name,
            gate_status=overlay.gate_status,
            sprint_id=sprint_context.id if sprint_context else None,
            sprint_number=sprint_context.number if sprint_context else None,
            sprint_goal=sprint_context.goal if sprint_context else None,
            constraints=[c.dict() for c in constraints],
            strict_mode=strict_mode,
            trigger_type=trigger_type,
            trigger_ref=trigger_ref,
        )

        overlay.id = saved.id
        return overlay

    def format_pr_comment(self, overlay: ContextOverlay) -> str:
        """
        Format overlay as PR comment for AI tools.

        Uses structured HTML comments for parsing by automation.
        Visible to Cursor, Copilot, Claude Code via PR conversation.
        """
        timestamp = overlay.generated_at.strftime('%b %d, %Y %H:%M UTC')

        # Stage and sprint info
        stage_text = overlay.stage_name or "Unknown"
        gate_text = overlay.gate_status or "N/A"

        sprint_text = "N/A"
        if overlay.sprint:
            sprint_text = f"Sprint {overlay.sprint.number}"
            if overlay.sprint.goal:
                sprint_text += f" - {overlay.sprint.goal}"
            if overlay.sprint.days_remaining is not None:
                sprint_text += f" ({overlay.sprint.days_remaining} days left)"

        # Constraints
        constraints_text = ""
        if overlay.constraints:
            for c in overlay.constraints:
                icon = {"info": "ℹ️", "warning": "⚠️", "error": "🔴"}.get(c.severity, "•")
                constraints_text += f"- {icon} **{c.type.replace('_', ' ').title()}**: {c.message}\n"
                if c.affected_files:
                    for f in c.affected_files[:3]:  # Limit to 3 files
                        constraints_text += f"  - `{f}`\n"
                    if len(c.affected_files) > 3:
                        constraints_text += f"  - ... and {len(c.affected_files) - 3} more\n"
        else:
            constraints_text = "- None\n"

        # Strict mode banner
        strict_banner = ""
        if overlay.strict_mode:
            strict_banner = "\n> 🔒 **STRICT MODE ACTIVE**: Only bug fixes allowed.\n"

        return f"""<!-- SDLC-CONTEXT-START -->
## 🎯 SDLC Context ({timestamp})
{strict_banner}
| Stage | Gate | Sprint |
|-------|------|--------|
| {stage_text} | {gate_text} | {sprint_text} |

### Active Constraints
{constraints_text}
---
*Generated by [SDLC Orchestrator](https://sdlc.dev) • [View Dashboard](#)*
<!-- SDLC-CONTEXT-END -->"""

    def format_cli_output(self, overlay: ContextOverlay) -> str:
        """Format overlay for CLI terminal output."""
        lines = [
            "",
            "┌─────────────────────────────────────────────────────────┐",
            "│                   SDLC CONTEXT                          │",
            "├─────────────────────────────────────────────────────────┤",
        ]

        # Stage
        stage = overlay.stage_name or "Unknown"
        lines.append(f"│  📍 Stage: {stage:<45} │")

        # Gate
        gate = overlay.gate_status or "N/A"
        lines.append(f"│  🚪 Gate:  {gate:<45} │")

        # Strict mode
        if overlay.strict_mode:
            lines.append("│  🔒 MODE:  STRICT (bug fixes only)                     │")

        # Sprint
        if overlay.sprint:
            sprint_info = f"Sprint {overlay.sprint.number}"
            if overlay.sprint.days_remaining is not None:
                sprint_info += f" ({overlay.sprint.days_remaining}d left)"
            lines.append(f"│  📅 Sprint: {sprint_info:<43} │")

        lines.append("├─────────────────────────────────────────────────────────┤")
        lines.append("│  📋 Constraints:                                         │")

        # Constraints
        if overlay.constraints:
            for c in overlay.constraints:
                icon = {"info": "ℹ️", "warning": "⚠️", "error": "🔴"}.get(c.severity, "•")
                msg = c.message[:47] + "..." if len(c.message) > 50 else c.message
                lines.append(f"│    {icon} {msg:<51} │")
        else:
            lines.append("│    None                                                 │")

        lines.append("└─────────────────────────────────────────────────────────┘")
        lines.append("")

        return "\n".join(lines)

    def format_check_run_output(self, overlay: ContextOverlay) -> str:
        """Format overlay for GitHub Check Run output."""
        return self.format_pr_comment(overlay)

    def format_json(self, overlay: ContextOverlay) -> dict:
        """Format overlay as JSON for API/VS Code."""
        return overlay.dict()

    def _calculate_days_remaining(self, sprint) -> Optional[int]:
        """Calculate days remaining in sprint."""
        if not sprint.end_date:
            return None

        delta = sprint.end_date - datetime.now().date()
        return max(0, delta.days)
```

---

## 6. CLI Implementation

### 6.1 Implementation Overview

**Location**: `backend/sdlcctl/commands/agents.py`
**Framework**: Typer + Rich (consistent with existing sdlcctl commands)
**Status**: ✅ IMPLEMENTED (Jan 19, 2026)

The CLI integrates into the existing `sdlcctl` command-line tool, maintaining consistency with other commands like `validate`, `init`, `magic`.

### 6.2 CLI Commands

```python
# backend/sdlcctl/commands/agents.py (IMPLEMENTED - 600+ lines)

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from pathlib import Path
from typing import Optional

console = Console()

# ============================================================================
# Command: sdlcctl agents init
# ============================================================================

def agents_init_command(
    path: Path = typer.Option(
        Path.cwd(),
        "--path", "-p",
        help="Project root path",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output file path (default: AGENTS.md in project root)",
    ),
    max_lines: int = typer.Option(
        150,
        "--max-lines", "-m",
        help="Maximum lines (50-200)",
        min=50, max=200,
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Overwrite existing AGENTS.md",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print content without writing file",
    ),
) -> None:
    """
    Generate AGENTS.md from project analysis.

    Analyzes project structure (docker-compose, package.json, etc.)
    and generates a compliant AGENTS.md file.
    """
    # 1. Analyze project structure
    analysis = analyze_project(path)

    # 2. Display analysis summary (Rich Table)
    table = Table(title="Project Analysis")
    table.add_row("Backend", analysis["backend_type"] or "Not detected")
    table.add_row("Frontend", analysis["frontend_type"] or "Not detected")
    table.add_row("AGPL Deps", "⚠️ Yes" if analysis["has_minio"] else "No")
    console.print(table)

    # 3. Generate AGENTS.md content
    content = generate_agents_md(analysis, max_lines)

    # 4. Validate for secrets
    secrets = detect_secrets(content)
    if secrets:
        console.print("[red]ERROR: Secrets detected![/red]")
        raise typer.Exit(code=1)

    # 5. Write or display
    if dry_run:
        console.print(Syntax(content, "markdown"))
    else:
        output_path.write_text(content)
        console.print(f"[green]✓ Generated AGENTS.md[/green]")


# ============================================================================
# Command: sdlcctl agents validate
# ============================================================================

def agents_validate_command(
    path: Path = typer.Argument(..., help="Path to AGENTS.md file"),
    strict: bool = typer.Option(False, "--strict", "-s", help="Treat warnings as errors"),
) -> None:
    """
    Validate AGENTS.md content.

    Checks for:
    - Secrets (API keys, tokens, passwords)
    - Line limits (150 recommended, 200 max)
    - Required sections
    - Markdown structure
    """
    content = path.read_text()

    # Run validations
    secrets = detect_secrets(content)
    structure = validate_structure(content)

    errors = [i for i in secrets + structure if i["type"] == "error"]
    warnings = [i for i in secrets + structure if i["type"] == "warning"]

    # Display results
    console.print(f"[bold]Summary:[/bold]")
    console.print(f"  📊 Lines: {count_lines(content)}/150")
    console.print(f"  ❌ Errors: {len(errors)}")
    console.print(f"  ⚠️  Warnings: {len(warnings)}")

    if errors or (strict and warnings):
        raise typer.Exit(code=1)


# ============================================================================
# Command: sdlcctl agents lint
# ============================================================================

def agents_lint_command(
    path: Path = typer.Argument(..., help="Path to AGENTS.md file"),
    fix: bool = typer.Option(False, "--fix", "-f", help="Apply fixes to file"),
) -> None:
    """
    Lint and auto-fix AGENTS.md.

    Fixes:
    - Trailing whitespace
    - Multiple blank lines
    - Missing newline at end
    """
    content = path.read_text()
    fixed_content, changes = lint_content(content)

    if not changes:
        console.print("[green]✓ No issues found[/green]")
        return

    console.print(f"[bold]Found {len(changes)} issue(s):[/bold]")
    for change in changes:
        console.print(f"  🔧 {change}")

    if fix:
        path.write_text(fixed_content)
        console.print(f"[green]✓ Fixed {len(changes)} issue(s)[/green]")


# ============================================================================
# Secret Detection Patterns
# ============================================================================

SECRET_PATTERNS = [
    (r'sk-[a-zA-Z0-9]{20,}', "OpenAI API key"),
    (r'ghp_[a-zA-Z0-9]{36}', "GitHub PAT"),
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
    (r'sk_live_[a-zA-Z0-9]{24,}', "Stripe Live Key"),
    (r'xox[baprs]-[0-9a-zA-Z-]{10,}', "Slack Token"),
    (r'sk-ant-api[a-zA-Z0-9-]{20,}', "Anthropic API Key"),
    (r'://[^:]+:[^@]+@', "URL with credentials"),
    (r'eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.', "JWT Token"),
]
```

### 6.3 CLI Registration in sdlcctl

```python
# backend/sdlcctl/cli.py (UPDATED)

from .commands.agents import (
    agents_init_command,
    agents_validate_command,
    agents_lint_command,
)

# Create agents sub-app
agents_app = typer.Typer(name="agents", help="AGENTS.md management commands")

agents_app.command(name="init")(agents_init_command)
agents_app.command(name="validate")(agents_validate_command)
agents_app.command(name="lint")(agents_lint_command)

# Register agents sub-app
app.add_typer(agents_app, name="agents")
```

### 6.4 CLI Help Output

```
$ sdlcctl agents --help

 Usage: sdlcctl agents [OPTIONS] COMMAND [ARGS]...

 AGENTS.md management commands.

╭─ Commands ──────────────────────────────────────────────────────╮
│ init      Generate AGENTS.md from project analysis              │
│ validate  Validate AGENTS.md content                            │
│ lint      Lint and auto-fix AGENTS.md                           │
╰─────────────────────────────────────────────────────────────────╯


$ sdlcctl agents init --help

 Usage: sdlcctl agents init [OPTIONS]

 Generate AGENTS.md from project analysis.

╭─ Options ───────────────────────────────────────────────────────╮
│ --path        -p  PATH     Project root path [default: .]       │
│ --output      -o  PATH     Output file path                     │
│ --max-lines   -m  INTEGER  Maximum lines (50-200) [default:150] │
│ --force       -f           Overwrite existing AGENTS.md         │
│ --dry-run                  Print content without writing file   │
│ --help                     Show this message and exit.          │
╰─────────────────────────────────────────────────────────────────╯


$ sdlcctl agents validate --help

 Usage: sdlcctl agents validate [OPTIONS] PATH

 Validate AGENTS.md content.

╭─ Arguments ─────────────────────────────────────────────────────╮
│ *  PATH  Path to AGENTS.md file [required]                      │
╰─────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────╮
│ --strict  -s  Treat warnings as errors                          │
│ --help        Show this message and exit.                       │
╰─────────────────────────────────────────────────────────────────╯


$ sdlcctl agents lint --help

 Usage: sdlcctl agents lint [OPTIONS] PATH

 Lint and auto-fix AGENTS.md.

╭─ Arguments ─────────────────────────────────────────────────────╮
│ *  PATH  Path to AGENTS.md file [required]                      │
╰─────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────╮
│ --fix   -f  Apply fixes to file                                 │
│ --help      Show this message and exit.                         │
╰─────────────────────────────────────────────────────────────────╯
```

### 6.5 CLI Example Workflows

```bash
# 1. Generate AGENTS.md for current project
$ sdlcctl agents init
┌─────────────────────────────────────────────┐
│         AGENTS.md Generator                 │
│                                             │
│ Generates AGENTS.md from project analysis.  │
│ Follows ADR-029 two-layer architecture.     │
└─────────────────────────────────────────────┘

        Project Analysis
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Property    ┃ Value           ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ Project     │ my-project      │
│ Backend     │ Python          │
│ Frontend    │ React           │
│ Database    │ PostgreSQL      │
│ Docker      │ ✅              │
│ AGPL Deps   │ ⚠️ Yes (MinIO)   │
└─────────────┴─────────────────┘

✓ Generated AGENTS.md
  Path: /path/to/AGENTS.md
  Lines: 142/150

Next steps:
  1. Review and customize the generated content
  2. Run 'sdlcctl agents validate' to check compliance
  3. Commit AGENTS.md to your repository


# 2. Validate existing AGENTS.md
$ sdlcctl agents validate AGENTS.md
Validating: AGENTS.md

Summary:
  📊 Lines: 142/150 (max 200)
  ❌ Errors: 0
  ⚠️  Warnings: 1

Warnings:
  Line 1: Recommended section 'Git Workflow' not found

✓ Validation PASSED with warnings


# 3. Validate with secrets (FAIL)
$ sdlcctl agents validate AGENTS.md
Validating: AGENTS.md

Errors:
  Line 15: OpenAI API key detected

Summary:
  📊 Lines: 145/150
  ❌ Errors: 1
  ⚠️  Warnings: 0

✗ Validation FAILED


# 4. Lint and fix
$ sdlcctl agents lint AGENTS.md --fix
Linting: AGENTS.md

Found 2 issue(s):
  🔧 Line 45: Removed trailing whitespace
  🔧 Added newline at end of file

✓ Fixed 2 issue(s)

Running validation...
✓ File is now valid
```

---

## 7. Integration Points

### 7.1 GitHub PR Webhook Integration

```python
# backend/app/webhooks/github_pr_handler.py

from uuid import UUID
from app.services.context_overlay_service import ContextOverlayService
from app.services.github_service import GitHubService


class GitHubPRHandler:
    """Handle GitHub PR webhooks for context overlay injection."""

    def __init__(
        self,
        overlay_service: ContextOverlayService,
        github_service: GitHubService,
    ):
        self.overlay_service = overlay_service
        self.github_service = github_service

    async def handle_pr_opened(
        self,
        project_id: UUID,
        pr_number: int,
        repo_owner: str,
        repo_name: str,
    ):
        """
        Handle PR opened event - post context overlay comment.

        Flow:
        1. Generate context overlay
        2. Format as PR comment
        3. Post to GitHub PR
        4. Update overlay record with comment ID
        """
        # Generate overlay
        overlay = await self.overlay_service.get_overlay(
            project_id=project_id,
            trigger_type="pr_webhook",
            trigger_ref=f"PR#{pr_number}",
        )

        # Format as PR comment
        comment_body = self.overlay_service.format_pr_comment(overlay)

        # Post to GitHub
        comment_id = await self.github_service.create_pr_comment(
            owner=repo_owner,
            repo=repo_name,
            pr_number=pr_number,
            body=comment_body,
        )

        # Update overlay record
        await self.overlay_service.repository.update_delivery(
            overlay_id=overlay.id,
            delivered_to_pr=True,
            pr_comment_id=comment_id,
        )

        return overlay

    async def handle_pr_updated(
        self,
        project_id: UUID,
        pr_number: int,
        repo_owner: str,
        repo_name: str,
        existing_comment_id: int,
    ):
        """Update existing context overlay comment on PR."""
        # Generate fresh overlay
        overlay = await self.overlay_service.get_overlay(
            project_id=project_id,
            trigger_type="pr_webhook",
            trigger_ref=f"PR#{pr_number}",
        )

        # Format as PR comment
        comment_body = self.overlay_service.format_pr_comment(overlay)

        # Update existing comment
        await self.github_service.update_pr_comment(
            owner=repo_owner,
            repo=repo_name,
            comment_id=existing_comment_id,
            body=comment_body,
        )

        return overlay
```

### 7.2 GitHub Check Run Integration (Sprint 79)

```python
# Integration with github_checks_service.py from Sprint 79

async def inject_overlay_to_check_run(
    project_id: UUID,
    check_run_id: int,
    github_checks_service: GitHubChecksService,
    overlay_service: ContextOverlayService,
):
    """Inject context overlay into GitHub Check Run output."""

    # Get overlay
    overlay = await overlay_service.get_overlay(project_id)

    # Format for check run
    overlay_text = overlay_service.format_check_run_output(overlay)

    # Include in check run summary
    # (This integrates with the format_context_overlay method in GitHubChecksService)
    return overlay_text
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
# tests/unit/services/test_agents_md_service.py

import pytest
from uuid import uuid4

from app.services.agents_md_service import AgentsMdService, AgentsMdConfig
from app.services.agents_md_validator import AgentsMdValidator


class TestAgentsMdService:
    """Unit tests for AgentsMdService."""

    @pytest.fixture
    def service(self, mock_repository, mock_file_analyzer, mock_validator):
        return AgentsMdService(
            repository=mock_repository,
            file_analyzer=mock_file_analyzer,
            validator=mock_validator,
        )

    async def test_generate_basic(self, service):
        """Test basic AGENTS.md generation."""
        project_id = uuid4()
        result = await service.generate(project_id)

        assert result.content.startswith("# AGENTS.md")
        assert result.line_count <= 150
        assert "Quick Start" in result.sections

    async def test_generate_respects_line_limit(self, service):
        """Test that generation respects max_lines config."""
        project_id = uuid4()
        config = AgentsMdConfig(max_lines=50)
        result = await service.generate(project_id, config)

        assert result.line_count <= 50

    async def test_generate_excludes_sections(self, service):
        """Test that sections can be excluded."""
        project_id = uuid4()
        config = AgentsMdConfig(
            include_quick_start=False,
            include_security=False,
        )
        result = await service.generate(project_id, config)

        assert "Quick Start" not in result.sections
        assert "Security" not in result.sections


class TestAgentsMdValidator:
    """Unit tests for AgentsMdValidator."""

    @pytest.fixture
    def validator(self):
        return AgentsMdValidator()

    def test_validate_valid_content(self, validator):
        """Test validation of valid AGENTS.md."""
        content = """# AGENTS.md - Test Project

## Quick Start
- `docker compose up`

## Architecture
Simple layered architecture.

## Conventions
- Python: snake_case
- TypeScript: camelCase

## Security
- No hardcoded secrets

## DO NOT
- Add mocks
"""
        result = validator.validate(content)

        assert result.valid is True
        assert len(result.errors) == 0
        assert result.line_count < 150

    def test_validate_detects_secrets(self, validator):
        """Test that secrets are detected."""
        content = """# AGENTS.md

## Config
api_key = "sk-abc123def456"
"""
        result = validator.validate(content)

        assert result.valid is False
        assert any("secret" in e.message.lower() for e in result.errors)

    def test_validate_warns_missing_sections(self, validator):
        """Test warning for missing recommended sections."""
        content = """# AGENTS.md

## Quick Start
- Run it
"""
        result = validator.validate(content)

        # Should have warnings for missing sections
        assert any("Architecture" in w.message for w in result.warnings)

    def test_validate_warns_long_file(self, validator):
        """Test warning for files over 150 lines."""
        content = "# AGENTS.md\n\n" + "\n".join([f"Line {i}" for i in range(160)])
        result = validator.validate(content)

        assert any("150 lines" in w.message for w in result.warnings)
```

### 8.2 Integration Tests

```python
# tests/integration/test_agents_md_api.py

import pytest
from httpx import AsyncClient


class TestAgentsMdAPI:
    """Integration tests for AGENTS.md API endpoints."""

    @pytest.mark.asyncio
    async def test_generate_agents_md(self, client: AsyncClient, test_project):
        """Test AGENTS.md generation endpoint."""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/agents-md/generate",
            json={
                "include_quick_start": True,
                "include_architecture": True,
                "max_lines": 150,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "content" in data
        assert data["content"].startswith("# AGENTS.md")
        assert data["line_count"] <= 150
        assert data["validation_status"] == "valid"

    @pytest.mark.asyncio
    async def test_validate_agents_md(self, client: AsyncClient):
        """Test AGENTS.md validation endpoint."""
        content = """# AGENTS.md - Test

## Quick Start
- Run it

## Conventions
- Be good
"""
        response = await client.post(
            "/api/v1/agents-md/validate",
            json={"content": content},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert "Quick Start" in data["sections_found"]

    @pytest.mark.asyncio
    async def test_get_context_overlay(self, client: AsyncClient, test_project):
        """Test context overlay retrieval."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/context-overlay",
        )

        assert response.status_code == 200
        data = response.json()

        assert "project_id" in data
        assert "constraints" in data
        assert "generated_at" in data

    @pytest.mark.asyncio
    async def test_get_context_overlay_pr_comment(self, client: AsyncClient, test_project):
        """Test context overlay as PR comment format."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/context-overlay/pr-comment",
        )

        assert response.status_code == 200
        data = response.json()

        assert "comment" in data
        assert "SDLC-CONTEXT-START" in data["comment"]
        assert "SDLC-CONTEXT-END" in data["comment"]
```

### 8.3 E2E Tests

```python
# tests/e2e/test_agents_md_flow.py

import pytest
from pathlib import Path


class TestAgentsMdE2EFlow:
    """E2E tests for complete AGENTS.md workflow."""

    @pytest.mark.e2e
    async def test_full_generate_validate_flow(self, cli_runner, test_project):
        """Test complete flow: generate → validate → commit."""
        project_id = str(test_project.id)

        # Step 1: Generate
        result = cli_runner.invoke(
            ["agents", "init", "-p", project_id, "-o", "AGENTS.md"]
        )
        assert result.exit_code == 0
        assert "Generated AGENTS.md" in result.output

        # Step 2: Verify file exists
        assert Path("AGENTS.md").exists()
        content = Path("AGENTS.md").read_text()
        assert content.startswith("# AGENTS.md")

        # Step 3: Validate
        result = cli_runner.invoke(["agents", "validate", "-f", "AGENTS.md"])
        assert result.exit_code == 0
        assert "is valid" in result.output

        # Step 4: Lint
        result = cli_runner.invoke(["agents", "lint", "-f", "AGENTS.md"])
        assert result.exit_code == 0

    @pytest.mark.e2e
    async def test_context_overlay_pr_flow(self, test_project, mock_github):
        """Test context overlay injection into PR."""
        # Simulate PR webhook
        # ...
        pass
```

---

## 9. Security Considerations

### 9.1 Secret Detection

The validator includes patterns for detecting common secrets:

| Pattern Type | Examples |
|-------------|----------|
| API Keys | `api_key = "sk-..."`, `API_KEY: "..."` |
| Tokens | `ghp_...`, `gho_...`, `sk-...` |
| AWS | `AKIA...`, `aws_secret_access_key` |
| Private Keys | `-----BEGIN PRIVATE KEY-----` |
| Passwords | `password = "..."`, `pwd: "..."` |
| Connection Strings | `://user:password@host` |

### 9.2 Input Validation

All inputs are validated:

- **project_id**: Must be valid UUID
- **content**: Max 500KB to prevent abuse
- **max_lines**: Range 50-200
- **config options**: Boolean only

### 9.3 AGPL Containment

The system ensures AGPL containment is always included in DO NOT section when MinIO/Grafana are detected in project configuration.

---

## 10. Performance Requirements

| Operation | Target p95 | Measurement |
|-----------|------------|-------------|
| Generate AGENTS.md | <2s | API response time |
| Validate AGENTS.md | <500ms | API response time |
| Get Context Overlay | <500ms | API response time |
| CLI `init` | <3s | End-to-end |
| CLI `validate` | <1s | End-to-end |

### 10.1 Optimization Strategies

1. **Caching**: Cache project analysis for 5 minutes
2. **Parallel section generation**: Generate sections concurrently
3. **Lazy loading**: Only load sections enabled in config
4. **Database indexes**: Optimized for project_id lookups

---

## 11. Deployment & Rollout

### 11.1 Feature Flags

```python
# Feature flags for gradual rollout
AGENTS_MD_ENABLED = os.getenv("AGENTS_MD_ENABLED", "true") == "true"
CONTEXT_OVERLAY_ENABLED = os.getenv("CONTEXT_OVERLAY_ENABLED", "true") == "true"
AUTO_PR_COMMENT_ENABLED = os.getenv("AUTO_PR_COMMENT_ENABLED", "false") == "true"
```

### 11.2 Rollout Plan

| Phase | Scope | Duration |
|-------|-------|----------|
| Phase 1 | Internal testing (BFlow, NQH) | 1 week |
| Phase 2 | CLI only (no auto-comments) | 1 week |
| Phase 3 | Full rollout (with PR comments) | Sprint 81 |

### 11.3 Monitoring

```yaml
Metrics to track:
  - agents_md_generations_total (counter)
  - agents_md_validations_total (counter)
  - agents_md_validation_errors_total (counter)
  - context_overlay_requests_total (counter)
  - agents_md_generation_duration_seconds (histogram)
  - context_overlay_generation_duration_seconds (histogram)

Alerts:
  - agents_md_validation_error_rate > 10%
  - agents_md_generation_duration_p95 > 5s
```

---

## 12. Dependencies

### 12.1 Sprint 79 Dependencies (RESOLVED)

| Dependency | Status | Notes |
|------------|--------|-------|
| Evidence Ed25519 signing | ✅ Complete | `evidence_manifest_service.py` |
| GitHub Check Run service | ✅ Complete | `github_checks_service.py` |
| Over-claims fixes | ✅ Complete | Expert docs updated |

### 12.2 External Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| pydantic | 2.0+ | Data validation |
| click | 8.0+ | CLI framework |
| httpx | 0.25+ | GitHub API calls |

---

## 13. Open Questions (For CTO Review)

1. **Line limit enforcement**: Should we hard-fail at 200 lines or just warn?
   - Current: Warn at 150, fail at 200

2. **PR comment frequency**: Auto-comment on every PR update or only on open?
   - Recommendation: Only on PR open + gate status change

3. **Context overlay caching**: How long to cache overlay data?
   - Recommendation: 5 minutes for performance

4. **Multi-repo support**: How to handle monorepos with multiple AGENTS.md?
   - Defer to Sprint 82

---

## 14. Appendix

### 14.1 Example Generated AGENTS.md

```markdown
# AGENTS.md - SDLC Orchestrator

## Quick Start
- Full stack: `docker compose up -d`
- Backend only: `cd backend && pytest`
- Frontend only: `cd frontend/web && npm run dev`

## Architecture
- Infrastructure: Docker Compose
- Backend: Python (FastAPI)
- Frontend: React (TypeScript)
- Database: PostgreSQL
See `/docs/02-design/` for detailed architecture documentation.

## Current Stage
Check project dashboard for current SDLC stage and gate status.
Dynamic context is delivered via PR comments (not in this file).

## Conventions
- Python: ruff + mypy strict mode
- TypeScript: strict mode enabled
- Files: snake_case (Python ≤50 chars), camelCase/PascalCase (TypeScript)
- Tests: 95%+ coverage required

## Security
- OWASP ASVS L2 compliance required
- No hardcoded secrets (use environment variables)
- Input validation on all API endpoints
- SQL injection prevention via ORM
- AGPL: MinIO/Grafana network-only (NO SDK imports)

## Git Workflow
- Branch: `feature/{ticket}-{description}`
- Commit: `feat|fix|chore(scope): message`
- PR: Must pass quality gates before merge

## DO NOT
- Add mocks or placeholders (Zero Mock Policy)
- Skip tests for 'quick fixes'
- Hardcode secrets or credentials
- Use `// TODO` without ticket reference
- Import AGPL libraries (MinIO SDK, Grafana SDK)
```

### 14.2 Example Context Overlay PR Comment

```markdown
<!-- SDLC-CONTEXT-START -->
## 🎯 SDLC Context (Feb 03, 2026 10:00 UTC)

> 🔒 **STRICT MODE ACTIVE**: Only bug fixes allowed.

| Stage | Gate | Sprint |
|-------|------|--------|
| Stage 04 (BUILD) | G3 PASSED | Sprint 80 - AGENTS.md Generator (8 days left) |

### Active Constraints
- ⚠️ **Strict Mode**: Post-G3: Only bug fixes allowed. Feature work blocked.
- 🔴 **Security Review**: CVE-2026-1234 detected in auth_service.py
  - `backend/app/services/auth_service.py`
- ℹ️ **Agpl**: AGPL: MinIO/Grafana network-only access (no SDK imports)

---
*Generated by [SDLC Orchestrator](https://sdlc.dev) • [View Dashboard](#)*
<!-- SDLC-CONTEXT-END -->
```

---

## 15. Implementation Notes

### 15.1 Gate Status Enum Mapping (Feb 11, 2026)

The system uses two different status enum systems that MUST be explicitly mapped:

| Gate Model (DB - UPPERCASE) | DynamicContext (Events) | Display String |
|-----------------------------|------------------------|----------------|
| `APPROVED` | `GateStatus.PASSED` | `PASSED` |
| `REJECTED` | `GateStatus.FAILED` | `FAILED` |
| `PENDING_APPROVAL` | `GateStatus.IN_PROGRESS` | `PENDING` |
| `IN_PROGRESS` | `GateStatus.IN_PROGRESS` | `IN PROGRESS` |
| `DRAFT` | `GateStatus.PENDING` | `DRAFT` |
| `ARCHIVED` | `GateStatus.BYPASSED` | `ARCHIVED` |

**Important**: Gate model uses UPPERCASE strings. Always use case-sensitive comparison with UPPERCASE values. See `ContextOverlayService._get_stage_and_gate()` and `DynamicContextService.load_context()` for reference implementations.

### 15.2 Cold-Start DB Hydration (Feb 11, 2026)

`DynamicContextService` maintains in-memory context that resets on server restart. The `load_context()` method MUST query the gates table to hydrate initial state when `update_count == 0`. This ensures the Context Overlay API returns correct data immediately after deployment, without waiting for an EventBus `GateStatusChanged` event.

---

## 16. Approvals

| Role | Name | Status | Date |
|------|------|--------|------|
| Author | Backend Lead | ✅ Draft Complete | Jan 19, 2026 |
| Tech Lead | Tech Lead | ⏳ Review | - |
| CTO | CTO | ⏳ Approval | - |

---

**SDLC 6.1.0 | Sprint 80+ | Stage 04 (BUILD)**

*Document ID: TDS-080-001*
