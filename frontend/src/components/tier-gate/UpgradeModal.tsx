"use client";

/**
 * =========================================================================
 * UpgradeModal — Tier Upgrade Call-to-Action Modal
 * SDLC Orchestrator — Sprint 184 (Enterprise Integrations + Tier Enforcement)
 *
 * Displayed when a user attempts to access a locked feature.
 * Shows a plan comparison table and CTA button to the billing portal.
 *
 * Triggered by:
 *   - LockedFeature overlay click
 *   - Global 402 handler in QueryProvider (TierGateError)
 *
 * SDLC 6.1.0 — Sprint 184 P2 Deliverable
 * Reference: ADR-059 (Tier Model), tier_gate.py 402 response schema
 * =========================================================================
 */

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
// F-05 fix (Sprint 185): import shared TIER_RANK to eliminate duplication with LockedFeature
import { TIER_RANK } from "@/lib/tierConstants";

/** Plan details for comparison table */
interface PlanFeature {
  label: string;
  lite: boolean | string;
  standard: boolean | string;
  professional: boolean | string;
  enterprise: boolean | string;
}

const PLAN_FEATURES: PlanFeature[] = [
  {
    label: "Projects",
    lite: "1",
    standard: "15",
    professional: "20",
    enterprise: "Unlimited",
  },
  {
    label: "Team members",
    lite: "1",
    standard: "30",
    professional: "Unlimited",
    enterprise: "Unlimited",
  },
  {
    label: "Evidence Vault storage",
    lite: "100 MB",
    standard: "50 GB",
    professional: "100 GB",
    enterprise: "Unlimited",
  },
  {
    label: "Multi-Agent Team Engine",
    lite: false,
    standard: false,
    professional: true,
    enterprise: true,
  },
  {
    label: "Jira / GitHub integration",
    lite: false,
    standard: false,
    professional: true,
    enterprise: true,
  },
  {
    label: "OTT channels (Teams, Slack)",
    lite: false,
    standard: "Telegram only",
    professional: true,
    enterprise: true,
  },
  {
    label: "Compliance evidence (SOC2/HIPAA)",
    lite: false,
    standard: false,
    professional: "SOC2",
    enterprise: "SOC2 + HIPAA + NIST",
  },
  {
    label: "Enterprise SSO (SAML/Azure AD)",
    lite: false,
    standard: false,
    professional: false,
    enterprise: true,
  },
  {
    label: "Custom SLA + dedicated CSM",
    lite: false,
    standard: false,
    professional: false,
    enterprise: true,
  },
];

const TIER_DISPLAY: Record<string, { label: string; price: string; color: string }> = {
  LITE: { label: "LITE", price: "Free", color: "text-gray-600" },
  STANDARD: { label: "STANDARD", price: "$99–$299/mo", color: "text-green-700" },
  PROFESSIONAL: { label: "PROFESSIONAL", price: "$499/mo", color: "text-blue-700" },
  ENTERPRISE: { label: "ENTERPRISE", price: "Custom", color: "text-purple-700" },
  // Legacy mappings
  free: { label: "LITE", price: "Free", color: "text-gray-600" },
  starter: { label: "STANDARD", price: "$99–$299/mo", color: "text-green-700" },
  pro: { label: "PROFESSIONAL", price: "$499/mo", color: "text-blue-700" },
  enterprise: { label: "ENTERPRISE", price: "Custom", color: "text-purple-700" },
};

/** Check icon */
function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      className={cn("h-4 w-4 text-green-600", className)}
      aria-hidden="true"
    >
      <path
        fillRule="evenodd"
        d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
        clipRule="evenodd"
      />
    </svg>
  );
}

/** X icon */
function XIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      className={cn("h-4 w-4 text-gray-300", className)}
      aria-hidden="true"
    >
      <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
    </svg>
  );
}

/** Render a feature value as checkmark, X, or text */
function FeatureValue({ value }: { value: boolean | string }) {
  if (value === true) return <CheckIcon />;
  if (value === false) return <XIcon />;
  return <span className="text-xs text-gray-700">{value}</span>;
}

interface UpgradeModalProps {
  /** Controls modal visibility */
  open: boolean;
  /** Called when modal is dismissed */
  onClose: () => void;
  /** Required tier (backend canonical name or legacy) */
  requiredTier: string;
  /** User's current tier */
  currentTier?: string;
  /** Optional feature name for context (e.g., "Jira Integration") */
  featureLabel?: string;
  /** Billing upgrade URL — overrides env default */
  upgradeUrl?: string;
}

/**
 * UpgradeModal displays a plan comparison table and CTA button to the
 * billing portal, shown when a user attempts to access a locked feature.
 */
export function UpgradeModal({
  open,
  onClose,
  requiredTier,
  currentTier = "LITE",
  featureLabel,
  upgradeUrl = "/billing/upgrade",
}: UpgradeModalProps) {
  const required = TIER_DISPLAY[requiredTier] ?? {
    label: requiredTier,
    price: "Paid",
    color: "text-blue-700",
  };
  const current = TIER_DISPLAY[currentTier] ?? {
    label: currentTier,
    price: "Free",
    color: "text-gray-600",
  };

  const requiredRank = TIER_RANK[requiredTier] ?? 2;

  // Highlight the required tier column and above
  function isHighlighted(colTier: string): boolean {
    return (TIER_RANK[colTier] ?? 0) >= requiredRank;
  }

  function handleUpgrade() {
    window.location.href = upgradeUrl;
  }

  return (
    <Dialog open={open} onOpenChange={(isOpen) => { if (!isOpen) onClose(); }}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold">
            {featureLabel
              ? `${featureLabel} requires ${required.label}`
              : `Upgrade to ${required.label}`}
          </DialogTitle>
          <DialogDescription>
            You are on the{" "}
            <span className={cn("font-semibold", current.color)}>
              {current.label}
            </span>{" "}
            plan. This feature requires{" "}
            <span className={cn("font-semibold", required.color)}>
              {required.label}
            </span>{" "}
            or higher.
          </DialogDescription>
        </DialogHeader>

        {/* Plan comparison table */}
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className="text-left py-2 pr-4 font-medium text-gray-500 w-40">
                  Feature
                </th>
                {(["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"] as const).map(
                  (tier) => (
                    <th
                      key={tier}
                      className={cn(
                        "text-center py-2 px-3 font-semibold",
                        isHighlighted(tier)
                          ? "text-blue-700 bg-blue-50 rounded-t"
                          : "text-gray-500"
                      )}
                    >
                      <div>{TIER_DISPLAY[tier].label}</div>
                      <div className="text-xs font-normal text-gray-500 mt-0.5">
                        {TIER_DISPLAY[tier].price}
                      </div>
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {PLAN_FEATURES.map((feature) => (
                <tr key={feature.label}>
                  <td className="py-2 pr-4 text-gray-700">{feature.label}</td>
                  {(
                    [
                      ["LITE", feature.lite],
                      ["STANDARD", feature.standard],
                      ["PROFESSIONAL", feature.professional],
                      ["ENTERPRISE", feature.enterprise],
                    ] as [string, boolean | string][]
                  ).map(([tier, value]) => (
                    <td
                      key={tier}
                      className={cn(
                        "text-center py-2 px-3",
                        isHighlighted(tier) && "bg-blue-50"
                      )}
                    >
                      <FeatureValue value={value} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <DialogFooter className="mt-4 flex-col sm:flex-row gap-2">
          <Button variant="outline" onClick={onClose}>
            Maybe later
          </Button>
          <Button
            onClick={handleUpgrade}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Upgrade to {required.label} →
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default UpgradeModal;
