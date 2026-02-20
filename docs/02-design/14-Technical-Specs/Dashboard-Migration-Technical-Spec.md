# Dashboard Migration Technical Specification
## React Vite → Next.js App Router

**Version**: 1.0.0
**Date**: January 03, 2026
**Status**: APPROVED
**Sprint**: 61-64
**Decision Reference**: [ADR-025](../01-ADRs/ADR-025-Frontend-Platform-Consolidation-Nextjs-Monolith.md)

---

## 1. Overview

### 1.1 Objective
Migrate the SDLC Orchestrator Dashboard from React 18 + Vite to Next.js 14+ App Router while maintaining feature parity, improving performance, and enabling unified codebase with the Landing page.

### 1.2 Scope
| In Scope | Out of Scope |
|----------|--------------|
| 34 dashboard routes | Backend API changes |
| 105 React components | Database schema |
| 13 custom hooks | Third-party integrations |
| TanStack Query patterns | Mobile app |
| Auth flow consolidation | Design system overhaul |

### 1.3 Success Criteria
- [ ] 100% route parity (34/34 routes)
- [ ] Navigation latency <100ms (p95)
- [ ] Bundle size <1MB (gzipped)
- [ ] Memory usage <512MB
- [ ] Test coverage 90%+
- [ ] Zero P0/P1 bugs at cutover

---

## 2. Architecture Design

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    NGINX Reverse Proxy                          │
│              sdlc.nhatquangholding.com                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Next.js 14 (App Router)                      │  │
│  │                   Port 8311                               │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │  (marketing) │  │    (auth)    │  │ (dashboard)  │   │  │
│  │  │   Server     │  │    Client    │  │   Client     │   │  │
│  │  │  Components  │  │  Components  │  │  Components  │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │           Route Handlers (API)                    │   │  │
│  │  │  /api/codegen/stream  /api/upload  /api/auth      │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              FastAPI Backend (Port 8300)                 │  │
│  │         91 API Endpoints | PostgreSQL | Redis            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Route Group Architecture

```
src/app/[locale]/
├── (marketing)/         # SSR - SEO optimized
│   └── ...existing...
│
├── (auth)/              # Client - OAuth/JWT
│   └── ...existing...
│
├── (dashboard)/         # Client-first - SPA-like UX
│   ├── layout.tsx       # Sidebar + Header (client)
│   ├── loading.tsx      # Skeleton loader
│   ├── error.tsx        # Error boundary
│   └── [routes]/        # Dashboard routes
│
└── (admin)/             # Client - Role-protected
    ├── layout.tsx       # Admin layout + role check
    └── [routes]/        # Admin routes
```

### 2.3 Component Strategy

| Component Type | Rendering | Use Case |
|----------------|-----------|----------|
| Server Component | SSR/RSC | Lists, static content, SEO |
| Client Component | CSR | Interactive, real-time, forms |
| Hybrid | Mixed | Layout with interactive parts |

**Decision**: Dashboard routes use **Client Components** by default for SPA-like experience. Server Components used selectively for data fetching.

---

## 3. Detailed Design

### 3.1 Layout Structure

#### 3.1.1 Dashboard Layout (`(dashboard)/layout.tsx`)

```typescript
// src/app/[locale]/(dashboard)/layout.tsx
'use client';

import { Suspense } from 'react';
import { SidebarProvider } from '@/components/dashboard/SidebarContext';
import { DashboardSidebar } from '@/components/dashboard/Sidebar';
import { DashboardHeader } from '@/components/dashboard/Header';
import { AuthGuard } from '@/components/auth/AuthGuard';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <SidebarProvider>
        <div className="flex h-screen">
          <DashboardSidebar />
          <div className="flex flex-col flex-1 overflow-hidden">
            <DashboardHeader />
            <main className="flex-1 overflow-y-auto p-6">
              <Suspense fallback={<DashboardSkeleton />}>
                {children}
              </Suspense>
            </main>
          </div>
        </div>
      </SidebarProvider>
    </AuthGuard>
  );
}
```

#### 3.1.2 Admin Layout (`(admin)/layout.tsx`)

