# Stage 04 (BUILD)
## Code Implementation - Production-Ready Development

**Version**: 2.0.0
**Date**: November 29, 2025
**Status**: ✅ WEEK 10 OF 13 - Gate G3 Target: Dec 13, 2025
**Authority**: CTO + Backend Lead + Tech Lead
**Foundation**: Stage 02 (Design & Architecture) - 24 documents ✅ COMPLETE
**Framework**: SDLC 5.1.3.1 Complete Lifecycle (10 Stages)
**Previous Stage**: Stage 02 (HOW - Design & Architecture) ✅ COMPLETE (Gate G2 PASSED)

---

## 🎯 Purpose

Stage 04 (BUILD) this with production quality?"**

This stage transforms architecture (Stage 02 - HOW) into working code with:
- **Development Standards** - Coding conventions, best practices, style guides
- **Code Review Process** - Peer review, automated checks, approval gates
- **Testing Strategy** - Unit tests (95%+), integration tests (90%+), E2E tests
- **Deployment Procedures** - CI/CD pipeline, rollback, monitoring
- **API Development** - FastAPI implementation, OpenAPI compliance

**Critical Success Factor**: We must write **ZERO MOCK code** and maintain **95%+ test coverage** from Day 1.

---

## Folder Structure (SDLC 5.1.3.1 Compliant)

```
03-Development-Implementation/
├── README.md (this file)
├── 01-Development-Standards/
│   ├── Zero-Mock-Policy.md ✅
│   ├── Python-Style-Guide.md ✅
│   ├── TypeScript-Style-Guide.md ✅
│   └── AI-Stage-Aware-Prompts.md ✅
├── 02-Sprint-Plans/
│   ├── WEEK-4-SPRINT-PLAN.md ✅
│   ├── WEEK-4-5-SUCCESS-CRITERIA.md ✅
│   ├── WEEK-06-DAY-01-INTEGRATION-TEST-SETUP.md ✅
│   ├── SPRINT-15-GITHUB-FOUNDATION.md ✅
│   ├── SPRINT-15-FINAL-SUMMARY.md ✅
│   ├── SPRINT-16-PROGRESS.md ✅
│   ├── SPRINT-16-COMPLETE.md ✅
│   ├── SPRINT-17-RECOMMENDATIONS.md ✅
│   ├── SPRINT-17-COMPLETE.md ✅
│   ├── SPRINT-18-EVIDENCE-INTEGRATION.md ✅
│   ├── SPRINT-18-19-20-SUMMARY.md ✅
│   ├── SPRINT-19-CRUD-OPERATIONS.md ✅
│   ├── SPRINT-20-ONBOARDING-COMPLETE.md ✅
│   ├── SPRINT-21-COMPLIANCE-SCANNER.md ✅ (Week 11)
│   └── SPRINT-22-HARDENING-PILOT.md ✅ (Week 12)
└── 03-Setup-Guides/
    ├── DEV-ENVIRONMENT-SETUP.md ✅
    ├── DAY-5-MORNING-RUNBOOK.md ✅
    ├── DAY-5-QUICK-REFERENCE.md ✅
    └── MINIO-TROUBLESHOOTING-GUIDE.md ✅
```

---

## ⏱️ Timeline (Week 1-13)

| Weeks | Phase | Focus | Deliverables |
|-------|-------|-------|--------------|
| 1-2 | **Foundation** | Setup + Auth | Docker Compose, JWT, OAuth, Database |
| 3-5 | **Core Features** | Gate Engine + Evidence | OPA, MinIO, Policy Packs |
| 6-8 | **Integration** | GitHub + AI + Reports | Bridge, AI Context, Dashboards |
| 9-10 | **Extensions** | Operate + VS Code | Grafana, Extension |
| 11-12 | **Hardening** | Pilot + Bug Fixes | Bflow Pilot, Performance |
| 13 | **Launch** | Production Deploy | Go-Live, Support |

---

## 🚫 Zero Mock Policy (MANDATORY)

### Prohibited Patterns

