# Sprint 79 Technical Design: Self-Governance Database Architecture

**Sprint:** 79 (February 17-28, 2026)  
**Epic:** Self-Governance (Meta-Sprint)  
**Story Points:** 38 SP  
**Budget:** $25,000

---

## Design Goals

1. **Database as Single Source of Truth** - Migrate from markdown-first to database-first
2. **Auto-Generated Documentation** - All governance docs generated from database
3. **Enforce Traceability** - Roadmap → Epic → Phase → Sprint via Foreign Keys
4. **Block Violations** - Pre-commit hooks + CI/CD validation

---

## Database Schema

### Core Tables

```sql
-- 1. Project Roadmap (top level)
CREATE TABLE project_roadmaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(20) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(project_id, version)
);

CREATE INDEX idx_roadmaps_project ON project_roadmaps(project_id);

COMMENT ON TABLE project_roadmaps IS 
'Single source of truth for project roadmap. All epics must reference a roadmap.';

-- 2. Epics (mid level)
CREATE TABLE epics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    roadmap_id UUID NOT NULL REFERENCES project_roadmaps(id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL,  -- EP-01, EP-02, etc.
    name VARCHAR(255) NOT NULL,
    description TEXT,
    budget_usd INTEGER,
    status VARCHAR(50) DEFAULT 'planned',
    
    start_date DATE,
    end_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(roadmap_id, code)
);

CREATE INDEX idx_epics_roadmap ON epics(roadmap_id);

COMMENT ON TABLE epics IS 
'Epics group multiple phases. Each epic must belong to a roadmap.';

-- 3. Phases (implementation grouping)
CREATE TABLE phases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    epic_id UUID NOT NULL REFERENCES epics(id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL,  -- PHASE-05, PHASE-06, etc.
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    sprint_range VARCHAR(50),  -- "Sprint 70-73"
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(epic_id, code)
);

CREATE INDEX idx_phases_epic ON phases(epic_id);

COMMENT ON TABLE phases IS 
'Phases group related sprints. Each phase must belong to an epic.';

-- 4. Sprints (already exists - ADD FOREIGN KEY)
ALTER TABLE sprints 
ADD COLUMN phase_id UUID REFERENCES phases(id) ON DELETE RESTRICT;

ALTER TABLE sprints 
ADD CONSTRAINT sprint_must_have_phase 
CHECK (phase_id IS NOT NULL);

CREATE INDEX idx_sprints_phase ON sprints(phase_id);

COMMENT ON COLUMN sprints.phase_id IS 
'REQUIRED: Every sprint must belong to a phase. Orphan sprints are forbidden.';
```

### Enforcement Constraints

```sql
-- Prevent orphan sprints
ALTER TABLE sprints 
ADD CONSTRAINT no_orphan_sprints 
CHECK (phase_id IS NOT NULL);

-- Prevent phase without epic
ALTER TABLE phases 
ADD CONSTRAINT phase_must_have_epic 
CHECK (epic_id IS NOT NULL);

-- Prevent epic without roadmap
ALTER TABLE epics 
ADD CONSTRAINT epic_must_have_roadmap 
CHECK (roadmap_id IS NOT NULL);

-- Sprint numbers must be unique per project
ALTER TABLE sprints 
ADD CONSTRAINT unique_sprint_number_per_project 
UNIQUE (project_id, number);
```

---

## Data Migration (Sprint 70-78)

### Step 1: Create Roadmap

```sql
-- SDLC Orchestrator Roadmap
INSERT INTO project_roadmaps (id, project_id, name, version, status)
VALUES (
    'roadmap-uuid',
    'orchestrator-project-uuid',
    'Q1-Q3 2026: Software 3.0 Pivot',
    '5.1.0',
    'active'
);
```

### Step 2: Create Epics

