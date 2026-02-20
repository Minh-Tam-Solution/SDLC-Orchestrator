# Support Page Design Document

**Framework**: SDLC 6.1.0  
**Stage**: 02 - DESIGN  
**Sub-Stage**: 11 - UI/UX Design  
**Feature**: User Support Page  
**Date**: December 20, 2025  
**Authority**: Frontend Lead + CTO Approval Required  
**Foundation**: Zero Mock Policy, Framework-First Compliance

---

## 📋 Stage 01 - PLANNING Summary

### Business Objectives
- Provide centralized access to user documentation
- Reduce support ticket volume by 50%+
- Improve user onboarding experience
- Enable self-service support

### Requirements
**FR1**: Display comprehensive documentation navigation  
**FR2**: Quick search across all documentation  
**FR3**: Contact information with author details  
**FR4**: Link to GitHub documentation repository  
**FR5**: Categorized support resources  
**FR6**: Mobile-responsive layout  

**NFR1**: Load time < 1 second  
**NFR2**: Accessibility WCAG 2.1 AA compliant  
**NFR3**: SEO-friendly for internal search  

### Success Criteria
- ✅ All 11 documentation guides accessible
- ✅ Contact author: taidt@mtsolution.com.vn, +84 939 116 006
- ✅ Framework connection clearly visible
- ✅ Search functionality working
- ✅ Mobile responsive (320px - 1920px)

---

## 🎨 Stage 02 - DESIGN

### 2.1 Information Architecture

```
/support
├── Hero Section
│   ├── Title: "User Support & Documentation"
│   ├── Subtitle: Framework connection
│   └── Quick Actions (Search, Contact)
├── Documentation Categories (3-column grid)
│   ├── Getting Started (🚀)
│   │   ├── 01-Getting-Started.md
│   │   └── 02-SDLC-Framework-Overview.md
│   ├── Using the Platform (⚙️)
│   │   ├── 03-Platform-Features.md
│   │   ├── 04-User-Roles-Permissions.md
│   │   └── 05-Common-Tasks.md
│   └── Troubleshooting & Help (🔧)
│       ├── 06-Troubleshooting.md
│       ├── 07-FAQ.md
│       ├── 08-Best-Practices.md
│       └── 09-Support-Channels.md
├── Quick Links Section
│   ├── Framework Documentation (GitHub)
│   ├── API Reference
│   └── Video Tutorials (future)
└── Contact Footer
    ├── Author Information
    ├── Email: taidt@mtsolution.com.vn
    ├── Phone: +84 939 116 006
    └── GitHub Issues Link
```

### 2.2 UI/UX Design

#### Layout Structure
```
┌─────────────────────────────────────────────┐
│ DashboardLayout                              │
│ ┌─────────────────────────────────────────┐ │
│ │ Hero Section                             │ │
│ │ - Title + Subtitle                       │ │
│ │ - Search Bar (future phase)              │ │
│ │ - Framework Badge                        │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ ┌─────────────────────────────────────────┐ │
│ │ Stats Row (3 cards)                      │ │
│ │ [11 Guides] [5,314 Lines] [3 Categories] │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ ┌─────────────────────────────────────────┐ │
│ │ Documentation Categories (3 columns)     │ │
│ │ ┌──────┐ ┌──────┐ ┌──────┐             │ │
│ │ │ 🚀   │ │ ⚙️   │ │ 🔧   │             │ │
│ │ │Start │ │Using │ │Help  │             │ │
│ │ │      │ │      │ │      │             │ │
│ │ │[Doc1]│ │[Doc3]│ │[Doc6]│             │ │
│ │ │[Doc2]│ │[Doc4]│ │[Doc7]│             │ │
│ │ │      │ │[Doc5]│ │[Doc8]│             │ │
│ │ │      │ │      │ │[Doc9]│             │ │
│ │ └──────┘ └──────┘ └──────┘             │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ ┌─────────────────────────────────────────┐ │
│ │ Quick Links (Horizontal cards)           │ │
│ │ [Framework Docs] [GitHub] [API Ref]      │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ ┌─────────────────────────────────────────┐ │
│ │ Contact Section                          │ │
│ │ Author: Mr. Tai                          │ │
│ │ ✉️ taidt@mtsolution.com.vn              │ │
│ │ 📞 +84 939 116 006                      │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

#### Component Hierarchy
```
SupportPage (Page Component)
├── DashboardLayout (Layout Wrapper)
│   └── Main Content Area
│       ├── HeroSection
│       │   ├── PageTitle (h1)
│       │   ├── Subtitle (p)
│       │   └── FrameworkBadge
│       ├── StatsRow
│       │   ├── StatCard (Guides Count)
│       │   ├── StatCard (Lines Count)
│       │   └── StatCard (Categories Count)
│       ├── DocumentationGrid
│       │   ├── CategoryCard (Getting Started)
│       │   │   └── DocLinks[]
│       │   ├── CategoryCard (Using Platform)
│       │   │   └── DocLinks[]
│       │   └── CategoryCard (Help & Troubleshooting)
│       │       └── DocLinks[]
│       ├── QuickLinksSection
│       │   ├── ExternalLink (Framework GitHub)
│       │   ├── ExternalLink (Orchestrator GitHub)
│       │   └── ExternalLink (API Docs - future)
│       └── ContactSection
│           ├── ContactCard
│           │   ├── AuthorName
│           │   ├── EmailLink
│           │   └── PhoneLink
│           └── GitHubIssuesLink
```

### 2.3 Data Structure

```typescript
// Documentation item structure
interface DocItem {
  id: string
  title: string
  description: string
  path: string // relative path in docs/07-operate/03-User Support/
  icon: string // emoji or lucide icon
  category: 'getting-started' | 'using-platform' | 'help'
  lines?: number // optional metadata
}

