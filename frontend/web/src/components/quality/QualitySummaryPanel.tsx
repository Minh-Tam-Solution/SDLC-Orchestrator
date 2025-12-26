/**
 * =========================================================================
 * QualitySummaryPanel - Compact Quality Summary Components
 * SDLC Orchestrator - Sprint 55 Day 5
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 *
 * Purpose:
 * - Display compact quality summary
 * - Show key metrics at a glance
 * - Provide quick access to detailed reports
 * - Support inline and card variants
 *
 * References:
 * - docs/02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md
 * =========================================================================
 */

import { useMemo } from "react";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  AlertCircle,
  Clock,
  Shield,
  Code2,
  Layers,
  TestTube2,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Minus,
  FileWarning,
  FileCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import type { PipelineResult, GateName, GateResult } from "@/types/quality";
import {
  isSyntaxResult,
  isSecurityResult,
  isArchitectureResult,
  isTestResult,
  GATE_CONFIGS,
} from "@/types/quality";

// ============================================================================
// Types
// ============================================================================

interface QualitySummaryPanelProps {
  /** Pipeline result */
  result: PipelineResult;
  /** Use Vietnamese labels */
  vietnamese?: boolean;
  /** Show trend indicator */
  trend?: "up" | "down" | "stable";
  /** Previous score for comparison */
  previousScore?: number;
  /** Click handler for viewing details */
  onViewDetails?: () => void;
  /** Additional class name */
  className?: string;
}

interface CompactQualitySummaryProps {
  /** Pipeline result */
  result: PipelineResult;
  /** Use Vietnamese labels */
  vietnamese?: boolean;
  /** Click handler */
  onClick?: () => void;
  /** Additional class name */
  className?: string;
}

interface InlineQualityBadgeProps {
  /** Pipeline result */
  result: PipelineResult;
  /** Use Vietnamese labels */
  vietnamese?: boolean;
  /** Show issue count */
  showIssueCount?: boolean;
  /** Additional class name */
  className?: string;
}

interface QualityTrendIndicatorProps {
  /** Current score */
  currentScore: number;
  /** Previous score */
  previousScore: number;
  /** Use Vietnamese labels */
  vietnamese?: boolean;
  /** Additional class name */
  className?: string;
}

interface GateStatusSummaryProps {
  /** Gate results */
  gates: GateResult[];
  /** Use Vietnamese labels */
  vietnamese?: boolean;
  /** Compact mode */
  compact?: boolean;
  /** Additional class name */
  className?: string;
}

// ============================================================================
// Utility Functions
// ============================================================================

function calculateScore(result: PipelineResult): number {
  let score = 100;
  let penalty = 0;

  for (const gate of result.gates) {
    if (gate.status === "failed") {
      penalty += 25;
    } else if (gate.status === "skipped") {
      penalty += 5;
    }

    if (isSecurityResult(gate.details)) {
      penalty += gate.details.criticalCount * 10;
      penalty += gate.details.highCount * 5;
      penalty += gate.details.mediumCount * 2;
      penalty += gate.details.lowCount * 0.5;
    }

    if (isSyntaxResult(gate.details)) {
      const errorRate =
        (gate.details.filesChecked - gate.details.filesPassed) /
        Math.max(gate.details.filesChecked, 1);
      penalty += errorRate * 20;
    }

    if (isTestResult(gate.details)) {
      const failRate =
        gate.details.testsFailed / Math.max(gate.details.testsRun, 1);
      penalty += failRate * 15;
    }

    if (isArchitectureResult(gate.details)) {
      penalty += gate.details.issues.length * 3;
    }
  }

  return Math.max(0, Math.min(100, Math.round(score - penalty)));
}

function getGrade(score: number): { letter: string; color: string; bgColor: string } {
  if (score >= 90) {
    return { letter: "A", color: "text-green-600", bgColor: "bg-green-100 dark:bg-green-900/30" };
  }
  if (score >= 80) {
    return { letter: "B", color: "text-blue-600", bgColor: "bg-blue-100 dark:bg-blue-900/30" };
  }
  if (score >= 70) {
    return { letter: "C", color: "text-yellow-600", bgColor: "bg-yellow-100 dark:bg-yellow-900/30" };
  }
  if (score >= 60) {
    return { letter: "D", color: "text-orange-600", bgColor: "bg-orange-100 dark:bg-orange-900/30" };
  }
  return { letter: "F", color: "text-red-600", bgColor: "bg-red-100 dark:bg-red-900/30" };
}

