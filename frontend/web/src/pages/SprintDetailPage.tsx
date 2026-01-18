/**
 * =========================================================================
 * SprintDetailPage - Sprint Detail and Management
 * SDLC Orchestrator - Sprint 75 Day 5
 *
 * Version: 1.1.0
 * Date: January 18, 2026
 * Status: ACTIVE - Sprint 75 Sprint Dashboard UI
 * Authority: Frontend Lead + CTO Approved
 * Framework: SDLC 5.1.3 Sprint Planning Governance
 *
 * Purpose:
 * - Display sprint details and progress
 * - Show backlog items with status (List + Kanban views)
 * - G-Sprint/G-Sprint-Close gate management
 * - Sprint status transitions
 *
 * SDLC 5.1.3 Compliance:
 * - Rule #1: Sprint number displayed (immutable)
 * - Rule #2: 24h documentation for G-Sprint-Close
 * - G-Sprint/G-Sprint-Close: Gate approval workflow
 * - SE4H Coach: Admin/owner gate approval
 * =========================================================================
 */

import { useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  Calendar,
  Target,
  Users,
  CheckCircle2,
  Clock,
  AlertCircle,
  PlayCircle,
  FileText,
  BarChart3,
  ListTodo,
  Shield,
  LayoutGrid,
  List,
} from "lucide-react";
import {
  useSprint,
  useSprintStatistics,
  useSprintGates,
  useBacklogItems,
} from "@/hooks/usePlanning";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import SprintGatePanel from "@/components/sprints/SprintGatePanel";
import SprintBacklogList from "@/components/sprints/SprintBacklogList";
import BacklogKanbanBoard from "@/components/sprints/BacklogKanbanBoard";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

/** Backlog view type */
type BacklogViewType = "list" | "kanban";

/**
 * Sprint Detail Page
 * Shows comprehensive sprint information with gate management
 */
