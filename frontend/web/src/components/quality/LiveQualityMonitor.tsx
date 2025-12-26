/**
 * =========================================================================
 * LiveQualityMonitor - Real-Time Quality Pipeline Monitor
 * SDLC Orchestrator - Sprint 55 Day 4
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 *
 * Purpose:
 * - Display real-time quality pipeline progress
 * - Show live gate execution status
 * - Stream issues as they are found
 * - Provide connection status indicator
 * - Support Vietnamese internationalization
 *
 * References:
 * - docs/02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md
 * =========================================================================
 */

import React, { useMemo } from "react";
import {
  Loader2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  AlertTriangle,
  Radio,
  Wifi,
  WifiOff,
  RefreshCw,
  Play,
  Square,
  Clock,
  FileWarning,
  Info,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import type { GateName, Severity } from "@/types/quality";
import { GATE_CONFIGS } from "@/types/quality";
import { useQualityStreamContext } from "./QualityStreamProvider";
import type { StreamConnectionState, StreamIssue, GateStreamState } from "@/hooks/useQualityStream";

// ============================================================================
// Types
// ============================================================================

export interface LiveQualityMonitorProps {
  /** Vietnamese mode */
  vietnamese?: boolean;
  /** Show connection controls */
  showControls?: boolean;
  /** Show live issue feed */
  showIssueFeed?: boolean;
  /** Max issues to show in feed */
  maxIssueFeedItems?: number;
  /** Show gate details */
  showGateDetails?: boolean;
  /** Compact mode */
  compact?: boolean;
  /** Additional CSS classes */
  className?: string;
}

// ============================================================================
// Connection Status Component
// ============================================================================

interface ConnectionStatusProps {
  state: StreamConnectionState;
  vietnamese?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onReset?: () => void;
  showControls?: boolean;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  state,
  vietnamese,
  onConnect,
  onDisconnect,
  onReset,
  showControls,
}) => {
  const getStatusConfig = () => {
    switch (state) {
      case "connected":
        return {
          icon: <Wifi className="h-4 w-4" />,
          label: vietnamese ? "Đã kết nối" : "Connected",
          color: "text-green-600",
          bgColor: "bg-green-100 dark:bg-green-900/30",
          pulse: true,
        };
      case "connecting":
        return {
          icon: <Loader2 className="h-4 w-4 animate-spin" />,
          label: vietnamese ? "Đang kết nối..." : "Connecting...",
          color: "text-blue-600",
          bgColor: "bg-blue-100 dark:bg-blue-900/30",
          pulse: false,
        };
      case "disconnected":
        return {
          icon: <WifiOff className="h-4 w-4" />,
          label: vietnamese ? "Ngắt kết nối" : "Disconnected",
          color: "text-gray-600",
          bgColor: "bg-gray-100 dark:bg-gray-800",
          pulse: false,
        };
      case "error":
        return {
          icon: <AlertCircle className="h-4 w-4" />,
          label: vietnamese ? "Lỗi kết nối" : "Connection Error",
          color: "text-red-600",
          bgColor: "bg-red-100 dark:bg-red-900/30",
          pulse: false,
        };
      case "completed":
        return {
          icon: <CheckCircle2 className="h-4 w-4" />,
          label: vietnamese ? "Hoàn thành" : "Completed",
          color: "text-green-600",
          bgColor: "bg-green-100 dark:bg-green-900/30",
          pulse: false,
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div
          className={cn(
            "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm",
            config.bgColor,
            config.color
          )}
        >
          {config.icon}
          <span className="font-medium">{config.label}</span>
          {config.pulse && (
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
            </span>
          )}
        </div>
      </div>

      {showControls && (
        <div className="flex items-center gap-2">
          {(state === "disconnected" || state === "error") && (
            <Button size="sm" variant="outline" onClick={onConnect}>
              <Play className="h-3.5 w-3.5 mr-1" />
              {vietnamese ? "Kết nối" : "Connect"}
            </Button>
          )}
          {(state === "connected" || state === "connecting") && (
            <Button size="sm" variant="outline" onClick={onDisconnect}>
              <Square className="h-3.5 w-3.5 mr-1" />
              {vietnamese ? "Ngắt" : "Disconnect"}
            </Button>
          )}
          {state === "completed" && (
            <Button size="sm" variant="outline" onClick={onReset}>
              <RefreshCw className="h-3.5 w-3.5 mr-1" />
              {vietnamese ? "Đặt lại" : "Reset"}
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// Live Gate Status Component
// ============================================================================

interface LiveGateStatusProps {
  gate: GateStreamState;
  isCurrent: boolean;
  vietnamese?: boolean;
}

const LiveGateStatus: React.FC<LiveGateStatusProps> = ({
  gate,
  isCurrent,
  vietnamese,
}) => {
  const config = GATE_CONFIGS[gate.gateName];
  const label = vietnamese ? config.vietnameseLabel : config.label;

  const getStatusIcon = () => {
    switch (gate.status) {
      case "passed":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "running":
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case "skipped":
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const progress =
    gate.filesTotal > 0
      ? Math.round((gate.filesProcessed / gate.filesTotal) * 100)
      : 0;

  return (
    <div
      className={cn(
        "p-3 rounded-lg border transition-all",
        isCurrent && "border-blue-500 bg-blue-50/50 dark:bg-blue-900/20",
        gate.status === "passed" && "border-green-200 bg-green-50/50 dark:bg-green-900/10",
        gate.status === "failed" && "border-red-200 bg-red-50/50 dark:bg-red-900/10",
        gate.status === "pending" && "border-gray-200 bg-gray-50/50 dark:bg-gray-800/50"
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className="font-medium text-sm">{label}</span>
          {isCurrent && (
            <Badge variant="secondary" className="text-xs">
              {vietnamese ? "Đang chạy" : "Running"}
            </Badge>
          )}
        </div>
        {gate.issuesFound > 0 && (
          <Badge
            variant={gate.status === "failed" ? "destructive" : "outline"}
            className="text-xs"
          >
            {gate.issuesFound} {vietnamese ? "lỗi" : "issues"}
          </Badge>
        )}
      </div>

      {gate.status === "running" && (
        <div className="space-y-1">
          <Progress value={progress} className="h-1.5" />
          <p className="text-xs text-gray-500">
            {gate.filesProcessed}/{gate.filesTotal}{" "}
            {vietnamese ? "tệp" : "files"}
          </p>
        </div>
      )}

      {gate.durationMs !== undefined && (
        <p className="text-xs text-gray-500 mt-1">
          {vietnamese ? "Thời gian" : "Duration"}: {gate.durationMs}ms
        </p>
      )}
    </div>
  );
};

// ============================================================================
// Live Issue Feed Component
// ============================================================================

interface LiveIssueFeedProps {
  issues: StreamIssue[];
  maxItems?: number;
  vietnamese?: boolean;
}

const SeverityIcon: React.FC<{ severity: Severity }> = ({ severity }) => {
  switch (severity) {
    case "critical":
      return <AlertCircle className="h-3.5 w-3.5 text-red-600" />;
    case "high":
      return <AlertTriangle className="h-3.5 w-3.5 text-orange-500" />;
    case "medium":
      return <AlertTriangle className="h-3.5 w-3.5 text-yellow-500" />;
    case "low":
      return <Info className="h-3.5 w-3.5 text-blue-500" />;
    default:
      return <Info className="h-3.5 w-3.5 text-gray-500" />;
  }
};

const LiveIssueFeed: React.FC<LiveIssueFeedProps> = ({
  issues,
  maxItems = 10,
  vietnamese,
}) => {
  const displayIssues = issues.slice(-maxItems).reverse();

  if (displayIssues.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-6 text-gray-500">
        <FileWarning className="h-8 w-8 mb-2 text-gray-300" />
        <p className="text-sm">
          {vietnamese ? "Chưa có lỗi nào" : "No issues found yet"}
        </p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-48">
      <div className="space-y-2 pr-4">
        {displayIssues.map((issue) => {
          const gateConfig = GATE_CONFIGS[issue.gateName];
          const gateLabel = vietnamese
            ? gateConfig.vietnameseLabel
            : gateConfig.label;

          return (
            <div
              key={issue.id}
              className={cn(
                "p-2 rounded border-l-2 bg-gray-50 dark:bg-gray-800/50",
                issue.severity === "critical" && "border-l-red-500",
                issue.severity === "high" && "border-l-orange-500",
                issue.severity === "medium" && "border-l-yellow-500",
                issue.severity === "low" && "border-l-blue-500"
              )}
            >
              <div className="flex items-start gap-2">
                <SeverityIcon severity={issue.severity} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <Badge variant="outline" className="text-xs px-1 py-0">
                      {gateLabel}
                    </Badge>
                    <span className="text-xs text-gray-500 font-mono truncate">
                      {issue.file}
                      {issue.line && `:${issue.line}`}
                    </span>
                  </div>
                  <p className="text-xs text-gray-700 dark:text-gray-300 line-clamp-2">
                    {issue.message}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </ScrollArea>
  );
};

// ============================================================================
// Overall Progress Component
// ============================================================================

interface OverallProgressProps {
  progress: number;
  currentGate?: GateName;
  vietnamese?: boolean;
}

const OverallProgress: React.FC<OverallProgressProps> = ({
  progress,
  currentGate,
  vietnamese,
}) => {
  const currentGateLabel = currentGate
    ? vietnamese
      ? GATE_CONFIGS[currentGate].vietnameseLabel
      : GATE_CONFIGS[currentGate].label
    : null;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">
          {vietnamese ? "Tiến độ tổng thể" : "Overall Progress"}
        </span>
        <span className="text-sm text-gray-500">{progress}%</span>
      </div>
      <Progress value={progress} className="h-2" />
      {currentGateLabel && (
        <p className="text-xs text-gray-500">
          {vietnamese ? "Đang xử lý" : "Processing"}: {currentGateLabel}
        </p>
      )}
    </div>
  );
};

// ============================================================================
// Main Component
// ============================================================================

export const LiveQualityMonitor: React.FC<LiveQualityMonitorProps> = ({
  vietnamese = false,
  showControls = true,
  showIssueFeed = true,
  maxIssueFeedItems = 10,
  showGateDetails = true,
  compact = false,
  className,
}) => {
  const context = useQualityStreamContext();
  const {
    connectionState,
    currentGate,
    progress,
    issues,
    gates,
    connect,
    disconnect,
    reset,
  } = context;

  const gateOrder: GateName[] = ["syntax", "security", "architecture", "tests"];

  // Summary stats
  const stats = useMemo(() => {
    const criticalCount = issues.filter((i) => i.severity === "critical").length;
    const highCount = issues.filter((i) => i.severity === "high").length;
    const passedGates = Object.values(gates).filter(
      (g) => g.status === "passed"
    ).length;
    const failedGates = Object.values(gates).filter(
      (g) => g.status === "failed"
    ).length;

    return { criticalCount, highCount, passedGates, failedGates };
  }, [issues, gates]);

  if (compact) {
    return (
      <div className={cn("flex items-center gap-4", className)}>
        <ConnectionStatus
          state={connectionState}
          vietnamese={vietnamese}
          showControls={false}
        />
        <Progress value={progress} className="flex-1 h-2" />
        <span className="text-sm text-gray-500">{progress}%</span>
        {issues.length > 0 && (
          <Badge variant="outline">
            {issues.length} {vietnamese ? "lỗi" : "issues"}
          </Badge>
        )}
      </div>
    );
  }

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Radio className="h-5 w-5 text-blue-500" />
            {vietnamese ? "Giám sát chất lượng" : "Quality Monitor"}
          </CardTitle>
        </div>
        <ConnectionStatus
          state={connectionState}
          vietnamese={vietnamese}
          showControls={showControls}
          onConnect={connect}
          onDisconnect={disconnect}
          onReset={reset}
        />
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Overall Progress */}
        <OverallProgress
          progress={progress}
          currentGate={currentGate}
          vietnamese={vietnamese}
        />

        {/* Summary Stats */}
        {(connectionState === "connected" ||
          connectionState === "completed") && (
          <div className="flex items-center gap-3">
            <Badge
              variant={stats.passedGates > 0 ? "default" : "outline"}
              className="bg-green-500"
            >
              {stats.passedGates} {vietnamese ? "đạt" : "passed"}
            </Badge>
            <Badge
              variant={stats.failedGates > 0 ? "destructive" : "outline"}
            >
              {stats.failedGates} {vietnamese ? "lỗi" : "failed"}
            </Badge>
            {stats.criticalCount > 0 && (
              <Badge variant="destructive">
                {stats.criticalCount} {vietnamese ? "nghiêm trọng" : "critical"}
              </Badge>
            )}
            {stats.highCount > 0 && (
              <Badge className="bg-orange-500">
                {stats.highCount} {vietnamese ? "cao" : "high"}
              </Badge>
            )}
          </div>
        )}

        <Separator />

        {/* Gate Details */}
        {showGateDetails && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {vietnamese ? "Chi tiết cổng" : "Gate Details"}
            </h4>
            <div className="grid grid-cols-2 gap-2">
              {gateOrder.map((gateName) => (
                <LiveGateStatus
                  key={gateName}
                  gate={gates[gateName]}
                  isCurrent={currentGate === gateName}
                  vietnamese={vietnamese}
                />
              ))}
            </div>
          </div>
        )}

        {/* Live Issue Feed */}
        {showIssueFeed && (
          <>
            <Separator />
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {vietnamese ? "Lỗi phát hiện" : "Issues Found"}
                </h4>
                {issues.length > 0 && (
                  <Badge variant="secondary">{issues.length}</Badge>
                )}
              </div>
              <LiveIssueFeed
                issues={issues}
                maxItems={maxIssueFeedItems}
                vietnamese={vietnamese}
              />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};

// ============================================================================
// Standalone Component (without context)
// ============================================================================

export interface StandaloneLiveMonitorProps extends LiveQualityMonitorProps {
  /** SSE endpoint URL */
  url: string;
  /** Session ID */
  sessionId: string;
  /** Auto-connect */
  autoConnect?: boolean;
}

export const StandaloneLiveMonitor: React.FC<StandaloneLiveMonitorProps> = ({
  url,
  sessionId,
  autoConnect = false,
  ...props
}) => {
  const QualityStreamProvider = React.lazy(
    () => import("./QualityStreamProvider")
  );

  return (
    <React.Suspense fallback={<div>Loading...</div>}>
      <QualityStreamProvider
        url={url}
        sessionId={sessionId}
        autoConnect={autoConnect}
      >
        <LiveQualityMonitor {...props} />
      </QualityStreamProvider>
    </React.Suspense>
  );
};

export default LiveQualityMonitor;
