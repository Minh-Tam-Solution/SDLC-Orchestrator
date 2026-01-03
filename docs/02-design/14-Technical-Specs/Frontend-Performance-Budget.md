# Frontend Performance Budget
## Sprint 61-64: Next.js Dashboard Migration

**Version**: 1.0.0
**Date**: January 03, 2026
**Status**: APPROVED
**Decision Reference**: [ADR-025](../01-ADRs/ADR-025-Frontend-Platform-Consolidation-Nextjs-Monolith.md)

---

## 1. Performance Targets

### 1.1 Core Web Vitals (Non-Negotiable)

| Metric | Target | Threshold | Measurement |
|--------|--------|-----------|-------------|
| **LCP** (Largest Contentful Paint) | < 2.5s | < 4.0s | Lighthouse CI |
| **FID** (First Input Delay) | < 100ms | < 300ms | Chrome UX Report |
| **CLS** (Cumulative Layout Shift) | < 0.1 | < 0.25 | Lighthouse CI |
| **INP** (Interaction to Next Paint) | < 200ms | < 500ms | Chrome UX Report |

### 1.2 Application-Specific Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Navigation Latency** | < 100ms | Custom timing |
| **Time to Interactive (TTI)** | < 3s | Lighthouse |
| **First Contentful Paint (FCP)** | < 1s | Lighthouse |
| **JavaScript Bundle Size** | < 500KB (initial) | Build analysis |
| **Total Bundle Size** | < 1MB (gzipped) | Build analysis |
| **Memory Usage** | < 512MB | Chrome DevTools |
| **API Response Time** | < 100ms (p95) | Backend metrics |

---

## 2. Bundle Size Budget

### 2.1 JavaScript Budget

| Category | Budget | Notes |
|----------|--------|-------|
| **Framework (Next.js + React)** | 150KB | Non-negotiable |
| **UI Library (shadcn/ui)** | 80KB | Tree-shaken |
| **Data Layer (TanStack Query)** | 40KB | Essential |
| **i18n (next-intl)** | 20KB | Minimal |
| **Charts (Recharts)** | 100KB | Lazy loaded |
| **Editor (Monaco)** | 150KB | Lazy loaded |
| **Utilities** | 60KB | date-fns, zod |
| **Total Initial** | ~350KB | Target: 500KB max |
| **Total with Lazy** | ~500KB | Target: 1MB max |

### 2.2 Per-Route Budget

| Route Group | JS Budget | CSS Budget |
|-------------|-----------|------------|
| Dashboard Home | 100KB | 30KB |
| Projects | 80KB | 25KB |
| Gates | 90KB | 25KB |
| Evidence | 100KB | 30KB |
| Policies (Monaco) | 200KB | 35KB |
| Codegen (SSE) | 150KB | 40KB |
| SOP | 120KB | 30KB |
| Admin | 90KB | 25KB |

---

## 3. Runtime Performance Budget

### 3.1 Memory Budget

| State | Budget | Measurement |
|-------|--------|-------------|
| Initial Load | < 100MB | Chrome Memory tab |
| After Navigation | < 150MB | Chrome Memory tab |
| Heavy Usage (30min) | < 300MB | Chrome Memory tab |
| Peak (Codegen stream) | < 512MB | Chrome Memory tab |

### 3.2 CPU Budget

| Operation | Budget | Notes |
|-----------|--------|-------|
| Page Render | < 50ms | React profiler |
| List Render (100 items) | < 100ms | Virtualized |
| Form Validation | < 10ms | Zod validation |
| Chart Render | < 200ms | Lazy loaded |
| SSE Processing | < 5ms/event | Streaming |

---

## 4. Network Budget

### 4.1 Request Budget

| Metric | Budget |
|--------|--------|
| Initial Page Load Requests | < 15 |
| Document Size | < 50KB (gzipped) |
| CSS Total | < 100KB (gzipped) |
| Images (above fold) | < 200KB |
| Fonts | < 100KB (woff2) |

### 4.2 API Budget

| Endpoint Type | Latency Budget |
|---------------|----------------|
| Auth (login, refresh) | < 200ms |
| List endpoints | < 100ms |
| Detail endpoints | < 80ms |
| Create/Update | < 150ms |
| File upload (10MB) | < 2s |
| SSE connection | < 500ms (establish) |

---

## 5. Measurement Tools

### 5.1 Automated (CI/CD)

