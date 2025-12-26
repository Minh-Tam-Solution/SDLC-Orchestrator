# VS Code Extension Technical Specification

**Sprint**: 53
**Version**: 1.0.0
**Date**: December 25, 2025
**Status**: DRAFT - Pending CTO Approval
**Authority**: Backend Team + Frontend Team
**Priority**: P0 - Developer Experience

---

## 1. Executive Summary

### 1.1 Purpose

The SDLC Orchestrator VS Code Extension provides developers with:
- **App Builder Integration**: Generate code from natural language or blueprints directly in VS Code
- **Real-time Streaming**: See generated files appear in real-time via SSE
- **Contract Lock**: Prevent spec modifications during active generation
- **4-Gate Quality Pipeline**: Inline validation and diagnostics

### 1.2 Design Philosophy

> Extension hoạt động giống Claude Code - hiểu context từ file đang mở,
> link tới files trong project, attach/upload nội dung. File mới tạo mở ngay trong VS Code để review.

### 1.3 Key Metrics

| Metric | Target |
|--------|--------|
| Extension activation time | <1s |
| Generation streaming lag | <200ms |
| Contract lock accuracy | 100% hash match |
| Marketplace rating target | 4.5+ stars |

---

## 2. Architecture

### 2.1 Extension Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ VS Code Extension: sdlc-orchestrator v0.2.0                     │
├─────────────────────────────────────────────────────────────────┤
│ UI Components:                                                  │
│ ├── Sidebar Views (existing)                                    │
│ │   ├── sdlc-gate-status (Gate Status monitoring)               │
│ │   ├── sdlc-violations (Compliance Violations)                 │
│ │   ├── sdlc-projects (Project list)                            │
│ │   └── sdlc-app-builder (NEW - Blueprint tree view)            │
│ ├── Webview Panels (NEW)                                        │
│ │   ├── AppBuilderPanel (Blueprint editor + actions)            │
│ │   └── GenerationPanel (Real-time streaming view)              │
│ ├── Chat Participant (existing)                                 │
│ │   └── @gate commands (status, evaluate, fix, council)         │
│ └── Status Bar Items (NEW)                                      │
│     ├── Generation status indicator                             │
│     └── Lock status indicator                                   │
├─────────────────────────────────────────────────────────────────┤
│ Commands (NEW):                                                 │
│ ├── sdlc.generate (Cmd+Shift+G) - Generate from blueprint       │
│ ├── sdlc.magic (Cmd+Shift+M) - Magic mode natural language      │
│ ├── sdlc.lock (Cmd+Shift+L) - Lock contract spec                │
│ ├── sdlc.unlock - Unlock contract spec                          │
│ ├── sdlc.preview (Cmd+Shift+P) - Preview generated code         │
│ ├── sdlc.resume (Cmd+Shift+R) - Resume failed generation        │
│ └── sdlc.openAppBuilder - Open App Builder panel                │
├─────────────────────────────────────────────────────────────────┤
│ Services:                                                       │
│ ├── ApiClient (existing) - REST API calls                       │
│ ├── AuthService (existing) - JWT token management               │
│ ├── CacheService (existing) - Response caching                  │
│ ├── CodegenApiService (NEW) - Codegen-specific API calls        │
│ ├── SSEClientService (NEW) - Server-Sent Events consumer        │
│ └── ContractLockService (NEW) - Lock/unlock operations          │
├─────────────────────────────────────────────────────────────────┤
│ API Integration:                                                │
│ ├── POST /codegen/generate/stream (SSE for streaming)           │
│ ├── POST /codegen/generate/resume/{session_id}                  │
│ ├── POST /onboarding/{id}/lock                                  │
│ ├── POST /onboarding/{id}/unlock                                │
│ └── GET  /onboarding/{id}/status                                │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │───►│   Extension     │───►│   Backend API   │
│                 │    │                 │    │                 │
│ "Nhà hàng Phở"  │    │ 1. Parse input  │    │ 1. NLP Parser   │
│ or blueprint.json    │ 2. Lock spec    │    │ 2. Blueprint gen │
│                 │    │ 3. Call API     │    │ 3. Codegen      │
└─────────────────┘    └─────────────────┘    └────────┬────────┘
                                                       │
                                                       │ SSE Stream
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Created  │◄───│  Extension      │◄───│  SSE Events     │
│                 │    │                 │    │                 │
│ - Open in tab   │    │ 1. Parse event  │    │ - started       │
│ - Show diff     │    │ 2. Create file  │    │ - file_generated│
│ - Accept/Reject │    │ 3. Update UI    │    │ - completed     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 3. Features Specification

