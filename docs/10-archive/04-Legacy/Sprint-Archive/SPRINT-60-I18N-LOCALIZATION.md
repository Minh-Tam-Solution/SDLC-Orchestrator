# SPRINT-60: Internationalization (i18n) - VN/EN Language Toggle
## Marketing & Growth | Multi-Language Support

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-60 |
| **Epic** | Marketing & Growth |
| **Duration** | 3 days (Dec 28-30, 2025) |
| **Status** | IN PROGRESS - G2 APPROVED (Dec 27, 2025) |
| **Priority** | P1 Should Have |
| **Dependencies** | Sprint 59 complete |
| **Framework** | SDLC 6.1.0 Universal Framework |
| **Design Spec** | [Frontend-I18n-Specification.md](../../02-design/14-Technical-Specs/Frontend-I18n-Specification.md) |

---

## Sprint Goal

Implement VN/EN language toggle for the landing page to support both Vietnamese and English-speaking users, enabling market expansion beyond Vietnam.

---

## Sprint Objectives

| Day | Focus | Deliverables | Effort |
|-----|-------|--------------|--------|
| Day 1 | i18n Infrastructure | next-intl setup, translation files, language context | 6h |
| Day 2 | Component Translation | Translate all landing components (12 files) | 8h |
| Day 3 | Language Toggle UI + Testing | Header toggle, persistence, QA | 4h |

---

## Technical Approach

### Option Analysis

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **next-intl** | Native Next.js App Router support, lightweight | Newer library | SELECTED |
| react-i18next | Mature, widely used | Complex setup with App Router | Rejected |
| Custom context | Full control | Maintenance burden | Rejected |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Language Toggle (Header)                      │
│                         VN | EN                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LanguageProvider                             │
│                  (React Context + localStorage)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌─────────┐     ┌─────────┐     ┌─────────┐
        │  vi.json │     │  en.json │     │  ...    │
        │ messages │     │ messages │     │         │
        └─────────┘     └─────────┘     └─────────┘
```

---

## Feature 1: i18n Infrastructure Setup

### Files to Create (per Design Spec Section 9.1)

| File | Purpose | Est. Lines |
|------|---------|------------|
| `frontend/landing/src/lib/i18n.ts` | i18n configuration and hooks | ~30 |
| `frontend/landing/src/messages/vi.json` | Vietnamese translations | ~500 |
| `frontend/landing/src/messages/en.json` | English translations | ~500 |
| `frontend/landing/src/app/providers/LanguageProvider.tsx` | Language context provider | ~80 |
| `frontend/landing/src/components/ui/LanguageToggle.tsx` | VN/EN toggle component | ~40 |

### Package Installation

```bash
npm install next-intl
```

### i18n Configuration (`frontend/landing/src/lib/i18n.ts`)

```typescript
// See Design Spec Section 3.1 for full implementation
export const locales = ['vi', 'en'] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = 'vi';

export const localeNames: Record<Locale, string> = {
  vi: 'Tiếng Việt',
  en: 'English',
};
```

### Language Provider (`frontend/landing/src/app/providers/LanguageProvider.tsx`)

```typescript
// See Design Spec Section 3.2 for full implementation
'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { NextIntlClientProvider } from 'next-intl';
import { Locale, defaultLocale } from '@/lib/i18n';

interface LanguageContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

const LanguageContext = createContext<LanguageContextType | null>(null);

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error('useLanguage must be used within LanguageProvider');
  return context;
}

