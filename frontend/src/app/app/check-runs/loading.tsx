/**
 * Check Runs Loading Skeleton - SDLC Orchestrator
 *
 * @module frontend/src/app/app/check-runs/loading
 * @description Loading skeleton for Check Runs page
 * @sdlc SDLC 5.1.3 Framework - Sprint 86 (GitHub Check Run UI)
 * @status Sprint 86 - CTO APPROVED (January 20, 2026)
 */

export default function CheckRunsLoading() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="flex items-start justify-between">
        <div>
          <div className="h-8 w-40 bg-gray-200 rounded animate-pulse" />
          <div className="mt-2 h-4 w-64 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="flex gap-2">
          <div className="h-10 w-24 bg-gray-200 rounded animate-pulse" />
          <div className="h-10 w-24 bg-gray-200 rounded animate-pulse" />
        </div>
      </div>

      {/* Stats skeleton */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 rounded-lg border bg-white p-4 animate-pulse">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-gray-200" />
              <div className="space-y-2">
                <div className="h-3 w-16 bg-gray-200 rounded" />
                <div className="h-6 w-12 bg-gray-200 rounded" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Mode stats skeleton */}
      <div className="h-24 rounded-lg bg-gray-100 animate-pulse" />

      {/* List skeleton */}
      <div>
        <div className="h-6 w-48 bg-gray-200 rounded animate-pulse mb-4" />
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="rounded-lg border bg-white p-4 animate-pulse">
              <div className="flex items-center gap-3">
                <div className="h-6 w-6 bg-gray-200 rounded-full" />
                <div className="flex-1 space-y-2">
                  <div className="h-5 w-48 bg-gray-200 rounded" />
                  <div className="h-4 w-32 bg-gray-100 rounded" />
                </div>
                <div className="flex gap-2">
                  <div className="h-8 w-20 bg-gray-200 rounded" />
                  <div className="h-8 w-20 bg-gray-200 rounded" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
