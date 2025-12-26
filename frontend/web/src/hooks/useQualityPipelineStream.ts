/**
 * =========================================================================
 * useQualityPipelineStream - SSE Hook for Quality Pipeline Streaming
 * SDLC Orchestrator - Sprint 56 Day 1
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Backend Integration
 *
 * Purpose:
 * - Connect to backend SSE for quality events
 * - Stream quality gate results in real-time
 * - Aggregate issues as they're discovered
 * - Build PipelineResult from streaming events
 *
 * References:
 * - backend/app/schemas/streaming.py
 * - Sprint 55 Quality Components
 * =========================================================================
 */

import { useState, useCallback, useRef, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getAccessToken } from "@/api/client";
import { qualityKeys } from "./useQualityApi";
import type {
  PipelineResult,
  GateResult,
  GateName,
  GateStatus,
  Severity,
} from "@/types/quality";

// ============================================================================
// Types
// ============================================================================

/** Stream connection state */
export type StreamConnectionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "error"
  | "completed";

/** Quality streaming event from backend */
interface BackendQualityEvent {
  type: "quality_started" | "quality_gate" | "completed" | "error";
  timestamp: string;
  session_id: string;
  gate_number?: number;
  gate_name?: string;
  status?: "passed" | "failed" | "skipped";
  issues?: number;
  duration_ms?: number;
  message?: string;
}

/** Gate state during streaming */
export interface StreamingGateState {
  gateName: GateName;
  status: GateStatus;
  startTime?: Date;
  endTime?: Date;
  durationMs: number;
  issueCount: number;
  issues: StreamingIssue[];
}

/** Issue found during streaming */
export interface StreamingIssue {
  id: string;
  gateName: GateName;
  severity: Severity;
  file: string;
  line?: number;
  message: string;
  timestamp: Date;
}

/** Quality pipeline stream state */
export interface QualityPipelineStreamState {
  connectionState: StreamConnectionState;
  sessionId: string | null;
  startTime: Date | null;
  currentGate: GateName | null;
  gates: Record<GateName, StreamingGateState>;
  issues: StreamingIssue[];
  progress: number;
  error: string | null;
}

/** Hook options */
export interface UseQualityPipelineStreamOptions {
  /** Base API URL */
  baseUrl?: string;
  /** Auto-reconnect on disconnect */
  autoReconnect?: boolean;
  /** Max reconnect attempts */
  maxReconnectAttempts?: number;
  /** Callback when gate starts */
  onGateStart?: (gateName: GateName) => void;
  /** Callback when gate completes */
  onGateComplete?: (gate: StreamingGateState) => void;
  /** Callback when issue found */
  onIssueFound?: (issue: StreamingIssue) => void;
  /** Callback when pipeline completes */
  onComplete?: (result: PipelineResult) => void;
  /** Callback when error occurs */
  onError?: (error: string) => void;
}

/** Hook return type */
export interface UseQualityPipelineStreamReturn {
  /** Current stream state */
  state: QualityPipelineStreamState;
  /** Connect to session quality stream */
  connect: (sessionId: string) => void;
  /** Disconnect from stream */
  disconnect: () => void;
  /** Reset stream state */
  reset: () => void;
  /** Build PipelineResult from current state */
  getPipelineResult: () => PipelineResult | null;
  /** Get issues for specific gate */
  getGateIssues: (gateName: GateName) => StreamingIssue[];
  /** Get issues for specific file */
  getFileIssues: (filePath: string) => StreamingIssue[];
  /** Get critical issues count */
  getCriticalCount: () => number;
}

// ============================================================================
// Constants
// ============================================================================

const GATE_ORDER: GateName[] = ["syntax", "security", "architecture", "tests"];

const INITIAL_GATES: Record<GateName, StreamingGateState> = {
  syntax: { gateName: "syntax", status: "pending", durationMs: 0, issueCount: 0, issues: [] },
  security: { gateName: "security", status: "pending", durationMs: 0, issueCount: 0, issues: [] },
  architecture: { gateName: "architecture", status: "pending", durationMs: 0, issueCount: 0, issues: [] },
  tests: { gateName: "tests", status: "pending", durationMs: 0, issueCount: 0, issues: [] },
};

const INITIAL_STATE: QualityPipelineStreamState = {
  connectionState: "disconnected",
  sessionId: null,
  startTime: null,
  currentGate: null,
  gates: { ...INITIAL_GATES },
  issues: [],
  progress: 0,
  error: null,
};

// ============================================================================
// Hook Implementation
// ============================================================================

