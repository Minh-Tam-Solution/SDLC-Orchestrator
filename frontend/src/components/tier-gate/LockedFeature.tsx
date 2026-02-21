"use client";

/**
 * =========================================================================
 * LockedFeature — Tier Gate UI Component
 * SDLC Orchestrator — Sprint 184 (Enterprise Integrations + Tier Enforcement)
 *
 * Wraps any feature that requires a higher subscription tier.
 * Renders children with a semi-transparent overlay + lock icon when the
 * user's current tier is below the required tier.
 * Clicking the overlay opens the UpgradeModal.
 *
 * Usage:
 *   <LockedFeature requiredTier="PROFESSIONAL" currentTier={userTier}>
 *     <FeatureComponent />
 *   </LockedFeature>
 *
 * SDLC 6.1.0 — Sprint 184 P2 Deliverable
 * Reference: ADR-059 Decision 1 (Tier Enforcement), tier_gate.py middleware
 * =========================================================================
 */

import { useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { UpgradeModal } from "./UpgradeModal";
// F-05 fix (Sprint 185): import shared TIER_RANK + BackendTier from tierConstants
// to eliminate duplication between LockedFeature and UpgradeModal
import { TIER_RANK } from "@/lib/tierConstants";
export type { BackendTier } from "@/lib/tierConstants";

interface LockedFeatureProps {
  /** Minimum tier required to access this feature */
  requiredTier: string;
  /** User's current effective tier */
  currentTier?: string;
  /** Feature label shown in UpgradeModal title (e.g., "Jira Integration") */
  featureLabel?: string;
  /** URL to billing upgrade page — defaults to /billing/upgrade */
  upgradeUrl?: string;
  /** React children to lock */
  children: ReactNode;
  /** Additional CSS classes on the wrapper */
  className?: string;
}

/** Lock SVG icon */
function LockIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      aria-hidden="true"
    >
      <path
        fillRule="evenodd"
        d="M12 1.5a5.25 5.25 0 00-5.25 5.25v3a3 3 0 00-3 3v6.75a3 3 0 003 3h10.5a3 3 0 003-3v-6.75a3 3 0 00-3-3v-3c0-2.9-2.35-5.25-5.25-5.25zm3.75 8.25v-3a3.75 3.75 0 10-7.5 0v3h7.5z"
        clipRule="evenodd"
      />
    </svg>
  );
}

/**
 * LockedFeature wraps children with a click-to-upgrade overlay when the
 * user's current tier is below the required tier.
 */
export function LockedFeature({
  requiredTier,
  currentTier = "LITE",
  featureLabel,
  upgradeUrl = "/billing/upgrade",
  children,
  className,
}: LockedFeatureProps) {
  const [modalOpen, setModalOpen] = useState(false);

  const currentRank = TIER_RANK[currentTier] ?? 1;
  const requiredRank = TIER_RANK[requiredTier] ?? 2;
  const isLocked = currentRank < requiredRank;

  // If the user already has access, render children as-is
  if (!isLocked) {
    return <>{children}</>;
  }

  const tierLabels: Record<string, string> = {
    STANDARD: "Standard",
    PROFESSIONAL: "Professional",
    ENTERPRISE: "Enterprise",
    pro: "Professional",
    enterprise: "Enterprise",
    starter: "Standard",
  };
  const requiredTierLabel = tierLabels[requiredTier] ?? requiredTier;

  return (
    <>
      {/* Locked wrapper */}
      <div className={cn("relative", className)}>
        {/* Blurred / faded children */}
        <div
          className="pointer-events-none select-none opacity-40 blur-[1px]"
          aria-hidden="true"
        >
          {children}
        </div>

        {/* Overlay — full coverage, click opens modal */}
        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className={cn(
            "absolute inset-0 flex flex-col items-center justify-center gap-2",
            "cursor-pointer rounded-lg bg-white/60 backdrop-blur-[2px]",
            "hover:bg-white/75 transition-colors duration-150",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          )}
          aria-label={`Upgrade to ${requiredTierLabel} to unlock this feature`}
          title={`Upgrade to ${requiredTierLabel} to unlock this feature`}
        >
          <LockIcon className="h-8 w-8 text-gray-500" />
          <span className="text-sm font-semibold text-gray-700">
            Upgrade to {requiredTierLabel}
          </span>
        </button>
      </div>

      {/* Upgrade modal */}
      <UpgradeModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        requiredTier={requiredTier}
        currentTier={currentTier}
        featureLabel={featureLabel}
        upgradeUrl={upgradeUrl}
      />
    </>
  );
}

export default LockedFeature;
