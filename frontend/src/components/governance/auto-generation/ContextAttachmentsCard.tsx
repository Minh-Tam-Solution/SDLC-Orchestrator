/**
 * =========================================================================
 * Context Attachments Card Component
 * SDLC Orchestrator - Sprint 113 (Governance UI - Auto-Generation)
 *
 * Version: 1.0.0
 * Date: January 28, 2026
 * Framework: SDLC 5.3.0 Quality Assurance System
 * ADR Reference: ADR-041
 *
 * Purpose: Auto-attach ADRs, specs, and design docs to PRs
 * Time Saved: ~5 min → automatic per PR
 * =========================================================================
 */

"use client";

import { useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useAttachContext } from "@/hooks/useAutoGeneration";
import type {
  ContextType,
  AttachedContext,
} from "@/lib/types/auto-generation";

// =============================================================================
// Icons
// =============================================================================

function LinkIcon({ className }: { className?: string }) {
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
        d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244"
      />
    </svg>
  );
}

function DocumentIcon({ className }: { className?: string }) {
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
        d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
      />
    </svg>
  );
}

function BookOpenIcon({ className }: { className?: string }) {
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
        d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25"
      />
    </svg>
  );
}

function CpuChipIcon({ className }: { className?: string }) {
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
        d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 0 0 2.25-2.25V6.75a2.25 2.25 0 0 0-2.25-2.25H6.75A2.25 2.25 0 0 0 4.5 6.75v10.5a2.25 2.25 0 0 0 2.25 2.25Zm.75-12h9v9h-9v-9Z"
      />
    </svg>
  );
}

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={2}
      stroke="currentColor"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  );
}

function XMarkIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={2}
      stroke="currentColor"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
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
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
      />
    </svg>
  );
}

// =============================================================================
// Props & Types
// =============================================================================

interface ContextAttachmentsCardProps {
  prNumber: number;
  repoId: string;
  projectId: string;
  changedFiles: string[];
  onContextAttached?: (contexts: AttachedContext[]) => void;
  onDescriptionUpdated?: (newDescription: string) => void;
}

// =============================================================================
// Utility Functions
// =============================================================================

function getContextTypeIcon(type: ContextType) {
  switch (type) {
    case "adr":
      return <BookOpenIcon className="h-4 w-4 text-purple-600" />;
    case "spec":
      return <DocumentIcon className="h-4 w-4 text-blue-600" />;
    case "design_doc":
      return <CpuChipIcon className="h-4 w-4 text-green-600" />;
    case "intent":
      return <DocumentIcon className="h-4 w-4 text-yellow-600" />;
    case "agents_md":
      return <CpuChipIcon className="h-4 w-4 text-indigo-600" />;
    default:
      return <DocumentIcon className="h-4 w-4 text-gray-600" />;
  }
}

function getContextTypeBadge(type: ContextType) {
  const config = {
    adr: { label: "ADR", color: "bg-purple-100 text-purple-700" },
    spec: { label: "Spec", color: "bg-blue-100 text-blue-700" },
    design_doc: { label: "Design", color: "bg-green-100 text-green-700" },
    intent: { label: "Intent", color: "bg-yellow-100 text-yellow-700" },
    agents_md: { label: "AGENTS.md", color: "bg-indigo-100 text-indigo-700" },
  };

  const cfg = config[type];
  return <Badge className={cfg.color}>{cfg.label}</Badge>;
}

function getRelevanceColor(score: number): string {
  if (score >= 0.8) return "text-green-600";
  if (score >= 0.5) return "text-yellow-600";
  return "text-gray-500";
}

// =============================================================================
// Component
// =============================================================================

