/**
 * UsageWidget — Sprint 212 Track F
 *
 * Displays current resource usage vs tier limits as 4 progress bars.
 * Color coding: green (<60%), yellow (60-80%), red (>80%).
 * Shows "Upgrade" CTA when approaching limits.
 *
 * @module frontend/src/components/dashboard/UsageWidget
 * @sprint 212
 */

"use client";

import { useEffect, useState } from "react";

interface UsageBucket {
  current: number;
  limit: number;
  percent: number;
}

interface UsageStats {
  tier: string;
  usage: {
    projects: UsageBucket;
    storage_mb: UsageBucket;
    gates_this_month: UsageBucket;
    members: UsageBucket;
  };
}

function barColor(percent: number): string {
  if (percent >= 80) return "bg-red-500";
  if (percent >= 60) return "bg-yellow-500";
  return "bg-green-500";
}

function ProgressRow({ label, bucket }: { label: string; bucket: UsageBucket }) {
  const pct = Math.min(bucket.percent, 100);
  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-700">{label}</span>
        <span className="font-medium text-gray-900">
          {label === "Storage" ? `${bucket.current.toFixed(1)} / ${bucket.limit} MB` : `${bucket.current} / ${bucket.limit}`}
        </span>
      </div>
      <div className="mt-1 h-2 w-full rounded-full bg-gray-200">
        <div
          className={`h-2 rounded-full transition-all ${barColor(pct)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function UsageWidget() {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    fetch(`${apiUrl}/usage/stats`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { if (data) setStats(data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 animate-pulse">
        <div className="h-4 w-32 rounded bg-gray-200 mb-4" />
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="space-y-1">
              <div className="h-3 w-24 rounded bg-gray-200" />
              <div className="h-2 w-full rounded bg-gray-200" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!stats) return null;

  const showUpgrade = Object.values(stats.usage).some((b) => b.percent >= 80);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900">
          Usage — {stats.tier.toUpperCase()} Tier
        </h3>
        {showUpgrade && (
          <a
            href="/pricing"
            className="text-xs font-medium text-blue-600 hover:text-blue-700"
          >
            Upgrade
          </a>
        )}
      </div>
      <div className="space-y-3">
        <ProgressRow label="Projects" bucket={stats.usage.projects} />
        <ProgressRow label="Storage" bucket={stats.usage.storage_mb} />
        <ProgressRow label="Gates / Month" bucket={stats.usage.gates_this_month} />
        <ProgressRow label="Team Members" bucket={stats.usage.members} />
      </div>
    </div>
  );
}