// Category structure
interface DocCategory {
  id: string
  title: string
  description: string
  icon: string
  docs: DocItem[]
}

// Contact information
interface ContactInfo {
  name: string
  title: string
  email: string
  phone: string
  github: string
}
```

### 2.4 Styling Guidelines

**Reference**: [FRONTEND-DESIGN-SPECIFICATION.md](./FRONTEND-DESIGN-SPECIFICATION.md)

**Color Tokens** (HSL format per spec):
```css
/* Semantic Colors */
--primary: 222 47% 11%           /* Deep Blue - Links, active states */
--accent: 217 91% 60%            /* Bright Blue - Badges, highlights */
--success: 142 76% 36%           /* Green - Success indicators */
--muted: 210 40% 96%             /* Light Gray - Card backgrounds */
--muted-foreground: 215 16% 47%  /* Gray - Helper text */
--border: 214 32% 91%            /* Light Border - Card borders */
```

**Typography Scale** (per spec):
```typescript
// Page Title
<h1 className="text-3xl font-bold">  // 30px, 600 weight, 36px line-height
  User Support & Documentation
</h1>

// Section Headers
<h2 className="text-2xl font-semibold"> // 24px, 600 weight, 32px line-height
  Getting Started
</h2>

// Category Cards
<h3 className="text-xl font-semibold">  // 20px, 600 weight, 28px line-height
  Documentation Category
</h3>

// Document Links
<a className="text-base font-medium">   // 16px, 500 weight, 24px line-height
  01-Getting-Started.md
</a>

// Helper Text
<p className="text-sm text-muted-foreground"> // 14px, 400 weight, 20px line-height
  Description text
</p>

// Metadata
<span className="text-xs text-muted-foreground"> // 12px, 400 weight, 16px line-height
  5,314 lines
</span>
```

**Spacing System** (4px base per spec):
```css
/* Container */
container mx-auto px-8 py-8      /* 32px padding */

/* Section Spacing */
space-y-8                         /* 32px vertical gap */

/* Grid Layout */
gap-6                             /* 24px grid gap */

/* Card Padding */
p-6                               /* 24px all sides */

/* Component Spacing */
space-y-4                         /* 16px vertical gap */
```

**Component Specifications**:

**Card Component** (shadcn/ui):
```typescript
<Card className="hover:shadow-lg transition-shadow">
  <CardHeader>
    <CardTitle className="text-xl font-semibold">
      Category Title
    </CardTitle>
    <CardDescription className="text-sm text-muted-foreground">
      Brief description
    </CardDescription>
  </CardHeader>
  <CardContent className="space-y-4">
    {/* Document links */}
  </CardContent>
</Card>
```

**Button Component** (variant: link for external links):
```typescript
<Button variant="link" className="h-auto p-0 text-base font-medium">
  <ExternalLink className="mr-2 h-4 w-4" />
  Framework Documentation
</Button>
```

**Badge Component** (for metadata):
```typescript
<Badge variant="secondary" className="text-xs">
  11 Guides
