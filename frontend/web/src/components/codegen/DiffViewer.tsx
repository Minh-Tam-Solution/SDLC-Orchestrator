/**
 * =========================================================================
 * DiffViewer - Before/After Code Comparison Component
 * SDLC Orchestrator - Sprint 54 Day 3
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 54 Implementation
 * Authority: Frontend Team + CTO Approved
 * Foundation: CURRENT-SPRINT.md - Sprint 54 Frontend Polish
 *
 * Purpose:
 * - Display side-by-side code comparison
 * - Highlight added/removed/modified lines
 * - Support unified or split view modes
 * - Show line-by-line diff statistics
 * - Navigate between changes
 * - Syntax highlighting for both sides
 *
 * References:
 * - docs/04-build/02-Sprint-Plans/CURRENT-SPRINT.md
 * =========================================================================
 */

import { useState, useMemo, useCallback } from "react";
import {
  Plus,
  Minus,
  ArrowLeftRight,
  ChevronUp,
  ChevronDown,
  Columns,
  Rows,
  FileCode,
  Copy,
  Check,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// ============================================================================
// Types
// ============================================================================

interface DiffViewerProps {
  /** Original/before content */
  oldContent: string;
  /** New/after content */
  newContent: string;
  /** File path for display */
  filePath?: string;
  /** Programming language */
  language?: string;
  /** View mode: split (side-by-side) or unified */
  viewMode?: "split" | "unified";
  /** Optional class name */
  className?: string;
  /** Show line numbers */
  showLineNumbers?: boolean;
  /** Max height */
  maxHeight?: string;
  /** Old content label */
  oldLabel?: string;
  /** New content label */
  newLabel?: string;
}

type DiffLineType = "unchanged" | "added" | "removed" | "modified";

interface DiffLine {
  type: DiffLineType;
  oldLineNumber: number | null;
  newLineNumber: number | null;
  oldContent: string;
  newContent: string;
}

interface DiffStats {
  added: number;
  removed: number;
  modified: number;
  unchanged: number;
}

// ============================================================================
// Diff Algorithm (Simple Line-by-Line)
// ============================================================================

function computeDiff(oldContent: string, newContent: string): DiffLine[] {
  const oldLines = oldContent.split("\n");
  const newLines = newContent.split("\n");
  const result: DiffLine[] = [];

  // Simple LCS-based diff (Longest Common Subsequence)
  const lcs = computeLCS(oldLines, newLines);

  let oldIdx = 0;
  let newIdx = 0;
  let lcsIdx = 0;

  while (oldIdx < oldLines.length || newIdx < newLines.length) {
    if (lcsIdx < lcs.length && oldIdx < oldLines.length && oldLines[oldIdx] === lcs[lcsIdx]) {
      // Line is in LCS - check if it's at same position in new
      if (newIdx < newLines.length && newLines[newIdx] === lcs[lcsIdx]) {
        // Unchanged
        result.push({
          type: "unchanged",
          oldLineNumber: oldIdx + 1,
          newLineNumber: newIdx + 1,
          oldContent: oldLines[oldIdx] ?? "",
          newContent: newLines[newIdx] ?? "",
        });
        oldIdx++;
        newIdx++;
        lcsIdx++;
      } else {
        // New line added before this LCS element
        result.push({
          type: "added",
          oldLineNumber: null,
          newLineNumber: newIdx + 1,
          oldContent: "",
          newContent: newLines[newIdx] ?? "",
        });
        newIdx++;
      }
    } else if (lcsIdx < lcs.length && newIdx < newLines.length && newLines[newIdx] === lcs[lcsIdx]) {
      // Old line removed
      result.push({
        type: "removed",
        oldLineNumber: oldIdx + 1,
        newLineNumber: null,
        oldContent: oldLines[oldIdx] ?? "",
        newContent: "",
      });
      oldIdx++;
    } else if (oldIdx < oldLines.length && newIdx < newLines.length) {
      // Both have content but different - modification
      result.push({
        type: "modified",
        oldLineNumber: oldIdx + 1,
        newLineNumber: newIdx + 1,
        oldContent: oldLines[oldIdx] ?? "",
        newContent: newLines[newIdx] ?? "",
      });
      oldIdx++;
      newIdx++;
    } else if (oldIdx < oldLines.length) {
      // Only old has content - removed
      result.push({
        type: "removed",
        oldLineNumber: oldIdx + 1,
        newLineNumber: null,
        oldContent: oldLines[oldIdx] ?? "",
        newContent: "",
      });
      oldIdx++;
    } else if (newIdx < newLines.length) {
      // Only new has content - added
      result.push({
        type: "added",
        oldLineNumber: null,
        newLineNumber: newIdx + 1,
        oldContent: "",
        newContent: newLines[newIdx] ?? "",
      });
      newIdx++;
    }
  }

  return result;
}

function computeLCS(oldLines: string[], newLines: string[]): string[] {
  const m = oldLines.length;
  const n = newLines.length;

  // Create DP table
  const dp: number[][] = Array(m + 1)
    .fill(null)
    .map(() => Array(n + 1).fill(0));

  // Fill DP table
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      const dpRow = dp[i];
      const dpPrevRow = dp[i - 1];
      if (!dpRow || !dpPrevRow) continue;

      if (oldLines[i - 1] === newLines[j - 1]) {
        dpRow[j] = (dpPrevRow[j - 1] ?? 0) + 1;
      } else {
        dpRow[j] = Math.max(dpPrevRow[j] ?? 0, dpRow[j - 1] ?? 0);
      }
    }
  }

  // Backtrack to find LCS
  const lcs: string[] = [];
  let i = m;
  let j = n;

  while (i > 0 && j > 0) {
    if (oldLines[i - 1] === newLines[j - 1]) {
      lcs.unshift(oldLines[i - 1] ?? "");
      i--;
      j--;
    } else if ((dp[i - 1]?.[j] ?? 0) > (dp[i]?.[j - 1] ?? 0)) {
      i--;
    } else {
      j--;
    }
  }

  return lcs;
}

