---
spec_id: SPEC-0026
title: Spec Converter & Editor Technical Specification
version: "1.0.0"
status: PROPOSED
tier:
  - LITE
  - STANDARD
  - PROFESSIONAL
  - ENTERPRISE
pillar: 7
owner: Backend Team + Frontend Team
last_updated: "2026-02-04"
tags:
  - spec-converter
  - bdd
  - openspec
  - visual-editor
related_adrs:
  - ADR-050
  - ADR-040
related_specs:
  - SPEC-0002
---

# SPEC-0026: Spec Converter & Editor Technical Specification

**Version**: 1.0.0
**Status**: PROPOSED
**Sprint**: Sprint 154 (Spec Standard Completion)
**Author**: Backend Team + Frontend Team
**ADR Reference**: [ADR-050-Spec-Converter-Editor-Architecture](../01-ADRs/ADR-050-Spec-Converter-Editor-Architecture.md)

---

## 1. Overview

### 1.1 Purpose

This specification defines the technical implementation of the Spec Converter and Visual Editor for SDLC Orchestrator, enabling bidirectional format conversion and visual spec authoring.

### 1.2 Scope

- Parser implementation for BDD, OpenSpec, User Story formats
- Intermediate Representation (IR) schema
- Converter service with bidirectional transformations
- Visual editor React components
- Template library with 10 templates
- Import capability for Jira/Linear

### 1.3 References

| Document | Location |
|----------|----------|
| ADR-050 | `docs/02-design/01-ADRs/ADR-050-Spec-Converter-Editor-Architecture.md` |
| SPEC-0002 | `docs/02-design/14-Technical-Specs/SPEC-0002-Specification-Standard.md` |
| ADR-040 | `docs/02-design/01-ADRs/ADR-040-App-Builder-OpenSpec-Integration.md` |

---

## 2. Functional Requirements

### 2.1 BDD to OpenSpec Conversion

**GIVEN** a valid BDD (Gherkin) feature file
**WHEN** the user requests conversion to OpenSpec YAML
**THEN** the system produces a valid SDLC 6.1.0 specification with:
- Complete YAML frontmatter
- BDD requirements in GIVEN-WHEN-THEN format
- Properly mapped acceptance criteria

**Acceptance Criteria**:
| ID | Scenario | Tier | Testable |
|----|----------|------|----------|
| AC-2.1.1 | Feature → spec_id mapping | ALL | ✅ |
| AC-2.1.2 | Scenario → requirements mapping | ALL | ✅ |
| AC-2.1.3 | Tags → metadata mapping | ALL | ✅ |
| AC-2.1.4 | Background → context mapping | ALL | ✅ |

### 2.2 OpenSpec to BDD Conversion

**GIVEN** a valid OpenSpec YAML specification
**WHEN** the user requests conversion to BDD format
**THEN** the system produces a valid Gherkin feature file with:
- Feature name from title
- Scenarios from requirements
- Steps from GIVEN-WHEN-THEN

**Acceptance Criteria**:
| ID | Scenario | Tier | Testable |
|----|----------|------|----------|
| AC-2.2.1 | Title → Feature mapping | ALL | ✅ |
| AC-2.2.2 | Requirements → Scenarios | ALL | ✅ |
| AC-2.2.3 | Metadata → Tags | ALL | ✅ |

### 2.3 User Story to BDD Conversion

**GIVEN** a user story in "As a... I want... So that..." format
**WHEN** the user requests conversion to BDD
**THEN** the system produces GIVEN-WHEN-THEN using:
- AI analysis of user story intent
- Rule-based extraction of actors, actions, outcomes
- Confidence score for quality assessment

**Acceptance Criteria**:
| ID | Scenario | Tier | Testable |
|----|----------|------|----------|
| AC-2.3.1 | Actor → GIVEN user type | ALL | ✅ |
| AC-2.3.2 | Want → WHEN action | ALL | ✅ |
| AC-2.3.3 | So that → THEN outcome | ALL | ✅ |
| AC-2.3.4 | Confidence score > 0.7 | ALL | ✅ |

