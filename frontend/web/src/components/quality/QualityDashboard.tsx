/**
 * =========================================================================
 * QualityDashboard - Overall Quality Metrics Dashboard
 * SDLC Orchestrator - Sprint 55 Day 2
 *
 * Version: 1.0.0
 * Date: December 27, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 * Authority: Frontend Team + CTO Approved
 *
 * Purpose:
 * - Display overall quality score and grade
 * - Show gate progress visualization
 * - Summarize issues by severity
 * - Provide quality metrics overview
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
  Timer,
  TrendingUp,
  TrendingDown,
  Minus,
  Shield,
  Code2,
  Layers,
  TestTube2,
  Award,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { GatePipeline } from "./GatePipeline";
import { GateStatusBadge } from "./GateStatusBadge";
import type {
  PipelineResult,
  GateResult,
  GateName,
} from "@/types/quality";
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

interface QualityDashboardProps {
  /** Pipeline result */
  result?: PipelineResult;
  /** Individual gate results (for streaming) */
  gates?: GateResult[];
  /** Current running gate */
  currentGate?: GateName;
  /** Use Vietnamese labels */
  vietnamese?: boolean;
  /** Show detailed breakdown */
  showDetails?: boolean;
  /** Gate click handler */
  onGateClick?: (gateName: GateName) => void;
  /** Additional class name */
  className?: string;
}

interface QualityGrade {
  letter: string;
  label: string;
  vietnameseLabel: string;
  color: string;
  bgColor: string;
  borderColor: string;
}

interface IssueSummary {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
  total: number;
}

// ============================================================================
// Quality Score Calculation
// ============================================================================

function calculateQualityScore(gates: GateResult[]): number {
  if (gates.length === 0) return 0;

  let score = 100;
  let penalty = 0;

  for (const gate of gates) {
    if (gate.status === "failed") {
      // Major penalty for failed gates
      penalty += 25;
    } else if (gate.status === "skipped") {
      // Minor penalty for skipped gates
      penalty += 5;
    }

    // Additional penalties based on issue severity
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
        gate.details.testsFailed /
        Math.max(gate.details.testsRun, 1);
      penalty += failRate * 15;
    }

    if (isArchitectureResult(gate.details)) {
      penalty += gate.details.issues.length * 3;
    }
  }

  score = Math.max(0, Math.min(100, score - penalty));
  return Math.round(score);
}

function getQualityGrade(score: number): QualityGrade {
  if (score >= 90) {
    return {
      letter: "A",
      label: "Excellent",
      vietnameseLabel: "Xuất sắc",
      color: "text-green-600",
      bgColor: "bg-green-100 dark:bg-green-900/30",
      borderColor: "border-green-500",
    };
  }
  if (score >= 80) {
    return {
      letter: "B",
      label: "Good",
      vietnameseLabel: "Tốt",
      color: "text-blue-600",
      bgColor: "bg-blue-100 dark:bg-blue-900/30",
      borderColor: "border-blue-500",
    };
  }
  if (score >= 70) {
    return {
      letter: "C",
      label: "Fair",
      vietnameseLabel: "Khá",
      color: "text-yellow-600",
      bgColor: "bg-yellow-100 dark:bg-yellow-900/30",
      borderColor: "border-yellow-500",
    };
  }
  if (score >= 60) {
    return {
      letter: "D",
      label: "Poor",
      vietnameseLabel: "Yếu",
      color: "text-orange-600",
      bgColor: "bg-orange-100 dark:bg-orange-900/30",
      borderColor: "border-orange-500",
    };
  }
  return {
    letter: "F",
    label: "Critical",
    vietnameseLabel: "Nghiêm trọng",
    color: "text-red-600",
    bgColor: "bg-red-100 dark:bg-red-900/30",
    borderColor: "border-red-500",
  };
}

