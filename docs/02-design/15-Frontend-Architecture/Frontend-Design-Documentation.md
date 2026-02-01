# Frontend Design Documentation - SDLC Orchestrator

**Version**: 1.0.0
**Date**: February 1, 2026
**Framework**: React 18 + Next.js 14 (App Router)
**UI Library**: shadcn/ui + Tailwind CSS
**Status**: ✅ ACTIVE

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Structure](#component-structure)
3. [Design Patterns](#design-patterns)
4. [State Management](#state-management)
5. [API Integration](#api-integration)
6. [UI/UX Guidelines](#uiux-guidelines)
7. [TypeScript Patterns](#typescript-patterns)
8. [Testing Strategy](#testing-strategy)
9. [Performance Optimization](#performance-optimization)
10. [Accessibility](#accessibility)

---

## 1. Architecture Overview

### Technology Stack

```yaml
Core:
  - React 18.2+ (hooks, suspense, concurrent mode)
  - Next.js 14.0+ (App Router, Server Components)
  - TypeScript 5.0+ (strict mode enabled)

State Management:
  - TanStack Query v5 (server state, caching)
  - Zustand (client state, lightweight)
  - React Context (theme, auth, simple shared state)

UI Framework:
  - shadcn/ui (Tailwind + Radix UI primitives)
  - Tailwind CSS v4 (utility-first CSS)
  - Lucide React (icon library)

Data Fetching:
  - TanStack Query (React Query v5)
  - Axios (HTTP client with interceptors)
  - SWR (optional, for real-time updates)

Forms & Validation:
  - React Hook Form (form state management)
  - Zod (schema validation)
  - yup (alternative validation)

Testing:
  - Vitest (unit tests, fast)
  - React Testing Library (component tests)
  - Playwright (E2E tests)

Build Tools:
  - Vite (dev server, fast HMR)
  - ESBuild (bundler)
  - PostCSS (CSS processing)
```

### Folder Structure

```
frontend/
├── public/                      # Static assets
│   ├── icons/
│   ├── images/
│   └── fonts/
├── src/
│   ├── app/                     # Next.js App Router pages
│   │   ├── (auth)/             # Auth layout group
│   │   │   ├── login/
│   │   │   ├── signup/
│   │   │   └── layout.tsx
│   │   ├── app/                # Authenticated app layout
│   │   │   ├── teams/
│   │   │   │   ├── [id]/
│   │   │   │   │   ├── invitations/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── members/
│   │   │   │   │   └── page.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── projects/
│   │   │   ├── gates/
│   │   │   └── layout.tsx
│   │   ├── layout.tsx          # Root layout
│   │   └── page.tsx            # Home page
│   ├── components/             # Reusable components
│   │   ├── ui/                 # shadcn/ui primitives
│   │   │   ├── button.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── card.tsx
│   │   │   └── ... (40+ components)
│   │   ├── teams/              # Team-specific components
│   │   │   ├── InviteMemberModal.tsx
│   │   │   ├── InvitationList.tsx
│   │   │   ├── InvitationCard.tsx
│   │   │   └── TeamMembersCard.tsx
│   │   ├── projects/           # Project-specific components
│   │   ├── gates/              # Gate-specific components
│   │   ├── evidence/           # Evidence-specific components
│   │   └── shared/             # Shared components
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       ├── ErrorBoundary.tsx
│   │       └── Loading.tsx
│   ├── hooks/                  # Custom React hooks
│   │   ├── useAuth.ts          # Authentication
│   │   ├── useTeams.ts         # Teams data
│   │   ├── useInvitations.ts   # Team invitations
│   │   ├── useProjects.ts      # Projects data
│   │   ├── useGates.ts         # Gates data
│   │   └── useDebounce.ts      # Utility hooks
│   ├── lib/                    # Utilities & helpers
│   │   ├── api.ts              # Axios instance + interceptors
│   │   ├── utils.ts            # Utility functions
│   │   ├── cn.ts               # Tailwind class merger
│   │   └── constants.ts        # App constants
│   ├── types/                  # TypeScript types
│   │   ├── api.ts              # API response types
│   │   ├── models.ts           # Data models
│   │   └── global.d.ts         # Global type declarations
│   ├── styles/                 # Global styles
│   │   └── globals.css         # Tailwind imports + custom CSS
│   └── middleware.ts           # Next.js middleware (auth)
├── e2e/                        # E2E tests (Playwright)
│   ├── auth.spec.ts
│   ├── teams.spec.ts
│   ├── invitations.spec.ts
│   └── gates.spec.ts
└── tests/                      # Unit tests (Vitest)
    ├── components/
    ├── hooks/
    └── utils/
```

---

## 2. Component Structure

### Component Anatomy

Every component follows this standard structure:

```typescript
"use client"; // Only for client components (Next.js App Router)

import { useState } from "react"; // React imports first
import { Button } from "@/components/ui/button"; // UI components
import { useAuth } from "@/hooks/useAuth"; // Custom hooks
import { api } from "@/lib/api"; // Utilities

// TypeScript interfaces (Props, State, etc.)
interface ComponentNameProps {
  id: string;
  name: string;
  onSubmit?: (data: FormData) => void;
  children?: React.ReactNode;
}

interface FormData {
  email: string;
  role: string;
}

// Main component function (PascalCase)
export function ComponentName({
  id,
  name,
  onSubmit,
  children,
}: ComponentNameProps) {
  // 1. Hooks (useState, useEffect, custom hooks)
  const [isLoading, setIsLoading] = useState(false);
  const { user } = useAuth();

  // 2. Event handlers (handle prefix)
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await api.post("/endpoint", data);
      onSubmit?.(data);
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  // 3. Computed values (const declarations)
  const isDisabled = isLoading || !user;

  // 4. Render (JSX)
  return (
    <div className="container">
      <h1>{name}</h1>
      <Button onClick={handleSubmit} disabled={isDisabled}>
        Submit
      </Button>
      {children}
    </div>
  );
}
```

### Component Types

```yaml
1. Page Components (app/*/page.tsx):
   - Entry points for routes
   - Fetch data with React Query
   - Layout structure + composition
   - Example: app/teams/[id]/invitations/page.tsx

2. Feature Components (components/domain/*):
   - Domain-specific logic
   - Composed of UI primitives
   - Example: components/teams/InviteMemberModal.tsx

3. UI Primitives (components/ui/*):
   - shadcn/ui components
   - Unstyled Radix UI + Tailwind
   - Example: components/ui/button.tsx

4. Shared Components (components/shared/*):
   - Reusable across features
   - Header, Sidebar, ErrorBoundary
   - Example: components/shared/Header.tsx

5. Layout Components (app/*/layout.tsx):
   - Wrap pages with common structure
   - Auth layout, App layout, Public layout
   - Example: app/app/layout.tsx
```

---

## 3. Design Patterns

### Pattern 1: Custom Hooks for Data Fetching

**Problem**: Components become bloated with API logic.

**Solution**: Extract data fetching into custom hooks.

```typescript
// hooks/useInvitations.ts
export function useInvitations(teamId: string) {
  // React Query for server state
  const { data, isLoading, error, refetch } = useQuery<TeamInvitation[]>({
    queryKey: ["team-invitations", teamId],
    queryFn: async () => {
      const response = await api.get(`/teams/${teamId}/invitations`);
      return response.data;
    },
    enabled: !!teamId,
  });

  // Mutations for actions
  const { mutateAsync: sendInvitation, isPending: isSending } = useMutation({
    mutationFn: async (data: SendInvitationRequest) => {
      return api.post(`/teams/${teamId}/invitations`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team-invitations", teamId] });
    },
  });

  // Computed values
  const pendingInvitations = data?.filter((i) => i.status === "pending") || [];

  // Return API
  return {
    invitations: data || [],
    pendingInvitations,
    isLoading,
    error,
    sendInvitation,
    isSending,
    refetch,
  };
}

// Usage in component
function InvitationList({ teamId }: Props) {
  const { pendingInvitations, sendInvitation, isSending } = useInvitations(teamId);

  return (
    <div>
      {pendingInvitations.map((inv) => (
        <InvitationCard key={inv.id} invitation={inv} />
      ))}
    </div>
  );
}
```

**Benefits**:
- ✅ Components stay focused on UI logic
- ✅ Data logic is reusable across components
- ✅ Automatic caching + refetching (React Query)
- ✅ Easy to test (mock hook, not API calls)

---

### Pattern 2: Controlled vs Uncontrolled Components

**Controlled Components** (React Hook Form):

```typescript
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const schema = z.object({
  email: z.string().email("Invalid email"),
  role: z.enum(["owner", "admin", "member", "viewer"]),
});

type FormData = z.infer<typeof schema>;

function InviteForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { role: "member" },
  });

  const onSubmit = (data: FormData) => {
    console.log(data); // Validated data
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("email")} />
      {errors.email && <p>{errors.email.message}</p>}

      <select {...register("role")}>
        <option value="owner">Owner</option>
        <option value="admin">Admin</option>
        <option value="member">Member</option>
        <option value="viewer">Viewer</option>
      </select>

      <button type="submit">Submit</button>
    </form>
  );
}
```

**Benefits**:
- ✅ Automatic validation with Zod
- ✅ Type-safe form data
- ✅ Less boilerplate (no manual state management)
- ✅ Performance optimized (uncontrolled inputs)

---

### Pattern 3: Composition over Inheritance

**Bad Pattern** (Inheritance):

```typescript
// ❌ DON'T: Extend base component
class BaseModal extends React.Component {
  render() { return <dialog>...</dialog> }
}

class InviteMemberModal extends BaseModal {
  // Override methods
}
```

**Good Pattern** (Composition):

```typescript
// ✅ DO: Compose smaller components
function InviteMemberModal({ teamId, onClose }: Props) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Invite Member</DialogTitle>
        </DialogHeader>
        <InviteForm teamId={teamId} />
        <DialogFooter>
          <Button onClick={onClose}>Cancel</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

**Benefits**:
- ✅ Flexible composition (combine any components)
- ✅ Easier to test (smaller units)
- ✅ Better TypeScript inference

---

### Pattern 4: Error Boundaries

```typescript
// components/shared/ErrorBoundary.tsx
import { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
    // Send to error tracking service (Sentry, etc.)
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="error-fallback">
            <h2>Something went wrong</h2>
            <button onClick={() => this.setState({ hasError: false })}>
              Try again
            </button>
          </div>
        )
      );
    }

    return this.props.children;
  }
}

// Usage in app/layout.tsx
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </body>
    </html>
  );
}
```

---

## 4. State Management

### State Classification

```yaml
1. Server State (React Query):
   - Data from API (teams, projects, gates)
   - Cached, refetched automatically
   - Example: useTeams(), useProjects()

2. Client State (Zustand):
   - UI state (sidebar open/closed, theme)
   - Form state (multi-step wizards)
   - Example: useUIStore(), useThemeStore()

3. Local State (useState):
   - Component-specific state
   - Form inputs, modals open/closed
   - Example: const [isOpen, setIsOpen] = useState(false)

4. URL State (Next.js Router):
   - Filters, pagination, search
   - Shareable links
   - Example: ?page=2&filter=pending
```

### React Query Configuration

```typescript
// lib/queryClient.ts
import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});
```

### Zustand Store Example

```typescript
// stores/uiStore.ts
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UIStore {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  theme: "light" | "dark" | "system";
  setTheme: (theme: "light" | "dark" | "system") => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      theme: "system",
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: "ui-store", // localStorage key
    }
  )
);
```

---

## 5. API Integration

### Axios Instance Configuration

```typescript
// lib/api.ts
import axios, { AxiosError, AxiosResponse } from "axios";
import { useAuthStore } from "@/stores/authStore";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor (add auth token)
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor (handle errors)
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    // Handle 401 Unauthorized (token expired)
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = "/login";
    }

    // Handle 403 Forbidden
    if (error.response?.status === 403) {
      console.error("Permission denied");
    }

    // Handle 429 Rate Limit
    if (error.response?.status === 429) {
      console.error("Rate limit exceeded");
    }

    return Promise.reject(error);
  }
);
```

---

## 6. UI/UX Guidelines

### Design System (shadcn/ui)

**Color Palette** (Tailwind CSS Variables):

```css
/* styles/globals.css */
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* ... dark mode values */
  }
}
```

**Typography**:

```yaml
Headings:
  - h1: text-4xl font-bold (36px)
  - h2: text-3xl font-bold (30px)
  - h3: text-2xl font-semibold (24px)
  - h4: text-xl font-semibold (20px)
  - h5: text-lg font-medium (18px)
  - h6: text-base font-medium (16px)

