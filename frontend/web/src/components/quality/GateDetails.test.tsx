/**
 * Unit Tests: GateDetails Component
 * SDLC Orchestrator - Sprint 55 Day 1
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 *
 * Test coverage:
 * - Syntax gate details
 * - Security gate details
 * - Architecture gate details
 * - Test gate details
 * - File grouping
 * - Vietnamese mode
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@/test/test-utils";
import { GateDetails } from "./GateDetails";
import type { GateResult } from "@/types/quality";
import "@testing-library/jest-dom";

// ============================================================================
// Test Data - Syntax
// ============================================================================

const syntaxPassedResult: GateResult = {
  gateName: "syntax",
  passed: true,
  status: "passed",
  durationMs: 250,
  details: {
    passed: true,
    issues: [],
    filesChecked: 15,
    filesPassed: 15,
  },
};

const syntaxFailedResult: GateResult = {
  gateName: "syntax",
  passed: false,
  status: "failed",
  durationMs: 180,
  details: {
    passed: false,
    issues: [
      {
        file: "src/app.py",
        line: 10,
        column: 5,
        message: "SyntaxError: unexpected indent",
        vietnameseMessage: "Lỗi cú pháp: thụt lề không mong muốn",
      },
      {
        file: "src/app.py",
        line: 25,
        column: 1,
        message: "SyntaxError: invalid syntax",
        vietnameseMessage: "Lỗi cú pháp: cú pháp không hợp lệ",
      },
      {
        file: "src/utils.py",
        line: 5,
        column: 1,
        message: "SyntaxError: missing parenthesis",
        vietnameseMessage: "Lỗi cú pháp: thiếu dấu ngoặc",
      },
    ],
    filesChecked: 15,
    filesPassed: 13,
  },
};

// ============================================================================
// Test Data - Security
// ============================================================================

const securityPassedResult: GateResult = {
  gateName: "security",
  passed: true,
  status: "passed",
  durationMs: 500,
  details: {
    passed: true,
    issues: [],
    criticalCount: 0,
    highCount: 0,
    mediumCount: 0,
    lowCount: 0,
  },
};

const securityFailedResult: GateResult = {
  gateName: "security",
  passed: false,
  status: "failed",
  durationMs: 800,
  details: {
    passed: false,
    issues: [
      {
        file: "src/auth.py",
        line: 45,
        ruleId: "python.lang.security.dangerous-eval",
        message: "Avoid using eval() as it can lead to code injection",
        vietnameseMessage: "Tránh sử dụng eval() vì có thể dẫn đến code injection",
        severity: "critical" as const,
        fixSuggestion: "Use ast.literal_eval() instead",
      },
      {
        file: "src/api.py",
        line: 20,
        ruleId: "python.lang.security.hardcoded-secret",
        message: "Hardcoded secret detected",
        vietnameseMessage: "Phát hiện secret được mã hóa cứng",
        severity: "high" as const,
        fixSuggestion: "Use environment variables",
      },
      {
        file: "src/db.py",
        line: 30,
        ruleId: "python.lang.security.sql-injection",
        message: "Possible SQL injection vulnerability",
        vietnameseMessage: "Có thể có lỗ hổng SQL injection",
        severity: "medium" as const,
      },
    ],
    criticalCount: 1,
    highCount: 1,
    mediumCount: 1,
    lowCount: 0,
  },
};

// ============================================================================
// Test Data - Architecture
// ============================================================================

const architecturePassedResult: GateResult = {
  gateName: "architecture",
  passed: true,
  status: "passed",
  durationMs: 300,
  details: {
    passed: true,
    issues: [],
  },
};

const architectureFailedResult: GateResult = {
  gateName: "architecture",
  passed: false,
  status: "failed",
  durationMs: 350,
  details: {
    passed: false,
    issues: [
      {
        file: "src/routes/api.py",
        line: 5,
        rule: "layer-violation",
        message: "Routes should not import from models directly",
        vietnameseMessage: "Routes không nên import trực tiếp từ models",
      },
      {
        file: "src/services/user.py",
        line: 10,
        rule: "circular-import",
        message: "Circular import detected: user.py → auth.py → user.py",
        vietnameseMessage: "Phát hiện import vòng: user.py → auth.py → user.py",
      },
    ],
  },
};

// ============================================================================
// Test Data - Tests
// ============================================================================

const testsPassedResult: GateResult = {
  gateName: "tests",
  passed: true,
  status: "passed",
  durationMs: 1500,
  details: {
    passed: true,
    results: [
      { testName: "test_user_creation", passed: true },
      { testName: "test_user_login", passed: true },
      { testName: "test_user_logout", passed: true },
    ],
    testsRun: 3,
    testsPassed: 3,
    testsFailed: 0,
  },
};

const testsFailedResult: GateResult = {
  gateName: "tests",
  passed: false,
  status: "failed",
  durationMs: 2000,
  details: {
    passed: false,
    results: [
      { testName: "test_user_creation", passed: true },
      { testName: "test_user_login", passed: false, errorMessage: "AssertionError: Expected status 200, got 401" },
      { testName: "test_user_logout", passed: true },
      { testName: "test_password_reset", passed: false, errorMessage: "TimeoutError: Operation timed out after 30s" },
    ],
    testsRun: 4,
    testsPassed: 2,
    testsFailed: 2,
  },
};

// ============================================================================
// Syntax Gate Tests
// ============================================================================

describe("GateDetails - Syntax Gate", () => {
  it("shows passed syntax gate", () => {
    render(<GateDetails result={syntaxPassedResult} />);

    expect(screen.getByText("Syntax")).toBeInTheDocument();
    expect(screen.getByText("Passed")).toBeInTheDocument();
    expect(screen.getByText("All files have valid syntax")).toBeInTheDocument();
  });

  it("shows file statistics", () => {
    render(<GateDetails result={syntaxPassedResult} />);

    // Should show "Files checked:" label
    expect(screen.getByText("Files checked:")).toBeInTheDocument();
  });

  it("shows syntax issues when failed", () => {
    render(<GateDetails result={syntaxFailedResult} />);

    expect(screen.getByText("Syntax")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  it("groups issues by file", () => {
    render(<GateDetails result={syntaxFailedResult} />);

    // Should show file names as collapsible headers (multiple matches per file)
    const appMatches = screen.getAllByText(/src\/app\.py/);
    const utilsMatches = screen.getAllByText(/src\/utils\.py/);
    expect(appMatches.length).toBeGreaterThan(0);
    expect(utilsMatches.length).toBeGreaterThan(0);
  });

  it("shows line numbers", () => {
    render(<GateDetails result={syntaxFailedResult} />);

    // Line numbers should be visible
    expect(screen.getByText(/:10/)).toBeInTheDocument();
  });
});

// ============================================================================
// Security Gate Tests
// ============================================================================

describe("GateDetails - Security Gate", () => {
  it("shows passed security gate", () => {
    render(<GateDetails result={securityPassedResult} />);

    expect(screen.getByText("Security")).toBeInTheDocument();
    expect(screen.getByText("Passed")).toBeInTheDocument();
    expect(screen.getByText("No security issues detected")).toBeInTheDocument();
  });

  it("shows severity badges when failed", () => {
    render(<GateDetails result={securityFailedResult} />);

    expect(screen.getByText("1 Critical")).toBeInTheDocument();
    expect(screen.getByText("1 High")).toBeInTheDocument();
    expect(screen.getByText("1 Medium")).toBeInTheDocument();
  });

  it("shows rule IDs", () => {
    render(<GateDetails result={securityFailedResult} />);

    expect(screen.getByText(/dangerous-eval/)).toBeInTheDocument();
    expect(screen.getByText(/hardcoded-secret/)).toBeInTheDocument();
  });

  it("shows fix suggestions", () => {
    render(<GateDetails result={securityFailedResult} />);

    expect(screen.getByText(/ast\.literal_eval/)).toBeInTheDocument();
    expect(screen.getByText(/environment variables/)).toBeInTheDocument();
  });
});

// ============================================================================
// Architecture Gate Tests
// ============================================================================

describe("GateDetails - Architecture Gate", () => {
  it("shows passed architecture gate", () => {
    render(<GateDetails result={architecturePassedResult} />);

    expect(screen.getByText("Architecture")).toBeInTheDocument();
    expect(screen.getByText("Passed")).toBeInTheDocument();
    expect(screen.getByText("Code architecture follows all rules")).toBeInTheDocument();
  });

  it("shows architecture issues when failed", () => {
    render(<GateDetails result={architectureFailedResult} />);

    expect(screen.getByText("Architecture")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  it("shows rule names", () => {
    render(<GateDetails result={architectureFailedResult} />);

    expect(screen.getByText(/layer-violation/)).toBeInTheDocument();
    expect(screen.getByText(/circular-import/)).toBeInTheDocument();
  });
});

// ============================================================================
// Test Gate Tests
// ============================================================================

describe("GateDetails - Tests Gate", () => {
  it("shows passed tests gate", () => {
    render(<GateDetails result={testsPassedResult} />);

    expect(screen.getByText("Tests")).toBeInTheDocument();
    expect(screen.getByText("Passed")).toBeInTheDocument();
  });

  it("shows test statistics", () => {
    render(<GateDetails result={testsPassedResult} />);

    // Should show "Tests run:" label
    expect(screen.getByText("Tests run:")).toBeInTheDocument();
  });

  it("shows individual test results", () => {
    render(<GateDetails result={testsPassedResult} />);

    expect(screen.getByText("test_user_creation")).toBeInTheDocument();
    expect(screen.getByText("test_user_login")).toBeInTheDocument();
    expect(screen.getByText("test_user_logout")).toBeInTheDocument();
  });

  it("shows failed tests with error messages", () => {
    render(<GateDetails result={testsFailedResult} />);

    expect(screen.getByText(/AssertionError/)).toBeInTheDocument();
    expect(screen.getByText(/TimeoutError/)).toBeInTheDocument();
  });

  it("shows passed/failed counts", () => {
    render(<GateDetails result={testsFailedResult} />);

    // Should show failed count
    const failedLabel = screen.getByText("Failed:");
    expect(failedLabel).toBeInTheDocument();
  });
});

// ============================================================================
// Vietnamese Mode Tests
// ============================================================================

describe("GateDetails - Vietnamese Mode", () => {
  it("shows Vietnamese gate labels", () => {
    render(<GateDetails result={syntaxPassedResult} vietnamese={true} />);

    expect(screen.getByText("Cú pháp")).toBeInTheDocument();
  });

  it("shows Vietnamese status labels", () => {
    render(<GateDetails result={syntaxPassedResult} vietnamese={true} />);

    expect(screen.getByText("Đạt")).toBeInTheDocument();
  });

  it("shows Vietnamese success message for syntax", () => {
    render(<GateDetails result={syntaxPassedResult} vietnamese={true} />);

    expect(screen.getByText("Tất cả các file đều có cú pháp hợp lệ")).toBeInTheDocument();
  });

  it("shows Vietnamese success message for security", () => {
    render(<GateDetails result={securityPassedResult} vietnamese={true} />);

    expect(screen.getByText("Không phát hiện vấn đề bảo mật")).toBeInTheDocument();
  });

  it("shows Vietnamese success message for architecture", () => {
    render(<GateDetails result={architecturePassedResult} vietnamese={true} />);

    expect(screen.getByText("Kiến trúc code tuân thủ các quy tắc")).toBeInTheDocument();
  });

  it("shows Vietnamese error messages when available", () => {
    render(<GateDetails result={syntaxFailedResult} vietnamese={true} />);

    expect(screen.getByText(/thụt lề không mong muốn/)).toBeInTheDocument();
  });

  it("shows Vietnamese security messages", () => {
    render(<GateDetails result={securityFailedResult} vietnamese={true} />);

    expect(screen.getByText(/code injection/)).toBeInTheDocument();
  });
});

// ============================================================================
// File Click Handler Tests
// ============================================================================

describe("GateDetails - File Click Handler", () => {
  it("calls onFileClick when file is clicked", () => {
    const handleClick = vi.fn();
    render(
      <GateDetails result={syntaxFailedResult} onFileClick={handleClick} />
    );

    // Find the file button inside an issue item (look for one with :line)
    const fileLink = screen.getByText(":10", { exact: false });
    fireEvent.click(fileLink.closest("button") as HTMLButtonElement);

    expect(handleClick).toHaveBeenCalled();
  });
});

// ============================================================================
// Styling Tests
// ============================================================================

describe("GateDetails - Styling", () => {
  it("applies custom className", () => {
    const { container } = render(
      <GateDetails result={syntaxPassedResult} className="custom-details" />
    );

    expect(container.querySelector(".custom-details")).toBeInTheDocument();
  });

  it("respects maxHeight prop", () => {
    const { container } = render(
      <GateDetails result={syntaxPassedResult} maxHeight="200px" />
    );

    const scrollArea = container.querySelector('[style*="max-height"]');
    expect(scrollArea).toBeInTheDocument();
  });
});

// ============================================================================
// Error State Tests
// ============================================================================

describe("GateDetails - Error State", () => {
  it("shows error message when gate has error", () => {
    const errorResult: GateResult = {
      gateName: "syntax",
      status: "failed",
      durationMs: 100,
      details: {
        error: "Failed to parse file: out of memory",
      } as any,
    };

    render(<GateDetails result={errorResult} />);

    expect(screen.getByText(/Failed to parse file/)).toBeInTheDocument();
  });
});
