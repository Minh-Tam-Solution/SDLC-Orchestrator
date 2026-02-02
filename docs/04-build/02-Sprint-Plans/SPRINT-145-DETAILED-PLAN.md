# Sprint 145: MCP Commands Implementation - DETAILED PLAN

**Sprint**: 145 (5 days - February 3-7, 2026)
**Theme**: Boris Cherny Tactics - MCP Integration (Track 2 Implementation)
**Status**: READY FOR EXECUTION (Pending CTO authorization)
**Based On**: SPEC-0023 MCP Commands Design (1,405 lines, CTO approved 9.6/10)

---

## 📊 Executive Summary

### Sprint Goals

**Primary Objective**: Implement 4 MCP CLI commands (connect, list, test, disconnect) with Slack and GitHub integration, enabling automated bug triage workflow as described by Boris Cherny.

**Deliverables**:
1. ✅ 4 CLI commands (connect, list, test, disconnect)
2. ✅ Slack adapter with HMAC-SHA256 signature verification
3. ✅ GitHub adapter with OAuth + webhook signature
4. ✅ Evidence Vault audit trail integration
5. ✅ Integration tests (E2E with real Slack/GitHub APIs)
6. ✅ Comprehensive documentation

**Effort Estimate**: 2,350 LOC, 88 hours (5 days × 8 hours/day + 8 hours buffer)

### Success Criteria

| Criterion | Target | Validation |
|-----------|--------|------------|
| **Functional** | All 43 acceptance criteria met | Manual testing + automated tests |
| **Performance** | <2s command latency (p95) | pytest-benchmark |
| **Security** | 100% webhook signature verification | Penetration testing |
| **Quality** | >90% test coverage | pytest-cov |
| **Documentation** | 100% CLI reference complete | Technical writer review |

### Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Slack API rate limits | Medium | Medium | Implement exponential backoff + caching |
| GitHub OAuth complexity | Medium | High | Use tested PyGithub library + sandbox testing |
| Evidence Vault integration delay | Low | Medium | Parallel track, can stub initially |
| Webhook signature verification bugs | Medium | High | Extensive unit tests + security review |

---

## 📅 Day-by-Day Breakdown

### Day 1 (February 3, 2026) - CLI Commands + MCP Service

**Goal**: Implement core CLI commands and MCP service foundation

**Tasks**:
1. **CLI Commands** (`sdlcctl/commands/mcp.py` - 300 LOC)
   - `mcp connect` command (100 LOC)
   - `mcp list` command (50 LOC)
   - `mcp test` command (100 LOC)
   - `mcp disconnect` command (50 LOC)

2. **MCP Service** (`services/mcp/mcp_service.py` - 200 LOC)
   - Platform credential validation (50 LOC)
   - Configuration management (50 LOC)
   - Evidence artifact creation (50 LOC)
   - Error handling (50 LOC)

3. **Unit Tests** (150 LOC)
   - Test CLI command parsing (50 LOC)
   - Test MCP service methods (100 LOC)

**Success Criteria**:
- ✅ All 4 commands execute without errors
- ✅ Unit tests pass with >80% coverage
- ✅ CLI help text complete

**Deliverables**:
- `sdlcctl/commands/mcp.py` (300 LOC)
- `services/mcp/mcp_service.py` (200 LOC)
- `tests/unit/commands/test_mcp.py` (150 LOC)
- **Total Day 1**: 650 LOC

---

### Day 2 (February 4, 2026) - Platform Adapters

**Goal**: Implement Slack and GitHub platform adapters with signature verification

**Tasks**:
1. **Slack Adapter** (`services/mcp/slack_adapter.py` - 150 LOC)
   - Bot token validation (30 LOC)
   - HMAC-SHA256 signature verification (40 LOC)
   - Channel access check (30 LOC)
   - Message posting (30 LOC)
   - Error handling (20 LOC)

