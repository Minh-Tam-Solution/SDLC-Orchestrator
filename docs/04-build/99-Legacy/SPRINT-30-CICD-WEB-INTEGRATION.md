# Sprint 30: CI/CD & Web Integration
## GitHub Actions Gate & Dashboard Integration

**Sprint**: 30
**Duration**: 5 days (January 13-17, 2026)
**Status**: PLANNED
**Team**: 2 Backend, 1 DevOps, 1 Frontend
**Framework**: SDLC 5.1.3 Complete Lifecycle
**Phase**: PHASE-04 (SDLC Structure Validator)
**Prerequisites**: Sprint 29 Complete

---

## Sprint Goal

Add CI/CD pipeline gate (GitHub Actions) and web dashboard integration for SDLC 5.1.3 structure validation, enabling automated compliance enforcement and visual compliance reporting across all NQH portfolio projects.

---

## Sprint Backlog

### Day 1: GitHub Action (Jan 13, 2026)

**Owner**: DevOps Engineer
**Story Points**: 8

#### Tasks

| Task | Description | Estimate | Priority |
|------|-------------|----------|----------|
| T1.1 | Create GitHub Action workflow template | 2h | P0 |
| T1.2 | Implement PR commenting with validation results | 2h | P0 |
| T1.3 | Add validation badge generator | 1h | P1 |
| T1.4 | Create reusable action package | 2h | P0 |
| T1.5 | Test with SDLC-Orchestrator repo | 2h | P0 |

#### Acceptance Criteria

```yaml
AC-1.1: GitHub Action triggers on push/PR to docs/**
AC-1.2: PR comments show validation status with details
AC-1.3: Badge shows PASSED/FAILED status
AC-1.4: Action runs in <30s
```

#### GitHub Action Specification

```yaml
# .github/workflows/sdlc-validate.yml
name: SDLC 5.1.3 Structure Validation

on:
  push:
    branches: [main, develop]
    paths:
      - 'docs/**'
      - '.sdlc-config.json'
  pull_request:
    branches: [main]
    paths:
      - 'docs/**'
      - '.sdlc-config.json'

jobs:
  validate:
    runs-on: ubuntu-latest
    name: SDLC Structure Validation

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install SDLC CLI
        run: pip install sdlcctl

      - name: Run Validation
        id: validate
        run: |
          sdlcctl validate --format json > validation.json
          echo "result=$(cat validation.json | jq -r '.valid')" >> $GITHUB_OUTPUT
          echo "score=$(cat validation.json | jq -r '.score')" >> $GITHUB_OUTPUT

      - name: Upload Validation Report
        uses: actions/upload-artifact@v4
        with:
          name: sdlc-validation-report
          path: validation.json
          retention-days: 30

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('validation.json', 'utf8'));

            const status = report.valid ? '✅ PASSED' : '❌ FAILED';
            const tier = report.tier.toUpperCase();
            const score = report.score;

            let body = `## SDLC 5.1.3 Structure Validation: ${status}\n\n`;
            body += `| Metric | Value |\n|--------|-------|\n`;
            body += `| Tier | ${tier} |\n`;
            body += `| Score | ${score}/100 |\n`;
            body += `| Stages | ${report.stages_found.length}/${report.stages_required} |\n`;
            body += `| P0 Artifacts | ${report.p0_status} |\n\n`;

            if (report.violations.length > 0) {
              body += `### Violations\n\n`;
              report.violations.forEach((v, i) => {
                body += `${i + 1}. **${v.type}**: ${v.message}\n`;
              });
            }

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });

      - name: Update Badge
        if: github.ref == 'refs/heads/main'
        run: |
          # Generate badge JSON for shields.io
          if [ "${{ steps.validate.outputs.result }}" == "true" ]; then
            echo '{"schemaVersion":1,"label":"SDLC 5.1.3","message":"PASSED","color":"green"}' > .github/badges/sdlc-status.json
          else
            echo '{"schemaVersion":1,"label":"SDLC 5.1.3","message":"FAILED","color":"red"}' > .github/badges/sdlc-status.json
          fi

      - name: Fail on Violations
        if: steps.validate.outputs.result != 'true'
        run: exit 1
