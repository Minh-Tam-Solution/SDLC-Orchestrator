# ADR-050: Spec Converter & Editor Architecture

**Status**: PROPOSED
**Date**: February 4, 2026
**Sprint**: Sprint 154 (Spec Standard Completion)
**Author**: CTO + AI Assistant
**Framework**: SDLC 6.1.0
**Related**: [SPEC-0002-Specification-Standard](../14-Technical-Specs/SPEC-0002-Specification-Standard.md), [ADR-040-App-Builder-OpenSpec-Integration](ADR-040-App-Builder-OpenSpec-Integration.md)

---

## Context

### Problem Statement

SDLC Framework 6.0.5 defines a Specification Standard (SPEC-0002) with YAML frontmatter and BDD requirements. However, the platform currently lacks:

1. **No Format Conversion**: Cannot convert between BDD (Gherkin), OpenSpec YAML, User Stories, and Acceptance Criteria
2. **No Visual Editor**: Developers must manually write YAML frontmatter and BDD syntax
3. **No Import Capability**: Cannot import specs from external tools (Jira, Linear, GitHub Issues)
4. **No Templates**: Each spec starts from scratch without pre-built templates

### Current State (55% Spec Standard Completion)

| Capability | Status | Gap |
|------------|--------|-----|
| YAML Frontmatter Validation | ✅ Implemented | - |
| BDD Syntax Validation | ✅ Implemented | - |
| Format Conversion | ❌ Not implemented | Critical |
| Visual Editor | ❌ Not implemented | Critical |
| Templates | ❌ Not implemented | High |
| Import (Jira/Linear) | ❌ Not implemented | Medium |

### Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| REQ-1 | Convert BDD ↔ OpenSpec YAML bidirectionally | P0 | Roadmap |
| REQ-2 | Convert User Story ↔ BDD | P0 | Roadmap |
| REQ-3 | Convert Acceptance Criteria ↔ Test Cases | P0 | Roadmap |
| REQ-4 | AI-assisted Natural Language → Structured Spec | P0 | Roadmap |
| REQ-5 | Visual WYSIWYG spec editor | P0 | UX Research |
| REQ-6 | 10 ready-to-use templates | P1 | Roadmap |
| REQ-7 | Import from Jira/Linear | P2 | Enterprise customers |

---

## Decision

### Architecture Overview

Implement a **3-Layer Spec Processing Architecture**:

1. **Parser Layer** - Parse various spec formats into AST
2. **Transformer Layer** - Convert between formats via intermediate representation
3. **Renderer Layer** - Output to target format or visual editor

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SPEC CONVERTER ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   BDD       │  │  OpenSpec   │  │ User Story  │  │  Natural    │   │
│  │  (Gherkin)  │  │   (YAML)    │  │  (Markdown) │  │  Language   │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                │                │                │           │
│         ▼                ▼                ▼                ▼           │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                      PARSER LAYER                                │  │
│  │  gherkin_parser │ yaml_parser │ story_parser │ ai_parser        │  │
│  └────────────────────────────────┬────────────────────────────────┘  │
│                                   │                                    │
│                                   ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                 INTERMEDIATE REPRESENTATION (IR)                 │  │
│  │                                                                  │  │
│  │  {                                                               │  │
│  │    "spec_id": "SPEC-0026",                                      │  │
│  │    "title": "...",                                               │  │
│  │    "requirements": [                                             │  │
│  │      {                                                           │  │
│  │        "id": "REQ-1",                                            │  │
│  │        "given": "...",                                           │  │
│  │        "when": "...",                                            │  │
│  │        "then": "...",                                            │  │
│  │        "acceptance_criteria": [...]                              │  │
│  │      }                                                           │  │
│  │    ],                                                            │  │
│  │    "metadata": {...}                                             │  │
│  │  }                                                               │  │
│  └────────────────────────────────┬────────────────────────────────┘  │
│                                   │                                    │
│                                   ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    TRANSFORMER LAYER                             │  │
│  │  validate │ enrich │ normalize │ cross_reference                 │  │
│  └────────────────────────────────┬────────────────────────────────┘  │
│                                   │                                    │
│                                   ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                      RENDERER LAYER                              │  │
│  │  bdd_renderer │ yaml_renderer │ markdown_renderer │ json_api    │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│         │                │                │                │           │
│         ▼                ▼                ▼                ▼           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   .feature  │  │   .yaml     │  │   .md       │  │  Visual     │   │
│  │    file     │  │    file     │  │    file     │  │   Editor    │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Intermediate Representation (IR) Schema

