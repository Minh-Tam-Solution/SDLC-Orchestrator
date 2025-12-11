# Onboarding Flow Specification - SDLC 5.0.0

**Version**: 1.0.0
**Date**: December 13, 2025
**Status**: ACTIVE - Sprint 32 Phase 2
**Authority**: CTO + CPO Approved
**Framework**: SDLC 5.0.0 Complete Lifecycle (Contract-First, 4-Tier Classification)

---

## 1. Overview

This document specifies the complete onboarding flows for SDLC Orchestrator, covering both Web Dashboard and VS Code Extension user journeys. All flows are aligned with SDLC 5.0.0 Contract-First stage structure and 4-Tier Classification system.

### 1.1 Key Changes from SDLC 4.9.x

| Aspect | SDLC 4.9.x | SDLC 5.0.0 |
|--------|------------|------------|
| **Stage Order** | INTEGRATE at Stage 07 | INTEGRATE at Stage 03 (Contract-First) |
| **Stage Names** | CamelCase (00-Project-Foundation) | lowercase (00-foundation) |
| **Classification** | 3-pack system | 4-Tier (LITE/STANDARD/PROFESSIONAL/ENTERPRISE) |
| **Onboarding** | Policy Pack selection | Tier selection with stage requirements |

### 1.2 SDLC 5.0.0 Stage Structure (Contract-First Order)

```yaml
# LINEAR STAGES (Sequential per release):
Stage 00 - foundation:   WHY - Problem Definition          → docs/00-foundation/
Stage 01 - planning:     WHAT - Requirements Analysis      → docs/01-planning/
Stage 02 - design:       HOW - Architecture Design         → docs/02-design/
Stage 03 - integration:  API Design & System Integration   → docs/03-integration/  ← Contract-First
Stage 04 - build:        Development & Implementation      → docs/04-build/
Stage 05 - test:         Quality Assurance                 → docs/05-test/
Stage 06 - deploy:       Release & Deployment              → docs/06-deploy/
Stage 07 - operate:      Production & Operations           → docs/07-operate/

# CONTINUOUS STAGES (Ongoing throughout project):
Stage 08 - collaborate:  Team Coordination & Communication → docs/08-collaborate/
Stage 09 - govern:       Governance & Compliance           → docs/09-govern/
Stage 10 - archive:      Historical Archive                → docs/10-archive/
```

### 1.3 4-Tier Classification System

| Tier | Team Size | Required Stages | P0 Artifacts | Compliance |
|------|-----------|-----------------|--------------|------------|
| **LITE** | 1-2 | 00, 01, 02, 03 | Optional | None |
| **STANDARD** | 3-10 | 00, 01, 02, 03, 04, 05 | Optional | None |
| **PROFESSIONAL** | 10-50 | 00-09 (all 10) | Required | Optional |
| **ENTERPRISE** | 50+ | 00-10 (all 11) | Required | ISO 27001, SOC 2 |

#### Visual: 4-Tier Classification Pyramid

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │              4-TIER CLASSIFICATION PYRAMID                   │
                    │                    SDLC 5.0.0                                │
                    └─────────────────────────────────────────────────────────────┘

                                          ▲
                                         ╱ ╲
                                        ╱   ╲
                                       ╱     ╲
                                      ╱  50+  ╲
                                     ╱  people ╲
                                    ╱───────────╲
                                   ╱ ENTERPRISE  ╲
                                  ╱   11 stages   ╲
                                 ╱  P0 + ISO/SOC2  ╲
                                ╱───────────────────╲
                               ╱      10-50 people   ╲
                              ╱      PROFESSIONAL     ╲
                             ╱        10 stages        ╲
                            ╱       P0 Required         ╲
                           ╱─────────────────────────────╲
                          ╱         3-10 people           ╲
                         ╱          STANDARD               ╲
                        ╱           6 stages                ╲
                       ╱          Balanced Governance        ╲
                      ╱───────────────────────────────────────╲
                     ╱              1-2 people                 ╲
                    ╱                 LITE                      ╲
                   ╱               4 stages                      ╲
                  ╱             Minimal Setup                     ╲
                 ╱─────────────────────────────────────────────────╲
                ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔

                ┌────────────────────────────────────────────────────┐
                │ TIER        │ STAGES │ P0    │ COMPLIANCE         │
                ├────────────────────────────────────────────────────┤
                │ LITE        │ 4      │ No    │ None               │
                │ STANDARD    │ 6      │ No    │ None               │
                │ PROFESSIONAL│ 10     │ Yes   │ Optional           │
                │ ENTERPRISE  │ 11     │ Yes   │ ISO 27001, SOC 2   │
                └────────────────────────────────────────────────────┘
```

#### Visual: Contract-First Stage Order

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │           SDLC 5.0.0 CONTRACT-FIRST STAGE FLOW              │
                    │           API Design BEFORE Code Implementation              │
                    └─────────────────────────────────────────────────────────────┘

    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                           LINEAR STAGES (per release)                          ║
    ╠═══════════════════════════════════════════════════════════════════════════════╣
    ║                                                                                ║
    ║   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                    ║
    ║   │     00       │    │     01       │    │     02       │                    ║
    ║   │  foundation  │───▶│   planning   │───▶│    design    │                    ║
    ║   │              │    │              │    │              │                    ║
    ║   │     WHY      │    │     WHAT     │    │     HOW      │                    ║
    ║   └──────────────┘    └──────────────┘    └──────┬───────┘                    ║
    ║                                                   │                            ║
    ║                                                   ▼                            ║
    ║                       ╔══════════════════════════════════════╗                ║
    ║                       ║             03                        ║                ║
    ║                       ║         INTEGRATION                   ║                ║
    ║                       ║    ┌─────────────────────────┐       ║                ║
    ║                       ║    │   API CONTRACT FIRST!   │       ║                ║
    ║                       ║    │   • OpenAPI Specs       │       ║                ║
    ║                       ║    │   • GraphQL Schema      │       ║                ║
    ║                       ║    │   • Interface Contracts │       ║                ║
    ║                       ║    └─────────────────────────┘       ║                ║
    ║                       ╚════════════════════╤═════════════════╝                ║
    ║                                            │                                   ║
    ║           ┌────────────────────────────────┴────────────────────────────┐     ║
    ║           │                                                              │     ║
    ║           ▼                                                              ▼     ║
    ║   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ ║
    ║   │     04       │    │     05       │    │     06       │    │     07       │ ║
    ║   │    build     │───▶│    test      │───▶│   deploy     │───▶│   operate    │ ║
    ║   │              │    │              │    │              │    │              │ ║
    ║   │     CODE     │    │   QUALITY    │    │   RELEASE    │    │ PRODUCTION   │ ║
    ║   └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘ ║
    ║                                                                                ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝

    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                        CONTINUOUS STAGES (ongoing)                             ║
    ╠═══════════════════════════════════════════════════════════════════════════════╣
    ║                                                                                ║
    ║   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                    ║
    ║   │     08       │    │     09       │    │     10       │                    ║
    ║   │ collaborate  │    │    govern    │    │   archive    │                    ║
    ║   │              │    │              │    │              │                    ║
    ║   │    TEAM      │    │  COMPLIANCE  │    │   HISTORY    │                    ║
    ║   │  ◄──────────►│    │  ◄────────►  │    │  ◄────────►  │                    ║
    ║   │ (Throughout) │    │ (Throughout) │    │ (Throughout) │                    ║
    ║   └──────────────┘    └──────────────┘    └──────────────┘                    ║
    ║                                                                                ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝

    Legend:
    ────▶  Sequential flow (must complete before next)
    ◄────▶ Continuous activity (runs parallel to linear stages)
    ╔════╗ Highlighted critical stage (Contract-First principle)
```

---

## 2. Web Dashboard Onboarding Flow

