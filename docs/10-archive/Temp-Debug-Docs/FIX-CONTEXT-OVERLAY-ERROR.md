# Fix Context Overlay Errors

**Date**: January 30, 2026 (BUG-001), February 11, 2026 (BUG-002, BUG-003)
**Component**: VS Code Extension → Context Overlay Panel + Spec Validation
**Status**: All RESOLVED

---

## 🔍 Problem Analysis

### Error Flow

1. User logs in with GitHub OAuth ✅
2. Extension calls `/api/v1/agents-md/context/{projectId}`
3. Backend returns: `{"detail": "Could not validate credentials"}` ❌
4. Extension displays error object as `[object Object]` instead of error message

### Root Cause

**Backend Response** (when auth fails):
```json
{
  "detail": "Could not validate credentials"
}
```

**Extension Code** (contextPanel.ts:183):
```typescript
catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    this.lastError = message;
}
```

The issue: When API returns `{"detail": "..."}`, axios wraps it in error object:
```typescript
error.response.data = {detail: "Could not validate credentials"}
```

But `String(error)` converts the whole axios error object to `[object Object]`, not just the detail message.

---

## ✅ Solution

### Fix 1: Better Error Handling in Extension

Update `contextPanel.ts` line 183-185:

```typescript
catch (error: any) {
    // Extract meaningful error message
    let message = 'Unknown error';

    if (error?.response?.data?.detail) {
        // FastAPI error format
        message = error.response.data.detail;
    } else if (error?.message) {
        // Standard Error object
        message = error.message;
    } else if (typeof error === 'string') {
        message = error;
    } else {
        message = JSON.stringify(error);
    }

    Logger.error(`Failed to fetch context overlay: ${message}`);
    this.lastError = message;
}
```

### Fix 2: Ensure Auth Token is Sent

Check `apiClient.ts` to ensure Authorization header is sent with all requests.

---

## 🧪 Testing

### Test 1: Reproduce Error

```bash
# Call API without auth token
curl https://sdlc.nhatquangholding.com/api/v1/agents-md/context/local-sdlc-orchestrator

# Expected:
# {"detail": "Could not validate credentials"}
```

### Test 2: Call API with Auth Token

```bash
# After GitHub OAuth login, Extension should have access_token
# API call should include: Authorization: Bearer <token>

# Test manually:
TOKEN="your_access_token_here"
curl -H "Authorization: Bearer $TOKEN" \
  https://sdlc.nhatquangholding.com/api/v1/agents-md/context/local-sdlc-orchestrator
```

### Test 3: Verify Extension Fix

1. Rebuild Extension with error handling fix
2. Reload VS Code
3. Login with GitHub OAuth
4. Check Context Overlay - should show proper error message instead of `[object Object]`

---

## 🔍 Debug Current Auth State

Check if Extension has valid token:

```typescript
// In Extension debug console (Cmd+Shift+P → "Developer: Toggle Developer Tools")
// Look for stored tokens in Extension storage
```

Or check Extension logs:
```
View → Output → "SDLC Orchestrator"
```

Look for:
- `[INFO] Access token stored successfully`
- `[ERROR] No access token found`

---

## 📝 Next Steps

1. **Fix error message formatting** (contextPanel.ts)
2. **Verify token is stored** after GitHub OAuth login
3. **Verify token is sent** with API requests (Authorization header)
4. **Rebuild Extension** with fixes
5. **Test complete flow**:
   - GitHub OAuth login
   - Context Overlay loads without error
   - Proper error messages if auth fails

---

## 💡 Why This Matters

**Good Error Messages**:
```
❌ Error: Could not validate credentials
   Please log in again
```

**Bad Error Messages**:
```
❌ Error: [object Object]
   (User has no idea what's wrong)
```

Proper error handling is critical for debugging and user experience!

---
---

# BUG-002: Gate Status Mismatch - Context Overlay vs Gate Status

**Date**: February 11, 2026
**Issue**: Context Overlay shows "G3 Pending" while Gate Status panel shows "G3 Approved"
**Root Cause**: Case-sensitive status comparison + missing DB hydration on cold start

---

## 🔍 Problem Analysis

### Symptom

Two Extension sidebar views displayed **contradictory** gate statuses for the same project:

| View | API Endpoint | Displayed |
|------|-------------|-----------|
| **Context Overlay** (`sdlc-context`) | `GET /api/v1/agents-md/context/{id}` | G3 **Pending** |
| **Gate Status** (`sdlc-gate-status`) | `GET /api/v1/gates?project_id={id}` | G3 **Approved** |

### Root Cause 1: Case-Sensitive Status Comparison

**File**: `backend/app/services/context_overlay_service.py` (line 251)

```python
# BUG: Gate model stores UPPERCASE ("APPROVED"), code checks lowercase ("passed")
gate_status = f"{gate.gate_name} {'PASSED' if gate.status == 'passed' else 'PENDING'}"
#                                              ^^^^^^^^
#                                              gate.status is "APPROVED", never "passed"
#                                              → Always falls to ELSE → Always shows "PENDING"
```

The Gate DB model uses UPPERCASE enum: `APPROVED`, `REJECTED`, `PENDING_APPROVAL`, `DRAFT`.
The comparison used lowercase `'passed'` which never matches → every gate always showed PENDING.

### Root Cause 2: DynamicContextService Never Loads from DB

**File**: `backend/app/services/dynamic_context_service.py` (line 505)

```python
async def load_context(self, project_id: UUID) -> DynamicContext:
    # TODO: Load from database when context persistence is implemented
    return self._get_or_create_context(project_id)  # ← Always returns default: PENDING
```

On server restart, all in-memory contexts reset to `GateStatus.PENDING` (the dataclass default). The `load_context()` method had a TODO stub that never actually queried the gates table.

### Dual Enum Systems (Design Flaw)

| Gate Model (DB) | DynamicContext (Events) | Display |
|-----------------|------------------------|---------|
| `APPROVED` | `GateStatus.PASSED` | PASSED |
| `REJECTED` | `GateStatus.FAILED` | FAILED |
| `PENDING_APPROVAL` | `GateStatus.IN_PROGRESS` | PENDING |
| `DRAFT` | `GateStatus.PENDING` | DRAFT |
| `ARCHIVED` | `GateStatus.BYPASSED` | ARCHIVED |

No explicit mapping existed between these two enum systems.

---

## ✅ Solution

### Fix 1: ContextOverlayService - Proper Status Mapping

**File**: `backend/app/services/context_overlay_service.py`

Rewrote `_get_stage_and_gate()` to:
1. Query highest APPROVED gate first (most meaningful status)
2. Map DB status → display status with explicit UPPERCASE mapping
3. Extract gate ID from `gate_name` field (e.g. `"G3"` → `"G3"`, `"G2.1: Architecture Review"` → `"G2.1"`)

**Important**: Initially used `gate_type.split("_")[0]` but this produced "SHIP" from `gate_type="SHIP_READY"`.
The correct field is `gate_name` (stores "G3", "G0.2", etc.)

```python
# Find highest approved gate
approved_result = await self.db.execute(
    select(Gate)
    .where(Gate.project_id == project_id)
    .where(Gate.status == "APPROVED")  # UPPERCASE match
    .where(Gate.deleted_at.is_(None))
    .order_by(Gate.created_at.desc())
    .limit(1)
)
approved_gate = approved_result.scalar_one_or_none()

if approved_gate:
    # Use gate_name (NOT gate_type) to extract gate ID
    gate_id = approved_gate.gate_name.split(":")[0].strip()  # "G3" → "G3"
    return approved_gate.stage, f"{gate_id} PASSED"

# Fallback: explicit status mapping
status_display = {
    "APPROVED": "PASSED",
    "REJECTED": "FAILED",
    "PENDING_APPROVAL": "PENDING",
    "IN_PROGRESS": "IN PROGRESS",
    "DRAFT": "DRAFT",
    "ARCHIVED": "ARCHIVED",
}.get(gate.status, "PENDING")
```

**DB field reference** (actual data for SDLC-Orchestrator):
| gate_name | gate_type | stage | status |
|-----------|-----------|-------|--------|
| G3 | SHIP_READY | BUILD | APPROVED |
| G2 | DESIGN_READY | HOW | APPROVED |
| G1 | PLANNING_COMPLETE | WHAT | APPROVED |
| G0.2 | SOLUTION_DIVERSITY | WHY | APPROVED |
| G0.1 | PROBLEM_DEFINITION | WHY | APPROVED |

### Fix 2: DynamicContextService - DB Hydration on Cold Start