function computeStats(diff: DiffLine[]): DiffStats {
  return diff.reduce(
    (stats, line) => {
      switch (line.type) {
        case "added":
          stats.added++;
          break;
        case "removed":
          stats.removed++;
          break;
        case "modified":
          stats.modified++;
          break;
        case "unchanged":
          stats.unchanged++;
          break;
      }
      return stats;
    },
    { added: 0, removed: 0, modified: 0, unchanged: 0 }
  );
}

// ============================================================================
// Line Component
// ============================================================================

interface DiffLineRowProps {
  line: DiffLine;
  viewMode: "split" | "unified";
  showLineNumbers: boolean;
}

function DiffLineRow({ line, viewMode, showLineNumbers }: DiffLineRowProps) {
  const getLineClasses = (type: DiffLineType, side: "old" | "new"): string => {
    switch (type) {
      case "added":
        return "bg-green-100 dark:bg-green-900/30";
      case "removed":
        return "bg-red-100 dark:bg-red-900/30";
      case "modified":
        return side === "old"
          ? "bg-yellow-100 dark:bg-yellow-900/30"
          : "bg-blue-100 dark:bg-blue-900/30";
      default:
        return "";
    }
  };

  const getIndicator = (type: DiffLineType, side: "old" | "new"): React.ReactNode => {
    switch (type) {
      case "added":
        return <Plus className="h-3 w-3 text-green-600" />;
      case "removed":
        return <Minus className="h-3 w-3 text-red-600" />;
      case "modified":
        return side === "old" ? (
          <Minus className="h-3 w-3 text-yellow-600" />
        ) : (
          <Plus className="h-3 w-3 text-blue-600" />
        );
      default:
        return <span className="w-3" />;
    }
  };

  if (viewMode === "unified") {
    // Unified view - show changes inline
    if (line.type === "removed" || line.type === "modified") {
      return (
        <div className={cn("flex font-mono text-sm", getLineClasses(line.type, "old"))}>
          {showLineNumbers && (
            <span className="w-12 px-2 text-right text-muted-foreground border-r flex-shrink-0">
              {line.oldLineNumber ?? ""}
            </span>
          )}
          <span className="w-6 flex items-center justify-center flex-shrink-0">
            {getIndicator(line.type, "old")}
          </span>
          <pre className="flex-1 px-2 whitespace-pre-wrap break-all">
            {line.oldContent}
          </pre>
        </div>
      );
    }

    return (
      <div className={cn("flex font-mono text-sm", getLineClasses(line.type, "new"))}>
        {showLineNumbers && (
          <span className="w-12 px-2 text-right text-muted-foreground border-r flex-shrink-0">
            {line.newLineNumber ?? ""}
          </span>
        )}
        <span className="w-6 flex items-center justify-center flex-shrink-0">
          {getIndicator(line.type, "new")}
        </span>
        <pre className="flex-1 px-2 whitespace-pre-wrap break-all">
          {line.newContent}
        </pre>
      </div>
    );
  }

  // Split view - side by side
  return (
    <div className="flex font-mono text-sm">
      {/* Old side */}
      <div
        className={cn(
          "flex flex-1 min-w-0 border-r",
          line.type === "added" ? "bg-muted/30" : getLineClasses(line.type, "old")
        )}
      >
        {showLineNumbers && (
          <span className="w-10 px-2 text-right text-muted-foreground border-r flex-shrink-0">
            {line.oldLineNumber ?? ""}
          </span>
        )}
        <span className="w-5 flex items-center justify-center flex-shrink-0">
          {line.type !== "added" && getIndicator(line.type, "old")}
        </span>
        <pre className="flex-1 px-2 whitespace-pre-wrap break-all overflow-hidden">
          {line.oldContent}
        </pre>
      </div>

      {/* New side */}
      <div
        className={cn(
          "flex flex-1 min-w-0",
          line.type === "removed" ? "bg-muted/30" : getLineClasses(line.type, "new")
        )}
      >
        {showLineNumbers && (
          <span className="w-10 px-2 text-right text-muted-foreground border-r flex-shrink-0">
            {line.newLineNumber ?? ""}
          </span>
        )}
        <span className="w-5 flex items-center justify-center flex-shrink-0">
          {line.type !== "removed" && getIndicator(line.type, "new")}
        </span>
        <pre className="flex-1 px-2 whitespace-pre-wrap break-all overflow-hidden">
          {line.newContent}
        </pre>
      </div>
    </div>
  );
}

