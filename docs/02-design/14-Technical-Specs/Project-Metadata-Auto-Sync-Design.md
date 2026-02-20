# Project Metadata Auto-Sync Technical Specification

**Status**: ✅ APPROVED (CTO)
**Version**: 1.0.0
**Date**: February 10, 2026
**Sprint**: Sprint 172
**Author**: Development Team
**Approver**: CTO
**Stage**: 02-design (HOW - Architecture & Design)
**Framework**: SDLC 6.1.0

---

## Executive Summary

Project Metadata Auto-Sync ensures database project records stay synchronized with repository reality by parsing canonical metadata files (`.sdlc-config.json`, `AGENTS.md`, `CLAUDE.md`, `README.md`) on project access.

**Business Value**:
- ✅ Always accurate project information in dashboard
- ✅ Eliminates 90% of manual metadata updates
- ✅ Better UX (users see current sprint, framework version, status)
- ✅ Follows ADR-029 (Static AGENTS.md + Dynamic Overlay pattern)

**Implementation Approach**: Phased rollout
- ✅ **Phase 1** (COMPLETE): SQL migration to fix SDLC-Orchestrator metadata
- 🔄 **Phase 2** (Sprint 172): Auto-sync service implementation
- ⏳ **Phase 3** (Future): GitHub webhook integration

---

## Problem Statement

### Current State

**Issue**: Project metadata in database drifts from repository reality over time.

**Example** (SDLC-Orchestrator project):
```yaml
Database (outdated):
  description: "SDLC 4.9.1 | MVP Development"
  framework: 4.9.1
  status: MVP Development
  target: G6 by Week 17

Repository Reality:
  description: "SDLC 6.1.0 | G3 Ship Ready (98.2%)"
  framework: 6.1.0
  status: Sprint 171 (Market Expansion - 90%)
  target: Vietnam SME Pilot Q1 2026
```

**Impact**:
- ❌ Users see outdated project information
- ❌ Dashboards show incorrect sprint/status
- ❌ Manual updates required every sprint (time-consuming)
- ❌ Risk of inconsistency across team members

### Root Cause

Database is **write-only** - no sync mechanism from repository files.

---

## Design Principles

### 1. **Vendor Neutrality** (ADR-029 Compliance)

SDLC Orchestrator works with **all AI codex tools**, not just Claude Code.

```yaml
Supported Tools:
  - Claude Code (Anthropic)
  - Cursor (Anysphere)
  - GitHub Copilot (Microsoft)
  - OpenCode (OpenAI)
  - RooCode (community)
```

**Implication**: Metadata must follow **industry standards**, not proprietary formats.

### 2. **Static + Dynamic Overlay** (ADR-029)

```
┌─────────────────────────────────────────────────────────┐
│ LAYER A: STATIC (Committed to repo)                     │
│  - .sdlc-config.json (project config)                   │
│  - AGENTS.md (conventions, setup)                       │
│  - CLAUDE.md (framework version, tech stack)            │
│  - README.md (project description)                      │
├─────────────────────────────────────────────────────────┤
│ LAYER B: DYNAMIC OVERLAY (Runtime API)                  │
│  - Current gate status                                  │
│  - Sprint context (velocity, blockers)                  │
│  - Incident constraints                                 │
│  - Strict mode flags                                    │
└─────────────────────────────────────────────────────────┘
```

**Decision**: Phase 2 syncs **LAYER A only** (static metadata). LAYER B provided via API.

### 3. **Source of Truth Priority**

```yaml
1. .sdlc-config.json (CANONICAL)
   - project.id, project.name, tier
   - Official project configuration

2. AGENTS.md (CURRENT STATE)
   - current_sprint (line 21)
   - sprint_status (line 22)
   - Current work in progress

3. CLAUDE.md (FRAMEWORK VERSION)
   - framework_version (line 4)
   - gate_status (line 5)
   - Tech stack context

4. README.md (DESCRIPTION)
   - First 200 chars
   - User-facing description

5. Git Metadata (TIMESTAMPS)
   - last_commit_date
   - last_commit_sha
```

### 4. **Performance First**

```yaml
Fast Path (Local Filesystem):
  - Read time: <100ms
  - No credentials needed
  - Works offline

Cache Strategy:
  - TTL: 5 minutes (Redis)
  - Skip sync if last_sync < 5 min ago
  - Background refresh (non-blocking)

UI Non-Blocking:
  - Mutation runs in background
  - Page loads with cached data
  - Updates UI when sync completes
```

