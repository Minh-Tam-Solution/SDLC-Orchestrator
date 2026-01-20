/**
 * AGENTS.md Repo Detail Loading State
 * @module frontend/src/app/app/agents-md/[repoId]/loading
 * @status Sprint 85 - AGENTS.md UI
 */

export default function AgentsMdRepoDetailLoading() {
  return (
    <div className="space-y-6">
      {/* Back link skeleton */}
      <div className="h-5 w-36 rounded bg-gray-200 animate-pulse" />

      {/* Header skeleton */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-lg bg-gray-200 animate-pulse" />
          <div>
            <div className="h-8 w-48 rounded bg-gray-200 animate-pulse" />
            <div className="mt-2 h-4 w-32 rounded bg-gray-200 animate-pulse" />
          </div>
        </div>
        <div className="h-10 w-32 rounded bg-gray-200 animate-pulse" />
      </div>

      {/* Metadata skeleton */}
      <div className="flex gap-4">
        <div className="h-4 w-32 rounded bg-gray-200 animate-pulse" />
        <div className="h-4 w-24 rounded bg-gray-200 animate-pulse" />
      </div>

      {/* Content Grid skeleton */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <div className="h-[400px] rounded-lg border border-gray-200 bg-gray-100 animate-pulse" />
          <div className="h-48 rounded-lg border border-gray-200 bg-gray-100 animate-pulse" />
        </div>
        <div className="space-y-4">
          <div className="h-6 w-32 rounded bg-gray-200 animate-pulse" />
          <div className="h-32 rounded-lg border border-gray-200 bg-gray-100 animate-pulse" />
          <div className="h-32 rounded-lg border border-gray-200 bg-gray-100 animate-pulse" />
        </div>
      </div>
    </div>
  );
}