2. **GitHub Adapter** (`services/mcp/github_adapter.py` - 150 LOC)
   - GitHub App authentication (40 LOC)
   - OAuth scope verification (30 LOC)
   - Issue creation (30 LOC)
   - PR creation (30 LOC)
   - Webhook signature verification (20 LOC)

3. **Config Manager** (`services/mcp/config_manager.py` - 100 LOC)
   - .mcp.json loading/saving (40 LOC)
   - Secret encryption (30 LOC)
   - Environment variable substitution (30 LOC)

4. **Unit Tests** (200 LOC)
   - Slack adapter tests (100 LOC)
   - GitHub adapter tests (100 LOC)

**Success Criteria**:
- ✅ Slack HMAC-SHA256 verification works
- ✅ GitHub OAuth flow complete
- ✅ .mcp.json saved with encrypted secrets
- ✅ Unit tests pass with >85% coverage

**Deliverables**:
- `services/mcp/slack_adapter.py` (150 LOC)
- `services/mcp/github_adapter.py` (150 LOC)
- `services/mcp/config_manager.py` (100 LOC)
- `tests/unit/services/mcp/test_slack_adapter.py` (100 LOC)
- `tests/unit/services/mcp/test_github_adapter.py` (100 LOC)
- **Total Day 2**: 600 LOC

---

### Day 3 (February 5, 2026) - Evidence Vault + Integration

**Goal**: Integrate Evidence Vault for audit trail and complete MCP service integration

**Tasks**:
1. **Evidence Vault Integration** (100 LOC)
   - Evidence artifact creation for MCP actions (50 LOC)
   - Ed25519 signature generation (30 LOC)
   - Hash-chaining with previous manifest (20 LOC)

2. **MCP Webhook Handler** (150 LOC)
   - Slack webhook ingress (50 LOC)
   - GitHub webhook ingress (50 LOC)
   - Rate limiting (30 LOC)
   - Audit logging (20 LOC)

3. **Configuration Validation** (100 LOC)
   - .mcp.json schema validation (50 LOC)
   - Platform credential testing (50 LOC)

4. **Unit Tests** (150 LOC)
   - Evidence Vault integration tests (50 LOC)
   - Webhook handler tests (50 LOC)
   - Config validation tests (50 LOC)

**Success Criteria**:
- ✅ Evidence artifacts created for all MCP actions
- ✅ Ed25519 signatures valid
- ✅ Hash-chaining working (immutable audit trail)
- ✅ Webhook handlers process Slack/GitHub events
- ✅ Unit tests pass with >90% coverage

**Deliverables**:
- `services/mcp/evidence_integration.py` (100 LOC)
- `services/mcp/webhook_handler.py` (150 LOC)
- `services/mcp/config_validator.py` (100 LOC)
- `tests/unit/services/mcp/test_evidence_integration.py` (50 LOC)
- `tests/unit/services/mcp/test_webhook_handler.py` (50 LOC)
- `tests/unit/services/mcp/test_config_validator.py` (50 LOC)
- **Total Day 3**: 500 LOC

---

### Day 4 (February 6, 2026) - Integration Tests (E2E)

**Goal**: Create comprehensive E2E integration tests with real Slack/GitHub APIs

**Tasks**:
1. **Slack E2E Tests** (`tests/integration/test_mcp_slack.py` - 200 LOC)
   - Test 1: Connect to Slack workspace (40 LOC)
   - Test 2: Post test message to channel (40 LOC)
   - Test 3: Verify webhook signature (40 LOC)
   - Test 4: Test bot permissions (40 LOC)
   - Test 5: Disconnect from Slack (40 LOC)

2. **GitHub E2E Tests** (`tests/integration/test_mcp_github.py` - 200 LOC)
   - Test 1: Connect to GitHub repository (40 LOC)
   - Test 2: Create test issue (40 LOC)
   - Test 3: Draft test PR (40 LOC)
   - Test 4: Verify OAuth scopes (40 LOC)
   - Test 5: Disconnect from GitHub (40 LOC)

