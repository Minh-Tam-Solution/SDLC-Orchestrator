/**
 * =========================================================================
 * useQualityStreamBackend - Unified Backend Quality Stream Hook
 * SDLC Orchestrator - Sprint 56 Day 2
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Backend Integration
 *
 * Purpose:
 * - Unified hook for quality pipeline streaming from backend
 * - Supports authenticated SSE connections via fetch
 * - Compatible with QualityStreamProvider API
 * - Handles backend event types and transforms to frontend
 *
 * References:
 * - backend/app/schemas/streaming.py
 * - Sprint 55 Quality Components
 * =========================================================================
 */

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
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
// Types (Compatible with useQualityStream API)
// ============================================================================

export type StreamConnectionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "error"
  | "completed";

export interface GateStreamState {
  gateName: GateName;
  status: GateStatus;
  filesProcessed: number;
  filesTotal: number;
  issuesFound: number;
  startTime?: number;
  endTime?: number;
  durationMs?: number;
  passed?: boolean;
}

export interface StreamIssue {
  id: string;
  gateName: GateName;
  severity: Severity;
  file: string;
  line?: number;
  message: string;
  timestamp: number;
}

export interface QualityStreamState {
  connectionState: StreamConnectionState;
  pipelineStartTime?: number;
  pipelineEndTime?: number;
  gates: Record<GateName, GateStreamState>;
  issues: StreamIssue[];
  currentGate?: GateName;
  overallProgress: number;
  error?: string;
}

/** Backend quality event structure */
interface BackendQualityEvent {
  type:
    | "quality_started"
    | "quality_gate"
    | "quality_issue"
    | "quality_completed"
    | "error";
  timestamp: string;
  session_id: string;
  gate_number?: number;
  gate_name?: string;
  status?: "pending" | "running" | "passed" | "failed" | "skipped";
  issues?: number;
  duration_ms?: number;
  files_processed?: number;
  files_total?: number;
  message?: string;
  severity?: string;
  file_path?: string;
  line?: number;
}

export interface UseQualityStreamBackendOptions {
  /** Base API URL */
  baseUrl?: string;
  /** Session ID to subscribe to */
  sessionId?: string;
  /** Auto-connect on mount */
  autoConnect?: boolean;
  /** Auto-reconnect on disconnect */
  autoReconnect?: boolean;
  /** Max reconnect attempts */
  maxReconnectAttempts?: number;
  /** Reconnect delay in ms */
  reconnectDelay?: number;
  /** Callback when pipeline starts */
  onPipelineStarted?: () => void;
  /** Callback when pipeline completes */
  onPipelineCompleted?: (result: PipelineResult) => void;
  /** Callback when gate starts */
  onGateStarted?: (gateName: GateName) => void;
  /** Callback when gate completes */
  onGateCompleted?: (gate: GateStreamState) => void;
  /** Callback when issue found */
  onIssueFound?: (issue: StreamIssue) => void;
  /** Callback when error occurs */
  onError?: (error: Error) => void;
}

export interface UseQualityStreamBackendReturn {
  /** Current stream state */
  state: QualityStreamState;
  /** Connect to SSE stream */
  connect: (sessionId?: string) => void;
  /** Disconnect from SSE stream */
  disconnect: () => void;
  /** Reset state to initial */
  reset: () => void;
  /** Check if currently streaming */
  isStreaming: boolean;
  /** Get computed pipeline result */
  getPipelineResult: () => PipelineResult | null;
  /** Get issues by gate */
  getIssuesByGate: (gateName: GateName) => StreamIssue[];
  /** Get issues by file */
  getIssuesByFile: (file: string) => StreamIssue[];
  /** Get critical issues count */
  getCriticalIssuesCount: () => number;
}

// ============================================================================
// Constants
// ============================================================================

const GATE_ORDER: GateName[] = ["syntax", "security", "architecture", "tests"];

