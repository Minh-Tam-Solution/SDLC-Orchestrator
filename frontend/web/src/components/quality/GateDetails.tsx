/**
 * =========================================================================
 * GateDetails - Detailed Gate Results Display
 * SDLC Orchestrator - Sprint 55 Day 1
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 * Authority: Frontend Team + CTO Approved
 *
 * Purpose:
 * - Display detailed gate validation results
 * - Show issues by file with line numbers
 * - Support Vietnamese error messages
 * - Collapsible issue groups
 *
 * References:
 * - docs/02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md
 * =========================================================================
 */

import { useState, useMemo } from "react";
import {
  ChevronDown,
  ChevronRight,
  FileCode,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle2,
  XCircle,
  Lightbulb,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { GateStatusBadge } from "./GateStatusBadge";
import type {
  GateResult,
  Severity,
  SyntaxIssue,
  SecurityIssue,
  ArchitectureIssue,
  TestResult,
} from "@/types/quality";
import {
  isSyntaxResult,
  isSecurityResult,
  isArchitectureResult,
  isTestResult,
} from "@/types/quality";

// ============================================================================
// Types
// ============================================================================

interface GateDetailsProps {
  /** Gate result to display */
  result: GateResult;
  /** Use Vietnamese messages */
  vietnamese?: boolean;
  /** Max height for scroll area */
  maxHeight?: string;
  /** File click handler */
  onFileClick?: (file: string, line?: number) => void;
  /** Additional class name */
  className?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

function getSeverityIcon(severity: Severity) {
  switch (severity) {
    case "critical":
    case "high":
      return AlertCircle;
    case "medium":
      return AlertTriangle;
    case "low":
    case "info":
    default:
      return Info;
  }
}

function getSeverityStyles(severity: Severity): string {
  switch (severity) {
    case "critical":
      return "text-red-600 bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800";
    case "high":
      return "text-orange-600 bg-orange-50 border-orange-200 dark:bg-orange-900/20 dark:border-orange-800";
    case "medium":
      return "text-yellow-600 bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800";
    case "low":
      return "text-blue-600 bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800";
    case "info":
    default:
      return "text-gray-600 bg-gray-50 border-gray-200 dark:bg-gray-900/20 dark:border-gray-800";
  }
}

function groupIssuesByFile<T extends { file: string }>(
  issues: T[]
): Map<string, T[]> {
  const grouped = new Map<string, T[]>();
  for (const issue of issues) {
    const existing = grouped.get(issue.file) || [];
    existing.push(issue);
    grouped.set(issue.file, existing);
  }
  return grouped;
}

// ============================================================================
// Sub-Components
// ============================================================================

interface IssueItemProps {
  file: string;
  line?: number;
  column?: number;
  message: string;
  vietnameseMessage?: string;
  severity?: Severity;
  fixSuggestion?: string;
  vietnamese?: boolean;
  onFileClick?: (file: string, line?: number) => void;
}

function IssueItem({
  file,
  line,
  column,
  message,
  vietnameseMessage,
  severity = "medium",
  fixSuggestion,
  vietnamese = false,
  onFileClick,
}: IssueItemProps) {
  const Icon = getSeverityIcon(severity);
  const displayMessage = vietnamese && vietnameseMessage ? vietnameseMessage : message;

  return (
    <div
      className={cn(
        "p-3 rounded-lg border",
        getSeverityStyles(severity)
      )}
    >
      <div className="flex items-start gap-2">
        <Icon className="h-4 w-4 mt-0.5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => onFileClick?.(file, line)}
              className="text-sm font-medium hover:underline"
            >
              {file}
              {line !== undefined && (
                <span className="text-muted-foreground">
                  :{line}
                  {column !== undefined && `:${column}`}
                </span>
              )}
            </button>
            <Badge
              variant="outline"
              className={cn(
                "text-xs capitalize",
                severity === "critical" && "border-red-500 text-red-500",
                severity === "high" && "border-orange-500 text-orange-500",
                severity === "medium" && "border-yellow-500 text-yellow-500",
                severity === "low" && "border-blue-500 text-blue-500"
              )}
            >
              {severity}
            </Badge>
          </div>
          <p className="text-sm mt-1">{displayMessage}</p>
          {fixSuggestion && (
            <div className="mt-2 flex items-start gap-2 text-sm text-muted-foreground">
              <Lightbulb className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>{vietnamese ? "Gợi ý: " : "Fix: "}{fixSuggestion}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface FileGroupProps {
  file: string;
  issues: Array<{
    line?: number;
    column?: number;
    message: string;
    vietnameseMessage?: string;
    severity?: Severity;
    fixSuggestion?: string;
  }>;
  vietnamese?: boolean;
  defaultOpen?: boolean;
  onFileClick?: (file: string, line?: number) => void;
}

function FileGroup({
  file,
  issues,
  vietnamese = false,
  defaultOpen = true,
  onFileClick,
}: FileGroupProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <Button
          variant="ghost"
          className="w-full justify-start gap-2 p-2 h-auto"
        >
          {isOpen ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
          <FileCode className="h-4 w-4" />
          <span className="font-mono text-sm truncate flex-1 text-left">
            {file}
          </span>
          <Badge variant="secondary" className="ml-auto">
            {issues.length}
          </Badge>
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="pl-6 space-y-2 mt-2">
        {issues.map((issue, index) => (
          <IssueItem
            key={index}
            file={file}
            line={issue.line}
            column={issue.column}
            message={issue.message}
            vietnameseMessage={issue.vietnameseMessage}
            severity={issue.severity}
            fixSuggestion={issue.fixSuggestion}
            vietnamese={vietnamese}
            onFileClick={onFileClick}
          />
        ))}
      </CollapsibleContent>
    </Collapsible>
  );
}

// ============================================================================
// Syntax Details Component
// ============================================================================

interface SyntaxDetailsProps {
  issues: SyntaxIssue[];
  filesChecked: number;
  filesPassed: number;
  vietnamese?: boolean;
  onFileClick?: (file: string, line?: number) => void;
}

function SyntaxDetails({
  issues,
  filesChecked,
  filesPassed,
  vietnamese = false,
  onFileClick,
}: SyntaxDetailsProps) {
  const groupedIssues = useMemo(() => groupIssuesByFile(issues), [issues]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 text-sm">
        <span>
          {vietnamese ? "Đã kiểm tra:" : "Files checked:"}{" "}
          <strong>{filesChecked}</strong>
        </span>
        <span className="text-green-600">
          {vietnamese ? "Đạt:" : "Passed:"} <strong>{filesPassed}</strong>
        </span>
        <span className="text-red-600">
          {vietnamese ? "Lỗi:" : "Failed:"}{" "}
          <strong>{filesChecked - filesPassed}</strong>
        </span>
      </div>

      {issues.length > 0 ? (
        <div className="space-y-2">
          {Array.from(groupedIssues.entries()).map(([file, fileIssues]) => (
            <FileGroup
              key={file}
              file={file}
              issues={fileIssues.map((i) => ({
                line: i.line,
                column: i.column,
                message: i.message,
                vietnameseMessage: i.vietnameseMessage,
                severity: "high" as Severity,
              }))}
              vietnamese={vietnamese}
              onFileClick={onFileClick}
            />
          ))}
        </div>
      ) : (
        <div className="flex items-center gap-2 text-green-600 p-3 bg-green-50 rounded-lg dark:bg-green-900/20">
          <CheckCircle2 className="h-5 w-5" />
          <span>
            {vietnamese
              ? "Tất cả các file đều có cú pháp hợp lệ"
              : "All files have valid syntax"}
          </span>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Security Details Component
// ============================================================================

interface SecurityDetailsProps {
  issues: SecurityIssue[];
  criticalCount: number;
  highCount: number;
  mediumCount: number;
  lowCount: number;
  vietnamese?: boolean;
  onFileClick?: (file: string, line?: number) => void;
}

function SecurityDetails({
  issues,
  criticalCount,
  highCount,
  mediumCount,
  lowCount,
  vietnamese = false,
  onFileClick,
}: SecurityDetailsProps) {
  const groupedIssues = useMemo(() => groupIssuesByFile(issues), [issues]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 text-sm flex-wrap">
        {criticalCount > 0 && (
          <Badge variant="destructive">
            {criticalCount} Critical
          </Badge>
        )}
        {highCount > 0 && (
          <Badge className="bg-orange-500">
            {highCount} High
          </Badge>
        )}
        {mediumCount > 0 && (
          <Badge className="bg-yellow-500 text-yellow-900">
            {mediumCount} Medium
          </Badge>
        )}
        {lowCount > 0 && (
          <Badge variant="secondary">
            {lowCount} Low
          </Badge>
        )}
        {issues.length === 0 && (
          <Badge className="bg-green-500">
            {vietnamese ? "Không có vấn đề" : "No issues"}
          </Badge>
        )}
      </div>

      {issues.length > 0 ? (
        <div className="space-y-2">
          {Array.from(groupedIssues.entries()).map(([file, fileIssues]) => (
            <FileGroup
              key={file}
              file={file}
              issues={fileIssues.map((i) => ({
                line: i.line,
                message: `[${i.ruleId}] ${i.message}`,
                vietnameseMessage: i.vietnameseMessage,
                severity: i.severity,
                fixSuggestion: i.fixSuggestion,
              }))}
              vietnamese={vietnamese}
              onFileClick={onFileClick}
            />
          ))}
        </div>
      ) : (
        <div className="flex items-center gap-2 text-green-600 p-3 bg-green-50 rounded-lg dark:bg-green-900/20">
          <CheckCircle2 className="h-5 w-5" />
          <span>
            {vietnamese
              ? "Không phát hiện vấn đề bảo mật"
              : "No security issues detected"}
          </span>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Architecture Details Component
// ============================================================================

interface ArchitectureDetailsProps {
  issues: ArchitectureIssue[];
  vietnamese?: boolean;
  onFileClick?: (file: string, line?: number) => void;
}

function ArchitectureDetails({
  issues,
  vietnamese = false,
  onFileClick,
}: ArchitectureDetailsProps) {
  const groupedIssues = useMemo(() => groupIssuesByFile(issues), [issues]);

  return (
    <div className="space-y-4">
      {issues.length > 0 ? (
        <div className="space-y-2">
          {Array.from(groupedIssues.entries()).map(([file, fileIssues]) => (
            <FileGroup
              key={file}
              file={file}
              issues={fileIssues.map((i) => ({
                line: i.line,
                message: `[${i.rule}] ${i.message}`,
                vietnameseMessage: i.vietnameseMessage,
                severity: "medium" as Severity,
              }))}
              vietnamese={vietnamese}
              onFileClick={onFileClick}
            />
          ))}
        </div>
      ) : (
        <div className="flex items-center gap-2 text-green-600 p-3 bg-green-50 rounded-lg dark:bg-green-900/20">
          <CheckCircle2 className="h-5 w-5" />
          <span>
            {vietnamese
              ? "Kiến trúc code tuân thủ các quy tắc"
              : "Code architecture follows all rules"}
          </span>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Test Details Component
// ============================================================================

interface TestDetailsProps {
  results: TestResult[];
  testsRun: number;
  testsPassed: number;
  testsFailed: number;
  vietnamese?: boolean;
}

function TestDetails({
  results,
  testsRun,
  testsPassed,
  testsFailed,
  vietnamese = false,
}: TestDetailsProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 text-sm">
        <span>
          {vietnamese ? "Đã chạy:" : "Tests run:"}{" "}
          <strong>{testsRun}</strong>
        </span>
        <span className="text-green-600">
          {vietnamese ? "Đạt:" : "Passed:"} <strong>{testsPassed}</strong>
        </span>
        <span className="text-red-600">
          {vietnamese ? "Lỗi:" : "Failed:"} <strong>{testsFailed}</strong>
        </span>
      </div>

      {results.length > 0 ? (
        <div className="space-y-2">
          {results.map((test, index) => (
            <div
              key={index}
              className={cn(
                "p-3 rounded-lg border flex items-start gap-2",
                test.passed
                  ? "bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800"
                  : "bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800"
              )}
            >
              {test.passed ? (
                <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5" />
              ) : (
                <XCircle className="h-4 w-4 text-red-600 mt-0.5" />
              )}
              <div className="flex-1">
                <p className="font-mono text-sm">{test.testName}</p>
                {test.errorMessage && (
                  <pre className="text-xs text-red-600 mt-1 whitespace-pre-wrap">
                    {test.errorMessage}
                  </pre>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-muted-foreground text-sm">
          {vietnamese ? "Không có bài test nào" : "No tests to display"}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function GateDetails({
  result,
  vietnamese = false,
  maxHeight = "400px",
  onFileClick,
  className,
}: GateDetailsProps) {
  const renderDetails = () => {
    if (isSyntaxResult(result.details)) {
      return (
        <SyntaxDetails
          issues={result.details.issues}
          filesChecked={result.details.filesChecked}
          filesPassed={result.details.filesPassed}
          vietnamese={vietnamese}
          onFileClick={onFileClick}
        />
      );
    }

    if (isSecurityResult(result.details)) {
      return (
        <SecurityDetails
          issues={result.details.issues}
          criticalCount={result.details.criticalCount}
          highCount={result.details.highCount}
          mediumCount={result.details.mediumCount}
          lowCount={result.details.lowCount}
          vietnamese={vietnamese}
          onFileClick={onFileClick}
        />
      );
    }

    if (isArchitectureResult(result.details)) {
      return (
        <ArchitectureDetails
          issues={result.details.issues}
          vietnamese={vietnamese}
          onFileClick={onFileClick}
        />
      );
    }

    if (isTestResult(result.details)) {
      return (
        <TestDetails
          results={result.details.results}
          testsRun={result.details.testsRun}
          testsPassed={result.details.testsPassed}
          testsFailed={result.details.testsFailed}
          vietnamese={vietnamese}
        />
      );
    }

    // Error case
    if ("error" in result.details) {
      return (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 dark:bg-red-900/20 dark:border-red-800">
          <p className="font-medium">
            {vietnamese ? "Lỗi:" : "Error:"}
          </p>
          <pre className="text-sm mt-1 whitespace-pre-wrap">
            {result.details.error}
          </pre>
        </div>
      );
    }

    return null;
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">
            <GateStatusBadge
              gateName={result.gateName}
              status={result.status}
              durationMs={result.durationMs}
              vietnamese={vietnamese}
            />
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea style={{ maxHeight }}>
          {renderDetails()}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Export
// ============================================================================

export default GateDetails;
