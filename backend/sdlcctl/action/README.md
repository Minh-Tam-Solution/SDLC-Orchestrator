# SDLC 6.0.5 Validator Action

GitHub Action to validate project documentation structure against SDLC 6.0.5 standards.

## Features

- Validate docs/ folder structure against SDLC 6.0.5
- Support for 4 tiers: LITE, STANDARD, PROFESSIONAL, ENTERPRISE
- P0 artifact detection for AI discoverability
- PR comments with validation results
- Status badge generation
- Configurable strictness levels

## Quick Start

```yaml
name: SDLC Validation

on:
  push:
    branches: [main]
    paths: ['docs/**']
  pull_request:
    paths: ['docs/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate SDLC Structure
        uses: nqh-org/sdlcctl/action@v1
        with:
          tier: professional
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `path` | Project root path | No | `.` |
| `docs_root` | Documentation folder | No | `docs` |
| `tier` | Project tier (lite/standard/professional/enterprise/auto) | No | `auto` |
| `config_file` | Path to .sdlc-config.json | No | `.sdlc-config.json` |
| `strict` | Fail on warnings | No | `false` |
| `comment_on_pr` | Post PR comment | No | `true` |
| `update_badge` | Update status badge | No | `true` |
| `fail_on_error` | Fail action on errors | No | `true` |
| `python_version` | Python version | No | `3.11` |

## Outputs

| Output | Description |
|--------|-------------|
| `valid` | Whether validation passed (true/false) |
| `score` | Compliance score (0-100) |
| `tier` | Detected or configured tier |
| `errors` | Number of errors found |
| `warnings` | Number of warnings found |
| `stages_found` | Number of stages found |
| `stages_required` | Required stages for tier |
| `report_path` | Path to JSON report |

## Usage Examples

### Basic Usage

```yaml
- uses: nqh-org/sdlcctl/action@v1
```

### With Configuration File

Create `.sdlc-config.json`:

```json
{
  "tier": "professional",
  "docs_root": "docs",
  "strict": true
}
```

```yaml
- uses: nqh-org/sdlcctl/action@v1
```

### Override Tier

```yaml
- uses: nqh-org/sdlcctl/action@v1
  with:
    tier: enterprise
    strict: 'true'
```

### Custom Documentation Path

```yaml
- uses: nqh-org/sdlcctl/action@v1
  with:
    docs_root: 'documentation'
```

### Monorepo Support

```yaml
jobs:
  validate:
    strategy:
      matrix:
        package: [core, api, web]
    steps:
      - uses: actions/checkout@v4
      - uses: nqh-org/sdlcctl/action@v1
        with:
          path: 'packages/${{ matrix.package }}'
          docs_root: 'docs'
```

### Using Outputs

```yaml
- name: Validate
  id: sdlc
  uses: nqh-org/sdlcctl/action@v1

- name: Check Results
  run: |
    echo "Valid: ${{ steps.sdlc.outputs.valid }}"
    echo "Score: ${{ steps.sdlc.outputs.score }}"
    if [ "${{ steps.sdlc.outputs.score }}" -lt "80" ]; then
      echo "Score below threshold!"
    fi
```

### Disable PR Comments

```yaml
- uses: nqh-org/sdlcctl/action@v1
  with:
    comment_on_pr: 'false'
```

### Continue on Failure

```yaml
- uses: nqh-org/sdlcctl/action@v1
  with:
    fail_on_error: 'false'

- name: Custom Failure Handling
  if: steps.sdlc.outputs.valid != 'true'
  run: echo "Validation failed but continuing..."
```

## Tier Requirements

| Tier | Team Size | Required Stages | P0 Artifacts |
|------|-----------|-----------------|--------------|
| LITE | 1-2 | 00-03 (4) | No |
| STANDARD | 3-10 | 00-05 (6) | No |
| PROFESSIONAL | 10-50 | 00-09 (10) | Yes |
| ENTERPRISE | 50+ | 00-10 (11) | Yes |

## Status Badge

After running on main branch, add to README:

```markdown
![SDLC Status](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/OWNER/REPO/main/.github/badges/sdlc-status.json)
```

## PR Comment Example

When validation runs on a PR, it posts a comment like:

```
## SDLC 6.0.5 Structure Validation Report

| Metric | Value |
|--------|-------|
| **Status** | ✅ PASSED |
| **Score** | 100/100 |
| **Tier** | PROFESSIONAL |
| **Stages** | 10/10 |
| **Errors** | 0 |
| **Warnings** | 0 |
```

## License

Apache-2.0

## Links

- [SDLC 6.0.5 Framework](https://github.com/nqh-org/SDLC-Enterprise-Framework)
- [sdlcctl CLI](https://github.com/nqh-org/sdlcctl)
- [Documentation](https://github.com/nqh-org/sdlcctl/docs)