function getTotalIssues(result: PipelineResult): number {
  let total = 0;

  for (const gate of result.gates) {
    if (isSyntaxResult(gate.details)) {
      total += gate.details.issues.length;
    } else if (isSecurityResult(gate.details)) {
      total += gate.details.issues.length;
    } else if (isArchitectureResult(gate.details)) {
      total += gate.details.issues.length;
    } else if (isTestResult(gate.details)) {
      total += gate.details.testsFailed;
    }
  }

  return total;
}

function getCriticalCount(result: PipelineResult): number {
  for (const gate of result.gates) {
    if (isSecurityResult(gate.details)) {
      return gate.details.criticalCount;
    }
  }
  return 0;
}

// ============================================================================
// Sub-Components
// ============================================================================

export function QualityTrendIndicator({
  currentScore,
  previousScore,
  vietnamese = false,
  className,
}: QualityTrendIndicatorProps) {
  const diff = currentScore - previousScore;
  const trend = diff > 0 ? "up" : diff < 0 ? "down" : "stable";

  const Icon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;
  const color = trend === "up" ? "text-green-500" : trend === "down" ? "text-red-500" : "text-gray-400";

  const label = trend === "up"
    ? vietnamese ? "Tăng" : "Improved"
    : trend === "down"
      ? vietnamese ? "Giảm" : "Declined"
      : vietnamese ? "Ổn định" : "Stable";

  return (
    <div className={cn("flex items-center gap-1", color, className)}>
      <Icon className="h-4 w-4" />
      <span className="text-sm font-medium">
        {diff !== 0 && `${diff > 0 ? "+" : ""}${diff}`} {label}
      </span>
    </div>
  );
}

export function GateStatusSummary({
  gates,
  vietnamese = false,
  compact = false,
  className,
}: GateStatusSummaryProps) {
  const gateOrder: GateName[] = ["syntax", "security", "architecture", "tests"];
  const gateIcons: Record<GateName, typeof Code2> = {
    syntax: Code2,
    security: Shield,
    architecture: Layers,
    tests: TestTube2,
  };

  if (compact) {
    return (
      <div className={cn("flex items-center gap-1", className)}>
        {gateOrder.map((gateName) => {
          const gate = gates.find((g) => g.gateName === gateName);
          const status = gate?.status || "pending";
          const Icon = gateIcons[gateName];

          return (
            <TooltipProvider key={gateName}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div
                    className={cn(
                      "p-1 rounded",
                      status === "passed" && "bg-green-100 dark:bg-green-900/30",
                      status === "failed" && "bg-red-100 dark:bg-red-900/30",
                      status === "running" && "bg-blue-100 dark:bg-blue-900/30",
                      status === "pending" && "bg-gray-100 dark:bg-gray-800/30"
                    )}
                  >
                    <Icon
                      className={cn(
                        "h-4 w-4",
                        status === "passed" && "text-green-500",
                        status === "failed" && "text-red-500",
                        status === "running" && "text-blue-500 animate-pulse",
                        status === "pending" && "text-gray-400"
                      )}
                    />
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>
                    {vietnamese
                      ? GATE_CONFIGS[gateName].vietnameseLabel
                      : GATE_CONFIGS[gateName].label}
                    : {status}
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          );
        })}
      </div>
    );
  }

  return (
    <div className={cn("grid grid-cols-4 gap-2", className)}>
      {gateOrder.map((gateName) => {
        const gate = gates.find((g) => g.gateName === gateName);
        const status = gate?.status || "pending";
        const Icon = gateIcons[gateName];
        const config = GATE_CONFIGS[gateName];

        return (
          <div
            key={gateName}
            className={cn(
              "flex flex-col items-center gap-1 p-2 rounded-lg text-center",
              status === "passed" && "bg-green-100 dark:bg-green-900/30",
              status === "failed" && "bg-red-100 dark:bg-red-900/30",
              status === "running" && "bg-blue-100 dark:bg-blue-900/30",
              status === "pending" && "bg-gray-100 dark:bg-gray-800/30"
            )}
          >
            <Icon
              className={cn(
                "h-5 w-5",
                status === "passed" && "text-green-500",
                status === "failed" && "text-red-500",
                status === "running" && "text-blue-500 animate-pulse",
                status === "pending" && "text-gray-400"
              )}
            />
            <span className="text-xs font-medium truncate w-full">
              {vietnamese ? config.vietnameseLabel : config.label}
            </span>
            {status === "passed" && (
              <CheckCircle2 className="h-3 w-3 text-green-500" />
            )}
            {status === "failed" && (
              <XCircle className="h-3 w-3 text-red-500" />
            )}
          </div>
        );
      })}
    </div>
  );
}