```sql
-- Epic: Teams & Planning (retroactive)
INSERT INTO epics (id, roadmap_id, code, name, budget_usd, start_date, end_date, status)
VALUES (
    'epic-teams-uuid',
    'roadmap-uuid',
    'EP-TEAMS',
    'Teams & Planning Hierarchy Foundation',
    50000,
    '2026-01-06',
    '2026-01-24',
    'completed'
);

-- Epic: SASE Integration
INSERT INTO epics (id, roadmap_id, code, name, budget_usd, start_date, end_date, status)
VALUES (
    'epic-sase-uuid',
    'roadmap-uuid',
    'EP-SASE',
    'SASE Workflow Integration & Sprint Context',
    15000,
    '2026-01-27',
    '2026-02-14',
    'in_progress'
);

-- Epic: AI Safety (planned)
INSERT INTO epics (id, roadmap_id, code, name, budget_usd, start_date, end_date, status)
VALUES (
    'epic-ai-safety-uuid',
    'roadmap-uuid',
    'EP-01-02-03',
    'AI Safety First (Idea Flow + AI Safety Layer)',
    40000,
    '2026-02-17',
    '2026-04-11',
    'planned'
);
```

### Step 3: Create Phases

```sql
-- PHASE-05: Teams & Planning (Sprint 70-75)
INSERT INTO phases (id, epic_id, code, name, sprint_range)
VALUES (
    'phase-05-uuid',
    'epic-teams-uuid',
    'PHASE-05',
    'Teams & Planning Hierarchy',
    'Sprint 70-75'
);

-- PHASE-06: SASE Integration (Sprint 76-77)
INSERT INTO phases (id, epic_id, code, name, sprint_range)
VALUES (
    'phase-06-uuid',
    'epic-sase-uuid',
    'PHASE-06',
    'SASE Workflow Integration',
    'Sprint 76-77'
);

-- PHASE-07: Sprint Analytics (Sprint 78)
INSERT INTO phases (id, epic_id, code, name, sprint_range)
VALUES (
    'phase-07-uuid',
    'epic-sase-uuid',
    'PHASE-07',
    'Sprint Analytics & Retrospective',
    'Sprint 78'
);

-- PHASE-08: AI Safety (Sprint 79-83)
INSERT INTO phases (id, epic_id, code, name, sprint_range)
VALUES (
    'phase-08-uuid',
    'epic-ai-safety-uuid',
    'PHASE-08',
    'AI Safety Layer Implementation',
    'Sprint 79-83'
);
```

### Step 4: Link Existing Sprints to Phases

```sql
-- Link Sprint 70-73 to PHASE-05
UPDATE sprints 
SET phase_id = 'phase-05-uuid'
WHERE number IN (70, 71, 72, 73) 
AND project_id = 'orchestrator-project-uuid';

-- Link Sprint 74-75 to PHASE-05
UPDATE sprints 
SET phase_id = 'phase-05-uuid'
WHERE number IN (74, 75) 
AND project_id = 'orchestrator-project-uuid';

-- Link Sprint 76-77 to PHASE-06
UPDATE sprints 
SET phase_id = 'phase-06-uuid'
WHERE number IN (76, 77) 
AND project_id = 'orchestrator-project-uuid';

-- Link Sprint 78 to PHASE-07
UPDATE sprints 
SET phase_id = 'phase-07-uuid'
WHERE number = 78 
AND project_id = 'orchestrator-project-uuid';
```

### Verification Queries

```sql
-- Check for orphan sprints (should return 0)
SELECT number, name 
FROM sprints 
WHERE phase_id IS NULL 
AND project_id = 'orchestrator-project-uuid';

-- Verify traceability chain
SELECT 
    r.version as roadmap_version,
    e.code as epic_code,
    p.code as phase_code,
    s.number as sprint_number,
    s.name as sprint_name
FROM sprints s
JOIN phases p ON s.phase_id = p.id
JOIN epics e ON p.epic_id = e.id
JOIN project_roadmaps r ON e.roadmap_id = r.id
WHERE s.project_id = 'orchestrator-project-uuid'
ORDER BY s.number;
```

---

## Document Generation Service

### Implementation

