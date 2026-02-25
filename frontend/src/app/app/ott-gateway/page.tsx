/**
 * OTT Gateway Dashboard — Sprint 198 Track A + Sprint 199 C-01/C-02
 *
 * Admin-only monitoring page for OTT channels (Telegram, Zalo, Teams, Slack).
 * Displays channel status cards, health metrics, conversation feed,
 * webhook log viewer (C-01), and channel config panel with test-webhook (C-02).
 *
 * Design reference: OpenClaw Gateway UI — adapted for Next.js + shadcn/ui.
 * CEO directive Sprint 190: Conversation-First — this is an admin monitoring tool.
 */

"use client";

import { useState } from "react";
import {
  useOttStats,
  useChannelHealth,
  useChannelConversations,
  type ChannelStat,
  type ConversationItem,
} from "@/hooks/useOttGateway";
import { WebhookLogViewer, ChannelConfigPanel, AgentActivityPanel } from "@/components/ott-gateway";

// ── Status Styling ───────────────────────────────────────────────────────────

const STATUS_COLORS: Record<string, string> = {
  online: "bg-green-100 text-green-800",
  configured: "bg-yellow-100 text-yellow-800",
  offline: "bg-gray-100 text-gray-600",
};

const STATUS_DOT: Record<string, string> = {
  online: "bg-green-500",
  configured: "bg-yellow-500",
  offline: "bg-gray-400",
};

// ── Icons ────────────────────────────────────────────────────────────────────

function TelegramIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
    </svg>
  );
}

function ChatBubbleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z" />
    </svg>
  );
}

function SignalIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.348 14.652a3.75 3.75 0 0 1 0-5.304m5.304 0a3.75 3.75 0 0 1 0 5.304m-7.425 2.121a6.75 6.75 0 0 1 0-9.546m9.546 0a6.75 6.75 0 0 1 0 9.546M5.106 18.894c-3.808-3.807-3.808-9.98 0-13.788m13.788 0c3.808 3.807 3.808 9.98 0 13.788M12 12h.008v.008H12V12Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
    </svg>
  );
}

function RefreshIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182" />
    </svg>
  );
}

// ── Channel Icon Map ─────────────────────────────────────────────────────────

const CHANNEL_ICONS: Record<string, typeof TelegramIcon> = {
  telegram: TelegramIcon,
  zalo: ChatBubbleIcon,
  teams: ChatBubbleIcon,
  slack: ChatBubbleIcon,
};

