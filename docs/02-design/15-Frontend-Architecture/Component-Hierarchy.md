# Component Hierarchy - SDLC Orchestrator Frontend

**Version**: 1.0.0
**Date**: February 1, 2026
**Status**: ✅ ACTIVE

---

## Application Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                         ROOT LAYOUT                             │
│  app/layout.tsx                                                 │
│  • QueryClientProvider (TanStack Query)                         │
│  • ThemeProvider (dark/light/system)                            │
│  • ErrorBoundary                                                │
│  • Toaster (notifications)                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│    AUTH LAYOUT GROUP     │    │     APP LAYOUT GROUP     │
│  app/(auth)/layout.tsx   │    │  app/app/layout.tsx      │
│  • Centered layout       │    │  • Header                │
│  • No sidebar            │    │  • Sidebar               │
│  • Public pages          │    │  • Main content area     │
└──────────────────────────┘    └──────────────────────────┘
         │                                  │
         │                                  │
    ┌────┴────┐                   ┌─────────┴─────────┐
    │         │                   │         │         │
    ▼         ▼                   ▼         ▼         ▼
┌──────┐  ┌──────┐        ┌──────┐  ┌──────┐  ┌──────┐
│Login │  │Signup│        │Teams │  │Projects│ │Gates │
│Page  │  │Page  │        │Pages │  │ Pages  │ │Pages │
└──────┘  └──────┘        └──────┘  └──────┘  └──────┘
```

---

## Page-Level Component Hierarchy

### 1. Teams Pages

```
app/app/teams/
│
├── page.tsx (Teams List)
│   ├── Header
│   │   ├── Breadcrumb
│   │   └── CreateTeamButton
│   ├── TeamsList
│   │   ├── TeamCard (multiple)
│   │   │   ├── Avatar
│   │   │   ├── TeamInfo
│   │   │   ├── MemberCount
│   │   │   └── TeamActions
│   │   │       ├── EditButton
│   │   │       └── DeleteButton
│   │   └── EmptyState (if no teams)
│   └── CreateTeamModal
│       ├── Dialog (shadcn/ui)
│       ├── Form (react-hook-form)
│       │   ├── Input (name)
│       │   ├── Textarea (description)
│       │   └── Select (tier)
│       └── FormActions
│           ├── CancelButton
│           └── SubmitButton
│
├── [id]/page.tsx (Team Details)
│   ├── Header
│   │   ├── Breadcrumb
│   │   ├── TeamName
│   │   └── TeamActions
│   ├── TabsNavigation
│   │   ├── OverviewTab
│   │   ├── MembersTab
│   │   ├── InvitationsTab
│   │   └── SettingsTab
│   ├── TeamOverview
│   │   ├── TeamInfoCard
│   │   ├── RecentActivityCard
│   │   └── ProjectsCard
│   └── TeamMembersCard
│       ├── MemberList
│       │   └── MemberRow (multiple)
│       │       ├── Avatar
│       │       ├── MemberInfo
│       │       ├── RoleBadge
│       │       └── MemberActions
│       └── InviteMemberButton
│
└── [id]/invitations/page.tsx (Team Invitations)
    ├── Header
    │   ├── BackButton
    │   ├── TeamName
    │   └── Description
    ├── PermissionWarning (if not admin)
    ├── InvitationList
    │   ├── InviteMemberButton (if admin)
    │   ├── Tabs (shadcn/ui)
    │   │   ├── PendingTab
    │   │   ├── AcceptedTab
    │   │   ├── ExpiredTab
    │   │   └── DeclinedTab
    │   ├── TabContent
    │   │   ├── InvitationCard (multiple)
    │   │   │   ├── Avatar
    │   │   │   ├── EmailInfo
    │   │   │   ├── StatusBadge
    │   │   │   ├── RoleInfo
    │   │   │   ├── Metadata
    │   │   │   │   ├── InvitedBy
    │   │   │   │   ├── CreatedAt
    │   │   │   │   └── ExpiresAt
    │   │   │   └── Actions
    │   │   │       ├── CancelButton (with AlertDialog)
    │   │   │       └── ResendButton
    │   │   └── EmptyState (if no invitations)
    │   └── InviteMemberModal
    │       ├── Dialog (shadcn/ui)
    │       ├── DialogHeader
    │       │   ├── DialogTitle
    │       │   └── DialogDescription
    │       ├── Form
    │       │   ├── EmailInput
    │       │   │   ├── Label
    │       │   │   ├── Input
    │       │   │   └── ErrorMessage
    │       │   ├── RoleSelect
    │       │   │   ├── Label
    │       │   │   ├── Select (shadcn/ui)
    │       │   │   │   ├── OwnerOption
    │       │   │   │   ├── AdminOption
    │       │   │   │   ├── MemberOption
    │       │   │   │   └── ViewerOption
    │       │   │   └── RoleDescription
    │       │   └── ErrorAlert (if error)
    │       └── DialogFooter
    │           ├── CancelButton
    │           └── SubmitButton (with loading state)