```typescript
// src/app/[locale]/(admin)/layout.tsx
'use client';

import { AuthGuard } from '@/components/auth/AuthGuard';
import { RoleGuard } from '@/components/auth/RoleGuard';
import { AdminSidebar } from '@/components/admin/AdminSidebar';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <RoleGuard requiredRoles={['admin', 'owner']}>
        <div className="flex h-screen">
          <AdminSidebar />
          <main className="flex-1 overflow-y-auto p-6">
            {children}
          </main>
        </div>
      </RoleGuard>
    </AuthGuard>
  );
}
```

### 3.2 Authentication Flow

#### 3.2.1 Auth Guard Component

```typescript
// src/components/auth/AuthGuard.tsx
'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      const locale = pathname.split('/')[1] || 'vi';
      router.push(`/${locale}/login?redirect=${encodeURIComponent(pathname)}`);
    }
  }, [isLoading, isAuthenticated, router, pathname]);

  if (isLoading) {
    return <AuthLoadingSkeleton />;
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
```

#### 3.2.2 Auth Hook (TanStack Query)

```typescript
// src/hooks/useAuth.ts
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  avatar_url?: string;
}

export function useAuth() {
  const queryClient = useQueryClient();

  const { data: user, isLoading, error } = useQuery({
    queryKey: ['auth', 'user'],
    queryFn: async () => {
      const response = await apiClient.get<User>('/api/v1/auth/me');
      return response.data;
    },
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const logout = useMutation({
    mutationFn: () => apiClient.post('/api/v1/auth/logout'),
    onSuccess: () => {
      queryClient.clear();
      window.location.href = '/login';
    },
  });

  return {
    user,
    isLoading,
    isAuthenticated: !!user && !error,
    logout: logout.mutate,
  };
}
```

### 3.3 Data Fetching Patterns

#### 3.3.1 TanStack Query Setup

```typescript
// src/providers/QueryProvider.tsx
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === 'development' && <ReactQueryDevtools />}
    </QueryClientProvider>
  );
}
```

#### 3.3.2 Data Hook Pattern (Projects Example)

```typescript
// src/hooks/useProjects.ts
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type { Project, CreateProjectDto } from '@/types/project';

const PROJECTS_KEY = ['projects'];

export function useProjects() {
  return useQuery({
    queryKey: PROJECTS_KEY,
    queryFn: async () => {
      const response = await apiClient.get<{ items: Project[]; total: number }>(
        '/api/v1/projects'
      );
      return response.data;
    },
  });
}

export function useProject(id: string) {
  return useQuery({
    queryKey: [...PROJECTS_KEY, id],
    queryFn: async () => {
      const response = await apiClient.get<Project>(`/api/v1/projects/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateProjectDto) => {
      const response = await apiClient.post<Project>('/api/v1/projects', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROJECTS_KEY });
    },
  });
}
```

### 3.4 SSE Streaming (Codegen)

#### 3.4.1 Route Handler for SSE

```typescript
// src/app/api/codegen/stream/route.ts
import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { session_id, prompt, provider } = body;

  // Get auth token from cookies
  const token = request.cookies.get('auth_token')?.value;
  if (!token) {
    return new Response('Unauthorized', { status: 401 });
  }

  // Create SSE stream to backend
  const backendUrl = `${process.env.BACKEND_URL}/api/v1/codegen/stream`;

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      try {
        const response = await fetch(backendUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ session_id, prompt, provider }),
        });

        const reader = response.body?.getReader();
        if (!reader) {
          controller.close();
          return;
        }

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          controller.enqueue(value);
        }
      } catch (error) {
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify({ error: 'Stream error' })}\n\n`)
        );
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  });
}
```

#### 3.4.2 Client Hook for SSE

```typescript
// src/hooks/useCodegenStream.ts
'use client';

import { useState, useCallback, useRef } from 'react';

interface CodegenEvent {
  type: 'code' | 'gate' | 'error' | 'complete';
  data: any;
}

export function useCodegenStream() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [events, setEvents] = useState<CodegenEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const startStream = useCallback(
    async (sessionId: string, prompt: string, provider: string) => {
      setIsStreaming(true);
      setEvents([]);
      setError(null);

      abortControllerRef.current = new AbortController();

      try {
        const response = await fetch('/api/codegen/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            prompt,
            provider,
          }),
          signal: abortControllerRef.current.signal,
        });

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) throw new Error('No reader available');

        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = JSON.parse(line.slice(6));
              setEvents((prev) => [...prev, data]);
            }
          }
        }
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          setError(err.message);
        }
      } finally {
        setIsStreaming(false);
      }
    },
    []
  );

  const stopStream = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
  }, []);

  return { isStreaming, events, error, startStream, stopStream };
}
```

