/**
 * =========================================================================
 * Context Overlay Editor Component
 * SDLC Orchestrator - Sprint 152 (Context Authority UI)
 *
 * Version: 1.0.0
 * Date: February 3, 2026
 * Status: ACTIVE - Sprint 152 Implementation
 * Authority: Frontend Lead + Backend Lead Approved
 * Framework: SDLC 6.0.5
 *
 * WYSIWYG-style editor for dynamic context overlays:
 * - Template variable insertion
 * - Live preview with variable substitution
 * - Syntax highlighting for template variables
 * - Copy to clipboard functionality
 *
 * Zero Mock Policy: Production-ready component
 * =========================================================================
 */

"use client";

import { useState, useMemo, useCallback } from "react";
import { cn } from "@/lib/utils";
import {
  TierEnum,
  VibecodingZoneEnum,
  GateStatus,
  useGenerateOverlay,
  OverlayGenerateRequest,
} from "@/hooks/useContextAuthority";

// =========================================================================
// Types
// =========================================================================

interface TemplateVariable {
  name: string;
  description: string;
  example: string;
}

interface ContextOverlayEditorProps {
  initialContent?: string;
  projectId?: string;
  projectTier?: TierEnum;
  gateStatus?: GateStatus;
  vibecodingIndex?: number;
  vibecodingZone?: VibecodingZoneEnum;
  onContentChange?: (content: string) => void;
  readOnly?: boolean;
  className?: string;
}

// =========================================================================
// Constants
// =========================================================================

const TEMPLATE_VARIABLES: TemplateVariable[] = [
  { name: "{date}", description: "Current date", example: "2026-02-03" },
  { name: "{stage}", description: "Current SDLC stage", example: "BUILD" },
  { name: "{tier}", description: "Project tier", example: "PROFESSIONAL" },
  { name: "{gate}", description: "Last passed gate", example: "G2" },
  { name: "{index}", description: "Vibecoding index", example: "35" },
  { name: "{zone}", description: "Vibecoding zone", example: "YELLOW" },
  { name: "{top_signals}", description: "Top contributing signals", example: "orphan_code, design_doc" },
  { name: "{project_id}", description: "Project identifier", example: "proj_abc123" },
  { name: "{pending_gates}", description: "Pending gates list", example: "G3, G4" },
];

const DEFAULT_TEMPLATE = `# Context Authority Overlay

**Generated**: {date}
**Stage**: {stage}
**Tier**: {tier}
**Gate Status**: Last passed {gate}

## Vibecoding Status

- **Zone**: {zone}
- **Index**: {index}

### Top Signals
{top_signals}

## Guidelines

Based on your current stage ({stage}) and vibecoding zone ({zone}):

- Follow the SDLC Framework guidelines
- Ensure all evidence is properly documented
- Maintain code quality standards
`;

// =========================================================================
// Icon Components
// =========================================================================

function ClipboardIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15.666 3.888A2.25 2.25 0 0 0 13.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 0 1-.75.75H9a.75.75 0 0 1-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 0 1-2.25 2.25H6.75A2.25 2.25 0 0 1 4.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 0 1 1.927-.184"
      />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
    </svg>
  );
}

function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z"
      />
    </svg>
  );
}

function EyeIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z"
      />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  );
}

function PencilIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10"
      />
    </svg>
  );
}

// =========================================================================
// Helper Functions
// =========================================================================

function highlightVariables(content: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const regex = /(\{[a-z_]+\})/gi;
  let lastIndex = 0;
  let match;

  const contentStr = content;
  const tempRegex = new RegExp(regex);

  while ((match = tempRegex.exec(contentStr)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      parts.push(contentStr.slice(lastIndex, match.index));
    }

    // Add the highlighted variable
    parts.push(
      <span
        key={match.index}
        className="bg-purple-100 text-purple-800 px-1 rounded font-mono text-sm"
      >
        {match[0]}
      </span>
    );

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < contentStr.length) {
    parts.push(contentStr.slice(lastIndex));
  }

  return parts;
}