3. **Evidence Vault E2E Tests** (100 LOC)
   - Test evidence artifact creation (50 LOC)
   - Test hash-chain verification (50 LOC)

4. **Performance Benchmarks** (100 LOC)
   - Benchmark CLI command latency (50 LOC)
   - Benchmark webhook processing (50 LOC)

**Success Criteria**:
- ✅ All E2E tests pass with real APIs (sandboxed)
- ✅ No test flakiness (3 consecutive runs pass)
- ✅ Performance benchmarks meet targets (<2s p95)
- ✅ Evidence artifacts validated

**Test Environment Setup**:
- Slack test workspace: `sdlc-testing.slack.com`
- GitHub test repository: `org/sdlc-test-repo`
- Test credentials stored in HashiCorp Vault

**Deliverables**:
- `tests/integration/test_mcp_slack.py` (200 LOC)
- `tests/integration/test_mcp_github.py` (200 LOC)
- `tests/integration/test_mcp_evidence.py` (100 LOC)
- `tests/performance/test_mcp_benchmarks.py` (100 LOC)
- **Total Day 4**: 600 LOC

---

### Day 5 (February 7, 2026) - Documentation + Polish

**Goal**: Complete documentation, polish CLI UX, and prepare for release

**Tasks**:
1. **CLI Reference Documentation** (300 LOC)
   - `CLI-MCP-COMMANDS-REFERENCE.md` (200 LOC)
   - Update `README.md` with MCP section (100 LOC)

2. **Examples & Tutorials** (100 LOC)
   - `docs/examples/mcp-slack-setup.md` (50 LOC)
   - `docs/examples/mcp-github-workflow.md` (50 LOC)

3. **Troubleshooting Guide** (100 LOC)
   - Common errors and solutions (50 LOC)
   - FAQ (50 LOC)

4. **CLI UX Polish** (100 LOC)
   - Error message improvements (50 LOC)
   - Progress indicators (30 LOC)
   - Color-coded output (20 LOC)

5. **Sprint Completion Report** (200 LOC)
   - Deliverables summary
   - Test results
   - Performance metrics
   - Known issues

**Success Criteria**:
- ✅ Documentation completeness >95%
- ✅ All examples tested and working
- ✅ Troubleshooting guide covers top 10 errors
- ✅ CLI UX polished (color, progress bars)
- ✅ Sprint completion report ready for CTO review

**Deliverables**:
- `docs/02-design/14-Technical-Specs/CLI-MCP-COMMANDS-REFERENCE.md` (200 LOC)
- `backend/sdlcctl/README.md` (updated, +100 LOC)
- `docs/examples/mcp-slack-setup.md` (50 LOC)
- `docs/examples/mcp-github-workflow.md` (50 LOC)
- `docs/troubleshooting/mcp-common-errors.md` (100 LOC)
- `docs/04-build/02-Sprint-Plans/SPRINT-145-COMPLETION-REPORT.md` (200 LOC)
- CLI UX improvements (100 LOC in `mcp.py`)
- **Total Day 5**: 800 LOC

---

## 📊 LOC Breakdown Summary

| Day | Component | LOC | Tests | Docs | Total |
|-----|-----------|-----|-------|------|-------|
| **Day 1** | CLI + MCP Service | 500 | 150 | 0 | 650 |
| **Day 2** | Platform Adapters | 400 | 200 | 0 | 600 |
| **Day 3** | Evidence Vault + Integration | 350 | 150 | 0 | 500 |
| **Day 4** | Integration Tests + Benchmarks | 0 | 600 | 0 | 600 |
| **Day 5** | Documentation + Polish | 100 | 0 | 700 | 800 |
| **Total** | | **1,350** | **1,100** | **700** | **3,150** |

**Note**: Total 3,150 LOC exceeds estimate 2,350 LOC by 34% (conservative estimate, includes buffer)

---

## 🎯 Detailed Task Checklist

### Day 1 Checklist

