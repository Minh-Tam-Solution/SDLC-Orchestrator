/**
 * =========================================================================
 * Attestation Form Card Component
 * SDLC Orchestrator - Sprint 113 (Governance UI - Auto-Generation)
 *
 * Version: 1.0.0
 * Date: January 28, 2026
 * Framework: SDLC 5.3.0 Quality Assurance System
 * ADR Reference: ADR-041
 *
 * Purpose: Pre-fill AI attestation form with session metadata
 * Time Saved: ~8 min → ~2 min (human confirmation only)
 * =========================================================================
 */

"use client";

import { useState, useEffect } from "react";
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
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import {
  usePreFillAttestation,
  useSubmitAttestation,
} from "@/hooks/useAutoGeneration";
import type {
  AttestationForm,
  AIProvider,
  HumanConfirmation,
} from "@/lib/types/auto-generation";

// =============================================================================
// Icons
// =============================================================================

function ShieldCheckIcon({ className }: { className?: string }) {
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
        d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z"
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

function CheckCircleIcon({ className }: { className?: string }) {
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
        d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
      />
    </svg>
  );
}

function ExclamationCircleIcon({ className }: { className?: string }) {
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
        d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z"
      />
    </svg>
  );
}

// =============================================================================
// Props & Types
// =============================================================================

interface AttestationFormCardProps {
  submissionId: string;
  aiSessionId?: string;
  prNumber?: number;
  filePaths?: string[];
  onAttestationSubmitted?: (attestation: AttestationForm) => void;
}

// =============================================================================
// Utility Functions
// =============================================================================

function getProviderBadge(provider: AIProvider) {
  const config: Record<AIProvider, { label: string; color: string }> = {
    ollama: { label: "Ollama", color: "bg-green-100 text-green-700" },
    claude: { label: "Claude", color: "bg-purple-100 text-purple-700" },
    openai: { label: "OpenAI", color: "bg-blue-100 text-blue-700" },
    deepcode: { label: "DeepCode", color: "bg-orange-100 text-orange-700" },
    other: { label: "Other", color: "bg-gray-100 text-gray-700" },
  };

  const cfg = config[provider];
  return <Badge className={cfg.color}>{cfg.label}</Badge>;
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
}

// =============================================================================
// Component
// =============================================================================

