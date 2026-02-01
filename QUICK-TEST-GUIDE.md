# Quick Test Guide - GitHub OAuth Device Flow

**Status**: ✅ Backend Ready, ⏳ GitHub Config Needed
**Date**: January 30, 2026

---

## ✅ Đã Hoàn Thành

1. **Backend Code**:
   - ✅ Device Flow endpoints added (`/auth/github/device`, `/auth/github/token`)
   - ✅ Backend rebuilt và running on port 8300 (staging)
   - ✅ Endpoints verified working

2. **Extension**:
   - ✅ Extension v1.2.2 installed
   - ✅ Extension already has correct Device Flow implementation

---

## ⏳ Cần Làm Ngay

### Step 1: Enable Device Flow trên GitHub OAuth App

**URL**: https://github.com/settings/developers

1. **Select OAuth App** (SDLC Orchestrator app)
2. **Settings tab**
3. **Find "Enable Device Flow" section**
4. **✅ Check the checkbox** to enable
5. **Save changes**

**Screenshot location** (nếu cần):
```
┌─────────────────────────────────────────────┐
│ □ Enable Device Flow                       │
│                                             │
│ Allow your app to use the device flow to   │
│ authorize users without a web browser.      │
│                                             │
│ Learn more about device flow                │
└─────────────────────────────────────────────┘
```

---

### Step 2: Update Extension Config

Extension cần biết backend port mới (8300 thay vì 8000):

**File**: VS Code Settings hoặc Extension settings

```json
{
  "sdlc.apiUrl": "http://localhost:8300/api/v1"
}
```

**OR** nếu Extension có config UI:
1. `Cmd+Shift+P` → "SDLC: Settings"
2. Update API URL: `http://localhost:8300`

---

### Step 3: Test GitHub Login

1. **Open VS Code**
2. **Cmd+Shift+P** → `SDLC: Login`
3. **Select**: `$(github) GitHub OAuth`

**Expected Flow**:
```
┌─────────────────────────────────────────┐
│ Enter code WDJB-MJHT at                │
│ https://github.com/login/device        │
│                                         │
│ [Open Browser]  [Copy Code]            │
└─────────────────────────────────────────┘
```

4. **Click "Open Browser"**
5. **Enter code** tại GitHub
6. **Authorize app**
7. **Extension auto-logs in** ✅

---

## 🧪 Test Commands

### Backend Tests

```bash
# Health check
curl http://localhost:8300/api/v1/auth/health

# Device Flow initiation (should return device_code if GitHub configured)
curl -X POST http://localhost:8300/api/v1/auth/github/device

# Expected after GitHub config:
# {
#   "device_code": "...",
#   "user_code": "WDJB-MJHT",
#   "verification_uri": "https://github.com/login/device",
#   "expires_in": 900,
#   "interval": 5
# }
```

### Extension Debug

1. **View → Output**
2. **Select**: "SDLC Orchestrator"
3. **Watch for**:
   - `[INFO] Initiating GitHub device flow...`
   - `[INFO] Device code received: ...`
   - `[INFO] Polling for authorization...`
   - `[INFO] GitHub authentication successful`

---

## ❌ Troubleshooting

### Issue: "device_flow_disabled"

**Cause**: Device Flow chưa enable trên GitHub OAuth App

**Fix**: Follow Step 1 above to enable

---

### Issue: Extension shows "Connection refused"

**Cause**: Extension đang gọi port 8000, nhưng backend chạy port 8300

**Fix**: Update Extension API URL:
```json
{
  "sdlc.apiUrl": "http://localhost:8300/api/v1"
}
```

---

### Issue: "GitHub OAuth is not configured"

**Cause**: Backend thiếu `GITHUB_CLIENT_ID` trong `.env.staging`

**Fix**:
```bash
cd /home/nqh/shared/SDLC-Orchestrator
cat .env.staging | grep GITHUB_CLIENT

# Should see:
# GITHUB_CLIENT_ID=Ov23li...
# GITHUB_CLIENT_SECRET=...
```

Nếu không có, add vào `.env.staging`:
```env
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
```

Then restart backend:
```bash
docker compose -f docker-compose.staging.yml restart backend
```

---

## ✅ Success Criteria

Test PASS khi:

- ✅ Device Flow endpoint returns `device_code`
- ✅ Extension shows user code notification
- ✅ Browser opens GitHub device authorization page
- ✅ Extension auto-logs in after authorization
- ✅ No "Session expired" errors
- ✅ Can run SDLC commands

---

## 📝 Test Report

**Tester**: _______________
**Date**: January 30, 2026

### Results

- [ ] GitHub Device Flow enabled on OAuth App
- [ ] Extension API URL updated to port 8300
- [ ] Device Flow initiation works (returns device_code)
- [ ] Extension shows user code
- [ ] GitHub authorization page loads
- [ ] Extension auto-logs in
- [ ] SDLC commands work without "Session expired"

### Notes

_______________________________________
_______________________________________
_______________________________________

---

**Next**: Sau khi test PASS, publish Extension v1.2.2 to Marketplace