**CLI Commands** (`sdlcctl/commands/mcp.py`):
- [ ] Import statements (Typer, Rich, subprocess)
- [ ] `mcp_connect_command()` - 4 platform flags (--slack, --github, --jira, --linear)
- [ ] `mcp_list_command()` - Rich table output + --porcelain JSON
- [ ] `mcp_test_command()` - 4-step validation (auth → signature → channel → server)
- [ ] `mcp_disconnect_command()` - Confirmation prompt + cleanup
- [ ] Error handling for all commands
- [ ] Typer CLI app registration

**MCP Service** (`services/mcp/mcp_service.py`):
- [ ] `validate_slack_credentials()` - Bot token + signing secret
- [ ] `validate_github_credentials()` - App ID + private key
- [ ] `save_configuration()` - .mcp.json write with encryption
- [ ] `load_configuration()` - .mcp.json read with decryption
- [ ] `create_evidence_artifact()` - Evidence Vault integration
- [ ] Error classes (InvalidCredentialsError, ConfigNotFoundError)

**Unit Tests** (`tests/unit/commands/test_mcp.py`):
- [ ] Test `mcp connect --slack` success
- [ ] Test `mcp connect --slack` failure (invalid token)
- [ ] Test `mcp list` with 2 platforms
- [ ] Test `mcp list --porcelain` JSON output
- [ ] Test `mcp test --slack` success
- [ ] Test `mcp disconnect --slack` with confirmation

---

### Day 2 Checklist

**Slack Adapter** (`services/mcp/slack_adapter.py`):
- [ ] `SlackAdapter` class initialization
- [ ] `validate_bot_token()` - Call Slack API auth.test
- [ ] `verify_webhook_signature()` - HMAC-SHA256 verification
- [ ] `check_channel_access()` - Verify bot can post to channel
- [ ] `post_message()` - Send message to Slack channel
- [ ] `get_thread_context()` - Retrieve conversation history
- [ ] Error handling (rate limits, network errors)

**GitHub Adapter** (`services/mcp/github_adapter.py`):
- [ ] `GitHubAdapter` class initialization
- [ ] `authenticate_app()` - GitHub App JWT generation
- [ ] `verify_oauth_scopes()` - Check required scopes
- [ ] `create_issue()` - Create GitHub issue from Slack thread
- [ ] `create_pr()` - Draft PR with fix
- [ ] `verify_webhook_signature()` - SHA256 verification
- [ ] Error handling (rate limits, permission errors)

**Config Manager** (`services/mcp/config_manager.py`):
- [ ] `load_config()` - Read .mcp.json
- [ ] `save_config()` - Write .mcp.json
- [ ] `encrypt_secret()` - AES-256 encryption
- [ ] `decrypt_secret()` - AES-256 decryption
- [ ] `substitute_env_vars()` - Replace {{ env.VAR }} placeholders
- [ ] JSON schema validation

**Unit Tests**:
- [ ] Test Slack signature verification (valid + invalid)
- [ ] Test GitHub OAuth flow
- [ ] Test config encryption/decryption
- [ ] Test environment variable substitution

---

### Day 3 Checklist

**Evidence Vault Integration** (`services/mcp/evidence_integration.py`):
- [ ] `create_mcp_artifact()` - Create Evidence artifact for MCP action
- [ ] `generate_ed25519_signature()` - Sign artifact with private key
- [ ] `chain_to_previous_manifest()` - Hash-chain linking
- [ ] `store_artifact()` - Upload to MinIO S3
- [ ] `index_metadata()` - Store metadata in PostgreSQL

**Webhook Handler** (`services/mcp/webhook_handler.py`):
- [ ] `handle_slack_webhook()` - Process Slack event
- [ ] `handle_github_webhook()` - Process GitHub event
- [ ] `rate_limit_check()` - Enforce 100 req/min
- [ ] `audit_log()` - Log all webhook events
- [ ] Error handling (malformed payloads, signature failures)