export function InlineQualityBadge({
  result,
  vietnamese = false,
  showIssueCount = true,
  className,
}: InlineQualityBadgeProps) {
  const score = useMemo(() => calculateScore(result), [result]);
  const grade = useMemo(() => getGrade(score), [score]);
  const totalIssues = useMemo(() => getTotalIssues(result), [result]);
  const criticalCount = useMemo(() => getCriticalCount(result), [result]);

  const passedGates = result.gates.filter((g) => g.status === "passed").length;
  const totalGates = result.gates.length;

  return (
    <div className={cn("inline-flex items-center gap-2", className)}>
      {/* Grade Badge */}
      <Badge
        variant="outline"
        className={cn("font-bold", grade.color)}
      >
        {grade.letter}
      </Badge>

      {/* Score */}
      <span className="text-sm font-medium">{score}/100</span>

      {/* Gates */}
      <div className="flex items-center gap-1 text-sm text-muted-foreground">
        <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
        <span>{passedGates}/{totalGates}</span>
      </div>

      {/* Issues */}
      {showIssueCount && totalIssues > 0 && (
        <Badge
          variant={criticalCount > 0 ? "destructive" : "secondary"}
          className="text-xs"
        >
          {totalIssues} {vietnamese ? "lỗi" : "issues"}
        </Badge>
      )}
    </div>
  );
}