### 2.4 Natural Language to Spec (AI-Assisted)

**GIVEN** a natural language description of a feature
**WHEN** the user requests spec generation
**THEN** the system produces a complete SpecIR with:
- Auto-generated spec_id
- Inferred requirements
- Suggested acceptance criteria

**Acceptance Criteria**:
| ID | Scenario | Tier | Testable |
|----|----------|------|----------|
| AC-2.4.1 | Generate valid SpecIR | ALL | ✅ |
| AC-2.4.2 | Latency < 10s | ALL | ✅ |
| AC-2.4.3 | Confidence score provided | ALL | ✅ |

### 2.5 Visual Editor

**GIVEN** a user with spec edit permissions
**WHEN** the user opens the visual editor
**THEN** the system provides:
- Metadata panel with form inputs
- Requirements editor with BDD fields
- Real-time preview panel
- Template selector
- Export/Import buttons

**Acceptance Criteria**:
| ID | Scenario | Tier | Testable |
|----|----------|------|----------|
| AC-2.5.1 | Metadata form saves to IR | ALL | ✅ |
| AC-2.5.2 | Requirements CRUD | ALL | ✅ |
| AC-2.5.3 | Live preview updates | ALL | ✅ |
| AC-2.5.4 | Format selector works | ALL | ✅ |

### 2.6 Template Library

**GIVEN** a user creating a new spec
**WHEN** the user selects a template
**THEN** the system pre-populates the editor with:
- Appropriate metadata defaults
- Placeholder requirements
- Tier-specific sections

**Acceptance Criteria**:
| ID | Scenario | Tier | Testable |
|----|----------|------|----------|
| AC-2.6.1 | 10 templates available | ALL | ✅ |
| AC-2.6.2 | Template → IR mapping | ALL | ✅ |
| AC-2.6.3 | Tier filtering works | ALL | ✅ |

### 2.7 Jira/Linear Import

**GIVEN** a Jira or Linear issue URL
**WHEN** the user requests import
**THEN** the system creates a SpecIR from:
- Issue title → spec title
- Issue description → problem statement
- Acceptance criteria → requirements (AI-assisted)
- Labels → tags

**Acceptance Criteria**:
| ID | Scenario | Tier | Testable |
|----|----------|------|----------|
| AC-2.7.1 | Jira issue import works | STANDARD+ | ✅ |
| AC-2.7.2 | Linear issue import works | STANDARD+ | ✅ |
| AC-2.7.3 | OAuth authentication | STANDARD+ | ✅ |

---

## 3. Technical Implementation

### 3.1 Backend Service

**File**: `backend/app/services/spec_converter_service.py`