export function LanguageProvider({
  children,
  initialLocale = defaultLocale
}: {
  children: React.ReactNode;
  initialLocale?: Locale;
}) {
  const [locale, setLocaleState] = useState<Locale>(initialLocale);
  const [messages, setMessages] = useState<Record<string, unknown>>({});

  useEffect(() => {
    // Load saved language from localStorage
    const saved = localStorage.getItem('sdlc-locale') as Locale;
    if (saved && ['vi', 'en'].includes(saved)) {
      setLocaleState(saved);
    }
  }, []);

  useEffect(() => {
    // Load messages for current locale
    import(`@/messages/${locale}.json`).then((m) => setMessages(m.default));
    localStorage.setItem('sdlc-locale', locale);
    document.documentElement.lang = locale;
  }, [locale]);

  return (
    <LanguageContext.Provider value={{ locale, setLocale: setLocaleState }}>
      <NextIntlClientProvider locale={locale} messages={messages}>
        {children}
      </NextIntlClientProvider>
    </LanguageContext.Provider>
  );
}
```

---

## Feature 2: Translation Files

### Vietnamese Messages (`frontend/landing/src/messages/vi.json`)

```json
{
  "header": {
    "features": "Tính năng",
    "pricing": "Bảng giá",
    "docs": "Tài liệu",
    "signIn": "Đăng nhập",
    "startFree": "Bắt đầu miễn phí"
  },
  "hero": {
    "badge": "Hệ điều hành cho Software 3.0",
    "title": "Control Plane cho {highlight}",
    "titleHighlight": "AI-Powered Development",
    "subtitle": "Điều phối mọi AI coder dưới quy chế doanh nghiệp. Native codegen cho team chưa có AI tools.",
    "cta": {
      "startFree": "Bắt đầu miễn phí",
      "watchDemo": "Xem Demo",
      "talkToUs": "Liên hệ"
    },
    "badges": {
      "owasp": "OWASP ASVS L2 Compliant",
      "vietnam": "Dành cho SME Việt Nam",
      "pipeline": "4-Gate Quality Pipeline"
    }
  },
  "features": {
    "title": "Một nền tảng. Bốn siêu năng lực.",
    "subtitle": "Mọi thứ bạn cần để quản trị phát triển AI với sự tự tin.",
    "qualityGates": {
      "title": "Quality Gates",
      "description": "Policy-as-Code gates ở mọi giai đoạn.",
      "highlight": "G0 → G4 với 110+ chính sách có sẵn."
    },
    "evidenceVault": {
      "title": "Evidence Vault",
      "description": "Audit trail bất biến cho mọi quyết định.",
      "highlight": "SHA256 integrity, 8-state lifecycle."
    },
    "aiCodegen": {
      "title": "AI Code Generation",
      "description": "Sinh code AI native.",
      "highlight": "Multi-provider, 4-Gate validated."
    },
    "policyGuards": {
      "title": "Policy Guards",
      "description": "Quản trị bằng OPA.",
      "highlight": "Block, warn, hoặc allow tự động."
    }
  },
  "howItWorks": {
    "title": "Bắt đầu trong vài phút",
    "subtitle": "Từ zero đến AI development có quản trị chỉ trong ba bước đơn giản.",
    "step1": {
      "title": "Kết nối",
      "description": "Liên kết GitHub repository của bạn.",
      "highlight": "Setup trong 2 phút."
    },
    "step2": {
      "title": "Cấu hình",
      "description": "Chọn policies và gates.",
      "highlight": "Templates cho các use case phổ biến."
    },
    "step3": {
      "title": "Ship",
      "description": "AI validates mọi PR.",
      "highlight": "Full audit trail, enterprise ready."
    }
  },
  "vietnamFounders": {
    "badge": "Dành cho Founders Việt Nam",
    "title": "AI Code Generation",
    "subtitle": "Từ ý tưởng đến sản phẩm đầu tiên",
    "description": "Bạn không cần Cursor hay Claude Code. AI Codegen tích hợp sẵn trong platform, giúp bạn build sản phẩm đầu tiên trong {time} với full audit trail.",
    "time": "~30 phút",
    "note": "*Typical for simple CRUD apps. Time varies by project scope.",
    "templates": {
      "title": "Vietnamese Domain Templates",
      "description": "E-commerce, HRM, CRM - built for VN market"
    },
    "pipeline": {
      "title": "4-Gate Quality Pipeline",
      "description": "Syntax → Security → Context → Tests"
    },
    "compliance": {
      "title": "VN Compliance Ready",
      "description": "BHXH, VAT, Luật Lao động templates"
    },
    "support": {
      "title": "Hỗ trợ tiếng Việt",
      "description": "Vietnamese support via Email + Discord"
    },
    "cta": "Bắt đầu ngay"
  },
  "pricing": {
    "title": "Bắt đầu miễn phí. Scale với tự tin.",
    "subtitle": "Chọn gói phù hợp với team của bạn. Nâng cấp bất kỳ lúc nào.",
    "mostPopular": "Phổ biến nhất",
    "free": {
      "name": "Free",
      "price": "0 VND",
      "description": "Hoàn hảo cho developer cá nhân và học tập",
      "features": [
        "1 dự án",
        "5 gates (G0-G4)",
        "1GB Evidence Vault",
        "Community support",
        "Basic analytics"
      ],
      "cta": "Bắt đầu miễn phí"
    },
    "founder": {
      "name": "Founder",
      "price": "2.5M VND",
      "priceNote": "/team/tháng (~$99)",
      "description": "Cho startup Việt Nam xây dựng sản phẩm đầu tiên",
      "features": [
        "Unlimited team members",
        "1 product (multiple repos)",
        "AI Code Generation",
        "10GB Evidence Vault",
        "5 policy packs có sẵn",
        "500 AI requests/tháng",
        "Email + Discord support",
        "99.5% SLA"
      ],
      "cta": "Bắt đầu ngay"
    },
    "enterprise": {
      "name": "Enterprise",
      "price": "Liên hệ",
      "description": "Cho tổ chức lớn với nhu cầu nâng cao",
      "features": [
        "Unlimited everything",
        "On-premise deployment",
        "Custom SLA (99.99%)",
        "Dedicated support team",
        "SSO (SAML/OIDC)",
        "Custom integrations",
        "7-year audit logs"
      ],
      "cta": "Liên hệ Sales"
    },
    "founderNote": "Founder Plan: Thiết kế cho startup Việt Nam xây dựng sản phẩm đầu tiên với AI-powered development.",
    "globalNote": "Cho global teams: Standard Plan $30/user/month.",
    "contactSetup": "Liên hệ để setup"
  },
  "cta": {
    "title": "Sẵn sàng chuyển đổi phát triển của bạn?",
    "subtitle": "Chọn cách bạn muốn bắt đầu với SDLC Orchestrator.",
    "demo": {
      "title": "Xem Demo",
      "description": "Xem cách hoạt động trong 3 phút",
      "cta": "View Sample Project"
    },
    "startFree": {
      "title": "Bắt đầu miễn phí",
      "description": "1 project, 5 gates. Không cần credit card.",
      "cta": "Tạo tài khoản"
    },
    "talkToUs": {
      "title": "Liên hệ",
      "description": "Cho SME và Enterprise",
      "cta": "Đặt lịch gọi"
    }
  },
  "footer": {
    "tagline": "Hệ điều hành cho Software 3.0",
    "builtBy": "Built by NQH Technology",
    "product": {
      "title": "Sản phẩm",
      "features": "Tính năng",
      "pricing": "Bảng giá",
      "docs": "Tài liệu",
      "changelog": "Changelog"
    },
    "company": {
      "title": "Công ty",
      "about": "Về chúng tôi",
      "blog": "Blog",
      "careers": "Tuyển dụng",
      "contact": "Liên hệ"
    },
    "legal": {
      "title": "Pháp lý",
      "privacy": "Chính sách bảo mật",
      "terms": "Điều khoản dịch vụ",
      "security": "Bảo mật"
    },
    "connect": {
      "title": "Kết nối"
    },
    "copyright": "© 2025 SDLC Orchestrator. All rights reserved."
  },
  "auth": {
    "login": {
      "title": "Đăng nhập",
      "subtitle": "Chào mừng trở lại! Đăng nhập để tiếp tục.",
      "email": "Email",
      "password": "Mật khẩu",
      "submit": "Đăng nhập",
      "submitting": "Đang xử lý...",
      "forgotPassword": "Quên mật khẩu?",
      "noAccount": "Chưa có tài khoản?",
      "register": "Đăng ký",
      "or": "hoặc",
      "continueWithGithub": "Tiếp tục với GitHub",
      "continueWithGoogle": "Tiếp tục với Google"
    },
    "register": {
      "title": "Tạo tài khoản",
      "subtitle": "Bắt đầu miễn phí. Không cần credit card.",
      "fullName": "Họ và tên",
      "email": "Email",
      "password": "Mật khẩu",
      "confirmPassword": "Xác nhận mật khẩu",
      "submit": "Đăng ký",
      "submitting": "Đang tạo tài khoản...",
      "hasAccount": "Đã có tài khoản?",
      "login": "Đăng nhập",
      "or": "hoặc",
      "continueWithGithub": "Tiếp tục với GitHub",
      "continueWithGoogle": "Tiếp tục với Google",
      "terms": "Bằng việc đăng ký, bạn đồng ý với",
      "termsLink": "Điều khoản dịch vụ",
      "and": "và",
      "privacyLink": "Chính sách bảo mật"
    }
  },
  "checkout": {
    "orderSummary": "Tóm tắt đơn hàng",
    "payment": "Thanh toán",
    "securePayment": "Thanh toán an toàn qua VNPay",
    "monthly": "Hàng tháng",
    "annual": "Hàng năm",
    "annualDiscount": "-17%",
    "includes": "Bao gồm:",
    "total": "Tổng cộng",
    "payButton": "Thanh toán {amount}",
    "processing": "Đang xử lý...",
    "redirectNote": "Bạn sẽ được chuyển đến trang thanh toán VNPay để hoàn tất giao dịch.",
    "termsNote": "Bằng việc thanh toán, bạn đồng ý với",
    "termsLink": "Điều khoản dịch vụ",
    "and": "và",
    "privacyLink": "Chính sách bảo mật",
    "backToPricing": "← Quay lại trang giá",
    "success": {
      "title": "Thanh toán thành công!",
      "subtitle": "Cảm ơn bạn đã đăng ký SDLC Orchestrator",
      "transactionId": "Mã giao dịch",
      "plan": "Gói",
      "amount": "Số tiền",
      "nextSteps": "Bước tiếp theo:",
      "step1": "Truy cập Dashboard để bắt đầu",
      "step2": "Kết nối GitHub repository",
      "step3": "Tạo dự án đầu tiên với AI Codegen",
      "gotoDashboard": "Vào Dashboard",
      "viewGuide": "Xem hướng dẫn",
      "needHelp": "Cần hỗ trợ?",
      "contactUs": "Liên hệ chúng tôi"
    },
    "failed": {
      "title": "Thanh toán thất bại",
      "subtitle": "Đã xảy ra lỗi trong quá trình thanh toán",
      "description": "Thanh toán của bạn không thành công. Vui lòng thử lại hoặc liên hệ hỗ trợ.",
      "tryAgain": "Thử lại",
      "contactSupport": "Liên hệ hỗ trợ"
    },
    "pending": {
      "title": "Đang xử lý thanh toán...",
      "subtitle": "Vui lòng đợi trong giây lát",
      "description": "Thanh toán của bạn đang được xử lý. Quá trình này có thể mất vài giây."
    }
  }
}
```

### English Messages (`frontend/landing/src/messages/en.json`)

```json
{
  "header": {
    "features": "Features",
    "pricing": "Pricing",
    "docs": "Docs",
    "signIn": "Sign In",
    "startFree": "Start Free"
  },
  "hero": {
    "badge": "Operating System for Software 3.0",
    "title": "Control Plane for {highlight}",
    "titleHighlight": "AI-Powered Development",
    "subtitle": "Orchestrate any AI coder under enterprise governance. Native codegen for teams without AI tools.",
    "cta": {
      "startFree": "Start Free",
      "watchDemo": "Watch Demo",
      "talkToUs": "Talk to Us"
    },
    "badges": {
      "owasp": "OWASP ASVS L2 Compliant",
      "vietnam": "Built for Vietnamese SME",
      "pipeline": "4-Gate Quality Pipeline"
    }
  },
  "features": {
    "title": "One platform. Four superpowers.",
    "subtitle": "Everything you need to govern AI-powered development with confidence.",
    "qualityGates": {
      "title": "Quality Gates",
      "description": "Policy-as-Code gates at every stage.",
      "highlight": "G0 → G4 with 110+ policies built-in."
    },
    "evidenceVault": {
      "title": "Evidence Vault",
      "description": "Immutable audit trail for every decision.",
      "highlight": "SHA256 integrity, 8-state lifecycle."
    },
    "aiCodegen": {
      "title": "AI Code Generation",
      "description": "Native AI code generation.",
      "highlight": "Multi-provider, 4-Gate validated."
    },
    "policyGuards": {
      "title": "Policy Guards",
      "description": "OPA-powered governance.",
      "highlight": "Block, warn, or allow automatically."
    }
  },
  "howItWorks": {
    "title": "Get started in minutes",
    "subtitle": "From zero to governed AI development in three simple steps.",
    "step1": {
      "title": "Connect",
      "description": "Link your GitHub repository.",
      "highlight": "2-minute setup."
    },
    "step2": {
      "title": "Configure",
      "description": "Choose policies and gates.",
      "highlight": "Templates for common use cases."
    },
    "step3": {
      "title": "Ship",
      "description": "AI validates every PR.",
      "highlight": "Full audit trail, enterprise ready."
    }
  },
  "vietnamFounders": {
    "badge": "For Vietnamese Founders",
    "title": "AI Code Generation",
    "subtitle": "From idea to first product",
    "description": "You don't need Cursor or Claude Code. AI Codegen is built into the platform, helping you build your first product in {time} with full audit trail.",
    "time": "~30 minutes",
    "note": "*Typical for simple CRUD apps. Time varies by project scope.",
    "templates": {
      "title": "Vietnamese Domain Templates",
      "description": "E-commerce, HRM, CRM - built for VN market"
    },
    "pipeline": {
      "title": "4-Gate Quality Pipeline",
      "description": "Syntax → Security → Context → Tests"
    },
    "compliance": {
      "title": "VN Compliance Ready",
      "description": "BHXH, VAT, Labor Law templates"
    },
    "support": {
      "title": "Vietnamese Support",
      "description": "Vietnamese support via Email + Discord"
    },
    "cta": "Get Started"
  },
  "pricing": {
    "title": "Start free. Scale with confidence.",
    "subtitle": "Choose the plan that fits your team. Upgrade anytime as you grow.",
    "mostPopular": "Most Popular",
    "free": {
      "name": "Free",
      "price": "$0",
      "description": "Perfect for solo developers and learners",
      "features": [
        "1 project",
        "5 gates (G0-G4)",
        "1GB Evidence Vault",
        "Community support",
        "Basic analytics"
      ],
      "cta": "Start Free"
    },
    "founder": {
      "name": "Founder",
      "price": "$99",
      "priceNote": "/team/month",
      "description": "For Vietnamese startups building their first product",
      "features": [
        "Unlimited team members",
        "1 product (multiple repos)",
        "AI Code Generation",
        "10GB Evidence Vault",
        "5 built-in policy packs",
        "500 AI requests/month",
        "Email + Discord support",
        "99.5% SLA"
      ],
      "cta": "Start Now"
    },
    "enterprise": {
      "name": "Enterprise",
      "price": "Custom",
      "description": "For large organizations with advanced needs",
      "features": [
        "Unlimited everything",
        "On-premise deployment",
        "Custom SLA (99.99%)",
        "Dedicated support team",
        "SSO (SAML/OIDC)",
        "Custom integrations",
        "7-year audit logs"
      ],
      "cta": "Contact Sales"
    },
    "founderNote": "Founder Plan: Designed for Vietnamese startups building their first product with AI-powered development.",
    "globalNote": "For global teams: Standard Plan at $30/user/month.",
    "contactSetup": "Contact us for setup"
  },
  "cta": {
    "title": "Ready to transform your development?",
    "subtitle": "Choose how you want to get started with SDLC Orchestrator.",
    "demo": {
      "title": "Watch Demo",
      "description": "See how it works in 3 minutes",
      "cta": "View Sample Project"
    },
    "startFree": {
      "title": "Start Free",
      "description": "1 project, 5 gates. No credit card.",
      "cta": "Create Account"
    },
    "talkToUs": {
      "title": "Talk to Us",
      "description": "For SME and Enterprise",
      "cta": "Schedule Call"
    }
  },
  "footer": {
    "tagline": "Operating System for Software 3.0",
    "builtBy": "Built by NQH Technology",
    "product": {
      "title": "Product",
      "features": "Features",
      "pricing": "Pricing",
      "docs": "Docs",
      "changelog": "Changelog"
    },
    "company": {
      "title": "Company",
      "about": "About",
      "blog": "Blog",
      "careers": "Careers",
      "contact": "Contact"
    },
    "legal": {
      "title": "Legal",
      "privacy": "Privacy Policy",
      "terms": "Terms of Service",
      "security": "Security"
    },
    "connect": {
      "title": "Connect"
    },
    "copyright": "© 2025 SDLC Orchestrator. All rights reserved."
  },
  "auth": {
    "login": {
      "title": "Sign In",
      "subtitle": "Welcome back! Sign in to continue.",
      "email": "Email",
      "password": "Password",
      "submit": "Sign In",
      "submitting": "Signing in...",
      "forgotPassword": "Forgot password?",
      "noAccount": "Don't have an account?",
      "register": "Register",
      "or": "or",
      "continueWithGithub": "Continue with GitHub",
      "continueWithGoogle": "Continue with Google"
    },
    "register": {
      "title": "Create Account",
      "subtitle": "Start free. No credit card required.",
      "fullName": "Full Name",
      "email": "Email",
      "password": "Password",
      "confirmPassword": "Confirm Password",
      "submit": "Create Account",
      "submitting": "Creating account...",
      "hasAccount": "Already have an account?",
      "login": "Sign In",
      "or": "or",
      "continueWithGithub": "Continue with GitHub",
      "continueWithGoogle": "Continue with Google",
      "terms": "By registering, you agree to our",
      "termsLink": "Terms of Service",
      "and": "and",
      "privacyLink": "Privacy Policy"
    }
  },
  "checkout": {
    "orderSummary": "Order Summary",
    "payment": "Payment",
    "securePayment": "Secure payment via VNPay",
    "monthly": "Monthly",
    "annual": "Annual",
    "annualDiscount": "-17%",
    "includes": "Includes:",
    "total": "Total",
    "payButton": "Pay {amount}",
    "processing": "Processing...",
    "redirectNote": "You will be redirected to VNPay to complete the transaction.",
    "termsNote": "By paying, you agree to our",
    "termsLink": "Terms of Service",
    "and": "and",
    "privacyLink": "Privacy Policy",
    "backToPricing": "← Back to pricing",
    "success": {
      "title": "Payment Successful!",
      "subtitle": "Thank you for subscribing to SDLC Orchestrator",
      "transactionId": "Transaction ID",
      "plan": "Plan",
      "amount": "Amount",
      "nextSteps": "Next Steps:",
      "step1": "Access Dashboard to get started",
      "step2": "Connect GitHub repository",
      "step3": "Create your first project with AI Codegen",
      "gotoDashboard": "Go to Dashboard",
      "viewGuide": "View Guide",
      "needHelp": "Need help?",
      "contactUs": "Contact us"
    },
    "failed": {
      "title": "Payment Failed",
      "subtitle": "An error occurred during payment",
      "description": "Your payment was not successful. Please try again or contact support.",
      "tryAgain": "Try Again",
      "contactSupport": "Contact Support"
    },
    "pending": {
      "title": "Processing Payment...",
      "subtitle": "Please wait a moment",
      "description": "Your payment is being processed. This may take a few seconds."
    }
  }
}
```

---

## Feature 3: Language Toggle Component

### Toggle UI (`frontend/landing/src/components/ui/LanguageToggle.tsx`)

```tsx
'use client';

