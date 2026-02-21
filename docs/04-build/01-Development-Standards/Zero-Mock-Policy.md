# Zero Mock Policy - Production-Ready Code from Day 1

**Version**: 1.0.0
**Date**: November 13, 2025
**Status**: ACTIVE - MANDATORY ENFORCEMENT
**Authority**: CTO + Backend Lead + Tech Lead
**Foundation**: NQH-Bot Crisis (679 mocks → 78% failure), Stage 02 Architecture
**Framework**: SDLC 6.1.0

---

## 🎯 Purpose

The Zero Mock Policy is a **MANDATORY** development standard that prohibits all forms of placeholder code, mock implementations, and TODO markers in production code. This policy ensures that every line of code committed to the repository is production-ready, fully tested, and maintainable.

**Critical Success Factor**: We learned from the NQH-Bot crisis where 679 mock implementations led to 78% project failure. We will NOT repeat this mistake.

---

## 📜 Policy Statement

**All code committed to the SDLC Orchestrator repository MUST be production-ready.**

This means:
- ✅ **NO** TODO comments or FIXME markers
- ✅ **NO** placeholder implementations
- ✅ **NO** mock data or fake responses
- ✅ **NO** commented-out code with "implement later" notes
- ✅ **NO** empty function bodies with pass statements
- ✅ **NO** hardcoded test values in production code

**Violation = Automatic PR rejection + Code review failure**

---

## 🚫 Prohibited Patterns (BANNED)

### 1. TODO/FIXME Comments

```python
# ❌ BANNED - Will be rejected in code review
def authenticate_user(username, password):
    # TODO: Implement authentication
    return {"user": "mock"}

# ❌ BANNED - FIXME markers
def get_projects():
    # FIXME: Add database query
    pass

# ❌ BANNED - Placeholder comments
def validate_gate_policy():
    # Implement later when OPA is ready
    return True
```

**Why banned**: TODO comments indicate incomplete work. If the function isn't ready, don't commit it.

**Alternative**: Complete the implementation before committing, OR break down the work into smaller, completable tasks.

---

### 2. Mock/Fake Data Returns

```python
# ❌ BANNED - Mock user data
def get_current_user(token: str):
    return {
        "id": "mock-user-123",
        "email": "mock@example.com",
        "role": "admin"
    }

# ❌ BANNED - Fake database response
def list_gates():
    return {
        "gates": [
            {"id": "mock-gate-1", "status": "PASS"},
            {"id": "mock-gate-2", "status": "FAIL"}
        ]
    }

# ❌ BANNED - Hardcoded test data
def get_evidence(evidence_id: str):
    if evidence_id == "test-123":
        return {"file": "mock-evidence.pdf"}
    return None
```

**Why banned**: Mock data masks real integration issues and leads to false confidence in testing.

**Alternative**: Implement real database queries, API calls, or file operations. Use test fixtures in test files only.

---

### 3. Empty/Pass Implementations

```python
# ❌ BANNED - Empty function
def create_project(project_data):
    pass

# ❌ BANNED - Not implemented
def delete_evidence(evidence_id: str):
    raise NotImplementedError("Will implement in Sprint 3")

# ❌ BANNED - Placeholder class
class PolicyEngine:
    def __init__(self):
        pass  # Setup later

    def evaluate(self, policy: str):
        pass  # Implement OPA integration
```

**Why banned**: Empty implementations provide no value and create confusion about what's actually working.

**Alternative**: Don't create the function/class until you're ready to implement it fully.

---

### 4. Commented-Out Future Code

```python
# ❌ BANNED - Commented future implementation
def authenticate_user(username: str, password: str):
    # For now, just return success
    return True

    # TODO: Uncomment when database is ready
    # user = db.query(User).filter(User.username == username).first()
    # if not user:
    #     return False
    # return verify_password(password, user.password_hash)

# ❌ BANNED - Disabled features
def create_gate(gate_data):
    # Basic implementation
    return {"id": "gate-123"}

    # # Later: Add policy validation
    # policy_result = opa.evaluate(gate_data.policy)
    # if not policy_result.passed:
    #     raise PolicyViolationError()
```

**Why banned**: Commented code creates confusion and violates the "one source of truth" principle.

**Alternative**: Commit only working code. Future enhancements should be tracked in Jira/GitHub Issues, not in code comments.

---