```python
from typing import Optional, Literal
from pydantic import BaseModel
from enum import Enum

class SpecFormat(str, Enum):
    BDD = "bdd"
    OPENSPEC = "openspec"
    USER_STORY = "user_story"
    NATURAL_LANGUAGE = "natural_language"

class SpecIR(BaseModel):
    """Intermediate Representation for specifications."""
    spec_id: str
    title: str
    version: str = "1.0.0"
    status: Literal["DRAFT", "PROPOSED", "APPROVED", "DEPRECATED"] = "DRAFT"
    tier: list[str] = ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"]
    owner: str = ""
    last_updated: str
    tags: list[str] = []
    related_adrs: list[str] = []
    related_specs: list[str] = []

    executive_summary: str = ""
    problem_statement: str = ""
    requirements: list["SpecRequirement"] = []
    acceptance_criteria: list["AcceptanceCriterion"] = []

class SpecRequirement(BaseModel):
    id: str
    title: str
    priority: Literal["P0", "P1", "P2", "P3"] = "P1"
    tier: list[str] = ["ALL"]
    given: str
    when: str
    then: str
    user_story: Optional[str] = None
    acceptance_criteria: list[str] = []

class AcceptanceCriterion(BaseModel):
    id: str
    scenario: str
    given: str
    when: str
    then: str
    tier: list[str] = ["ALL"]
    testable: bool = True

class SpecConverterService:
    """Service for converting between spec formats."""

    async def parse(
        self,
        content: str,
        format: SpecFormat
    ) -> SpecIR:
        """Parse content from any format to IR."""
        parser = self._get_parser(format)
        return await parser.parse(content)

    async def convert(
        self,
        content: str,
        from_format: SpecFormat,
        to_format: SpecFormat
    ) -> str:
        """Convert between formats."""
        ir = await self.parse(content, from_format)
        renderer = self._get_renderer(to_format)
        return await renderer.render(ir)

    async def generate_from_natural_language(
        self,
        description: str,
        template: Optional[str] = None
    ) -> tuple[SpecIR, float]:
        """AI-generate spec from natural language."""
        # Use Ollama qwen3-coder:30b
        ...
        return ir, confidence_score

    def _get_parser(self, format: SpecFormat):
        parsers = {
            SpecFormat.BDD: GherkinParser(),
            SpecFormat.OPENSPEC: OpenSpecParser(),
            SpecFormat.USER_STORY: UserStoryParser(),
            SpecFormat.NATURAL_LANGUAGE: NaturalLanguageParser(),
        }
        return parsers[format]

    def _get_renderer(self, format: SpecFormat):
        renderers = {
            SpecFormat.BDD: GherkinRenderer(),
            SpecFormat.OPENSPEC: OpenSpecRenderer(),
            SpecFormat.USER_STORY: UserStoryRenderer(),
        }
        return renderers[format]
```

### 3.2 Parsers

**Gherkin Parser** (`parsers/gherkin_parser.py`):
```python
import re
from typing import List

class GherkinParser:
    """Parse Gherkin feature files to IR."""

    FEATURE_PATTERN = r"Feature:\s*(.+)"
    SCENARIO_PATTERN = r"Scenario(?:\s+Outline)?:\s*(.+)"
    STEP_PATTERNS = {
        "given": r"Given\s+(.+)",
        "when": r"When\s+(.+)",
        "then": r"Then\s+(.+)",
        "and": r"And\s+(.+)",
    }

    async def parse(self, content: str) -> SpecIR:
        lines = content.strip().split("\n")

        feature_name = self._extract_feature(lines)
        scenarios = self._extract_scenarios(lines)
        tags = self._extract_tags(lines)

        requirements = [
            SpecRequirement(
                id=f"REQ-{i+1}",
                title=scenario["name"],
                given=scenario["given"],
                when=scenario["when"],
                then=scenario["then"],
            )
            for i, scenario in enumerate(scenarios)
        ]

        return SpecIR(
            spec_id=self._generate_spec_id(feature_name),
            title=feature_name,
            last_updated=datetime.utcnow().isoformat(),
            tags=tags,
            requirements=requirements,
        )
```

**OpenSpec Parser** (`parsers/openspec_parser.py`):
```python
import yaml

class OpenSpecParser:
    """Parse OpenSpec YAML to IR."""

    async def parse(self, content: str) -> SpecIR:
        # Split frontmatter and body
        parts = content.split("---")
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            body = "---".join(parts[2:])
        else:
            frontmatter = {}
            body = content

        # Parse requirements from body
        requirements = self._extract_requirements(body)
        acceptance_criteria = self._extract_acceptance_criteria(body)

        return SpecIR(
            spec_id=frontmatter.get("spec_id", ""),
            title=frontmatter.get("title", ""),
            version=frontmatter.get("version", "1.0.0"),
            status=frontmatter.get("status", "DRAFT"),
            tier=frontmatter.get("tier", []),
            owner=frontmatter.get("owner", ""),
            last_updated=frontmatter.get("last_updated", ""),
            tags=frontmatter.get("tags", []),
            related_adrs=frontmatter.get("related_adrs", []),
            related_specs=frontmatter.get("related_specs", []),
            requirements=requirements,
            acceptance_criteria=acceptance_criteria,
        )
```

### 3.3 Renderers

