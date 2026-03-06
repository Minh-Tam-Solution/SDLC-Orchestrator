/**
 * Data Residency Management Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/data-residency/page
 * @description Region selection, storage routing, and GDPR compliance badges
 * @sdlc SDLC 6.1.1 — Sprint 214 Track A (ENT Compliance #10)
 * @status Active — ENTERPRISE+ required (ADR-063)
 */

"use client";

import { useState } from "react";
import { LockedFeature } from "@/components/tier-gate/LockedFeature";
import { useUserTier } from "@/hooks/useUserTier";
import {
  useAvailableRegions,
  useProjectRegion,
  useUpdateProjectRegion,
  type RegionInfo,
} from "@/hooks/useDataResidency";

export default function DataResidencyPage() {
  const { effectiveTier, isLoading: tierLoading } = useUserTier();
  const currentTier = tierLoading ? "LITE" : effectiveTier;

  return (
    <LockedFeature
      requiredTier="ENTERPRISE"
      currentTier={currentTier}
      featureLabel="Data Residency Management"
    >
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Data Residency Management</h1>
          <p className="mt-1 text-sm text-gray-500">
            Choose where your project data is stored. Supports VN (Asia Pacific), EU (Frankfurt — GDPR
            compliant), and US regions.
          </p>
        </div>

        <AvailableRegionsSection />
        <ProjectRegionSection />
      </div>
    </LockedFeature>
  );
}

// ---------------------------------------------------------------------------
// Available Regions
// ---------------------------------------------------------------------------

const REGION_META: Record<string, { flag: string; description: string }> = {
  VN: { flag: "🇻🇳", description: "Asia Pacific — Ho Chi Minh City" },
  EU: { flag: "🇪🇺", description: "Europe — Frankfurt (GDPR compliant)" },
  US: { flag: "🇺🇸", description: "United States — Virginia" },
};

function AvailableRegionsSection() {
  const { data, isLoading, error } = useAvailableRegions();

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900">Available Regions</h2>

      {isLoading && <p className="mt-3 text-sm text-gray-500">Loading regions...</p>}
      {error && <p className="mt-3 text-sm text-red-600">Error: {error.message}</p>}

      {data && (
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {data.regions.map((region: RegionInfo) => {
            const meta = REGION_META[region.region] || { flag: "🌍", description: region.display_name };
            return (
              <div
                key={region.region}
                className="rounded-lg border border-gray-200 p-4 hover:border-blue-300"
              >
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{meta.flag}</span>
                  <div>
                    <h3 className="font-semibold text-gray-900">{region.display_name}</h3>
                    <p className="text-xs text-gray-500">{meta.description}</p>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  <span className="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600">
                    {region.region}
                  </span>
                  {region.gdpr_compliant && (
                    <span className="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-green-100 text-green-800">
                      GDPR Compliant
                    </span>
                  )}
                </div>
                <p className="mt-2 truncate text-xs text-gray-400" title={region.endpoint_url}>
                  {region.endpoint_url}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Project Region Selector
// ---------------------------------------------------------------------------

function ProjectRegionSection() {
  const { data: regionsData } = useAvailableRegions();
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const { data: projectRegion, isLoading: regionLoading } = useProjectRegion(
    selectedProjectId || undefined
  );
  const updateRegion = useUpdateProjectRegion();
  const [confirmRegion, setConfirmRegion] = useState<string | null>(null);

  const handleChangeRegion = (newRegion: string) => {
    if (projectRegion && newRegion !== projectRegion.data_region) {
      setConfirmRegion(newRegion);
    }
  };

  const handleConfirm = () => {
    if (!selectedProjectId || !confirmRegion) return;
    updateRegion.mutate(
      { projectId: selectedProjectId, data: { data_region: confirmRegion as "VN" | "EU" | "US" } },
      {
        onSuccess: () => setConfirmRegion(null),
      }
    );
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900">Project Region Settings</h2>
      <p className="mt-1 text-sm text-gray-500">
        Select a project to view or change its data storage region.
      </p>

      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700">Project ID</label>
        <input
          type="text"
          value={selectedProjectId}
          onChange={(e) => {
            setSelectedProjectId(e.target.value);
            setConfirmRegion(null);
          }}
          placeholder="Enter project UUID..."
          className="mt-1 block w-full max-w-md rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      {selectedProjectId && regionLoading && (
        <p className="mt-3 text-sm text-gray-500">Loading project region...</p>
      )}

      {projectRegion && (
        <div className="mt-4">
          <div className="rounded-lg bg-blue-50 p-4">
            <p className="text-sm font-medium text-blue-900">
              {projectRegion.project_name}
            </p>
            <p className="text-xs text-blue-700">
              Current region: <strong>{projectRegion.data_region}</strong> — Bucket: {projectRegion.bucket}
            </p>
          </div>

          {regionsData && (
            <div className="mt-4">
              <p className="text-sm font-medium text-gray-700">Change region:</p>
              <div className="mt-2 flex gap-2">
                {regionsData.regions.map((r: RegionInfo) => (
                  <button
                    key={r.region}
                    onClick={() => handleChangeRegion(r.region)}
                    disabled={r.region === projectRegion.data_region}
                    className={`rounded-md border px-4 py-2 text-sm font-medium transition ${
                      r.region === projectRegion.data_region
                        ? "border-blue-300 bg-blue-100 text-blue-800 cursor-default"
                        : "border-gray-300 bg-white text-gray-700 hover:border-blue-400 hover:bg-blue-50"
                    }`}
                  >
                    {REGION_META[r.region]?.flag || "🌍"} {r.region}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Confirmation Dialog */}
          {confirmRegion && (
            <div className="mt-4 rounded-lg border border-yellow-200 bg-yellow-50 p-4">
              <p className="text-sm font-medium text-yellow-800">
                Confirm region change: {projectRegion.data_region} → {confirmRegion}
              </p>
              {projectRegion.data_region === "EU" && confirmRegion !== "EU" && (
                <p className="mt-1 text-xs text-red-600">
                  Warning: Moving data out of EU may have GDPR implications. This action will be logged.
                </p>
              )}
              <div className="mt-3 flex gap-2">
                <button
                  onClick={handleConfirm}
                  disabled={updateRegion.isPending}
                  className="rounded-md bg-yellow-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-yellow-700 disabled:opacity-50"
                >
                  {updateRegion.isPending ? "Updating..." : "Confirm Change"}
                </button>
                <button
                  onClick={() => setConfirmRegion(null)}
                  className="rounded-md border border-gray-300 px-4 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
              {updateRegion.isError && (
                <p className="mt-2 text-sm text-red-600">{updateRegion.error.message}</p>
              )}
            </div>
          )}

          {updateRegion.isSuccess && !confirmRegion && (
            <div className="mt-3 rounded-lg border border-green-200 bg-green-50 p-3">
              <p className="text-sm text-green-800">
                Region updated successfully: {updateRegion.data.old_region} → {updateRegion.data.new_region}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