import { useLanguage } from '@/lib/i18n/LanguageProvider';
import { Button } from '@/components/ui/button';
import { Locale } from '@/lib/i18n';

const localeLabels: Record<Locale, string> = {
  vi: 'VN',
  en: 'EN',
};

export function LanguageToggle() {
  const { locale, setLocale } = useLanguage();

  return (
    <div className="flex items-center gap-1 border rounded-md p-0.5 bg-muted/50">
      {(['vi', 'en'] as Locale[]).map((loc) => (
        <Button
          key={loc}
          variant={locale === loc ? 'default' : 'ghost'}
          size="sm"
          className="h-7 px-2 text-xs font-medium"
          onClick={() => setLocale(loc)}
        >
          {localeLabels[loc]}
        </Button>
      ))}
    </div>
  );
}
```

### Header Integration

```tsx
// In Header.tsx
import { LanguageToggle } from '@/components/ui/language-toggle';

// Add next to Sign In button
<div className="hidden md:flex items-center gap-3">
  <LanguageToggle />
  <Button variant="ghost" size="sm" asChild>
    <Link href="/login">{t('header.signIn')}</Link>
  </Button>
  ...
</div>
```

---

## Feature 4: Component Migration

### Files to Update

| Component | File | Priority |
|-----------|------|----------|
| Header | `components/landing/Header.tsx` | P0 |
| Hero | `components/landing/Hero.tsx` | P0 |
| Features | `components/landing/Features.tsx` | P0 |
| HowItWorks | `components/landing/HowItWorks.tsx` | P0 |
| VietnamFounders | `components/landing/VietnamFounders.tsx` | P0 |
| Pricing | `components/landing/Pricing.tsx` | P0 |
| CTASection | `components/landing/CTASection.tsx` | P0 |
| Footer | `components/landing/Footer.tsx` | P0 |
| Login | `app/login/page.tsx` | P1 |
| Register | `app/register/page.tsx` | P1 |
| Checkout | `app/checkout/page.tsx` | P1 |
| Checkout Success | `app/checkout/success/page.tsx` | P1 |

### Migration Pattern

**Before (Hardcoded):**
```tsx
<h1>Control Plane for AI-Powered Development</h1>
```

**After (i18n):**
```tsx
import { useTranslations } from 'next-intl';