```python
# ❌ BANNED - Will be rejected in code review
def authenticate_user(username, password):
    # TODO: Implement authentication
    return {"user": "mock"}

# ❌ BANNED - Placeholder implementation
def get_projects():
    pass  # Implement later

# ❌ BANNED - Fake data
def list_gates():
    return {"gates": [{"id": "mock", "status": "PASS"}]}
```

### Required Patterns

```python
# ✅ REQUIRED - Production-ready implementation
def authenticate_user(username: str, password: str, db: Session) -> User | None:
    """
    Authenticate user with username and password.

    Args:
        username: User's username or email
        password: Plain text password (will be hashed for comparison)
        db: Database session for user lookup

    Returns:
        User object if authentication successful, None otherwise

    Raises:
        AuthenticationError: If authentication fails due to system error

    Example:
        >>> user = authenticate_user("john@example.com", "password123", db)
        >>> user.email
        'john@example.com'
    """
    try:
        if not username or not password:
            return None

        user = db.query(User).filter(
            User.username == username.lower().strip()
        ).first()

        if not user or not user.is_active:
            return None

        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash):
            return None

        user.last_login = datetime.utcnow()
        db.commit()

        return user

    except Exception as e:
        logger.error(f"Authentication error for user {username}: {str(e)}")
        raise AuthenticationError("Authentication system error")
```

**Enforcement**:
- Pre-commit hook blocks keywords: `TODO`, `FIXME`, `mock`, `placeholder`
- CI/CD fails if banned patterns detected
- Code review requires 2+ approvers

---

## 🏗️ Development Standards

### Python (Backend)

**Framework**: FastAPI 0.104+
**Style**: PEP 8 (enforced by black + ruff)
**Type Hints**: 100% coverage (mypy strict mode)
**Testing**: pytest + pytest-asyncio (95%+ coverage)

```python
# Example: Type hints + docstrings
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ProjectResponse:
    """
    Create new project.

    Args:
        project: Project data from request body
        current_user: Authenticated user (from JWT token)
        db: Database session (from dependency injection)

    Returns:
        ProjectResponse with created project details

    Raises:
        HTTPException 409: If project name already exists
        HTTPException 403: If user lacks permission

    Example:
        POST /api/v1/projects
        {
            "name": "SDLC Orchestrator",
            "description": "First governance platform on SDLC 5.1.3"
        }
    """
    # Validate project name uniqueness
    existing = db.query(Project).filter(
        Project.name == project.name,
        Project.organization_id == current_user.organization_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Project '{project.name}' already exists"
        )

    # Create project
    db_project = Project(
        name=project.name,
        description=project.description,
        owner_id=current_user.id,
        organization_id=current_user.organization_id,
        created_at=datetime.utcnow()
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return ProjectResponse.from_orm(db_project)
```

---

### TypeScript (Frontend)

**Framework**: React 18 + TypeScript 5.0
**Style**: ESLint + Prettier
**State**: Zustand (lightweight)
**Testing**: Vitest + React Testing Library (90%+ coverage)

```typescript
// Example: Type-safe React component
interface ProjectListProps {
  organizationId: string;
  onProjectClick: (projectId: string) => void;
}

export const ProjectList: React.FC<ProjectListProps> = ({
  organizationId,
  onProjectClick
}) => {
  // TanStack Query for data fetching + caching
  const { data: projects, isLoading, error } = useQuery({
    queryKey: ['projects', organizationId],
    queryFn: () => api.projects.list(organizationId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorAlert error={error} />;
  if (!projects || projects.length === 0) {
    return <EmptyState message="No projects yet" />;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {projects.map((project) => (
        <ProjectCard
          key={project.id}
          project={project}
          onClick={() => onProjectClick(project.id)}
        />
      ))}
    </div>
  );
};
```

---

## 🔍 Code Review Process

### Pull Request Requirements