```yaml
# .github/workflows/performance.yml
name: Performance Check

on:
  pull_request:
    branches: [main]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci
        working-directory: frontend/landing

      - name: Build
        run: npm run build
        working-directory: frontend/landing

      - name: Lighthouse CI
        uses: treosh/lighthouse-ci-action@v11
        with:
          configPath: './frontend/landing/lighthouserc.json'
          uploadArtifacts: true
          temporaryPublicStorage: true

  bundle-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4

      - name: Install dependencies
        run: npm ci
        working-directory: frontend/landing

      - name: Analyze bundle
        run: npm run analyze
        working-directory: frontend/landing

      - name: Check bundle size
        run: |
          SIZE=$(cat .next/analyze/client.json | jq '.bundles | map(.size) | add')
          if [ $SIZE -gt 1048576 ]; then
            echo "Bundle size exceeds 1MB: $SIZE bytes"
            exit 1
          fi
```

### 5.2 Lighthouse CI Configuration

```json
// lighthouserc.json
{
  "ci": {
    "collect": {
      "url": [
        "http://localhost:3000/vi",
        "http://localhost:3000/vi/projects",
        "http://localhost:3000/vi/gates",
        "http://localhost:3000/vi/codegen"
      ],
      "numberOfRuns": 3
    },
    "assert": {
      "preset": "lighthouse:recommended",
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "categories:accessibility": ["error", { "minScore": 0.9 }],
        "first-contentful-paint": ["error", { "maxNumericValue": 1000 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }],
        "total-blocking-time": ["error", { "maxNumericValue": 300 }]
      }
    },
    "upload": {
      "target": "temporary-public-storage"
    }
  }
}
```

### 5.3 Custom Performance Tracking

```typescript
// src/lib/performance.ts
'use client';

interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
}

class PerformanceTracker {
  private metrics: PerformanceMetric[] = [];

  // Track navigation timing
  trackNavigation(from: string, to: string) {
    const start = performance.now();

    return {
      end: () => {
        const duration = performance.now() - start;
        this.record(`nav:${from}->${to}`, duration);

        // Alert if over budget
        if (duration > 100) {
          console.warn(`Navigation exceeded budget: ${duration}ms (target: 100ms)`);
        }
      },
    };
  }

  // Track component render
  trackRender(componentName: string) {
    const start = performance.now();

    return () => {
      const duration = performance.now() - start;
      this.record(`render:${componentName}`, duration);

      if (duration > 50) {
        console.warn(`Render exceeded budget: ${componentName} ${duration}ms`);
      }
    };
  }

  // Track API call
  trackAPI(endpoint: string) {
    const start = performance.now();

    return () => {
      const duration = performance.now() - start;
      this.record(`api:${endpoint}`, duration);

      if (duration > 100) {
        console.warn(`API exceeded budget: ${endpoint} ${duration}ms`);
      }
    };
  }

  private record(name: string, value: number) {
    this.metrics.push({
      name,
      value,
      timestamp: Date.now(),
    });

    // Send to analytics in production
    if (process.env.NODE_ENV === 'production') {
      this.sendToAnalytics({ name, value });
    }
  }

  private sendToAnalytics(metric: Omit<PerformanceMetric, 'timestamp'>) {
    // Send to your analytics service
    navigator.sendBeacon('/api/metrics', JSON.stringify(metric));
  }

  // Get metrics for dashboard display
  getMetrics() {
    return [...this.metrics];
  }
}

export const performanceTracker = new PerformanceTracker();
```

### 5.4 React Profiler Integration

```typescript
// src/components/PerformanceProfiler.tsx
'use client';

import { Profiler, ProfilerOnRenderCallback } from 'react';
import { performanceTracker } from '@/lib/performance';

const onRenderCallback: ProfilerOnRenderCallback = (
  id,
  phase,
  actualDuration,
  baseDuration,
  startTime,
  commitTime
) => {
  if (actualDuration > 16) {
    // More than one frame (60fps)
    console.warn(
      `Slow render: ${id} (${phase}) took ${actualDuration.toFixed(2)}ms`
    );
  }

  if (process.env.NODE_ENV === 'development') {
    console.debug(`[Profiler] ${id}:`, {
      phase,
      actualDuration: `${actualDuration.toFixed(2)}ms`,
      baseDuration: `${baseDuration.toFixed(2)}ms`,
    });
  }
};

export function PerformanceProfiler({
  id,
  children,
}: {
  id: string;
  children: React.ReactNode;
}) {
  return (
    <Profiler id={id} onRender={onRenderCallback}>
      {children}
    </Profiler>
  );
}
```

