/**
 * Web App Layout - SDLC Orchestrator
 *
 * @module frontend/landing/src/app/app/layout
 * @description Protected layout for the main Web App
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 88 - Platform Admin Privacy Fix (Day 1 Task 2)
 * @security Requires authentication + NON-PLATFORM-ADMIN user
 */

"use client";

import { Suspense, useEffect } from "react";
import { useRouter } from "next/navigation";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { QueryProvider } from "@/app/providers/QueryProvider";
import { WorkspaceProvider } from "@/contexts/WorkspaceContext";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { Header } from "@/components/dashboard/Header";

/**
 * Inner layout component with access to auth context
 * Sprint 88: Block platform admins from accessing customer UI
 */
function AppLayoutInner({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    // Sprint 88 Day 4-5: Redirect platform admins to /admin
    // Platform admins (is_platform_admin) should NOT access customer data (/app routes)
    if (!isLoading && user?.is_platform_admin) {
      console.warn(
        "[AppLayout] Platform admin detected - redirecting to /admin",
        { user_id: user.id, email: user.email }
      );
      router.replace("/admin");
    }
  }, [user, isLoading, router]);

  // Show loading while checking user role
  if (isLoading) {
    return <PageLoadingSkeleton />;
  }

  // Block render if platform admin (will redirect)
  if (user?.is_platform_admin) {
    return <PageLoadingSkeleton />;
  }

  // Render customer UI for regular users
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <Header />

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Suspense fallback={<PageLoadingSkeleton />}>
            {children}
          </Suspense>
        </main>
      </div>
    </div>
  );
}

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <QueryProvider>
      <AuthProvider>
        <AuthGuard>
          <WorkspaceProvider>
            <AppLayoutInner>{children}</AppLayoutInner>
          </WorkspaceProvider>
        </AuthGuard>
      </AuthProvider>
    </QueryProvider>
  );
}

/**
 * Page loading skeleton
 */
function PageLoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-48 animate-pulse rounded bg-gray-200" />
      <div className="grid gap-4 md:grid-cols-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-32 animate-pulse rounded-lg bg-gray-200" />
        ))}
      </div>
      <div className="h-64 animate-pulse rounded-lg bg-gray-200" />
    </div>
  );
}