```yaml
Required Checks (All must PASS):
  ✅ Linting: black, ruff (Python), eslint (TypeScript)
  ✅ Type checking: mypy (Python), tsc (TypeScript)
  ✅ Tests: pytest (95%+), vitest (90%+)
  ✅ Security: Semgrep (OWASP rules)
  ✅ Dependencies: Grype (no critical CVEs)
  ✅ SBOM: Syft (generated)
  ✅ Zero Mock: No banned keywords

Required Approvals:
  ✅ 2+ reviewers (Tech Lead + Backend/Frontend Lead)
  ✅ CTO approval (for architecture changes)
```

### Review Checklist

- [ ] Code follows style guide (PEP 8, ESLint)
- [ ] Type hints 100% (Python), types 100% (TypeScript)
- [ ] Docstrings for all functions (Google style)
- [ ] Unit tests written (95%+ coverage)
- [ ] Integration tests (if API changes)
- [ ] No banned patterns (TODO, mock, placeholder)
- [ ] Error handling comprehensive
- [ ] Logging structured (JSON format)
- [ ] Security validated (no SQL injection, XSS, etc)
- [ ] Performance validated (<100ms p95)

---

## 🧪 Testing Strategy

### Test Coverage Targets

```yaml
Backend (Python):
  Unit Tests: 95%+ coverage (pytest)
  Integration Tests: 90%+ coverage (API contracts)
  E2E Tests: Critical user journeys (Playwright)
  Performance Tests: <100ms p95 (Locust)

Frontend (TypeScript):
  Unit Tests: 90%+ coverage (Vitest)
  Component Tests: 85%+ (React Testing Library)
  E2E Tests: User flows (Playwright)
  Visual Tests: Storybook snapshots
```

### Testing Pyramid

```
       /\
      /E2E\      10% - User journeys (Playwright)
     /------\
    /  INT  \    30% - API contracts, Database
   /----------\
  /   UNIT    \  60% - Functions, Components
 /--------------\
```

### Example: Unit Test (Backend)

```python
# tests/test_auth.py
import pytest
from app.core.security import verify_password, get_password_hash

def test_password_hashing():
    """Test password hashing and verification."""
    password = "supersecret123"
    hashed = get_password_hash(password)

    # Verify correct password
    assert verify_password(password, hashed) is True

    # Verify incorrect password
    assert verify_password("wrongpassword", hashed) is False

def test_password_hash_uniqueness():
    """Test that same password generates different hashes."""
    password = "supersecret123"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    # Hashes should be different (bcrypt uses random salt)
    assert hash1 != hash2

    # But both should verify
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True
```

---

## 🚀 Deployment Procedures

### CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/backend-ci.yml
name: Backend CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint (black, ruff)
        run: |
          black --check .
          ruff check .

      - name: Type check (mypy)
        run: mypy app/

      - name: Security scan (Semgrep)
        run: semgrep --config=auto .

      - name: Run tests (pytest)
        run: pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: echo "Deploy to staging"