```

---

### Day 2: CI/CD Integration (Jan 14, 2026)

**Owner**: DevOps Engineer + Backend Lead
**Story Points**: 8

#### Tasks

| Task | Description | Estimate | Priority |
|------|-------------|----------|----------|
| T2.1 | Configure branch protection rules | 2h | P0 |
| T2.2 | Test with multiple NQH repos | 3h | P0 |
| T2.3 | Create monorepo support | 2h | P1 |
| T2.4 | Add Slack/Teams notification | 1h | P2 |
| T2.5 | Documentation for CI/CD setup | 2h | P0 |

#### Acceptance Criteria

```yaml
AC-2.1: Branch protection requires SDLC validation pass
AC-2.2: Works on all 5 NQH portfolio repos
AC-2.3: Monorepo with multiple docs/ folders supported
AC-2.4: Setup documentation complete
```

#### Branch Protection Configuration

```yaml
# Branch protection rules for main branch
Branch Protection:
  Required status checks:
    - "SDLC Structure Validation"
  Require branches to be up to date: true

  # Additional recommendations
  Require conversation resolution: true
  Require linear history: false
  Include administrators: true
```

#### Multi-Repo Testing Matrix

| Repository | Tier | Expected Result |
|------------|------|-----------------|
| SDLC-Orchestrator | PROFESSIONAL | PASS (100%) |
| Bflow-Platform | PROFESSIONAL | PASS (100%) |
| NQH-Bot | STANDARD | PASS after fix |
| SOP-Generator | STANDARD | PASS after fix |
| AI-Platform | LITE | PASS after fix |

---

### Day 3: Web API Endpoint (Jan 15, 2026)

**Owner**: Backend Lead
**Story Points**: 8

#### Tasks

| Task | Description | Estimate | Priority |
|------|-------------|----------|----------|
| T3.1 | Create validation API endpoint | 3h | P0 |
| T3.2 | Add validation history storage | 2h | P0 |
| T3.3 | Implement async validation for large projects | 2h | P1 |
| T3.4 | Add rate limiting | 1h | P1 |
| T3.5 | API documentation (OpenAPI) | 1h | P0 |

#### Acceptance Criteria

```yaml
AC-3.1: POST /projects/{id}/validate-structure returns <1s
AC-3.2: Validation history stored (last 30 days)
AC-3.3: Large projects validated async with polling
AC-3.4: Rate limit: 10 validations/minute per project
```

#### API Specification

```yaml
# OpenAPI spec addition
paths:
  /projects/{project_id}/validate-structure:
    post:
      summary: Validate SDLC 5.1.3 structure
      tags:
        - Compliance
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                tier:
                  type: string
                  enum: [lite, standard, professional, enterprise]
                  description: Override auto-detected tier
                strict_mode:
                  type: boolean
                  default: true
                include_p0:
                  type: boolean
                  default: true
      responses:
        '200':
          description: Validation completed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ValidationResult'
        '202':
          description: Validation in progress (async)
          content:
            application/json:
              schema:
                type: object
                properties:
                  validation_id:
                    type: string
                    format: uuid
                  status:
                    type: string
                    enum: [pending, in_progress]
                  poll_url:
                    type: string

  /projects/{project_id}/validation-history:
    get:
      summary: Get validation history
      tags:
        - Compliance
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
            maximum: 100
      responses:
        '200':
          description: Validation history
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/ValidationResult'

components:
  schemas:
    ValidationResult:
      type: object
      properties:
        id:
          type: string
          format: uuid
        valid:
          type: boolean
        score:
          type: integer
          minimum: 0
          maximum: 100
        tier:
          type: string
          enum: [lite, standard, professional, enterprise]
        stages_found:
          type: array
          items:
            type: string
        stages_missing:
          type: array
          items:
            type: string
        p0_status:
          type: object
          properties:
            total:
              type: integer
            found:
              type: integer
            missing:
              type: array
              items:
                type: string
        violations:
          type: array
          items:
            type: object
            properties:
              type:
                type: string
              message:
                type: string
              severity:
                type: string
                enum: [error, warning, info]
              fix:
                type: string
        validated_at:
          type: string
          format: date-time
