/**
 * Dashboard Header - SDLC Orchestrator
 *
 * @module frontend/src/components/dashboard/Header
 * @description Top navigation header for dashboard with dynamic breadcrumbs
 * @sdlc SDLC 5.1.3 Framework - Sprint 84 (Teams & Organizations UI)
 * @status Sprint 84 - Navigation Integration
 */

"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { useWorkspace } from "@/contexts/WorkspaceContext";

function BellIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
    </svg>
  );
}

function ChevronDownIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
    </svg>
  );
}

function UserCircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  );
}

function ArrowRightStartOnRectangleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 9V5.25A2.25 2.25 0 0 1 10.5 3h6a2.25 2.25 0 0 1 2.25 2.25v13.5A2.25 2.25 0 0 1 16.5 21h-6a2.25 2.25 0 0 1-2.25-2.25V15m-3 0-3-3m0 0 3-3m-3 3H15" />
    </svg>
  );
}

function CogIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  );
}

function ChevronRightSmallIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
    </svg>
  );
}

function BuildingOfficeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
    </svg>
  );
}

function UsersIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
    </svg>
  );
}

/**
 * Workspace Switcher Component
 * Sprint 91: Organization and Team selector in navbar
 */
function WorkspaceSwitcher() {
  const [isOpen, setIsOpen] = useState(false);
  const {
    selectedOrganization,
    selectedTeam,
    organizations,
    teams,
    isLoadingOrganizations,
    isLoadingTeams,
    selectOrganization,
    selectTeam,
    hasOrganizations,
  } = useWorkspace();

  // Don't render if no organizations
  if (!hasOrganizations && !isLoadingOrganizations) {
    return null;
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm hover:bg-gray-50"
      >
        {isLoadingOrganizations ? (
          <div className="h-4 w-24 animate-pulse rounded bg-gray-200" />
        ) : (
          <>
            <BuildingOfficeIcon className="h-4 w-4 text-gray-500" />
            <span className="max-w-[120px] truncate font-medium text-gray-700">
              {selectedOrganization?.name || "Select Org"}
            </span>
            {selectedTeam && (
              <>
                <ChevronRightSmallIcon className="h-3 w-3 text-gray-400" />
                <UsersIcon className="h-4 w-4 text-gray-500" />
                <span className="max-w-[100px] truncate text-gray-600">
                  {selectedTeam.name}
                </span>
              </>
            )}
            <ChevronDownIcon className="h-4 w-4 text-gray-400" />
          </>
        )}
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute left-0 z-20 mt-2 w-72 origin-top-left rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5">
            {/* Organizations Section */}
            <div className="border-b border-gray-100 p-2">
              <p className="px-2 py-1 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Organizations
              </p>
              <div className="max-h-48 overflow-y-auto">
                {organizations.map((org) => (
                  <button
                    key={org.id}
                    onClick={() => {
                      selectOrganization(org.id);
                    }}
                    className={`flex w-full items-center justify-between rounded-md px-2 py-2 text-sm hover:bg-gray-50 ${
                      selectedOrganization?.id === org.id
                        ? "bg-blue-50 text-blue-700"
                        : "text-gray-700"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <BuildingOfficeIcon className="h-4 w-4" />
                      <span className="truncate">{org.name}</span>
                    </div>
                    {selectedOrganization?.id === org.id && (
                      <CheckIcon className="h-4 w-4 text-blue-600" />
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Teams Section */}
            {selectedOrganization && (
              <div className="p-2">
                <p className="px-2 py-1 text-xs font-semibold uppercase tracking-wider text-gray-500">
                  Teams in {selectedOrganization.name}
                </p>
                <div className="max-h-48 overflow-y-auto">
                  {isLoadingTeams ? (
                    <div className="flex items-center justify-center py-4">
                      <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
                    </div>
                  ) : teams.length === 0 ? (
                    <p className="px-2 py-2 text-sm text-gray-500">
                      No teams in this organization
                    </p>
                  ) : (
                    teams.map((team) => (
                      <button
                        key={team.id}
                        onClick={() => {
                          selectTeam(team.id);
                          setIsOpen(false);
                        }}
                        className={`flex w-full items-center justify-between rounded-md px-2 py-2 text-sm hover:bg-gray-50 ${
                          selectedTeam?.id === team.id
                            ? "bg-blue-50 text-blue-700"
                            : "text-gray-700"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <UsersIcon className="h-4 w-4" />
                          <span className="truncate">{team.name}</span>
                        </div>
                        {selectedTeam?.id === team.id && (
                          <CheckIcon className="h-4 w-4 text-blue-600" />
                        )}
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* Quick Links */}
            <div className="border-t border-gray-100 p-2">
              <Link
                href="/app/organizations"
                onClick={() => setIsOpen(false)}
                className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm text-gray-600 hover:bg-gray-50"
              >
                <BuildingOfficeIcon className="h-4 w-4" />
                Manage Organizations
              </Link>
              <Link
                href="/app/teams"
                onClick={() => setIsOpen(false)}
                className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm text-gray-600 hover:bg-gray-50"
              >
                <UsersIcon className="h-4 w-4" />
                Manage Teams
              </Link>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// Route name mappings for breadcrumbs (Sprint 87 - added Evidence Manifests, Sprint 86 - System Settings)
const routeNameMap: Record<string, string> = {
  app: "Dashboard",
  projects: "Projects",
  teams: "Teams",
  organizations: "Organizations",
  gates: "Gates",
  evidence: "Evidence",
  "evidence-manifests": "Hash Chain",
  policies: "Policies",
  "agents-md": "AGENTS.md",
  "cli-tokens": "CLI Tokens",
  "check-runs": "Check Runs",
  analytics: "Analytics",
  codegen: "App Builder",
  "sop-generator": "SOP Generator",
  settings: "Settings",
  admin: "Admin",
};

// Special route mappings for nested admin routes (Sprint 86)
const adminRouteNameMap: Record<string, string> = {
  settings: "System Settings",
};

// Build breadcrumbs from pathname
function useBreadcrumbs() {
  const pathname = usePathname();

  return useMemo(() => {
    const segments = pathname.split("/").filter(Boolean);
    const breadcrumbs: { name: string; href: string; isLast: boolean }[] = [];

    let currentPath = "";
    let isInAdminSection = false;

    segments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      const isLast = index === segments.length - 1;

      // Track if we're in admin section for special naming
      if (segment === "admin") {
        isInAdminSection = true;
      }

      // Check if this is a UUID (detail page)
      const isUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(segment);

      if (isUUID) {
        // For detail pages, show "Detail" or skip
        breadcrumbs.push({
          name: "Detail",
          href: currentPath,
          isLast,
        });
      } else {
        // Use admin-specific naming for nested admin routes
        let name: string;
        if (isInAdminSection && segment !== "admin" && adminRouteNameMap[segment]) {
          name = adminRouteNameMap[segment];
        } else {
          name = routeNameMap[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);
        }
        breadcrumbs.push({
          name,
          href: currentPath,
          isLast,
        });
      }
    });

    return breadcrumbs;
  }, [pathname]);
}

export function Header() {
  const { user, logout } = useAuth();
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const breadcrumbs = useBreadcrumbs();

  const handleLogout = async () => {
    await logout();
    window.location.href = "/login";
  };

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      {/* Left side - Breadcrumbs */}
      <div className="flex items-center gap-2">
        <nav className="flex items-center" aria-label="Breadcrumb">
          <ol className="flex items-center gap-1">
            {breadcrumbs.map((crumb, index) => (
              <li key={crumb.href} className="flex items-center">
                {index > 0 && (
                  <ChevronRightSmallIcon className="mx-1 h-4 w-4 flex-shrink-0 text-gray-400" />
                )}
                {crumb.isLast ? (
                  <span className="text-sm font-semibold text-gray-900">
                    {crumb.name}
                  </span>
                ) : (
                  <Link
                    href={crumb.href}
                    className="text-sm font-medium text-gray-500 hover:text-gray-700"
                  >
                    {crumb.name}
                  </Link>
                )}
              </li>
            ))}
          </ol>
        </nav>
      </div>

      {/* Right side - Actions */}
      <div className="flex items-center gap-4">
        {/* Workspace Switcher - Sprint 91 */}
        <WorkspaceSwitcher />

        {/* Notifications */}
        <button className="relative rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700">
          <BellIcon className="h-5 w-5" />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" />
        </button>

        {/* Profile dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="flex items-center gap-2 rounded-lg p-2 hover:bg-gray-100"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100">
              {user?.name ? (
                <span className="text-sm font-medium text-blue-600">
                  {user.name.charAt(0).toUpperCase()}
                </span>
              ) : (
                <UserCircleIcon className="h-5 w-5 text-blue-600" />
              )}
            </div>
            <div className="hidden text-left md:block">
              <p className="text-sm font-medium text-gray-900">
                {user?.name || user?.email || "User"}
              </p>
              <p className="text-xs text-gray-500">
                {user?.roles?.[0] || "Member"}
              </p>
            </div>
            <ChevronDownIcon className="hidden h-4 w-4 text-gray-400 md:block" />
          </button>

          {/* Dropdown menu */}
          {isProfileOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setIsProfileOpen(false)}
              />
              <div className="absolute right-0 z-20 mt-2 w-56 origin-top-right rounded-lg bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5">
                <div className="border-b border-gray-100 px-4 py-3">
                  <p className="text-sm font-medium text-gray-900">
                    {user?.name || "User"}
                  </p>
                  <p className="text-xs text-gray-500">{user?.email}</p>
                </div>

                <Link
                  href="/app/settings"
                  className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                  onClick={() => setIsProfileOpen(false)}
                >
                  <CogIcon className="h-4 w-4" />
                  Settings
                </Link>

                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  <ArrowRightStartOnRectangleIcon className="h-4 w-4" />
                  Sign out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
