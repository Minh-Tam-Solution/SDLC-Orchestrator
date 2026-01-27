"""
Next.js SaaS Template - Production-ready SaaS boilerplate with payments

SDLC Framework Compliance:
- Framework: SDLC 5.2.0 (7-Pillar + AI Governance Principles)
- Pillar 3: Build Phase - Template-Based Code Generation
- AI Governance Principle 4: Deterministic Intermediate Representations
- Methodology: Template Method pattern for SaaS app scaffolding

Purpose:
Next.js 14 App Router + Stripe + Subscription Management template.
Generates production-ready SaaS boilerplate with:
- Authentication (NextAuth.js with multiple providers)
- Payment integration (Stripe subscriptions)
- Database (Prisma + PostgreSQL)
- UI Components (Tailwind CSS + shadcn/ui)
- Email notifications (Resend)
- Admin dashboard
- Usage tracking & billing

Related ADRs:
- ADR-022: IR-Based Codegen with 4-Gate Quality Pipeline
- ADR-040: App Builder Integration - Competitive Necessity

Sprint: 106 - App Builder Integration (MVP)
Date: January 28, 2026
Owner: Backend Team
Status: ACTIVE
"""

from typing import List, Dict
from pathlib import Path
import json

from backend.app.schemas.codegen.template_blueprint import (
    TemplateBlueprint,
    TemplateType,
    Entity,
    APIRoute,
    Page,
    EntityField
)
from .base_template import BaseTemplate, GeneratedFile


class NextJSSaaSTemplate(BaseTemplate):
    """
    Next.js SaaS Template with Stripe integration.

    Tech Stack:
    - Next.js 14 (App Router, React Server Components)
    - TypeScript (strict mode)
    - Prisma (PostgreSQL ORM)
    - NextAuth.js (Authentication with GitHub, Google, Email)
    - Stripe (Subscriptions, Webhooks, Customer Portal)
    - Tailwind CSS + shadcn/ui (UI Components)
    - Resend (Transactional emails)
    - Zod (Validation)

    Features:
    - Multi-tier subscription plans (Free, Pro, Enterprise)
    - Usage-based billing (optional)
    - Customer portal (manage subscriptions)
    - Admin dashboard (user management, analytics)
    - Webhook handling (Stripe events)
    - Email notifications (welcome, payment success, subscription changes)
    """

    template_type = TemplateType.NEXTJS_SAAS
    template_name = "Next.js SaaS"
    template_version = "1.0.0"

    default_tech_stack = [
        "nextjs",
        "react",
        "typescript",
        "prisma",
        "postgresql",
        "nextauth",
        "stripe",
        "tailwind",
        "shadcn-ui",
        "resend",
        "zod"
    ]

    required_env_vars = [
        "DATABASE_URL",
        "NEXTAUTH_URL",
        "NEXTAUTH_SECRET",
        "GITHUB_CLIENT_ID",
        "GITHUB_CLIENT_SECRET",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY",
        "RESEND_API_KEY",
        "NEXT_PUBLIC_APP_URL"
    ]

    def get_file_structure(self, blueprint: TemplateBlueprint) -> Dict[str, str]:
        """Define Next.js SaaS project structure"""
        return {
            "src/": "Source code root",
            "src/app/": "Next.js App Router pages",
            "src/app/api/": "API routes",
            "src/app/api/auth/": "NextAuth.js routes",
            "src/app/api/webhooks/": "Stripe webhook handlers",
            "src/app/(marketing)/": "Marketing pages (public)",
            "src/app/(dashboard)/": "Dashboard pages (authenticated)",
            "src/app/(admin)/": "Admin pages (admin role only)",
            "src/components/": "React components",
            "src/components/ui/": "shadcn/ui components",
            "src/components/marketing/": "Marketing components",
            "src/components/dashboard/": "Dashboard components",
            "src/lib/": "Utility functions",
            "src/lib/stripe/": "Stripe utilities",
            "src/lib/email/": "Email templates and sender",
            "src/hooks/": "React hooks",
            "src/types/": "TypeScript type definitions",
            "prisma/": "Prisma schema and migrations",
            "public/": "Static assets",
        }

    def generate_config_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate configuration files for Next.js SaaS"""
        files = []

        # package.json
        package_json = {
            "name": blueprint.project_name.lower().replace(" ", "-"),
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "prisma generate && next build",
                "start": "next start",
                "lint": "next lint",
                "db:push": "prisma db push",
                "db:studio": "prisma studio",
                "stripe:listen": "stripe listen --forward-to localhost:3000/api/webhooks/stripe"
            },
            "dependencies": {
                "next": "14.1.0",
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "@prisma/client": "^5.8.0",
                "next-auth": "^4.24.5",
                "stripe": "^14.11.0",
                "@stripe/stripe-js": "^2.4.0",
                "resend": "^3.1.0",
                "zod": "^3.22.4",
                "class-variance-authority": "^0.7.0",
                "clsx": "^2.1.0",
                "tailwind-merge": "^2.2.0",
                "lucide-react": "^0.309.0",
                "@radix-ui/react-dropdown-menu": "^2.0.6",
                "@radix-ui/react-dialog": "^1.0.5",
                "@radix-ui/react-toast": "^1.1.5",
                "date-fns": "^3.0.6"
            },
            "devDependencies": {
                "typescript": "^5.3.3",
                "@types/node": "^20.10.6",
                "@types/react": "^18.2.46",
                "@types/react-dom": "^18.2.18",
                "prisma": "^5.8.0",
                "tailwindcss": "^3.4.1",
                "postcss": "^8.4.33",
                "autoprefixer": "^10.4.16",
                "eslint": "^8.56.0",
                "eslint-config-next": "14.1.0"
            }
        }

        files.append(GeneratedFile(
            path="package.json",
            content=json.dumps(package_json, indent=2),
            language="json"
        ))

        # tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "lib": ["dom", "dom.iterable", "esnext"],
                "allowJs": True,
                "skipLibCheck": True,
                "strict": True,
                "noEmit": True,
                "esModuleInterop": True,
                "module": "esnext",
                "moduleResolution": "bundler",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
                "plugins": [{"name": "next"}],
                "paths": {
                    "@/*": ["./src/*"]
                }
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
            "exclude": ["node_modules"]
        }

        files.append(GeneratedFile(
            path="tsconfig.json",
            content=json.dumps(tsconfig, indent=2),
            language="json"
        ))

        # next.config.js
        next_config = """/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['avatars.githubusercontent.com', 'lh3.googleusercontent.com'],
  },
  experimental: {
    serverComponentsExternalPackages: ['@prisma/client'],
  },
}

