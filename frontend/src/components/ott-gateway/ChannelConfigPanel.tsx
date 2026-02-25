/**
 * ChannelConfigPanel — Sprint 199 C-02 (deferred from Sprint 198 A-10).
 *
 * Displays channel configuration details (webhook URL, HMAC, secrets, tier)
 * and provides a "Test Webhook" button that fires a synthetic payload through
 * the normalizer pipeline (C-03 backend endpoint).
 *
 * Extracted from inline ChannelConfigPanel in page.tsx and enhanced.
 */

"use client";

import { useState } from "react";
import {
  useOttConfig,
  useTestWebhook,
  type TestWebhookResult,
} from "@/hooks/useOttGateway";

// ── Config Row ──────────────────────────────────────────────────────────────

function ConfigRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex justify-between rounded bg-gray-50 p-2 text-sm">
      <span className="text-gray-500">{label}</span>
      <span>{children}</span>
    </div>
  );
}

// ── Test Result Display ─────────────────────────────────────────────────────

function TestResultBanner({ result }: { result: TestWebhookResult }) {
  const isOk = result.status === "ok";
  return (
    <div
      className={`rounded-lg border p-3 text-sm ${
        isOk
          ? "border-green-200 bg-green-50 text-green-800"
          : "border-red-200 bg-red-50 text-red-800"
      }`}
    >
      <div className="flex items-center gap-2 font-medium">
        <span>{isOk ? "\u2713" : "\u2717"}</span>
        <span>
          {isOk ? "Pipeline test passed" : "Pipeline test failed"}
        </span>
        {result.timing_ms != null && (
          <span className="ml-auto text-xs font-normal opacity-70">
            {result.timing_ms}ms
          </span>
        )}
      </div>
      {isOk && result.normalization && (
        <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
          <span className="text-green-600">Sender ID</span>
          <span className="font-mono">{result.normalization.sender_id}</span>
          <span className="text-green-600">Content Length</span>
          <span>{result.normalization.content_length} chars</span>
          <span className="text-green-600">Channel</span>
          <span>{result.normalization.channel}</span>
        </div>
      )}
      {!isOk && result.error && (
        <p className="mt-1 text-xs">{result.error}</p>
      )}
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────────

export default function ChannelConfigPanel({
  channel,
}: {
  channel: string;
}) {
  const { data, isLoading } = useOttConfig();
  const testWebhook = useTestWebhook();
  const [lastResult, setLastResult] = useState<TestWebhookResult | null>(null);

  if (isLoading || !data) {
    return <div className="p-4 text-gray-400">Loading config...</div>;
  }

  const config = data.channels.find((c) => c.channel === channel);
  if (!config) {
    return <div className="p-4 text-gray-400">No config for {channel}</div>;
  }

  function handleTestWebhook() {
    setLastResult(null);
    testWebhook.mutate(channel, {
      onSuccess: (res) => setLastResult(res),
      onError: (err) =>
        setLastResult({
          status: "error",
          channel,
          error: (err as Error).message,
        }),
    });
  }

  return (
    <div className="space-y-4 p-4">
      {/* Config details */}
      <div className="grid gap-3">
        <ConfigRow label="Webhook URL">
          <code className="text-xs text-gray-700">{config.webhook_url}</code>
        </ConfigRow>
        <ConfigRow label="HMAC Enabled">
          <span
            className={
              config.hmac_enabled ? "text-green-600" : "text-yellow-600"
            }
          >
            {config.hmac_enabled ? "Yes" : "No (dev mode)"}
          </span>
        </ConfigRow>
        <ConfigRow label="Secret">
          {config.secret_configured ? (
            <code className="text-xs text-gray-600">
              {config.secret_masked}
            </code>
          ) : (
            <span className="text-red-500">Not configured</span>
          )}
        </ConfigRow>
        {config.bot_token_configured !== undefined && (
          <ConfigRow label="Bot Token">
            {config.bot_token_configured ? (
              <code className="text-xs text-gray-600">
                {config.bot_token_masked}
              </code>
            ) : (
              <span className="text-red-500">Not configured</span>
            )}
          </ConfigRow>
        )}
        {config.app_id_configured !== undefined && (
          <ConfigRow label="App ID">
            {config.app_id_configured ? (
              <code className="text-xs text-gray-600">
                {config.app_id_masked}
              </code>
            ) : (
              <span className="text-red-500">Not configured</span>
            )}
          </ConfigRow>
        )}
        <ConfigRow label="Tier Requirement">
          <span className="font-medium">{config.tier}</span>
        </ConfigRow>
        <ConfigRow label="Status">
          <span className="font-medium">{config.status}</span>
        </ConfigRow>
      </div>

      {/* Global config */}
      <div>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
          Global Settings
        </h4>
        <div className="grid gap-2">
          <ConfigRow label="Webhook Base URL">
            <code className="text-xs text-gray-700">
              {data.global.webhook_base_url}
            </code>
          </ConfigRow>
          <ConfigRow label="Dedupe TTL">
            <span>{data.global.dedupe_ttl_seconds}s</span>
          </ConfigRow>
        </div>
      </div>

      {/* Test Webhook button */}
      <div className="border-t border-gray-100 pt-4">
        <button
          onClick={handleTestWebhook}
          disabled={testWebhook.isPending}
          className="inline-flex items-center gap-2 rounded-lg border border-blue-300 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 hover:bg-blue-100 disabled:opacity-50"
        >
          {testWebhook.isPending ? (
            <>
              <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
              Testing...
            </>
          ) : (
            <>
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z"
                />
              </svg>
              Test Webhook Pipeline
            </>
          )}
        </button>
        <p className="mt-1 text-xs text-gray-400">
          Sends a synthetic payload through the normalizer pipeline for{" "}
          {channel}.
        </p>
      </div>

      {/* Test result */}
      {lastResult && <TestResultBanner result={lastResult} />}
    </div>
  );
}