Body:
  - text-base: 16px (default)
  - text-sm: 14px (small)
  - text-xs: 12px (extra small)

Line Height:
  - leading-tight: 1.25
  - leading-normal: 1.5
  - leading-relaxed: 1.75
```

**Spacing** (Tailwind):

```yaml
Padding/Margin:
  - p-0: 0px
  - p-1: 4px
  - p-2: 8px
  - p-3: 12px
  - p-4: 16px
  - p-6: 24px
  - p-8: 32px
  - p-12: 48px
  - p-16: 64px

Container Widths:
  - max-w-sm: 640px
  - max-w-md: 768px
  - max-w-lg: 1024px
  - max-w-xl: 1280px
  - max-w-2xl: 1536px
```

**Component Variants**:

```typescript
// Example: Button variants (shadcn/ui pattern)
const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent",
        ghost: "hover:bg-accent hover:text-accent-foreground",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 px-3",
        lg: "h-11 px-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);
```

---

## 7. TypeScript Patterns

### Type-Safe API Responses

```typescript
// types/api.ts
export interface APIResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// types/models.ts
export interface TeamInvitation {
  id: string;
  team_id: string;
  invited_email: string;
  role: "owner" | "admin" | "member" | "viewer";
  status: "pending" | "accepted" | "declined" | "expired";
  invited_by: string;
  expires_at: string;
  created_at: string;
  accepted_at?: string;
  declined_at?: string;
}