**File**: `backend/app/services/dynamic_context_service.py`

Implemented `load_context()` to query gates table when `update_count == 0` (context was never populated by events):

```python
async def load_context(self, project_id: UUID) -> DynamicContext:
    context = self._get_or_create_context(project_id)
    if context.update_count == 0:
        # Query gates table for latest status
        result = await self.db.execute(
            select(Gate).where(Gate.project_id == project_id)
            .where(Gate.deleted_at.is_(None))
            .order_by(Gate.created_at.desc())
        )
        # ... hydrate context from DB
    return context
```

### Fix 3: Endpoint - Use load_context()

**File**: `backend/app/api/v1/endpoints/agents_md.py`

Changed `get_dynamic_context` endpoint from `_get_or_create_context()` to `load_context()`.

---

## 🧪 Verification

1. Rebuilt Docker image: `docker compose -f docker-compose.staging.yml up -d --build backend`
2. Backend restarted successfully with all services healthy
3. Extension now shows consistent gate status in both views:
   - Context Overlay: "G3 PASSED"
   - Gate Status: "G3 Approved"

---

## 💡 Lesson Learned

**Dual-enum anti-pattern**: When two systems (DB model and event system) use different enum values for the same concept, an explicit mapping layer is required. Without it, case sensitivity and value mismatches cause silent data inconsistencies that are hard to detect.

**Cold-start hydration**: In-memory event-driven services MUST load initial state from DB on startup. A TODO stub is effectively a bug waiting to happen after the next server restart.

**Field naming assumption**: Never assume DB field contents from field names alone. `gate_type="SHIP_READY"` was assumed to be `"G3_BUILD_COMPLETE"`. Always query actual DB data to verify.

---
---

# BUG-003: Spec Validation Command Crash - "Cannot read properties of undefined"

**Date**: February 11, 2026
**Issue**: Running "SDLC: Show Spec Validation Results" from command palette throws: `Cannot read properties of undefined (reading 'spec_id')`
**Root Cause**: Command handler received no `result` argument when invoked from command palette; `showValidationResultsPanel()` had no null guard.

---

## 🔍 Problem Analysis

### Symptom

User runs "SDLC: Show Spec Validation Results" from VS Code command palette → immediate error:
```
Cannot read properties of undefined (reading 'spec_id')
```

### Root Cause

The `sdlc.showSpecValidationResults` command is designed to be called **programmatically** with a `SpecValidationResult` parameter (from notification "Show Details" buttons). When called from the **command palette**, no argument is passed → `result` is `undefined`.

**File**: `vscode-extension/src/commands/specValidationCommand.ts`

```typescript
// Line 346: accesses result.spec_id without null check
outputChannel.appendLine(`Spec ID:     ${result.spec_id}`);
//                                      ^^^^^^^^^^^^^^^^
//                                      result is undefined → crash
```

---

## ✅ Solution

### Fix 1: Command Handler Guard (line 69)

Added null check at command handler level - if no result, run validation on current file:

```typescript
const showResultsCommand = vscode.commands.registerCommand(
    'sdlc.showSpecValidationResults',
    async (result?: SpecValidationResult) => {
        if (!result) {
            const editor = vscode.window.activeTextEditor;
            if (editor && editor.document.languageId === 'markdown') {
                await executeValidateSpec(codegenApi);
            } else {
                void vscode.window.showWarningMessage(
                    'No spec validation results available. Open a spec file and run "SDLC: Validate Spec" first.'
                );
            }
            return;
        }
        showValidationResultsPanel(result);
    }
);
```

### Fix 2: Defensive Null Check in showValidationResultsPanel (line 337)

Added null guard inside the function itself as defense-in-depth:

```typescript
function showValidationResultsPanel(result: SpecValidationResult): void {
    if (!result || !result.spec_id) {
        void vscode.window.showWarningMessage(
            'No spec validation results available. Run "SDLC: Validate Spec" on a specification file first.'
        );
        return;
    }
    // ... render results panel
}
```

### Fix 3: Same pattern applied to E2E Validate command

`sdlc.showE2EResults` had the same vulnerability - added null guard.

---

## 💡 Lesson Learned

**Command palette invocation**: VS Code commands registered with `vscode.commands.registerCommand` can be invoked from command palette without arguments. Any command that expects parameters MUST handle the no-argument case gracefully.