export default function SprintDetailPage() {
  const { sprintId } = useParams<{ sprintId: string }>();
  const [backlogView, setBacklogView] = useState<BacklogViewType>("list");

  const { data: sprint, isLoading: isLoadingSprint } = useSprint(
    sprintId || null
  );
  const { data: statistics } = useSprintStatistics(sprintId || null);
  const { data: gatesData } = useSprintGates(sprintId || null);
  const { data: backlogData } = useBacklogItems({
    sprintId: sprintId || undefined,
  });

  // Get G-Sprint and G-Sprint-Close gate evaluations
  const gSprintGate = useMemo(() => {
    return gatesData?.items.find((g) => g.gate_type === "g_sprint");
  }, [gatesData]);

  const gSprintCloseGate = useMemo(() => {
    return gatesData?.items.find((g) => g.gate_type === "g_sprint_close");
  }, [gatesData]);

  // Calculate progress
  const progressPercent = useMemo(() => {
    if (!statistics || statistics.total_items === 0) return 0;
    return Math.round(
      (statistics.completed_items / statistics.total_items) * 100
    );
  }, [statistics]);

  // Calculate story points progress
  const storyPointsPercent = useMemo(() => {
    if (!statistics || statistics.total_story_points === 0) return 0;
    return Math.round(
      (statistics.completed_story_points / statistics.total_story_points) * 100
    );
  }, [statistics]);

  if (isLoadingSprint) {
    return <SprintDetailSkeleton />;
  }

  if (!sprint) {
    return (
      <div className="container mx-auto py-6">
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <AlertCircle className="w-12 h-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">Sprint not found</h3>
          <p className="text-muted-foreground mb-4">
            The sprint you&apos;re looking for doesn&apos;t exist or you
            don&apos;t have access.
          </p>
          <Link to="/sprints">
            <Button>Back to Sprints</Button>
          </Link>
        </div>
      </div>
    );
  }

  const statusConfig = getStatusConfig(sprint.status);

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <Link to={`/sprints?project=${sprint.project_id}`}>
              <Button variant="ghost" size="sm">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
            </Link>
            <Badge variant="outline" className="text-lg px-3 py-1">
              S{sprint.number}
            </Badge>
            <Badge
              variant={statusConfig.variant}
              className={statusConfig.className}
            >
              {statusConfig.icon}
              {statusConfig.label}
            </Badge>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">{sprint.name}</h1>
          {sprint.goal && (
            <p className="text-muted-foreground max-w-2xl">{sprint.goal}</p>
          )}
        </div>

        {/* Action Buttons based on status */}
        <div className="flex items-center gap-2">
          {sprint.status === "planning" &&
            sprint.g_sprint_status === "approved" && (
              <Button>
                <PlayCircle className="w-4 h-4 mr-2" />
                Start Sprint
              </Button>
            )}
          {sprint.status === "in_progress" && (
            <Button variant="outline">
              <CheckCircle2 className="w-4 h-4 mr-2" />
              Complete Sprint
            </Button>
          )}
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Progress</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{progressPercent}%</div>
            <Progress value={progressPercent} className="h-2 mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {statistics?.completed_items || 0} / {statistics?.total_items || 0}{" "}
              items
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Story Points</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statistics?.completed_story_points || 0} /{" "}
              {statistics?.total_story_points || sprint.capacity_points || 0}
            </div>
            <Progress value={storyPointsPercent} className="h-2 mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {storyPointsPercent}% completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Duration</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {sprint.start_date && sprint.end_date ? (
              <>
                <div className="text-2xl font-bold">
                  {calculateDuration(sprint.start_date, sprint.end_date)} days
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {formatDate(sprint.start_date)} - {formatDate(sprint.end_date)}
                </p>
              </>
            ) : (
              <>
                <div className="text-2xl font-bold">-</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Dates not set
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Team</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{sprint.team_size || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">team members</p>
          </CardContent>
        </Card>
      </div>

      {/* Priority Breakdown (by Rule #8) */}
      {statistics && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Priority Breakdown (SDLC 5.1.3 Rule #8)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="flex items-center justify-between p-3 rounded-lg bg-red-50 border border-red-200">
                <div>
                  <div className="font-medium text-red-700">P0 - Must Have</div>
                  <div className="text-sm text-red-600">
                    {statistics.by_priority.P0.completed} /{" "}
                    {statistics.by_priority.P0.total} completed
                  </div>
                </div>
                <Badge variant="destructive">
                  {statistics.by_priority.P0.total}
                </Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-yellow-50 border border-yellow-200">
                <div>
                  <div className="font-medium text-yellow-700">
                    P1 - Should Have
                  </div>
                  <div className="text-sm text-yellow-600">
                    {statistics.by_priority.P1.completed} /{" "}
                    {statistics.by_priority.P1.total} completed
                  </div>
                </div>
                <Badge className="bg-yellow-500">
                  {statistics.by_priority.P1.total}
                </Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50 border border-gray-200">
                <div>
                  <div className="font-medium text-gray-700">
                    P2 - Could Have
                  </div>
                  <div className="text-sm text-gray-600">
                    {statistics.by_priority.P2.completed} /{" "}
                    {statistics.by_priority.P2.total} completed
                  </div>
                </div>
                <Badge variant="secondary">
                  {statistics.by_priority.P2.total}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs: Gates, Backlog, Details */}
      <Tabs defaultValue="gates" className="space-y-4">
        <TabsList>
          <TabsTrigger value="gates" className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Gates
          </TabsTrigger>
          <TabsTrigger value="backlog" className="flex items-center gap-2">
            <ListTodo className="w-4 h-4" />
            Backlog ({backlogData?.total || 0})
          </TabsTrigger>
          <TabsTrigger value="details" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Details
          </TabsTrigger>
        </TabsList>

        {/* Gates Tab */}
        <TabsContent value="gates" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <SprintGatePanel
              sprintId={sprintId!}
              gateType="g_sprint"
              gateEvaluation={gSprintGate}
              sprintStatus={sprint.status}
              canEvaluate={sprint.status === "planning"}
            />
            <SprintGatePanel
              sprintId={sprintId!}
              gateType="g_sprint_close"
              gateEvaluation={gSprintCloseGate}
              sprintStatus={sprint.status}
              canEvaluate={
                sprint.status === "completed" &&
                sprint.g_sprint_status === "approved"
              }
            />
          </div>
        </TabsContent>

        {/* Backlog Tab */}
        <TabsContent value="backlog" className="space-y-4">
          {/* View Toggle */}
          <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              {backlogData?.total || 0} items in backlog
            </div>
            <ToggleGroup
              type="single"
              value={backlogView}
              onValueChange={(v) => v && setBacklogView(v as BacklogViewType)}
            >
              <ToggleGroupItem value="list" aria-label="List view">
                <List className="w-4 h-4 mr-2" />
                List
              </ToggleGroupItem>
              <ToggleGroupItem value="kanban" aria-label="Kanban view">
                <LayoutGrid className="w-4 h-4 mr-2" />
                Kanban
              </ToggleGroupItem>
            </ToggleGroup>
          </div>

          {/* Backlog View */}
          {backlogView === "list" ? (
            <SprintBacklogList
              sprintId={sprintId!}
              projectId={sprint.project_id}
              items={backlogData?.items || []}
              isLoading={!backlogData}
            />
          ) : (
            <BacklogKanbanBoard
              items={backlogData?.items || []}
              isLoading={!backlogData}
            />
          )}
        </TabsContent>

        {/* Details Tab */}
        <TabsContent value="details">
          <Card>
            <CardHeader>
              <CardTitle>Sprint Details</CardTitle>
              <CardDescription>
                Detailed information about this sprint
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <div className="text-sm font-medium text-muted-foreground">
                    Sprint Number
                  </div>
                  <div className="text-lg font-semibold">
                    S{sprint.number}{" "}
                    <span className="text-xs text-muted-foreground">
                      (immutable)
                    </span>
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">
                    Created
                  </div>
                  <div className="text-lg">
                    {formatDateTime(sprint.created_at)}
                  </div>
                </div>
                {sprint.approved_at && (
                  <div>
                    <div className="text-sm font-medium text-muted-foreground">
                      G-Sprint Approved
                    </div>
                    <div className="text-lg">
                      {formatDateTime(sprint.approved_at)}
                    </div>
                  </div>
                )}
                {sprint.closed_at && (
                  <div>
                    <div className="text-sm font-medium text-muted-foreground">
                      Sprint Closed
                    </div>
                    <div className="text-lg">
                      {formatDateTime(sprint.closed_at)}
                    </div>
                  </div>
                )}
              </div>

              {sprint.goal && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-1">
                    Sprint Goal
                  </div>
                  <div className="p-3 rounded-lg bg-muted">{sprint.goal}</div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

/**
 * Get status configuration for display
 */
function getStatusConfig(status: string) {
  switch (status) {
    case "planning":
      return {
        label: "Planning",
        variant: "secondary" as const,
        className: "bg-yellow-100 text-yellow-700 border-yellow-200",
        icon: <Clock className="w-3 h-3 mr-1" />,
      };
    case "in_progress":
      return {
        label: "In Progress",
        variant: "default" as const,
        className: "bg-blue-100 text-blue-700 border-blue-200",
        icon: <PlayCircle className="w-3 h-3 mr-1" />,
      };
    case "completed":
      return {
        label: "Completed",
        variant: "default" as const,
        className: "bg-green-100 text-green-700 border-green-200",
        icon: <CheckCircle2 className="w-3 h-3 mr-1" />,
      };
    case "closed":
      return {
        label: "Closed",
        variant: "outline" as const,
        className: "bg-gray-100 text-gray-700 border-gray-200",
        icon: <CheckCircle2 className="w-3 h-3 mr-1" />,
      };
    default:
      return {
        label: status,
        variant: "outline" as const,
        className: "",
        icon: null,
      };
  }
}

/**
 * Calculate duration between two dates
 */
function calculateDuration(startDate: string, endDate: string): number {
  const start = new Date(startDate);
  const end = new Date(endDate);
  return Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
}

/**
 * Format date for display
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/**
 * Format datetime for display
 */
function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Loading Skeleton Component
 */
function SprintDetailSkeleton() {
  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <Skeleton className="h-9 w-20" />
          <Skeleton className="h-8 w-16" />
          <Skeleton className="h-6 w-24" />
        </div>
        <Skeleton className="h-10 w-1/2" />
        <Skeleton className="h-5 w-2/3" />
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-20" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-24 mb-2" />
              <Skeleton className="h-2 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>

      <Skeleton className="h-10 w-64" />
      <Skeleton className="h-96 w-full" />
    </div>
  );
}