### 3.5 Form Handling

#### 3.5.1 Form Pattern (React Hook Form + Zod)

```typescript
// src/components/gates/GateEvaluationForm.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useEvaluateGate } from '@/hooks/useGates';

const evaluationSchema = z.object({
  project_id: z.string().uuid(),
  gate_id: z.string().uuid(),
  evidence_ids: z.array(z.string().uuid()).min(1, 'At least one evidence required'),
  notes: z.string().optional(),
});

type EvaluationFormData = z.infer<typeof evaluationSchema>;

export function GateEvaluationForm({ gateId }: { gateId: string }) {
  const { mutate: evaluate, isPending } = useEvaluateGate();

  const form = useForm<EvaluationFormData>({
    resolver: zodResolver(evaluationSchema),
    defaultValues: {
      gate_id: gateId,
      evidence_ids: [],
      notes: '',
    },
  });

  const onSubmit = (data: EvaluationFormData) => {
    evaluate(data, {
      onSuccess: () => {
        form.reset();
      },
    });
  };

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {/* Form fields */}
      <Button type="submit" disabled={isPending}>
        {isPending ? 'Evaluating...' : 'Evaluate Gate'}
      </Button>
    </form>
  );
}
```

---

## 4. Component Migration Guide

### 4.1 Migration Checklist per Component

```markdown
## Component: [ComponentName]
- [ ] Create file in Next.js structure
- [ ] Add 'use client' if needed
- [ ] Update imports (relative → @/ aliases)
- [ ] Replace useNavigate → useRouter
- [ ] Replace useParams → useParams (next/navigation)
- [ ] Replace Link (react-router) → Link (next/link)
- [ ] Update TanStack Query patterns if needed
- [ ] Add TypeScript types
- [ ] Write unit test
- [ ] Manual QA test
```

### 4.2 Import Mapping

| React Router | Next.js |
|--------------|---------|
| `import { useNavigate } from 'react-router-dom'` | `import { useRouter } from 'next/navigation'` |
| `import { useParams } from 'react-router-dom'` | `import { useParams } from 'next/navigation'` |
| `import { Link } from 'react-router-dom'` | `import Link from 'next/link'` |
| `import { Outlet } from 'react-router-dom'` | `{children}` prop |
| `navigate('/path')` | `router.push('/path')` |
| `navigate(-1)` | `router.back()` |

### 4.3 Path Mapping

| Current Path | Next.js Path |
|--------------|--------------|
| `/` | `/(dashboard)/page.tsx` |
| `/projects` | `/(dashboard)/projects/page.tsx` |
| `/projects/:id` | `/(dashboard)/projects/[id]/page.tsx` |
| `/gates/:id/evaluate` | `/(dashboard)/gates/[id]/evaluate/page.tsx` |
| `/codegen/sessions/:id` | `/(dashboard)/codegen/sessions/[id]/page.tsx` |
| `/admin/users` | `/(admin)/users/page.tsx` |

---

## 5. Testing Strategy

### 5.1 Test Structure

```
__tests__/
├── unit/
│   ├── components/
│   │   ├── dashboard/
│   │   ├── gates/
│   │   └── codegen/
│   └── hooks/
├── integration/
│   ├── auth.test.tsx
│   ├── projects.test.tsx
│   └── gates.test.tsx
└── e2e/
    ├── auth.spec.ts
    ├── dashboard.spec.ts
    └── codegen.spec.ts
```

### 5.2 Unit Test Example

```typescript
// __tests__/unit/hooks/useProjects.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useProjects } from '@/hooks/useProjects';
import { apiClient } from '@/lib/api';

jest.mock('@/lib/api');

const wrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useProjects', () => {
  it('fetches projects successfully', async () => {
    const mockProjects = {
      items: [{ id: '1', name: 'Project 1' }],
      total: 1,
    };

    (apiClient.get as jest.Mock).mockResolvedValueOnce({ data: mockProjects });

    const { result } = renderHook(() => useProjects(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockProjects);
  });
});
```

### 5.3 E2E Test Example (Playwright)

