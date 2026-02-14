# SDLC Orchestrator VS Code Extension

**Version**: 1.5.0
**Status**: GA (General Availability)
**Framework**: SDLC 6.0.5 (E2E API Testing + Stage Cross-Reference)
**Sprint**: 139 - E2E Commands Implementation
**Last Updated**: February 2, 2026

Gate status monitoring, AI-powered code generation, and compliance assistance directly in VS Code. Part of the SDLC Orchestrator governance platform - the **Operating System for Software 3.0**.

## What's New in 1.5.0 (Sprint 139)

### E2E Testing Commands (RFC-SDLC-602)
- **E2E Validate** (`Cmd+Shift+E`): Validate E2E testing compliance with CLI integration
- **E2E Cross-Reference**: Validate Stage 03 ↔ Stage 05 bidirectional links
- **E2E Initialize**: Create E2E testing folder structure in Stage 05
- **E2E Validate with Options**: Advanced validation with custom pass rate threshold
- **Show E2E Results**: View detailed validation results in tree view

### New Backend API Endpoints
- `POST /api/v1/cross-reference/validate`: Full cross-reference validation
- `GET /api/v1/cross-reference/coverage/{id}`: Quick coverage check
- `GET /api/v1/cross-reference/missing-tests/{id}`: Get missing test endpoints
- `GET /api/v1/cross-reference/ssot-check/{id}`: SSOT compliance check

### SSOT Enforcement
- Validates `openapi.json` exists only in Stage 03
- Detects duplicate OpenAPI files in Stage 05 or other folders
- Reports violations with actionable fix suggestions

### CLI Integration (Zero Mock Policy)
- Real `sdlcctl e2e validate` execution via Extension
- Falls back to local validation when CLI unavailable
- JSON output parsing for structured results

## What's New in 1.4.0 (Sprint 138)

### SDLC 6.0.5 Framework Support
- **Framework 6.0.5**: RFC-SDLC-602 E2E API Testing Enhancement
- **E2E API Testing Workflow**: 6-phase standardized testing process awareness
- **Stage Cross-Reference**: Stage 03 ↔ Stage 05 bidirectional traceability
- **OWASP API Top 10**: Security checklist integration ready
- **Version Sync**: Synchronized with `sdlcctl` CLI v1.4.0

### New Features
- **E2E Testing Commands**: Extension recognizes `sdlcctl e2e validate` and `sdlcctl e2e cross-reference`
- **Cross-Reference Validation**: Validates Stage 03 (API) ↔ Stage 05 (Testing) links
- **SSOT Enforcement**: Single Source of Truth for openapi.json in Stage 03
- **4 New Evidence Types**: e2e_test_report, security_test_report, api_coverage_report, cross_reference_validation

### Quick Start Guide Integration
- See: `SDLC-Enterprise-Framework/07-Implementation-Guides/E2E-TESTING-QUICKSTART.md`
- Time savings: 3 hours → 30 minutes E2E setup

## What's New in 1.3.0 (Sprint 136)

### SDLC 6.0.5 Framework Support
- **Framework 6.0.5**: Updated from 6.0.5 to latest version
- **SPEC-0021**: Stage Consistency Validation support
- **Version Sync**: Synchronized with `sdlcctl` CLI v1.3.0

### New CLI Command: validate-consistency
- Extension now recognizes the new `sdlcctl validate-consistency` command
- Validates cross-stage consistency between:
  - Stage 01 (Planning) ↔ Stage 02 (Design)
  - Stage 02 (Design) ↔ Stage 03 (Integrate)
  - Stage 03 (Integrate) ↔ Stage 04 (Build)
  - Stage 01 (Planning) ↔ Stage 04 (Build)

## What's New in 1.2.0 (Sprint 127)

### Multi-Frontend Alignment
- **SDLC 6.0.5 Framework**: Full alignment with latest framework version
- **Specification Validation**: YAML frontmatter validation (SPEC-0002 compliant)
- **BDD Requirements**: GIVEN-WHEN-THEN validation support
- **Tier-Specific Sections**: LITE/STANDARD/PROFESSIONAL/ENTERPRISE validation
- **Extension Parity**: 67% → 89% feature parity (+22 points)

See [CHANGELOG](CHANGELOG.md) for complete details.

## Key Features