const createInitialGateState = (gateName: GateName): GateStreamState => ({
  gateName,
  status: "pending",
  filesProcessed: 0,
  filesTotal: 0,
  issuesFound: 0,
});

const createInitialState = (): QualityStreamState => ({
  connectionState: "disconnected",
  gates: {
    syntax: createInitialGateState("syntax"),
    security: createInitialGateState("security"),
    architecture: createInitialGateState("architecture"),
    tests: createInitialGateState("tests"),
  },
  issues: [],
  overallProgress: 0,
});

// ============================================================================
// Utility Functions
// ============================================================================

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

function mapGateStatus(backendStatus: string): GateStatus {
  return backendStatus as GateStatus;
}

function calculateOverallProgress(gates: Record<GateName, GateStreamState>): number {
  let totalProgress = 0;

  for (const gateName of GATE_ORDER) {
    const gate = gates[gateName];
    const gateWeight = 25;

    if (gate.status === "passed" || gate.status === "failed" || gate.status === "skipped") {
      totalProgress += gateWeight;
    } else if (gate.status === "running") {
      const gateProgress =
        gate.filesTotal > 0
          ? (gate.filesProcessed / gate.filesTotal) * gateWeight
          : gateWeight * 0.5;
      totalProgress += gateProgress;
    }
  }

  return Math.round(totalProgress);
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useQualityStreamBackend(
  options: UseQualityStreamBackendOptions = {}
): UseQualityStreamBackendReturn {
  const {
    baseUrl = import.meta.env["VITE_API_URL"] || "http://localhost:8320/api/v1",
    sessionId: initialSessionId,
    autoConnect = false,
    autoReconnect = true,
    maxReconnectAttempts = 3,
    reconnectDelay = 3000,
    onPipelineStarted,
    onPipelineCompleted,
    onGateStarted,
    onGateCompleted,
    onIssueFound,
    onError,
  } = options;

  const queryClient = useQueryClient();
  const [state, setState] = useState<QualityStreamState>(createInitialState());
  const abortControllerRef = useRef<AbortController | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const issueIdCounterRef = useRef(0);
  const currentSessionIdRef = useRef<string | undefined>(initialSessionId);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Process SSE event
  const processEvent = useCallback(
    (event: BackendQualityEvent) => {
      const eventTime = new Date(event.timestamp).getTime();

      setState((prev) => {
        const newState = { ...prev };

        switch (event.type) {
          case "quality_started":
            newState.pipelineStartTime = eventTime;
            newState.connectionState = "connected";
            newState.currentGate = "syntax";
            newState.gates = {
              ...newState.gates,
              syntax: {
                ...newState.gates.syntax,
                status: "running",
                startTime: eventTime,
              },
            };
            onPipelineStarted?.();
            onGateStarted?.("syntax");
            break;

          case "quality_gate": {
            if (!event.gate_name || !event.status) break;

            const gateName = mapGateName(event.gate_name);
            const status = mapGateStatus(event.status);

            if (status === "running") {
              // Gate started
              newState.currentGate = gateName;
              newState.gates = {
                ...newState.gates,
                [gateName]: {
                  ...newState.gates[gateName],
                  status: "running",
                  startTime: eventTime,
                  filesTotal: event.files_total || 0,
                  filesProcessed: event.files_processed || 0,
                },
              };
              onGateStarted?.(gateName);
            } else {
              // Gate completed
              const updatedGate: GateStreamState = {
                ...newState.gates[gateName],
                status,
                endTime: eventTime,
                durationMs: event.duration_ms || 0,
                issuesFound: event.issues || 0,
                passed: status === "passed",
                filesProcessed: event.files_total || newState.gates[gateName].filesTotal,
                filesTotal: event.files_total || newState.gates[gateName].filesTotal,
              };
              newState.gates = {
                ...newState.gates,
                [gateName]: updatedGate,
              };

              // Find next pending gate
              const currentGateIndex = GATE_ORDER.indexOf(gateName);
              const nextGateName = GATE_ORDER[currentGateIndex + 1];
              if (nextGateName && newState.gates[nextGateName].status === "pending") {
                newState.currentGate = nextGateName;
                newState.gates = {
                  ...newState.gates,
                  [nextGateName]: {
                    ...newState.gates[nextGateName],
                    status: "running",
                    startTime: eventTime,
                  },
                };
                onGateStarted?.(nextGateName);
              } else {
                newState.currentGate = undefined;
              }

              onGateCompleted?.(updatedGate);
            }

            newState.overallProgress = calculateOverallProgress(newState.gates);
            break;
          }

          case "quality_issue": {
            const gateName = event.gate_name ? mapGateName(event.gate_name) : "syntax";
            const newIssue: StreamIssue = {
              id: `issue-${issueIdCounterRef.current++}`,
              gateName,
              severity: (event.severity as Severity) || "medium",
              file: event.file_path || "unknown",
              line: event.line,
              message: event.message || "Unknown issue",
              timestamp: eventTime,
            };
            newState.issues = [...newState.issues, newIssue];
            newState.gates = {
              ...newState.gates,
              [gateName]: {
                ...newState.gates[gateName],
                issuesFound: newState.gates[gateName].issuesFound + 1,
              },
            };
            onIssueFound?.(newIssue);
            break;
          }

          case "quality_completed":
            newState.pipelineEndTime = eventTime;
            newState.connectionState = "completed";
            newState.overallProgress = 100;
            newState.currentGate = undefined;
            break;

          case "error":
            newState.connectionState = "error";
            newState.error = event.message || "Unknown error";
            newState.currentGate = undefined;
            onError?.(new Error(event.message || "Unknown error"));
            break;
        }

        return newState;
      });
    },
    [onPipelineStarted, onPipelineCompleted, onGateStarted, onGateCompleted, onIssueFound, onError]
  );

  // Connect to SSE stream
  const connect = useCallback(
    async (sessionId?: string) => {
      const targetSessionId = sessionId || currentSessionIdRef.current;
      if (!targetSessionId) {
        setState((prev) => ({
          ...prev,
          connectionState: "error",
          error: "No session ID provided",
        }));
        return;
      }

      currentSessionIdRef.current = targetSessionId;
      const token = getAccessToken();
      if (!token) {
        setState((prev) => ({
          ...prev,
          connectionState: "error",
          error: "Not authenticated",
        }));
        return;
      }

      // Cleanup any existing connection
      cleanup();

      // Reset state for new connection
      setState({
        ...createInitialState(),
        connectionState: "connecting",
      });

      // Create abort controller
      abortControllerRef.current = new AbortController();

      try {
        const url = `${baseUrl}/codegen/sessions/${targetSessionId}/quality/stream`;
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

        setState((prev) => ({
          ...prev,
          connectionState: "connected",
        }));

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
                  console.error("Failed to parse quality event:", eventData);
                }
              }
            }
          }
        }

        // Stream ended normally
        setState((prev) => {
          if (prev.connectionState === "error") {
            return prev;
          }
          return {
            ...prev,
            connectionState: "completed",
            overallProgress: 100,
          };
        });

        // Invalidate quality cache
        queryClient.invalidateQueries({
          queryKey: qualityKeys.session(targetSessionId),
        });

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
        onError?.(new Error(message));

        // Auto-reconnect logic
        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(
            () => connect(targetSessionId),
            reconnectDelay * reconnectAttemptsRef.current
          );
        }
      }
    },
    [
      baseUrl,
      cleanup,
      processEvent,
      onError,
      autoReconnect,
      maxReconnectAttempts,
      reconnectDelay,
      queryClient,
    ]
  );

  // Disconnect from stream
  const disconnect = useCallback(() => {
    cleanup();
    setState((prev) => ({
      ...prev,
      connectionState: "disconnected",
    }));
  }, [cleanup]);

  // Reset state
  const reset = useCallback(() => {
    cleanup();
    issueIdCounterRef.current = 0;
    reconnectAttemptsRef.current = 0;
    setState(createInitialState());
  }, [cleanup]);

  // Build gate-specific details from streaming state
  const buildGateDetails = useCallback(
    (gateName: GateName, gate: GateStreamState, issues: StreamIssue[]): GateResult["details"] => {
      const gateIssues = issues.filter((i) => i.gateName === gateName);
      const passed = gate.passed ?? gate.status === "passed";

      switch (gateName) {
        case "syntax":
          return {
            passed,
            filesChecked: gate.filesTotal || 0,
            filesPassed: passed ? (gate.filesTotal || 0) : 0,
            issues: gateIssues.map((issue) => ({
              file: issue.file,
              line: issue.line || 0,
              column: 0,
              message: issue.message,
              vietnameseMessage: issue.message,
            })),
          };
        case "security": {
          const criticalCount = gateIssues.filter((i) => i.severity === "critical").length;
          const highCount = gateIssues.filter((i) => i.severity === "high").length;
          const mediumCount = gateIssues.filter((i) => i.severity === "medium").length;
          const lowCount = gateIssues.filter((i) => i.severity === "low").length;
          return {
            passed,
            criticalCount,
            highCount,
            mediumCount,
            lowCount,
            issues: gateIssues.map((issue) => ({
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
            issues: gateIssues.map((issue) => ({
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
            testsRun: gate.issuesFound,
            testsPassed: passed ? gate.issuesFound : 0,
            testsFailed: passed ? 0 : gate.issuesFound,
            results: gateIssues.map((issue) => ({
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

  // Compute pipeline result from current state
  const computePipelineResult = useCallback((): PipelineResult | null => {
    if (state.connectionState !== "completed") {
      return null;
    }

    const gates: GateResult[] = GATE_ORDER.map((gateName) => {
      const gate = state.gates[gateName];
      return {
        gateName,
        passed: gate.passed ?? gate.status === "passed",
        status: gate.status,
        durationMs: gate.durationMs ?? 0,
        details: buildGateDetails(gateName, gate, state.issues),
      };
    });

    const gatesPassed = gates.filter((g) => g.status === "passed").length;
    const gatesFailed = gates.filter((g) => g.status === "failed").length;
    const totalDurationMs =
      (state.pipelineEndTime || Date.now()) - (state.pipelineStartTime || Date.now());

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

  // Get pipeline result
  const getPipelineResult = useCallback((): PipelineResult | null => {
    return computePipelineResult();
  }, [computePipelineResult]);

  // Get issues by gate
  const getIssuesByGate = useCallback(
    (gateName: GateName): StreamIssue[] => {
      return state.issues.filter((issue) => issue.gateName === gateName);
    },
    [state.issues]
  );

  // Get issues by file
  const getIssuesByFile = useCallback(
    (file: string): StreamIssue[] => {
      return state.issues.filter((issue) => issue.file === file);
    },
    [state.issues]
  );

  // Get critical issues count
  const getCriticalIssuesCount = useCallback((): number => {
    return state.issues.filter((issue) => issue.severity === "critical").length;
  }, [state.issues]);

  // Trigger onComplete when pipeline completes
  useEffect(() => {
    if (state.connectionState === "completed" && onPipelineCompleted) {
      const result = computePipelineResult();
      if (result) {
        onPipelineCompleted(result);
      }
    }
  }, [state.connectionState, computePipelineResult, onPipelineCompleted]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect && initialSessionId) {
      connect(initialSessionId);
    }

    return () => {
      cleanup();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Computed isStreaming
  const isStreaming = useMemo(
    () =>
      state.connectionState === "connected" ||
      state.connectionState === "connecting",
    [state.connectionState]
  );

  return {
    state,
    connect,
    disconnect,
    reset,
    isStreaming,
    getPipelineResult,
    getIssuesByGate,
    getIssuesByFile,
    getCriticalIssuesCount,
  };
}

export default useQualityStreamBackend;