module.exports = nextConfig
"""

        files.append(GeneratedFile(
            path="next.config.js",
            content=next_config,
            language="javascript"
        ))

        # tailwind.config.ts
        tailwind_config = """import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ["class"],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
export default config
"""

        files.append(GeneratedFile(
            path="tailwind.config.ts",
            content=tailwind_config,
            language="typescript"
        ))

        # Prisma schema
        prisma_schema = f"""// Prisma schema for {blueprint.project_name}
// Generated by SDLC Orchestrator - Next.js SaaS Template

generator client {{
  provider = "prisma-client-js"
}}

datasource db {{
  provider = "postgresql"
  url      = env("DATABASE_URL")
}}

model Account {{
  id                String  @id @default(cuid())
  userId            String
  type              String
  provider          String
  providerAccountId String
  refresh_token     String? @db.Text
  access_token      String? @db.Text
  expires_at        Int?
  token_type        String?
  scope             String?
  id_token          String? @db.Text
  session_state     String?

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@unique([provider, providerAccountId])
  @@index([userId])
}}

model Session {{
  id           String   @id @default(cuid())
  sessionToken String   @unique
  userId       String
  expires      DateTime
  user         User     @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@index([userId])
}}

model User {{
  id            String    @id @default(cuid())
  name          String?
  email         String?   @unique
  emailVerified DateTime?
  image         String?
  role          String    @default("user") // user, admin
  accounts      Account[]
  sessions      Session[]

  // Subscription fields
  stripeCustomerId       String?   @unique
  stripeSubscriptionId   String?   @unique
  stripePriceId          String?
  stripeCurrentPeriodEnd DateTime?

  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}}

model VerificationToken {{
  identifier String
  token      String   @unique
  expires    DateTime

  @@unique([identifier, token])
}}

