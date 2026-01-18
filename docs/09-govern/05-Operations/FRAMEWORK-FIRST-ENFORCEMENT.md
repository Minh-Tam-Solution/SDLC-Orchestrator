# Framework-First Principle Enforcement
## SDLC Orchestrator - SE 3.0 SASE Integration

**Document Version:** 1.0.0
**Status:** ACTIVE - PRODUCTION
**Authority:** CTO + CPO MANDATED
**Effective Date:** December 9, 2025
**Enforcement Level:** MANDATORY (pre-commit + CI/CD gates)

---

## 🎯 PURPOSE

This document defines **automated enforcement mechanisms** to ensure all SDLC Orchestrator features follow the Framework-First Principle. Violations are blocked at commit and CI/CD stages.

**Non-Negotiable Requirement:** All developers MUST pass Framework-First checks before merging to main.

---

## 🏛️ FRAMEWORK-FIRST PRINCIPLE (RECAP)

**Mandate:** Any feature added to SDLC Orchestrator MUST:

### **Option A: Framework Enhancement First** (Preferred)
1. Add to SDLC Framework as methodology/template (tools-agnostic)
2. Commit to Framework repo: `https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework`
3. Update main repo submodule pointer
4. THEN build Orchestrator automation (Track 2, conditional)

### **Option B: Framework Compatibility** (If Orchestrator-specific)
1. Ensure feature is Orchestrator-specific (e.g., Evidence Vault API, MinIO integration)
2. Verify compatibility with Framework methodology
3. Document alignment in ADR (Architecture Decision Record)

**Rationale:**
- Framework = methodology layer (timeless, vendor-neutral, universal)
- Orchestrator = automation layer (specific implementation, tool-specific)
- Framework survives even if Orchestrator is replaced

---

## 🚫 VIOLATION EXAMPLES (3 SCENARIOS)

### **Violation 1: SASE Artifact Generated in Orchestrator Backend**

**Scenario:** Developer adds BriefingScript generation API endpoint without adding template to Framework first.

**Violating Code:**
```python
# ❌ VIOLATION - backend/app/api/routes/sase.py
@router.post("/sase/briefing-script")
async def generate_briefing_script(request: BRSRequest):
    """Generate BriefingScript for agentic task."""

    # VIOLATION: Hard-coded template in Orchestrator backend
    template = """
    # BriefingScript (BRS)

    ## Problem Context
    {problem_context}

    ## Solution Requirements
    {solution_requirements}

    ## Expected Deliverables
    {deliverables}
    """

    return {"brs": template.format(**request.dict())}
```

**Why Violates Framework-First:**
- BriefingScript template hard-coded in Orchestrator (not in Framework)
- Template not tools-agnostic (Orchestrator-specific format)
- Other projects (NQH, BFlow, MTEP) cannot reuse this template
- If Orchestrator is replaced, template is lost

**Corrected Implementation:**

**Step 1: Add to Framework First**
```bash
# Framework repo: SDLC-Enterprise-Framework
cd /home/nqh/shared/SDLC-Orchestrator/SDLC-Enterprise-Framework

# Create template
cat > 03-Templates-Tools/SASE-Artifacts/01-BriefingScript-Template.md << 'EOF'
# BriefingScript (BRS)
## SASE Artifact - MANDATORY

**Version:** 1.0.0
**Stage:** Stage 00 (WHY - Problem Definition)
**Tools:** ANY (Claude, GPT-4, Gemini, Ollama, manual)

---

## 1. Problem Context (WHY)

**Business Problem:**
{problem_description}

**User Pain Points:**
{pain_points}

**Success Criteria:**
{success_criteria}

---

## 2. Solution Requirements (WHAT)

**Functional Requirements:**
{functional_requirements}

**Non-Functional Requirements:**
{non_functional_requirements}

---

## 3. Technical Constraints (HOW)

**Technology Stack:**
{tech_stack}

**Performance Budget:**
{performance_budget}

**Security Requirements:**
{security_requirements}

---

## 4. SE4H vs SE4A Decision

**Human Tasks (SE4H):**
{human_tasks}

**Agentic Tasks (SE4A):**
{agentic_tasks}

**Rationale:**
{decision_rationale}

---

## 5. Expected Deliverables

{deliverables}

---

## 6. Acceptance Criteria

{acceptance_criteria}

EOF

# Commit to Framework repo
git add .
git commit -m "feat(SDLC 5.1.0): Add BriefingScript (BRS) template

Tools-agnostic SASE artifact template.
Works with any AI tool (Claude, GPT-4, Gemini, Ollama).

Related: SE 3.0 Track 1 - Framework Enhancement"
git push origin main
```

