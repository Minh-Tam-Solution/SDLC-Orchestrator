/**
 * =========================================================================
 * FileIssuesList - Display Issues for a Specific File
 * SDLC Orchestrator - Sprint 55 Day 3
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 *
 * Purpose:
 * - Display all quality issues for a specific file
 * - Group issues by gate (Syntax, Security, Architecture)
 * - Show severity-colored issue items
 * - Support filtering by gate and severity
 * - Vietnamese internationalization
 *
 * References:
 * - docs/02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md
 * =========================================================================
 */

import React, { useState, useMemo } from "react";
import {
  AlertTriangle,
  AlertCircle,
  Info,
  Code2,
  Shield,
  Layers,
  ChevronDown,
  ChevronRight,
  FileCode,
  Lightbulb,
  ExternalLink,
  Filter,
} from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import type {
  GateName,
  Severity,
  PipelineResult,
} from "@/types/quality";
import {
  isSyntaxResult,
  isSecurityResult,
  isArchitectureResult,
  GATE_CONFIGS,
} from "@/types/quality";

// ============================================================================
// Types
// ============================================================================

export interface UnifiedIssue {
  id: string;
  gate: GateName;
  file: string;
  line?: number;
  column?: number;
  severity?: Severity;
  ruleId?: string;
  rule?: string;
  message: string;
  vietnameseMessage?: string;
  fixSuggestion?: string;
}