"""

        # Add blueprint entities to Prisma schema
        for entity in blueprint.entities:
            prisma_schema += f"\nmodel {entity.name} {{\n"
            prisma_schema += "  id        String   @id @default(cuid())\n"

            for field in entity.fields:
                prisma_type = self._map_field_type_to_prisma(field.type)
                optional = "" if field.required else "?"
                unique = " @unique" if field.unique else ""

                if field.relation_to:
                    prisma_schema += f"  {field.name}   {field.relation_to}{optional}{unique}\n"
                else:
                    prisma_schema += f"  {field.name}   {prisma_type}{optional}{unique}\n"

            prisma_schema += "  createdAt DateTime @default(now())\n"
            prisma_schema += "  updatedAt DateTime @updatedAt\n"
            prisma_schema += "}\n"

        files.append(GeneratedFile(
            path="prisma/schema.prisma",
            content=prisma_schema,
            language="prisma"
        ))

        return files

    def generate_entry_point(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate Next.js app entry point and core files"""
        files = []

        # Root layout
        layout_tsx = f"""import type {{ Metadata }} from 'next'
import {{ Inter }} from 'next/font/google'
import './globals.css'
import {{ Toaster }} from '@/components/ui/toaster'
import {{ Providers }} from '@/components/providers'

const inter = Inter({{ subsets: ['latin'] }})

export const metadata: Metadata = {{
  title: '{blueprint.project_name}',
  description: 'Generated by SDLC Orchestrator',
}}

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode
}}) {{
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={{inter.className}}>
        <Providers>
          {{children}}
          <Toaster />
        </Providers>
      </body>
    </html>
  )
}}
"""

        files.append(GeneratedFile(
            path="src/app/layout.tsx",
            content=layout_tsx,
            language="typescriptreact"
        ))

        # Marketing landing page
        landing_page = f"""import Link from 'next/link'
import {{ Button }} from '@/components/ui/button'

export default function Home() {{
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b">
        <div className="container flex h-16 items-center justify-between">
          <h1 className="text-xl font-bold">{blueprint.project_name}</h1>
          <nav className="flex items-center gap-4">
            <Link href="/signin">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link href="/signup">
              <Button>Get Started</Button>
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <section className="container flex flex-col items-center justify-center gap-4 py-24 text-center">
          <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl md:text-6xl">
            Welcome to {blueprint.project_name}
          </h1>
          <p className="max-w-[600px] text-gray-500 md:text-xl">
            Start building your SaaS product with authentication, payments, and more.
          </p>
          <div className="flex gap-4">
            <Link href="/signup">
              <Button size="lg">Get Started</Button>
            </Link>
            <Link href="/pricing">
              <Button size="lg" variant="outline">View Pricing</Button>
            </Link>
          </div>
        </section>

        <section className="container py-24">
          <h2 className="mb-12 text-center text-3xl font-bold">Features</h2>
          <div className="grid gap-8 md:grid-cols-3">
            <div className="rounded-lg border p-6">
              <h3 className="mb-2 text-xl font-semibold">Authentication</h3>
              <p className="text-gray-500">
                Secure authentication with NextAuth.js. Support for GitHub, Google, and email.
              </p>
            </div>
            <div className="rounded-lg border p-6">
              <h3 className="mb-2 text-xl font-semibold">Payments</h3>
              <p className="text-gray-500">
                Stripe integration with subscriptions, webhooks, and customer portal.
              </p>
            </div>
            <div className="rounded-lg border p-6">
              <h3 className="mb-2 text-xl font-semibold">Dashboard</h3>
              <p className="text-gray-500">
                Beautiful dashboard with analytics, user management, and settings.
              </p>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-6">
        <div className="container text-center text-sm text-gray-500">
          Built with SDLC Orchestrator
        </div>
      </footer>
    </div>
  )
}}
"""

        files.append(GeneratedFile(
            path="src/app/(marketing)/page.tsx",
            content=landing_page,
            language="typescriptreact"
        ))

        # Prisma client
        prisma_client = """import { PrismaClient } from '@prisma/client'

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

export const prisma = globalForPrisma.prisma ?? new PrismaClient()

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma
"""

        files.append(GeneratedFile(
            path="src/lib/prisma.ts",
            content=prisma_client,
            language="typescript"
        ))

        # NextAuth configuration
        nextauth_config = """import { NextAuthOptions } from 'next-auth'
import GithubProvider from 'next-auth/providers/github'
import GoogleProvider from 'next-auth/providers/google'
import { PrismaAdapter } from '@next-auth/prisma-adapter'
import { prisma } from '@/lib/prisma'

export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),
  providers: [
    GithubProvider({
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    }),
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async session({ session, user }) {
      if (session.user) {
        session.user.id = user.id
        session.user.role = user.role
        session.user.stripeCustomerId = user.stripeCustomerId
        session.user.stripeSubscriptionId = user.stripeSubscriptionId
        session.user.stripePriceId = user.stripePriceId
        session.user.stripeCurrentPeriodEnd = user.stripeCurrentPeriodEnd
      }
      return session
    },
  },
  pages: {
    signIn: '/signin',
  },
}
"""

        files.append(GeneratedFile(
            path="src/lib/auth.ts",
            content=nextauth_config,
            language="typescript"
        ))

        # Stripe utilities
        stripe_config = """import Stripe from 'stripe'

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
  typescript: true,
})

export const STRIPE_PRICE_IDS = {
  FREE: null,
  PRO: process.env.STRIPE_PRO_PRICE_ID,
  ENTERPRISE: process.env.STRIPE_ENTERPRISE_PRICE_ID,
}

export const PLANS = [
  {
    name: 'Free',
    price: 0,
    priceId: null,
    features: [
      '10 projects',
      'Basic analytics',
      'Email support',
    ],
  },
  {
    name: 'Pro',
    price: 29,
    priceId: STRIPE_PRICE_IDS.PRO,
    features: [
      'Unlimited projects',
      'Advanced analytics',
      'Priority support',
      'Custom domain',
    ],
  },
  {
    name: 'Enterprise',
    price: 99,
    priceId: STRIPE_PRICE_IDS.ENTERPRISE,
    features: [
      'Everything in Pro',
      'Dedicated support',
      'SLA guarantee',
      'Advanced security',
    ],
  },
]
"""

        files.append(GeneratedFile(
            path="src/lib/stripe/config.ts",
            content=stripe_config,
            language="typescript"
        ))

        # Global CSS with shadcn/ui variables
        globals_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
