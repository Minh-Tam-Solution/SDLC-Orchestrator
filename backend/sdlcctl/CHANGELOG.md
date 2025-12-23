# Changelog

All notable changes to sdlcctl will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2025-12-23

### Added

**Sprint 44: SDLC Structure Scanner Engine**

#### New Validators (5 total, 15 rules)

- **StageFolderValidator** (5 rules)
  - `STAGE-001`: Invalid stage folder naming (ERROR, auto-fix)
  - `STAGE-002`: Unknown stage number (ERROR)
  - `STAGE-003`: Stage name mismatch (WARNING, auto-fix)
  - `STAGE-004`: Duplicate stage numbers (ERROR)
  - `STAGE-005`: Missing required core stages (ERROR, auto-fix)

- **SequentialNumberingValidator** (3 rules)
  - `NUM-001`: Duplicate numbering within stage (ERROR)
  - `NUM-002`: Sequence gaps (INFO, auto-fix)
  - `NUM-003`: Invalid numbering format (WARNING, auto-fix)

- **NamingConventionValidator** (2 rules)
  - `NAME-001`: Invalid characters in names (WARNING, auto-fix)
  - `NAME-002`: Inconsistent casing (INFO)

- **HeaderMetadataValidator** (2 rules)
  - `HDR-001`: Missing required header fields (WARNING)
  - `HDR-002`: Invalid header field format (INFO)

- **CrossReferenceValidator** (3 rules)
  - `REF-001`: Broken internal links (ERROR)
  - `REF-002`: Orphaned files (WARNING)
  - `SCANNER-001`: Structure health metrics (INFO/WARNING)

#### Configuration System

- `.sdlc-config.json` support with hierarchical search
- Per-rule enable/disable, severity override, auto_fix toggle
- Ignore patterns for node_modules, .git, __pycache__, etc.
- Parallel validation with configurable max_workers

#### CLI Enhancements

- `sdlcctl validate --tier` now enforces required stages
- `sdlcctl validate --format json/summary/github` output formats
- `sdlcctl fix` conservative auto-fix for safe operations:
  - Create missing required stage folders
  - Rename invalid stage folders (STAGE-001, STAGE-003)
  - Fix invalid numbering prefixes (NUM-003)

#### Documentation

- Comprehensive `.sdlc-config.json` examples in README
- Configuration options reference table
- Per-rule configuration examples

### Fixed

- Typer/Click 8.2+ incompatibility (pin `click<8.2`)
- False positives for README.md in naming/header validators
- `--strict` flag logic to fail on warnings/errors correctly

### Changed

- Validators now skip README.md and index.md files
- Health metrics use tiered severity (HEALTHY/NEEDS ATTENTION/UNHEALTHY)

---

## [1.0.0] - 2025-11-15

### Added

- Initial release of sdlcctl CLI
- `sdlcctl validate` - Validate SDLC 5.0.0 structure
- `sdlcctl init` - Initialize new project structure
- `sdlcctl fix` - Fix missing stages and P0 artifacts
- `sdlcctl report` - Generate compliance reports
- `sdlcctl tiers` - Display tier classification
- `sdlcctl stages` - Display stage definitions
- `sdlcctl p0` - Display P0 artifact requirements
- 4-tier classification (LITE, STANDARD, PROFESSIONAL, ENTERPRISE)
- Pre-commit hook integration
- CI/CD integration examples (GitHub Actions, GitLab CI)

---

## Links

- [Repository](https://github.com/Minh-Tam-Solution/SDLC-Orchestrator)
- [Documentation](./README.md)
- [SDLC 5.0.0 Framework](https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework)
