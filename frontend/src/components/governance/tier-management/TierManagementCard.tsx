/**
 * =========================================================================
 * Tier Management Card Component
 * SDLC Orchestrator - Sprint 118 (4-Tier Classification System)
 *
 * Version: 1.0.0
 * Date: January 29, 2026
 * Framework: SDLC 5.3.0 Quality Assurance System
 * ADR Reference: ADR-041
 *
 * Purpose: Display project tier status and upgrade eligibility
 * Tiers: LITE, STANDARD, PROFESSIONAL, ENTERPRISE
 * =========================================================================
 */

"use client";

import { useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  useProjectTier,
  useTierDisplay,
  useTierProgression,
  useCanRequestUpgrade,
  useRequestTierUpgrade,
  type TierLevel,
} from "@/hooks/useTierManagement";

// =============================================================================
// Icons
// =============================================================================

function ShieldCheckIcon({ className }: { className?: string }) {
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
        d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z"
      />
    </svg>
  );
}

function ArrowUpIcon({ className }: { className?: string }) {
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
        d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18"
      />
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

function XCircleIcon({ className }: { className?: string }) {
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
        d="m9.75 9.75 4.5 4.5m0-4.5-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
      />
    </svg>
  );
}

function SparklesIcon({ className }: { className?: string }) {
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
        d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z"
      />
    </svg>
  );
}

// =============================================================================
// Sub-components
// =============================================================================

interface TierBadgeProps {
  tier: TierLevel;
  size?: "sm" | "md" | "lg";
}

function TierBadge({ tier, size = "md" }: TierBadgeProps) {
  const display = useTierDisplay(tier);

  const sizeClasses = {
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-3 py-1",
    lg: "text-lg px-4 py-2",
  };

  return (
    <Badge className={`${display.bgColor} ${display.textColor} ${display.borderColor} ${sizeClasses[size]}`}>
      <span className="font-bold mr-1">{display.icon}</span>
      {display.name}
    </Badge>
  );
}

interface TierProgressProps {
  currentTier: TierLevel;
  completionPercentage: number;
}

function TierProgress({ currentTier, completionPercentage }: TierProgressProps) {
  const { progressPercentage, nextTier } = useTierProgression(currentTier);

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-gray-500">Tier Progress</span>
        <span className="font-medium">{progressPercentage.toFixed(0)}%</span>
      </div>
      <div className="relative">
        <Progress value={progressPercentage} className="h-3" />
        <div className="absolute inset-0 flex items-center justify-between px-1">
          {["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"].map((tier) => (
            <div
              key={tier}
              className={`w-2 h-2 rounded-full ${
                tier === currentTier
                  ? "bg-blue-600 ring-2 ring-white"
                  : "bg-gray-300"
              }`}
            />
          ))}
        </div>
      </div>
      {nextTier && (
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Current: {currentTier}</span>
          <span>Next: {nextTier} ({completionPercentage}% ready)</span>
        </div>
      )}
    </div>
  );
}

interface MissingRequirementsProps {
  requirements: string[];
  maxShow?: number;
}