### 3.1 App Builder Panel

**Purpose**: Visual interface to create/edit blueprints and trigger generation

**UI Components**:

```typescript
interface AppBuilderPanelState {
  blueprint: AppBlueprint | null;
  locked: boolean;
  lockedAt: string | null;
  specHash: string | null;
  generationStatus: 'idle' | 'generating' | 'completed' | 'failed';
  generatedFiles: GeneratedFile[];
}

interface AppBlueprint {
  name: string;
  version: string;
  business_domain: string;
  description: string;
  modules: Module[];
  metadata: {
    generated_by: string;
    language: string;
    source_description: string;
  };
}

interface GeneratedFile {
  path: string;
  content: string;
  lines: number;
  status: 'generating' | 'valid' | 'error';
  syntaxValid: boolean;
}
```

**Webview HTML Structure**:

```html
<div class="app-builder-panel">
  <!-- Header with lock status -->
  <header class="panel-header">
    <h2>App Builder</h2>
    <div class="lock-status">
      <span class="lock-icon" data-locked="{{locked}}"></span>
      <span class="lock-text">{{lockStatus}}</span>
    </div>
  </header>

  <!-- Blueprint Editor -->
  <section class="blueprint-editor">
    <div class="field">
      <label>App Name</label>
      <input type="text" id="appName" value="{{blueprint.name}}" />
    </div>
    <div class="field">
      <label>Domain</label>
      <select id="domain">
        <option value="restaurant">Restaurant (Nhà hàng)</option>
        <option value="ecommerce">E-commerce (Thương mại điện tử)</option>
        <option value="hrm">HRM (Quản lý nhân sự)</option>
        <option value="crm">CRM (Quản lý khách hàng)</option>
        <option value="inventory">Inventory (Quản lý kho)</option>
        <option value="education">Education (Giáo dục)</option>
        <option value="healthcare">Healthcare (Y tế)</option>
      </select>
    </div>
    <div class="field">
      <label>Description (Vietnamese supported)</label>
      <textarea id="description">{{blueprint.description}}</textarea>
    </div>
  </section>

  <!-- Actions -->
  <section class="actions">
    <button id="lockBtn" class="btn-secondary">
      {{locked ? 'Unlock' : 'Lock Spec'}}
    </button>
    <button id="previewBtn" class="btn-secondary">Preview</button>
    <button id="generateBtn" class="btn-primary" {{locked ? '' : 'disabled'}}>
      Generate Code
    </button>
  </section>

  <!-- Generated Files Tree -->
  <section class="file-tree">
    <h3>Generated Files</h3>
    <ul class="tree">
      {{#each generatedFiles}}
      <li class="file-item" data-status="{{status}}">
        <span class="file-icon">{{icon}}</span>
        <span class="file-path">{{path}}</span>
        <span class="file-lines">({{lines}} lines)</span>
      </li>
      {{/each}}
    </ul>
  </section>
</div>
```

### 3.2 Generation Panel (Real-time Streaming)

**Purpose**: Show real-time code generation progress with file previews

**Features**:
- Real-time file tree updates via SSE
- Click to preview generated code
- Inline error display with suggestions
- One-click retry for failed files
- Cancel button to abort generation

**SSE Event Handling**:

```typescript
// src/lib/sse.ts
export class SSEClientService {
  private eventSource: EventSource | null = null;
  private onEvent: (event: StreamEvent) => void;

  constructor(onEvent: (event: StreamEvent) => void) {
    this.onEvent = onEvent;
  }

  connect(url: string, token: string): void {
    // EventSource doesn't support custom headers, use workaround
    this.eventSource = new EventSource(`${url}?token=${token}`);

    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as StreamEvent;
        this.onEvent(data);
      } catch (e) {
        console.error('Failed to parse SSE event:', e);
      }
    };

    this.eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      this.disconnect();
    };
  }

  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}

// Event types from Sprint 51A/51B
type StreamEvent =
  | StartedEvent
  | FileGeneratingEvent
  | FileGeneratedEvent
  | QualityGateEvent
  | CompletedEvent
  | ErrorEvent
  | CheckpointEvent;

interface StartedEvent {
  type: 'started';
  timestamp: string;
  session_id: string;
  model: string;
  provider: string;
}

interface FileGeneratedEvent {
  type: 'file_generated';
  timestamp: string;
  session_id: string;
  path: string;
  content: string;
  lines: number;
  language: string;
  syntax_valid: boolean;
}

interface CompletedEvent {
  type: 'completed';
  timestamp: string;
  session_id: string;
  total_files: number;
  total_lines: number;
  duration_ms: number;
  success: boolean;
}

interface CheckpointEvent {
  type: 'checkpoint';
  timestamp: string;
  session_id: string;
  files_completed: number;
  last_file_path: string;
}

interface ErrorEvent {
  type: 'error';
  timestamp: string;
  session_id: string;
  message: string;
  recovery_id?: string;
}
```

### 3.3 Contract Lock

**Purpose**: Prevent specification changes during active code generation

**Backend API**:

```yaml
# POST /api/v1/onboarding/{id}/lock
Request:
  Headers:
    Authorization: Bearer <jwt_token>
  Body: {}

Response (200 OK):
  {
    "locked": true,
    "spec_hash": "sha256:a7f3c2d1e5b4f6a8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
    "locked_at": "2025-12-26T10:00:00Z",
    "locked_by": "user-uuid-123"
  }

# POST /api/v1/onboarding/{id}/unlock
Request:
  Headers:
    Authorization: Bearer <jwt_token>
  Body:
    {
      "unlock_reason": "Generation complete" | "Manual unlock"
    }

Response (200 OK):
  {
    "locked": false,
    "unlocked_at": "2025-12-26T10:30:00Z",
    "unlocked_by": "user-uuid-123"
  }

# GET /api/v1/onboarding/{id}/status
Response (200 OK):
  {
    "id": "uuid",
    "name": "pho24_restaurant",
    "locked": true,
    "spec_hash": "sha256:...",
    "locked_at": "2025-12-26T10:00:00Z",
    "locked_by": "user-uuid-123",
    "generation_status": "in_progress" | "completed" | "failed" | "idle"
  }
```

**Database Schema Changes**:

```sql
-- Alembic migration: add_contract_lock_fields.py
ALTER TABLE onboarding_sessions
ADD COLUMN spec_hash VARCHAR(256),
ADD COLUMN locked BOOLEAN DEFAULT FALSE,
ADD COLUMN locked_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN locked_by UUID REFERENCES users(id);

CREATE INDEX idx_onboarding_locked ON onboarding_sessions(locked);
```

**Lock Workflow**:

```
┌─────────────────────────────────────────────────────────────────┐
│ Contract Lock Workflow                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User edits AppBlueprint in VS Code                          │
│     └── Blueprint saved to backend                              │
│                                                                 │
│  2. User clicks "Lock Spec" (Cmd+Shift+L)                       │
│     ├── Extension calls POST /onboarding/{id}/lock              │
│     ├── Backend calculates SHA256(blueprint_json)               │
│     ├── Backend sets locked=true, locked_at=now()               │
│     └── Extension shows lock icon 🔒                            │
│                                                                 │
│  3. LOCKED STATE                                                │
│     ├── Edit controls disabled                                  │
│     ├── Generate button enabled                                 │
│     └── Spec immutable until unlock                             │
│                                                                 │
│  4. User clicks "Generate Code" (Cmd+Shift+G)                   │
│     ├── Extension calls POST /codegen/generate/stream           │
│     ├── Backend verifies spec_hash matches                      │
│     │   └── If mismatch → 409 Conflict error                    │
│     └── Generation starts with SSE streaming                    │
│                                                                 │
│  5. Generation completes                                        │
│     ├── Auto-unlock if success                                  │
│     └── Keep locked if failed (allow retry)                     │
│                                                                 │
│  6. Manual unlock (if needed)                                   │
│     ├── User clicks "Unlock"                                    │
│     ├── Extension calls POST /onboarding/{id}/unlock            │
│     └── Edit controls re-enabled                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Commands

| Command | Keybinding | When Condition | Description |
|---------|------------|----------------|-------------|
| `sdlc.generate` | `Cmd+Shift+G` | `sdlc.isAuthenticated && sdlc.hasBlueprint && sdlc.specLocked` | Generate code from locked blueprint |
| `sdlc.magic` | `Cmd+Shift+M` | `sdlc.isAuthenticated` | Magic mode - natural language input |
| `sdlc.lock` | `Cmd+Shift+L` | `sdlc.isAuthenticated && sdlc.hasBlueprint && !sdlc.specLocked` | Lock contract spec |
| `sdlc.unlock` | - | `sdlc.isAuthenticated && sdlc.specLocked` | Unlock contract spec |
| `sdlc.preview` | `Cmd+Shift+P` | `sdlc.hasGeneratedFiles` | Preview generated code |
| `sdlc.resume` | `Cmd+Shift+R` | `sdlc.hasFailedGeneration` | Resume from last checkpoint |
| `sdlc.openAppBuilder` | - | `sdlc.isAuthenticated` | Open App Builder webview |

### 3.5 Magic Mode Flow

```typescript
// src/commands/magic.ts
export async function magicCommand(): Promise<void> {
  // 1. Show input box for natural language
  const description = await vscode.window.showInputBox({
    prompt: 'Describe your app (Vietnamese or English)',
    placeHolder: 'Nhà hàng Phở 24 với menu và đặt bàn...',
    validateInput: (value) => {
      if (!value || value.length < 10) {
        return 'Please enter at least 10 characters';
      }
      return null;
    }
  });

  if (!description) return;

  // 2. Show domain picker (auto-detected with option to change)
  const detectedDomain = await detectDomain(description);
  const domain = await vscode.window.showQuickPick(
    SUPPORTED_DOMAINS.map(d => ({
      label: d.name,
      description: d.description,
      picked: d.id === detectedDomain
    })),
    { placeHolder: `Detected: ${detectedDomain}. Select domain:` }
  );

  if (!domain) return;

  // 3. Show output folder picker
  const outputFolder = await vscode.window.showOpenDialog({
    canSelectFolders: true,
    canSelectFiles: false,
    canSelectMany: false,
    title: 'Select output folder'
  });

  if (!outputFolder || outputFolder.length === 0) return;

  // 4. Generate blueprint and start generation
  const blueprint = await generateBlueprint(description, domain.label);

  // 5. Show preview and confirm
  const confirm = await showBlueprintPreview(blueprint);
  if (!confirm) return;

  // 6. Lock and generate
  await lockSpec(blueprint.id);
  await startStreamingGeneration(blueprint.id, outputFolder[0].fsPath);
}

