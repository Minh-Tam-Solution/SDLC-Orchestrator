# Frontend Internationalization (i18n) Specification

## Document Control

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Status | G2 APPROVED (Dec 27, 2025) |
| Author | AI Development Partner |
| Date | December 27, 2025 |
| Depends On | Landing-Page-Design-Specification v1.1.0 |
| Gate | G2 (Design Ready) |
| Framework | SDLC 6.1.0 Universal Framework |

---

## 1. Overview

### 1.1 Purpose

This document defines the technical specification for implementing internationalization (i18n) support in the SDLC Orchestrator Landing Page frontend. The implementation enables Vietnamese (vi) and English (en) language switching with client-side persistence.

### 1.2 Scope

- Landing page at `sdlc.nhatquangholding.com`
- Language toggle component in navigation
- Client-side language switching without page reload
- localStorage persistence for language preference
- Translation files for all user-facing text

### 1.3 Design Principles

1. **Vietnamese-first** - Vietnamese (vi) as default locale
2. **No URL complexity** - No locale-in-URL routing (/vi/, /en/)
3. **Client-side switching** - Dynamic without page reload
4. **Persistence** - Remember user preference via localStorage
5. **SEO-friendly** - Proper lang attribute and meta tags
6. **Type-safe** - Full TypeScript support with IntelliSense

---

## 2. Technical Architecture

### 2.1 Technology Choice: next-intl

**Selected Library**: `next-intl` (v4.x)

**Rationale**:
- Official support for Next.js App Router
- RSC (React Server Components) compatible
- Lightweight bundle size (~2KB gzipped)
- ICU message format support
- TypeScript-first design

**Alternatives Considered**:
| Library | Decision | Reason |
|---------|----------|--------|
| react-i18next | Rejected | Extra complexity for App Router |
| lingui | Rejected | Build-time extraction adds complexity |
| next-translate | Rejected | Less active maintenance |

### 2.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SDLC Landing Page                                  │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                          LanguageProvider                              │ │
│  │  • Wraps entire app                                                    │ │
│  │  • Manages locale state                                                │ │
│  │  • Syncs with localStorage                                             │ │
│  │  • Provides IntlProvider context                                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Header     │  │    Hero      │  │  Features    │  │   Footer     │   │
│  │ + Toggle     │  │              │  │              │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│         │                │                 │                 │             │
│         ▼                ▼                 ▼                 ▼             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      useTranslations() Hook                            │ │
│  │  • t('key') → localized string                                         │ │
│  │  • t('key', { param }) → interpolated string                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│                                    ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      Translation Files                                 │ │
│  │  /messages/vi.json  │  /messages/en.json                               │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Component Hierarchy (Actual Project Structure)

```
frontend/landing/src/
├── app/
│   ├── layout.tsx                    # Root layout - wrap with LanguageProvider
│   ├── page.tsx                      # Landing page
│   ├── login/page.tsx                # Login page - translate
│   ├── register/page.tsx             # Register page - translate
│   ├── checkout/
│   │   ├── page.tsx                  # Checkout page - translate
│   │   └── success/page.tsx          # Success page - translate
│   └── providers/
│       └── LanguageProvider.tsx      # NEW: i18n context provider
│
├── components/
│   ├── landing/
│   │   ├── Header.tsx                # Add LanguageToggle, use t()
│   │   ├── Hero.tsx                  # Use t()
│   │   ├── Features.tsx              # Use t()
│   │   ├── HowItWorks.tsx            # Use t()
│   │   ├── VietnamFounders.tsx       # Use t() (was EP06Section)
│   │   ├── Pricing.tsx               # Use t()
│   │   ├── CTASection.tsx            # Use t() (was CTAs)
│   │   └── Footer.tsx                # Use t()
│   └── ui/
│       └── LanguageToggle.tsx        # NEW: VN/EN switch button
│
├── lib/
│   └── i18n.ts                       # NEW: i18n configuration
│
└── messages/
    ├── vi.json                       # NEW: Vietnamese translations (~500 lines)
    └── en.json                       # NEW: English translations (~500 lines)
```

**Total Files to Migrate**: 12 UI files
- 8 landing components: Header, Hero, Features, HowItWorks, VietnamFounders, Pricing, CTASection, Footer
- 4 app pages: login, register, checkout, checkout/success

---

## 3. Configuration Specification

