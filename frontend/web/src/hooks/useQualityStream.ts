/**
 * =========================================================================
 * useQualityStream - Custom Hook for Quality Pipeline SSE Events
 * SDLC Orchestrator - Sprint 55 Day 4
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 *
 * Purpose:
 * - Subscribe to SSE quality pipeline events
 * - Manage streaming connection state
 * - Aggregate real-time quality updates
 * - Handle connection errors and reconnection
 *
 * References:
 * - docs/02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md
 * =========================================================================
 */

import { useState, useEffect, useCallback, useRef } from "react";
import type {
  GateName,
  GateStatus,
  QualityEventType,
  GateStartedEvent,
  GateProgressEvent,
  GateCompletedEvent,
  IssueFoundEvent,
  Severity,
  PipelineResult,
  GateResult,
} from "@/types/quality";

// ============================================================================
// Types
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

export interface QualityStreamEvent {
  type: QualityEventType;
  gateName?: GateName;
  timestamp: number;
  data: Record<string, unknown>;
}

export interface UseQualityStreamOptions {
  /** SSE endpoint URL */
  url: string;
  /** Session ID to subscribe to */
  sessionId: string;
  /** Auto-connect on mount */
  autoConnect?: boolean;
  /** Reconnect on disconnect */
  autoReconnect?: boolean;
  /** Reconnect delay in ms */
  reconnectDelay?: number;
  /** Max reconnect attempts */
  maxReconnectAttempts?: number;
  /** Event handlers */
  onGateStarted?: (event: GateStartedEvent) => void;
  onGateProgress?: (event: GateProgressEvent) => void;
  onGateCompleted?: (event: GateCompletedEvent) => void;
  onIssueFound?: (event: IssueFoundEvent) => void;
  onPipelineStarted?: () => void;
  onPipelineCompleted?: (result: PipelineResult) => void;
  onError?: (error: Error) => void;
}

export interface UseQualityStreamReturn {
  /** Current stream state */
  state: QualityStreamState;
  /** Connect to SSE stream */
  connect: () => void;
  /** Disconnect from SSE stream */
  disconnect: () => void;
  /** Reset state to initial */
  reset: () => void;
  /** Check if currently streaming */
  isStreaming: boolean;
  /** Get computed pipeline result */
  getPipelineResult: () => PipelineResult | null;
}

// ============================================================================
// Initial State
// ============================================================================

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
// Progress Calculation
// ============================================================================

const calculateOverallProgress = (
  gates: Record<GateName, GateStreamState>
): number => {
  const gateOrder: GateName[] = ["syntax", "security", "architecture", "tests"];
  let totalProgress = 0;

  for (const gateName of gateOrder) {
    const gate = gates[gateName];
    const gateWeight = 25; // Each gate is 25% of total

    if (gate.status === "passed" || gate.status === "failed") {
      totalProgress += gateWeight;
    } else if (gate.status === "running") {
      const gateProgress =
        gate.filesTotal > 0
          ? (gate.filesProcessed / gate.filesTotal) * gateWeight
          : 0;
      totalProgress += gateProgress;
    }
  }

  return Math.round(totalProgress);
};

// ============================================================================
// Custom Hook
// ============================================================================

