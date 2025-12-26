/**
 * =========================================================================
 * QualityStreamProvider - Context Provider for Quality Streaming
 * SDLC Orchestrator - Sprint 55 Day 4 (Updated Sprint 56 Day 2)
 *
 * Version: 2.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Backend Integration
 *
 * Purpose:
 * - Provide quality streaming context to child components
 * - Manage SSE connection lifecycle with backend API
 * - Share streaming state across components
 * - Handle connection errors and notifications
 * - Support authenticated SSE connections
 *
 * References:
 * - docs/02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md
 * - backend/app/schemas/streaming.py
 * =========================================================================
 */

import React, {
  createContext,
  useContext,
  useCallback,
  useMemo,
  ReactNode,
} from "react";
import {
  useQualityStreamBackend,
  type QualityStreamState,
  type StreamConnectionState,
  type StreamIssue,
  type GateStreamState,
} from "@/hooks/useQualityStreamBackend";
import type { GateName, PipelineResult } from "@/types/quality";

// ============================================================================
// Types
// ============================================================================

export interface QualityStreamContextValue {
  /** Current stream state */
  state: QualityStreamState;
  /** Connection state shortcut */
  connectionState: StreamConnectionState;
  /** Whether currently streaming */
  isStreaming: boolean;
  /** Whether pipeline is complete */
  isComplete: boolean;
  /** Current active gate */
  currentGate?: GateName;
  /** Overall progress (0-100) */
  progress: number;
  /** All streamed issues */
  issues: StreamIssue[];
  /** Gate states */
  gates: Record<GateName, GateStreamState>;
  /** Connect to stream */
  connect: () => void;
  /** Disconnect from stream */
  disconnect: () => void;
  /** Reset state */
  reset: () => void;
  /** Get computed pipeline result */
  getPipelineResult: () => PipelineResult | null;
  /** Get issues by gate */
  getIssuesByGate: (gateName: GateName) => StreamIssue[];
  /** Get issues by file */
  getIssuesByFile: (file: string) => StreamIssue[];
  /** Get critical issues count */
  getCriticalIssuesCount: () => number;
}

export interface QualityStreamProviderProps {
  /** Base API URL (optional, uses VITE_API_URL if not specified) */
  url?: string;
  /** Session ID to subscribe to */
  sessionId: string;
  /** Auto-connect on mount */
  autoConnect?: boolean;
  /** Auto-reconnect on disconnect */
  autoReconnect?: boolean;
  /** Event handlers (optional) */
  onPipelineStarted?: () => void;
  onPipelineCompleted?: (result: PipelineResult) => void;
  onGateStarted?: (gateName: GateName) => void;
  onGateCompleted?: (gate: GateStreamState) => void;
  onIssueFound?: (issue: StreamIssue) => void;
  onError?: (error: Error) => void;
  /** Children */
  children: ReactNode;
}

// ============================================================================
// Context
// ============================================================================

const QualityStreamContext = createContext<QualityStreamContextValue | null>(
  null
);

// ============================================================================
// Provider Component
// ============================================================================

export const QualityStreamProvider: React.FC<QualityStreamProviderProps> = ({
  url,
  sessionId,
  autoConnect = false,
  autoReconnect = true,
  onPipelineStarted,
  onPipelineCompleted,
  onGateStarted,
  onGateCompleted,
  onIssueFound,
  onError,
  children,
}) => {
  const {
    state,
    connect: hookConnect,
    disconnect,
    reset,
    isStreaming,
    getPipelineResult,
    getIssuesByGate,
    getIssuesByFile,
    getCriticalIssuesCount,
  } = useQualityStreamBackend({
    baseUrl: url,
    sessionId,
    autoConnect,
    autoReconnect,
    onPipelineStarted,
    onPipelineCompleted,
    onGateStarted,
    onGateCompleted,
    onIssueFound,
    onError,
  });

  // Wrapper to allow connect without sessionId (uses the one from props)
  const connect = useCallback(() => {
    hookConnect(sessionId);
  }, [hookConnect, sessionId]);

  // Context value
  const value = useMemo<QualityStreamContextValue>(
    () => ({
      state,
      connectionState: state.connectionState,
      isStreaming,
      isComplete: state.connectionState === "completed",
      currentGate: state.currentGate,
      progress: state.overallProgress,
      issues: state.issues,
      gates: state.gates,
      connect,
      disconnect,
      reset,
      getPipelineResult,
      getIssuesByGate,
      getIssuesByFile,
      getCriticalIssuesCount,
    }),
    [
      state,
      isStreaming,
      connect,
      disconnect,
      reset,
      getPipelineResult,
      getIssuesByGate,
      getIssuesByFile,
      getCriticalIssuesCount,
    ]
  );

  return (
    <QualityStreamContext.Provider value={value}>
      {children}
    </QualityStreamContext.Provider>
  );
};

// ============================================================================
// Custom Hook
// ============================================================================

export function useQualityStreamContext(): QualityStreamContextValue {
  const context = useContext(QualityStreamContext);

  if (!context) {
    throw new Error(
      "useQualityStreamContext must be used within a QualityStreamProvider"
    );
  }

  return context;
}

// ============================================================================
// HOC for Components that Need Stream Context
// ============================================================================

export function withQualityStream<P extends object>(
  Component: React.ComponentType<P & { streamContext: QualityStreamContextValue }>
): React.FC<P & Partial<QualityStreamProviderProps>> {
  const WrappedComponent: React.FC<P & Partial<QualityStreamProviderProps>> = (
    props
  ) => {
    const {
      url,
      sessionId,
      autoConnect,
      autoReconnect,
      onPipelineStarted,
      onPipelineCompleted,
      onError,
      ...componentProps
    } = props;

    // If url and sessionId are provided, wrap with provider
    if (url && sessionId) {
      return (
        <QualityStreamProvider
          url={url}
          sessionId={sessionId}
          autoConnect={autoConnect}
          autoReconnect={autoReconnect}
          onPipelineStarted={onPipelineStarted}
          onPipelineCompleted={onPipelineCompleted}
          onError={onError}
        >
          <ComponentWithContext {...(componentProps as P)} />
        </QualityStreamProvider>
      );
    }

    // Otherwise, use existing context
    return <ComponentWithContext {...(componentProps as P)} />;
  };

  const ComponentWithContext: React.FC<P> = (props) => {
    const streamContext = useQualityStreamContext();
    return <Component {...props} streamContext={streamContext} />;
  };

  WrappedComponent.displayName = `withQualityStream(${
    Component.displayName || Component.name || "Component"
  })`;

  return WrappedComponent;
}

export default QualityStreamProvider;