### 3.1 i18n Configuration (`lib/i18n.ts`)

```typescript
import { getRequestConfig } from 'next-intl/server';
import { notFound } from 'next/navigation';

export const locales = ['vi', 'en'] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = 'vi';

export default getRequestConfig(async ({ locale }) => {
  // Validate locale
  if (!locales.includes(locale as Locale)) {
    notFound();
  }

  return {
    messages: (await import(`@/messages/${locale}.json`)).default,
    timeZone: 'Asia/Ho_Chi_Minh',
    now: new Date(),
  };
});
```

### 3.2 LanguageProvider (`providers/LanguageProvider.tsx`)

```typescript
'use client';

import { NextIntlClientProvider } from 'next-intl';
import { ReactNode, useEffect, useState } from 'react';
import { Locale, defaultLocale, locales } from '@/lib/i18n';

const STORAGE_KEY = 'sdlc-locale';

interface LanguageProviderProps {
  children: ReactNode;
  initialLocale?: Locale;
}

export function LanguageProvider({
  children,
  initialLocale = defaultLocale
}: LanguageProviderProps) {
  const [locale, setLocale] = useState<Locale>(initialLocale);
  const [messages, setMessages] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);

  // Load locale from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Locale;
    if (stored && locales.includes(stored)) {
      setLocale(stored);
    }
  }, []);

  // Load messages when locale changes
  useEffect(() => {
    async function loadMessages() {
      setIsLoading(true);
      try {
        const msgs = await import(`@/messages/${locale}.json`);
        setMessages(msgs.default);
        document.documentElement.lang = locale;
        localStorage.setItem(STORAGE_KEY, locale);
      } catch (error) {
        console.error('Failed to load messages:', error);
      } finally {
        setIsLoading(false);
      }
    }
    loadMessages();
  }, [locale]);

  const changeLocale = (newLocale: Locale) => {
    if (locales.includes(newLocale)) {
      setLocale(newLocale);
    }
  };

  if (isLoading) {
    return null; // Or skeleton loader
  }

  return (
    <LanguageContext.Provider value={{ locale, changeLocale }}>
      <NextIntlClientProvider
        locale={locale}
        messages={messages}
        timeZone="Asia/Ho_Chi_Minh"
      >
        {children}
      </NextIntlClientProvider>
    </LanguageContext.Provider>
  );
}
```

### 3.3 LanguageToggle Component

```typescript
'use client';

import { useLanguage } from '@/providers/LanguageProvider';

export function LanguageToggle() {
  const { locale, changeLocale } = useLanguage();

  return (
    <button
      onClick={() => changeLocale(locale === 'vi' ? 'en' : 'vi')}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-md
                 border border-gray-200 hover:border-gray-300
                 text-sm font-medium transition-colors"
      aria-label={locale === 'vi' ? 'Switch to English' : 'Chuyển sang Tiếng Việt'}
    >
      <span className="text-base">{locale === 'vi' ? '🇻🇳' : '🇬🇧'}</span>
      <span>{locale === 'vi' ? 'VN' : 'EN'}</span>
    </button>
  );
}
```

---

## 4. Translation File Specification

### 4.1 Message Key Structure

```yaml
Translation Key Convention:
  Format: {section}.{subsection}.{element}
  Examples:
    - nav.features → "Tính năng"
    - hero.headline → "Control Plane for AI-Powered Development"
    - pricing.founder.price → "2.5M VND/tháng"

Namespace Structure:
  nav:               # Navigation links
  hero:              # Hero section
  features:          # Features section
  howItWorks:        # How it works section
  vietnamFounders:   # Vietnam Founders section (was ep06)
  pricing:           # Pricing section
  ctas:              # CTA cards section
  footer:            # Footer section
  auth:              # Login/Register pages
    login:           # Login page
    register:        # Register page
  checkout:          # Checkout flow
    success:         # Success page
  common:            # Shared strings (buttons, labels)
```

### 4.2 Vietnamese Translations (`messages/vi.json`)

