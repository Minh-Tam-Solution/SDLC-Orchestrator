# Fix Context Overlay Error `[object Object]`

**Date**: January 30, 2026
**Issue**: Extension shows `[object Object]` in Context Overlay
**Root Cause**: Authentication error not properly formatted

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