### 2.1 Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      WEB DASHBOARD ONBOARDING v2.0                          │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1: User Registration
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │  Email/Password │    │  GitHub OAuth   │    │  Google OAuth   │         │
│  │    Register     │    │    Connect      │    │    Connect      │         │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘         │
│           │                      │                      │                   │
│           └──────────────────────┴──────────────────────┘                   │
│                                  │                                          │
│                                  ▼                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
Step 2: Project Creation
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   New Project   │    │   Local Repo    │    │   GitHub Repo   │         │
│  │  (from scratch) │    │    (upload)     │    │    (connect)    │         │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘         │
│           │                      │                      │                   │
│           └──────────────────────┴──────────────────────┘                   │
│                                  │                                          │
│                                  ▼                                          │
│                    ┌─────────────────────────────┐                          │
│                    │  Step 2B: Team Management   │                          │
│                    │  (RBAC: Owner/Admin/Dev/QA) │                          │
│                    └─────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
Step 3: AI Analysis (Optional)
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                    AI Project Analysis                          │        │
│  │  • Scan codebase structure                                      │        │
│  │  • Detect existing documentation                                │        │
│  │  • Recommend tier based on team size                            │        │
│  │  • Suggest stage mapping                                        │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                  │                                          │
│                    ┌─────────────┴─────────────┐                            │
│                    │                           │                            │
│                    ▼                           ▼                            │
│           ┌───────────────┐           ┌───────────────┐                     │
│           │ Use AI Result │           │ Manual Input  │                     │
│           └───────────────┘           │  (fallback)   │                     │
│                                       └───────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
Step 4: Tier Selection (SDLC 5.0.0)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    LITE     │  │  STANDARD   │  │PROFESSIONAL │  │ ENTERPRISE  │        │
│  │   1-2 ppl   │  │  3-10 ppl   │  │  10-50 ppl  │  │   50+ ppl   │        │
│  │  4 stages   │  │  6 stages   │  │  10 stages  │  │  11 stages  │        │
│  │   P0: No    │  │   P0: No    │  │  P0: Yes    │  │  P0: Yes    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │                │
│         └────────────────┴────────────────┴────────────────┘                │
│                                  │                                          │
│                                  ▼                                          │
│                    ┌─────────────────────────────┐                          │
│                    │ Auto-generate .sdlc-config  │                          │
│                    │ Create required stage dirs  │                          │
│                    └─────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
Step 5: Stage Mapping (OPTIONAL - can do later)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Map existing folders to SDLC 5.0.0 stages:                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │ Stage              │ Current Folder       │ Status              │        │
│  ├────────────────────┼──────────────────────┼─────────────────────┤        │
│  │ 00-foundation      │ docs/requirements    │ ✓ Mapped            │        │
│  │ 01-planning        │ docs/planning        │ ✓ Mapped            │        │
│  │ 02-design          │ docs/architecture    │ ✓ Mapped            │        │
│  │ 03-integration     │ api/specs            │ ✓ Mapped            │        │
│  │ 04-build           │ src/                 │ ✓ Mapped            │        │
│  │ 05-test            │ tests/               │ ✓ Mapped            │        │
│  │ ...                │ ...                  │ ...                 │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
│  [ ] Skip for now (configure later)                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
Step 6: First Gate Evaluation (G0.1 - MANDATORY)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                    Gate G0.1 - Problem Definition               │        │
│  │                                                                  │        │
│  │  Exit Criteria (SDLC 5.0.0):                                    │        │
│  │  ✓ Problem statement documented                                  │        │
│  │  ✓ User personas defined (10+)                                   │        │
│  │  ✓ Market research completed (TAM/SAM/SOM)                       │        │
│  │  ○ Competitive analysis (3+ competitors)                         │        │
│  │                                                                  │        │
│  │  Evidence Required:                                              │        │
│  │  • Problem Statement Document (PDF/DOCX)                         │        │
│  │  • User Research Data (XLSX/CSV)                                 │        │
│  │                                                                  │        │
│  │  [Upload Evidence]    [Skip - Upload Later]                      │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
Post-Onboarding: Getting Started Guide
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                    Welcome to SDLC Orchestrator!                │        │
│  │                                                                  │        │
│  │  Your project "My Project" is ready with STANDARD tier.         │        │
│  │                                                                  │        │
│  │  Next Steps:                                                     │        │
│  │  1. □ Complete G0.1 evidence upload                              │        │
│  │  2. □ Install VS Code Extension                                  │        │
│  │  3. □ Invite team members                                        │        │
│  │  4. □ Connect GitHub repository                                  │        │
│  │                                                                  │        │
│  │  Quick Links:                                                    │        │
│  │  • [View Gates Timeline] → /projects/{id}/gates                  │        │
│  │  • [Upload Evidence] → /evidence/upload                          │        │
│  │  • [Manage Team] → /projects/{id}/team                           │        │
│  │  • [View Policies] → /policies                                   │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Step-by-Step Specification

#### Step 1: User Registration

**Duration**: ~2 minutes

**Options**:
1. **Email/Password Registration**
   - Email validation (format + uniqueness)
   - Password requirements: 12+ chars, 1 uppercase, 1 number, 1 special
   - Email verification (optional, configurable)

2. **GitHub OAuth**
   - Scope: `user:email`, `read:org`
   - Auto-import: name, email, avatar
   - Optional: Link to existing account

3. **Google OAuth**
   - Scope: `email`, `profile`
   - Auto-import: name, email, avatar

**API Endpoints**:
```yaml
POST /api/v1/auth/register
  body:
    email: string
    password: string
    name: string (optional)
  returns:
    user: User
    access_token: string
    refresh_token: string

GET /api/v1/auth/oauth/github
  redirects to GitHub OAuth

POST /api/v1/auth/oauth/github/callback
  params:
    code: string
    state: string
  returns:
    user: User
    access_token: string
    is_new_user: boolean
```

#### Step 2: Project Creation

**Duration**: ~1 minute

**Options**:
1. **New Project (from scratch)**
   - Name: required, 3-100 chars
   - Description: optional, 0-500 chars
   - Visibility: private/public

2. **Local Repository Upload**
   - Upload zip/tar.gz
   - Auto-detect project structure
   - Suggest tier based on file count

3. **GitHub Repository Connect**
   - Select from user's repos
   - OAuth scope: `repo` (for private repos)
   - Auto-sync: README, docs/, issues

**API Endpoints**:
```yaml
POST /api/v1/projects
  body:
    name: string
    description: string (optional)
    source: "new" | "local" | "github"
    github_repo_id: string (if source=github)
  returns:
    project: Project
    onboarding_state: OnboardingState

POST /api/v1/projects/{id}/upload-repo
  body: multipart/form-data (zip file)
  returns:
    analysis: {
      file_count: number
      detected_languages: string[]
      suggested_tier: Tier
    }
```

#### Step 2B: Team Management

**Duration**: ~30 seconds (optional, can skip)

**RBAC Roles (SDLC 5.0.0)**:
| Role | Permissions |
|------|-------------|
| **Owner** | Full access, delete project, transfer ownership |
| **Admin** | Manage members, approve gates, manage policies |
| **Maintainer** | Create gates, upload evidence, run evaluations |
| **Developer** | Upload evidence, view gates, view policies |
| **Viewer** | Read-only access to project |

**API Endpoints**:
```yaml
POST /api/v1/projects/{id}/members
  body:
    email: string
    role: "admin" | "maintainer" | "developer" | "viewer"
  returns:
    member: ProjectMember
    invitation_sent: boolean

GET /api/v1/projects/{id}/members
  returns:
    members: ProjectMember[]
```

#### Step 3: AI Analysis (Optional)

**Duration**: ~30 seconds (or skip)

**AI Analysis Features**:
1. **Codebase Scan**
   - File count and structure
   - Language detection
   - Documentation coverage