### App Builder (New in 1.1.1)
- **Blueprint Editor**: Visual tree view for building AppBlueprint specifications
- **Module Management**: Add/remove modules with entity definitions
- **Domain Templates**: Pre-built templates for Vietnamese SME (Restaurant, Hotel, Retail, HRM, CRM)
- **Real-time Validation**: Immediate feedback on blueprint structure

### Code Generation (New in 1.1.1)
- **IR-Based Generation**: Deterministic output via Intermediate Representation
- **Multi-Provider**: Ollama (primary) -> Claude (fallback) -> Rule-based
- **4-Gate Quality Pipeline**: Syntax -> Security -> Context -> Tests
- **SSE Streaming**: Real-time progress with file-by-file updates
- **Resume Capability**: Checkpoint-based recovery for failed generations

### Contract Lock (New in 1.1.1)
- **Specification Immutability**: Lock blueprints before code generation
- **SHA256 Hash Verification**: Cryptographic integrity checking
- **Audit Trail**: Full history of lock/unlock operations
- **Auto-Expiry**: Orphaned locks expire after 1 hour

### Gate Status Sidebar
- View G0-G5 gate progress in real-time
- See evidence count and approval status
- Auto-refresh every 30 seconds
- Click to open gates in browser
- Progress percentage visualization

### Inline AI Chat (@gate)
Use Copilot-style commands in VS Code Chat:

```
@gate /status      - Show current gate status (G0-G5)
@gate /evaluate    - Run compliance evaluation, show violations
@gate /fix <id>    - Get AI recommendation for a violation
@gate /council <id> - Use AI Council 3-stage deliberation
```

### Violations Panel
- View compliance violations grouped by severity (Critical, High, Medium, Low)
- Quick actions to get AI recommendations
- Navigate to file locations
- Filter by status (open, resolved)

### Projects Panel
- List all projects you have access to
- Quick project selection
- View compliance scores
- See current gate status

### Offline Mode Support
- Automatic cache fallback when network unavailable
- Stale-while-revalidate pattern for smooth UX
- Visual indicator when using cached data
- Graceful degradation with user-friendly messages

## Installation

### From VS Code Marketplace
1. Open VS Code Extensions (Ctrl+Shift+X)
2. Search for "SDLC Orchestrator"
3. Click Install

### From VSIX (Development)
1. Download the latest `.vsix` file from releases
2. In VS Code, open Command Palette (Cmd+Shift+P / Ctrl+Shift+P)
3. Run "Extensions: Install from VSIX..."
4. Select the downloaded file

## Quick Start

1. **Install** the extension
2. **Create API Key** (Recommended):
   - Go to SDLC Orchestrator Dashboard → Settings → API Keys
   - Click "Create New API Key"
   - Copy the key (starts with `sdlc_live_`)
3. **Login** using Command Palette > "SDLC: Login"
   - Select "API Token" (Recommended - Never expires)
   - Paste your API key
4. **Select Project** using Command Palette > "SDLC: Select Project"
5. **View Gates** in the SDLC sidebar

**Why API Key?** Unlike email/password (JWT expires after 8 hours), API keys never expire until you revoke them - perfect for development tools!
5. **Generate Code**:
   - Open App Builder: "SDLC: Open App Builder"
   - Create a blueprint with modules and entities
   - Lock the specification: "SDLC: Lock Contract Spec"
   - Generate code: "SDLC: Generate from Blueprint"

## Commands

| Command | Keybinding | Description |
|---------|------------|-------------|
| SDLC: Refresh Gate Status | Cmd+Shift+R | Refresh all views |
| SDLC: Select Project | - | Choose project to monitor |
| SDLC: Login | - | Login to SDLC Orchestrator |
| SDLC: Logout | - | Logout and clear tokens |
| SDLC: Open App Builder | Cmd+Shift+B | Open blueprint editor |
| SDLC: Generate from Blueprint | Cmd+Shift+G | Start code generation |
| SDLC: Magic Mode | Cmd+Shift+M | Natural language to code |
| SDLC: Lock Contract Spec | Cmd+Shift+L | Lock blueprint for generation |
| SDLC: Unlock Contract Spec | - | Unlock blueprint for editing |
| SDLC: Preview Generated Code | Cmd+Shift+P | Preview with QR code |
| SDLC: Resume Failed Generation | - | Resume from checkpoint |
| **E2E: Validate Testing Compliance** | Cmd+Shift+E | Validate E2E testing with CLI |
| **E2E: Validate Cross-References** | - | Validate Stage 03 ↔ 05 links |
| **E2E: Initialize Testing Structure** | - | Create E2E folder structure |
| **E2E: Validate with Options** | - | Advanced validation with options |
| **E2E: Show Validation Results** | - | View detailed E2E results |

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `sdlc.apiUrl` | `https://sdlc.nhatquangholding.com` | Backend API URL |
| `sdlc.autoRefreshInterval` | `30` | Auto-refresh interval (seconds) |
| `sdlc.defaultProjectId` | `` | (Optional) Manual project UUID - auto-detected from workspace if not set |
| `sdlc.enableNotifications` | `true` | Show gate status notifications |
| `sdlc.aiCouncilEnabled` | `true` | Enable AI Council for critical violations |
| `sdlc.showViolationBadge` | `true` | Show violation count in activity bar |
| `sdlc.showProjectsPanel` | `false` | Always show Projects panel (auto-hidden when project detected) |

