/**
 * =========================================================================
 * FileQualityIndicator - Per-File Quality Status Badge
 * SDLC Orchestrator - Sprint 55 Day 3
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 *
 * Purpose:
 * - Display quality status indicator for individual files
 * - Show issue count badges per gate
 * - Indicate severity levels with color coding
 * - Support compact and detailed views
 *
 * References:
 * - docs/02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md
 * =========================================================================
 */

import React from "react";
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Code2,
  Shield,
  Layers,
  TestTube2,
  MinusCircle,
  Info,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type {
  GateName,
  Severity,
  PipelineResult,
  SyntaxIssue,
  SecurityIssue,
  ArchitectureIssue,
} from "@/types/quality";
import {
  isSyntaxResult,
  isSecurityResult,
  isArchitectureResult,
} from "@/types/quality";

// ============================================================================
// Types
// ============================================================================

export interface FileQualityStatus {
  file: string;
  hasIssues: boolean;
  issueCount: number;
  highestSeverity: Severity | null;
  issuesByGate: {
    syntax: number;
    security: number;
    architecture: number;
    tests: number;
  };
  securitySeverities: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

export interface FileQualityIndicatorProps {
  /** File path to show quality for */
  file: string;
  /** Pipeline result to extract file issues from */
  pipelineResult?: PipelineResult;
  /** Pre-computed file quality status */
  status?: FileQualityStatus;
  /** Show compact indicator (icon only) */
  compact?: boolean;
  /** Show issue count badge */
  showCount?: boolean;
  /** Show gate breakdown */
  showGates?: boolean;
  /** Vietnamese mode */
  vietnamese?: boolean;
  /** Click handler */
  onClick?: (file: string) => void;
  /** Additional CSS classes */
  className?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Extract file quality status from pipeline result
 */
export function getFileQualityStatus(
  file: string,
  pipelineResult: PipelineResult
): FileQualityStatus {
  const issuesByGate = {
    syntax: 0,
    security: 0,
    architecture: 0,
    tests: 0,
  };

  const securitySeverities = {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  };

  let highestSeverity: Severity | null = null;

  for (const gate of pipelineResult.gates) {
    const details = gate.details;

    if (isSyntaxResult(details)) {
      const fileIssues = details.issues.filter((i) => i.file === file);
      issuesByGate.syntax = fileIssues.length;
    } else if (isSecurityResult(details)) {
      const fileIssues = details.issues.filter((i) => i.file === file);
      issuesByGate.security = fileIssues.length;

      for (const issue of fileIssues) {
        if (issue.severity === "critical") {
          securitySeverities.critical++;
          if (!highestSeverity || highestSeverity !== "critical") {
            highestSeverity = "critical";
          }
        } else if (issue.severity === "high") {
          securitySeverities.high++;
          if (!highestSeverity || (highestSeverity !== "critical")) {
            highestSeverity = "high";
          }
        } else if (issue.severity === "medium") {
          securitySeverities.medium++;
          if (!highestSeverity || !["critical", "high"].includes(highestSeverity)) {
            highestSeverity = "medium";
          }
        } else if (issue.severity === "low") {
          securitySeverities.low++;
          if (!highestSeverity) {
            highestSeverity = "low";
          }
        }
      }
    } else if (isArchitectureResult(details)) {
      const fileIssues = details.issues.filter((i) => i.file === file);
      issuesByGate.architecture = fileIssues.length;
    }
  }

  const issueCount =
    issuesByGate.syntax +
    issuesByGate.security +
    issuesByGate.architecture +
    issuesByGate.tests;

  return {
    file,
    hasIssues: issueCount > 0,
    issueCount,
    highestSeverity,
    issuesByGate,
    securitySeverities,
  };
}

/**
 * Get all files with issues from pipeline result
 */
export function getFilesWithIssues(
  pipelineResult: PipelineResult
): FileQualityStatus[] {
  const fileMap = new Map<string, FileQualityStatus>();

  for (const gate of pipelineResult.gates) {
    const details = gate.details;
    let issues: Array<SyntaxIssue | SecurityIssue | ArchitectureIssue> = [];

    if (isSyntaxResult(details)) {
      issues = details.issues;
    } else if (isSecurityResult(details)) {
      issues = details.issues;
    } else if (isArchitectureResult(details)) {
      issues = details.issues;
    }

    for (const issue of issues) {
      if (!fileMap.has(issue.file)) {
        fileMap.set(issue.file, getFileQualityStatus(issue.file, pipelineResult));
      }
    }
  }

  return Array.from(fileMap.values()).sort((a, b) => {
    // Sort by severity first (critical > high > medium > low > null)
    const severityOrder: Record<string, number> = {
      critical: 0,
      high: 1,
      medium: 2,
      low: 3,
      info: 4,
    };
    const aSev = a.highestSeverity ? (severityOrder[a.highestSeverity] ?? 5) : 5;
    const bSev = b.highestSeverity ? (severityOrder[b.highestSeverity] ?? 5) : 5;
    if (aSev !== bSev) return aSev - bSev;

    // Then by issue count
    return b.issueCount - a.issueCount;
  });
}

// ============================================================================
// Severity Icon Component
// ============================================================================

const SeverityIcon: React.FC<{
  severity: Severity | null;
  hasIssues: boolean;
  className?: string;
}> = ({ severity, hasIssues, className }) => {
  if (!hasIssues) {
    return (
      <CheckCircle2
        className={cn("h-4 w-4 text-green-500", className)}
        aria-label="No issues"
      />
    );
  }

  switch (severity) {
    case "critical":
      return (
        <AlertCircle
          className={cn("h-4 w-4 text-red-600", className)}
          aria-label="Critical issues"
        />
      );
    case "high":
      return (
        <AlertTriangle
          className={cn("h-4 w-4 text-orange-500", className)}
          aria-label="High severity issues"
        />
      );
    case "medium":
      return (
        <AlertTriangle
          className={cn("h-4 w-4 text-yellow-500", className)}
          aria-label="Medium severity issues"
        />
      );
    case "low":
      return (
        <Info
          className={cn("h-4 w-4 text-blue-500", className)}
          aria-label="Low severity issues"
        />
      );
    default:
      return (
        <MinusCircle
          className={cn("h-4 w-4 text-gray-500", className)}
          aria-label="Issues found"
        />
      );
  }
};

// ============================================================================
// Gate Icon Component
// ============================================================================

const GateIcon: React.FC<{ gate: GateName; className?: string }> = ({
  gate,
  className,
}) => {
  const iconClass = cn("h-3 w-3", className);

  switch (gate) {
    case "syntax":
      return <Code2 className={iconClass} />;
    case "security":
      return <Shield className={iconClass} />;
    case "architecture":
      return <Layers className={iconClass} />;
    case "tests":
      return <TestTube2 className={iconClass} />;
  }
};

// ============================================================================
// Main Component
// ============================================================================

export const FileQualityIndicator: React.FC<FileQualityIndicatorProps> = ({
  file,
  pipelineResult,
  status: providedStatus,
  compact = false,
  showCount = true,
  showGates = false,
  vietnamese = false,
  onClick,
  className,
}) => {
  // Get status from props or compute from pipeline result
  const status = providedStatus ||
    (pipelineResult ? getFileQualityStatus(file, pipelineResult) : null);

  if (!status) {
    return (
      <div className={cn("flex items-center gap-1", className)}>
        <MinusCircle className="h-4 w-4 text-gray-400" />
        {!compact && (
          <span className="text-xs text-gray-500">
            {vietnamese ? "Chưa kiểm tra" : "Not checked"}
          </span>
        )}
      </div>
    );
  }

  const handleClick = () => {
    if (onClick) {
      onClick(file);
    }
  };

  // Compact mode: icon only with tooltip
  if (compact) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={handleClick}
              className={cn(
                "inline-flex items-center gap-1 rounded p-0.5 hover:bg-gray-100 dark:hover:bg-gray-800",
                onClick && "cursor-pointer",
                className
              )}
              aria-label={`Quality status for ${file}`}
            >
              <SeverityIcon
                severity={status.highestSeverity}
                hasIssues={status.hasIssues}
              />
              {showCount && status.issueCount > 0 && (
                <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                  {status.issueCount}
                </span>
              )}
            </button>
          </TooltipTrigger>
          <TooltipContent side="right" className="max-w-xs">
            <div className="space-y-1">
              <p className="font-medium">
                {status.hasIssues
                  ? vietnamese
                    ? `${status.issueCount} vấn đề`
                    : `${status.issueCount} issue${status.issueCount > 1 ? "s" : ""}`
                  : vietnamese
                  ? "Không có vấn đề"
                  : "No issues"}
              </p>
              {status.hasIssues && (
                <div className="flex flex-wrap gap-1">
                  {status.issuesByGate.syntax > 0 && (
                    <Badge variant="outline" className="text-xs">
                      <GateIcon gate="syntax" className="mr-1" />
                      {status.issuesByGate.syntax}
                    </Badge>
                  )}
                  {status.issuesByGate.security > 0 && (
                    <Badge variant="outline" className="text-xs">
                      <GateIcon gate="security" className="mr-1" />
                      {status.issuesByGate.security}
                    </Badge>
                  )}
                  {status.issuesByGate.architecture > 0 && (
                    <Badge variant="outline" className="text-xs">
                      <GateIcon gate="architecture" className="mr-1" />
                      {status.issuesByGate.architecture}
                    </Badge>
                  )}
                </div>
              )}
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Full mode: icon + count + optional gate breakdown
  return (
    <div
      role={onClick ? "button" : undefined}
      onClick={handleClick}
      className={cn(
        "flex items-center gap-2",
        onClick && "cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded p-1",
        className
      )}
    >
      <SeverityIcon
        severity={status.highestSeverity}
        hasIssues={status.hasIssues}
      />

      {showCount && (
        <span
          className={cn(
            "text-sm",
            status.hasIssues
              ? "font-medium text-gray-700 dark:text-gray-300"
              : "text-gray-500"
          )}
        >
          {status.hasIssues
            ? vietnamese
              ? `${status.issueCount} vấn đề`
              : `${status.issueCount} issue${status.issueCount > 1 ? "s" : ""}`
            : vietnamese
            ? "Đạt"
            : "Passed"}
        </span>
      )}

      {showGates && status.hasIssues && (
        <div className="flex items-center gap-1 ml-2">
          {status.issuesByGate.syntax > 0 && (
            <Badge
              variant="outline"
              className="text-xs px-1.5 py-0 h-5"
            >
              <GateIcon gate="syntax" className="mr-0.5" />
              {status.issuesByGate.syntax}
            </Badge>
          )}
          {status.issuesByGate.security > 0 && (
            <Badge
              variant={
                status.securitySeverities.critical > 0
                  ? "destructive"
                  : "outline"
              }
              className="text-xs px-1.5 py-0 h-5"
            >
              <GateIcon gate="security" className="mr-0.5" />
              {status.issuesByGate.security}
            </Badge>
          )}
          {status.issuesByGate.architecture > 0 && (
            <Badge
              variant="outline"
              className="text-xs px-1.5 py-0 h-5"
            >
              <GateIcon gate="architecture" className="mr-0.5" />
              {status.issuesByGate.architecture}
            </Badge>
          )}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// File List with Quality Indicators
// ============================================================================

export interface FileQualityListProps {
  /** List of files to show */
  files: string[];
  /** Pipeline result for quality data */
  pipelineResult: PipelineResult;
  /** Currently selected file */
  selectedFile?: string;
  /** File selection handler */
  onFileSelect?: (file: string) => void;
  /** Show only files with issues */
  showOnlyIssues?: boolean;
  /** Vietnamese mode */
  vietnamese?: boolean;
  /** Additional CSS classes */
  className?: string;
}

export const FileQualityList: React.FC<FileQualityListProps> = ({
  files,
  pipelineResult,
  selectedFile,
  onFileSelect,
  showOnlyIssues = false,
  vietnamese = false,
  className,
}) => {
  // Get quality status for each file
  const fileStatuses = files.map((file) => ({
    file,
    status: getFileQualityStatus(file, pipelineResult),
  }));

  // Filter if needed
  const displayFiles = showOnlyIssues
    ? fileStatuses.filter((f) => f.status.hasIssues)
    : fileStatuses;

  // Sort by severity/issue count
  displayFiles.sort((a, b) => {
    const severityOrder: Record<string, number> = {
      critical: 0,
      high: 1,
      medium: 2,
      low: 3,
      info: 4,
    };
    const aSev = a.status.highestSeverity
      ? (severityOrder[a.status.highestSeverity] ?? 5)
      : 5;
    const bSev = b.status.highestSeverity
      ? (severityOrder[b.status.highestSeverity] ?? 5)
      : 5;
    if (aSev !== bSev) return aSev - bSev;
    return b.status.issueCount - a.status.issueCount;
  });

  if (displayFiles.length === 0) {
    return (
      <div
        className={cn(
          "text-center py-4 text-gray-500",
          className
        )}
      >
        {showOnlyIssues
          ? vietnamese
            ? "Không có file nào có vấn đề"
            : "No files with issues"
          : vietnamese
          ? "Không có file nào"
          : "No files"}
      </div>
    );
  }

  return (
    <div className={cn("space-y-1", className)}>
      {displayFiles.map(({ file, status }) => (
        <div
          key={file}
          role="button"
          onClick={() => onFileSelect?.(file)}
          className={cn(
            "flex items-center justify-between px-2 py-1.5 rounded",
            "hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer",
            selectedFile === file && "bg-blue-50 dark:bg-blue-900/20"
          )}
        >
          <span
            className={cn(
              "text-sm truncate flex-1 mr-2",
              selectedFile === file
                ? "text-blue-700 dark:text-blue-300 font-medium"
                : "text-gray-700 dark:text-gray-300"
            )}
            title={file}
          >
            {file.split("/").pop()}
          </span>
          <FileQualityIndicator
            file={file}
            status={status}
            compact
            showCount
            vietnamese={vietnamese}
          />
        </div>
      ))}
    </div>
  );
};

export default FileQualityIndicator;