```

---

## Progress Tracker

### 01-Development-Standards (100% complete)
- ✅ Zero-Mock-Policy.md (5,500+ lines)
- ✅ Python-Style-Guide.md (6,500+ lines)
- ✅ TypeScript-Style-Guide.md (5,600+ lines)
- ✅ AI-Stage-Aware-Prompts.md

### 02-Sprint-Plans (100% complete - Week 10)
- ✅ WEEK-4-SPRINT-PLAN.md
- ✅ WEEK-4-5-SUCCESS-CRITERIA.md
- ✅ WEEK-06-DAY-01-INTEGRATION-TEST-SETUP.md
- ✅ SPRINT-15 through SPRINT-20 (8 documents)
- ✅ SPRINT-21-COMPLIANCE-SCANNER.md (Week 11 - Dec 2-6)
- ✅ SPRINT-22-HARDENING-PILOT.md (Week 12 - Dec 9-13)

### 03-Setup-Guides (100% complete)
- ✅ DEV-ENVIRONMENT-SETUP.md
- ✅ DAY-5-MORNING-RUNBOOK.md
- ✅ DAY-5-QUICK-REFERENCE.md
- ✅ MINIO-TROUBLESHOOTING-GUIDE.md

### Implementation Status (Week 10 of 13)

| Component | Status | Completion |
|-----------|--------|------------|
| **Backend API** | ✅ | 30+ endpoints, FastAPI |
| **Database** | ✅ | 24 tables, Alembic migrations |
| **Frontend** | ✅ | React + shadcn/ui + TanStack Query |
| **Authentication** | ✅ | JWT + OAuth (GitHub) |
| **Gate Engine** | ✅ | OPA integration |
| **Evidence Vault** | ✅ | MinIO S3 integration |
| **GitHub Bridge** | ✅ | Read-only sync |
| **Compliance Scanner** | ⏳ | Sprint 21 (Dec 2-6) |
| **AI Integration** | ⏳ | Sprint 21 (Ollama) |
| **Pilot Launch** | ⏳ | Sprint 22 (Dec 9-13) |

**Overall Progress**: ✅ 75% (Week 10 of 13)

---

## ✅ Exit Criteria (Must Complete Before Stage 04)

### Code Completion
- [ ] All planned features implemented (Gate Engine, Evidence Vault, GitHub Bridge)
- [ ] Zero Mock Policy enforced (0 placeholders, 0 TODOs)
- [ ] Test coverage: Backend 95%+, Frontend 90%+
- [ ] Security scan: 0 critical CVEs (Semgrep, Grype)
- [ ] Performance validated: <100ms p95 (Locust load tests)

### Code Quality
- [ ] All PRs reviewed (2+ approvers)
- [ ] CTO approval for architecture changes
- [ ] Linting passes (black, ruff, eslint)
- [ ] Type checking passes (mypy, tsc)
- [ ] Documentation complete (API docs, README, ADRs)

### Deployment Readiness
- [ ] CI/CD pipeline automated (GitHub Actions)
- [ ] Docker Compose working locally
- [ ] Staging environment deployed
- [ ] Rollback procedures tested (<5min)
- [ ] Monitoring instrumented (Prometheus, Grafana)

**Stage 03 Status**: ✅ IN PROGRESS - Week 10 of 13 (Gate G3 Target: Dec 13, 2025)

---

## Sprint Roadmap (Weeks 11-13)

### Week 11: Sprint 21 - Compliance Scanner & AI (Dec 2-6, 2025)
```yaml
Focus: Automated SDLC compliance enforcement + Ollama AI

Deliverables:
  - ComplianceScanner service (detect violations automatically)
  - 15+ SDLC 5.1.3.1 policy rules (Rego)
  - Scheduled daily scans
  - Ollama AI integration (recommendations)
  - Compliance Dashboard UI
  - Email notifications for violations

Why This Sprint Matters:
  "SDLC Framework có compliance script scanner thủ công,
   nhưng AI Codex làm sai chuẩn sẽ không được phát hiện kịp thời.
   Platform cần scan tự động để enforce - không chỉ suggest."
```

### Week 12: Sprint 22 - Hardening & Pilot (Dec 9-13, 2025)
```yaml
Focus: Performance + Security + Internal Pilot + Gate G3

Deliverables:
  - Performance optimization (<100ms p95)
  - Security hardening (OWASP ASVS L2)
  - 5 internal teams onboarded (BFlow, NQH-Bot, SDLC-O, Framework, MTEP)
  - Bug fixes from pilot feedback
  - Gate G3 evidence package
  - CTO + CPO + CEO sign-off

Gate G3 Exit Criteria:
  - Zero P0/P1 bugs
  - <100ms p95 API latency
  - 99.9%+ uptime (pilot)
  - All approvals obtained
```

### Week 13: Launch (Dec 16-20, 2025)
```yaml
Focus: Production deployment + Support

Activities:
  - Day 1: Final deployment
  - Day 2: Internal announcement
  - Day 3-4: Monitor & support
  - Day 5: Retrospective + MVP celebration

Success Criteria:
  - Production live ✓
  - Zero incidents ✓
  - MVP 90-day goal achieved ✓
```

---

## Success Metrics

### Velocity Tracking
```yaml
Sprint 1-2 (Foundation):
  Target Velocity: 75-80 points/sprint
  Test Coverage: 95%+ backend, 90%+ frontend
  CI/CD Pipeline: <5min

