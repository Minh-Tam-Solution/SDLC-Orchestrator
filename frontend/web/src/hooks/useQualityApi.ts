/**
 * =========================================================================
 * useQualityApi - React Query Hooks for Quality Pipeline API
 * SDLC Orchestrator - Sprint 56 Day 1
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Backend Integration
 *
 * Purpose:
 * - Connect quality components to backend API
 * - Fetch quality pipeline results
 * - Transform backend data to frontend types
 * - Cache and invalidate quality data
 *
 * References:
 * - backend/app/schemas/streaming.py
 * - backend/app/api/routes/codegen.py
 * =========================================================================
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import type {
  PipelineResult,
  GateResult,
  GateName,
  GateStatus,
  Severity,
  SyntaxValidationResult,
  SecurityValidationResult,
  ArchitectureValidationResult,
  TestValidationResult,
} from "@/types/quality";

// ============================================================================
// API Types (from backend)
// ============================================================================

/** Backend gate status enum */
type BackendGateStatus = "pending" | "running" | "passed" | "failed" | "skipped";

/** Backend gate issue structure */
interface BackendGateIssue {
  file_path: string;
  line: number;
  column: number;
  severity: "critical" | "high" | "medium" | "low" | "info";
  code: string;
  message: string;
  suggestion?: string;
}

/** Backend gate result from API */
interface BackendGateResult {
  gate_name: string;
  gate_number: number;
  status: BackendGateStatus;
  duration_ms: number;
  issues: BackendGateIssue[];
  summary: string;
  details?: Record<string, unknown>;
}

/** Backend pipeline result from API */
interface BackendPipelineResult {
  success: boolean;
  gates: BackendGateResult[];
  total_duration_ms: number;
  failed_gate?: string;
  summary: string;
}

/** Generate with quality response */
interface GenerateWithQualityResponse {
  session_id: string;
  files: Array<{
    path: string;
    content: string;
    lines: number;
    language: string;
  }>;
  quality: BackendPipelineResult;
  metadata: {
    model: string;
    provider: string;
    generated_at: string;
    duration_ms: number;
  };
}

/** Validation request */
interface ValidateCodeRequest {
  files: Array<{
    path: string;
    content: string;
    language?: string;
  }>;
  run_tests?: boolean;
}

/** Validation response */
interface ValidateCodeResponse {
  valid: boolean;
  quality: BackendPipelineResult;
}

// ============================================================================
// Transform Functions
// ============================================================================

/**
 * Map backend gate name to frontend GateName type
 */
function mapGateName(backendName: string): GateName {
  const nameMap: Record<string, GateName> = {
    Syntax: "syntax",
    syntax: "syntax",
    Security: "security",
    security: "security",
    Context: "architecture",
    context: "architecture",
    Architecture: "architecture",
    architecture: "architecture",
    Tests: "tests",
    tests: "tests",
  };
  return nameMap[backendName] || "syntax";
}

/**
 * Map backend gate status to frontend GateStatus type
 */
function mapGateStatus(backendStatus: BackendGateStatus): GateStatus {
  return backendStatus as GateStatus;
}

/**
 * Map backend severity to frontend Severity type
 */
function mapSeverity(backendSeverity: string): Severity {
  return backendSeverity as Severity;
}

/**
 * Transform backend gate result to frontend GateResult
 */
function transformGateResult(backend: BackendGateResult): GateResult {
  const gateName = mapGateName(backend.gate_name);
  const status = mapGateStatus(backend.status);
  const passed = status === "passed";

  // Build gate-specific details based on gate type
  let details: GateResult["details"];

  if (gateName === "syntax") {
    const syntaxDetails: SyntaxValidationResult = {
      passed,
      filesChecked: (backend.details?.["files_checked"] as number) || 0,
      filesPassed: (backend.details?.["files_passed"] as number) || 0,
      issues: backend.issues.map((issue) => ({
        file: issue.file_path,
        line: issue.line,
        column: issue.column,
        message: issue.message,
        vietnameseMessage: issue.message, // TODO: Add translation
      })),
    };
    details = syntaxDetails;
  } else if (gateName === "security") {
    const criticalCount = backend.issues.filter((i) => i.severity === "critical").length;
    const highCount = backend.issues.filter((i) => i.severity === "high").length;
    const mediumCount = backend.issues.filter((i) => i.severity === "medium").length;
    const lowCount = backend.issues.filter((i) => i.severity === "low").length;

    const securityDetails: SecurityValidationResult = {
      passed,
      criticalCount,
      highCount,
      mediumCount,
      lowCount,
      issues: backend.issues.map((issue) => ({
        file: issue.file_path,
        line: issue.line,
        ruleId: issue.code,
        severity: mapSeverity(issue.severity),
        message: issue.message,
        vietnameseMessage: issue.message, // TODO: Add translation
        fixSuggestion: issue.suggestion,
      })),
    };
    details = securityDetails;
  } else if (gateName === "architecture") {
    const archDetails: ArchitectureValidationResult = {
      passed,
      issues: backend.issues.map((issue) => ({
        file: issue.file_path,
        line: issue.line,
        rule: issue.code,
        message: issue.message,
        vietnameseMessage: issue.message, // TODO: Add translation
      })),
    };
    details = archDetails;
  } else if (gateName === "tests") {
    const testsRun = (backend.details?.["tests_run"] as number) || 0;
    const testsPassed = (backend.details?.["tests_passed"] as number) || 0;
    const testsFailed = (backend.details?.["tests_failed"] as number) || 0;

    const testDetails: TestValidationResult = {
      passed,
      testsRun,
      testsPassed,
      testsFailed,
      results: backend.issues.map((issue) => ({
        testName: issue.code,
        passed: false,
        errorMessage: issue.message,
      })),
    };
    details = testDetails;
  } else {
    details = { error: "Unknown gate type" };
  }

  return {
    gateName,
    passed,
    status,
    durationMs: backend.duration_ms,
    details,
  };
}

