/**
 * =========================================================================
 * Quality Gate Types - Type Definitions for 4-Gate Quality Pipeline
 * SDLC Orchestrator - Sprint 55 Day 1
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 * Authority: Frontend Team + CTO Approved
 *
 * Purpose:
 * - Define types for 4-Gate Quality Pipeline
 * - Gate 1: Syntax Validation
 * - Gate 2: Security Validation (Semgrep)
 * - Gate 3: Architecture Validation
 * - Gate 4: Test Execution
 *
 * References:
 * - docs/02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md
 * =========================================================================
 */

// ============================================================================
// Gate Status Types
// ============================================================================

export type GateStatus = "pending" | "running" | "passed" | "failed" | "skipped";

export type GateName = "syntax" | "security" | "architecture" | "tests";

export type Severity = "critical" | "high" | "medium" | "low" | "info";

// ============================================================================
// Issue Types
// ============================================================================

export interface SyntaxIssue {
  file: string;
  line: number;
  column: number;
  message: string;
  vietnameseMessage: string;
}

export interface SecurityIssue {
  file: string;
  line: number;
  ruleId: string;
  severity: Severity;
  message: string;
  vietnameseMessage: string;
  fixSuggestion?: string;
}

export interface ArchitectureIssue {
  file: string;
  line?: number;
  rule: string;
  message: string;
  vietnameseMessage: string;
}

export interface TestResult {
  testName: string;
  passed: boolean;
  errorMessage?: string;
  duration?: number;
}

// ============================================================================
// Gate Result Types
// ============================================================================

export interface SyntaxValidationResult {
  passed: boolean;
  issues: SyntaxIssue[];
  filesChecked: number;
  filesPassed: number;
}

export interface SecurityValidationResult {
  passed: boolean;
  issues: SecurityIssue[];
  criticalCount: number;
  highCount: number;
  mediumCount: number;
  lowCount: number;
}

export interface ArchitectureValidationResult {
  passed: boolean;
  issues: ArchitectureIssue[];
}

export interface TestValidationResult {
  passed: boolean;
  testsRun: number;
  testsPassed: number;
  testsFailed: number;
  results: TestResult[];
}

// ============================================================================
// Gate Result Union Type
// ============================================================================

export type GateDetails =
  | SyntaxValidationResult
  | SecurityValidationResult
  | ArchitectureValidationResult
  | TestValidationResult
  | { error: string };

export interface GateResult {
  gateName: GateName;
  passed: boolean;
  status: GateStatus;
  durationMs: number;
  details: GateDetails;
}

// ============================================================================
// Pipeline Result Types
// ============================================================================

export interface PipelineSummary {
  gatesRun: number;
  gatesPassed: number;
  gatesFailed: number;
}

export interface PipelineResult {
  passed: boolean;
  totalDurationMs: number;
  gates: GateResult[];
  summary: PipelineSummary;
  vietnameseSummary: string;
}

// ============================================================================
// Streaming Event Types
// ============================================================================

export type QualityEventType =
  | "gate_started"
  | "gate_progress"
  | "gate_completed"
  | "pipeline_started"
  | "pipeline_completed"
  | "issue_found";

export interface QualityEvent {
  type: QualityEventType;
  gateName?: GateName;
  timestamp: number;
  data: Record<string, unknown>;
}

export interface GateStartedEvent {
  type: "gate_started";
  gateName: GateName;
  timestamp: number;
  data: {
    filesCount: number;
  };
}

export interface GateProgressEvent {
  type: "gate_progress";
  gateName: GateName;
  timestamp: number;
  data: {
    filesProcessed: number;
    filesTotal: number;
    issuesFound: number;
  };
}

export interface GateCompletedEvent {
  type: "gate_completed";
  gateName: GateName;
  timestamp: number;
  data: {
    passed: boolean;
    durationMs: number;
    issuesCount: number;
  };
}

export interface IssueFoundEvent {
  type: "issue_found";
  gateName: GateName;
  timestamp: number;
  data: {
    severity: Severity;
    file: string;
    line?: number;
    message: string;
  };
}

// ============================================================================
// Display Helper Types
// ============================================================================

export interface GateDisplayConfig {
  name: GateName;
  label: string;
  vietnameseLabel: string;
  icon: string;
  description: string;
  vietnameseDescription: string;
}

export const GATE_CONFIGS: Record<GateName, GateDisplayConfig> = {
  syntax: {
    name: "syntax",
    label: "Syntax",
    vietnameseLabel: "Cú pháp",
    icon: "Code2",
    description: "Validates code syntax and structure",
    vietnameseDescription: "Kiểm tra cú pháp và cấu trúc code",
  },
  security: {
    name: "security",
    label: "Security",
    vietnameseLabel: "Bảo mật",
    icon: "Shield",
    description: "Scans for security vulnerabilities",
    vietnameseDescription: "Quét lỗ hổng bảo mật",
  },
  architecture: {
    name: "architecture",
    label: "Architecture",
    vietnameseLabel: "Kiến trúc",
    icon: "Layers",
    description: "Checks architectural rules and patterns",
    vietnameseDescription: "Kiểm tra quy tắc và mẫu kiến trúc",
  },
  tests: {
    name: "tests",
    label: "Tests",
    vietnameseLabel: "Kiểm thử",
    icon: "TestTube2",
    description: "Runs generated tests",
    vietnameseDescription: "Chạy các bài kiểm thử",
  },
};

// ============================================================================
// Status Color Mapping
// ============================================================================

export const STATUS_COLORS: Record<GateStatus, string> = {
  pending: "gray",
  running: "blue",
  passed: "green",
  failed: "red",
  skipped: "yellow",
};

export const SEVERITY_COLORS: Record<Severity, string> = {
  critical: "red",
  high: "orange",
  medium: "yellow",
  low: "blue",
  info: "gray",
};

// ============================================================================
// Utility Functions
// ============================================================================

export function getGateConfig(gateName: GateName): GateDisplayConfig {
  return GATE_CONFIGS[gateName];
}

export function isSecurityResult(
  details: GateDetails
): details is SecurityValidationResult {
  return "criticalCount" in details;
}

export function isSyntaxResult(
  details: GateDetails
): details is SyntaxValidationResult {
  return "filesChecked" in details;
}

export function isArchitectureResult(
  details: GateDetails
): details is ArchitectureValidationResult {
  return "issues" in details && !("criticalCount" in details) && !("testsRun" in details);
}

export function isTestResult(
  details: GateDetails
): details is TestValidationResult {
  return "testsRun" in details;
}

export function getTotalIssueCount(result: PipelineResult): number {
  let total = 0;
  for (const gate of result.gates) {
    if (isSyntaxResult(gate.details)) {
      total += gate.details.issues.length;
    } else if (isSecurityResult(gate.details)) {
      total += gate.details.issues.length;
    } else if (isArchitectureResult(gate.details)) {
      total += gate.details.issues.length;
    } else if (isTestResult(gate.details)) {
      total += gate.details.testsFailed;
    }
  }
  return total;
}

export function getHighestSeverity(result: PipelineResult): Severity | null {
  for (const gate of result.gates) {
    if (isSecurityResult(gate.details)) {
      if (gate.details.criticalCount > 0) return "critical";
      if (gate.details.highCount > 0) return "high";
      if (gate.details.mediumCount > 0) return "medium";
      if (gate.details.lowCount > 0) return "low";
    }
  }
  return null;
}