---

## 6. Optimization Strategies

### 6.1 Code Splitting

```typescript
// Dynamic imports for heavy components
import dynamic from 'next/dynamic';

// Monaco Editor (150KB)
export const PolicyEditor = dynamic(
  () => import('@/components/policies/PolicyEditor'),
  {
    loading: () => <EditorSkeleton />,
    ssr: false,
  }
);

// Recharts (100KB)
export const DashboardCharts = dynamic(
  () => import('@/components/dashboard/Charts'),
  {
    loading: () => <ChartSkeleton />,
  }
);

// Codegen viewer (complex)
export const QualityPipelineViewer = dynamic(
  () => import('@/components/codegen/QualityPipelineViewer'),
  {
    loading: () => <PipelineSkeleton />,
  }
);
```

### 6.2 List Virtualization

```typescript
// For lists with 100+ items
import { useVirtualizer } from '@tanstack/react-virtual';

export function ProjectList({ projects }: { projects: Project[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: projects.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 72, // Row height
    overscan: 5,
  });

  return (
    <div ref={parentRef} className="h-[600px] overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualRow) => (
          <div
            key={virtualRow.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualRow.size}px`,
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            <ProjectCard project={projects[virtualRow.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 6.3 Image Optimization

```typescript
// next.config.js
module.exports = {
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256],
    domains: ['avatars.githubusercontent.com', 'minio.nhatquangholding.com'],
  },
};
```

### 6.4 Font Optimization

```typescript
// src/app/layout.tsx
import { Inter } from 'next/font/google';

const inter = Inter({
  subsets: ['latin', 'vietnamese'],
  display: 'swap',
  variable: '--font-inter',
  preload: true,
});

export default function RootLayout({ children }) {
  return (
    <html lang="vi" className={inter.variable}>
      <body>{children}</body>
    </html>
  );
}
```

---

## 7. Monitoring & Alerts

### 7.1 Performance Alerts

| Metric | Warning | Critical |
|--------|---------|----------|
| LCP | > 2.5s | > 4.0s |
| Navigation | > 100ms | > 200ms |
| Bundle Size | > 800KB | > 1MB |
| Memory | > 300MB | > 512MB |
| API Latency | > 100ms | > 200ms |

### 7.2 Grafana Dashboard Panels

```yaml
# Performance dashboard panels
panels:
  - title: "Core Web Vitals"
    type: stat
    targets:
      - expr: histogram_quantile(0.75, frontend_lcp_seconds)
      - expr: histogram_quantile(0.75, frontend_fid_milliseconds)
      - expr: avg(frontend_cls)

  - title: "Navigation Latency (p95)"
    type: graph
    targets:
      - expr: histogram_quantile(0.95, frontend_navigation_duration_ms)

  - title: "Bundle Size Trend"
    type: graph
    targets:
      - expr: frontend_bundle_size_bytes

  - title: "Memory Usage"
    type: graph
    targets:
      - expr: frontend_memory_usage_bytes
```

---

## 8. Budget Enforcement

### 8.1 Pre-commit Hook

```bash
#!/bin/bash
# .husky/pre-commit

# Check bundle size
cd frontend/landing
npm run build > /dev/null 2>&1

BUNDLE_SIZE=$(cat .next/analyze/client.json | jq '.bundles | map(.size) | add' 2>/dev/null || echo "0")

if [ "$BUNDLE_SIZE" -gt 1048576 ]; then
  echo "ERROR: Bundle size exceeds 1MB budget"
  echo "Current size: $((BUNDLE_SIZE / 1024))KB"
  exit 1
fi

echo "Bundle size OK: $((BUNDLE_SIZE / 1024))KB"
```

### 8.2 PR Check Requirements

- [ ] Lighthouse performance score >= 90
- [ ] Bundle size < 1MB
- [ ] No new npm dependencies > 50KB without approval
- [ ] All dynamic imports for components > 50KB

---

## 9. References

- [ADR-025: Frontend Platform Consolidation](../01-ADRs/ADR-025-Frontend-Platform-Consolidation-Nextjs-Monolith.md)
- [Route Migration Map](./Frontend-Migration-Route-Map.md)
- [Technical Spec](./Dashboard-Migration-Technical-Spec.md)
- [Core Web Vitals](https://web.dev/vitals/)
- [Next.js Performance](https://nextjs.org/docs/app/building-your-application/optimizing)