/**
 * Transform backend pipeline result to frontend PipelineResult
 */
function transformPipelineResult(backend: BackendPipelineResult): PipelineResult {
  const gates = backend.gates.map(transformGateResult);
  const gatesRun = gates.length;
  const gatesPassed = gates.filter((g) => g.status === "passed").length;
  const gatesFailed = gates.filter((g) => g.status === "failed").length;

  // Generate Vietnamese summary
  let vietnameseSummary = "";
  if (backend.success) {
    vietnameseSummary = `Tất cả ${gatesRun} cổng đã đạt`;
  } else if (backend.failed_gate) {
    const failedGateName = mapGateName(backend.failed_gate);
    const gateLabels: Record<GateName, string> = {
      syntax: "Cú pháp",
      security: "Bảo mật",
      architecture: "Kiến trúc",
      tests: "Kiểm thử",
    };
    vietnameseSummary = `Thất bại tại cổng ${gateLabels[failedGateName]}`;
  } else {
    vietnameseSummary = `${gatesPassed}/${gatesRun} cổng đã đạt`;
  }

  return {
    passed: backend.success,
    totalDurationMs: backend.total_duration_ms,
    gates,
    summary: {
      gatesRun,
      gatesPassed,
      gatesFailed,
    },
    vietnameseSummary,
  };
}

// ============================================================================
// Query Keys
// ============================================================================

export const qualityKeys = {
  all: ["quality"] as const,
  session: (sessionId: string) => [...qualityKeys.all, "session", sessionId] as const,
  history: (projectId: string) => [...qualityKeys.all, "history", projectId] as const,
  providers: () => [...qualityKeys.all, "providers"] as const,
  usage: () => [...qualityKeys.all, "usage"] as const,
};

// ============================================================================
// API Functions
// ============================================================================

/**
 * Fetch quality result for a session
 */
async function fetchSessionQuality(sessionId: string): Promise<PipelineResult> {
  const response = await apiClient.get<GenerateWithQualityResponse>(
    `/codegen/sessions/${sessionId}`
  );
  return transformPipelineResult(response.data.quality);
}

/**
 * Validate code files
 */
async function validateCode(request: ValidateCodeRequest): Promise<PipelineResult> {
  const response = await apiClient.post<ValidateCodeResponse>(
    "/codegen/validate",
    request
  );
  return transformPipelineResult(response.data.quality);
}

/**
 * Fetch provider health and availability
 */
interface ProviderInfo {
  name: string;
  available: boolean;
  latency_ms?: number;
  model?: string;
}

async function fetchProviders(): Promise<ProviderInfo[]> {
  const response = await apiClient.get<{ providers: ProviderInfo[] }>(
    "/codegen/providers"
  );
  return response.data.providers;
}

/**
 * Fetch usage report with quality metrics
 */
interface UsageReport {
  period: string;
  total_generations: number;
  total_tokens: number;
  total_cost_usd: number;
  quality_metrics: {
    pass_rate: number;
    avg_gate_time_ms: number;
    issues_by_severity: Record<Severity, number>;
  };
}

async function fetchUsageReport(): Promise<UsageReport> {
  const response = await apiClient.get<UsageReport>("/codegen/usage/report");
  return response.data;
}

// ============================================================================
// React Query Hooks
// ============================================================================

/**
 * Hook to fetch quality result for a session
 */
export function useSessionQuality(sessionId: string | null) {
  return useQuery({
    queryKey: qualityKeys.session(sessionId || ""),
    queryFn: () => fetchSessionQuality(sessionId!),
    enabled: !!sessionId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes (previously cacheTime)
  });
}

/**
 * Hook to validate code files
 */
export function useValidateCode() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: validateCode,
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: qualityKeys.all });
    },
  });
}

/**
 * Hook to fetch available providers
 */
export function useCodegenProviders() {
  return useQuery({
    queryKey: qualityKeys.providers(),
    queryFn: fetchProviders,
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch usage report
 */
export function useUsageReport() {
  return useQuery({
    queryKey: qualityKeys.usage(),
    queryFn: fetchUsageReport,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// ============================================================================
// Helper Hooks
// ============================================================================

/**
 * Hook to get quality score from a session
 */
export function useQualityScore(sessionId: string | null): {
  score: number;
  grade: string;
  isLoading: boolean;
  error: Error | null;
} {
  const { data, isLoading, error } = useSessionQuality(sessionId);

  if (!data) {
    return { score: 0, grade: "N/A", isLoading, error };
  }

  // Calculate score based on gates
  let score = 100;
  let penalty = 0;

  for (const gate of data.gates) {
    if (gate.status === "failed") {
      penalty += 25;
    } else if (gate.status === "skipped") {
      penalty += 5;
    }
  }

  score = Math.max(0, score - penalty);
  const grade =
    score >= 90 ? "A" :
    score >= 80 ? "B" :
    score >= 70 ? "C" :
    score >= 60 ? "D" : "F";

  return { score, grade, isLoading, error };
}

/**
 * Hook to invalidate quality cache
 */
export function useInvalidateQualityCache() {
  const queryClient = useQueryClient();

  return {
    invalidateSession: (sessionId: string) => {
      queryClient.invalidateQueries({ queryKey: qualityKeys.session(sessionId) });
    },
    invalidateAll: () => {
      queryClient.invalidateQueries({ queryKey: qualityKeys.all });
    },
  };
}

// ============================================================================
// Export
// ============================================================================

export {
  transformPipelineResult,
  transformGateResult,
  mapGateName,
  mapGateStatus,
  mapSeverity,
};