```json
{
  "nav": {
    "features": "Tính năng",
    "pricing": "Bảng giá",
    "docs": "Tài liệu",
    "login": "Đăng nhập",
    "register": "Đăng ký"
  },
  "hero": {
    "badge": "Operating System for Software 3.0",
    "headline": "Control Plane for AI-Powered Development",
    "subheadline": "Orchestrate any AI coder under enterprise governance. Native codegen for teams without AI tools.",
    "cta": {
      "primary": "Bắt đầu miễn phí",
      "secondary": "Xem Demo",
      "tertiary": "Liên hệ tư vấn"
    },
    "trust": {
      "owasp": "OWASP L2",
      "vnSme": "VN SME",
      "fourGate": "4-Gate"
    }
  },
  "features": {
    "title": "One platform. Four superpowers.",
    "qualityGates": {
      "title": "Quality Gates",
      "description": "Policy-as-Code gates at every stage."
    },
    "evidenceVault": {
      "title": "Evidence Vault",
      "description": "Immutable audit trail for every decision."
    },
    "codegen": {
      "title": "AI Code Generation",
      "description": "Native AI code generation. IR-based, 4-Gate validated."
    },
    "policyGuards": {
      "title": "Policy Guards",
      "description": "OPA-powered governance. Block, warn, or allow auto."
    }
  },
  "howItWorks": {
    "title": "How It Works",
    "step1": {
      "title": "Connect",
      "description": "Link your GitHub repo. 2 phút setup."
    },
    "step2": {
      "title": "Configure",
      "description": "Choose policies and gates."
    },
    "step3": {
      "title": "Ship",
      "description": "AI validates every PR. Full audit trail."
    }
  },
  "vietnamFounders": {
    "flag": "🇻🇳",
    "title": "Dành cho Founders Việt Nam",
    "subtitle": "IR-based Codegen - Từ ý tưởng đến sản phẩm đầu tiên",
    "description": "Bạn không cần Cursor hay Claude Code. AI Code Generation tích hợp sẵn trong platform, giúp bạn build sản phẩm đầu tiên trong 30 phút* với full audit trail.",
    "disclaimer": "*Typical for simple CRUD apps. Time varies by project scope.",
    "features": {
      "templates": "Vietnamese domain templates (E-commerce, HRM, CRM)",
      "pipeline": "4-Gate Quality Pipeline",
      "compliance": "Tuân thủ quy định VN (BHXH, VAT, Luật Lao động)",
      "support": "Hỗ trợ tiếng Việt"
    },
    "cta": "Bắt đầu với AI Code Generation"
  },
  "pricing": {
    "title": "Bảng giá",
    "subtitle": "Start free. Scale with confidence.",
    "free": {
      "name": "FREE",
      "price": "0 VND",
      "features": {
        "projects": "1 project",
        "gates": "5 gates",
        "support": "Community"
      },
      "cta": "Thử ngay"
    },
    "founder": {
      "name": "FOUNDER",
      "badge": "PHỔ BIẾN NHẤT",
      "price": "2.5M VND/tháng",
      "priceNote": "(~$99/team)",
      "features": {
        "users": "Unlimited users",
        "codegen": "AI Code Generation",
        "vault": "Evidence Vault",
        "support": "VN Support"
      },
      "cta": "Bắt đầu ngay"
    },
    "enterprise": {
      "name": "ENTERPRISE",
      "price": "Liên hệ",
      "features": {
        "unlimited": "Unlimited",
        "onPremise": "On-premise",
        "sla": "Custom SLA",
        "dedicated": "Dedicated"
      },
      "cta": "Liên hệ Sales"
    },
    "founderNote": "Founder Plan: Dành cho startup VN xây dựng sản phẩm đầu tiên",
    "globalNote": "For global teams: Standard Plan at $30/user/month",
    "globalLink": "View Global Pricing"
  },
  "ctas": {
    "demo": {
      "icon": "👀",
      "title": "Watch Demo",
      "description": "See how it works in 3 minutes",
      "cta": "View Sample Project"
    },
    "free": {
      "icon": "🚀",
      "title": "Start Free",
      "description": "1 project, 5 gates. No credit card",
      "cta": "Create Account"
    },
    "talk": {
      "icon": "📞",
      "title": "Talk to Us",
      "description": "For SME and Enterprise",
      "cta": "Schedule"
    }
  },
  "footer": {
    "tagline": "Operating System for Software 3.0",
    "product": {
      "title": "Product",
      "features": "Features",
      "pricing": "Pricing",
      "demo": "Demo"
    },
    "resources": {
      "title": "Resources",
      "docs": "Documentation",
      "blog": "Blog",
      "changelog": "Changelog"
    },
    "company": {
      "title": "Company",
      "about": "About Us",
      "contact": "Contact",
      "careers": "Careers"
    },
    "legal": {
      "title": "Legal",
      "privacy": "Privacy",
      "terms": "Terms",
      "cookies": "Cookies"
    },
    "copyright": "© 2025 NQH Technology. All rights reserved."
  },
  "auth": {
    "login": {
      "title": "Đăng nhập",
      "email": "Email",
      "password": "Mật khẩu",
      "submit": "Đăng nhập",
      "forgotPassword": "Quên mật khẩu?",
      "noAccount": "Chưa có tài khoản?",
      "signUp": "Đăng ký ngay",
      "orContinueWith": "Hoặc tiếp tục với",
      "github": "GitHub",
      "google": "Google"
    },
    "register": {
      "title": "Đăng ký",
      "name": "Họ tên",
      "email": "Email",
      "password": "Mật khẩu",
      "confirmPassword": "Xác nhận mật khẩu",
      "submit": "Tạo tài khoản",
      "hasAccount": "Đã có tài khoản?",
      "signIn": "Đăng nhập",
      "orContinueWith": "Hoặc tiếp tục với",
      "terms": "Bằng cách đăng ký, bạn đồng ý với",
      "termsLink": "Điều khoản sử dụng",
      "and": "và",
      "privacyLink": "Chính sách bảo mật"
    }
  },
  "checkout": {
    "title": "Thanh toán",
    "plan": "Gói dịch vụ",
    "billing": "Chu kỳ thanh toán",
    "monthly": "Hàng tháng",
    "annually": "Hàng năm",
    "annualDiscount": "Tiết kiệm 2 tháng",
    "total": "Tổng cộng",
    "payNow": "Thanh toán ngay",
    "securePayment": "Thanh toán an toàn qua VNPay",
    "success": {
      "title": "Thanh toán thành công!",
      "subtitle": "Cảm ơn bạn đã đăng ký",
      "nextSteps": "Các bước tiếp theo",
      "step1": "Truy cập Dashboard để bắt đầu",
      "step2": "Kết nối GitHub repository",
      "step3": "Tạo dự án đầu tiên với AI Codegen",
      "goToDashboard": "Đến Dashboard",
      "backToHome": "Quay về trang chủ"
    }
  },
  "common": {
    "learnMore": "Tìm hiểu thêm",
    "getStarted": "Bắt đầu",
    "contactUs": "Liên hệ",
    "viewDocs": "Xem tài liệu"
  }
}
```