```python
# backend/app/services/document_generator.py
from jinja2 import Template

class DocumentGeneratorService:
    """Generate governance documents from database."""
    
    async def generate_product_roadmap(
        self,
        project_id: UUID,
    ) -> str:
        """
        Generate Product-Roadmap.md from database.
        
        Template: docs/00-foundation/04-Roadmap/Product-Roadmap.md.j2
        Output: docs/00-foundation/04-Roadmap/Product-Roadmap.md
        """
        roadmap = await self.db.execute(
            select(ProjectRoadmap)
            .options(
                selectinload(ProjectRoadmap.epics)
                .selectinload(Epic.phases)
                .selectinload(Phase.sprints)
            )
            .where(ProjectRoadmap.project_id == project_id)
            .where(ProjectRoadmap.status == 'active')
        )
        roadmap = roadmap.scalar_one()
        
        # Calculate totals
        total_budget = sum(e.budget_usd for e in roadmap.epics if e.budget_usd)
        total_sprints = sum(len(p.sprints) for e in roadmap.epics for p in e.phases)
        
        # Render template
        template = Template(self._read_template('Product-Roadmap.md.j2'))
        return template.render(
            roadmap=roadmap,
            total_budget=total_budget,
            total_sprints=total_sprints,
            generated_at=datetime.utcnow(),
        )
    
    async def generate_sprint_plan(
        self,
        sprint_id: UUID,
    ) -> str:
        """
        Generate SPRINT-XX-*.md from database.
        
        INCLUDES automatic traceability section.
        """
        sprint = await self.db.execute(
            select(Sprint)
            .options(
                selectinload(Sprint.phase)
                .selectinload(Phase.epic)
                .selectinload(Epic.roadmap)
            )
            .where(Sprint.id == sprint_id)
        )
        sprint = sprint.scalar_one()
        
        # Build traceability chain
        traceability = {
            'roadmap': sprint.phase.epic.roadmap,
            'epic': sprint.phase.epic,
            'phase': sprint.phase,
            'sprint': sprint,
        }
        
        template = Template(self._read_template('Sprint-Plan.md.j2'))
        return template.render(
            sprint=sprint,
            traceability=traceability,
            generated_at=datetime.utcnow(),
        )
    
    async def generate_phase_plan(
        self,
        phase_id: UUID,
    ) -> str:
        """Generate PHASE-XX-*.md from database."""
        phase = await self.db.execute(
            select(Phase)
            .options(
                selectinload(Phase.sprints),
                selectinload(Phase.epic).selectinload(Epic.roadmap),
            )
            .where(Phase.id == phase_id)
        )
        phase = phase.scalar_one()
        
        template = Template(self._read_template('Phase-Plan.md.j2'))
        return template.render(
            phase=phase,
            sprints=sorted(phase.sprints, key=lambda s: s.number),
            generated_at=datetime.utcnow(),
        )
```

### Jinja2 Templates

```jinja2
{# docs/00-foundation/04-Roadmap/Product-Roadmap.md.j2 #}
# Product Roadmap

**Version**: {{ roadmap.version }}
**Status**: {{ roadmap.status }}
**Generated**: {{ generated_at.isoformat() }}

---

## Overview

{{ roadmap.name }}

**Investment**: ${{ "{:,}".format(total_budget) }} ({{ total_sprints }} sprints)

---

## Epics

{% for epic in roadmap.epics %}
### {{ epic.code }}: {{ epic.name }}

**Budget**: ${{ "{:,}".format(epic.budget_usd) }}
**Status**: {{ epic.status }}
**Timeline**: {{ epic.start_date }} to {{ epic.end_date }}

{% for phase in epic.phases %}
#### {{ phase.code }}: {{ phase.name }}

**Sprints**: {{ phase.sprint_range }}

{% for sprint in phase.sprints | sort(attribute='number') %}
- Sprint {{ sprint.number }}: {{ sprint.name }} ({{ sprint.story_points }} SP)
{% endfor %}

{% endfor %}
{% endfor %}

---

*This document is AUTO-GENERATED from database. Do not edit manually.*
*To update: Modify database, then run `make generate-roadmap`*
```

---

## API Endpoints

### Governance API

