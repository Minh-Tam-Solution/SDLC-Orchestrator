"""
Next.js Fullstack Template - Full-stack web app with Prisma + NextAuth

SDLC Framework Compliance:
- Framework: SDLC 5.2.0 (7-Pillar + AI Governance Principles)
- Pillar 3: Build Phase - Full-Stack Web Application Template
- AI Governance Principle 4: Deterministic Code Generation
- Methodology: Next.js App Router best practices (React Server Components)

Purpose:
Scaffolds production-ready Next.js 14 application with:
- App Router (React Server Components)
- Prisma ORM + PostgreSQL
- NextAuth.js authentication
- TypeScript strict mode
- Tailwind CSS
- Server actions for mutations

Tech Stack:
- Next.js 14+, React 18, TypeScript 5
- Prisma, NextAuth.js
- Tailwind CSS v3
- Zod for validation

Sprint: 106 - App Builder Integration (MVP)
Date: January 28, 2026
Owner: Backend Team
Status: ACTIVE
"""

from typing import List
from .base_template import BaseTemplate, GeneratedFile, TemplateBlueprint, TemplateType


class NextJSFullstackTemplate(BaseTemplate):
    """Next.js 14 App Router with Prisma + NextAuth"""

    template_type = TemplateType.NEXTJS_FULLSTACK
    template_name = "Next.js Fullstack"
    template_version = "1.0.0"

    default_tech_stack = ["nextjs", "react", "typescript", "prisma", "nextauth", "tailwind"]
    required_env_vars = ["DATABASE_URL", "NEXTAUTH_SECRET", "NEXTAUTH_URL"]

    def get_file_structure(self, blueprint: TemplateBlueprint) -> dict:
        """Next.js App Router structure"""
        return {
            "src/": "Source code",
            "src/app/": "App Router pages",
            "src/app/api/": "API routes",
            "src/components/": "React components",
            "src/lib/": "Utilities and helpers",
            "prisma/": "Prisma schema and migrations",
            "public/": "Static assets",
        }

    def generate_config_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate Next.js configuration files"""
        files = []

        # package.json
        files.append(GeneratedFile(
            path="package.json",
            content=self._generate_package_json(blueprint),
            language="json"
        ))

        # tsconfig.json
        files.append(GeneratedFile(
            path="tsconfig.json",
            content=self._generate_tsconfig(blueprint),
            language="json"
        ))

        # next.config.js
        files.append(GeneratedFile(
            path="next.config.js",
            content=self._generate_next_config(blueprint),
            language="javascript"
        ))

        # tailwind.config.ts
        files.append(GeneratedFile(
            path="tailwind.config.ts",
            content=self._generate_tailwind_config(blueprint),
            language="typescript"
        ))

        # postcss.config.js
        files.append(GeneratedFile(
            path="postcss.config.js",
            content=self._generate_postcss_config(blueprint),
            language="javascript"
        ))

        # prisma/schema.prisma
        files.append(GeneratedFile(
            path="prisma/schema.prisma",
            content=self._generate_prisma_schema(blueprint),
            language="prisma"
        ))

        return files

    def generate_entry_point(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate Next.js entry point files"""
        files = []

        # src/app/layout.tsx
        files.append(GeneratedFile(
            path="src/app/layout.tsx",
            content=self._generate_root_layout(blueprint),
            language="typescriptreact"
        ))

        # src/app/page.tsx
        files.append(GeneratedFile(
            path="src/app/page.tsx",
            content=self._generate_home_page(blueprint),
            language="typescriptreact"
        ))

        # src/app/globals.css
        files.append(GeneratedFile(
            path="src/app/globals.css",
            content=self._generate_globals_css(blueprint),
            language="css"
        ))

        # src/lib/prisma.ts
        files.append(GeneratedFile(
            path="src/lib/prisma.ts",
            content=self._generate_prisma_client(blueprint),
            language="typescript"
        ))

        # src/lib/auth.ts (NextAuth config)
        files.append(GeneratedFile(
            path="src/lib/auth.ts",
            content=self._generate_auth_config(blueprint),
            language="typescript"
        ))

        # src/app/api/auth/[...nextauth]/route.ts
        files.append(GeneratedFile(
            path="src/app/api/auth/[...nextauth]/route.ts",
            content=self._generate_auth_route(blueprint),
            language="typescript"
        ))

        return files

    def generate_route_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate API routes"""
        files = []

        # Group routes by entity
        entity_routes = {}
        for route in blueprint.api_routes:
            if route.entity:
                if route.entity not in entity_routes:
                    entity_routes[route.entity] = []
                entity_routes[route.entity].append(route)

        # Generate API route for each entity
        for entity_name, routes in entity_routes.items():
            entity = next((e for e in blueprint.entities if e.name == entity_name), None)
            if entity:
                # List route
                files.append(GeneratedFile(
                    path=f"src/app/api/{entity_name.lower()}/route.ts",
                    content=self._generate_api_route(entity, routes, blueprint),
                    language="typescript"
                ))

                # Detail route
                files.append(GeneratedFile(
                    path=f"src/app/api/{entity_name.lower()}/[id]/route.ts",
                    content=self._generate_api_detail_route(entity, routes, blueprint),
                    language="typescript"
                ))

        return files

    def generate_page_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate frontend page files"""
        files = []

        for page in blueprint.pages:
            # Generate page component
            files.append(GeneratedFile(
                path=f"src/app{page.path}/page.tsx",
                content=self._generate_page(page, blueprint),
                language="typescriptreact"
            ))

            # Generate components for entities used in page
            for entity_name in page.entities_used:
                entity = next((e for e in blueprint.entities if e.name == entity_name), None)
                if entity:
                    files.append(GeneratedFile(
                        path=f"src/components/{entity_name}List.tsx",
                        content=self._generate_list_component(entity, blueprint),
                        language="typescriptreact"
                    ))

                    files.append(GeneratedFile(
                        path=f"src/components/{entity_name}Form.tsx",
                        content=self._generate_form_component(entity, blueprint),
                        language="typescriptreact"
                    ))

        return files

    def get_smoke_test_command(self) -> str:
        """Smoke test: Check if Next.js build succeeds"""
        return "npm run build"

    # Private helper methods

    def _generate_package_json(self, blueprint: TemplateBlueprint) -> str:
        return f'''{{
  "name": "{blueprint.project_name}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "prisma:generate": "prisma generate",
    "prisma:migrate": "prisma migrate dev"
  }},
  "dependencies": {{
    "next": "14.0.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@prisma/client": "^5.7.1",
    "next-auth": "^4.24.5",
    "zod": "^3.22.4",
    "bcrypt": "^5.1.1"
  }},
  "devDependencies": {{
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "@types/bcrypt": "^5.0.2",
    "typescript": "^5",
    "prisma": "^5.7.1",
    "tailwindcss": "^3.3.0",
    "postcss": "^8",
    "autoprefixer": "^10.0.1",
    "eslint": "^8",
    "eslint-config-next": "14.0.4"
  }}
}}
'''

    def _generate_tsconfig(self, blueprint: TemplateBlueprint) -> str:
        return '''{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
'''

    def _generate_next_config(self, blueprint: TemplateBlueprint) -> str:
        return '''/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: true,
  },
}

module.exports = nextConfig
'''

    def _generate_tailwind_config(self, blueprint: TemplateBlueprint) -> str:
        return '''import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
export default config
'''

    def _generate_postcss_config(self, blueprint: TemplateBlueprint) -> str:
        return '''module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
'''

    def _generate_prisma_schema(self, blueprint: TemplateBlueprint) -> str:
        models = []

        # Add User model for auth
        models.append('''model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String?
  password  String
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
''')

        # Add entity models
        for entity in blueprint.entities:
            fields = []
            fields.append(f"  id        Int      @id @default(autoincrement())")

            for field in entity.fields:
                prisma_type = {
                    "string": "String",
                    "integer": "Int",
                    "boolean": "Boolean",
                    "date": "DateTime",
                    "datetime": "DateTime",
                }.get(field.type, "String")

                optional = "?" if not field.required else ""
                unique = " @unique" if field.unique else ""

                fields.append(f"  {field.name} {prisma_type}{optional}{unique}")

            fields.append(f"  createdAt DateTime @default(now())")
            fields.append(f"  updatedAt DateTime @updatedAt")

            fields_str = "\n".join(fields)
            models.append(f'''model {entity.name} {{
{fields_str}
}}
''')

        models_str = "\n".join(models)

        return f'''generator client {{
  provider = "prisma-client-js"
}}

datasource db {{
  provider = "postgresql"
  url      = env("DATABASE_URL")
}}

{models_str}
'''

    def _generate_root_layout(self, blueprint: TemplateBlueprint) -> str:
        return f'''import type {{ Metadata }} from 'next'
import {{ Inter }} from 'next/font/google'
import './globals.css'

const inter = Inter({{ subsets: ['latin'] }})

export const metadata: Metadata = {{
  title: '{blueprint.project_name}',
  description: 'Generated with SDLC Orchestrator',
}}

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode
}}) {{
  return (
    <html lang="en">
      <body className={{inter.className}}>{{children}}</body>
    </html>
  )
}}
'''

    def _generate_home_page(self, blueprint: TemplateBlueprint) -> str:
        return f'''export default function Home() {{
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm">
        <h1 className="text-4xl font-bold mb-4">
          Welcome to {blueprint.project_name}
        </h1>
        <p className="text-lg text-gray-600">
          Generated with SDLC Orchestrator App Builder
        </p>
      </div>
    </main>
  )
}}
'''

    def _generate_globals_css(self, blueprint: TemplateBlueprint) -> str:
        return '''@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground-rgb: 0, 0, 0;
  --background-start-rgb: 214, 219, 220;
  --background-end-rgb: 255, 255, 255;
}

@media (prefers-color-scheme: dark) {
  :root {
    --foreground-rgb: 255, 255, 255;
    --background-start-rgb: 0, 0, 0;
    --background-end-rgb: 0, 0, 0;
  }
}

body {
  color: rgb(var(--foreground-rgb));
  background: linear-gradient(
      to bottom,
      transparent,
      rgb(var(--background-end-rgb))
    )
    rgb(var(--background-start-rgb));
}
'''

    def _generate_prisma_client(self, blueprint: TemplateBlueprint) -> str:
        return '''import { PrismaClient } from '@prisma/client'

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

export const prisma = globalForPrisma.prisma ?? new PrismaClient()

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma
'''

    def _generate_auth_config(self, blueprint: TemplateBlueprint) -> str:
        return '''import { NextAuthOptions } from 'next-auth'
import CredentialsProvider from 'next-auth/providers/credentials'
import { compare } from 'bcrypt'
import { prisma } from './prisma'

export const authOptions: NextAuthOptions = {
  session: {
    strategy: 'jwt',
  },
  pages: {
    signIn: '/login',
  },
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null
        }

        const user = await prisma.user.findUnique({
          where: { email: credentials.email }
        })

        if (!user) {
          return null
        }

        const isPasswordValid = await compare(credentials.password, user.password)

        if (!isPasswordValid) {
          return null
        }

        return {
          id: user.id.toString(),
          email: user.email,
          name: user.name,
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id
      }
      return token
    },
    async session({ session, token }) {
      if (token && session.user) {
        session.user.id = token.id as string
      }
      return session
    },
  },
}
'''

    def _generate_auth_route(self, blueprint: TemplateBlueprint) -> str:
        return '''import NextAuth from 'next-auth'
import { authOptions } from '@/lib/auth'

const handler = NextAuth(authOptions)

export { handler as GET, handler as POST }
'''

    def _generate_api_route(self, entity, routes, blueprint: TemplateBlueprint) -> str:
        has_get = any("GET" in r.methods for r in routes)
        has_post = any("POST" in r.methods for r in routes)

        get_handler = ''
        if has_get:
            get_handler = f'''export async function GET(request: Request) {{
  try {{
    const items = await prisma.{entity.name.lower()}.findMany()
    return NextResponse.json(items)
  }} catch (error) {{
    return NextResponse.json(
      {{ error: 'Failed to fetch {entity.name.lower()}s' }},
      {{ status: 500 }}
    )
  }}
}}
'''

        post_handler = ''
        if has_post:
            post_handler = f'''export async function POST(request: Request) {{
  try {{
    const body = await request.json()
    const item = await prisma.{entity.name.lower()}.create({{
      data: body,
    }})
    return NextResponse.json(item, {{ status: 201 }})
  }} catch (error) {{
    return NextResponse.json(
      {{ error: 'Failed to create {entity.name.lower()}' }},
      {{ status: 500 }}
    )
  }}
}}
'''

        return f'''import {{ NextResponse }} from 'next/server'
import {{ prisma }} from '@/lib/prisma'

{get_handler}

{post_handler}
'''

    def _generate_api_detail_route(self, entity, routes, blueprint: TemplateBlueprint) -> str:
        return f'''import {{ NextResponse }} from 'next/server'
import {{ prisma }} from '@/lib/prisma'

export async function GET(
  request: Request,
  {{ params }}: {{ params: {{ id: string }} }}
) {{
  try {{
    const item = await prisma.{entity.name.lower()}.findUnique({{
      where: {{ id: parseInt(params.id) }},
    }})

    if (!item) {{
      return NextResponse.json(
        {{ error: '{entity.name} not found' }},
        {{ status: 404 }}
      )
    }}

    return NextResponse.json(item)
  }} catch (error) {{
    return NextResponse.json(
      {{ error: 'Failed to fetch {entity.name.lower()}' }},
      {{ status: 500 }}
    )
  }}
}}

export async function PUT(
  request: Request,
  {{ params }}: {{ params: {{ id: string }} }}
) {{
  try {{
    const body = await request.json()
    const item = await prisma.{entity.name.lower()}.update({{
      where: {{ id: parseInt(params.id) }},
      data: body,
    }})
    return NextResponse.json(item)
  }} catch (error) {{
    return NextResponse.json(
      {{ error: 'Failed to update {entity.name.lower()}' }},
      {{ status: 500 }}
    )
  }}
}}

export async function DELETE(
  request: Request,
  {{ params }}: {{ params: {{ id: string }} }}
) {{
  try {{
    await prisma.{entity.name.lower()}.delete({{
      where: {{ id: parseInt(params.id) }},
    }})
    return NextResponse.json({{ success: true }}, {{ status: 204 }})
  }} catch (error) {{
    return NextResponse.json(
      {{ error: 'Failed to delete {entity.name.lower()}' }},
      {{ status: 500 }}
    )
  }}
}}
'''

    def _generate_page(self, page, blueprint: TemplateBlueprint) -> str:
        entity_components = "\n".join([
            f'      <{entity_name}List />'
            for entity_name in page.entities_used
        ])

        imports = "\n".join([
            f"import {entity_name}List from '@/components/{entity_name}List'"
            for entity_name in page.entities_used
        ])

        return f'''{imports}

export default function {page.name.replace(" ", "")}Page() {{
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">{page.name}</h1>
{entity_components}
    </div>
  )
}}
'''

    def _generate_list_component(self, entity, blueprint: TemplateBlueprint) -> str:
        return f'''\'use client\'

import {{ useEffect, useState }} from 'react'

export default function {entity.name}List() {{
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {{
    fetch('/api/{entity.name.lower()}')
      .then(res => res.json())
      .then(data => {{
        setItems(data)
        setLoading(false)
      }})
  }}, [])

  if (loading) return <div>Loading...</div>

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">{entity.name}s</h2>
      <div className="grid gap-4">
        {{items.map((item: any) => (
          <div key={{item.id}} className="border p-4 rounded-lg">
            <pre>{{JSON.stringify(item, null, 2)}}</pre>
          </div>
        ))}}
      </div>
    </div>
  )
}}
'''

    def _generate_form_component(self, entity, blueprint: TemplateBlueprint) -> str:
        return f'''\'use client\'

import {{ useState }} from 'react'

export default function {entity.name}Form() {{
  const [formData, setFormData] = useState({{}})

  const handleSubmit = async (e: React.FormEvent) => {{
    e.preventDefault()
    const res = await fetch('/api/{entity.name.lower()}', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify(formData),
    }})
    if (res.ok) {{
      window.location.reload()
    }}
  }}

  return (
    <form onSubmit={{handleSubmit}} className="space-y-4">
      <h3 className="text-xl font-semibold">Create {entity.name}</h3>
      <button
        type="submit"
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
      >
        Create
      </button>
    </form>
  )
}}
'''
