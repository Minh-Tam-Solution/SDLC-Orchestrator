/**
 * =========================================================================
 * Spec Validation Panel Component
 * SDLC Orchestrator - Sprint 118 (SPEC-0002 Specification Standard)
 *
 * Version: 1.0.0
 * Date: January 29, 2026
 * Framework: SDLC 5.3.0 Quality Assurance System
 * Spec Reference: SPEC-0002
 *
 * Purpose: YAML frontmatter validation panel for specifications
 * Features: Real-time validation, error display, compliance scoring
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
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  useValidateFrontmatter,
  useComplianceScoreDisplay,
  type FrontmatterValidationResponse,
  type ValidationError,
} from "@/hooks/useSpecifications";

// =============================================================================
// Icons
// =============================================================================

function DocumentCheckIcon({ className }: { className?: string }) {
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
        d="M10.125 2.25h-4.5c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125v-9M10.125 2.25h.375a9 9 0 0 1 9 9v.375M10.125 2.25A3.375 3.375 0 0 1 13.5 5.625v1.5c0 .621.504 1.125 1.125 1.125h1.5a3.375 3.375 0 0 1 3.375 3.375M9 15l2.25 2.25L15 12"
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

function XCircleIcon({ className }: { className?: string }) {
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
        d="m9.75 9.75 4.5 4.5m0-4.5-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
      />
    </svg>
  );
}

function ExclamationTriangleIcon({ className }: { className?: string }) {
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
        d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
      />
    </svg>
  );
}

function LightBulbIcon({ className }: { className?: string }) {
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
        d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18"
      />
    </svg>
  );
}

function PlayIcon({ className }: { className?: string }) {
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
        d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z"
      />
    </svg>
  );
}

// =============================================================================
// Sub-components
// =============================================================================

interface ValidationErrorItemProps {
  error: ValidationError;
}

function ValidationErrorItem({ error }: ValidationErrorItemProps) {
  const isError = error.severity === "error";

  return (
    <div
      className={`flex items-start gap-2 p-3 rounded-lg ${
        isError ? "bg-red-50 border border-red-200" : "bg-yellow-50 border border-yellow-200"
      }`}
    >
      {isError ? (
        <XCircleIcon className="h-5 w-5 text-red-500 flex-shrink-0" />
      ) : (
        <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 flex-shrink-0" />
      )}
      <div>
        <div className={`font-medium ${isError ? "text-red-700" : "text-yellow-700"}`}>
          {error.field}
          {error.line_number && (
            <span className="ml-2 text-xs text-gray-500">
              (Line {error.line_number})
            </span>
          )}
        </div>
        <div className={`text-sm ${isError ? "text-red-600" : "text-yellow-600"}`}>
          {error.message}
        </div>
      </div>
    </div>
  );
}

interface ParsedMetadataDisplayProps {
  metadata: FrontmatterValidationResponse["parsed_metadata"];
}

function ParsedMetadataDisplay({ metadata }: ParsedMetadataDisplayProps) {
  if (!metadata) return null;

  const fields = [
    { label: "Spec ID", value: metadata.spec_id },
    { label: "Version", value: metadata.spec_version },
    { label: "Status", value: metadata.status },
    { label: "Tier", value: metadata.tier },
    { label: "Stage", value: metadata.stage },
    { label: "Owner", value: metadata.owner },
    { label: "Created", value: metadata.created },
    { label: "Updated", value: metadata.last_updated },
    { label: "Related ADRs", value: metadata.related_adrs?.join(", ") },
  ].filter((f) => f.value);

  return (
    <div className="p-4 bg-gray-50 rounded-lg">
      <div className="text-sm font-medium text-gray-700 mb-3">
        Parsed Metadata
      </div>
      <div className="grid grid-cols-2 gap-2 text-sm">
        {fields.map((field, idx) => (
          <div key={idx}>
            <span className="text-gray-500">{field.label}:</span>{" "}
            <span className="font-medium">{field.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// =============================================================================
// Sample Template
// =============================================================================

const SAMPLE_FRONTMATTER = `---
spec_version: "1.0"
spec_id: SPEC-0001
status: approved
tier: PROFESSIONAL
stage: 04-build
owner: backend-team
created: 2026-01-29
last_updated: 2026-01-29
related_adrs: [ADR-041, ADR-022]
---

## 1. Overview
This specification defines the requirements for...

## 2. Requirements
### 2.1 Functional Requirements (BDD)
- GIVEN a user submits code WHEN validation runs THEN index is calculated

### 2.2 Non-Functional Requirements
- Performance: <100ms p95 latency
- Security: OWASP ASVS L2

## 3. Acceptance Criteria
- [ ] All signals calculate correctly
- [ ] Routing decisions match zone thresholds
`;

// =============================================================================
// Main Component
// =============================================================================

interface SpecValidationPanelProps {
  initialContent?: string;
  onValidationComplete?: (result: FrontmatterValidationResponse) => void;
}

export function SpecValidationPanel({
  initialContent = "",
  onValidationComplete,
}: SpecValidationPanelProps) {
  const [content, setContent] = useState(initialContent);
  const [result, setResult] = useState<FrontmatterValidationResponse | null>(null);
  const validateMutation = useValidateFrontmatter();

  const handleValidate = async () => {
    try {
      const validationResult = await validateMutation.mutateAsync({
        content,
      });
      setResult(validationResult);
      onValidationComplete?.(validationResult);
    } catch (error) {
      console.error("Validation failed:", error);
    }
  };

  const handleLoadSample = () => {
    setContent(SAMPLE_FRONTMATTER);
    setResult(null);
  };

  // Call hook unconditionally (React rules of hooks)
  const scoreDisplay = useComplianceScoreDisplay(result?.compliance_score ?? 0);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <DocumentCheckIcon className="h-5 w-5 text-blue-600" />
            <CardTitle className="text-lg">Specification Validator</CardTitle>
          </div>
          {result && (
            <Badge
              className={
                result.valid
                  ? "bg-green-100 text-green-700 border-green-200"
                  : "bg-red-100 text-red-700 border-red-200"
              }
            >
              {result.valid ? (
                <>
                  <CheckCircleIcon className="h-3 w-3 mr-1" />
                  Valid
                </>
              ) : (
                <>
                  <XCircleIcon className="h-3 w-3 mr-1" />
                  Invalid
                </>
              )}
            </Badge>
          )}
        </div>
        <CardDescription>
          Validate YAML frontmatter against SPEC-0002 Specification Standard
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Input Area */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Specification Content</label>
            <Button variant="ghost" size="sm" onClick={handleLoadSample}>
              Load Sample
            </Button>
          </div>
          <Textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste your specification markdown with YAML frontmatter..."
            className="font-mono text-sm min-h-[200px]"
          />
        </div>

        {/* Validate Button */}
        <Button
          onClick={handleValidate}
          disabled={!content || validateMutation.isPending}
          className="w-full"
        >
          <PlayIcon className="h-4 w-4 mr-2" />
          {validateMutation.isPending ? "Validating..." : "Validate Specification"}
        </Button>

        {/* Results */}
        {result && (
          <div className="space-y-4 border-t pt-4">
            {/* Compliance Score */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <div className="text-sm text-gray-500">Compliance Score</div>
                <div className={`text-3xl font-bold ${scoreDisplay?.color}`}>
                  {result.compliance_score}%
                </div>
              </div>
              <div className={`text-lg font-medium ${scoreDisplay?.color}`}>
                {scoreDisplay?.label}
              </div>
            </div>

            {/* Errors */}
            {result.errors.length > 0 && (
              <div className="space-y-2">
                <div className="text-sm font-medium text-red-700">
                  Errors ({result.errors.length})
                </div>
                {result.errors.map((error, idx) => (
                  <ValidationErrorItem key={idx} error={error} />
                ))}
              </div>
            )}

            {/* Warnings */}
            {result.warnings.length > 0 && (
              <div className="space-y-2">
                <div className="text-sm font-medium text-yellow-700">
                  Warnings ({result.warnings.length})
                </div>
                {result.warnings.map((warning, idx) => (
                  <ValidationErrorItem key={idx} error={warning} />
                ))}
              </div>
            )}

            {/* Parsed Metadata */}
            {result.parsed_metadata && (
              <ParsedMetadataDisplay metadata={result.parsed_metadata} />
            )}

            {/* Suggestions */}
            {result.suggestions.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium text-amber-700">
                  <LightBulbIcon className="h-4 w-4" />
                  Suggestions
                </div>
                <ul className="space-y-1 text-sm text-amber-600">
                  {result.suggestions.map((suggestion, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-amber-500">•</span>
                      {suggestion}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Success Message */}
            {result.valid && result.errors.length === 0 && (
              <div className="flex items-center gap-2 p-4 bg-green-50 rounded-lg text-green-700">
                <CheckCircleIcon className="h-5 w-5" />
                <span>
                  Specification is valid and compliant with SPEC-0002 standard.
                </span>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default SpecValidationPanel;
