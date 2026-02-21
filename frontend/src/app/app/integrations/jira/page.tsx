/**
 * Jira Integration Page — SDLC Orchestrator
 *
 * @module frontend/src/app/app/integrations/jira/page
 * @description Connect Jira Cloud workspace and sync sprint issues to the
 *   Evidence Vault. Requires PROFESSIONAL+ subscription (ADR-059).
 *   LITE/STANDARD users see LockedFeature overlay with upgrade CTA.
 * @sdlc SDLC 6.1.0 — Sprint 185 (F-07: PROFESSIONAL tier gate wired)
 */

"use client";

import { useState } from "react";
import { LockedFeature } from "@/components/tier-gate/LockedFeature";
import { useUserTier } from "@/hooks/useUserTier";

function JiraIntegrationContent() {
  const [connecting, setConnecting] = useState(false);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Jira Integration</h1>
        <p className="mt-1 text-sm text-gray-500">
          Connect your Jira Cloud workspace to automatically sync sprint issues
          into the Evidence Vault as GateEvidence records. Powered by Sprint 184 (ADR-059).
        </p>
      </div>

      {/* Connect panel */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold text-gray-900">Connect Jira Workspace</h3>
        <p className="mt-1 text-sm text-gray-500">
          Your Jira API token is encrypted at-rest using Fernet AES-128-CBC (F-03 fix, Sprint 185).
          Credentials are verified against{" "}
          <code className="rounded bg-gray-100 px-1 py-0.5 text-xs">/rest/api/3/myself</code>{" "}
          before saving.
        </p>

        <form
          className="mt-4 space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            setConnecting(true);
            // Integration via POST /api/v1/jira/connect
            // Full form implementation in Sprint 186
            setTimeout(() => setConnecting(false), 1000);
          }}
        >
          <div>
            <label
              htmlFor="jira-url"
              className="block text-sm font-medium text-gray-700"
            >
              Jira Cloud URL
            </label>
            <input
              id="jira-url"
              type="url"
              placeholder="https://your-workspace.atlassian.net"
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
                         shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label
              htmlFor="jira-email"
              className="block text-sm font-medium text-gray-700"
            >
              Atlassian Account Email
            </label>
            <input
              id="jira-email"
              type="email"
              placeholder="you@company.com"
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
                         shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label
              htmlFor="jira-token"
              className="block text-sm font-medium text-gray-700"
            >
              API Token
            </label>
            <input
              id="jira-token"
              type="password"
              placeholder="Jira API token from id.atlassian.com"
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
                         shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Generate at{" "}
              <span className="font-medium text-blue-600">
                id.atlassian.com → Security → API tokens
              </span>
            </p>
          </div>

          <button
            type="submit"
            disabled={connecting}
            className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm
                       font-semibold text-white shadow-sm hover:bg-blue-500 disabled:opacity-60
                       focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2
                       focus-visible:outline-blue-600"
          >
            {connecting ? "Connecting…" : "Connect Jira"}
          </button>
        </form>
      </div>

      {/* Sync panel */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold text-gray-900">Sprint Sync</h3>
        <p className="mt-1 text-sm text-gray-500">
          Sync Jira sprint issues to the Evidence Vault as GateEvidence records
          (source=&quot;jira&quot;). Idempotent — re-running updates existing evidence descriptions.
        </p>
        <p className="mt-3 text-xs text-gray-400">
          Connect a workspace first, then sprint sync will appear here.
        </p>
      </div>
    </div>
  );
}

export default function JiraIntegrationPage() {
  // F-07 (Sprint 185): PROFESSIONAL tier gate — Jira integration is a PROFESSIONAL+ feature
  // ADR-059 Decision 1: /api/v1/jira → tier 3 (PROFESSIONAL)
  const { effectiveTier, isLoading } = useUserTier();
  const currentTier = isLoading ? "LITE" : effectiveTier;

  return (
    <LockedFeature
      requiredTier="PROFESSIONAL"
      currentTier={currentTier}
      featureLabel="Jira Integration"
    >
      <JiraIntegrationContent />
    </LockedFeature>
  );
}