**Config Validator** (`services/mcp/config_validator.py`):
- [ ] `validate_mcp_config()` - JSON schema validation
- [ ] `test_slack_connection()` - Verify Slack connectivity
- [ ] `test_github_connection()` - Verify GitHub connectivity
- [ ] Error reporting (detailed validation errors)

**Unit Tests**:
- [ ] Test Evidence artifact creation
- [ ] Test Ed25519 signature generation
- [ ] Test hash-chaining
- [ ] Test webhook rate limiting
- [ ] Test config schema validation

---

### Day 4 Checklist

**Slack E2E Tests** (`tests/integration/test_mcp_slack.py`):
- [ ] Test 1: Connect to test Slack workspace
- [ ] Test 2: Post message to #test channel
- [ ] Test 3: Verify HMAC-SHA256 signature
- [ ] Test 4: Check bot permissions (channels:history, chat:write)
- [ ] Test 5: Disconnect and cleanup

**GitHub E2E Tests** (`tests/integration/test_mcp_github.py`):
- [ ] Test 1: Connect to test GitHub repo
- [ ] Test 2: Create test issue with labels
- [ ] Test 3: Draft test PR linked to issue
- [ ] Test 4: Verify OAuth scopes (repo:write, issues:write)
- [ ] Test 5: Close issue and delete PR

**Evidence Vault E2E Tests** (`tests/integration/test_mcp_evidence.py`):
- [ ] Test evidence artifact creation for Slack → GitHub flow
- [ ] Test hash-chain verification across 3 artifacts
- [ ] Test artifact immutability (tamper detection)

**Performance Benchmarks** (`tests/performance/test_mcp_benchmarks.py`):
- [ ] Benchmark `mcp connect` latency (target: <10s)
- [ ] Benchmark `mcp list` latency (target: <2s)
- [ ] Benchmark `mcp test` latency (target: <5s)
- [ ] Benchmark webhook processing (target: <500ms)

---

### Day 5 Checklist

**CLI Reference Documentation** (`CLI-MCP-COMMANDS-REFERENCE.md`):
- [ ] Introduction (purpose, use cases)
- [ ] Installation instructions
- [ ] Command reference for all 4 commands
- [ ] Examples (beginner, intermediate, advanced)
- [ ] Troubleshooting section
- [ ] FAQ

**Examples & Tutorials**:
- [ ] `mcp-slack-setup.md` - Step-by-step Slack integration guide
- [ ] `mcp-github-workflow.md` - End-to-end bug triage workflow

**Troubleshooting Guide**:
- [ ] "invalid_auth" error → Fix: Check bot token
- [ ] "channel_not_found" error → Fix: Invite bot to channel
- [ ] "rate_limit_exceeded" error → Fix: Wait or upgrade tier
- [ ] "webhook_signature_mismatch" error → Fix: Check signing secret
- [ ] Top 10 common errors documented

**CLI UX Polish**:
- [ ] Add Rich progress bars for long operations
- [ ] Color-coded success (green), warning (yellow), error (red)
- [ ] Interactive prompts for secrets (hidden input)
- [ ] Better error messages with actionable hints

**Sprint Completion Report**:
- [ ] Deliverables summary (3,150 LOC delivered)
- [ ] Test results (>90% coverage, all E2E tests pass)
- [ ] Performance metrics (<2s p95 latency achieved)
- [ ] Known issues (list + mitigation)
- [ ] Next sprint recommendations

---

## 🔒 Security Checklist

**OWASP API Security Top 10 Compliance**:
- [ ] API1: Broken Object Level Authorization → Row-level security enforced
- [ ] API2: Broken Authentication → OAuth + JWT validated
- [ ] API3: Broken Object Property Level Authorization → Field-level permissions
- [ ] API4: Unrestricted Resource Consumption → Rate limiting (100 req/min)
- [ ] API5: Broken Function Level Authorization → RBAC enforced
- [ ] API6: Unrestricted Access to Sensitive Business Flows → Webhook signature verification
- [ ] API7: Server Side Request Forgery (SSRF) → Input validation
- [ ] API8: Security Misconfiguration → Secrets encrypted, .mcp.json gitignored
- [ ] API9: Improper Inventory Management → SBOM generated (Syft + Grype)
- [ ] API10: Unsafe Consumption of APIs → Slack/GitHub API responses validated

