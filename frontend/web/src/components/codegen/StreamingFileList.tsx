/**
 * =========================================================================
 * StreamingFileList - Real-time File List with Progress
 * SDLC Orchestrator - Sprint 54 Day 1
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 54 Implementation
 * Authority: Frontend Team + CTO Approved
 * Foundation: CURRENT-SPRINT.md - Sprint 54 Frontend Polish
 *
 * Purpose:
 * - Display real-time file generation progress
 * - Show file tree structure with folder collapsing
 * - Animate file additions
 * - Display file status (generating, valid, error)
 * - Allow file selection for preview
 * - Show overall generation progress
 *
 * References:
 * - docs/04-build/02-Sprint-Plans/CURRENT-SPRINT.md
 * - frontend/web/src/types/streaming.ts
 * =========================================================================
 */

import { useMemo, useState, useCallback, useEffect, useRef } from "react";
import {
  FileCode,
  Folder,
  FolderOpen,
  ChevronRight,
  ChevronDown,
  Loader2,
  Check,
  AlertCircle,
  File,
  Code2,
  FileJson,
  FileText,
  Cog,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { StreamingFile } from "@/types/streaming";

// ============================================================================
// Types
// ============================================================================

interface StreamingFileListProps {
  /** List of files being streamed */
  files: StreamingFile[];
  /** Total expected files (for progress) */
  totalExpected?: number;
  /** Whether generation is in progress */
  isGenerating: boolean;
  /** Currently selected file path */
  selectedPath?: string;
  /** Callback when file is selected */
  onFileSelect?: (file: StreamingFile) => void;
  /** Current file being generated */
  currentGeneratingPath?: string;
  /** Optional class name */
  className?: string;
  /** Show detailed stats */
  showStats?: boolean;
  /** Generation start time for duration display */
  startTime?: Date;
}

interface FileTreeNode {
  name: string;
  path: string;
  type: "file" | "folder";
  children: FileTreeNode[];
  file?: StreamingFile;
  isExpanded?: boolean;
}

// ============================================================================
// File Icon Helpers
// ============================================================================

function getFileIcon(path: string, language: string): React.ReactNode {
  const ext = path.split(".").pop()?.toLowerCase() || "";
  const iconClass = "h-4 w-4";

  // Language-specific icons
  switch (language) {
    case "python":
      return <Code2 className={cn(iconClass, "text-yellow-500")} />;
    case "typescript":
    case "javascript":
      return <FileCode className={cn(iconClass, "text-blue-500")} />;
    case "json":
      return <FileJson className={cn(iconClass, "text-yellow-600")} />;
    case "yaml":
    case "toml":
    case "ini":
      return <Cog className={cn(iconClass, "text-purple-500")} />;
    case "markdown":
      return <FileText className={cn(iconClass, "text-gray-500")} />;
    case "sql":
      return <FileCode className={cn(iconClass, "text-green-500")} />;
  }

  // Extension-based fallback
  switch (ext) {
    case "py":
      return <Code2 className={cn(iconClass, "text-yellow-500")} />;
    case "ts":
    case "tsx":
      return <FileCode className={cn(iconClass, "text-blue-500")} />;
    case "js":
    case "jsx":
      return <FileCode className={cn(iconClass, "text-yellow-400")} />;
    case "json":
      return <FileJson className={cn(iconClass, "text-yellow-600")} />;
    case "md":
      return <FileText className={cn(iconClass, "text-gray-500")} />;
    case "txt":
      return <FileText className={cn(iconClass, "text-gray-400")} />;
    case "yml":
    case "yaml":
      return <Cog className={cn(iconClass, "text-purple-500")} />;
    default:
      return <File className={cn(iconClass, "text-gray-400")} />;
  }
}

function getStatusIcon(status: StreamingFile["status"]): React.ReactNode {
  const iconClass = "h-3.5 w-3.5";
  switch (status) {
    case "generating":
      return <Loader2 className={cn(iconClass, "text-blue-500 animate-spin")} />;
    case "valid":
      return <Check className={cn(iconClass, "text-green-500")} />;
    case "error":
      return <AlertCircle className={cn(iconClass, "text-red-500")} />;
  }
}

// ============================================================================
// File Tree Builder
// ============================================================================

function buildFileTree(files: StreamingFile[]): FileTreeNode[] {
  const root: FileTreeNode[] = [];

  for (const file of files) {
    const parts = file.path.split("/").filter((p) => p.length > 0);
    let currentLevel = root;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i] as string; // Safe after filter
      const isLastPart = i === parts.length - 1;
      const currentPath = parts.slice(0, i + 1).join("/");

      // Find existing node
      const existingNodeIndex = currentLevel.findIndex((n) => n.name === part);
      let node: FileTreeNode;

      if (existingNodeIndex === -1) {
        // Create new node
        node = {
          name: part,
          path: currentPath,
          type: isLastPart ? "file" : "folder",
          children: [],
          file: isLastPart ? file : undefined,
          isExpanded: true, // Default expanded
        };
        currentLevel.push(node);
      } else {
        node = currentLevel[existingNodeIndex] as FileTreeNode;
      }

      if (!isLastPart) {
        currentLevel = node.children;
      }
    }
  }

  // Sort: folders first, then files, alphabetically
  const sortNodes = (nodes: FileTreeNode[]): FileTreeNode[] => {
    return nodes
      .map((node) => ({
        ...node,
        children: sortNodes(node.children),
      }))
      .sort((a, b) => {
        if (a.type !== b.type) {
          return a.type === "folder" ? -1 : 1;
        }
        return a.name.localeCompare(b.name);
      });
  };

  return sortNodes(root);
}

