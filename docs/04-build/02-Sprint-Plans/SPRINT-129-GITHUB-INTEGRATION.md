# Sprint 129: GitHub Integration (WITHOUT Webhooks)

**Sprint Duration**: Feb 17-28, 2026 (2 weeks)
**Sprint Goal**: Enable GitHub repository connection and gap analysis
**Story Points**: 8 SP (reduced from 9 SP - webhooks deferred)
**Team**: Backend (1 FTE), Extension (2 FTE), CLI (1 FTE)
**Priority**: P0 (BLOCKING for March 1 launch)

---

## Executive Summary

Sprint 129 implements **GitHub Project Onboarding**, enabling users to connect their GitHub repositories and run SDLC 6.1.0 gap analysis. This sprint uses a **clone-local strategy** (NOT API fetch) for better performance and user experience.

**Strategic Context**:
- **Problem**: Users need to onboard existing GitHub projects to SDLC Orchestrator
- **Solution**: GitHub App integration + local clone + gap analysis
- **Impact**: Enables seamless project import, reduces time-to-first-value from hours to minutes

**Key Architectural Decision**:
- ✅ **GitHub App** (NOT OAuth user tokens) → Multi-tenant, webhook-ready, better security
- ✅ **Clone-local strategy** (NOT API fetch) → Faster, no rate limits, better UX
- ❌ **Webhooks deferred** to Sprint 129.5 (P1.5) → Reduce scope risk

**Success Criteria**:
- ✅ App installation completion rate >90%
- ✅ Repo connection success rate >85%
- ✅ Clone + scan completes <30s for typical repo
- ✅ 10 E2E tests passing

---

## Sprint Backlog

### Week 3: Backend + Extension (6 SP, 4 days)

#### Day 1-2: GitHub App Setup (2 SP)

**Tasks**:
- [ ] **GITHUB-001**: Create GitHub App on GitHub.com
  - App name: "SDLC Orchestrator"
  - Homepage URL: `https://sdlc.nhatquangholding.com`
  - Webhook URL: `https://sdlc.nhatquangholding.com/api/webhooks/github` (placeholder)
  - Permissions:
    - **Repository**: Contents (read-only), Metadata (read-only)
    - **Organization**: Members (read-only)
  - Events: Push, Pull Request, Installation
  - Generate private key (.pem file)
  - Note App ID and Installation ID
- [ ] **GITHUB-002**: Store GitHub App credentials
  - `GITHUB_APP_ID` → Vault secret
  - `GITHUB_APP_PRIVATE_KEY` → Vault secret (PEM file contents)
  - `GITHUB_WEBHOOK_SECRET` → Vault secret (random 32-char string)
- [ ] **DB-002**: Create migration `s129_001_github_installations.py`
  - Table: `github_installations` (installation_id, user_id, org_name, installed_at)
  - Table: `project_github_links` (project_id, repo_full_name, installation_id, synced_at)
- [ ] **MODEL-002**: Create SQLAlchemy models
  - `GitHubInstallation`: installation_id, user_id, org_name, installed_at
  - `ProjectGitHubLink`: project_id, repo_full_name, installation_id, synced_at
- [ ] **SERVICE-002**: Implement `github_app_service.py`
  - `generate_jwt()`: Create GitHub App JWT token (10-min expiry)
  - `get_installation_token()`: Get installation access token (1-hour expiry, auto-refresh)
  - `list_installations()`: Get user's GitHub App installations
  - `list_repositories()`: Get repos for an installation
  - `_token_cache`: Cache installation tokens (auto-refresh 5min before expiry)
- [ ] **API-002**: Create GitHub endpoints
  - `GET /github/installations`: List user's installations
  - `GET /github/installations/{id}/repositories`: List repos for installation
  - `POST /projects/{id}/github/link`: Link project to GitHub repo
  - `DELETE /projects/{id}/github/unlink`: Unlink project from GitHub
- [ ] **TEST-004**: Write 8 integration tests
  - JWT generation correctness (signature validation)
  - Installation token retrieval (mock GitHub API)
  - Token auto-refresh (5min before expiry)
  - Token caching (no duplicate API calls)
  - Installation listing (pagination support)
  - Repository listing (large repos >100)
  - Project linking (creates DB record)
  - Project unlinking (soft delete)

