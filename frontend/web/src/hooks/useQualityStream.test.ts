/**
 * =========================================================================
 * useQualityStream Hook Tests - Sprint 55 Day 4
 * SDLC Orchestrator
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * =========================================================================
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useQualityStream } from "./useQualityStream";
import type { QualityStreamState } from "./useQualityStream";

// ============================================================================
// Mock EventSource
// ============================================================================

class MockEventSource {
  static instances: MockEventSource[] = [];

  url: string;
  readyState: number = EventSource.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);

    // Simulate connection after a brief delay
    setTimeout(() => {
      this.readyState = EventSource.OPEN;
      if (this.onopen) {
        this.onopen(new Event("open"));
      }
    }, 10);
  }

  close() {
    this.readyState = EventSource.CLOSED;
  }

  // Helper to simulate sending events
  simulateMessage(data: object) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent("message", { data: JSON.stringify(data) }));
    }
  }

  // Helper to simulate error
  simulateError() {
    this.readyState = EventSource.CLOSED;
    if (this.onerror) {
      this.onerror(new Event("error"));
    }
  }

  static clearInstances() {
    MockEventSource.instances = [];
  }
}

// Replace global EventSource with mock
const originalEventSource = global.EventSource;

beforeEach(() => {
  MockEventSource.clearInstances();
  // @ts-expect-error - replacing EventSource for testing
  global.EventSource = MockEventSource;
});

afterEach(() => {
  global.EventSource = originalEventSource;
});

// ============================================================================
// Tests
// ============================================================================

describe("useQualityStream", () => {
  const defaultOptions = {
    url: "http://localhost:8000/api/quality/stream",
    sessionId: "test-session-123",
  };

  describe("Initial State", () => {
    it("should have disconnected state initially", () => {
      const { result } = renderHook(() => useQualityStream(defaultOptions));

      expect(result.current.state.connectionState).toBe("disconnected");
      expect(result.current.isStreaming).toBe(false);
    });

    it("should have all gates in pending state initially", () => {
      const { result } = renderHook(() => useQualityStream(defaultOptions));

      expect(result.current.state.gates.syntax.status).toBe("pending");
      expect(result.current.state.gates.security.status).toBe("pending");
      expect(result.current.state.gates.architecture.status).toBe("pending");
      expect(result.current.state.gates.tests.status).toBe("pending");
    });

    it("should have empty issues array initially", () => {
      const { result } = renderHook(() => useQualityStream(defaultOptions));

      expect(result.current.state.issues).toEqual([]);
    });

    it("should have zero progress initially", () => {
      const { result } = renderHook(() => useQualityStream(defaultOptions));

      expect(result.current.state.overallProgress).toBe(0);
    });
  });

  describe("Connection", () => {
    it("should connect when connect() is called", async () => {
      const { result } = renderHook(() => useQualityStream(defaultOptions));

      act(() => {
        result.current.connect();
      });

      expect(result.current.state.connectionState).toBe("connecting");

      await waitFor(() => {
        expect(result.current.state.connectionState).toBe("connected");
      });

      expect(result.current.isStreaming).toBe(true);
    });

    it("should auto-connect when autoConnect is true", async () => {
      const { result } = renderHook(() =>
        useQualityStream({ ...defaultOptions, autoConnect: true })
      );

      await waitFor(() => {
        expect(result.current.state.connectionState).toBe("connected");
      });
    });

    it("should disconnect when disconnect() is called", async () => {
      const { result } = renderHook(() => useQualityStream(defaultOptions));

      act(() => {
        result.current.connect();
      });

      await waitFor(() => {
        expect(result.current.state.connectionState).toBe("connected");
      });

      act(() => {
        result.current.disconnect();
      });

      expect(result.current.state.connectionState).toBe("disconnected");
      expect(result.current.isStreaming).toBe(false);
    });

    it("should include session ID in URL", () => {
      const { result } = renderHook(() => useQualityStream(defaultOptions));

      act(() => {
        result.current.connect();
      });

      const instance = MockEventSource.instances[0];
      expect(instance.url).toContain("session_id=test-session-123");
    });
  });

  describe("Event Handling", () => {
    it("should handle pipeline_started event", async () => {
      const onPipelineStarted = vi.fn();
      const { result } = renderHook(() =>
        useQualityStream({ ...defaultOptions, onPipelineStarted })
      );

      act(() => {
        result.current.connect();
      });

      await waitFor(() => {
        expect(result.current.state.connectionState).toBe("connected");
      });

      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "pipeline_started",
          timestamp: Date.now(),
          data: {},
        });
      });

      expect(onPipelineStarted).toHaveBeenCalled();
      expect(result.current.state.pipelineStartTime).toBeDefined();
    });

    it("should handle gate_started event", async () => {
      const onGateStarted = vi.fn();
      const { result } = renderHook(() =>
        useQualityStream({ ...defaultOptions, onGateStarted })
      );

      act(() => {
        result.current.connect();
      });

      await waitFor(() => {
        expect(result.current.state.connectionState).toBe("connected");
      });

      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "gate_started",
          gateName: "syntax",
          timestamp: Date.now(),
          data: { filesCount: 10 },
        });
      });

      expect(onGateStarted).toHaveBeenCalled();
      expect(result.current.state.gates.syntax.status).toBe("running");
      expect(result.current.state.gates.syntax.filesTotal).toBe(10);
      expect(result.current.state.currentGate).toBe("syntax");
    });

    it("should handle gate_progress event", async () => {
      const onGateProgress = vi.fn();
      const { result } = renderHook(() =>
        useQualityStream({ ...defaultOptions, onGateProgress })
      );

      act(() => {
        result.current.connect();
      });

      await waitFor(() => {
        expect(result.current.state.connectionState).toBe("connected");
      });

      // Start gate first
      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "gate_started",
          gateName: "syntax",
          timestamp: Date.now(),
          data: { filesCount: 10 },
        });
      });

      // Then progress
      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "gate_progress",
          gateName: "syntax",
          timestamp: Date.now(),
          data: { filesProcessed: 5, filesTotal: 10, issuesFound: 2 },
        });
      });

      expect(onGateProgress).toHaveBeenCalled();
      expect(result.current.state.gates.syntax.filesProcessed).toBe(5);
      expect(result.current.state.gates.syntax.issuesFound).toBe(2);
      expect(result.current.state.overallProgress).toBeGreaterThan(0);
    });

    it("should handle gate_completed event", async () => {
      const onGateCompleted = vi.fn();
      const { result } = renderHook(() =>
        useQualityStream({ ...defaultOptions, onGateCompleted })
      );

      act(() => {
        result.current.connect();
      });

      await waitFor(() => {
        expect(result.current.state.connectionState).toBe("connected");
      });

      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "gate_completed",
          gateName: "syntax",
          timestamp: Date.now(),
          data: { passed: true, durationMs: 1500, issuesCount: 0 },
        });
      });

      expect(onGateCompleted).toHaveBeenCalled();
      expect(result.current.state.gates.syntax.status).toBe("passed");
      expect(result.current.state.gates.syntax.durationMs).toBe(1500);
      expect(result.current.state.gates.syntax.passed).toBe(true);
    });

    it("should handle issue_found event", async () => {
      const onIssueFound = vi.fn();
      const { result } = renderHook(() =>
        useQualityStream({ ...defaultOptions, onIssueFound })
      );

      act(() => {
        result.current.connect();
      });

      await waitFor(() => {
        expect(result.current.state.connectionState).toBe("connected");
      });

      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "issue_found",
          gateName: "security",
          timestamp: Date.now(),
          data: {
            severity: "critical",
            file: "src/main.py",
            line: 42,
            message: "SQL injection vulnerability",
          },
        });
      });

      expect(onIssueFound).toHaveBeenCalled();
      expect(result.current.state.issues).toHaveLength(1);
      expect(result.current.state.issues[0].severity).toBe("critical");
      expect(result.current.state.issues[0].file).toBe("src/main.py");
    });

    it("should handle pipeline_completed event", async () => {
      const onPipelineCompleted = vi.fn();
      const { result } = renderHook(() =>
        useQualityStream({ ...defaultOptions, onPipelineCompleted })
      );

      act(() => {
        result.current.connect();
      });

      await waitFor(() => {
        expect(result.current.state.connectionState).toBe("connected");
      });

      // Start pipeline
      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "pipeline_started",
          timestamp: Date.now(),
          data: {},
        });
      });

      // Complete a gate
      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "gate_completed",
          gateName: "syntax",
          timestamp: Date.now(),
          data: { passed: true, durationMs: 1000, issuesCount: 0 },
        });
      });

      // Complete pipeline
      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "pipeline_completed",
          timestamp: Date.now(),
          data: {},
        });
      });

      expect(onPipelineCompleted).toHaveBeenCalled();
      expect(result.current.state.connectionState).toBe("completed");
      expect(result.current.state.overallProgress).toBe(100);
    });
  });

  describe("Progress Calculation", () => {
    it("should calculate progress for single gate running", async () => {
      const { result } = renderHook(() => useQualityStream(defaultOptions));

      act(() => {
        result.current.connect();
      });

      await waitFor(() => {
        expect(result.current.state.connectionState).toBe("connected");
      });

      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "gate_started",
          gateName: "syntax",
          timestamp: Date.now(),
          data: { filesCount: 10 },
        });
      });

      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "gate_progress",
          gateName: "syntax",
          timestamp: Date.now(),
          data: { filesProcessed: 5, filesTotal: 10, issuesFound: 0 },
        });
      });

      // 50% of first gate (25% weight) = 12.5% ≈ 13%
      expect(result.current.state.overallProgress).toBeCloseTo(13, 0);
    });

    it("should calculate progress for completed gates", async () => {
      const { result } = renderHook(() => useQualityStream(defaultOptions));

      act(() => {
        result.current.connect();
      });

      await waitFor(() => {
        expect(result.current.state.connectionState).toBe("connected");
      });

      // Complete first gate
      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "gate_completed",
          gateName: "syntax",
          timestamp: Date.now(),
          data: { passed: true, durationMs: 1000, issuesCount: 0 },
        });
      });

      expect(result.current.state.overallProgress).toBe(25);

      // Complete second gate
      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "gate_completed",
          gateName: "security",
          timestamp: Date.now(),
          data: { passed: true, durationMs: 1000, issuesCount: 0 },
        });
      });

      expect(result.current.state.overallProgress).toBe(50);
    });
  });

  describe("Reset", () => {
    it("should reset state to initial values", async () => {
      const { result } = renderHook(() => useQualityStream(defaultOptions));

      act(() => {
        result.current.connect();
      });

      await waitFor(() => {
        expect(result.current.state.connectionState).toBe("connected");
      });

      // Add some issues
      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "issue_found",
          gateName: "syntax",
          timestamp: Date.now(),
          data: { severity: "high", file: "test.py", message: "Error" },
        });
      });

      expect(result.current.state.issues).toHaveLength(1);

      // Reset
      act(() => {
        result.current.reset();
      });

      expect(result.current.state.connectionState).toBe("disconnected");
      expect(result.current.state.issues).toHaveLength(0);
      expect(result.current.state.overallProgress).toBe(0);
    });
  });

  describe("getPipelineResult", () => {
    it("should return null when pipeline not started", () => {
      const { result } = renderHook(() => useQualityStream(defaultOptions));

      expect(result.current.getPipelineResult()).toBeNull();
    });

    it("should return pipeline result after completion", async () => {
      const { result } = renderHook(() => useQualityStream(defaultOptions));

      act(() => {
        result.current.connect();
      });

      await waitFor(() => {
        expect(result.current.state.connectionState).toBe("connected");
      });

      // Start pipeline
      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "pipeline_started",
          timestamp: Date.now(),
          data: {},
        });
      });

      // Complete gates
      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "gate_completed",
          gateName: "syntax",
          timestamp: Date.now(),
          data: { passed: true, durationMs: 1000, issuesCount: 0 },
        });
      });

      act(() => {
        MockEventSource.instances[0].simulateMessage({
          type: "gate_completed",
          gateName: "security",
          timestamp: Date.now(),
          data: { passed: false, durationMs: 2000, issuesCount: 3 },
        });
      });

      const pipelineResult = result.current.getPipelineResult();

      expect(pipelineResult).not.toBeNull();
      expect(pipelineResult?.passed).toBe(false); // One gate failed
      expect(pipelineResult?.summary.gatesPassed).toBe(1);
      expect(pipelineResult?.summary.gatesFailed).toBe(1);
    });
  });

  describe("Error Handling", () => {
    it("should handle connection errors", async () => {
      const onError = vi.fn();
      const { result } = renderHook(() =>
        useQualityStream({
          ...defaultOptions,
          autoReconnect: false,
          onError,
        })
      );

      act(() => {
        result.current.connect();
      });

      await waitFor(() => {
        expect(result.current.state.connectionState).toBe("connected");
      });

      act(() => {
        MockEventSource.instances[0].simulateError();
      });

      expect(result.current.state.connectionState).toBe("error");
    });
  });
});