export interface FileIssuesListProps {
  /** File path to show issues for */
  file: string;
  /** Pipeline result to extract issues from */
  pipelineResult: PipelineResult;
  /** Initial gate filter (show only issues from this gate) */
  gateFilter?: GateName[];
  /** Initial severity filter */
  severityFilter?: Severity[];
  /** Vietnamese mode */
  vietnamese?: boolean;
  /** Handler when line is clicked (for navigation) */
  onLineClick?: (file: string, line: number) => void;
  /** Show filter controls */
  showFilters?: boolean;
  /** Collapse all sections by default */
  defaultCollapsed?: boolean;
  /** Maximum height with scroll */
  maxHeight?: string;
  /** Additional CSS classes */
  className?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Extract all issues for a specific file from pipeline result
 */
export function getFileIssues(
  file: string,
  pipelineResult: PipelineResult
): UnifiedIssue[] {
  const issues: UnifiedIssue[] = [];
  let issueId = 0;

  for (const gate of pipelineResult.gates) {
    const details = gate.details;

    if (isSyntaxResult(details)) {
      for (const issue of details.issues) {
        if (issue.file === file) {
          issues.push({
            id: `syntax-${issueId++}`,
            gate: "syntax",
            file: issue.file,
            line: issue.line,
            column: issue.column,
            message: issue.message,
            vietnameseMessage: issue.vietnameseMessage,
          });
        }
      }
    } else if (isSecurityResult(details)) {
      for (const issue of details.issues) {
        if (issue.file === file) {
          issues.push({
            id: `security-${issueId++}`,
            gate: "security",
            file: issue.file,
            line: issue.line,
            severity: issue.severity,
            ruleId: issue.ruleId,
            message: issue.message,
            vietnameseMessage: issue.vietnameseMessage,
            fixSuggestion: issue.fixSuggestion,
          });
        }
      }
    } else if (isArchitectureResult(details)) {
      for (const issue of details.issues) {
        if (issue.file === file) {
          issues.push({
            id: `architecture-${issueId++}`,
            gate: "architecture",
            file: issue.file,
            line: issue.line,
            rule: issue.rule,
            message: issue.message,
            vietnameseMessage: issue.vietnameseMessage,
          });
        }
      }
    }
  }

  return issues;
}

/**
 * Group issues by gate
 */
function groupIssuesByGate(
  issues: UnifiedIssue[]
): Record<GateName, UnifiedIssue[]> {
  const grouped: Record<GateName, UnifiedIssue[]> = {
    syntax: [],
    security: [],
    architecture: [],
    tests: [],
  };

  for (const issue of issues) {
    grouped[issue.gate].push(issue);
  }

  return grouped;
}

// ============================================================================
// Gate Icon Component
// ============================================================================

const GateIcon: React.FC<{ gate: GateName; className?: string }> = ({
  gate,
  className,
}) => {
  const iconClass = cn("h-4 w-4", className);

  switch (gate) {
    case "syntax":
      return <Code2 className={iconClass} />;
    case "security":
      return <Shield className={iconClass} />;
    case "architecture":
      return <Layers className={iconClass} />;
    default:
      return <FileCode className={iconClass} />;
  }
};

// ============================================================================
// Severity Icon Component
// ============================================================================

const SeverityIcon: React.FC<{ severity?: Severity; className?: string }> = ({
  severity,
  className,
}) => {
  const iconClass = cn("h-4 w-4", className);

  switch (severity) {
    case "critical":
      return <AlertCircle className={cn(iconClass, "text-red-600")} />;
    case "high":
      return <AlertTriangle className={cn(iconClass, "text-orange-500")} />;
    case "medium":
      return <AlertTriangle className={cn(iconClass, "text-yellow-500")} />;
    case "low":
      return <Info className={cn(iconClass, "text-blue-500")} />;
    default:
      return <AlertCircle className={cn(iconClass, "text-gray-500")} />;
  }
};

// ============================================================================
// Issue Item Component
// ============================================================================

interface IssueItemProps {
  issue: UnifiedIssue;
  vietnamese?: boolean;
  onLineClick?: (file: string, line: number) => void;
}

const IssueItem: React.FC<IssueItemProps> = ({
  issue,
  vietnamese,
  onLineClick,
}) => {
  const message = vietnamese && issue.vietnameseMessage
    ? issue.vietnameseMessage
    : issue.message;

  const handleLineClick = () => {
    if (onLineClick && issue.line) {
      onLineClick(issue.file, issue.line);
    }
  };

  return (
    <div
      className={cn(
        "border-l-2 pl-3 py-2",
        issue.severity === "critical" && "border-l-red-500",
        issue.severity === "high" && "border-l-orange-500",
        issue.severity === "medium" && "border-l-yellow-500",
        issue.severity === "low" && "border-l-blue-500",
        !issue.severity && issue.gate === "syntax" && "border-l-red-400",
        !issue.severity && issue.gate === "architecture" && "border-l-purple-400"
      )}
    >
      <div className="flex items-start gap-2">
        {issue.severity ? (
          <SeverityIcon severity={issue.severity} />
        ) : (
          <GateIcon gate={issue.gate} className="text-gray-500 mt-0.5" />
        )}

        <div className="flex-1 min-w-0">
          {/* Line number and location */}
          <div className="flex items-center gap-2 mb-1">
            {issue.line && (
              <button
                onClick={handleLineClick}
                className={cn(
                  "text-xs font-mono px-1.5 py-0.5 rounded",
                  "bg-gray-100 dark:bg-gray-800",
                  onLineClick && "hover:bg-blue-100 dark:hover:bg-blue-900 cursor-pointer"
                )}
              >
                {vietnamese ? "Dòng" : "Line"} {issue.line}
                {issue.column && `:${issue.column}`}
              </button>
            )}

            {issue.severity && (
              <Badge
                variant={
                  issue.severity === "critical"
                    ? "destructive"
                    : issue.severity === "high"
                    ? "default"
                    : "outline"
                }
                className={cn(
                  "text-xs",
                  issue.severity === "high" && "bg-orange-500",
                  issue.severity === "medium" && "bg-yellow-500 text-gray-900",
                  issue.severity === "low" && "bg-blue-100 text-blue-800"
                )}
              >
                {issue.severity.charAt(0).toUpperCase() + issue.severity.slice(1)}
              </Badge>
            )}

            {issue.ruleId && (
              <span className="text-xs text-gray-500 font-mono truncate">
                {issue.ruleId}
              </span>
            )}

            {issue.rule && (
              <span className="text-xs text-gray-500 font-mono">
                {issue.rule}
              </span>
            )}
          </div>

          {/* Message */}
          <p className="text-sm text-gray-700 dark:text-gray-300">
            {message}
          </p>

          {/* Fix suggestion */}
          {issue.fixSuggestion && (
            <div className="flex items-start gap-1.5 mt-2 text-xs text-green-700 dark:text-green-400">
              <Lightbulb className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
              <span>{issue.fixSuggestion}</span>
            </div>
          )}
        </div>

        {/* Navigate button */}
        {onLineClick && issue.line && (
          <button
            onClick={handleLineClick}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            title={vietnamese ? "Đi đến dòng" : "Go to line"}
          >
            <ExternalLink className="h-3.5 w-3.5 text-gray-400" />
          </button>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// Gate Section Component
// ============================================================================

interface GateSectionProps {
  gate: GateName;
  issues: UnifiedIssue[];
  vietnamese?: boolean;
  onLineClick?: (file: string, line: number) => void;
  defaultOpen?: boolean;
}

const GateSection: React.FC<GateSectionProps> = ({
  gate,
  issues,
  vietnamese,
  onLineClick,
  defaultOpen = true,
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const config = GATE_CONFIGS[gate];
  const label = vietnamese ? config.vietnameseLabel : config.label;

  if (issues.length === 0) {
    return null;
  }

  // Count severities for security gate
  const severityCounts = issues.reduce(
    (acc, issue) => {
      if (issue.severity) {
        acc[issue.severity] = (acc[issue.severity] || 0) + 1;
      }
      return acc;
    },
    {} as Record<Severity, number>
  );

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="mb-3">
      <CollapsibleTrigger asChild>
        <button
          className={cn(
            "flex items-center justify-between w-full px-3 py-2 rounded-lg",
            "bg-gray-50 dark:bg-gray-800/50",
            "hover:bg-gray-100 dark:hover:bg-gray-800"
          )}
        >
          <div className="flex items-center gap-2">
            {isOpen ? (
              <ChevronDown className="h-4 w-4 text-gray-500" />
            ) : (
              <ChevronRight className="h-4 w-4 text-gray-500" />
            )}
            <GateIcon gate={gate} />
            <span className="font-medium text-sm">{label}</span>
            <Badge variant="secondary" className="ml-1">
              {issues.length}
            </Badge>
          </div>

          {/* Severity badges for security gate */}
          {gate === "security" && Object.keys(severityCounts).length > 0 && (
            <div className="flex items-center gap-1">
              {severityCounts.critical && (
                <Badge variant="destructive" className="text-xs">
                  {severityCounts.critical} {vietnamese ? "nghiêm trọng" : "critical"}
                </Badge>
              )}
              {severityCounts.high && (
                <Badge className="text-xs bg-orange-500">
                  {severityCounts.high} {vietnamese ? "cao" : "high"}
                </Badge>
              )}
            </div>
          )}
        </button>
      </CollapsibleTrigger>

      <CollapsibleContent className="mt-2 space-y-2 pl-6">
        {issues
          .sort((a, b) => {
            // Sort by severity (critical first), then by line number
            const severityOrder: Record<Severity, number> = {
              critical: 0,
              high: 1,
              medium: 2,
              low: 3,
              info: 4,
            };
            if (a.severity && b.severity) {
              const diff = severityOrder[a.severity] - severityOrder[b.severity];
              if (diff !== 0) return diff;
            }
            return (a.line || 0) - (b.line || 0);
          })
          .map((issue) => (
            <IssueItem
              key={issue.id}
              issue={issue}
              vietnamese={vietnamese}
              onLineClick={onLineClick}
            />
          ))}
      </CollapsibleContent>
    </Collapsible>
  );
};

// ============================================================================
// Filter Controls Component
// ============================================================================

interface FilterControlsProps {
  gateFilter: GateName[];
  severityFilter: Severity[];
  onGateFilterChange: (gates: GateName[]) => void;
  onSeverityFilterChange: (severities: Severity[]) => void;
  vietnamese?: boolean;
  availableGates: GateName[];
  availableSeverities: Severity[];
}

const FilterControls: React.FC<FilterControlsProps> = ({
  gateFilter,
  severityFilter,
  onGateFilterChange,
  onSeverityFilterChange,
  vietnamese,
  availableGates,
  availableSeverities,
}) => {
  const toggleGate = (gate: GateName) => {
    if (gateFilter.includes(gate)) {
      onGateFilterChange(gateFilter.filter((g) => g !== gate));
    } else {
      onGateFilterChange([...gateFilter, gate]);
    }
  };

  const toggleSeverity = (severity: Severity) => {
    if (severityFilter.includes(severity)) {
      onSeverityFilterChange(severityFilter.filter((s) => s !== severity));
    } else {
      onSeverityFilterChange([...severityFilter, severity]);
    }
  };

  const hasFilters = gateFilter.length > 0 || severityFilter.length > 0;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="h-8">
          <Filter className="h-3.5 w-3.5 mr-1.5" />
          {vietnamese ? "Lọc" : "Filter"}
          {hasFilters && (
            <Badge variant="secondary" className="ml-1.5 h-4 px-1 text-xs">
              {gateFilter.length + severityFilter.length}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuLabel>
          {vietnamese ? "Cổng chất lượng" : "Quality Gates"}
        </DropdownMenuLabel>
        {availableGates.map((gate) => (
          <DropdownMenuCheckboxItem
            key={gate}
            checked={gateFilter.includes(gate)}
            onCheckedChange={() => toggleGate(gate)}
          >
            <GateIcon gate={gate} className="mr-2" />
            {vietnamese
              ? GATE_CONFIGS[gate].vietnameseLabel
              : GATE_CONFIGS[gate].label}
          </DropdownMenuCheckboxItem>
        ))}

        {availableSeverities.length > 0 && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuLabel>
              {vietnamese ? "Mức độ nghiêm trọng" : "Severity"}
            </DropdownMenuLabel>
            {availableSeverities.map((severity) => (
              <DropdownMenuCheckboxItem
                key={severity}
                checked={severityFilter.includes(severity)}
                onCheckedChange={() => toggleSeverity(severity)}
              >
                <SeverityIcon severity={severity} className="mr-2" />
                {severity.charAt(0).toUpperCase() + severity.slice(1)}
              </DropdownMenuCheckboxItem>
            ))}
          </>
        )}

        {hasFilters && (
          <>
            <DropdownMenuSeparator />
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start text-xs"
              onClick={() => {
                onGateFilterChange([]);
                onSeverityFilterChange([]);
              }}
            >
              {vietnamese ? "Xóa bộ lọc" : "Clear filters"}
            </Button>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

// ============================================================================
// Main Component
// ============================================================================

export const FileIssuesList: React.FC<FileIssuesListProps> = ({
  file,
  pipelineResult,
  gateFilter: initialGateFilter = [],
  severityFilter: initialSeverityFilter = [],
  vietnamese = false,
  onLineClick,
  showFilters = true,
  defaultCollapsed = false,
  maxHeight,
  className,
}) => {
  const [gateFilter, setGateFilter] = useState<GateName[]>(initialGateFilter);
  const [severityFilter, setSeverityFilter] = useState<Severity[]>(
    initialSeverityFilter
  );

  // Get all issues for this file
  const allIssues = useMemo(
    () => getFileIssues(file, pipelineResult),
    [file, pipelineResult]
  );

  // Get available gates and severities for filter
  const availableGates = useMemo(() => {
    const gates = new Set<GateName>();
    for (const issue of allIssues) {
      gates.add(issue.gate);
    }
    return Array.from(gates);
  }, [allIssues]);

  const availableSeverities = useMemo(() => {
    const severities = new Set<Severity>();
    for (const issue of allIssues) {
      if (issue.severity) {
        severities.add(issue.severity);
      }
    }
    return Array.from(severities);
  }, [allIssues]);

  // Apply filters
  const filteredIssues = useMemo(() => {
    let issues = allIssues;

    if (gateFilter.length > 0) {
      issues = issues.filter((i) => gateFilter.includes(i.gate));
    }

    if (severityFilter.length > 0) {
      issues = issues.filter(
        (i) => i.severity && severityFilter.includes(i.severity)
      );
    }

    return issues;
  }, [allIssues, gateFilter, severityFilter]);

  // Group by gate
  const groupedIssues = useMemo(
    () => groupIssuesByGate(filteredIssues),
    [filteredIssues]
  );

  // Empty state
  if (allIssues.length === 0) {
    return (
      <div
        className={cn(
          "flex flex-col items-center justify-center py-8 text-gray-500",
          className
        )}
      >
        <FileCode className="h-12 w-12 mb-3 text-gray-300" />
        <p className="text-sm">
          {vietnamese
            ? "Không có vấn đề nào trong file này"
            : "No issues found in this file"}
        </p>
      </div>
    );
  }

  // Filtered empty state
  if (filteredIssues.length === 0) {
    return (
      <div className={cn("space-y-4", className)}>
        {showFilters && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">
              {vietnamese
                ? `${allIssues.length} vấn đề (đã lọc)`
                : `${allIssues.length} issues (filtered)`}
            </span>
            <FilterControls
              gateFilter={gateFilter}
              severityFilter={severityFilter}
              onGateFilterChange={setGateFilter}
              onSeverityFilterChange={setSeverityFilter}
              vietnamese={vietnamese}
              availableGates={availableGates}
              availableSeverities={availableSeverities}
            />
          </div>
        )}
        <div className="flex flex-col items-center justify-center py-8 text-gray-500">
          <Filter className="h-8 w-8 mb-2 text-gray-300" />
          <p className="text-sm">
            {vietnamese
              ? "Không có kết quả khớp với bộ lọc"
              : "No issues match the current filters"}
          </p>
          <Button
            variant="ghost"
            size="sm"
            className="mt-2"
            onClick={() => {
              setGateFilter([]);
              setSeverityFilter([]);
            }}
          >
            {vietnamese ? "Xóa bộ lọc" : "Clear filters"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header with filter */}
      {showFilters && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">
            {filteredIssues.length === allIssues.length
              ? vietnamese
                ? `${allIssues.length} vấn đề`
                : `${allIssues.length} issue${allIssues.length > 1 ? "s" : ""}`
              : vietnamese
              ? `${filteredIssues.length}/${allIssues.length} vấn đề`
              : `${filteredIssues.length}/${allIssues.length} issues`}
          </span>
          <FilterControls
            gateFilter={gateFilter}
            severityFilter={severityFilter}
            onGateFilterChange={setGateFilter}
            onSeverityFilterChange={setSeverityFilter}
            vietnamese={vietnamese}
            availableGates={availableGates}
            availableSeverities={availableSeverities}
          />
        </div>
      )}

      {/* Issues by gate */}
      <div
        className={cn(maxHeight && "overflow-y-auto")}
        style={maxHeight ? { maxHeight } : undefined}
      >
        {(["syntax", "security", "architecture"] as GateName[]).map((gate) => (
          <GateSection
            key={gate}
            gate={gate}
            issues={groupedIssues[gate]}
            vietnamese={vietnamese}
            onLineClick={onLineClick}
            defaultOpen={!defaultCollapsed}
          />
        ))}
      </div>
    </div>
  );
};

export default FileIssuesList;