---

## Architecture

### System Context Diagram

```
┌────────────────────────────────────────────────────────────┐
│                        USER                                 │
└────────────────────┬───────────────────────────────────────┘
                     │ visits /app/projects/{id}
                     ▼
┌────────────────────────────────────────────────────────────┐
│               FRONTEND (React + Next.js)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ useProjectSync() hook                                │  │
│  │  - Auto-calls on mount                               │  │
│  │  - 5-min cache check                                 │  │
│  │  - Updates UI on success                             │  │
│  └────────────────────┬─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │ POST /projects/{id}/sync
                       ▼
┌────────────────────────────────────────────────────────────┐
│               BACKEND (FastAPI + Python)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ProjectSyncService                                   │  │
│  │  - Parse .sdlc-config.json                           │  │
│  │  - Parse AGENTS.md (lines 20-30)                     │  │
│  │  - Parse CLAUDE.md (lines 1-10)                      │  │
│  │  - Parse README.md (first paragraph)                 │  │
│  │  - Get git metadata (optional)                       │  │
│  └────────────────────┬─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │ read files
                       ▼
┌────────────────────────────────────────────────────────────┐
│           REPOSITORY (Local Filesystem)                     │
│  ├── .sdlc-config.json     (project config)                │
│  ├── AGENTS.md             (current sprint)                │
│  ├── CLAUDE.md             (framework version)             │
│  └── README.md             (description)                   │
└────────────────────────────────────────────────────────────┘
                       │ update database
                       ▼
┌────────────────────────────────────────────────────────────┐
│           DATABASE (PostgreSQL)                             │
│  projects table:                                            │
│    - description (updated)                                  │
│    - tier (updated)                                         │
│    - current_sprint (updated)                               │
│    - framework_version (updated)                            │
└────────────────────────────────────────────────────────────┘
```

### Component Design

#### 1. **ProjectSyncService** (Backend)

