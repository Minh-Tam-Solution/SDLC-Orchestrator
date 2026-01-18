/**
 * =========================================================================
 * BacklogKanbanBoard - Visual Kanban Board for Sprint Backlog
 * SDLC Orchestrator - Sprint 75 Day 5
 *
 * Version: 1.0.0
 * Date: January 18, 2026
 * Status: ACTIVE - Sprint 75 Sprint Dashboard UI
 * Authority: Frontend Lead + CTO Approved
 * Framework: SDLC 5.1.3 Sprint Planning Governance
 *
 * Purpose:
 * - Visual Kanban board for sprint backlog
 * - Column-based status display (Todo, In Progress, Review, Done)
 * - Drag-and-drop item movement (future enhancement)
 * - Priority and type visual indicators
 *
 * SDLC 5.1.3 Compliance:
 * - Rule #8: P0/P1/P2 priority visual indicators
 * - Status workflow: todo → in_progress → review → done
 * =========================================================================
 */

import { useMemo } from "react";
import {
  CheckCircle2,
  Circle,
  Clock,
  Eye,
  AlertTriangle,
  Bug,
  FileText,
  Lightbulb,
  BookOpen,
  GripVertical,
  User,
} from "lucide-react";
import {
  BacklogItemWithDetails,
  BacklogItemStatus,
  BacklogItemType,
  Priority,
} from "@/hooks/usePlanning";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

/**
 * Kanban column configuration
 */
const KANBAN_COLUMNS: {
  status: BacklogItemStatus;
  label: string;
  icon: React.ReactNode;
  className: string;
  headerClassName: string;
}[] = [
  {
    status: "todo",
    label: "To Do",
    icon: <Circle className="w-4 h-4" />,
    className: "bg-gray-50 dark:bg-gray-900/50",
    headerClassName: "text-gray-700 dark:text-gray-300 border-gray-300",
  },
  {
    status: "in_progress",
    label: "In Progress",
    icon: <Clock className="w-4 h-4" />,
    className: "bg-blue-50 dark:bg-blue-900/20",
    headerClassName: "text-blue-700 dark:text-blue-300 border-blue-400",
  },
  {
    status: "review",
    label: "Review",
    icon: <Eye className="w-4 h-4" />,
    className: "bg-purple-50 dark:bg-purple-900/20",
    headerClassName: "text-purple-700 dark:text-purple-300 border-purple-400",
  },
  {
    status: "done",
    label: "Done",
    icon: <CheckCircle2 className="w-4 h-4" />,
    className: "bg-green-50 dark:bg-green-900/20",
    headerClassName: "text-green-700 dark:text-green-300 border-green-400",
  },
];

/**
 * BacklogKanbanBoard Props
 */
interface BacklogKanbanBoardProps {
  items: BacklogItemWithDetails[];
  isLoading: boolean;
  onItemClick?: (item: BacklogItemWithDetails) => void;
}

/**
 * BacklogKanbanBoard Component
 * Displays backlog items in a Kanban board layout
 */
