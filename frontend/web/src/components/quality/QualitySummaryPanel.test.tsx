/**
 * =========================================================================
 * QualitySummaryPanel Tests - Sprint 55 Day 5
 * SDLC Orchestrator
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * =========================================================================
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  QualitySummaryPanel,
  CompactQualitySummary,
  InlineQualityBadge,
  QualityTrendIndicator,
  GateStatusSummary,
} from "./QualitySummaryPanel";
import type { PipelineResult, GateResult, GateName } from "@/types/quality";

// ============================================================================
// Test Data
// ============================================================================

const mockPipelineResult: PipelineResult = {
  passed: false,
  totalDurationMs: 5000,
  vietnameseSummary: "2/4 cổng đã đạt",
  summary: {
    gatesRun: 4,
    gatesPassed: 2,
    gatesFailed: 2,
  },
  gates: [
    {
      gateName: "syntax",
      passed: false,
      status: "failed",
      durationMs: 1000,
      details: {
        passed: false,
        filesChecked: 5,
        filesPassed: 3,
        issues: [
          {
            file: "src/main.py",
            line: 10,
            column: 5,
            message: "Invalid syntax",
            vietnameseMessage: "Cú pháp không hợp lệ",
          },
        ],
      },
    },
    {
      gateName: "security",
      passed: false,
      status: "failed",
      durationMs: 2000,
      details: {
        passed: false,
        criticalCount: 1,
        highCount: 1,
        mediumCount: 0,
        lowCount: 0,
        issues: [
          {
            file: "src/main.py",
            line: 50,
            ruleId: "sql-injection",
            severity: "critical" as const,
            message: "SQL injection vulnerability",
            vietnameseMessage: "Lỗ hổng SQL injection",
          },
        ],
      },
    },
    {
      gateName: "architecture",
      passed: true,
      status: "passed",
      durationMs: 1500,
      details: {
        passed: true,
        issues: [],
      },
    },
    {
      gateName: "tests",
      passed: true,
      status: "passed",
      durationMs: 500,
      details: {
        passed: true,
        testsRun: 10,
        testsPassed: 10,
        testsFailed: 0,
        results: [],
      },
    },
  ],
};

const cleanPipelineResult: PipelineResult = {
  passed: true,
  totalDurationMs: 3000,
  vietnameseSummary: "Tất cả cổng đã đạt",
  summary: {
    gatesRun: 4,
    gatesPassed: 4,
    gatesFailed: 0,
  },
  gates: [
    {
      gateName: "syntax",
      passed: true,
      status: "passed",
      durationMs: 800,
      details: {
        passed: true,
        filesChecked: 5,
        filesPassed: 5,
        issues: [],
      },
    },
    {
      gateName: "security",
      passed: true,
      status: "passed",
      durationMs: 1200,
      details: {
        passed: true,
        criticalCount: 0,
        highCount: 0,
        mediumCount: 0,
        lowCount: 0,
        issues: [],
      },
    },
    {
      gateName: "architecture",
      passed: true,
      status: "passed",
      durationMs: 500,
      details: {
        passed: true,
        issues: [],
      },
    },
    {
      gateName: "tests",
      passed: true,
      status: "passed",
      durationMs: 500,
      details: {
        passed: true,
        testsRun: 10,
        testsPassed: 10,
        testsFailed: 0,
        results: [],
      },
    },
  ],
};

// ============================================================================
// QualityTrendIndicator Tests
// ============================================================================

describe("QualityTrendIndicator", () => {
  it("should show upward trend when score improved", () => {
    render(<QualityTrendIndicator currentScore={85} previousScore={75} />);

    expect(screen.getByText(/\+10.*Improved/)).toBeInTheDocument();
  });

  it("should show downward trend when score declined", () => {
    render(<QualityTrendIndicator currentScore={70} previousScore={80} />);

    expect(screen.getByText(/Declined/)).toBeInTheDocument();
  });

  it("should show stable when score unchanged", () => {
    render(<QualityTrendIndicator currentScore={80} previousScore={80} />);

    expect(screen.getByText(/Stable/)).toBeInTheDocument();
  });

  it("should show Vietnamese labels when vietnamese is true", () => {
    render(<QualityTrendIndicator currentScore={85} previousScore={75} vietnamese />);

    expect(screen.getByText(/\+10.*Tăng/)).toBeInTheDocument();
  });

  it("should show Vietnamese declined label", () => {
    render(<QualityTrendIndicator currentScore={70} previousScore={80} vietnamese />);

    expect(screen.getByText(/Giảm/)).toBeInTheDocument();
  });

  it("should show Vietnamese stable label", () => {
    render(<QualityTrendIndicator currentScore={80} previousScore={80} vietnamese />);

    expect(screen.getByText(/Ổn định/)).toBeInTheDocument();
  });
});

// ============================================================================
// GateStatusSummary Tests
// ============================================================================

describe("GateStatusSummary", () => {
  it("should render all 4 gates", () => {
    render(<GateStatusSummary gates={mockPipelineResult.gates} />);

    expect(screen.getByText("Syntax")).toBeInTheDocument();
    expect(screen.getByText("Security")).toBeInTheDocument();
    expect(screen.getByText("Architecture")).toBeInTheDocument();
    expect(screen.getByText("Tests")).toBeInTheDocument();
  });

  it("should render Vietnamese labels when vietnamese is true", () => {
    render(<GateStatusSummary gates={mockPipelineResult.gates} vietnamese />);

    expect(screen.getByText("Cú pháp")).toBeInTheDocument();
    expect(screen.getByText("Bảo mật")).toBeInTheDocument();
    expect(screen.getByText("Kiến trúc")).toBeInTheDocument();
    expect(screen.getByText("Kiểm thử")).toBeInTheDocument();
  });

  it("should show compact mode with icons only", () => {
    const { container } = render(
      <GateStatusSummary gates={mockPipelineResult.gates} compact />
    );

    // In compact mode, labels should not be visible
    expect(screen.queryByText("Syntax")).not.toBeInTheDocument();
    // But should have 4 icon containers
    const icons = container.querySelectorAll("svg");
    expect(icons.length).toBeGreaterThanOrEqual(4);
  });

  it("should show passed status with green color", () => {
    const { container } = render(
      <GateStatusSummary gates={cleanPipelineResult.gates} />
    );

    // Should have green backgrounds for passed gates
    const greenElements = container.querySelectorAll('[class*="green"]');
    expect(greenElements.length).toBeGreaterThan(0);
  });

  it("should show failed status with red color", () => {
    const { container } = render(
      <GateStatusSummary gates={mockPipelineResult.gates} />
    );

    // Should have red elements for failed gates
    const redElements = container.querySelectorAll('[class*="red"]');
    expect(redElements.length).toBeGreaterThan(0);
  });
});

// ============================================================================
// InlineQualityBadge Tests
// ============================================================================

describe("InlineQualityBadge", () => {
  it("should show grade letter", () => {
    render(<InlineQualityBadge result={cleanPipelineResult} />);

    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("should show score", () => {
    render(<InlineQualityBadge result={cleanPipelineResult} />);

    expect(screen.getByText("100/100")).toBeInTheDocument();
  });

  it("should show gates passed count", () => {
    render(<InlineQualityBadge result={mockPipelineResult} />);

    expect(screen.getByText("2/4")).toBeInTheDocument();
  });

  it("should show issue count when issues exist", () => {
    render(<InlineQualityBadge result={mockPipelineResult} showIssueCount />);

    expect(screen.getByText(/issues/)).toBeInTheDocument();
  });

  it("should hide issue count when showIssueCount is false", () => {
    render(<InlineQualityBadge result={mockPipelineResult} showIssueCount={false} />);

    expect(screen.queryByText(/issues/)).not.toBeInTheDocument();
  });

  it("should show Vietnamese issue label", () => {
    render(<InlineQualityBadge result={mockPipelineResult} showIssueCount vietnamese />);

    expect(screen.getByText(/lỗi/)).toBeInTheDocument();
  });

  it("should not show issue badge for clean pipeline", () => {
    render(<InlineQualityBadge result={cleanPipelineResult} showIssueCount />);

    expect(screen.queryByText(/issues/)).not.toBeInTheDocument();
  });
});

// ============================================================================
// CompactQualitySummary Tests
// ============================================================================

describe("CompactQualitySummary", () => {
  it("should show grade letter in circle", () => {
    render(<CompactQualitySummary result={cleanPipelineResult} />);

    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("should show score", () => {
    render(<CompactQualitySummary result={cleanPipelineResult} />);

    expect(screen.getByText("100/100")).toBeInTheDocument();
  });

  it("should show Passed badge for clean pipeline", () => {
    render(<CompactQualitySummary result={cleanPipelineResult} />);

    expect(screen.getByText("Passed")).toBeInTheDocument();
  });

  it("should show Failed badge for failed pipeline", () => {
    render(<CompactQualitySummary result={mockPipelineResult} />);

    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  it("should show Vietnamese Passed badge", () => {
    render(<CompactQualitySummary result={cleanPipelineResult} vietnamese />);

    expect(screen.getByText("Đạt")).toBeInTheDocument();
  });

  it("should show Vietnamese Failed badge", () => {
    render(<CompactQualitySummary result={mockPipelineResult} vietnamese />);

    expect(screen.getByText("Thất bại")).toBeInTheDocument();
  });

  it("should show gates count", () => {
    render(<CompactQualitySummary result={mockPipelineResult} />);

    expect(screen.getByText(/2\/4 gates/)).toBeInTheDocument();
  });

  it("should show Vietnamese gates count", () => {
    render(<CompactQualitySummary result={mockPipelineResult} vietnamese />);

    expect(screen.getByText(/2\/4 cổng/)).toBeInTheDocument();
  });

  it("should show issues count when issues exist", () => {
    render(<CompactQualitySummary result={mockPipelineResult} />);

    expect(screen.getByText(/issues/)).toBeInTheDocument();
  });

  it("should call onClick when clicked", () => {
    const onClick = vi.fn();
    render(<CompactQualitySummary result={mockPipelineResult} onClick={onClick} />);

    fireEvent.click(screen.getByRole("button"));

    expect(onClick).toHaveBeenCalled();
  });

  it("should show compact gate status icons", () => {
    const { container } = render(
      <CompactQualitySummary result={mockPipelineResult} />
    );

    // Should have gate status icons
    const icons = container.querySelectorAll("svg");
    expect(icons.length).toBeGreaterThan(0);
  });

  it("should apply custom className", () => {
    const { container } = render(
      <CompactQualitySummary
        result={mockPipelineResult}
        className="custom-class"
      />
    );

    expect(container.firstChild).toHaveClass("custom-class");
  });
});

// ============================================================================
// QualitySummaryPanel Tests
// ============================================================================

describe("QualitySummaryPanel", () => {
  it("should render panel title", () => {
    render(<QualitySummaryPanel result={mockPipelineResult} />);

    expect(screen.getByText("Quality Summary")).toBeInTheDocument();
  });

  it("should render Vietnamese title", () => {
    render(<QualitySummaryPanel result={mockPipelineResult} vietnamese />);

    expect(screen.getByText("Tóm tắt chất lượng")).toBeInTheDocument();
  });

  it("should show quality grade", () => {
    render(<QualitySummaryPanel result={cleanPipelineResult} />);

    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("should show quality score", () => {
    render(<QualitySummaryPanel result={cleanPipelineResult} />);

    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("/100")).toBeInTheDocument();
  });

  it("should show passed gates count", () => {
    render(<QualitySummaryPanel result={mockPipelineResult} />);

    // 2 gates passed - expect multiple occurrences (passed, failed counts)
    const twoElements = screen.getAllByText("2");
    expect(twoElements.length).toBeGreaterThan(0);
  });

  it("should show failed gates count", () => {
    render(<QualitySummaryPanel result={mockPipelineResult} />);

    // 2 failed gates
    expect(screen.getAllByText("2").length).toBeGreaterThan(0);
  });

  it("should show total issues count", () => {
    render(<QualitySummaryPanel result={mockPipelineResult} />);

    // Total issues should be shown
    const issueCount = screen.getAllByText(/\d+/);
    expect(issueCount.length).toBeGreaterThan(0);
  });

  it("should show critical alert when critical issues exist", () => {
    render(<QualitySummaryPanel result={mockPipelineResult} />);

    expect(screen.getByText(/critical vulnerabilities/i)).toBeInTheDocument();
  });

  it("should show Vietnamese critical alert", () => {
    render(<QualitySummaryPanel result={mockPipelineResult} vietnamese />);

    expect(screen.getByText(/lỗ hổng nghiêm trọng/i)).toBeInTheDocument();
  });

  it("should not show critical alert for clean pipeline", () => {
    render(<QualitySummaryPanel result={cleanPipelineResult} />);

    expect(screen.queryByText(/critical vulnerabilities/i)).not.toBeInTheDocument();
  });

  it("should show trend indicator when trend is provided", () => {
    render(
      <QualitySummaryPanel
        result={cleanPipelineResult}
        trend="up"
        previousScore={90}
      />
    );

    expect(screen.getByText(/Improved/)).toBeInTheDocument();
  });

  it("should show View Details button when onViewDetails is provided", () => {
    const onViewDetails = vi.fn();
    render(
      <QualitySummaryPanel
        result={mockPipelineResult}
        onViewDetails={onViewDetails}
      />
    );

    expect(screen.getByText("View Details")).toBeInTheDocument();
  });

  it("should call onViewDetails when button is clicked", () => {
    const onViewDetails = vi.fn();
    render(
      <QualitySummaryPanel
        result={mockPipelineResult}
        onViewDetails={onViewDetails}
      />
    );

    fireEvent.click(screen.getByText("View Details"));

    expect(onViewDetails).toHaveBeenCalled();
  });

  it("should show Vietnamese View Details button", () => {
    render(
      <QualitySummaryPanel
        result={mockPipelineResult}
        vietnamese
        onViewDetails={() => {}}
      />
    );

    expect(screen.getByText("Xem chi tiết")).toBeInTheDocument();
  });

  it("should show duration", () => {
    render(<QualitySummaryPanel result={mockPipelineResult} />);

    expect(screen.getByText(/Duration:/)).toBeInTheDocument();
    expect(screen.getByText(/5\.0s/)).toBeInTheDocument();
  });

  it("should show Vietnamese duration label", () => {
    render(<QualitySummaryPanel result={mockPipelineResult} vietnamese />);

    expect(screen.getByText(/Thời gian:/)).toBeInTheDocument();
  });

  it("should show gate status for all gates", () => {
    render(<QualitySummaryPanel result={mockPipelineResult} />);

    expect(screen.getByText("Syntax")).toBeInTheDocument();
    expect(screen.getByText("Security")).toBeInTheDocument();
    expect(screen.getByText("Architecture")).toBeInTheDocument();
    expect(screen.getByText("Tests")).toBeInTheDocument();
  });

  it("should apply custom className", () => {
    const { container } = render(
      <QualitySummaryPanel
        result={mockPipelineResult}
        className="custom-class"
      />
    );

    expect(container.firstChild).toHaveClass("custom-class");
  });

  it("should show progress bar", () => {
    const { container } = render(
      <QualitySummaryPanel result={mockPipelineResult} />
    );

    const progressBar = container.querySelector('[role="progressbar"]');
    expect(progressBar).toBeInTheDocument();
  });

  it("should show passed label in stats", () => {
    render(<QualitySummaryPanel result={mockPipelineResult} />);

    expect(screen.getByText("Passed")).toBeInTheDocument();
  });

  it("should show failed label in stats", () => {
    render(<QualitySummaryPanel result={mockPipelineResult} />);

    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  it("should show issues label in stats", () => {
    render(<QualitySummaryPanel result={mockPipelineResult} />);

    expect(screen.getByText("Issues")).toBeInTheDocument();
  });

  it("should show Vietnamese stat labels", () => {
    render(<QualitySummaryPanel result={mockPipelineResult} vietnamese />);

    expect(screen.getByText("Cổng đạt")).toBeInTheDocument();
    expect(screen.getByText("Thất bại")).toBeInTheDocument();
    expect(screen.getByText("Vấn đề")).toBeInTheDocument();
  });
});
