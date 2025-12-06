# SDLC Orchestrator VS Code Extension

**Version**: 0.1.0
**Status**: MVP (Sprint 27)
**SDLC Stage**: 03 (BUILD)

Monitor gate status, get compliance assistance, and use AI-powered recommendations directly in VS Code. Part of the SDLC Orchestrator governance platform built on SDLC 4.9.1 Complete Lifecycle methodology.

## Features

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

### Error Handling
- User-friendly error messages (no technical jargon)
- Suggested actions based on error type
- Clickable error items (login for auth errors, retry for network errors)
- Rich tooltips with error details

## Installation

### From VSIX (Development)
1. Download the latest `.vsix` file from releases
2. In VS Code, open Command Palette (Cmd+Shift+P / Ctrl+Shift+P)
3. Run "Extensions: Install from VSIX..."
4. Select the downloaded file

### From Marketplace (Coming Soon)
Search for "SDLC Orchestrator" in VS Code Extensions

## Quick Start

1. **Install** the extension
2. **Login** using Command Palette > "SDLC: Login"
3. **Select Project** using Command Palette > "SDLC: Select Project"
4. **View Gates** in the SDLC sidebar
5. **Use AI Chat** by typing `@gate /status` in VS Code Chat

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `sdlc.apiUrl` | `http://localhost:8000` | Backend API URL |
| `sdlc.autoRefreshInterval` | `30` | Auto-refresh interval (seconds) |
| `sdlc.defaultProjectId` | `` | Default project to load on startup |
| `sdlc.enableNotifications` | `true` | Show gate status notifications |
| `sdlc.aiCouncilEnabled` | `true` | Enable AI Council for critical violations |

## Commands

| Command | Keybinding | Description |
|---------|------------|-------------|
| SDLC: Refresh Gate Status | Cmd+Shift+G | Refresh all views |
| SDLC: Select Project | - | Choose project to monitor |
| SDLC: Login | - | Login to SDLC Orchestrator |
| SDLC: Logout | - | Logout and clear tokens |

## Requirements

- VS Code 1.80.0 or higher
- SDLC Orchestrator backend running (v1.0.0+)
- Valid API token or GitHub OAuth

## Authentication

### API Token
1. Run "SDLC: Login" command (Cmd+Shift+P > "SDLC: Login")
2. Select "API Token"
3. Paste your token from SDLC Orchestrator dashboard (Settings > API Tokens)

### GitHub OAuth
1. Run "SDLC: Login" command
2. Select "GitHub OAuth"
3. Follow the browser flow to authorize
4. Extension will automatically receive the token

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
# Creates sdlc-orchestrator-0.1.0.vsix
```

### Run Tests
```bash
npm run test
```

### Debug in VS Code
1. Open `vscode-extension` folder in VS Code
2. Press F5 to launch Extension Development Host
3. The extension will be loaded in a new VS Code window

## Architecture

```
src/
├── extension.ts           # Main entry point, activation
├── services/
│   ├── apiClient.ts       # Backend API client (axios-based)
│   ├── authService.ts     # JWT token management, OAuth flow
│   └── cacheService.ts    # Offline cache with TTL
├── views/
│   ├── gateStatusView.ts  # Gate sidebar TreeDataProvider
│   ├── violationsView.ts  # Violations TreeDataProvider
│   ├── projectsView.ts    # Projects TreeDataProvider
│   └── complianceChat.ts  # Chat participant (@gate)
├── utils/
│   ├── config.ts          # Configuration manager
│   ├── logger.ts          # Structured logging
│   └── errors.ts          # Error classification & handling
└── test/
    └── suite/
        ├── apiClient.test.ts
        ├── authService.test.ts
        ├── cacheService.test.ts
        ├── complianceChat.test.ts
        ├── gateStatusView.test.ts
        ├── violationsView.test.ts
        ├── projectsView.test.ts
        ├── offlineMode.test.ts
        └── errorHandling.test.ts
```

## Cache Strategy

The extension uses a sophisticated caching strategy for offline support:

| Data Type | TTL | Description |
|-----------|-----|-------------|
| Projects | 10 min | List of all projects |
| Gates | 2 min | Gate status (frequently updated) |
| Violations | 2 min | Compliance violations |
| User | 30 min | User profile data |

- **Stale-while-revalidate**: Returns cached data immediately, refreshes in background
- **Offline fallback**: Uses cached data when network unavailable
- **Visual indicators**: Shows "Offline mode" when using cached data

## Error Codes

| Range | Category | Examples |
|-------|----------|----------|
| 1xx | Network | Connection refused, timeout |
| 2xx | Auth | Unauthorized, token expired |
| 3xx | API | Not found, rate limited, server error |
| 4xx | Client | No project selected |

## Changelog

### 0.1.0 (Sprint 27 - December 2025)
- Initial MVP release
- Gate Status sidebar with progress visualization
- Inline AI Chat with @gate commands (/status, /evaluate, /fix, /council)
- Violations panel with severity grouping
- Projects panel with quick selection
- API Token and GitHub OAuth authentication
- Offline mode support with cache fallback
- User-friendly error handling
- Comprehensive test suite (~200 tests)

## Performance

| Metric | Target | Achieved |
|--------|--------|----------|
| Extension activation | <3s | ~1.5s |
| Cache read (memory) | <1ms | ~0.1ms |
| Cache read (persisted) | <5ms | ~2ms |
| API request (cached) | <10ms | ~5ms |

## Troubleshooting

### Connection Refused
- Ensure SDLC Orchestrator backend is running
- Check `sdlc.apiUrl` configuration
- Verify firewall/proxy settings

### Token Expired
- Run "SDLC: Logout" then "SDLC: Login"
- Check token expiration in dashboard

### No Data Showing
- Select a project first: "SDLC: Select Project"
- Check if you have access to the project
- Try "SDLC: Refresh Gate Status"

### Offline Mode
- Extension shows "Offline mode (cached data)" indicator
- Click refresh when back online
- Data may be outdated until refreshed

## License

Apache-2.0

## Support

- GitHub Issues: https://github.com/nqh-team/sdlc-orchestrator/issues
- Documentation: https://docs.sdlc-orchestrator.dev
- Discord: https://discord.gg/sdlc-orchestrator