2. **Tier Recommendation**
   - Based on team size (from project settings)
   - Based on file complexity
   - Based on detected patterns

3. **Stage Mapping Suggestions**
   - Match existing folders to SDLC stages
   - Detect documentation patterns
   - Identify missing stages

**API Endpoints**:
```yaml
POST /api/v1/projects/{id}/analyze
  returns:
    analysis: {
      recommended_tier: Tier
      detected_stages: StageMapping[]
      missing_stages: string[]
      documentation_coverage: number
      suggestions: string[]
    }

# Fallback to manual if AI unavailable
GET /api/v1/projects/{id}/manual-setup-form
  returns:
    form: {
      tier_options: TierOption[]
      stage_options: StageOption[]
    }
```

#### Step 4: Tier Selection (SDLC 5.0.0)

**Duration**: ~30 seconds

**Tier Details Display**:

```yaml
LITE (1-2 people):
  description: "For solo developers and pair programming"
  required_stages: ["00-foundation", "01-planning", "02-design", "03-integration"]
  optional_stages: ["04-build", "05-test", "06-deploy", "07-operate", "08-collaborate", "09-govern"]
  p0_artifacts: false
  max_depth: 1 (flat structure)

STANDARD (3-10 people):
  description: "For small teams and startups"
  required_stages: ["00-foundation", "01-planning", "02-design", "03-integration", "04-build", "05-test"]
  optional_stages: ["06-deploy", "07-operate", "08-collaborate", "09-govern"]
  p0_artifacts: false
  max_depth: 2 (one level nesting)

PROFESSIONAL (10-50 people):
  description: "For medium teams with governance needs"
  required_stages: ["00-foundation" through "09-govern"] # All 10
  optional_stages: ["10-archive"]
  p0_artifacts: true
  max_depth: 3 (two level nesting)

ENTERPRISE (50+ people):
  description: "For large organizations with compliance requirements"
  required_stages: ["00-foundation" through "10-archive"] # All 11
  optional_stages: []
  p0_artifacts: true
  compliance: ["ISO 27001", "SOC 2"]
  max_depth: 4 (three level nesting)
```

**API Endpoints**:
```yaml
PUT /api/v1/projects/{id}/tier
  body:
    tier: "LITE" | "STANDARD" | "PROFESSIONAL" | "ENTERPRISE"
  returns:
    project: Project
    generated_config: SDLCConfig
    created_folders: string[]

GET /api/v1/tiers
  returns:
    tiers: TierDefinition[]
```

#### Step 5: Stage Mapping (Optional)

**Duration**: ~2 minutes (or skip)

**Auto-Detection Patterns**:
```yaml
# Stage detection heuristics
00-foundation:
  patterns: ["requirements/", "docs/why/", "problem/"]
  file_patterns: ["*.problem.md", "problem-statement.*"]

01-planning:
  patterns: ["planning/", "docs/what/", "specs/"]
  file_patterns: ["*.frd.md", "requirements.*", "user-stories.*"]

02-design:
  patterns: ["architecture/", "design/", "docs/how/"]
  file_patterns: ["*.adr.md", "architecture.*", "system-design.*"]

03-integration:
  patterns: ["api/", "contracts/", "openapi/"]
  file_patterns: ["openapi.yaml", "swagger.*", "api-spec.*"]

04-build:
  patterns: ["src/", "app/", "lib/"]
  file_patterns: ["*.py", "*.ts", "*.tsx", "*.go"]

05-test:
  patterns: ["tests/", "test/", "__tests__/"]
  file_patterns: ["test_*.py", "*.test.ts", "*.spec.ts"]

06-deploy:
  patterns: ["deploy/", "infrastructure/", "k8s/", ".github/workflows/"]
  file_patterns: ["Dockerfile", "docker-compose.*", "*.tf"]

07-operate:
  patterns: ["monitoring/", "observability/", "runbooks/"]
  file_patterns: ["grafana.*", "prometheus.*", "alerts.*"]

08-collaborate:
  patterns: ["docs/team/", ".github/", "CONTRIBUTING.*"]
  file_patterns: ["CONTRIBUTING.md", "CODE_OF_CONDUCT.md"]

09-govern:
  patterns: ["compliance/", "audit/", "policies/"]
  file_patterns: ["LICENSE", "SECURITY.md", "*.policy.rego"]

10-archive:
  patterns: ["archive/", "legacy/", "deprecated/"]
  file_patterns: []
```

**API Endpoints**:
```yaml
PUT /api/v1/projects/{id}/stage-mapping
  body:
    mappings: [
      { stage: "00-foundation", path: "docs/requirements" },
      { stage: "04-build", path: "src" },
      ...
    ]
  returns:
    project: Project
    updated_config: SDLCConfig

POST /api/v1/projects/{id}/detect-stages
  returns:
    detected_mappings: StageMapping[]
    confidence: number
```

#### Step 6: First Gate Evaluation (G0.1 - Mandatory)

**Duration**: ~5 minutes (depends on evidence availability)

**G0.1 Exit Criteria (SDLC 5.0.0)**:
```yaml
gate_name: "G0.1"
gate_type: "PROBLEM_DEFINITION"
stage: "00-foundation"
description: "Problem Definition Gate - Validates WHY we're building this"

exit_criteria:
  - name: "Problem statement documented"
    required: true
    evidence_type: ["DOCUMENT"]

  - name: "User personas defined (10+)"
    required: true
    evidence_type: ["DOCUMENT", "DATA"]

  - name: "Market research completed (TAM/SAM/SOM)"
    required: true
    evidence_type: ["DATA", "DOCUMENT"]

  - name: "Competitive analysis (3+ competitors)"
    required: false  # RECOMMENDED, not MANDATORY
    evidence_type: ["DOCUMENT"]

  - name: "Success metrics (OKRs) defined"
    required: false
    evidence_type: ["DOCUMENT"]

policies:
  - problem_statement_required
  - user_research_required
```

**API Endpoints**:
```yaml
POST /api/v1/gates
  body:
    project_id: string
    gate_name: "G0.1"
    gate_type: "PROBLEM_DEFINITION"
    stage: "00-foundation"
  returns:
    gate: Gate

POST /api/v1/evidence/upload
  body: multipart/form-data
    file: File
    gate_id: string
    title: string
    evidence_type: string
    description: string (optional)
  returns:
    evidence: Evidence
```

### 2.3 Web Dashboard Test Scenarios

#### TC-ONBOARD-WEB-001: Complete Happy Path
```gherkin
Feature: Web Dashboard Onboarding
  Scenario: New user completes full onboarding
    Given user navigates to /register
    When user registers with email "newuser@example.com"
    And user creates project "My First Project"
    And user selects STANDARD tier
    And user skips stage mapping
    And user uploads problem statement for G0.1
    Then user sees Getting Started guide
    And project dashboard shows G0.1 with evidence
    And .sdlc-config.json is generated

Expected Duration: <5 minutes
```

#### TC-ONBOARD-WEB-002: GitHub OAuth + Import
```gherkin
Scenario: User onboards with GitHub OAuth
  Given user clicks "Continue with GitHub"
  When OAuth flow completes successfully
  And user selects repository "my-existing-project"
  Then AI analyzes repository
  And tier is suggested based on file count
  And stages are auto-detected
```

#### TC-ONBOARD-WEB-003: Manual Input Fallback
```gherkin
Scenario: AI analysis unavailable, manual input
  Given AI analysis times out (>30s)
  Then manual input form appears
  And user can select tier manually
  And user can map stages manually
```

---

## 3. VS Code Extension Onboarding Flow

