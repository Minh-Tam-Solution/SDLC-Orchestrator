/**
 * =========================================================================
 * CodePreviewPanel - Syntax-Highlighted Code Viewer
 * SDLC Orchestrator - Sprint 54 Day 2
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 54 Implementation
 * Authority: Frontend Team + CTO Approved
 * Foundation: CURRENT-SPRINT.md - Sprint 54 Frontend Polish
 *
 * Purpose:
 * - Display generated code with syntax highlighting
 * - Support multiple languages (Python, TypeScript, JSON, YAML, etc.)
 * - Show file metadata (path, lines, language)
 * - Copy to clipboard functionality
 * - Line numbers with highlighting
 * - Search within code
 * - Keyboard navigation
 *
 * References:
 * - docs/04-build/02-Sprint-Plans/CURRENT-SPRINT.md
 * - frontend/web/src/components/codegen/CopyableCodeBlock.tsx
 * =========================================================================
 */

import { useState, useCallback, useMemo, useRef, useEffect } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark, oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import {
  Copy,
  Check,
  FileCode,
  FileJson,
  FileText,
  Code2,
  Cog,
  X,
  Search,
  ChevronUp,
  ChevronDown,
  Download,
  Maximize2,
  Minimize2,
  Sun,
  Moon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
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

interface CodePreviewPanelProps {
  /** File to preview */
  file: StreamingFile | null;
  /** Optional class name */
  className?: string;
  /** Show header with file info */
  showHeader?: boolean;
  /** Show toolbar with actions */
  showToolbar?: boolean;
  /** Show line numbers */
  showLineNumbers?: boolean;
  /** Max height (default: 100%) */
  maxHeight?: string;
  /** Callback when file is downloaded */
  onDownload?: (file: StreamingFile) => void;
  /** Callback when panel is closed */
  onClose?: () => void;
  /** Enable full screen mode */
  allowFullScreen?: boolean;
  /** Initial theme */
  initialTheme?: "dark" | "light";
}

interface SearchMatch {
  lineNumber: number;
  startIndex: number;
  endIndex: number;
}

// ============================================================================
// Language Helpers
// ============================================================================

function getLanguageIcon(language: string): React.ReactNode {
  const iconClass = "h-4 w-4";

  switch (language) {
    case "python":
      return <Code2 className={cn(iconClass, "text-yellow-500")} />;
    case "typescript":
    case "javascript":
    case "tsx":
    case "jsx":
      return <FileCode className={cn(iconClass, "text-blue-500")} />;
    case "json":
      return <FileJson className={cn(iconClass, "text-yellow-600")} />;
    case "yaml":
    case "yml":
    case "toml":
    case "ini":
      return <Cog className={cn(iconClass, "text-purple-500")} />;
    case "markdown":
    case "md":
      return <FileText className={cn(iconClass, "text-gray-500")} />;
    case "sql":
      return <FileCode className={cn(iconClass, "text-green-500")} />;
    default:
      return <FileCode className={cn(iconClass, "text-gray-400")} />;
  }
}

function getLanguageLabel(language: string): string {
  const labels: Record<string, string> = {
    python: "Python",
    typescript: "TypeScript",
    javascript: "JavaScript",
    tsx: "TypeScript React",
    jsx: "JavaScript React",
    json: "JSON",
    yaml: "YAML",
    yml: "YAML",
    toml: "TOML",
    ini: "INI",
    markdown: "Markdown",
    md: "Markdown",
    sql: "SQL",
    html: "HTML",
    css: "CSS",
    bash: "Bash",
    shell: "Shell",
    text: "Plain Text",
  };

  return labels[language] || language.toUpperCase();
}

function getPrismLanguage(language: string): string {
  const mapping: Record<string, string> = {
    py: "python",
    ts: "typescript",
    tsx: "tsx",
    js: "javascript",
    jsx: "jsx",
    yml: "yaml",
    md: "markdown",
    sh: "bash",
    txt: "text",
  };

  return mapping[language] || language;
}

// ============================================================================
// Search Helpers
// ============================================================================

function findMatches(content: string, searchTerm: string): SearchMatch[] {
  if (!searchTerm || searchTerm.length < 2) return [];

  const matches: SearchMatch[] = [];
  const lines = content.split("\n");
  const searchLower = searchTerm.toLowerCase();

  lines.forEach((line, lineIndex) => {
    const lineLower = line.toLowerCase();
    let startIndex = 0;

    while (true) {
      const index = lineLower.indexOf(searchLower, startIndex);
      if (index === -1) break;

      matches.push({
        lineNumber: lineIndex + 1,
        startIndex: index,
        endIndex: index + searchTerm.length,
      });

      startIndex = index + 1;
    }
  });

  return matches;
}

// ============================================================================
// Empty State Component
// ============================================================================

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full py-12 text-muted-foreground">
      <FileCode className="h-16 w-16 mb-4 opacity-30" />
      <p className="text-lg font-medium">No file selected</p>
      <p className="text-sm mt-1">Select a file from the list to preview</p>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function CodePreviewPanel({
  file,
  className,
  showHeader = true,
  showToolbar = true,
  showLineNumbers = true,
  maxHeight = "100%",
  onDownload,
  onClose,
  allowFullScreen = true,
  initialTheme = "dark",
}: CodePreviewPanelProps) {
  // State
  const [copied, setCopied] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light">(initialTheme);
  const [showSearch, setShowSearch] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentMatchIndex, setCurrentMatchIndex] = useState(0);

  // Refs
  const searchInputRef = useRef<HTMLInputElement>(null);
  const codeContainerRef = useRef<HTMLDivElement>(null);

  // Computed
  const matches = useMemo(() => {
    if (!file) return [];
    return findMatches(file.content, searchTerm);
  }, [file, searchTerm]);

  // Reset search when file changes
  useEffect(() => {
    setSearchTerm("");
    setCurrentMatchIndex(0);
    setShowSearch(false);
  }, [file?.path]);

  // Focus search input when shown
  useEffect(() => {
    if (showSearch && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [showSearch]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + F for search
      if ((e.metaKey || e.ctrlKey) && e.key === "f") {
        e.preventDefault();
        setShowSearch(true);
      }
      // Escape to close search
      if (e.key === "Escape" && showSearch) {
        setShowSearch(false);
        setSearchTerm("");
      }
      // Enter to go to next match
      if (e.key === "Enter" && showSearch && matches.length > 0) {
        e.preventDefault();
        if (e.shiftKey) {
          goToPreviousMatch();
        } else {
          goToNextMatch();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [showSearch, matches.length]);

  // Handlers
  const handleCopy = useCallback(async () => {
    if (!file) return;

    try {
      await navigator.clipboard.writeText(file.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  }, [file]);

  const handleDownload = useCallback(() => {
    if (!file) return;

    if (onDownload) {
      onDownload(file);
    } else {
      // Default download behavior
      const blob = new Blob([file.content], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.path.split("/").pop() || "file.txt";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  }, [file, onDownload]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  const toggleFullScreen = useCallback(() => {
    setIsFullScreen((prev) => !prev);
  }, []);

  const goToNextMatch = useCallback(() => {
    if (matches.length === 0) return;
    setCurrentMatchIndex((prev) => (prev + 1) % matches.length);
  }, [matches.length]);

  const goToPreviousMatch = useCallback(() => {
    if (matches.length === 0) return;
    setCurrentMatchIndex((prev) => (prev - 1 + matches.length) % matches.length);
  }, [matches.length]);

  // Scroll to current match
  useEffect(() => {
    if (matches.length > 0 && codeContainerRef.current) {
      const match = matches[currentMatchIndex];
      if (match) {
        // Find line element and scroll to it
        const lineElements = codeContainerRef.current.querySelectorAll(
          ".react-syntax-highlighter-line-number"
        );
        const targetLine = lineElements[match.lineNumber - 1];
        if (targetLine) {
          targetLine.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }
    }
  }, [currentMatchIndex, matches]);

  // Empty state
  if (!file) {
    return (
      <div className={cn("flex flex-col h-full bg-background", className)}>
        <EmptyState />
      </div>
    );
  }

  const prismLanguage = getPrismLanguage(file.language);
  const syntaxStyle = theme === "dark" ? oneDark : oneLight;

  return (
    <div
      className={cn(
        "flex flex-col bg-background border rounded-lg overflow-hidden",
        isFullScreen && "fixed inset-4 z-50 shadow-2xl",
        className
      )}
      style={{ maxHeight: isFullScreen ? undefined : maxHeight }}
    >
      {/* Header */}
      {showHeader && (
        <div className="flex items-center justify-between px-4 py-2 bg-muted/50 border-b flex-shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            {getLanguageIcon(file.language)}
            <span className="font-medium truncate" title={file.path}>
              {file.path}
            </span>
            <Badge variant="secondary" className="text-xs flex-shrink-0">
              {getLanguageLabel(file.language)}
            </Badge>
          </div>

          <div className="flex items-center gap-1 flex-shrink-0">
            <span className="text-xs text-muted-foreground mr-2">
              {file.lines} lines
            </span>

            {file.status === "error" && (
              <Badge variant="destructive" className="text-xs">
                Syntax Error
              </Badge>
            )}

            {onClose && (
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Search bar */}
      {showSearch && (
        <div className="flex items-center gap-2 px-4 py-2 bg-muted/30 border-b flex-shrink-0">
          <Search className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          <Input
            ref={searchInputRef}
            type="text"
            placeholder="Search in file..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentMatchIndex(0);
            }}
            className="h-7 text-sm flex-1"
          />
          {matches.length > 0 && (
            <>
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {currentMatchIndex + 1} of {matches.length}
              </span>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={goToPreviousMatch}
              >
                <ChevronUp className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={goToNextMatch}
              >
                <ChevronDown className="h-4 w-4" />
              </Button>
            </>
          )}
          {searchTerm && matches.length === 0 && (
            <span className="text-xs text-muted-foreground">No matches</span>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => {
              setShowSearch(false);
              setSearchTerm("");
            }}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Toolbar */}
      {showToolbar && (
        <div className="flex items-center justify-between px-4 py-1.5 bg-muted/30 border-b flex-shrink-0">
          <div className="flex items-center gap-1">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 gap-1.5"
                    onClick={() => setShowSearch(!showSearch)}
                  >
                    <Search className="h-3.5 w-3.5" />
                    <span className="text-xs">Search</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Search (Cmd+F)</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>

          <div className="flex items-center gap-1">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={toggleTheme}
                  >
                    {theme === "dark" ? (
                      <Sun className="h-3.5 w-3.5" />
                    ) : (
                      <Moon className="h-3.5 w-3.5" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{theme === "dark" ? "Light theme" : "Dark theme"}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={handleDownload}
                  >
                    <Download className="h-3.5 w-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Download file</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={handleCopy}
                  >
                    {copied ? (
                      <Check className="h-3.5 w-3.5 text-green-500" />
                    ) : (
                      <Copy className="h-3.5 w-3.5" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{copied ? "Copied!" : "Copy to clipboard"}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            {allowFullScreen && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={toggleFullScreen}
                    >
                      {isFullScreen ? (
                        <Minimize2 className="h-3.5 w-3.5" />
                      ) : (
                        <Maximize2 className="h-3.5 w-3.5" />
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{isFullScreen ? "Exit full screen" : "Full screen"}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
        </div>
      )}

      {/* Code content */}
      <ScrollArea className="flex-1" ref={codeContainerRef}>
        <SyntaxHighlighter
          language={prismLanguage}
          style={syntaxStyle}
          showLineNumbers={showLineNumbers}
          wrapLines={true}
          lineProps={(lineNumber) => {
            const isHighlighted = matches.some(
              (m) => m.lineNumber === lineNumber
            );
            const isCurrentMatch =
              matches[currentMatchIndex]?.lineNumber === lineNumber;

            return {
              style: {
                display: "block",
                backgroundColor: isCurrentMatch
                  ? theme === "dark"
                    ? "rgba(234, 179, 8, 0.3)"
                    : "rgba(234, 179, 8, 0.4)"
                  : isHighlighted
                  ? theme === "dark"
                    ? "rgba(234, 179, 8, 0.15)"
                    : "rgba(234, 179, 8, 0.2)"
                  : undefined,
              },
            };
          }}
          customStyle={{
            margin: 0,
            borderRadius: 0,
            fontSize: "13px",
            lineHeight: "1.6",
            minHeight: "100%",
          }}
          codeTagProps={{
            style: {
              fontFamily:
                'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
            },
          }}
        >
          {file.content || "// Empty file"}
        </SyntaxHighlighter>
      </ScrollArea>

      {/* Full screen overlay backdrop */}
      {isFullScreen && (
        <div
          className="fixed inset-0 bg-black/50 -z-10"
          onClick={toggleFullScreen}
        />
      )}
    </div>
  );
}

export default CodePreviewPanel;
