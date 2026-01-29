/**
 * =========================================================================
 * Vibecoding Dashboard Component
 * SDLC Orchestrator - Sprint 118 (SPEC-0001 Anti-Vibecoding System)
 *
 * Version: 1.0.0
 * Date: January 29, 2026
 * Framework: SDLC 5.3.0 Quality Assurance System
 * Spec Reference: SPEC-0001
 *
 * Purpose: Main dashboard for Vibecoding Index visualization
 * Features: Zone distribution, signal breakdown, trend analysis
 * =========================================================================
 */

"use client";

import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  useVibecodingStats,
  useZoneColor,
} from "@/hooks/useVibecodingIndex";

// =============================================================================
// Icons
// =============================================================================

function ChartBarIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z"
      />
    </svg>
  );
}

function ArrowTrendingUpIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941"
      />
    </svg>
  );
}

function ArrowTrendingDownIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M2.25 6 9 12.75l4.286-4.286a11.948 11.948 0 0 1 4.306 6.43l.776 2.898m0 0 3.182-5.511m-3.182 5.51-5.511-3.181"
      />
    </svg>
  );
}

function MinusIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14" />
    </svg>
  );
}

function CheckCircleIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
      />
    </svg>
  );
}

// =============================================================================
// Sub-components
// =============================================================================

interface ZoneBarProps {
  zone: "GREEN" | "YELLOW" | "ORANGE" | "RED";
  count: number;
  total: number;
}

function ZoneBar({ zone, count, total }: ZoneBarProps) {
  const { bgColor, textColor, label } = useZoneColor(zone);
  const percentage = total > 0 ? (count / total) * 100 : 0;

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded ${bgColor.replace("100", "500")}`} />
          <span className="font-medium">{zone}</span>
          <span className="text-gray-500">({label})</span>
        </div>
        <span className={textColor}>
          {count} ({percentage.toFixed(1)}%)
        </span>
      </div>
      <Progress value={percentage} className="h-2" />
    </div>
  );
}

interface TrendIndicatorProps {
  trend: "improving" | "stable" | "degrading";
}

function TrendIndicator({ trend }: TrendIndicatorProps) {
  if (trend === "improving") {
    return (
      <div className="flex items-center gap-1 text-green-600">
        <ArrowTrendingDownIcon className="h-4 w-4" />
        <span className="text-xs font-medium">Improving</span>
      </div>
    );
  } else if (trend === "degrading") {
    return (
      <div className="flex items-center gap-1 text-red-600">
        <ArrowTrendingUpIcon className="h-4 w-4" />
        <span className="text-xs font-medium">Degrading</span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-1 text-gray-500">
      <MinusIcon className="h-4 w-4" />
      <span className="text-xs font-medium">Stable</span>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

interface VibecodingDashboardProps {
  projectId: string;
  showZoneDistribution?: boolean;
  showTrend?: boolean;
  compact?: boolean;
}

export function VibecodingDashboard({
  projectId,
  showZoneDistribution = true,
  showTrend = true,
  compact = false,
}: VibecodingDashboardProps) {
  const { data: stats, isLoading, isError } = useVibecodingStats(projectId);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isError || !stats) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="text-center text-gray-500">
            Failed to load Vibecoding statistics
          </div>
        </CardContent>
      </Card>
    );
  }

  const averageIndex = stats.average_index;
  const averageZone =
    averageIndex <= 20
      ? "GREEN"
      : averageIndex <= 40
      ? "YELLOW"
      : averageIndex <= 60
      ? "ORANGE"
      : "RED";
  const { bgColor, textColor, borderColor, label } = useZoneColor(averageZone);

  if (compact) {
    return (
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <ChartBarIcon className="h-5 w-5 text-blue-600" />
              <div>
                <div className="font-medium">Vibecoding Index</div>
                <div className="text-sm text-gray-500">
                  {stats.total_submissions} submissions
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge className={`${bgColor} ${textColor} ${borderColor}`}>
                {averageIndex.toFixed(1)}
              </Badge>
              {showTrend && <TrendIndicator trend={stats.trend_7d} />}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ChartBarIcon className="h-5 w-5 text-blue-600" />
            <CardTitle className="text-lg">Vibecoding Index</CardTitle>
          </div>
          <Badge className={`${bgColor} ${textColor} ${borderColor}`}>
            Avg: {averageIndex.toFixed(1)} ({label})
          </Badge>
        </div>
        <CardDescription>
          Quality governance metrics based on 5-signal formula
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 border rounded-lg text-center">
            <div className="text-2xl font-bold text-blue-600">
              {stats.total_submissions}
            </div>
            <div className="text-sm text-gray-500">Total Submissions</div>
          </div>
          <div className="p-4 border rounded-lg text-center">
            <div className={`text-2xl font-bold ${textColor}`}>
              {averageIndex.toFixed(1)}
            </div>
            <div className="text-sm text-gray-500">Average Index</div>
          </div>
          <div className="p-4 border rounded-lg text-center">
            <div className="text-2xl font-bold text-green-600">
              {(stats.auto_merge_rate * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500">Auto-Merge Rate</div>
          </div>
        </div>

        {/* Zone Distribution */}
        {showZoneDistribution && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-medium">Zone Distribution</h4>
              {showTrend && <TrendIndicator trend={stats.trend_7d} />}
            </div>
            <div className="space-y-3">
              <ZoneBar
                zone="GREEN"
                count={stats.zone_distribution.GREEN}
                total={stats.total_submissions}
              />
              <ZoneBar
                zone="YELLOW"
                count={stats.zone_distribution.YELLOW}
                total={stats.total_submissions}
              />
              <ZoneBar
                zone="ORANGE"
                count={stats.zone_distribution.ORANGE}
                total={stats.total_submissions}
              />
              <ZoneBar
                zone="RED"
                count={stats.zone_distribution.RED}
                total={stats.total_submissions}
              />
            </div>
          </div>
        )}

        {/* Formula Reference */}
        <div className="border-t pt-4">
          <h4 className="font-medium text-sm mb-2">5-Signal Formula</h4>
          <div className="grid grid-cols-5 gap-2 text-xs">
            <div className="p-2 bg-blue-50 rounded text-center">
              <div className="font-bold text-blue-700">30%</div>
              <div className="text-blue-600">Intent</div>
            </div>
            <div className="p-2 bg-purple-50 rounded text-center">
              <div className="font-bold text-purple-700">25%</div>
              <div className="text-purple-600">Ownership</div>
            </div>
            <div className="p-2 bg-green-50 rounded text-center">
              <div className="font-bold text-green-700">20%</div>
              <div className="text-green-600">Context</div>
            </div>
            <div className="p-2 bg-amber-50 rounded text-center">
              <div className="font-bold text-amber-700">15%</div>
              <div className="text-amber-600">AI Attest</div>
            </div>
            <div className="p-2 bg-red-50 rounded text-center">
              <div className="font-bold text-red-700">10%</div>
              <div className="text-red-600">Rejection</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default VibecodingDashboard;