function getIssueSummary(gates: GateResult[]): IssueSummary {
  const summary: IssueSummary = {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    info: 0,
    total: 0,
  };

  for (const gate of gates) {
    if (isSecurityResult(gate.details)) {
      summary.critical += gate.details.criticalCount;
      summary.high += gate.details.highCount;
      summary.medium += gate.details.mediumCount;
      summary.low += gate.details.lowCount;
    }

    if (isSyntaxResult(gate.details)) {
      summary.high += gate.details.issues.length;
    }

    if (isArchitectureResult(gate.details)) {
      summary.medium += gate.details.issues.length;
    }

    if (isTestResult(gate.details)) {
      summary.high += gate.details.testsFailed;
    }
  }

  summary.total =
    summary.critical + summary.high + summary.medium + summary.low + summary.info;

  return summary;
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  return `${minutes}m ${seconds}s`;
}

// ============================================================================
// Sub-Components
// ============================================================================

interface QualityScoreCardProps {
  score: number;
  grade: QualityGrade;
  vietnamese?: boolean;
  trend?: "up" | "down" | "stable";
  previousScore?: number;
}

function QualityScoreCard({
  score,
  grade,
  vietnamese = false,
  trend,
  previousScore,
}: QualityScoreCardProps) {
  const TrendIcon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;
  const trendColor =
    trend === "up"
      ? "text-green-500"
      : trend === "down"
        ? "text-red-500"
        : "text-gray-400";

  return (
    <Card className={cn("relative overflow-hidden", grade.bgColor)}>
      <div className="absolute top-0 right-0 w-32 h-32 -mr-8 -mt-8 opacity-10">
        <Award className="w-full h-full" />
      </div>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {vietnamese ? "Điểm chất lượng" : "Quality Score"}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-end gap-3">
          <div
            className={cn(
              "text-5xl font-bold",
              grade.color
            )}
          >
            {score}
          </div>
          <div className="flex flex-col mb-1">
            <Badge
              variant="outline"
              className={cn("text-lg px-3 py-0.5", grade.color, grade.borderColor)}
            >
              {grade.letter}
            </Badge>
            <span className="text-sm text-muted-foreground mt-1">
              {vietnamese ? grade.vietnameseLabel : grade.label}
            </span>
          </div>
          {trend && (
            <div className={cn("flex items-center gap-1 ml-auto", trendColor)}>
              <TrendIcon className="h-4 w-4" />
              {previousScore !== undefined && (
                <span className="text-sm">
                  {trend === "up" ? "+" : trend === "down" ? "-" : ""}
                  {Math.abs(score - previousScore)}
                </span>
              )}
            </div>
          )}
        </div>
        <Progress
          value={score}
          className="h-2 mt-4"
        />
      </CardContent>
    </Card>
  );
}

interface IssueSummaryCardProps {
  summary: IssueSummary;
  vietnamese?: boolean;
}

