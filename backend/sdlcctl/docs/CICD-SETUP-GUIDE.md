# SDLC 6.0.0 CI/CD Setup Guide

**Version**: 1.0.0
**Framework**: SDLC 6.0.0 Complete Lifecycle
**Last Updated**: December 5, 2025

---

## Quick Start

### 1. Add Configuration File

Create `.sdlc-config.json` in your repository root:

```json
{
  "$schema": "https://raw.githubusercontent.com/nqh-org/sdlcctl/main/schemas/sdlc-config.schema.json",
  "tier": "professional",
  "docs_root": "docs",
  "strict": true,
  "ci": {
    "comment_on_pr": true,
    "update_badge": true,
    "block_merge_on_fail": true
  }
}
```

### 2. Add GitHub Action Workflow

Copy `.github/workflows/sdlc-validate.yml` from this repository or create:

```yaml
name: SDLC 6.0.0 Validation

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
  workflow_dispatch:
    inputs:
      tier:
        description: 'Override tier'
        type: choice
        options: [auto, lite, standard, professional, enterprise]
        default: auto

jobs:
  validate:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install sdlcctl
      - run: sdlcctl validate --format json > validation.json
      - uses: actions/upload-artifact@v4
        with:
          name: sdlc-validation
          path: validation.json
```

### 3. Configure Branch Protection

Go to **Settings > Branches > Branch protection rules** and add:

| Setting | Value |
|---------|-------|
| Branch name pattern | `main` |
| Require status checks | `SDLC Structure Validation` |
| Require branches to be up to date | Yes |
| Include administrators | Yes (recommended) |

---

## Configuration Reference

### `.sdlc-config.json` Options

```json
{
  "$schema": "path/to/schema.json",
  "version": "1.0.0",

  "project": {
    "name": "My Project",
    "description": "Project description",
    "repository": "https://github.com/org/repo"
  },

  "tier": "professional",
  "team_size": 10,
  "docs_root": "docs",
  "strict": false,

  "validation": {
    "fail_on_error": true,
    "fail_on_warning": false,
    "required_score": 80
  },

  "stages": {
    "enabled": ["00", "01", "02", "03", "04", "05"],
    "custom_names": {
      "04": "04-QA-Testing"
    }
  },

  "p0_artifacts": {
    "required": true,
    "custom_paths": {
      "P0-02-SAD": "02-Architecture/system-design.md"
    }
  },

  "ci": {
    "comment_on_pr": true,
    "update_badge": true,
    "block_merge_on_fail": true
  },

  "ignore": [
    "**/node_modules/**",
    "**/.git/**",
    "**/dist/**"
  ]
}
```

### Tier Classification

| Tier | Team Size | Required Stages | P0 Required |
|------|-----------|-----------------|-------------|
| LITE | 1-2 | 4 (00-03) | No |
| STANDARD | 3-10 | 6 (00-05) | No |
| PROFESSIONAL | 10-50 | 10 (00-09) | Yes |
| ENTERPRISE | 50+ | 11 (00-10) | Yes |

---

## Branch Protection Configuration

### Recommended Settings for Main Branch

```yaml
Branch Protection Rules:
  Branch name pattern: main

  Protect matching branches:
    Require a pull request before merging: true
      Required approving reviews: 1
      Dismiss stale reviews: true
      Require review from code owners: false

    Require status checks to pass before merging: true
      Require branches to be up to date: true
      Status checks:
        - "SDLC Structure Validation"  # Required
        - "test"                        # Optional
        - "lint"                        # Optional

    Require conversation resolution: true
    Require signed commits: false
    Require linear history: false

    Include administrators: true

    Allow force pushes: false
    Allow deletions: false
```

### Setting Up via GitHub CLI

```bash
# Enable branch protection with SDLC validation
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["SDLC Structure Validation"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null
```

### Verifying Protection Rules

```bash
# Check current branch protection
gh api repos/{owner}/{repo}/branches/main/protection

# Check required status checks
gh api repos/{owner}/{repo}/branches/main/protection/required_status_checks
```

---

## Monorepo Support

For monorepos with multiple documentation roots:

### Configuration

```json
{
  "tier": "professional",
  "docs_root": "packages/core/docs",
  "monorepo": {
    "enabled": true,
    "packages": [
      {
        "name": "core",
        "docs_root": "packages/core/docs",
        "tier": "professional"
      },
      {
        "name": "utils",
        "docs_root": "packages/utils/docs",
        "tier": "lite"
      }
    ]
  }
}
```

### Workflow for Monorepo

```yaml
name: SDLC 6.0.0 Validation (Monorepo)

on:
  push:
    paths:
      - 'packages/*/docs/**'
      - '.sdlc-config.json'

jobs:
  validate:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        package: [core, utils, api]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install sdlcctl
      - name: Validate ${{ matrix.package }}
        run: |
          sdlcctl validate \
            --path . \
            --docs "packages/${{ matrix.package }}/docs" \
            --format json > validation-${{ matrix.package }}.json
```