```python
# backend/app/services/project_sync_service.py

class ProjectSyncService:
    """
    Sync project metadata from repository files to database.

    Follows ADR-029: Static AGENTS.md + Dynamic Overlay pattern.
    Source priority: .sdlc-config.json > AGENTS.md > CLAUDE.md > README.md
    """

    async def sync_project_metadata(
        self,
        project_id: UUID,
        repo_path: str,
        db: AsyncSession
    ) -> ProjectMetadata:
        """
        Main orchestration method.

        Args:
            project_id: Project UUID
            repo_path: Absolute path to repository
            db: Database session

        Returns:
            ProjectMetadata with extracted fields

        Raises:
            FileNotFoundError: If repo_path doesn't exist
            ValidationError: If required files missing
        """

        # 1. Validate repo path exists
        if not Path(repo_path).exists():
            raise FileNotFoundError(f"Repository not found: {repo_path}")

        # 2. Parse metadata files in priority order
        config = await self._parse_sdlc_config(repo_path)
        agents_md = await self._parse_agents_md(repo_path)
        claude_md = await self._parse_claude_md(repo_path)
        readme = await self._parse_readme(repo_path)
        git_meta = await self._get_git_metadata(repo_path)

        # 3. Merge metadata (priority: config > agents > claude > readme)
        metadata = ProjectMetadata(
            id=config.get("project", {}).get("id", project_id),
            name=config.get("project", {}).get("name"),
            tier=config.get("tier", "professional"),
            description=readme.get("description"),
            current_sprint=agents_md.get("current_sprint"),
            sprint_status=agents_md.get("sprint_status"),
            framework_version=claude_md.get("framework_version"),
            gate_status=claude_md.get("gate_status"),
            last_commit_date=git_meta.get("commit_date"),
            last_commit_sha=git_meta.get("commit_sha")
        )

        # 4. Update database
        project = await db.get(Project, project_id)
        if not project:
            raise NotFoundError(f"Project {project_id} not found")

        project.description = metadata.description
        project.tier = metadata.tier
        # ... update other fields

        await db.commit()

        return metadata

    async def _parse_sdlc_config(self, repo_path: str) -> dict:
        """Parse .sdlc-config.json"""
        config_path = Path(repo_path) / ".sdlc-config.json"
        if not config_path.exists():
            logger.warning(f"Missing .sdlc-config.json in {repo_path}")
            return {}

        with open(config_path, "r") as f:
            return json.load(f)

    async def _parse_agents_md(self, repo_path: str) -> dict:
        """
        Parse AGENTS.md for current sprint info.

        Expected format (lines 20-23):
        **Sprint 171**: Market Expansion Foundation (Phase 6) — ✅ 90% COMPLETE
        """
        agents_path = Path(repo_path) / "AGENTS.md"
        if not agents_path.exists():
            return {}

        with open(agents_path, "r") as f:
            lines = f.readlines()

        # Extract sprint info from lines 20-23
        for i in range(19, min(30, len(lines))):
            line = lines[i]
            if "**Sprint" in line:
                # Parse: **Sprint 171**: Market Expansion Foundation (Phase 6) — ✅ 90% COMPLETE
                match = re.match(r'\*\*Sprint (\d+)\*\*:\s*(.+?)\s*—\s*(.+)', line)
                if match:
                    return {
                        "current_sprint": f"Sprint {match.group(1)}",
                        "sprint_description": match.group(2).strip(),
                        "sprint_status": match.group(3).strip()
                    }

        return {}

    async def _parse_claude_md(self, repo_path: str) -> dict:
        """
        Parse CLAUDE.md for framework version and gate status.

        Expected format (lines 3-5):
        **Version**: 3.3.0
        **Status**: Gate G3 APPROVED - Ship Ready (98.2%)
        **Framework**: SDLC 6.0.5
        """
        claude_path = Path(repo_path) / "CLAUDE.md"
        if not claude_path.exists():
            return {}

        with open(claude_path, "r") as f:
            lines = f.readlines()

        metadata = {}
        for i in range(min(10, len(lines))):
            line = lines[i]
            if "**Framework**:" in line:
                # Parse: **Framework**: SDLC 6.0.5
                match = re.search(r'SDLC\s+([\d.]+)', line)
                if match:
                    metadata["framework_version"] = f"SDLC {match.group(1)}"
            elif "**Status**:" in line:
                # Parse: **Status**: Gate G3 APPROVED - Ship Ready (98.2%)
                status = line.split("**Status**:")[1].strip()
                metadata["gate_status"] = status

        return metadata

    async def _parse_readme(self, repo_path: str) -> dict:
        """Parse README.md for project description (first 200 chars)"""
        readme_path = Path(repo_path) / "README.md"
        if not readme_path.exists():
            return {}

        with open(readme_path, "r") as f:
            content = f.read()

        # Get first paragraph (skip title lines starting with #)
        lines = content.split("\n")
        description_lines = []
        for line in lines:
            if line.strip() and not line.startswith("#"):
                description_lines.append(line.strip())
                if len(" ".join(description_lines)) > 200:
                    break

        description = " ".join(description_lines)[:200]
        return {"description": description}

    async def _get_git_metadata(self, repo_path: str) -> dict:
        """Get git metadata (last commit date, SHA) - optional"""
        try:
            # Get last commit date
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ci"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            commit_date = result.stdout.strip() if result.returncode == 0 else None

            # Get last commit SHA
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            commit_sha = result.stdout.strip() if result.returncode == 0 else None

            return {
                "commit_date": commit_date,
                "commit_sha": commit_sha[:8] if commit_sha else None
            }
        except Exception as e:
            logger.warning(f"Failed to get git metadata: {e}")
            return {}
```

#### 2. **API Endpoint** (Backend)

```python
# backend/app/api/routes/projects.py

@router.post("/{project_id}/sync", response_model=ProjectResponse)
async def sync_project_metadata(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ProjectResponse:
    """
    Sync project metadata from repository files.

    **Flow**:
    1. Check 5-min cache (skip if recently synced)
    2. Parse .sdlc-config.json, AGENTS.md, CLAUDE.md, README.md
    3. Update database with extracted metadata
    4. Return updated project

    **Cache Strategy**:
    - TTL: 5 minutes (avoid excessive file I/O)
    - Key: `project:sync:{project_id}`

    **Auth**: Project members only

    **Performance**: <200ms (local filesystem read)
    """

    # 1. Get project
    project = await get_project_or_404(project_id, db)

    # 2. Check permissions (user must be project member)
    if not await is_project_member(current_user.id, project_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a project member"
        )

    # 3. Check cache (skip if synced < 5 min ago)
    cache_key = f"project:sync:{project_id}"
    last_sync = await redis.get(cache_key)
    if last_sync:
        last_sync_time = datetime.fromisoformat(last_sync)
        if datetime.now() - last_sync_time < timedelta(minutes=5):
            logger.info(f"Skipping sync for {project_id} (cached)")
            return project

    # 4. Sync metadata
    sync_service = ProjectSyncService()
    try:
        metadata = await sync_service.sync_project_metadata(
            project_id=project_id,
            repo_path=project.repo_path or f"/home/nqh/shared/{project.name}",
            db=db
        )

        # 5. Update cache
        await redis.set(
            cache_key,
            datetime.now().isoformat(),
            ex=300  # 5 minutes TTL
        )

        logger.info(f"Synced metadata for project {project_id}")

        # 6. Return updated project
        await db.refresh(project)
        return project

    except FileNotFoundError as e:
        logger.error(f"Repository not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to sync project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )
```

