/**
 * Organization Detail Page - SDLC Orchestrator Dashboard
 *
 * @module frontend/src/app/app/organizations/[id]/page
 * @description Organization detail with teams list
 * @sdlc SDLC 5.1.3 Framework - Sprint 84 (Teams & Organizations UI)
 * @status Sprint 84 - CTO APPROVED (January 20, 2026)
 */

"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  useOrganization,
  useOrganizationStats,
  useUpdateOrganization,
  type OrganizationUpdate,
} from "@/hooks/useOrganizations";
import { useTeams, useCreateTeam } from "@/hooks/useTeams";
import { useAuth } from "@/hooks/useAuth";
import {
  ORGANIZATION_PLAN_META,
  type OrganizationPlan,
  type OrganizationSettings,
} from "@/lib/types/organization";
import {
  AGENTIC_MATURITY_META,
  type AgenticMaturity,
} from "@/lib/types/team";

// =============================================================================
// Icons
// =============================================================================

function ArrowLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
    </svg>
  );
}

function PencilIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
    </svg>
  );
}

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
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

function UserGroupIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z" />
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

function BotIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23-.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
    </svg>
  );
}

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
    </svg>
  );
}

// =============================================================================
// Components
// =============================================================================

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: number | string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${color}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-sm text-gray-500">{label}</p>
        </div>
      </div>
    </div>
  );
}

function PlanBadge({ plan }: { plan: OrganizationPlan }) {
  const meta = ORGANIZATION_PLAN_META[plan];
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${meta.color}`}>
      {meta.label}
    </span>
  );
}

function MaturityBadge({ maturity }: { maturity?: AgenticMaturity }) {
  const level = maturity || "L0";
  const meta = AGENTIC_MATURITY_META[level];
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${meta.color}`}>
      {meta.label}
    </span>
  );
}

interface Team {
  id: string;
  name: string;
  description: string | null;
  members_count: number;
  human_members_count: number;
  ai_agents_count: number;
  projects_count: number;
  settings?: {
    agentic_maturity?: AgenticMaturity;
  };
}

function TeamRow({ team }: { team: Team }) {
  const maturity = team.settings?.agentic_maturity || "L0";

  return (
    <Link
      href={`/app/teams/${team.id}`}
      className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
    >
      <div className="flex items-center gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50">
          <UserGroupIcon className="h-5 w-5 text-indigo-600" />
        </div>
        <div>
          <p className="font-medium text-gray-900">{team.name}</p>
          <p className="text-sm text-gray-500 line-clamp-1">{team.description || "No description"}</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <MaturityBadge maturity={maturity} />
        <div className="flex items-center gap-1 text-sm text-gray-500">
          <UsersIcon className="h-4 w-4" />
          <span>{team.human_members_count}</span>
        </div>
        {team.ai_agents_count > 0 && (
          <div className="flex items-center gap-1 text-sm text-orange-600">
            <BotIcon className="h-4 w-4" />
            <span>{team.ai_agents_count}</span>
          </div>
        )}
        <div className="flex items-center gap-1 text-sm text-gray-500">
          <FolderIcon className="h-4 w-4" />
          <span>{team.projects_count}</span>
        </div>
        <ChevronRightIcon className="h-5 w-5 text-gray-400" />
      </div>
    </Link>
  );
}

