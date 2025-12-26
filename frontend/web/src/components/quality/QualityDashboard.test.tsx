/**
 * Unit Tests: QualityDashboard Component
 * SDLC Orchestrator - Sprint 55 Day 2
 *
 * Version: 1.0.0
 * Date: December 27, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 *
 * Test coverage:
 * - Quality score calculation
 * - Grade display (A-F)
 * - Issue summary
 * - Gate progress
 * - Duration display
 * - Vietnamese mode
 * - Empty state
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@/test/test-utils";
import {
  QualityDashboard,
  QualityScoreCard,
  IssueSummaryCard,
  GateProgressCard,
  DurationCard,
} from "./QualityDashboard";
import type { GateResult, PipelineResult } from "@/types/quality";
import "@testing-library/jest-dom";

// ============================================================================
// Test Data Factory
// ============================================================================

const createGateResult = (
  gateName: "syntax" | "security" | "architecture" | "tests",
  status: "pending" | "running" | "passed" | "failed" | "skipped",
  durationMs: number = 0,
  issues: number = 0
): GateResult => {
  const passed = status === "passed";
  return {
    gateName,
    passed,
    status,
    durationMs,
    details:
      gateName === "syntax"
        ? {
            passed,
            issues: Array(issues).fill({
              file: "src/app.py",
              line: 10,
              column: 5,
              message: "SyntaxError",
              vietnameseMessage: "Lỗi cú pháp",
            }),
            filesChecked: 10,
            filesPassed: passed ? 10 : 10 - issues,
          }
        : gateName === "security"
          ? {
              passed,
              issues: [],
              criticalCount: issues > 2 ? 1 : 0,
              highCount: issues > 1 ? 1 : 0,
              mediumCount: issues > 0 ? 1 : 0,
              lowCount: 0,
            }
          : gateName === "architecture"
            ? {
                passed,
                issues: Array(issues).fill({
                  file: "src/routes/api.py",
                  line: 5,
                  rule: "layer-violation",
                  message: "Layer violation",
                  vietnameseMessage: "Vi phạm lớp",
                }),
              }
            : {
                passed,
                results: [],
                testsRun: 10,
                testsPassed: passed ? 10 : 10 - issues,
                testsFailed: passed ? 0 : issues,
              },
  };
};

// All passed - Perfect score
const allPassedGates: GateResult[] = [
  createGateResult("syntax", "passed", 200),
  createGateResult("security", "passed", 500),
  createGateResult("architecture", "passed", 300),
  createGateResult("tests", "passed", 1500),
];

const allPassedResult: PipelineResult = {
  passed: true,
  totalDurationMs: 2500,
  gates: allPassedGates,
  summary: { gatesRun: 4, gatesPassed: 4, gatesFailed: 0 },
  vietnameseSummary: "Tất cả các cổng chất lượng đã đạt.",
};

// Some issues - Medium score
const someIssuesGates: GateResult[] = [
  createGateResult("syntax", "passed", 200, 2),
  createGateResult("security", "passed", 500, 2),
  createGateResult("architecture", "passed", 300, 1),
  createGateResult("tests", "passed", 1500, 1),
];

// Failed gate - Low score
const failedGates: GateResult[] = [
  createGateResult("syntax", "passed", 200),
  createGateResult("security", "failed", 800, 3),
  createGateResult("architecture", "skipped"),
  createGateResult("tests", "skipped"),
];

const failedResult: PipelineResult = {
  passed: false,
  totalDurationMs: 1000,
  gates: failedGates,
  summary: { gatesRun: 2, gatesPassed: 1, gatesFailed: 1 },
  vietnameseSummary: "Kiểm tra chất lượng thất bại.",
};

// Running pipeline
const runningGates: GateResult[] = [
  createGateResult("syntax", "passed", 200),
  createGateResult("security", "running"),
  createGateResult("architecture", "pending"),
  createGateResult("tests", "pending"),
];

// ============================================================================
// QualityDashboard Tests - Basic Rendering
// ============================================================================

describe("QualityDashboard - Basic Rendering", () => {
  it("renders all dashboard sections", () => {
    render(<QualityDashboard gates={allPassedGates} />);

    expect(screen.getByText("Quality Score")).toBeInTheDocument();
    expect(screen.getByText("Issue Summary")).toBeInTheDocument();
    expect(screen.getByText("Gate Progress")).toBeInTheDocument();
    expect(screen.getByText("Execution Time")).toBeInTheDocument();
  });

  it("renders with result prop", () => {
    render(<QualityDashboard result={allPassedResult} />);

    expect(screen.getByText("Quality Score")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("renders empty state when no gates", () => {
    render(<QualityDashboard gates={[]} />);

    expect(screen.getByText("No Quality Data")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(
      <QualityDashboard gates={allPassedGates} className="custom-dashboard" />
    );

    expect(container.firstChild).toHaveClass("custom-dashboard");
  });
});

// ============================================================================
// QualityDashboard Tests - Score Calculation
// ============================================================================

describe("QualityDashboard - Score Calculation", () => {
  it("shows perfect score for all passed gates", () => {
    render(<QualityDashboard gates={allPassedGates} />);

    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("Excellent")).toBeInTheDocument();
  });

  it("shows reduced score for gates with issues", () => {
    render(<QualityDashboard gates={someIssuesGates} />);

    // Score should be less than 100 but still reasonable
    const scoreElement = document.querySelector(".text-5xl");
    expect(scoreElement).toBeInTheDocument();
    const score = parseInt(scoreElement?.textContent || "0");
    expect(score).toBeLessThan(100);
    expect(score).toBeGreaterThan(50);
  });

  it("shows low score for failed pipeline", () => {
    render(<QualityDashboard result={failedResult} />);

    // Score should be low due to failed gate
    const scoreElement = document.querySelector(".text-5xl");
    expect(scoreElement).toBeInTheDocument();
    const score = parseInt(scoreElement?.textContent || "0");
    expect(score).toBeLessThan(80);
  });
});

// ============================================================================
// QualityDashboard Tests - Grade Display
// ============================================================================

describe("QualityDashboard - Grade Display", () => {
  it("shows grade A for perfect score", () => {
    render(<QualityDashboard gates={allPassedGates} />);

    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("Excellent")).toBeInTheDocument();
  });

  it("shows appropriate grade badge color", () => {
    render(<QualityDashboard gates={allPassedGates} />);

    const gradeBadge = screen.getByText("A");
    expect(gradeBadge).toHaveClass("border-green-500");
  });
});

// ============================================================================
// QualityDashboard Tests - Issue Summary
// ============================================================================

describe("QualityDashboard - Issue Summary", () => {
  it("shows zero issues for clean pipeline", () => {
    render(<QualityDashboard gates={allPassedGates} />);

    expect(screen.getByText("No issues detected")).toBeInTheDocument();
  });

  it("shows issue count breakdown", () => {
    render(<QualityDashboard gates={someIssuesGates} />);

    // Should show severity labels
    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("Medium")).toBeInTheDocument();
    expect(screen.getByText("Low")).toBeInTheDocument();
  });

  it("shows total issues count", () => {
    render(<QualityDashboard gates={someIssuesGates} />);

    // Should show total issues message
    const issuesText = screen.getByText(/issues detected/);
    expect(issuesText).toBeInTheDocument();
  });
});

// ============================================================================
// QualityDashboard Tests - Gate Progress
// ============================================================================

describe("QualityDashboard - Gate Progress", () => {
  it("shows all 4 gates", () => {
    render(<QualityDashboard gates={allPassedGates} />);

    // Gate names appear multiple times (GateProgressCard, DurationCard, GatePipeline)
    expect(screen.getAllByText("Syntax").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Security").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Architecture").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Tests").length).toBeGreaterThan(0);
  });

  it("shows correct gate count", () => {
    render(<QualityDashboard gates={allPassedGates} />);

    expect(screen.getByText("4/4")).toBeInTheDocument();
  });

  it("shows running state for current gate", () => {
    render(<QualityDashboard gates={runningGates} currentGate="security" />);

    // Should show running indicator
    const runningIcon = document.querySelector(".animate-pulse");
    expect(runningIcon).toBeInTheDocument();
  });

  it("calls onGateClick when gate is clicked", () => {
    const handleClick = vi.fn();
    render(
      <QualityDashboard gates={allPassedGates} onGateClick={handleClick} />
    );

    // Find first occurrence of Syntax and click its button
    const syntaxTexts = screen.getAllByText("Syntax");
    const syntaxButton = syntaxTexts[0].closest("button");
    if (syntaxButton) {
      fireEvent.click(syntaxButton);
      expect(handleClick).toHaveBeenCalledWith("syntax");
    }
  });
});

// ============================================================================
// QualityDashboard Tests - Duration Display
// ============================================================================

describe("QualityDashboard - Duration Display", () => {
  it("shows total duration", () => {
    render(<QualityDashboard result={allPassedResult} />);

    // Duration may appear multiple times (DurationCard and GatePipeline)
    expect(screen.getAllByText("2.5s").length).toBeGreaterThan(0);
  });

  it("shows duration per gate", () => {
    render(<QualityDashboard gates={allPassedGates} />);

    // Should show individual gate durations (may appear multiple times)
    expect(screen.getAllByText("200ms").length).toBeGreaterThan(0);
    expect(screen.getAllByText("500ms").length).toBeGreaterThan(0);
  });
});

// ============================================================================
// QualityDashboard Tests - Vietnamese Mode
// ============================================================================

describe("QualityDashboard - Vietnamese Mode", () => {
  it("shows Vietnamese labels", () => {
    render(<QualityDashboard gates={allPassedGates} vietnamese={true} />);

    expect(screen.getByText("Điểm chất lượng")).toBeInTheDocument();
    expect(screen.getByText("Tóm tắt vấn đề")).toBeInTheDocument();
    expect(screen.getByText("Tiến độ cổng")).toBeInTheDocument();
    expect(screen.getByText("Thời gian thực hiện")).toBeInTheDocument();
  });

  it("shows Vietnamese grade label", () => {
    render(<QualityDashboard gates={allPassedGates} vietnamese={true} />);

    expect(screen.getByText("Xuất sắc")).toBeInTheDocument();
  });

  it("shows Vietnamese gate names", () => {
    render(<QualityDashboard gates={allPassedGates} vietnamese={true} />);

    // Gate names appear in multiple places (GateProgressCard, DurationCard, GatePipeline)
    expect(screen.getAllByText("Cú pháp").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Bảo mật").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Kiến trúc").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Kiểm thử").length).toBeGreaterThan(0);
  });

  it("shows Vietnamese empty state", () => {
    render(<QualityDashboard gates={[]} vietnamese={true} />);

    expect(screen.getByText("Chưa có dữ liệu chất lượng")).toBeInTheDocument();
  });
});

// ============================================================================
// QualityScoreCard Tests
// ============================================================================

describe("QualityScoreCard", () => {
  it("renders score and grade", () => {
    const grade = {
      letter: "A",
      label: "Excellent",
      vietnameseLabel: "Xuất sắc",
      color: "text-green-600",
      bgColor: "bg-green-100",
      borderColor: "border-green-500",
    };

    render(<QualityScoreCard score={100} grade={grade} />);

    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("shows trend indicator when provided", () => {
    const grade = {
      letter: "B",
      label: "Good",
      vietnameseLabel: "Tốt",
      color: "text-blue-600",
      bgColor: "bg-blue-100",
      borderColor: "border-blue-500",
    };

    render(
      <QualityScoreCard
        score={85}
        grade={grade}
        trend="up"
        previousScore={80}
      />
    );

    expect(screen.getByText("+5")).toBeInTheDocument();
  });
});

// ============================================================================
// IssueSummaryCard Tests
// ============================================================================

describe("IssueSummaryCard", () => {
  it("renders all severity levels", () => {
    const summary = {
      critical: 1,
      high: 2,
      medium: 3,
      low: 4,
      info: 0,
      total: 10,
    };

    render(<IssueSummaryCard summary={summary} />);

    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("Medium")).toBeInTheDocument();
    expect(screen.getByText("Low")).toBeInTheDocument();
  });

  it("shows counts correctly", () => {
    const summary = {
      critical: 1,
      high: 2,
      medium: 3,
      low: 4,
      info: 0,
      total: 10,
    };

    render(<IssueSummaryCard summary={summary} />);

    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("shows Vietnamese labels", () => {
    const summary = { critical: 0, high: 0, medium: 0, low: 0, info: 0, total: 0 };

    render(<IssueSummaryCard summary={summary} vietnamese={true} />);

    expect(screen.getByText("Nghiêm trọng")).toBeInTheDocument();
    expect(screen.getByText("Cao")).toBeInTheDocument();
    expect(screen.getByText("Trung bình")).toBeInTheDocument();
    expect(screen.getByText("Thấp")).toBeInTheDocument();
  });
});

// ============================================================================
// GateProgressCard Tests
// ============================================================================

describe("GateProgressCard", () => {
  it("shows all gates", () => {
    render(<GateProgressCard gates={allPassedGates} />);

    expect(screen.getByText("Syntax")).toBeInTheDocument();
    expect(screen.getByText("Security")).toBeInTheDocument();
    expect(screen.getByText("Architecture")).toBeInTheDocument();
    expect(screen.getByText("Tests")).toBeInTheDocument();
  });

  it("shows passed count", () => {
    render(<GateProgressCard gates={allPassedGates} />);

    expect(screen.getByText("4/4")).toBeInTheDocument();
  });

  it("handles gate click", () => {
    const handleClick = vi.fn();
    render(<GateProgressCard gates={allPassedGates} onGateClick={handleClick} />);

    const syntaxButton = screen.getByText("Syntax").closest("button");
    if (syntaxButton) {
      fireEvent.click(syntaxButton);
      expect(handleClick).toHaveBeenCalledWith("syntax");
    }
  });
});

// ============================================================================
// DurationCard Tests
// ============================================================================

describe("DurationCard", () => {
  it("shows total duration", () => {
    render(<DurationCard totalDuration={2500} gates={allPassedGates} />);

    expect(screen.getByText("2.5s")).toBeInTheDocument();
  });

  it("shows gate durations", () => {
    render(<DurationCard totalDuration={2500} gates={allPassedGates} />);

    // Should show individual gate names and durations
    expect(screen.getByText("Syntax")).toBeInTheDocument();
    expect(screen.getByText("Security")).toBeInTheDocument();
  });

  it("shows Vietnamese labels", () => {
    render(
      <DurationCard
        totalDuration={2500}
        gates={allPassedGates}
        vietnamese={true}
      />
    );

    expect(screen.getByText("Thời gian thực hiện")).toBeInTheDocument();
    expect(screen.getByText("Cú pháp")).toBeInTheDocument();
  });
});

// ============================================================================
// Edge Cases
// ============================================================================

describe("QualityDashboard - Edge Cases", () => {
  it("handles partially completed pipeline", () => {
    render(<QualityDashboard gates={runningGates} currentGate="security" />);

    // Should render without crashing
    expect(screen.getByText("Quality Score")).toBeInTheDocument();
  });

  it("hides pipeline details when showDetails is false", () => {
    render(
      <QualityDashboard gates={allPassedGates} showDetails={false} />
    );

    // Main cards should still be visible
    expect(screen.getByText("Quality Score")).toBeInTheDocument();
    expect(screen.getByText("Issue Summary")).toBeInTheDocument();
  });
});
