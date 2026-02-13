# Sprint 69: Route Restructure + Auth Flow Fix

**Status**: ✅ COMPLETE (Jan 04, 2026)
**Duration**: 1 day
**Goal**: Fix confusing route naming and implement proper role-based access control

---

## Summary

Sprint 69 addressed the confusing `/platform-admin` route naming and implemented proper RBAC for the Web App and Admin Panel.

### Key Changes

| Before | After | Access |
|--------|-------|--------|
| `/platform-admin/*` | `/app/*` | All authenticated users |
| `/platform-admin/admin/*` | `/admin/*` | Superusers only |
| `/dashboard` | Redirect to `/app` | - |

---

## Route Architecture (Option A - Implemented)

```
/                     → Landing page (public)
/login                → Login page (public)
/register             → Register page (public)
/app/*                → Web App (authenticated users)
  /app                → Dashboard
  /app/projects       → Projects list
  /app/gates          → Gates list
  /app/evidence       → Evidence list
  /app/policies       → Policies
  /app/codegen        → App Builder
  /app/sop-generator  → SOP Generator
  /app/settings       → User settings
/admin/*              → Admin Panel (superusers only)
  /admin              → Admin overview
  /admin/users        → User management
  /admin/audit-logs   → Audit logs
  /admin/overrides    → Override queue
  /admin/health       → System health
  /admin/settings     → Admin settings
/dashboard            → Redirects to /app
```

---

## Implementation Details

### 1. Directory Restructure

```bash
# Before
src/app/platform-admin/       # Confusing name
src/app/platform-admin/admin/ # Nested admin

# After
src/app/app/                  # Web App (all users)
src/app/admin/                # Admin Panel (superusers)
```

### 2. Route Guards

| Guard | Location | Requirement |
|-------|----------|-------------|
| `AuthGuard` | `/app/*` | Any authenticated user |
| `AdminGuard` | `/admin/*` | `is_superuser=true` |

**PlatformAdminGuard**: Deprecated (now passes through for backwards compatibility)

### 3. Sidebar Visibility

- **Settings**: Always visible to all users
- **Admin Panel**: Only visible to superusers (`is_superuser=true`)

### 4. OAuth Callback

Default redirect changed from `/dashboard` to `/app`

---

## Files Modified

### Layouts
- [app/layout.tsx](frontend/landing/src/app/app/layout.tsx) - Removed PlatformAdminGuard, only AuthGuard
- [admin/layout.tsx](frontend/landing/src/app/admin/layout.tsx) - Created with AdminGuard

### Components
- [Sidebar.tsx](frontend/landing/src/components/dashboard/Sidebar.tsx) - Conditional Admin Panel link
- [Header.tsx](frontend/landing/src/components/landing/Header.tsx) - Updated navigation links
- [AuthGuard.tsx](frontend/landing/src/components/auth/AuthGuard.tsx) - Deprecated PlatformAdminGuard

### Admin Panel Components (New)
- [AdminSidebar.tsx](frontend/landing/src/components/admin/AdminSidebar.tsx)
- [AdminHeader.tsx](frontend/landing/src/components/admin/AdminHeader.tsx)

### Pages
- [dashboard/page.tsx](frontend/landing/src/app/dashboard/page.tsx) - Now redirects to /app
- [login/page.tsx](frontend/landing/src/app/login/page.tsx) - Default redirect to /app
- [auth/callback/page.tsx](frontend/landing/src/app/auth/callback/page.tsx) - Default redirect to /app

### Bulk Updates
- All `/platform-admin/*` references → `/app/*`
- All `/platform-admin/admin/*` references → `/admin/*`

---

## Testing Checklist

| Test Case | Status |
|-----------|--------|
| Member login → redirects to `/app` | ✅ |
| Member can access Web App (`/app/*`) | ✅ |
| Member cannot see Admin Panel in sidebar | ✅ |
| Superuser login → redirects to `/app` | ✅ |
| Superuser can access Admin Panel (`/admin/*`) | ✅ |
| Superuser sees Admin Panel in sidebar | ✅ |
| OAuth callback redirects to `/app` | ✅ |
| `/dashboard` redirects to `/app` | ✅ |
| Build successful (no errors) | ✅ |

---

## Security Notes

1. **AdminGuard** enforces `is_superuser=true` for `/admin/*` routes
2. Regular Members cannot access Admin Panel (403 redirect)
3. Sidebar hides Admin Panel link for non-superusers
4. Backend API should also enforce `is_superuser` for admin endpoints

---

## Deployment

```bash
# Build
cd frontend/landing && npm run build

# Docker rebuild
docker compose build frontend-landing --no-cache

# Restart
docker compose up -d frontend-landing
```

**Production URL**: https://sdlc.nhatquangholding.com

---

## Next Steps

1. Update E2E tests for new route structure
2. Update API documentation
3. Consider renaming sidebar items for clarity
4. Add redirect from old `/platform-admin/*` URLs (nginx)

---

## Definition of Done

- [x] Routes restructured (`/platform-admin` → `/app`, `/admin`)
- [x] Access control implemented (AuthGuard, AdminGuard)
- [x] Sidebar conditional rendering (Admin Panel for superusers only)
- [x] OAuth redirect updated
- [x] Build successful
- [x] Deployed to production
- [x] Documentation updated