```typescript
interface SpecIR {
  // Metadata (from YAML frontmatter)
  spec_id: string;           // e.g., "SPEC-0026"
  title: string;
  version: string;
  status: 'DRAFT' | 'PROPOSED' | 'APPROVED' | 'DEPRECATED';
  tier: ('LITE' | 'STANDARD' | 'PROFESSIONAL' | 'ENTERPRISE')[];
  owner: string;
  last_updated: string;
  tags: string[];
  related_adrs: string[];
  related_specs: string[];

  // Content
  executive_summary: string;
  problem_statement: string;

  // Requirements (BDD format internally)
  requirements: SpecRequirement[];

  // Acceptance Criteria
  acceptance_criteria: AcceptanceCriterion[];

  // Additional sections
  design_decisions: DesignDecision[];
  implementation_plan: ImplementationStep[];
  references: Reference[];
}

interface SpecRequirement {
  id: string;              // e.g., "REQ-1"
  title: string;
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  tier: string[];          // Which tiers require this

  // BDD format
  given: string;           // Context/precondition
  when: string;            // Action/trigger
  then: string;            // Expected outcome

  // Alternative formats (derived)
  user_story?: string;     // "As a... I want... So that..."
  acceptance_criteria: string[];
  test_cases?: string[];
}

interface AcceptanceCriterion {
  id: string;
  scenario: string;
  given: string;
  when: string;
  then: string;
  tier: string[];
  testable: boolean;
}
```

### Visual Editor Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       SPEC VISUAL EDITOR                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │     METADATA PANEL          │  │     PREVIEW PANEL               │  │
│  │                             │  │                                 │  │
│  │  Spec ID: [SPEC-____]       │  │  # SPEC-0026: Feature Name      │  │
│  │  Title: [___________]       │  │                                 │  │
│  │  Status: [Dropdown___]      │  │  ---                            │  │
│  │  Tier: [x]LITE [x]STANDARD  │  │  spec_id: SPEC-0026             │  │
│  │        [ ]PRO  [ ]ENTERPRISE│  │  title: Feature Name            │  │
│  │  Owner: [___________]       │  │  status: DRAFT                  │  │
│  │  Tags: [tag1] [tag2] [+]    │  │  ...                            │  │
│  │                             │  │  ---                            │  │
│  │  Related ADRs: [ADR-___][+] │  │                                 │  │
│  │  Related Specs: [SPEC-_][+] │  │  ## Requirements                │  │
│  │                             │  │                                 │  │
│  └─────────────────────────────┘  │  ### REQ-1: Requirement         │  │
│                                   │                                 │  │
│  ┌─────────────────────────────┐  │  **GIVEN** context              │  │
│  │   REQUIREMENTS EDITOR       │  │  **WHEN** action                │  │
│  │                             │  │  **THEN** outcome               │  │
│  │  [+ Add Requirement]        │  │                                 │  │
│  │                             │  │  ---                            │  │
│  │  REQ-1: [_______________]   │  │                                 │  │
│  │  Priority: [P0 ▼]           │  │  Format: [BDD ▼] [Copy] [DL]   │  │
│  │  Tier: [x]ALL [ ]Specific   │  │                                 │  │
│  │                             │  └─────────────────────────────────┘  │
│  │  GIVEN: [________________]  │                                       │
│  │  WHEN:  [________________]  │  ┌─────────────────────────────────┐  │
│  │  THEN:  [________________]  │  │     TEMPLATE SELECTOR           │  │
│  │                             │  │                                 │  │
│  │  [Generate from User Story] │  │  [API Endpoint] [UI Feature]   │  │
│  │  [AI Assist ✨]             │  │  [Database] [Integration]       │  │
│  │                             │  │  [Security] [Performance]       │  │
│  └─────────────────────────────┘  │  [Workflow] [Report] [Import]   │  │
│                                   │                                 │  │
│  ┌─────────────────────────────┐  └─────────────────────────────────┘  │
│  │   ACCEPTANCE CRITERIA       │                                       │
│  │                             │  ┌─────────────────────────────────┐  │
│  │  [+ Add Criterion]          │  │     ACTIONS                     │  │
│  │                             │  │                                 │  │
│  │  AC-1: Scenario name        │  │  [💾 Save] [📤 Export] [🔄 Conv]│  │
│  │  ├─ Given: context          │  │  [👁 Preview] [✓ Validate]      │  │
│  │  ├─ When: action            │  │  [📥 Import from Jira/Linear]   │  │
│  │  └─ Then: outcome           │  │                                 │  │
│  │                             │  └─────────────────────────────────┘  │
│  └─────────────────────────────┘                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Supported Conversions

| From | To | Method |
|------|-----|--------|
| BDD (Gherkin) | OpenSpec YAML | Parser → IR → YAML Renderer |
| OpenSpec YAML | BDD (Gherkin) | Parser → IR → BDD Renderer |
| User Story | BDD | AI + Rule-based transformation |
| User Story | OpenSpec | User Story → BDD → OpenSpec |
| Natural Language | Structured Spec | AI (Ollama qwen3-coder:30b) |
| Jira Issue | OpenSpec | API fetch → Parser → IR → Renderer |
| Linear Issue | OpenSpec | API fetch → Parser → IR → Renderer |
| Acceptance Criteria | Test Cases | Rule-based + AI enhancement |

### AI-Assisted Features

