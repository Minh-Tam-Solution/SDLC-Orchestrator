# Hướng Dẫn Test GitHub OAuth Device Flow

**Date**: January 30, 2026
**Extension Version**: v1.2.2
**Backend Version**: v1.2.0 (cần update)

---

## 🎯 Mục Tiêu Test

Test chức năng GitHub OAuth login trong VS Code Extension sau khi fix lỗi 404.

**Lỗi cũ**:
```
Error: GitHub login failed: Request failed with status code 404
```

**Fix**: Backend đã thêm Device Flow endpoints (`/auth/github/device` và `/auth/github/token`)

---

## 📋 Bước 1: Chuẩn Bị Backend

### 1.1. Update Backend Code

Backend đã có Device Flow endpoints, nhưng cần restart để apply changes:

```bash
cd /home/nqh/shared/SDLC-Orchestrator/backend

# Check nếu có syntax errors
python -m py_compile app/services/oauth_service.py app/api/routes/auth.py

# Restart backend
docker-compose restart
# HOẶC nếu chạy local:
# pkill -f uvicorn
# uvicorn app.main:app --reload
```

### 1.2. Verify Backend Endpoints

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/auth/health

# Test Device Flow endpoint (should return 400 if GitHub not configured)
curl -X POST http://localhost:8000/api/v1/auth/github/device
```

**Expected Output**:
- Health: `{"status":"healthy","service":"authentication","version":"..."}`
- Device Flow: Hoặc là data (nếu GitHub configured) hoặc error message

---

## 📋 Bước 2: Install Extension v1.2.2

### Option A: Install từ VSIX (Recommended cho test)

```bash
cd /home/nqh/shared/SDLC-Orchestrator/vscode-extension

# Extension đã được build tại:
ls -lh sdlc-orchestrator-1.2.2.vsix
```

**Trong VS Code**:
1. Press `Cmd+Shift+P` (Mac) hoặc `Ctrl+Shift+P` (Windows/Linux)
2. Type: `Extensions: Install from VSIX...`
3. Select file: `/home/nqh/shared/SDLC-Orchestrator/vscode-extension/sdlc-orchestrator-1.2.2.vsix`
4. Reload VS Code

### Option B: Publish to Marketplace (sau khi test pass)

```bash
cd vscode-extension
vsce publish patch  # Auto increment 1.2.2 → 1.2.3
```

---

## 📋 Bước 3: Test GitHub OAuth Login

### 3.1. Start Login Flow

1. **Open VS Code**
2. **Open Command Palette**: `Cmd+Shift+P` / `Ctrl+Shift+P`
3. **Type**: `SDLC: Login`
4. **Select**: `$(github) GitHub OAuth`

### 3.2. Expected Behavior - Device Flow

Extension sẽ hiển thị notification:

```
┌─────────────────────────────────────────────────────────┐
│  Enter code WDJB-MJHT at                               │
│  https://github.com/login/device                       │
│                                                         │
│  [Open Browser]  [Copy Code]                           │
└─────────────────────────────────────────────────────────┘
```

**Nếu click "Open Browser"**:
- ✅ Browser mở https://github.com/login/device
- ✅ User code được copy to clipboard
- ✅ Extension shows "Code WDJB-MJHT copied to clipboard"

**Nếu click "Copy Code"**:
- ✅ User code được copy to clipboard
- User tự mở browser và paste code

### 3.3. Authorize on GitHub

1. **Paste user code** tại https://github.com/login/device
2. **Click "Continue"**
3. **Review permissions**: `read:user` và `user:email`
4. **Click "Authorize"**

### 3.4. Extension Auto-Login

Extension sẽ poll backend mỗi 5 giây:

```
Polling... (authorization_pending)
Polling... (authorization_pending)
Polling... (authorization_pending)
✅ Login successful!
```

**Success Indicators**:
- ✅ Status bar shows: `SDLC: <your-email>`
- ✅ No "Session expired" errors
- ✅ Can run SDLC commands without re-login

---

## 🧪 Bước 4: Verify Login State

### 4.1. Check Status Bar

Bottom-right corner should show:
```
SDLC: user@example.com
```

### 4.2. Test SDLC Command

1. Press `Cmd+Shift+P` / `Ctrl+Shift+P`
2. Type: `SDLC: Get Gate Status`
3. Should work without "Session expired" error

### 4.3. Check Extension Output

1. View → Output
2. Select "SDLC Orchestrator" from dropdown
3. Should see:
   ```
   [INFO] GitHub authentication successful
   [INFO] Access token stored successfully
   ```

---

## ❌ Troubleshooting

### Issue 1: Still getting 404 error

**Cause**: Backend chưa restart hoặc endpoints chưa deploy

**Fix**:
```bash
cd backend
docker-compose restart
# Wait 10 seconds
curl http://localhost:8000/api/v1/auth/github/device
```

### Issue 2: "GitHub OAuth is not configured"

**Cause**: Backend thiếu `GITHUB_CLIENT_ID` và `GITHUB_CLIENT_SECRET` trong `.env`

**Fix**:
```bash
cd backend
cat .env | grep GITHUB_CLIENT
# Should see:
# GITHUB_CLIENT_ID=your_client_id
# GITHUB_CLIENT_SECRET=your_client_secret
```

Nếu không có, cần tạo GitHub OAuth App:
1. https://github.com/settings/developers
2. New OAuth App
3. Callback URL: `http://localhost:3000/auth/callback` (for web)
4. Copy Client ID + Secret vào `.env`

### Issue 3: "authorization_pending" forever

**Cause**: User chưa authorize hoặc device code expired (15 min)

**Fix**:
- Check browser: Đã paste code và click "Authorize" chưa?
- Restart flow: Logout và login lại (device code mới)

### Issue 4: Extension shows old version

**Cause**: VS Code cache

**Fix**:
```bash
# Uninstall old version
code --uninstall-extension mtsolution.sdlc-orchestrator

# Install new version
code --install-extension /path/to/sdlc-orchestrator-1.2.2.vsix

# Reload VS Code
# Cmd+Shift+P → "Developer: Reload Window"
```

---

## ✅ Success Criteria

Test PASS khi:

1. ✅ **No 404 Error**: GitHub login không bị 404
2. ✅ **Device Flow Works**: User code hiển thị, browser mở đúng URL
3. ✅ **Auto-Login**: Extension tự động login sau khi user authorize
4. ✅ **Persistent Session**: Không bị "Session expired" sau login
5. ✅ **SDLC Commands Work**: Các lệnh SDLC chạy bình thường

---

## 📝 Test Report Template

Sau khi test, ghi lại kết quả:

```markdown
## GitHub OAuth Device Flow Test - v1.2.2

**Tester**: <your-name>
**Date**: January 30, 2026
**Backend**: v1.2.0
**Extension**: v1.2.2

### Test Results

- [ ] Backend Device Flow endpoint exists (POST /auth/github/device)
- [ ] Extension shows user code notification
- [ ] "Open Browser" button works
- [ ] GitHub authorization page loads
- [ ] Extension auto-logs in after authorization
- [ ] No "Session expired" errors
- [ ] SDLC commands work without re-login

### Issues Found

1. <issue-description>
2. <issue-description>

### Notes

<any-additional-notes>
```

---

## 🚀 Next Steps (Sau khi test PASS)

1. ✅ Update backend CHANGELOG.md
2. ✅ Update Extension README.md
3. ✅ Deploy backend to staging
4. ✅ Test trên staging environment
5. ✅ Deploy to production
6. ✅ Publish Extension v1.2.2 to Marketplace

---

**Happy Testing!** 🎉
