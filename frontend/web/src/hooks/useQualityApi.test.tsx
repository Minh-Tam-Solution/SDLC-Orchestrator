/**
 * =========================================================================
 * useQualityApi Tests - Sprint 56 Day 1
 * SDLC Orchestrator
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * =========================================================================
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode } from "react";
import {
  transformPipelineResult,
  transformGateResult,
  mapGateName,
  mapGateStatus,
  mapSeverity,
  useSessionQuality,
  useQualityScore,
  qualityKeys,
} from "./useQualityApi";

// ============================================================================
// Mock API Client
// ============================================================================

vi.mock("@/api/client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// ============================================================================
// Test Wrapper
// ============================================================================

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

// ============================================================================
// Test Data
// ============================================================================

const mockBackendGateResult = {
  gate_name: "Syntax",
  gate_number: 1,
  status: "passed" as const,
  duration_ms: 500,
  issues: [],
  summary: "All files passed syntax validation",
  details: {
    files_checked: 5,
    files_passed: 5,
  },
};

const mockBackendGateResultWithIssues = {
  gate_name: "Security",
  gate_number: 2,
  status: "failed" as const,
  duration_ms: 1200,
  issues: [
    {
      file_path: "src/main.py",
      line: 50,
      column: 10,
      severity: "critical" as const,
      code: "sql-injection",
      message: "SQL injection vulnerability detected",
      suggestion: "Use parameterized queries",
    },
    {
      file_path: "src/utils.py",
      line: 25,
      column: 5,
      severity: "high" as const,
      code: "hardcoded-secret",
      message: "Hardcoded API key found",
    },
  ],
  summary: "2 security issues found",
};

const mockBackendPipelineResult = {
  success: false,
  gates: [mockBackendGateResult, mockBackendGateResultWithIssues],
  total_duration_ms: 1700,
  failed_gate: "Security",
  summary: "Failed at Security gate",
};

const mockCleanPipelineResult = {
  success: true,
  gates: [
    {
      gate_name: "Syntax",
      gate_number: 1,
      status: "passed" as const,
      duration_ms: 400,
      issues: [],
      summary: "All files passed",
      details: { files_checked: 5, files_passed: 5 },
    },
    {
      gate_name: "Security",
      gate_number: 2,
      status: "passed" as const,
      duration_ms: 600,
      issues: [],
      summary: "No security issues",
    },
    {
      gate_name: "Architecture",
      gate_number: 3,
      status: "passed" as const,
      duration_ms: 300,
      issues: [],
      summary: "Architecture validated",
    },
    {
      gate_name: "Tests",
      gate_number: 4,
      status: "passed" as const,
      duration_ms: 500,
      issues: [],
      summary: "All tests passed",
      details: { tests_run: 10, tests_passed: 10, tests_failed: 0 },
    },
  ],
  total_duration_ms: 1800,
  summary: "All gates passed",
};

// ============================================================================
// mapGateName Tests
// ============================================================================

describe("mapGateName", () => {
  it("should map Syntax to syntax", () => {
    expect(mapGateName("Syntax")).toBe("syntax");
  });

  it("should map lowercase syntax to syntax", () => {
    expect(mapGateName("syntax")).toBe("syntax");
  });

  it("should map Security to security", () => {
    expect(mapGateName("Security")).toBe("security");
  });

  it("should map Context to architecture", () => {
    expect(mapGateName("Context")).toBe("architecture");
  });

  it("should map Architecture to architecture", () => {
    expect(mapGateName("Architecture")).toBe("architecture");
  });

  it("should map Tests to tests", () => {
    expect(mapGateName("Tests")).toBe("tests");
  });

  it("should default to syntax for unknown gate", () => {
    expect(mapGateName("Unknown")).toBe("syntax");
  });
});

// ============================================================================
// mapGateStatus Tests
// ============================================================================

describe("mapGateStatus", () => {
  it("should map passed to passed", () => {
    expect(mapGateStatus("passed")).toBe("passed");
  });

  it("should map failed to failed", () => {
    expect(mapGateStatus("failed")).toBe("failed");
  });

  it("should map pending to pending", () => {
    expect(mapGateStatus("pending")).toBe("pending");
  });

  it("should map running to running", () => {
    expect(mapGateStatus("running")).toBe("running");
  });

  it("should map skipped to skipped", () => {
    expect(mapGateStatus("skipped")).toBe("skipped");
  });
});

// ============================================================================
// mapSeverity Tests
// ============================================================================

describe("mapSeverity", () => {
  it("should map critical to critical", () => {
    expect(mapSeverity("critical")).toBe("critical");
  });

  it("should map high to high", () => {
    expect(mapSeverity("high")).toBe("high");
  });

  it("should map medium to medium", () => {
    expect(mapSeverity("medium")).toBe("medium");
  });

  it("should map low to low", () => {
    expect(mapSeverity("low")).toBe("low");
  });

  it("should map info to info", () => {
    expect(mapSeverity("info")).toBe("info");
  });
});

// ============================================================================
// transformGateResult Tests
// ============================================================================

describe("transformGateResult", () => {
  it("should transform passed syntax gate", () => {
    const result = transformGateResult(mockBackendGateResult);

    expect(result.gateName).toBe("syntax");
    expect(result.passed).toBe(true);
    expect(result.status).toBe("passed");
    expect(result.durationMs).toBe(500);
  });

  it("should transform failed security gate with issues", () => {
    const result = transformGateResult(mockBackendGateResultWithIssues);

    expect(result.gateName).toBe("security");
    expect(result.passed).toBe(false);
    expect(result.status).toBe("failed");
    expect(result.durationMs).toBe(1200);
  });

  it("should include security details with severity counts", () => {
    const result = transformGateResult(mockBackendGateResultWithIssues);

    // Check that details include issues
    const details = result.details as {
      criticalCount: number;
      highCount: number;
      issues: Array<{ severity: string }>;
    };
    expect(details.criticalCount).toBe(1);
    expect(details.highCount).toBe(1);
    expect(details.issues).toHaveLength(2);
  });

  it("should include issue details with file and line", () => {
    const result = transformGateResult(mockBackendGateResultWithIssues);

    const details = result.details as {
      issues: Array<{ file: string; line: number; message: string }>;
    };
    expect(details.issues[0].file).toBe("src/main.py");
    expect(details.issues[0].line).toBe(50);
    expect(details.issues[0].message).toBe("SQL injection vulnerability detected");
  });
});

// ============================================================================
// transformPipelineResult Tests
// ============================================================================

describe("transformPipelineResult", () => {
  it("should transform failed pipeline result", () => {
    const result = transformPipelineResult(mockBackendPipelineResult);

    expect(result.passed).toBe(false);
    expect(result.totalDurationMs).toBe(1700);
    expect(result.gates).toHaveLength(2);
  });

  it("should include gate summary", () => {
    const result = transformPipelineResult(mockBackendPipelineResult);

    expect(result.summary.gatesRun).toBe(2);
    expect(result.summary.gatesPassed).toBe(1);
    expect(result.summary.gatesFailed).toBe(1);
  });

  it("should generate Vietnamese summary for failed pipeline", () => {
    const result = transformPipelineResult(mockBackendPipelineResult);

    expect(result.vietnameseSummary).toContain("Thất bại");
    expect(result.vietnameseSummary).toContain("Bảo mật");
  });

  it("should transform clean pipeline result", () => {
    const result = transformPipelineResult(mockCleanPipelineResult);

    expect(result.passed).toBe(true);
    expect(result.gates).toHaveLength(4);
    expect(result.summary.gatesPassed).toBe(4);
    expect(result.summary.gatesFailed).toBe(0);
  });

  it("should generate Vietnamese summary for passed pipeline", () => {
    const result = transformPipelineResult(mockCleanPipelineResult);

    expect(result.vietnameseSummary).toContain("Tất cả");
    expect(result.vietnameseSummary).toContain("cổng đã đạt");
  });

  it("should preserve gate order", () => {
    const result = transformPipelineResult(mockCleanPipelineResult);

    expect(result.gates[0].gateName).toBe("syntax");
    expect(result.gates[1].gateName).toBe("security");
    expect(result.gates[2].gateName).toBe("architecture");
    expect(result.gates[3].gateName).toBe("tests");
  });
});

// ============================================================================
// qualityKeys Tests
// ============================================================================

describe("qualityKeys", () => {
  it("should generate all key", () => {
    expect(qualityKeys.all).toEqual(["quality"]);
  });

  it("should generate session key", () => {
    expect(qualityKeys.session("abc123")).toEqual(["quality", "session", "abc123"]);
  });

  it("should generate history key", () => {
    expect(qualityKeys.history("project-1")).toEqual(["quality", "history", "project-1"]);
  });

  it("should generate providers key", () => {
    expect(qualityKeys.providers()).toEqual(["quality", "providers"]);
  });

  it("should generate usage key", () => {
    expect(qualityKeys.usage()).toEqual(["quality", "usage"]);
  });
});

// ============================================================================
// useSessionQuality Hook Tests
// ============================================================================

describe("useSessionQuality", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should not fetch when sessionId is null", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSessionQuality(null), { wrapper });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBeUndefined();
  });

  it("should have correct initial state", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSessionQuality("session-123"), { wrapper });

    // Initial loading state
    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();
  });
});

// ============================================================================
// useQualityScore Hook Tests
// ============================================================================

describe("useQualityScore", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return default values when sessionId is null", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityScore(null), { wrapper });

    expect(result.current.score).toBe(0);
    expect(result.current.grade).toBe("N/A");
  });

  it("should return loading state initially", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useQualityScore("session-123"), { wrapper });

    expect(result.current.isLoading).toBe(true);
  });
});

// ============================================================================
// Integration Tests
// ============================================================================

describe("Quality API Integration", () => {
  it("should correctly transform complex pipeline result", () => {
    const complexBackend = {
      success: false,
      gates: [
        {
          gate_name: "Syntax",
          gate_number: 1,
          status: "passed" as const,
          duration_ms: 500,
          issues: [],
          summary: "OK",
          details: { files_checked: 10, files_passed: 10 },
        },
        {
          gate_name: "Security",
          gate_number: 2,
          status: "failed" as const,
          duration_ms: 1500,
          issues: [
            {
              file_path: "app.py",
              line: 10,
              column: 0,
              severity: "critical" as const,
              code: "VULN001",
              message: "Critical vulnerability",
            },
            {
              file_path: "app.py",
              line: 20,
              column: 0,
              severity: "high" as const,
              code: "VULN002",
              message: "High severity issue",
            },
            {
              file_path: "utils.py",
              line: 5,
              column: 0,
              severity: "medium" as const,
              code: "VULN003",
              message: "Medium severity issue",
            },
          ],
          summary: "3 issues found",
        },
        {
          gate_name: "Architecture",
          gate_number: 3,
          status: "skipped" as const,
          duration_ms: 0,
          issues: [],
          summary: "Skipped due to previous failure",
        },
        {
          gate_name: "Tests",
          gate_number: 4,
          status: "skipped" as const,
          duration_ms: 0,
          issues: [],
          summary: "Skipped",
        },
      ],
      total_duration_ms: 2000,
      failed_gate: "Security",
      summary: "Pipeline failed at Security",
    };

    const result = transformPipelineResult(complexBackend);

    // Overall result
    expect(result.passed).toBe(false);
    expect(result.totalDurationMs).toBe(2000);

    // Gate summary
    expect(result.summary.gatesRun).toBe(4);
    expect(result.summary.gatesPassed).toBe(1);
    expect(result.summary.gatesFailed).toBe(1);

    // Security gate details
    const securityGate = result.gates.find((g) => g.gateName === "security");
    expect(securityGate).toBeDefined();
    expect(securityGate?.status).toBe("failed");

    const securityDetails = securityGate?.details as {
      criticalCount: number;
      highCount: number;
      mediumCount: number;
      issues: Array<unknown>;
    };
    expect(securityDetails.criticalCount).toBe(1);
    expect(securityDetails.highCount).toBe(1);
    expect(securityDetails.mediumCount).toBe(1);
    expect(securityDetails.issues).toHaveLength(3);

    // Skipped gates
    const archGate = result.gates.find((g) => g.gateName === "architecture");
    expect(archGate?.status).toBe("skipped");

    const testsGate = result.gates.find((g) => g.gateName === "tests");
    expect(testsGate?.status).toBe("skipped");
  });
});