**Gherkin Renderer** (`renderers/gherkin_renderer.py`):
```python
class GherkinRenderer:
    """Render IR to Gherkin feature file."""

    async def render(self, ir: SpecIR) -> str:
        lines = []

        # Tags
        if ir.tags:
            lines.append(" ".join(f"@{tag}" for tag in ir.tags))

        # Feature
        lines.append(f"Feature: {ir.title}")
        if ir.problem_statement:
            lines.append(f"  {ir.problem_statement}")
        lines.append("")

        # Scenarios
        for req in ir.requirements:
            lines.append(f"  Scenario: {req.title}")
            lines.append(f"    Given {req.given}")
            lines.append(f"    When {req.when}")
            lines.append(f"    Then {req.then}")
            lines.append("")

        return "\n".join(lines)
```

**OpenSpec Renderer** (`renderers/openspec_renderer.py`):
```python
class OpenSpecRenderer:
    """Render IR to OpenSpec YAML."""

    async def render(self, ir: SpecIR) -> str:
        # Frontmatter
        frontmatter = {
            "spec_id": ir.spec_id,
            "title": ir.title,
            "version": ir.version,
            "status": ir.status,
            "tier": ir.tier,
            "owner": ir.owner,
            "last_updated": ir.last_updated,
            "tags": ir.tags,
            "related_adrs": ir.related_adrs,
            "related_specs": ir.related_specs,
        }

        yaml_front = yaml.dump(frontmatter, default_flow_style=False)

        # Body
        body_lines = [
            f"# {ir.spec_id}: {ir.title}",
            "",
            "## Functional Requirements",
            "",
        ]

        for req in ir.requirements:
            body_lines.extend([
                f"### {req.id}: {req.title}",
                "",
                f"**GIVEN** {req.given}",
                f"**WHEN** {req.when}",
                f"**THEN** {req.then}",
                "",
            ])

        return f"---\n{yaml_front}---\n\n" + "\n".join(body_lines)
```

### 3.4 API Routes

**File**: `backend/app/api/routes/specs.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.spec_converter_service import (
    SpecConverterService,
    SpecFormat,
    SpecIR
)

router = APIRouter(prefix="/specs", tags=["Specifications"])

class ParseRequest(BaseModel):
    content: str
    format: SpecFormat

class ConvertRequest(BaseModel):
    content: str
    from_format: SpecFormat
    to_format: SpecFormat

class GenerateRequest(BaseModel):
    description: str
    template: str | None = None

class ImportJiraRequest(BaseModel):
    issue_url: str
    project_id: str

@router.post("/parse", response_model=SpecIR)
async def parse_spec(
    request: ParseRequest,
    service: SpecConverterService = Depends()
):
    """Parse spec from any format to IR."""
    return await service.parse(request.content, request.format)

@router.post("/convert")
async def convert_spec(
    request: ConvertRequest,
    service: SpecConverterService = Depends()
):
    """Convert between spec formats."""
    result = await service.convert(
        request.content,
        request.from_format,
        request.to_format
    )
    return {"result": result, "format": request.to_format}

@router.post("/generate")
async def generate_spec(
    request: GenerateRequest,
    service: SpecConverterService = Depends()
):
    """Generate spec from natural language."""
    ir, confidence = await service.generate_from_natural_language(
        request.description,
        request.template
    )
    return {"spec": ir, "confidence": confidence}

@router.get("/templates")
async def list_templates():
    """List available spec templates."""
    return {
        "templates": [
            {"id": "api-endpoint", "name": "API Endpoint", "tier": ["ALL"]},
            {"id": "ui-feature", "name": "UI Feature", "tier": ["ALL"]},
            {"id": "database-schema", "name": "Database Schema", "tier": ["STANDARD+"]},
            {"id": "integration", "name": "Third-party Integration", "tier": ["STANDARD+"]},
            {"id": "security-feature", "name": "Security Feature", "tier": ["PROFESSIONAL+"]},
            {"id": "performance", "name": "Performance Requirement", "tier": ["PROFESSIONAL+"]},
            {"id": "workflow", "name": "Business Workflow", "tier": ["ALL"]},
            {"id": "report", "name": "Analytics Report", "tier": ["STANDARD+"]},
            {"id": "migration", "name": "Data Migration", "tier": ["PROFESSIONAL+"]},
            {"id": "compliance", "name": "Compliance Requirement", "tier": ["ENTERPRISE"]},
        ]
    }

@router.post("/import/jira")
async def import_from_jira(
    request: ImportJiraRequest,
    service: SpecConverterService = Depends()
):
    """Import spec from Jira issue."""
    # Requires Jira OAuth integration
    ...

@router.post("/import/linear")
async def import_from_linear(
    request: ImportJiraRequest,
    service: SpecConverterService = Depends()
):
    """Import spec from Linear issue."""
    # Requires Linear OAuth integration
    ...

@router.post("/validate")
async def validate_spec(
    request: ParseRequest,
    service: SpecConverterService = Depends()
):
    """Validate spec against schema."""
    try:
        ir = await service.parse(request.content, request.format)
        errors = service.validate(ir)
        return {"valid": len(errors) == 0, "errors": errors}
    except Exception as e:
        return {"valid": False, "errors": [str(e)]}
```