// ============================================================================
// Stats Component
// ============================================================================

interface StatsBarProps {
  files: StreamingFile[];
  totalExpected?: number;
  isGenerating: boolean;
  startTime?: Date;
}

function StatsBar({ files, totalExpected, isGenerating, startTime }: StatsBarProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!isGenerating || !startTime) return;

    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime.getTime()) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [isGenerating, startTime]);

  const stats = useMemo(() => {
    const valid = files.filter((f) => f.status === "valid").length;
    const errors = files.filter((f) => f.status === "error").length;
    const generating = files.filter((f) => f.status === "generating").length;
    const totalLines = files.reduce((sum, f) => sum + f.lines, 0);

    return { valid, errors, generating, totalLines };
  }, [files]);

  const progress = totalExpected
    ? Math.round((files.length / totalExpected) * 100)
    : 0;

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="space-y-2 p-3 bg-muted/30 rounded-lg border border-border/50">
      {/* Progress bar */}
      <div className="flex items-center gap-3">
        <Progress value={progress} className="flex-1 h-2" />
        <span className="text-sm font-medium text-muted-foreground w-12 text-right">
          {progress}%
        </span>
      </div>

      {/* Stats row */}
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-muted-foreground">
            <File className="h-3 w-3" />
            {files.length}
            {totalExpected ? `/${totalExpected}` : ""} files
          </span>
          <span className="flex items-center gap-1 text-muted-foreground">
            <Code2 className="h-3 w-3" />
            {stats.totalLines.toLocaleString()} lines
          </span>
        </div>

        <div className="flex items-center gap-2">
          {stats.generating > 0 && (
            <Badge variant="secondary" className="gap-1 text-xs py-0 h-5">
              <Loader2 className="h-3 w-3 animate-spin" />
              {stats.generating}
            </Badge>
          )}
          {stats.valid > 0 && (
            <Badge variant="secondary" className="gap-1 text-xs py-0 h-5 bg-green-100 text-green-700">
              <Check className="h-3 w-3" />
              {stats.valid}
            </Badge>
          )}
          {stats.errors > 0 && (
            <Badge variant="destructive" className="gap-1 text-xs py-0 h-5">
              <AlertCircle className="h-3 w-3" />
              {stats.errors}
            </Badge>
          )}
          {startTime && (
            <span className="text-muted-foreground">
              {formatTime(elapsed)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Tree Node Component
// ============================================================================

interface TreeNodeProps {
  node: FileTreeNode;
  depth: number;
  selectedPath?: string;
  currentGeneratingPath?: string;
  onFileSelect?: (file: StreamingFile) => void;
  expandedPaths: Set<string>;
  toggleExpanded: (path: string) => void;
  isNew?: boolean;
}

function TreeNode({
  node,
  depth,
  selectedPath,
  currentGeneratingPath,
  onFileSelect,
  expandedPaths,
  toggleExpanded,
  isNew,
}: TreeNodeProps) {
  const isExpanded = expandedPaths.has(node.path);
  const isSelected = node.path === selectedPath;
  const isGenerating = node.path === currentGeneratingPath;

  const handleClick = useCallback(() => {
    if (node.type === "folder") {
      toggleExpanded(node.path);
    } else if (node.file && onFileSelect) {
      onFileSelect(node.file);
    }
  }, [node, toggleExpanded, onFileSelect]);

  return (
    <div>
      <button
        onClick={handleClick}
        className={cn(
          "w-full flex items-center gap-1.5 py-1 px-2 text-sm text-left",
          "hover:bg-muted/50 rounded transition-colors",
          isSelected && "bg-primary/10 text-primary hover:bg-primary/15",
          isGenerating && "bg-blue-50 dark:bg-blue-900/20",
          isNew && "animate-pulse"
        )}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {/* Expand/collapse icon for folders */}
        {node.type === "folder" ? (
          <span className="w-4 h-4 flex items-center justify-center">
            {isExpanded ? (
              <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
            )}
          </span>
        ) : (
          <span className="w-4" />
        )}

        {/* Icon */}
        {node.type === "folder" ? (
          isExpanded ? (
            <FolderOpen className="h-4 w-4 text-yellow-500 flex-shrink-0" />
          ) : (
            <Folder className="h-4 w-4 text-yellow-500 flex-shrink-0" />
          )
        ) : (
          getFileIcon(node.path, node.file?.language || "")
        )}

        {/* Name */}
        <span
          className={cn(
            "flex-1 truncate",
            node.type === "folder" && "font-medium"
          )}
        >
          {node.name}
        </span>

        {/* Status icon for files */}
        {node.type === "file" && node.file && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="flex-shrink-0">
                  {getStatusIcon(node.file.status)}
                </span>
              </TooltipTrigger>
              <TooltipContent side="right" className="text-xs">
                {node.file.status === "generating" && "Generating..."}
                {node.file.status === "valid" &&
                  `${node.file.lines} lines · ${node.file.language}`}
                {node.file.status === "error" && "Syntax error"}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {/* Lines count for files */}
        {node.type === "file" && node.file?.status === "valid" && (
          <span className="text-xs text-muted-foreground flex-shrink-0">
            {node.file.lines}L
          </span>
        )}
      </button>

      {/* Children */}
      {node.type === "folder" && isExpanded && (
        <div>
          {node.children.map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              currentGeneratingPath={currentGeneratingPath}
              onFileSelect={onFileSelect}
              expandedPaths={expandedPaths}
              toggleExpanded={toggleExpanded}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function StreamingFileList({
  files,
  totalExpected,
  isGenerating,
  selectedPath,
  onFileSelect,
  currentGeneratingPath,
  className,
  showStats = true,
  startTime,
}: StreamingFileListProps) {
  // Track expanded folders
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set());

  // Track recently added files for animation
  const [newFiles, setNewFiles] = useState<Set<string>>(new Set());
  const prevFileCountRef = useRef(0);

  // Build file tree
  const fileTree = useMemo(() => buildFileTree(files), [files]);

  // Auto-expand all folders by default
  useEffect(() => {
    const allFolderPaths = new Set<string>();

    const collectFolderPaths = (nodes: FileTreeNode[]) => {
      for (const node of nodes) {
        if (node.type === "folder") {
          allFolderPaths.add(node.path);
          collectFolderPaths(node.children);
        }
      }
    };

    collectFolderPaths(fileTree);
    setExpandedPaths(allFolderPaths);
  }, [fileTree]);

  // Track new files for animation
  useEffect(() => {
    if (files.length > prevFileCountRef.current) {
      const newFilePaths = files
        .slice(prevFileCountRef.current)
        .map((f) => f.path);

      setNewFiles((prev) => {
        const updated = new Set(prev);
        newFilePaths.forEach((p) => updated.add(p));
        return updated;
      });

      // Remove animation class after animation completes
      const timer = setTimeout(() => {
        setNewFiles((prev) => {
          const updated = new Set(prev);
          newFilePaths.forEach((p) => updated.delete(p));
          return updated;
        });
      }, 1000);

      prevFileCountRef.current = files.length;
      return () => clearTimeout(timer);
    }
    prevFileCountRef.current = files.length;
    return undefined;
  }, [files]);

  const toggleExpanded = useCallback((path: string) => {
    setExpandedPaths((prev) => {
      const updated = new Set(prev);
      if (updated.has(path)) {
        updated.delete(path);
      } else {
        updated.add(path);
      }
      return updated;
    });
  }, []);

  const expandAll = useCallback(() => {
    const allFolderPaths = new Set<string>();
    const collectFolderPaths = (nodes: FileTreeNode[]) => {
      for (const node of nodes) {
        if (node.type === "folder") {
          allFolderPaths.add(node.path);
          collectFolderPaths(node.children);
        }
      }
    };
    collectFolderPaths(fileTree);
    setExpandedPaths(allFolderPaths);
  }, [fileTree]);

  const collapseAll = useCallback(() => {
    setExpandedPaths(new Set());
  }, []);

  if (files.length === 0 && !isGenerating) {
    return (
      <div
        className={cn(
          "flex flex-col items-center justify-center py-12 text-muted-foreground",
          className
        )}
      >
        <FileCode className="h-12 w-12 mb-3 opacity-30" />
        <p className="text-sm">No files generated yet</p>
        <p className="text-xs mt-1">Start generation to see files here</p>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Stats bar */}
      {showStats && (
        <div className="flex-shrink-0 mb-3">
          <StatsBar
            files={files}
            totalExpected={totalExpected}
            isGenerating={isGenerating}
            startTime={startTime}
          />
        </div>
      )}

      {/* Toolbar */}
      <div className="flex items-center justify-between mb-2 px-1">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Generated Files
        </span>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs"
            onClick={expandAll}
          >
            Expand All
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs"
            onClick={collapseAll}
          >
            Collapse
          </Button>
        </div>
      </div>

      {/* File tree */}
      <ScrollArea className="flex-1">
        <div className="pb-4">
          {fileTree.map((node) => (
            <TreeNode
              key={node.path}
              node={node}
              depth={0}
              selectedPath={selectedPath}
              currentGeneratingPath={currentGeneratingPath}
              onFileSelect={onFileSelect}
              expandedPaths={expandedPaths}
              toggleExpanded={toggleExpanded}
              isNew={newFiles.has(node.path)}
            />
          ))}
        </div>
      </ScrollArea>

      {/* Generation indicator */}
      {isGenerating && (
        <div className="flex-shrink-0 mt-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
          <div className="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-300">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>
              {currentGeneratingPath
                ? `Generating: ${currentGeneratingPath}`
                : "Waiting for next file..."}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default StreamingFileList;
