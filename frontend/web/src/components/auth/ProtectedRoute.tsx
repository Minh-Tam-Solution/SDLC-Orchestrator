/**
 * File: frontend/web/src/components/auth/ProtectedRoute.tsx
 * Version: 1.1.0
 * Status: ACTIVE - Sprint 37 Admin Panel
 * Date: 2025-12-16
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 5.1.1 Complete Lifecycle, Zero Mock Policy
 *
 * Description:
 * Protected route wrapper that requires authentication.
 * Redirects unauthenticated users to login page.
 * Supports superuser-only routes for Admin Panel (ADR-017).
 *
 * Changelog:
 * - v1.1.0 (2025-12-16): Add requireSuperuser prop for Admin Panel
 * - v1.0.0 (2025-11-27): Initial implementation
 */

import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
  /**
   * If true, requires is_superuser=true (Admin Panel access)
   * Non-superusers will see "Access Denied" page
   */
  requireSuperuser?: boolean
}

/**
 * Access denied component for non-superusers
 */
function AccessDenied() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center">
        <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
          <svg className="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h1 className="mb-2 text-2xl font-bold text-foreground">Access Denied</h1>
        <p className="mb-6 text-muted-foreground">
          You need administrator privileges to access this page.
        </p>
        <a
          href="/"
          className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Go to Dashboard
        </a>
      </div>
    </div>
  )
}

/**
 * Protected route component
 *
 * Wraps routes that require authentication.
 * Redirects to login if user is not authenticated.
 * Shows access denied if requireSuperuser is true but user is not superuser.
 * Preserves the attempted URL for redirect after login.
 *
 * @param children - Child components to render if authenticated
 * @param requireSuperuser - If true, requires is_superuser=true
 * @returns Protected content, redirect to login, or access denied
 */
export default function ProtectedRoute({ children, requireSuperuser = false }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth()
  const location = useLocation()

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    // Save the attempted URL for redirect after login
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Check superuser requirement for Admin Panel
  if (requireSuperuser && !user?.is_superuser) {
    return <AccessDenied />
  }

  return <>{children}</>
}
