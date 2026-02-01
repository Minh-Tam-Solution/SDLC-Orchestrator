# ADR-044: GitHub Integration Strategy

**Status**: ✅ APPROVED (CTO Sign-off: Jan 30, 2026)
**Date**: January 30, 2026
**Decision Maker**: CTO + Backend Lead
**Context**: Sprint 129 preparation (Feb 17-28, 2026)
**Related ADRs**: ADR-008 (Authentication), ADR-043 (Team Invitations)
**Sprint**: Sprint 129 (GitHub Project Onboarding)

---

## Context and Problem Statement

Users need to connect GitHub repositories to SDLC Orchestrator for:
1. **Project initialization** (clone existing repo structure)
2. **Gap analysis** (scan repo against SDLC Framework requirements)
3. **Evidence collection** (link PRs, commits to Evidence Vault)
4. **Gate evaluation** (block/pass based on GitHub state)

**Two integration approaches exist**:
- **GitHub App** (app-level authentication, webhook support)
- **OAuth User Token** (user-level authentication, simpler setup)

**Business Impact**:
- **Blocks March 1 launch** if not completed
- **Core value proposition** (evidence-based development requires GitHub integration)
- **Multi-tenant requirement** (100+ teams need isolated GitHub access)

**Requirements**:
- Multi-tenant isolation (team A cannot access team B's repos)
- Webhook support (auto-trigger gap analysis on push/PR events)
- Clone-local strategy (avoid GitHub API rate limits)
- Token auto-refresh (GitHub installation tokens expire after 1 hour)
- Audit trail (who connected which repo, when)

---

## Decision Drivers

### Must Have (P0)
- **Multi-tenant isolation**: Team A's GitHub App installation cannot access Team B's repos
- **Webhook support**: Receive `push`, `pull_request`, `installation` events
- **Rate limit avoidance**: Clone-local to avoid GitHub API rate limits (5000/hour)
- **Token management**: Auto-refresh installation tokens (1-hour TTL)
- **Audit trail**: Who installed, which repos authorized, when

### Should Have (P1)
- **Minimal permissions**: Read-only access to code (no write permissions)
- **Easy setup**: User clicks "Connect GitHub Repo" → OAuth flow → Done
- **Offline support**: Works even if GitHub API is down (uses local clone)
- **Error recovery**: Handle token expiry, network failures gracefully

### Nice to Have (P2)
- **Fine-grained permissions**: Repo-level access control (not org-level)
- **Multi-platform**: Support GitLab, Bitbucket in future
- **Self-hosted GitHub**: Support GitHub Enterprise Server

---

## Considered Options

### Option 1: OAuth User Token (REJECTED)

**Implementation**:
```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='github',
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    authorize_url='https://github.com/login/oauth/authorize',
    access_token_url='https://github.com/login/oauth/access_token',
    userinfo_endpoint='https://api.github.com/user',
    client_kwargs={'scope': 'repo'}
)

@router.get("/auth/github")
async def github_login():
    redirect_uri = "http://localhost:8000/auth/github/callback"
    return await oauth.github.authorize_redirect(redirect_uri)

@router.get("/auth/github/callback")
async def github_callback(request: Request):
    token = await oauth.github.authorize_access_token(request)
    user_info = await oauth.github.get('user', token=token)

    # Store token in database (USER owns token)
    github_integration = GitHubIntegration(
        user_id=current_user.id,
        access_token=token['access_token'],  # User's personal token
        scope='repo'
    )
    db.add(github_integration)
    return {"status": "connected"}
```

**Pros**:
- ✅ Simple setup (standard OAuth 2.0 flow)
- ✅ No GitHub App creation needed
- ✅ User grants permissions via familiar OAuth consent screen

**Cons**:
- ❌ **User-scoped token**: Token tied to user, not organization
- ❌ **No webhook support**: Cannot receive push/PR events
- ❌ **Token tied to user**: If user leaves team, integration breaks
- ❌ **Harder to manage at scale**: 100 teams = 100 OAuth tokens to refresh
- ❌ **Broad permissions**: `repo` scope grants read/write (too much)

**Verdict**: ❌ REJECTED (no webhook support, user-scoped tokens break multi-tenant)

---

### Option 2: GitHub App - API Fetch Strategy (REJECTED)

**Implementation**:
```python
import jwt
import requests

class GitHubAppService:
    def __init__(self, app_id: int, private_key: str):
        self.app_id = app_id
        self.private_key = private_key

    def _generate_jwt(self) -> str:
        """Generate JWT for GitHub App authentication"""
        now = int(time.time())
        payload = {
            "iat": now,
            "exp": now + 600,  # 10 minutes
            "iss": self.app_id
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")

    def get_installation_token(self, installation_id: int) -> str:
        """Get installation access token (1-hour TTL)"""
        jwt_token = self._generate_jwt()
        response = requests.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json"
            }
        )
        data = response.json()
        return data["token"]

    def get_repo_files(self, installation_id: int, owner: str, repo: str) -> list[dict]:
        """Fetch repo files via GitHub API (RATE LIMITED!)"""
        token = self.get_installation_token(installation_id)

        # Recursive tree traversal via API
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            }
        )
        tree = response.json()
        return tree["tree"]  # List of files
```

**Pros**:
- ✅ Multi-tenant isolation (each team has separate installation_id)
- ✅ Webhook support (push, PR events)
- ✅ Organization-level permissions
- ✅ No local disk storage needed

**Cons**:
- ❌ **Rate limits**: 5000 requests/hour per installation (exhausted quickly)
- ❌ **API latency**: 100-300ms per API call (slow for large repos)
- ❌ **Pagination required**: Large repos need multiple API calls
- ❌ **No offline support**: Fails if GitHub API is down
- ❌ **Cost**: API calls count against GitHub quota

**Example Rate Limit Issue**:
```python
# Large repo with 10,000 files
# API recursive tree fetch = 1 request (OK)
# BUT: Content fetch for each file = 10,000 requests (RATE LIMITED!)

for file in files:
    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{file['path']}",
        headers={"Authorization": f"Bearer {token}"}
    )
    content = response.json()  # ❌ Rate limit exceeded after ~1000 files
```

**Verdict**: ❌ REJECTED (rate limits make it unusable for gap analysis on large repos)

---

### Option 3: GitHub App - Clone-Local Strategy (APPROVED ✅)

**Implementation**:
```python
import subprocess
from pathlib import Path

class GitHubAppService:
    def __init__(self, app_id: int, private_key: str):
        self.app_id = app_id
        self.private_key = private_key
        self._token_cache = {}  # {installation_id: (token, expires_at)}

    def _generate_jwt(self) -> str:
        """Generate JWT for GitHub App authentication"""
        now = int(time.time())
        payload = {
            "iat": now,
            "exp": now + 600,  # 10 minutes
            "iss": self.app_id
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")

    def get_installation_token(self, installation_id: int) -> str:
        """
        Get installation access token with auto-refresh.

        Tokens are cached and automatically refreshed 5 minutes before expiry.
        """
        # Check cache
        if installation_id in self._token_cache:
            token, expires_at = self._token_cache[installation_id]

            # Refresh if expiring in <5 minutes
            if datetime.utcnow() < expires_at - timedelta(minutes=5):
                return token

        # Request new token
        jwt_token = self._generate_jwt()
        response = requests.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json"
            }
        )
        response.raise_for_status()

        data = response.json()
        token = data["token"]
        expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))

        # Cache token
        self._token_cache[installation_id] = (token, expires_at)

        return token

    def clone_repo(
        self,
        installation_id: int,
        owner: str,
        repo: str,
        target_dir: Path
    ) -> Path:
        """
        Clone GitHub repo to local filesystem.

        Uses shallow clone (depth=1) to minimize bandwidth.
        """
        token = self.get_installation_token(installation_id)

        # Clone with installation token
        clone_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"

        subprocess.run(
            ["git", "clone", "--depth=1", clone_url, str(target_dir)],
            check=True,
            capture_output=True
        )

        return target_dir

    def scan_local_repo(self, repo_path: Path) -> dict:
        """
        Scan local repo structure (NOT via API).

        Returns folder structure for gap analysis.
        """
        folders = []
        files = []

        for item in repo_path.rglob("*"):
            if item.is_dir() and ".git" not in item.parts:
                folders.append(str(item.relative_to(repo_path)))
            elif item.is_file():
                files.append(str(item.relative_to(repo_path)))

        return {
            "folders": folders,
            "files": files,
            "total_folders": len(folders),
            "total_files": len(files)
        }
```

**Pros**:
- ✅ **No rate limits**: Clone is single API call, scan is local filesystem
- ✅ **Fast**: Local filesystem scan ~10ms for 1000 files (vs 100s via API)
- ✅ **Offline support**: Once cloned, works even if GitHub API is down
- ✅ **Multi-tenant isolation**: Each installation_id has separate permissions
- ✅ **Webhook support**: Receive push/PR events, re-clone on changes
- ✅ **Token auto-refresh**: Cached tokens refreshed 5min before expiry
- ✅ **Audit trail**: Installation events logged

**Cons**:
- ⚠️ Requires local disk storage (~100MB per repo)
- ⚠️ Clone latency (~5-10s for typical repo)
- ⚠️ Token management complexity (auto-refresh, caching)

**Verdict**: ✅ **APPROVED** (best performance, no rate limits, offline support)

---

## Decision Outcome

**Chosen Option**: **Option 3 - GitHub App with Clone-Local Strategy**

### Implementation Details

#### 1. GitHub App Setup

**Create GitHub App** (Pre-Sprint 129 - Jan 30-Feb 2):
```yaml
App Name: SDLC Orchestrator
Homepage URL: https://sdlc.nhatquangholding.com
Webhook URL: https://sdlc.nhatquangholding.com/api/webhooks/github
Webhook Secret: (generate random string, store in secrets)

Permissions:
  Repository permissions:
    - Contents: Read-only (clone repos)
    - Metadata: Read-only (repo info)
    - Pull requests: Read & write (for PR comments - Sprint 129.5)

  Organization permissions:
    - Members: Read-only (team membership)

Subscribe to events:
  - Push (trigger gap analysis)
  - Pull request (trigger gate evaluation - Sprint 129.5)
  - Installation (track app install/uninstall)

Generate private key → Download .pem file

Store in secrets:
  - GITHUB_APP_ID
  - GITHUB_APP_PRIVATE_KEY (contents of .pem file)
  - GITHUB_WEBHOOK_SECRET
```

#### 2. Database Schema

```sql
CREATE TABLE github_installations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  installation_id BIGINT UNIQUE NOT NULL,  -- GitHub installation ID
  account_type VARCHAR(20) NOT NULL,       -- 'user' or 'organization'
  account_login VARCHAR(255) NOT NULL,     -- GitHub username/org name
  installed_by UUID NOT NULL REFERENCES users(id),
  installed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  uninstalled_at TIMESTAMP WITH TIME ZONE,
  status installation_status DEFAULT 'active',  -- 'active', 'suspended', 'uninstalled'

  CONSTRAINT valid_account_type CHECK (account_type IN ('user', 'organization'))
);

CREATE TABLE github_repositories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  installation_id UUID NOT NULL REFERENCES github_installations(id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  github_repo_id BIGINT NOT NULL,          -- GitHub's internal repo ID
  owner VARCHAR(255) NOT NULL,             -- Repo owner (user/org)
  name VARCHAR(255) NOT NULL,              -- Repo name
  full_name VARCHAR(512) NOT NULL,         -- owner/name
  default_branch VARCHAR(100) DEFAULT 'main',

  -- Clone tracking
  local_path TEXT,                         -- Path to local clone
  last_cloned_at TIMESTAMP WITH TIME ZONE,
  clone_status clone_status DEFAULT 'pending',  -- 'pending', 'cloning', 'cloned', 'failed'

  -- Audit
  connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  connected_by UUID NOT NULL REFERENCES users(id),

  CONSTRAINT unique_github_repo UNIQUE (github_repo_id),
  CONSTRAINT unique_project_repo UNIQUE (project_id)
);

CREATE INDEX idx_github_installations_installation_id
  ON github_installations(installation_id);
CREATE INDEX idx_github_repositories_project_id
  ON github_repositories(project_id);
CREATE INDEX idx_github_repositories_full_name
  ON github_repositories(owner, name);
```

#### 3. Installation Flow

**User Flow**:
```
1. User clicks "Connect GitHub Repo" in Extension/Web Dashboard
2. Backend redirects to GitHub App install URL
3. User authorizes SDLC Orchestrator GitHub App
4. GitHub redirects back with installation_id
5. Backend stores installation_id in database
6. User selects which repo to connect
7. Backend clones repo to local storage
8. Extension scans local clone for gap analysis
9. Extension submits gap report to backend
```

**Installation Webhook**:
```python
@router.post("/api/webhooks/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None),
    db: Session = Depends(get_db)
):
    """Handle GitHub webhook events"""
    # Verify signature
    payload = await request.body()
    if not verify_webhook_signature(payload, x_hub_signature_256, WEBHOOK_SECRET):
        raise HTTPException(401, "Invalid signature")

    data = await request.json()

    if x_github_event == "installation":
        action = data["action"]  # created, deleted, suspend, unsuspend

        if action == "created":
            installation = GitHubInstallation(
                installation_id=data["installation"]["id"],
                account_type=data["installation"]["account"]["type"],
                account_login=data["installation"]["account"]["login"],
                installed_by=current_user.id,
                status="active"
            )
            db.add(installation)
            db.commit()

            return {"status": "installation_created"}

        elif action == "deleted":
            installation = db.query(GitHubInstallation).filter(
                GitHubInstallation.installation_id == data["installation"]["id"]
            ).first()

            installation.status = "uninstalled"
            installation.uninstalled_at = datetime.utcnow()
            db.commit()

            return {"status": "installation_deleted"}

    return {"status": "ignored"}
```

#### 4. Clone Strategy

**Shallow Clone** (minimize bandwidth):
```python
async def clone_repo_task(
    installation_id: int,
    owner: str,
    repo: str,
    project_id: UUID,
    db: Session
):
    """Background task to clone GitHub repo"""
    github_service = GitHubAppService()

    # Get repo record
    github_repo = db.query(GitHubRepository).filter(
        GitHubRepository.project_id == project_id
    ).first()

    # Update status
    github_repo.clone_status = "cloning"
    db.commit()

    try:
        # Shallow clone (depth=1, no history)
        target_dir = Path(f"/var/sdlc/repos/{project_id}")
        target_dir.mkdir(parents=True, exist_ok=True)

        token = github_service.get_installation_token(installation_id)
        clone_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"

        subprocess.run(
            [
                "git", "clone",
                "--depth=1",                    # Shallow clone (no history)
                "--single-branch",              # Only default branch
                "--no-tags",                    # No tags
                clone_url,
                str(target_dir)
            ],
            check=True,
            capture_output=True,
            timeout=300  # 5 minutes max
        )

        # Update status
        github_repo.clone_status = "cloned"
        github_repo.local_path = str(target_dir)
        github_repo.last_cloned_at = datetime.utcnow()
        db.commit()

        logger.info(f"Cloned repo {owner}/{repo} to {target_dir}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Clone failed: {e.stderr.decode()}")
        github_repo.clone_status = "failed"
        db.commit()
        raise
```

**Re-clone on Push** (Sprint 129.5):
```python
@router.post("/api/webhooks/github")
async def github_webhook(x_github_event: str = Header(None)):
    if x_github_event == "push":
        data = await request.json()

        # Find project by repo
        github_repo = db.query(GitHubRepository).filter(
            GitHubRepository.github_repo_id == data["repository"]["id"]
        ).first()

        if github_repo:
            # Re-clone repo (fetch latest changes)
            clone_repo_task.delay(
                installation_id=github_repo.installation.installation_id,
                owner=data["repository"]["owner"]["login"],
                repo=data["repository"]["name"],
                project_id=github_repo.project_id
            )

            # Trigger gap analysis (Sprint 129.5)
            trigger_gap_analysis.delay(github_repo.project_id)

        return {"status": "push_received"}
```

#### 5. Token Auto-Refresh

**Problem**: GitHub installation tokens expire after 1 hour

**Solution**: Cache tokens and refresh 5 minutes before expiry

```python
from datetime import datetime, timedelta
from typing import Dict, Tuple

class GitHubAppService:
    def __init__(self, app_id: int, private_key: str):
        self.app_id = app_id
        self.private_key = private_key
        self._token_cache: Dict[int, Tuple[str, datetime]] = {}

    def get_installation_token(self, installation_id: int) -> str:
        """
        Get installation access token with auto-refresh.

        Tokens are cached and automatically refreshed 5 minutes before expiry.
        GitHub tokens have 1-hour TTL.
        """
        # Check cache
        if installation_id in self._token_cache:
            token, expires_at = self._token_cache[installation_id]

            # Refresh if expiring in <5 minutes
            if datetime.utcnow() < expires_at - timedelta(minutes=5):
                logger.debug(f"Using cached token for installation {installation_id}")
                return token
            else:
                logger.info(f"Token expiring soon for installation {installation_id}, refreshing...")

        # Request new token
        jwt_token = self._generate_jwt()
        response = requests.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json"
            }
        )
        response.raise_for_status()

        data = response.json()
        token = data["token"]
        expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))

        # Cache token
        self._token_cache[installation_id] = (token, expires_at)

        logger.info(f"Refreshed token for installation {installation_id}, expires at {expires_at}")

        return token
```

---

## Consequences

### Positive

1. **Performance**:
   - ✅ Clone once, scan locally (no API rate limits)
   - ✅ Local scan ~10ms for 1000 files (vs 100s via API)
   - ✅ Offline support (works even if GitHub API is down)

2. **Security**:
   - ✅ Installation-scoped tokens (multi-tenant isolation)
   - ✅ Fine-grained permissions (read-only, no write access)
   - ✅ Token auto-refresh (no manual intervention)
   - ✅ Audit trail (installation events logged)

3. **Scalability**:
   - ✅ Webhook support (auto-trigger gap analysis on push)
   - ✅ No API rate limits (clone is single API call)
   - ✅ Scales to 100+ teams (each team has separate installation_id)

4. **UX**:
   - ✅ Simple setup (user clicks "Connect GitHub Repo" → Done)
   - ✅ Fast gap analysis (local filesystem scan)
   - ✅ Clear error messages (clone failed, token expired, etc.)

### Negative

1. **Storage**:
   - ⚠️ Requires local disk storage (~100MB per repo)
   - ⚠️ Cleanup required (delete old clones after 30 days)
   - **Mitigation**: Shallow clone (depth=1), periodic cleanup job

2. **Latency**:
   - ⚠️ Clone latency ~5-10s for typical repo
   - ⚠️ Large repos (>1GB) may take 30-60s
   - **Mitigation**: Background job (async), show "Cloning..." status

3. **Complexity**:
   - ⚠️ Token management complexity (auto-refresh, caching)
   - ⚠️ Webhook signature validation required
   - **Mitigation**: Well-tested token refresh logic, HMAC validation

---

## Alternatives Not Chosen

### Alternative A: Self-Hosted GitHub Runner

Use GitHub Actions self-hosted runner to scan repo.

**Pros**: Leverage GitHub Actions infrastructure
**Cons**: Complex setup, requires runner management
**Verdict**: Rejected (too complex for MVP)

### Alternative B: GitLab/Bitbucket Support

Support multiple Git platforms, not just GitHub.

**Pros**: More users, platform-agnostic
**Cons**: 3x integration work, different OAuth flows
**Verdict**: Deferred to post-MVP (Sprint 131+)

### Alternative C: GitHub App with Container Isolation

Run clones in isolated containers (Docker).

**Pros**: Better security, no local disk pollution
**Cons**: Slower (container startup overhead), complex orchestration
**Verdict**: Deferred to P2 (nice-to-have for security)

---

## References

- **GitHub Apps Documentation**: https://docs.github.com/en/apps
- **GitHub App Authentication**: https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app
- **GitHub Webhooks**: https://docs.github.com/en/webhooks
- **GitHub API Rate Limits**: https://docs.github.com/en/rest/rate-limit
- **Git Shallow Clone**: https://git-scm.com/docs/git-clone#Documentation/git-clone.txt---depthltdepthgt

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| Jan 25, 2026 | Explored OAuth User Token | Simple, but no webhook support |
| Jan 27, 2026 | Explored GitHub App + API Fetch | Multi-tenant, but rate limits |
| Jan 29, 2026 | Explored GitHub App + Clone-Local | No rate limits, fast, offline support |
| Jan 30, 2026 | **APPROVED Clone-Local** | Best performance, no rate limits, audit trail |
| Jan 30, 2026 | Add token auto-refresh | Prevent expiry mid-operation |
| Jan 30, 2026 | Add shallow clone | Minimize bandwidth + storage |

---

## Implementation Checklist

- [ ] Pre-Sprint 129: Create GitHub App on GitHub.com
- [ ] Pre-Sprint 129: Install GitHub App on test org
- [ ] Database migration: `s129_001_github_integration.py`
- [ ] Backend API: Installation webhook handler
- [ ] Backend API: Clone repo background job
- [ ] Backend API: List repositories endpoint
- [ ] Extension: "Connect GitHub Repo" command
- [ ] Extension: Repository selection dropdown
- [ ] CLI: `--github=owner/repo` flag
- [ ] Tests: Installation webhook tests
- [ ] Tests: Clone repo tests
- [ ] Tests: Token auto-refresh tests
- [ ] Documentation: GitHub App setup guide
- [ ] Documentation: Troubleshooting common GitHub errors

---

**Status**: ✅ **APPROVED FOR SPRINT 129**
**Approval**: CTO + Backend Lead (Jan 30, 2026)
**Implementation**: Sprint 129 (Feb 17-28, 2026)
**Review Date**: Feb 28, 2026 (Sprint 129 demo)

---

**Document Version**: v1.0
**Author**: Backend Lead + DevOps Lead
**Reviewers**: CTO, Product Owner, Security Team
**Last Updated**: January 30, 2026