function MissingRequirements({ requirements, maxShow = 5 }: MissingRequirementsProps) {
  const [showAll, setShowAll] = useState(false);
  const displayRequirements = showAll ? requirements : requirements.slice(0, maxShow);
  const remaining = requirements.length - maxShow;

  if (requirements.length === 0) {
    return (
      <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg text-green-700">
        <CheckCircleIcon className="h-5 w-5" />
        <span className="text-sm">All requirements met for next tier!</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="text-sm font-medium text-gray-700">
        Missing Requirements ({requirements.length})
      </div>
      <div className="space-y-1">
        {displayRequirements.map((req, idx) => (
          <div
            key={idx}
            className="flex items-start gap-2 p-2 bg-red-50 rounded text-red-700 text-sm"
          >
            <XCircleIcon className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <span>{req}</span>
          </div>
        ))}
      </div>
      {remaining > 0 && !showAll && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowAll(true)}
          className="text-xs"
        >
          Show {remaining} more...
        </Button>
      )}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

interface TierManagementCardProps {
  projectId: string;
  showUpgradeEligibility?: boolean;
  showFeatures?: boolean;
  compact?: boolean;
}

export function TierManagementCard({
  projectId,
  showUpgradeEligibility = true,
  showFeatures = true,
  compact = false,
}: TierManagementCardProps) {
  const { data: tierData, isLoading, isError } = useProjectTier(projectId);
  const canRequestUpgrade = useCanRequestUpgrade();
  const upgradeMutation = useRequestTierUpgrade();

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

  if (isError || !tierData) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="text-center text-gray-500">
            Failed to load tier information
          </div>
        </CardContent>
      </Card>
    );
  }

  const currentTier = tierData.current_tier as TierLevel;
  const display = useTierDisplay(currentTier);
  const eligibility = tierData.upgrade_eligibility;

  if (compact) {
    return (
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <ShieldCheckIcon className={`h-5 w-5 ${display.textColor}`} />
              <div>
                <div className="font-medium">{tierData.project_name}</div>
                <div className="text-sm text-gray-500">
                  {tierData.requirements_met}/{tierData.requirements_total} requirements
                </div>
              </div>
            </div>
            <TierBadge tier={currentTier} />
          </div>
        </CardContent>
      </Card>
    );
  }

  const handleRequestUpgrade = async () => {
    if (!tierData.next_tier) return;

    try {
      await upgradeMutation.mutateAsync({
        projectId,
        request: {
          target_tier: tierData.next_tier as TierLevel,
          justification: "Automatic upgrade request - all requirements met",
        },
      });
    } catch (error) {
      console.error("Failed to request upgrade:", error);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheckIcon className={`h-5 w-5 ${display.textColor}`} />
            <CardTitle className="text-lg">Project Tier</CardTitle>
          </div>
          <TierBadge tier={currentTier} size="lg" />
        </div>
        <CardDescription>{display.description}</CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Project Info */}
        <div className="p-4 border rounded-lg">
          <div className="font-medium text-lg">{tierData.project_name}</div>
          <div className="text-sm text-gray-500 mt-1">
            Tier since {new Date(tierData.tier_since).toLocaleDateString()}
          </div>
          <div className="mt-3 flex items-center gap-4">
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {tierData.compliance_score}%
              </div>
              <div className="text-xs text-gray-500">Compliance Score</div>
            </div>
            <div className="h-10 border-l" />
            <div>
              <div className="text-2xl font-bold text-green-600">
                {tierData.requirements_met}/{tierData.requirements_total}
              </div>
              <div className="text-xs text-gray-500">Requirements Met</div>
            </div>
          </div>
        </div>

        {/* Tier Progress */}
        <TierProgress
          currentTier={currentTier}
          completionPercentage={eligibility.completion_percentage}
        />

        {/* Features */}
        {showFeatures && (
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">
              Included Features
            </div>
            <div className="grid grid-cols-2 gap-2">
              {display.features.map((feature, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 text-sm text-gray-600"
                >
                  <CheckCircleIcon className="h-4 w-4 text-green-500" />
                  {feature}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Upgrade Eligibility */}
        {showUpgradeEligibility && tierData.next_tier && (
          <div className="border-t pt-4 space-y-4">
            <div className="flex items-center gap-2">
              <SparklesIcon className="h-5 w-5 text-amber-500" />
              <span className="font-medium">
                Upgrade to{" "}
                <TierBadge tier={tierData.next_tier as TierLevel} size="sm" />
              </span>
            </div>

            <Progress
              value={eligibility.completion_percentage}
              className="h-2"
            />
            <div className="text-sm text-gray-500">
              {eligibility.completion_percentage}% complete
            </div>

            <MissingRequirements
              requirements={eligibility.missing_requirements}
            />

            {eligibility.eligible && canRequestUpgrade && (
              <Button
                onClick={handleRequestUpgrade}
                disabled={upgradeMutation.isPending}
                className="w-full"
              >
                <ArrowUpIcon className="h-4 w-4 mr-2" />
                {upgradeMutation.isPending
                  ? "Requesting..."
                  : `Request Upgrade to ${tierData.next_tier}`}
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default TierManagementCard;