"""

        files.append(GeneratedFile(
            path="src/app/globals.css",
            content=globals_css,
            language="css"
        ))

        return files

    def generate_route_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate API routes for Stripe and entities"""
        files = []

        # NextAuth API route
        nextauth_route = """import NextAuth from 'next-auth'
import { authOptions } from '@/lib/auth'

const handler = NextAuth(authOptions)

export { handler as GET, handler as POST }
"""

        files.append(GeneratedFile(
            path="src/app/api/auth/[...nextauth]/route.ts",
            content=nextauth_route,
            language="typescript"
        ))

        # Stripe checkout session API
        checkout_route = """import { NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { stripe } from '@/lib/stripe/config'
import { prisma } from '@/lib/prisma'

export async function POST(req: Request) {
  try {
    const session = await getServerSession(authOptions)

    if (!session?.user) {
      return new NextResponse('Unauthorized', { status: 401 })
    }

    const { priceId } = await req.json()

    const user = await prisma.user.findUnique({
      where: { id: session.user.id },
    })

    if (!user) {
      return new NextResponse('User not found', { status: 404 })
    }

    let customerId = user.stripeCustomerId

    if (!customerId) {
      const customer = await stripe.customers.create({
        email: user.email!,
        metadata: {
          userId: user.id,
        },
      })

      await prisma.user.update({
        where: { id: user.id },
        data: { stripeCustomerId: customer.id },
      })

      customerId = customer.id
    }

    const checkoutSession = await stripe.checkout.sessions.create({
      customer: customerId,
      mode: 'subscription',
      payment_method_types: ['card'],
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      success_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard?success=true`,
      cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/pricing?canceled=true`,
      metadata: {
        userId: user.id,
      },
    })

    return NextResponse.json({ url: checkoutSession.url })
  } catch (error) {
    console.error('Checkout error:', error)
    return new NextResponse('Internal Server Error', { status: 500 })
  }
}
"""

        files.append(GeneratedFile(
            path="src/app/api/stripe/checkout/route.ts",
            content=checkout_route,
            language="typescript"
        ))

        # Stripe webhook handler
        webhook_route = """import { NextResponse } from 'next/server'
import { headers } from 'next/headers'
import Stripe from 'stripe'
import { stripe } from '@/lib/stripe/config'
import { prisma } from '@/lib/prisma'

export async function POST(req: Request) {
  const body = await req.text()
  const signature = headers().get('Stripe-Signature')!

  let event: Stripe.Event

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    )
  } catch (error) {
    return new NextResponse('Webhook signature verification failed', { status: 400 })
  }

  const session = event.data.object as Stripe.Checkout.Session

  if (event.type === 'checkout.session.completed') {
    const subscription = await stripe.subscriptions.retrieve(
      session.subscription as string
    )

    await prisma.user.update({
      where: {
        stripeCustomerId: session.customer as string,
      },
      data: {
        stripeSubscriptionId: subscription.id,
        stripePriceId: subscription.items.data[0].price.id,
        stripeCurrentPeriodEnd: new Date(subscription.current_period_end * 1000),
      },
    })
  }

  if (event.type === 'invoice.payment_succeeded') {
    const subscription = await stripe.subscriptions.retrieve(
      session.subscription as string
    )

    await prisma.user.update({
      where: {
        stripeSubscriptionId: subscription.id,
      },
      data: {
        stripePriceId: subscription.items.data[0].price.id,
        stripeCurrentPeriodEnd: new Date(subscription.current_period_end * 1000),
      },
    })
  }

  return new NextResponse(null, { status: 200 })
}
"""

        files.append(GeneratedFile(
            path="src/app/api/webhooks/stripe/route.ts",
            content=webhook_route,
            language="typescript"
        ))

        # Customer portal API
        portal_route = """import { NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { stripe } from '@/lib/stripe/config'
import { prisma } from '@/lib/prisma'

export async function POST(req: Request) {
  try {
    const session = await getServerSession(authOptions)

    if (!session?.user) {
      return new NextResponse('Unauthorized', { status: 401 })
    }

    const user = await prisma.user.findUnique({
      where: { id: session.user.id },
    })

    if (!user?.stripeCustomerId) {
      return new NextResponse('No subscription found', { status: 404 })
    }

    const portalSession = await stripe.billingPortal.sessions.create({
      customer: user.stripeCustomerId,
      return_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard/billing`,
    })

    return NextResponse.json({ url: portalSession.url })
  } catch (error) {
    console.error('Portal error:', error)
    return new NextResponse('Internal Server Error', { status: 500 })
  }
}
"""

        files.append(GeneratedFile(
            path="src/app/api/stripe/portal/route.ts",
            content=portal_route,
            language="typescript"
        ))

        # Generate CRUD routes for blueprint entities
        for route in blueprint.api_routes:
            entity_name = route.entity if route.entity else "resource"

            if "GET" in route.methods or "POST" in route.methods:
                list_create_route = self._generate_nextjs_list_create_route(entity_name, route)
                files.append(GeneratedFile(
                    path=f"src/app/api/{entity_name.lower()}/route.ts",
                    content=list_create_route,
                    language="typescript"
                ))

            if "GET" in route.methods or "PUT" in route.methods or "DELETE" in route.methods:
                detail_route = self._generate_nextjs_detail_route(entity_name, route)
                files.append(GeneratedFile(
                    path=f"src/app/api/{entity_name.lower()}/[id]/route.ts",
                    content=detail_route,
                    language="typescript"
                ))

        return files

    def generate_page_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate dashboard pages"""
        files = []

        # Dashboard layout with auth check
        dashboard_layout = """import { getServerSession } from 'next-auth'