const CHANNEL_LABELS: Record<string, string> = {
  telegram: "Telegram",
  zalo: "Zalo OA",
  teams: "MS Teams",
  slack: "Slack",
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(dateString: string | null): string {
  if (!dateString) return "Never";
  const d = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHrs = Math.floor(diffMin / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  return d.toLocaleDateString();
}

// ── Channel Status Card ──────────────────────────────────────────────────────

function ChannelStatusCard({
  stat,
  isSelected,
  onClick,
}: {
  stat: ChannelStat;
  isSelected: boolean;
  onClick: () => void;
}) {
  const Icon = CHANNEL_ICONS[stat.channel] || ChatBubbleIcon;
  const label = CHANNEL_LABELS[stat.channel] || stat.channel;

  return (
    <button
      onClick={onClick}
      className={`rounded-lg border p-4 text-left transition-all hover:shadow-md ${
        isSelected
          ? "border-blue-500 bg-blue-50 ring-2 ring-blue-200"
          : "border-gray-200 bg-white hover:border-gray-300"
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-5 w-5 text-gray-600" />
          <span className="font-medium text-gray-900">{label}</span>
        </div>
        <span
          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
            STATUS_COLORS[stat.status] || STATUS_COLORS.offline
          }`}
        >
          <span
            className={`inline-block h-1.5 w-1.5 rounded-full ${
              STATUS_DOT[stat.status] || STATUS_DOT.offline
            }`}
          />
          {stat.status}
        </span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-sm text-gray-500">
        <div>
          <span className="text-lg font-semibold text-gray-900">
            {stat.messages_total}
          </span>
          <span className="ml-1">msgs</span>
        </div>
        <div>
          <span className="text-lg font-semibold text-gray-900">
            {stat.conversations_active}
          </span>
          <span className="ml-1">active</span>
        </div>
      </div>
      <div className="mt-1 text-xs text-gray-400">
        {stat.messages_last_24h} messages in last 24h | Tier: {stat.tier}
      </div>
    </button>
  );
}

// ── Conversation Feed ────────────────────────────────────────────────────────

function ConversationFeed({
  channel,
  page,
  onPageChange,
}: {
  channel: string;
  page: number;
  onPageChange: (p: number) => void;
}) {
  const { data, isLoading, error } = useChannelConversations(channel, page);

  if (isLoading) {
    return (
      <div className="flex h-48 items-center justify-center text-gray-400">
        Loading conversations...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-48 items-center justify-center text-red-500">
        Error loading conversations: {(error as Error).message}
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-gray-400">
        No conversations for {CHANNEL_LABELS[channel] || channel}
      </div>
    );
  }

  return (
    <div>
      <div className="divide-y divide-gray-100">
        {data.items.map((conv: ConversationItem) => (
          <div key={conv.id} className="flex items-start gap-3 px-4 py-3 hover:bg-gray-50">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-xs font-medium text-blue-700">
              {conv.initiator_id.slice(0, 2).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-900">
                  {conv.initiator_id}
                </span>
                <span
                  className={`rounded-full px-1.5 py-0.5 text-xs ${
                    conv.status === "active"
                      ? "bg-green-100 text-green-700"
                      : conv.status === "completed"
                        ? "bg-gray-100 text-gray-600"
                        : "bg-red-100 text-red-700"
                  }`}
                >
                  {conv.status}
                </span>
              </div>
              {conv.last_message?.content && (
                <p className="mt-0.5 truncate text-sm text-gray-500">
                  {conv.last_message.content}
                </p>
              )}
              <div className="mt-1 flex gap-3 text-xs text-gray-400">
                <span>{conv.total_messages} msgs</span>
                <span>{conv.total_tokens} tokens</span>
                <span>{formatDate(conv.started_at)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {data.pagination.pages > 1 && (
        <div className="flex items-center justify-between border-t border-gray-100 px-4 py-3">
          <span className="text-sm text-gray-500">
            Page {data.pagination.page} of {data.pagination.pages} ({data.pagination.total} total)
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="rounded border px-3 py-1 text-sm disabled:opacity-50"
            >
              Prev
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= data.pagination.pages}
              className="rounded border px-3 py-1 text-sm disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Channel Health Panel ─────────────────────────────────────────────────────

function ChannelHealthPanel({ channel }: { channel: string }) {
  const { data, isLoading } = useChannelHealth(channel);

  if (isLoading || !data) {
    return <div className="p-4 text-gray-400">Loading health data...</div>;
  }

  return (
    <div className="space-y-4 p-4">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-lg bg-gray-50 p-3">
          <div className="text-xs text-gray-500">Messages (24h)</div>
          <div className="text-xl font-semibold">{data.health.messages_24h}</div>
        </div>
        <div className="rounded-lg bg-gray-50 p-3">
          <div className="text-xs text-gray-500">Errors (24h)</div>
          <div className={`text-xl font-semibold ${data.health.errors_24h > 0 ? "text-red-600" : ""}`}>
            {data.health.errors_24h}
          </div>
        </div>
        <div className="rounded-lg bg-gray-50 p-3">
          <div className="text-xs text-gray-500">Avg Latency</div>
          <div className="text-xl font-semibold">
            {data.health.avg_latency_ms != null
              ? `${data.health.avg_latency_ms}ms`
              : "N/A"}
          </div>
        </div>
        <div className="rounded-lg bg-gray-50 p-3">
          <div className="text-xs text-gray-500">Last Webhook</div>
          <div className="text-sm font-medium">
            {formatDate(data.health.last_webhook_at)}
          </div>
        </div>
      </div>

      {/* Conversation status breakdown */}
      {Object.keys(data.conversations).length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-medium text-gray-700">
            Conversation Status
          </h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(data.conversations).map(([s, count]) => (
              <span
                key={s}
                className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600"
              >
                {s}: {count}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Dashboard Page ──────────────────────────────────────────────────────

export default function OttGatewayPage() {
  const [selectedChannel, setSelectedChannel] = useState<string>("telegram");
  const [activeTab, setActiveTab] = useState<"conversations" | "agents" | "webhook-log" | "health" | "config">("conversations");
  const [convPage, setConvPage] = useState(1);
  const { data: stats, isLoading, error, refetch } = useOttStats();

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-gray-400">Loading OTT Gateway Dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6">
        <h2 className="text-lg font-semibold text-red-800">
          OTT Gateway Dashboard Error
        </h2>
        <p className="mt-2 text-sm text-red-600">
          {(error as Error).message}
        </p>
        <p className="mt-1 text-xs text-red-500">
          This page requires admin access (is_superuser or is_platform_admin).
        </p>
      </div>
    );
  }

  const tabs = [
    { key: "conversations" as const, label: "Conversations" },
    { key: "agents" as const, label: "Agents" },
    { key: "webhook-log" as const, label: "Webhook Log" },
    { key: "health" as const, label: "Health" },
    { key: "config" as const, label: "Config" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">OTT Gateway</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor OTT channels, conversations, and webhook health
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <RefreshIcon className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Summary bar */}
      {stats && (
        <div className="flex gap-6 rounded-lg bg-white p-4 shadow-sm ring-1 ring-gray-100">
          <div>
            <span className="text-sm text-gray-500">Channels</span>
            <span className="ml-2 text-lg font-semibold">
              {stats.summary.online_channels}/{stats.summary.total_channels} online
            </span>
          </div>
          <div className="border-l pl-6">
            <span className="text-sm text-gray-500">Conversations</span>
            <span className="ml-2 text-lg font-semibold">
              {stats.summary.total_conversations}
            </span>
          </div>
          <div className="border-l pl-6">
            <span className="text-sm text-gray-500">Messages (24h)</span>
            <span className="ml-2 text-lg font-semibold">
              {stats.summary.total_messages_24h}
            </span>
          </div>
          <div className="border-l pl-6">
            <span className="text-sm text-gray-500">Dedupe Keys</span>
            <span className="ml-2 text-lg font-semibold">
              {stats.dedupe.keys_active}
            </span>
          </div>
        </div>
      )}

      {/* Channel cards grid */}
      {stats && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stats.channels.map((stat) => (
            <ChannelStatusCard
              key={stat.channel}
              stat={stat}
              isSelected={selectedChannel === stat.channel}
              onClick={() => {
                setSelectedChannel(stat.channel);
                setConvPage(1);
              }}
            />
          ))}
        </div>
      )}

      {/* Detail panel with tabs */}
      <div className="overflow-hidden rounded-lg bg-white shadow-sm ring-1 ring-gray-100">
        {/* Tab bar */}
        <div className="flex border-b border-gray-200">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "border-b-2 border-blue-500 text-blue-600"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
          <div className="ml-auto flex items-center px-4 text-sm text-gray-400">
            {CHANNEL_LABELS[selectedChannel] || selectedChannel}
          </div>
        </div>

        {/* Tab content */}
        {activeTab === "conversations" && (
          <ConversationFeed
            channel={selectedChannel}
            page={convPage}
            onPageChange={setConvPage}
          />
        )}
        {activeTab === "agents" && (
          <AgentActivityPanel />
        )}
        {activeTab === "webhook-log" && (
          <WebhookLogViewer channel={selectedChannel} />
        )}
        {activeTab === "health" && (
          <ChannelHealthPanel channel={selectedChannel} />
        )}
        {activeTab === "config" && (
          <ChannelConfigPanel channel={selectedChannel} />
        )}
      </div>
    </div>
  );
}
