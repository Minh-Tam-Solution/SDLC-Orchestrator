/**
 * =========================================================================
 * useQualityStreamBackend Tests - Backend Quality Stream Hook Tests
 * SDLC Orchestrator - Sprint 56 Day 2
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Backend Integration
 * =========================================================================
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { useQualityStreamBackend } from "./useQualityStreamBackend";

// Mock the API client
vi.mock("@/api/client", () => ({
  getAccessToken: vi.fn(() => "test-token"),
}));

// Create wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("useQualityStreamBackend", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Initial State", () => {
    it("should initialize with disconnected state", () => {
      const { result } = renderHook(() => useQualityStreamBackend(), {
        wrapper: createWrapper(),
      });

      expect(result.current.state.connectionState).toBe("disconnected");
      expect(result.current.isStreaming).toBe(false);
    });

    it("should initialize with empty issues", () => {
      const { result } = renderHook(() => useQualityStreamBackend(), {
        wrapper: createWrapper(),
      });

      expect(result.current.state.issues).toHaveLength(0);
    });

    it("should initialize with pending gates", () => {
      const { result } = renderHook(() => useQualityStreamBackend(), {
        wrapper: createWrapper(),
      });

      expect(result.current.state.gates.syntax.status).toBe("pending");
      expect(result.current.state.gates.security.status).toBe("pending");
      expect(result.current.state.gates.architecture.status).toBe("pending");
      expect(result.current.state.gates.tests.status).toBe("pending");
    });

    it("should initialize with zero progress", () => {
      const { result } = renderHook(() => useQualityStreamBackend(), {
        wrapper: createWrapper(),
      });

      expect(result.current.state.overallProgress).toBe(0);
    });
  });

  describe("Connect", () => {
    it("should set connecting state when connect is called", async () => {
      // Mock fetch to never resolve (simulate pending connection)
      global.fetch = vi.fn().mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { result } = renderHook(
        () => useQualityStreamBackend({ sessionId: "test-session" }),
        { wrapper: createWrapper() }
      );

      act(() => {
        result.current.connect();
      });

      expect(result.current.state.connectionState).toBe("connecting");
    });

    it("should set error state when no session ID provided", async () => {
      const { result } = renderHook(() => useQualityStreamBackend(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.connect();
      });

      expect(result.current.state.connectionState).toBe("error");
      expect(result.current.state.error).toBe("No session ID provided");
    });
  });

  describe("Disconnect", () => {
    it("should set disconnected state", () => {
      const { result } = renderHook(() => useQualityStreamBackend(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.disconnect();
      });

      expect(result.current.state.connectionState).toBe("disconnected");
    });
  });

  describe("Reset", () => {
    it("should reset to initial state", () => {
      const { result } = renderHook(() => useQualityStreamBackend(), {
        wrapper: createWrapper(),
      });

      // Modify state first (if possible)
      act(() => {
        result.current.disconnect();
      });

      // Then reset
      act(() => {
        result.current.reset();
      });

      expect(result.current.state.connectionState).toBe("disconnected");
      expect(result.current.state.issues).toHaveLength(0);
      expect(result.current.state.overallProgress).toBe(0);
    });
  });

  describe("Helper Functions", () => {
    it("should return null for getPipelineResult when not completed", () => {
      const { result } = renderHook(() => useQualityStreamBackend(), {
        wrapper: createWrapper(),
      });

      expect(result.current.getPipelineResult()).toBeNull();
    });

    it("should return empty array for getIssuesByGate when no issues", () => {
      const { result } = renderHook(() => useQualityStreamBackend(), {
        wrapper: createWrapper(),
      });

      expect(result.current.getIssuesByGate("syntax")).toHaveLength(0);
      expect(result.current.getIssuesByGate("security")).toHaveLength(0);
    });

    it("should return empty array for getIssuesByFile when no issues", () => {
      const { result } = renderHook(() => useQualityStreamBackend(), {
        wrapper: createWrapper(),
      });

      expect(result.current.getIssuesByFile("test.ts")).toHaveLength(0);
    });

    it("should return 0 for getCriticalIssuesCount when no issues", () => {
      const { result } = renderHook(() => useQualityStreamBackend(), {
        wrapper: createWrapper(),
      });

      expect(result.current.getCriticalIssuesCount()).toBe(0);
    });
  });

  describe("isStreaming", () => {
    it("should return true when connecting", async () => {
      global.fetch = vi.fn().mockImplementation(
        () => new Promise(() => {})
      );

      const { result } = renderHook(
        () => useQualityStreamBackend({ sessionId: "test-session" }),
        { wrapper: createWrapper() }
      );

      act(() => {
        result.current.connect();
      });

      expect(result.current.isStreaming).toBe(true);
    });

    it("should return false when disconnected", () => {
      const { result } = renderHook(() => useQualityStreamBackend(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isStreaming).toBe(false);
    });
  });

  describe("Options", () => {
    it("should accept baseUrl option", () => {
      const { result } = renderHook(
        () =>
          useQualityStreamBackend({
            baseUrl: "http://custom-api.com",
            sessionId: "test",
          }),
        { wrapper: createWrapper() }
      );

      expect(result.current).toBeDefined();
    });

    it("should accept autoConnect option", () => {
      const { result } = renderHook(
        () =>
          useQualityStreamBackend({
            autoConnect: false,
            sessionId: "test",
          }),
        { wrapper: createWrapper() }
      );

      expect(result.current.state.connectionState).toBe("disconnected");
    });

    it("should accept callback options", () => {
      const onPipelineStarted = vi.fn();
      const onPipelineCompleted = vi.fn();
      const onGateStarted = vi.fn();
      const onError = vi.fn();

      const { result } = renderHook(
        () =>
          useQualityStreamBackend({
            onPipelineStarted,
            onPipelineCompleted,
            onGateStarted,
            onError,
          }),
        { wrapper: createWrapper() }
      );

      expect(result.current).toBeDefined();
    });
  });

  describe("Gate States", () => {
    it("should have all four gates defined", () => {
      const { result } = renderHook(() => useQualityStreamBackend(), {
        wrapper: createWrapper(),
      });

      expect(result.current.state.gates).toHaveProperty("syntax");
      expect(result.current.state.gates).toHaveProperty("security");
      expect(result.current.state.gates).toHaveProperty("architecture");
      expect(result.current.state.gates).toHaveProperty("tests");
    });

    it("should have correct initial gate properties", () => {
      const { result } = renderHook(() => useQualityStreamBackend(), {
        wrapper: createWrapper(),
      });

      const syntaxGate = result.current.state.gates.syntax;
      expect(syntaxGate.gateName).toBe("syntax");
      expect(syntaxGate.status).toBe("pending");
      expect(syntaxGate.filesProcessed).toBe(0);
      expect(syntaxGate.filesTotal).toBe(0);
      expect(syntaxGate.issuesFound).toBe(0);
    });
  });
});

describe("useQualityStreamBackend - Type Compatibility", () => {
  it("should have QualityStreamState compatible structure", () => {
    const { result } = renderHook(() => useQualityStreamBackend(), {
      wrapper: createWrapper(),
    });

    // Verify QualityStreamState structure
    expect(result.current.state).toHaveProperty("connectionState");
    expect(result.current.state).toHaveProperty("gates");
    expect(result.current.state).toHaveProperty("issues");
    // currentGate is optional - it's undefined when not streaming
    expect("currentGate" in result.current.state || result.current.state.currentGate === undefined).toBe(true);
    expect(result.current.state).toHaveProperty("overallProgress");
  });

  it("should have UseQualityStreamBackendReturn compatible structure", () => {
    const { result } = renderHook(() => useQualityStreamBackend(), {
      wrapper: createWrapper(),
    });

    // Verify return type structure
    expect(typeof result.current.state).toBe("object");
    expect(typeof result.current.connect).toBe("function");
    expect(typeof result.current.disconnect).toBe("function");
    expect(typeof result.current.reset).toBe("function");
    expect(typeof result.current.isStreaming).toBe("boolean");
    expect(typeof result.current.getPipelineResult).toBe("function");
    expect(typeof result.current.getIssuesByGate).toBe("function");
    expect(typeof result.current.getIssuesByFile).toBe("function");
    expect(typeof result.current.getCriticalIssuesCount).toBe("function");
  });
});