export function AttestationFormCard({
  submissionId,
  aiSessionId,
  prNumber,
  filePaths = [],
  onAttestationSubmitted,
}: AttestationFormCardProps) {
  const [attestation, setAttestation] = useState<AttestationForm | null>(null);
  const [reviewTime, setReviewTime] = useState(0);
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [humanConfirmation, setHumanConfirmation] = useState<HumanConfirmation>({
    review_time_seconds: 0,
    minimum_required_seconds: 120, // 2 minutes minimum
    meets_minimum: false,
    modifications_made: false,
    modification_description: "",
    understanding_confirmed: false,
  });

  const preFillMutation = usePreFillAttestation();
  const submitMutation = useSubmitAttestation();

  // Review timer
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isTimerRunning) {
      interval = setInterval(() => {
        setReviewTime((t) => {
          const newTime = t + 1;
          setHumanConfirmation((prev) => ({
            ...prev,
            review_time_seconds: newTime,
            meets_minimum: newTime >= prev.minimum_required_seconds,
          }));
          return newTime;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isTimerRunning]);

  const handlePreFill = async () => {
    try {
      const response = await preFillMutation.mutateAsync({
        submission_id: submissionId,
        ai_session_id: aiSessionId,
        pr_number: prNumber,
        file_paths: filePaths,
      });

      setAttestation(response.attestation);
      setIsTimerRunning(true);
    } catch {
      // Error handling managed by mutation
    }
  };

  const handleSubmit = async () => {
    if (!attestation) return;

    try {
      const result = await submitMutation.mutateAsync({
        attestation_id: attestation.id,
        human_confirmation: humanConfirmation,
      });

      setIsTimerRunning(false);
      onAttestationSubmitted?.(result);
    } catch {
      // Error handling managed by mutation
    }
  };

  const canSubmit =
    attestation &&
    humanConfirmation.meets_minimum &&
    humanConfirmation.understanding_confirmed;

  const completionPercent = attestation?.completion_percent || 0;

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheckIcon className="h-5 w-5 text-emerald-600" />
            <CardTitle className="text-lg">AI Attestation</CardTitle>
          </div>
          {attestation && (
            <Badge
              className={
                attestation.status === "approved"
                  ? "bg-green-100 text-green-700"
                  : attestation.status === "submitted"
                  ? "bg-blue-100 text-blue-700"
                  : "bg-yellow-100 text-yellow-700"
              }
            >
              {attestation.status}
            </Badge>
          )}
        </div>
        <CardDescription>
          Attest to AI-assisted code understanding and review
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Pre-fill Button */}
        {!attestation && (
          <div className="text-center py-8">
            <CpuChipIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">
              Pre-fill attestation form with AI session metadata
            </p>
            <Button
              onClick={handlePreFill}
              disabled={preFillMutation.isPending}
            >
              {preFillMutation.isPending ? (
                <>
                  <span className="animate-spin mr-2">...</span>
                  Loading session data...
                </>
              ) : (
                <>
                  <CpuChipIcon className="h-4 w-4 mr-2" />
                  Pre-fill Attestation
                </>
              )}
            </Button>
          </div>
        )}

        {/* Attestation Form */}
        {attestation && (
          <>
            {/* Completion Progress */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Form Completion</span>
                <span>{completionPercent}%</span>
              </div>
              <Progress value={completionPercent} className="h-2" />
            </div>

            {/* AI Session Info (Auto-filled) */}
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <CpuChipIcon className="h-4 w-4" />
                AI Session Details (Auto-filled)
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-gray-500">Provider</Label>
                  <div className="mt-1">
                    {getProviderBadge(attestation.ai_session.provider)}
                  </div>
                </div>
                <div>
                  <Label className="text-xs text-gray-500">Model Version</Label>
                  <p className="text-sm font-mono">
                    {attestation.ai_session.model_version}
                  </p>
                </div>
                <div>
                  <Label className="text-xs text-gray-500">Generated Lines</Label>
                  <p className="text-sm">
                    {attestation.ai_session.generated_lines} /{" "}
                    {attestation.ai_session.total_lines} (
                    {Math.round(attestation.ai_session.ai_dependency_ratio * 100)}%
                    AI)
                  </p>
                </div>
                <div>
                  <Label className="text-xs text-gray-500">Session ID</Label>
                  <p className="text-sm font-mono truncate">
                    {attestation.ai_session.session_id.slice(0, 16)}...
                  </p>
                </div>
              </div>
            </div>

            {/* Review Timer */}
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <ClockIcon className="h-4 w-4 text-blue-600" />
                  <span className="font-medium text-blue-900">Review Time</span>
                </div>
                <span className="text-2xl font-mono text-blue-700">
                  {formatDuration(reviewTime)}
                </span>
              </div>
              <Progress
                value={Math.min(
                  (reviewTime / humanConfirmation.minimum_required_seconds) * 100,
                  100
                )}
                className="h-2"
              />
              <div className="flex items-center justify-between mt-2 text-sm">
                <span className="text-blue-600">
                  Minimum: {formatDuration(humanConfirmation.minimum_required_seconds)}
                </span>
                {humanConfirmation.meets_minimum ? (
                  <span className="flex items-center text-green-600">
                    <CheckCircleIcon className="h-4 w-4 mr-1" />
                    Requirement met
                  </span>
                ) : (
                  <span className="flex items-center text-amber-600">
                    <ExclamationCircleIcon className="h-4 w-4 mr-1" />
                    Keep reviewing
                  </span>
                )}
              </div>
            </div>

            {/* Human Confirmation Section */}
            <div className="space-y-4">
              <div className="font-medium">Human Confirmation (Required)</div>

              {/* Understanding Confirmation */}
              <div className="flex items-start gap-3 p-3 border rounded-lg">
                <Checkbox
                  id="understanding"
                  checked={humanConfirmation.understanding_confirmed}
                  onCheckedChange={(checked) =>
                    setHumanConfirmation((prev) => ({
                      ...prev,
                      understanding_confirmed: checked === true,
                    }))
                  }
                />
                <div className="flex-1">
                  <Label htmlFor="understanding" className="font-medium">
                    I confirm that I understand the AI-generated code
                  </Label>
                  <p className="text-sm text-gray-500 mt-1">
                    I have reviewed the AI-generated code, understand its logic, and
                    take responsibility for its behavior in production.
                  </p>
                </div>
              </div>

              {/* Modifications Made */}
              <div className="flex items-start gap-3 p-3 border rounded-lg">
                <Checkbox
                  id="modifications"
                  checked={humanConfirmation.modifications_made}
                  onCheckedChange={(checked) =>
                    setHumanConfirmation((prev) => ({
                      ...prev,
                      modifications_made: checked === true,
                    }))
                  }
                />
                <div className="flex-1">
                  <Label htmlFor="modifications" className="font-medium">
                    I made modifications to the AI-generated code
                  </Label>
                  {humanConfirmation.modifications_made && (
                    <Textarea
                      placeholder="Describe the modifications you made..."
                      value={humanConfirmation.modification_description || ""}
                      onChange={(e) =>
                        setHumanConfirmation((prev) => ({
                          ...prev,
                          modification_description: e.target.value,
                        }))
                      }
                      className="mt-2"
                    />
                  )}
                </div>
              </div>
            </div>

            {/* Auto-filled Fields Summary */}
            <div className="text-sm text-gray-500">
              <span className="font-medium">
                {attestation.auto_filled_fields.length}
              </span>{" "}
              fields auto-filled from AI session
            </div>
          </>
        )}

        {/* Error State */}
        {preFillMutation.isError && (
          <div className="bg-red-50 text-red-700 p-4 rounded-lg">
            Failed to load AI session data. Please try again or fill manually.
          </div>
        )}
      </CardContent>

      {attestation && (
        <CardFooter className="flex justify-between">
          <div className="text-sm text-gray-500">
            Time saved: ~8 min → ~2 min
          </div>
          <Button
            onClick={handleSubmit}
            disabled={!canSubmit || submitMutation.isPending}
          >
            {submitMutation.isPending ? (
              <>
                <span className="animate-spin mr-2">...</span>
                Submitting...
              </>
            ) : (
              <>
                <ShieldCheckIcon className="h-4 w-4 mr-2" />
                Submit Attestation
              </>
            )}
          </Button>
        </CardFooter>
      )}
    </Card>
  );
}

export default AttestationFormCard;