**Webhook Signature Verification**:
- [ ] Slack: HMAC-SHA256 signature verified for all incoming webhooks
- [ ] GitHub: SHA256 signature verified for all incoming webhooks
- [ ] Replay attack prevention (5-minute timestamp window)
- [ ] Constant-time comparison (prevent timing attacks)

**Secret Management**:
- [ ] All secrets stored in HashiCorp Vault (production)
- [ ] Development secrets in .env file (gitignored)
- [ ] .mcp.json encrypted with AES-256
- [ ] 90-day secret rotation policy enforced

**Audit Trail**:
- [ ] All MCP actions logged to Evidence Vault
- [ ] Ed25519 signatures for tamper-evidence
- [ ] Hash-chaining for immutability
- [ ] Audit trail traceable (Slack thread → GitHub issue → PR → deploy)

---

## 📏 Quality Gates

**Pre-Commit**:
- [ ] Linting (ruff) passes
- [ ] Formatting (black) applied
- [ ] Type checking (mypy --strict) passes
- [ ] No TODOs or placeholders (Zero Mock Policy)

**CI/CD**:
- [ ] All unit tests pass (>90% coverage)
- [ ] All integration tests pass (3 consecutive runs)
- [ ] Performance benchmarks meet targets
- [ ] Security scan (Semgrep) passes
- [ ] SBOM generated (Syft + Grype, zero critical/high CVEs)
- [ ] License compliance (no AGPL contamination)

**Code Review**:
- [ ] 2+ approvers (Tech Lead + Backend Lead)
- [ ] SPEC-0023 alignment verified
- [ ] Security model validated
- [ ] Error handling reviewed
- [ ] Documentation completeness checked

**CTO Approval**:
- [ ] Sprint completion report reviewed
- [ ] All 43 acceptance criteria met
- [ ] Performance metrics validated
- [ ] Security baseline verified
- [ ] Production deployment authorized

---

## 🚀 Deployment Plan

**Sprint 145 Deployment** (February 7, 2026 - End of Day 5):

**Step 1: Staging Deployment** (2 hours)
- [ ] Deploy to staging environment
- [ ] Run smoke tests (4 MCP commands)
- [ ] Verify Evidence Vault integration
- [ ] Test Slack/GitHub integrations with test workspaces

**Step 2: Production Deployment** (2 hours)
- [ ] Deploy CLI to PyPI (pip install sdlcctl)
- [ ] Update GitHub release notes
- [ ] Deploy MCP server to production (Kubernetes)
- [ ] Configure secrets in HashiCorp Vault

**Step 3: Post-Deployment Validation** (1 hour)
- [ ] Run E2E tests against production
- [ ] Monitor Prometheus metrics (latency, errors)
- [ ] Check Grafana dashboards (MCP health)
- [ ] Verify Evidence Vault audit trail

**Rollback Plan** (if issues detected):
- [ ] Revert CLI to previous version
- [ ] Rollback MCP server deployment
- [ ] Notify on-call team
- [ ] Root cause analysis within 24 hours

---

## 📊 Success Metrics

**Functional Metrics**:
- ✅ All 43 acceptance criteria met (from SPEC-0023)
- ✅ 4 CLI commands functional (connect, list, test, disconnect)
- ✅ Slack integration working (webhook signature verified)
- ✅ GitHub integration working (OAuth + issue creation)
- ✅ Evidence Vault audit trail operational

**Performance Metrics**:
- ✅ `mcp connect` latency: <10s (p95)
- ✅ `mcp list` latency: <2s (p95)
- ✅ `mcp test` latency: <5s (p95)
- ✅ `mcp disconnect` latency: <5s (p95)
- ✅ Webhook processing: <500ms (p95)

