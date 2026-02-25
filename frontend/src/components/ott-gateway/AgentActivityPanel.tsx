/**
 * AgentActivityPanel — Sprint 200 B-05
 *
 * Real-time panel showing active agent conversations, token usage,
 * and cost attribution per provider. Displayed as a tab on the
 * OTT Gateway Dashboard.
 *
 * Data source: GET /api/v1/ott/gateway/agent-activity
 * CEO directive Sprint 190: Admin monitoring tool.
 */

"use client";

import { useQuery } from "@tanstack/react-query";

// ── Types ───────────────────────────────────────────────────────────────────

interface AgentConversationSummary {
  id: string;
  agent_name: string;
  sdlc_role: string;
  status: string;
  total_messages: number;
  total_tokens: number;
  current_cost_cents: number;
  max_budget_cents: number;
  provider: string;
  channel: string;
  started_at: string;
  initiator_id: string;
}

interface CostByProvider {
  provider: string;
  total_cents: number;
  total_tokens: number;
  invocations: number;
}

interface AgentActivityData {
  active_conversations: AgentConversationSummary[];
  cost_by_provider: CostByProvider[];
  summary: {
    total_active: number;
    total_tokens_24h: number;
    total_cost_cents_24h: number;
    budget_warnings: number;
  };
}

// ── API Hook ────────────────────────────────────────────────────────────────

function useAgentActivity() {
  return useQuery<AgentActivityData>({
    queryKey: ["ott", "agent-activity"],
    queryFn: async () => {
      const res = await fetch("/api/v1/ott/gateway/agent-activity", {
        credentials: "include",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      return res.json();
    },
    refetchInterval: 10_000, // Refresh every 10s for real-time feel
  });
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function formatCost(cents: number): string {
  if (cents === 0) return "$0.00";
  return `$${(cents / 100).toFixed(2)}`;
}

function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`;
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}K`;
  return String(tokens);
}

function budgetPercentage(current: number, max: number): number {
  if (max <= 0) return 0;
  return Math.min(100, Math.round((current / max) * 100));
}

function budgetColor(pct: number): string {
  if (pct >= 100) return "bg-red-500";
  if (pct >= 80) return "bg-yellow-500";
  return "bg-green-500";
}

function budgetTextColor(pct: number): string {
  if (pct >= 100) return "text-red-700";
  if (pct >= 80) return "text-yellow-700";
  return "text-green-700";
}

function statusBadge(status: string): string {
  switch (status) {
    case "active":
      return "bg-green-100 text-green-700";
    case "completed":
      return "bg-gray-100 text-gray-600";
    case "max_reached":
      return "bg-red-100 text-red-700";
    case "paused_by_human":
      return "bg-yellow-100 text-yellow-700";
    default:
      return "bg-gray-100 text-gray-600";
  }
}

function timeAgo(dateString: string): string {
  const d = new Date(dateString);
  const now = new Date();
  const diffMin = Math.floor((now.getTime() - d.getTime()) / 60000);
  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHrs = Math.floor(diffMin / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  return d.toLocaleDateString();
}

// ── Component ───────────────────────────────────────────────────────────────

export default function AgentActivityPanel() {
  const { data, isLoading, error } = useAgentActivity();

  if (isLoading) {
    return (
      <div className="flex h-48 items-center justify-center text-gray-400">
        Loading agent activity...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-48 items-center justify-center text-red-500">
        Error: {(error as Error).message}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-48 items-center justify-center text-gray-400">
        No agent activity data
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4">
      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-lg bg-blue-50 p-3">
          <div className="text-xs text-blue-600">Active Conversations</div>
          <div className="text-2xl font-bold text-blue-900">
            {data.summary.total_active}
          </div>
        </div>
        <div className="rounded-lg bg-purple-50 p-3">
          <div className="text-xs text-purple-600">Tokens (24h)</div>
          <div className="text-2xl font-bold text-purple-900">
            {formatTokens(data.summary.total_tokens_24h)}
          </div>
        </div>
        <div className="rounded-lg bg-green-50 p-3">
          <div className="text-xs text-green-600">Cost (24h)</div>
          <div className="text-2xl font-bold text-green-900">
            {formatCost(data.summary.total_cost_cents_24h)}
          </div>
        </div>
        <div className="rounded-lg bg-yellow-50 p-3">
          <div className="text-xs text-yellow-600">Budget Warnings</div>
          <div className={`text-2xl font-bold ${data.summary.budget_warnings > 0 ? "text-yellow-700" : "text-yellow-900"}`}>
            {data.summary.budget_warnings}
          </div>
        </div>
      </div>

      {/* Cost by provider (B-06) */}
      {data.cost_by_provider.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-medium text-gray-700">
            Cost Attribution by Provider
          </h4>
          <div className="overflow-hidden rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">
                    Provider
                  </th>
                  <th className="px-4 py-2 text-right font-medium text-gray-600">
                    Cost
                  </th>
                  <th className="px-4 py-2 text-right font-medium text-gray-600">
                    Tokens
                  </th>
                  <th className="px-4 py-2 text-right font-medium text-gray-600">
                    Calls
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.cost_by_provider.map((p) => (
                  <tr key={p.provider}>
                    <td className="px-4 py-2 font-medium text-gray-900">
                      {p.provider}
                    </td>
                    <td className="px-4 py-2 text-right text-gray-700">
                      {formatCost(p.total_cents)}
                    </td>
                    <td className="px-4 py-2 text-right text-gray-700">
                      {formatTokens(p.total_tokens)}
                    </td>
                    <td className="px-4 py-2 text-right text-gray-700">
                      {p.invocations}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Active conversations list */}
      <div>
        <h4 className="mb-2 text-sm font-medium text-gray-700">
          Active Agent Conversations ({data.active_conversations.length})
        </h4>
        {data.active_conversations.length === 0 ? (
          <div className="rounded-lg bg-gray-50 p-6 text-center text-sm text-gray-400">
            No active agent conversations
          </div>
        ) : (
          <div className="divide-y divide-gray-100 rounded-lg border border-gray-200">
            {data.active_conversations.map((conv) => {
              const pct = budgetPercentage(
                conv.current_cost_cents,
                conv.max_budget_cents,
              );
              return (
                <div key={conv.id} className="flex items-center gap-4 px-4 py-3">
                  {/* Agent info */}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900">
                        {conv.agent_name}
                      </span>
                      <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700">
                        {conv.sdlc_role}
                      </span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs ${statusBadge(conv.status)}`}
                      >
                        {conv.status}
                      </span>
                    </div>
                    <div className="mt-1 flex gap-3 text-xs text-gray-400">
                      <span>{conv.total_messages} msgs</span>
                      <span>{formatTokens(conv.total_tokens)} tokens</span>
                      <span>{formatCost(conv.current_cost_cents)}</span>
                      <span>{conv.provider}</span>
                      <span>{timeAgo(conv.started_at)}</span>
                    </div>
                  </div>

                  {/* Budget bar */}
                  <div className="w-32 shrink-0">
                    <div className="flex items-center justify-between text-xs">
                      <span className={budgetTextColor(pct)}>{pct}%</span>
                      <span className="text-gray-400">
                        {formatCost(conv.max_budget_cents)}
                      </span>
                    </div>
                    <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-gray-200">
                      <div
                        className={`h-full rounded-full transition-all ${budgetColor(pct)}`}
                        style={{ width: `${Math.min(pct, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