**Acceptance Criteria**:
- GitHub App created and installed on test org
- Backend can authenticate as GitHub App
- Installation tokens auto-refresh correctly
- All 8 integration tests passing

---

#### Day 3: Extension Integration (2 SP)

**Tasks**:
- [ ] **EXT-001**: Create `SDLC: Connect GitHub Repository` command
  - Command ID: `sdlc.connectGitHub`
  - Shortcut: None (accessed via command palette)
- [ ] **EXT-002**: Implement `githubService.ts`
  - `listInstallations()`: GET /github/installations
  - `listRepositories(installationId)`: GET /github/installations/{id}/repositories
  - `linkRepository(projectId, repo)`: POST /projects/{id}/github/link
  - `unlinkRepository(projectId)`: DELETE /projects/{id}/github/unlink
- [ ] **EXT-003**: Create repository selection UI
  - Step 1: Select installation (dropdown, if multiple)
  - Step 2: Select repository (quick pick, filterable)
  - Step 3: Confirm clone location (default: workspace root)
  - Progress indicator: "Cloning repository..." (progress bar)
- [ ] **EXT-004**: Implement clone strategy
  - Use `git clone --depth=1` for shallow clone (faster)
  - Check if repo already exists locally (skip clone if exists)
  - Detect `.sdlc-config.json` (link existing project if found)
  - Show success message: "Connected to {repo_name}"
- [ ] **EXT-005**: Trigger gap analysis after connect
  - Automatically run gap analysis on cloned repo
  - Show results in Context Panel
  - Submit gap report to backend (POST /projects/{id}/gap-reports)
- [ ] **EXT-006**: Register project with `github_repo_id`
  - If project doesn't exist, create new project
  - Set `github_repo_id` = `owner/repo`
  - Set `github_installation_id` = installation ID
- [ ] **TEST-005**: Write 10 unit tests
  - Command registered correctly
  - Installation listing (mock API)
  - Repository selection (mock UI input)
  - Clone success (mock git command)
  - Clone failure (show error message)
  - Existing repo detection (skip clone)
  - Gap analysis trigger (after clone)
  - Project creation (if not exists)
  - Project linking (update DB)
  - Error handling (GitHub API failures)

**Acceptance Criteria**:
- Command appears in command palette
- UI guides user through 3-step flow
- Clone completes <30s for typical repo
- Gap analysis runs automatically
- All 10 unit tests passing

---

#### Day 4: Error Handling + Recovery (2 SP)

**Tasks**:
- [ ] **ERROR-001**: Handle user not authorized for repo
  - Detect: GitHub API returns 403 Forbidden
  - Action: Show message "You don't have access to {repo}. Ask owner to grant access."
  - UI: Offer "Choose Different Repo" button
- [ ] **ERROR-002**: Handle GitHub App not installed
  - Detect: No installations found for user
  - Action: Show message "Please install SDLC Orchestrator GitHub App"
  - UI: Open GitHub.com installation page (button)
  - After install: Automatically retry connection
- [ ] **ERROR-003**: Handle rate limit exceeded
  - Detect: GitHub API returns 429 Too Many Requests
  - Action: Show message "GitHub API rate limit exceeded. Retry in {reset_time} minutes."
  - UI: Disable "Retry" button until reset time
  - Log: Track rate limit events for monitoring
- [ ] **ERROR-004**: Handle network errors
  - Detect: ECONNREFUSED, ETIMEDOUT, DNS errors
  - Action: Show message "Network error. Check your connection and try again."
  - Retry: Exponential backoff (1s, 2s, 4s, 8s, max 3 retries)
  - UI: Show retry progress
- [ ] **ERROR-005**: Handle large repos (>10K files)
  - Detect: Repo size from GitHub API
  - Action: Show warning "This repo is large ({size}MB). Clone may take a few minutes."
  - UI: Offer shallow clone option (default: --depth=1)
  - Progress: Show clone progress bar
- [ ] **ERROR-006**: Handle clone failures
  - Detect: `git clone` exit code ≠ 0
  - Action: Parse error message and show user-friendly version
  - Common errors:
    - "Repository not found" → "Repo doesn't exist or access denied"
    - "Authentication failed" → "GitHub credentials expired. Reinstall GitHub App"
    - "Disk full" → "Not enough disk space. Free up space and try again"