```yaml
AI Capabilities:
  natural_language_to_spec:
    model: qwen3-coder:30b
    input: "User description of feature"
    output: Complete SpecIR

  user_story_to_bdd:
    model: qwen3:32b
    input: "As a user, I want..."
    output: GIVEN-WHEN-THEN format

  spec_enhancement:
    model: qwen3-coder:30b
    input: Draft spec
    output: Enhanced spec with edge cases

  template_suggestion:
    model: qwen3:14b
    input: Spec context
    output: Recommended template
```

### Template Library

| Template | Use Case | Tier |
|----------|----------|------|
| `api-endpoint` | REST API endpoint spec | ALL |
| `ui-feature` | Frontend feature spec | ALL |
| `database-schema` | Database change spec | STANDARD+ |
| `integration` | Third-party integration spec | STANDARD+ |
| `security-feature` | Security-related spec | PROFESSIONAL+ |
| `performance` | Performance requirement spec | PROFESSIONAL+ |
| `workflow` | Business workflow spec | ALL |
| `report` | Analytics/reporting spec | STANDARD+ |
| `migration` | Data migration spec | PROFESSIONAL+ |
| `compliance` | Compliance requirement spec | ENTERPRISE |

---

## Alternatives Considered

### Alternative 1: Separate Tools per Format

**Approach**: Build separate converter tools for each format pair.

**Pros**:
- Simpler individual implementations
- No need for IR design

**Cons**:
- N² complexity (for N formats)
- Inconsistent behavior between converters
- Harder to maintain

**Decision**: Rejected - IR-based approach scales better

### Alternative 2: Use Existing Tools (Cucumber, etc.)

**Approach**: Integrate existing BDD tools.

**Pros**:
- Mature, battle-tested
- Large ecosystem

**Cons**:
- Limited to BDD format
- No OpenSpec support
- No visual editor
- External dependency

**Decision**: Rejected - Our spec standard is unique

### Alternative 3: LLM-Only Conversion

**Approach**: Use LLM for all conversions without parser/IR.

**Pros**:
- Flexible, handles edge cases
- No grammar maintenance

**Cons**:
- Non-deterministic output
- Expensive for bulk operations
- Quality varies

**Decision**: Rejected - Hybrid approach (rule-based + AI assist) is better

---

## Consequences

### Positive

1. **Complete Spec Standard**: 55% → 90% completion
2. **Developer Productivity**: Visual editor reduces spec authoring time by 70%
3. **Format Flexibility**: Teams can work in preferred format
4. **Import Capability**: Migrate existing specs from Jira/Linear
5. **AI Enhancement**: Natural language to structured spec

### Negative

1. **Complexity**: 3-layer architecture adds complexity
2. **Maintenance**: Must maintain parsers for each format
3. **AI Cost**: LLM calls for AI-assisted features

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Parser bugs | Comprehensive test suite with edge cases |
| AI hallucinations | Validation layer + human review |
| Format drift | Version-controlled IR schema |
| Performance | Caching + incremental parsing |

---

## Implementation Plan

### Sprint 154 Deliverables

| Day | Task | LOC | Owner |
|-----|------|-----|-------|
| Day 1 | IR Schema + Parser Layer | ~600 | Backend |
| Day 2 | BDD ↔ OpenSpec Converters | ~400 | Backend |
| Day 3 | Spec Editor UI (Metadata + Requirements) | ~500 | Frontend |
| Day 4 | Template Library + AI Integration | ~400 | Full Stack |
| Day 5 | Import (Jira/Linear) + Testing | ~400 | Full Stack |
| **Total** | | **~2,300** | |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/specs/parse` | Parse spec from any format |
| POST | `/api/v1/specs/convert` | Convert between formats |
| GET | `/api/v1/specs/templates` | List available templates |
| POST | `/api/v1/specs/generate` | AI-generate from natural language |
| POST | `/api/v1/specs/import/jira` | Import from Jira |
| POST | `/api/v1/specs/import/linear` | Import from Linear |
| POST | `/api/v1/specs/validate` | Validate spec against schema |
| GET | `/api/v1/specs/{id}` | Get spec by ID |
| PUT | `/api/v1/specs/{id}` | Update spec |

---

## References

- [SPEC-0002: Framework 6.0.5 Specification Standard](../14-Technical-Specs/SPEC-0002-Specification-Standard.md)
- [ADR-040: App Builder OpenSpec Integration](ADR-040-App-Builder-OpenSpec-Integration.md)
- [Gherkin Syntax Reference](https://cucumber.io/docs/gherkin/reference/)
- [YAML 1.2 Specification](https://yaml.org/spec/1.2/)

---

## Approval

| Role | Name | Date | Decision |
|------|------|------|----------|
| CTO | - | Feb 4, 2026 | ⏳ PENDING |
| Backend Lead | - | Feb 4, 2026 | ⏳ PENDING |
| Frontend Lead | - | Feb 4, 2026 | ⏳ PENDING |

---

**Document Status**: PROPOSED
**Implementation Status**: ⏳ Sprint 154 Planned