**Step 2: Update Orchestrator Submodule Pointer**
```bash
cd /home/nqh/shared/SDLC-Orchestrator
git submodule update --remote SDLC-Enterprise-Framework
git add SDLC-Enterprise-Framework
git commit -m "chore: Update Framework - BRS template added"
git push origin main
```

**Step 3: THEN Build Orchestrator Automation (Track 2)**
```python
# ✅ CORRECT - backend/app/api/routes/sase.py
from pathlib import Path

@router.post("/sase/briefing-script")
async def generate_briefing_script(request: BRSRequest):
    """Generate BriefingScript using Framework template."""

    # Read template from Framework submodule (NOT hard-coded)
    template_path = Path(__file__).parent.parent.parent.parent / \
                   "SDLC-Enterprise-Framework/03-Templates-Tools/SASE-Artifacts/01-BriefingScript-Template.md"

    with open(template_path, "r") as f:
        template = f.read()

    # Populate template with request data
    populated = template.format(
        problem_description=request.problem_description,
        pain_points="\n".join(f"- {p}" for p in request.pain_points),
        success_criteria="\n".join(f"- {s}" for s in request.success_criteria),
        # ... other fields
    )

    return {"brs": populated, "template_source": "Framework/03-Templates-Tools/SASE-Artifacts/01-BriefingScript-Template.md"}
```

**Result:**
- ✅ Template lives in Framework (reusable across projects)
- ✅ Tools-agnostic (any AI tool can use markdown template)
- ✅ Orchestrator reads from Framework submodule (automation layer)
- ✅ If Orchestrator replaced, template survives in Framework

---

### **Violation 2: SDLC Structure Validation Logic in Orchestrator**

**Scenario:** Developer adds new SDLC 5.1.0 folder requirement directly in Orchestrator validation logic.

**Violating Code:**
```python
# ❌ VIOLATION - backend/app/services/sdlc_validator.py
def validate_sdlc_structure(project_path: Path) -> ValidationResult:
    """Validate SDLC 5.1.0 structure."""

    # VIOLATION: Hard-coded SASE folder requirement
    required_folders = [
        "00-Why",
        "01-What",
        "02-How",
        "03-Build",
        "04-Test",
        "05-Deploy",
        "06-Operate",
        "07-Monitor",
        "08-Improve",
        "09-Govern",
        "10-SASE-Artifacts",  # ❌ NEW requirement not documented in Framework
    ]

    missing = []
    for folder in required_folders:
        if not (project_path / folder).exists():
            missing.append(folder)

    return ValidationResult(is_valid=len(missing) == 0, missing_folders=missing)
```

**Why Violates Framework-First:**
- SDLC 5.1.0 structure change NOT documented in Framework first
- Framework still shows SDLC 5.1.3 (10 stages: 00-09, no `10-SASE-Artifacts`)
- Other projects cannot discover this new requirement
- Validation logic diverges from Framework methodology

**Corrected Implementation:**