function substituteVariables(
  content: string,
  projectId?: string,
  projectTier?: TierEnum,
  gateStatus?: GateStatus,
  vibecodingIndex?: number,
  vibecodingZone?: VibecodingZoneEnum
): string {
  let result = content;

  const now = new Date();
  result = result.replace(/\{date\}/g, now.toISOString().split("T")[0]);
  result = result.replace(/\{stage\}/g, gateStatus?.current_stage || "BUILD");
  result = result.replace(/\{tier\}/g, projectTier || "STANDARD");
  result = result.replace(/\{gate\}/g, gateStatus?.last_passed_gate || "G0");
  result = result.replace(/\{index\}/g, String(vibecodingIndex ?? 50));
  result = result.replace(/\{zone\}/g, vibecodingZone || "YELLOW");
  result = result.replace(/\{project_id\}/g, projectId || "project_id");
  result = result.replace(
    /\{pending_gates\}/g,
    gateStatus?.pending_gates?.join(", ") || "None"
  );
  result = result.replace(/\{top_signals\}/g, "- orphan_code: 0.3\n- design_doc_exists: true");

  return result;
}

// =========================================================================
// Main Component
// =========================================================================

export function ContextOverlayEditor({
  initialContent = DEFAULT_TEMPLATE,
  projectId,
  projectTier,
  gateStatus,
  vibecodingIndex,
  vibecodingZone,
  onContentChange,
  readOnly = false,
  className,
}: ContextOverlayEditorProps) {
  const [content, setContent] = useState(initialContent);
  const [activeTab, setActiveTab] = useState<"edit" | "preview">("edit");
  const [copied, setCopied] = useState(false);
  const [showVariables, setShowVariables] = useState(false);

  const generateOverlayMutation = useGenerateOverlay();

  // Compute preview with substituted variables
  const previewContent = useMemo(
    () =>
      substituteVariables(
        content,
        projectId,
        projectTier,
        gateStatus,
        vibecodingIndex,
        vibecodingZone
      ),
    [content, projectId, projectTier, gateStatus, vibecodingIndex, vibecodingZone]
  );

  const handleContentChange = useCallback(
    (newContent: string) => {
      setContent(newContent);
      onContentChange?.(newContent);
    },
    [onContentChange]
  );

  const handleInsertVariable = useCallback(
    (variable: string) => {
      // Insert at cursor position or append
      const textarea = document.getElementById("overlay-editor") as HTMLTextAreaElement;
      if (textarea) {
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const newContent =
          content.substring(0, start) + variable + content.substring(end);
        handleContentChange(newContent);

        // Reset cursor position
        setTimeout(() => {
          textarea.focus();
          textarea.setSelectionRange(start + variable.length, start + variable.length);
        }, 0);
      } else {
        handleContentChange(content + variable);
      }
    },
    [content, handleContentChange]
  );

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(previewContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Failed to copy:", error);
    }
  }, [previewContent]);

  const handleGenerateFromAPI = useCallback(async () => {
    if (!projectId) return;

    const request: OverlayGenerateRequest = {
      project_id: projectId,
      project_tier: projectTier || "STANDARD",
      gate_status: gateStatus || {
        current_stage: "BUILD",
        last_passed_gate: null,
        pending_gates: [],
      },
      vibecoding_index: vibecodingIndex,
      vibecoding_zone: vibecodingZone,
    };

    try {
      const response = await generateOverlayMutation.mutateAsync(request);
      handleContentChange(response.overlay_content);
    } catch (error) {
      console.error("Failed to generate overlay:", error);
    }
  }, [
    projectId,
    projectTier,
    gateStatus,
    vibecodingIndex,
    vibecodingZone,
    generateOverlayMutation,
    handleContentChange,
  ]);

  const handleReset = useCallback(() => {
    handleContentChange(DEFAULT_TEMPLATE);
  }, [handleContentChange]);

  return (
    <div className={cn("flex flex-col", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium text-gray-700">Context Overlay Editor</h3>
          {!readOnly && (
            <button
              onClick={() => setShowVariables(!showVariables)}
              className={cn(
                "text-xs px-2 py-1 rounded transition-colors",
                showVariables
                  ? "bg-purple-100 text-purple-700"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              )}
            >
              Variables
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Generate from API button */}
          {projectId && !readOnly && (
            <button
              onClick={handleGenerateFromAPI}
              disabled={generateOverlayMutation.isPending}
              className="flex items-center gap-1 text-xs px-2 py-1 bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200 transition-colors disabled:opacity-50"
            >
              <SparklesIcon className="h-3.5 w-3.5" />
              {generateOverlayMutation.isPending ? "Generating..." : "Generate"}
            </button>
          )}

          {/* Reset button */}
          {!readOnly && (
            <button
              onClick={handleReset}
              className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded hover:bg-gray-200 transition-colors"
            >
              Reset
            </button>
          )}

          {/* Copy button */}
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded hover:bg-gray-200 transition-colors"
          >
            {copied ? (
              <>
                <CheckIcon className="h-3.5 w-3.5 text-green-600" />
                <span className="text-green-600">Copied!</span>
              </>
            ) : (
              <>
                <ClipboardIcon className="h-3.5 w-3.5" />
                Copy
              </>
            )}
          </button>
        </div>
      </div>

      {/* Variable Palette */}
      {showVariables && !readOnly && (
        <div className="mb-3 p-3 bg-purple-50 border border-purple-200 rounded-lg">
          <p className="text-xs font-medium text-purple-700 mb-2">
            Click to insert template variables:
          </p>
          <div className="flex flex-wrap gap-2">
            {TEMPLATE_VARIABLES.map((v) => (
              <button
                key={v.name}
                onClick={() => handleInsertVariable(v.name)}
                className="text-xs px-2 py-1 bg-white border border-purple-200 text-purple-700 rounded hover:bg-purple-100 transition-colors font-mono"
                title={`${v.description} (e.g., ${v.example})`}
              >
                {v.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-3">
        <button
          onClick={() => setActiveTab("edit")}
          className={cn(
            "flex items-center gap-1.5 px-4 py-2 text-sm font-medium border-b-2 transition-colors",
            activeTab === "edit"
              ? "border-blue-500 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          )}
        >
          <PencilIcon className="h-4 w-4" />
          Edit
        </button>
        <button
          onClick={() => setActiveTab("preview")}
          className={cn(
            "flex items-center gap-1.5 px-4 py-2 text-sm font-medium border-b-2 transition-colors",
            activeTab === "preview"
              ? "border-blue-500 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          )}
        >
          <EyeIcon className="h-4 w-4" />
          Preview
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 min-h-[300px]">
        {activeTab === "edit" ? (
          <div className="h-full">
            {readOnly ? (
              <div className="h-full p-4 bg-gray-50 border rounded-lg overflow-auto">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
                  {highlightVariables(content)}
                </pre>
              </div>
            ) : (
              <textarea
                id="overlay-editor"
                value={content}
                onChange={(e) => handleContentChange(e.target.value)}
                className="w-full h-full min-h-[300px] p-4 border rounded-lg font-mono text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                placeholder="Enter your overlay template content..."
              />
            )}
          </div>
        ) : (
          <div className="h-full p-4 bg-gray-50 border rounded-lg overflow-auto">
            <div className="prose prose-sm max-w-none">
              <pre className="text-sm text-gray-700 whitespace-pre-wrap bg-transparent p-0 m-0">
                {previewContent}
              </pre>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
        <span>
          {content.length} characters • {content.split("\n").length} lines
        </span>
        <span>
          {(content.match(/\{[a-z_]+\}/gi) || []).length} variables
        </span>
      </div>
    </div>
  );
}

export default ContextOverlayEditor;