### 5. Conditional Mock Behavior

```python
# ❌ BANNED - Development mode bypass
def verify_jwt_token(token: str):
    if os.getenv("ENV") == "development":
        return {"user_id": "dev-user"}  # Skip validation in dev

    # Real implementation
    return jwt.decode(token, SECRET_KEY)

# ❌ BANNED - Feature flag mocks
def upload_to_minio(file_data):
    if not MINIO_ENABLED:
        return {"url": "mock://file.pdf"}  # Mock when MinIO disabled

    return minio_client.upload(file_data)
```

**Why banned**: Conditional mocks create environment-specific bugs and inconsistent behavior.

**Alternative**: Use real services in all environments (use Docker Compose for local dev with real MinIO/PostgreSQL).

---

## ✅ Required Patterns (PRODUCTION-READY)

### 1. Complete Implementation with Error Handling

```python
# ✅ REQUIRED - Production-ready authentication
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
            logger.warning("Authentication attempt with empty credentials")
            return None

        user = db.query(User).filter(
            User.username == username.lower().strip()
        ).first()

        if not user or not user.is_active:
            logger.warning(f"Authentication failed for user: {username}")
            return None

        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash):
            logger.warning(f"Invalid password for user: {username}")
            return None

        user.last_login = datetime.utcnow()
        db.commit()

        logger.info(f"User authenticated successfully: {username}")
        return user

    except Exception as e:
        logger.error(f"Authentication error for user {username}: {str(e)}")
        raise AuthenticationError("Authentication system error")
```

**Why good**: Complete implementation with validation, error handling, logging, and type hints.

---

### 2. Real Database Integration

```python
# ✅ REQUIRED - Real database query
async def get_projects(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> list[ProjectResponse]:
    """
    List all projects for organization.

    Args:
        organization_id: Organization UUID
        current_user: Authenticated user (from JWT)
        db: Database session (async)
        skip: Pagination offset (default: 0)
        limit: Max results (default: 100, max: 1000)

    Returns:
        List of ProjectResponse objects

    Raises:
        HTTPException 403: If user lacks permission
        HTTPException 404: If organization not found

    Example:
        GET /api/v1/projects?organization_id=123&skip=0&limit=50
    """
    # Verify user has access to organization
    if current_user.organization_id != organization_id:
        if not current_user.is_c_suite:
            raise HTTPException(
                status_code=403,
                detail="Access denied to organization projects"
            )

    # Query projects with pagination
    result = await db.execute(
        select(Project)
        .where(Project.organization_id == organization_id)
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(min(limit, 1000))
    )
    projects = result.scalars().all()

    # Log query for audit
    logger.info(
        f"User {current_user.id} queried {len(projects)} projects "
        f"for organization {organization_id}"
    )

    return [ProjectResponse.from_orm(p) for p in projects]
```

**Why good**: Real async database query, pagination, permission checks, audit logging.

---

### 3. External API Integration

```python
# ✅ REQUIRED - Real GitHub API integration
async def fetch_github_repos(
    access_token: str,
    org_name: str
) -> list[GitHubRepo]:
    """
    Fetch all repositories for GitHub organization.

    Args:
        access_token: GitHub OAuth token (requires repo scope)
        org_name: GitHub organization name

    Returns:
        List of GitHubRepo objects

    Raises:
        GitHubAPIError: If API call fails (rate limit, auth error, etc)
        HTTPException 404: If organization not found

    Example:
        >>> repos = await fetch_github_repos("ghp_abc123", "anthropics")
        >>> len(repos)
        42
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.github.com/orgs/{org_name}/repos",
                headers=headers,
                params={"per_page": 100, "sort": "updated"},
                timeout=30.0
            )

            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"GitHub organization '{org_name}' not found"
                )

            if response.status_code == 403:
                # Rate limit exceeded
                raise GitHubAPIError(
                    "GitHub API rate limit exceeded. Try again later.",
                    retry_after=response.headers.get("X-RateLimit-Reset")
                )

            response.raise_for_status()

            repos_data = response.json()
            repos = [GitHubRepo.parse_obj(r) for r in repos_data]

            logger.info(
                f"Fetched {len(repos)} repositories for organization {org_name}"
            )

            return repos

        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error: {e.response.status_code}")
            raise GitHubAPIError(f"GitHub API error: {str(e)}")

        except httpx.TimeoutException:
            logger.error(f"GitHub API timeout for organization {org_name}")
            raise GitHubAPIError("GitHub API request timeout")
```

