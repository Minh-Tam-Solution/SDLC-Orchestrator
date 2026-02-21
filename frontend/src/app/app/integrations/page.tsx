/**
 * Integrations Overview Page — SDLC Orchestrator
 *
 * @module frontend/src/app/app/integrations/page
 * @description List of available third-party integrations with tier badges.
 * @sdlc SDLC 6.1.0 — Sprint 185 (F-07: integration hub with tier gates)
 */

"use client";

import Link from "next/link";

const integrations = [
  {
    id: "jira",
    name: "Jira",
    vendor: "Atlassian",
    description:
      "Sync sprint issues to the Evidence Vault as GateEvidence records. Idempotent — re-running updates existing evidence.",
    href: "/app/integrations/jira",
    requiredTier: "PROFESSIONAL",
    status: "available" as const,
  },
  {
    id: "github",
    name: "GitHub",
    vendor: "GitHub Inc.",
    description:
      "Collect PR evidence, run Check Runs, and sync GitHub Projects to SDLC gates.",
    href: "/app/check-runs",
    requiredTier: "STANDARD",
    status: "available" as const,
  },
  {
    id: "slack",
    name: "Slack",
    vendor: "Salesforce",
    description:
      "Receive gate notifications and approve/reject gates via Slack messages. Requires OTT Gateway.",
    href: "#",
    requiredTier: "ENTERPRISE",
    status: "coming_soon" as const,
  },
  {
    id: "teams",
    name: "Microsoft Teams",
    vendor: "Microsoft",
    description:
      "Chat-based gate management via Adaptive Cards. Sprint 186+.",
    href: "#",
    requiredTier: "PROFESSIONAL",
    status: "coming_soon" as const,
  },
];

const TIER_COLORS: Record<string, string> = {
  STANDARD: "bg-gray-100 text-gray-700",
  PROFESSIONAL: "bg-blue-100 text-blue-700",
  ENTERPRISE: "bg-purple-100 text-purple-700",
};

export default function IntegrationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Integrations</h1>
        <p className="mt-1 text-sm text-gray-500">
          Connect SDLC Orchestrator to your existing toolchain. Tier gates are
          enforced at both the API and UI level (ADR-059).
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {integrations.map((integration) => (
          <div
            key={integration.id}
            className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <h3 className="text-base font-semibold text-gray-900">
                  {integration.name}
                </h3>
                <p className="text-xs text-gray-500">{integration.vendor}</p>
              </div>
              <div className="flex flex-col items-end gap-1">
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${TIER_COLORS[integration.requiredTier] ?? ""}`}
                >
                  {integration.requiredTier}+
                </span>
                {integration.status === "coming_soon" && (
                  <span className="text-xs text-gray-400">Coming soon</span>
                )}
              </div>
            </div>

            <p className="mt-2 text-sm text-gray-600">{integration.description}</p>

            {integration.status === "available" ? (
              <Link
                href={integration.href}
                className="mt-4 inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-500"
              >
                Configure →
              </Link>
            ) : (
              <p className="mt-4 text-xs text-gray-400">Sprint 186+</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
