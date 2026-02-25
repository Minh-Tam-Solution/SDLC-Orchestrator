/**
 * OTT Gateway hooks — TanStack Query hooks for OTT admin endpoints.
 *
 * Sprint 198 Track A: OTT Gateway Dashboard data fetching.
 * Sprint 199 C-01/C-02: Webhook log viewer + channel config panel hooks.
 * Endpoints: /api/v1/admin/ott-channels/{stats,config,{channel}/health,{channel}/conversations,{channel}/test-webhook}
 */

import { useMutation, useQuery } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchWithAuth<T>(path: string): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    credentials: "include",
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface ChannelStat {
  channel: string;
  status: "online" | "configured" | "offline";
  tier: string;
  conversations_total: number;
  conversations_active: number;
  messages_total: number;
  messages_last_24h: number;
}

export interface OttStats {
  channels: ChannelStat[];
  summary: {
    total_channels: number;
    online_channels: number;
    configured_channels: number;
    total_conversations: number;
    total_messages_24h: number;
  };
  dedupe: { hits: number; keys_active: number };
  generated_at: string;
}

export interface ChannelConfig {
  channel: string;
  status: string;
  tier: string;
  webhook_url: string;
  hmac_enabled: boolean;
  secret_configured: boolean;
  secret_masked: string | null;
  bot_token_configured?: boolean;
  bot_token_masked?: string | null;
  app_id_configured?: boolean;
  app_id_masked?: string | null;
}

export interface OttConfig {
  channels: ChannelConfig[];
  global: {
    hmac_enabled: boolean;
    webhook_base_url: string;
    dedupe_ttl_seconds: number;
  };
  generated_at: string;
}

export interface ChannelHealth {
  channel: string;
  status: string;
  tier: string;
  health: {
    last_webhook_at: string | null;
    messages_24h: number;
    errors_24h: number;
    avg_latency_ms: number | null;
  };
  conversations: Record<string, number>;
  checked_at: string;
}

export interface ConversationItem {
  id: string;
  initiator_id: string;
  status: string;
  total_messages: number;
  total_tokens: number;
  current_cost_cents: number;
  started_at: string;
  completed_at: string | null;
  last_message: {
    content: string | null;
    sender_type: string | null;
    created_at: string | null;
  } | null;
}

export interface ConversationsResponse {
  channel: string;
  items: ConversationItem[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    pages: number;
  };
}

// ── Query Keys ───────────────────────────────────────────────────────────────

export const ottKeys = {
  all: ["ott-gateway"] as const,
  stats: () => [...ottKeys.all, "stats"] as const,
  config: () => [...ottKeys.all, "config"] as const,
  health: (channel: string) => [...ottKeys.all, "health", channel] as const,
  conversations: (channel: string, page: number) =>
    [...ottKeys.all, "conversations", channel, page] as const,
};

// ── Hooks ────────────────────────────────────────────────────────────────────

export function useOttStats() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  return useQuery({
    queryKey: ottKeys.stats(),
    queryFn: () => fetchWithAuth<OttStats>("/admin/ott-channels/stats"),
    enabled: isAuthenticated && !authLoading,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Auto-refresh every 60s
  });
}

export function useOttConfig() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  return useQuery({
    queryKey: ottKeys.config(),
    queryFn: () => fetchWithAuth<OttConfig>("/admin/ott-channels/config"),
    enabled: isAuthenticated && !authLoading,
    staleTime: 5 * 60 * 1000, // 5 minutes (config rarely changes)
  });
}

export function useChannelHealth(channel: string) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  return useQuery({
    queryKey: ottKeys.health(channel),
    queryFn: () =>
      fetchWithAuth<ChannelHealth>(`/admin/ott-channels/${channel}/health`),
    enabled: isAuthenticated && !authLoading && !!channel,
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  });
}

export function useChannelConversations(channel: string, page: number = 1) {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  return useQuery({
    queryKey: ottKeys.conversations(channel, page),
    queryFn: () =>
      fetchWithAuth<ConversationsResponse>(
        `/admin/ott-channels/${channel}/conversations?page=${page}&page_size=20`,
      ),
    enabled: isAuthenticated && !authLoading && !!channel,
    staleTime: 30 * 1000,
  });
}

// ── Test Webhook (Sprint 199 C-03) ──────────────────────────────────────────

export interface TestWebhookResult {
  status: "ok" | "error";
  channel: string;
  message?: string;
  error?: string;
  normalization?: {
    sender_id: string;
    content_length: number;
    channel: string;
  };
  pipeline?: {
    hmac_enabled: boolean;
    channel_status: string;
  };
  timing_ms?: number;
}

async function postWithAuth<T>(path: string): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    credentials: "include",
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export function useTestWebhook() {
  return useMutation({
    mutationFn: (channel: string) =>
      postWithAuth<TestWebhookResult>(
        `/admin/ott-channels/${channel}/test-webhook`,
      ),
  });
}