#### 3. **Frontend Integration**

```typescript
// frontend/src/hooks/useProjectSync.ts

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { syncProjectMetadata } from '@/lib/api';

export function useProjectSync(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => syncProjectMetadata(projectId),
    onSuccess: (updatedProject) => {
      // Update cache immediately (no waiting for refetch)
      queryClient.setQueryData(['project', projectId], updatedProject);

      // Invalidate project list to refresh on other pages
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: (error) => {
      console.error('Project sync failed:', error);
      // Optional: Show toast notification
    }
  });
}

// frontend/src/app/app/projects/[id]/page.tsx

export default function ProjectDetailPage({ params }: { params: { id: string } }) {
  const { data: project, isLoading } = useProject(params.id);
  const syncMutation = useProjectSync(params.id);

  // Auto-sync on mount (backend checks cache, so safe to call)
  useEffect(() => {
    syncMutation.mutate();
  }, [params.id]);

  return (
    <div>
      {/* Project details */}
      <h1>{project?.name}</h1>
      <p>{project?.description}</p>

      {/* Sync indicator (optional) */}
      {syncMutation.isPending && (
        <span className="text-sm text-muted-foreground">
          Syncing metadata...
        </span>
      )}
    </div>
  );
}
```

---

## Data Model

### ProjectMetadata Schema

```python
from pydantic import BaseModel
from typing import Optional

class ProjectMetadata(BaseModel):
    """
    Metadata extracted from repository files.

    Source priority:
    1. .sdlc-config.json (canonical config)
    2. AGENTS.md (current state)
    3. CLAUDE.md (framework version)
    4. README.md (description)
    5. Git metadata (timestamps)
    """

    # From .sdlc-config.json
    id: UUID
    name: str
    tier: str  # "lite" | "professional" | "enterprise"

    # From AGENTS.md (lines 20-30)
    current_sprint: Optional[str] = None  # "Sprint 171"
    sprint_status: Optional[str] = None   # "90% COMPLETE"
    sprint_description: Optional[str] = None

    # From CLAUDE.md (lines 1-10)
    framework_version: Optional[str] = None  # "SDLC 6.1.0"
    gate_status: Optional[str] = None        # "G3 Ship Ready (98.2%)"

    # From README.md (first paragraph)
    description: Optional[str] = None

    # From Git metadata
    last_commit_date: Optional[str] = None
    last_commit_sha: Optional[str] = None
```

### Database Schema Updates

```sql
-- No new tables needed (Phase 2)
-- Uses existing `projects` table

-- Migration: Add columns for synced metadata (optional - can use existing description field)
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS current_sprint VARCHAR(50),
ADD COLUMN IF NOT EXISTS framework_version VARCHAR(20),
ADD COLUMN IF NOT EXISTS gate_status VARCHAR(100),
ADD COLUMN IF NOT EXISTS last_sync_at TIMESTAMP;

-- Index for faster sync checks
CREATE INDEX IF NOT EXISTS idx_projects_last_sync
ON projects(last_sync_at);
```

---

## API Specification

### POST /api/v1/projects/{project_id}/sync

**Description**: Sync project metadata from repository files

**Auth**: JWT Bearer token (project member required)

**Request**:
```http
POST /api/v1/projects/c0000000-0000-0000-0000-000000000003/sync
Authorization: Bearer {token}
```

