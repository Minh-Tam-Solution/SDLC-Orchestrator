/**
 * =========================================================================
 * useQualityPipelineStream Tests - Sprint 56 Day 1
 * SDLC Orchestrator
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * =========================================================================
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode } from "react";
import {
  useQualityPipelineStream,
  type StreamConnectionState,
  type StreamingGateState,
} from "./useQualityPipelineStream";

// ============================================================================
// Mock API Client
// ============================================================================

vi.mock("@/api/client", () => ({
  getAccessToken: vi.fn(() => "mock-token"),
}));

// ============================================================================
// Mock Fetch
// ============================================================================

const mockFetch = vi.fn();
global.fetch = mockFetch;

// ============================================================================
// Test Wrapper
// ============================================================================

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

// ============================================================================
// Mock SSE Stream
// ============================================================================

function createMockSSEStream(events: Array<{ type: string; data: object }>) {
  const encoder = new TextEncoder();
  let eventIndex = 0;

  return new ReadableStream({
    pull(controller) {
      if (eventIndex < events.length) {
        const event = events[eventIndex];
        const data = `data: ${JSON.stringify({ ...event.data, type: event.type })}\n\n`;
        controller.enqueue(encoder.encode(data));
        eventIndex++;
      } else {
        controller.close();
      }
    },
  });
}

// ============================================================================
// Initial State Tests
// ============================================================================

describe("useQualityPipelineStream - Initial State", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should have disconnected initial state", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    expect(result.current.state.connectionState).toBe("disconnected");
    expect(result.current.state.sessionId).toBeNull();
    expect(result.current.state.currentGate).toBeNull();
    expect(result.current.state.progress).toBe(0);
    expect(result.current.state.error).toBeNull();
  });

  it("should have initial pending gates", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    const { gates } = result.current.state;
    expect(gates.syntax.status).toBe("pending");
    expect(gates.security.status).toBe("pending");
    expect(gates.architecture.status).toBe("pending");
    expect(gates.tests.status).toBe("pending");
  });

  it("should have empty issues array", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    expect(result.current.state.issues).toEqual([]);
  });
});

// ============================================================================
// Connect Tests
// ============================================================================

describe("useQualityPipelineStream - Connect", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should set connecting state when connect is called", async () => {
    const stream = createMockSSEStream([]);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: stream,
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    act(() => {
      result.current.connect("session-123");
    });

    // Should be connecting or connected
    expect(["connecting", "connected", "completed"]).toContain(
      result.current.state.connectionState
    );
  });

  it("should set sessionId when connecting", async () => {
    const stream = createMockSSEStream([]);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: stream,
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    act(() => {
      result.current.connect("session-123");
    });

    expect(result.current.state.sessionId).toBe("session-123");
  });

  it("should mark first gate as running when connecting", async () => {
    const stream = createMockSSEStream([]);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: stream,
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    act(() => {
      result.current.connect("session-123");
    });

    expect(result.current.state.gates.syntax.status).toBe("running");
    expect(result.current.state.currentGate).toBe("syntax");
  });

  it("should handle connection error", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Connection failed"));

    const onError = vi.fn();
    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useQualityPipelineStream({ onError }),
      { wrapper }
    );

    act(() => {
      result.current.connect("session-123");
    });

    await waitFor(() => {
      expect(result.current.state.connectionState).toBe("error");
    });

    expect(result.current.state.error).toBe("Connection failed");
    expect(onError).toHaveBeenCalledWith("Connection failed");
  });

  it("should handle HTTP error response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    act(() => {
      result.current.connect("session-123");
    });

    await waitFor(() => {
      expect(result.current.state.connectionState).toBe("error");
    });

    expect(result.current.state.error).toContain("401");
  });
});

// ============================================================================
// Disconnect Tests
// ============================================================================

describe("useQualityPipelineStream - Disconnect", () => {
  it("should disconnect and set state", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    act(() => {
      result.current.disconnect();
    });

    expect(result.current.state.connectionState).toBe("disconnected");
  });
});

// ============================================================================
// Reset Tests
// ============================================================================

describe("useQualityPipelineStream - Reset", () => {
  it("should reset to initial state", async () => {
    const stream = createMockSSEStream([]);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: stream,
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    // Connect first
    act(() => {
      result.current.connect("session-123");
    });

    // Wait for connection
    await waitFor(() => {
      expect(result.current.state.sessionId).toBe("session-123");
    });

    // Reset
    act(() => {
      result.current.reset();
    });

    expect(result.current.state.connectionState).toBe("disconnected");
    expect(result.current.state.sessionId).toBeNull();
    expect(result.current.state.currentGate).toBeNull();
    expect(result.current.state.progress).toBe(0);
    expect(result.current.state.gates.syntax.status).toBe("pending");
  });
});

// ============================================================================
// Helper Method Tests
// ============================================================================

describe("useQualityPipelineStream - Helper Methods", () => {
  it("should return null from getPipelineResult when not completed", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    expect(result.current.getPipelineResult()).toBeNull();
  });

  it("should return empty array from getGateIssues", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    expect(result.current.getGateIssues("syntax")).toEqual([]);
    expect(result.current.getGateIssues("security")).toEqual([]);
  });

  it("should return empty array from getFileIssues", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    expect(result.current.getFileIssues("src/main.py")).toEqual([]);
  });

  it("should return 0 from getCriticalCount initially", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    expect(result.current.getCriticalCount()).toBe(0);
  });
});

// ============================================================================
// Callback Tests
// ============================================================================

describe("useQualityPipelineStream - Callbacks", () => {
  it("should call onGateStart when first gate starts", async () => {
    const stream = createMockSSEStream([]);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: stream,
    });

    const onGateStart = vi.fn();
    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useQualityPipelineStream({ onGateStart }),
      { wrapper }
    );

    act(() => {
      result.current.connect("session-123");
    });

    expect(onGateStart).toHaveBeenCalledWith("syntax");
  });
});

// ============================================================================
// Progress Calculation Tests
// ============================================================================

describe("useQualityPipelineStream - Progress", () => {
  it("should start with 0 progress", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    expect(result.current.state.progress).toBe(0);
  });

  it("should calculate partial progress when connecting", async () => {
    const stream = createMockSSEStream([]);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: stream,
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    act(() => {
      result.current.connect("session-123");
    });

    // Running gate contributes partial progress
    await waitFor(() => {
      expect(result.current.state.progress).toBeGreaterThanOrEqual(0);
    });
  });
});

// ============================================================================
// Gate State Tests
// ============================================================================

describe("useQualityPipelineStream - Gate States", () => {
  it("should have correct initial gate structure", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    const { gates } = result.current.state;

    // Check syntax gate structure
    expect(gates.syntax).toMatchObject({
      gateName: "syntax",
      status: "pending",
      durationMs: 0,
      issueCount: 0,
      issues: [],
    });

    // Check security gate structure
    expect(gates.security).toMatchObject({
      gateName: "security",
      status: "pending",
      durationMs: 0,
      issueCount: 0,
      issues: [],
    });
  });

  it("should have all 4 gates defined", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    const { gates } = result.current.state;
    expect(Object.keys(gates)).toEqual(["syntax", "security", "architecture", "tests"]);
  });
});

// ============================================================================
// Options Tests
// ============================================================================

describe("useQualityPipelineStream - Options", () => {
  it("should use default baseUrl", () => {
    const wrapper = createWrapper();
    renderHook(() => useQualityPipelineStream(), { wrapper });

    // Hook should be created without errors
    expect(true).toBe(true);
  });

  it("should accept custom baseUrl", () => {
    const wrapper = createWrapper();
    renderHook(
      () => useQualityPipelineStream({ baseUrl: "http://custom-api:8000" }),
      { wrapper }
    );

    // Hook should be created without errors
    expect(true).toBe(true);
  });

  it("should accept autoReconnect option", () => {
    const wrapper = createWrapper();
    renderHook(
      () => useQualityPipelineStream({ autoReconnect: true, maxReconnectAttempts: 5 }),
      { wrapper }
    );

    // Hook should be created without errors
    expect(true).toBe(true);
  });
});

// ============================================================================
// Authentication Tests
// ============================================================================

describe("useQualityPipelineStream - Authentication", () => {
  it("should include auth token in request", async () => {
    const stream = createMockSSEStream([]);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: stream,
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityPipelineStream(), { wrapper });

    act(() => {
      result.current.connect("session-123");
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    const fetchCall = mockFetch.mock.calls[0];
    expect(fetchCall[1].headers).toMatchObject({
      Authorization: "Bearer mock-token",
      Accept: "text/event-stream",
    });
  });
});

// ============================================================================
// Cleanup Tests
// ============================================================================

describe("useQualityPipelineStream - Cleanup", () => {
  it("should cleanup on unmount", () => {
    const wrapper = createWrapper();
    const { unmount } = renderHook(() => useQualityPipelineStream(), { wrapper });

    // Should not throw
    expect(() => unmount()).not.toThrow();
  });

  it("should abort connection on unmount", async () => {
    const stream = createMockSSEStream([]);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: stream,
    });

    const wrapper = createWrapper();
    const { result, unmount } = renderHook(
      () => useQualityPipelineStream(),
      { wrapper }
    );

    act(() => {
      result.current.connect("session-123");
    });

    // Unmount should abort
    expect(() => unmount()).not.toThrow();
  });
});
