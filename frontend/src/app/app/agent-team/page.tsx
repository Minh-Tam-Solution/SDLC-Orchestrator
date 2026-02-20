/**
 * Multi-Agent Team Engine Page — SDLC Orchestrator
 *
 * @module frontend/src/app/app/agent-team/page
 * @description Entry point for the EP-07 Multi-Agent Team Engine feature.
 *   Requires PROFESSIONAL+ subscription (ADR-056, ADR-059).
 *   LITE/STANDARD users see LockedFeature overlay with upgrade CTA.
 * @sdlc SDLC 6.1.0 — Sprint 185 (F-07: PROFESSIONAL tier gate wired)
 */

"use client";

import { LockedFeature } from "@/components/tier-gate/LockedFeature";
import { useUserTier } from "@/hooks/useUserTier";

function AgentTeamContent() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">
          Multi-Agent Team Engine
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Orchestrate teams of AI agents (Initializer → Coder → Reviewer) with lane-based
          concurrency, provider failover, and budget controls. Powered by EP-07 (ADR-056).
        </p>
      </div>

      {/* Status cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-gray-500">Active Conversations</p>
          <p className="mt-1 text-3xl font-bold text-gray-900">—</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-gray-500">Agent Definitions</p>
          <p className="mt-1 text-3xl font-bold text-gray-900">—</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-gray-500">Messages Processed</p>
          <p className="mt-1 text-3xl font-bold text-gray-900">—</p>
        </div>
      </div>

      {/* Coming soon notice */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-6">
        <h3 className="text-base font-semibold text-blue-900">
          Full Dashboard Coming in Sprint 186
        </h3>
        <p className="mt-1 text-sm text-blue-700">
          The Multi-Agent Team Engine API is live at{" "}
          <code className="rounded bg-blue-100 px-1 py-0.5 text-xs">/api/v1/agent-team</code>.
          The full web dashboard (conversation viewer, agent builder, message queue inspector)
          is being built in Sprint 186.
        </p>
        <ul className="mt-3 space-y-1 text-sm text-blue-700 list-disc list-inside">
          <li>Create agent definitions via API or CLI</li>
          <li>Lane-based concurrency with SKIP LOCKED + Redis pub/sub</li>
          <li>6-reason provider failover (auth, rate-limit, billing, timeout, format, unknown)</li>
          <li>Budget circuit breaker + delegation depth limits (Nanobot N2)</li>
        </ul>
      </div>
    </div>
  );
}

export default function AgentTeamPage() {
  // F-07 (Sprint 185): PROFESSIONAL tier gate — agent-team is a PROFESSIONAL+ feature
  // ADR-059 Decision 1: /api/v1/agent-team → tier 3 (PROFESSIONAL)
  const { effectiveTier, isLoading } = useUserTier();
  const currentTier = isLoading ? "LITE" : effectiveTier;

  return (
    <LockedFeature
      requiredTier="PROFESSIONAL"
      currentTier={currentTier}
      featureLabel="Multi-Agent Team Engine"
    >
      <AgentTeamContent />
    </LockedFeature>
  );
}
