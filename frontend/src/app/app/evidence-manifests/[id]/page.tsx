"use client";

/**
 * Evidence Manifest Detail Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/evidence-manifests/[id]/page
 * @description Individual manifest detail with artifacts and chain info
 * @sdlc SDLC 5.1.3 Framework - Sprint 87 (Evidence Hash Chain v1)
 * @status Sprint 87 - CTO APPROVED (January 20, 2026)
 */

import React from "react";
import { useParams, useRouter } from "next/navigation";
import { useManifestDetail } from "@/hooks/useEvidenceManifest";
import {
  getChainIntegrityStatus,
  getChainStatusMetadata,
  formatFileSize,
  formatManifestTime,
  formatRelativeTime,
  getShortHash,
  isGenesisManifest,
} from "@/lib/types/evidence-manifest";
import type { ArtifactEntry } from "@/lib/types/evidence-manifest";

// =============================================================================
// Artifact Item Component
// =============================================================================

interface ArtifactItemProps {
  artifact: ArtifactEntry;
  index: number;
}

function ArtifactItem({ artifact, index }: ArtifactItemProps) {
  // Determine file type icon based on content_type
  const getFileIcon = (contentType: string) => {
    if (contentType.startsWith("image/")) {
      return (
        <svg
          className="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
          />
        </svg>
      );
    }
    if (contentType.includes("pdf")) {
      return (
        <svg
          className="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
          />
        </svg>
      );
    }
    if (contentType.includes("json") || contentType.includes("text")) {
      return (
        <svg
          className="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5"
          />
        </svg>
      );
    }
    return (
      <svg
        className="h-5 w-5"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
        />
      </svg>
    );
  };

  return (
    <div className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-10 h-10 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center">
          {getFileIcon(artifact.content_type)}
        </div>
        <div className="flex-grow min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs text-gray-400">#{index + 1}</span>
            <h4 className="font-medium text-gray-900 truncate">
              {artifact.file_path.split("/").pop() || artifact.file_path}
            </h4>
          </div>
          <p className="text-sm text-gray-500 truncate mb-2">
            {artifact.file_path}
          </p>
          <div className="flex flex-wrap gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <span className="font-medium">Size:</span>
              {formatFileSize(artifact.size_bytes)}
            </span>
            <span className="flex items-center gap-1">
              <span className="font-medium">Type:</span>
              {artifact.content_type}
            </span>
            <span className="flex items-center gap-1">
              <span className="font-medium">Uploaded:</span>
              {formatRelativeTime(artifact.uploaded_at)}
            </span>
          </div>
        </div>
      </div>

      {/* SHA256 Hash */}
      <div className="mt-3 pt-3 border-t">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-500">SHA256:</span>
          <code className="text-xs font-mono text-gray-600 bg-gray-100 px-2 py-1 rounded break-all">
            {artifact.sha256_hash}
          </code>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Hash Info Card Component
// =============================================================================

interface HashInfoCardProps {
  label: string;
  hash: string | null;
  isGenesis?: boolean;
}

function HashInfoCard({ label, hash, isGenesis }: HashInfoCardProps) {
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <p className="text-sm font-medium text-gray-500 mb-1">{label}</p>
      {hash ? (
        <code className="text-sm font-mono text-gray-900 break-all">{hash}</code>
      ) : isGenesis ? (
        <span className="text-sm text-purple-600 italic">Genesis block (no previous)</span>
      ) : (
        <span className="text-sm text-gray-400">N/A</span>
      )}
    </div>
  );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function ManifestDetailPage() {
  const params = useParams();
  const router = useRouter();
  const manifestId = params.id as string;

  const { manifest, chainStatus, isLoading, isError, error } =
    useManifestDetail(manifestId);

  const status = getChainIntegrityStatus(chainStatus);
  const statusMeta = getChainStatusMetadata(status);
  const isGenesis = manifest ? isGenesisManifest(manifest) : false;

  if (isLoading) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse mb-6" />
        <div className="space-y-6">
          <div className="h-40 bg-gray-100 rounded-lg animate-pulse" />
          <div className="h-60 bg-gray-100 rounded-lg animate-pulse" />
          <div className="h-80 bg-gray-100 rounded-lg animate-pulse" />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
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
            Error Loading Manifest
          </h3>
          <p className="text-red-700">
            {error instanceof Error ? error.message : "Failed to load manifest"}
          </p>
          <button
            onClick={() => router.back()}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!manifest) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div className="text-center py-12 bg-gray-50 rounded-lg">
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
              d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
            />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Manifest Not Found
          </h3>
          <p className="text-gray-500">
            The manifest you&apos;re looking for doesn&apos;t exist.
          </p>
          <button
            onClick={() => router.back()}
            className="mt-4 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => router.back()}
          className="p-2 hover:bg-gray-100 rounded-md transition-colors"
        >
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
              d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
            />
          </svg>
        </button>
        <div className="flex-grow">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">
              Manifest #{manifest.sequence_number}
            </h1>
            {isGenesis && (
              <span className="px-3 py-1 bg-purple-100 text-purple-700 text-sm font-medium rounded-full">
                Genesis
              </span>
            )}
            <span
              className={`px-3 py-1 ${statusMeta.bgColor} ${statusMeta.color} text-sm font-medium rounded-full flex items-center gap-1`}
            >
              <span>{statusMeta.icon}</span>
              {statusMeta.label}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Created {formatManifestTime(manifest.created_at)} by{" "}
            {manifest.created_by}
          </p>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white border rounded-lg p-4">
          <p className="text-sm text-gray-500">Artifacts</p>
          <p className="text-2xl font-bold text-gray-900">
            {manifest.artifact_count}
          </p>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <p className="text-sm text-gray-500">Total Size</p>
          <p className="text-2xl font-bold text-gray-900">
            {formatFileSize(manifest.total_size_bytes)}
          </p>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <p className="text-sm text-gray-500">Sequence</p>
          <p className="text-2xl font-bold text-gray-900">
            #{manifest.sequence_number}
          </p>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <p className="text-sm text-gray-500">Project</p>
          <p className="text-lg font-mono text-gray-900 truncate">
            {getShortHash(manifest.project_id)}
          </p>
        </div>
      </div>

      {/* Hash Chain Information */}
      <div className="bg-white border rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
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
          Hash Chain Information
        </h2>
        <div className="space-y-4">
          <HashInfoCard label="Manifest Hash" hash={manifest.manifest_hash} />
          <HashInfoCard
            label="Previous Manifest Hash"
            hash={manifest.previous_manifest_hash}
            isGenesis={isGenesis}
          />
        </div>

        {/* Digital Signature */}
        <div className="mt-4 pt-4 border-t">
          <p className="text-sm font-medium text-gray-500 mb-2 flex items-center gap-2">
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
                d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"
              />
            </svg>
            Digital Signature (Ed25519)
          </p>
          <code className="text-xs font-mono text-gray-600 bg-gray-50 p-3 rounded block break-all">
            {manifest.signature}
          </code>
        </div>
      </div>

      {/* Artifacts List */}
      <div className="bg-white border rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg
            className="h-5 w-5 text-green-600"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z"
            />
          </svg>
          Artifacts ({manifest.artifact_count})
        </h2>
        {manifest.artifacts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No artifacts in this manifest</p>
          </div>
        ) : (
          <div className="space-y-4">
            {manifest.artifacts.map((artifact, index) => (
              <ArtifactItem key={artifact.artifact_id} artifact={artifact} index={index} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
