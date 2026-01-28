/**
 * =========================================================================
 * Intent Generator Card Component
 * SDLC Orchestrator - Sprint 113 (Governance UI - Auto-Generation)
 *
 * Version: 1.0.0
 * Date: January 28, 2026
 * Framework: SDLC 5.3.0 Quality Assurance System
 * ADR Reference: ADR-041
 *
 * Purpose: Generate intent skeleton from task description
 * Time Saved: ~15 min → <1 min per intent document
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
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useGenerateIntent } from "@/hooks/useAutoGeneration";
import type {
  GenerateIntentRequest,
  IntentDocument,
  GenerationState,
} from "@/lib/types/auto-generation";

// =============================================================================
// Icons
// =============================================================================

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

function DocumentTextIcon({ className }: { className?: string }) {
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
        d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
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

function ClockIcon({ className }: { className?: string }) {
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
        d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
      />
    </svg>
  );
}

// =============================================================================
// Props & Types
// =============================================================================

interface IntentGeneratorCardProps {
  taskId: string;
  taskTitle: string;
  taskDescription: string;
  acceptanceCriteria?: string[];
  onIntentGenerated?: (intent: IntentDocument) => void;
  onIntentSaved?: (intent: IntentDocument) => void;
}

// =============================================================================
// Component
// =============================================================================

export function IntentGeneratorCard({
  taskId,
  taskTitle,
  taskDescription,
  acceptanceCriteria = [],
  onIntentGenerated,
  onIntentSaved,
}: IntentGeneratorCardProps) {
  const [generationState, setGenerationState] = useState<GenerationState>("idle");
  const [generatedIntent, setGeneratedIntent] = useState<IntentDocument | null>(null);
  const [editedContent, setEditedContent] = useState<string>("");
  const [isEditing, setIsEditing] = useState(false);

  const generateMutation = useGenerateIntent();

  const handleGenerate = async () => {
    setGenerationState("generating");

    const request: GenerateIntentRequest = {
      task_id: taskId,
      title: taskTitle,
      description: taskDescription,
      acceptance_criteria: acceptanceCriteria,
      use_llm: true,
    };

    try {
      const response = await generateMutation.mutateAsync(request);
      setGeneratedIntent(response.intent);
      setEditedContent(response.intent.content);
      setGenerationState(response.fallback_used ? "fallback" : "success");
      onIntentGenerated?.(response.intent);
    } catch {
      setGenerationState("error");
    }
  };

  const handleSave = () => {
    if (generatedIntent) {
      const savedIntent: IntentDocument = {
        ...generatedIntent,
        content: editedContent,
        auto_generated: !isEditing || editedContent === generatedIntent.content,
      };
      onIntentSaved?.(savedIntent);
    }
  };

  const getGenerationBadge = () => {
    if (!generatedIntent) return null;

    switch (generatedIntent.generation_method) {
      case "llm":
        return (
          <Badge className="bg-green-100 text-green-700 border-green-200">
            <SparklesIcon className="h-3 w-3 mr-1" />
            AI Generated
          </Badge>
        );
      case "template":
        return (
          <Badge className="bg-yellow-100 text-yellow-700 border-yellow-200">
            <DocumentTextIcon className="h-3 w-3 mr-1" />
            Template
          </Badge>
        );
      default:
        return (
          <Badge className="bg-gray-100 text-gray-700 border-gray-200">
            Manual
          </Badge>
        );
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <DocumentTextIcon className="h-5 w-5 text-blue-600" />
            <CardTitle className="text-lg">Intent Generator</CardTitle>
          </div>
          {getGenerationBadge()}
        </div>
        <CardDescription>
          Generate intent skeleton for &quot;{taskTitle}&quot;
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Task Context Display */}
        <div className="bg-gray-50 rounded-lg p-4 space-y-2">
          <Label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Task Description
          </Label>
          <p className="text-sm text-gray-700">{taskDescription}</p>
          {acceptanceCriteria.length > 0 && (
            <>
              <Label className="text-xs font-medium text-gray-500 uppercase tracking-wide mt-3 block">
                Acceptance Criteria
              </Label>
              <ul className="list-disc list-inside text-sm text-gray-700">
                {acceptanceCriteria.map((criteria, idx) => (
                  <li key={idx}>{criteria}</li>
                ))}
              </ul>
            </>
          )}
        </div>

        {/* Generated Intent Display */}
        {generatedIntent && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-medium">Generated Intent</Label>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsEditing(!isEditing)}
              >
                {isEditing ? "Preview" : "Edit"}
              </Button>
            </div>

            {isEditing ? (
              <Textarea
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                className="min-h-[200px] font-mono text-sm"
              />
            ) : (
              <div className="bg-white border rounded-lg p-4 space-y-3">
                <div>
                  <Label className="text-xs text-gray-500">Why This Change</Label>
                  <p className="text-sm">{generatedIntent.sections.why_this_change}</p>
                </div>
                <div>
                  <Label className="text-xs text-gray-500">Problem Solved</Label>
                  <p className="text-sm">{generatedIntent.sections.problem_solved}</p>
                </div>
                {generatedIntent.sections.alternatives_considered.length > 0 && (
                  <div>
                    <Label className="text-xs text-gray-500">Alternatives Considered</Label>
                    <ul className="list-disc list-inside text-sm">
                      {generatedIntent.sections.alternatives_considered.map((alt, idx) => (
                        <li key={idx}>{alt}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Confidence Score */}
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span>Confidence:</span>
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    generatedIntent.confidence_score >= 0.8
                      ? "bg-green-500"
                      : generatedIntent.confidence_score >= 0.5
                      ? "bg-yellow-500"
                      : "bg-red-500"
                  }`}
                  style={{ width: `${generatedIntent.confidence_score * 100}%` }}
                />
              </div>
              <span>{Math.round(generatedIntent.confidence_score * 100)}%</span>
            </div>

            {generatedIntent.review_required && (
              <div className="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 p-2 rounded">
                <ClockIcon className="h-4 w-4" />
                <span>Review required before submission</span>
              </div>
            )}
          </div>
        )}

        {/* Loading State */}
        {generationState === "generating" && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            <span className="ml-3 text-gray-600">Generating intent...</span>
          </div>
        )}

        {/* Error State */}
        {generationState === "error" && (
          <div className="bg-red-50 text-red-700 p-4 rounded-lg">
            Failed to generate intent. Please try again or create manually.
          </div>
        )}
      </CardContent>

      <CardFooter className="flex justify-between">
        {!generatedIntent ? (
          <Button
            onClick={handleGenerate}
            disabled={generationState === "generating"}
            className="w-full"
          >
            <SparklesIcon className="h-4 w-4 mr-2" />
            Generate Intent Skeleton
          </Button>
        ) : (
          <div className="flex gap-2 w-full">
            <Button
              variant="outline"
              onClick={handleGenerate}
              disabled={generationState === "generating"}
            >
              Regenerate
            </Button>
            <Button onClick={handleSave} className="flex-1">
              <CheckIcon className="h-4 w-4 mr-2" />
              Save Intent
            </Button>
          </div>
        )}
      </CardFooter>
    </Card>
  );
}

export default IntentGeneratorCard;
