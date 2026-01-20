/**
 * Evidence Manifest Types - SDLC Orchestrator
 *
 * @module frontend/src/lib/types/evidence-manifest
 * @description TypeScript interfaces for Evidence Hash Chain (P0 Blocker)
 * @sdlc SDLC 5.1.3 Framework - Sprint 87 (Evidence Hash Chain v1)
 * @status Sprint 87 - CTO APPROVED (January 20, 2026)
 */

// =============================================================================
// Artifact Types
// =============================================================================

/**
 * Evidence artifact stored in manifest
 */
export interface ArtifactEntry {
  artifact_id: string;
  file_path: string;
  sha256_hash: string;
  size_bytes: number;
  content_type: string;
  uploaded_at: string;
  uploaded_by: string;
  metadata?: Record<string, unknown>;
}

/**
 * Input for creating manifest artifact
 */
export interface ArtifactInput {
  artifact_id: string;
  file_path: string;
  sha256_hash: string;
  size_bytes: number;
  content_type: string;
  uploaded_at: string;
  uploaded_by: string;
  metadata?: Record<string, unknown>;
}

// =============================================================================
// Manifest Types
// =============================================================================

/**
 * Evidence Manifest - Tamper-evident hash chain entry
 */
export interface EvidenceManifest {
  id: string;
  project_id: string;
  sequence_number: number;
  manifest_hash: string;
  previous_manifest_hash: string | null;
  artifacts: ArtifactEntry[];
  signature: string;
  is_genesis: boolean;
  created_at: string;
  created_by: string;
  artifact_count: number;
  total_size_bytes: number;
}

/**
 * Manifest list response
 */
export interface ManifestListResponse {
  total: number;
  manifests: EvidenceManifest[];
}

/**
 * Create manifest request
 */
export interface CreateManifestRequest {
  project_id: string;
  artifacts: ArtifactInput[];
}

// =============================================================================
// Verification Types
// =============================================================================

/**
 * Chain verification request
 */
export interface VerifyChainRequest {
  project_id: string;
  verified_by?: string;
}

/**
 * Chain verification result
 */
export interface VerifyChainResponse {
  is_valid: boolean;
  manifest_id?: string;
  errors: string[];
  warnings: string[];
  verified_at: string;
  manifests_checked: number;
}

/**
 * Chain status summary
 */
export interface ChainStatusResponse {
  project_id: string;
  total_manifests: number;
  latest_sequence: number;
  latest_manifest_hash: string | null;
  latest_manifest_at: string | null;
  last_verification_valid: boolean | null;
  last_verified_at: string | null;
  last_verified_by: string | null;
}

/**
 * Verification history item
 */
export interface VerificationHistoryItem {
  id: string;
  project_id: string;
  verified_at: string;
  manifests_checked: number;
  chain_valid: boolean;
  first_broken_at: string | null;
  error_message: string | null;
  verified_by: string;
}

/**
 * Verification history response
 */
export interface VerificationHistoryResponse {
  total: number;
  verifications: VerificationHistoryItem[];
}

// =============================================================================
// List Params
// =============================================================================

/**
 * Manifest list params
 */
export interface ManifestListParams {
  project_id: string;
  limit?: number;
  offset?: number;
}

// =============================================================================
// UI Helper Types
// =============================================================================

/**
 * Chain integrity status for UI
 */
export type ChainIntegrityStatus =
  | "verified" // Chain verified, all manifests valid
  | "unverified" // Never verified
  | "broken" // Chain broken at some point
  | "pending"; // Verification in progress

/**
 * Manifest status for UI badge
 */
export interface ManifestStatusMetadata {
  status: ChainIntegrityStatus;
  label: string;
  description: string;
  icon: string;
  color: string;
  bgColor: string;
}

/**
 * Status metadata for chain integrity
 */
export const CHAIN_INTEGRITY_STATUS: ManifestStatusMetadata[] = [
  {
    status: "verified",
    label: "Verified",
    description: "Hash chain integrity verified - all manifests are valid",
    icon: "✅",
    color: "text-green-600",
    bgColor: "bg-green-50",
  },
  {
    status: "unverified",
    label: "Unverified",
    description: "Chain has not been verified yet",
    icon: "⏳",
    color: "text-gray-600",
    bgColor: "bg-gray-50",
  },
  {
    status: "broken",
    label: "Broken",
    description: "Chain integrity compromised - tampering detected",
    icon: "❌",
    color: "text-red-600",
    bgColor: "bg-red-50",
  },
  {
    status: "pending",
    label: "Verifying",
    description: "Chain verification in progress",
    icon: "🔄",
    color: "text-blue-600",
    bgColor: "bg-blue-50",
  },
];

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get chain integrity status metadata
 */
export function getChainStatusMetadata(
  status: ChainIntegrityStatus
): ManifestStatusMetadata {
  return (
    CHAIN_INTEGRITY_STATUS.find((s) => s.status === status) ?? {
      status: "unverified",
      label: "Unknown",
      description: "Unknown status",
      icon: "❓",
      color: "text-gray-600",
      bgColor: "bg-gray-50",
    }
  );
}

/**
 * Get chain integrity status from verification result
 */
export function getChainIntegrityStatus(
  chainStatus?: ChainStatusResponse
): ChainIntegrityStatus {
  if (!chainStatus) return "unverified";

  if (chainStatus.last_verification_valid === null) {
    return "unverified";
  }

  return chainStatus.last_verification_valid ? "verified" : "broken";
}

/**
 * Format file size in bytes to human-readable
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

/**
 * Get short hash (first 8 characters)
 */
export function getShortHash(hash: string | null): string {
  if (!hash) return "N/A";
  return hash.slice(0, 8);
}

/**
 * Format manifest timestamp
 */
export function formatManifestTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Format relative time for manifest
 */
export function formatRelativeTime(dateString?: string | null): string {
  if (!dateString) return "Never";
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

/**
 * Check if manifest is genesis (first in chain)
 */
export function isGenesisManifest(manifest: EvidenceManifest): boolean {
  return manifest.is_genesis || manifest.previous_manifest_hash === null;
}

/**
 * Get verification status label
 */
export function getVerificationStatusLabel(isValid: boolean): string {
  return isValid ? "Valid" : "Invalid";
}

/**
 * Get verifier type label
 */
export function getVerifierLabel(verifiedBy: string): string {
  if (verifiedBy === "system-cron") return "System (Scheduled)";
  if (verifiedBy === "api-request") return "API Request";
  if (verifiedBy.startsWith("user-")) return "User";
  return verifiedBy;
}