export function ContextAttachmentsCard({
  prNumber,
  repoId,
  projectId,
  changedFiles,
  onContextAttached,
  onDescriptionUpdated,
}: ContextAttachmentsCardProps) {
  const [attachedContexts, setAttachedContexts] = useState<AttachedContext[]>([]);
  const [enrichedDescription, setEnrichedDescription] = useState<string>("");
  const [showPreview, setShowPreview] = useState(false);
  const [manualPath, setManualPath] = useState("");
  const [selectedContext, setSelectedContext] = useState<AttachedContext | null>(null);

  const attachMutation = useAttachContext();

  const handleAutoAttach = async () => {
    try {
      const response = await attachMutation.mutateAsync({
        pr_number: prNumber,
        repo_id: repoId,
        changed_files: changedFiles,
        project_id: projectId,
      });

      setAttachedContexts(response.attached_contexts);
      setEnrichedDescription(response.enriched_description);
      onContextAttached?.(response.attached_contexts);
      if (response.pr_description_updated) {
        onDescriptionUpdated?.(response.enriched_description);
      }
    } catch {
      // Error handling managed by mutation
    }
  };

  const handleRemoveContext = (contextId: string) => {
    setAttachedContexts((prev) => prev.filter((c) => c.id !== contextId));
  };

  const handleAddManual = () => {
    if (manualPath.trim()) {
      const newContext: AttachedContext = {
        id: `manual-${Date.now()}`,
        type: manualPath.includes("ADR") ? "adr" : "spec",
        title: manualPath.split("/").pop() || manualPath,
        path: manualPath,
        relevance_score: 1.0,
        summary: "Manually added context",
      };
      setAttachedContexts((prev) => [...prev, newContext]);
      setManualPath("");
    }
  };

  const groupedContexts = attachedContexts.reduce((acc, ctx) => {
    if (!acc[ctx.type]) acc[ctx.type] = [];
    acc[ctx.type].push(ctx);
    return acc;
  }, {} as Record<ContextType, AttachedContext[]>);

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <LinkIcon className="h-5 w-5 text-teal-600" />
            <CardTitle className="text-lg">Context Attachments</CardTitle>
          </div>
          <Badge variant="outline">{attachedContexts.length} attached</Badge>
        </div>
        <CardDescription>
          Auto-link ADRs, specs, and design docs to PR #{prNumber}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Changed Files Summary */}
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
            Changed Files ({changedFiles.length})
          </div>
          <div className="flex flex-wrap gap-1">
            {changedFiles.slice(0, 5).map((file, idx) => (
              <code
                key={idx}
                className="text-xs bg-gray-200 px-2 py-0.5 rounded truncate max-w-[150px]"
                title={file}
              >
                {file.split("/").pop()}
              </code>
            ))}
            {changedFiles.length > 5 && (
              <span className="text-xs text-gray-500">
                +{changedFiles.length - 5} more
              </span>
            )}
          </div>
        </div>

        {/* Auto-attach Button */}
        <Button
          onClick={handleAutoAttach}
          disabled={attachMutation.isPending}
          className="w-full"
          variant={attachedContexts.length > 0 ? "outline" : "default"}
        >
          {attachMutation.isPending ? (
            <>
              <span className="animate-spin mr-2">...</span>
              Analyzing files...
            </>
          ) : (
            <>
              <LinkIcon className="h-4 w-4 mr-2" />
              {attachedContexts.length > 0 ? "Re-scan for Context" : "Auto-attach Context"}
            </>
          )}
        </Button>

        {/* Attached Contexts by Type */}
        {Object.entries(groupedContexts).map(([type, contexts]) => (
          <div key={type} className="space-y-2">
            <div className="flex items-center gap-2">
              {getContextTypeIcon(type as ContextType)}
              <span className="text-sm font-medium capitalize">{type.replace("_", " ")}s</span>
              <Badge variant="outline" className="text-xs">
                {contexts.length}
              </Badge>
            </div>
            <div className="space-y-2 pl-6">
              {contexts.map((ctx) => (
                <div
                  key={ctx.id}
                  className="flex items-center justify-between bg-white border rounded-lg p-2 hover:bg-gray-50"
                >
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {getContextTypeBadge(ctx.type)}
                    <span className="text-sm font-medium truncate">{ctx.title}</span>
                    <span className={`text-xs ${getRelevanceColor(ctx.relevance_score)}`}>
                      {Math.round(ctx.relevance_score * 100)}%
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0"
                      onClick={() => setSelectedContext(ctx)}
                    >
                      <EyeIcon className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 text-red-500 hover:text-red-700"
                      onClick={() => handleRemoveContext(ctx.id)}
                    >
                      <XMarkIcon className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* Manual Add */}
        <div className="border-t pt-4">
          <div className="text-sm font-medium mb-2">Add Manual Context</div>
          <div className="flex gap-2">
            <Input
              placeholder="e.g., docs/02-design/03-ADRs/ADR-041.md"
              value={manualPath}
              onChange={(e) => setManualPath(e.target.value)}
              className="flex-1"
            />
            <Button variant="outline" onClick={handleAddManual} disabled={!manualPath.trim()}>
              <PlusIcon className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Context Preview Modal */}
        {selectedContext && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  {getContextTypeIcon(selectedContext.type)}
                  <h3 className="font-semibold">{selectedContext.title}</h3>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedContext(null)}
                >
                  <XMarkIcon className="h-4 w-4" />
                </Button>
              </div>
              <div className="space-y-3">
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Path</div>
                  <code className="text-sm bg-gray-100 px-2 py-1 rounded block">
                    {selectedContext.path}
                  </code>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Relevance</div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-teal-500"
                        style={{ width: `${selectedContext.relevance_score * 100}%` }}
                      />
                    </div>
                    <span className="text-sm">
                      {Math.round(selectedContext.relevance_score * 100)}%
                    </span>
                  </div>
                </div>
                {selectedContext.summary && (
                  <div>
                    <div className="text-xs text-gray-500 uppercase tracking-wide">Summary</div>
                    <p className="text-sm text-gray-700">{selectedContext.summary}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Enriched Description Preview */}
        {enrichedDescription && (
          <div className="border-t pt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Updated PR Description</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowPreview(!showPreview)}
              >
                {showPreview ? "Hide" : "Preview"}
              </Button>
            </div>
            {showPreview && (
              <div className="bg-gray-50 rounded-lg p-3 text-sm font-mono whitespace-pre-wrap max-h-[200px] overflow-y-auto">
                {enrichedDescription}
              </div>
            )}
          </div>
        )}
      </CardContent>

      <CardFooter className="text-sm text-gray-500">
        Time saved: ~5 min → automatic context linking
      </CardFooter>
    </Card>
  );
}

export default ContextAttachmentsCard;
