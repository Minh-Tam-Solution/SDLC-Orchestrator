/**
 * Evidence Manifests Loading Skeleton - SDLC Orchestrator
 *
 * @module frontend/src/app/app/evidence-manifests/loading
 * @description Loading state for Evidence Manifests page
 * @sdlc SDLC 5.1.3 Framework - Sprint 87 (Evidence Hash Chain v1)
 */

export default function EvidenceManifestsLoading() {
  return (
    <div className="p-6 max-w-7xl mx-auto animate-pulse">
      {/* Header Skeleton */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="h-8 w-48 bg-gray-200 rounded mb-2" />
          <div className="h-4 w-64 bg-gray-100 rounded" />
        </div>
        <div className="h-10 w-64 bg-gray-200 rounded" />
      </div>

      {/* Chain Status Card Skeleton */}
      <div className="rounded-lg border bg-gray-50 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 bg-gray-200 rounded-full" />
            <div>
              <div className="h-6 w-24 bg-gray-200 rounded mb-1" />
              <div className="h-4 w-48 bg-gray-100 rounded" />
            </div>
          </div>
          <div className="h-10 w-32 bg-gray-200 rounded" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-md p-3 border">
              <div className="h-4 w-20 bg-gray-100 rounded mb-2" />
              <div className="h-8 w-16 bg-gray-200 rounded" />
            </div>
          ))}
        </div>
      </div>

      {/* Main Content Grid Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Manifest List Skeleton */}
        <div className="lg:col-span-2 bg-white rounded-lg border p-6">
          <div className="h-6 w-32 bg-gray-200 rounded mb-4" />
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="border rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 bg-gray-200 rounded-full" />
                  <div className="flex-grow">
                    <div className="h-4 w-32 bg-gray-200 rounded mb-2" />
                    <div className="h-3 w-48 bg-gray-100 rounded" />
                  </div>
                  <div className="text-right">
                    <div className="h-4 w-16 bg-gray-100 rounded mb-1" />
                    <div className="h-3 w-20 bg-gray-50 rounded" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Verification History Skeleton */}
        <div className="bg-white rounded-lg border p-6">
          <div className="h-6 w-40 bg-gray-200 rounded mb-4" />
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                <div className="flex items-center gap-3">
                  <div className="h-6 w-6 bg-gray-200 rounded" />
                  <div>
                    <div className="h-4 w-16 bg-gray-200 rounded mb-1" />
                    <div className="h-3 w-24 bg-gray-100 rounded" />
                  </div>
                </div>
                <div className="text-right">
                  <div className="h-4 w-12 bg-gray-100 rounded mb-1" />
                  <div className="h-3 w-16 bg-gray-50 rounded" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