import { redirect } from 'next/navigation'
import { authOptions } from '@/lib/auth'
import { DashboardNav } from '@/components/dashboard/nav'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await getServerSession(authOptions)

  if (!session) {
    redirect('/signin')
  }

  return (
    <div className="flex min-h-screen">
      <DashboardNav />
      <main className="flex-1 p-8">{children}</main>
    </div>
  )
}
"""

        files.append(GeneratedFile(
            path="src/app/(dashboard)/dashboard/layout.tsx",
            content=dashboard_layout,
            language="typescriptreact"
        ))

        # Dashboard home page
        dashboard_page = """import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'

export default async function DashboardPage() {
  const session = await getServerSession(authOptions)
  const user = await prisma.user.findUnique({
    where: { id: session!.user.id },
  })

  const isSubscribed =
    user?.stripePriceId &&
    user?.stripeCurrentPeriodEnd &&
    user.stripeCurrentPeriodEnd.getTime() + 86400000 > Date.now()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-gray-500">Welcome back, {user?.name}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border p-6">
          <h3 className="text-sm font-medium text-gray-500">Subscription Status</h3>
          <p className="mt-2 text-2xl font-bold">
            {isSubscribed ? 'Active' : 'Free'}
          </p>
        </div>
        <div className="rounded-lg border p-6">
          <h3 className="text-sm font-medium text-gray-500">Plan</h3>
          <p className="mt-2 text-2xl font-bold">
            {user?.stripePriceId ? 'Pro' : 'Free'}
          </p>
        </div>
        <div className="rounded-lg border p-6">
          <h3 className="text-sm font-medium text-gray-500">Next Billing</h3>
          <p className="mt-2 text-2xl font-bold">
            {user?.stripeCurrentPeriodEnd
              ? new Date(user.stripeCurrentPeriodEnd).toLocaleDateString()
              : 'N/A'}
          </p>
        </div>
      </div>
    </div>
  )
}
"""

        files.append(GeneratedFile(
            path="src/app/(dashboard)/dashboard/page.tsx",
            content=dashboard_page,
            language="typescriptreact"
        ))

        # Pricing page
        pricing_page = """'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { PLANS } from '@/lib/stripe/config'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'

