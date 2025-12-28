# Sprint 60 - i18n Localization QA Checklist

**Date**: December 27, 2025
**Sprint**: 60 - i18n Localization (VN/EN)
**Status**: Day 3 - Polish & QA

---

## Build Status

- [x] `npm run build` - **PASSED** (13/13 pages prerendered)
- [x] No TypeScript errors
- [x] No linting errors

---

## Infrastructure Verification

### i18n Configuration
- [x] `src/lib/i18n.ts` - Locales defined (vi, en)
- [x] `src/messages/vi.json` - Vietnamese translations complete
- [x] `src/messages/en.json` - English translations complete

### Language Provider
- [x] `src/app/providers/LanguageProvider.tsx` - Context provider
- [x] localStorage key: `sdlc-locale`
- [x] Dynamic message loading
- [x] `document.documentElement.lang` updates on locale change

### Language Toggle
- [x] `src/components/ui/LanguageToggle.tsx` - Toggle button
- [x] `LanguageDropdown` component for mobile

---

## Manual QA Checklist

### Pages to Test

| Page | Route | VN Text | EN Text | Toggle |
|------|-------|---------|---------|--------|
| Landing | `/` | [ ] | [ ] | [ ] |
| Login | `/login` | [ ] | [ ] | [ ] |
| Register | `/register` | [ ] | [ ] | [ ] |
| Checkout | `/checkout?plan=founder` | [ ] | [ ] | [ ] |
| Success | `/checkout/success` | [ ] | [ ] | [ ] |
| Failed | `/checkout/failed` | [ ] | [ ] | [ ] |
| OAuth Callback | `/auth/callback` | [ ] | [ ] | [ ] |

### Language Toggle Tests

- [ ] Click toggle button switches VN <-> EN
- [ ] Flag icon updates (VN=Flag, EN=Flag)
- [ ] Text updates immediately (no page refresh)
- [ ] `<html lang>` attribute changes (inspect element)

### localStorage Persistence Tests

1. [ ] Set language to EN
2. [ ] Refresh page (F5)
3. [ ] Verify language stays EN
4. [ ] Close browser, reopen
5. [ ] Verify language stays EN

### Components to Verify

| Component | VN | EN |
|-----------|----|----|
| Header | [ ] | [ ] |
| Hero | [ ] | [ ] |
| Features | [ ] | [ ] |
| HowItWorks | [ ] | [ ] |
| VietnamFounders | [ ] | [ ] |
| Pricing | [ ] | [ ] |
| CTASection | [ ] | [ ] |
| Footer | [ ] | [ ] |

### Form Validation Messages (Login/Register)

| Field | VN Error | EN Error |
|-------|----------|----------|
| Email empty | [ ] | [ ] |
| Email invalid | [ ] | [ ] |
| Password empty | [ ] | [ ] |
| Password mismatch | [ ] | [ ] |

### OAuth Error Messages

- [ ] GitHub OAuth error - VN message
- [ ] GitHub OAuth error - EN message
- [ ] Google OAuth error - VN message
- [ ] Google OAuth error - EN message

### VNPay Error Codes (Checkout Failed)

| Code | VN Message | EN Message |
|------|------------|------------|
| 07 | [ ] | [ ] |
| 09 | [ ] | [ ] |
| 24 | [ ] | [ ] |
| 51 | [ ] | [ ] |
| 99 | [ ] | [ ] |

---

## Translation Coverage Summary

### Namespaces Implemented

1. **header** - Navigation, menu
2. **hero** - Landing hero section
3. **features** - Feature cards
4. **howItWorks** - 3-step guide
5. **vietnamFounders** - Vietnam section
6. **pricing** - Pricing tiers
7. **ctas** - Call-to-action cards
8. **footer** - Footer links
9. **auth.login** - Login form
10. **auth.register** - Register form
11. **auth.callback** - OAuth callback
12. **checkout** - Checkout flow
13. **i18n** - Language toggle labels
14. **common** - Shared strings

### Key Count (Verified)

| File | Scalar Keys |
|------|-------------|
| vi.json | 286 |
| en.json | 286 |

*Counted via: `jq '[paths(scalars)] | length'`*

---

## Sign-off

- [ ] QA Lead
- [ ] Frontend Lead
- [ ] CTO

**Sprint 60 Status**: Ready for merge after QA sign-off
