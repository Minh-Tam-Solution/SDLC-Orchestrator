# Changelog

All notable changes to the SDLC Orchestrator VS Code Extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-12-04

### Added

#### Core Services
- **AuthService**: JWT token management with secure storage
- **ApiClient**: Axios-based HTTP client with authentication
- **CacheService**: Stale-while-revalidate caching with offline support
- **ConfigManager**: Centralized settings management
- **Logger**: Debug logging with configurable levels

#### Tree View Providers
- **Gate Status View**: Real-time gate status (G0-G5) with status icons
- **Violations View**: Grouped violations by severity with quick actions
- **Projects View**: Project list with quick switching

#### Chat Participant (@gate)
- `/status` command: Show current gate status
- `/evaluate` command: Run compliance evaluation
- `/fix <id>` command: Get AI fix recommendation
- `/council <id>` command: AI Council decision

#### Error Handling
- Comprehensive error classification (network, auth, API, client)
- User-friendly error messages with suggested actions
- Retry logic with exponential backoff

#### Offline Mode
- Cache-first data fetching strategy
- Graceful degradation when backend unavailable
- Visual indicators for cached data

### Technical Details
- TypeScript strict mode enabled
- ESLint with @typescript-eslint rules
- Mocha test framework with TDD UI
- VS Code 1.80.0+ compatibility

---

## [Unreleased]

### Planned for v0.2.0
- Evidence Submit panel
- Template Generator
- WebSocket real-time updates
- Webpack bundling for smaller package size
