/**
 * Unit Tests: GatePipeline Component
 * SDLC Orchestrator - Sprint 55 Day 1
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 *
 * Test coverage:
 * - Pipeline rendering (4 gates)
 * - Gate status display
 * - Progress calculation
 * - Horizontal/vertical layouts
 * - Compact mode
 * - Vietnamese mode
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@/test/test-utils";
import { GatePipeline, CompactPipeline } from "./GatePipeline";
import type { GateResult, PipelineResult } from "@/types/quality";
import "@testing-library/jest-dom";

// ============================================================================
// Test Data Factory
// ============================================================================

const createGateResult = (
  gateName: "syntax" | "security" | "architecture" | "tests",
  status: "pending" | "running" | "passed" | "failed" | "skipped",
  durationMs?: number
): GateResult => {
  const passed = status === "passed";
  return {
    gateName,
    passed,
    status,
    durationMs: durationMs ?? 0,
    details:
      gateName === "syntax"
        ? { passed, issues: [], filesChecked: 10, filesPassed: passed ? 10 : 8 }
        : gateName === "security"
        ? {
            passed,
            issues: [],
            criticalCount: 0,
            highCount: 0,
            mediumCount: 0,
            lowCount: 0,
          }
        : gateName === "architecture"
        ? { passed, issues: [] }
        : { passed, results: [], testsRun: 5, testsPassed: passed ? 5 : 3, testsFailed: passed ? 0 : 2 },
  };
};

// Running pipeline with one gate passed
const runningGates: GateResult[] = [
  createGateResult("syntax", "passed", 250),
  createGateResult("security", "running"),
  createGateResult("architecture", "pending"),
  createGateResult("tests", "pending"),
];

// Completed pipeline (all passed)
const completedGates: GateResult[] = [
  createGateResult("syntax", "passed", 200),
  createGateResult("security", "passed", 500),
  createGateResult("architecture", "passed", 300),
  createGateResult("tests", "passed", 1500),
];

const completedPipelineResult: PipelineResult = {
  passed: true,
  totalDurationMs: 2500,
  gates: completedGates,
  summary: { gatesRun: 4, gatesPassed: 4, gatesFailed: 0 },
  vietnameseSummary: "Tất cả các cổng chất lượng đã đạt.",
};

// Failed pipeline
const failedGates: GateResult[] = [
  createGateResult("syntax", "passed", 200),
  createGateResult("security", "failed", 800),
  createGateResult("architecture", "skipped"),
  createGateResult("tests", "skipped"),
];

const failedPipelineResult: PipelineResult = {
  passed: false,
  totalDurationMs: 1000,
  gates: failedGates,
  summary: { gatesRun: 2, gatesPassed: 1, gatesFailed: 1 },
  vietnameseSummary: "Kiểm tra chất lượng thất bại.",
};

// ============================================================================
// GatePipeline Tests - Basic Rendering
// ============================================================================

describe("GatePipeline - Basic Rendering", () => {
  it("renders all 4 gates", () => {
    render(<GatePipeline gates={runningGates} />);

    expect(screen.getByText("Syntax")).toBeInTheDocument();
    expect(screen.getByText("Security")).toBeInTheDocument();
    expect(screen.getByText("Architecture")).toBeInTheDocument();
    expect(screen.getByText("Tests")).toBeInTheDocument();
  });

  it("renders with result prop", () => {
    render(<GatePipeline result={completedPipelineResult} />);

    expect(screen.getByText("Syntax")).toBeInTheDocument();
    expect(screen.getByText("Quality Pipeline")).toBeInTheDocument();
  });

  it("shows running spinner for running gate", () => {
    render(<GatePipeline gates={runningGates} currentGate="security" />);

    const spinner = document.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });

  it("renders completed pipeline", () => {
    render(<GatePipeline result={completedPipelineResult} />);

    // Pipeline shows the passed state
    const checkIcon = document.querySelector(".text-green-500");
    expect(checkIcon).toBeInTheDocument();
  });

  it("renders failed pipeline", () => {
    render(<GatePipeline result={failedPipelineResult} />);

    // Pipeline shows the failed state
    const failIcon = document.querySelector(".text-red-500");
    expect(failIcon).toBeInTheDocument();
  });
});

// ============================================================================
// GatePipeline Tests - Progress
// ============================================================================

describe("GatePipeline - Progress", () => {
  it("shows progress bar", () => {
    render(<GatePipeline gates={runningGates} />);

    // Progress bar container should exist
    const progressContainer = document.querySelector('[class*="h-2"]');
    expect(progressContainer).toBeInTheDocument();
  });

  it("shows duration when pipeline is complete", () => {
    render(<GatePipeline result={completedPipelineResult} />);

    // Total duration: 2500ms = 2.5s
    expect(screen.getByText("2.5s")).toBeInTheDocument();
  });
});

// ============================================================================
// GatePipeline Tests - Layout
// ============================================================================

describe("GatePipeline - Layout", () => {
  it("renders horizontal layout by default", () => {
    const { container } = render(<GatePipeline gates={runningGates} />);

    // Horizontal layout uses flex-row
    const flexRow = container.querySelector('[class*="flex-row"]');
    expect(flexRow).toBeInTheDocument();
  });

  it("renders vertical layout when specified", () => {
    const { container } = render(
      <GatePipeline gates={runningGates} direction="vertical" />
    );

    // Vertical layout uses flex-col
    const flexCol = container.querySelector('[class*="flex-col"]');
    expect(flexCol).toBeInTheDocument();
  });
});

// ============================================================================
// GatePipeline Tests - Vietnamese Mode
// ============================================================================

describe("GatePipeline - Vietnamese Mode", () => {
  it("shows Vietnamese gate labels", () => {
    render(<GatePipeline gates={runningGates} vietnamese={true} />);

    expect(screen.getByText("Cú pháp")).toBeInTheDocument();
    expect(screen.getByText("Bảo mật")).toBeInTheDocument();
    expect(screen.getByText("Kiến trúc")).toBeInTheDocument();
    expect(screen.getByText("Kiểm thử")).toBeInTheDocument();
  });

  it("shows Vietnamese pipeline title", () => {
    render(<GatePipeline gates={runningGates} vietnamese={true} />);

    expect(screen.getByText("Đường ống chất lượng")).toBeInTheDocument();
  });
});

// ============================================================================
// GatePipeline Tests - Click Handler
// ============================================================================

describe("GatePipeline - Click Handler", () => {
  it("calls onGateClick when gate is clicked", () => {
    const handleClick = vi.fn();
    render(
      <GatePipeline gates={runningGates} onGateClick={handleClick} />
    );

    // Find a gate button and click it
    const syntaxButton = screen.getByText("Syntax").closest("button");
    if (syntaxButton) {
      fireEvent.click(syntaxButton);
      expect(handleClick).toHaveBeenCalledWith("syntax");
    }
  });
});

// ============================================================================
// CompactPipeline Tests
// ============================================================================

describe("CompactPipeline", () => {
  it("renders compact badges for all gates", () => {
    render(<CompactPipeline gates={runningGates} />);

    // Compact mode uses smaller badges
    const badges = document.querySelectorAll('[class*="rounded-full"]');
    expect(badges.length).toBeGreaterThanOrEqual(4);
  });

  it("shows gate icons in compact mode", () => {
    render(<CompactPipeline gates={runningGates} />);

    // Should have SVG icons for each gate
    const icons = document.querySelectorAll("svg");
    expect(icons.length).toBeGreaterThanOrEqual(4);
  });

  it("applies custom className", () => {
    const { container } = render(
      <CompactPipeline gates={runningGates} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass("custom-class");
  });

  it("supports currentGate prop", () => {
    render(<CompactPipeline gates={runningGates} currentGate="security" />);

    // Should show running state for security
    const spinner = document.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });
});

// ============================================================================
// Edge Cases
// ============================================================================

describe("GatePipeline - Edge Cases", () => {
  it("handles empty gates array", () => {
    render(<GatePipeline gates={[]} />);

    // Should render without crashing, still show gate names
    expect(screen.getByText("Syntax")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(
      <GatePipeline gates={runningGates} className="custom-pipeline" />
    );

    expect(container.querySelector(".custom-pipeline")).toBeInTheDocument();
  });

  it("shows details when showDetails is true", () => {
    render(
      <GatePipeline result={completedPipelineResult} showDetails={true} />
    );

    // Should show summary message
    expect(screen.getByText(/All quality gates passed/)).toBeInTheDocument();
  });
});