export default function PricingPage() {
  const { data: session } = useSession()
  const router = useRouter()
  const [loading, setLoading] = useState<string | null>(null)

  const handleSubscribe = async (priceId: string | null) => {
    if (!session) {
      router.push('/signin')
      return
    }

    if (!priceId) {
      router.push('/dashboard')
      return
    }

    setLoading(priceId)

    try {
      const response = await fetch('/api/stripe/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ priceId }),
      })

      const { url } = await response.json()
      window.location.href = url
    } catch (error) {
      console.error('Subscription error:', error)
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="container py-24">
      <div className="mx-auto max-w-4xl text-center">
        <h1 className="mb-4 text-4xl font-bold">Simple, Transparent Pricing</h1>
        <p className="mb-12 text-xl text-gray-500">
          Choose the plan that's right for you
        </p>
      </div>

      <div className="mx-auto grid max-w-6xl gap-8 md:grid-cols-3">
        {PLANS.map((plan) => (
          <div
            key={plan.name}
            className="flex flex-col rounded-lg border p-8"
          >
            <h3 className="mb-2 text-2xl font-bold">{plan.name}</h3>
            <p className="mb-6 text-4xl font-bold">
              ${plan.price}
              <span className="text-lg font-normal text-gray-500">/month</span>
            </p>
            <ul className="mb-8 flex-1 space-y-3">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-center">
                  <svg
                    className="mr-2 h-5 w-5 text-green-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  {feature}
                </li>
              ))}
            </ul>
            <Button
              onClick={() => handleSubscribe(plan.priceId)}
              disabled={loading === plan.priceId}
              className="w-full"
            >
              {loading === plan.priceId ? 'Loading...' : 'Get Started'}
            </Button>
          </div>
        ))}
      </div>
    </div>
  )
}
"""

        files.append(GeneratedFile(
            path="src/app/(marketing)/pricing/page.tsx",
            content=pricing_page,
            language="typescriptreact"
        ))

        # Generate pages for blueprint entities
        for page in blueprint.pages:
            page_component = self._generate_nextjs_page_component(page, blueprint)
            files.append(GeneratedFile(
                path=f"src/app/(dashboard)/dashboard/{page.path.lower()}/page.tsx",
                content=page_component,
                language="typescriptreact"
            ))

        return files

    def _map_field_type_to_prisma(self, field_type: str) -> str:
        """Map blueprint field type to Prisma type"""
        type_map = {
            "string": "String",
            "integer": "Int",
            "boolean": "Boolean",
            "date": "DateTime",
            "float": "Float",
            "json": "Json",
        }
        return type_map.get(field_type.lower(), "String")

    def _generate_nextjs_list_create_route(self, entity_name: str, route: APIRoute) -> str:
        """Generate Next.js API route for list and create operations"""
        return f"""import {{ NextResponse }} from 'next/server'
import {{ getServerSession }} from 'next-auth'
import {{ authOptions }} from '@/lib/auth'
import {{ prisma }} from '@/lib/prisma'