function CreateTeamModal({
  isOpen,
  onClose,
  organizationId,
}: {
  isOpen: boolean;
  onClose: () => void;
  organizationId: string;
}) {
  const router = useRouter();
  const createTeam = useCreateTeam();

  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [maturity, setMaturity] = useState<AgenticMaturity>("L0");
  const [error, setError] = useState<string | null>(null);

  const handleNameChange = (value: string) => {
    setName(value);
    const generatedSlug = value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .substring(0, 100);
    setSlug(generatedSlug);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("Team name is required");
      return;
    }

    if (!slug.trim()) {
      setError("Team slug is required");
      return;
    }

    try {
      const result = await createTeam.mutateAsync({
        name: name.trim(),
        slug: slug.trim(),
        description: description.trim() || undefined,
        organization_id: organizationId,
        settings: {
          agentic_maturity: maturity,
        },
      });

      onClose();
      router.push(`/app/teams/${result.id}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create team";
      setError(errorMessage);
    }
  };

  const handleClose = () => {
    setName("");
    setSlug("");
    setDescription("");
    setMaturity("L0");
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={handleClose} />

      <div className="relative z-10 w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Create Team</h2>
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

          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Team Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder="Enter team name"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              autoFocus
            />
          </div>

          <div>
            <label htmlFor="slug" className="block text-sm font-medium text-gray-700 mb-1">
              Team Slug <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="slug"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              placeholder="team-slug"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter team description (optional)"
              rows={2}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="maturity" className="block text-sm font-medium text-gray-700 mb-1">
              Agentic Maturity Level
            </label>
            <select
              id="maturity"
              value={maturity}
              onChange={(e) => setMaturity(e.target.value as AgenticMaturity)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {(Object.entries(AGENTIC_MATURITY_META) as [AgenticMaturity, typeof AGENTIC_MATURITY_META["L0"]][]).map(
                ([level, meta]) => (
                  <option key={level} value={level}>
                    {meta.label}
                  </option>
                )
              )}
            </select>
          </div>

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
              disabled={createTeam.isPending}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createTeam.isPending ? "Creating..." : "Create Team"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/**
 * Edit Organization Modal
 * Sprint 91: Added edit functionality for organization name/settings
 */
function EditOrganizationModal({
  isOpen,
  onClose,
  organization,
}: {
  isOpen: boolean;
  onClose: () => void;
  organization: { id: string; name: string; plan: OrganizationPlan; settings: OrganizationSettings };
}) {
  const updateOrg = useUpdateOrganization(organization.id);
  const [name, setName] = useState(organization.name);
  const [requireMfa, setRequireMfa] = useState(organization.settings?.require_mfa || false);
  const [allowedDomains, setAllowedDomains] = useState(
    (organization.settings?.allowed_domains || []).join(", ")
  );
  const [error, setError] = useState<string | null>(null);

  // Reset form when modal opens with new organization data
  useState(() => {
    setName(organization.name);
    setRequireMfa(organization.settings?.require_mfa || false);
    setAllowedDomains((organization.settings?.allowed_domains || []).join(", "));
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("Organization name is required");
      return;
    }

    try {
      const domains = allowedDomains
        .split(",")
        .map((d) => d.trim())
        .filter((d) => d.length > 0);

      const updateData: OrganizationUpdate = {
        name: name.trim(),
        settings: {
          ...organization.settings,
          require_mfa: requireMfa,
          allowed_domains: domains.length > 0 ? domains : undefined,
        },
      };
      await updateOrg.mutateAsync(updateData);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update organization");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      <div className="relative z-10 w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Edit Organization</h2>
          <button
            onClick={onClose}
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

          <div>
            <label htmlFor="orgName" className="block text-sm font-medium text-gray-700 mb-1">
              Organization Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="orgName"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter organization name"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Current Plan
            </label>
            <div className="flex items-center gap-2">
              <PlanBadge plan={organization.plan} />
              <span className="text-sm text-gray-500">
                (Contact support to change plan)
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="requireMfa"
              checked={requireMfa}
              onChange={(e) => setRequireMfa(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="requireMfa" className="text-sm font-medium text-gray-700">
              Require MFA for all members
            </label>
          </div>

          <div>
            <label htmlFor="allowedDomains" className="block text-sm font-medium text-gray-700 mb-1">
              Allowed Email Domains
            </label>
            <input
              type="text"
              id="allowedDomains"
              value={allowedDomains}
              onChange={(e) => setAllowedDomains(e.target.value)}
              placeholder="example.com, company.org"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Comma-separated list of domains. Leave empty to allow any domain.
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updateOrg.isPending}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {updateOrg.isPending ? "Saving..." : "Save Changes"}
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

export default function OrganizationDetailPage() {
  const params = useParams();
  const orgId = params.id as string;

  const [isCreateTeamOpen, setIsCreateTeamOpen] = useState(false);
  const [isEditOrgOpen, setIsEditOrgOpen] = useState(false);

  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { data: org, isLoading: orgLoading, error: orgError } = useOrganization(orgId);
  const { data: stats } = useOrganizationStats(orgId);
  const { data: teamsData } = useTeams({ organization_id: orgId });

  const teams = teamsData?.items || [];

  if (authLoading || orgLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="text-amber-600 mb-4">Please log in to view organization details.</div>
        <Link
          href="/login"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Go to Login
        </Link>
      </div>
    );
  }

  if (orgError || !org) {
    return (
      <div className="space-y-4">
        <Link
          href="/app/organizations"
          className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          Back to Organizations
        </Link>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-700">
            Organization not found or you don&apos;t have access.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <Link
            href="/app/organizations"
            className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeftIcon className="h-4 w-4" />
            Back to Organizations
          </Link>
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-50">
              <BuildingOffice2Icon className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{org.name}</h1>
              <p className="text-gray-500">/{org.slug}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 pt-1">
            <PlanBadge plan={org.plan} />
          </div>
        </div>

        <button
          onClick={() => setIsEditOrgOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <PencilIcon className="h-4 w-4" />
          Edit
        </button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          label="Teams"
          value={stats?.teams_count || org.teams_count}
          icon={UserGroupIcon}
          color="bg-indigo-50 text-indigo-600"
        />
        <StatCard
          label="Total Users"
          value={stats?.users_count || org.users_count}
          icon={UsersIcon}
          color="bg-green-50 text-green-600"
        />
        <StatCard
          label="Plan"
          value={ORGANIZATION_PLAN_META[org.plan].label}
          icon={BuildingOffice2Icon}
          color="bg-purple-50 text-purple-600"
        />
      </div>

      {/* Plan Features */}
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Plan Features</h2>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {ORGANIZATION_PLAN_META[org.plan].features.map((feature, idx) => (
            <div key={idx} className="flex items-center gap-2 text-sm text-gray-600">
              <svg className="h-4 w-4 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {feature}
            </div>
          ))}
        </div>
      </div>

      {/* Teams */}
      <div className="rounded-lg border border-gray-200 bg-white">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Teams ({teams.length})
          </h2>
          <button
            onClick={() => setIsCreateTeamOpen(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <PlusIcon className="h-4 w-4" />
            Create Team
          </button>
        </div>

        <div className="divide-y divide-gray-100">
          {teams.map((team) => (
            <TeamRow key={team.id} team={team} />
          ))}
          {teams.length === 0 && (
            <div className="py-12 text-center">
              <UserGroupIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-4 text-lg font-medium text-gray-900">No teams yet</h3>
              <p className="mt-1 text-gray-500">Create your first team to get started.</p>
              <button
                onClick={() => setIsCreateTeamOpen(true)}
                className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                <PlusIcon className="h-4 w-4" />
                Create Team
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Create Team Modal */}
      <CreateTeamModal
        isOpen={isCreateTeamOpen}
        onClose={() => setIsCreateTeamOpen(false)}
        organizationId={orgId}
      />

      {/* Edit Organization Modal - Sprint 91 */}
      {org && (
        <EditOrganizationModal
          isOpen={isEditOrgOpen}
          onClose={() => setIsEditOrgOpen(false)}
          organization={org}
        />
      )}
    </div>
  );
}