```

#### Backend Implementation

```python
# backend/app/api/routes/compliance.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.services.sdlc_validator import SDLCValidatorService
from app.schemas.compliance import (
    ValidationRequest,
    ValidationResult,
    ValidationHistoryResponse
)

router = APIRouter(prefix="/projects/{project_id}", tags=["Compliance"])

@router.post("/validate-structure", response_model=ValidationResult)
async def validate_structure(
    project_id: UUID,
    request: ValidationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate SDLC 5.1.3 structure for a project.

    For large projects (>1000 files), validation runs async
    and returns a 202 with poll URL.
    """
    validator = SDLCValidatorService(db)

    # Check project exists
    project = await validator.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check rate limit
    if await validator.is_rate_limited(project_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 10 validations/minute."
        )

    # Run validation
    result = await validator.validate(
        project_id=project_id,
        tier_override=request.tier,
        strict_mode=request.strict_mode,
        include_p0=request.include_p0
    )

    # Store result
    await validator.store_result(project_id, result)

    return result

@router.get("/validation-history", response_model=list[ValidationResult])
async def get_validation_history(
    project_id: UUID,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get validation history for a project (last 30 days)."""
    validator = SDLCValidatorService(db)
    return await validator.get_history(project_id, limit=limit)
```

---

### Day 4: Dashboard Component (Jan 16, 2026)

**Owner**: Frontend Engineer
**Story Points**: 8

#### Tasks

| Task | Description | Estimate | Priority |
|------|-------------|----------|----------|
| T4.1 | Create ComplianceDashboard component | 3h | P0 |
| T4.2 | Add tier visualization (badges, icons) | 2h | P0 |
| T4.3 | Create validation trigger button | 1h | P0 |
| T4.4 | Add validation history timeline | 2h | P1 |
| T4.5 | E2E tests for compliance dashboard | 2h | P0 |

#### Acceptance Criteria

```yaml
AC-4.1: Dashboard shows compliance status for all projects
AC-4.2: Tier badges display correctly (LITE/STANDARD/PROFESSIONAL/ENTERPRISE)
AC-4.3: "Run Validation" button triggers validation
AC-4.4: History shows last 10 validations with trend
```

#### Component Specification

```tsx
// frontend/web/src/components/compliance/ComplianceDashboard.tsx

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { CheckCircle, XCircle, AlertTriangle, RefreshCw } from 'lucide-react';

interface Project {
  id: string;
  name: string;
  tier: 'lite' | 'standard' | 'professional' | 'enterprise';
  lastValidation?: ValidationResult;
}

interface ValidationResult {
  valid: boolean;
  score: number;
  tier: string;
  stages_found: string[];
  stages_missing: string[];
  p0_status: { total: number; found: number };
  validated_at: string;
}

const TIER_COLORS = {
  lite: 'bg-gray-500',
  standard: 'bg-blue-500',
  professional: 'bg-purple-500',
  enterprise: 'bg-gold-500',
};

export function ComplianceDashboard() {
  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects-compliance'],
    queryFn: fetchProjectsCompliance,
  });

  const validateMutation = useMutation({
    mutationFn: (projectId: string) => validateProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries(['projects-compliance']);
    },
  });

  if (isLoading) return <ComplianceSkeleton />;

  const compliantCount = projects?.filter(p => p.lastValidation?.valid).length ?? 0;
  const totalCount = projects?.length ?? 0;
  const overallScore = Math.round(
    (projects?.reduce((acc, p) => acc + (p.lastValidation?.score ?? 0), 0) ?? 0) / totalCount
  );

  return (
    <div className="space-y-6">
      {/* Overview Card */}
      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">SDLC 5.1.3 Compliance</h2>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold">{overallScore}%</div>
              <div className="text-sm text-muted-foreground">Overall Score</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold">{compliantCount}/{totalCount}</div>
              <div className="text-sm text-muted-foreground">Projects Compliant</div>
            </div>
            <div className="text-center">
              <Progress value={overallScore} className="h-4" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Project List */}
      <div className="grid gap-4">
        {projects?.map((project) => (
          <ProjectComplianceCard
            key={project.id}
            project={project}
            onValidate={() => validateMutation.mutate(project.id)}
            isValidating={validateMutation.isLoading}
          />
        ))}
      </div>
    </div>
  );
}

