"use client";

/**
 * Evidence Manifests Dashboard - SDLC Orchestrator
 *
 * @module frontend/src/app/app/evidence-manifests/page
 * @description Hash Chain dashboard with verification and manifest list
 * @sdlc SDLC 5.1.3 Framework - Sprint 87 (Evidence Hash Chain v1)
 * @status Sprint 87 - CTO APPROVED (January 20, 2026)
 */

import React, { useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  useEvidenceManifestDashboard,
  useVerifyChain,
} from "@/hooks/useEvidenceManifest";
import {
  getChainIntegrityStatus,
  getChainStatusMetadata,
  formatFileSize,
  formatRelativeTime,
  getShortHash,
  isGenesisManifest,
} from "@/lib/types/evidence-manifest";
import type {
  EvidenceManifest,
  ChainStatusResponse,
} from "@/lib/types/evidence-manifest";

// =============================================================================
// Chain Status Card Component
// =============================================================================

interface ChainStatusCardProps {
  projectId: string;
  chainStatus: ChainStatusResponse | undefined;
  onVerify: () => void;
  isVerifying: boolean;
}

function ChainStatusCard({
  chainStatus,
  onVerify,
  isVerifying,
}: ChainStatusCardProps) {
  const status = getChainIntegrityStatus(chainStatus);
  const statusMeta = getChainStatusMetadata(status);

  return (
    <div className={`rounded-lg border p-6 ${statusMeta.bgColor}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-3xl">{statusMeta.icon}</span>
          <div>
            <h3 className={`text-lg font-semibold ${statusMeta.color}`}>
              {statusMeta.label}
            </h3>
            <p className="text-sm text-gray-600">{statusMeta.description}</p>
          </div>
        </div>
        <button
          onClick={onVerify}
          disabled={isVerifying}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isVerifying ? (
            <>
              <svg
                className="animate-spin h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Verifying...
            </>
          ) : (
            <>
              {/* Shield Check Icon */}
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
                />
              </svg>
              Verify Chain
            </>
          )}
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
        <div className="bg-white rounded-md p-3 border">
          <p className="text-sm text-gray-500">Total Manifests</p>
          <p className="text-2xl font-bold text-gray-900">
            {chainStatus?.total_manifests ?? 0}
          </p>
        </div>
        <div className="bg-white rounded-md p-3 border">
          <p className="text-sm text-gray-500">Latest Sequence</p>
          <p className="text-2xl font-bold text-gray-900">
            #{chainStatus?.latest_sequence ?? 0}
          </p>
        </div>
        <div className="bg-white rounded-md p-3 border">
          <p className="text-sm text-gray-500">Latest Hash</p>
          <p className="text-lg font-mono text-gray-900">
            {getShortHash(chainStatus?.latest_manifest_hash ?? null)}
          </p>
        </div>
        <div className="bg-white rounded-md p-3 border">
          <p className="text-sm text-gray-500">Last Verified</p>
          <p className="text-lg text-gray-900">
            {formatRelativeTime(chainStatus?.last_verified_at)}
          </p>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Manifest List Item Component
// =============================================================================

interface ManifestListItemProps {
  manifest: EvidenceManifest;
  onClick: () => void;
}

function ManifestListItem({ manifest, onClick }: ManifestListItemProps) {
  const isGenesis = isGenesisManifest(manifest);

  return (
    <div
      onClick={onClick}
      className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 bg-blue-100 text-blue-600 rounded-full font-mono text-sm font-bold">
            #{manifest.sequence_number}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm text-gray-700">
                {getShortHash(manifest.manifest_hash)}
              </span>
              {isGenesis && (
                <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">
                  Genesis
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500">
              {manifest.artifact_count} artifacts •{" "}
              {formatFileSize(manifest.total_size_bytes)}
            </p>
          </div>
        </div>

        <div className="text-right">
          <p className="text-sm text-gray-500">
            {formatRelativeTime(manifest.created_at)}
          </p>
          <p className="text-xs text-gray-400">by {manifest.created_by}</p>
        </div>
      </div>

      {/* Hash Chain Link */}
      {manifest.previous_manifest_hash && (
        <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
          {/* Link Icon */}
          <svg
            className="h-3 w-3"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244"
            />
          </svg>
          <span>Previous: {getShortHash(manifest.previous_manifest_hash)}</span>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Hash Chain Visualization Component
// =============================================================================

interface HashChainVisualizationProps {
  manifests: EvidenceManifest[];
  onSelectManifest: (id: string) => void;
}

function HashChainVisualization({
  manifests,
  onSelectManifest,
}: HashChainVisualizationProps) {
  if (manifests.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <svg
          className="h-12 w-12 mx-auto mb-4 text-gray-300"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244"
          />
        </svg>
        <p>No manifests in the chain yet</p>
        <p className="text-sm">Upload evidence to create the first manifest</p>
      </div>
    );
  }

  // Sort by sequence number descending (newest first)
  const sortedManifests = [...manifests].sort(
    (a, b) => b.sequence_number - a.sequence_number
  );

  return (
    <div className="relative">
      {sortedManifests.map((manifest, index) => (
        <div key={manifest.id} className="relative">
          {/* Chain connector line */}
          {index < sortedManifests.length - 1 && (
            <div className="absolute left-5 top-14 w-0.5 h-8 bg-blue-200" />
          )}
          <ManifestListItem
            manifest={manifest}
            onClick={() => onSelectManifest(manifest.id)}
          />
          {index < sortedManifests.length - 1 && <div className="h-2" />}
        </div>
      ))}
    </div>
  );
}

// =============================================================================
// Project Selector Component
// =============================================================================

interface ProjectSelectorProps {
  selectedProjectId: string;
  onSelectProject: (projectId: string) => void;
}

function ProjectSelector({
  selectedProjectId,
  onSelectProject,
}: ProjectSelectorProps) {
  // In a real implementation, this would fetch projects from API
  // For now, we'll use a simple input
  return (
    <div className="flex items-center gap-2">
      <label htmlFor="project-select" className="text-sm font-medium text-gray-700">
        Project ID:
      </label>
      <input
        id="project-select"
        type="text"
        value={selectedProjectId}
        onChange={(e) => onSelectProject(e.target.value)}
        placeholder="Enter project ID"
        className="px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
      />
    </div>
  );
}

// =============================================================================
// Verification History Component
// =============================================================================

interface VerificationHistoryProps {
  history: Array<{
    id: string;
    verified_at: string;
    manifests_checked: number;
    chain_valid: boolean;
    verified_by: string;
    error_message: string | null;
  }>;
}

function VerificationHistory({ history }: VerificationHistoryProps) {
  if (history.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500 text-sm">
        No verification history
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {history.slice(0, 5).map((item) => (
        <div
          key={item.id}
          className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
        >
          <div className="flex items-center gap-3">
            <span
              className={`text-lg ${item.chain_valid ? "text-green-500" : "text-red-500"}`}
            >
              {item.chain_valid ? "✓" : "✗"}
            </span>
            <div>
              <p className="text-sm font-medium">
                {item.chain_valid ? "Valid" : "Invalid"}
              </p>
              <p className="text-xs text-gray-500">
                {item.manifests_checked} manifests checked
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">
              {formatRelativeTime(item.verified_at)}
            </p>
            <p className="text-xs text-gray-400">by {item.verified_by}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function EvidenceManifestsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [projectId, setProjectId] = useState(
    searchParams.get("project_id") || ""
  );

  const { chainStatus, verificationHistory, manifests, isLoading, error, refetch } =
    useEvidenceManifestDashboard(projectId || undefined);

  const verifyChainMutation = useVerifyChain();

  const handleVerifyChain = useCallback(() => {
    if (!projectId) return;
    verifyChainMutation.mutate(
      { project_id: projectId },
      {
        onSuccess: () => {
          refetch();
        },
      }
    );
  }, [projectId, verifyChainMutation, refetch]);

  const handleSelectManifest = useCallback(
    (manifestId: string) => {
      router.push(`/app/evidence-manifests/${manifestId}`);
    },
    [router]
  );

  const handleSelectProject = useCallback(
    (newProjectId: string) => {
      setProjectId(newProjectId);
      if (newProjectId) {
        router.push(`/app/evidence-manifests?project_id=${newProjectId}`);
      }
    },
    [router]
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Evidence Manifests</h1>
          <p className="text-sm text-gray-500 mt-1">
            Tamper-evident hash chain for evidence integrity
          </p>
        </div>
        <ProjectSelector
          selectedProjectId={projectId}
          onSelectProject={handleSelectProject}
        />
      </div>

      {!projectId ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <svg
            className="h-16 w-16 mx-auto mb-4 text-gray-300"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z"
            />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Select a Project
          </h3>
          <p className="text-gray-500">
            Enter a project ID to view its evidence manifest chain
          </p>
        </div>
      ) : isLoading ? (
        <div className="space-y-6">
          {/* Loading skeleton */}
          <div className="h-40 bg-gray-100 rounded-lg animate-pulse" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 h-96 bg-gray-100 rounded-lg animate-pulse" />
            <div className="h-96 bg-gray-100 rounded-lg animate-pulse" />
          </div>
        </div>
      ) : error ? (
        <div className="text-center py-12 bg-red-50 rounded-lg">
          <svg
            className="h-12 w-12 mx-auto mb-4 text-red-400"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
            />
          </svg>
          <h3 className="text-lg font-medium text-red-900 mb-2">
            Error Loading Manifests
          </h3>
          <p className="text-red-700">
            {error instanceof Error ? error.message : "Failed to load data"}
          </p>
          <button
            onClick={() => refetch()}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Chain Status Card */}
          <ChainStatusCard
            projectId={projectId}
            chainStatus={chainStatus}
            onVerify={handleVerifyChain}
            isVerifying={verifyChainMutation.isPending}
          />

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Manifest List (2/3 width) */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  {/* Link Icon */}
                  <svg
                    className="h-5 w-5 text-blue-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244"
                    />
                  </svg>
                  Hash Chain
                </h2>
                <HashChainVisualization
                  manifests={manifests?.manifests ?? []}
                  onSelectManifest={handleSelectManifest}
                />
              </div>
            </div>

            {/* Verification History (1/3 width) */}
            <div>
              <div className="bg-white rounded-lg border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  {/* Clock Icon */}
                  <svg
                    className="h-5 w-5 text-gray-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  Verification History
                </h2>
                <VerificationHistory
                  history={verificationHistory?.verifications ?? []}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