export function Hero() {
  const t = useTranslations('hero');

  return (
    <h1>
      {t.rich('title', {
        highlight: (chunks) => <span className="text-primary">{chunks}</span>
      })}
    </h1>
  );
}
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Language switch latency | <100ms |
| Translation coverage | 100% |
| localStorage persistence | Works |
| SEO lang attribute | Updated |
| No layout shift | CLS < 0.1 |

---

## Implementation Checklist

### Day 1: Infrastructure

- [ ] Install next-intl package
- [ ] Create i18n configuration (`lib/i18n/index.ts`)
- [ ] Create LanguageProvider
- [ ] Create vi.json translation file
- [ ] Create en.json translation file
- [ ] Create LanguageToggle component
- [ ] Update layout.tsx with LanguageProvider

### Day 2: Component Translation

- [ ] Migrate Header.tsx
- [ ] Migrate Hero.tsx
- [ ] Migrate Features.tsx
- [ ] Migrate HowItWorks.tsx
- [ ] Migrate VietnamFounders.tsx
- [ ] Migrate Pricing.tsx
- [ ] Migrate CTASection.tsx
- [ ] Migrate Footer.tsx
- [ ] Migrate login/page.tsx
- [ ] Migrate register/page.tsx
- [ ] Migrate checkout/page.tsx
- [ ] Migrate checkout/success/page.tsx

### Day 3: Polish & Testing

- [ ] Add LanguageToggle to Header
- [ ] Test localStorage persistence
- [ ] Test all pages in VN mode
- [ ] Test all pages in EN mode
- [ ] Verify SEO meta tags update
- [ ] Rebuild and deploy
- [ ] QA sign-off

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Translation missing | Fallback to English |
| Layout shift on language change | Pre-render both locales |
| SEO impact | Dynamic lang attribute |
| Bundle size increase | Split JSON files by route |

---

## Files Summary

| Category | Files | Lines (Est.) |
|----------|-------|--------------|
| i18n Infrastructure | 4 | ~200 |
| Translation Files | 2 | ~600 |
| Component Updates | 12 | ~400 |
| **Total** | **18** | **~1,200** |

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Last Updated** | December 27, 2025 |
| **Owner** | Frontend Lead |
| **Approved By** | CTO (Pending) |
