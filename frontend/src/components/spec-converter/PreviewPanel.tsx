/**
 * PreviewPanel Component
 * Sprint 155 Day 4 - Track 1: Visual Editor Integration
 *
 * Displays live format preview of spec content.
 *
 * Features:
 * - Real-time SpecIR → format conversion
 * - Support for OpenSpec, BDD, User Story formats
 * - Syntax highlighting
 * - Copy to clipboard functionality
 *
 * Architecture: ADR-050 Visual Editor
 */

"use client";

import * as React from "react";
import { SpecIR, SpecFormat } from "@/hooks/useSpecConverter";
import { cn } from "@/lib/utils";
import { Copy, Check, AlertCircle, RefreshCw, FileText } from "lucide-react";

// =============================================================================
// Types
// =============================================================================

interface PreviewPanelProps {
  spec: SpecIR;
  content: string;
  format: SpecFormat;
  onFormatChange: (format: SpecFormat) => void;
  loading?: boolean;
  error?: string;
  onRetry?: () => void;
  className?: string;
}

// =============================================================================
// Constants
// =============================================================================

const FORMAT_OPTIONS: { value: SpecFormat; label: string }[] = [
  { value: "BDD", label: "BDD" },
  { value: "OPENSPEC", label: "OpenSpec" },
  { value: "USER_STORY", label: "User Story" },
];

// =============================================================================
// Main Component
// =============================================================================

export function PreviewPanel({
  spec,
  content,
  format,
  onFormatChange,
  loading = false,
  error,
  onRetry,
  className,
}: PreviewPanelProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      console.error("Failed to copy to clipboard");
    }
  };

  const handleFormatChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFormatChange(e.target.value as SpecFormat);
  };

  const hasContent = content.trim().length > 0;
  const hasRequirements =
    spec.requirements.length > 0 || spec.acceptance_criteria.length > 0;

  return (
    <div className={cn("flex flex-col h-full border rounded-lg", className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-muted/30">
        <h3 className="text-lg font-semibold" role="heading">
          Preview
        </h3>
        <div className="flex items-center gap-3">
          {/* Format Selector */}
          <div className="flex items-center gap-2">
            <label htmlFor="format-select" className="text-sm text-muted-foreground">
              Format:
            </label>
            <select
              id="format-select"
              aria-label="Format"
              value={format}
              onChange={handleFormatChange}
              className="h-9 px-3 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {FORMAT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Copy Button */}
          <button
            type="button"
            onClick={handleCopy}
            disabled={loading || !hasContent}
            aria-label="Copy to clipboard"
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md border",
              "hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed",
              copied && "bg-green-100 text-green-700 border-green-300"
            )}
          >
            {copied ? (
              <>
                <Check className="h-4 w-4" />
                <span role="status">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="h-4 w-4" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto p-4">
        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center h-full gap-3">
            <div
              role="progressbar"
              className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin"
            />
            <p className="text-sm text-muted-foreground">Generating preview...</p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-destructive">
            <AlertCircle className="h-12 w-12" data-testid="error-icon" />
            <p className="text-sm font-medium">{error}</p>
            {onRetry && (
              <button
                type="button"
                onClick={onRetry}
                aria-label="Retry"
                className="flex items-center gap-1.5 px-4 py-2 text-sm bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90"
              >
                <RefreshCw className="h-4 w-4" />
                Retry
              </button>
            )}
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && !hasContent && (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground">
            <FileText className="h-12 w-12 opacity-50" />
            <p className="text-sm font-medium">No preview available</p>
            {!hasRequirements && (
              <p className="text-xs">Add requirements to see preview</p>
            )}
          </div>
        )}

        {/* Content Display */}
        {!loading && !error && hasContent && (
          <pre
            data-testid="preview-content"
            className={cn(
              "syntax-highlight language-markdown",
              "p-4 rounded-lg bg-muted/50 text-sm font-mono",
              "whitespace-pre-wrap break-words"
            )}
          >
            {content}
          </pre>
        )}
      </div>
    </div>
  );
}

export default PreviewPanel;
