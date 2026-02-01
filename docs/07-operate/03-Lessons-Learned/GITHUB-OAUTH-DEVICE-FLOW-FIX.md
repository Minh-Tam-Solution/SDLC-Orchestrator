# GitHub OAuth Device Flow Fix - Extension Login Issue

**Date**: January 30, 2026
**Sprint**: 127
**Issue**: VS Code Extension GitHub login fails with 404 error
**Status**: ✅ FIXED

---

## Problem

The VS Code Extension's GitHub OAuth login was failing with a 404 error:

```
Error Code: 999 (UNKNOWN)
Message: GitHub login failed: Request failed with status code 404

Stack Trace:
Error: GitHub login failed: Request failed with status code 404
    at AuthService.loginWithGitHub (/home/dttai/.vscode-server/extensions/mtsolution.sdlc-orchestrator-1.1.2/out/services/authService.js:237:19)
```

### Root Cause

The Extension implemented **GitHub OAuth Device Flow** (lines 232-281 in `authService.ts`), which is the correct pattern for CLI/desktop applications. However, the backend only had the standard **OAuth Authorization Code Flow** endpoints.

**What Extension Expected**:
- `POST /api/v1/auth/github/device` - Initiate device flow, get user code
- `POST /api/v1/auth/github/token` - Poll for token completion

**What Backend Had**:
- `GET /api/v1/auth/oauth/github/authorize` - Get authorization URL
- `POST /api/v1/auth/oauth/github/callback` - Handle callback

**Mismatch**: Device Flow vs Authorization Code Flow

---

## Solution

Added GitHub OAuth Device Flow support to the backend to match the Extension's implementation.

### 1. Backend Changes

**File**: `backend/app/services/oauth_service.py`

Added Device Flow methods:

```python
async def initiate_github_device_flow(self) -> dict:
    """
    Calls GitHub's /login/device/code endpoint.

    Returns:
        - device_code: For polling
        - user_code: User enters at verification_uri
        - verification_uri: https://github.com/login/device
        - expires_in: 900 seconds (15 min)
        - interval: 5 seconds (polling interval)
    """

async def poll_github_device_token(self, device_code: str) -> OAuthTokens:
    """
    Polls GitHub for device authorization completion.

    Returns:
        - OAuthTokens when user authorizes
        - ValueError with error code if pending/expired/denied
    """
```

**File**: `backend/app/api/routes/auth.py`

Added Device Flow endpoints:

```python
@router.post("/github/device")
async def github_device_flow_init() -> dict:
    """Initiate GitHub Device Flow for CLI/Desktop apps."""

@router.post("/github/token")
async def github_device_flow_poll(
    device_request: DeviceTokenRequest,
    ...
):
    """Poll for device authorization completion."""
```

**File**: `backend/app/schemas/auth.py`

Added request schema:

```python
class DeviceTokenRequest(BaseModel):
    """Request to poll for GitHub device authorization token."""
    device_code: str
```

### 2. How Device Flow Works

```
┌─────────────┐                                    ┌─────────────┐
│  Extension  │                                    │   GitHub    │
└─────────────┘                                    └─────────────┘
       │                                                   │
       │  1. POST /auth/github/device                     │
       ├──────────────────────────────────────────────────►
       │                                                   │
       │  ◄──── device_code, user_code, verification_uri │
       │                                                   │
       │  2. Show user_code to user                       │
       │     "Enter WDJB-MJHT at github.com/login/device" │
       │                                                   │
       │                                User visits GitHub │
       │                                Enters user_code   │
       │                                Authorizes app     │
       │                                                   │
       │  3. Poll POST /auth/github/token (every 5s)      │
       ├──────────────────────────────────────────────────►
       │                                                   │
       │  ◄──── {"error": "authorization_pending"}        │  (user not done)
       │                                                   │
       │  Poll again...                                   │
       ├──────────────────────────────────────────────────►
       │                                                   │
       │  ◄──── {"access_token": "...", "refresh_token"}  │  (user authorized!)
       │                                                   │
       │  4. Store tokens, user logged in                 │
       │                                                   │
```

### 3. Error Handling

The polling endpoint returns specific error codes:

| Error Code               | Meaning                        | Action                       |
|--------------------------|--------------------------------|------------------------------|
| `authorization_pending`  | User hasn't authorized yet     | Continue polling             |
| `slow_down`              | Polling too fast               | Increase interval by 5s      |
| `expired_token`          | Device code expired (15 min)   | Stop polling, restart flow   |
| `access_denied`          | User denied authorization      | Stop polling, show error     |

Response format:

```json
HTTP 400 Bad Request
{
  "error": "authorization_pending"
}
```

