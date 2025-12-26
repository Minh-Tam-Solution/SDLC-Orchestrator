/**
 * =========================================================================
 * DownloadManager - Zip Download with Folder Structure
 * SDLC Orchestrator - Sprint 54 Day 4
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 54 Implementation
 * Authority: Frontend Team + CTO Approved
 * Foundation: CURRENT-SPRINT.md - Sprint 54 Frontend Polish
 *
 * Purpose:
 * - Download generated files as ZIP with folder structure
 * - Download individual files
 * - Show download progress
 * - Support batch selection
 * - Preview before download
 *
 * References:
 * - docs/04-build/02-Sprint-Plans/CURRENT-SPRINT.md
 * =========================================================================
 */

import { useState, useCallback, useMemo } from "react";
import JSZip from "jszip";
import {
  Download,
  FileArchive,
  Folder,
  FileCode,
  Loader2,
  CheckSquare,
  Square,
  FolderOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import type { StreamingFile } from "@/types/streaming";

// ============================================================================
// Types
// ============================================================================

interface DownloadManagerProps {
  /** Files to download */
  files: StreamingFile[];
  /** Project/folder name for ZIP */
  projectName?: string;
  /** Optional class name */
  className?: string;
  /** Disabled state */
  disabled?: boolean;
  /** Compact mode (button only) */
  compact?: boolean;
}

interface FileTreeNode {
  name: string;
  path: string;
  type: "file" | "folder";
  children: FileTreeNode[];
  file?: StreamingFile;
  selected: boolean;
}

// ============================================================================
// Helpers
// ============================================================================

function buildFileTree(
  files: StreamingFile[],
  selectedPaths: Set<string>
): FileTreeNode[] {
  const root: FileTreeNode[] = [];

  for (const file of files) {
    const parts = file.path.split("/").filter((p) => p.length > 0);
    let currentLevel = root;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i] as string;
      const isLastPart = i === parts.length - 1;
      const currentPath = parts.slice(0, i + 1).join("/");

      const existingIdx = currentLevel.findIndex((n) => n.name === part);
      let node: FileTreeNode;

      if (existingIdx === -1) {
        node = {
          name: part,
          path: currentPath,
          type: isLastPart ? "file" : "folder",
          children: [],
          file: isLastPart ? file : undefined,
          selected: selectedPaths.has(currentPath),
        };
        currentLevel.push(node);
      } else {
        node = currentLevel[existingIdx] as FileTreeNode;
        node.selected = selectedPaths.has(node.path);
      }

      if (!isLastPart) {
        currentLevel = node.children;
      }
    }
  }

  // Sort: folders first, then files
  const sortNodes = (nodes: FileTreeNode[]): FileTreeNode[] => {
    return nodes
      .map((n) => ({ ...n, children: sortNodes(n.children) }))
      .sort((a, b) => {
        if (a.type !== b.type) return a.type === "folder" ? -1 : 1;
        return a.name.localeCompare(b.name);
      });
  };

  return sortNodes(root);
}

function getAllFilePaths(nodes: FileTreeNode[]): string[] {
  const paths: string[] = [];

  const traverse = (nodeList: FileTreeNode[]) => {
    for (const node of nodeList) {
      if (node.type === "file") {
        paths.push(node.path);
      } else {
        traverse(node.children);
      }
    }
  };

  traverse(nodes);
  return paths;
}


function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

// ============================================================================
// Tree Node Component
// ============================================================================

interface TreeNodeRowProps {
  node: FileTreeNode;
  depth: number;
  selected: Set<string>;
  onToggle: (path: string, isFolder: boolean) => void;
  expanded: Set<string>;
  onToggleExpand: (path: string) => void;
}