### 4.3 English Translations (`messages/en.json`)

```json
{
  "nav": {
    "features": "Features",
    "pricing": "Pricing",
    "docs": "Docs",
    "login": "Login",
    "register": "Sign Up"
  },
  "hero": {
    "badge": "Operating System for Software 3.0",
    "headline": "Control Plane for AI-Powered Development",
    "subheadline": "Orchestrate any AI coder under enterprise governance. Native codegen for teams without AI tools.",
    "cta": {
      "primary": "Start Free",
      "secondary": "Watch Demo",
      "tertiary": "Contact Us"
    },
    "trust": {
      "owasp": "OWASP L2",
      "vnSme": "VN SME",
      "fourGate": "4-Gate"
    }
  },
  "features": {
    "title": "One platform. Four superpowers.",
    "qualityGates": {
      "title": "Quality Gates",
      "description": "Policy-as-Code gates at every stage."
    },
    "evidenceVault": {
      "title": "Evidence Vault",
      "description": "Immutable audit trail for every decision."
    },
    "codegen": {
      "title": "AI Code Generation",
      "description": "Native AI code generation. IR-based, 4-Gate validated."
    },
    "policyGuards": {
      "title": "Policy Guards",
      "description": "OPA-powered governance. Block, warn, or allow auto."
    }
  },
  "howItWorks": {
    "title": "How It Works",
    "step1": {
      "title": "Connect",
      "description": "Link your GitHub repo. 2-minute setup."
    },
    "step2": {
      "title": "Configure",
      "description": "Choose policies and gates."
    },
    "step3": {
      "title": "Ship",
      "description": "AI validates every PR. Full audit trail."
    }
  },
  "vietnamFounders": {
    "flag": "🇻🇳",
    "title": "For Vietnamese Founders",
    "subtitle": "IR-based Codegen - From idea to first product",
    "description": "You don't need Cursor or Claude Code. AI Code Generation is built into the platform, helping you build your first product in 30 minutes* with full audit trail.",
    "disclaimer": "*Typical for simple CRUD apps. Time varies by project scope.",
    "features": {
      "templates": "Vietnamese domain templates (E-commerce, HRM, CRM)",
      "pipeline": "4-Gate Quality Pipeline",
      "compliance": "VN compliance (Social Insurance, VAT, Labor Law)",
      "support": "Vietnamese language support"
    },
    "cta": "Get Started with AI Code Generation"
  },
  "pricing": {
    "title": "Pricing",
    "subtitle": "Start free. Scale with confidence.",
    "free": {
      "name": "FREE",
      "price": "$0",
      "features": {
        "projects": "1 project",
        "gates": "5 gates",
        "support": "Community"
      },
      "cta": "Try Now"
    },
    "founder": {
      "name": "FOUNDER",
      "badge": "MOST POPULAR",
      "price": "$99/month",
      "priceNote": "(per team)",
      "features": {
        "users": "Unlimited users",
        "codegen": "AI Code Generation",
        "vault": "Evidence Vault",
        "support": "VN Support"
      },
      "cta": "Get Started"
    },
    "enterprise": {
      "name": "ENTERPRISE",
      "price": "Contact Us",
      "features": {
        "unlimited": "Unlimited",
        "onPremise": "On-premise",
        "sla": "Custom SLA",
        "dedicated": "Dedicated"
      },
      "cta": "Contact Sales"
    },
    "founderNote": "Founder Plan: For VN startups building their first product",
    "globalNote": "For global teams: Standard Plan at $30/user/month",
    "globalLink": "View Global Pricing"
  },
  "ctas": {
    "demo": {
      "icon": "👀",
      "title": "Watch Demo",
      "description": "See how it works in 3 minutes",
      "cta": "View Sample Project"
    },
    "free": {
      "icon": "🚀",
      "title": "Start Free",
      "description": "1 project, 5 gates. No credit card",
      "cta": "Create Account"
    },
    "talk": {
      "icon": "📞",
      "title": "Talk to Us",
      "description": "For SME and Enterprise",
      "cta": "Schedule"
    }
  },
  "footer": {
    "tagline": "Operating System for Software 3.0",
    "product": {
      "title": "Product",
      "features": "Features",
      "pricing": "Pricing",
      "demo": "Demo"
    },
    "resources": {
      "title": "Resources",
      "docs": "Documentation",
      "blog": "Blog",
      "changelog": "Changelog"
    },
    "company": {
      "title": "Company",
      "about": "About Us",
      "contact": "Contact",
      "careers": "Careers"
    },
    "legal": {
      "title": "Legal",
      "privacy": "Privacy",
      "terms": "Terms",
      "cookies": "Cookies"
    },
    "copyright": "© 2025 NQH Technology. All rights reserved."
  },
  "auth": {
    "login": {
      "title": "Login",
      "email": "Email",
      "password": "Password",
      "submit": "Login",
      "forgotPassword": "Forgot password?",
      "noAccount": "Don't have an account?",
      "signUp": "Sign up",
      "orContinueWith": "Or continue with",
      "github": "GitHub",
      "google": "Google"
    },
    "register": {
      "title": "Sign Up",
      "name": "Full Name",
      "email": "Email",
      "password": "Password",
      "confirmPassword": "Confirm Password",
      "submit": "Create Account",
      "hasAccount": "Already have an account?",
      "signIn": "Sign in",
      "orContinueWith": "Or continue with",
      "terms": "By signing up, you agree to our",
      "termsLink": "Terms of Service",
      "and": "and",
      "privacyLink": "Privacy Policy"
    }
  },
  "checkout": {
    "title": "Checkout",
    "plan": "Plan",
    "billing": "Billing Cycle",
    "monthly": "Monthly",
    "annually": "Annually",
    "annualDiscount": "Save 2 months",
    "total": "Total",
    "payNow": "Pay Now",
    "securePayment": "Secure payment via VNPay",
    "success": {
      "title": "Payment Successful!",
      "subtitle": "Thank you for subscribing",
      "nextSteps": "Next Steps",
      "step1": "Access Dashboard to get started",
      "step2": "Connect your GitHub repository",
      "step3": "Create your first project with AI Codegen",
      "goToDashboard": "Go to Dashboard",
      "backToHome": "Back to Home"
    }
  },
  "common": {
    "learnMore": "Learn More",
    "getStarted": "Get Started",
    "contactUs": "Contact Us",
    "viewDocs": "View Docs"
  }
}
```