**Step 1: Update Framework Methodology First**
```bash
cd /home/nqh/shared/SDLC-Orchestrator/SDLC-Enterprise-Framework

# Update SDLC structure documentation
cat >> 01-Overview/SDLC-Structure-Guide.md << 'EOF'

## SDLC 5.1.0 Structure (SASE-Enabled)

**New in 5.1.0:**
- Optional `SASE-Artifacts/` folder for projects using Software Engineering 3.0 agentic workflows

**Folder Structure:**
```
project-root/
├── 00-Why/           # Stage 00 - Problem Definition
├── 01-What/          # Stage 01 - Planning & Analysis
├── 02-How/           # Stage 02 - Design & Architecture
├── 03-Build/         # Stage 03 - Development & Implementation
├── 04-Test/          # Stage 04 - Testing & Quality Assurance
├── 05-Deploy/        # Stage 05 - Deployment & Release
├── 06-Operate/       # Stage 06 - Operations & Maintenance
├── 07-Monitor/       # Stage 07 - Monitoring & Observability
├── 08-Improve/       # Stage 08 - Continuous Improvement
├── 09-Govern/        # Stage 09 - Governance & Compliance
└── SASE-Artifacts/   # OPTIONAL - SE 3.0 agentic artifacts (BRS, MRP, VCR, ACE, AEE, PDS)
```

**SASE-Artifacts/ Subfolder Structure:**
```
SASE-Artifacts/
├── BriefingScript.md           # BRS - MANDATORY (human → agent briefing)
├── MergeReadinessPack.md       # MRP - MANDATORY (agent → human handoff)
├── VerificationContextReport.md # VCR - MANDATORY (verification results)
├── AgenticCodingEvidence.md    # ACE - OPTIONAL (coding session logs)
├── AgenticExecutionEvidence.md # AEE - OPTIONAL (execution traces)
└── PostDeploymentSummary.md    # PDS - OPTIONAL (deployment summary)
```

**Backward Compatibility:**
- SDLC 5.1.3 projects (no SASE) remain valid (no `SASE-Artifacts/` required)
- SDLC 5.1.0 projects using SASE MUST include `SASE-Artifacts/` with 3 MANDATORY files

EOF

git add .
git commit -m "docs(SDLC 5.1.0): Add SASE-Artifacts/ folder to structure guide

Backward compatible with SDLC 5.1.3.
SASE folder optional unless project uses SE 3.0 workflows.

Related: SE 3.0 Track 1 - Framework Enhancement"
git push origin main
```

**Step 2: Update Orchestrator Validator (Reads from Framework)**
```python
# ✅ CORRECT - backend/app/services/sdlc_validator.py
import yaml
from pathlib import Path

def validate_sdlc_structure(project_path: Path, sdlc_version: str = "5.1.0") -> ValidationResult:
    """Validate SDLC structure using Framework-defined rules."""

    # Read structure definition from Framework (NOT hard-coded)
    framework_path = Path(__file__).parent.parent.parent / "SDLC-Enterprise-Framework"
    structure_config = framework_path / "01-Overview/sdlc-structure-config.yml"

    with open(structure_config, "r") as f:
        config = yaml.safe_load(f)

    # Get required folders for specified version
    required = config["versions"][sdlc_version]["required_folders"]
    optional = config["versions"][sdlc_version]["optional_folders"]

    missing_required = []
    for folder in required:
        if not (project_path / folder).exists():
            missing_required.append(folder)

    return ValidationResult(
        is_valid=len(missing_required) == 0,
        missing_folders=missing_required,
        sdlc_version=sdlc_version,
        config_source="Framework/01-Overview/sdlc-structure-config.yml"
    )
```

**Framework Config Example:**
```yaml
# SDLC-Enterprise-Framework/01-Overview/sdlc-structure-config.yml
versions:
  "5.0.0":
    required_folders:
      - 00-Why
      - 01-What
      - 02-How
      - 03-Build
      - 04-Test
      - 05-Deploy
      - 06-Operate
      - 07-Monitor
      - 08-Improve
      - 09-Govern
    optional_folders: []

  "5.1.0":
    required_folders:
      - 00-Why
      - 01-What
      - 02-How
      - 03-Build
      - 04-Test
      - 05-Deploy
      - 06-Operate
      - 07-Monitor
      - 08-Improve
      - 09-Govern
    optional_folders:
      - SASE-Artifacts  # Optional - only for SE 3.0 projects
```