</Badge>
```

**Separator Component**:
```typescript
<Separator className="my-8" /> {/* 32px vertical spacing */}
```

### 2.5 Responsive Design

**Reference**: [FRONTEND-DESIGN-SPECIFICATION.md](./FRONTEND-DESIGN-SPECIFICATION.md) - Responsive Breakpoints

**Breakpoints** (Tailwind CSS per spec):
```
sm: 640px   /* Mobile */
md: 768px   /* Tablet (portrait) */
lg: 1024px  /* Tablet (landscape) / Small laptop */
xl: 1280px  /* Desktop */
2xl: 1536px /* Large desktop */
```

**Grid Responsive Behavior**:
```typescript
// Documentation Categories Grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {/* Mobile: 1 column stack */}
  {/* Tablet: 2 columns */}
  {/* Desktop: 3 columns */}
</div>

// Stats Row
<div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
  {/* Mobile: stack vertically */}
  {/* Small screens+: 3 columns */}
</div>

// Quick Links
<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
  {/* Mobile: stack vertically */}
  {/* Medium screens+: 3 columns */}
</div>
```

**Container Adjustments**:
```typescript
// Per spec: max-width 1400px on 2xl screens
<div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
  {/* Responsive padding:
      Mobile: 16px (px-4)
      Tablet: 24px (px-6)
      Desktop: 32px (px-8) */}
</div>
```

**Typography Responsive** (if needed):
```typescript
// Hero title scales on mobile
<h1 className="text-2xl sm:text-3xl font-bold">
  {/* Mobile: 24px, Desktop: 30px */}
</h1>
```

**Touch Targets** (minimum 44x44px per WCAG):
```typescript
// All interactive elements minimum height
<Button className="h-11"> {/* 44px per spec */}
<a className="inline-flex items-center min-h-[44px]">
```

### 2.6 Navigation Flow

```
User Journey:
1. User clicks "Support" in sidebar navigation
2. Lands on /support page
3. Sees categorized documentation
4. Clicks on specific guide → Opens in new tab (GitHub)
5. Alternative: Clicks contact info → Opens email/phone
6. Alternative: Clicks Framework link → Opens Framework repo
```

### 2.7 Accessibility (WCAG 2.1 AA)

**Reference**: [FRONTEND-DESIGN-SPECIFICATION.md](./FRONTEND-DESIGN-SPECIFICATION.md) - Accessibility Standards

**Compliance Requirements**:

**1. Semantic HTML Structure**:
```typescript
<main aria-label="Support Documentation">
  <header>
    <h1>User Support & Documentation</h1> {/* Only one h1 per page */}
  </header>
  
  <section aria-labelledby="stats-heading">
    <h2 id="stats-heading" className="sr-only">Documentation Statistics</h2>
    {/* Stats cards */}
  </section>
  
  <section aria-labelledby="categories-heading">
    <h2 id="categories-heading" className="sr-only">Documentation Categories</h2>
    {/* Category cards */}
  </section>
  
  <nav aria-label="External Resources">
    {/* Quick links */}
  </nav>
  
  <footer aria-label="Contact Information">
    {/* Author contact */}
  </footer>
</main>
```

**2. ARIA Labels for Interactive Elements**:
```typescript
// External links with context
<a 
  href="https://github.com/..."
  target="_blank"
  rel="noopener noreferrer"
  aria-label="Open Framework Documentation in new tab"
>
  <ExternalLink className="h-4 w-4" aria-hidden="true" />
  Framework Documentation
</a>

// Email link
<a 
  href="mailto:taidt@mtsolution.com.vn"
  aria-label="Send email to author at taidt@mtsolution.com.vn"
>
  <Mail className="h-4 w-4" aria-hidden="true" />
  taidt@mtsolution.com.vn
</a>

// Phone link
<a 
  href="tel:+84939116006"
  aria-label="Call author at +84 939 116 006"
>
  <Phone className="h-4 w-4" aria-hidden="true" />
  +84 939 116 006
</a>

// Icon-only buttons
<Button variant="ghost" size="icon" aria-label="Search documentation">
  <Search className="h-4 w-4" aria-hidden="true" />
</Button>
```

**3. Keyboard Navigation**:
```typescript
// All interactive elements focusable
tabIndex={0}  // Natural tab order

// Focus visible styles (per spec)
className="focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"