function IssueSummaryCard({ summary, vietnamese = false }: IssueSummaryCardProps) {
  const severities: Array<{
    key: keyof IssueSummary;
    label: string;
    vietnameseLabel: string;
    icon: typeof AlertCircle;
    color: string;
    bgColor: string;
  }> = [
    {
      key: "critical",
      label: "Critical",
      vietnameseLabel: "Nghiêm trọng",
      icon: AlertCircle,
      color: "text-red-600",
      bgColor: "bg-red-100 dark:bg-red-900/30",
    },
    {
      key: "high",
      label: "High",
      vietnameseLabel: "Cao",
      icon: AlertTriangle,
      color: "text-orange-600",
      bgColor: "bg-orange-100 dark:bg-orange-900/30",
    },
    {
      key: "medium",
      label: "Medium",
      vietnameseLabel: "Trung bình",
      icon: AlertTriangle,
      color: "text-yellow-600",
      bgColor: "bg-yellow-100 dark:bg-yellow-900/30",
    },
    {
      key: "low",
      label: "Low",
      vietnameseLabel: "Thấp",
      icon: AlertCircle,
      color: "text-blue-600",
      bgColor: "bg-blue-100 dark:bg-blue-900/30",
    },
  ];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          {vietnamese ? "Tóm tắt vấn đề" : "Issue Summary"}
        </CardTitle>
        <CardDescription>
          {summary.total === 0
            ? vietnamese
              ? "Không có vấn đề nào được phát hiện"
              : "No issues detected"
            : vietnamese
              ? `${summary.total} vấn đề được phát hiện`
              : `${summary.total} issues detected`}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          {severities.map((severity) => {
            const count = summary[severity.key];
            const Icon = severity.icon;

            return (
              <div
                key={severity.key}
                className={cn(
                  "flex items-center gap-2 p-2 rounded-lg",
                  count > 0 ? severity.bgColor : "bg-muted/30"
                )}
              >
                <Icon
                  className={cn(
                    "h-4 w-4",
                    count > 0 ? severity.color : "text-muted-foreground"
                  )}
                />
                <div className="flex-1">
                  <div className="text-xs text-muted-foreground">
                    {vietnamese ? severity.vietnameseLabel : severity.label}
                  </div>
                  <div
                    className={cn(
                      "text-lg font-semibold",
                      count > 0 ? severity.color : "text-muted-foreground"
                    )}
                  >
                    {count}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

interface GateProgressCardProps {
  gates: GateResult[];
  currentGate?: GateName;
  vietnamese?: boolean;
  onGateClick?: (gateName: GateName) => void;
}

function GateProgressCard({
  gates,
  currentGate,
  vietnamese = false,
  onGateClick,
}: GateProgressCardProps) {
  const gateOrder: GateName[] = ["syntax", "security", "architecture", "tests"];

  const passedCount = gates.filter((g) => g.status === "passed").length;
  const failedCount = gates.filter((g) => g.status === "failed").length;
  const runningCount = gates.filter((g) => g.status === "running").length;
  const totalCount = gateOrder.length;

  const progress = (passedCount / totalCount) * 100;
  const isComplete = passedCount === totalCount;
  const hasFailed = failedCount > 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            {isComplete ? (
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            ) : hasFailed ? (
              <XCircle className="h-4 w-4 text-red-500" />
            ) : runningCount > 0 ? (
              <Clock className="h-4 w-4 text-blue-500 animate-pulse" />
            ) : (
              <Clock className="h-4 w-4 text-gray-400" />
            )}
            {vietnamese ? "Tiến độ cổng" : "Gate Progress"}
          </CardTitle>
          <Badge
            variant={isComplete ? "default" : hasFailed ? "destructive" : "secondary"}
          >
            {passedCount}/{totalCount}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <Progress value={progress} className="h-2 mb-4" />
        <div className="space-y-2">
          {gateOrder.map((gateName) => {
            const gateResult = gates.find((g) => g.gateName === gateName);
            const status = gateResult?.status || (currentGate === gateName ? "running" : "pending");
            const config = GATE_CONFIGS[gateName];
            const Icon =
              gateName === "syntax"
                ? Code2
                : gateName === "security"
                  ? Shield
                  : gateName === "architecture"
                    ? Layers
                    : TestTube2;

            return (
              <button
                key={gateName}
                onClick={() => onGateClick?.(gateName)}
                className={cn(
                  "w-full flex items-center gap-3 p-2 rounded-lg transition-colors",
                  "hover:bg-muted/50 focus:outline-none focus:ring-2 focus:ring-ring",
                  status === "passed" && "bg-green-50 dark:bg-green-900/10",
                  status === "failed" && "bg-red-50 dark:bg-red-900/10",
                  status === "running" && "bg-blue-50 dark:bg-blue-900/10"
                )}
              >
                <Icon
                  className={cn(
                    "h-4 w-4",
                    status === "passed" && "text-green-500",
                    status === "failed" && "text-red-500",
                    status === "running" && "text-blue-500 animate-pulse",
                    status === "pending" && "text-gray-400",
                    status === "skipped" && "text-yellow-500"
                  )}
                />
                <span className="flex-1 text-left text-sm font-medium">
                  {vietnamese ? config.vietnameseLabel : config.label}
                </span>
                <GateStatusBadge
                  gateName={gateName}
                  status={status}
                  durationMs={gateResult?.durationMs}
                  compact
                  vietnamese={vietnamese}
                />
              </button>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

interface DurationCardProps {
  totalDuration: number;
  gates: GateResult[];
  vietnamese?: boolean;
}

function DurationCard({ totalDuration, gates, vietnamese = false }: DurationCardProps) {
  const gateOrder: GateName[] = ["syntax", "security", "architecture", "tests"];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Timer className="h-4 w-4" />
          {vietnamese ? "Thời gian thực hiện" : "Execution Time"}
        </CardTitle>
        <CardDescription className="text-2xl font-bold">
          {formatDuration(totalDuration)}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {gateOrder.map((gateName) => {
            const gateResult = gates.find((g) => g.gateName === gateName);
            const duration = gateResult?.durationMs || 0;
            const percentage = totalDuration > 0 ? (duration / totalDuration) * 100 : 0;
            const config = GATE_CONFIGS[gateName];

            return (
              <div key={gateName} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">
                    {vietnamese ? config.vietnameseLabel : config.label}
                  </span>
                  <span className="font-mono">
                    {duration > 0 ? formatDuration(duration) : "-"}
                  </span>
                </div>
                <Progress value={percentage} className="h-1" />
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function QualityDashboard({
  result,
  gates = [],
  currentGate,
  vietnamese = false,
  showDetails = true,
  onGateClick,
  className,
}: QualityDashboardProps) {
  const effectiveGates = result?.gates || gates;

  const score = useMemo(
    () => calculateQualityScore(effectiveGates),
    [effectiveGates]
  );

  const grade = useMemo(() => getQualityGrade(score), [score]);

  const issueSummary = useMemo(
    () => getIssueSummary(effectiveGates),
    [effectiveGates]
  );

  const totalDuration = useMemo(() => {
    if (result) return result.totalDurationMs;
    return effectiveGates.reduce((sum, g) => sum + (g.durationMs || 0), 0);
  }, [result, effectiveGates]);

  const hasData = effectiveGates.length > 0;

  if (!hasData) {
    return (
      <Card className={className}>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Clock className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold">
            {vietnamese ? "Chưa có dữ liệu chất lượng" : "No Quality Data"}
          </h3>
          <p className="text-sm text-muted-foreground text-center max-w-sm mt-2">
            {vietnamese
              ? "Chạy đường ống chất lượng để xem kết quả ở đây."
              : "Run the quality pipeline to see results here."}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Top Row: Score and Issue Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <QualityScoreCard
          score={score}
          grade={grade}
          vietnamese={vietnamese}
        />
        <IssueSummaryCard
          summary={issueSummary}
          vietnamese={vietnamese}
        />
      </div>

      {/* Middle Row: Gate Progress and Duration */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <GateProgressCard
          gates={effectiveGates}
          currentGate={currentGate}
          vietnamese={vietnamese}
          onGateClick={onGateClick}
        />
        <DurationCard
          totalDuration={totalDuration}
          gates={effectiveGates}
          vietnamese={vietnamese}
        />
      </div>

      {/* Bottom Row: Full Pipeline (if showDetails) */}
      {showDetails && (
        <GatePipeline
          result={result}
          gates={effectiveGates}
          currentGate={currentGate}
          vietnamese={vietnamese}
          showDetails={true}
          onGateClick={onGateClick}
        />
      )}
    </div>
  );
}

// ============================================================================
// Export
// ============================================================================

export default QualityDashboard;
export { QualityScoreCard, IssueSummaryCard, GateProgressCard, DurationCard };
export type { QualityGrade, IssueSummary };