**Response** (200 OK):
```json
{
  "id": "c0000000-0000-0000-0000-000000000003",
  "name": "SDLC-Orchestrator",
  "description": "Operating System for Software 3.0 | SDLC 6.1.0...",
  "tier": "professional",
  "current_sprint": "Sprint 171",
  "framework_version": "SDLC 6.1.0",
  "gate_status": "G3 Ship Ready (98.2%)",
  "created_at": "2025-11-13T09:00:00Z",
  "updated_at": "2026-02-10T11:24:14Z",
  "last_sync_at": "2026-02-10T11:30:00Z"
}
```

**Errors**:
- `401 Unauthorized`: Invalid/missing token
- `403 Forbidden`: Not a project member
- `404 Not Found`: Project or repository not found
- `500 Internal Server Error`: Sync failed (file parsing error)

**Cache Behavior**:
- If synced < 5 min ago → skip sync, return cached project
- Else → parse files, update DB, set cache, return updated project

**Performance**:
- Cache hit: <50ms (skip sync)
- Cache miss: <200ms (parse 4 files + update DB)

---

## Testing Strategy

### Unit Tests

```python
# backend/tests/unit/services/test_project_sync_service.py

@pytest.mark.asyncio
async def test_parse_sdlc_config_valid():
    """Test parsing valid .sdlc-config.json"""
    service = ProjectSyncService()
    config = await service._parse_sdlc_config("/path/to/repo")

    assert config["project"]["name"] == "SDLC-Orchestrator"
    assert config["tier"] == "professional"

@pytest.mark.asyncio
async def test_parse_agents_md_sprint_171():
    """Test extracting Sprint 171 from AGENTS.md"""
    service = ProjectSyncService()
    agents_md = await service._parse_agents_md("/path/to/repo")

    assert agents_md["current_sprint"] == "Sprint 171"
    assert "90% COMPLETE" in agents_md["sprint_status"]

@pytest.mark.asyncio
async def test_parse_claude_md_framework_version():
    """Test extracting framework version from CLAUDE.md"""
    service = ProjectSyncService()
    claude_md = await service._parse_claude_md("/path/to/repo")

    assert claude_md["framework_version"] == "SDLC 6.1.0"
    assert "G3" in claude_md["gate_status"]
```

### Integration Tests

```python
# backend/tests/integration/test_project_sync_api.py

@pytest.mark.asyncio
async def test_sync_project_metadata_success(client, auth_headers, test_project):
    """Test successful project metadata sync"""
    response = await client.post(
        f"/api/v1/projects/{test_project.id}/sync",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] != ""  # Updated
    assert data["last_sync_at"] is not None

@pytest.mark.asyncio
async def test_sync_project_metadata_cache(client, auth_headers, test_project):
    """Test cache prevents duplicate syncs within 5 minutes"""
    # First sync
    response1 = await client.post(
        f"/api/v1/projects/{test_project.id}/sync",
        headers=auth_headers
    )

    # Second sync immediately (should use cache)
    response2 = await client.post(
        f"/api/v1/projects/{test_project.id}/sync",
        headers=auth_headers
    )

    assert response1.status_code == 200
    assert response2.status_code == 200
    # Check logs show "Skipping sync (cached)"
```

### E2E Tests

```typescript
// frontend/e2e/project-metadata-sync.spec.ts

test('auto-syncs project metadata on page load', async ({ page }) => {
  await page.goto('/app/projects/c0000000-0000-0000-0000-000000000003');

  // Wait for sync to complete
  await page.waitForResponse(
    response => response.url().includes('/sync') && response.status() === 200
  );

  // Verify updated metadata displayed
  await expect(page.locator('h1')).toContainText('SDLC-Orchestrator');
  await expect(page.locator('text=SDLC 6.1.0')).toBeVisible();
  await expect(page.locator('text=Sprint 171')).toBeVisible();
});
```

---

## Performance Requirements

### Latency Targets

```yaml
API Response Time (p95):
  Cache Hit (skip sync): <50ms
  Cache Miss (full sync): <200ms

File Parsing Time:
  .sdlc-config.json: <10ms
  AGENTS.md: <20ms
  CLAUDE.md: <20ms
  README.md: <30ms
  Git metadata: <50ms (optional)

Total Pipeline: <130ms (well under 200ms target)
```

### Scalability

```yaml
Concurrent Requests:
  - 100 users → 100 sync requests
  - Cache hit rate: ~80% (reuses 5-min cache)
  - Actual syncs: ~20 requests
  - File I/O: 20 × 4 files = 80 file reads
  - Performance: <200ms per request (acceptable)

Future Optimization (Phase 3):
  - GitHub API (remote repos)
  - Background job (non-blocking)
  - Webhook triggers (real-time sync)
```

