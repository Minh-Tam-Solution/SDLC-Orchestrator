/**
 * Auth Guard Component - SDLC Orchestrator Dashboard
 *
 * @module frontend/landing/src/components/auth/AuthGuard
 * @description Protects routes requiring authentication
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 61 - Frontend Platform Consolidation
 */

"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

interface AuthGuardProps {
  children: React.ReactNode;
  fallbackPath?: string;
}

/**
 * Loading skeleton for auth check
 */
function AuthLoadingSkeleton() {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-gray-50">
      <div className="flex flex-col items-center gap-4">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
        <p className="text-sm text-gray-500">Đang xác thực...</p>
      </div>
    </div>
  );
}

/**
 * Auth Guard - Redirects to login if not authenticated
 */
export function AuthGuard({ children, fallbackPath = "/login" }: AuthGuardProps) {
  const { isLoading, isAuthenticated } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      // Encode current path for redirect after login
      const redirectUrl = encodeURIComponent(pathname);
      router.push(`${fallbackPath}?redirect=${redirectUrl}`);
    }
  }, [isLoading, isAuthenticated, router, pathname, fallbackPath]);

  // Show loading while checking auth
  if (isLoading) {
    return <AuthLoadingSkeleton />;
  }

  // Don't render children if not authenticated
  if (!isAuthenticated) {
    return <AuthLoadingSkeleton />;
  }

  return <>{children}</>;
}

/**
 * Role Guard - Requires specific roles
 */
interface RoleGuardProps {
  children: React.ReactNode;
  requiredRoles: string[];
  fallbackPath?: string;
}

export function RoleGuard({
  children,
  requiredRoles,
  fallbackPath = "/unauthorized",
}: RoleGuardProps) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      const hasRole = requiredRoles.some((role) => user.roles?.includes(role));
      if (!hasRole) {
        router.push(fallbackPath);
      }
    }
  }, [isLoading, isAuthenticated, user, requiredRoles, router, fallbackPath]);

  if (isLoading) {
    return <AuthLoadingSkeleton />;
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  const hasRole = requiredRoles.some((role) => user.roles?.includes(role));
  if (!hasRole) {
    return null;
  }

  return <>{children}</>;
}

/**
 * Admin Guard - Requires is_superuser=true
 * Used for /admin/* routes (superuser only)
 */
interface AdminGuardProps {
  children: React.ReactNode;
  fallbackPath?: string;
}

export function AdminGuard({
  children,
  fallbackPath = "/app",
}: AdminGuardProps) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      if (!user.is_superuser) {
        router.push(fallbackPath);
      }
    }
  }, [isLoading, isAuthenticated, user, router, fallbackPath]);

  if (isLoading) {
    return <AuthLoadingSkeleton />;
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  if (!user.is_superuser) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Access Denied</h1>
          <p className="mt-2 text-gray-600">
            You need admin privileges to access this page.
          </p>
          <button
            onClick={() => router.push(fallbackPath)}
            className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * Customer User Guard - BLOCKS platform admins from customer UI
 * Sprint 88: Platform Admin Privacy Fix (ADR-030)
 * 
 * Used for /app/* routes (customer UI only - no platform admins)
 * Platform admins (is_superuser=true) should stay in /admin/* exclusively
 */
interface CustomerUserGuardProps {
  children: React.ReactNode;
  fallbackPath?: string;
}

export function CustomerUserGuard({
  children,
  fallbackPath = "/admin",
}: CustomerUserGuardProps) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      // BLOCK platform admins from customer UI
      if (user.is_superuser) {
        console.warn('[CustomerUserGuard] Platform admin blocked from /app - redirecting to /admin');
        router.push(fallbackPath);
      }
    }
  }, [isLoading, isAuthenticated, user, router, fallbackPath]);

  if (isLoading) {
    return <AuthLoadingSkeleton />;
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  // BLOCK platform admins
  if (user.is_superuser) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Access Denied</h1>
          <p className="mt-2 text-gray-600">
            Platform administrators cannot access customer UI.
          </p>
          <p className="mt-1 text-sm text-gray-500">
            Use the Admin Panel to manage system settings.
          </p>
          <button
            onClick={() => router.push(fallbackPath)}
            className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            Go to Admin Panel
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * @deprecated PlatformAdminGuard is no longer needed
 * After Sprint 69 route restructure:
 * - /app/* is accessible to ALL authenticated users
 * - /admin/* requires is_superuser (use AdminGuard)
 *
 * Keeping for backwards compatibility, but it now just passes through.
 */
interface PlatformAdminGuardProps {
  children: React.ReactNode;
  fallbackPath?: string;
}

export function PlatformAdminGuard({
  children,
}: PlatformAdminGuardProps) {
  // After Sprint 69: /app/* is for all authenticated users
  // This guard is deprecated - just pass through
  return <>{children}</>;
}