export function CompactQualitySummary({
  result,
  vietnamese = false,
  onClick,
  className,
}: CompactQualitySummaryProps) {
  const score = useMemo(() => calculateScore(result), [result]);
  const grade = useMemo(() => getGrade(score), [score]);
  const totalIssues = useMemo(() => getTotalIssues(result), [result]);

  const passedGates = result.gates.filter((g) => g.status === "passed").length;
  const totalGates = result.gates.length;
  const allPassed = passedGates === totalGates;

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-center gap-4 p-3 rounded-lg border transition-colors",
        "hover:bg-muted/50 focus:outline-none focus:ring-2 focus:ring-ring",
        allPassed ? "border-green-200 dark:border-green-800" : "border-border",
        className
      )}
    >
      {/* Score Circle */}
      <div
        className={cn(
          "flex-shrink-0 flex items-center justify-center",
          "w-12 h-12 rounded-full",
          grade.bgColor
        )}
      >
        <span className={cn("text-xl font-bold", grade.color)}>
          {grade.letter}
        </span>
      </div>

      {/* Details */}
      <div className="flex-1 text-left min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium">{score}/100</span>
          {allPassed ? (
            <Badge variant="outline" className="text-green-600 border-green-500 text-xs">
              {vietnamese ? "Đạt" : "Passed"}
            </Badge>
          ) : (
            <Badge variant="outline" className="text-red-600 border-red-500 text-xs">
              {vietnamese ? "Thất bại" : "Failed"}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground">
          <span>{passedGates}/{totalGates} {vietnamese ? "cổng" : "gates"}</span>
          {totalIssues > 0 && (
            <span className="text-orange-500">
              {totalIssues} {vietnamese ? "vấn đề" : "issues"}
            </span>
          )}
        </div>
      </div>

      {/* Gate Icons */}
      <GateStatusSummary gates={result.gates} vietnamese={vietnamese} compact />

      {/* Arrow */}
      <ChevronRight className="h-5 w-5 text-muted-foreground flex-shrink-0" />
    </button>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function QualitySummaryPanel({
  result,
  vietnamese = false,
  trend,
  previousScore,
  onViewDetails,
  className,
}: QualitySummaryPanelProps) {
  const score = useMemo(() => calculateScore(result), [result]);
  const grade = useMemo(() => getGrade(score), [score]);
  const totalIssues = useMemo(() => getTotalIssues(result), [result]);
  const criticalCount = useMemo(() => getCriticalCount(result), [result]);

  const passedGates = result.gates.filter((g) => g.status === "passed").length;
  const failedGates = result.gates.filter((g) => g.status === "failed").length;
  const totalGates = result.gates.length;
  const allPassed = passedGates === totalGates;

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className={cn("pb-2", grade.bgColor)}>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {allPassed ? (
              <FileCheck className="h-5 w-5 text-green-500" />
            ) : (
              <FileWarning className="h-5 w-5 text-red-500" />
            )}
            {vietnamese ? "Tóm tắt chất lượng" : "Quality Summary"}
          </CardTitle>
          {onViewDetails && (
            <Button variant="ghost" size="sm" onClick={onViewDetails}>
              {vietnamese ? "Xem chi tiết" : "View Details"}
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-4">
        {/* Score Section */}
        <div className="flex items-center gap-4 mb-4">
          <div
            className={cn(
              "flex items-center justify-center",
              "w-16 h-16 rounded-full",
              grade.bgColor
            )}
          >
            <span className={cn("text-3xl font-bold", grade.color)}>
              {grade.letter}
            </span>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{score}</span>
              <span className="text-lg text-muted-foreground">/100</span>
              {trend && previousScore !== undefined && (
                <QualityTrendIndicator
                  currentScore={score}
                  previousScore={previousScore}
                  vietnamese={vietnamese}
                  className="ml-2"
                />
              )}
            </div>
            <Progress value={score} className="h-2 mt-2" />
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          {/* Gates Passed */}
          <div className="text-center p-2 rounded-lg bg-muted/30">
            <div className="flex items-center justify-center gap-1 text-green-600 mb-1">
              <CheckCircle2 className="h-4 w-4" />
              <span className="text-lg font-bold">{passedGates}</span>
            </div>
            <span className="text-xs text-muted-foreground">
              {vietnamese ? "Cổng đạt" : "Passed"}
            </span>
          </div>

          {/* Gates Failed */}
          <div className="text-center p-2 rounded-lg bg-muted/30">
            <div className="flex items-center justify-center gap-1 text-red-600 mb-1">
              <XCircle className="h-4 w-4" />
              <span className="text-lg font-bold">{failedGates}</span>
            </div>
            <span className="text-xs text-muted-foreground">
              {vietnamese ? "Thất bại" : "Failed"}
            </span>
          </div>

          {/* Total Issues */}
          <div className="text-center p-2 rounded-lg bg-muted/30">
            <div className="flex items-center justify-center gap-1 text-orange-600 mb-1">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-lg font-bold">{totalIssues}</span>
            </div>
            <span className="text-xs text-muted-foreground">
              {vietnamese ? "Vấn đề" : "Issues"}
            </span>
          </div>
        </div>

        {/* Critical Alert */}
        {criticalCount > 0 && (
          <div className="flex items-center gap-2 p-2 rounded-lg bg-red-100 dark:bg-red-900/30 mb-4">
            <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
            <span className="text-sm text-red-600 font-medium">
              {criticalCount} {vietnamese ? "lỗ hổng nghiêm trọng cần xử lý ngay" : "critical vulnerabilities require immediate attention"}
            </span>
          </div>
        )}

        {/* Gate Status */}
        <GateStatusSummary
          gates={result.gates}
          vietnamese={vietnamese}
          compact={false}
        />

        {/* Duration */}
        <div className="flex items-center justify-center gap-2 mt-4 text-sm text-muted-foreground">
          <Clock className="h-4 w-4" />
          <span>
            {vietnamese ? "Thời gian:" : "Duration:"} {(result.totalDurationMs / 1000).toFixed(1)}s
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Export
// ============================================================================

export default QualitySummaryPanel;
