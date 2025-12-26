/**
 * =========================================================================
 * QualityPanel Tests - Integrated Quality Pipeline Panel Tests
 * SDLC Orchestrator - Sprint 56 Day 3
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Backend Integration
 * =========================================================================
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import QualityPanel from "./QualityPanel";

// Mock the API client
vi.mock("@/api/client", () => ({
  getAccessToken: vi.fn(() => "test-token"),
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// Mock the hooks
vi.mock("@/hooks/useQualityApi", () => ({
  useSessionQuality: vi.fn(() => ({
    data: null,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  })),
  useInvalidateQualityCache: vi.fn(() => ({
    invalidateSession: vi.fn(),
    invalidateAll: vi.fn(),
  })),
  qualityKeys: {
    all: ["quality"],
    session: (id: string) => ["quality", "session", id],
  },
}));

vi.mock("@/hooks/useQualityStreamBackend", () => ({
  useQualityStreamBackend: vi.fn(() => ({
    state: {
      connectionState: "disconnected",
      gates: {
        syntax: { gateName: "syntax", status: "pending", durationMs: 0, issuesFound: 0, filesProcessed: 0, filesTotal: 0 },
        security: { gateName: "security", status: "pending", durationMs: 0, issuesFound: 0, filesProcessed: 0, filesTotal: 0 },
        architecture: { gateName: "architecture", status: "pending", durationMs: 0, issuesFound: 0, filesProcessed: 0, filesTotal: 0 },
        tests: { gateName: "tests", status: "pending", durationMs: 0, issuesFound: 0, filesProcessed: 0, filesTotal: 0 },
      },
      issues: [],
      overallProgress: 0,
    },
    connect: vi.fn(),
    disconnect: vi.fn(),
    reset: vi.fn(),
    isStreaming: false,
    getPipelineResult: vi.fn(() => null),
  })),
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

describe("QualityPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Rendering", () => {
    it("should render with title", () => {
      render(<QualityPanel sessionId={null} />, { wrapper: createWrapper() });
      expect(screen.getByText("Code Quality")).toBeInTheDocument();
    });

    it("should render Vietnamese title when vietnamese prop is true", () => {
      render(<QualityPanel sessionId={null} vietnamese />, {
        wrapper: createWrapper(),
      });
      expect(screen.getByText("Chất lượng Code")).toBeInTheDocument();
    });

    it("should render tabs", () => {
      render(<QualityPanel sessionId="test-session" />, {
        wrapper: createWrapper(),
      });
      expect(screen.getByText("Summary")).toBeInTheDocument();
      expect(screen.getByText("Live")).toBeInTheDocument();
      expect(screen.getByText("Report")).toBeInTheDocument();
    });

    it("should render Vietnamese tabs when vietnamese prop is true", () => {
      render(<QualityPanel sessionId="test-session" vietnamese />, {
        wrapper: createWrapper(),
      });
      expect(screen.getByText("Tóm tắt")).toBeInTheDocument();
      expect(screen.getByText("Trực tiếp")).toBeInTheDocument();
      expect(screen.getByText("Báo cáo")).toBeInTheDocument();
    });
  });

  describe("Compact Mode", () => {
    it("should render compact version when compact prop is true", () => {
      render(<QualityPanel sessionId={null} compact />, {
        wrapper: createWrapper(),
      });
      expect(screen.getByText("No quality data")).toBeInTheDocument();
    });

    it("should render Vietnamese compact message", () => {
      render(<QualityPanel sessionId={null} compact vietnamese />, {
        wrapper: createWrapper(),
      });
      expect(screen.getByText("Chưa có dữ liệu chất lượng")).toBeInTheDocument();
    });

    it("should show start button in compact mode with sessionId", () => {
      render(<QualityPanel sessionId="test-session" compact />, {
        wrapper: createWrapper(),
      });
      expect(screen.getByText("Start")).toBeInTheDocument();
    });
  });

  describe("No Data State", () => {
    it("should show no data message when no sessionId", () => {
      render(<QualityPanel sessionId={null} />, { wrapper: createWrapper() });
      expect(
        screen.getByText("No quality data for this session")
      ).toBeInTheDocument();
    });

    it("should show start quality check button when sessionId provided", () => {
      render(<QualityPanel sessionId="test-session" />, {
        wrapper: createWrapper(),
      });
      expect(screen.getByText("Start Quality Check")).toBeInTheDocument();
    });

    it("should show Vietnamese no data message", () => {
      render(<QualityPanel sessionId={null} vietnamese />, {
        wrapper: createWrapper(),
      });
      expect(
        screen.getByText("Chưa có dữ liệu chất lượng cho phiên này")
      ).toBeInTheDocument();
    });
  });

  describe("Actions", () => {
    it("should have refresh button", () => {
      render(<QualityPanel sessionId="test-session" />, {
        wrapper: createWrapper(),
      });
      // Find refresh button by its icon container
      const buttons = screen.getAllByRole("button");
      expect(buttons.length).toBeGreaterThan(0);
    });

    it("should have stream button when sessionId provided", () => {
      render(<QualityPanel sessionId="test-session" />, {
        wrapper: createWrapper(),
      });
      expect(screen.getByText("Stream")).toBeInTheDocument();
    });

    it("should not show stream button when enableStreaming is false", () => {
      render(
        <QualityPanel sessionId="test-session" enableStreaming={false} />,
        { wrapper: createWrapper() }
      );
      expect(screen.queryByText("Stream")).not.toBeInTheDocument();
    });
  });

  describe("Props", () => {
    it("should accept className prop", () => {
      render(
        <QualityPanel sessionId="test" className="custom-class" />,
        { wrapper: createWrapper() }
      );
      const card = document.querySelector(".custom-class");
      expect(card).toBeInTheDocument();
    });

    it("should hide report tab when showReport is false", () => {
      render(<QualityPanel sessionId="test" showReport={false} />, {
        wrapper: createWrapper(),
      });
      expect(screen.queryByText("Report")).not.toBeInTheDocument();
    });
  });
});
