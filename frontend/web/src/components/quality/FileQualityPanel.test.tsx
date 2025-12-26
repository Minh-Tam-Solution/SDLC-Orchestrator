/**
 * =========================================================================
 * FileQualityPanel Tests - Sprint 55 Day 3
 * SDLC Orchestrator
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * =========================================================================
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FileQualityPanel, FileQualityCard } from "./FileQualityPanel";
import type { PipelineResult } from "@/types/quality";

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
          {
            file: "src/main.py",
            line: 25,
            column: 10,
            message: "Missing colon",
            vietnameseMessage: "Thiếu dấu hai chấm",
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
            fixSuggestion: "Use parameterized queries",
          },
          {
            file: "src/main.py",
            line: 100,
            ruleId: "xss",
            severity: "high" as const,
            message: "XSS vulnerability",
            vietnameseMessage: "Lỗ hổng XSS",
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

const cleanFilePipelineResult: PipelineResult = {
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
// FileQualityPanel Tests
// ============================================================================

describe("FileQualityPanel", () => {
  it("should render file name and path", () => {
    render(
      <FileQualityPanel
        file="src/main.py"
        pipelineResult={mockPipelineResult}
      />
    );

    expect(screen.getByText("main.py")).toBeInTheDocument();
    expect(screen.getByText("src/main.py")).toBeInTheDocument();
  });

  it("should display quality score", () => {
    render(
      <FileQualityPanel
        file="src/main.py"
        pipelineResult={mockPipelineResult}
      />
    );

    // Score should be displayed
    expect(screen.getByText("/100")).toBeInTheDocument();
  });

  it("should display grade letter", () => {
    render(
      <FileQualityPanel
        file="src/main.py"
        pipelineResult={mockPipelineResult}
      />
    );

    // Grade letter should be visible (A, B, C, D, or F)
    const grades = ["A", "B", "C", "D", "F"];
    const hasGrade = grades.some((g) =>
      screen.queryAllByText(g).length > 0
    );
    expect(hasGrade).toBe(true);
  });

  it("should show gate results section", () => {
    render(
      <FileQualityPanel
        file="src/main.py"
        pipelineResult={mockPipelineResult}
      />
    );

    expect(screen.getByText("Gate Results")).toBeInTheDocument();
  });

  it("should show Vietnamese labels when vietnamese is true", () => {
    render(
      <FileQualityPanel
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        vietnamese
      />
    );

    expect(screen.getByText("Kết quả theo cổng")).toBeInTheDocument();
  });

  it("should show passed gates with check icon", () => {
    render(
      <FileQualityPanel
        file="src/main.py"
        pipelineResult={mockPipelineResult}
      />
    );

    // Architecture gate passed
    expect(screen.getAllByText("Passed").length).toBeGreaterThan(0);
  });

  it("should show failed gates with issue count", () => {
    render(
      <FileQualityPanel
        file="src/main.py"
        pipelineResult={mockPipelineResult}
      />
    );

    // Syntax and Security gates failed - multiple elements may have "2 issues"
    expect(screen.getAllByText(/2 (issues|lỗi)/).length).toBeGreaterThan(0);
  });

  it("should show security severity breakdown when security issues exist", () => {
    render(
      <FileQualityPanel
        file="src/main.py"
        pipelineResult={mockPipelineResult}
      />
    );

    expect(screen.getByText("Security Severity")).toBeInTheDocument();
    expect(screen.getAllByText(/critical/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/high/i).length).toBeGreaterThan(0);
  });

  it("should show issue details when showIssues is true", () => {
    render(
      <FileQualityPanel
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        showIssues
      />
    );

    expect(screen.getByText("Issue Details")).toBeInTheDocument();
    expect(screen.getByText("Invalid syntax")).toBeInTheDocument();
  });

  it("should hide issue details when showIssues is false", () => {
    render(
      <FileQualityPanel
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        showIssues={false}
      />
    );

    expect(screen.queryByText("Issue Details")).not.toBeInTheDocument();
  });

  it("should call onLineClick when issue line is clicked", () => {
    const onLineClick = vi.fn();
    render(
      <FileQualityPanel
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        onLineClick={onLineClick}
        showIssues
      />
    );

    // Multiple lines may match, use getAllByText
    const lineButtons = screen.getAllByText(/Line 10/);
    fireEvent.click(lineButtons[0]);

    expect(onLineClick).toHaveBeenCalled();
  });

  it("should show no issues state for clean file", () => {
    render(
      <FileQualityPanel
        file="src/clean.py"
        pipelineResult={cleanFilePipelineResult}
      />
    );

    expect(screen.getByText("This file has no issues")).toBeInTheDocument();
    expect(screen.getByText("All quality checks passed")).toBeInTheDocument();
  });

  it("should show Vietnamese no issues state", () => {
    render(
      <FileQualityPanel
        file="src/clean.py"
        pipelineResult={cleanFilePipelineResult}
        vietnamese
      />
    );

    expect(screen.getByText("File này không có vấn đề")).toBeInTheDocument();
    expect(
      screen.getByText("Tất cả các kiểm tra chất lượng đã đạt")
    ).toBeInTheDocument();
  });

  it("should show A grade for clean file", () => {
    render(
      <FileQualityPanel
        file="src/clean.py"
        pipelineResult={cleanFilePipelineResult}
      />
    );

    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("Excellent")).toBeInTheDocument();
  });

  it("should apply maxHeight style when provided", () => {
    const { container } = render(
      <FileQualityPanel
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        maxHeight="400px"
      />
    );

    const content = container.querySelector("[class*='overflow-y-auto']");
    expect(content).toHaveStyle({ maxHeight: "400px" });
  });
});

// ============================================================================
// FileQualityCard Tests
// ============================================================================

describe("FileQualityCard", () => {
  it("should render file name and path", () => {
    render(
      <FileQualityCard file="src/main.py" pipelineResult={mockPipelineResult} />
    );

    expect(screen.getByText("main.py")).toBeInTheDocument();
    expect(screen.getByText("src/main.py")).toBeInTheDocument();
  });

  it("should show grade letter badge", () => {
    render(
      <FileQualityCard file="src/main.py" pipelineResult={mockPipelineResult} />
    );

    const grades = ["A", "B", "C", "D", "F"];
    const hasGrade = grades.some((g) => screen.queryAllByText(g).length > 0);
    expect(hasGrade).toBe(true);
  });

  it("should call onClick when clicked", () => {
    const onClick = vi.fn();
    render(
      <FileQualityCard
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        onClick={onClick}
      />
    );

    const card = screen.getByRole("button");
    fireEvent.click(card);

    expect(onClick).toHaveBeenCalledWith("src/main.py");
  });

  it("should highlight when selected", () => {
    render(
      <FileQualityCard
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        selected
      />
    );

    const card = screen.getByRole("button");
    expect(card).toHaveClass("bg-blue-50");
  });

  it("should show issue count badges per gate", () => {
    render(
      <FileQualityCard file="src/main.py" pipelineResult={mockPipelineResult} />
    );

    // Should show syntax and security issue counts (multiple "2" elements)
    expect(screen.getAllByText("2").length).toBeGreaterThan(0);
  });

  it("should show check icon for clean file", () => {
    render(
      <FileQualityCard
        file="src/clean.py"
        pipelineResult={cleanFilePipelineResult}
      />
    );

    // Should show A grade
    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("should show destructive badge for critical security issues", () => {
    const { container } = render(
      <FileQualityCard file="src/main.py" pipelineResult={mockPipelineResult} />
    );

    // Should have destructive variant badge for security
    const destructiveBadge = container.querySelector('[class*="destructive"]');
    expect(destructiveBadge).toBeInTheDocument();
  });

  it("should truncate long file paths", () => {
    render(
      <FileQualityCard
        file="src/very/long/path/to/some/deeply/nested/file.py"
        pipelineResult={cleanFilePipelineResult}
      />
    );

    const pathElement = screen.getByText(
      "src/very/long/path/to/some/deeply/nested/file.py"
    );
    expect(pathElement).toHaveClass("truncate");
  });

  it("should apply custom className", () => {
    render(
      <FileQualityCard
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        className="custom-class"
      />
    );

    const card = screen.getByRole("button");
    expect(card).toHaveClass("custom-class");
  });
});

// ============================================================================
// Score Calculation Tests
// ============================================================================

describe("Score Calculation", () => {
  it("should give perfect score for file with no issues", () => {
    render(
      <FileQualityPanel
        file="src/clean.py"
        pipelineResult={cleanFilePipelineResult}
      />
    );

    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("should penalize more heavily for critical security issues", () => {
    // File with critical issue should have lower score than file with only syntax issues
    render(
      <FileQualityPanel
        file="src/main.py"
        pipelineResult={mockPipelineResult}
      />
    );

    // Score should be significantly less than 100 due to critical issue
    // Look for the grade letter - should be D or F for file with critical issues
    const grades = ["D", "F"];
    const hasLowGrade = grades.some((g) =>
      screen.queryAllByText(g).length > 0
    );
    expect(hasLowGrade).toBe(true);
  });
});