---

## Notification Integration

### Slack Notification

Add to workflow after validation step:

```yaml
- name: Notify Slack
  if: failure()
  uses: slackapi/slack-github-action@v1.24.0
  with:
    channel-id: 'sdlc-alerts'
    slack-message: |
      :x: SDLC Validation Failed
      Repository: ${{ github.repository }}
      Branch: ${{ github.ref_name }}
      Commit: ${{ github.sha }}
      Author: ${{ github.actor }}
      <${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View Details>
  env:
    SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
```

### Microsoft Teams Notification

```yaml
- name: Notify Teams
  if: failure()
  uses: jdcargile/ms-teams-notification@v1.4
  with:
    github-token: ${{ github.token }}
    ms-teams-webhook-uri: ${{ secrets.TEAMS_WEBHOOK }}
    notification-summary: "SDLC Validation Failed"
    notification-color: "dc3545"
    timezone: "Asia/Ho_Chi_Minh"
```

### Email Notification (via GitHub)

```yaml
- name: Create Issue on Failure
  if: failure() && github.event_name == 'push' && github.ref == 'refs/heads/main'
  uses: actions/github-script@v7
  with:
    script: |
      await github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: `SDLC Validation Failed on ${context.sha.substring(0, 7)}`,
        body: `## SDLC 6.0.0 Validation Failed\n\n` +
              `**Commit**: ${context.sha}\n` +
              `**Author**: @${context.actor}\n` +
              `**Branch**: main\n\n` +
              `Please review the [validation results](${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}).`,
        labels: ['sdlc-violation', 'priority:high']
      });
```

---

## Advanced Configurations

### Custom Validation Rules

```yaml
# .sdlc-config.json
{
  "validation": {
    "custom_rules": [
      {
        "id": "CUSTOM-001",
        "description": "README must have badges",
        "pattern": "docs/**/README.md",
        "contains": ["![", "shields.io"],
        "severity": "warning"
      }
    ]
  }
}
```

### Excluding Paths

```yaml
{
  "ignore": [
    "**/node_modules/**",
    "**/.git/**",
    "**/dist/**",
    "**/99-Legacy/**",
    "**/archive/**",
    "docs/99-Archive/**"
  ]
}
```

### Tier Auto-Detection

If `tier` is not specified, sdlcctl auto-detects based on:

1. `team_size` in config
2. Number of stages found
3. Default to PROFESSIONAL

```json
{
  "tier": null,
  "team_size": 5
}
```

Result: STANDARD tier (3-10 people)

---

## Troubleshooting

### Common Issues

#### 1. Workflow Not Triggering

**Symptom**: Changes to docs/ don't trigger validation

**Solution**: Check paths filter in workflow
```yaml
paths:
  - 'docs/**'        # Include all docs
  - '!docs/99-*/**'  # Exclude legacy folders
```

#### 2. PR Comment Not Appearing

**Symptom**: Validation runs but no PR comment

**Solution**: Check permissions
```yaml
permissions:
  contents: write
  pull-requests: write
  issues: write
```

#### 3. Badge Not Updating

**Symptom**: Badge shows old status

**Solution**:
1. Ensure `.github/badges/` directory exists
2. Check workflow has push permission
3. Verify branch protection allows GitHub Actions

#### 4. False Positive on P0 Artifacts

**Symptom**: P0 artifact reported missing but exists

**Solution**: Check alternative paths or add custom path
```json
{
  "p0_artifacts": {
    "custom_paths": {
      "P0-04-README": "04-Testing-Quality/README.md"
    }
  }
}
```

### Debug Mode

Run with verbose output:

```bash
sdlcctl validate --verbose --format text
```

Check JSON output:

```bash
sdlcctl validate --format json | jq '.issues'
```

---

## Best Practices

### 1. Start with Warnings Only

```json
{
  "validation": {
    "fail_on_error": true,
    "fail_on_warning": false
  }
}
```

### 2. Gradual Tier Upgrade

1. Start at LITE tier
2. Add stages incrementally
3. Upgrade tier when ready
4. Enable P0 enforcement

### 3. Document Structure First

Before enabling validation:
1. Run `sdlcctl init --tier <your-tier>`
2. Review created structure
3. Add initial content
4. Then enable CI/CD validation

### 4. Use Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: sdlc-validate
        name: SDLC 6.0.0 Validation
        entry: sdlcctl validate --format summary
        language: system
        pass_filenames: false
        files: ^docs/
```

---

## Support

- **Documentation**: [sdlcctl README](../README.md)
- **Issues**: [GitHub Issues](https://github.com/nqh-org/sdlcctl/issues)
- **Framework**: [SDLC 6.0.0 Documentation](https://github.com/nqh-org/SDLC-Enterprise-Framework)

---

**Document Status**: Production Ready
**Compliance**: SDLC 6.0.0 Stage 05
**Last Updated**: December 5, 2025