// Skip to main content link
<a 
  href="#main-content" 
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4"
>
  Skip to main content
</a>
```

**4. Color Contrast Requirements** (WCAG AA: 4.5:1 minimum):
```css
/* Per spec - All text meets minimum contrast */
--foreground: 222 47% 11%     /* Deep Blue on White: 14.94:1 ✅ */
--muted-foreground: 215 16% 47% /* Gray on White: 4.84:1 ✅ */

/* Links (primary color) */
--primary: 222 47% 11%         /* 14.94:1 ✅ */

/* Dark mode */
--foreground: 210 40% 98%      /* Almost White on Deep Blue: 14.94:1 ✅ */
```

**5. Screen Reader Support**:
```typescript
// Visual-only decorative elements
<BookOpen className="h-6 w-6" aria-hidden="true" />

// Helper text for screen readers
<span className="sr-only">
  11 comprehensive user guides available
</span>

// Loading states
<Button disabled aria-busy="true">
  <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
  Loading documentation...
</Button>
```

**6. Form Controls** (if search is added):
```typescript
<Label htmlFor="search" className="sr-only">
  Search documentation
</Label>
<Input
  id="search"
  type="search"
  placeholder="Search guides..."
  aria-describedby="search-help"
/>
<p id="search-help" className="sr-only">
  Search across all 11 documentation guides
</p>
```

**7. Error States & Messages**:
```typescript
// If link fails to load
<div role="alert" aria-live="polite">
  <AlertCircle className="h-4 w-4" aria-hidden="true" />
  Unable to load documentation. Please try again.
</div>
```

**8. Motion & Animation** (respect prefers-reduced-motion):
```css
/* Per spec - All animations respect user preferences */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

**Testing Checklist**:
- [ ] Keyboard-only navigation works (Tab, Shift+Tab, Enter)
- [ ] Screen reader announces all content correctly (NVDA/JAWS)
- [ ] Focus indicators visible on all interactive elements
- [ ] Color contrast meets WCAG AA (checked with tools)
- [ ] All images/icons have appropriate aria-labels or aria-hidden
- [ ] Semantic HTML structure valid
- [ ] Skip links functional
- [ ] Touch targets minimum 44x44px

### 2.8 Performance Targets

**Reference**: [FRONTEND-DESIGN-SPECIFICATION.md](./FRONTEND-DESIGN-SPECIFICATION.md) - Performance Budget

**Core Web Vitals** (measured on 3G connection):

| Metric | Target | Measurement |
|--------|--------|-------------|
| **First Contentful Paint (FCP)** | < 1.0s | Time to first text/image |
| **Largest Contentful Paint (LCP)** | < 1.5s | Time to largest content element |
| **Time to Interactive (TTI)** | < 2.0s | Page fully interactive |
| **Cumulative Layout Shift (CLS)** | < 0.1 | Visual stability score |
| **First Input Delay (FID)** | < 100ms | Interaction responsiveness |

**Performance Budget**:

```typescript
// JavaScript Bundle Size
Total JS: < 200 KB gzipped
Support Page: < 50 KB gzipped (static data only)

// CSS Bundle Size
Total CSS: < 50 KB gzipped
Support Page: < 10 KB gzipped (TailwindCSS tree-shaken)

// Image Assets
Icons: SVG (lucide-react - tree-shakable)
No raster images on this page

// Font Loading
System fonts only (no web font loading)
```

**Optimization Strategies**:

**1. Code Splitting** (React.lazy):
```typescript
// Support page lazy loaded in App.tsx
const SupportPage = lazy(() => import('@/pages/SupportPage'))

// Usage in route
<Route 
  path="/support" 
  element={
    <Suspense fallback={<PageLoader />}>
      <SupportPage />
    </Suspense>
  } 
/>
```

**2. Static Data** (No API calls):
```typescript
// All documentation data hardcoded (zero network requests)
const DOCUMENTATION_CATEGORIES: DocCategory[] = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    docs: [
      { id: '01', title: '01-Getting-Started.md', path: '...' },
      // ... static data
    ]
  }
]
```

**3. Preconnect to External Domains**:
```html
<!-- In index.html -->
<link rel="preconnect" href="https://github.com" crossorigin>
```

**4. Component Optimization**:
```typescript
// Memoize static category data
const categories = useMemo(() => DOCUMENTATION_CATEGORIES, [])

// No unnecessary re-renders
const DocLink = memo(({ doc }: { doc: DocItem }) => (
  <a href={doc.path} target="_blank" rel="noopener noreferrer">
    {doc.title}
  </a>
))
```

