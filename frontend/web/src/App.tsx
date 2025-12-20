/**
 * File: frontend/web/src/App.tsx
 * Version: 1.2.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-17
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 5.1.1 Complete Lifecycle, Zero Mock Policy
 *
 * Description:
 * Root component for SDLC Orchestrator frontend application.
 * Configures routing, authentication, and layout structure.
 *
 * Sprint 23 Day 5: Bundle Optimization
 * - React.lazy for code splitting (route-based)
 * - Suspense for loading states
 * - Reduces initial bundle by ~60%
 *
 * Sprint 39: Toast Notification System
 * - Added Toaster component for global toast notifications
 */

import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { Toaster } from '@/components/ui/toaster'

// Lazy-loaded pages (route-based code splitting)
// Critical path: Login loaded immediately
import LoginPage from '@/pages/LoginPage'

// Non-critical pages: Lazy loaded on navigation
const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const ProjectsPage = lazy(() => import('@/pages/ProjectsPage'))
const ProjectDetailPage = lazy(() => import('@/pages/ProjectDetailPage'))
const GatesPage = lazy(() => import('@/pages/GatesPage'))
const GateDetailPage = lazy(() => import('@/pages/GateDetailPage'))
const EvidencePage = lazy(() => import('@/pages/EvidencePage'))
const PoliciesPage = lazy(() => import('@/pages/PoliciesPage'))
const PolicyDetailPage = lazy(() => import('@/pages/PolicyDetailPage'))
const SettingsPage = lazy(() => import('@/pages/SettingsPage'))
const CompliancePage = lazy(() => import('@/pages/CompliancePage'))
const OnboardingPage = lazy(() => import('@/pages/OnboardingPage'))
const GitHubCallbackPage = lazy(() => import('@/pages/GitHubCallbackPage'))
const SOPGeneratorPage = lazy(() => import('@/pages/SOPGeneratorPage'))  // Phase 2-Pilot Week 3
const SOPHistoryPage = lazy(() => import('@/pages/SOPHistoryPage'))  // Phase 2-Pilot Week 4
const SOPDetailPage = lazy(() => import('@/pages/SOPDetailPage'))  // Phase 2-Pilot Week 4
const SupportPage = lazy(() => import('@/pages/SupportPage'))  // User Support & Documentation
const DocumentationViewerPage = lazy(() => import('@/pages/DocumentationViewerPage'))  // Documentation Viewer
const GettingStartedPage = lazy(() => import('@/pages/support/GettingStartedPage'))  // Getting Started Guide
const FrameworkOverviewPage = lazy(() => import('@/pages/support/FrameworkOverviewPage'))  // Framework Overview
const PlatformFeaturesPage = lazy(() => import('@/pages/support/PlatformFeaturesPage'))  // Platform Features
const UserRolesPage = lazy(() => import('@/pages/support/UserRolesPage'))  // User Roles & Permissions
const CommonTasksPage = lazy(() => import('@/pages/support/CommonTasksPage'))  // Common Tasks
const TroubleshootingPage = lazy(() => import('@/pages/support/TroubleshootingPage'))  // Troubleshooting
const FAQPage = lazy(() => import('@/pages/support/FAQPage'))  // FAQ
const BestPracticesPage = lazy(() => import('@/pages/support/BestPracticesPage'))  // Best Practices
const SupportChannelsPage = lazy(() => import('@/pages/support/SupportChannelsPage'))  // Support Channels

// Admin Panel pages (Sprint 37)
const AdminDashboardPage = lazy(() => import('@/pages/admin/AdminDashboardPage'))
const UserManagementPage = lazy(() => import('@/pages/admin/UserManagementPage'))
const AuditLogsPage = lazy(() => import('@/pages/admin/AuditLogsPage'))
const SystemSettingsPage = lazy(() => import('@/pages/admin/SystemSettingsPage'))
const SystemHealthPage = lazy(() => import('@/pages/admin/SystemHealthPage'))

/**
 * Loading fallback component for Suspense
 * Displays centered spinner during lazy load
 */
function PageLoader() {
  return (
    <div className="flex h-screen w-full items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    </div>
  )
}

/**
 * Root App component
 *
 * Routing structure:
 * - /login - Public authentication page
 * - /auth/github/callback - GitHub OAuth callback handler
 * - /onboarding/* - Public onboarding wizard (6 steps)
 * - / - Protected dashboard (requires authentication)
 * - /projects - Protected projects list
 * - /projects/:id - Protected project detail
 * - /gates - Protected gates list
 * - /gates/:id - Protected gate detail
 * - /evidence - Protected evidence vault
 * - /policies - Protected policies library
 *
 * @returns App component with routing configured
 */
function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/auth/github/callback"
              element={<GitHubCallbackPage />}
            />
            <Route path="/onboarding/*" element={<OnboardingPage />} />

          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <ProjectsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:id"
            element={
              <ProtectedRoute>
                <ProjectDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/gates"
            element={
              <ProtectedRoute>
                <GatesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/gates/:id"
            element={
              <ProtectedRoute>
                <GateDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/evidence"
            element={
              <ProtectedRoute>
                <EvidencePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/policies"
            element={
              <ProtectedRoute>
                <PoliciesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/policies/:id"
            element={
              <ProtectedRoute>
                <PolicyDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/support"
            element={
              <ProtectedRoute>
                <SupportPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/support/getting-started"
            element={
              <ProtectedRoute>
                <GettingStartedPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/support/framework-overview"
            element={
              <ProtectedRoute>
                <FrameworkOverviewPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/support/platform-features"
            element={
              <ProtectedRoute>
                <PlatformFeaturesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/support/user-roles"
            element={
              <ProtectedRoute>
                <UserRolesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/support/common-tasks"
            element={
              <ProtectedRoute>
                <CommonTasksPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/support/troubleshooting"
            element={
              <ProtectedRoute>
                <TroubleshootingPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/support/faq"
            element={
              <ProtectedRoute>
                <FAQPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/support/best-practices"
            element={
              <ProtectedRoute>
                <BestPracticesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/support/support-channels"
            element={
              <ProtectedRoute>
                <SupportChannelsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/support/docs/:filename"
            element={
              <ProtectedRoute>
                <DocumentationViewerPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/compliance"
            element={
              <ProtectedRoute>
                <CompliancePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sop-generator"
            element={
              <ProtectedRoute>
                <SOPGeneratorPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sop-history"
            element={
              <ProtectedRoute>
                <SOPHistoryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sop/:sopId"
            element={
              <ProtectedRoute>
                <SOPDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sop/:sopId/mrp"
            element={
              <ProtectedRoute>
                <SOPDetailPage />
              </ProtectedRoute>
            }
          />

          {/* Admin Panel routes (Sprint 37) - Requires is_superuser=true */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute requireSuperuser>
                <AdminDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute requireSuperuser>
                <UserManagementPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/audit-logs"
            element={
              <ProtectedRoute requireSuperuser>
                <AuditLogsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/settings"
            element={
              <ProtectedRoute requireSuperuser>
                <SystemSettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/health"
            element={
              <ProtectedRoute requireSuperuser>
                <SystemHealthPage />
              </ProtectedRoute>
            }
          />

            {/* Catch-all route - Redirect to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
        <Toaster />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