### 3.5 Frontend Components

**Spec Editor Hook** (`frontend/src/hooks/useSpecEditor.ts`):
```typescript
import { useState, useCallback } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export type SpecFormat = 'bdd' | 'openspec' | 'user_story' | 'natural_language';

export interface SpecIR {
  spec_id: string;
  title: string;
  version: string;
  status: 'DRAFT' | 'PROPOSED' | 'APPROVED' | 'DEPRECATED';
  tier: string[];
  owner: string;
  last_updated: string;
  tags: string[];
  related_adrs: string[];
  related_specs: string[];
  requirements: SpecRequirement[];
  acceptance_criteria: AcceptanceCriterion[];
}

export interface SpecRequirement {
  id: string;
  title: string;
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  tier: string[];
  given: string;
  when: string;
  then: string;
}

export function useSpecEditor() {
  const [spec, setSpec] = useState<SpecIR | null>(null);
  const [previewFormat, setPreviewFormat] = useState<SpecFormat>('openspec');

  // Parse spec
  const parseMutation = useMutation({
    mutationFn: async ({ content, format }: { content: string; format: SpecFormat }) => {
      const response = await api.post<SpecIR>('/specs/parse', { content, format });
      return response.data;
    },
    onSuccess: (data) => setSpec(data),
  });

  // Convert spec
  const convertMutation = useMutation({
    mutationFn: async ({
      content,
      fromFormat,
      toFormat
    }: {
      content: string;
      fromFormat: SpecFormat;
      toFormat: SpecFormat
    }) => {
      const response = await api.post('/specs/convert', {
        content,
        from_format: fromFormat,
        to_format: toFormat,
      });
      return response.data;
    },
  });

  // Generate from natural language
  const generateMutation = useMutation({
    mutationFn: async ({ description, template }: { description: string; template?: string }) => {
      const response = await api.post('/specs/generate', { description, template });
      return response.data;
    },
    onSuccess: (data) => setSpec(data.spec),
  });

  // Templates
  const { data: templates } = useQuery({
    queryKey: ['specs', 'templates'],
    queryFn: async () => {
      const response = await api.get('/specs/templates');
      return response.data.templates;
    },
  });

  // Update spec fields
  const updateMetadata = useCallback((updates: Partial<SpecIR>) => {
    setSpec((prev) => prev ? { ...prev, ...updates } : null);
  }, []);

  const addRequirement = useCallback(() => {
    setSpec((prev) => {
      if (!prev) return null;
      const newReq: SpecRequirement = {
        id: `REQ-${prev.requirements.length + 1}`,
        title: '',
        priority: 'P1',
        tier: ['ALL'],
        given: '',
        when: '',
        then: '',
      };
      return { ...prev, requirements: [...prev.requirements, newReq] };
    });
  }, []);

  const updateRequirement = useCallback((id: string, updates: Partial<SpecRequirement>) => {
    setSpec((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        requirements: prev.requirements.map((req) =>
          req.id === id ? { ...req, ...updates } : req
        ),
      };
    });
  }, []);

  const deleteRequirement = useCallback((id: string) => {
    setSpec((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        requirements: prev.requirements.filter((req) => req.id !== id),
      };
    });
  }, []);

  return {
    spec,
    setSpec,
    previewFormat,
    setPreviewFormat,
    templates,
    parseMutation,
    convertMutation,
    generateMutation,
    updateMetadata,
    addRequirement,
    updateRequirement,
    deleteRequirement,
  };
}
```