export function useQualityStream(
  options: UseQualityStreamOptions
): UseQualityStreamReturn {
  const {
    url,
    sessionId,
    autoConnect = false,
    autoReconnect = true,
    reconnectDelay = 3000,
    maxReconnectAttempts = 5,
    onGateStarted,
    onGateProgress,
    onGateCompleted,
    onIssueFound,
    onPipelineStarted,
    onPipelineCompleted,
    onError,
  } = options;

  const [state, setState] = useState<QualityStreamState>(createInitialState());
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const issueIdCounterRef = useRef(0);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Handle SSE events
  const handleEvent = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as QualityStreamEvent;

        setState((prev) => {
          const newState = { ...prev };

          switch (data.type) {
            case "pipeline_started":
              newState.pipelineStartTime = data.timestamp;
              newState.currentGate = undefined;
              onPipelineStarted?.();
              break;

            case "gate_started": {
              const gateName = data.gateName as GateName;
              newState.currentGate = gateName;
              newState.gates = {
                ...newState.gates,
                [gateName]: {
                  ...newState.gates[gateName],
                  status: "running",
                  startTime: data.timestamp,
                  filesTotal: (data.data as GateStartedEvent["data"]).filesCount,
                },
              };
              onGateStarted?.(data as GateStartedEvent);
              break;
            }

            case "gate_progress": {
              const gateName = data.gateName as GateName;
              const progressData = data.data as GateProgressEvent["data"];
              newState.gates = {
                ...newState.gates,
                [gateName]: {
                  ...newState.gates[gateName],
                  filesProcessed: progressData.filesProcessed,
                  filesTotal: progressData.filesTotal,
                  issuesFound: progressData.issuesFound,
                },
              };
              newState.overallProgress = calculateOverallProgress(newState.gates);
              onGateProgress?.(data as GateProgressEvent);
              break;
            }

            case "gate_completed": {
              const gateName = data.gateName as GateName;
              const completedData = data.data as GateCompletedEvent["data"];
              newState.gates = {
                ...newState.gates,
                [gateName]: {
                  ...newState.gates[gateName],
                  status: completedData.passed ? "passed" : "failed",
                  endTime: data.timestamp,
                  durationMs: completedData.durationMs,
                  passed: completedData.passed,
                  issuesFound: completedData.issuesCount,
                },
              };
              newState.overallProgress = calculateOverallProgress(newState.gates);
              onGateCompleted?.(data as GateCompletedEvent);
              break;
            }

            case "issue_found": {
              const gateName = data.gateName as GateName;
              const issueData = data.data as IssueFoundEvent["data"];
              const newIssue: StreamIssue = {
                id: `issue-${issueIdCounterRef.current++}`,
                gateName,
                severity: issueData.severity,
                file: issueData.file,
                line: issueData.line,
                message: issueData.message,
                timestamp: data.timestamp,
              };
              newState.issues = [...newState.issues, newIssue];
              onIssueFound?.(data as IssueFoundEvent);
              break;
            }

            case "pipeline_completed": {
              newState.pipelineEndTime = data.timestamp;
              newState.connectionState = "completed";
              newState.overallProgress = 100;
              newState.currentGate = undefined;

              // Compute final result
              const result = computePipelineResult(newState);
              if (result) {
                onPipelineCompleted?.(result);
              }
              break;
            }
          }

          return newState;
        });
      } catch (err) {
        console.error("Failed to parse SSE event:", err);
      }
    },
    [
      onGateStarted,
      onGateProgress,
      onGateCompleted,
      onIssueFound,
      onPipelineStarted,
      onPipelineCompleted,
    ]
  );

  // Connect to SSE
  const connect = useCallback(() => {
    cleanup();

    setState((prev) => ({
      ...prev,
      connectionState: "connecting",
      error: undefined,
    }));

    try {
      const sseUrl = `${url}?session_id=${sessionId}`;
      const eventSource = new EventSource(sseUrl);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        reconnectAttemptsRef.current = 0;
        setState((prev) => ({
          ...prev,
          connectionState: "connected",
        }));
      };

      eventSource.onmessage = handleEvent;

      eventSource.onerror = (err) => {
        console.error("SSE error:", err);

        if (eventSource.readyState === EventSource.CLOSED) {
          setState((prev) => ({
            ...prev,
            connectionState: "error",
            error: "Connection closed",
          }));

          // Attempt reconnection
          if (
            autoReconnect &&
            reconnectAttemptsRef.current < maxReconnectAttempts
          ) {
            reconnectAttemptsRef.current++;
            reconnectTimeoutRef.current = setTimeout(() => {
              connect();
            }, reconnectDelay);
          } else {
            const error = new Error(
              `Failed to connect after ${maxReconnectAttempts} attempts`
            );
            onError?.(error);
          }
        }
      };
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setState((prev) => ({
        ...prev,
        connectionState: "error",
        error: error.message,
      }));
      onError?.(error);
    }
  }, [
    url,
    sessionId,
    autoReconnect,
    reconnectDelay,
    maxReconnectAttempts,
    cleanup,
    handleEvent,
    onError,
  ]);

  // Disconnect from SSE
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
    setState(createInitialState());
  }, [cleanup]);

  // Compute pipeline result from current state
  const computePipelineResult = (
    streamState: QualityStreamState
  ): PipelineResult | null => {
    if (!streamState.pipelineStartTime) {
      return null;
    }

    const gateOrder: GateName[] = [
      "syntax",
      "security",
      "architecture",
      "tests",
    ];
    const gates: GateResult[] = [];
    let gatesPassed = 0;
    let gatesFailed = 0;

    for (const gateName of gateOrder) {
      const gate = streamState.gates[gateName];
      if (gate.status === "passed" || gate.status === "failed") {
        if (gate.passed) {
          gatesPassed++;
        } else {
          gatesFailed++;
        }

        gates.push({
          gateName,
          passed: gate.passed ?? false,
          status: gate.status,
          durationMs: gate.durationMs ?? 0,
          details: { error: "Details not available in streaming mode" },
        });
      }
    }

    const totalDurationMs =
      (streamState.pipelineEndTime ?? Date.now()) -
      streamState.pipelineStartTime;

    return {
      passed: gatesFailed === 0 && gatesPassed > 0,
      totalDurationMs,
      gates,
      summary: {
        gatesRun: gatesPassed + gatesFailed,
        gatesPassed,
        gatesFailed,
      },
      vietnameseSummary: `${gatesPassed}/${gatesPassed + gatesFailed} cổng đã đạt`,
    };
  };

  // Get pipeline result
  const getPipelineResult = useCallback((): PipelineResult | null => {
    return computePipelineResult(state);
  }, [state]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      cleanup();
    };
  }, [autoConnect, connect, cleanup]);

  return {
    state,
    connect,
    disconnect,
    reset,
    isStreaming:
      state.connectionState === "connected" ||
      state.connectionState === "connecting",
    getPipelineResult,
  };
}

export default useQualityStream;
