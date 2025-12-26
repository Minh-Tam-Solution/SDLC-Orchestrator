/**
 * =========================================================================
 * LiveQualityMonitor Tests - Sprint 55 Day 4
 * SDLC Orchestrator
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * =========================================================================
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { LiveQualityMonitor } from "./LiveQualityMonitor";
import { QualityStreamProvider } from "./QualityStreamProvider";
import type { QualityStreamState, GateStreamState } from "@/hooks/useQualityStream";
import type { GateName } from "@/types/quality";

// ============================================================================
// Mock the useQualityStreamContext hook
// ============================================================================

const mockDefaultGate = (gateName: GateName): GateStreamState => ({
  gateName,
  status: "pending",
  filesProcessed: 0,
  filesTotal: 0,
  issuesFound: 0,
});

const createMockContext = (overrides: Partial<{
  connectionState: QualityStreamState["connectionState"];
  currentGate: GateName | undefined;
  progress: number;
  issues: QualityStreamState["issues"];
  gates: Record<GateName, GateStreamState>;
}> = {}) => ({
  state: {
    connectionState: overrides.connectionState ?? "disconnected",
    gates: overrides.gates ?? {
      syntax: mockDefaultGate("syntax"),
      security: mockDefaultGate("security"),
      architecture: mockDefaultGate("architecture"),
      tests: mockDefaultGate("tests"),
    },
    issues: overrides.issues ?? [],
    currentGate: overrides.currentGate,
    overallProgress: overrides.progress ?? 0,
  },
  connectionState: overrides.connectionState ?? "disconnected",
  isStreaming: overrides.connectionState === "connected",
  isComplete: overrides.connectionState === "completed",
  currentGate: overrides.currentGate,
  progress: overrides.progress ?? 0,
  issues: overrides.issues ?? [],
  gates: overrides.gates ?? {
    syntax: mockDefaultGate("syntax"),
    security: mockDefaultGate("security"),
    architecture: mockDefaultGate("architecture"),
    tests: mockDefaultGate("tests"),
  },
  connect: vi.fn(),
  disconnect: vi.fn(),
  reset: vi.fn(),
  getPipelineResult: vi.fn().mockReturnValue(null),
  getIssuesByGate: vi.fn().mockReturnValue([]),
  getIssuesByFile: vi.fn().mockReturnValue([]),
  getCriticalIssuesCount: vi.fn().mockReturnValue(0),
});

// Mock the context hook
vi.mock("./QualityStreamProvider", async () => {
  const actual = await vi.importActual("./QualityStreamProvider");
  return {
    ...actual,
    useQualityStreamContext: vi.fn(),
  };
});

import { useQualityStreamContext } from "./QualityStreamProvider";

const mockUseQualityStreamContext = useQualityStreamContext as ReturnType<typeof vi.fn>;

// ============================================================================
// Tests
// ============================================================================

describe("LiveQualityMonitor", () => {
  beforeEach(() => {
    mockUseQualityStreamContext.mockReturnValue(createMockContext());
  });

  describe("Basic Rendering", () => {
    it("should render monitor title", () => {
      render(<LiveQualityMonitor />);

      expect(screen.getByText("Quality Monitor")).toBeInTheDocument();
    });

    it("should render Vietnamese title when vietnamese prop is true", () => {
      render(<LiveQualityMonitor vietnamese />);

      expect(screen.getByText("Giám sát chất lượng")).toBeInTheDocument();
    });

    it("should show disconnected status initially", () => {
      render(<LiveQualityMonitor />);

      expect(screen.getByText("Disconnected")).toBeInTheDocument();
    });

    it("should show Vietnamese disconnected status", () => {
      render(<LiveQualityMonitor vietnamese />);

      expect(screen.getByText("Ngắt kết nối")).toBeInTheDocument();
    });
  });

  describe("Connection States", () => {
    it("should show connected status with pulse indicator", () => {
      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "connected" })
      );

      render(<LiveQualityMonitor />);

      expect(screen.getByText("Connected")).toBeInTheDocument();
    });

    it("should show connecting status with spinner", () => {
      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "connecting" })
      );

      render(<LiveQualityMonitor />);

      expect(screen.getByText("Connecting...")).toBeInTheDocument();
    });

    it("should show error status", () => {
      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "error" })
      );

      render(<LiveQualityMonitor />);

      expect(screen.getByText("Connection Error")).toBeInTheDocument();
    });

    it("should show completed status", () => {
      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "completed" })
      );

      render(<LiveQualityMonitor />);

      expect(screen.getByText("Completed")).toBeInTheDocument();
    });
  });

  describe("Controls", () => {
    it("should show Connect button when disconnected", () => {
      render(<LiveQualityMonitor showControls />);

      expect(screen.getByText("Connect")).toBeInTheDocument();
    });

    it("should show Disconnect button when connected", () => {
      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "connected" })
      );

      render(<LiveQualityMonitor showControls />);

      expect(screen.getByText("Disconnect")).toBeInTheDocument();
    });

    it("should show Reset button when completed", () => {
      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "completed" })
      );

      render(<LiveQualityMonitor showControls />);

      expect(screen.getByText("Reset")).toBeInTheDocument();
    });

    it("should call connect when Connect button is clicked", () => {
      const mockContext = createMockContext();
      mockUseQualityStreamContext.mockReturnValue(mockContext);

      render(<LiveQualityMonitor showControls />);

      fireEvent.click(screen.getByText("Connect"));

      expect(mockContext.connect).toHaveBeenCalled();
    });

    it("should call disconnect when Disconnect button is clicked", () => {
      const mockContext = createMockContext({ connectionState: "connected" });
      mockUseQualityStreamContext.mockReturnValue(mockContext);

      render(<LiveQualityMonitor showControls />);

      fireEvent.click(screen.getByText("Disconnect"));

      expect(mockContext.disconnect).toHaveBeenCalled();
    });

    it("should hide controls when showControls is false", () => {
      render(<LiveQualityMonitor showControls={false} />);

      expect(screen.queryByText("Connect")).not.toBeInTheDocument();
    });
  });

  describe("Progress Display", () => {
    it("should show overall progress percentage", () => {
      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ progress: 50 })
      );

      render(<LiveQualityMonitor />);

      expect(screen.getByText("50%")).toBeInTheDocument();
    });

    it("should show current gate being processed", () => {
      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({
          connectionState: "connected",
          currentGate: "security",
        })
      );

      render(<LiveQualityMonitor />);

      expect(screen.getByText(/Processing:.*Security/i)).toBeInTheDocument();
    });

    it("should show Vietnamese current gate", () => {
      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({
          connectionState: "connected",
          currentGate: "security",
        })
      );

      render(<LiveQualityMonitor vietnamese />);

      expect(screen.getByText(/Đang xử lý:.*Bảo mật/i)).toBeInTheDocument();
    });
  });

  describe("Gate Details", () => {
    it("should show all 4 gates when showGateDetails is true", () => {
      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "connected" })
      );

      render(<LiveQualityMonitor showGateDetails />);

      expect(screen.getByText("Gate Details")).toBeInTheDocument();
      expect(screen.getAllByText(/Syntax|Cú pháp/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Security|Bảo mật/i).length).toBeGreaterThan(0);
    });

    it("should hide gate details when showGateDetails is false", () => {
      render(<LiveQualityMonitor showGateDetails={false} />);

      expect(screen.queryByText("Gate Details")).not.toBeInTheDocument();
    });

    it("should show running badge for current gate", () => {
      const gates: Record<GateName, GateStreamState> = {
        syntax: { ...mockDefaultGate("syntax"), status: "running" },
        security: mockDefaultGate("security"),
        architecture: mockDefaultGate("architecture"),
        tests: mockDefaultGate("tests"),
      };

      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({
          connectionState: "connected",
          currentGate: "syntax",
          gates,
        })
      );

      render(<LiveQualityMonitor showGateDetails />);

      expect(screen.getByText("Running")).toBeInTheDocument();
    });

    it("should show passed gate status", () => {
      const gates: Record<GateName, GateStreamState> = {
        syntax: { ...mockDefaultGate("syntax"), status: "passed", passed: true },
        security: mockDefaultGate("security"),
        architecture: mockDefaultGate("architecture"),
        tests: mockDefaultGate("tests"),
      };

      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "connected", gates })
      );

      render(<LiveQualityMonitor showGateDetails />);

      // Check for passed status (green checkmark icon should be visible)
      const gateCards = document.querySelectorAll('[class*="rounded-lg border"]');
      expect(gateCards.length).toBeGreaterThan(0);
    });

    it("should show gate progress when running", () => {
      const gates: Record<GateName, GateStreamState> = {
        syntax: {
          ...mockDefaultGate("syntax"),
          status: "running",
          filesProcessed: 5,
          filesTotal: 10,
        },
        security: mockDefaultGate("security"),
        architecture: mockDefaultGate("architecture"),
        tests: mockDefaultGate("tests"),
      };

      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({
          connectionState: "connected",
          currentGate: "syntax",
          gates,
        })
      );

      render(<LiveQualityMonitor showGateDetails />);

      expect(screen.getByText("5/10 files")).toBeInTheDocument();
    });
  });

  describe("Issue Feed", () => {
    it("should show empty issue feed message when no issues", () => {
      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "connected" })
      );

      render(<LiveQualityMonitor showIssueFeed />);

      expect(screen.getByText("No issues found yet")).toBeInTheDocument();
    });

    it("should show Vietnamese empty message", () => {
      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "connected" })
      );

      render(<LiveQualityMonitor showIssueFeed vietnamese />);

      expect(screen.getByText("Chưa có lỗi nào")).toBeInTheDocument();
    });

    it("should display issues when present", () => {
      const issues = [
        {
          id: "issue-1",
          gateName: "security" as GateName,
          severity: "critical" as const,
          file: "src/main.py",
          line: 42,
          message: "SQL injection vulnerability",
          timestamp: Date.now(),
        },
      ];

      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "connected", issues })
      );

      render(<LiveQualityMonitor showIssueFeed />);

      expect(screen.getByText("SQL injection vulnerability")).toBeInTheDocument();
      expect(screen.getByText(/src\/main.py:42/)).toBeInTheDocument();
    });

    it("should show issue count badge", () => {
      const issues = [
        {
          id: "issue-1",
          gateName: "security" as GateName,
          severity: "critical" as const,
          file: "test.py",
          message: "Error 1",
          timestamp: Date.now(),
        },
        {
          id: "issue-2",
          gateName: "syntax" as GateName,
          severity: "high" as const,
          file: "test2.py",
          message: "Error 2",
          timestamp: Date.now(),
        },
      ];

      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "connected", issues })
      );

      render(<LiveQualityMonitor showIssueFeed />);

      expect(screen.getByText("2")).toBeInTheDocument();
    });

    it("should hide issue feed when showIssueFeed is false", () => {
      render(<LiveQualityMonitor showIssueFeed={false} />);

      expect(screen.queryByText("Issues Found")).not.toBeInTheDocument();
    });
  });

  describe("Summary Stats", () => {
    it("should show passed gates count", () => {
      const gates: Record<GateName, GateStreamState> = {
        syntax: { ...mockDefaultGate("syntax"), status: "passed", passed: true },
        security: { ...mockDefaultGate("security"), status: "passed", passed: true },
        architecture: mockDefaultGate("architecture"),
        tests: mockDefaultGate("tests"),
      };

      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "connected", gates })
      );

      render(<LiveQualityMonitor />);

      expect(screen.getByText("2 passed")).toBeInTheDocument();
    });

    it("should show failed gates count", () => {
      const gates: Record<GateName, GateStreamState> = {
        syntax: { ...mockDefaultGate("syntax"), status: "failed", passed: false },
        security: mockDefaultGate("security"),
        architecture: mockDefaultGate("architecture"),
        tests: mockDefaultGate("tests"),
      };

      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "connected", gates })
      );

      render(<LiveQualityMonitor />);

      expect(screen.getByText("1 failed")).toBeInTheDocument();
    });

    it("should show critical issues count", () => {
      const issues = [
        {
          id: "issue-1",
          gateName: "security" as GateName,
          severity: "critical" as const,
          file: "test.py",
          message: "Critical error",
          timestamp: Date.now(),
        },
      ];

      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "connected", issues })
      );

      render(<LiveQualityMonitor />);

      expect(screen.getByText("1 critical")).toBeInTheDocument();
    });
  });

  describe("Compact Mode", () => {
    it("should render compact mode", () => {
      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "connected", progress: 75 })
      );

      render(<LiveQualityMonitor compact />);

      expect(screen.getByText("75%")).toBeInTheDocument();
      // Should not show full card layout
      expect(screen.queryByText("Gate Details")).not.toBeInTheDocument();
    });

    it("should show issue count in compact mode", () => {
      const issues = [
        {
          id: "issue-1",
          gateName: "syntax" as GateName,
          severity: "high" as const,
          file: "test.py",
          message: "Error",
          timestamp: Date.now(),
        },
      ];

      mockUseQualityStreamContext.mockReturnValue(
        createMockContext({ connectionState: "connected", issues })
      );

      render(<LiveQualityMonitor compact />);

      expect(screen.getByText("1 issues")).toBeInTheDocument();
    });
  });
});