---

## 4. Template Library

### 4.1 Template Definitions

| ID | Name | Sections | Tier |
|----|------|----------|------|
| `api-endpoint` | API Endpoint | Request/Response/Auth/Errors | ALL |
| `ui-feature` | UI Feature | User Flow/Components/States | ALL |
| `database-schema` | Database Schema | Tables/Relations/Migrations | STANDARD+ |
| `integration` | Third-party Integration | Auth/Endpoints/Errors/Retry | STANDARD+ |
| `security-feature` | Security Feature | Threats/Mitigations/Compliance | PROFESSIONAL+ |
| `performance` | Performance Requirement | Latency/Throughput/Scalability | PROFESSIONAL+ |
| `workflow` | Business Workflow | Steps/Conditions/Outcomes | ALL |
| `report` | Analytics Report | Metrics/Filters/Export | STANDARD+ |
| `migration` | Data Migration | Source/Target/Validation/Rollback | PROFESSIONAL+ |
| `compliance` | Compliance Requirement | Regulation/Controls/Evidence | ENTERPRISE |

---

## 5. Testing

### 5.1 Unit Tests

| Test Suite | Tests | Description |
|------------|-------|-------------|
| Gherkin Parser | 15 | Feature, Scenario, Steps, Tags, Background |
| OpenSpec Parser | 12 | Frontmatter, Requirements, AC |
| User Story Parser | 8 | Actor, Action, Outcome extraction |
| Gherkin Renderer | 10 | Feature file generation |
| OpenSpec Renderer | 10 | YAML generation |
| Converter Service | 20 | End-to-end conversions |
| **Total** | **75** | |

### 5.2 Integration Tests

| Test | Description |
|------|-------------|
| BDD → OpenSpec → BDD roundtrip | Lossless conversion |
| Natural language → Spec | AI generation quality |
| Template → Editor → Export | Full workflow |
| Jira import → Spec | External integration |

---

## 6. Performance Requirements

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Parse (any format) | <100ms | p95 latency |
| Convert | <200ms | p95 latency |
| AI Generate | <10s | p95 latency |
| Editor load | <500ms | TTI |
| Preview update | <100ms | Debounced |

---

## 7. Security Considerations

- OAuth tokens for Jira/Linear stored encrypted
- AI prompts sanitized to prevent injection
- Spec content validated before storage
- Rate limiting on AI generation (10 req/min)

---

## 8. Implementation Plan

| Day | Task | Owner | LOC |
|-----|------|-------|-----|
| Day 1 | IR Schema + Parsers | Backend | ~600 |
| Day 2 | Renderers + Converter Service | Backend | ~400 |
| Day 3 | API Routes + useSpecEditor | Full Stack | ~500 |
| Day 4 | Visual Editor UI | Frontend | ~500 |
| Day 5 | Templates + Import + Tests | Full Stack | ~400 |
| **Total** | | | **~2,400** |

---

## 9. Exit Criteria

- [ ] BDD ↔ OpenSpec bidirectional conversion works
- [ ] User Story → BDD conversion with AI assist
- [ ] Visual editor with metadata + requirements panels
- [ ] Live preview in multiple formats
- [ ] 10 templates available
- [ ] Jira/Linear import functional
- [ ] 75 unit tests passing
- [ ] Spec Standard: 55% → 90% complete

---

**Specification Status**: PROPOSED
**Implementation Status**: ⏳ Sprint 154 Planned