**Quality Metrics**:
- ✅ Unit test coverage: >90%
- ✅ Integration test coverage: 100% (all 4 commands E2E tested)
- ✅ Security scan: PASS (zero critical/high CVEs)
- ✅ Documentation completeness: >95%

**Business Metrics**:
- ✅ Time saved: 25 minutes/bug → 5 minutes/bug (5x faster)
- ✅ Developer satisfaction: >4.5/5 (quarterly survey)
- ✅ Adoption rate: 80%+ of team using MCP within 30 days

---

## 🔄 Dependencies & Blockers

**Internal Dependencies**:
- ✅ SPEC-0023 approved (CTO review complete)
- ✅ Sprint 144 complete (worktree commands baseline)
- ✅ Evidence Vault service operational
- ✅ HashiCorp Vault configured (secrets management)

**External Dependencies**:
- ⏳ Slack test workspace access (DevOps to provision)
- ⏳ GitHub test repository access (DevOps to provision)
- ⏳ PyGithub library tested (version 2.1.0+)
- ⏳ Slack SDK for Python tested (version 3.23.0+)

**Potential Blockers**:
- ⚠️ Slack API rate limits (mitigated with caching + exponential backoff)
- ⚠️ GitHub OAuth complexity (mitigated with PyGithub library)
- ⚠️ Evidence Vault integration delay (mitigated with parallel track)

---

## 📋 Communication Plan

**Daily Standup** (9:00 AM):
- What did you complete yesterday?
- What are you working on today?
- Any blockers?

**Mid-Sprint Check-in** (Day 3, 3:00 PM):
- Progress review (50% complete expected)
- Risk assessment
- Adjust plan if needed

**Sprint Demo** (Day 5, 4:00 PM):
- Demonstrate all 4 MCP commands
- Show Slack → GitHub integration E2E
- Present performance metrics
- Q&A with stakeholders

**Sprint Retrospective** (Day 5, 5:00 PM):
- What went well?
- What could be improved?
- Action items for Sprint 146

---

## 🎯 Next Sprint Preview (Sprint 146)

**Potential Focus Areas**:
1. **Discord + Jira Integration** (P1 - High priority)
   - Discord bot for bug reports
   - Jira ticket creation from Slack

2. **MCP Server Scalability** (P1 - High priority)
   - Horizontal scaling (3 replicas)
   - Load balancing
   - Performance optimization

3. **Evidence Vault Enhancements** (P2 - Medium priority)
   - Evidence search UI
   - Audit trail visualization
   - Compliance reports

4. **VSCode Worktree Integration** (P2 - Medium priority)
   - Sidebar panel
   - Command palette integration
   - (From Sprint 144 Day 3 P2 design)

---

## ✅ Pre-Sprint Checklist

**Before Day 1 Starts**:
- [ ] CTO approval received for Sprint 145
- [ ] Sprint 144 completion report finalized
- [ ] Slack test workspace provisioned
- [ ] GitHub test repository provisioned
- [ ] HashiCorp Vault secrets configured
- [ ] Development environment setup complete
- [ ] Team briefed on Sprint 145 plan
- [ ] Risk mitigation strategies reviewed

---

**Sprint 145 Status**: 📋 **READY FOR EXECUTION**

**CTO Authorization Required**: ✅ Pending (SPEC-0023 approved 9.6/10)

**Estimated Start Date**: February 3, 2026 (Monday)

**Estimated Completion Date**: February 7, 2026 (Friday)

**Team**: Backend Lead (1 FTE) + Backend Engineer (1 FTE) + QA Engineer (0.5 FTE)

---

*Sprint 145: MCP Commands Implementation - Detailed Plan*
*Based on SPEC-0023 MCP Commands Design (CTO Approved)*
*Framework-First Compliance: ✅ VERIFIED*
*Zero Mock Policy: ✅ ENFORCED*