export function useQualityPipelineStream(
  options: UseQualityPipelineStreamOptions = {}
): UseQualityPipelineStreamReturn {
  const {
    baseUrl = import.meta.env["VITE_API_URL"] || "http://localhost:8320/api/v1",
    autoReconnect = false,
    maxReconnectAttempts = 3,
    onGateStart,
    onGateComplete,
    onIssueFound: _onIssueFound, // Reserved for future use
    onComplete,
    onError,
  } = options;

  const queryClient = useQueryClient();
  const abortControllerRef = useRef<AbortController | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // State
  const [state, setState] = useState<QualityPipelineStreamState>(INITIAL_STATE);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Map backend gate name to frontend
  const mapGateName = useCallback((backendName: string): GateName => {
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
  }, []);

  // Calculate progress based on completed gates
  const calculateProgress = useCallback((gates: Record<GateName, StreamingGateState>): number => {
    let completed = 0;
    let running = 0;

    for (const gateName of GATE_ORDER) {
      const gate = gates[gateName];
      if (gate.status === "passed" || gate.status === "failed" || gate.status === "skipped") {
        completed++;
      } else if (gate.status === "running") {
        running++;
      }
    }

    // Each gate is 25%, running gate contributes partial progress
    const baseProgress = (completed / GATE_ORDER.length) * 100;
    const runningProgress = (running / GATE_ORDER.length) * 12.5; // Half of 25%
    return Math.round(baseProgress + runningProgress);
  }, []);

  // Process SSE event
  const processEvent = useCallback(
    (event: BackendQualityEvent) => {
      switch (event.type) {
        case "quality_started":
          setState((prev) => ({
            ...prev,
            connectionState: "connected",
            startTime: new Date(),
            currentGate: null,
          }));
          break;

        case "quality_gate": {
          if (!event.gate_name || !event.status) break;

          const gateName = mapGateName(event.gate_name);
          const now = new Date();

          setState((prev) => {
            const updatedGates = { ...prev.gates };
            const existingGate = updatedGates[gateName];

            updatedGates[gateName] = {
              ...existingGate,
              gateName,
              status: event.status as GateStatus,
              endTime: now,
              durationMs: event.duration_ms || 0,
              issueCount: event.issues || 0,
            };

            // Find next pending gate
            let nextGate: GateName | null = null;
            for (const name of GATE_ORDER) {
              if (updatedGates[name].status === "pending") {
                nextGate = name;
                break;
              }
            }

            // Mark next gate as running if exists
            if (nextGate) {
              updatedGates[nextGate] = {
                ...updatedGates[nextGate],
                status: "running",
                startTime: now,
              };
              onGateStart?.(nextGate);
            }

            // Trigger gate complete callback
            onGateComplete?.(updatedGates[gateName]);

            return {
              ...prev,
              gates: updatedGates,
              currentGate: nextGate,
              progress: calculateProgress(updatedGates),
            };
          });
          break;
        }

        case "completed":
          setState((prev) => ({
            ...prev,
            connectionState: "completed",
            currentGate: null,
            progress: 100,
          }));

          // Invalidate quality cache
          if (state.sessionId) {
            queryClient.invalidateQueries({
              queryKey: qualityKeys.session(state.sessionId),
            });
          }
          break;

        case "error":
          setState((prev) => ({
            ...prev,
            connectionState: "error",
            error: event.message || "Unknown error",
            currentGate: null,
          }));
          onError?.(event.message || "Unknown error");
          break;
      }
    },
    [mapGateName, calculateProgress, onGateStart, onGateComplete, onError, queryClient, state.sessionId]
  );

  // Connect to SSE stream
  const connect = useCallback(
    async (sessionId: string) => {
      const token = getAccessToken();
      if (!token) {
        setState((prev) => ({
          ...prev,
          connectionState: "error",
          error: "Not authenticated",
        }));
        return;
      }

      // Reset state
      setState({
        ...INITIAL_STATE,
        connectionState: "connecting",
        sessionId,
        gates: {
          syntax: { ...INITIAL_GATES.syntax, status: "running", startTime: new Date() },
          security: { ...INITIAL_GATES.security },
          architecture: { ...INITIAL_GATES.architecture },
          tests: { ...INITIAL_GATES.tests },
        },
        currentGate: "syntax",
      });

      // Start first gate callback
      onGateStart?.("syntax");

      // Create abort controller
      abortControllerRef.current = new AbortController();

      try {
        const url = `${baseUrl}/codegen/sessions/${sessionId}/quality/stream`;
        const response = await fetch(url, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "text/event-stream",
          },
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
                  const event = JSON.parse(eventData) as BackendQualityEvent;
                  processEvent(event);
                } catch {
                  console.error("Failed to parse quality event");
                }
              }
            }
          }
        }

        // Stream ended normally
        setState((prev) => ({
          ...prev,
          connectionState: prev.connectionState === "error" ? "error" : "completed",
          progress: 100,
        }));

        reconnectAttemptsRef.current = 0;
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") {
          return;
        }

        const message = err instanceof Error ? err.message : "Connection failed";
        setState((prev) => ({
          ...prev,
          connectionState: "error",
          error: message,
        }));
        onError?.(message);

        // Auto-reconnect logic
        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          setTimeout(() => connect(sessionId), 2000 * reconnectAttemptsRef.current);
        }
      }
    },
    [baseUrl, processEvent, onGateStart, onError, autoReconnect, maxReconnectAttempts]
  );

  // Disconnect from stream
  const disconnect = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setState((prev) => ({
      ...prev,
      connectionState: "disconnected",
    }));
  }, []);

  // Reset state
  const reset = useCallback(() => {
    disconnect();
    setState(INITIAL_STATE);
    reconnectAttemptsRef.current = 0;
  }, [disconnect]);

  // Build gate-specific details from streaming state
  const buildGateDetails = useCallback(
    (gateName: GateName, gateState: StreamingGateState): GateResult["details"] => {
      const issues = gateState.issues;
      const passed = gateState.status === "passed";

      switch (gateName) {
        case "syntax":
          return {
            passed,
            filesChecked: 0, // Not available in streaming
            filesPassed: passed ? 0 : 0,
            issues: issues.map((issue) => ({
              file: issue.file,
              line: issue.line || 0,
              column: 0,
              message: issue.message,
              vietnameseMessage: issue.message,
            })),
          };
        case "security": {
          const criticalCount = issues.filter((i) => i.severity === "critical").length;
          const highCount = issues.filter((i) => i.severity === "high").length;
          const mediumCount = issues.filter((i) => i.severity === "medium").length;
          const lowCount = issues.filter((i) => i.severity === "low").length;
          return {
            passed,
            criticalCount,
            highCount,
            mediumCount,
            lowCount,
            issues: issues.map((issue) => ({
              file: issue.file,
              line: issue.line || 0,
              ruleId: issue.id,
              severity: issue.severity,
              message: issue.message,
              vietnameseMessage: issue.message,
            })),
          };
        }
        case "architecture":
          return {
            passed,
            issues: issues.map((issue) => ({
              file: issue.file,
              line: issue.line,
              rule: "streaming",
              message: issue.message,
              vietnameseMessage: issue.message,
            })),
          };
        case "tests":
          return {
            passed,
            testsRun: gateState.issueCount,
            testsPassed: passed ? gateState.issueCount : 0,
            testsFailed: passed ? 0 : gateState.issueCount,
            results: issues.map((issue) => ({
              testName: issue.message,
              passed: false,
              errorMessage: issue.message,
            })),
          };
        default:
          return { error: "Unknown gate type" };
      }
    },
    []
  );

  // Build PipelineResult from current state
  const getPipelineResult = useCallback((): PipelineResult | null => {
    if (state.connectionState !== "completed") {
      return null;
    }

    const gates: GateResult[] = GATE_ORDER.map((gateName) => {
      const gateState = state.gates[gateName];
      return {
        gateName,
        passed: gateState.status === "passed",
        status: gateState.status,
        durationMs: gateState.durationMs,
        details: buildGateDetails(gateName, gateState),
      };
    });

    const gatesPassed = gates.filter((g) => g.status === "passed").length;
    const gatesFailed = gates.filter((g) => g.status === "failed").length;
    const totalDurationMs = gates.reduce((sum, g) => sum + g.durationMs, 0);

    const vietnameseSummary =
      gatesFailed === 0
        ? `Tất cả ${gates.length} cổng đã đạt`
        : `${gatesPassed}/${gates.length} cổng đã đạt`;

    return {
      passed: gatesFailed === 0,
      totalDurationMs,
      gates,
      summary: {
        gatesRun: gates.length,
        gatesPassed,
        gatesFailed,
      },
      vietnameseSummary,
    };
  }, [state, buildGateDetails]);

  // Get issues for specific gate
  const getGateIssues = useCallback(
    (gateName: GateName): StreamingIssue[] => {
      return state.issues.filter((issue) => issue.gateName === gateName);
    },
    [state.issues]
  );

  // Get issues for specific file
  const getFileIssues = useCallback(
    (filePath: string): StreamingIssue[] => {
      return state.issues.filter((issue) => issue.file === filePath);
    },
    [state.issues]
  );

  // Get critical issues count
  const getCriticalCount = useCallback((): number => {
    return state.issues.filter((issue) => issue.severity === "critical").length;
  }, [state.issues]);

  // Trigger onComplete when pipeline completes
  useEffect(() => {
    if (state.connectionState === "completed") {
      const result = getPipelineResult();
      if (result) {
        onComplete?.(result);
      }
    }
  }, [state.connectionState, getPipelineResult, onComplete]);

  return {
    state,
    connect,
    disconnect,
    reset,
    getPipelineResult,
    getGateIssues,
    getFileIssues,
    getCriticalCount,
  };
}

// ============================================================================
// Export
// ============================================================================

export default useQualityPipelineStream;