// Usage with React Query
function useInvitations(teamId: string) {
  return useQuery<APIResponse<TeamInvitation[]>>({
    queryKey: ["invitations", teamId],
    queryFn: () => api.get(`/teams/${teamId}/invitations`).then((res) => res.data),
  });
}
```

### Discriminated Unions

```typescript
// For handling different states
type LoadingState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: Error };

function Component() {
  const [state, setState] = useState<LoadingState<TeamInvitation[]>>({
    status: "idle",
  });

  // TypeScript knows what properties are available based on status
  if (state.status === "success") {
    console.log(state.data); // ✅ data is available
  }

  if (state.status === "error") {
    console.log(state.error); // ✅ error is available
  }
}
```

---

## 8. Testing Strategy

### Unit Tests (Vitest + React Testing Library)

```typescript
// components/teams/InviteMemberModal.test.tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { InviteMemberModal } from "./InviteMemberModal";

describe("InviteMemberModal", () => {
  it("should send invitation with valid data", async () => {
    const mockSendInvitation = vi.fn().mockResolvedValue({ success: true });

    render(<InviteMemberModal teamId="123" onClose={vi.fn()} />);

    // Fill form
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "test@example.com" },
    });

    // Submit
    fireEvent.click(screen.getByText("Send Invitation"));

    // Assert
    await waitFor(() => {
      expect(mockSendInvitation).toHaveBeenCalledWith({
        email: "test@example.com",
        role: "member",
      });
    });
  });
});
```

### E2E Tests (Playwright)

```typescript
// e2e/invitations.spec.ts
import { test, expect } from "@playwright/test";