const SUPPORTED_DOMAINS = [
  { id: 'restaurant', name: 'Restaurant (Nhà hàng)', description: 'Thực đơn, đặt bàn, order' },
  { id: 'ecommerce', name: 'E-commerce (Thương mại)', description: 'Sản phẩm, giỏ hàng, VNPay' },
  { id: 'hrm', name: 'HRM (Nhân sự)', description: 'Nhân viên, chấm công, lương' },
  { id: 'crm', name: 'CRM (Khách hàng)', description: 'Leads, deals, pipeline' },
  { id: 'inventory', name: 'Inventory (Kho)', description: 'Tồn kho, nhập/xuất' },
  { id: 'education', name: 'Education (Giáo dục)', description: 'Sinh viên, khóa học' },
  { id: 'healthcare', name: 'Healthcare (Y tế)', description: 'Bệnh nhân, lịch khám' },
];
```

---

## 4. File Structure

### 4.1 New Files to Create

```
vscode-extension/
├── src/
│   ├── commands/
│   │   ├── generate.ts        # Generate command (~100 lines)
│   │   ├── magic.ts           # Magic mode command (~150 lines)
│   │   └── lock.ts            # Lock/unlock commands (~80 lines)
│   ├── panels/
│   │   ├── AppBuilderPanel.ts # App Builder webview (~250 lines)
│   │   └── GenerationPanel.ts # Streaming view (~200 lines)
│   ├── providers/
│   │   └── BlueprintProvider.ts # Tree view for blueprint (~100 lines)
│   ├── lib/
│   │   ├── codegenApi.ts      # Codegen API client (~120 lines)
│   │   └── sse.ts             # SSE client service (~100 lines)
│   └── types/
│       └── codegen.ts         # TypeScript types (~80 lines)
├── media/
│   ├── app-builder.css        # Panel styles (~150 lines)
│   └── app-builder.js         # Panel scripts (~200 lines)
└── package.json               # Updated with new commands
```

### 4.2 Files to Modify

| File | Changes |
|------|---------|
| `package.json` | Add new commands, keybindings, views |
| `src/extension.ts` | Register new commands, providers, panels |
| `src/services/apiClient.ts` | Add codegen-specific API methods |

---

## 5. Backend Changes

### 5.1 New API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/onboarding/{id}/lock` | POST | Lock contract spec |
| `/api/v1/onboarding/{id}/unlock` | POST | Unlock contract spec |
| `/api/v1/onboarding/{id}/status` | GET | Get lock status |

### 5.2 Database Migration

```python
# backend/alembic/versions/xxx_add_contract_lock.py
"""Add contract lock fields to onboarding_sessions

Revision ID: xxx_add_contract_lock
Revises: previous_revision
Create Date: 2025-12-26
"""

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.add_column('onboarding_sessions',
        sa.Column('spec_hash', sa.String(256), nullable=True))
    op.add_column('onboarding_sessions',
        sa.Column('locked', sa.Boolean(), server_default='false'))
    op.add_column('onboarding_sessions',
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('onboarding_sessions',
        sa.Column('locked_by', sa.UUID(), sa.ForeignKey('users.id'), nullable=True))

    op.create_index('idx_onboarding_locked', 'onboarding_sessions', ['locked'])

def downgrade() -> None:
    op.drop_index('idx_onboarding_locked')
    op.drop_column('onboarding_sessions', 'locked_by')
    op.drop_column('onboarding_sessions', 'locked_at')
    op.drop_column('onboarding_sessions', 'locked')
    op.drop_column('onboarding_sessions', 'spec_hash')
```

### 5.3 Model Updates

```python
# backend/app/models/onboarding.py - additions
class OnboardingSession(Base):
    # ... existing fields ...

    # Contract Lock fields (Sprint 53)
    spec_hash: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationship
    locked_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[locked_by])
```

### 5.4 Schema Updates