export async function GET(req: Request) {{
  try {{
    {"const session = await getServerSession(authOptions)" if route.auth_required else ""}
    {"if (!session?.user) { return new NextResponse('Unauthorized', { status: 401 }) }" if route.auth_required else ""}

    const items = await prisma.{entity_name.lower()}.findMany({{
      orderBy: {{ createdAt: 'desc' }},
    }})

    return NextResponse.json(items)
  }} catch (error) {{
    console.error('GET /{entity_name.lower()} error:', error)
    return new NextResponse('Internal Server Error', {{ status: 500 }})
  }}
}}

export async function POST(req: Request) {{
  try {{
    {"const session = await getServerSession(authOptions)" if route.auth_required else ""}
    {"if (!session?.user) { return new NextResponse('Unauthorized', { status: 401 }) }" if route.auth_required else ""}

    const body = await req.json()

    const item = await prisma.{entity_name.lower()}.create({{
      data: body,
    }})

    return NextResponse.json(item, {{ status: 201 }})
  }} catch (error) {{
    console.error('POST /{entity_name.lower()} error:', error)
    return new NextResponse('Internal Server Error', {{ status: 500 }})
  }}
}}
"""

    def _generate_nextjs_detail_route(self, entity_name: str, route: APIRoute) -> str:
        """Generate Next.js API route for detail operations"""
        return f"""import {{ NextResponse }} from 'next/server'
import {{ getServerSession }} from 'next-auth'
import {{ authOptions }} from '@/lib/auth'
import {{ prisma }} from '@/lib/prisma'

export async function GET(
  req: Request,
  {{ params }}: {{ params: {{ id: string }} }}
) {{
  try {{
    {"const session = await getServerSession(authOptions)" if route.auth_required else ""}
    {"if (!session?.user) { return new NextResponse('Unauthorized', { status: 401 }) }" if route.auth_required else ""}

    const item = await prisma.{entity_name.lower()}.findUnique({{
      where: {{ id: params.id }},
    }})

    if (!item) {{
      return new NextResponse('Not Found', {{ status: 404 }})
    }}

    return NextResponse.json(item)
  }} catch (error) {{
    console.error('GET /{entity_name.lower()}/{{id}} error:', error)
    return new NextResponse('Internal Server Error', {{ status: 500 }})
  }}
}}

export async function PUT(
  req: Request,
  {{ params }}: {{ params: {{ id: string }} }}
) {{
  try {{
    {"const session = await getServerSession(authOptions)" if route.auth_required else ""}
    {"if (!session?.user) { return new NextResponse('Unauthorized', { status: 401 }) }" if route.auth_required else ""}

    const body = await req.json()

    const item = await prisma.{entity_name.lower()}.update({{
      where: {{ id: params.id }},
      data: body,
    }})

    return NextResponse.json(item)
  }} catch (error) {{
    console.error('PUT /{entity_name.lower()}/{{id}} error:', error)
    return new NextResponse('Internal Server Error', {{ status: 500 }})
  }}
}}

export async function DELETE(
  req: Request,
  {{ params }}: {{ params: {{ id: string }} }}
) {{
  try {{
    {"const session = await getServerSession(authOptions)" if route.auth_required else ""}
    {"if (!session?.user) { return new NextResponse('Unauthorized', { status: 401 }) }" if route.auth_required else ""}

    await prisma.{entity_name.lower()}.delete({{
      where: {{ id: params.id }},
    }})

    return new NextResponse(null, {{ status: 204 }})
  }} catch (error) {{
    console.error('DELETE /{entity_name.lower()}/{{id}} error:', error)
    return new NextResponse('Internal Server Error', {{ status: 500 }})
  }}
}}
"""

    def _generate_nextjs_page_component(self, page: Page, blueprint: TemplateBlueprint) -> str:
        """Generate Next.js page component"""
        return f"""import {{ prisma }} from '@/lib/prisma'

export default async function {page.name}Page() {{
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{page.name}</h1>
        <p className="text-gray-500">
          {page.name} page for {blueprint.project_name}
        </p>
      </div>

      <div className="rounded-lg border p-6">
        <p>Implement your {page.name.lower()} content here</p>
      </div>
    </div>
  )
}}
"""

    def get_smoke_test_command(self) -> str:
        """Get smoke test command for Next.js SaaS"""
        return "npm run build"
