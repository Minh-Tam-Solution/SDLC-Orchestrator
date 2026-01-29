/**
 * =========================================================================
 * Routing Decision Card Component
 * SDLC Orchestrator - Sprint 118 (SPEC-0001 Anti-Vibecoding System)
 *
 * Version: 1.0.0
 * Date: January 29, 2026
 * Framework: SDLC 5.3.0 Quality Assurance System
 * Spec Reference: SPEC-0001
 *
 * Purpose: Display routing decision based on Vibecoding Index zone
 * Zones: GREEN (0-20), YELLOW (20-40), ORANGE (40-60), RED (60-100)
 * =========================================================================
 */

"use client";

import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useZoneColor } from "@/hooks/useVibecodingIndex";

// =============================================================================
// Icons
// =============================================================================

function CheckIcon({ className }: { className?: string }) {
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
        d="m4.5 12.75 6 6 9-13.5"
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

function UsersIcon({ className }: { className?: string }) {
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
        d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z"
      />
    </svg>
  );
}

function XMarkIcon({ className }: { className?: string }) {
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
        d="M6 18 18 6M6 6l12 12"
      />
    </svg>
  );
}

function ArrowRightIcon({ className }: { className?: string }) {
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
        d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"
      />
    </svg>
  );
}

// =============================================================================
// Types
// =============================================================================

type RoutingDecision = "AUTO_MERGE" | "HUMAN_REVIEW" | "SENIOR_REVIEW" | "BLOCK";
type Zone = "GREEN" | "YELLOW" | "ORANGE" | "RED";

interface RoutingConfig {
  decision: RoutingDecision;
  icon: React.ReactNode;
  title: string;
  description: string;
  action: string;
}

const ROUTING_CONFIG: Record<RoutingDecision, RoutingConfig> = {
  AUTO_MERGE: {
    decision: "AUTO_MERGE",
    icon: <CheckIcon className="h-6 w-6" />,
    title: "Auto-Merge",
    description: "Submission passes all quality criteria",
    action: "PR will be auto-approved",
  },
  HUMAN_REVIEW: {
    decision: "HUMAN_REVIEW",
    icon: <UserIcon className="h-6 w-6" />,
    title: "Human Review Required",
    description: "Submission requires team lead review",
    action: "Awaiting team lead approval",
  },
  SENIOR_REVIEW: {
    decision: "SENIOR_REVIEW",
    icon: <UsersIcon className="h-6 w-6" />,
    title: "Senior Review Required",
    description: "Submission requires senior engineer or CTO review",
    action: "Escalated for senior review",
  },
  BLOCK: {
    decision: "BLOCK",
    icon: <XMarkIcon className="h-6 w-6" />,
    title: "Blocked",
    description: "Submission does not meet minimum quality criteria",
    action: "Must improve before proceeding",
  },
};

// =============================================================================
// Sub-components
// =============================================================================

interface ZoneIndicatorProps {
  zone: Zone;
  indexScore: number;
}

function ZoneIndicator({ zone, indexScore }: ZoneIndicatorProps) {
  const { bgColor, textColor, borderColor, label } = useZoneColor(zone);

  return (
    <div className={`p-4 rounded-lg border-2 ${bgColor} ${borderColor}`}>
      <div className="flex items-center justify-between">
        <div>
          <div className={`text-3xl font-bold ${textColor}`}>
            {indexScore.toFixed(1)}
          </div>
          <div className={`text-sm ${textColor}`}>Vibecoding Index</div>
        </div>
        <Badge className={`${bgColor} ${textColor} ${borderColor} text-lg px-4 py-2`}>
          {zone}
        </Badge>
      </div>
      <div className={`mt-2 text-sm ${textColor}`}>{label}</div>
    </div>
  );
}

interface EscalationPathProps {
  path: string[];
}