export default function BacklogKanbanBoard({
  items,
  isLoading,
  onItemClick,
}: BacklogKanbanBoardProps) {
  // Group items by status
  const itemsByStatus = useMemo(() => {
    const grouped: Record<BacklogItemStatus, BacklogItemWithDetails[]> = {
      todo: [],
      in_progress: [],
      review: [],
      done: [],
      blocked: [],
    };

    items.forEach((item) => {
      if (grouped[item.status]) {
        grouped[item.status].push(item);
      }
    });

    // Sort each column by priority (P0 first)
    Object.keys(grouped).forEach((status) => {
      grouped[status as BacklogItemStatus].sort((a, b) => {
        const priorityOrder: Record<Priority, number> = { P0: 0, P1: 1, P2: 2 };
        return priorityOrder[a.priority] - priorityOrder[b.priority];
      });
    });

    return grouped;
  }, [items]);

  // Get blocked items (shown as overlay on their original column)
  const blockedItems = useMemo(() => {
    return items.filter((item) => item.status === "blocked");
  }, [items]);

  if (isLoading) {
    return <KanbanLoadingSkeleton />;
  }

  return (
    <TooltipProvider>
      <div className="w-full">
        {/* Blocked Items Warning */}
        {blockedItems.length > 0 && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
              <AlertTriangle className="w-4 h-4" />
              <span className="font-medium">
                {blockedItems.length} item{blockedItems.length > 1 ? "s" : ""} blocked
              </span>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {blockedItems.map((item) => (
                <Badge
                  key={item.id}
                  variant="outline"
                  className="bg-red-100 text-red-700 border-red-200 cursor-pointer"
                  onClick={() => onItemClick?.(item)}
                >
                  {item.title.slice(0, 30)}
                  {item.title.length > 30 ? "..." : ""}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Kanban Board */}
        <div className="grid grid-cols-4 gap-4">
          {KANBAN_COLUMNS.map((column) => (
            <KanbanColumn
              key={column.status}
              column={column}
              items={itemsByStatus[column.status]}
              onItemClick={onItemClick}
            />
          ))}
        </div>

        {/* Story Points Summary */}
        <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
          <div className="flex items-center gap-4">
            <span>
              Total: <strong>{items.length}</strong> items
            </span>
            <span>
              Done:{" "}
              <strong>
                {itemsByStatus.done.length}/{items.length}
              </strong>
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span>
              Story Points:{" "}
              <strong>
                {items
                  .filter((i) => i.status === "done")
                  .reduce((acc, i) => acc + (i.story_points || 0), 0)}
                /
                {items.reduce((acc, i) => acc + (i.story_points || 0), 0)}
              </strong>
            </span>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}

/**
 * Kanban Column Component
 */
interface KanbanColumnProps {
  column: (typeof KANBAN_COLUMNS)[number];
  items: BacklogItemWithDetails[];
  onItemClick?: (item: BacklogItemWithDetails) => void;
}

function KanbanColumn({ column, items, onItemClick }: KanbanColumnProps) {
  const totalPoints = items.reduce((acc, i) => acc + (i.story_points || 0), 0);

  return (
    <div className={cn("rounded-lg border", column.className)}>
      {/* Column Header */}
      <div
        className={cn(
          "px-3 py-2 border-b-2 flex items-center justify-between",
          column.headerClassName
        )}
      >
        <div className="flex items-center gap-2">
          {column.icon}
          <span className="font-medium">{column.label}</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Badge variant="secondary" className="h-5 px-1.5">
            {items.length}
          </Badge>
          {totalPoints > 0 && (
            <span className="text-xs text-muted-foreground">
              {totalPoints} SP
            </span>
          )}
        </div>
      </div>

      {/* Column Content */}
      <ScrollArea className="h-[400px]">
        <div className="p-2 space-y-2">
          {items.length === 0 ? (
            <div className="flex items-center justify-center h-20 text-sm text-muted-foreground">
              No items
            </div>
          ) : (
            items.map((item) => (
              <KanbanCard
                key={item.id}
                item={item}
                onClick={() => onItemClick?.(item)}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

/**
 * Kanban Card Component
 */
interface KanbanCardProps {
  item: BacklogItemWithDetails;
  onClick?: () => void;
}

function KanbanCard({ item, onClick }: KanbanCardProps) {
  return (
    <Card
      className={cn(
        "cursor-pointer hover:shadow-md transition-shadow",
        item.status === "blocked" && "border-red-300 bg-red-50 dark:bg-red-900/20"
      )}
      onClick={onClick}
    >
      <CardHeader className="p-3 pb-2">
        <div className="flex items-start gap-2">
          {/* Drag Handle (visual only for now) */}
          <GripVertical className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0 opacity-50" />

          {/* Type Icon */}
          <TypeIcon type={item.type} />

          {/* Title */}
          <CardTitle className="text-sm font-medium leading-tight flex-1 line-clamp-2">
            {item.title}
          </CardTitle>
        </div>
      </CardHeader>

      <CardContent className="p-3 pt-0">
        <div className="flex items-center justify-between">
          {/* Left: Priority + Points */}
          <div className="flex items-center gap-2">
            <PriorityBadge priority={item.priority} />
            {item.story_points && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge variant="outline" className="h-5 px-1.5 text-xs">
                    {item.story_points} SP
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>Story Points</TooltipContent>
              </Tooltip>
            )}
          </div>

          {/* Right: Assignee */}
          {item.assignee ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs font-medium text-primary">
                  {getInitials(item.assignee.full_name || item.assignee.email)}
                </div>
              </TooltipTrigger>
              <TooltipContent>
                {item.assignee.full_name || item.assignee.email}
              </TooltipContent>
            </Tooltip>
          ) : (
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="w-6 h-6 rounded-full bg-muted flex items-center justify-center">
                  <User className="w-3 h-3 text-muted-foreground" />
                </div>
              </TooltipTrigger>
              <TooltipContent>Unassigned</TooltipContent>
            </Tooltip>
          )}
        </div>

        {/* Subtasks Progress */}
        {item.children_count > 0 && (
          <div className="mt-2 pt-2 border-t">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>
                Subtasks: {item.completed_children_count}/{item.children_count}
              </span>
              <span>
                {Math.round(
                  (item.completed_children_count / item.children_count) * 100
                )}
                %
              </span>
            </div>
            <div className="mt-1 h-1 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all"
                style={{
                  width: `${(item.completed_children_count / item.children_count) * 100}%`,
                }}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Type Icon Component
 */
function TypeIcon({ type }: { type: BacklogItemType }) {
  const config = getTypeIconConfig(type);
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className={cn("flex-shrink-0", config.className)}>
          {config.icon}
        </div>
      </TooltipTrigger>
      <TooltipContent>{config.label}</TooltipContent>
    </Tooltip>
  );
}

function getTypeIconConfig(type: BacklogItemType) {
  switch (type) {
    case "story":
      return {
        icon: <BookOpen className="w-4 h-4" />,
        className: "text-blue-500",
        label: "Story",
      };
    case "task":
      return {
        icon: <FileText className="w-4 h-4" />,
        className: "text-green-500",
        label: "Task",
      };
    case "bug":
      return {
        icon: <Bug className="w-4 h-4" />,
        className: "text-red-500",
        label: "Bug",
      };
    case "spike":
      return {
        icon: <Lightbulb className="w-4 h-4" />,
        className: "text-yellow-500",
        label: "Spike",
      };
    default:
      return {
        icon: <FileText className="w-4 h-4" />,
        className: "text-gray-500",
        label: type,
      };
  }
}

/**
 * Priority Badge Component
 */
function PriorityBadge({ priority }: { priority: Priority }) {
  const config = getPriorityConfig(priority);
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge variant="outline" className={cn("h-5 px-1.5", config.className)}>
          {priority}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>{config.tooltip}</TooltipContent>
    </Tooltip>
  );
}

function getPriorityConfig(priority: Priority) {
  switch (priority) {
    case "P0":
      return {
        className: "bg-red-100 text-red-700 border-red-200",
        tooltip: "P0 - Must Have (Critical)",
      };
    case "P1":
      return {
        className: "bg-yellow-100 text-yellow-700 border-yellow-200",
        tooltip: "P1 - Should Have (Important)",
      };
    case "P2":
      return {
        className: "bg-gray-100 text-gray-700 border-gray-200",
        tooltip: "P2 - Could Have (Nice to have)",
      };
    default:
      return {
        className: "",
        tooltip: priority,
      };
  }
}

/**
 * Get initials from name or email
 */
function getInitials(name: string): string {
  if (!name) return "??";
  const parts = name.split(/[\s@]+/);
  if (parts.length >= 2 && parts[0] && parts[1]) {
    const first = parts[0][0] || "";
    const second = parts[1][0] || "";
    return (first + second).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

/**
 * Loading Skeleton for Kanban Board
 */
function KanbanLoadingSkeleton() {
  return (
    <div className="grid grid-cols-4 gap-4">
      {KANBAN_COLUMNS.map((column) => (
        <div key={column.status} className="rounded-lg border bg-muted/30">
          <div className="px-3 py-2 border-b flex items-center justify-between">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-5 w-8" />
          </div>
          <div className="p-2 space-y-2">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-24 w-full rounded-lg" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
