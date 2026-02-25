/**
 * WebhookLogViewer — Sprint 199 C-01 (deferred from Sprint 198 A-09).
 *
 * Log-style view of recent webhook activity for a selected OTT channel.
 * Uses conversation + health data as a proxy for webhook events since
 * conversations are 1:1 with inbound webhook messages.
 */

"use client";

import { useState } from "react";
import {
  useChannelConversations,
  useChannelHealth,
  type ConversationItem,
} from "@/hooks/useOttGateway";

// ── Status badge colours ────────────────────────────────────────────────────

const CONV_STATUS: Record<string, string> = {
  active: "bg-green-100 text-green-700",
  completed: "bg-gray-100 text-gray-600",
  error: "bg-red-100 text-red-700",
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function relativeTime(dateString: string | null): string {
  if (!dateString) return "—";
  const d = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHrs = Math.floor(diffMin / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  return d.toLocaleString();
}

function truncate(text: string | null | undefined, max: number): string {
  if (!text) return "—";
  return text.length > max ? text.slice(0, max) + "..." : text;
}

// ── Log Entry Row ───────────────────────────────────────────────────────────

function LogEntry({ conv }: { conv: ConversationItem }) {
  return (
    <div className="flex items-start gap-3 border-b border-gray-50 px-4 py-2.5 font-mono text-xs hover:bg-gray-50">
      {/* Timestamp */}
      <span className="w-24 shrink-0 text-gray-400">
        {relativeTime(conv.started_at)}
      </span>

      {/* Status indicator */}
      <span
        className={`inline-flex w-20 shrink-0 items-center justify-center rounded-full px-2 py-0.5 text-[10px] font-medium ${
          CONV_STATUS[conv.status] || CONV_STATUS.error
        }`}
      >
        {conv.status}
      </span>

      {/* Sender */}
      <span className="w-28 shrink-0 truncate text-blue-600">
        {conv.initiator_id}
      </span>

      {/* Message preview */}
      <span className="min-w-0 flex-1 text-gray-600">
        {truncate(conv.last_message?.content, 100)}
      </span>

      {/* Metrics */}
      <span className="w-16 shrink-0 text-right text-gray-400">
        {conv.total_messages} msg
      </span>
      <span className="w-20 shrink-0 text-right text-gray-400">
        {conv.total_tokens} tok
      </span>
    </div>
  );
}

// ── Health Summary Bar ──────────────────────────────────────────────────────

function HealthSummary({ channel }: { channel: string }) {
  const { data } = useChannelHealth(channel);
  if (!data) return null;

  const errorRate =
    data.health.messages_24h > 0
      ? ((data.health.errors_24h / data.health.messages_24h) * 100).toFixed(1)
      : "0.0";

  return (
    <div className="flex items-center gap-6 border-b border-gray-100 bg-gray-50 px-4 py-2 text-xs text-gray-500">
      <span>
        <strong className="text-gray-700">{data.health.messages_24h}</strong>{" "}
        webhooks (24h)
      </span>
      <span>
        <strong
          className={
            data.health.errors_24h > 0 ? "text-red-600" : "text-gray-700"
          }
        >
          {data.health.errors_24h}
        </strong>{" "}
        errors ({errorRate}%)
      </span>
      <span>
        Avg latency:{" "}
        <strong className="text-gray-700">
          {data.health.avg_latency_ms != null
            ? `${data.health.avg_latency_ms}ms`
            : "N/A"}
        </strong>
      </span>
      <span>
        Last webhook:{" "}
        <strong className="text-gray-700">
          {relativeTime(data.health.last_webhook_at)}
        </strong>
      </span>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────────

export default function WebhookLogViewer({ channel }: { channel: string }) {
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = useChannelConversations(channel, page);

  return (
    <div className="flex flex-col">
      {/* Health summary bar */}
      <HealthSummary channel={channel} />

      {/* Column headers */}
      <div className="flex items-center gap-3 border-b border-gray-200 bg-gray-50 px-4 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
        <span className="w-24 shrink-0">Time</span>
        <span className="w-20 shrink-0 text-center">Status</span>
        <span className="w-28 shrink-0">Sender</span>
        <span className="min-w-0 flex-1">Message</span>
        <span className="w-16 shrink-0 text-right">Msgs</span>
        <span className="w-20 shrink-0 text-right">Tokens</span>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex h-48 items-center justify-center text-sm text-gray-400">
          Loading webhook log...
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="flex h-48 items-center justify-center text-sm text-red-500">
          Error: {(error as Error).message}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && (!data || data.items.length === 0) && (
        <div className="flex h-48 items-center justify-center text-sm text-gray-400">
          No webhook activity for this channel
        </div>
      )}

      {/* Log entries */}
      {data?.items.map((conv) => <LogEntry key={conv.id} conv={conv} />)}

      {/* Pagination */}
      {data && data.pagination.pages > 1 && (
        <div className="flex items-center justify-between border-t border-gray-100 px-4 py-2">
          <span className="text-xs text-gray-500">
            Page {data.pagination.page} of {data.pagination.pages} (
            {data.pagination.total} events)
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="rounded border px-2.5 py-1 text-xs disabled:opacity-50"
            >
              Prev
            </button>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= data.pagination.pages}
              className="rounded border px-2.5 py-1 text-xs disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
