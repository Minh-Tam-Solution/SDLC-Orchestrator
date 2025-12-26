/**
 * =========================================================================
 * QualityPanel - Integrated Quality Pipeline Panel
 * SDLC Orchestrator - Sprint 56 Day 3
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Backend Integration
 *
 * Purpose:
 * - Unified quality panel for code generation pages
 * - Combines QualitySummaryPanel, LiveQualityMonitor, and QualityReportGenerator
 * - Manages SSE streaming for real-time quality updates
 * - Uses backend API hooks for data fetching
 *
 * References:
 * - docs/02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md
 * - Sprint 55 Quality Components
 * =========================================================================
 */

import React, { useState, useMemo, useEffect } from "react";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Radio,
  RefreshCw,
  XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSessionQuality, useInvalidateQualityCache } from "@/hooks/useQualityApi";
import { useQualityStreamBackend } from "@/hooks/useQualityStreamBackend";
import { QualitySummaryPanel, CompactQualitySummary } from "./QualitySummaryPanel";
import { QualityReportGenerator } from "./QualityReportGenerator";
import { GatePipeline } from "./GatePipeline";
import type { PipelineResult } from "@/types/quality";

// ============================================================================
// Types
// ============================================================================

export interface QualityPanelProps {
  /** Session ID for fetching quality data */
  sessionId: string | null;
  /** Base API URL (optional) */
  baseUrl?: string;
  /** Vietnamese mode */
  vietnamese?: boolean;
  /** Enable live streaming */
  enableStreaming?: boolean;
  /** Auto-connect to streaming when sessionId is set */
  autoConnect?: boolean;
  /** Show full report tab */
  showReport?: boolean;
  /** Compact mode - shows only summary */
  compact?: boolean;
  /** Callback when quality check completes */
  onComplete?: (result: PipelineResult) => void;
  /** Callback when error occurs */
  onError?: (error: Error) => void;
  /** Additional CSS classes */
  className?: string;
}

export interface QualityPanelHandle {
  /** Refresh quality data */
  refresh: () => void;
  /** Start streaming */
  startStream: () => void;
  /** Stop streaming */
  stopStream: () => void;
}

// ============================================================================
// Component
// ============================================================================

