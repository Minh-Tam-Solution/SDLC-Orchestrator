/**
 * DORA Metrics Dashboard — Sprint 211 Track C
 *
 * Displays the four key DORA metrics derived from gate lifecycle data:
 * Deployment Frequency, Lead Time, MTTR, and Change Failure Rate.
 * Includes a Recharts line chart for daily trend visualisation.
 */

"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface MetricEntry {
  value: number;
  unit: string;
  rating: "Elite" | "High" | "Medium" | "Low";
}

interface TrendPoint {
  date: string;
  deployment_frequency: number;
  lead_time_hours: number;
  mttr_hours: number;
  change_failure_rate: number;
}

interface DoraResponse {
  project_id: string;
  period_days: number;
  metrics: {
    deployment_frequency: MetricEntry;
    lead_time_hours: MetricEntry;
    mttr_hours: MetricEntry;
    change_failure_rate: MetricEntry;
  };
  trend: TrendPoint[];
}

const RATING_COLORS: Record<string, string> = {
  Elite: "bg-green-100 text-green-800",
  High: "bg-blue-100 text-blue-800",
  Medium: "bg-amber-100 text-amber-800",
  Low: "bg-red-100 text-red-800",
};

const PERIOD_OPTIONS = ["7d", "30d", "90d"] as const;

function MetricCard({ title, metric }: { title: string; metric: MetricEntry }) {
  const badge = RATING_COLORS[metric.rating] || "bg-gray-100 text-gray-800";
  const display =
    metric.unit === "percentage"
      ? `${(metric.value * 100).toFixed(1)}%`
      : `${metric.value} ${metric.unit === "per_week" ? "/ week" : metric.unit}`;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-gray-500">{title}</p>
      <p className="mt-2 text-2xl font-semibold text-gray-900">{display}</p>
      <span className={`mt-2 inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${badge}`}>
        {metric.rating}
      </span>
    </div>
  );
}

export default function DoraPage() {
  const [period, setPeriod] = useState<string>("30d");
  const [data, setData] = useState<DoraResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const token = localStorage.getItem("access_token");

    async function fetchMetrics() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(
          `${API_BASE}/api/v1/dora/metrics?period=${period}`,
          { headers: token ? { Authorization: `Bearer ${token}` } : {} },
        );
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail || `HTTP ${res.status}`);
        }
        const json: DoraResponse = await res.json();
        if (!cancelled) setData(json);
      } catch (err: unknown) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load metrics");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchMetrics();
    return () => { cancelled = true; };
  }, [period]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">DORA Metrics</h1>
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {PERIOD_OPTIONS.map((p) => (
            <option key={p} value={p}>{p === "7d" ? "Last 7 days" : p === "30d" ? "Last 30 days" : "Last 90 days"}</option>
          ))}
        </select>
      </div>

      {/* Loading skeleton */}
      {loading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-28 animate-pulse rounded-lg bg-gray-100" />
          ))}
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
      )}

      {/* No data */}
      {!loading && !error && data && !data.trend.length && (
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center text-gray-500">
          No data available for the selected period.
        </div>
      )}

      {/* Metric cards */}
      {!loading && !error && data && data.trend.length > 0 && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <MetricCard title="Deployment Frequency" metric={data.metrics.deployment_frequency} />
            <MetricCard title="Lead Time for Changes" metric={data.metrics.lead_time_hours} />
            <MetricCard title="Mean Time to Restore" metric={data.metrics.mttr_hours} />
            <MetricCard title="Change Failure Rate" metric={data.metrics.change_failure_rate} />
          </div>

          {/* Trend chart */}
          <div className="mt-8 rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">Trend</h2>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={data.trend} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="deployment_frequency" name="Deploy Freq" stroke="#3b82f6" dot={false} />
                <Line type="monotone" dataKey="lead_time_hours" name="Lead Time (h)" stroke="#22c55e" dot={false} />
                <Line type="monotone" dataKey="mttr_hours" name="MTTR (h)" stroke="#f97316" dot={false} />
                <Line type="monotone" dataKey="change_failure_rate" name="CFR" stroke="#ef4444" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
