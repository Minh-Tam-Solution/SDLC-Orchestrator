# i18n Developer Guide - SDLC Landing Page

**Version**: 1.0.0
**Sprint**: 60 - i18n Localization
**Date**: December 27, 2025

---

## Quick Start

### Adding a New Translation

1. Add key to both translation files:

```json
// src/messages/vi.json
{
  "mySection": {
    "title": "Tiêu đề tiếng Việt"
  }
}

// src/messages/en.json
{
  "mySection": {
    "title": "English Title"
  }
}
```

2. Use in component:

```tsx
'use client';

import { useTranslations } from 'next-intl';

export function MyComponent() {
  const t = useTranslations('mySection');

  return <h1>{t('title')}</h1>;
}
```

---

## Architecture Overview

```
src/
├── lib/i18n.ts                    # Locale config (vi, en)
├── app/providers/LanguageProvider.tsx  # Context + localStorage
├── components/ui/LanguageToggle.tsx    # VN/EN toggle button
└── messages/
    ├── vi.json                    # 286 translation keys
    └── en.json                    # 286 translation keys
```

---

## Translation Namespaces

| Namespace | Purpose | Example |
|-----------|---------|---------|
| `header` | Navigation | `t('features')` |
| `hero` | Hero section | `t('headline')` |
| `features` | Feature cards | `t('items.gateEngine.title')` |
| `howItWorks` | How it works | `t('step1.title')` |
| `vietnamFounders` | VN section | `t('title')` |
| `pricing` | Pricing tiers | `t('founder.price')` |
| `ctas` | CTA cards | `t('demo.title')` |
| `footer` | Footer links | `t('product.features')` |
| `auth.login` | Login form | `t('validation.emailRequired')` |
| `auth.register` | Register form | `t('success.title')` |
| `auth.callback` | OAuth callback | `t('loadingTitle')` |
| `checkout` | Checkout flow | `t('failed.errors.51')` |
| `i18n` | Language toggle | `t('toggle.ariaLabel')` |
| `common` | Shared strings | `t('loading')` |

---

## Common Patterns

### 1. Basic Translation

```tsx
const t = useTranslations('header');
return <span>{t('features')}</span>;
```

### 2. Nested Keys

```tsx
const t = useTranslations('features');
return <h3>{t('items.gateEngine.title')}</h3>;
```

### 3. Interpolation

```tsx
const t = useTranslations('checkout');
return <span>{t('payAmount', { amount: '2,500,000 VND' })}</span>;

// In JSON: "payAmount": "Thanh toán {amount}"
```

### 4. Multiple Namespaces

```tsx
const t = useTranslations('checkout');
const tCommon = useTranslations('common');

return (
  <>
    <h1>{t('title')}</h1>
    <span>{tCommon('loading')}</span>
  </>
);
```

### 5. Array Translations

```tsx
// In JSON: "features": ["Feature 1", "Feature 2", "Feature 3"]
const features = t.raw('pricing.founder.features') as string[];
return features.map((f, i) => <li key={i}>{f}</li>);
```

### 6. Dynamic Keys

```tsx
const FEATURE_KEYS = ['unlimitedMembers', 'aiCodegen', 'sla'] as const;

return FEATURE_KEYS.map(key => (
  <li key={key}>{t(`planInfo.features.${key}`)}</li>
));
```

---

## Language Toggle

The `LanguageToggle` component is already in Header (desktop + mobile).

### Manual Usage

```tsx
import { useLanguage } from '@/app/providers/LanguageProvider';

function MyComponent() {
  const { locale, setLocale } = useLanguage();

  return (
    <button onClick={() => setLocale(locale === 'vi' ? 'en' : 'vi')}>
      {locale === 'vi' ? 'EN' : 'VN'}
    </button>
  );
}
```

---

## localStorage Persistence

- Key: `sdlc-locale`
- Values: `'vi'` | `'en'`
- Default: `'vi'` (Vietnamese)

```ts
// Read
const locale = localStorage.getItem('sdlc-locale');

// Write (handled by LanguageProvider)
localStorage.setItem('sdlc-locale', 'en');
```

---

## HTML Lang Attribute

Automatically updated by LanguageProvider:

```ts
document.documentElement.lang = locale;
```

---

## Adding a New Page

1. Ensure page has `'use client'` directive
2. Import `useTranslations` from `next-intl`
3. Add translations to both `vi.json` and `en.json`
4. Use `t('key')` pattern

```tsx
'use client';

import { useTranslations } from 'next-intl';

export default function NewPage() {
  const t = useTranslations('newPage');

  return <h1>{t('title')}</h1>;
}
```

---

## Build Verification

```bash
cd frontend/landing
npm run build

# Expected: 13/13 pages prerendered
# No TypeScript errors
```

---

## Troubleshooting

### "useTranslations not working"

Ensure component has `'use client'` directive at top.

### "Missing translation key"

Check both `vi.json` and `en.json` have the key.

### "Translation not updating"

Clear localStorage and refresh:
```js
localStorage.removeItem('sdlc-locale');
location.reload();
```

---

## Key Counts (Verified)

| File | Scalar Keys |
|------|-------------|
| vi.json | 286 |
| en.json | 286 |

---

## References

- [next-intl Docs](https://next-intl-docs.vercel.app/)
- [Frontend-I18n-Specification.md](../../../docs/02-design/14-Technical-Specs/Frontend-I18n-Specification.md)
- [QA-CHECKLIST-SPRINT-60.md](../QA-CHECKLIST-SPRINT-60.md)