- [ ] **TEST-006**: Write 12 error scenario tests
  - User not authorized (403)
  - GitHub App not installed (no installations)
  - Rate limit exceeded (429)
  - Network timeout (ETIMEDOUT)
  - Large repo warning (>10K files)
  - Clone failure (git command error)
  - Disk full error (ENOSPC)
  - Invalid installation ID (404)
  - Token expired (401)
  - Concurrent clone (prevent race)
  - Partial clone (network interruption)
  - Retry logic (exponential backoff)

**Acceptance Criteria**:
- All error messages are user-friendly
- Retry logic works correctly (exponential backoff)
- Large repos show warning before clone
- All 12 error tests passing

---

### Week 4: CLI + Documentation (2 SP, 2 days)

#### Day 5: CLI GitHub Flag (1 SP)

**Tasks**:
- [ ] **CLI-001**: Add `--github` flag to `sdlcctl init`
  - Syntax: `sdlcctl init --github=owner/repo [--tier=PROFESSIONAL]`
  - Example: `sdlcctl init --github=facebook/react --tier=ENTERPRISE`
- [ ] **CLI-002**: Implement GitHub App installation detection
  - Check if GitHub App is installed on user/org
  - If not installed: Show installation URL and prompt user
  - After install: Wait for webhook confirmation (or manual refresh)
- [ ] **CLI-003**: Implement repo cloning logic
  - If repo doesn't exist locally: Clone to current directory
  - If repo exists locally: Link to GitHub installation
  - Use `git clone --depth=1` for shallow clone
  - Show progress: "Cloning {repo}... (X/Y MB)"
- [ ] **CLI-004**: Register project with backend
  - Create project via API (POST /projects)
  - Set `github_repo_id` and `github_installation_id`
  - Upload gap analysis report
- [ ] **TEST-007**: Write 8 unit tests
  - Flag parsing (`--github=owner/repo`)
  - Installation detection (mock GitHub API)
  - Clone success (mock git command)
  - Clone failure (show error)
  - Existing repo detection (skip clone)
  - Project registration (mock backend API)
  - Gap analysis trigger (after clone)
  - Error handling (invalid repo format)

**Acceptance Criteria**:
- `--github` flag works correctly
- Installation check prevents errors
- Clone completes successfully
- Project registered with backend
- All 8 unit tests passing

---

#### Day 6-7: Documentation + Testing (1 SP)

**Tasks**:
- [ ] **DOC-004**: Write GitHub integration user guide
  - How to install GitHub App (screenshots)
  - How to connect repo from Extension (step-by-step)
  - How to connect repo from CLI (examples)
  - Troubleshooting common errors:
    - "GitHub App not installed" → Install guide
    - "Access denied" → Permission guide
    - "Rate limit exceeded" → Wait time explanation
    - "Clone failed" → Network/disk troubleshooting
- [ ] **DOC-005**: Write GitHub App setup guide (for admins)
  - How to create GitHub App (detailed)
  - How to configure permissions
  - How to generate private key
  - How to store secrets securely (Vault)
- [ ] **DOC-006**: Update API documentation
  - Add GitHub endpoints to OpenAPI spec
  - Add request/response examples
  - Add error codes (400, 401, 403, 404, 429)
- [ ] **DOC-007**: Write troubleshooting guide
  - Common GitHub API errors and fixes
  - Clone failures and solutions
  - Token expiry handling
  - Rate limit recovery
- [ ] **TEST-008**: Write 10 E2E tests
  - Install GitHub App → Connect repo → Gap analysis
  - Connect existing local repo → Link to GitHub
  - Unlink repo → Remove GitHub connection
  - Reconnect repo → Update installation ID
  - Multiple installations → Select correct one
  - Large repo → Show warning → Clone successfully
  - Rate limit → Show message → Retry after reset
  - Network error → Retry → Success
  - Invalid token → Reinstall app → Retry
  - Concurrent clones → Prevent race condition

**Acceptance Criteria**:
- User guide published to docs site
- API docs updated with GitHub endpoints
- Troubleshooting guide covers all errors
- 10 E2E tests passing

---

#### Day 8: Final Testing + Demo (0 SP - buffer)

**Tasks**:
- [ ] **FINAL-001**: Run full regression test suite
  - Unit tests: 36 tests (8+10+12+8)
  - E2E tests: 10 tests
  - Performance tests: Clone time, API latency
  - Security tests: Token validation, rate limiting