**Result:**
- ✅ SDLC structure defined in Framework (single source of truth)
- ✅ Orchestrator reads from Framework config (automation layer)
- ✅ Other projects can reference Framework docs (not Orchestrator code)
- ✅ Backward compatible (5.0.0 projects still valid)

---

### **Violation 3: AI Prompt Template Hard-Coded in Orchestrator**

**Scenario:** Developer adds SE 3.0 agent prompting template directly in Orchestrator AI service.

**Violating Code:**
```python
# ❌ VIOLATION - backend/app/services/ai_service.py
async def generate_agentic_task(user_story: str) -> AgenticTask:
    """Generate SE4A task from user story."""

    # VIOLATION: Prompt template hard-coded in Orchestrator
    prompt = f"""
    You are a software engineering AI agent following SE 3.0 methodology.

    User Story: {user_story}

    Generate a BriefingScript (BRS) with:
    1. Problem Context (WHY)
    2. Solution Requirements (WHAT)
    3. Technical Constraints (HOW)
    4. SE4H vs SE4A split
    5. Expected Deliverables

    Output in markdown format.
    """

    response = await llm_client.complete(prompt)
    return AgenticTask(brs=response.content)
```

**Why Violates Framework-First:**
- SE 3.0 prompting template NOT documented in Framework
- Prompt structure hard-coded (cannot be updated without code change)
- Other AI tools (GPT-4, Gemini, Ollama) cannot reuse this template
- Prompt engineering knowledge locked in Orchestrator code

**Corrected Implementation:**

**Step 1: Add Prompt Template to Framework**
```bash
cd /home/nqh/shared/SDLC-Orchestrator/SDLC-Enterprise-Framework

mkdir -p 04-AI-Prompts/SE3.0-Agentic-Prompts

cat > 04-AI-Prompts/SE3.0-Agentic-Prompts/BRS-Generation-Prompt.md << 'EOF'
# BriefingScript Generation Prompt
## SE 3.0 Agentic Task Decomposition

**Version:** 1.0.0
**AI Tools:** Claude, GPT-4, Gemini, Ollama (any LLM)
**Input:** User Story
**Output:** BriefingScript (BRS) markdown

---

## System Prompt

You are a software engineering AI agent following Software Engineering 3.0 (SE 3.0) methodology with SASE artifacts.

Your role: Decompose user stories into structured BriefingScript (BRS) artifacts for human-agentic collaboration.

---

## User Prompt Template

```
User Story:
{user_story}

Generate a BriefingScript (BRS) with the following structure:

# BriefingScript (BRS)

## 1. Problem Context (WHY)
- Business problem
- User pain points
- Success criteria

## 2. Solution Requirements (WHAT)
- Functional requirements
- Non-functional requirements
- Constraints

## 3. Technical Constraints (HOW)
- Technology stack
- Performance budget
- Security requirements

## 4. SE4H vs SE4A Decision
- Human Tasks (SE4H): [tasks requiring human judgment]
- Agentic Tasks (SE4A): [tasks suitable for AI automation]
- Rationale: [why this split makes sense]

## 5. Expected Deliverables
- Code files
- Documentation
- Tests

## 6. Acceptance Criteria
- [Testable success conditions]

Output in markdown format following this exact structure.
```

---

## Example Output

[See 03-Templates-Tools/SASE-Artifacts/01-BriefingScript-Template.md for example]

---

## Validation Checklist

- [ ] All 6 sections present
- [ ] SE4H vs SE4A split clearly justified
- [ ] Acceptance criteria testable
- [ ] Markdown format valid
- [ ] No vendor-specific syntax

EOF

git add .
git commit -m "feat(SDLC 5.1.0): Add BRS generation prompt template

Tools-agnostic prompt for any LLM (Claude, GPT-4, Gemini, Ollama).
Supports SE 3.0 agentic task decomposition.

Related: SE 3.0 Track 1 - Framework Enhancement"
git push origin main
```

