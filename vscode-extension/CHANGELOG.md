# Changelog

All notable changes to the SDLC Orchestrator VS Code Extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-26

### Added - Sprint 53: VS Code Extension + Contract Lock

#### Day 1: Extension Foundation (~4,500 lines)
- **Types**: Complete TypeScript type definitions for codegen API
  - `AppBlueprint`, `BlueprintModule`, `BlueprintMetadata`
  - `GeneratedFile`, `QualityGateResult`, `CodegenSession`
  - `ContractLockStatus`, `ContractLockResponse`, `UnlockReason`
  - SSE event types: `SSEStartedEvent`, `SSEFileGeneratedEvent`, etc.
- **Services**: CodegenApiService for backend communication
  - Session management (create, get, update, list)
  - Code generation (start, stream, resume, cancel)
  - Contract lock (lock, unlock, status, verify-hash)
  - Blueprint validation and domain templates
- **Commands**: Lock/unlock command registration
  - `sdlc.lock` - Lock contract specification
  - `sdlc.unlock` - Unlock contract specification
  - `sdlc.lockStatus` - View lock status
  - `sdlc.verifyHash` - Verify specification hash

#### Day 2: App Builder Panel (~2,600 lines)
- **Blueprint Editor**: Visual webview panel for building specifications
  - Tree view with modules and entities
  - Add/remove module with entity definitions
  - Edit blueprint metadata (name, version, description)
  - Domain selection (restaurant, hotel, retail, hrm, crm)
- **Blueprint Tree View**: Sidebar tree data provider
  - Hierarchical view of blueprint structure
  - Context menu actions for modules and entities
  - Real-time updates on blueprint changes
- **Panel Integration**: Webview lifecycle management
  - State persistence across panel close/reopen
  - Message passing between extension and webview
  - Error handling with user-friendly messages

#### Day 3: Streaming Integration (~2,200 lines)
- **Generation Panel**: Real-time code generation view
  - SSE event stream parsing and display
  - File-by-file generation progress
  - Quality gate status visualization
  - Error display with recovery options
- **SSE Client**: Server-Sent Events handling
  - Reconnection with exponential backoff
  - Event type discrimination
  - Checkpoint tracking for resume
- **Resume Capability**: Checkpoint-based recovery
  - Session resume banner
  - Last checkpoint display
  - One-click resume action

#### Day 4: Contract Lock Backend (~1,800 lines)
- **Schemas**: Pydantic models for Contract Lock API
  - `SpecLockRequest`, `SpecUnlockRequest`, `HashVerifyRequest`
  - `SpecLockResponse`, `SpecUnlockResponse`, `HashVerifyResponse`
  - `LockAuditLogEntry`, `LockAuditLogResponse`
  - `UnlockReason` enum (modification_needed, generation_failed, admin_override, session_expired)
- **Service**: ContractLockService with business logic
  - Lock with SHA256 hash calculation
  - Unlock with permission validation (owner or admin)
  - Hash verification for integrity checking
  - Audit log for compliance
  - Auto-unlock for expired locks (1 hour timeout)
- **API Routes**: FastAPI endpoints
  - `POST /api/v1/onboarding/{session_id}/lock`
  - `POST /api/v1/onboarding/{session_id}/unlock`
  - `GET /api/v1/onboarding/{session_id}/lock-status`
  - `POST /api/v1/onboarding/{session_id}/verify-hash`
  - `GET /api/v1/onboarding/{session_id}/lock-audit`
  - `POST /api/v1/onboarding/{session_id}/force-unlock` (admin)
- **Migration**: Database schema changes
  - Added columns to `onboarding_sessions`: locked, spec_hash, locked_at, locked_by, lock_expires_at, lock_version
  - Created `lock_audit_log` table with indexes

#### Day 5: Testing + Publish (~500 lines)
- **Unit Tests**: Type and API tests
  - `codegenApi.test.ts` - Blueprint and lock type tests
  - `streaming.test.ts` - SSE event parsing tests
- **README**: Updated for v1.0.0 with new features
- **CHANGELOG**: Complete Sprint 53 documentation

### Changed
- Updated `package.json` version to 1.0.0
- Updated README with new commands and features
- Enhanced error handling with UnlockReason enum

### Technical Details
- Total lines added: ~11,600
- TypeScript compilation: Clean (0 errors)
- Test coverage: ~200 test cases
- API endpoints: 6 new Contract Lock routes
- Database tables: 1 new table, 6 new columns

---

## [0.2.0] - 2025-12-20

### Added - Sprint 51B: QR Preview
- QR code generation for mobile preview
- Preview modal with copy/share functionality

---

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
