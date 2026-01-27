/**
 * Teams List Page - SDLC Orchestrator Dashboard
 *
 * @module frontend/src/app/app/teams/page
 * @description Team list and management page
 * @sdlc SDLC 5.1.3 Framework - Sprint 84 (Teams & Organizations UI)
 * @status Sprint 84 - CTO APPROVED (January 20, 2026)
 */

"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTeams, useCreateTeam, type Team } from "@/hooks/useTeams";
import { useOrganizations } from "@/hooks/useOrganizations";
import { useAuth } from "@/hooks/useAuth";
import {
  AGENTIC_MATURITY_META,
  type AgenticMaturity,
} from "@/lib/types/team";

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

function UsersIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
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

// =============================================================================
// Components
// =============================================================================

function MaturityBadge({ maturity }: { maturity?: AgenticMaturity }) {
  const level = maturity || "L0";
  const meta = AGENTIC_MATURITY_META[level];

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${meta.color}`}>
      {meta.label}
    </span>
  );
}

function TeamCard({ team }: { team: Team }) {
  const maturity = team.settings?.agentic_maturity || "L0";

  return (
    <Link
      href={`/app/teams/${team.id}`}
      className="group block rounded-lg border border-gray-200 bg-white p-6 transition-all hover:border-blue-300 hover:shadow-md"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50">
            <UsersIcon className="h-5 w-5 text-indigo-600" />
          </div>
          <div>
            <h3 className="font-medium text-gray-900 group-hover:text-blue-600">
              {team.name}
            </h3>
            <p className="text-sm text-gray-500 line-clamp-1">
              {team.description || "No description"}
            </p>
          </div>
        </div>
        <ChevronRightIcon className="h-5 w-5 text-gray-400 group-hover:text-blue-600" />
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <MaturityBadge maturity={maturity} />
        <div className="flex items-center gap-1 text-sm text-gray-500">
          <UsersIcon className="h-4 w-4" />
          <span>{team.human_members_count} humans</span>
        </div>
        {team.ai_agents_count > 0 && (
          <div className="flex items-center gap-1 text-sm text-orange-600">
            <BotIcon className="h-4 w-4" />
            <span>{team.ai_agents_count} AI agents</span>
          </div>
        )}
        <div className="flex items-center gap-1 text-sm text-gray-500">
          <FolderIcon className="h-4 w-4" />
          <span>{team.projects_count} projects</span>
        </div>
      </div>
    </Link>
  );
}

function TeamCardSkeleton() {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 animate-pulse">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-gray-200" />
          <div className="space-y-2">
            <div className="h-4 w-32 rounded bg-gray-200" />
            <div className="h-3 w-48 rounded bg-gray-200" />
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

function CreateTeamModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const router = useRouter();
  const createTeam = useCreateTeam();
  const { data: orgsData } = useOrganizations();
  const organizations = orgsData?.items || [];

  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [organizationId, setOrganizationId] = useState("");
  const [maturity, setMaturity] = useState<AgenticMaturity>("L0");
  const [error, setError] = useState<string | null>(null);

  // Auto-generate slug from name
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

    if (!organizationId) {
      setError("Please select an organization");
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
      // Sprint 105: Handle API error object { detail, status } properly
      const apiErr = err as { detail?: string; status?: number };
      const errorMessage = apiErr.detail || (err instanceof Error ? err.message : "Failed to create team");
      setError(errorMessage);
    }
  };

  const handleClose = () => {
    setName("");
    setSlug("");
    setDescription("");
    setOrganizationId("");
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
          <h2 className="text-lg font-semibold text-gray-900">Create New Team</h2>
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

          {/* Organization Select */}
          <div>
            <label htmlFor="organization" className="block text-sm font-medium text-gray-700 mb-1">
              Organization <span className="text-red-500">*</span>
            </label>
            <select
              id="organization"
              value={organizationId}
              onChange={(e) => setOrganizationId(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">Select an organization</option>
              {organizations.map((org) => (
                <option key={org.id} value={org.id}>
                  {org.name}
                </option>
              ))}
            </select>
          </div>

          {/* Team Name */}
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

          {/* Team Slug */}
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
            <p className="mt-1 text-xs text-gray-500">URL-friendly identifier (unique per organization)</p>
          </div>

          {/* Description */}
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

          {/* Agentic Maturity */}
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
                    {meta.label} - {meta.description}
                  </option>
                )
              )}
            </select>
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
              disabled={createTeam.isPending}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createTeam.isPending ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Creating...
                </>
              ) : (
                "Create Team"
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

export default function TeamsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { data: teamsData, isLoading, error } = useTeams();
  const teams = teamsData?.items || [];

  if (authLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="text-amber-600 mb-4">Please log in to view teams.</div>
        <Link
          href="/login"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Go to Login
        </Link>
      </div>
    );
  }

  const filteredTeams = teams.filter((team) => {
    const matchesSearch =
      team.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (team.description || "").toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Teams</h1>
          <p className="mt-1 text-gray-500">
            Manage your teams and collaborate with AI agents
          </p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <PlusIcon className="h-4 w-4" />
          New Team
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search teams..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      {/* Error state - only show for actual errors, not empty data */}
      {error && !teams.length && (
        <div className="hidden">
          {/* Silently handle errors when no data - show empty state instead */}
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <TeamCardSkeleton key={i} />
          ))}
        </div>
      )}

      {/* Teams grid */}
      {!isLoading && !error && filteredTeams.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredTeams.map((team) => (
            <TeamCard key={team.id} team={team} />
          ))}
        </div>
      )}

      {/* Empty state - show when no teams (including error cases) */}
      {!isLoading && filteredTeams.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 p-12">
          <UsersIcon className="h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No teams found</h3>
          <p className="mt-1 text-gray-500">
            {searchQuery
              ? "Try adjusting your search query"
              : "Get started by creating a new team"}
          </p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <PlusIcon className="h-4 w-4" />
            New Team
          </button>
        </div>
      )}

      {/* Create Team Modal */}
      <CreateTeamModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </div>
  );
}
