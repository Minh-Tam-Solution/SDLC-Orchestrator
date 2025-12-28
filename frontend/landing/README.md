# SDLC Orchestrator Landing Page

Next.js 14 landing page for SDLC Orchestrator with authentication (email/password + OAuth).

**Sprint**: 60 - i18n Localization
**Framework**: SDLC 5.1.2 Universal Framework

## Features

- Registration & Login with email/password
- OAuth authentication (GitHub + Google)
- VNPay payment integration
- Mixpanel analytics
- **i18n Support** (Vietnamese/English) - Sprint 60

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## Environment Variables

Create a `.env.local` file with the following variables:

```env
# API URL
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Mixpanel Analytics (optional)
NEXT_PUBLIC_MIXPANEL_TOKEN=your_mixpanel_token
```

## OAuth Setup (Sprint 59)

OAuth is handled server-side by the FastAPI backend. The frontend only needs to:

1. Call `GET /auth/oauth/{provider}/authorize` to get the authorization URL
2. Redirect user to the authorization URL
3. Handle the callback at `/auth/callback` with the code from the provider

### Frontend OAuth Flow

```
1. User clicks "GitHub" or "Google" button
2. Frontend calls backend: GET /api/v1/auth/oauth/github/authorize
3. Backend returns: { authorization_url, state }
4. Frontend stores state in sessionStorage
5. Frontend redirects to authorization_url
6. User authenticates with provider
7. Provider redirects to /auth/callback?code=xxx&state=xxx
8. Callback page exchanges code: POST /api/v1/auth/oauth/github/callback
9. Backend returns JWT tokens
10. Frontend stores tokens, redirects to dashboard
```

### Backend OAuth Configuration

The backend requires these environment variables:

```env
# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# OAuth Redirect URL (frontend callback page)
OAUTH_REDIRECT_URL=http://localhost:3000/auth/callback
```

### Setting up OAuth Applications

#### GitHub OAuth App

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Fill in:
   - Application name: SDLC Orchestrator (Dev)
   - Homepage URL: http://localhost:3000
   - Authorization callback URL: http://localhost:3000/auth/callback
4. Copy Client ID and generate Client Secret

#### Google OAuth Client

1. Go to Google Cloud Console → APIs & Services → Credentials
2. Create OAuth 2.0 Client ID (Web application)
3. Add authorized redirect URI: http://localhost:3000/auth/callback
4. Copy Client ID and Client Secret

## i18n (Internationalization) - Sprint 60

### Supported Languages

- Vietnamese (vi) - Default
- English (en)

### Quick Start

```tsx
'use client';

import { useTranslations } from 'next-intl';

export function MyComponent() {
  const t = useTranslations('myNamespace');
  return <h1>{t('title')}</h1>;
}
```

### Translation Files

- `src/messages/vi.json` - Vietnamese (286 keys)
- `src/messages/en.json` - English (286 keys)

### Language Toggle

The language toggle is in the Header component. Users can switch between VN/EN.

Language preference is saved to `localStorage` (`sdlc-locale` key) and persists across sessions.

### Developer Guide

See [docs/I18N-DEVELOPER-GUIDE.md](docs/I18N-DEVELOPER-GUIDE.md) for:
- Adding new translations
- Common patterns (interpolation, arrays, dynamic keys)
- Troubleshooting

## Project Structure

```
src/
├── app/
│   ├── auth/
│   │   └── callback/     # OAuth callback handler
│   ├── checkout/         # VNPay payment flow
│   ├── login/            # Login page with OAuth
│   ├── register/         # Registration page with OAuth
│   ├── providers/
│   │   └── LanguageProvider.tsx  # i18n context
│   └── page.tsx          # Landing page
├── components/
│   ├── landing/          # Landing page components
│   └── ui/
│       └── LanguageToggle.tsx    # VN/EN toggle
├── lib/
│   ├── api.ts            # API client
│   ├── analytics.ts      # Mixpanel tracking
│   └── i18n.ts           # i18n configuration
└── messages/
    ├── vi.json           # Vietnamese translations
    └── en.json           # English translations
```