- [ ] **FINAL-002**: Performance validation
  - Clone + scan <30s for typical repo (<10K files)
  - API response <2s (p95)
  - Token refresh <500ms
  - Installation listing <1s
- [ ] **FINAL-003**: Security validation
  - Token storage (hashed, not raw)
  - Installation token auto-refresh
  - Rate limiting enforcement
  - No secrets in logs
- [ ] **FINAL-004**: Demo to stakeholders
  - Show Extension flow (connect repo)
  - Show CLI flow (`--github` flag)
  - Show gap analysis results
  - Show error handling (simulate failures)
- [ ] **FINAL-005**: Sprint retrospective
  - What went well
  - What could be improved
  - Learnings for Sprint 129.5 (webhooks)

**Acceptance Criteria**:
- All 46 tests passing (36 unit + 10 E2E)
- Performance requirements met
- Security scan passing (Semgrep)
- Demo successful
- Retrospective documented

---

## Technical Architecture

### GitHub App Authentication Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│Extension │     │ Backend  │     │ GitHub   │     │  User    │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │ "Connect repo" │                │                │
     │───────────────>│                │                │
     │                │                │                │
     │                │ List installations              │
     │                │───────────────>│                │
     │                │                │                │
     │                │ No installations found          │
     │                │<───────────────│                │
     │                │                │                │
     │ "Install app"  │                │                │
     │───────────────────────────────>│                │
     │                │                │                │
     │                │                │ Open GitHub.com│
     │                │                │───────────────>│
     │                │                │                │
     │                │                │ Install app    │
     │                │                │<───────────────│
     │                │                │                │
     │                │ Webhook: installation_created   │
     │                │<───────────────│                │
     │                │                │                │
     │ Retry "Connect"│                │                │
     │───────────────>│                │                │
     │                │                │                │
     │                │ List installations (found!)     │
     │                │───────────────>│                │
     │                │                │                │
     │                │ Generate JWT   │                │
     │                │ (10-min expiry)│                │
     │                │                │                │
     │                │ Get installation token          │
     │                │───────────────>│                │
     │                │                │                │
     │                │ Installation token (1-hour)     │
     │                │<───────────────│                │
     │                │                │                │
     │ Installations  │                │                │
     │<───────────────│                │                │
     │                │                │                │
     │ Select installation              │                │
     │───────────────>│                │                │
     │                │                │                │
     │                │ List repos     │                │
     │                │───────────────>│                │
     │                │                │                │
     │                │ Repos (with token)              │
     │                │<───────────────│                │
     │                │                │                │
     │ Repos list     │                │                │
     │<───────────────│                │                │
     │                │                │                │
     │ Select repo    │                │                │
     │───────────────>│                │                │
     │                │                │                │
     │                │ Link project   │                │
     │                │ (store installation_id)         │
     │                │                │                │
     │ Success        │                │                │
     │<───────────────│                │                │
     │                │                │                │
     │ git clone --depth=1 {repo}      │                │
     │────────────────────────────────>│                │
     │                │                │                │
     │ Clone complete │                │                │
     │<────────────────────────────────│                │
     │                │                │                │
```

### Clone-Local Strategy

**Why clone-local instead of API fetch?**

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **API Fetch** | No disk usage | Rate limits (5000/hour), slow for large repos, complex pagination | ❌ |
| **Clone-local** | Fast, no rate limits, works offline, familiar tool (git) | Disk usage (~100MB per repo) | ✅ |

**Implementation**:
```typescript
async function cloneRepository(repoUrl: string, targetDir: string): Promise<void> {
    const command = `git clone --depth=1 ${repoUrl} ${targetDir}`;

    return new Promise((resolve, reject) => {
        exec(command, { maxBuffer: 1024 * 1024 * 10 }, (error, stdout, stderr) => {
            if (error) {
                reject(new Error(`Clone failed: ${stderr}`));
            } else {
                resolve();
            }
        });
    });
}
```

### Gap Analysis on Local Clone

**Sequence**:
1. **Clone repo** → Local filesystem
2. **Scan structure** → Read directories, check for SDLC folders
3. **Compute compliance** → Compare against tier requirements
4. **Submit report** → POST /projects/{id}/gap-reports

**Gap Analysis Service** (runs locally in Extension/CLI):
```typescript
interface GapAnalysisReport {
    project_id: string;
    tier: 'LITE' | 'STANDARD' | 'PROFESSIONAL' | 'ENTERPRISE';
    existing_folders: string[];
    missing_folders: string[];
    compliance_score: number;  // 0-100
    recommendations: string[];
}