**Step 2: Update Orchestrator AI Service (Reads from Framework)**
```python
# ✅ CORRECT - backend/app/services/ai_service.py
from pathlib import Path

async def generate_agentic_task(user_story: str) -> AgenticTask:
    """Generate SE4A task using Framework prompt template."""

    # Read prompt template from Framework (NOT hard-coded)
    framework_path = Path(__file__).parent.parent.parent / "SDLC-Enterprise-Framework"
    prompt_template_path = framework_path / "04-AI-Prompts/SE3.0-Agentic-Prompts/BRS-Generation-Prompt.md"

    with open(prompt_template_path, "r") as f:
        prompt_template = f.read()

    # Extract user prompt section (between ```...```)
    user_prompt = extract_prompt_section(prompt_template, "User Prompt Template")

    # Populate template with user story
    prompt = user_prompt.format(user_story=user_story)

    # Call LLM (supports multi-provider: Claude, GPT-4, Gemini, Ollama)
    response = await llm_client.complete(prompt, model=config.AI_MODEL)

    return AgenticTask(
        brs=response.content,
        prompt_source="Framework/04-AI-Prompts/SE3.0-Agentic-Prompts/BRS-Generation-Prompt.md",
        model_used=config.AI_MODEL
    )
```

**Result:**
- ✅ Prompt template lives in Framework (methodology layer)
- ✅ Tools-agnostic (works with any LLM: Claude, GPT-4, Gemini, Ollama)
- ✅ Prompt engineering knowledge documented (not locked in code)
- ✅ Orchestrator reads from Framework (automation layer)
- ✅ Template can be updated without code changes

---

## 🔧 ENFORCEMENT MECHANISMS

### **Mechanism 1: Pre-Commit Hook**

**File:** `.git/hooks/pre-commit`

```bash
#!/bin/bash
# Framework-First Principle Enforcement - Pre-Commit Hook

set -e

echo "🔍 Running Framework-First compliance check..."

# Check 1: Detect hard-coded SASE templates in backend
SASE_HARDCODED=$(git diff --cached --name-only | \
  grep -E 'backend/app/(api/routes|services)' | \
  xargs grep -l "BriefingScript\|MergeReadinessPack\|VerificationContextReport" 2>/dev/null || true)

if [ -n "$SASE_HARDCODED" ]; then
  echo "❌ COMMIT BLOCKED - Framework-First violation detected!"
  echo ""
  echo "Files with hard-coded SASE templates:"
  echo "$SASE_HARDCODED"
  echo ""
  echo "SASE templates must be added to Framework first:"
  echo "  1. Add to SDLC-Enterprise-Framework/03-Templates-Tools/SASE-Artifacts/"
  echo "  2. Commit to Framework repo"
  echo "  3. Update main repo submodule pointer"
  echo "  4. THEN read templates from Framework submodule in Orchestrator code"
  echo ""
  echo "See: docs/09-govern/05-Operations/FRAMEWORK-FIRST-ENFORCEMENT.md"
  exit 1
fi

# Check 2: Detect hard-coded SDLC structure rules
SDLC_STRUCTURE_HARDCODED=$(git diff --cached --name-only | \
  grep -E 'backend/app/services/sdlc_validator\.py' | \
  xargs grep -l "required_folders\s*=\s*\[" 2>/dev/null || true)

if [ -n "$SDLC_STRUCTURE_HARDCODED" ]; then
  echo "❌ COMMIT BLOCKED - SDLC structure hard-coded in validator!"
  echo ""
  echo "SDLC structure rules must be defined in Framework config:"
  echo "  SDLC-Enterprise-Framework/01-Overview/sdlc-structure-config.yml"
  echo ""
  echo "Validator should READ from Framework config, not hard-code rules."
  echo ""
  echo "See: docs/09-govern/05-Operations/FRAMEWORK-FIRST-ENFORCEMENT.md (Violation 2)"
  exit 1
fi

# Check 3: Detect hard-coded AI prompts
AI_PROMPT_HARDCODED=$(git diff --cached --name-only | \
  grep -E 'backend/app/services/ai_service\.py' | \
  xargs grep -l 'prompt\s*=\s*f"""' 2>/dev/null || true)

if [ -n "$AI_PROMPT_HARDCODED" ]; then
  echo "⚠️  WARNING - AI prompt template detected in code!"
  echo ""
  echo "Consider moving prompt template to Framework:"
  echo "  SDLC-Enterprise-Framework/04-AI-Prompts/SE3.0-Agentic-Prompts/"
  echo ""
  echo "This ensures prompt templates are tools-agnostic and reusable."
  echo ""
  echo "Proceed with commit? (y/n)"
  read -r response
  if [ "$response" != "y" ]; then
    echo "Commit cancelled."
    exit 1
  fi
fi

echo "✅ Framework-First compliance: PASS"
exit 0
```

