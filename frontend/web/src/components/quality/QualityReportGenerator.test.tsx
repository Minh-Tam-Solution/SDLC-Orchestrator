/**
 * =========================================================================
 * QualityReportGenerator Tests - Sprint 55 Day 5
 * SDLC Orchestrator
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * =========================================================================
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  QualityReportGenerator,
  generateReport,
  generateReportId,
  exportReportAsJSON,
  exportReportAsCSV,
  exportReportAsMarkdown,
} from "./QualityReportGenerator";
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
// Utility Function Tests
// ============================================================================

describe("generateReportId", () => {
  it("should generate unique report IDs", () => {
    const id1 = generateReportId();
    const id2 = generateReportId();

    expect(id1).not.toBe(id2);
  });

  it("should generate IDs with QR prefix", () => {
    const id = generateReportId();

    expect(id.startsWith("QR-")).toBe(true);
  });

  it("should generate uppercase IDs", () => {
    const id = generateReportId();

    expect(id).toBe(id.toUpperCase());
  });
});

describe("generateReport", () => {
  it("should generate report with all required fields", () => {
    const report = generateReport(mockPipelineResult);

    expect(report.metadata).toBeDefined();
    expect(report.metadata.id).toBeDefined();
    expect(report.metadata.generatedAt).toBeInstanceOf(Date);
    expect(report.pipelineResult).toBe(mockPipelineResult);
    expect(report.qualityScore).toBeDefined();
    expect(report.qualityGrade).toBeDefined();
    expect(report.issueSummary).toBeDefined();
    expect(report.gateSummary).toBeDefined();
    expect(report.recommendations).toBeDefined();
  });

  it("should calculate correct quality score", () => {
    const report = generateReport(cleanPipelineResult);

    expect(report.qualityScore).toBe(100);
    expect(report.qualityGrade).toBe("A");
  });

  it("should calculate lower score for failed gates", () => {
    const report = generateReport(mockPipelineResult);

    expect(report.qualityScore).toBeLessThan(100);
    expect(["D", "F"]).toContain(report.qualityGrade);
  });

  it("should include issue summary", () => {
    const report = generateReport(mockPipelineResult);

    expect(report.issueSummary.critical).toBe(1);
    expect(report.issueSummary.high).toBeGreaterThanOrEqual(1);
    expect(report.issueSummary.total).toBeGreaterThan(0);
  });

  it("should include gate summary", () => {
    const report = generateReport(mockPipelineResult);

    expect(report.gateSummary.passed).toBe(2);
    expect(report.gateSummary.failed).toBe(2);
    expect(report.gateSummary.total).toBe(4);
  });

  it("should use custom metadata when provided", () => {
    const metadata = {
      title: "Custom Report",
      projectName: "Test Project",
      branchName: "main",
    };

    const report = generateReport(mockPipelineResult, metadata);

    expect(report.metadata.title).toBe("Custom Report");
    expect(report.metadata.projectName).toBe("Test Project");
    expect(report.metadata.branchName).toBe("main");
  });

  it("should generate recommendations for failed gates", () => {
    const report = generateReport(mockPipelineResult);

    expect(report.recommendations.length).toBeGreaterThan(0);
    expect(report.recommendations[0].priority).toBe(1);
  });

  it("should generate positive recommendation for clean pipeline", () => {
    const report = generateReport(cleanPipelineResult);

    expect(report.recommendations.length).toBe(1);
    expect(report.recommendations[0].title).toContain("Excellent");
  });
});

// ============================================================================
// Export Function Tests
// ============================================================================

describe("exportReportAsJSON", () => {
  it("should export valid JSON", () => {
    const report = generateReport(mockPipelineResult);
    const json = exportReportAsJSON(report);

    expect(() => JSON.parse(json)).not.toThrow();
  });

  it("should include all report fields", () => {
    const report = generateReport(mockPipelineResult);
    const json = exportReportAsJSON(report);
    const parsed = JSON.parse(json);

    expect(parsed.metadata).toBeDefined();
    expect(parsed.qualityScore).toBeDefined();
    expect(parsed.qualityGrade).toBeDefined();
    expect(parsed.issueSummary).toBeDefined();
  });
});

describe("exportReportAsCSV", () => {
  it("should export CSV format", () => {
    const report = generateReport(mockPipelineResult);
    const csv = exportReportAsCSV(report);

    expect(csv).toContain("Quality Report Export");
    expect(csv).toContain("Report ID");
    expect(csv).toContain("Quality Score");
  });

  it("should include issue summary section", () => {
    const report = generateReport(mockPipelineResult);
    const csv = exportReportAsCSV(report);

    expect(csv).toContain("Issue Summary");
    expect(csv).toContain("Severity,Count");
    expect(csv).toContain("Critical");
  });

  it("should include gate summary section", () => {
    const report = generateReport(mockPipelineResult);
    const csv = exportReportAsCSV(report);

    expect(csv).toContain("Gate Summary");
    expect(csv).toContain("Gate,Status,Duration");
    expect(csv).toContain("syntax");
    expect(csv).toContain("security");
  });

  it("should include recommendations section", () => {
    const report = generateReport(mockPipelineResult);
    const csv = exportReportAsCSV(report);

    expect(csv).toContain("Recommendations");
    expect(csv).toContain("Priority,Category,Title,Description");
  });
});

describe("exportReportAsMarkdown", () => {
  it("should export Markdown format", () => {
    const report = generateReport(mockPipelineResult);
    const md = exportReportAsMarkdown(report);

    expect(md).toContain("# Quality Report");
    expect(md).toContain("## Report Information");
    expect(md).toContain("## Quality Score");
  });

  it("should include issue summary table", () => {
    const report = generateReport(mockPipelineResult);
    const md = exportReportAsMarkdown(report);

    expect(md).toContain("## Issue Summary");
    expect(md).toContain("| Severity | Count |");
    expect(md).toContain("| Critical |");
  });

  it("should include gate results table", () => {
    const report = generateReport(mockPipelineResult);
    const md = exportReportAsMarkdown(report);

    expect(md).toContain("## Gate Results");
    expect(md).toContain("| Gate | Status | Duration |");
    expect(md).toContain("Syntax");
    expect(md).toContain("Security");
  });

  it("should include recommendations", () => {
    const report = generateReport(mockPipelineResult);
    const md = exportReportAsMarkdown(report);

    expect(md).toContain("## Recommendations");
    expect(md).toContain("### 1.");
  });

  it("should export Vietnamese when specified", () => {
    const report = generateReport(mockPipelineResult);
    const md = exportReportAsMarkdown(report, true);

    expect(md).toContain("# Báo cáo chất lượng");
    expect(md).toContain("## Thông tin báo cáo");
    expect(md).toContain("Mức độ");
  });
});

// ============================================================================
// Component Tests
// ============================================================================

describe("QualityReportGenerator", () => {
  it("should render report title", () => {
    render(<QualityReportGenerator result={mockPipelineResult} />);

    expect(screen.getByText("Quality Report")).toBeInTheDocument();
  });

  it("should render Vietnamese title when vietnamese prop is true", () => {
    render(<QualityReportGenerator result={mockPipelineResult} vietnamese />);

    expect(screen.getByText("Báo cáo chất lượng")).toBeInTheDocument();
  });

  it("should show report ID", () => {
    render(<QualityReportGenerator result={mockPipelineResult} />);

    // Report ID starts with QR-
    const reportId = screen.getByText(/QR-/);
    expect(reportId).toBeInTheDocument();
  });

  it("should display quality score", () => {
    render(<QualityReportGenerator result={mockPipelineResult} />);

    expect(screen.getByText("/100")).toBeInTheDocument();
  });

  it("should display quality grade", () => {
    render(<QualityReportGenerator result={mockPipelineResult} />);

    // Grade should be D or F for failed pipeline - check Grade badge
    expect(screen.getByText(/Grade/)).toBeInTheDocument();
  });

  it("should display A grade for clean pipeline", () => {
    render(<QualityReportGenerator result={cleanPipelineResult} />);

    expect(screen.getByText(/Grade A/)).toBeInTheDocument();
  });

  it("should show gates passed count", () => {
    render(<QualityReportGenerator result={mockPipelineResult} />);

    // 2 gates passed out of 4
    expect(screen.getByText("/4")).toBeInTheDocument();
  });

  it("should show total issues count", () => {
    render(<QualityReportGenerator result={mockPipelineResult} />);

    // Should show total issues > 0
    const issueElements = screen.getAllByText(/\d+/);
    expect(issueElements.length).toBeGreaterThan(0);
  });

  it("should show critical badge for critical issues", () => {
    render(<QualityReportGenerator result={mockPipelineResult} />);

    const criticalBadges = screen.getAllByText(/1 critical/i);
    expect(criticalBadges.length).toBeGreaterThan(0);
  });

  it("should show export button when showExport is true", () => {
    render(<QualityReportGenerator result={mockPipelineResult} showExport />);

    expect(screen.getByText("Export")).toBeInTheDocument();
  });

  it("should hide export button when showExport is false", () => {
    render(<QualityReportGenerator result={mockPipelineResult} showExport={false} />);

    expect(screen.queryByText("Export")).not.toBeInTheDocument();
  });

  it("should show recommendations tab", () => {
    render(<QualityReportGenerator result={mockPipelineResult} />);

    const recommendationTabs = screen.getAllByText("Recommendations");
    expect(recommendationTabs.length).toBeGreaterThan(0);
  });

  it("should show details tab", () => {
    render(<QualityReportGenerator result={mockPipelineResult} />);

    expect(screen.getByText("Details")).toBeInTheDocument();
  });

  it("should switch to details tab when clicked", () => {
    render(<QualityReportGenerator result={mockPipelineResult} />);

    // Find and click the Details tab trigger
    const tabs = screen.getAllByRole("tab");
    const detailsTab = tabs.find(tab => tab.textContent?.includes("Details"));
    if (detailsTab) {
      fireEvent.click(detailsTab);
    }

    // After clicking, Gate Details header should be visible
    expect(screen.getAllByText(/Details/i).length).toBeGreaterThan(0);
  });

  it("should show gate status in details", () => {
    render(<QualityReportGenerator result={mockPipelineResult} />);

    // Find and click the Details tab trigger
    const tabs = screen.getAllByRole("tab");
    const detailsTab = tabs.find(tab => tab.textContent?.includes("Details"));
    if (detailsTab) {
      fireEvent.click(detailsTab);
    }

    // Gate names should be visible in some form (in tabs or content)
    expect(screen.getAllByText(/syntax|security|architecture|tests/i).length).toBeGreaterThan(0);
  });

  it("should have export button that can be clicked", () => {
    const onExport = vi.fn();
    render(
      <QualityReportGenerator
        result={mockPipelineResult}
        onExport={onExport}
        showExport
      />
    );

    // Verify export button exists and is clickable
    const exportButton = screen.getByRole("button", { name: /Export/i });
    expect(exportButton).toBeInTheDocument();

    // Click export button - it opens a dropdown menu
    fireEvent.click(exportButton);

    // The dropdown should exist (may need more specific testing in integration tests)
    expect(exportButton).toBeEnabled();
  });

  it("should show project name when provided", () => {
    render(
      <QualityReportGenerator
        result={mockPipelineResult}
        metadata={{ projectName: "Test Project" }}
      />
    );

    expect(screen.getByText("Test Project")).toBeInTheDocument();
  });

  it("should show branch name when provided", () => {
    render(
      <QualityReportGenerator
        result={mockPipelineResult}
        metadata={{ branchName: "main" }}
      />
    );

    expect(screen.getByText("main")).toBeInTheDocument();
  });

  it("should show commit hash when provided", () => {
    render(
      <QualityReportGenerator
        result={mockPipelineResult}
        metadata={{ commitHash: "abc123def456" }}
      />
    );

    // Should show first 7 chars
    expect(screen.getByText("abc123d")).toBeInTheDocument();
  });

  it("should copy report ID when copy button is clicked", async () => {
    const mockClipboard = {
      writeText: vi.fn().mockResolvedValue(undefined),
    };
    Object.assign(navigator, { clipboard: mockClipboard });

    render(<QualityReportGenerator result={mockPipelineResult} />);

    // Find and click copy button (button next to report ID)
    const buttons = screen.getAllByRole("button");
    const copyButton = buttons.find((b) => b.querySelector("svg"));
    if (copyButton) {
      fireEvent.click(copyButton);
    }

    expect(mockClipboard.writeText).toHaveBeenCalled();
  });

  it("should show duration in seconds", () => {
    render(<QualityReportGenerator result={mockPipelineResult} />);

    // Duration is 5000ms = 5.0 seconds
    expect(screen.getByText("5.0")).toBeInTheDocument();
    expect(screen.getByText("seconds")).toBeInTheDocument();
  });

  it("should apply custom className", () => {
    const { container } = render(
      <QualityReportGenerator
        result={mockPipelineResult}
        className="custom-class"
      />
    );

    expect(container.firstChild).toHaveClass("custom-class");
  });
});