```python
# backend/app/api/governance.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/governance", tags=["Governance"])

@router.post("/roadmaps/{roadmap_id}/generate")
async def generate_roadmap_document(
    roadmap_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Generate Product-Roadmap.md from database.
    
    Returns:
    - Generated markdown content
    - File path where it was written
    - Git commit SHA
    """
    doc_gen = DocumentGeneratorService(db)
    
    # Generate content
    content = await doc_gen.generate_product_roadmap(roadmap_id)
    
    # Write to file
    file_path = "docs/00-foundation/04-Roadmap/Product-Roadmap.md"
    with open(file_path, 'w') as f:
        f.write(content)
    
    # Git commit
    commit_sha = subprocess.check_output([
        "git", "add", file_path,
        "&&",
        "git", "commit", "-m", f"docs: Auto-generate Product Roadmap from database",
        "&&",
        "git", "rev-parse", "HEAD"
    ]).decode().strip()
    
    return {
        "file_path": file_path,
        "commit_sha": commit_sha,
        "generated_at": datetime.utcnow(),
    }

@router.post("/sprints/{sprint_id}/generate")
async def generate_sprint_document(
    sprint_id: UUID,
    db: Session = Depends(get_db),
):
    """Generate SPRINT-XX-*.md from database."""
    # Similar to above

@router.get("/validate/traceability")
async def validate_traceability(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Validate Roadmap → Epic → Phase → Sprint traceability.
    
    Checks:
    - All sprints have phase_id
    - All phases have epic_id
    - All epics have roadmap_id
    - No orphan entities
    """
    # Query for orphans
    orphan_sprints = await db.execute(
        select(Sprint)
        .where(Sprint.project_id == project_id)
        .where(Sprint.phase_id == None)
    )
    orphan_sprints = orphan_sprints.scalars().all()
    
    # ... similar for phases, epics
    
    return {
        "valid": len(orphan_sprints) == 0,
        "orphan_sprints": [s.number for s in orphan_sprints],
        "orphan_phases": [],
        "orphan_epics": [],
    }
```

---

## Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

PROJECT_ROOT="/home/nqh/shared/SDLC-Orchestrator"
cd "$PROJECT_ROOT"

echo "🔍 Self-Governance Validation..."

# 1. Check if roadmap was manually edited
if git diff --cached --name-only | grep -q "Product-Roadmap.md"; then
    # Check if file contains auto-generation marker
    if ! grep -q "AUTO-GENERATED from database" docs/00-foundation/04-Roadmap/Product-Roadmap.md; then
        echo "❌ BLOCKED: Product-Roadmap.md appears to be manually edited"
        echo "   Roadmap must be generated from database using:"
        echo "   curl -X POST http://localhost:8000/governance/roadmaps/{id}/generate"
        exit 1
    fi
fi

# 2. Check if sprint plan has phase reference
if git diff --cached --name-only | grep -q "docs/04-build/02-Sprint-Plans/SPRINT-.*\.md"; then
    SPRINT_FILES=$(git diff --cached --name-only | grep "SPRINT-.*\.md")
    
    for SPRINT_FILE in $SPRINT_FILES; do
        SPRINT_NUM=$(echo "$SPRINT_FILE" | grep -oP 'SPRINT-\K\d+')
        
        # Query database for sprint
        PHASE_ID=$(psql -U postgres -d sdlc_orchestrator -t -c \
            "SELECT phase_id FROM sprints WHERE number=$SPRINT_NUM AND project_id=(SELECT id FROM projects WHERE name='SDLC-Orchestrator')")
        
        if [ -z "$PHASE_ID" ] || [ "$PHASE_ID" = "NULL" ]; then
            echo "❌ BLOCKED: Sprint $SPRINT_NUM has no phase_id in database"
            echo "   Create phase and link sprint first:"
            echo "   1. POST /governance/phases (create phase)"
            echo "   2. UPDATE sprints SET phase_id=? WHERE number=$SPRINT_NUM"
            exit 1
        fi
        
        echo "✅ Sprint $SPRINT_NUM linked to phase (ID: $PHASE_ID)"
    done
fi

