# SDLC Orchestrator - Pilot Team Onboarding Runbook

**Version**: 1.0.0
**Last Updated**: January 29, 2026
**Owner**: Customer Success Team
**Framework**: SDLC 6.1.0

---

## Table of Contents

1. [Overview](#overview)
2. [Pilot Teams](#pilot-teams)
3. [Onboarding Workflow](#onboarding-workflow)
4. [Tier Configuration](#tier-configuration)
5. [GitHub Integration](#github-integration)
6. [Post-Onboarding Checklist](#post-onboarding-checklist)
7. [Support Procedures](#support-procedures)

---

## Overview

This runbook covers the onboarding process for SDLC Orchestrator pilot teams. Each pilot team receives:

- Dedicated project workspace
- Tier-appropriate configuration
- GitHub integration (webhooks, OAuth)
- Pre-configured gates (G0.1 - G9)
- API credentials
- Welcome kit with documentation

---

## Pilot Teams

### Team Profiles

| Team ID | Company | Tier | Contact | Special Requirements |
|---------|---------|------|---------|---------------------|
| **alpha** | NHQ Holdings | ENTERPRISE | cto@nhq.com | Full feature validation, high SLA |
| **beta** | TechViet Solutions | PROFESSIONAL | lead@techviet.vn | Multi-project governance |
| **gamma** | StartupHub VN | STANDARD | founder@startuphub.vn | High-velocity teams |
| **delta** | DataFlow Analytics | PROFESSIONAL | eng@dataflow.io | Compliance-heavy workflows |
| **epsilon** | MicroSaaS Studio | LITE | solo@microsaas.dev | Minimal overhead |

### Tier Feature Matrix

| Feature | LITE | STANDARD | PROFESSIONAL | ENTERPRISE |
|---------|------|----------|--------------|------------|
| Gates Enabled | G0-G2 | G0-G4 | All (G0-G9) | All (G0-G9) |
| Vibecoding Index | Basic | Full | Full + Alerts | Full + Custom |
| GitHub Integration | Basic | Full | Full + Webhooks | Full + SSO |
| Support SLA | 48h | 24h | 4h | 1h |
| Custom Policies | No | No | Yes | Yes + Review |
| Evidence Retention | 30 days | 90 days | 1 year | Unlimited |

---

## Onboarding Workflow

### Automated Onboarding

Use the pilot onboarding script for automated setup:

```bash
cd backend/scripts/production

# Onboard specific team
python pilot_onboarding.py --team alpha

# Onboard all teams
python pilot_onboarding.py --all

# Dry-run mode (preview changes)
python pilot_onboarding.py --team beta --dry-run
```

### Manual Onboarding Steps

If manual onboarding is required:

#### Step 1: Verify Prerequisites

```bash
# Check environment
python pilot_onboarding.py --team <team_id> --step verify_prerequisites

# Required:
# - API server running
# - Database accessible
# - GitHub OAuth configured
# - Email service available
```

#### Step 2: Create Project

```bash
# Create project via API
curl -X POST https://api.sdlc-orchestrator.io/api/v1/projects \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alpha Team Project",
    "slug": "alpha-team",
    "tier": "ENTERPRISE",
    "owner_email": "cto@nhq.com"
  }'
```

#### Step 3: Configure Tier Settings

```bash
# Apply tier configuration
python pilot_onboarding.py --team <team_id> --step configure_tier

# Settings applied:
# - Gate requirements
# - Evidence retention
# - Vibecoding thresholds
# - Support SLA
```

#### Step 4: Setup GitHub Integration

```bash
# Register GitHub App
python pilot_onboarding.py --team <team_id> --step setup_github

# This will:
# 1. Create GitHub App installation
# 2. Configure webhooks (push, pull_request, issues)
# 3. Set up OAuth for team members
# 4. Enable repository sync
```

#### Step 5: Create Gates

```bash
# Initialize gates for project
python pilot_onboarding.py --team <team_id> --step create_gates

# Gates created:
# G0.1 - Foundation Ready
# G0.2 - Solution Diversity
# G1 - Design Ready
# G2 - Ship Ready
# G3 - Build Complete
# G4 - Test Complete
# ... (tier-dependent)
```

#### Step 6: Generate API Key

```bash
# Generate API credentials
python pilot_onboarding.py --team <team_id> --step generate_api_key

# Output:
# API Key: sk_live_xxxxxxxxxxxxxxxxxxxx
# API Secret: (stored in Vault, sent via secure email)
```

#### Step 7: Send Welcome Email

```bash
# Send welcome email with quickstart
python pilot_onboarding.py --team <team_id> --step send_welcome

# Email includes:
# - Login credentials
# - API documentation link
# - Quickstart guide
# - Support contact
```

---

## Tier Configuration

### LITE Tier

```yaml
tier: LITE
config:
  gates_enabled: ["G0.1", "G0.2", "G1", "G2"]
  vibecoding:
    enabled: true
    thresholds:
      green: 30
      yellow: 60
      red: 80
    alerts: false
  github:
    webhooks: basic
    oauth: true
    sso: false
  evidence:
    retention_days: 30
  support:
    sla_hours: 48
    channels: ["email"]
```

### STANDARD Tier

```yaml
tier: STANDARD
config:
  gates_enabled: ["G0.1", "G0.2", "G1", "G2", "G3", "G4"]
  vibecoding:
    enabled: true
    thresholds:
      green: 30
      yellow: 60
      red: 80
    alerts: true
  github:
    webhooks: full
    oauth: true
    sso: false
  evidence:
    retention_days: 90
  support:
    sla_hours: 24
    channels: ["email", "slack"]
```

### PROFESSIONAL Tier

```yaml
tier: PROFESSIONAL
config:
  gates_enabled: ["G0.1", "G0.2", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9"]
  vibecoding:
    enabled: true
    thresholds:
      green: 25
      yellow: 50
      red: 75
    alerts: true
    custom_rules: true
  github:
    webhooks: full
    oauth: true
    sso: false
  evidence:
    retention_days: 365
  policies:
    custom_enabled: true
  support:
    sla_hours: 4
    channels: ["email", "slack", "phone"]
```

### ENTERPRISE Tier

```yaml
tier: ENTERPRISE
config:
  gates_enabled: all
  vibecoding:
    enabled: true
    thresholds: custom
    alerts: true
    custom_rules: true
    executive_dashboard: true
  github:
    webhooks: full
    oauth: true
    sso: true
  evidence:
    retention_days: unlimited
  policies:
    custom_enabled: true
    review_required: true
  support:
    sla_hours: 1
    channels: ["email", "slack", "phone", "dedicated_csm"]
    dedicated_support: true
```

---

## GitHub Integration

### Webhook Configuration

Webhooks are automatically configured for:

| Event | Action |
|-------|--------|
| `push` | Trigger code analysis |
| `pull_request` | Gate evaluation |
| `pull_request_review` | Approval tracking |
| `issues` | Task linkage |
| `check_run` | CI/CD integration |

### OAuth Scopes

Required OAuth scopes:

```yaml
scopes:
  - repo           # Full repository access
  - read:org       # Organization membership
  - workflow       # GitHub Actions
  - admin:repo_hook # Webhook management
```

### Repository Setup

After onboarding, teams should:

1. **Add `.sdlc.yaml`** to repository root:

```yaml
# .sdlc.yaml
version: "1.0"
project_id: <from-onboarding>
tier: <LITE|STANDARD|PROFESSIONAL|ENTERPRISE>

gates:
  auto_evaluate: true
  block_merge: true  # Block PRs that fail gates

evidence:
  auto_collect: true
  include_patterns:
    - "docs/**/*.md"
    - "tests/**/*.py"
```

2. **Configure branch protection**:

```bash
# Enable required status checks
gh api repos/{owner}/{repo}/branches/main/protection \
  -X PUT \
  -F required_status_checks='{"strict":true,"contexts":["sdlc-gate-check"]}'
```

---

## Post-Onboarding Checklist

After onboarding is complete, verify:

### Technical Verification

- [ ] Project accessible in dashboard
- [ ] API key works (`curl /health` with auth)
- [ ] GitHub webhooks receiving events
- [ ] Gates visible in project settings
- [ ] Evidence vault accessible

### Communication Verification

- [ ] Welcome email received
- [ ] Team members can login
- [ ] Slack channel created (if applicable)
- [ ] Support ticket system configured

### Documentation Verification

- [ ] Quickstart guide sent
- [ ] API documentation accessible
- [ ] Tier-specific features documented
- [ ] Contact information provided

---

## Support Procedures

### Support Tiers

| Priority | LITE | STANDARD | PROFESSIONAL | ENTERPRISE |
|----------|------|----------|--------------|------------|
| P1 (Critical) | 48h | 24h | 4h | 1h |
| P2 (High) | 72h | 48h | 8h | 4h |
| P3 (Medium) | 5 days | 3 days | 24h | 8h |
| P4 (Low) | Best effort | 5 days | 3 days | 24h |

### Escalation Path

```
Level 1: Customer Success →
Level 2: Technical Support →
Level 3: Engineering Team →
Level 4: CTO
```

### Common Issues

#### Issue: Webhooks not receiving events

```bash
# Check webhook delivery
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/{owner}/{repo}/hooks/{hook_id}/deliveries

# Re-register webhook
python pilot_onboarding.py --team <team_id> --step setup_github --force
```

#### Issue: Gate evaluation timing out

```bash
# Check OPA health
curl https://api.sdlc-orchestrator.io/api/v1/gates/health

# Clear cache and retry
curl -X POST https://api.sdlc-orchestrator.io/api/v1/gates/cache/clear
```

#### Issue: Evidence upload failing

```bash
# Check MinIO connectivity
curl https://api.sdlc-orchestrator.io/api/v1/evidence/health

# Verify storage quota
curl https://api.sdlc-orchestrator.io/api/v1/projects/{id}/storage
```

---

## Emergency Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| Customer Success Lead | cs@sdlc-orchestrator.io | Business hours |
| Technical Support | support@sdlc-orchestrator.io | 24/7 (Enterprise) |
| Engineering On-Call | #eng-oncall Slack | 24/7 |

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | Jan 29, 2026 | CS Team | Initial runbook |

---

**Document Status**: ✅ Production Ready