```python
# backend/app/schemas/onboarding.py - additions

class SpecLockRequest(BaseModel):
    """Request to lock a spec."""
    pass  # No body needed, just auth

class SpecUnlockRequest(BaseModel):
    """Request to unlock a spec."""
    unlock_reason: str = Field(..., min_length=1, max_length=500)

class SpecLockResponse(BaseModel):
    """Response after locking spec."""
    locked: bool
    spec_hash: str
    locked_at: datetime
    locked_by: UUID

class SpecUnlockResponse(BaseModel):
    """Response after unlocking spec."""
    locked: bool
    unlocked_at: datetime
    unlocked_by: UUID

class OnboardingStatusResponse(BaseModel):
    """Full status of an onboarding session."""
    id: UUID
    name: str
    locked: bool
    spec_hash: Optional[str]
    locked_at: Optional[datetime]
    locked_by: Optional[UUID]
    generation_status: Literal["idle", "in_progress", "completed", "failed"]
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

```typescript
// src/test/commands/generate.test.ts
describe('Generate Command', () => {
  it('should require authentication', async () => {
    // Mock not authenticated
    // Call generate command
    // Expect error message
  });

  it('should require locked spec', async () => {
    // Mock authenticated but spec not locked
    // Call generate command
    // Expect prompt to lock first
  });

  it('should start SSE connection on generate', async () => {
    // Mock authenticated and locked
    // Call generate command
    // Verify SSE connection established
  });
});

// src/test/lib/sse.test.ts
describe('SSE Client Service', () => {
  it('should parse started event', () => {
    const event = { type: 'started', session_id: '123', model: 'qwen' };
    // Verify parsing
  });

  it('should handle file_generated event', () => {
    const event = { type: 'file_generated', path: 'app/main.py', lines: 50 };
    // Verify file creation callback
  });

  it('should handle connection errors', () => {
    // Mock connection error
    // Verify error handling and reconnection
  });
});
```

### 6.2 Integration Tests

```typescript
// src/test/integration/appBuilder.test.ts
describe('App Builder Integration', () => {
  it('should complete full magic mode flow', async () => {
    // 1. Input natural language
    // 2. Detect domain
    // 3. Generate blueprint
    // 4. Lock spec
    // 5. Start generation
    // 6. Receive SSE events
    // 7. Create files
    // 8. Unlock on complete
  });

  it('should resume failed generation', async () => {
    // 1. Mock failed generation with checkpoint
    // 2. Call resume command
    // 3. Verify resumes from last checkpoint
  });
});
```

### 6.3 E2E Tests (Playwright)

```typescript
// e2e/appBuilder.spec.ts
import { test, expect } from '@playwright/test';