**Installation:**
```bash
chmod +x .git/hooks/pre-commit
```

---

### **Mechanism 2: CI/CD Pipeline Gate**

**File:** `.github/workflows/framework-first-check.yml`

```yaml
name: Framework-First Compliance Check

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  framework-first-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive
          fetch-depth: 0  # Full git history for diff

      - name: Check Framework Submodule Initialized
        run: |
          echo "🔍 Verifying Framework submodule..."

          if [ ! -f "SDLC-Enterprise-Framework/.git" ]; then
            echo "❌ FAIL: Framework submodule not initialized!"
            echo "Run: git submodule update --init --recursive"
            exit 1
          fi

          echo "✅ Framework submodule initialized"

      - name: Check SASE Templates in Framework (Not Orchestrator)
        run: |
          echo "🔍 Checking for hard-coded SASE templates..."

          # Check if SASE keywords exist in backend code
          if grep -r "BriefingScript\|MergeReadinessPack\|VerificationContextReport" \
             backend/app/api/routes backend/app/services 2>/dev/null | \
             grep -v "template_path\|Framework" | \
             grep -v "# Framework-First compliant"; then

            echo "❌ FAIL: Hard-coded SASE templates found in backend!"
            echo ""
            echo "SASE templates must be added to Framework first:"
            echo "  Location: SDLC-Enterprise-Framework/03-Templates-Tools/SASE-Artifacts/"
            echo "  Then read from Framework submodule in Orchestrator code."
            echo ""
            echo "See: docs/09-govern/05-Operations/FRAMEWORK-FIRST-ENFORCEMENT.md"
            exit 1
          fi

          echo "✅ No hard-coded SASE templates detected"

      - name: Check SDLC Structure Config in Framework
        run: |
          echo "🔍 Checking SDLC structure config source..."

          # Verify sdlc_validator.py reads from Framework config
          if grep -q "required_folders\s*=\s*\[" backend/app/services/sdlc_validator.py; then
            echo "❌ FAIL: SDLC structure hard-coded in validator!"
            echo ""
            echo "Structure rules must be in Framework config:"
            echo "  SDLC-Enterprise-Framework/01-Overview/sdlc-structure-config.yml"
            echo ""
            echo "See: docs/09-govern/05-Operations/FRAMEWORK-FIRST-ENFORCEMENT.md (Violation 2)"
            exit 1
          fi

          echo "✅ SDLC validator reads from Framework config"

      - name: Check AI Prompts Location
        run: |
          echo "🔍 Checking AI prompt template location..."

          # Count AI prompts in backend code
          PROMPT_COUNT=$(grep -r 'prompt\s*=\s*f"""' backend/app/services/ai_service.py 2>/dev/null | wc -l || echo 0)

          if [ "$PROMPT_COUNT" -gt 2 ]; then
            echo "⚠️  WARNING: $PROMPT_COUNT hard-coded AI prompts detected!"
            echo ""
            echo "Consider moving prompt templates to Framework:"
            echo "  SDLC-Enterprise-Framework/04-AI-Prompts/SE3.0-Agentic-Prompts/"
            echo ""
            echo "This is a warning, not a failure (for now)."
          else
            echo "✅ AI prompt count acceptable ($PROMPT_COUNT templates)"
          fi

      - name: Framework-First Summary
        run: |
          echo "✅ Framework-First compliance check PASSED"
          echo ""
          echo "Summary:"
          echo "  - Framework submodule initialized"
          echo "  - No hard-coded SASE templates"
          echo "  - SDLC structure reads from Framework config"
          echo "  - AI prompt template count acceptable"

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '✅ Framework-First compliance check **PASSED**\n\n' +
                    'All features properly use Framework methodology layer.\n\n' +
                    'See: [Framework-First Enforcement Guide](docs/09-govern/05-Operations/FRAMEWORK-FIRST-ENFORCEMENT.md)'
            })
```