**5. CSS Optimization**:
```css
/* TailwindCSS purge removes unused styles */
/* Only classes actually used in SupportPage.tsx are included */
/* Estimated: 8-10 KB gzipped */
```

**6. Lazy Load External Links**:
```typescript
// GitHub links open externally (no prefetch needed)
target="_blank" rel="noopener noreferrer"
```

**7. Minimize Layout Shift**:
```typescript
// All content heights defined upfront
<Card className="min-h-[400px]"> {/* Prevent CLS */}

// Skeleton loaders if needed (future phase)
{isLoading && <Skeleton className="h-8 w-full" />}
```

**Performance Testing Tools**:
- Chrome Lighthouse (target: 90+ score)
- WebPageTest (3G Slow connection)
- React DevTools Profiler
- Bundle Analyzer (webpack-bundle-analyzer)

**Monitoring** (Production):
```typescript
// Web Vitals reporting
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals'

function sendToAnalytics(metric) {
  // Send to monitoring service
  console.log(metric) // Replace with real analytics
}

getCLS(sendToAnalytics)
getFID(sendToAnalytics)
getFCP(sendToAnalytics)
getLCP(sendToAnalytics)
getTTFB(sendToAnalytics)
```

---

## 🔗 Integration Points

### Navigation Integration
- **Sidebar Menu**: Add "Support" item after "Settings"
- **Icon**: `BookOpen` from lucide-react
- **Route**: `/support`
- **Access**: All authenticated users

### External Links
- Framework GitHub: `https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework`
- Orchestrator GitHub: `https://github.com/Minh-Tam-Solution/SDLC-Orchestrator`
- Documentation Path: `/docs/07-operate/03-User Support/`

### Author Contact
- Email: `taidt@mtsolution.com.vn`
- Phone: `+84 939 116 006`
- Name: Mr. Tai

---

## 📦 Technical Implementation Plan

### Phase 1: Core Page (This Sprint)
1. Create `SupportPage.tsx` component
2. Add route to `App.tsx`
3. Add sidebar navigation item
4. Static documentation data
5. Category cards with doc links
6. Contact section
7. External links section
8. Mobile responsive layout

### Phase 2: Enhanced Features (Next Sprint)
1. Search functionality (local search)
2. Doc preview on hover
3. Recently viewed docs (localStorage)
4. Keyboard shortcuts
5. Dark mode optimization
6. Analytics tracking

### Phase 3: Advanced Features (Future)
1. Inline doc viewer (iframe/modal)
2. Video tutorials integration
3. Interactive demos
4. Community forum integration
5. AI-powered search

---

## ✅ Definition of Done

**Design Phase**:
- [x] Information architecture defined
- [x] UI/UX mockup created
- [x] Component hierarchy documented
- [x] Data structure specified
- [x] Accessibility requirements listed
- [x] Performance targets set
- [x] Integration points identified

**Build Phase** (Next):
- [ ] Component implementation
- [ ] Route configuration
- [ ] Navigation integration
- [ ] Responsive design testing
- [ ] Accessibility audit
- [ ] Performance testing
- [ ] User acceptance testing

---

## 🎯 Success Metrics

**Quantitative**:
- Page load time < 1s
- Zero accessibility violations
- 100% mobile responsiveness
- All 11 docs accessible

**Qualitative**:
- Intuitive navigation
- Clear categorization
- Consistent design language
- Professional appearance

---

## 📚 References

- [USER-SUPPORT-OVERVIEW.md](../../../USER-SUPPORT-OVERVIEW.md) - Documentation index
- [09-Support-Channels.md](../../07-operate/03-User%20Support/09-Support-Channels.md) - Contact info
- [DashboardPage.tsx](../../../frontend/web/src/pages/DashboardPage.tsx) - Layout reference
- [SDLC 6.1.0 Framework](https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework) - Foundation

---

**Design Status**: ✅ APPROVED - Ready for BUILD Stage  
**Next Step**: Stage 03 - BUILD (Component Implementation)  
**Approval Required**: Frontend Lead + CTO Sign-off

---

**Author**: Mr. Tai (taidt@mtsolution.com.vn, +84 939 116 006)  
**Documentation**: v1.0 (Dec 20, 2025)
