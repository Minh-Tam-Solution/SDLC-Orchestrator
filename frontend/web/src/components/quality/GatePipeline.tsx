/**
 * =========================================================================
 * GatePipeline - 4-Gate Quality Pipeline Display
 * SDLC Orchestrator - Sprint 55 Day 1
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 * Authority: Frontend Team + CTO Approved
 *
 * Purpose:
 * - Display all 4 quality gates in sequence
 * - Show pipeline progress and status
 * - Animate gate transitions
 * - Support horizontal and vertical layouts
 *
 * References:
 * - docs/02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md
 * =========================================================================
 */

import { useMemo } from "react";
import {
  ArrowRight,
  ArrowDown,
  CheckCircle2,
  XCircle,
  Timer,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { GateStatusBadge, GateStatusIcon } from "./GateStatusBadge";
import type {
  GateResult,
  GateName,
  GateStatus,
  PipelineResult,
} from "@/types/quality";
import {
  GATE_CONFIGS,
  isSyntaxResult,
  isSecurityResult,
  isArchitectureResult,
  isTestResult,
} from "@/types/quality";

// ============================================================================
// Types
// ============================================================================

interface GatePipelineProps {
  /** Pipeline result (optional - for completed pipelines) */
  result?: PipelineResult;
  /** Individual gate results (for streaming updates) */
  gates?: GateResult[];
  /** Current running gate */
  currentGate?: GateName;
  /** Layout direction */
  direction?: "horizontal" | "vertical";
  /** Compact mode */
  compact?: boolean;
  /** Use Vietnamese labels */
  vietnamese?: boolean;
  /** Show detailed stats */
  showDetails?: boolean;
  /** Gate click handler */
  onGateClick?: (gateName: GateName) => void;
  /** Additional class name */
  className?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

function getGateOrder(): GateName[] {
  return ["syntax", "security", "architecture", "tests"];
}

function getGateStatus(
  gateName: GateName,
  gates: GateResult[],
  currentGate?: GateName
): GateStatus {
  const gateResult = gates.find((g) => g.gateName === gateName);

  if (gateResult) {
    return gateResult.status;
  }

  if (currentGate === gateName) {
    return "running";
  }

  const gateOrder = getGateOrder();
  const currentIndex = currentGate
    ? gateOrder.indexOf(currentGate)
    : -1;
  const gateIndex = gateOrder.indexOf(gateName);

  if (currentIndex >= 0 && gateIndex < currentIndex) {
    // Gates before current should be either passed or show as passed if not in results
    return "pending";
  }

  return "pending";
}

function getIssueCount(gate: GateResult): number {
  if (isSyntaxResult(gate.details)) {
    return gate.details.issues.length;
  }
  if (isSecurityResult(gate.details)) {
    return gate.details.issues.length;
  }
  if (isArchitectureResult(gate.details)) {
    return gate.details.issues.length;
  }
  if (isTestResult(gate.details)) {
    return gate.details.testsFailed;
  }
  return 0;
}

function formatTotalDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  if (ms < 60000) {
    return `${(ms / 1000).toFixed(1)}s`;
  }
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  return `${minutes}m ${seconds}s`;
}

function calculateProgress(gates: GateResult[], currentGate?: GateName): number {
  const gateOrder = getGateOrder();
  const completedGates = gates.filter(
    (g) => g.status === "passed" || g.status === "failed"
  ).length;

  let progress = (completedGates / gateOrder.length) * 100;

  if (currentGate) {
    const currentIndex = gateOrder.indexOf(currentGate);
    const gateProgress = ((currentIndex + 0.5) / gateOrder.length) * 100;
    progress = Math.max(progress, gateProgress);
  }

  return Math.min(progress, 100);
}

// ============================================================================
// Sub-Components
// ============================================================================

interface GateConnectorProps {
  direction: "horizontal" | "vertical";
  status: "pending" | "active" | "completed";
}

function GateConnector({ direction, status }: GateConnectorProps) {
  const isHorizontal = direction === "horizontal";
  const Icon = isHorizontal ? ArrowRight : ArrowDown;

  const colorClass =
    status === "completed"
      ? "text-green-500"
      : status === "active"
        ? "text-blue-500 animate-pulse"
        : "text-gray-300 dark:text-gray-600";

  return (
    <div
      className={cn(
        "flex items-center justify-center",
        isHorizontal ? "px-2" : "py-2"
      )}
    >
      <Icon className={cn("h-4 w-4", colorClass)} />
    </div>
  );
}

interface GateCardProps {
  gateName: GateName;
  status: GateStatus;
  durationMs?: number;
  issuesCount?: number;
  vietnamese?: boolean;
  compact?: boolean;
  onClick?: () => void;
}

function GateCard({
  gateName,
  status,
  durationMs,
  issuesCount,
  vietnamese = false,
  compact = false,
  onClick,
}: GateCardProps) {
  const config = GATE_CONFIGS[gateName];

  if (compact) {
    return (
      <GateStatusBadge
        gateName={gateName}
        status={status}
        durationMs={durationMs}
        issuesCount={issuesCount}
        compact={true}
        vietnamese={vietnamese}
        onClick={onClick}
      />
    );
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        "flex flex-col items-center gap-2 p-3 rounded-lg border transition-all",
        "hover:bg-muted/50 focus:outline-none focus:ring-2 focus:ring-ring",
        status === "passed" && "border-green-300 bg-green-50/50 dark:bg-green-900/10",
        status === "failed" && "border-red-300 bg-red-50/50 dark:bg-red-900/10",
        status === "running" && "border-blue-300 bg-blue-50/50 dark:bg-blue-900/10",
        status === "pending" && "border-gray-200 dark:border-gray-700"
      )}
    >
      <GateStatusIcon status={status} size="lg" />
      <span className="text-sm font-medium">
        {vietnamese ? config.vietnameseLabel : config.label}
      </span>
      {durationMs !== undefined && status !== "pending" && (
        <span className="text-xs text-muted-foreground">
          {formatTotalDuration(durationMs)}
        </span>
      )}
      {issuesCount !== undefined && issuesCount > 0 && (
        <Badge variant="destructive" className="text-xs">
          {issuesCount} {vietnamese ? "lỗi" : "issues"}
        </Badge>
      )}
    </button>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function GatePipeline({
  result,
  gates = [],
  currentGate,
  direction = "horizontal",
  compact = false,
  vietnamese = false,
  showDetails = false,
  onGateClick,
  className,
}: GatePipelineProps) {
  const gateOrder = getGateOrder();
  const effectiveGates = result?.gates || gates;
  const progress = calculateProgress(effectiveGates, currentGate);

  const pipelineStatus = useMemo(() => {
    if (result) {
      return result.passed ? "passed" : "failed";
    }
    if (effectiveGates.some((g) => g.status === "failed")) {
      return "failed";
    }
    if (currentGate) {
      return "running";
    }
    if (effectiveGates.every((g) => g.status === "passed")) {
      return "passed";
    }
    return "pending";
  }, [result, effectiveGates, currentGate]);

  const totalDuration = useMemo(() => {
    if (result) {
      return result.totalDurationMs;
    }
    return effectiveGates.reduce((sum, g) => sum + (g.durationMs || 0), 0);
  }, [result, effectiveGates]);

  const totalIssues = useMemo(() => {
    return effectiveGates.reduce((sum, g) => sum + getIssueCount(g), 0);
  }, [effectiveGates]);

  const isHorizontal = direction === "horizontal";

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            {pipelineStatus === "passed" && (
              <CheckCircle2 className="h-5 w-5 text-green-500" />
            )}
            {pipelineStatus === "failed" && (
              <XCircle className="h-5 w-5 text-red-500" />
            )}
            {vietnamese ? "Đường ống chất lượng" : "Quality Pipeline"}
          </CardTitle>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            {totalDuration > 0 && (
              <span className="flex items-center gap-1">
                <Timer className="h-4 w-4" />
                {formatTotalDuration(totalDuration)}
              </span>
            )}
            {totalIssues > 0 && (
              <Badge variant="destructive">
                {totalIssues} {vietnamese ? "lỗi" : "issues"}
              </Badge>
            )}
          </div>
        </div>
        <Progress value={progress} className="h-2 mt-2" />
      </CardHeader>

      <CardContent>
        {/* Gate Pipeline */}
        <div
          className={cn(
            "flex items-center gap-1",
            isHorizontal ? "flex-row justify-between" : "flex-col"
          )}
        >
          {gateOrder.map((gateName, index) => {
            const gateResult = effectiveGates.find(
              (g) => g.gateName === gateName
            );
            const status = gateResult?.status || getGateStatus(gateName, effectiveGates, currentGate);
            const durationMs = gateResult?.durationMs;
            const issuesCount = gateResult ? getIssueCount(gateResult) : undefined;

            const connectorStatus =
              status === "passed"
                ? "completed"
                : status === "running"
                  ? "active"
                  : "pending";

            return (
              <div
                key={gateName}
                className={cn(
                  "flex items-center",
                  isHorizontal ? "flex-row" : "flex-col"
                )}
              >
                <GateCard
                  gateName={gateName}
                  status={status}
                  durationMs={durationMs}
                  issuesCount={issuesCount}
                  vietnamese={vietnamese}
                  compact={compact}
                  onClick={() => onGateClick?.(gateName)}
                />
                {index < gateOrder.length - 1 && (
                  <GateConnector
                    direction={direction}
                    status={connectorStatus}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Summary Message */}
        {result && showDetails && (
          <div
            className={cn(
              "mt-4 p-3 rounded-lg text-sm",
              result.passed
                ? "bg-green-50 text-green-800 dark:bg-green-900/20 dark:text-green-400"
                : "bg-red-50 text-red-800 dark:bg-red-900/20 dark:text-red-400"
            )}
          >
            {vietnamese ? result.vietnameseSummary : (
              result.passed
                ? "All quality gates passed. Code is ready for use."
                : `Quality check failed. ${totalIssues} issues found.`
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Variant: Compact Pipeline (Inline)
// ============================================================================

interface CompactPipelineProps {
  gates: GateResult[];
  currentGate?: GateName;
  vietnamese?: boolean;
  className?: string;
}

export function CompactPipeline({
  gates,
  currentGate,
  vietnamese = false,
  className,
}: CompactPipelineProps) {
  const gateOrder = getGateOrder();

  return (
    <div className={cn("flex items-center gap-1", className)}>
      {gateOrder.map((gateName) => {
        const gateResult = gates.find((g) => g.gateName === gateName);
        const status = gateResult?.status || getGateStatus(gateName, gates, currentGate);

        return (
          <GateStatusBadge
            key={gateName}
            gateName={gateName}
            status={status}
            compact={true}
            vietnamese={vietnamese}
          />
        );
      })}
    </div>
  );
}

// ============================================================================
// Export
// ============================================================================

export default GatePipeline;