```typescript
// e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/vi/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/vi/projects');
  });

  test('displays project list', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Projects' })).toBeVisible();
    await expect(page.getByTestId('project-card')).toHaveCount.greaterThan(0);
  });

  test('navigates to project detail', async ({ page }) => {
    await page.getByTestId('project-card').first().click();
    await expect(page).toHaveURL(/\/projects\/[a-f0-9-]+/);
  });

  test('navigation latency < 100ms', async ({ page }) => {
    const start = Date.now();
    await page.click('a[href*="/gates"]');
    await page.waitForLoadState('domcontentloaded');
    const duration = Date.now() - start;
    expect(duration).toBeLessThan(100);
  });
});
```

---

## 6. Performance Optimization

### 6.1 Bundle Optimization

```typescript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    optimizePackageImports: ['@radix-ui/react-icons', 'lucide-react'],
  },

  // Dynamic imports for heavy components
  modularizeImports: {
    'recharts': {
      transform: 'recharts/es6/{{member}}',
    },
  },

  // Bundle analyzer
  webpack: (config, { isServer }) => {
    if (process.env.ANALYZE === 'true') {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          reportFilename: isServer
            ? '../analyze/server.html'
            : './analyze/client.html',
        })
      );
    }
    return config;
  },
};

module.exports = nextConfig;
```

### 6.2 Code Splitting

```typescript
// Dynamic import for Monaco Editor
import dynamic from 'next/dynamic';

const PolicyEditor = dynamic(
  () => import('@/components/policies/PolicyEditor'),
  {
    loading: () => <EditorSkeleton />,
    ssr: false, // Monaco doesn't support SSR
  }
);

// Dynamic import for Recharts
const DashboardCharts = dynamic(
  () => import('@/components/dashboard/Charts'),
  {
    loading: () => <ChartSkeleton />,
  }
);
```

### 6.3 Image Optimization

```typescript
// Use next/image for optimized images
import Image from 'next/image';

export function UserAvatar({ user }: { user: User }) {
  return (
    <Image
      src={user.avatar_url || '/default-avatar.png'}
      alt={user.name}
      width={40}
      height={40}
      className="rounded-full"
      priority={false}
    />
  );
}
```

---

## 7. Rollback Plan

### 7.1 NGINX Rollback Configuration

```nginx
# Quick rollback: uncomment to restore Vite Dashboard
# location /platform-admin {
#     proxy_pass http://127.0.0.1:8310;
#     include /etc/nginx/snippets/proxy-params.conf;
# }

# Current: All dashboard routes to Next.js
location ~ ^/(vi|en)/(projects|gates|evidence|policies|codegen|sop|settings|admin) {
    proxy_pass http://127.0.0.1:8311;
    include /etc/nginx/snippets/proxy-params.conf;
}
```

### 7.2 Rollback Procedure

1. **Detect Issue** (monitoring alert or user report)
2. **Decision** (CTO approval for rollback)
3. **Execute** (< 5 minutes)
   ```bash
   cd /home/nqh/shared/SDLC-Orchestrator/infrastructure/nginx
   cp sdlc-server-rollback.conf sdlc-server-update.conf
   sudo bash update-sdlc-nginx.sh
   ```
4. **Verify** (curl tests + smoke test)
5. **Post-mortem** (root cause analysis)

---

## 8. Timeline

| Phase | Sprint | Duration | Deliverables |
|-------|--------|----------|--------------|
| Spike | 61 | 3-5 days | Shell, auth, 5 screens, go/no-go |
| Migration 1 | 62 | 2 weeks | Groups 2-5 (Dashboard, Gates, Evidence, Policies) |
| Migration 2 | 63 | 2 weeks | Groups 6-8 (Codegen, SOP, Admin) |
| Cutover | 64 | 1 week | NGINX switch, deprecate Vite, docs |

---

## 9. References

- [ADR-025: Frontend Platform Consolidation](../01-ADRs/ADR-025-Frontend-Platform-Consolidation-Nextjs-Monolith.md)
- [Route Migration Map](./Frontend-Migration-Route-Map.md)
- [Sprint 61-64 Plan](../../04-build/02-Sprint-Plans/SPRINT-61-64-FRONTEND-PLATFORM-CONSOLIDATION.md)
- [Next.js App Router Documentation](https://nextjs.org/docs/app)
- [TanStack Query v5 Documentation](https://tanstack.com/query/latest)