**Why good**: Real HTTP client, error handling, rate limiting, logging, retries.

---

### 4. File Storage with MinIO

```python
# ✅ REQUIRED - Real MinIO integration
async def upload_evidence(
    file: UploadFile,
    gate_id: str,
    current_user: User = Depends(get_current_user),
    minio_client: Minio = Depends(get_minio_client)
) -> EvidenceResponse:
    """
    Upload evidence file to MinIO object storage.

    Args:
        file: Uploaded file from FastAPI (max 100MB)
        gate_id: Gate UUID this evidence belongs to
        current_user: Authenticated user
        minio_client: MinIO client (from dependency injection)

    Returns:
        EvidenceResponse with file URL and metadata

    Raises:
        HTTPException 413: If file exceeds 100MB
        HTTPException 415: If file type not allowed
        MinIOError: If upload fails

    Example:
        POST /api/v1/gates/{gate_id}/evidence
        Content-Type: multipart/form-data
        file: test-report.pdf
    """
    # Validate file size (100MB max)
    MAX_SIZE = 100 * 1024 * 1024
    file_size = 0
    file_content = bytearray()

    async for chunk in file.stream():
        file_size += len(chunk)
        if file_size > MAX_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File exceeds 100MB limit"
            )
        file_content.extend(chunk)

    # Validate file type (PDF, PNG, JPG, TXT, MD)
    ALLOWED_TYPES = {
        "application/pdf", "image/png", "image/jpeg",
        "text/plain", "text/markdown"
    }
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"File type '{file.content_type}' not allowed"
        )

    # Generate unique object name
    object_name = f"{gate_id}/{uuid4()}-{file.filename}"
    bucket_name = "evidence-vault"

    try:
        # Upload to MinIO
        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=io.BytesIO(file_content),
            length=file_size,
            content_type=file.content_type,
            metadata={
                "uploaded_by": str(current_user.id),
                "gate_id": gate_id,
                "original_filename": file.filename
            }
        )

        # Generate presigned URL (expires in 7 days)
        file_url = minio_client.presigned_get_object(
            bucket_name=bucket_name,
            object_name=object_name,
            expires=timedelta(days=7)
        )

        logger.info(
            f"Evidence uploaded: {object_name} ({file_size} bytes) "
            f"by user {current_user.id}"
        )

        return EvidenceResponse(
            id=str(uuid4()),
            gate_id=gate_id,
            filename=file.filename,
            file_url=file_url,
            file_size=file_size,
            content_type=file.content_type,
            uploaded_by=current_user.id,
            uploaded_at=datetime.utcnow()
        )

    except S3Error as e:
        logger.error(f"MinIO upload error: {str(e)}")
        raise MinIOError(f"File upload failed: {str(e)}")
```

**Why good**: Real file upload, size validation, type checking, MinIO integration, presigned URLs.

---

## 🔍 Detection & Enforcement

### 1. Pre-Commit Hook (Git)

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Detect banned keywords in staged files
BANNED_KEYWORDS=("TODO" "FIXME" "mock" "placeholder" "implement later" "HACK")

for keyword in "${BANNED_KEYWORDS[@]}"; do
    if git diff --cached --name-only | xargs grep -l "$keyword" 2>/dev/null; then
        echo "❌ ERROR: Banned keyword '$keyword' found in staged files"
        echo "Zero Mock Policy violation - remove before committing"
        exit 1
    fi
done

echo "✅ Zero Mock Policy check passed"
exit 0
```

**Installation**:
```bash
cp .githooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

### 2. CI/CD Pipeline Check (GitHub Actions)

```yaml
# .github/workflows/zero-mock-check.yml
name: Zero Mock Policy

on:
  pull_request:
    branches: [main, develop]

jobs:
  check-mock-code:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Scan for banned keywords
        run: |
          BANNED="TODO|FIXME|mock|placeholder|implement later|HACK|NotImplementedError"

          # Scan Python files (exclude tests)
          if grep -rn -E "$BANNED" backend/app/ --include="*.py" --exclude-dir=tests; then
            echo "❌ Zero Mock Policy violation detected"
            exit 1
          fi

          # Scan TypeScript files (exclude tests)
          if grep -rn -E "$BANNED" frontend/src/ --include="*.ts" --include="*.tsx" --exclude-dir=__tests__; then
            echo "❌ Zero Mock Policy violation detected"
            exit 1
          fi

          echo "✅ Zero Mock Policy check passed"

      - name: Verify no commented code blocks
        run: |
          # Detect large commented code blocks (3+ consecutive lines)
          if python scripts/detect_commented_code.py; then
            echo "❌ Large commented code blocks detected"
            exit 1
          fi

          echo "✅ No commented code blocks"
```

