/**
 * =========================================================================
 * GateStatusBadge - Status Badge for Quality Gates
 * SDLC Orchestrator - Sprint 55 Day 1
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 * Authority: Frontend Team + CTO Approved
 *
 * Purpose:
 * - Display gate status with icon and color
 * - Show progress indicator for running gates
 * - Animate status transitions
 * - Support compact and full modes
 *
 * References:
 * - docs/02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md
 * =========================================================================
 */

import { useMemo } from "react";
import {
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  SkipForward,
  Code2,
  Shield,
  Layers,
  TestTube2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { GateName, GateStatus } from "@/types/quality";
import { GATE_CONFIGS } from "@/types/quality";

// ============================================================================
// Types
// ============================================================================

interface GateStatusBadgeProps {
  /** Gate name */
  gateName: GateName;
  /** Current status */
  status: GateStatus;
  /** Duration in milliseconds (optional) */
  durationMs?: number;
  /** Number of issues found */
  issuesCount?: number;
  /** Compact mode (icon only) */
  compact?: boolean;
  /** Show duration */
  showDuration?: boolean;
  /** Use Vietnamese labels */
  vietnamese?: boolean;
  /** Additional class name */
  className?: string;
  /** Click handler */
  onClick?: () => void;
}

// ============================================================================
// Helper Functions
// ============================================================================

function getStatusIcon(status: GateStatus) {
  switch (status) {
    case "passed":
      return CheckCircle2;
    case "failed":
      return XCircle;
    case "running":
      return Loader2;
    case "skipped":
      return SkipForward;
    case "pending":
    default:
      return Clock;
  }
}

function getGateIcon(gateName: GateName) {
  switch (gateName) {
    case "syntax":
      return Code2;
    case "security":
      return Shield;
    case "architecture":
      return Layers;
    case "tests":
      return TestTube2;
  }
}

function getStatusStyles(status: GateStatus): string {
  switch (status) {
    case "passed":
      return "bg-green-100 text-green-800 border-green-300 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800";
    case "failed":
      return "bg-red-100 text-red-800 border-red-300 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800";
    case "running":
      return "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800";
    case "skipped":
      return "bg-yellow-100 text-yellow-800 border-yellow-300 dark:bg-yellow-900/30 dark:text-yellow-400 dark:border-yellow-800";
    case "pending":
    default:
      return "bg-gray-100 text-gray-600 border-gray-300 dark:bg-gray-800/30 dark:text-gray-400 dark:border-gray-700";
  }
}

function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  return `${(ms / 1000).toFixed(1)}s`;
}

function getStatusLabel(status: GateStatus, vietnamese: boolean): string {
  const labels: Record<GateStatus, { en: string; vn: string }> = {
    pending: { en: "Pending", vn: "Chờ" },
    running: { en: "Running", vn: "Đang chạy" },
    passed: { en: "Passed", vn: "Đạt" },
    failed: { en: "Failed", vn: "Lỗi" },
    skipped: { en: "Skipped", vn: "Bỏ qua" },
  };
  return vietnamese ? labels[status].vn : labels[status].en;
}

// ============================================================================
// Component
// ============================================================================

export function GateStatusBadge({
  gateName,
  status,
  durationMs,
  issuesCount,
  compact = false,
  showDuration = true,
  vietnamese = false,
  className,
  onClick,
}: GateStatusBadgeProps) {
  const config = GATE_CONFIGS[gateName];
  const StatusIcon = getStatusIcon(status);
  const GateIcon = getGateIcon(gateName);

  const content = useMemo(() => {
    const statusStyles = getStatusStyles(status);
    const isRunning = status === "running";
    const label = vietnamese ? config.vietnameseLabel : config.label;
    const statusLabel = getStatusLabel(status, vietnamese);

    if (compact) {
      return (
        <Badge
          variant="outline"
          className={cn(
            "gap-1 px-2 py-1 cursor-pointer transition-all hover:opacity-80",
            statusStyles,
            className
          )}
          onClick={onClick}
        >
          <GateIcon className="h-3.5 w-3.5" />
          <StatusIcon
            className={cn("h-3.5 w-3.5", isRunning && "animate-spin")}
          />
        </Badge>
      );
    }

    return (
      <Badge
        variant="outline"
        className={cn(
          "gap-2 px-3 py-1.5 cursor-pointer transition-all hover:opacity-80",
          statusStyles,
          className
        )}
        onClick={onClick}
      >
        <GateIcon className="h-4 w-4" />
        <span className="font-medium">{label}</span>
        <span className="text-xs opacity-75">|</span>
        <StatusIcon
          className={cn("h-4 w-4", isRunning && "animate-spin")}
        />
        <span className="text-xs">{statusLabel}</span>
        {showDuration && durationMs !== undefined && status !== "pending" && (
          <>
            <span className="text-xs opacity-75">|</span>
            <span className="text-xs">{formatDuration(durationMs)}</span>
          </>
        )}
        {issuesCount !== undefined && issuesCount > 0 && (
          <Badge
            variant="secondary"
            className={cn(
              "ml-1 h-5 px-1.5 text-xs",
              status === "failed"
                ? "bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200"
                : "bg-yellow-200 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200"
            )}
          >
            {issuesCount}
          </Badge>
        )}
      </Badge>
    );
  }, [
    gateName,
    status,
    durationMs,
    issuesCount,
    compact,
    showDuration,
    vietnamese,
    className,
    onClick,
    config,
  ]);

  if (compact) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>{content}</TooltipTrigger>
          <TooltipContent>
            <div className="text-sm">
              <p className="font-medium">
                {vietnamese ? config.vietnameseLabel : config.label}
              </p>
              <p className="text-muted-foreground">
                {getStatusLabel(status, vietnamese)}
                {durationMs !== undefined && ` • ${formatDuration(durationMs)}`}
                {issuesCount !== undefined && issuesCount > 0 && (
                  <span className="text-red-500"> • {issuesCount} issues</span>
                )}
              </p>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return content;
}

// ============================================================================
// Variant: GateStatusIcon (Icon only)
// ============================================================================

interface GateStatusIconProps {
  status: GateStatus;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function GateStatusIcon({
  status,
  size = "md",
  className,
}: GateStatusIconProps) {
  const Icon = getStatusIcon(status);
  const isRunning = status === "running";

  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-5 w-5",
    lg: "h-6 w-6",
  };

  const colorClasses: Record<GateStatus, string> = {
    passed: "text-green-500",
    failed: "text-red-500",
    running: "text-blue-500",
    skipped: "text-yellow-500",
    pending: "text-gray-400",
  };

  return (
    <Icon
      className={cn(
        sizeClasses[size],
        colorClasses[status],
        isRunning && "animate-spin",
        className
      )}
    />
  );
}

// ============================================================================
// Export
// ============================================================================

export default GateStatusBadge;