function TreeNodeRow({
  node,
  depth,
  selected,
  onToggle,
  expanded,
  onToggleExpand,
}: TreeNodeRowProps) {
  const isSelected = selected.has(node.path);
  const isExpanded = expanded.has(node.path);

  // For folders, check if all children are selected
  const allChildrenSelected = useMemo(() => {
    if (node.type !== "folder") return false;
    const childPaths = getAllFilePaths([node]);
    return childPaths.length > 0 && childPaths.every((p) => selected.has(p));
  }, [node, selected]);

  const someChildrenSelected = useMemo(() => {
    if (node.type !== "folder") return false;
    const childPaths = getAllFilePaths([node]);
    return childPaths.some((p) => selected.has(p)) && !allChildrenSelected;
  }, [node, selected, allChildrenSelected]);

  return (
    <>
      <div
        className={cn(
          "flex items-center gap-2 py-1.5 px-2 hover:bg-muted/50 rounded cursor-pointer",
          isSelected && node.type === "file" && "bg-primary/10"
        )}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={() => {
          if (node.type === "folder") {
            onToggleExpand(node.path);
          } else {
            onToggle(node.path, false);
          }
        }}
      >
        {/* Checkbox */}
        <Checkbox
          checked={node.type === "folder" ? allChildrenSelected : isSelected}
          // @ts-expect-error - indeterminate is valid but not in types
          indeterminate={someChildrenSelected}
          onCheckedChange={() => onToggle(node.path, node.type === "folder")}
          onClick={(e) => e.stopPropagation()}
          className="h-4 w-4"
        />

        {/* Icon */}
        {node.type === "folder" ? (
          isExpanded ? (
            <FolderOpen className="h-4 w-4 text-yellow-500 flex-shrink-0" />
          ) : (
            <Folder className="h-4 w-4 text-yellow-500 flex-shrink-0" />
          )
        ) : (
          <FileCode className="h-4 w-4 text-blue-500 flex-shrink-0" />
        )}

        {/* Name */}
        <span
          className={cn(
            "flex-1 truncate text-sm",
            node.type === "folder" && "font-medium"
          )}
        >
          {node.name}
        </span>

        {/* File size */}
        {node.type === "file" && node.file && (
          <span className="text-xs text-muted-foreground">
            {formatBytes(node.file.content.length)}
          </span>
        )}
      </div>

      {/* Children */}
      {node.type === "folder" && isExpanded && (
        <>
          {node.children.map((child) => (
            <TreeNodeRow
              key={child.path}
              node={child}
              depth={depth + 1}
              selected={selected}
              onToggle={onToggle}
              expanded={expanded}
              onToggleExpand={onToggleExpand}
            />
          ))}
        </>
      )}
    </>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function DownloadManager({
  files,
  projectName = "generated-code",
  className,
  disabled = false,
  compact = false,
}: DownloadManagerProps) {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);

  // Build file tree
  const fileTree = useMemo(
    () => buildFileTree(files, selected),
    [files, selected]
  );

  // Get all file paths
  const allFilePaths = useMemo(() => getAllFilePaths(fileTree), [fileTree]);

  // Initialize selection with all files when dialog opens
  const handleOpenChange = useCallback(
    (isOpen: boolean) => {
      setOpen(isOpen);
      if (isOpen) {
        setSelected(new Set(allFilePaths));
        // Expand first level folders
        const firstLevelFolders = fileTree
          .filter((n) => n.type === "folder")
          .map((n) => n.path);
        setExpanded(new Set(firstLevelFolders));
      }
    },
    [allFilePaths, fileTree]
  );

  // Toggle file/folder selection
  const handleToggle = useCallback(
    (path: string, isFolder: boolean) => {
      setSelected((prev) => {
        const next = new Set(prev);

        if (isFolder) {
          // Find all files in this folder
          const folderNode = fileTree.find((n) => n.path === path);
          const childPaths = folderNode ? getAllFilePaths([folderNode]) : [];

          // If all are selected, deselect all; otherwise select all
          const allSelected = childPaths.every((p) => next.has(p));

          childPaths.forEach((p) => {
            if (allSelected) {
              next.delete(p);
            } else {
              next.add(p);
            }
          });
        } else {
          if (next.has(path)) {
            next.delete(path);
          } else {
            next.add(path);
          }
        }

        return next;
      });
    },
    [fileTree]
  );

  // Toggle folder expansion
  const handleToggleExpand = useCallback((path: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  }, []);

  // Select/deselect all
  const handleSelectAll = useCallback(() => {
    if (selected.size === allFilePaths.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(allFilePaths));
    }
  }, [allFilePaths, selected.size]);

  // Download as ZIP
  const handleDownload = useCallback(async () => {
    if (selected.size === 0) return;

    setIsDownloading(true);
    setDownloadProgress(0);

    try {
      const zip = new JSZip();
      const selectedFiles = files.filter((f) => selected.has(f.path));
      let processed = 0;

      for (const file of selectedFiles) {
        zip.file(file.path, file.content);
        processed++;
        setDownloadProgress(Math.round((processed / selectedFiles.length) * 100));
      }

      const blob = await zip.generateAsync({
        type: "blob",
        compression: "DEFLATE",
        compressionOptions: { level: 6 },
      });

      // Create download link
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${projectName}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setOpen(false);
    } catch (err) {
      console.error("Download failed:", err);
    } finally {
      setIsDownloading(false);
      setDownloadProgress(0);
    }
  }, [files, projectName, selected]);

  // Quick download (all files)
  const handleQuickDownload = useCallback(async () => {
    if (files.length === 0) return;

    setIsDownloading(true);

    try {
      const zip = new JSZip();

      for (const file of files) {
        zip.file(file.path, file.content);
      }

      const blob = await zip.generateAsync({
        type: "blob",
        compression: "DEFLATE",
        compressionOptions: { level: 6 },
      });

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${projectName}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download failed:", err);
    } finally {
      setIsDownloading(false);
    }
  }, [files, projectName]);

  // Calculate total size
  const totalSize = useMemo(() => {
    return files.reduce((sum, f) => sum + f.content.length, 0);
  }, [files]);

  const selectedSize = useMemo(() => {
    return files
      .filter((f) => selected.has(f.path))
      .reduce((sum, f) => sum + f.content.length, 0);
  }, [files, selected]);

  if (compact) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={handleQuickDownload}
        disabled={disabled || files.length === 0 || isDownloading}
        className={cn("gap-2", className)}
      >
        {isDownloading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Download className="h-4 w-4" />
        )}
        Download ZIP
      </Button>
    );
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          disabled={disabled || files.length === 0}
          className={cn("gap-2", className)}
        >
          <FileArchive className="h-4 w-4" />
          Download ({files.length} files)
        </Button>
      </DialogTrigger>

      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileArchive className="h-5 w-5" />
            Download Files
          </DialogTitle>
          <DialogDescription>
            Select files to include in the download. Files will be packaged as a
            ZIP with folder structure preserved.
          </DialogDescription>
        </DialogHeader>

        {/* Stats bar */}
        <div className="flex items-center justify-between py-2 px-3 bg-muted/30 rounded border">
          <div className="flex items-center gap-4 text-sm">
            <span className="text-muted-foreground">
              {selected.size} of {allFilePaths.length} files selected
            </span>
            <Badge variant="secondary">
              {formatBytes(selectedSize)} / {formatBytes(totalSize)}
            </Badge>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSelectAll}
            className="gap-1 h-7"
          >
            {selected.size === allFilePaths.length ? (
              <>
                <Square className="h-3.5 w-3.5" />
                Deselect All
              </>
            ) : (
              <>
                <CheckSquare className="h-3.5 w-3.5" />
                Select All
              </>
            )}
          </Button>
        </div>

        {/* File tree */}
        <ScrollArea className="flex-1 border rounded max-h-[400px]">
          <div className="py-2">
            {fileTree.map((node) => (
              <TreeNodeRow
                key={node.path}
                node={node}
                depth={0}
                selected={selected}
                onToggle={handleToggle}
                expanded={expanded}
                onToggleExpand={handleToggleExpand}
              />
            ))}
          </div>
        </ScrollArea>

        {/* Download progress */}
        {isDownloading && (
          <div className="space-y-2">
            <Progress value={downloadProgress} className="h-2" />
            <p className="text-xs text-center text-muted-foreground">
              Packaging files... {downloadProgress}%
            </p>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleDownload}
            disabled={selected.size === 0 || isDownloading}
            className="gap-2"
          >
            {isDownloading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Packaging...
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                Download {selected.size > 0 && `(${selected.size} files)`}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default DownloadManager;