---

## 5. Component Migration Plan

### 5.1 Files to Migrate (12 Total)

**Landing Components (8 files)**:

| Component | Path | Current State | Translation Keys |
|-----------|------|---------------|------------------|
| Header | `src/components/landing/Header.tsx` | Mix VN/EN | nav.* |
| Hero | `src/components/landing/Hero.tsx` | English | hero.* |
| Features | `src/components/landing/Features.tsx` | English | features.* |
| HowItWorks | `src/components/landing/HowItWorks.tsx` | English | howItWorks.* |
| VietnamFounders | `src/components/landing/VietnamFounders.tsx` | Vietnamese | vietnamFounders.* |
| Pricing | `src/components/landing/Pricing.tsx` | Mix VN/EN | pricing.* |
| CTASection | `src/components/landing/CTASection.tsx` | English | ctas.* |
| Footer | `src/components/landing/Footer.tsx` | English | footer.* |

**App Pages (4 files)**:

| Page | Path | Current State | Translation Keys |
|------|------|---------------|------------------|
| Login | `src/app/login/page.tsx` | Mix VN/EN | auth.login.* |
| Register | `src/app/register/page.tsx` | Mix VN/EN | auth.register.* |
| Checkout | `src/app/checkout/page.tsx` | Vietnamese | checkout.* |
| Checkout Success | `src/app/checkout/success/page.tsx` | Vietnamese | checkout.success.* |