function EscalationPath({ path }: EscalationPathProps) {
  if (path.length === 0) return null;

  return (
    <div className="mt-4 p-3 bg-gray-50 rounded-lg">
      <div className="text-xs font-medium text-gray-500 mb-2">
        Escalation Path
      </div>
      <div className="flex items-center gap-2 flex-wrap">
        {path.map((step, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <Badge variant="outline">{step}</Badge>
            {idx < path.length - 1 && (
              <ArrowRightIcon className="h-3 w-3 text-gray-400" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

interface RoutingDecisionCardProps {
  indexScore: number;
  decision: RoutingDecision;
  approverRequired?: string | null;
  reason: string;
  escalationPath?: string[];
  compact?: boolean;
}

export function RoutingDecisionCard({
  indexScore,
  decision,
  approverRequired,
  reason,
  escalationPath = [],
  compact = false,
}: RoutingDecisionCardProps) {
  const zone: Zone =
    indexScore <= 20
      ? "GREEN"
      : indexScore <= 40
      ? "YELLOW"
      : indexScore <= 60
      ? "ORANGE"
      : "RED";
  const { bgColor, textColor, borderColor } = useZoneColor(zone);
  const config = ROUTING_CONFIG[decision];

  if (compact) {
    return (
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${bgColor}`}>
                <span className={textColor}>{config.icon}</span>
              </div>
              <div>
                <div className="font-medium">{config.title}</div>
                <div className="text-sm text-gray-500">{config.action}</div>
              </div>
            </div>
            <Badge className={`${bgColor} ${textColor} ${borderColor}`}>
              {indexScore.toFixed(1)}
            </Badge>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Routing Decision</CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Zone Indicator */}
        <ZoneIndicator zone={zone} indexScore={indexScore} />

        {/* Decision Card */}
        <div className={`p-4 rounded-lg border-2 ${bgColor} ${borderColor}`}>
          <div className="flex items-start gap-4">
            <div className={`p-3 rounded-lg bg-white shadow-sm`}>
              <span className={textColor}>{config.icon}</span>
            </div>
            <div className="flex-1">
              <div className={`font-bold text-lg ${textColor}`}>
                {config.title}
              </div>
              <div className="text-gray-600 mt-1">{config.description}</div>
              <div className={`mt-2 font-medium ${textColor}`}>
                {config.action}
              </div>
            </div>
          </div>

          {approverRequired && (
            <div className="mt-4 p-3 bg-white/50 rounded-lg">
              <div className="text-sm">
                <span className="font-medium">Approver Required:</span>{" "}
                <span className={textColor}>{approverRequired}</span>
              </div>
            </div>
          )}
        </div>

        {/* Reason */}
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="text-xs font-medium text-gray-500 mb-1">Reason</div>
          <div className="text-sm text-gray-700">{reason}</div>
        </div>

        {/* Escalation Path */}
        <EscalationPath path={escalationPath} />

        {/* Zone Thresholds Reference */}
        <div className="border-t pt-4">
          <div className="text-xs font-medium text-gray-500 mb-2">
            Zone Thresholds
          </div>
          <div className="grid grid-cols-4 gap-2 text-xs">
            <div className={`p-2 rounded text-center ${zone === "GREEN" ? "ring-2 ring-green-500" : ""} bg-green-100`}>
              <div className="font-bold text-green-700">0-20</div>
              <div className="text-green-600">GREEN</div>
            </div>
            <div className={`p-2 rounded text-center ${zone === "YELLOW" ? "ring-2 ring-yellow-500" : ""} bg-yellow-100`}>
              <div className="font-bold text-yellow-700">20-40</div>
              <div className="text-yellow-600">YELLOW</div>
            </div>
            <div className={`p-2 rounded text-center ${zone === "ORANGE" ? "ring-2 ring-orange-500" : ""} bg-orange-100`}>
              <div className="font-bold text-orange-700">40-60</div>
              <div className="text-orange-600">ORANGE</div>
            </div>
            <div className={`p-2 rounded text-center ${zone === "RED" ? "ring-2 ring-red-500" : ""} bg-red-100`}>
              <div className="font-bold text-red-700">60-100</div>
              <div className="text-red-600">RED</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default RoutingDecisionCard;
