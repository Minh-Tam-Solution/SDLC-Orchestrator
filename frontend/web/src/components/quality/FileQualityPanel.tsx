/**
 * =========================================================================
 * FileQualityPanel - Complete Quality View for a Single File
 * SDLC Orchestrator - Sprint 55 Day 3
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 *
 * Purpose:
 * - Display comprehensive quality information for a single file
 * - Combine quality indicator, score, and issue list
 * - Support navigation to specific lines
 * - Provide summary statistics
 * - Vietnamese internationalization
 *
 * References:
 * - docs/02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md
 * =========================================================================
 */

import React, { useMemo } from "react";
import {
  FileCode,
  CheckCircle2,
  AlertTriangle,
  Code2,
  Shield,
  Layers,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import type {
  GateName,
  PipelineResult,
} from "@/types/quality";
import { GATE_CONFIGS } from "@/types/quality";
import {
  FileQualityIndicator,
  getFileQualityStatus,
  type FileQualityStatus,
} from "./FileQualityIndicator";
import { FileIssuesList, getFileIssues } from "./FileIssuesList";

// ============================================================================
// Types
// ============================================================================

export interface FileQualityPanelProps {
  /** File path to show quality for */
  file: string;
  /** Pipeline result for quality data */
  pipelineResult: PipelineResult;
  /** Vietnamese mode */
  vietnamese?: boolean;
  /** Handler when line is clicked */
  onLineClick?: (file: string, line: number) => void;
  /** Handler to close the panel */
  onClose?: () => void;
  /** Show issue list (can be collapsed) */
  showIssues?: boolean;
  /** Maximum height for the panel */
  maxHeight?: string;
  /** Additional CSS classes */
  className?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Calculate file quality score (0-100)
 */
function calculateFileScore(status: FileQualityStatus): number {
  let score = 100;

  // Syntax issues: -10 per issue
  score -= status.issuesByGate.syntax * 10;

  // Security issues by severity
  score -= status.securitySeverities.critical * 25;
  score -= status.securitySeverities.high * 15;
  score -= status.securitySeverities.medium * 8;
  score -= status.securitySeverities.low * 3;

  // Architecture issues: -12 per issue
  score -= status.issuesByGate.architecture * 12;

  return Math.max(0, Math.min(100, score));
}

/**
 * Get grade from score
 */
function getGrade(score: number): { letter: string; color: string; label: string; vietnameseLabel: string } {
  if (score >= 90) {
    return { letter: "A", color: "text-green-600", label: "Excellent", vietnameseLabel: "Xuất sắc" };
  }
  if (score >= 80) {
    return { letter: "B", color: "text-blue-600", label: "Good", vietnameseLabel: "Tốt" };
  }
  if (score >= 70) {
    return { letter: "C", color: "text-yellow-600", label: "Fair", vietnameseLabel: "Khá" };
  }
  if (score >= 60) {
    return { letter: "D", color: "text-orange-600", label: "Poor", vietnameseLabel: "Yếu" };
  }
  return { letter: "F", color: "text-red-600", label: "Critical", vietnameseLabel: "Nghiêm trọng" };
}

// ============================================================================
// Gate Summary Component
// ============================================================================

interface GateSummaryProps {
  gate: GateName;
  issueCount: number;
  vietnamese?: boolean;
}

const GateSummary: React.FC<GateSummaryProps> = ({
  gate,
  issueCount,
  vietnamese,
}) => {
  const config = GATE_CONFIGS[gate];
  const label = vietnamese ? config.vietnameseLabel : config.label;
  const passed = issueCount === 0;

  const GateIconComponent = () => {
    switch (gate) {
      case "syntax":
        return <Code2 className="h-4 w-4" />;
      case "security":
        return <Shield className="h-4 w-4" />;
      case "architecture":
        return <Layers className="h-4 w-4" />;
      default:
        return <FileCode className="h-4 w-4" />;
    }
  };

  return (
    <div
      className={cn(
        "flex items-center justify-between px-3 py-2 rounded-lg",
        passed
          ? "bg-green-50 dark:bg-green-900/20"
          : "bg-red-50 dark:bg-red-900/20"
      )}
    >
      <div className="flex items-center gap-2">
        <GateIconComponent />
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        {passed ? (
          <>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            <span className="text-sm text-green-600 dark:text-green-400">
              {vietnamese ? "Đạt" : "Passed"}
            </span>
          </>
        ) : (
          <>
            <Badge
              variant="destructive"
              className="text-xs"
            >
              {issueCount}
            </Badge>
            <span className="text-sm text-red-600 dark:text-red-400">
              {vietnamese
                ? `${issueCount} lỗi`
                : `${issueCount} issue${issueCount > 1 ? "s" : ""}`}
            </span>
          </>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// Score Display Component
// ============================================================================

interface ScoreDisplayProps {
  score: number;
  vietnamese?: boolean;
}

const ScoreDisplay: React.FC<ScoreDisplayProps> = ({ score, vietnamese }) => {
  const grade = getGrade(score);

  return (
    <div className="flex items-center gap-4">
      {/* Score circle */}
      <div
        className={cn(
          "relative w-16 h-16 rounded-full flex items-center justify-center",
          "bg-gradient-to-br",
          score >= 80 ? "from-green-100 to-green-200 dark:from-green-900/30 dark:to-green-800/30" :
          score >= 60 ? "from-yellow-100 to-yellow-200 dark:from-yellow-900/30 dark:to-yellow-800/30" :
          "from-red-100 to-red-200 dark:from-red-900/30 dark:to-red-800/30"
        )}
      >
        <span className={cn("text-2xl font-bold", grade.color)}>
          {grade.letter}
        </span>
      </div>

      {/* Score details */}
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-2xl font-bold">{score}</span>
          <span className="text-sm text-gray-500">/100</span>
        </div>
        <p className={cn("text-sm", grade.color)}>
          {vietnamese ? grade.vietnameseLabel : grade.label}
        </p>
        <Progress
          value={score}
          className={cn(
            "mt-1 h-1.5",
            score >= 80 && "[&>div]:bg-green-500",
            score >= 60 && score < 80 && "[&>div]:bg-yellow-500",
            score < 60 && "[&>div]:bg-red-500"
          )}
        />
      </div>
    </div>
  );
};

// ============================================================================
// Severity Summary Component
// ============================================================================

interface SeveritySummaryProps {
  securitySeverities: FileQualityStatus["securitySeverities"];
  vietnamese?: boolean;
}

const SeveritySummary: React.FC<SeveritySummaryProps> = ({
  securitySeverities,
  vietnamese,
}) => {
  const hasSecurity =
    securitySeverities.critical > 0 ||
    securitySeverities.high > 0 ||
    securitySeverities.medium > 0 ||
    securitySeverities.low > 0;

  if (!hasSecurity) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {securitySeverities.critical > 0 && (
        <Badge variant="destructive" className="gap-1">
          <AlertTriangle className="h-3 w-3" />
          {securitySeverities.critical} {vietnamese ? "nghiêm trọng" : "critical"}
        </Badge>
      )}
      {securitySeverities.high > 0 && (
        <Badge className="gap-1 bg-orange-500 hover:bg-orange-600">
          <AlertTriangle className="h-3 w-3" />
          {securitySeverities.high} {vietnamese ? "cao" : "high"}
        </Badge>
      )}
      {securitySeverities.medium > 0 && (
        <Badge className="gap-1 bg-yellow-500 hover:bg-yellow-600 text-gray-900">
          {securitySeverities.medium} {vietnamese ? "trung bình" : "medium"}
        </Badge>
      )}
      {securitySeverities.low > 0 && (
        <Badge variant="outline" className="gap-1">
          {securitySeverities.low} {vietnamese ? "thấp" : "low"}
        </Badge>
      )}
    </div>
  );
};

// ============================================================================
// Main Component
// ============================================================================

export const FileQualityPanel: React.FC<FileQualityPanelProps> = ({
  file,
  pipelineResult,
  vietnamese = false,
  onLineClick,
  onClose: _onClose,
  showIssues = true,
  maxHeight,
  className,
}) => {
  // Note: onClose can be used by parent to add a close button in the header
  void _onClose;
  // Get file quality status
  const status = useMemo(
    () => getFileQualityStatus(file, pipelineResult),
    [file, pipelineResult]
  );

  // Get issues for this file
  const issues = useMemo(
    () => getFileIssues(file, pipelineResult),
    [file, pipelineResult]
  );

  // Calculate score
  const score = useMemo(() => calculateFileScore(status), [status]);

  // Get filename from path
  const filename = file.split("/").pop() || file;

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <FileCode className="h-5 w-5 mt-0.5 text-gray-500" />
            <div>
              <CardTitle className="text-base">{filename}</CardTitle>
              <p className="text-xs text-gray-500 font-mono mt-0.5">{file}</p>
            </div>
          </div>
          <FileQualityIndicator
            file={file}
            status={status}
            compact
            showCount
            vietnamese={vietnamese}
          />
        </div>
      </CardHeader>

      <CardContent
        className={cn("space-y-4", maxHeight && "overflow-y-auto")}
        style={maxHeight ? { maxHeight } : undefined}
      >
        {/* Score display */}
        <ScoreDisplay score={score} vietnamese={vietnamese} />

        <Separator />

        {/* Gate summaries */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {vietnamese ? "Kết quả theo cổng" : "Gate Results"}
          </h4>
          <div className="space-y-1.5">
            <GateSummary
              gate="syntax"
              issueCount={status.issuesByGate.syntax}
              vietnamese={vietnamese}
            />
            <GateSummary
              gate="security"
              issueCount={status.issuesByGate.security}
              vietnamese={vietnamese}
            />
            <GateSummary
              gate="architecture"
              issueCount={status.issuesByGate.architecture}
              vietnamese={vietnamese}
            />
          </div>
        </div>

        {/* Security severity breakdown */}
        {status.issuesByGate.security > 0 && (
          <>
            <Separator />
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {vietnamese ? "Mức độ bảo mật" : "Security Severity"}
              </h4>
              <SeveritySummary
                securitySeverities={status.securitySeverities}
                vietnamese={vietnamese}
              />
            </div>
          </>
        )}

        {/* Issues list */}
        {showIssues && issues.length > 0 && (
          <>
            <Separator />
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {vietnamese ? "Chi tiết vấn đề" : "Issue Details"}
              </h4>
              <FileIssuesList
                file={file}
                pipelineResult={pipelineResult}
                vietnamese={vietnamese}
                onLineClick={onLineClick}
                showFilters={issues.length > 3}
                maxHeight="300px"
              />
            </div>
          </>
        )}

        {/* No issues state */}
        {status.issueCount === 0 && (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <CheckCircle2 className="h-12 w-12 text-green-500 mb-3" />
            <p className="text-sm font-medium text-green-700 dark:text-green-400">
              {vietnamese
                ? "File này không có vấn đề"
                : "This file has no issues"}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {vietnamese
                ? "Tất cả các kiểm tra chất lượng đã đạt"
                : "All quality checks passed"}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// ============================================================================
// Compact File Quality Card
// ============================================================================

export interface FileQualityCardProps {
  /** File path */
  file: string;
  /** Pipeline result */
  pipelineResult: PipelineResult;
  /** Vietnamese mode */
  vietnamese?: boolean;
  /** Click handler */
  onClick?: (file: string) => void;
  /** Selected state */
  selected?: boolean;
  /** Additional CSS classes */
  className?: string;
}

export const FileQualityCard: React.FC<FileQualityCardProps> = ({
  file,
  pipelineResult,
  vietnamese: _vietnamese = false,
  onClick,
  selected = false,
  className,
}) => {
  // Reserved for future Vietnamese label support
  void _vietnamese;

  const status = useMemo(
    () => getFileQualityStatus(file, pipelineResult),
    [file, pipelineResult]
  );

  const score = useMemo(() => calculateFileScore(status), [status]);
  const grade = getGrade(score);
  const filename = file.split("/").pop() || file;

  const handleClick = () => {
    onClick?.(file);
  };

  return (
    <div
      role="button"
      onClick={handleClick}
      className={cn(
        "flex items-center justify-between px-3 py-2 rounded-lg border",
        "transition-colors cursor-pointer",
        selected
          ? "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
          : "bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800",
        className
      )}
    >
      <div className="flex items-center gap-3 min-w-0">
        {/* Score badge */}
        <div
          className={cn(
            "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
            score >= 80 && "bg-green-100 dark:bg-green-900/30 text-green-600",
            score >= 60 && score < 80 && "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600",
            score < 60 && "bg-red-100 dark:bg-red-900/30 text-red-600"
          )}
        >
          {grade.letter}
        </div>

        {/* File info */}
        <div className="min-w-0">
          <p className="text-sm font-medium truncate">{filename}</p>
          <p className="text-xs text-gray-500 truncate">{file}</p>
        </div>
      </div>

      {/* Issue indicators */}
      <div className="flex items-center gap-2 ml-2">
        {status.issueCount > 0 ? (
          <>
            {status.issuesByGate.syntax > 0 && (
              <Badge variant="outline" className="text-xs px-1.5 py-0 h-5">
                <Code2 className="h-3 w-3 mr-0.5" />
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
                <Shield className="h-3 w-3 mr-0.5" />
                {status.issuesByGate.security}
              </Badge>
            )}
            {status.issuesByGate.architecture > 0 && (
              <Badge variant="outline" className="text-xs px-1.5 py-0 h-5">
                <Layers className="h-3 w-3 mr-0.5" />
                {status.issuesByGate.architecture}
              </Badge>
            )}
          </>
        ) : (
          <CheckCircle2 className="h-5 w-5 text-green-500" />
        )}
      </div>
    </div>
  );
};

export default FileQualityPanel;
