/**
 * AGENTS.md Dashboard Loading State
 * @module frontend/src/app/app/agents-md/loading
 * @status Sprint 85 - AGENTS.md UI
 */

export default function AgentsMdDashboardLoading() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div>
          <div className="h-8 w-64 rounded bg-gray-200 animate-pulse" />
          <div className="mt-2 h-4 w-96 rounded bg-gray-200 animate-pulse" />
        </div>
        <div className="h-10 w-32 rounded bg-gray-200 animate-pulse" />
      </div>

      {/* Stats skeleton */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-gray-200 animate-pulse" />
              <div>
                <div className="h-8 w-16 rounded bg-gray-200 animate-pulse" />
                <div className="mt-1 h-4 w-24 rounded bg-gray-200 animate-pulse" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Search skeleton */}
      <div className="flex items-center gap-4">
        <div className="h-10 flex-1 rounded-lg bg-gray-200 animate-pulse" />
        <div className="h-10 w-32 rounded-lg bg-gray-200 animate-pulse" />
      </div>

      {/* Table skeleton */}
      <div className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-200 px-4 py-3">
          <div className="h-4 w-full rounded bg-gray-200 animate-pulse" />
        </div>
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="border-b border-gray-200 px-4 py-4">
            <div className="h-10 w-full rounded bg-gray-200 animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}