async function runGapAnalysis(projectPath: string, tier: string): Promise<GapAnalysisReport> {
    // 1. Get tier requirements from backend
    const requirements = await apiClient.get(`/rulesets/${tier}`);

    // 2. Scan local project structure
    const existingFolders = await scanProjectFolders(projectPath);

    // 3. Compute missing folders
    const missingFolders = requirements.required_stages.filter(
        stage => !existingFolders.includes(stage)
    );

    // 4. Calculate compliance score
    const complianceScore = Math.round(
        (existingFolders.length / requirements.required_stages.length) * 100
    );

    // 5. Generate recommendations
    const recommendations = generateRecommendations(missingFolders, tier);

    return {
        project_id: projectId,
        tier,
        existing_folders: existingFolders,
        missing_folders: missingFolders,
        compliance_score: complianceScore,
        recommendations
    };
}
```

---

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/github/installations` | GET | User | List user's GitHub App installations |
| `/github/installations/{id}/repositories` | GET | User | List repos for installation |
| `/projects/{id}/github/link` | POST | Admin | Link project to GitHub repo |
| `/projects/{id}/github/unlink` | DELETE | Admin | Unlink project from GitHub |
| `/rulesets/{tier}` | GET | Public | Get tier requirements for gap analysis |
| `/projects/{id}/gap-reports` | POST | User | Submit gap analysis report |
| `/projects/{id}/gap-reports` | GET | User | Get historical gap reports |

---

## Performance Requirements

| Metric | Target | Measurement | Rationale |
|--------|--------|-------------|-----------|
| Clone Time | <30s (typical repo) | Extension timer | Typical repo ~10K files, <100MB |
| API Response | <2s (p95) | Prometheus | GitHub API + token refresh |
| Installation Token | <500ms | Backend timer | JWT generation + GitHub API |
| Gap Analysis | <5s (10K files) | Extension timer | Local filesystem scan |
| Repo Listing | <1s (100 repos) | Backend timer | GitHub API pagination |

---

## Risk Assessment (UPDATED - Webhooks Deferred)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| GitHub API rate limits | Medium | High | Clone-local strategy (no API scan) |
| Large repo (>10K files) | Medium | Medium | Shallow clone (--depth=1), show warning |
| Installation token expiry | High | High | Auto-refresh 5min before expiry |
| Clone failure | Medium | Medium | Retry with exponential backoff |
| Disk space full | Low | Medium | Check free space before clone |
| Network errors | Medium | Medium | Exponential backoff (max 3 retries) |
| ~~Webhook overload~~ | ~~High~~ | ~~High~~ | **DEFERRED to Sprint 129.5** ✅ |

---

## Definition of Done

- [ ] All 8 user stories completed
- [ ] 46 tests passing (36 unit + 10 E2E)
- [ ] Code coverage >95%
- [ ] Security scan passing (Semgrep)
- [ ] Performance requirements met (<30s clone)
- [ ] GitHub App created and tested
- [ ] User guides published
- [ ] API docs updated
- [ ] Demo to stakeholders completed
- [ ] CTO approval received

---

## Sprint Retrospective Template

**What went well**:
- [ ] Clone-local strategy (faster than API fetch)
- [ ] GitHub App authentication (multi-tenant ready)
- [ ] Error handling (user-friendly messages)

**What could be improved**:
- [ ] Large repo handling (show progress bar)
- [ ] Token caching (reduce API calls)
- [ ] Documentation (more screenshots)

**Deferred to Sprint 129.5**:
- [ ] GitHub webhooks (push, PR events)
- [ ] Auto-trigger gate evaluation
- [ ] PR status checks

**Action items**:
- [ ] Monitor clone times in production
- [ ] Track GitHub API rate limits
- [ ] Gather user feedback on UX flow

---

**Sprint Owner**: Extension Lead
**Product Owner**: CTO
**Stakeholders**: Backend Team, CLI Team, Product Team

**Status**: 🟡 READY FOR KICKOFF (Feb 17, 2026)