### 5.2 Migration Pattern

**Before (Hardcoded):**
```tsx
export function Hero() {
  return (
    <section>
      <h1>Control Plane for AI-Powered Development</h1>
      <p>Orchestrate any AI coder under enterprise governance.</p>
      <Button>Bắt đầu miễn phí</Button>
    </section>
  );
}
```

**After (i18n):**
```tsx
'use client';

import { useTranslations } from 'next-intl';

export function Hero() {
  const t = useTranslations('hero');

  return (
    <section>
      <h1>{t('headline')}</h1>
      <p>{t('subheadline')}</p>
      <Button>{t('cta.primary')}</Button>
    </section>
  );
}
```

### 5.3 Migration Checklist

| Step | File | Status |
|------|------|--------|
| 1 | Add `'use client'` directive | Pending |
| 2 | Import `useTranslations` | Pending |
| 3 | Initialize `const t = useTranslations('namespace')` | Pending |
| 4 | Replace hardcoded strings with `t('key')` | Pending |
| 5 | Test both locales | Pending |
| 6 | Verify responsive layout with different text lengths | Pending |

---

## 6. SEO & Accessibility

### 6.1 HTML Language Attribute

```tsx
// app/layout.tsx
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi" suppressHydrationWarning>
      {/* lang attribute updated dynamically by LanguageProvider */}
      <body>{children}</body>
    </html>
  );
}
```

### 6.2 Meta Tags

```tsx
// app/layout.tsx
export const metadata: Metadata = {
  title: 'SDLC Orchestrator - Operating System for Software 3.0',
  description: 'Control plane that governs all your AI coders. Native codegen for Vietnamese SME.',
  alternates: {
    languages: {
      'vi': 'https://sdlc.nhatquangholding.com',
      'en': 'https://sdlc.nhatquangholding.com',
    },
  },
};
```

### 6.3 Accessibility for Language Toggle

```tsx
<button
  aria-label={locale === 'vi' ? 'Switch to English' : 'Chuyển sang Tiếng Việt'}
  aria-pressed={locale === 'en'}
>
  {/* Toggle content */}
</button>
```

---

## 7. Performance Considerations

### 7.1 Bundle Size

| Library | Size (gzipped) | Impact |
|---------|----------------|--------|
| next-intl | ~2KB | Minimal |
| Translation JSON (vi) | ~5KB | Acceptable |
| Translation JSON (en) | ~5KB | Acceptable |

**Total i18n overhead**: ~12KB gzipped

### 7.2 Loading Strategy