function ProjectComplianceCard({
  project,
  onValidate,
  isValidating
}: {
  project: Project;
  onValidate: () => void;
  isValidating: boolean;
}) {
  const validation = project.lastValidation;
  const StatusIcon = validation?.valid ? CheckCircle : XCircle;
  const statusColor = validation?.valid ? 'text-green-500' : 'text-red-500';

  return (
    <Card>
      <CardContent className="flex items-center justify-between p-4">
        <div className="flex items-center gap-4">
          <StatusIcon className={`h-8 w-8 ${statusColor}`} />
          <div>
            <div className="font-semibold">{project.name}</div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Badge className={TIER_COLORS[project.tier]}>
                {project.tier.toUpperCase()}
              </Badge>
              <span>Score: {validation?.score ?? 'N/A'}%</span>
              <span>Stages: {validation?.stages_found.length ?? 0}/{validation?.stages_found.length + (validation?.stages_missing.length ?? 0)}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onValidate}
            disabled={isValidating}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isValidating ? 'animate-spin' : ''}`} />
            Validate
          </Button>
          <Button variant="ghost" size="sm">
            View Details
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
```

---

### Day 5: Rollout & Polish (Jan 17, 2026)

**Owner**: Full Team
**Story Points**: 6

#### Tasks

| Task | Description | Estimate | Priority |
|------|-------------|----------|----------|
| T5.1 | Roll out to all 5 NQH projects | 3h | P0 |
| T5.2 | Fix violations in non-compliant projects | 2h | P0 |
| T5.3 | Update documentation | 2h | P0 |
| T5.4 | CTO review and sign-off | 1h | P0 |
| T5.5 | Create rollout report | 1h | P1 |

#### Acceptance Criteria

```yaml
AC-5.1: All 5 NQH projects have GitHub Action configured
AC-5.2: All projects at 100% compliance score
AC-5.3: Documentation updated (README, setup guide)
AC-5.4: CTO approval received
```

#### Rollout Checklist

```yaml
# Per-Project Rollout Checklist

SDLC-Orchestrator:
  - [ ] Add .sdlc-config.json
  - [ ] Add .github/workflows/sdlc-validate.yml
  - [ ] Configure branch protection
  - [ ] Run initial validation
  - [ ] Fix any violations
  - [ ] Verify 100% score

Bflow-Platform:
  - [ ] Add .sdlc-config.json
  - [ ] Add .github/workflows/sdlc-validate.yml
  - [ ] Configure branch protection
  - [ ] Run initial validation
  - [ ] Fix any violations
  - [ ] Verify 100% score

NQH-Bot:
  - [ ] Add .sdlc-config.json (tier: standard)
  - [ ] Add .github/workflows/sdlc-validate.yml
  - [ ] Fix stage 06 naming (06-Maintenance-Support → 06-Operations-Maintenance)
  - [ ] Run validation
  - [ ] Verify 100% score

SOP-Generator:
  - [ ] Add .sdlc-config.json (tier: standard)
  - [ ] Add .github/workflows/sdlc-validate.yml
  - [ ] Fix stage 05 naming
  - [ ] Run validation
  - [ ] Verify 100% score

AI-Platform:
  - [ ] Add .sdlc-config.json (tier: lite)
  - [ ] Add .github/workflows/sdlc-validate.yml
  - [ ] Remove duplicate stage 05 folders
  - [ ] Run validation
  - [ ] Verify 100% score
```