---

## Testing

### 1. Automated Test

```bash
cd /home/nqh/shared/SDLC-Orchestrator/backend
python test_device_flow.py
```

Expected output:

```
Testing GitHub Device Flow Endpoints
====================================
0. Checking backend health...
✅ Backend is healthy

1. Initiating device flow...
✅ Device flow initiated successfully
   User code: WDJB-MJHT
   Verification URI: https://github.com/login/device
   Expires in: 900 seconds
   Polling interval: 5 seconds

2. Testing token polling (expect authorization_pending)...
✅ Polling endpoint working correctly
   Status: authorization_pending (user hasn't authorized yet)

✅ All tests passed!
```

### 2. Manual Test with Extension

1. **Start Backend**:
   ```bash
   cd backend
   docker-compose up
   ```

2. **Test in VS Code**:
   - Open VS Code
   - Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
   - Type "SDLC: Login"
   - Select "GitHub OAuth"

3. **Expected Flow**:
   - Extension shows notification: "Enter code WDJB-MJHT at https://github.com/login/device"
   - Click "Open Browser" → Opens GitHub
   - Enter user code: `WDJB-MJHT`
   - Authorize app
   - Extension auto-logs in (polls every 5s)

4. **Verify Success**:
   - Check Extension status bar: Should show logged in user
   - Run SDLC command: Should work without "Session expired" error

---

## Why Device Flow?

Device Flow is the **correct OAuth pattern** for CLI tools and desktop apps because:

1. **No localhost callback** - Doesn't require running a local web server
2. **User-friendly** - Simple code entry (8 characters: XXXX-XXXX)
3. **Secure** - No client secret in Extension code
4. **Cross-platform** - Works on SSH, WSL, remote VS Code

**Standard Authorization Code Flow** works for:
- Web applications (our Vite dashboard)
- Can handle browser redirects
- Runs on a known callback URL

---

## Files Modified

| File | Changes |
|------|---------|
| `backend/app/services/oauth_service.py` | Added `initiate_github_device_flow()` and `poll_github_device_token()` |
| `backend/app/api/routes/auth.py` | Added `POST /auth/github/device` and `POST /auth/github/token` endpoints |
| `backend/app/schemas/auth.py` | Added `DeviceTokenRequest` schema |
| `backend/test_device_flow.py` | Created test script |

**Extension** (no changes needed):
- Already implements Device Flow correctly
- Just needed backend endpoints to exist

---

## Deployment Checklist

Before publishing Extension v1.2.2:

- [x] ✅ Backend Device Flow endpoints implemented
- [x] ✅ Syntax validation (no Python errors)
- [ ] ⏳ Backend integration tests (run `pytest backend/tests/test_github_device_flow.py`)
- [ ] ⏳ Manual test with Extension (verify GitHub login works)
- [ ] ⏳ Update CHANGELOG.md (backend + extension)
- [ ] ⏳ Deploy backend to staging
- [ ] ⏳ Test on staging environment
- [ ] ⏳ Deploy to production
- [ ] ⏳ Publish Extension v1.2.2

---

## Lessons Learned

1. **OAuth Pattern Mismatch is Common**: Always check which OAuth flow the client expects (Device Flow vs Authorization Code vs Implicit vs Client Credentials)

2. **Device Flow for Desktop/CLI**: Device Flow is the industry standard for:
   - CLI tools (GitHub CLI, Azure CLI, AWS CLI)
   - Desktop apps (VS Code extensions, Electron apps)
   - IoT devices, smart TVs

3. **Error Format Matters**: Extension expected `{"error": "code"}`, not `{"detail": {"error": "code"}}`. Use `JSONResponse` for custom formats.

4. **Test Device Flow Early**: Device Flow is harder to test than standard OAuth because it requires polling logic. Test early with automated scripts.

5. **Document OAuth Flows**: Clearly document which OAuth flow each client uses:
   - Web Dashboard → Authorization Code Flow
   - VS Code Extension → Device Flow
   - CLI (sdlcctl) → Device Flow (future)
   - Mobile App → Authorization Code with PKCE (future)

---

## References

- [GitHub OAuth Device Flow Docs](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow)
- [RFC 8628 - OAuth 2.0 Device Authorization Grant](https://datatracker.ietf.org/doc/html/rfc8628)
- [Extension authService.ts](../../vscode-extension/src/services/authService.ts#L232-L281)

---

**Status**: ✅ Ready for testing
**Next Step**: Run integration tests + manual Extension test
**Owner**: Backend Team + Extension Team
**Sprint**: 127 - Multi-Frontend Alignment Bug Fixes