```typescript
// Lazy load non-active locale
useEffect(() => {
  async function loadMessages() {
    // Only load messages for current locale
    const msgs = await import(`@/messages/${locale}.json`);
    setMessages(msgs.default);
  }
  loadMessages();
}, [locale]);
```

### 7.3 Caching

- Translation files are statically imported at build time
- localStorage caches user preference
- No additional network requests for language switching

---

## 8. Testing Strategy

> **Note**: Test infrastructure (Jest/Playwright) is **out of scope** for Sprint 60.
> Testing will be done via manual QA. Automated tests are documented here for future sprints.

### 8.1 Manual QA Checklist (Sprint 60)

| Test Case | Expected Result |
|-----------|-----------------|
| Default locale | Page loads with `lang="vi"` |
| Click VN→EN toggle | All text switches to English |
| Click EN→VN toggle | All text switches to Vietnamese |
| Reload after toggle | Locale persists from localStorage |
| Clear localStorage, reload | Returns to default (Vietnamese) |
| Check all 12 UI files | No hardcoded strings visible |
| Check button widths | Text fits without overflow |
| Lighthouse check | Performance >80 |

### 8.2 Unit Tests (Future Sprint)

```typescript
// __tests__/i18n/translations.test.ts
import vi from '@/messages/vi.json';
import en from '@/messages/en.json';

describe('Translation files', () => {
  it('should have matching keys', () => {
    const viKeys = Object.keys(flatten(vi));
    const enKeys = Object.keys(flatten(en));
    expect(viKeys).toEqual(enKeys);
  });

  it('should not have empty values', () => {
    const viValues = Object.values(flatten(vi));
    const emptyValues = viValues.filter(v => !v || v.trim() === '');
    expect(emptyValues).toHaveLength(0);
  });
});
```

### 8.3 E2E Tests (Future Sprint)

```typescript
// e2e/i18n.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Language switching', () => {
  test('should switch from VN to EN', async ({ page }) => {
    await page.goto('/');

    // Default is Vietnamese
    await expect(page.locator('html')).toHaveAttribute('lang', 'vi');

    // Click language toggle
    await page.click('[aria-label="Switch to English"]');

    // Verify English
    await expect(page.locator('html')).toHaveAttribute('lang', 'en');
    await expect(page.getByText('Start Free')).toBeVisible();
  });

  test('should persist language preference', async ({ page }) => {
    await page.goto('/');
    await page.click('[aria-label="Switch to English"]');

    // Reload page
    await page.reload();

    // Should still be English
    await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  });
});
```

---

## 9. File Structure Summary

### 9.1 New Files to Create (5 files)

```
frontend/landing/src/
├── lib/
│   └── i18n.ts                       # i18n configuration (~30 lines)
├── app/providers/
│   └── LanguageProvider.tsx          # Context provider (~80 lines)
├── components/ui/
│   └── LanguageToggle.tsx            # Toggle button (~40 lines)
└── messages/
    ├── vi.json                       # Vietnamese translations (~500 lines)
    └── en.json                       # English translations (~500 lines)
```

### 9.2 Files to Modify (13 files)

```
frontend/landing/src/
├── app/
│   ├── layout.tsx                    # Wrap with LanguageProvider
│   ├── login/page.tsx                # Use t() for auth.login.*
│   ├── register/page.tsx             # Use t() for auth.register.*
│   └── checkout/
│       ├── page.tsx                  # Use t() for checkout.*
│       └── success/page.tsx          # Use t() for checkout.success.*
├── components/landing/
│   ├── Header.tsx                    # Add LanguageToggle, use t()
│   ├── Hero.tsx                      # Use t()
│   ├── Features.tsx                  # Use t()
│   ├── HowItWorks.tsx                # Use t()
│   ├── VietnamFounders.tsx           # Use t() for vietnamFounders.*
│   ├── Pricing.tsx                   # Use t()
│   ├── CTASection.tsx                # Use t()
│   └── Footer.tsx                    # Use t()
└── package.json                      # Already has next-intl
```

---

## 10. Implementation Acceptance Criteria

### 10.1 Day 1: Infrastructure

| Criterion | Validation |
|-----------|------------|
| next-intl installed | `npm list next-intl` shows version |
| i18n.ts configuration complete | File exists with correct exports |
| LanguageProvider implemented | Context provides locale + changeLocale |
| LanguageToggle renders | VN/EN button visible in Header |
| vi.json has all keys | ~400 lines, no empty values |
| en.json has all keys | Same keys as vi.json |
| localStorage persistence works | Locale survives page reload |
| html lang attribute updates | DOM shows `lang="vi"` or `lang="en"` |

