/**
 * =========================================================================
 * Quality Components - Export Index
 * SDLC Orchestrator - Sprint 55
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 * =========================================================================
 */

// Gate Status Components
export { GateStatusBadge, GateStatusIcon } from "./GateStatusBadge";

// Pipeline Components
export { GatePipeline, CompactPipeline } from "./GatePipeline";

// Detail Components
export { GateDetails } from "./GateDetails";

// Dashboard Components
export {
  QualityDashboard,
  QualityScoreCard,
  IssueSummaryCard,
  GateProgressCard,
  DurationCard,
} from "./QualityDashboard";
export type { QualityGrade, IssueSummary } from "./QualityDashboard";

// File-Level Quality Components (Day 3)
export {
  FileQualityIndicator,
  FileQualityList,
  getFileQualityStatus,
  getFilesWithIssues,
} from "./FileQualityIndicator";
export type { FileQualityStatus } from "./FileQualityIndicator";

export {
  FileIssuesList,
  getFileIssues,
} from "./FileIssuesList";
export type { UnifiedIssue } from "./FileIssuesList";

export {
  FileQualityPanel,
  FileQualityCard,
} from "./FileQualityPanel";

// Quality Streaming Components (Day 4)
export {
  QualityStreamProvider,
  useQualityStreamContext,
  withQualityStream,
} from "./QualityStreamProvider";

export {
  LiveQualityMonitor,
  StandaloneLiveMonitor,
} from "./LiveQualityMonitor";

// Quality Report Components (Day 5)
export {
  QualityReportGenerator,
  generateReport,
  generateReportId,
  exportReportAsJSON,
  exportReportAsCSV,
  exportReportAsMarkdown,
} from "./QualityReportGenerator";
export type {
  QualityReport,
  ReportMetadata,
  ReportRecommendation,
  ExportFormat,
} from "./QualityReportGenerator";

export {
  QualitySummaryPanel,
  CompactQualitySummary,
  InlineQualityBadge,
  QualityTrendIndicator,
  GateStatusSummary,
} from "./QualitySummaryPanel";

// Integrated Quality Panel (Sprint 56 - Backend Integration)
export { QualityPanel } from "./QualityPanel";
export type { QualityPanelProps, QualityPanelHandle } from "./QualityPanel";