test("should send invitation successfully", async ({ page }) => {
  // Login
  await page.goto("/login");
  await page.fill('input[type="email"]', "owner@example.com");
  await page.click('button[type="submit"]');

  // Navigate to invitations
  await page.goto("/app/teams/test-team/invitations");

  // Click "Invite Member"
  await page.click('button:has-text("Invite Member")');

  // Fill form
  await page.fill('input[type="email"]', "newmember@example.com");

  // Submit
  await page.click('button:has-text("Send Invitation")');

  // Assert invitation appears
  await expect(page.locator("text=newmember@example.com")).toBeVisible();
});
```

---

## 9. Performance Optimization

### Code Splitting (Next.js)

```typescript
// Dynamic imports for large components
import dynamic from "next/dynamic";

const InviteMemberModal = dynamic(
  () => import("@/components/teams/InviteMemberModal"),
  {
    loading: () => <div>Loading...</div>,
    ssr: false, // Client-side only
  }
);
```

### React.memo for Expensive Components

```typescript
import { memo } from "react";

export const InvitationCard = memo(function InvitationCard({ invitation }: Props) {
  // Expensive rendering logic
  return <div>...</div>;
}, (prevProps, nextProps) => {
  // Custom comparison
  return prevProps.invitation.id === nextProps.invitation.id;
});
```

### Virtual Lists (react-window)

```typescript
import { FixedSizeList } from "react-window";