### 10.2 Day 2: Component Migration

| Criterion | Validation |
|-----------|------------|
| All 12 UI files migrated | 8 landing components + 4 app pages |
| Both locales render correctly | Visual inspection VN and EN |
| No layout breaks | Text doesn't overflow containers |
| Button widths accommodate both | Vietnamese/English button text fits |

### 10.3 Day 3: Polish & QA

| Criterion | Validation |
|-----------|------------|
| Lighthouse Performance >80 | Post-build measurement |
| Bundle size <100KB | Build output check |
| Manual QA checklist pass | Section 8.1 all green |
| Translation completeness | 100% key coverage, no empty values |

> **Note**: E2E tests are out of scope for Sprint 60 (test infra not yet set up).

---

## 11. Design Decisions

### 11.1 SEO Strategy

| Decision | No locale-in-URL for MVP |
|----------|--------------------------|
| Rationale | Target market is Vietnamese SME (>90% expected traffic). EN locale is for UX only (investors, partners). |
| Trade-off | EN content not separately indexed by search engines. |
| Future | If EN SEO needed, migrate to `/vi/`, `/en/` routing in future sprint. |

### 11.2 Testing Scope

| Decision | Test infrastructure out of scope for Sprint 60 |
|----------|------------------------------------------------|
| Rationale | Sprint focus is i18n UI, not framework setup. Manual QA sufficient for 12 files. |
| Trade-off | No automated regression tests initially. |
| Future | Add Jest + Playwright in Sprint 61+. |

### 11.3 Server vs Client Components

| Decision | All 8 landing components become Client Components |
|----------|---------------------------------------------------|
| Rationale | `useTranslations()` is a client hook. No way to avoid `'use client'` with next-intl client-side switching. |
| Trade-off | Bundle size increases slightly (~2KB next-intl + component overhead). |
| Mitigation | Still within ~12KB i18n budget. Acceptable for UX benefit of instant language switching. |

---

## 12. G2 Gate Checklist

### 12.1 Design Review Criteria

| Criterion | Status | Reviewer |
|-----------|--------|----------|
| Technology choice documented | ✅ next-intl selected with rationale | CTO |
| Architecture diagram provided | ✅ Section 2.2 | CTO |
| Translation structure defined | ✅ Section 4 | CTO |
| Component migration plan complete | ✅ Section 5 | CTO |
| Performance budget defined | ✅ Section 7 (~12KB overhead) | CTO |
| Testing strategy documented | ✅ Section 8 (manual QA for Sprint 60) | CTO |
| Accessibility requirements | ✅ Section 6 | CTO |
| Design decisions documented | ✅ Section 11 (SEO, Testing, Components) | CTO |
| No sprint references in doc name | ✅ Frontend-I18n-Specification.md | CTO |

### 12.2 G2 Approval Requirements

```yaml
Required Artifacts:
  ✅ Technical Specification Document (this document)
  ✅ Technology choice rationale (Section 2.1)
  ✅ Architecture diagram (Section 2.2)
  ✅ Translation file structure (Section 4)
  ✅ Component migration plan (Section 5)
  ✅ Testing strategy (Section 8)
  ✅ Design decisions (Section 11)

Approvers:
  - [x] CTO - APPROVED (Dec 27, 2025)
  - [x] Frontend Lead - APPROVED (Dec 27, 2025)
```

---

## 13. Document Control

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Status | G2 APPROVED (Dec 27, 2025) |
| Author | AI Development Partner |
| Created | December 27, 2025 |
| Last Updated | December 27, 2025 |
| Depends On | Landing-Page-Design-Specification v1.1.0 |
| Gate | G2 (Design Ready) |

### Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Dec 27, 2025 | Initial i18n technical specification |

---

## 14. References

- [next-intl Documentation](https://next-intl-docs.vercel.app/)
- [SDLC Framework 5.1.2](../../SDLC-Enterprise-Framework/)
- [Landing Page Design Specification](../09-UI-Design/Landing-Page-Design-Specification.md)
- [Sprint 60 Plan](../../../04-build/02-Sprint-Plans/SPRINT-60-I18N-LOCALIZATION.md)