# 3. Validate traceability before commit
HTTP_RESPONSE=$(curl -s http://localhost:8000/governance/validate/traceability?project_id=$(psql -U postgres -d sdlc_orchestrator -t -c "SELECT id FROM projects WHERE name='SDLC-Orchestrator'"))

if echo "$HTTP_RESPONSE" | grep -q '"valid":false'; then
    echo "❌ BLOCKED: Traceability validation failed"
    echo "$HTTP_RESPONSE" | jq .
    exit 1
fi

echo "✅ Self-governance validation passed"
exit 0
```

---

## GitHub Actions Workflow

```yaml
# .github/workflows/self-governance.yml
name: Self-Governance Validation

on:
  pull_request:
    paths:
      - 'docs/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: sdlc_orchestrator
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install -e backend/sdlcctl
      
      - name: Run Migrations
        run: |
          cd backend
          alembic upgrade head
      
      - name: Validate Traceability
        run: |
          python -c "
          from app.services.governance import GovernanceService
          from app.db.session import SessionLocal
          
          db = SessionLocal()
          gov = GovernanceService(db)
          
          result = gov.validate_traceability(project_name='SDLC-Orchestrator')
          
          if not result['valid']:
              print('❌ Traceability validation failed:')
              print(f'  Orphan sprints: {result[\"orphan_sprints\"]}')
              print(f'  Orphan phases: {result[\"orphan_phases\"]}')
              print(f'  Orphan epics: {result[\"orphan_epics\"]}')
              exit(1)
          
          print('✅ Traceability validation passed')
          "
      
      - name: Generate Compliance Report
        run: |
          sdlcctl report governance \
            --project=SDLC-Orchestrator \
            --format=markdown \
            --output=governance-report.md
      
      - name: Comment PR
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('governance-report.md', 'utf8');
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 🔍 Self-Governance Validation\n\n${report}`
            });
```

---

## Makefile Targets

```makefile
# Makefile additions

.PHONY: generate-roadmap
generate-roadmap:
	@echo "🗺️  Generating Product Roadmap from database..."
	@curl -X POST http://localhost:8000/governance/roadmaps/$(ROADMAP_ID)/generate
	@echo "✅ Roadmap generated"

.PHONY: generate-sprint
generate-sprint:
	@echo "📋 Generating Sprint Plan from database..."
	@curl -X POST http://localhost:8000/governance/sprints/$(SPRINT_ID)/generate
	@echo "✅ Sprint plan generated"

.PHONY: generate-all-docs
generate-all-docs:
	@echo "📚 Regenerating ALL governance documents..."
	@python backend/scripts/generate_all_docs.py
	@echo "✅ All docs regenerated"

.PHONY: validate-governance
validate-governance:
	@echo "🔍 Validating self-governance..."
	@sdlcctl validate governance --project=SDLC-Orchestrator
	@echo "✅ Governance validation passed"

.PHONY: install-hooks
install-hooks:
	@echo "🪝 Installing git hooks..."
	@cp scripts/hooks/pre-commit .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "✅ Git hooks installed"
```

---

## Sprint 79 Implementation Plan

### Week 1 (Days 1-5)

**Day 1:**
- Create database schema (roadmaps, epics, phases tables)
- Run migrations
- Add phase_id FK to sprints table

**Day 2:**
- Implement data migration script
- Backfill Sprint 70-78 with phase_id
- Verify no orphan sprints

**Day 3:**
- Implement `DocumentGeneratorService`
- Create Jinja2 templates
- Test roadmap generation

**Day 4:**
- Implement governance API endpoints
- Test document generation via API
- Create Makefile targets

**Day 5:**
- Implement pre-commit hooks
- Test with intentional violations
- Document installation process

### Week 2 (Days 6-10)

**Day 6:**
- Implement GitHub Actions workflow
- Test on PR
- Fix any issues

**Day 7:**
- Generate all docs from database
- Compare with existing docs
- Fix any mismatches

**Day 8:**
- Create AI agent service wrapper
- Update AI prompts with constraints
- Test AI agent compliance

**Day 9:**
- Integration testing
- Load testing (1000 sprints)
- Performance optimization

**Day 10:**
- Documentation
- Sprint 79 completion report
- Handoff to Sprint 80

---

## Success Criteria

- [ ] All sprints (70-78) have phase_id in database
- [ ] Product-Roadmap.md auto-generated from database
- [ ] All SPRINT-XX-*.md auto-generated with traceability
- [ ] Pre-commit hook blocks orphan sprints
- [ ] GitHub Actions validates traceability on every PR
- [ ] Zero manual markdown editing required
- [ ] AI agents forced through governance API
- [ ] 100% compliance rate (AI + human)

---

**SDLC 5.1.3 | Sprint 79 Technical Design | Self-Governance**

*Commit: faa7390*