---

## Security Considerations

### 1. **File Access Control**

```yaml
Risk: Malicious user reads arbitrary files via repo_path manipulation

Mitigation:
  - Whitelist allowed repo paths (e.g., /home/nqh/shared/*)
  - Validate repo_path is directory (not file)
  - Check user has project membership before sync
  - Sanitize file paths (prevent ../../../etc/passwd)
```

### 2. **File Content Validation**

```yaml
Risk: Malicious .sdlc-config.json with code injection

Mitigation:
  - JSON schema validation (reject unexpected fields)
  - Max file size: 50KB (.sdlc-config.json), 100KB (AGENTS.md, CLAUDE.md)
  - No executable code blocks in parsed content
  - Escape special chars before database insert
```

### 3. **Rate Limiting**

```yaml
Risk: DoS via excessive sync requests

Mitigation:
  - 5-min cache (prevents spam)
  - Rate limit: 10 sync requests per user per minute
  - Background job for batch syncs (Phase 3)
```

---

## Rollout Plan

### Phase 1: Quick Fix ✅ COMPLETE

**Date**: Feb 10, 2026
**Duration**: 30 min

- ✅ SQL migration to fix SDLC-Orchestrator metadata
- ✅ Verify on web app

### Phase 2: Auto-Sync MVP (Sprint 172)

**Date**: Feb 10-14, 2026
**Duration**: 3-4 hours

**Day 1** (2 hours):
- Implement `ProjectSyncService` with 4 parsers
- Implement POST `/projects/{id}/sync` endpoint
- Unit tests (95%+ coverage)

**Day 2** (1 hour):
- Frontend `useProjectSync()` hook
- Auto-call on project page mount
- Cache behavior testing

**Day 3** (1 hour):
- Integration tests (API + database)
- E2E test (full user flow)
- Performance profiling

**Day 4** (0.5 hour):
- Deploy to staging
- Smoke test with real projects
- Monitor logs for errors

### Phase 3: Production Enhancements (Sprint 173+)

**Features**:
- GitHub API support (remote repos)
- Webhook integration (push → auto-sync)
- Background job (non-blocking)
- Admin dashboard (sync status for all projects)

---

## Success Metrics

```yaml
Phase 2 Completion Criteria:
  ✅ POST /projects/{id}/sync endpoint live
  ✅ 95%+ test coverage (unit + integration)
  ✅ <200ms p95 latency (measured)
  ✅ E2E test passing
  ✅ SDLC-Orchestrator project metadata accurate

Business KPIs (30 days post-launch):
  - 90% reduction in manual metadata updates
  - 100% project metadata accuracy
  - <5 support tickets related to outdated info
  - User satisfaction: 4.5+ / 5
```

---

## Appendices

### A. File Format Examples

#### .sdlc-config.json

```json
{
  "version": "1.0.0",
  "project": {
    "id": "c0000000-0000-0000-0000-000000000003",
    "name": "SDLC-Orchestrator",
    "description": "First Governance-First Platform on SDLC 6.1.0"
  },
  "tier": "professional",
  "team_size": 8
}
```

#### AGENTS.md (lines 20-23)

```markdown
## Current Stage

**Sprint 171**: Market Expansion Foundation (Phase 6) — ✅ 90% COMPLETE
- Days 1–4: ✅ complete (i18n infra + Vietnamese UI + VND pricing)
```

#### CLAUDE.md (lines 3-5)

```markdown
**Version**: 3.3.0
**Status**: Gate G3 APPROVED - Ship Ready (98.2%)
**Framework**: SDLC 6.1.0
```

### B. Error Handling Matrix

| Error Scenario | HTTP Status | User Message | Action |
|----------------|-------------|--------------|--------|
| Repository not found | 404 | "Repository not accessible" | Check repo_path config |
| Missing .sdlc-config.json | 200 | "Partial sync (missing config)" | Use defaults |
| Invalid JSON syntax | 500 | "Config file corrupted" | Fix .sdlc-config.json |
| Permission denied | 403 | "Access denied" | Check project membership |
| File too large | 413 | "Config file too large" | Reduce file size |

---

**Document Status**: ✅ APPROVED FOR IMPLEMENTATION
**Next Steps**: Create Sprint 172 Plan → Implement Phase 2 → Test → Deploy