---

### **Mechanism 3: Code Review Checklist**

**File:** `.github/PULL_REQUEST_TEMPLATE.md`

```markdown
## Framework-First Compliance Checklist

Before merging, verify:

- [ ] **SASE Templates in Framework First**
  - If adding SASE features, templates added to `SDLC-Enterprise-Framework/03-Templates-Tools/SASE-Artifacts/` first
  - Orchestrator reads from Framework submodule (NOT hard-coded)

- [ ] **SDLC Structure in Framework**
  - Structure rules defined in `SDLC-Enterprise-Framework/01-Overview/sdlc-structure-config.yml`
  - Validator reads from Framework config (NOT hard-coded)

- [ ] **AI Prompts in Framework**
  - Prompt templates in `SDLC-Enterprise-Framework/04-AI-Prompts/SE3.0-Agentic-Prompts/`
  - AI service reads from Framework (NOT hard-coded f-strings)

- [ ] **Submodule Pointer Updated**
  - If Framework changed, main repo submodule pointer updated
  - Commit message: "chore: Update Framework submodule - [description]"

- [ ] **ADR Created (if Orchestrator-specific)**
  - If feature is Orchestrator-specific (Option B), ADR created
  - ADR documents Framework compatibility

## References

- [Framework-First Enforcement Guide](docs/09-govern/05-Operations/FRAMEWORK-FIRST-ENFORCEMENT.md)
- [Violation Examples](docs/09-govern/05-Operations/FRAMEWORK-FIRST-ENFORCEMENT.md#violation-examples)
```

---

## 📊 ENFORCEMENT METRICS

**Track compliance with weekly reports:**

```yaml
Metrics to Monitor:
  1. Pre-commit hook blocks per week (target: <5 violations)
  2. CI/CD pipeline failures due to Framework-First (target: <3 per week)
  3. PRs requiring rework (target: <10%)
  4. Average rework time (target: <30 min)

Success Criteria:
  - 95%+ PRs pass Framework-First check on first attempt
  - <5 violations per week after Week 2
  - Zero hard-coded SASE templates in production
```

---

## ✅ COMPLIANCE CERTIFICATION

**Team Lead Certification:**

> I certify that all team members understand Framework-First Principle and enforcement mechanisms are installed on all developer machines.
>
> - [ ] Pre-commit hook installed (9/9 developers)
> - [ ] CI/CD pipeline active (GitHub Actions)
> - [ ] PR template updated
> - [ ] Team training complete (90-min workshop)
>
> Signed: [Team Lead]
> Date: [Date]

---

**Document Owner:** CTO + Tech Lead
**Last Updated:** December 9, 2025
**Next Review:** Weekly during SE 3.0 Track 1

---

**CTO Notes:**
> "Framework-First is non-negotiable. Enforcement at pre-commit + CI/CD ensures compliance."
> "3 violation examples = teaching moments, not gotchas. Learn from them."
> "Track metrics weekly. Goal: 95%+ PRs pass on first attempt by Week 3."
