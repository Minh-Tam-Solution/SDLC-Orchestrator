"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Users,
  FileText,
  RefreshCw,
  Download,
  Info,
} from "lucide-react";

// Types
interface DogfoodingMetrics {
  sprint: string;
  mode: "WARNING" | "SOFT" | "FULL" | "OFF";
  startDate: string;
  endDate: string;
  daysElapsed: number;
  totalDays: number;

  // PR Metrics
  prsEvaluated: number;
  prsTarget: number;

  // Vibecoding Index Distribution
  distribution: {
    green: number;
    yellow: number;
    orange: number;
    red: number;
  };
  averageIndex: number;

  // Developer Friction
  avgFrictionMinutes: number;
  frictionTarget: number;

  // Accuracy
  falsePositiveRate: number;
  falsePositiveTarget: number;

  // Team Satisfaction
  teamNPS: number | null;
  npsTarget: number;

  // Go/No-Go Readiness
  goNoGoReady: boolean;
  blockers: string[];
}

interface PRMetric {
  prNumber: number;
  title: string;
  author: string;
  vibecodeIndex: number;
  zone: "green" | "yellow" | "orange" | "red";
  frictionMinutes: number;
  autoGenUsed: boolean;
  timestamp: string;
}

// Mock data for Sprint 114 dogfooding
const mockMetrics: DogfoodingMetrics = {
  sprint: "114",
  mode: "WARNING",
  startDate: "2026-02-03",
  endDate: "2026-02-07",
  daysElapsed: 1,
  totalDays: 5,

  prsEvaluated: 3,
  prsTarget: 15,

  distribution: {
    green: 2,
    yellow: 1,
    orange: 0,
    red: 0,
  },
  averageIndex: 25,

  avgFrictionMinutes: 4.5,
  frictionTarget: 10,

  falsePositiveRate: 0,
  falsePositiveTarget: 20,

  teamNPS: null, // Survey not started yet
  npsTarget: 50,

  goNoGoReady: false,
  blockers: [
    "Need 15+ PRs evaluated (currently: 3)",
    "Team NPS survey not completed",
  ],
};

const mockPRHistory: PRMetric[] = [
  {
    prNumber: 1234,
    title: "feat: Add governance dashboard components",
    author: "developer1",
    vibecodeIndex: 22,
    zone: "green",
    frictionMinutes: 3,
    autoGenUsed: true,
    timestamp: "2026-02-03T09:15:00Z",
  },
  {
    prNumber: 1235,
    title: "fix: Resolve type errors in kill switch",
    author: "developer2",
    vibecodeIndex: 18,
    zone: "green",
    frictionMinutes: 2,
    autoGenUsed: true,
    timestamp: "2026-02-03T11:30:00Z",
  },
  {
    prNumber: 1236,
    title: "refactor: Update metrics collection service",
    author: "developer1",
    vibecodeIndex: 45,
    zone: "yellow",
    frictionMinutes: 8,
    autoGenUsed: false,
    timestamp: "2026-02-03T14:45:00Z",
  },
];

// Components
function MetricCard({
  title,
  value,
  target,
  unit,
  icon: Icon,
  status,
}: {
  title: string;
  value: number | string;
  target?: number | string;
  unit?: string;
  icon: React.ElementType;
  status: "success" | "warning" | "error" | "neutral";
}) {
  const statusColors = {
    success: "text-green-600 bg-green-50 border-green-200",
    warning: "text-yellow-600 bg-yellow-50 border-yellow-200",
    error: "text-red-600 bg-red-50 border-red-200",
    neutral: "text-gray-600 bg-gray-50 border-gray-200",
  };

  return (
    <Card className={`border ${statusColors[status]}`}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {value}
          {unit && <span className="text-sm font-normal ml-1">{unit}</span>}
        </div>
        {target && (
          <p className="text-xs text-muted-foreground mt-1">Target: {target}{unit}</p>
        )}
      </CardContent>
    </Card>
  );
}

