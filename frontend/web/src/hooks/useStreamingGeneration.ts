/**
 * =========================================================================
 * useStreamingGeneration - SSE Streaming Hook for Code Generation
 * SDLC Orchestrator - Sprint 54 Day 1
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 54 Implementation
 * Authority: Frontend Team + CTO Approved
 * Foundation: Progressive Code Generation Flow Plan
 *
 * Purpose:
 * - Connect to SSE endpoint for code generation
 * - Parse and handle streaming events
 * - Track generated files with status
 * - Handle quality gate results
 * - Support resume from checkpoint
 * - Manage connection lifecycle
 *
 * References:
 * - docs/04-build/02-Sprint-Plans/CURRENT-SPRINT.md
 * - backend/app/schemas/streaming.py
 * =========================================================================
 */

import { useState, useCallback, useRef, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getAccessToken } from "@/api/client";
import type {
  StreamingFile,
  CodegenStreamEvent,
  StartedEvent,
  FileGeneratingEvent,
  FileGeneratedEvent,
  QualityGateEvent,
  CompletedEvent,
  ErrorEvent,
} from "@/types/streaming";

// ============================================================================
// Types
// ============================================================================

export type GenerationStatus =
  | "idle"
  | "connecting"
  | "generating"
  | "quality_check"
  | "completed"
  | "error"
  | "cancelled";

export interface QualityGateResult {
  gate_number: number;
  gate_name: string;
  status: "passed" | "failed" | "skipped";
  issues: number;
  duration_ms: number;
}

export interface GenerationResult {
  success: boolean;
  total_files: number;
  total_lines: number;
  duration_ms: number;
  files: StreamingFile[];
  quality_gates: QualityGateResult[];
  error?: string;
}

export interface UseStreamingGenerationOptions {
  /** Base API URL */
  baseUrl?: string;
  /** Callback when generation starts */
  onStart?: (event: StartedEvent) => void;
  /** Callback when file starts generating */
  onFileGenerating?: (event: FileGeneratingEvent) => void;
  /** Callback when file is generated */
  onFileGenerated?: (event: FileGeneratedEvent) => void;
  /** Callback when quality gate completes */
  onQualityGate?: (event: QualityGateEvent) => void;
  /** Callback when generation completes */
  onComplete?: (result: GenerationResult) => void;
  /** Callback when error occurs */
  onError?: (error: string) => void;
}