---

## Definition of Done

### Sprint Level

- [ ] All tasks completed (T1.1 - T5.5)
- [ ] GitHub Action working on all 5 repos
- [ ] API endpoint <1s response time
- [ ] Dashboard component tested
- [ ] All 5 NQH projects at 100% compliance
- [ ] CTO sign-off received

### Feature Level

- [ ] GitHub Action triggers on docs/** changes
- [ ] PR comments show validation results
- [ ] Branch protection enforces validation
- [ ] API stores validation history
- [ ] Dashboard shows all projects
- [ ] Tier badges display correctly

---

## Technical Decisions

### TD-1: Database Schema Addition

```sql
-- Migration: add_sdlc_validation_history.sql

CREATE TABLE sdlc_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    valid BOOLEAN NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    tier VARCHAR(20) NOT NULL,
    stages_found JSONB NOT NULL DEFAULT '[]',
    stages_missing JSONB NOT NULL DEFAULT '[]',
    p0_status JSONB NOT NULL DEFAULT '{}',
    violations JSONB NOT NULL DEFAULT '[]',
    validated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_tier CHECK (tier IN ('lite', 'standard', 'professional', 'enterprise'))
);

-- Index for fast project lookup
CREATE INDEX idx_sdlc_validations_project_id ON sdlc_validations(project_id);

-- Index for history queries (most recent first)
CREATE INDEX idx_sdlc_validations_validated_at ON sdlc_validations(project_id, validated_at DESC);

-- Cleanup old validations (keep 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_validations()
RETURNS void AS $$
BEGIN
    DELETE FROM sdlc_validations
    WHERE validated_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;
```

### TD-2: API Rate Limiting

```python
# backend/app/core/rate_limit.py

from datetime import datetime, timedelta
from typing import Optional
import redis.asyncio as redis

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def is_rate_limited(
        self,
        key: str,
        max_requests: int = 10,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if rate limit exceeded.
        Uses sliding window algorithm.
        """
        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds)

        results = await pipe.execute()
        request_count = results[2]

        return request_count > max_requests
```

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| GitHub API rate limits | Medium | Low | Cache validation results, batch requests |
| Large repo validation timeout | High | Medium | Async validation with polling |
| Dashboard performance | Medium | Low | Pagination, lazy loading |
| Cross-repo coordination | Medium | Medium | Central config template, documentation |

---

## Dependencies

### Blocking Dependencies

- Sprint 29 Complete (CLI tool working)

### Non-blocking Dependencies

- GitHub Actions enabled on all repos
- Branch protection permissions

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| GitHub Action time | <30s | Action logs |
| API response time | <1s | APM metrics |
| Dashboard load time | <2s | Lighthouse |
| Portfolio compliance | 100% | Validation results |
| Zero false positives | 0 | User reports |

---

## Sprint Ceremonies

| Ceremony | Time | Participants |
|----------|------|--------------|
| Sprint Planning | Jan 13, 9:00 AM | Full team |
| Daily Standup | 9:30 AM daily | Full team |
| Sprint Review | Jan 17, 4:00 PM | Team + CTO + Stakeholders |
| Retrospective | Jan 17, 5:00 PM | Full team |

---

## References

- [PHASE-04: SDLC Structure Validator](../04-Phase-Plans/PHASE-04-SDLC-VALIDATOR.md)
- [Sprint 29: SDLC Validator CLI](./SPRINT-29-SDLC-VALIDATOR-CLI.md)
- [SDLC 5.1.3 Framework](../../../SDLC-Enterprise-Framework/)
- [ADR-014: SDLC Structure Validator](../../02-design/01-ADRs/ADR-014-SDLC-Validator.md)

---

**Document Status**: PLANNED
**Last Updated**: December 5, 2025
**Owner**: DevOps + Backend + Frontend
**Phase Complete**: PHASE-04 Complete after Sprint 30