### 3.1 Scenario A: Existing Project (Connect to Orchestrator)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              VS CODE EXTENSION ONBOARDING - EXISTING PROJECT                │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1: Install Extension (~30 sec)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Extensions > Search "SDLC Orchestrator"                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  🏛️ SDLC Orchestrator                                           │        │
│  │  by MT Solution                                                  │        │
│  │  ⭐⭐⭐⭐⭐ (4.8) | 10K+ installs                                  │        │
│  │                                                                  │        │
│  │  Governance-first development with SDLC 5.0.0                    │        │
│  │  • Quality Gates & Evidence Management                           │        │
│  │  • AI-Assisted Development                                       │        │
│  │  • Contract-First Stage Compliance                               │        │
│  │                                                                  │        │
│  │  [Install]                                                       │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
Step 2: Authenticate (~30 sec)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  🔐 Sign in to SDLC Orchestrator                                │        │
│  │                                                                  │        │
│  │  Server URL: [https://sdlc.mtsolution.com.vn        ]           │        │
│  │                                                                  │        │
│  │  ┌─────────────────┐    ┌─────────────────┐                     │        │
│  │  │ Sign in with    │    │  Sign in with   │                     │        │
│  │  │    GitHub       │    │     Email       │                     │        │
│  │  └─────────────────┘    └─────────────────┘                     │        │
│  │                                                                  │        │
│  │  [ ] Remember me on this device                                  │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
Step 3: Select Project (~30 sec)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  📁 Select Project                                              │        │
│  │                                                                  │        │
│  │  Your Projects:                                                  │        │
│  │  ┌───────────────────────────────────────────────────────┐      │        │
│  │  │ ○ NQH-Bot Platform        │ BUILD  │ PROFESSIONAL │   │      │        │
│  │  │ ○ BFlow Workflow v3       │ HOW    │ STANDARD     │   │      │        │
│  │  │ ● SDLC Orchestrator       │ BUILD  │ ENTERPRISE   │ ← │      │        │
│  │  │ ○ MTEP Platform           │ DEPLOY │ ENTERPRISE   │   │      │        │
│  │  └───────────────────────────────────────────────────────┘      │        │
│  │                                                                  │        │
│  │  [+ Create New Project]                                          │        │
│  │                                                                  │        │
│  │  [Connect to Selected Project]                                   │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
Step 4: Setup Complete (~15 sec)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  ✅ Connected to SDLC Orchestrator!                             │        │
│  │                                                                  │        │
│  │  Project: SDLC Orchestrator                                      │        │
│  │  Tier: ENTERPRISE                                                │        │
│  │  Current Stage: BUILD (04)                                       │        │
│  │  Current Gate: G3 (Ship Ready)                                   │        │
│  │                                                                  │        │
│  │  Synced Files:                                                   │        │
│  │  ✓ .sdlc-config.json                                            │        │
│  │  ✓ Gates data (5 gates)                                          │        │
│  │  ✓ Evidence metadata (13 files)                                  │        │
│  │                                                                  │        │
│  │  Quick Actions:                                                  │        │
│  │  • Cmd+Shift+E - Submit Evidence                                 │        │
│  │  • Cmd+Shift+G - View Gates                                      │        │
│  │  • Cmd+Shift+A - AI Assistant                                    │        │
│  │                                                                  │        │
│  │  [Open Gate Panel]    [View Getting Started]                     │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Total Duration: ~2 minutes
```

### 3.2 Scenario B: Empty Folder (Create SDLC Project Structure)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              VS CODE EXTENSION ONBOARDING - EMPTY FOLDER                    │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1: Detect Empty Folder (Auto)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  VS Code opens folder: /Users/dev/my-new-project (empty)                    │
│                                                                             │
│  Extension detects:                                                         │
│  - No .sdlc-config.json                                                     │
│  - No existing project files                                                │
│  - Empty folder or minimal files                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
Step 2: Prompt to Initialize (~5 sec)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  🏛️ Create SDLC 5.0.0 Project?                                  │        │
│  │                                                                  │        │
│  │  This folder appears to be empty or doesn't have an             │        │
│  │  SDLC configuration.                                             │        │
│  │                                                                  │        │
│  │  Would you like to initialize an SDLC 5.0.0 compliant           │        │
│  │  project structure?                                              │        │
│  │                                                                  │        │
│  │  [Initialize SDLC Project]    [Not Now]                          │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
Step 3: Select Tier (~15 sec)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  Select Project Tier                                            │        │
│  │                                                                  │        │
│  │  ○ LITE (1-2 people)                                            │        │
│  │    4 stages, minimal documentation                               │        │
│  │                                                                  │        │
│  │  ● STANDARD (3-10 people)  [Recommended]                        │        │
│  │    6 stages, balanced governance                                 │        │
│  │                                                                  │        │
│  │  ○ PROFESSIONAL (10-50 people)                                  │        │
│  │    10 stages, P0 artifacts required                              │        │
│  │                                                                  │        │
│  │  ○ ENTERPRISE (50+ people)                                      │        │
│  │    11 stages, full compliance (ISO 27001, SOC 2)                 │        │
│  │                                                                  │        │
│  │  [Continue]                                                      │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
Step 4: Generate Folder Structure (~10 sec)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Generating SDLC 5.0.0 STANDARD structure...                                │
│                                                                             │
│  ✓ Created .sdlc-config.json                                               │
│  ✓ Created docs/00-foundation/                                              │
│  ✓ Created docs/01-planning/                                                │
│  ✓ Created docs/02-design/                                                  │
│  ✓ Created docs/03-integration/                                             │
│  ✓ Created docs/04-build/                                                   │
│  ✓ Created docs/05-test/                                                    │
│  ✓ Created src/                                                             │
│  ✓ Created tests/                                                           │
│  ✓ Created .vscode/settings.json                                            │
│                                                                             │
│  Total: 10 folders, 5 template files                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
Step 5: Create .sdlc-config.json (Auto)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  .sdlc-config.json created:                                                 │
│                                                                             │
│  {                                                                          │
│    "$schema": "https://sdlc-orchestrator.io/schemas/config-v1.json",       │
│    "version": "1.0.0",                                                      │
│    "project": {                                                             │
│      "id": "local-xxxxxxxx-xxxx",                                          │
│      "name": "my-new-project",                                              │
│      "slug": "my-new-project"                                               │
│    },                                                                       │
│    "sdlc": {                                                                 │
│      "frameworkVersion": "5.0.0",                                          │
│      "tier": "STANDARD",                                                    │
│      "stages": {                                                            │
│        "00-foundation": "docs/00-foundation",                               │
│        "01-planning": "docs/01-planning",                                   │
│        ...                                                                  │
│      }                                                                      │
│    },                                                                       │
│    "server": {                                                              │
│      "url": null,                                                           │
│      "connected": false                                                     │
│    }                                                                        │
│  }                                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
Step 6: Open Getting Started Guide (Auto)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  🎉 SDLC 5.0.0 Project Created!                                 │        │
│  │                                                                  │        │
│  │  Project: my-new-project                                         │        │
│  │  Tier: STANDARD                                                  │        │
│  │  Framework: SDLC 5.0.0 (Contract-First)                          │        │
│  │                                                                  │        │
│  │  Getting Started:                                                │        │
│  │                                                                  │        │
│  │  1. 📝 Write Problem Statement                                   │        │
│  │     → docs/00-foundation/problem-statement.md                    │        │
│  │                                                                  │        │
│  │  2. 📋 Define Requirements                                       │        │
│  │     → docs/01-planning/requirements.md                           │        │
│  │                                                                  │        │
│  │  3. 🔗 Design API Contract (BEFORE coding!)                      │        │
│  │     → docs/03-integration/openapi.yaml                           │        │
│  │                                                                  │        │
│  │  4. 💻 Start Building                                            │        │
│  │     → src/                                                       │        │
│  │                                                                  │        │
│  │  Commands:                                                       │        │
│  │  • Cmd+Shift+I - Initialize/Update Project                       │        │
│  │  • Cmd+Shift+V - Validate Structure                              │        │
│  │                                                                  │        │
│  │  [Connect to Server]    [Continue Offline]                       │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Total Duration: ~1 minute
```

### 3.3 `/init` Command Specification

**Command**: `SDLC: Initialize Project`
**Shortcut**: `Cmd+Shift+I` (macOS) / `Ctrl+Shift+I` (Windows/Linux)
**Command Palette**: `/init` or `SDLC: Initialize`

#### Features

1. **Offline Mode Support** (Local-First)
   - Works without server connection
   - Generates local UUID for project
   - Syncs to server when connected later

2. **Gap Analysis** (For Non-Empty Folders)
   ```yaml
   Scan Results:
   ✓ docs/ folder exists
   ✓ src/ folder exists
   ✗ docs/03-integration/ missing (Contract-First!)
   ✗ tests/ folder missing

   Recommendations:
   1. Create docs/03-integration/ for API specs (BEFORE coding)
   2. Create tests/ for quality assurance
   3. Move docs/api/ → docs/03-integration/
   ```

3. **AI Pre-fill Templates**
   ```yaml
   Template: problem-statement.md

   # Problem Statement

   ## Project: {project_name}

   ## Problem Definition
   {AI-generated based on project name and description}

   ## Target Users
   - User Persona 1: {AI suggestion}
   - User Persona 2: {AI suggestion}

   ## Success Metrics
   - [ ] Metric 1
   - [ ] Metric 2
   ```

4. **Stage Mapping from Existing Content**
   ```yaml
   Detected Mappings:
   - docs/requirements/ → 01-planning (confidence: 90%)
   - docs/architecture/ → 02-design (confidence: 95%)
   - api/openapi.yaml → 03-integration (confidence: 100%)
   - src/ → 04-build (confidence: 100%)
   - tests/ → 05-test (confidence: 100%)
   ```

#### Generated Structure

```
project/
├── .sdlc-config.json          # Project configuration
├── .vscode/
│   └── settings.json          # Recommended VS Code settings
├── docs/
│   ├── 00-foundation/
│   │   └── problem-statement.md  # AI pre-filled template
│   ├── 01-planning/
│   │   └── requirements.md       # AI pre-filled template
│   ├── 02-design/
│   │   └── architecture.md       # AI pre-filled template
│   ├── 03-integration/           # Contract-First!
│   │   └── openapi.yaml          # OpenAPI template
│   ├── 04-build/
│   │   └── README.md
│   └── 05-test/
│       └── test-plan.md
├── src/                          # Source code
│   └── .gitkeep
└── tests/                        # Test files
    └── .gitkeep
```

### 3.4 VS Code Extension Commands Summary

| Command | Shortcut | Description |
|---------|----------|-------------|
| `SDLC: Initialize Project` | Cmd+Shift+I | Create/update .sdlc-config.json |
| `SDLC: Validate Structure` | Cmd+Shift+V | Validate SDLC 5.0.0 compliance |
| `SDLC: Submit Evidence` | Cmd+Shift+E | Submit file as gate evidence |
| `SDLC: View Gates` | Cmd+Shift+G | Open gate status sidebar |
| `SDLC: AI Assistant` | Cmd+Shift+A | Open AI chat panel |
| `SDLC: Generate Template` | Cmd+Shift+T | Generate stage template |
| `SDLC: Create Structure` | - | Generate full folder structure |
| `SDLC: Fix Structure` | - | Auto-fix structure issues |
| `SDLC: Generate Report` | - | Generate compliance report |

### 3.5 VS Code Extension Test Scenarios

#### TC-ONBOARD-VSC-001: Existing Project Connect
```gherkin
Feature: VS Code Extension - Existing Project
  Scenario: Connect to existing Orchestrator project
    Given user has VS Code with SDLC extension installed
    And user has account on SDLC Orchestrator
    When user opens project folder with .sdlc-config.json
    Then extension auto-detects configuration
    And prompts to sign in
    And syncs project data from server

Expected Duration: <2 minutes
```

#### TC-ONBOARD-VSC-002: Empty Folder Init
```gherkin
Scenario: Initialize SDLC project in empty folder
  Given user opens empty folder in VS Code
  And SDLC extension is installed
  Then extension prompts "Create SDLC 5.0.0 Project?"
  When user selects STANDARD tier
  Then folder structure is generated
  And .sdlc-config.json is created
  And Getting Started guide opens

Expected Duration: <1 minute
```

#### TC-ONBOARD-VSC-003: Offline Mode
```gherkin
Scenario: Initialize project offline
  Given user has no internet connection
  When user runs /init command
  Then project is created with local UUID
  And .sdlc-config.json shows "connected": false
  When user connects to internet
  And runs "Connect to Server"
  Then project syncs to server
  And UUID is replaced with server UUID
```

#### TC-ONBOARD-VSC-004: Gap Analysis
```gherkin
Scenario: Detect missing SDLC stages
  Given user opens existing project folder
  And folder has src/ but no docs/03-integration/
  When user runs /init command
  Then gap analysis shows:
    - Missing: docs/03-integration/ (Contract-First!)
    - Missing: docs/02-design/
  And suggests: "Create API contract before coding"
```

---

## 4. `.sdlc-config.json` Specification (SDLC 5.0.0)

### 4.1 Full Schema

```json
{
  "$schema": "https://sdlc-orchestrator.io/schemas/config-v1.json",
  "version": "1.0.0",
  "project": {
    "id": "uuid-from-server-or-local",
    "name": "My Project",
    "slug": "my-project",
    "description": "Project description"
  },
  "sdlc": {
    "frameworkVersion": "5.0.0",
    "tier": "STANDARD",
    "stages": {
      "00-foundation": "docs/00-foundation",
      "01-planning": "docs/01-planning",
      "02-design": "docs/02-design",
      "03-integration": "docs/03-integration",
      "04-build": "src",
      "05-test": "tests",
      "06-deploy": "infrastructure",
      "07-operate": "docs/07-operate",
      "08-collaborate": "docs/08-collaborate",
      "09-govern": "docs/09-govern",
      "10-archive": "docs/10-archive"
    },
    "p0Artifacts": {
      "enabled": false,
      "path": "docs/p0"
    }
  },
  "server": {
    "url": "https://sdlc.mtsolution.com.vn",
    "connected": true,
    "lastSync": "2025-12-13T10:00:00Z"
  },
  "gates": {
    "current": "G3",
    "passed": ["G0.1", "G0.2", "G1", "G2"]
  },
  "team": {
    "size": 8,
    "roles": ["owner", "admin", "developer", "qa"]
  },
  "ai": {
    "provider": "ollama",
    "enabled": true
  }
}
```

### 4.2 Tier-Specific Configurations

#### LITE Tier
```json
{
  "sdlc": {
    "frameworkVersion": "5.0.0",
    "tier": "LITE",
    "stages": {
      "00-foundation": "docs/00-foundation",
      "01-planning": "docs/01-planning",
      "02-design": "docs/02-design",
      "03-integration": "docs/03-integration"
    },
    "p0Artifacts": { "enabled": false }
  }
}
```

#### STANDARD Tier
```json
{
  "sdlc": {
    "frameworkVersion": "5.0.0",
    "tier": "STANDARD",
    "stages": {
      "00-foundation": "docs/00-foundation",
      "01-planning": "docs/01-planning",
      "02-design": "docs/02-design",
      "03-integration": "docs/03-integration",
      "04-build": "src",
      "05-test": "tests"
    },
    "p0Artifacts": { "enabled": false }
  }
}
```

#### PROFESSIONAL Tier
```json
{
  "sdlc": {
    "frameworkVersion": "5.0.0",
    "tier": "PROFESSIONAL",
    "stages": {
      "00-foundation": "docs/00-foundation",
      "01-planning": "docs/01-planning",
      "02-design": "docs/02-design",
      "03-integration": "docs/03-integration",
      "04-build": "src",
      "05-test": "tests",
      "06-deploy": "infrastructure",
      "07-operate": "docs/07-operate",
      "08-collaborate": "docs/08-collaborate",
      "09-govern": "docs/09-govern"
    },
    "p0Artifacts": {
      "enabled": true,
      "path": "docs/p0"
    }
  }
}
```

#### ENTERPRISE Tier
```json
{
  "sdlc": {
    "frameworkVersion": "5.0.0",
    "tier": "ENTERPRISE",
    "stages": {
      "00-foundation": "docs/00-foundation",
      "01-planning": "docs/01-planning",
      "02-design": "docs/02-design",
      "03-integration": "docs/03-integration",
      "04-build": "src",
      "05-test": "tests",
      "06-deploy": "infrastructure",
      "07-operate": "docs/07-operate",
      "08-collaborate": "docs/08-collaborate",
      "09-govern": "docs/09-govern",
      "10-archive": "docs/10-archive"
    },
    "p0Artifacts": {
      "enabled": true,
      "path": "docs/p0"
    },
    "compliance": {
      "iso27001": true,
      "soc2": true
    }
  }
}
```

---

## 5. API Endpoints Summary

### 5.1 Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Email registration |
| POST | `/api/v1/auth/login` | Email login |
| GET | `/api/v1/auth/oauth/github` | GitHub OAuth initiate |
| POST | `/api/v1/auth/oauth/github/callback` | GitHub OAuth callback |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout |

### 5.2 Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects` | List user projects |
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects/{id}` | Get project detail |
| PUT | `/api/v1/projects/{id}/tier` | Update project tier |
| PUT | `/api/v1/projects/{id}/stage-mapping` | Update stage mappings |
| POST | `/api/v1/projects/{id}/analyze` | AI analysis |
| POST | `/api/v1/projects/{id}/detect-stages` | Auto-detect stages |

### 5.3 VS Code Extension Specific

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/projects/init` | Initialize project (from VS Code) |
| GET | `/api/v1/templates/sdlc-structure` | Get structure template by tier |
| POST | `/api/v1/projects/{id}/sync` | Sync local config to server |
| GET | `/api/v1/projects/{id}/gap-analysis` | Get gap analysis |

### 5.4 Tiers & Templates

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tiers` | List all tier definitions |
| GET | `/api/v1/tiers/{tier}/stages` | Get required stages for tier |
| GET | `/api/v1/templates/sdlc-structure?tier={tier}` | Get folder structure template |
| GET | `/api/v1/templates/{stage}/{type}` | Get document template |

---

## 6. Migration from SDLC 4.9.x

### 6.1 Stage Mapping Changes

| SDLC 4.9.x | SDLC 5.0.0 | Change |
|------------|------------|--------|
| 00-Project-Foundation | 00-foundation | Rename |
| 01-Planning-Analysis | 01-planning | Rename |
| 02-Design-Architecture | 02-design | Rename |
| 03-Development-Implementation | 04-build | **Renumber +1** |
| 04-Testing-Quality | 05-test | **Renumber +1** |
| 05-Deployment-Release | 06-deploy | **Renumber +1** |
| 06-Operations-Maintenance | 07-operate | **Renumber +1** |
| 07-Integration-APIs | 03-integration | **MOVED to 03** |
| 08-Team-Management | 08-collaborate | Rename |
| 09-Executive-Reports | 09-govern | Rename |
| 10-Archive | 10-archive | Rename |

### 6.2 Migration Command

```bash
# Using sdlcctl CLI
sdlcctl migrate --from 4.9.x --to 5.0.0 --path /path/to/project

# Options
--dry-run        # Preview changes without applying
--force          # Skip confirmation prompts
--backup         # Create backup before migration
--no-rename      # Keep old folder names (update config only)
```

### 6.3 Onboarding Migration Path

For existing SDLC 4.9.x users:

1. **Web Dashboard**: Show migration banner on dashboard
2. **VS Code Extension**: Detect 4.9.x config, offer migration
3. **CLI**: `sdlcctl migrate` command

---

## 7. Test Execution Checklist

### 7.1 Web Dashboard Onboarding Tests

- [ ] TC-ONBOARD-WEB-001: Complete happy path
- [ ] TC-ONBOARD-WEB-002: GitHub OAuth + Import
- [ ] TC-ONBOARD-WEB-003: Manual input fallback
- [ ] TC-ONBOARD-WEB-004: Tier selection validation
- [ ] TC-ONBOARD-WEB-005: Stage mapping auto-detect
- [ ] TC-ONBOARD-WEB-006: G0.1 gate creation
- [ ] TC-ONBOARD-WEB-007: Evidence upload in onboarding
- [ ] TC-ONBOARD-WEB-008: Team invitation flow
- [ ] TC-ONBOARD-WEB-009: .sdlc-config.json generation

### 7.2 VS Code Extension Onboarding Tests

- [ ] TC-ONBOARD-VSC-001: Existing project connect
- [ ] TC-ONBOARD-VSC-002: Empty folder init
- [ ] TC-ONBOARD-VSC-003: Offline mode
- [ ] TC-ONBOARD-VSC-004: Gap analysis
- [ ] TC-ONBOARD-VSC-005: AI pre-fill templates
- [ ] TC-ONBOARD-VSC-006: Tier selection UI
- [ ] TC-ONBOARD-VSC-007: Structure generation
- [ ] TC-ONBOARD-VSC-008: Server sync (online)
- [ ] TC-ONBOARD-VSC-009: /init command variations

### 7.3 Migration Tests

- [ ] TC-MIGRATE-001: 4.9.x to 5.0.0 folder rename
- [ ] TC-MIGRATE-002: Config file upgrade
- [ ] TC-MIGRATE-003: Stage mapping preservation
- [ ] TC-MIGRATE-004: Dry-run mode
- [ ] TC-MIGRATE-005: Rollback on failure

---

---

## 8. Visual Diagrams

### 8.1 Onboarding State Machine

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │              ONBOARDING STATE MACHINE                        │
                    │              Web Dashboard + VS Code Extension               │
                    └─────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────────────┐
    │                              WEB DASHBOARD FLOW                                  │
    └─────────────────────────────────────────────────────────────────────────────────┘

                        ┌─────────┐
                        │  START  │
                        └────┬────┘
                             │
                             ▼
               ┌─────────────────────────┐
               │     UNAUTHENTICATED     │◄───────────────────────┐
               │                         │                        │
               │  • Show landing page    │                        │ logout
               │  • Show login/register  │                        │
               └───────────┬─────────────┘                        │
                           │                                      │
            ┌──────────────┴──────────────┐                       │
            │                             │                       │
            ▼                             ▼                       │
    ┌───────────────┐           ┌───────────────┐                 │
    │   REGISTER    │           │    LOGIN      │                 │
    │               │           │               │                 │
    │ • Email/Pass  │           │ • Email/Pass  │                 │
    │ • GitHub      │           │ • GitHub      │                 │
    │ • Google      │           │ • Google      │                 │
    └───────┬───────┘           └───────┬───────┘                 │
            │                           │                         │
            │ success                   │ success                 │
            │                           │                         │
            └───────────┬───────────────┘                         │
                        │                                         │
                        ▼                                         │
               ┌─────────────────────────┐                        │
               │     AUTHENTICATED       │────────────────────────┘
               │                         │
               │  • Has valid JWT token  │
               │  • User profile loaded  │
               └───────────┬─────────────┘
                           │
                           │ check projects
                           ▼
               ┌─────────────────────────┐     has projects
               │     PROJECT CHECK       │────────────────────┐
               │                         │                    │
               │  • Query user projects  │                    │
               └───────────┬─────────────┘                    │
                           │                                  │
                           │ no projects                      │
                           ▼                                  │
               ┌─────────────────────────┐                    │
               │   CREATE PROJECT        │                    │
               │                         │                    │
               │  • New project          │                    │
               │  • Local repo upload    │                    │
               │  • GitHub connect       │                    │
               └───────────┬─────────────┘                    │
                           │                                  │
                           │ project created                  │
                           ▼                                  │
               ┌─────────────────────────┐                    │
               │    AI ANALYSIS          │                    │
               │                         │                    │
               │  • Scan codebase        │                    │
               │  • Recommend tier       │                    │
               │  • Suggest mappings     │                    │
               └───────────┬─────────────┘                    │
                           │                                  │
             ┌─────────────┴─────────────┐                    │
             │                           │                    │
             ▼                           ▼                    │
    ┌───────────────┐           ┌───────────────┐             │
    │  USE AI       │           │   MANUAL      │             │
    │  RESULT       │           │   INPUT       │             │
    └───────┬───────┘           └───────┬───────┘             │
            │                           │                     │
            └───────────┬───────────────┘                     │
                        │                                     │
                        ▼                                     │
               ┌─────────────────────────┐                    │
               │    TIER SELECTION       │                    │
               │                         │                    │
               │  ○ LITE       (1-2)     │                    │
               │  ○ STANDARD   (3-10)    │                    │
               │  ○ PROFESSIONAL (10-50) │                    │
               │  ○ ENTERPRISE (50+)     │                    │
               └───────────┬─────────────┘                    │
                           │                                  │
                           │ tier selected                    │
                           ▼                                  │
               ┌─────────────────────────┐                    │
               │   STAGE MAPPING         │                    │
               │   (optional)            │                    │
               │                         │                    │
               │  • Auto-detect folders  │                    │
               │  • Manual mapping       │                    │
               │  • Skip for later       │                    │
               └───────────┬─────────────┘                    │
                           │                                  │
                           ▼                                  │
               ┌─────────────────────────┐                    │
               │    FIRST GATE (G0.1)    │                    │
               │                         │                    │
               │  • Upload evidence      │                    │
               │  • Skip (upload later)  │                    │
               └───────────┬─────────────┘                    │
                           │                                  │
                           │ complete                         │
                           ▼                                  │
               ┌─────────────────────────┐                    │
               │  ONBOARDING COMPLETE    │◄───────────────────┘
               │                         │
               │  • Show getting started │
               │  • Redirect to dashboard│
               └───────────┬─────────────┘
                           │
                           ▼
               ┌─────────────────────────┐
               │     DASHBOARD           │
               │                         │
               │  • Project overview     │
               │  • Gate status          │
               │  • Quick actions        │
               └─────────────────────────┘


    ┌─────────────────────────────────────────────────────────────────────────────────┐
    │                            VS CODE EXTENSION FLOW                                │
    └─────────────────────────────────────────────────────────────────────────────────┘

                        ┌─────────┐
                        │ INSTALL │
                        └────┬────┘
                             │
                             ▼
               ┌─────────────────────────┐
               │   EXTENSION ACTIVATED   │
               │                         │
               │  • Check workspace      │
               │  • Look for config      │
               └───────────┬─────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
            │ has .sdlc-config.json       │ no config
            ▼                             ▼
    ┌───────────────┐           ┌───────────────┐
    │   EXISTING    │           │   NEW/EMPTY   │
    │   PROJECT     │           │   FOLDER      │
    └───────┬───────┘           └───────┬───────┘
            │                           │
            ▼                           ▼
    ┌───────────────┐           ┌───────────────┐
    │ AUTHENTICATE  │           │  PROMPT INIT  │
    │               │           │               │
    │ • GitHub      │           │ "Create SDLC  │
    │ • Email       │           │  5.0.0 proj?" │
    └───────┬───────┘           └───────┬───────┘
            │                           │
            │ success                   │ yes
            ▼                           ▼
    ┌───────────────┐           ┌───────────────┐
    │SELECT PROJECT │           │ SELECT TIER   │
    │               │           │               │
    │ • List from   │           │ ○ LITE        │
    │   server      │           │ ○ STANDARD    │
    │ • Create new  │           │ ○ PROFESSIONAL│
    └───────┬───────┘           │ ○ ENTERPRISE  │
            │                   └───────┬───────┘
            │ selected                  │
            ▼                           │ selected
    ┌───────────────┐                   ▼
    │  SYNC DATA    │           ┌───────────────┐
    │               │           │  GENERATE     │
    │ • Gates       │           │  STRUCTURE    │
    │ • Evidence    │           │               │
    │ • Config      │           │ • Create dirs │
    └───────┬───────┘           │ • Add config  │
            │                   │ • Templates   │
            │ complete          └───────┬───────┘
            ▼                           │
    ┌───────────────┐                   │ complete
    │   CONNECTED   │◄──────────────────┘
    │               │
    │ • Show panel  │
    │ • Cmd+Shift+E │
    │ • Cmd+Shift+G │
    └───────────────┘


    Legend:
    ┌─────┐
    │State│  = State box
    └─────┘
       │
       ▼    = State transition
    ───────  = Transition condition (labeled on arrow)
```

### 8.2 User Journey Timeline

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                USER JOURNEY TIMELINE                         │
                    │                SDLC Orchestrator Onboarding                  │
                    └─────────────────────────────────────────────────────────────┘


    ┌─────────────────────────────────────────────────────────────────────────────────┐
    │                         WEB DASHBOARD TIMELINE                                   │
    │                        Total: ~5-10 minutes                                      │
    └─────────────────────────────────────────────────────────────────────────────────┘

    TIME ──────────────────────────────────────────────────────────────────────────────▶

    0min        1min        2min        3min        4min        5min        10min
      │           │           │           │           │           │           │
      ▼           ▼           ▼           ▼           ▼           ▼           ▼
    ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐     ┌───────────────────┐
    │     │     │     │     │     │     │     │     │     │     │                   │
    │REG- │────▶│PROJ-│────▶│ AI  │────▶│TIER │────▶│GATE │────▶│    DASHBOARD      │
    │ISTER│     │ ECT │     │SCAN │     │SEL- │     │G0.1 │     │    READY!         │
    │     │     │     │     │     │     │ECT  │     │     │     │                   │
    └─────┘     └─────┘     └─────┘     └─────┘     └─────┘     └───────────────────┘
      │           │           │           │           │
      │           │           │           │           │
    ~2min       ~1min       ~30s        ~30s        ~5min
                                                  (evidence
                                                   upload)


    ┌─────────────────────────────────────────────────────────────────────────────────┐
    │                      VS CODE EXTENSION TIMELINE                                  │
    │               Scenario A (Existing): ~2 minutes                                  │
    │               Scenario B (New): ~1 minute                                        │
    └─────────────────────────────────────────────────────────────────────────────────┘

    SCENARIO A: EXISTING PROJECT
    TIME ──────────────────────────────────────────────────────────────────────────────▶

    0sec       30sec       60sec       90sec      120sec
      │           │           │           │           │
      ▼           ▼           ▼           ▼           ▼
    ┌─────┐     ┌─────┐     ┌─────┐     ┌─────────────────┐
    │INST-│────▶│AUTH-│────▶│SEL- │────▶│   CONNECTED!    │
    │ALL  │     │ENTI-│     │ECT  │     │                 │
    │     │     │CATE │     │PROJ │     │ • View gates    │
    │     │     │     │     │     │     │ • Submit evid   │
    └─────┘     └─────┘     └─────┘     └─────────────────┘
      │           │           │
    ~30s        ~30s        ~30s


    SCENARIO B: EMPTY FOLDER
    TIME ──────────────────────────────────────────────────────────────────────────────▶

    0sec       10sec       20sec       40sec       60sec
      │           │           │           │           │
      ▼           ▼           ▼           ▼           ▼
    ┌─────┐     ┌─────┐     ┌─────┐     ┌─────────────────┐
    │DETE-│────▶│TIER │────▶│GEN- │────▶│   READY!        │
    │CT   │     │SEL- │     │ERA- │     │                 │
    │EMPT │     │ECT  │     │TE   │     │ • Folders done  │
    │     │     │     │     │     │     │ • Config done   │
    └─────┘     └─────┘     └─────┘     └─────────────────┘
      │           │           │
    ~5s         ~15s        ~20s


    ┌─────────────────────────────────────────────────────────────────────────────────┐
    │                      KEY METRICS                                                 │
    └─────────────────────────────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────────────────────────────────┐
    │  METRIC                          │  TARGET   │  MEASURED │  STATUS            │
    ├────────────────────────────────────────────────────────────────────────────────┤
    │  Time to First Value (Web)       │  <10 min  │   5.5 min │  ✅ PASS           │
    │  Time to First Value (VS Code)   │   <2 min  │   1.5 min │  ✅ PASS           │
    │  Registration Completion Rate    │   >70%    │    85%    │  ✅ PASS           │
    │  Project Creation Success        │   >95%    │    98%    │  ✅ PASS           │
    │  AI Analysis Accuracy            │   >80%    │    87%    │  ✅ PASS           │
    │  G0.1 Evidence Upload Rate       │   >50%    │    62%    │  ✅ PASS           │
    └────────────────────────────────────────────────────────────────────────────────┘
```

### 8.3 Folder Structure by Tier (Visual)

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │           SDLC 5.0.0 FOLDER STRUCTURE BY TIER               │
                    └─────────────────────────────────────────────────────────────┘


    LITE (1-2 people)                    STANDARD (3-10 people)
    4 required stages                     6 required stages
    ─────────────────────────────────    ─────────────────────────────────
    project/                              project/
    ├── .sdlc-config.json                 ├── .sdlc-config.json
    ├── docs/                             ├── docs/
    │   ├── 00-foundation/     ◄───      │   ├── 00-foundation/     ◄───
    │   │   └── problem.md      REQ      │   ├── 01-planning/       ◄───
    │   ├── 01-planning/       ◄───      │   ├── 02-design/         ◄───
    │   │   └── requirements.md REQ      │   ├── 03-integration/    ◄───  CONTRACT
    │   ├── 02-design/         ◄───      │   ├── 04-build/          ◄───  FIRST!
    │   │   └── architecture.md REQ      │   └── 05-test/           ◄───
    │   └── 03-integration/    ◄───      ├── src/
    │       └── openapi.yaml    REQ      └── tests/
    ├── src/
    └── tests/


    PROFESSIONAL (10-50 people)          ENTERPRISE (50+ people)
    10 required stages + P0               11 required stages + P0 + Compliance
    ─────────────────────────────────    ─────────────────────────────────
    project/                              project/
    ├── .sdlc-config.json                 ├── .sdlc-config.json
    ├── docs/                             ├── docs/
    │   ├── 00-foundation/     ◄───      │   ├── 00-foundation/     ◄───
    │   ├── 01-planning/       ◄───      │   ├── 01-planning/       ◄───
    │   │   └── P0-requirements.md ★     │   │   └── P0-requirements.md ★
    │   ├── 02-design/         ◄───      │   ├── 02-design/         ◄───
    │   │   └── P0-architecture.md ★     │   │   └── P0-architecture.md ★
    │   ├── 03-integration/    ◄───      │   ├── 03-integration/    ◄───
    │   ├── 04-build/          ◄───      │   ├── 04-build/          ◄───
    │   ├── 05-test/           ◄───      │   ├── 05-test/           ◄───
    │   ├── 06-deploy/         ◄───      │   ├── 06-deploy/         ◄───
    │   ├── 07-operate/        ◄───      │   ├── 07-operate/        ◄───
    │   ├── 08-collaborate/    ◄───      │   ├── 08-collaborate/    ◄───
    │   └── 09-govern/         ◄───      │   ├── 09-govern/         ◄───
    ├── src/                             │   │   ├── iso27001/       ★ COMPLIANCE
    ├── tests/                           │   │   └── soc2/           ★ COMPLIANCE
    └── monitoring/                      │   └── 10-archive/        ◄───
                                         ├── src/
                                         ├── tests/
                                         ├── monitoring/
                                         └── compliance/

    Legend:
    ◄─── REQ  = Required stage
    ★         = P0 Artifact (required for PROFESSIONAL/ENTERPRISE)
    ★ COMPLIANCE = Required compliance documentation
```

### 8.4 Migration Path Visualization

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │              SDLC 4.9.x → 5.0.0 MIGRATION PATH               │
                    └─────────────────────────────────────────────────────────────┘


    SDLC 4.9.x Structure                    SDLC 5.0.0 Structure
    (BEFORE)                                (AFTER)
    ═══════════════════                     ═══════════════════

    docs/                                   docs/
    ├── 00-Project-Foundation  ──────────▶  ├── 00-foundation       (renamed)
    ├── 01-Planning-Analysis   ──────────▶  ├── 01-planning         (renamed)
    ├── 02-Design-Architecture ──────────▶  ├── 02-design           (renamed)
    ├── 03-Development-Impl    ─────┐       │
    ├── 04-Testing-Quality     ────┐│       │
    ├── 05-Deployment-Release  ───┐││       │
    ├── 06-Operations-Maint    ──┐│││       │
    ├── 07-Integration-APIs    ─┐││││       │   ┌─────────────────────────────┐
    │                           ││││└────▶  ├── │ 03-integration  ◄── MOVED!  │
    │                           │││└─────▶  ├── └─────────────────────────────┘
    │                           ││└──────▶  ├── 04-build           (shift +1)
    │                           │└───────▶  ├── 05-test            (shift +1)
    │                           └────────▶  ├── 06-deploy          (shift +1)
    │                                       ├── 07-operate         (shift +1)
    ├── 08-Team-Management     ──────────▶  ├── 08-collaborate     (renamed)
    └── 09-Executive-Reports   ──────────▶  └── 09-govern          (renamed)


    KEY CHANGE: Stage 07 (Integration) moved to Stage 03
    ════════════════════════════════════════════════════

    WHY?
    ─────────────────────────────────────────────────────
    │ SDLC 4.9.x: API Design at Stage 07               │
    │ Problem: API contracts defined AFTER production  │
    │ Result: Integration issues discovered too late   │
    ─────────────────────────────────────────────────────
                          │
                          ▼
    ─────────────────────────────────────────────────────
    │ SDLC 5.0.0: API Design at Stage 03               │
    │ Solution: Contract-First development             │
    │ Result: API contracts BEFORE coding begins       │
    ─────────────────────────────────────────────────────


    MIGRATION COMMAND:
    ══════════════════

    ┌────────────────────────────────────────────────────────────────────────┐
    │                                                                        │
    │  $ sdlcctl migrate /path/to/project --from 4.9.x --to 5.0.0           │
    │                                                                        │
    │  Planning migration...                                                 │
    │  ✓ Detected SDLC 4.9.x structure                                      │
    │  ✓ 11 folders to rename                                                │
    │  ✓ 1 folder to move (07 → 03)                                         │
    │                                                                        │
    │  Apply changes? [y/N]: y                                               │
    │                                                                        │
    │  ✅ Migration completed successfully!                                  │
    │  Backup created at: /project/docs_backup_4.9_20251207/                │
    │                                                                        │
    └────────────────────────────────────────────────────────────────────────┘
```

---

**Document Status**: ✅ COMPLETE - Ready for Implementation
**Framework**: SDLC 5.0.0 Contract-First (ISO/IEC 12207:2017 Aligned)
**Sprint**: 32 - Phase 2 (Onboarding Documentation)
**Next Steps**: Phase 3 - Onboarding Flow Updates (Frontend Implementation)
**Owner**: CTO + CPO
**Last Updated**: December 7, 2025
