# SDLC 5.1.3 MIGRATION GUIDE
## Migrating from SDLC 5.1.3.x to Contract-First Structure

**Version**: 1.0.0
**Last Updated**: December 7, 2025
**Target Audience**: Project Managers, Tech Leads, DevOps Engineers
**Estimated Migration Time**: 15-30 minutes per project

**Framework**: SDLC 5.1.3 Complete Lifecycle (11 Stages + 4-Tier Classification)
**Current Stage**: Stage 04 (BUILD - Development & Implementation)

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Key Changes in SDLC 5.1.3](#key-changes-in-sdlc-500)
3. [Pre-Migration Checklist](#pre-migration-checklist)
4. [Migration Methods](#migration-methods)
5. [Stage Mapping Reference](#stage-mapping-reference)
6. [4-Tier Classification](#4-tier-classification)
7. [Post-Migration Validation](#post-migration-validation)
8. [Troubleshooting](#troubleshooting)
9. [Backward Compatibility](#backward-compatibility)
10. [FAQ](#faq)

---

## OVERVIEW

SDLC 5.1.3 introduces **Contract-First Development** by restructuring stage order. The most significant change is moving **INTEGRATE** from Stage 07 to Stage 03, ensuring API contracts are defined **BEFORE** coding begins.

### Why This Change?

| Problem (SDLC 5.1.3.x) | Solution (SDLC 5.1.3) |
|----------------------|----------------------|
| API design after coding | API design BEFORE coding (Contract-First) |
| Integration at Stage 07 (post-operation) | Integration at Stage 03 (pre-build) |
| Long folder names (e.g., `03-Development-Implementation`) | Short names (e.g., `04-build`) |
| Misaligned with ISO/IEC 12207:2017 | Fully aligned with industry standards |

### Industry Standards Alignment

| Standard | SDLC 5.1.3 Alignment |
|----------|---------------------|
| **ISO/IEC 12207:2017** | Integration in Technical processes (pre-operation) |
| **DevOps 7 C's** | CI/CD within Build/Test phases |
| **CMMI v2.0** | Engineering practices in development |
| **SAFe** | Continuous Delivery Pipeline |

---

## KEY CHANGES IN SDLC 5.1.3

### 1. Stage Restructuring (Contract-First)

```
SDLC 5.1.3.x Order          →    SDLC 5.1.3 Order (Contract-First)
─────────────────────           ─────────────────────────────────
00-Project-Foundation     →    00-foundation       (WHY)
01-Planning-Analysis      →    01-planning         (WHAT)
02-Design-Architecture    →    02-design           (HOW)
03-Development-Impl       →    04-build            [SHIFTED +1]
04-Testing-Quality        →    05-test             [SHIFTED +1]
05-Deployment-Release     →    06-deploy           [SHIFTED +1]
06-Operations-Maint       →    07-operate          [SHIFTED +1]
07-Integration-APIs       →    03-integration      [MOVED to 03] ★
08-Team-Management        →    08-collaborate
09-Executive-Reports      →    09-govern
10-Archive                →    10-archive
```

**Key Insight**: Stage 03 (`integration`) now comes BEFORE Stage 04 (`build`), enforcing the Contract-First principle where OpenAPI specs must exist before coding.

### 2. Simplified Folder Names

| SDLC 5.1.3.x (Long) | SDLC 5.1.3 (Short) |
|-------------------|-------------------|
| `00-Project-Foundation` | `00-foundation` |
| `01-Planning-Analysis` | `01-planning` |
| `02-Design-Architecture` | `02-design` |
| `03-Development-Implementation` | `04-build` |
| `04-Testing-Quality` | `05-test` |
| `05-Deployment-Release` | `06-deploy` |
| `06-Operations-Maintenance` | `07-operate` |
| `07-Integration-APIs` | `03-integration` |
| `08-Team-Management` | `08-collaborate` |
| `09-Executive-Reports` | `09-govern` |
| `10-Archive` | `10-archive` |

### 3. New 4-Tier Classification System

| Tier | Team Size | Required Stages | P0 Artifacts | Compliance |
|------|-----------|-----------------|--------------|------------|
| **LITE** | 1-2 | 00, 01, 02, 03 | No | - |
| **STANDARD** | 3-10 | 00-05 | No | - |
| **PROFESSIONAL** | 10-50 | 00-09 | Yes | - |
| **ENTERPRISE** | 50+ | 00-10 | Yes | ISO27001, SOC2 |

### 4. New Configuration File (.sdlc-config.json)

```json
{
  "$schema": "https://sdlc-orchestrator.io/schemas/config-v1.json",
  "version": "1.0.0",
  "project": {
    "id": "project-uuid",
    "name": "My Project",
    "slug": "my-project"
  },
  "sdlc": {
    "frameworkVersion": "5.0.0",
    "tier": "STANDARD",
    "stages": {
      "00": "docs/00-foundation",
      "01": "docs/01-planning",
      "02": "docs/02-design",
      "03": "docs/03-integration",
      "04": "docs/04-build",
      "05": "docs/05-test",
      "06": "docs/06-deploy",
      "07": "docs/07-operate",
      "08": "docs/08-collaborate",
      "09": "docs/09-govern",
      "10": "docs/10-archive"
    }
  }
}
```

---

## PRE-MIGRATION CHECKLIST

Before migrating, ensure the following:

### Environment Requirements

- [ ] Python 3.11+ installed
- [ ] `sdlcctl` CLI tool installed (v1.0.0+)
- [ ] Sufficient disk space (2x docs folder size for backup)
- [ ] Git repository with clean working directory (no uncommitted changes)

### Project Requirements

- [ ] Valid SDLC 5.1.3.x folder structure exists
- [ ] All team members notified of migration
- [ ] CI/CD pipelines paused (optional but recommended)
- [ ] Backup strategy confirmed

### Install sdlcctl CLI

```bash
# Install from PyPI (recommended)
pip install sdlcctl

# Or install from source
cd backend/sdlcctl
pip install -e .

# Verify installation
sdlcctl --version
# Expected output: sdlcctl v1.0.0 (Framework: SDLC 5.1.3)
```

---

## MIGRATION METHODS

### Method 1: Automated Migration (Recommended)

Use the `sdlcctl migrate` command for automated migration:

```bash
# Step 1: Preview changes (dry run)
sdlcctl migrate /path/to/project --dry-run

# Step 2: Review planned changes
# The command will show:
# - Folders to be renamed
# - Config files to be updated
# - Document references to be updated

# Step 3: Apply migration (with backup)
sdlcctl migrate /path/to/project

# Step 4: Validate migration
sdlcctl validate /path/to/project
```

#### Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dry-run`, `-n` | Preview changes without applying | `false` |
| `--no-backup` | Skip backup creation | `false` (creates backup) |
| `--force`, `-F` | Force migration even if already migrated | `false` |
| `--from`, `-f` | Source SDLC version | `4.9.1` |
| `--to`, `-t` | Target SDLC version | `5.0.0` |

#### Example Output

```
┌──────────────────────────────────────────┐
│ SDLC 5.1.3 Migration Tool                │
│ Contract-First Stage Restructuring       │
└──────────────────────────────────────────┘

Project: /Users/dev/my-project
Detected Version: 4.9.x

Planned Changes (11):

┌────────┬───────────────────────────────────┬───────────────────────────────────┐
│ Type   │ Source                            │ Target                            │
├────────┼───────────────────────────────────┼───────────────────────────────────┤
│ RENAME │ docs/00-Project-Foundation        │ docs/00-foundation                │
│ RENAME │ docs/01-Planning-Analysis         │ docs/01-planning                  │
│ RENAME │ docs/02-Design-Architecture       │ docs/02-design                    │
│ RENAME │ docs/03-Development-Implementation│ docs/04-build                     │
│ RENAME │ docs/04-Testing-Quality           │ docs/05-test                      │
│ RENAME │ docs/05-Deployment-Release        │ docs/06-deploy                    │
│ RENAME │ docs/06-Operations-Maintenance    │ docs/07-operate                   │
│ RENAME │ docs/07-Integration-APIs          │ docs/03-integration               │
│ RENAME │ docs/08-Team-Management           │ docs/08-collaborate               │
│ RENAME │ docs/09-Executive-Reports         │ docs/09-govern                    │
│ UPDATE │ .sdlc-config.json                 │ .sdlc-config.json                 │
└────────┴───────────────────────────────────┴───────────────────────────────────┘

Stage Mapping (Contract-First):
  03-Development-Implementation → 04-build (shifted +1)
  04-Testing-Quality → 05-test (shifted +1)
  05-Deployment-Release → 06-deploy (shifted +1)
  06-Operations-Maintenance → 07-operate (shifted +1)
  07-Integration-APIs → 03-integration (MOVED to Stage 03)

Apply these changes? [y/N]: y

✅ Migration completed successfully!

Backup created at: /Users/dev/my-project/docs_backup_4.9_20251207_143022

Applied Changes: 11/11

Next Steps:
  1. Review migrated folder structure
  2. Run sdlcctl validate to check compliance
  3. Update any custom stage references in your code
```

### Method 2: Manual Migration

If you prefer manual control or need custom migration:

#### Step 1: Create Backup

```bash
# Create timestamped backup
cp -r docs docs_backup_$(date +%Y%m%d_%H%M%S)
```

#### Step 2: Rename Folders

Execute in order to avoid conflicts:

```bash
cd /path/to/project

# Stage 03-07 must be renamed carefully due to number shift
# IMPORTANT: Rename 07 FIRST (before 03-06 to avoid conflict)

# 1. Rename 07-Integration-APIs → 03-integration (temporary name first)
mv docs/07-Integration-APIs docs/03-integration-temp

# 2. Rename 06 → 07
mv docs/06-Operations-Maintenance docs/07-operate

# 3. Rename 05 → 06
mv docs/05-Deployment-Release docs/06-deploy

# 4. Rename 04 → 05
mv docs/04-Testing-Quality docs/05-test

# 5. Rename 03 → 04
mv docs/03-Development-Implementation docs/04-build

# 6. Finalize 03-integration
mv docs/03-integration-temp docs/03-integration

# 7. Rename other stages (no shift, just simplify names)
mv docs/00-Project-Foundation docs/00-foundation
mv docs/01-Planning-Analysis docs/01-planning
mv docs/02-Design-Architecture docs/02-design
mv docs/08-Team-Management docs/08-collaborate
mv docs/09-Executive-Reports docs/09-govern
mv docs/10-Archive docs/10-archive 2>/dev/null || true
```

#### Step 3: Update .sdlc-config.json

```bash
# If .sdlc-config.json exists, update it
# Otherwise, create new one

cat > .sdlc-config.json << 'EOF'
{
  "$schema": "https://sdlc-orchestrator.io/schemas/config-v1.json",
  "version": "1.0.0",
  "sdlc": {
    "frameworkVersion": "5.0.0",
    "tier": "STANDARD",
    "stages": {
      "00": "docs/00-foundation",
      "01": "docs/01-planning",
      "02": "docs/02-design",
      "03": "docs/03-integration",
      "04": "docs/04-build",
      "05": "docs/05-test",
      "06": "docs/06-deploy",
      "07": "docs/07-operate",
      "08": "docs/08-collaborate",
      "09": "docs/09-govern"
    }
  }
}
EOF
```

#### Step 4: Update Document References

```bash
# Find and replace old stage names in all markdown files
find docs -name "*.md" -exec sed -i '' \
  -e 's/00-Project-Foundation/00-foundation/g' \
  -e 's/01-Planning-Analysis/01-planning/g' \
  -e 's/02-Design-Architecture/02-design/g' \
  -e 's/03-Development-Implementation/04-build/g' \
  -e 's/04-Testing-Quality/05-test/g' \
  -e 's/05-Deployment-Release/06-deploy/g' \
  -e 's/06-Operations-Maintenance/07-operate/g' \
  -e 's/07-Integration-APIs/03-integration/g' \
  -e 's/08-Team-Management/08-collaborate/g' \
  -e 's/09-Executive-Reports/09-govern/g' \
  -e 's/SDLC 4\.9\.[0-9]/SDLC 5.1.3/g' \
  {} \;
```

#### Step 5: Validate Migration

```bash
sdlcctl validate /path/to/project
```

### Method 3: VS Code Extension /init Command

For new projects or projects without existing SDLC structure:

1. Open empty folder or existing project in VS Code
2. Press `Cmd+Shift+I` (macOS) or `Ctrl+Shift+I` (Windows/Linux)
3. Select tier (LITE / STANDARD / PROFESSIONAL / ENTERPRISE)
4. Extension generates SDLC 5.1.3 compliant structure
5. Review gap analysis if existing files detected

---

## STAGE MAPPING REFERENCE

### Complete Stage Mapping Table

| Stage ID | SDLC 5.1.3.x Name | SDLC 5.1.3 Name | Question | Type | Change |
|----------|-----------------|-----------------|----------|------|--------|
| 00 | 00-Project-Foundation | 00-foundation | WHY | Linear | Rename only |
| 01 | 01-Planning-Analysis | 01-planning | WHAT | Linear | Rename only |
| 02 | 02-Design-Architecture | 02-design | HOW | Linear | Rename only |
| 03 | 03-Development-Implementation | **04-build** | BUILD | Linear | **Shifted +1** |
| 04 | 04-Testing-Quality | **05-test** | TEST | Linear | **Shifted +1** |
| 05 | 05-Deployment-Release | **06-deploy** | DEPLOY | Linear | **Shifted +1** |
| 06 | 06-Operations-Maintenance | **07-operate** | OPERATE | Linear | **Shifted +1** |
| 07 | 07-Integration-APIs | **03-integration** | INTEGRATE | Linear | **MOVED to 03** |
| 08 | 08-Team-Management | 08-collaborate | COLLABORATE | Continuous | Rename only |
| 09 | 09-Executive-Reports | 09-govern | GOVERN | Continuous | Rename only |
| 10 | 10-Archive | 10-archive | ARCHIVE | Continuous | Rename only |

### Why Stage 03 for Integration?

```
                    SDLC 5.1.3 Contract-First Flow
                    ═══════════════════════════════

    ┌─────────────────────────────────────────────────────────────┐
    │                    LINEAR STAGES                             │
    │                                                              │
    │  00-foundation → 01-planning → 02-design                     │
    │       WHY           WHAT          HOW                        │
    │                                                              │
    │                         ↓                                    │
    │                                                              │
    │              ┌─────────────────────┐                         │
    │              │   03-integration    │ ← API Design FIRST      │
    │              │   (Contract-First)  │   (OpenAPI specs)       │
    │              └─────────────────────┘                         │
    │                         ↓                                    │
    │                                                              │
    │  04-build → 05-test → 06-deploy → 07-operate                │
    │    CODE      TEST      RELEASE     PRODUCTION                │
    │                                                              │
    └─────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │                  CONTINUOUS STAGES                          │
    │                                                              │
    │  08-collaborate    09-govern       10-archive               │
    │     TEAM           COMPLIANCE       HISTORY                 │
    │                                                              │
    └─────────────────────────────────────────────────────────────┘
```

**Benefits of Contract-First:**
1. Frontend and backend can develop in parallel
2. API documentation exists before implementation
3. Clear interface contracts reduce integration bugs
4. Easier to generate client SDKs and test mocks

---

## 4-TIER CLASSIFICATION

### Tier Selection Guide

```
                           TIER SELECTION FLOWCHART
                           ════════════════════════

                                ┌───────────┐
                                │ Team Size │
                                └─────┬─────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                ┌───▼───┐         ┌───▼───┐         ┌───▼───┐
                │  1-2  │         │ 3-50  │         │  50+  │
                └───┬───┘         └───┬───┘         └───┬───┘
                    │                 │                 │
                ┌───▼───┐         ┌───▼───┐         ┌───▼───┐
                │ LITE  │         │3-10?  │         │ENTERP.│
                │4 stg  │         │       │         │11 stg │
                └───────┘         └───┬───┘         └───────┘
                                      │
                              ┌───────┼───────┐
                              │               │
                          ┌───▼───┐       ┌───▼───┐
                          │ STD   │       │ PRO   │
                          │6 stg  │       │10 stg │
                          └───────┘       └───────┘
```

### Folder Structure by Tier

#### LITE Tier (1-2 developers)

```
project/
├── .sdlc-config.json
├── docs/
│   ├── 00-foundation/
│   │   └── problem-statement.md
│   ├── 01-planning/
│   │   └── requirements.md
│   ├── 02-design/
│   │   └── architecture.md
│   └── 03-integration/
│       └── api-spec.md
├── src/
└── tests/
```

#### STANDARD Tier (3-10 developers)

```
project/
├── .sdlc-config.json
├── docs/
│   ├── 00-foundation/
│   ├── 01-planning/
│   ├── 02-design/
│   ├── 03-integration/
│   ├── 04-build/
│   └── 05-test/
├── src/
├── tests/
└── infrastructure/
```

#### PROFESSIONAL Tier (10-50 developers)

```
project/
├── .sdlc-config.json
├── docs/
│   ├── 00-foundation/
│   ├── 01-planning/
│   │   └── P0-requirements.md   ← P0 artifacts required
│   ├── 02-design/
│   │   └── P0-architecture.md   ← P0 artifacts required
│   ├── 03-integration/
│   ├── 04-build/
│   ├── 05-test/
│   ├── 06-deploy/
│   ├── 07-operate/
│   ├── 08-collaborate/
│   └── 09-govern/
├── src/
├── tests/
├── infrastructure/
└── monitoring/
```

#### ENTERPRISE Tier (50+ developers)

```
project/
├── .sdlc-config.json
├── docs/
│   ├── 00-foundation/
│   ├── 01-planning/
│   ├── 02-design/
│   ├── 03-integration/
│   ├── 04-build/
│   ├── 05-test/
│   ├── 06-deploy/
│   ├── 07-operate/
│   ├── 08-collaborate/
│   ├── 09-govern/
│   │   ├── iso27001/           ← Compliance required
│   │   └── soc2/               ← Compliance required
│   └── 10-archive/
├── src/
├── tests/
├── infrastructure/
├── monitoring/
└── compliance/
```

---

## POST-MIGRATION VALIDATION

### Step 1: Run sdlcctl validate

```bash
sdlcctl validate /path/to/project --tier STANDARD

# Expected output:
# ✅ SDLC 5.1.3 Structure Valid
#
# Summary:
#   Framework Version: 5.0.0
#   Project Tier: STANDARD
#   Stages Found: 6/6 required
#   P0 Artifacts: Not required for STANDARD tier
#   Compliance Score: 100%
```

### Step 2: Verify Folder Structure

```bash
# List all stage folders
ls -la docs/

# Expected output:
# drwxr-xr-x  00-foundation
# drwxr-xr-x  01-planning
# drwxr-xr-x  02-design
# drwxr-xr-x  03-integration    ← Verify this exists
# drwxr-xr-x  04-build
# drwxr-xr-x  05-test
# ...
```

### Step 3: Check Document References

```bash
# Search for any remaining old stage names
grep -r "03-Development-Implementation" docs/
grep -r "07-Integration-APIs" docs/
grep -r "SDLC 5.1.3" docs/

# Should return no matches after successful migration
```

### Step 4: Validate .sdlc-config.json

```bash
# Check config file
cat .sdlc-config.json | jq '.sdlc.frameworkVersion'
# Expected: "5.0.0"

cat .sdlc-config.json | jq '.sdlc.stages'
# Expected: Stage 03 should be "docs/03-integration"
```

### Step 5: Update CI/CD Pipelines

If your CI/CD references specific stage folders, update them:

```yaml
# .github/workflows/sdlc-validate.yml
name: SDLC Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install sdlcctl
        run: pip install sdlcctl
      - name: Validate SDLC 5.1.3 structure
        run: sdlcctl validate . --tier STANDARD
```

---

## TROUBLESHOOTING

### Issue 1: "Both old and new folder names exist"

```bash
# Error message:
# ⚠️ Both 03-Development-Implementation and 04-build exist. Skipping rename.

# Solution: Manually merge or remove duplicate
mv docs/03-Development-Implementation/* docs/04-build/
rm -rf docs/03-Development-Implementation
```

### Issue 2: "Permission denied during rename"

```bash
# Error message:
# ❌ Failed to rename docs/03-Development-Implementation: [Errno 13] Permission denied

# Solution: Check file permissions
chmod -R u+w docs/
sdlcctl migrate /path/to/project --force
```

### Issue 3: "Config file parse error"

```bash
# Error message:
# ❌ Failed to update config: JSONDecodeError

# Solution: Validate and fix JSON
python -m json.tool .sdlc-config.json

# If invalid, regenerate:
rm .sdlc-config.json
sdlcctl init . --tier STANDARD
```

### Issue 4: "Git conflicts after migration"

```bash
# If team members have pending PRs with old paths:

# Option A: Rebase PRs after migration
git fetch origin main
git rebase origin/main

# Option B: Use git mv for better tracking
git mv docs/03-Development-Implementation docs/04-build
git commit -m "Migrate to SDLC 5.1.3: Rename stages"
```

### Issue 5: "CI/CD pipeline failures"

```bash
# If CI/CD fails due to missing paths:

# 1. Update workflow files
sed -i 's/03-Development-Implementation/04-build/g' .github/workflows/*.yml

# 2. Update any hardcoded paths in scripts
grep -r "03-Development-Implementation" scripts/ | xargs -I {} sed -i 's/03-Development-Implementation/04-build/g' {}
```

---

## BACKWARD COMPATIBILITY

### Transition Period (3 months)

To support teams migrating at different times, SDLC 5.1.3 tools support a 3-month backward compatibility period:

| Feature | 4.9.x Support | 5.0.0 Native |
|---------|---------------|--------------|
| `sdlcctl validate` | Detects 4.9.x, suggests migration | Full support |
| `sdlcctl fix` | Auto-converts 4.9.x names | Native 5.0.0 |
| VS Code Extension | Works with both | Prefers 5.0.0 |
| GitHub Actions | Accepts both | Prefers 5.0.0 |

### Automatic Detection

```bash
# sdlcctl automatically detects version
sdlcctl validate /path/to/project

# Output for 4.9.x project:
# ⚠️ Detected SDLC 5.1.3.x structure
# 💡 Run 'sdlcctl migrate' to upgrade to 5.0.0
#
# Continuing validation with 4.9.x rules...
```

### Gradual Migration Strategy

For large organizations:

1. **Week 1-2**: Migrate documentation-only projects
2. **Week 3-4**: Migrate active development projects (after sprint completion)
3. **Week 5-8**: Migrate production projects (with extra testing)
4. **Week 9-12**: Deprecate 4.9.x support in CI/CD

---

## FAQ

### Q1: Can I migrate a project that's currently in development?

**A**: Yes, but we recommend:
1. Complete current sprint first
2. Run migration during off-hours
3. Notify all team members
4. Update local clones after push

### Q2: Will my git history be preserved?

**A**: Yes. The migration renames folders, and git tracks renames. Use `git log --follow` to see full history:

```bash
git log --follow docs/04-build/README.md
```

### Q3: Do I need to update all my markdown links?

**A**: The `sdlcctl migrate` command automatically updates internal references. External links (from other repos) need manual updates.

### Q4: What if I'm using custom stage names?

**A**: Custom names are supported via `.sdlc-config.json`:

```json
{
  "sdlc": {
    "stages": {
      "04": "src",           // Custom: Use 'src' instead of 'docs/04-build'
      "05": "tests"          // Custom: Use 'tests' instead of 'docs/05-test'
    }
  }
}
```

### Q5: Is there a rollback option?

**A**: Yes. Migration creates automatic backup:

```bash
# Rollback using backup
rm -rf docs
mv docs_backup_4.9_20251207_143022 docs

# Or use git
git checkout HEAD~1 -- docs/
```

### Q6: How do I migrate multiple projects at once?

**A**: Use a shell script:

```bash
#!/bin/bash
# migrate-all.sh

PROJECTS=(
  "/path/to/project1"
  "/path/to/project2"
  "/path/to/project3"
)

for project in "${PROJECTS[@]}"; do
  echo "Migrating: $project"
  sdlcctl migrate "$project" --force
  echo "---"
done
```

### Q7: What's the difference between P0 artifacts and regular docs?

**A**: P0 (Priority Zero) artifacts are **mandatory entry points** for PROFESSIONAL and ENTERPRISE tiers. They must exist and follow specific naming conventions. View all P0 requirements:

```bash
sdlcctl p0
```

---

## ADDITIONAL RESOURCES

- [SDLC 5.1.3 Framework Overview](../../../docs/00-foundation/README.md)
- [ONBOARDING-FLOW-SPEC.md](../../05-test/07-E2E-Testing/ONBOARDING-FLOW-SPEC.md)
- [VS Code Extension Setup](./DEV-ENVIRONMENT-SETUP.md)
- [sdlcctl CLI Reference](../../../backend/sdlcctl/README.md)

---

## SUPPORT

If you encounter issues during migration:

1. **Check sdlcctl logs**: `sdlcctl migrate --verbose`
2. **Review this guide**: Search for error message
3. **Open GitHub Issue**: [SDLC-Orchestrator Issues](https://github.com/nqh/sdlc-orchestrator/issues)

---

**Document Status**: ✅ COMPLETE
**Framework**: SDLC 5.1.3 Contract-First Lifecycle
**Last Updated**: December 7, 2025

*Migration guide for SDLC 5.1.3.x → 5.0.0. Contract-First development. Industry-standard alignment.*