function VibecodingDistributionChart({ distribution }: { distribution: DogfoodingMetrics["distribution"] }) {
  const total = distribution.green + distribution.yellow + distribution.orange + distribution.red;
  const getPercent = (count: number) => (total > 0 ? (count / total) * 100 : 0);

  const zones = [
    { name: "Green", count: distribution.green, color: "bg-green-500", range: "0-30" },
    { name: "Yellow", count: distribution.yellow, color: "bg-yellow-500", range: "31-60" },
    { name: "Orange", count: distribution.orange, color: "bg-orange-500", range: "61-80" },
    { name: "Red", count: distribution.red, color: "bg-red-500", range: "81-100" },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Vibecoding Index Distribution
        </CardTitle>
        <CardDescription>PR distribution across quality zones</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {zones.map((zone) => (
          <div key={zone.name} className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${zone.color}`} />
                {zone.name} ({zone.range})
              </span>
              <span className="font-medium">
                {zone.count} ({getPercent(zone.count).toFixed(0)}%)
              </span>
            </div>
            <Progress value={getPercent(zone.count)} className="h-2" />
          </div>
        ))}
        <div className="pt-2 border-t">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Total PRs</span>
            <span className="font-medium">{total}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function GoNoGoStatus({ metrics }: { metrics: DogfoodingMetrics }) {
  const checks = [
    {
      name: "PRs Evaluated",
      current: metrics.prsEvaluated,
      target: metrics.prsTarget,
      unit: " PRs",
      passed: metrics.prsEvaluated >= metrics.prsTarget,
    },
    {
      name: "Developer Friction",
      current: metrics.avgFrictionMinutes,
      target: metrics.frictionTarget,
      unit: " min",
      passed: metrics.avgFrictionMinutes <= metrics.frictionTarget,
    },
    {
      name: "False Positive Rate",
      current: metrics.falsePositiveRate,
      target: metrics.falsePositiveTarget,
      unit: "%",
      passed: metrics.falsePositiveRate <= metrics.falsePositiveTarget,
    },
    {
      name: "Team NPS",
      current: metrics.teamNPS ?? "N/A",
      target: metrics.npsTarget,
      unit: "",
      passed: metrics.teamNPS !== null && metrics.teamNPS >= metrics.npsTarget,
    },
  ];

  const allPassed = checks.every((c) => c.passed);

  return (
    <Card className={allPassed ? "border-green-500" : "border-yellow-500"}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {allPassed ? (
            <CheckCircle className="h-5 w-5 text-green-600" />
          ) : (
            <AlertTriangle className="h-5 w-5 text-yellow-600" />
          )}
          Go/No-Go Decision
        </CardTitle>
        <CardDescription>
          Sprint 115 (SOFT Mode) readiness assessment
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {checks.map((check) => (
            <div key={check.name} className="flex items-center justify-between">
              <span className="text-sm">{check.name}</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">
                  {check.current}
                  {check.unit} / {check.target}
                  {check.unit}
                </span>
                {check.passed ? (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 pt-4 border-t">
          <Badge variant={allPassed ? "default" : "secondary"} className="w-full justify-center py-2">
            {allPassed ? "READY FOR SOFT MODE" : "NOT READY - Continue Dogfooding"}
          </Badge>
        </div>

        {metrics.blockers.length > 0 && (
          <div className="mt-4">
            <p className="text-sm font-medium text-muted-foreground mb-2">Blockers:</p>
            <ul className="text-sm text-muted-foreground space-y-1">
              {metrics.blockers.map((blocker, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-yellow-600">•</span>
                  {blocker}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PRHistoryTable({ prs }: { prs: PRMetric[] }) {
  const zoneColors = {
    green: "bg-green-100 text-green-800",
    yellow: "bg-yellow-100 text-yellow-800",
    orange: "bg-orange-100 text-orange-800",
    red: "bg-red-100 text-red-800",
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          PR Evaluation History
        </CardTitle>
        <CardDescription>Recent PRs evaluated in WARNING mode</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 font-medium">PR</th>
                <th className="text-left py-2 font-medium">Index</th>
                <th className="text-left py-2 font-medium">Zone</th>
                <th className="text-left py-2 font-medium">Friction</th>
                <th className="text-left py-2 font-medium">Auto-Gen</th>
              </tr>
            </thead>
            <tbody>
              {prs.map((pr) => (
                <tr key={pr.prNumber} className="border-b last:border-0">
                  <td className="py-2">
                    <div>
                      <span className="font-medium">#{pr.prNumber}</span>
                      <p className="text-xs text-muted-foreground truncate max-w-[200px]">
                        {pr.title}
                      </p>
                    </div>
                  </td>
                  <td className="py-2 font-mono">{pr.vibecodeIndex}</td>
                  <td className="py-2">
                    <Badge className={zoneColors[pr.zone]}>{pr.zone}</Badge>
                  </td>
                  <td className="py-2">{pr.frictionMinutes} min</td>
                  <td className="py-2">
                    {pr.autoGenUsed ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

// Main Component
export default function DogfoodingDashboard() {
  const [metrics, setMetrics] = useState<DogfoodingMetrics>(mockMetrics);
  const [prHistory, setPRHistory] = useState<PRMetric[]>(mockPRHistory);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const handleRefresh = async () => {
    setIsRefreshing(true);
    // TODO: Fetch real metrics from API
    // const response = await fetch('/api/v1/governance/dogfooding/metrics');
    // const data = await response.json();
    // setMetrics(data);
    setTimeout(() => {
      setIsRefreshing(false);
      setLastUpdated(new Date());
    }, 1000);
  };

  const handleExportReport = () => {
    // TODO: Generate and download Sprint 114 metrics report
    const report = {
      sprint: metrics.sprint,
      mode: metrics.mode,
      period: { start: metrics.startDate, end: metrics.endDate },
      metrics: {
        prsEvaluated: metrics.prsEvaluated,
        averageIndex: metrics.averageIndex,
        distribution: metrics.distribution,
        avgFrictionMinutes: metrics.avgFrictionMinutes,
        falsePositiveRate: metrics.falsePositiveRate,
        teamNPS: metrics.teamNPS,
      },
      prHistory: prHistory,
      goNoGoReady: metrics.goNoGoReady,
      blockers: metrics.blockers,
      exportedAt: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sprint-${metrics.sprint}-dogfooding-report.json`;
    a.click();
  };

  const progressPercent = (metrics.daysElapsed / metrics.totalDays) * 100;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Sprint {metrics.sprint} Dogfooding Dashboard</h1>
          <p className="text-muted-foreground">
            WARNING Mode - Observing governance without blocking
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isRefreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportReport}>
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Sprint Progress */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Sprint Progress</span>
            <span className="text-sm text-muted-foreground">
              Day {metrics.daysElapsed} of {metrics.totalDays}
            </span>
          </div>
          <Progress value={progressPercent} className="h-2" />
          <div className="flex justify-between mt-2 text-xs text-muted-foreground">
            <span>{metrics.startDate}</span>
            <span>{metrics.endDate}</span>
          </div>
        </CardContent>
      </Card>

      {/* Mode Alert */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>WARNING Mode Active</AlertTitle>
        <AlertDescription>
          Governance violations are being logged but <strong>not blocking</strong> PRs.
          This helps calibrate thresholds before enforcement in Sprint 115.
        </AlertDescription>
      </Alert>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="PRs Evaluated"
          value={metrics.prsEvaluated}
          target={metrics.prsTarget}
          icon={FileText}
          status={metrics.prsEvaluated >= metrics.prsTarget ? "success" : "warning"}
        />
        <MetricCard
          title="Avg Vibecoding Index"
          value={metrics.averageIndex}
          target="< 40"
          icon={Activity}
          status={metrics.averageIndex < 40 ? "success" : metrics.averageIndex < 60 ? "warning" : "error"}
        />
        <MetricCard
          title="Developer Friction"
          value={metrics.avgFrictionMinutes}
          target={metrics.frictionTarget}
          unit=" min"
          icon={Clock}
          status={metrics.avgFrictionMinutes <= metrics.frictionTarget ? "success" : "warning"}
        />
        <MetricCard
          title="False Positive Rate"
          value={metrics.falsePositiveRate}
          target={metrics.falsePositiveTarget}
          unit="%"
          icon={AlertTriangle}
          status={metrics.falsePositiveRate <= metrics.falsePositiveTarget ? "success" : "error"}
        />
      </div>

      {/* Main Content */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="history">PR History</TabsTrigger>
          <TabsTrigger value="feedback">Team Feedback</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <VibecodingDistributionChart distribution={metrics.distribution} />
            <GoNoGoStatus metrics={metrics} />
          </div>
        </TabsContent>

        <TabsContent value="history">
          <PRHistoryTable prs={prHistory} />
        </TabsContent>

        <TabsContent value="feedback">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Team Feedback Survey
              </CardTitle>
              <CardDescription>
                Collect developer feedback on governance experience
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Alert>
                <Info className="h-4 w-4" />
                <AlertTitle>Survey Not Started</AlertTitle>
                <AlertDescription>
                  Team feedback survey will be sent on Day 4 (Feb 6).
                  Results will be used for Go/No-Go decision.
                </AlertDescription>
              </Alert>

              <div className="mt-4 space-y-2">
                <p className="text-sm font-medium">Survey Questions:</p>
                <ul className="text-sm text-muted-foreground space-y-1 ml-4">
                  <li>• How much did governance slow down your workflow? (1-5)</li>
                  <li>• How useful was auto-generated intent? (1-5)</li>
                  <li>• How accurate were ownership suggestions? (1-5)</li>
                  <li>• Would you recommend this system to other teams? (NPS 1-10)</li>
                  <li>• What improvements would you suggest? (Open text)</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Footer */}
      <div className="text-xs text-muted-foreground text-center">
        Last updated: {lastUpdated.toLocaleTimeString()} | Sprint 114 Track 2 | Dogfooding Mode
      </div>
    </div>
  );
}