---

### 3. Code Review Checklist

Every PR must pass this checklist:

- [ ] **No TODO/FIXME comments** in production code
- [ ] **No mock/fake data** returned from functions
- [ ] **No empty implementations** (pass, NotImplementedError)
- [ ] **No commented-out code** blocks
- [ ] **No conditional mock behavior** (env-based bypasses)
- [ ] **All functions fully implemented** with error handling
- [ ] **All external integrations real** (database, APIs, file storage)
- [ ] **All hardcoded values** moved to config/environment variables
- [ ] **All edge cases handled** (null checks, validation, errors)
- [ ] **All code documented** with docstrings (Google style)

**Approval Requirements**: 2+ reviewers (Tech Lead + Backend/Frontend Lead)

---

## 📊 Metrics & Monitoring

### Sprint Velocity Tracking

```yaml
Sprint 1 (Week 1):
  Planned Stories: 6 stories (80 hours backend)
  Zero Mock Violations: 0 (target)
  PR Rejections: 0 (target)

Sprint 2 (Week 2):
  Planned Stories: 6 stories (80 hours backend)
  Zero Mock Violations: 0 (target)
  PR Rejections: 0 (target)
```

**Consequences of Violations**:
- 1st violation: Warning + immediate fix required
- 2nd violation: Sprint velocity penalty (-10 points)
- 3rd violation: Developer coaching session + CTO review

---

## 🎓 Training & Onboarding

### New Developer Checklist

Before committing first code, all developers must:

1. **Read this document** (Zero-Mock-Policy.md)
2. **Read NQH-Bot Crisis Report** (679 mocks → 78% failure)
3. **Complete Zero Mock training** (1-hour workshop with Tech Lead)
4. **Setup pre-commit hooks** (.githooks/pre-commit)
5. **Review example code** (backend/app/models/user.py, backend/app/core/security.py)
6. **Pass Zero Mock quiz** (10 questions, 90%+ required)

### Training Resources

- **Workshop Slides**: docs/08-Team-Management/05-Training/Zero-Mock-Workshop.pdf
- **NQH-Bot Crisis Report**: docs/00-Project-Foundation/05-Lessons-Learned/NQH-Bot-Crisis.md
- **Example Code**: backend/app/ (all production code follows Zero Mock Policy)
- **Video Tutorial**: Loom recording by CTO (30 minutes)

---

## 🔗 References

### Internal References

- [Stage 03: Development Implementation](../README.md) - Development standards overview
- [ADR-002: Authentication Model](../../02-Design-Architecture/02-System-Architecture/Architecture-Decisions/ADR-002-Authentication-Model.md) - Example of complete design
- [Sprint Execution Plan](../../08-Team-Management/04-Sprint-Management/Sprint-Execution-Plan.md) - Sprint planning
- [NQH-Bot Crisis Report](../../00-Project-Foundation/05-Lessons-Learned/NQH-Bot-Crisis.md) - Lessons learned

### External References

- [OWASP Code Review Guide](https://owasp.org/www-project-code-review-guide/)
- [Google Engineering Practices](https://google.github.io/eng-practices/)
- [Clean Code by Robert C. Martin](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)

---

## 📝 Document Summary

**Purpose**: Enforce production-ready code from Day 1 (no TODOs, mocks, placeholders)
**Authority**: CTO + Backend Lead + Tech Lead
**Enforcement**: Pre-commit hooks + CI/CD checks + Code review checklist
**Violation Consequences**: PR rejection → Warning → Velocity penalty → CTO review
**Training Required**: All developers before first commit

---

**Last Updated**: November 13, 2025
**Owner**: CTO + Tech Lead
**Status**: ✅ ACTIVE - MANDATORY ENFORCEMENT
**Next Review**: Weekly sprint retrospectives