```

---

## Component Dependency Graph

```
Page Components
    │
    ├── Feature Components (domain-specific)
    │   │
    │   ├── UI Primitives (shadcn/ui)
    │   │   │
    │   │   └── Radix UI Primitives
    │   │
    │   └── Custom Hooks (data + logic)
    │       │
    │       ├── React Query (server state)
    │       │
    │       └── Zustand (client state)
    │
    └── Shared Components (cross-domain)
        │
        └── UI Primitives (shadcn/ui)
```

**Example Dependency Chain**:

```
InvitationsPage (app/teams/[id]/invitations/page.tsx)
    ↓ uses
InvitationList (components/teams/InvitationList.tsx)
    ↓ uses
InvitationCard (components/teams/InvitationCard.tsx)
    ↓ uses
Badge, Button, Card (components/ui/*)
    ↓ uses
Radix UI Primitives (@radix-ui/react-*)
    ↓ uses
useInvitations (hooks/useInvitations.ts)
        ↓ uses
    useQuery, useMutation (TanStack Query)
        ↓ uses
    api (lib/api.ts - Axios instance)
```

---

## State Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     USER INTERACTION                          │
│  (Click "Send Invitation" button)                            │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│               COMPONENT EVENT HANDLER                         │
│  handleSubmit() in InviteMemberModal.tsx                     │
│  • Validate email format                                     │
│  • Call sendInvitation()                                     │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                 CUSTOM HOOK (useInvitations)                  │
│  sendInvitation mutation (TanStack Query)                    │
│  • Execute mutationFn                                        │
│  • Handle loading state                                      │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                    API CLIENT (lib/api.ts)                    │
│  api.post("/teams/:id/invitations", data)                   │
│  • Add auth token (interceptor)                             │
│  • Send HTTP request                                        │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                  BACKEND API (FastAPI)                        │
│  POST /api/v1/teams/{team_id}/invitations                   │
│  • Validate request                                          │
│  • Create invitation record                                  │
│  • Send email                                                │
│  • Return response                                           │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│               MUTATION SUCCESS CALLBACK                       │
│  onSuccess() in useInvitations                               │
│  • Invalidate query cache                                    │
│  • Trigger refetch of invitations                           │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                  COMPONENT RE-RENDER                          │
│  InvitationList.tsx                                          │
│  • Display new invitation                                    │
│  • Show success message                                      │
│  • Close modal                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Flow: React Query Caching

```
┌──────────────────────────────────────────────────────────────┐
│                   INITIAL PAGE LOAD                           │
│  InvitationsPage mounts                                      │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│              useInvitations(teamId) HOOK                      │
│  useQuery({ queryKey: ["team-invitations", teamId] })       │
│  • Check cache for existing data                            │
│  • Cache MISS → Trigger queryFn                             │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                 FETCH FROM API                                │
│  api.get("/teams/:id/invitations")                          │
│  • isLoading = true                                          │
│  • Component shows Loading spinner                          │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│              CACHE DATA (React Query)                         │
│  queryClient.setQueryData(["team-invitations", teamId], data)│
│  • staleTime: 5 minutes (won't refetch)                     │
│  • cacheTime: 10 minutes (keep in memory)                   │
│  • isLoading = false                                         │
│  • Component renders data                                    │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│           USER NAVIGATES AWAY AND BACK                        │
│  InvitationsPage unmounts, then remounts                     │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│              useInvitations(teamId) HOOK                      │
│  • Check cache for existing data                            │
│  • Cache HIT (data still fresh) → Return cached data        │
│  • NO network request!                                       │
│  • Instant render                                            │
└──────────────────────────────────────────────────────────────┘
```

---

## Component Communication Patterns

### Pattern 1: Parent → Child (Props)

```typescript
// Parent passes data and callbacks to child
<InvitationCard
  invitation={invitation}
  onCancel={() => cancelInvitation(invitation.id)}
  onResend={() => resendInvitation(invitation.id)}
/>
```

### Pattern 2: Child → Parent (Callbacks)

```typescript
// Child calls parent's callback
function InviteMemberModal({ onClose, onSuccess }: Props) {
  const handleSubmit = async () => {
    await sendInvitation(data);
    onSuccess?.(); // Notify parent of success
    onClose();     // Close modal
  };
}
```

### Pattern 3: Sibling Communication (Shared State)

```typescript
// Option A: Lift state to parent
function ParentComponent() {
  const [selectedTab, setSelectedTab] = useState("pending");

  return (
    <>
      <TabsNavigation activeTab={selectedTab} onChange={setSelectedTab} />
      <TabContent activeTab={selectedTab} />
    </>
  );
}

// Option B: Use React Query cache
function Sibling1() {
  const { mutate } = useMutation({
    onSuccess: () => {
      queryClient.invalidateQueries(["shared-data"]);
    },
  });
}

function Sibling2() {
  const { data } = useQuery({ queryKey: ["shared-data"] });
  // Automatically re-fetches when Sibling1 invalidates cache
}
```

### Pattern 4: Global State (Zustand)

```typescript
// UI state shared across app
function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  // ...
}

function Header() {
  const { toggleSidebar } = useUIStore(); // Same store
  // ...
}
```

---

## Component Lifecycle Hooks

### Mounting Phase

```typescript
function Component() {
  // 1. Initial render (constructor in class components)
  const [state, setState] = useState(initialValue);

  // 2. useEffect with empty deps (componentDidMount)
  useEffect(() => {
    console.log("Component mounted");
    // Fetch data, subscribe to events
    return () => {
      console.log("Cleanup on unmount");
    };
  }, []);

  // 3. useEffect with deps (componentDidUpdate)
  useEffect(() => {
    console.log("Dependency changed");
  }, [dependency]);

  return <div>...</div>;
}
```

### Unmounting Phase

```typescript
useEffect(() => {
  // Setup
  const subscription = subscribeToEvents();

  // Cleanup (componentWillUnmount)
  return () => {
    subscription.unsubscribe();
  };
}, []);
```

---

## Error Handling Hierarchy

```
ErrorBoundary (app/layout.tsx)
    │
    ├── Catches all React errors
    │   (component render errors, lifecycle errors)
    │
    ├── API Error Handling (lib/api.ts interceptors)
    │   │
    │   ├── 401 Unauthorized → Redirect to login
    │   ├── 403 Forbidden → Show permission error
    │   ├── 429 Rate Limit → Show rate limit error
    │   └── 500 Server Error → Show generic error
    │
    └── Component-Level Error Handling
        │
        ├── Form Validation Errors (react-hook-form + zod)
        │   └── Show inline error messages
        │
        ├── Mutation Errors (TanStack Query)
        │   └── Display error alert in component
        │
        └── Query Errors (TanStack Query)
            └── Display error state with retry button
```

---

## Performance Optimization Hierarchy

```
App-Level Optimizations
    │
    ├── Code Splitting (Next.js dynamic imports)
    │   └── Split large components into separate bundles
    │
    ├── Image Optimization (Next.js Image component)
    │   └── Automatic lazy loading, WebP conversion
    │
    └── Route Prefetching (Next.js Link component)
        └── Prefetch routes on hover

Component-Level Optimizations
    │
    ├── React.memo (prevent unnecessary re-renders)
    │   └── Memoize expensive components
    │
    ├── useCallback (memoize event handlers)
    │   └── Prevent child re-renders
    │
    ├── useMemo (memoize expensive computations)
    │   └── Cache computed values
    │
    └── Virtual Lists (react-window)
        └── Render only visible items (long lists)

React Query Optimizations
    │
    ├── Query Caching (5 min staleTime)
    │   └── Avoid redundant API calls
    │
    ├── Optimistic Updates
    │   └── Instant UI feedback before API response
    │
    ├── Query Prefetching
    │   └── Fetch data before user navigates
    │
    └── Query Invalidation
        └── Selectively refetch stale data
```

---

## Accessibility Hierarchy

```
App-Level A11y
    │
    ├── Document Structure
    │   ├── Semantic HTML (header, nav, main, footer)
    │   ├── Skip to main content link
    │   └── Page title updates (Next.js Head)
    │
    ├── Keyboard Navigation
    │   ├── Tab order (tabindex)
    │   ├── Focus management (modals, dropdowns)
    │   └── Keyboard shortcuts
    │
    └── Screen Reader Support
        ├── ARIA landmarks
        ├── ARIA live regions
        └── ARIA labels

Component-Level A11y
    │
    ├── Forms
    │   ├── Label associations (htmlFor, id)
    │   ├── Error announcements (aria-describedby, role="alert")
    │   └── Required fields (aria-required)
    │
    ├── Modals
    │   ├── Focus trap (react-focus-lock)
    │   ├── Escape to close
    │   └── Focus restoration (return focus on close)
    │
    ├── Buttons
    │   ├── Accessible labels (aria-label)
    │   ├── Disabled state (aria-disabled)
    │   └── Loading state announcement
    │
    └── Dynamic Content
        ├── Live regions (aria-live)
        ├── Status announcements (role="status")
        └── Alert announcements (role="alert")
```

---

**Document Status**: ✅ ACTIVE
**Last Updated**: February 1, 2026
**Owner**: Frontend Team Lead
**Review Cycle**: Quarterly
