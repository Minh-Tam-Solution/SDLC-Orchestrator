/**
 * =========================================================================
 * FileIssuesList Tests - Sprint 55 Day 3
 * SDLC Orchestrator
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * =========================================================================
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FileIssuesList, getFileIssues } from "./FileIssuesList";
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
      passed: false,
      status: "failed",
      durationMs: 1500,
      details: {
        passed: false,
        issues: [
          {
            file: "src/main.py",
            line: 150,
            rule: "no-circular-import",
            message: "Circular import detected",
            vietnameseMessage: "Phát hiện import vòng tròn",
          },
        ],
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
// getFileIssues Tests
// ============================================================================

describe("getFileIssues", () => {
  it("should extract all issues for a specific file", () => {
    const issues = getFileIssues("src/main.py", mockPipelineResult);

    expect(issues.length).toBe(5); // 2 syntax + 2 security + 1 architecture
  });

  it("should assign correct gate to each issue", () => {
    const issues = getFileIssues("src/main.py", mockPipelineResult);

    const syntaxIssues = issues.filter((i) => i.gate === "syntax");
    const securityIssues = issues.filter((i) => i.gate === "security");
    const architectureIssues = issues.filter((i) => i.gate === "architecture");

    expect(syntaxIssues.length).toBe(2);
    expect(securityIssues.length).toBe(2);
    expect(architectureIssues.length).toBe(1);
  });

  it("should include severity for security issues", () => {
    const issues = getFileIssues("src/main.py", mockPipelineResult);
    const securityIssues = issues.filter((i) => i.gate === "security");

    expect(securityIssues[0].severity).toBe("critical");
    expect(securityIssues[1].severity).toBe("high");
  });

  it("should include fix suggestion when available", () => {
    const issues = getFileIssues("src/main.py", mockPipelineResult);
    const criticalIssue = issues.find((i) => i.severity === "critical");

    expect(criticalIssue?.fixSuggestion).toBe("Use parameterized queries");
  });

  it("should return empty array for file with no issues", () => {
    const issues = getFileIssues("src/clean.py", mockPipelineResult);
    expect(issues.length).toBe(0);
  });

  it("should include line and column information", () => {
    const issues = getFileIssues("src/main.py", mockPipelineResult);
    const syntaxIssue = issues.find((i) => i.gate === "syntax");

    expect(syntaxIssue?.line).toBe(10);
    expect(syntaxIssue?.column).toBe(5);
  });

  it("should include rule/ruleId information", () => {
    const issues = getFileIssues("src/main.py", mockPipelineResult);
    const securityIssue = issues.find((i) => i.ruleId === "sql-injection");
    const archIssue = issues.find((i) => i.rule === "no-circular-import");

    expect(securityIssue).toBeDefined();
    expect(archIssue).toBeDefined();
  });
});

// ============================================================================
// FileIssuesList Component Tests
// ============================================================================

describe("FileIssuesList", () => {
  it("should render all issues grouped by gate", () => {
    render(
      <FileIssuesList file="src/main.py" pipelineResult={mockPipelineResult} />
    );

    // Should show gate section headers
    expect(screen.getAllByText(/Syntax/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Security/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Architecture/i).length).toBeGreaterThan(0);
  });

  it("should show issue count in header", () => {
    render(
      <FileIssuesList file="src/main.py" pipelineResult={mockPipelineResult} />
    );

    expect(screen.getByText("5 issues")).toBeInTheDocument();
  });

  it("should show Vietnamese text when vietnamese prop is true", () => {
    render(
      <FileIssuesList
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        vietnamese
      />
    );

    expect(screen.getByText("5 vấn đề")).toBeInTheDocument();
    expect(screen.getAllByText(/Cú pháp/i).length).toBeGreaterThan(0);
  });

  it("should show empty state for file with no issues", () => {
    render(
      <FileIssuesList
        file="src/clean.py"
        pipelineResult={cleanFilePipelineResult}
      />
    );

    expect(screen.getByText("No issues found in this file")).toBeInTheDocument();
  });

  it("should show Vietnamese empty state", () => {
    render(
      <FileIssuesList
        file="src/clean.py"
        pipelineResult={cleanFilePipelineResult}
        vietnamese
      />
    );

    expect(
      screen.getByText("Không có vấn đề nào trong file này")
    ).toBeInTheDocument();
  });

  it("should show line numbers for issues", () => {
    render(
      <FileIssuesList file="src/main.py" pipelineResult={mockPipelineResult} />
    );

    // Multiple lines may match /Line 10/ pattern (10, 100, etc)
    expect(screen.getAllByText(/Line 10/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Line 50/).length).toBeGreaterThan(0);
  });

  it("should show severity badges for security issues", () => {
    render(
      <FileIssuesList file="src/main.py" pipelineResult={mockPipelineResult} />
    );

    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
  });

  it("should show fix suggestions when available", () => {
    render(
      <FileIssuesList file="src/main.py" pipelineResult={mockPipelineResult} />
    );

    expect(screen.getByText("Use parameterized queries")).toBeInTheDocument();
  });

  it("should call onLineClick when line is clicked", () => {
    const onLineClick = vi.fn();
    render(
      <FileIssuesList
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        onLineClick={onLineClick}
      />
    );

    // Use getAllByText and click the first match
    const lineButtons = screen.getAllByText(/Line 10/);
    fireEvent.click(lineButtons[0]);

    expect(onLineClick).toHaveBeenCalled();
  });

  it("should show filter controls when showFilters is true", () => {
    render(
      <FileIssuesList
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        showFilters
      />
    );

    expect(screen.getByText("Filter")).toBeInTheDocument();
  });

  it("should collapse sections when defaultCollapsed is true", () => {
    render(
      <FileIssuesList
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        defaultCollapsed
      />
    );

    // Issues should not be in the document when collapsed
    expect(screen.queryByText("Invalid syntax")).not.toBeInTheDocument();
  });

  it("should toggle section when header is clicked", () => {
    render(
      <FileIssuesList
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        defaultCollapsed
      />
    );

    // Find and click the Syntax section header
    const syntaxButtons = screen.getAllByRole("button");
    const syntaxHeader = syntaxButtons.find((btn) =>
      btn.textContent?.includes("Syntax") || btn.textContent?.includes("Cú pháp")
    );

    if (syntaxHeader) {
      fireEvent.click(syntaxHeader);
    }

    // Issue should now be visible
    expect(screen.getByText("Invalid syntax")).toBeVisible();
  });

  it("should show severity summary in security section header", () => {
    render(
      <FileIssuesList file="src/main.py" pipelineResult={mockPipelineResult} />
    );

    // Security section should show critical and high counts
    expect(screen.getByText(/1 critical/)).toBeInTheDocument();
    expect(screen.getByText(/1 high/)).toBeInTheDocument();
  });

  it("should filter issues by gate when gateFilter is set", () => {
    render(
      <FileIssuesList
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        gateFilter={["security"]}
      />
    );

    // Should show only security issues (2 out of 5)
    expect(screen.getByText("2/5 issues")).toBeInTheDocument();
  });

  it("should filter issues by severity when severityFilter is set", () => {
    render(
      <FileIssuesList
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        severityFilter={["critical"]}
      />
    );

    // Should show only critical issues (1 out of 5)
    expect(screen.getByText("1/5 issues")).toBeInTheDocument();
  });

  it("should show filtered empty state when no issues match filter", () => {
    render(
      <FileIssuesList
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        severityFilter={["low"]}
      />
    );

    expect(
      screen.getByText("No issues match the current filters")
    ).toBeInTheDocument();
  });

  it("should show Vietnamese messages for issues when vietnamese is true", () => {
    render(
      <FileIssuesList
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        vietnamese
      />
    );

    expect(screen.getByText("Cú pháp không hợp lệ")).toBeInTheDocument();
    expect(screen.getByText("Lỗ hổng SQL injection")).toBeInTheDocument();
  });

  it("should show ruleId for security issues", () => {
    render(
      <FileIssuesList file="src/main.py" pipelineResult={mockPipelineResult} />
    );

    expect(screen.getByText("sql-injection")).toBeInTheDocument();
  });

  it("should show rule for architecture issues", () => {
    render(
      <FileIssuesList file="src/main.py" pipelineResult={mockPipelineResult} />
    );

    expect(screen.getByText("no-circular-import")).toBeInTheDocument();
  });
});