Sprint 3-5 (Core Features):
  Target Velocity: 80-90 points/sprint
  Feature Completion: Gate Engine + Evidence Vault
  Performance: <100ms p95

Sprint 6-10 (Integration):
  Target Velocity: 90-100 points/sprint
  Integration Tests: 90%+ coverage
  E2E Tests: Critical user journeys

Sprint 11-13 (Launch):
  Target Velocity: 60-70 points/sprint
  Bug Fixing: P0/P1 resolved
  Production Ready: 100%
```

### Quality Gates (Per Sprint)
```yaml
Code Quality:
  ✅ Linting: 0 errors (black, ruff, eslint)
  ✅ Type checking: 0 errors (mypy, tsc)
  ✅ Test coverage: 95%+ (backend), 90%+ (frontend)
  ✅ Security scan: 0 critical CVEs

Performance:
  ✅ API latency: <100ms p95
  ✅ Dashboard load: <1s p95
  ✅ CI/CD execution: <5min

Documentation:
  ✅ API docs: OpenAPI spec up-to-date
  ✅ Code docs: Docstrings 100%
  ✅ ADRs: Architecture decisions documented
```

---

## 🔗 References

### Internal References
- [Stage 02: Design & Architecture](../02-Design-Architecture/README.md) - Architecture foundation
- [ADR-002: Authentication Model](../02-Design-Architecture/02-System-Architecture/Architecture-Decisions/ADR-002-Authentication-Model.md) - Auth design
- [openapi.yml](../02-Design-Architecture/04-API-Specifications/openapi.yml) - API contract
- [Sprint Execution Plan](../08-Team-Management/04-Sprint-Management/Sprint-Execution-Plan.md) - 13-week plan

### External References
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [OWASP ASVS Level 2](https://owasp.org/www-project-application-security-verification-standard/)
- [SDLC 5.1.3 Framework](/Users/dttai/Documents/Python/01.NQH/Bflow-Platform/Sub-Repo/SDLC-Enterprise-Framework)

---

**Last Updated**: November 29, 2025
**Owner**: CTO + Backend Lead + Tech Lead
**Status**: ✅ IN PROGRESS - Week 10 of 13 (75% complete)
**Next Gate**: G3 (Ship Ready) - Target: Dec 13, 2025

---

## Document Summary

**Total Documents**: 22 documents (across 3 folders)
**Sprint Plans**: 15 documents (Week 4 → Sprint 22)
**Total Lines**: 25,000+ lines
**Quality Gates**: Weekly sprint reviews + CTO architecture reviews
**Current Sprint**: Sprint 20 (Nov 29, 2025)
**Next Milestone**: Sprint 21 - Compliance Scanner (Dec 2, 2025)

---

## Key Insight: Iterative Workflow Enforcement

> "Việc thiết kế, code, test không phải là tuyến tính mà vòng lặp đi lặp lại.
> Khi có thay đổi thiết kế thì phải refactor hoặc code mới.
> Khi bổ sung code khác với thiết kế thì phải quay lại cập nhật thiết kế."

### Sprint 21 sẽ implement:

```yaml
Documentation Drift Detection:
  1. Scan code changes → Compare with /docs
  2. Detect when code differs from design docs
  3. Create "Documentation Update Required" gate blocker
  4. AI suggest what docs need updating

Enforcement Rules:
  - PR cannot merge if docs are outdated
  - Weekly doc sync reminders
  - Stage gates require doc consistency check

Example Violations:
  ❌ "API endpoint /gates has 5 new fields not in openapi.yml"
  ❌ "Database has 4 new tables not in Data-Model-ERD.md"
  ❌ "Auth flow changed but Security-Baseline.md not updated"
```

### Platform vs Manual Approach

| Aspect | Manual (Current) | Platform (Sprint 21+) |
|--------|-----------------|----------------------|
| Doc update reminder | No one reminds | Automated blocker |
| Design-code sync | Trust-based | System-enforced |
| Outdated docs | Discovered late | Detected on commit |
| AI Codex changes | Often missed | All changes tracked |
| Gate blocking | Manual check | Auto-block if drift |
