/**
 * =========================================================================
 * Signal Breakdown Component
 * SDLC Orchestrator - Sprint 118 (SPEC-0001 Anti-Vibecoding System)
 *
 * Version: 1.0.0
 * Date: January 29, 2026
 * Framework: SDLC 5.3.0 Quality Assurance System
 * Spec Reference: SPEC-0001
 *
 * Purpose: Detailed visualization of 5-signal breakdown for a submission
 * Signals: Intent (30%), Ownership (25%), Context (20%), AI Attestation (15%), Rejection (10%)
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
import { useVibecodingSignals, useZoneColor } from "@/hooks/useVibecodingIndex";

// =============================================================================
// Icons
// =============================================================================

function DocumentTextIcon({ className }: { className?: string }) {
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
        d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
      />
    </svg>
  );
}

function UserIcon({ className }: { className?: string }) {
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
        d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"
      />
    </svg>
  );
}

function LinkIcon({ className }: { className?: string }) {
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
        d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244"
      />
    </svg>
  );
}

function CpuChipIcon({ className }: { className?: string }) {
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
        d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 0 0 2.25-2.25V6.75a2.25 2.25 0 0 0-2.25-2.25H6.75A2.25 2.25 0 0 0 4.5 6.75v10.5a2.25 2.25 0 0 0 2.25 2.25Zm.75-12h9v9h-9v-9Z"
      />
    </svg>
  );
}

function ExclamationTriangleIcon({ className }: { className?: string }) {
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
        d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
      />
    </svg>
  );
}

function LightBulbIcon({ className }: { className?: string }) {
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
        d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18"
      />
    </svg>
  );
}

// =============================================================================
// Types
// =============================================================================

interface SignalConfig {
  key: string;
  name: string;
  weight: number;
  icon: React.ReactNode;
  colorClass: string;
  bgClass: string;
}

const SIGNAL_CONFIG: SignalConfig[] = [
  {
    key: "intent",
    name: "Intent",
    weight: 30,
    icon: <DocumentTextIcon className="h-4 w-4" />,
    colorClass: "text-blue-600",
    bgClass: "bg-blue-50",
  },
  {
    key: "ownership",
    name: "Ownership",
    weight: 25,
    icon: <UserIcon className="h-4 w-4" />,
    colorClass: "text-purple-600",
    bgClass: "bg-purple-50",
  },
  {
    key: "context",
    name: "Context",
    weight: 20,
    icon: <LinkIcon className="h-4 w-4" />,
    colorClass: "text-green-600",
    bgClass: "bg-green-50",
  },
  {
    key: "ai_attestation",
    name: "AI Attestation",
    weight: 15,
    icon: <CpuChipIcon className="h-4 w-4" />,
    colorClass: "text-amber-600",
    bgClass: "bg-amber-50",
  },
  {
    key: "rejection_history",
    name: "Rejection History",
    weight: 10,
    icon: <ExclamationTriangleIcon className="h-4 w-4" />,
    colorClass: "text-red-600",
    bgClass: "bg-red-50",
  },
];

// =============================================================================
// Sub-components
// =============================================================================

interface SignalRowProps {
  config: SignalConfig;
  score: number;
  weight: number;
  contribution: number;
  details: string;
}

function SignalRow({ config, score, weight, contribution, details }: SignalRowProps) {
  const scoreColor =
    score <= 20
      ? "text-green-600"
      : score <= 40
      ? "text-yellow-600"
      : score <= 60
      ? "text-orange-600"
      : "text-red-600";

  return (
    <div className={`p-4 rounded-lg border ${config.bgClass}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={config.colorClass}>{config.icon}</span>
          <span className="font-medium">{config.name}</span>
          <Badge variant="outline" className="text-xs">
            {weight}%
          </Badge>
        </div>
        <div className="flex items-center gap-3">
          <span className={`font-bold ${scoreColor}`}>{score.toFixed(1)}</span>
          <span className="text-xs text-gray-500">
            → {contribution.toFixed(1)} pts
          </span>
        </div>
      </div>
      <Progress value={score} max={100} className="h-2 mb-2" />
      <div className="text-xs text-gray-600">{details}</div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

interface SignalBreakdownProps {
  submissionId: string;
  showSuggestions?: boolean;
  compact?: boolean;
}

export function SignalBreakdown({
  submissionId,
  showSuggestions = true,
  compact = false,
}: SignalBreakdownProps) {
  const { data, isLoading, isError } = useVibecodingSignals(submissionId);

  // Calculate zone and call hook unconditionally (React rules of hooks)
  const indexScore = data?.index_score ?? 0;
  const zone =
    indexScore <= 20
      ? "GREEN"
      : indexScore <= 40
      ? "YELLOW"
      : indexScore <= 60
      ? "ORANGE"
      : "RED";
  const { bgColor, textColor, borderColor, label } = useZoneColor(zone);

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

  if (isError || !data) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="text-center text-gray-500">
            Failed to load signal breakdown
          </div>
        </CardContent>
      </Card>
    );
  }

  if (compact) {
    return (
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between mb-3">
            <span className="font-medium">Signal Breakdown</span>
            <Badge className={`${bgColor} ${textColor} ${borderColor}`}>
              {indexScore.toFixed(1)} - {label}
            </Badge>
          </div>
          <div className="grid grid-cols-5 gap-2">
            {SIGNAL_CONFIG.map((config) => {
              const signalData = data.signals[config.key as keyof typeof data.signals];
              return (
                <div
                  key={config.key}
                  className={`p-2 rounded text-center ${config.bgClass}`}
                >
                  <div className={`text-sm font-bold ${config.colorClass}`}>
                    {signalData.score.toFixed(0)}
                  </div>
                  <div className="text-xs text-gray-500">{config.name}</div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Signal Breakdown</CardTitle>
            <CardDescription>
              Detailed analysis of vibecoding index components
            </CardDescription>
          </div>
          <Badge className={`${bgColor} ${textColor} ${borderColor} text-lg px-3 py-1`}>
            {indexScore.toFixed(1)}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Signal Details */}
        {SIGNAL_CONFIG.map((config) => {
          const signalData = data.signals[config.key as keyof typeof data.signals];
          return (
            <SignalRow
              key={config.key}
              config={config}
              score={signalData.score}
              weight={signalData.weight}
              contribution={signalData.contribution}
              details={signalData.details}
            />
          );
        })}

        {/* Top Contributors */}
        {showSuggestions && data.top_contributors.length > 0 && (
          <div className="border-t pt-4">
            <div className="flex items-center gap-2 mb-3">
              <LightBulbIcon className="h-5 w-5 text-amber-500" />
              <h4 className="font-medium">Improvement Suggestions</h4>
            </div>
            <div className="space-y-2">
              {data.top_contributors.map((contributor, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-amber-50 border border-amber-200 rounded-lg"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-amber-800">
                      {contributor.signal}
                    </span>
                    <Badge variant="outline" className="text-amber-700">
                      {contributor.contribution_percent.toFixed(0)}% impact
                    </Badge>
                  </div>
                  <div className="text-sm text-amber-700">
                    {contributor.improvement_suggestion}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default SignalBreakdown;