// ============================================================================
// Stats Badge Component
// ============================================================================

interface StatsBadgeProps {
  stats: DiffStats;
}

function StatsBadge({ stats }: StatsBadgeProps) {
  return (
    <div className="flex items-center gap-2">
      {stats.added > 0 && (
        <Badge variant="secondary" className="gap-1 bg-green-100 text-green-700">
          <Plus className="h-3 w-3" />
          {stats.added}
        </Badge>
      )}
      {stats.removed > 0 && (
        <Badge variant="secondary" className="gap-1 bg-red-100 text-red-700">
          <Minus className="h-3 w-3" />
          {stats.removed}
        </Badge>
      )}
      {stats.modified > 0 && (
        <Badge variant="secondary" className="gap-1 bg-yellow-100 text-yellow-700">
          <ArrowLeftRight className="h-3 w-3" />
          {stats.modified}
        </Badge>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function DiffViewer({
  oldContent,
  newContent,
  filePath,
  language,
  viewMode: initialViewMode = "split",
  className,
  showLineNumbers = true,
  maxHeight = "500px",
  oldLabel = "Original",
  newLabel = "Modified",
}: DiffViewerProps) {
  const [viewMode, setViewMode] = useState<"split" | "unified">(initialViewMode);
  const [copied, setCopied] = useState<"old" | "new" | null>(null);

  // Compute diff
  const diff = useMemo(() => computeDiff(oldContent, newContent), [oldContent, newContent]);
  const stats = useMemo(() => computeStats(diff), [diff]);

  // Find change indices for navigation
  const changeIndices = useMemo(() => {
    return diff
      .map((line, idx) => (line.type !== "unchanged" ? idx : -1))
      .filter((idx) => idx !== -1);
  }, [diff]);

  const [currentChangeIdx, setCurrentChangeIdx] = useState(0);

  const goToNextChange = useCallback(() => {
    if (changeIndices.length === 0) return;
    setCurrentChangeIdx((prev) => (prev + 1) % changeIndices.length);
  }, [changeIndices.length]);

  const goToPrevChange = useCallback(() => {
    if (changeIndices.length === 0) return;
    setCurrentChangeIdx((prev) => (prev - 1 + changeIndices.length) % changeIndices.length);
  }, [changeIndices.length]);

  const handleCopy = useCallback(
    async (side: "old" | "new") => {
      const content = side === "old" ? oldContent : newContent;
      try {
        await navigator.clipboard.writeText(content);
        setCopied(side);
        setTimeout(() => setCopied(null), 2000);
      } catch (err) {
        console.error("Failed to copy:", err);
      }
    },
    [oldContent, newContent]
  );

  // No changes
  if (diff.length === 0 || (stats.added === 0 && stats.removed === 0 && stats.modified === 0)) {
    return (
      <div className={cn("border rounded-lg overflow-hidden", className)}>
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <FileCode className="h-8 w-8 mr-3 opacity-50" />
          <span>No differences found</span>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("border rounded-lg overflow-hidden flex flex-col", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-muted/50 border-b flex-shrink-0">
        <div className="flex items-center gap-3">
          {filePath && (
            <span className="font-medium text-sm truncate">{filePath}</span>
          )}
          {language && (
            <Badge variant="outline" className="text-xs">
              {language}
            </Badge>
          )}
          <StatsBadge stats={stats} />
        </div>

        <div className="flex items-center gap-1">
          {/* Change navigation */}
          {changeIndices.length > 0 && (
            <>
              <span className="text-xs text-muted-foreground mr-2">
                {currentChangeIdx + 1} / {changeIndices.length} changes
              </span>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={goToPrevChange}
                    >
                      <ChevronUp className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Previous change</TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={goToNextChange}
                    >
                      <ChevronDown className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Next change</TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </>
          )}

          {/* View mode toggle */}
          <div className="flex items-center border rounded ml-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant={viewMode === "split" ? "secondary" : "ghost"}
                    size="icon"
                    className="h-7 w-7 rounded-r-none"
                    onClick={() => setViewMode("split")}
                  >
                    <Columns className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Split view</TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant={viewMode === "unified" ? "secondary" : "ghost"}
                    size="icon"
                    className="h-7 w-7 rounded-l-none"
                    onClick={() => setViewMode("unified")}
                  >
                    <Rows className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Unified view</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </div>

      {/* Column headers for split view */}
      {viewMode === "split" && (
        <div className="flex border-b flex-shrink-0">
          <div className="flex-1 flex items-center justify-between px-4 py-1.5 bg-red-50 dark:bg-red-900/10 border-r">
            <span className="text-sm font-medium text-red-700 dark:text-red-400">
              {oldLabel}
            </span>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 gap-1 text-xs"
              onClick={() => handleCopy("old")}
            >
              {copied === "old" ? (
                <Check className="h-3 w-3 text-green-500" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
              Copy
            </Button>
          </div>
          <div className="flex-1 flex items-center justify-between px-4 py-1.5 bg-green-50 dark:bg-green-900/10">
            <span className="text-sm font-medium text-green-700 dark:text-green-400">
              {newLabel}
            </span>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 gap-1 text-xs"
              onClick={() => handleCopy("new")}
            >
              {copied === "new" ? (
                <Check className="h-3 w-3 text-green-500" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
              Copy
            </Button>
          </div>
        </div>
      )}

      {/* Diff content */}
      <ScrollArea style={{ maxHeight }} className="flex-1">
        <div className="divide-y">
          {diff.map((line, idx) => (
            <DiffLineRow
              key={idx}
              line={line}
              viewMode={viewMode}
              showLineNumbers={showLineNumbers}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}

export default DiffViewer;
