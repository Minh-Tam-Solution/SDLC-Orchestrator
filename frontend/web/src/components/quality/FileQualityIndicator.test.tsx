/**
 * =========================================================================
 * FileQualityIndicator Tests - Sprint 55 Day 3
 * SDLC Orchestrator
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * =========================================================================
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  FileQualityIndicator,
  FileQualityList,
  getFileQualityStatus,
  getFilesWithIssues,
  type FileQualityStatus,
} from "./FileQualityIndicator";
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
          {
            file: "src/utils.py",
            line: 5,
            column: 1,
            message: "Unexpected indent",
            vietnameseMessage: "Thụt đầu dòng không mong đợi",
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
        highCount: 2,
        mediumCount: 1,
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
            file: "src/auth.py",
            line: 15,
            ruleId: "weak-password",
            severity: "high" as const,
            message: "Weak password validation",
            vietnameseMessage: "Xác thực mật khẩu yếu",
          },
          {
            file: "src/main.py",
            line: 100,
            ruleId: "xss",
            severity: "high" as const,
            message: "XSS vulnerability",
            vietnameseMessage: "Lỗ hổng XSS",
          },
          {
            file: "src/utils.py",
            line: 30,
            ruleId: "insecure-random",
            severity: "medium" as const,
            message: "Insecure random number generator",
            vietnameseMessage: "Bộ tạo số ngẫu nhiên không an toàn",
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
// getFileQualityStatus Tests
// ============================================================================

describe("getFileQualityStatus", () => {
  it("should return correct status for file with multiple issues", () => {
    const status = getFileQualityStatus("src/main.py", mockPipelineResult);

    expect(status.file).toBe("src/main.py");
    expect(status.hasIssues).toBe(true);
    expect(status.issueCount).toBe(4); // 2 syntax + 2 security
    expect(status.highestSeverity).toBe("critical");
    expect(status.issuesByGate.syntax).toBe(2);
    expect(status.issuesByGate.security).toBe(2);
    expect(status.securitySeverities.critical).toBe(1);
    expect(status.securitySeverities.high).toBe(1);
  });

  it("should return correct status for file with no issues", () => {
    const status = getFileQualityStatus("src/clean.py", mockPipelineResult);

    expect(status.file).toBe("src/clean.py");
    expect(status.hasIssues).toBe(false);
    expect(status.issueCount).toBe(0);
    expect(status.highestSeverity).toBeNull();
  });

  it("should track security severities correctly", () => {
    const status = getFileQualityStatus("src/utils.py", mockPipelineResult);

    expect(status.issuesByGate.syntax).toBe(1);
    expect(status.issuesByGate.security).toBe(1);
    expect(status.securitySeverities.medium).toBe(1);
  });
});

// ============================================================================
// getFilesWithIssues Tests
// ============================================================================

describe("getFilesWithIssues", () => {
  it("should return all files with issues", () => {
    const files = getFilesWithIssues(mockPipelineResult);

    expect(files.length).toBe(3);
    expect(files.map((f) => f.file)).toContain("src/main.py");
    expect(files.map((f) => f.file)).toContain("src/utils.py");
    expect(files.map((f) => f.file)).toContain("src/auth.py");
  });

  it("should sort files by severity (critical first)", () => {
    const files = getFilesWithIssues(mockPipelineResult);

    // src/main.py has critical issue, should be first
    expect(files[0].file).toBe("src/main.py");
    expect(files[0].highestSeverity).toBe("critical");
  });

  it("should return empty array for clean pipeline", () => {
    const files = getFilesWithIssues(cleanPipelineResult);
    expect(files.length).toBe(0);
  });
});

// ============================================================================
// FileQualityIndicator Component Tests
// ============================================================================

describe("FileQualityIndicator", () => {
  it("should render with pipeline result", () => {
    render(
      <FileQualityIndicator
        file="src/main.py"
        pipelineResult={mockPipelineResult}
      />
    );

    expect(screen.getByText(/4 issues/)).toBeInTheDocument();
  });

  it("should render with pre-computed status", () => {
    const status: FileQualityStatus = {
      file: "test.py",
      hasIssues: true,
      issueCount: 5,
      highestSeverity: "high",
      issuesByGate: { syntax: 2, security: 3, architecture: 0, tests: 0 },
      securitySeverities: { critical: 0, high: 2, medium: 1, low: 0 },
    };

    render(<FileQualityIndicator file="test.py" status={status} />);

    expect(screen.getByText(/5 issues/)).toBeInTheDocument();
  });

  it("should show 'Passed' for file with no issues", () => {
    render(
      <FileQualityIndicator
        file="src/clean.py"
        pipelineResult={cleanPipelineResult}
      />
    );

    expect(screen.getByText("Passed")).toBeInTheDocument();
  });

  it("should show Vietnamese text when vietnamese prop is true", () => {
    render(
      <FileQualityIndicator
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        vietnamese
      />
    );

    expect(screen.getByText(/4 vấn đề/)).toBeInTheDocument();
  });

  it("should render compact mode with icon only", () => {
    render(
      <FileQualityIndicator
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        compact
        showCount
      />
    );

    // Should show count but in compact form
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("should call onClick when clicked", () => {
    const onClick = vi.fn();
    render(
      <FileQualityIndicator
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        onClick={onClick}
      />
    );

    const button = screen.getByRole("button");
    fireEvent.click(button);

    expect(onClick).toHaveBeenCalledWith("src/main.py");
  });

  it("should show gate breakdown when showGates is true", () => {
    render(
      <FileQualityIndicator
        file="src/main.py"
        pipelineResult={mockPipelineResult}
        showGates
      />
    );

    // Should show gate badges (multiple elements with count "2")
    expect(screen.getAllByText("2").length).toBeGreaterThan(0);
  });

  it("should show 'Not checked' when no status or pipeline result", () => {
    render(<FileQualityIndicator file="src/unknown.py" />);

    expect(screen.getByText("Not checked")).toBeInTheDocument();
  });

  it("should show Vietnamese 'Not checked' text", () => {
    render(<FileQualityIndicator file="src/unknown.py" vietnamese />);

    expect(screen.getByText("Chưa kiểm tra")).toBeInTheDocument();
  });
});

// ============================================================================
// FileQualityList Component Tests
// ============================================================================

describe("FileQualityList", () => {
  const files = ["src/main.py", "src/utils.py", "src/auth.py", "src/clean.py"];

  it("should render list of files with quality indicators", () => {
    render(
      <FileQualityList files={files} pipelineResult={mockPipelineResult} />
    );

    expect(screen.getByText("main.py")).toBeInTheDocument();
    expect(screen.getByText("utils.py")).toBeInTheDocument();
    expect(screen.getByText("auth.py")).toBeInTheDocument();
  });

  it("should highlight selected file", () => {
    render(
      <FileQualityList
        files={files}
        pipelineResult={mockPipelineResult}
        selectedFile="src/main.py"
      />
    );

    const selectedItem = screen.getByText("main.py").closest("div[role='button']");
    expect(selectedItem).toHaveClass("bg-blue-50");
  });

  it("should call onFileSelect when file is clicked", () => {
    const onFileSelect = vi.fn();
    render(
      <FileQualityList
        files={files}
        pipelineResult={mockPipelineResult}
        onFileSelect={onFileSelect}
      />
    );

    fireEvent.click(screen.getByText("main.py"));
    expect(onFileSelect).toHaveBeenCalledWith("src/main.py");
  });

  it("should filter to show only files with issues when showOnlyIssues is true", () => {
    render(
      <FileQualityList
        files={files}
        pipelineResult={mockPipelineResult}
        showOnlyIssues
      />
    );

    expect(screen.getByText("main.py")).toBeInTheDocument();
    expect(screen.queryByText("clean.py")).not.toBeInTheDocument();
  });

  it("should sort files by severity", () => {
    const { container } = render(
      <FileQualityList files={files} pipelineResult={mockPipelineResult} />
    );

    const fileNames = container.querySelectorAll("span.truncate");
    // First file should be main.py (has critical issue)
    expect(fileNames[0].textContent).toBe("main.py");
  });

  it("should show empty message when no files match filter", () => {
    render(
      <FileQualityList
        files={["src/clean.py"]}
        pipelineResult={cleanPipelineResult}
        showOnlyIssues
      />
    );

    expect(screen.getByText("No files with issues")).toBeInTheDocument();
  });

  it("should show Vietnamese empty message", () => {
    render(
      <FileQualityList
        files={["src/clean.py"]}
        pipelineResult={cleanPipelineResult}
        showOnlyIssues
        vietnamese
      />
    );

    expect(screen.getByText("Không có file nào có vấn đề")).toBeInTheDocument();
  });
});