export const QualityPanel: React.FC<QualityPanelProps> = ({
  sessionId,
  baseUrl,
  vietnamese = false,
  enableStreaming = true,
  autoConnect = false,
  showReport = true,
  compact = false,
  onComplete,
  onError,
  className,
}) => {
  const [activeTab, setActiveTab] = useState<"summary" | "live" | "report">("summary");

  // API Query for stored quality result
  const {
    data: storedResult,
    isLoading: isLoadingStored,
    error: storedError,
    refetch,
  } = useSessionQuality(sessionId);

  const { invalidateSession } = useInvalidateQualityCache();

  // Streaming hook
  const {
    state: streamState,
    connect,
    disconnect,
    reset,
    isStreaming,
    getPipelineResult: getStreamResult,
  } = useQualityStreamBackend({
    baseUrl,
    sessionId: sessionId || undefined,
    autoConnect: autoConnect && enableStreaming && !!sessionId,
    onPipelineCompleted: (result) => {
      onComplete?.(result);
      if (sessionId) {
        invalidateSession(sessionId);
      }
    },
    onError: (err) => onError?.(err),
  });

  // Determine which result to show
  const displayResult = useMemo((): PipelineResult | null => {
    // If streaming is completed, use stream result
    if (streamState.connectionState === "completed") {
      return getStreamResult();
    }
    // Otherwise use stored result
    return storedResult || null;
  }, [streamState.connectionState, getStreamResult, storedResult]);

  // Handle refresh
  const handleRefresh = () => {
    if (isStreaming) {
      disconnect();
    }
    reset();
    refetch();
  };

  // Handle start stream
  const handleStartStream = () => {
    if (sessionId) {
      connect(sessionId);
      setActiveTab("live");
    }
  };

  // Error handling
  useEffect(() => {
    if (storedError) {
      onError?.(storedError);
    }
  }, [storedError, onError]);

  // Compact mode - just show summary
  if (compact) {
    if (isLoadingStored) {
      return (
        <div className={cn("flex items-center gap-2 p-2", className)}>
          <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
          <span className="text-sm text-muted-foreground">
            {vietnamese ? "Đang tải..." : "Loading..."}
          </span>
        </div>
      );
    }

    if (!displayResult) {
      return (
        <div className={cn("flex items-center gap-2 p-2", className)}>
          <AlertCircle className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">
            {vietnamese ? "Chưa có dữ liệu chất lượng" : "No quality data"}
          </span>
          {enableStreaming && sessionId && (
            <Button size="sm" variant="outline" onClick={handleStartStream}>
              <Radio className="h-3 w-3 mr-1" />
              {vietnamese ? "Bắt đầu" : "Start"}
            </Button>
          )}
        </div>
      );
    }

    return (
      <CompactQualitySummary
        result={displayResult}
        vietnamese={vietnamese}
        onClick={() => setActiveTab("summary")}
        className={className}
      />
    );
  }

  // Full panel mode
  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              {vietnamese ? "Chất lượng Code" : "Code Quality"}
            </CardTitle>
            <CardDescription>
              {vietnamese
                ? "Kết quả kiểm tra chất lượng 4 cổng"
                : "4-Gate quality pipeline results"}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {/* Streaming status */}
            {isStreaming && (
              <Badge variant="secondary" className="animate-pulse">
                <Radio className="h-3 w-3 mr-1" />
                {vietnamese ? "Đang stream" : "Streaming"}
              </Badge>
            )}
            {streamState.connectionState === "completed" && (
              <Badge variant="outline" className="text-green-600">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                {vietnamese ? "Hoàn thành" : "Complete"}
              </Badge>
            )}
            {streamState.connectionState === "error" && (
              <Badge variant="destructive">
                <XCircle className="h-3 w-3 mr-1" />
                {vietnamese ? "Lỗi" : "Error"}
              </Badge>
            )}

            {/* Actions */}
            <Button size="sm" variant="outline" onClick={handleRefresh}>
              <RefreshCw
                className={cn("h-4 w-4", isLoadingStored && "animate-spin")}
              />
            </Button>
            {enableStreaming && sessionId && !isStreaming && (
              <Button size="sm" variant="outline" onClick={handleStartStream}>
                <Radio className="h-4 w-4 mr-1" />
                {vietnamese ? "Stream" : "Stream"}
              </Button>
            )}
            {isStreaming && (
              <Button size="sm" variant="outline" onClick={disconnect}>
                {vietnamese ? "Dừng" : "Stop"}
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="summary">
              {vietnamese ? "Tóm tắt" : "Summary"}
            </TabsTrigger>
            <TabsTrigger value="live" disabled={!enableStreaming}>
              {vietnamese ? "Trực tiếp" : "Live"}
            </TabsTrigger>
            {showReport && (
              <TabsTrigger value="report" disabled={!displayResult}>
                {vietnamese ? "Báo cáo" : "Report"}
              </TabsTrigger>
            )}
          </TabsList>

          {/* Summary Tab */}
          <TabsContent value="summary" className="mt-4">
            {isLoadingStored && !displayResult ? (
              <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                <RefreshCw className="h-8 w-8 animate-spin mb-2" />
                <span>{vietnamese ? "Đang tải..." : "Loading..."}</span>
              </div>
            ) : !displayResult ? (
              <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                <AlertCircle className="h-8 w-8 mb-2" />
                <span className="mb-4">
                  {vietnamese
                    ? "Chưa có dữ liệu chất lượng cho phiên này"
                    : "No quality data for this session"}
                </span>
                {enableStreaming && sessionId && (
                  <Button onClick={handleStartStream}>
                    <Radio className="h-4 w-4 mr-2" />
                    {vietnamese ? "Bắt đầu kiểm tra" : "Start Quality Check"}
                  </Button>
                )}
              </div>
            ) : (
              <QualitySummaryPanel
                result={displayResult}
                vietnamese={vietnamese}
                onViewDetails={() => setActiveTab("report")}
              />
            )}
          </TabsContent>

          {/* Live Tab */}
          <TabsContent value="live" className="mt-4">
            <div className="space-y-4">
              {/* Progress */}
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">
                  {vietnamese ? "Tiến độ" : "Progress"}
                </span>
                <Badge variant="outline">{streamState.overallProgress}%</Badge>
              </div>
              <div className="w-full bg-muted h-2 rounded-full overflow-hidden">
                <div
                  className="bg-primary h-full transition-all duration-300"
                  style={{ width: `${streamState.overallProgress}%` }}
                />
              </div>

              {/* Gate Pipeline */}
              <Separator />
              <GatePipeline
                gates={Object.values(streamState.gates).map((g) => ({
                  gateName: g.gateName,
                  passed: g.status === "passed",
                  status: g.status,
                  durationMs: g.durationMs || 0,
                  details: { error: "Streaming mode" },
                }))}
                currentGate={streamState.currentGate}
                vietnamese={vietnamese}
              />

              {/* Issues */}
              {streamState.issues.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <h4 className="text-sm font-medium mb-2">
                      {vietnamese ? "Vấn đề phát hiện" : "Issues Found"} (
                      {streamState.issues.length})
                    </h4>
                    <div className="max-h-40 overflow-y-auto space-y-1">
                      {streamState.issues.slice(-10).map((issue) => (
                        <div
                          key={issue.id}
                          className="text-xs p-2 bg-muted rounded flex items-start gap-2"
                        >
                          <Badge
                            variant={
                              issue.severity === "critical"
                                ? "destructive"
                                : "secondary"
                            }
                            className="text-xs"
                          >
                            {issue.severity}
                          </Badge>
                          <span className="flex-1 truncate">{issue.message}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          </TabsContent>

          {/* Report Tab */}
          {showReport && (
            <TabsContent value="report" className="mt-4">
              {displayResult ? (
                <QualityReportGenerator
                  result={displayResult}
                  vietnamese={vietnamese}
                  metadata={{
                    title: vietnamese ? "Báo cáo chất lượng" : "Quality Report",
                    generatedAt: new Date(),
                  }}
                />
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                  <FileText className="h-8 w-8 mb-2" />
                  <span>
                    {vietnamese
                      ? "Chạy kiểm tra chất lượng để tạo báo cáo"
                      : "Run quality check to generate report"}
                  </span>
                </div>
              )}
            </TabsContent>
          )}
        </Tabs>
      </CardContent>
    </Card>
  );
};

// ============================================================================
// Export
// ============================================================================

export default QualityPanel;
