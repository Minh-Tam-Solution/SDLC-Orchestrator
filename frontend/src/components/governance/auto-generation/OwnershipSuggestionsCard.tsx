/**
 * =========================================================================
 * Ownership Suggestions Card Component
 * SDLC Orchestrator - Sprint 113 (Governance UI - Auto-Generation)
 *
 * Version: 1.0.0
 * Date: January 28, 2026
 * Framework: SDLC 5.3.0 Quality Assurance System
 * ADR Reference: ADR-041
 *
 * Purpose: Suggest file ownership from git blame analysis
 * Time Saved: ~2 min → <30 sec per file
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
import { useSuggestOwnershipBatch } from "@/hooks/useAutoGeneration";
import type {
  OwnershipSource,
  OwnershipSuggestionResponse,
} from "@/lib/types/auto-generation";

// =============================================================================
// Icons
// =============================================================================

function UserIcon({ className }: { className?: string }) {
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
        d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"
      />
    </svg>
  );
}

function UsersIcon({ className }: { className?: string }) {
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
        d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z"
      />
    </svg>
  );
}

function CodeBracketIcon({ className }: { className?: string }) {
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
        d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5"
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
      strokeWidth={2}
      stroke="currentColor"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
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

// =============================================================================
// Props & Types
// =============================================================================

interface OwnershipSuggestionsCardProps {
  filePaths: string[];
  repoId: string;
  projectId: string;
  onOwnershipAccepted?: (filePath: string, owner: string) => void;
  onOwnershipRejected?: (filePath: string) => void;
  onAllAccepted?: (ownerships: Record<string, string>) => void;
}

interface FileOwnership {
  filePath: string;
  suggestion: OwnershipSuggestionResponse | null;
  status: "pending" | "loading" | "accepted" | "rejected" | "manual";
  selectedOwner: string;
}

// =============================================================================
// Utility Functions
// =============================================================================

function getSourceBadge(source: OwnershipSource) {
  const config = {
    codeowners: { label: "CODEOWNERS", color: "bg-purple-100 text-purple-700" },
    git_blame: { label: "Git Blame", color: "bg-blue-100 text-blue-700" },
    directory_pattern: { label: "Directory", color: "bg-green-100 text-green-700" },
    task_creator: { label: "Task Creator", color: "bg-yellow-100 text-yellow-700" },
    fallback: { label: "Fallback", color: "bg-gray-100 text-gray-700" },
  };

  const cfg = config[source];
  return <Badge className={cfg.color}>{cfg.label}</Badge>;
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return "text-green-600";
  if (confidence >= 0.5) return "text-yellow-600";
  return "text-red-600";
}

// =============================================================================
// Component
// =============================================================================

export function OwnershipSuggestionsCard({
  filePaths,
  repoId,
  projectId,
  onOwnershipAccepted,
  onOwnershipRejected,
  onAllAccepted,
}: OwnershipSuggestionsCardProps) {
  const [ownerships, setOwnerships] = useState<FileOwnership[]>(
    filePaths.map((fp) => ({
      filePath: fp,
      suggestion: null,
      status: "pending",
      selectedOwner: "",
    }))
  );
  const [manualOwner, setManualOwner] = useState("");

  const batchMutation = useSuggestOwnershipBatch();

  const handleSuggestAll = async () => {
    setOwnerships((prev) =>
      prev.map((o) => ({ ...o, status: "loading" as const }))
    );

    try {
      const response = await batchMutation.mutateAsync({
        file_paths: filePaths,
        repo_id: repoId,
        project_id: projectId,
      });

      setOwnerships((prev) =>
        prev.map((o) => ({
          ...o,
          suggestion: response.suggestions[o.filePath] || null,
          status: response.suggestions[o.filePath] ? "pending" : "manual",
          selectedOwner: response.suggestions[o.filePath]?.recommended.owner || "",
        }))
      );
    } catch {
      setOwnerships((prev) =>
        prev.map((o) => ({ ...o, status: "pending" as const }))
      );
    }
  };

  const handleAccept = (filePath: string) => {
    const ownership = ownerships.find((o) => o.filePath === filePath);
    if (ownership?.selectedOwner) {
      setOwnerships((prev) =>
        prev.map((o) =>
          o.filePath === filePath ? { ...o, status: "accepted" } : o
        )
      );
      onOwnershipAccepted?.(filePath, ownership.selectedOwner);
    }
  };

  const handleReject = (filePath: string) => {
    setOwnerships((prev) =>
      prev.map((o) =>
        o.filePath === filePath ? { ...o, status: "rejected", selectedOwner: "" } : o
      )
    );
    onOwnershipRejected?.(filePath);
  };

  const handleSelectOwner = (filePath: string, owner: string) => {
    setOwnerships((prev) =>
      prev.map((o) =>
        o.filePath === filePath ? { ...o, selectedOwner: owner } : o
      )
    );
  };

  const handleAcceptAll = () => {
    const acceptedOwnerships: Record<string, string> = {};
    const updatedOwnerships = ownerships.map((o) => {
      if (o.selectedOwner && o.status === "pending") {
        acceptedOwnerships[o.filePath] = o.selectedOwner;
        return { ...o, status: "accepted" as const };
      }
      return o;
    });
    setOwnerships(updatedOwnerships);
    onAllAccepted?.(acceptedOwnerships);
  };

  const pendingCount = ownerships.filter((o) => o.status === "pending" && o.suggestion).length;
  const acceptedCount = ownerships.filter((o) => o.status === "accepted").length;
  const totalFiles = filePaths.length;

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <UsersIcon className="h-5 w-5 text-indigo-600" />
            <CardTitle className="text-lg">Ownership Suggestions</CardTitle>
          </div>
          <Badge variant="outline">
            {acceptedCount}/{totalFiles} assigned
          </Badge>
        </div>
        <CardDescription>
          Suggest file ownership based on git blame and CODEOWNERS
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Batch Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSuggestAll}
            disabled={batchMutation.isPending}
          >
            {batchMutation.isPending ? (
              <>
                <span className="animate-spin mr-2">...</span>
                Analyzing...
              </>
            ) : (
              <>
                <CodeBracketIcon className="h-4 w-4 mr-2" />
                Suggest All
              </>
            )}
          </Button>
          {pendingCount > 0 && (
            <Button size="sm" onClick={handleAcceptAll}>
              <CheckIcon className="h-4 w-4 mr-2" />
              Accept All ({pendingCount})
            </Button>
          )}
        </div>

        {/* File List */}
        <div className="space-y-3 max-h-[400px] overflow-y-auto">
          {ownerships.map((ownership) => (
            <div
              key={ownership.filePath}
              className={`border rounded-lg p-3 ${
                ownership.status === "accepted"
                  ? "bg-green-50 border-green-200"
                  : ownership.status === "rejected"
                  ? "bg-red-50 border-red-200"
                  : "bg-white"
              }`}
            >
              {/* File Path */}
              <div className="flex items-center justify-between mb-2">
                <code className="text-sm font-mono text-gray-600 truncate max-w-[300px]">
                  {ownership.filePath}
                </code>
                {ownership.status === "accepted" && (
                  <Badge className="bg-green-100 text-green-700">Assigned</Badge>
                )}
                {ownership.status === "rejected" && (
                  <Badge className="bg-red-100 text-red-700">Skipped</Badge>
                )}
              </div>

              {/* Loading State */}
              {ownership.status === "loading" && (
                <div className="flex items-center text-sm text-gray-500">
                  <span className="animate-pulse">Analyzing git history...</span>
                </div>
              )}

              {/* Suggestion Display */}
              {ownership.suggestion && ownership.status !== "loading" && (
                <div className="space-y-2">
                  {/* Recommended Owner */}
                  <div className="flex items-center gap-2">
                    <UserIcon className="h-4 w-4 text-gray-400" />
                    <span className="text-sm font-medium">
                      {ownership.suggestion.recommended.owner}
                    </span>
                    {getSourceBadge(ownership.suggestion.recommended.source)}
                    <span className={`text-sm ${getConfidenceColor(ownership.suggestion.recommended.confidence)}`}>
                      {Math.round(ownership.suggestion.recommended.confidence * 100)}%
                    </span>
                  </div>

                  {/* Alternative Suggestions */}
                  {ownership.suggestion.suggestions.length > 1 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {ownership.suggestion.suggestions.slice(1, 4).map((s, idx) => (
                        <button
                          key={idx}
                          className={`text-xs px-2 py-1 rounded border ${
                            ownership.selectedOwner === s.owner
                              ? "bg-blue-100 border-blue-300"
                              : "bg-gray-50 border-gray-200 hover:bg-gray-100"
                          }`}
                          onClick={() => handleSelectOwner(ownership.filePath, s.owner)}
                        >
                          {s.owner} ({Math.round(s.confidence * 100)}%)
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Actions */}
                  {ownership.status === "pending" && (
                    <div className="flex items-center gap-2 mt-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-green-600 border-green-300 hover:bg-green-50"
                        onClick={() => handleAccept(ownership.filePath)}
                      >
                        <CheckIcon className="h-3 w-3 mr-1" />
                        Accept
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-red-600 border-red-300 hover:bg-red-50"
                        onClick={() => handleReject(ownership.filePath)}
                      >
                        <XMarkIcon className="h-3 w-3 mr-1" />
                        Skip
                      </Button>
                    </div>
                  )}
                </div>
              )}

              {/* Manual Entry */}
              {ownership.status === "manual" && (
                <div className="flex items-center gap-2">
                  <Input
                    placeholder="Enter owner username"
                    value={manualOwner}
                    onChange={(e) => setManualOwner(e.target.value)}
                    className="flex-1"
                  />
                  <Button
                    size="sm"
                    onClick={() => {
                      handleSelectOwner(ownership.filePath, manualOwner);
                      handleAccept(ownership.filePath);
                    }}
                    disabled={!manualOwner}
                  >
                    Assign
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>

      <CardFooter className="text-sm text-gray-500">
        Time saved: ~{Math.round(totalFiles * 1.5)} min → ~{Math.round(totalFiles * 0.25)} min
      </CardFooter>
    </Card>
  );
}

export default OwnershipSuggestionsCard;
