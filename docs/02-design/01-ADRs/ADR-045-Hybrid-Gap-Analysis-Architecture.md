# ADR-045: Hybrid Gap Analysis Architecture

**Status**: ✅ APPROVED (CTO Sign-off: Jan 30, 2026)
**Date**: January 30, 2026
**Decision Maker**: CTO + Backend Lead + Extension Lead
**Context**: Sprint 129 preparation (Feb 17-28, 2026)
**Related ADRs**: ADR-044 (GitHub Integration), ADR-021 (SDLC Scanner)
**Sprint**: Sprint 129 (GitHub Project Onboarding)

---

## Context and Problem Statement

SDLC Orchestrator needs to perform **gap analysis** to compare a project's current structure against SDLC Framework requirements (tier-specific stage requirements).

**Gap Analysis Input**:
- Project tier (LITE, STANDARD, PROFESSIONAL, ENTERPRISE)
- Existing folder structure (what stages/artifacts exist)
- SDLC Framework requirements (what stages/artifacts are required)

**Gap Analysis Output**:
- Compliance score (% of required stages present)
- Missing stages (what needs to be added)
- Recommendations (prioritized action items)

**Three architectural approaches exist**:
1. **Backend scans local filesystem** (Backend reads user's files directly)
2. **Client scans, backend validates** (Extension/CLI scans, submits to backend)
3. **Hybrid** (Backend provides ruleset, clients scan and submit reports)

**Business Impact**:
- **Core feature** for project onboarding (Sprint 129)
- **Privacy concern** if backend reads user files
- **Performance concern** if backend scans large repos
- **Offline support** if clients can scan without backend

**Requirements**:
- Multi-tier support (LITE/STANDARD/PROFESSIONAL/ENTERPRISE)
- Fast gap analysis (<10s for typical repo)
- Privacy-first (no user files sent to backend)
- Offline-capable (Extension can scan without internet)
- Audit trail (track gap reports over time)

---

## Decision Drivers

### Must Have (P0)
- **Privacy**: User files NEVER sent to backend (only folder names)
- **Performance**: Gap analysis <10s for typical repo (1000 files)
- **Multi-tier**: Support all 4 tiers with different requirements
- **Audit trail**: Store historical gap reports (track progress)
- **Versioned rulesets**: Framework 6.0.0 ruleset can be upgraded to 6.1.0

### Should Have (P1)
- **Offline support**: Extension/CLI can scan without internet
- **Stage name mapping**: Map old stage names (4.9 → 6.0.0)
- **Recommendation engine**: Suggest next steps based on gaps
- **Progress tracking**: Show compliance score over time

### Nice to Have (P2)
- **AI-powered suggestions**: Use LLM to suggest missing artifacts
- **Custom rules**: Allow teams to define custom validation rules
- **Visual diff**: Show before/after folder structure

---

## Considered Options

### Option 1: Backend Scans Local Filesystem (REJECTED)

**Architecture**:
```
┌─────────────┐
│  User's PC  │
│  (no client)│
└─────┬───────┘
      │ POST /projects (project_path)
      ↓
┌─────────────┐
│   Backend   │
│  (FastAPI)  │
└─────┬───────┘
      │ os.walk(project_path)  ❌ READS USER FILES
      ↓
┌─────────────┐
│  Filesystem │
│  (User's)   │
└─────────────┘
```

**Implementation**:
```python
import os
from pathlib import Path

@router.post("/api/v1/projects/{project_id}/gap-analysis")
async def run_gap_analysis(project_id: UUID, project_path: str):
    """Backend scans user's filesystem (INSECURE!)"""
    # Backend reads user's local files directly
    folders = []

    for root, dirs, files in os.walk(project_path):
        for dir_name in dirs:
            folders.append(os.path.join(root, dir_name))

    # Compare against ruleset
    tier = get_project_tier(project_id)
    required_stages = get_required_stages(tier)
    missing_stages = [s for s in required_stages if s not in folders]

    return {
        "compliance_score": 1 - (len(missing_stages) / len(required_stages)),
        "missing_stages": missing_stages
    }
```

**Pros**:
- ✅ Simple implementation (single API endpoint)
- ✅ No client logic needed (backend does everything)

**Cons**:
- ❌ **Privacy violation**: Backend reads user's files directly
- ❌ **Security risk**: Path traversal attacks (user sends `../../../etc/passwd`)
- ❌ **Performance**: Backend CPU 100% if scanning 100 repos simultaneously
- ❌ **Cannot scale**: Backend needs access to ALL user filesystems
- ❌ **No offline support**: Requires backend connection

**Verdict**: ❌ REJECTED (privacy violation, security risk, cannot scale)

---

### Option 2: Client Scans, Backend Validates (REJECTED)

**Architecture**:
```
┌─────────────┐
│  Extension  │
│  (Client)   │
└─────┬───────┘
      │ 1. os.walk(local_repo)
      │ 2. POST /gap-analysis (ALL FILE PATHS)  ❌ SENDS USER DATA
      ↓
┌─────────────┐
│   Backend   │
│  (FastAPI)  │
└─────┬───────┘
      │ 3. Validate against ruleset
      │ 4. Return gaps
      ↓
```

**Implementation**:

**Client (Extension)**:
```typescript
async function runGapAnalysis(projectPath: string) {
  // Client scans local filesystem
  const folders = [];
  for await (const entry of walk(projectPath)) {
    if (entry.isDirectory) {
      folders.push(entry.path);  // Full file paths! ❌ Privacy issue
    }
  }

  // Send ALL file paths to backend
  const response = await fetch('/api/v1/gap-analysis', {
    method: 'POST',
    body: JSON.stringify({ folders })  // ❌ Sends user data to backend
  });

  return response.json();
}
```

**Backend**:
```python
@router.post("/api/v1/gap-analysis")
async def validate_gap_analysis(data: GapAnalysisRequest):
    """Backend validates submitted folder structure"""
    folders = data.folders  # ❌ Receives user file paths

    # Validate against ruleset
    tier = data.tier
    required_stages = get_required_stages(tier)
    missing_stages = [s for s in required_stages if s not in folders]

    return {
        "compliance_score": 1 - (len(missing_stages) / len(required_stages)),
        "missing_stages": missing_stages
    }
```

**Pros**:
- ✅ Client does scanning (offload work from backend)
- ✅ Backend validates (centralized logic)

**Cons**:
- ❌ **Privacy issue**: Full file paths sent to backend (`/home/user/secret-project/...`)
- ❌ **Bandwidth waste**: Sending 1000s of file paths over network
- ❌ **No offline support**: Requires backend connection
- ❌ **Tight coupling**: Client must match backend validation logic

**Verdict**: ❌ REJECTED (privacy issue, bandwidth waste, no offline support)

---

### Option 3: Hybrid - Backend Ruleset + Client Compute (APPROVED ✅)

**Architecture**:
```
┌─────────────┐
│  Extension  │
│  (Client)   │
└─────┬───────┘
      │ 1. GET /rulesets/professional (fetch ruleset)
      ↓
┌─────────────┐
│   Backend   │
│  (FastAPI)  │
└─────┬───────┘
      │ 2. Return ruleset (required stages, mappings)
      ↓
┌─────────────┐
│  Extension  │
│  (Client)   │
└─────┬───────┘
      │ 3. os.walk(local_repo) - Scan local filesystem
      │ 4. Compare against ruleset (LOCAL compute)
      │ 5. POST /gap-reports (SUMMARY only, no file paths)
      ↓
┌─────────────┐
│   Backend   │
│  (FastAPI)  │
└─────┬───────┘
      │ 6. Store gap report (for history/trending)
      ↓
```

**Implementation**:

**Backend - Ruleset API**:
```python
from pydantic import BaseModel

class StageRequirement(BaseModel):
    stage_id: str  # "00-foundation", "01-planning", etc
    required: bool  # MANDATORY vs OPTIONAL
    artifacts: list[str]  # Required files/folders

class Ruleset(BaseModel):
    version: str  # "6.0.0"
    tier: str  # "PROFESSIONAL"
    required_stages: list[StageRequirement]
    stage_mappings: dict[str, str]  # {"00-discover": "00-foundation"}

@router.get("/api/v1/rulesets/{tier}")
async def get_ruleset(tier: str) -> Ruleset:
    """
    Return ruleset for gap analysis (versioned, cached).

    Client downloads this ONCE and uses offline.
    """
    ruleset = {
        "version": "6.0.0",
        "tier": tier.upper(),
        "required_stages": [
            {
                "stage_id": "00-foundation",
                "required": True,
                "artifacts": ["README.md", "Business-Case.md"]
            },
            {
                "stage_id": "01-planning",
                "required": True,
                "artifacts": ["Requirements.md", "API-Design.md"]
            },
            # ... 10 stages for PROFESSIONAL tier
        ],
        "stage_mappings": {
            "00-discover": "00-foundation",  # 4.9 → 6.0.0 mapping
            "01-requirements": "01-planning"
        }
    }

    return Ruleset(**ruleset)
```

**Client - Gap Analysis Logic**:
```typescript
import * as fs from 'fs';
import * as path from 'path';

interface Ruleset {
  version: string;
  tier: string;
  required_stages: StageRequirement[];
  stage_mappings: Record<string, string>;
}

interface GapAnalysisResult {
  compliance_score: number;
  missing_stages: string[];
  existing_stages: string[];
  recommendations: string[];
}

async function runGapAnalysis(
  projectPath: string,
  tier: string
): Promise<GapAnalysisResult> {
  // 1. Fetch ruleset from backend (cached for 24 hours)
  const ruleset = await fetchRuleset(tier);

  // 2. Scan local filesystem (NO data sent to backend)
  const existingFolders = scanLocalFilesystem(projectPath);

  // 3. Apply stage name mappings (support old framework versions)
  const mappedFolders = existingFolders.map(folder => {
    return ruleset.stage_mappings[folder] || folder;
  });

  // 4. Compare against required stages (LOCAL compute)
  const requiredStages = ruleset.required_stages
    .filter(s => s.required)
    .map(s => s.stage_id);

  const missingStages = requiredStages.filter(
    stage => !mappedFolders.includes(stage)
  );

  const complianceScore = 1 - (missingStages.length / requiredStages.length);

  // 5. Generate recommendations
  const recommendations = generateRecommendations(missingStages, ruleset);

  // 6. Return result (computed locally, no backend needed)
  return {
    compliance_score: complianceScore,
    missing_stages: missingStages,
    existing_stages: mappedFolders,
    recommendations: recommendations
  };
}

function scanLocalFilesystem(projectPath: string): string[] {
  """Scan local filesystem for stage folders"""
  const folders: string[] = [];

  // Only scan top-level folders (stage folders)
  const entries = fs.readdirSync(projectPath, { withFileTypes: true });

  for (const entry of entries) {
    if (entry.isDirectory() && entry.name.match(/^\d{2}-/)) {
      folders.push(entry.name);  // e.g., "00-foundation"
    }
  }

  return folders;
}

function generateRecommendations(
  missingStages: string[],
  ruleset: Ruleset
): string[] {
  """Generate prioritized recommendations"""
  return missingStages.map(stage => {
    const requirement = ruleset.required_stages.find(r => r.stage_id === stage);
    return `Create ${stage} with: ${requirement.artifacts.join(', ')}`;
  });
}
```

**Backend - Gap Report Storage**:
```python
from pydantic import BaseModel

class GapReportSubmission(BaseModel):
    project_id: UUID
    compliance_score: float  # 0.0 to 1.0
    missing_stages: list[str]  # ["00-foundation", "01-planning"]
    existing_stages: list[str]  # ["02-design", "04-build"]
    framework_version: str  # "6.0.0"

@router.post("/api/v1/projects/{project_id}/gap-reports")
async def submit_gap_report(
    project_id: UUID,
    report: GapReportSubmission,
    db: Session = Depends(get_db)
):
    """
    Store gap report for historical tracking.

    NO user file paths are stored, only SUMMARY data.
    """
    gap_report = GapReport(
        project_id=project_id,
        compliance_score=report.compliance_score,
        missing_stages=report.missing_stages,
        existing_stages=report.existing_stages,
        framework_version=report.framework_version,
        analyzed_at=datetime.utcnow()
    )

    db.add(gap_report)
    db.commit()

    return {
        "status": "stored",
        "report_id": str(gap_report.id),
        "compliance_score": report.compliance_score
    }

@router.get("/api/v1/projects/{project_id}/gap-reports")
async def get_gap_reports(project_id: UUID, db: Session = Depends(get_db)):
    """
    Get historical gap reports (for trending).

    Shows compliance score over time.
    """
    reports = db.query(GapReport).filter(
        GapReport.project_id == project_id
    ).order_by(GapReport.analyzed_at.desc()).limit(10).all()

    return {
        "reports": [
            {
                "report_id": str(r.id),
                "compliance_score": r.compliance_score,
                "missing_stages": r.missing_stages,
                "analyzed_at": r.analyzed_at.isoformat()
            }
            for r in reports
        ]
    }
```

**Pros**:
- ✅ **Privacy**: User files NEVER leave client (only folder names submitted)
- ✅ **Performance**: Client CPU does scanning (backend saves 90% CPU)
- ✅ **Offline support**: Client can scan without internet (after fetching ruleset once)
- ✅ **Versioned rulesets**: Backend can upgrade ruleset (6.0.0 → 6.1.0) without client changes
- ✅ **Audit trail**: Backend stores gap reports for trending
- ✅ **Stage name mapping**: Supports old framework versions (4.9 → 6.0.0)
- ✅ **Scalability**: Backend serves lightweight rulesets (not scanning repos)

**Cons**:
- ⚠️ Client logic complexity (scan + compare + map stages)
- ⚠️ Ruleset versioning (need migration strategy)
- **Mitigation**: Well-tested client library, semantic versioning

**Verdict**: ✅ **APPROVED** (best privacy, performance, offline support)

---

## Decision Outcome

**Chosen Option**: **Option 3 - Hybrid (Backend Ruleset + Client Compute)**

### Implementation Details

#### 1. Database Schema

```sql
CREATE TABLE rulesets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  version VARCHAR(20) NOT NULL,       -- "6.0.0"
  tier tier_type NOT NULL,            -- LITE, STANDARD, PROFESSIONAL, ENTERPRISE
  ruleset_json JSONB NOT NULL,        -- Full ruleset definition
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  CONSTRAINT unique_ruleset_version_tier UNIQUE (version, tier)
);

CREATE TABLE gap_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  compliance_score FLOAT NOT NULL CHECK (compliance_score >= 0 AND compliance_score <= 1),
  missing_stages TEXT[] NOT NULL,     -- ["00-foundation", "01-planning"]
  existing_stages TEXT[] NOT NULL,    -- ["02-design", "04-build"]
  framework_version VARCHAR(20) NOT NULL,  -- "6.0.0"
  analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Metadata
  source VARCHAR(50) NOT NULL,        -- "extension", "cli", "web"
  client_version VARCHAR(20)          -- "1.2.3" (Extension/CLI version)
);

CREATE INDEX idx_gap_reports_project_id ON gap_reports(project_id);
CREATE INDEX idx_gap_reports_analyzed_at ON gap_reports(analyzed_at DESC);
```

#### 2. Ruleset Versioning

**Semantic Versioning**:
```yaml
Version Format: MAJOR.MINOR.PATCH (e.g., 6.0.0)

MAJOR: Breaking changes (stage rename, removal)
  Example: 5.x → 6.x (10 stages → 11 stages)
  Impact: Client MUST upgrade

MINOR: Additive changes (new optional stage, new tier)
  Example: 6.0.x → 6.1.x (add LITE tier)
  Impact: Client can continue (backward compatible)

PATCH: Fixes (typo in stage name, artifact clarification)
  Example: 6.0.0 → 6.0.1 (fix typo in stage name)
  Impact: Client can continue (no logic change)
```

**Ruleset Migration**:
```python
# Seed initial ruleset (v6.0.0)
def seed_rulesets():
    rulesets = [
        {
            "version": "6.0.0",
            "tier": "LITE",
            "ruleset_json": {
                "required_stages": [
                    {"stage_id": "00-foundation", "required": True},
                    {"stage_id": "01-planning", "required": True},
                    {"stage_id": "02-design", "required": True},
                    {"stage_id": "04-build", "required": True}
                ],
                "stage_mappings": {
                    "00-discover": "00-foundation"
                }
            }
        },
        {
            "version": "6.0.0",
            "tier": "PROFESSIONAL",
            "ruleset_json": {
                "required_stages": [
                    # ... 10 stages
                ],
                "stage_mappings": {
                    "00-discover": "00-foundation",
                    "01-requirements": "01-planning"
                }
            }
        }
    ]

    for ruleset_data in rulesets:
        ruleset = Ruleset(**ruleset_data)
        db.add(ruleset)
    db.commit()
```

#### 3. Stage Name Mapping (Framework Migration)

**Problem**: Projects using old framework (SDLC 4.9) have different stage names

**Solution**: Stage name mapping in ruleset

```json
{
  "stage_mappings": {
    "00-discover": "00-foundation",      // 4.9 → 6.0.0
    "01-requirements": "01-planning",    // 4.9 → 6.0.0
    "02-design-architecture": "02-design"
  }
}
```

**Client applies mapping**:
```typescript
function applyStageMapping(
  existingFolders: string[],
  mappings: Record<string, string>
): string[] {
  return existingFolders.map(folder => {
    // If old stage name found, map to new name
    return mappings[folder] || folder;
  });
}

// Example
const existingFolders = ["00-discover", "01-requirements"];
const mappings = {
  "00-discover": "00-foundation",
  "01-requirements": "01-planning"
};

const mappedFolders = applyStageMapping(existingFolders, mappings);
// Result: ["00-foundation", "01-planning"]
```

#### 4. Offline Support

**Ruleset Caching**:
```typescript
import * as fs from 'fs';
import * as path from 'path';

const CACHE_DIR = path.join(os.homedir(), '.sdlc-orchestrator', 'cache');
const CACHE_TTL = 24 * 60 * 60 * 1000;  // 24 hours

async function fetchRuleset(tier: string): Promise<Ruleset> {
  const cacheFile = path.join(CACHE_DIR, `ruleset-${tier}.json`);

  // Check cache
  if (fs.existsSync(cacheFile)) {
    const stats = fs.statSync(cacheFile);
    const age = Date.now() - stats.mtimeMs;

    if (age < CACHE_TTL) {
      // Cache hit
      const cached = fs.readFileSync(cacheFile, 'utf-8');
      return JSON.parse(cached);
    }
  }

  // Cache miss or expired, fetch from backend
  try {
    const response = await fetch(`/api/v1/rulesets/${tier}`);
    const ruleset = await response.json();

    // Write to cache
    fs.mkdirSync(CACHE_DIR, { recursive: true });
    fs.writeFileSync(cacheFile, JSON.stringify(ruleset));

    return ruleset;
  } catch (error) {
    // Offline? Use stale cache
    if (fs.existsSync(cacheFile)) {
      console.warn('Using stale ruleset cache (offline mode)');
      const cached = fs.readFileSync(cacheFile, 'utf-8');
      return JSON.parse(cached);
    }

    throw new Error('Cannot fetch ruleset and no cache available');
  }
}
```

#### 5. Gap Report Trending

**Dashboard - Compliance Over Time**:
```typescript
async function fetchComplianceTrend(projectId: string) {
  const response = await fetch(`/api/v1/projects/${projectId}/gap-reports`);
  const data = await response.json();

  // Chart data
  const chartData = data.reports.map(r => ({
    date: new Date(r.analyzed_at),
    compliance: r.compliance_score * 100  // 0.75 → 75%
  }));

  return chartData;
}
```

**Example Chart**:
```
Compliance Score Over Time

100% ┤                                     ●
     │                               ●
 75% ┤                         ●
     │                   ●
 50% ┤             ●
     │       ●
 25% ┤ ●
     │
  0% └─────────────────────────────────────
     Jan  Feb  Mar  Apr  May  Jun  Jul
```

---

## Consequences

### Positive

1. **Privacy**:
   - ✅ User files NEVER sent to backend (only folder names)
   - ✅ Full file paths stay on client (no privacy violation)
   - ✅ GDPR compliant (no user data processing)

2. **Performance**:
   - ✅ Backend saves 90% CPU (no filesystem scanning)
   - ✅ Client scan <10s for typical repo (1000 files)
   - ✅ Offline support (works without internet after initial ruleset fetch)

3. **Scalability**:
   - ✅ Backend serves lightweight rulesets (kilobytes, not gigabytes)
   - ✅ Client does heavy lifting (distributed compute)
   - ✅ Scales to 100K teams (backend only stores summaries)

4. **Flexibility**:
   - ✅ Versioned rulesets (Framework 6.0.0 → 6.1.0 upgrade path)
   - ✅ Stage name mapping (support old framework versions)
   - ✅ Audit trail (gap reports stored for trending)

### Negative

1. **Complexity**:
   - ⚠️ Client logic complexity (scan + compare + map stages)
   - ⚠️ Ruleset versioning (need migration strategy)
   - **Mitigation**: Well-tested client library, semantic versioning

2. **Client Updates**:
   - ⚠️ Major framework changes require client updates
   - ⚠️ Extension/CLI need to download new logic
   - **Mitigation**: Auto-update mechanism, backward compatibility

---

## Alternatives Not Chosen

### Alternative A: Backend Scans via SSH

Backend connects to user machine via SSH and scans filesystem remotely.

**Pros**: No client logic needed
**Cons**: Security nightmare (SSH credentials), complex setup
**Verdict**: Rejected (security risk, complex setup)

### Alternative B: AI-Powered Gap Analysis

Use LLM to analyze project structure and suggest improvements.

**Pros**: Smart recommendations, natural language output
**Cons**: Expensive (LLM API costs), slower (<10s target)
**Verdict**: Deferred to P2 (nice-to-have for recommendations)

### Alternative C: Browser-Based Scanning

Use File System Access API in web browser to scan filesystem.

**Pros**: No Extension/CLI needed (web-only)
**Cons**: Limited browser support (Chrome only), security restrictions
**Verdict**: Deferred to P2 (nice-to-have for web dashboard)

---

## References

- **SDLC Framework 6.0.0**: Stage definitions and requirements
- **Extension Architecture**: Client-side scanning implementation
- **ADR-044**: GitHub Integration Strategy (clone-local approach)
- **ADR-021**: SDLC Scanner (original gap analysis design)

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| Jan 25, 2026 | Explored backend scanning | Simple, but privacy violation |
| Jan 27, 2026 | Explored client scanning | Privacy-safe, but tight coupling |
| Jan 29, 2026 | Explored hybrid approach | Best privacy + performance trade-off |
| Jan 30, 2026 | **APPROVED Hybrid** | Backend ruleset + client compute |
| Jan 30, 2026 | Add stage name mapping | Support framework migrations (4.9 → 6.0.0) |
| Jan 30, 2026 | Add offline support | 24-hour ruleset cache |

---

## Implementation Checklist

- [ ] Database migration: `s129_002_gap_reports.py`
- [ ] Backend API: `GET /api/v1/rulesets/{tier}`
- [ ] Backend API: `POST /api/v1/projects/{id}/gap-reports`
- [ ] Backend API: `GET /api/v1/projects/{id}/gap-reports` (trending)
- [ ] Seed rulesets: LITE, STANDARD, PROFESSIONAL, ENTERPRISE (v6.0.0)
- [ ] Extension: Ruleset cache (24-hour TTL)
- [ ] Extension: Gap analysis logic (scan + compare)
- [ ] Extension: Stage name mapping (4.9 → 6.0.0)
- [ ] CLI: Gap analysis command (`sdlcctl gap-analysis`)
- [ ] Tests: Ruleset API tests
- [ ] Tests: Gap analysis logic tests
- [ ] Tests: Stage name mapping tests
- [ ] Documentation: Gap analysis architecture guide
- [ ] Documentation: Ruleset versioning guide

---

**Status**: ✅ **APPROVED FOR SPRINT 129**
**Approval**: CTO + Backend Lead + Extension Lead (Jan 30, 2026)
**Implementation**: Sprint 129 (Feb 17-28, 2026)
**Review Date**: Feb 28, 2026 (Sprint 129 demo)

---

**Document Version**: v1.0
**Author**: Backend Lead + Extension Lead
**Reviewers**: CTO, Product Owner, Privacy Team
**Last Updated**: January 30, 2026