export interface UseStreamingGenerationReturn {
  /** Current generation status */
  status: GenerationStatus;
  /** List of generated/generating files */
  files: StreamingFile[];
  /** Current file being generated */
  currentFile: string | null;
  /** Quality gate results */
  qualityGates: QualityGateResult[];
  /** Provider info (model, provider name) */
  providerInfo: { model: string; provider: string } | null;
  /** Progress percentage (0-100) */
  progress: number;
  /** Total expected files */
  totalExpected: number | null;
  /** Generation start time */
  startTime: Date | null;
  /** Error message if any */
  error: string | null;
  /** Start generation with blueprint */
  startGeneration: (sessionId: string, blueprint: object) => void;
  /** Resume generation from session */
  resumeGeneration: (sessionId: string) => void;
  /** Cancel current generation */
  cancelGeneration: () => void;
  /** Reset state */
  reset: () => void;
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useStreamingGeneration(
  options: UseStreamingGenerationOptions = {}
): UseStreamingGenerationReturn {
  const {
    baseUrl = import.meta.env["VITE_API_URL"] || "http://localhost:8320/api/v1",
    onStart,
    onFileGenerating,
    onFileGenerated,
    onQualityGate,
    onComplete,
    onError,
  } = options;

  const queryClient = useQueryClient();
  const abortControllerRef = useRef<AbortController | null>(null);

  // State
  const [status, setStatus] = useState<GenerationStatus>("idle");
  const [files, setFiles] = useState<StreamingFile[]>([]);
  const [currentFile, setCurrentFile] = useState<string | null>(null);
  const [qualityGates, setQualityGates] = useState<QualityGateResult[]>([]);
  const [providerInfo, setProviderInfo] = useState<{
    model: string;
    provider: string;
  } | null>(null);
  const [progress, setProgress] = useState(0);
  const [totalExpected, setTotalExpected] = useState<number | null>(null);
  const [startTime, setStartTime] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Process SSE event
  const processEvent = useCallback(
    (event: CodegenStreamEvent) => {
      switch (event.type) {
        case "started": {
          const startedEvent = event as StartedEvent;
          setProviderInfo({
            model: startedEvent.model,
            provider: startedEvent.provider,
          });
          setStatus("generating");
          onStart?.(startedEvent);
          break;
        }

        case "file_generating": {
          const generatingEvent = event as FileGeneratingEvent;
          setCurrentFile(generatingEvent.path);

          // Add file with generating status
          setFiles((prev) => {
            // Check if file already exists
            if (prev.some((f) => f.path === generatingEvent.path)) {
              return prev;
            }
            return [
              ...prev,
              {
                path: generatingEvent.path,
                content: "",
                lines: 0,
                language: detectLanguage(generatingEvent.path),
                status: "generating",
              },
            ];
          });

          onFileGenerating?.(generatingEvent);
          break;
        }

        case "file_generated": {
          const generatedEvent = event as FileGeneratedEvent;
          setCurrentFile(null);

          // Update file with content and valid status
          setFiles((prev) =>
            prev.map((f) =>
              f.path === generatedEvent.path
                ? {
                    path: generatedEvent.path,
                    content: generatedEvent.content,
                    lines: generatedEvent.lines,
                    language: generatedEvent.language,
                    status: generatedEvent.syntax_valid === false ? "error" : "valid",
                  }
                : f
            )
          );

          // Update progress
          if (totalExpected) {
            const completedCount = files.filter(
              (f) => f.status !== "generating"
            ).length + 1;
            setProgress(Math.round((completedCount / totalExpected) * 100));
          }

          onFileGenerated?.(generatedEvent);
          break;
        }

        case "quality_started":
          setStatus("quality_check");
          break;

        case "quality_gate": {
          const gateEvent = event as QualityGateEvent;
          const gateResult: QualityGateResult = {
            gate_number: gateEvent.gate_number,
            gate_name: gateEvent.gate_name,
            status: gateEvent.status,
            issues: gateEvent.issues,
            duration_ms: gateEvent.duration_ms,
          };
          setQualityGates((prev) => [...prev, gateResult]);
          onQualityGate?.(gateEvent);
          break;
        }

        case "completed": {
          const completedEvent = event as CompletedEvent;
          setStatus("completed");
          setProgress(100);
          setCurrentFile(null);

          const result: GenerationResult = {
            success: completedEvent.success,
            total_files: completedEvent.total_files,
            total_lines: completedEvent.total_lines,
            duration_ms: completedEvent.duration_ms,
            files,
            quality_gates: qualityGates,
          };

          onComplete?.(result);

          // Invalidate session queries
          queryClient.invalidateQueries({ queryKey: ["sessions"] });
          break;
        }

        case "error": {
          const errorEvent = event as ErrorEvent;
          setStatus("error");
          setError(errorEvent.message);
          setCurrentFile(null);
          onError?.(errorEvent.message);
          break;
        }
      }
    },
    [files, qualityGates, totalExpected, onStart, onFileGenerating, onFileGenerated, onQualityGate, onComplete, onError, queryClient]
  );

  // Start SSE connection
  const connectSSE = useCallback(
    async (url: string, method: "GET" | "POST" = "GET", body?: object) => {
      const token = getAccessToken();
      if (!token) {
        setError("Not authenticated");
        setStatus("error");
        return;
      }

      setStatus("connecting");
      setError(null);
      setFiles([]);
      setQualityGates([]);
      setProgress(0);
      setStartTime(new Date());

      // Create abort controller
      abortControllerRef.current = new AbortController();

      try {
        const response = await fetch(url, {
          method,
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "text/event-stream",
            "Content-Type": "application/json",
          },
          body: body ? JSON.stringify(body) : undefined,
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        if (!response.body) {
          throw new Error("No response body");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const eventData = line.slice(6).trim();
              if (eventData) {
                try {
                  const event = JSON.parse(eventData) as CodegenStreamEvent;
                  processEvent(event);
                } catch (e) {
                  console.error("Failed to parse SSE event:", e);
                }
              }
            }
          }
        }
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") {
          setStatus("cancelled");
          return;
        }

        const message = err instanceof Error ? err.message : "Unknown error";
        setError(message);
        setStatus("error");
        onError?.(message);
      }
    },
    [processEvent, onError]
  );

  // Start generation with blueprint
  const startGeneration = useCallback(
    (sessionId: string, blueprint: object) => {
      const url = `${baseUrl}/codegen/generate/stream`;
      connectSSE(url, "POST", { session_id: sessionId, blueprint });
    },
    [baseUrl, connectSSE]
  );

  // Resume generation from session
  const resumeGeneration = useCallback(
    (sessionId: string) => {
      const url = `${baseUrl}/codegen/generate/resume/${sessionId}`;
      connectSSE(url, "POST");
    },
    [baseUrl, connectSSE]
  );

  // Cancel current generation
  const cancelGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStatus("cancelled");
    setCurrentFile(null);
  }, []);

  // Reset state
  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStatus("idle");
    setFiles([]);
    setCurrentFile(null);
    setQualityGates([]);
    setProviderInfo(null);
    setProgress(0);
    setTotalExpected(null);
    setStartTime(null);
    setError(null);
  }, []);

  return {
    status,
    files,
    currentFile,
    qualityGates,
    providerInfo,
    progress,
    totalExpected,
    startTime,
    error,
    startGeneration,
    resumeGeneration,
    cancelGeneration,
    reset,
  };
}

// ============================================================================
// Helpers
// ============================================================================

function detectLanguage(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase() || "";
  const langMap: Record<string, string> = {
    py: "python",
    ts: "typescript",
    tsx: "typescript",
    js: "javascript",
    jsx: "javascript",
    json: "json",
    yaml: "yaml",
    yml: "yaml",
    md: "markdown",
    sql: "sql",
    html: "html",
    css: "css",
    sh: "bash",
    txt: "text",
    toml: "toml",
    ini: "ini",
    cfg: "ini",
  };
  return langMap[ext] || ext;
}

export default useStreamingGeneration;