## Requirements

- VS Code 1.80.0 or higher
- SDLC Orchestrator backend running (v1.1.1+)
- Valid API token or GitHub OAuth

## Architecture

```
src/
├── extension.ts           # Main entry point, activation
├── services/
│   ├── apiClient.ts       # Backend API client (axios-based)
│   ├── authService.ts     # JWT token management, OAuth flow
│   ├── cacheService.ts    # Offline cache with TTL
│   └── codegenApi.ts      # Code generation API client
├── panels/
│   ├── appBuilderPanel.ts # Blueprint editor webview
│   └── generationPanel.ts # Real-time generation view
├── views/
│   ├── gateStatusView.ts  # Gate sidebar TreeDataProvider
│   ├── violationsView.ts  # Violations TreeDataProvider
│   ├── projectsView.ts    # Projects TreeDataProvider
│   ├── complianceChat.ts  # Chat participant (@gate)
│   └── blueprintView.ts   # Blueprint tree view
├── commands/
│   ├── lockCommand.ts     # Contract lock/unlock commands
│   ├── generateCommand.ts # Code generation commands
│   ├── magicCommand.ts    # Natural language mode
│   ├── e2eValidateCommand.ts   # E2E validation (Sprint 139)
│   └── e2eCrossRefCommand.ts   # Cross-reference validation
├── utils/
│   ├── config.ts          # Configuration manager
│   ├── logger.ts          # Structured logging
│   └── errors.ts          # Error classification & handling
├── types/
│   ├── codegen.ts         # Type definitions for codegen
│   └── evidence.ts        # E2E evidence types (RFC-SDLC-602)
└── test/
    └── suite/
        ├── apiClient.test.ts
        ├── authService.test.ts
        ├── cacheService.test.ts
        ├── codegenApi.test.ts
        ├── streaming.test.ts
        └── errorHandling.test.ts
```

## Development

### Prerequisites
- Node.js 18+
- npm 9+
- VS Code 1.80+

### Setup
```bash
cd vscode-extension
npm install
npm run compile
```

### Watch Mode
```bash
npm run watch
```

### Package Extension
```bash
npm run package
# Creates sdlc-orchestrator-1.1.1.vsix
```

### Run Tests
```bash
npm run test
```

### Debug in VS Code
1. Open `vscode-extension` folder in VS Code
2. Press F5 to launch Extension Development Host
3. The extension will be loaded in a new VS Code window

## Cache Strategy

| Data Type | TTL | Description |
|-----------|-----|-------------|
| Projects | 10 min | List of all projects |
| Gates | 2 min | Gate status (frequently updated) |
| Violations | 2 min | Compliance violations |
| Sessions | 5 min | Onboarding sessions |
| Blueprints | 10 min | App blueprints |

## Troubleshooting

### Connection Refused
- Ensure SDLC Orchestrator backend is running
- Check `sdlc.apiUrl` configuration
- Verify firewall/proxy settings

### Token Expired
- Run "SDLC: Logout" then "SDLC: Login"
- Check token expiration in dashboard

### Generation Failed
- Check if blueprint is locked: "SDLC: Lock Contract Spec"
- Verify backend AI providers are available
- Try "SDLC: Resume Failed Generation" if checkpoint exists

### Lock Expired
- Locks auto-expire after 1 hour of inactivity
- Re-lock the specification before generation

## License

Apache-2.0

## Support

- GitHub Issues: https://github.com/Minh-Tam-Solution/SDLC-Orchestrator/issues
- Documentation: https://docs.sdlc-orchestrator.dev