function InvitationList({ invitations }: Props) {
  return (
    <FixedSizeList
      height={600}
      itemCount={invitations.length}
      itemSize={80}
      width="100%"
    >
      {({ index, style }) => (
        <div style={style}>
          <InvitationCard invitation={invitations[index]} />
        </div>
      )}
    </FixedSizeList>
  );
}
```

---

## 10. Accessibility

### WCAG 2.1 AA Compliance

```yaml
Keyboard Navigation:
  - ✅ All interactive elements focusable (Tab key)
  - ✅ Skip to main content link
  - ✅ Modal traps focus when open (Escape to close)
  - ✅ Dropdowns navigable with Arrow keys

Screen Reader Support:
  - ✅ Semantic HTML (header, nav, main, footer)
  - ✅ ARIA labels for icon buttons
  - ✅ Live regions for dynamic content (aria-live)
  - ✅ Form labels properly associated

Color Contrast:
  - ✅ Text: 4.5:1 ratio (WCAG AA)
  - ✅ Large text: 3:1 ratio
  - ✅ Focus indicators visible
  - ✅ Dark mode support

Error Handling:
  - ✅ Error messages linked to inputs (aria-describedby)
  - ✅ Error summary at top of form
  - ✅ Visible error icons
```

### Example: Accessible Form

```typescript
<form onSubmit={handleSubmit} aria-labelledby="form-title">
  <h2 id="form-title">Invite Member</h2>

  <div>
    <label htmlFor="email">Email Address</label>
    <input
      id="email"
      type="email"
      aria-required="true"
      aria-invalid={!!errors.email}
      aria-describedby={errors.email ? "email-error" : undefined}
    />
    {errors.email && (
      <p id="email-error" role="alert">
        {errors.email.message}
      </p>
    )}
  </div>

  <button type="submit" aria-disabled={isLoading}>
    {isLoading ? "Sending..." : "Send Invitation"}
  </button>
</form>
```

---

## Appendix: Component Checklist

**Before Creating a New Component**:

- [ ] Is this a new UI primitive? → Add to `components/ui/`
- [ ] Is this domain-specific? → Add to `components/{domain}/`
- [ ] Is this reusable across features? → Add to `components/shared/`
- [ ] Does it need data fetching? → Create custom hook in `hooks/`
- [ ] Is it a page? → Add to `app/*/page.tsx`

**Component Requirements**:

- [ ] TypeScript interfaces for props
- [ ] "use client" directive if client component
- [ ] Proper error handling (try/catch)
- [ ] Loading states (isLoading, isSending)
- [ ] Accessibility (ARIA labels, keyboard navigation)
- [ ] Unit test (`.test.tsx`)
- [ ] E2E test (if critical user journey)
- [ ] Documentation (JSDoc comments)

**Performance Checklist**:

- [ ] Use React.memo for expensive renders
- [ ] Avoid inline functions in render
- [ ] Use useCallback for event handlers
- [ ] Use useMemo for expensive computations
- [ ] Dynamic imports for large components
- [ ] Virtual lists for long lists (>100 items)

---

**Document Status**: ✅ ACTIVE
**Last Updated**: February 1, 2026
**Owner**: Frontend Team Lead
**Review Cycle**: Monthly
