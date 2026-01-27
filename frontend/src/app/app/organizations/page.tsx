/**
 * Organizations List Page - SDLC Orchestrator Dashboard
 *
 * @module frontend/src/app/app/organizations/page
 * @description Organization list and management page
 * @sdlc SDLC 5.1.3 Framework - Sprint 84 (Teams & Organizations UI)
 * @status Sprint 84 - CTO APPROVED (January 20, 2026)
 */

"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useOrganizations, useCreateOrganization, type Organization } from "@/hooks/useOrganizations";
import { useAuth } from "@/hooks/useAuth";
import {
  ORGANIZATION_PLAN_META,
  type OrganizationPlan,
  formatOrgSlug,
} from "@/lib/types/organization";

// =============================================================================
// Icons
// =============================================================================

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  );
}

function MagnifyingGlassIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
    </svg>
  );
}

function BuildingOffice2Icon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Z" />
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

function ChevronRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
    </svg>
  );
}

function XMarkIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
    </svg>
  );
}

function UserGroupIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z" />
    </svg>
  );
}

// =============================================================================
// Components
// =============================================================================

function PlanBadge({ plan }: { plan: OrganizationPlan }) {
  const meta = ORGANIZATION_PLAN_META[plan];
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${meta.color}`}>
      {meta.label}
    </span>
  );
}

function OrganizationCard({ org }: { org: Organization }) {
  return (
    <Link
      href={`/app/organizations/${org.id}`}
      className="group block rounded-lg border border-gray-200 bg-white p-6 transition-all hover:border-blue-300 hover:shadow-md"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-50">
            <BuildingOffice2Icon className="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <h3 className="font-medium text-gray-900 group-hover:text-blue-600">
              {org.name}
            </h3>
            <p className="text-sm text-gray-500">/{org.slug}</p>
          </div>
        </div>
        <ChevronRightIcon className="h-5 w-5 text-gray-400 group-hover:text-blue-600" />
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <PlanBadge plan={org.plan} />
        <div className="flex items-center gap-1 text-sm text-gray-500">
          <UserGroupIcon className="h-4 w-4" />
          <span>{org.teams_count} teams</span>
        </div>
        <div className="flex items-center gap-1 text-sm text-gray-500">
          <UsersIcon className="h-4 w-4" />
          <span>{org.users_count} users</span>
        </div>
      </div>
    </Link>
  );
}

function OrganizationCardSkeleton() {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 animate-pulse">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-gray-200" />
          <div className="space-y-2">
            <div className="h-4 w-32 rounded bg-gray-200" />
            <div className="h-3 w-20 rounded bg-gray-200" />
          </div>
        </div>
      </div>
      <div className="mt-4 flex gap-3">
        <div className="h-5 w-16 rounded-full bg-gray-200" />
        <div className="h-5 w-20 rounded bg-gray-200" />
        <div className="h-5 w-20 rounded bg-gray-200" />
      </div>
    </div>
  );
}

function CreateOrganizationModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const router = useRouter();
  const createOrg = useCreateOrganization();

  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [plan, setPlan] = useState<OrganizationPlan>("free");
  const [error, setError] = useState<string | null>(null);
  // Sprint 105: Prevent double-submit race condition
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Auto-generate slug from name
  const handleNameChange = (value: string) => {
    setName(value);
    setSlug(formatOrgSlug(value));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Sprint 105: Double-submit protection - check both local and mutation state
    if (isSubmitting || createOrg.isPending) {
      console.log("[CreateOrg] Already submitting, skipping duplicate request");
      return;
    }

    if (!name.trim()) {
      setError("Organization name is required");
      return;
    }

    if (!slug.trim()) {
      setError("Organization slug is required");
      return;
    }

    // Sprint 105: Set local submitting state BEFORE async call
    setIsSubmitting(true);

    try {
      const result = await createOrg.mutateAsync({
        name: name.trim(),
        slug: slug.trim(),
        plan,
      });

      onClose();
      router.push(`/app/organizations/${result.id}`);
    } catch (err: unknown) {
      // Sprint 105: Extract error message from API response or Error object
      let errorMessage = "Failed to create organization";
      if (err instanceof Error) {
        errorMessage = err.message;
      } else if (err && typeof err === "object") {
        // API errors come as {detail: "...", status: 409}
        if ("detail" in err && typeof err.detail === "string") {
          errorMessage = err.detail;
        } else if ("message" in err && typeof err.message === "string") {
          errorMessage = err.message;
        }
      }
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setName("");
    setSlug("");
    setPlan("free");
    setError(null);
    setIsSubmitting(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={handleClose} />

      <div className="relative z-10 w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Create Organization</h2>
          <button
            onClick={handleClose}
            className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Organization Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Organization Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder="Enter organization name"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              autoFocus
            />
          </div>

          {/* Organization Slug */}
          <div>
            <label htmlFor="slug" className="block text-sm font-medium text-gray-700 mb-1">
              Organization Slug <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="slug"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              placeholder="organization-slug"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">Globally unique URL identifier</p>
          </div>

          {/* Plan */}
          <div>
            <label htmlFor="plan" className="block text-sm font-medium text-gray-700 mb-1">
              Plan
            </label>
            <select
              id="plan"
              value={plan}
              onChange={(e) => setPlan(e.target.value as OrganizationPlan)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {(Object.entries(ORGANIZATION_PLAN_META) as [OrganizationPlan, typeof ORGANIZATION_PLAN_META["free"]][]).map(
                ([planKey, meta]) => (
                  <option key={planKey} value={planKey}>
                    {meta.label} - {meta.description}
                  </option>
                )
              )}
            </select>
          </div>

          {/* Plan features preview */}
          <div className="rounded-lg bg-gray-50 p-3">
            <p className="text-xs font-medium text-gray-700 mb-2">Plan Features:</p>
            <ul className="text-xs text-gray-600 space-y-1">
              {ORGANIZATION_PLAN_META[plan].features.slice(0, 4).map((feature, idx) => (
                <li key={idx} className="flex items-center gap-1">
                  <svg className="h-3 w-3 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {feature}
                </li>
              ))}
            </ul>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || createOrg.isPending}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {(isSubmitting || createOrg.isPending) ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Creating...
                </>
              ) : (
                "Create Organization"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
    </div>
  );
}

// =============================================================================
// Main Page
// =============================================================================

export default function OrganizationsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { data: orgsData, isLoading, error } = useOrganizations();
  const organizations = orgsData?.items || [];

  if (authLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="text-amber-600 mb-4">Please log in to view organizations.</div>
        <Link
          href="/login"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Go to Login
        </Link>
      </div>
    );
  }

  const filteredOrgs = organizations.filter((org) => {
    const matchesSearch =
      org.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      org.slug.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Organizations</h1>
          <p className="mt-1 text-gray-500">
            Manage your organizations and teams
          </p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <PlusIcon className="h-4 w-4" />
          New Organization
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search organizations..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      {/* Error state - only show for actual errors, not empty data */}
      {error && !organizations.length && (
        <div className="hidden">
          {/* Silently handle errors when no data - show empty state instead */}
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <OrganizationCardSkeleton key={i} />
          ))}
        </div>
      )}

      {/* Organizations grid */}
      {!isLoading && !error && filteredOrgs.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredOrgs.map((org) => (
            <OrganizationCard key={org.id} org={org} />
          ))}
        </div>
      )}

      {/* Empty state - show when no organizations (including error cases) */}
      {!isLoading && filteredOrgs.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 p-12">
          <BuildingOffice2Icon className="h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No organizations found</h3>
          <p className="mt-1 text-gray-500">
            {searchQuery
              ? "Try adjusting your search query"
              : "Get started by creating a new organization"}
          </p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <PlusIcon className="h-4 w-4" />
            New Organization
          </button>
        </div>
      )}

      {/* Create Organization Modal */}
      <CreateOrganizationModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </div>
  );
}