test('Magic Mode generates code successfully', async ({ page }) => {
  // 1. Open VS Code with extension
  // 2. Trigger magic mode command
  // 3. Enter description
  // 4. Confirm generation
  // 5. Wait for SSE completion
  // 6. Verify files created in workspace
});
```

---

## 7. Success Criteria

### 7.1 Functional Requirements

- [ ] Extension installable from VSIX or marketplace
- [ ] User can login with SDLC Orchestrator credentials
- [ ] Magic mode accepts Vietnamese/English input
- [ ] Domain auto-detection works for 7 domains
- [ ] Lock command generates SHA256 hash correctly
- [ ] Generation streams files in real-time via SSE
- [ ] Files open automatically in VS Code tabs
- [ ] Resume command continues from checkpoint
- [ ] Unlock auto-triggers on generation complete

### 7.2 Non-Functional Requirements

- [ ] Extension activation <1s
- [ ] SSE streaming lag <200ms
- [ ] Contract lock hash validation 100% accurate
- [ ] No memory leaks during long streaming sessions
- [ ] Works offline for lock/unlock (cached state)

### 7.3 Acceptance Criteria per Use Case

| Use Case | Acceptance Criteria |
|----------|---------------------|
| UC-53-01: Validate Code | Validate <3s for <500 lines, inline diagnostics accurate |
| UC-53-02: Generate Code | File opens <1s after generate, diff view works |
| UC-53-03: @References | @file, @doc references parse correctly |
| UC-53-04: Submit Evidence | Submit <2s, auto-detect evidence type |
| UC-53-05: Validate on Save | Latency <2s, non-blocking |

---

## 8. Dependencies

### 8.1 Sprint Dependencies

- **Sprint 51A/51B**: SSE streaming endpoint `/generate/stream` ✅
- **Sprint 52**: CLI magic mode validates NLP parser ✅
- **Backend**: Contract Lock API (to be implemented in Sprint 53)

### 8.2 Package Dependencies

```json
{
  "dependencies": {
    "axios": "^1.6.2"  // existing
  }
}
```

No new npm dependencies required. EventSource is built into VS Code's Node.js environment.

---

## 9. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| SSE connection drops | Medium | Medium | Implement auto-reconnect with exponential backoff |
| Large files cause UI freeze | Low | High | Use virtual scrolling, lazy load file content |
| Hash collision (spec_hash) | Very Low | High | Use SHA256 (negligible collision probability) |
| Browser EventSource limitations | Low | Medium | Fallback to polling if EventSource fails |

---

## 10. Timeline

| Day | Focus | Deliverables |
|-----|-------|--------------|
| Day 1 | Foundation | Commands registered, package.json updated, stubs created |
| Day 2 | App Builder Panel | Webview panel with blueprint editor, basic styling |
| Day 3 | Streaming Integration | SSE client, real-time file tree, generation panel |
| Day 4 | Contract Lock | Backend API, frontend integration, lock/unlock flow |
| Day 5 | Testing + Polish | E2E tests, bug fixes, marketplace prep |

---

## Appendix A: package.json Updates

```json
{
  "contributes": {
    "commands": [
      // ... existing commands ...
      {
        "command": "sdlc.generate",
        "title": "Generate from Blueprint",
        "category": "SDLC",
        "icon": "$(code)"
      },
      {
        "command": "sdlc.magic",
        "title": "Magic Mode (Natural Language)",
        "category": "SDLC",
        "icon": "$(wand)"
      },
      {
        "command": "sdlc.lock",
        "title": "Lock Contract Spec",
        "category": "SDLC",
        "icon": "$(lock)"
      },
      {
        "command": "sdlc.unlock",
        "title": "Unlock Contract Spec",
        "category": "SDLC",
        "icon": "$(unlock)"
      },
      {
        "command": "sdlc.preview",
        "title": "Preview Generated Code",
        "category": "SDLC",
        "icon": "$(preview)"
      },
      {
        "command": "sdlc.resume",
        "title": "Resume Failed Generation",
        "category": "SDLC",
        "icon": "$(debug-restart)"
      },
      {
        "command": "sdlc.openAppBuilder",
        "title": "Open App Builder",
        "category": "SDLC",
        "icon": "$(window)"
      }
    ],
    "keybindings": [
      // ... existing keybindings ...
      {
        "command": "sdlc.generate",
        "key": "ctrl+shift+alt+g",
        "mac": "cmd+shift+g",
        "when": "sdlc.isAuthenticated && sdlc.specLocked"
      },
      {
        "command": "sdlc.magic",
        "key": "ctrl+shift+m",
        "mac": "cmd+shift+m",
        "when": "sdlc.isAuthenticated"
      },
      {
        "command": "sdlc.lock",
        "key": "ctrl+shift+l",
        "mac": "cmd+shift+l",
        "when": "sdlc.isAuthenticated && !sdlc.specLocked"
      },
      {
        "command": "sdlc.resume",
        "key": "ctrl+shift+r",
        "mac": "cmd+shift+r",
        "when": "sdlc.hasFailedGeneration"
      }
    ],
    "views": {
      "sdlc-explorer": [
        // ... existing views ...
        {
          "id": "sdlc-app-builder",
          "name": "App Builder",
          "icon": "$(code)",
          "contextualTitle": "SDLC App Builder"
        }
      ]
    }
  }
}
```

---

**Document Status**: DRAFT
**Author**: AI Development Partner
**Reviewer**: CTO (Pending)
**Last Updated**: December 25, 2025
