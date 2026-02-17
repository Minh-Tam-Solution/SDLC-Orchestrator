/**
 * Planning Hierarchy Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/planning/page
 * @description Full Planning Hierarchy visualization (Roadmap → Phase → Sprint)
 * @sdlc SDLC 6.0.6 Framework - Sprint 175 (Frontend Feature Completion)
 * @reference SDLC 6.0.6 Pillar 2: Sprint Planning Governance
 * @status Sprint 175 - Hook Wiring + Active Sprint Dashboard
 */

"use client";

import { useState } from "react";
import Link from "next/link";
import { useProjects } from "@/hooks/useProjects";
import {
  usePlanningHierarchy,
  useSprints,
  useActiveSprint,
  useActiveSprintDashboard,
  useBacklogItems,
  useDeleteRoadmap,
  useDeletePhase,
  useDeleteSprint,
} from "@/hooks/usePlanningHierarchy";
import { PlanningHierarchyTree, SprintTimeline } from "@/app/app/sprints/components";
import { RoadmapModal, PhaseModal } from "./components";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import type { Roadmap, Phase, BacklogItem } from "@/lib/types/planning";

// =============================================================================
// ICONS
// =============================================================================

function TreeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 0 1 0 3.75H5.625a1.875 1.875 0 0 1 0-3.75Z" />
    </svg>
  );
}

function ChartBarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
  );
}

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  );
}

function ArrowLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
    </svg>
  );
}

function ExclamationTriangleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
    </svg>
  );
}

// =============================================================================
// VIEW TOGGLE COMPONENT
// =============================================================================

type ViewMode = "tree" | "timeline";

function ViewToggle({
  activeView,
  onViewChange,
}: {
  activeView: ViewMode;
  onViewChange: (view: ViewMode) => void;
}) {
  return (
    <div className="flex items-center rounded-lg border border-gray-200 bg-white p-1">
      <button
        onClick={() => onViewChange("tree")}
        className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
          activeView === "tree"
            ? "bg-blue-100 text-blue-700"
            : "text-gray-600 hover:bg-gray-100"
        }`}
      >
        <TreeIcon className="h-4 w-4" />
        Tree View
      </button>
      <button
        onClick={() => onViewChange("timeline")}
        className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
          activeView === "timeline"
            ? "bg-blue-100 text-blue-700"
            : "text-gray-600 hover:bg-gray-100"
        }`}
      >
        <ChartBarIcon className="h-4 w-4" />
        Timeline
      </button>
    </div>
  );
}

// =============================================================================
// STATS CARDS
// =============================================================================

function StatsCards({
  totalRoadmaps,
  totalPhases,
  totalSprints,
  activeSprintName,
}: {
  totalRoadmaps: number;
  totalPhases: number;
  totalSprints: number;
  activeSprintName?: string;
}) {
  return (
    <div className="grid gap-4 md:grid-cols-4">
      <div className="rounded-lg border border-purple-200 bg-purple-50 p-4">
        <div className="text-2xl font-bold text-purple-700">{totalRoadmaps}</div>
        <div className="text-sm text-purple-600">Roadmaps</div>
      </div>
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
        <div className="text-2xl font-bold text-blue-700">{totalPhases}</div>
        <div className="text-sm text-blue-600">Phases</div>
      </div>
      <div className="rounded-lg border border-green-200 bg-green-50 p-4">
        <div className="text-2xl font-bold text-green-700">{totalSprints}</div>
        <div className="text-sm text-green-600">Sprints</div>
      </div>
      <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-4">
        <div className="truncate text-lg font-bold text-indigo-700">
          {activeSprintName || "None"}
        </div>
        <div className="text-sm text-indigo-600">Active Sprint</div>
      </div>
    </div>
  );
}

// =============================================================================
// DELETE CONFIRMATION DIALOG
// =============================================================================

interface DeleteConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  itemName: string;
  onConfirm: () => void;
  isDeleting: boolean;
}

function DeleteConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  itemName,
  onConfirm,
  isDeleting,
}: DeleteConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-red-600">
            <ExclamationTriangleIcon className="h-5 w-5" />
            {title}
          </DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <p className="text-sm text-gray-700">
            You are about to delete:{" "}
            <span className="font-semibold">&quot;{itemName}&quot;</span>
          </p>
          <p className="mt-2 text-sm text-red-600">
            This action cannot be undone. All child items will also be deleted.
          </p>
        </div>
        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={onConfirm}
            disabled={isDeleting}
          >
            {isDeleting ? "Deleting..." : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// =============================================================================
// LOADING SKELETON
// =============================================================================

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-20 animate-pulse rounded-lg bg-gray-200" />
        ))}
      </div>
      {/* Main Content */}
      <div className="h-[500px] animate-pulse rounded-xl bg-gray-200" />
    </div>
  );
}

// =============================================================================
// ACTIVE SPRINT PROGRESS PANEL
// =============================================================================

function ActiveSprintProgress({
  itemsByStatus,
}: {
  itemsByStatus: {
    todo: number;
    in_progress: number;
    review: number;
    done: number;
    carried_over: number;
  };
}) {
  const total =
    itemsByStatus.todo +
    itemsByStatus.in_progress +
    itemsByStatus.review +
    itemsByStatus.done +
    itemsByStatus.carried_over;

  if (total === 0) return null;

  const segments = [
    { label: "Done", count: itemsByStatus.done, color: "bg-green-500" },
    { label: "Review", count: itemsByStatus.review, color: "bg-blue-500" },
    { label: "In Progress", count: itemsByStatus.in_progress, color: "bg-yellow-500" },
    { label: "To Do", count: itemsByStatus.todo, color: "bg-gray-300" },
    { label: "Carried Over", count: itemsByStatus.carried_over, color: "bg-red-300" },
  ];

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Sprint Progress</h3>
      {/* Progress bar */}
      <div className="flex h-3 rounded-full overflow-hidden mb-3">
        {segments.map(
          (seg) =>
            seg.count > 0 && (
              <div
                key={seg.label}
                className={`${seg.color}`}
                style={{ width: `${(seg.count / total) * 100}%` }}
                title={`${seg.label}: ${seg.count}`}
              />
            )
        )}
      </div>
      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-xs text-gray-600">
        {segments
          .filter((s) => s.count > 0)
          .map((seg) => (
            <span key={seg.label} className="flex items-center gap-1">
              <span className={`h-2 w-2 rounded-full ${seg.color}`} />
              {seg.label}: {seg.count}
            </span>
          ))}
      </div>
    </div>
  );
}

// =============================================================================
// BACKLOG ITEMS PANEL
// =============================================================================

const PRIORITY_COLORS: Record<string, string> = {
  p0: "bg-red-100 text-red-700",
  p1: "bg-orange-100 text-orange-700",
  p2: "bg-yellow-100 text-yellow-700",
  p3: "bg-gray-100 text-gray-600",
};

const STATUS_COLORS: Record<string, string> = {
  todo: "bg-gray-100 text-gray-700",
  in_progress: "bg-blue-100 text-blue-700",
  review: "bg-purple-100 text-purple-700",
  done: "bg-green-100 text-green-700",
  carried_over: "bg-red-100 text-red-700",
};

function BacklogPanel({ items }: { items: BacklogItem[] }) {
  if (items.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 p-6 text-center text-sm text-gray-500">
        No backlog items in this sprint yet.
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <div className="px-4 py-3 border-b border-gray-100">
        <h3 className="text-sm font-medium text-gray-700">
          Backlog Items ({items.length})
        </h3>
      </div>
      <div className="divide-y divide-gray-100">
        {items.slice(0, 10).map((item) => (
          <div key={item.id} className="px-4 py-3 flex items-center gap-3">
            <span
              className={`px-1.5 py-0.5 text-[10px] font-semibold uppercase rounded ${PRIORITY_COLORS[item.priority] || "bg-gray-100"}`}
            >
              {item.priority}
            </span>
            <span className="flex-1 text-sm text-gray-900 truncate">
              {item.title}
            </span>
            <span
              className={`px-2 py-0.5 text-xs rounded-full ${STATUS_COLORS[item.status] || "bg-gray-100"}`}
            >
              {item.status.replace("_", " ")}
            </span>
            {item.story_points != null && (
              <span className="text-xs text-gray-400 font-mono">
                {item.story_points}sp
              </span>
            )}
            {item.assignee_name && (
              <span className="text-xs text-gray-500 truncate max-w-[100px]">
                {item.assignee_name}
              </span>
            )}
          </div>
        ))}
        {items.length > 10 && (
          <div className="px-4 py-2 text-center text-xs text-gray-400">
            +{items.length - 10} more items
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function PlanningPage() {
  const [viewMode, setViewMode] = useState<ViewMode>("tree");

  // Modal states
  const [roadmapModalOpen, setRoadmapModalOpen] = useState(false);
  const [phaseModalOpen, setPhaseModalOpen] = useState(false);
  const [editingRoadmap, setEditingRoadmap] = useState<Roadmap | null>(null);
  const [editingPhase, setEditingPhase] = useState<Phase | null>(null);
  const [selectedRoadmapId, setSelectedRoadmapId] = useState<string | null>(null);
  const [selectedRoadmapName, setSelectedRoadmapName] = useState<string>("");

  // Delete confirmation states
  const [deleteRoadmapDialog, setDeleteRoadmapDialog] = useState<{
    open: boolean;
    id: string;
    name: string;
  }>({ open: false, id: "", name: "" });
  const [deletePhaseDialog, setDeletePhaseDialog] = useState<{
    open: boolean;
    id: string;
    name: string;
    roadmapId: string;
  }>({ open: false, id: "", name: "", roadmapId: "" });

  // Get first project
  const { data: projects, isLoading: isLoadingProjects } = useProjects();
  const firstProject = projects?.[0];

  // Delete mutations
  const deleteRoadmapMutation = useDeleteRoadmap();
  const deletePhaseMutation = useDeletePhase();
  const deleteSprintMutation = useDeleteSprint();

  // Get planning hierarchy
  const {
    data: hierarchy,
    isLoading: isLoadingHierarchy,
    error: hierarchyError,
  } = usePlanningHierarchy(firstProject?.id || "");

  // Get sprints for timeline view
  const { data: sprintsData, isLoading: isLoadingSprints } = useSprints({
    projectId: firstProject?.id,
  });

  // Active sprint details + dashboard
  const { data: activeSprint } = useActiveSprint(firstProject?.id || "");
  const { data: sprintDashboard } = useActiveSprintDashboard(firstProject?.id || "");

  // Backlog items for active sprint
  const { data: backlogData } = useBacklogItems({
    sprintId: activeSprint?.id,
  });

  const isLoading = isLoadingProjects || isLoadingHierarchy || isLoadingSprints;

  // Render loading state
  if (isLoading) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Planning Hierarchy</h1>
          <p className="text-sm text-gray-500">
            SDLC 6.0.6 - Roadmap → Phase → Sprint Visualization
          </p>
        </div>
        <LoadingSkeleton />
      </div>
    );
  }

  // Render error state
  if (hierarchyError) {
    return (
      <div className="flex min-h-[400px] items-center justify-center p-6">
        <div className="text-center">
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-500" />
          <h3 className="mt-4 text-lg font-semibold text-gray-900">Error Loading Planning Data</h3>
          <p className="mt-2 text-sm text-gray-500">
            {hierarchyError instanceof Error ? hierarchyError.message : "Failed to load planning hierarchy"}
          </p>
        </div>
      </div>
    );
  }

  // Render no project state
  if (!firstProject) {
    return (
      <div className="flex min-h-[400px] items-center justify-center p-6">
        <div className="text-center">
          <TreeIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-semibold text-gray-900">No Projects Found</h3>
          <p className="mt-2 text-sm text-gray-500">Create a project first to manage planning hierarchy.</p>
          <Link
            href="/app/projects"
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Go to Projects
          </Link>
        </div>
      </div>
    );
  }

  // Prepare sprints for timeline
  const sprintsForTimeline = (sprintsData?.sprints || []).map((sprint) => ({
    ...sprint,
    phase_name: hierarchy?.hierarchy.find(
      (roadmap) =>
        roadmap.children?.find((phase) =>
          phase.children?.find((s) => s.id === sprint.id)
        )
    )?.children?.find((phase) => phase.children?.find((s) => s.id === sprint.id))?.name,
  }));

  // ===========================================================================
  // ACTION HANDLERS
  // ===========================================================================

  const handleEditRoadmap = (roadmap: Roadmap) => {
    setEditingRoadmap(roadmap);
    setRoadmapModalOpen(true);
  };

  const handleDeleteRoadmap = (roadmapId: string, roadmapName: string) => {
    setDeleteRoadmapDialog({ open: true, id: roadmapId, name: roadmapName });
  };

  const handleConfirmDeleteRoadmap = async () => {
    if (!firstProject?.id) return;
    try {
      await deleteRoadmapMutation.mutateAsync({
        id: deleteRoadmapDialog.id,
        projectId: firstProject.id,
      });
      setDeleteRoadmapDialog({ open: false, id: "", name: "" });
    } catch (error) {
      console.error("Failed to delete roadmap:", error);
    }
  };

  const handleAddPhase = (roadmapId: string, roadmapName: string) => {
    setSelectedRoadmapId(roadmapId);
    setSelectedRoadmapName(roadmapName);
    setEditingPhase(null);
    setPhaseModalOpen(true);
  };

  const handleEditPhase = (phase: Phase) => {
    setEditingPhase(phase);
    setSelectedRoadmapId(phase.roadmap_id);
    setSelectedRoadmapName(""); // Will be looked up in modal if needed
    setPhaseModalOpen(true);
  };

  const handleDeletePhase = (phaseId: string, phaseName: string, roadmapId?: string) => {
    setDeletePhaseDialog({
      open: true,
      id: phaseId,
      name: phaseName,
      roadmapId: roadmapId || "",
    });
  };

  const handleConfirmDeletePhase = async () => {
    try {
      await deletePhaseMutation.mutateAsync({
        id: deletePhaseDialog.id,
        roadmapId: deletePhaseDialog.roadmapId,
      });
      setDeletePhaseDialog({ open: false, id: "", name: "", roadmapId: "" });
    } catch (error) {
      console.error("Failed to delete phase:", error);
    }
  };

  const handleAddSprint = (phaseId: string, phaseName: string) => {
    // Navigate to sprint creation page with phase context
    window.location.href = `/app/sprints?phaseId=${phaseId}&phaseName=${encodeURIComponent(phaseName)}`;
  };

  const handleDeleteSprint = async (sprintId: string) => {
    if (!firstProject?.id) return;
    try {
      await deleteSprintMutation.mutateAsync({
        id: sprintId,
        projectId: firstProject.id,
      });
    } catch (error) {
      console.error("Failed to delete sprint:", error);
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/app/sprints"
            className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeftIcon className="h-4 w-4" />
            Back to Sprints
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Planning Hierarchy</h1>
            <p className="text-sm text-gray-500">
              SDLC 6.0.6 - {firstProject.name}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <ViewToggle activeView={viewMode} onViewChange={setViewMode} />
          <button
            onClick={() => {
              setEditingRoadmap(null);
              setRoadmapModalOpen(true);
            }}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <PlusIcon className="h-4 w-4" />
            New Roadmap
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="mb-6">
        <StatsCards
          totalRoadmaps={hierarchy?.total_roadmaps || 0}
          totalPhases={hierarchy?.total_phases || 0}
          totalSprints={hierarchy?.total_sprints || 0}
          activeSprintName={activeSprint?.name}
        />
      </div>

      {/* Main Content */}
      {viewMode === "tree" ? (
        <PlanningHierarchyTree
          hierarchy={hierarchy?.hierarchy || []}
          activeSprintId={hierarchy?.active_sprint_id}
          projectName={firstProject.name}
          defaultExpanded={true}
          onEditRoadmap={handleEditRoadmap}
          onDeleteRoadmap={handleDeleteRoadmap}
          onAddPhase={handleAddPhase}
          onEditPhase={handleEditPhase}
          onDeletePhase={handleDeletePhase}
          onAddSprint={handleAddSprint}
        />
      ) : (
        <SprintTimeline
          sprints={sprintsForTimeline}
          activeSprintId={hierarchy?.active_sprint_id}
        />
      )}

      {/* Active Sprint Dashboard */}
      {sprintDashboard && (
        <div className="mt-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Active Sprint: {sprintDashboard.sprint.name}
          </h2>
          <ActiveSprintProgress itemsByStatus={sprintDashboard.items_by_status} />
          {backlogData && <BacklogPanel items={backlogData.items} />}
        </div>
      )}

      {/* Help Text */}
      <div className="mt-6 rounded-lg bg-gray-50 p-4">
        <h4 className="text-sm font-medium text-gray-900">SDLC 6.0.6 Planning Hierarchy</h4>
        <p className="mt-1 text-xs text-gray-500">
          <strong>Roadmap</strong> (12-month vision) → <strong>Phase</strong> (4-8 weeks) →{" "}
          <strong>Sprint</strong> (5-10 days) → <strong>Backlog Items</strong> (individual tasks).
          This hierarchy ensures strategic alignment from vision to execution.
        </p>
      </div>

      {/* Roadmap Modal */}
      <RoadmapModal
        open={roadmapModalOpen}
        onOpenChange={(open) => {
          setRoadmapModalOpen(open);
          if (!open) setEditingRoadmap(null);
        }}
        projectId={firstProject?.id || ""}
        roadmap={editingRoadmap}
      />

      {/* Phase Modal */}
      <PhaseModal
        open={phaseModalOpen}
        onOpenChange={(open) => {
          setPhaseModalOpen(open);
          if (!open) {
            setEditingPhase(null);
            setSelectedRoadmapId(null);
            setSelectedRoadmapName("");
          }
        }}
        roadmapId={selectedRoadmapId || ""}
        roadmapName={selectedRoadmapName}
        phase={editingPhase}
      />

      {/* Delete Roadmap Confirmation */}
      <DeleteConfirmDialog
        open={deleteRoadmapDialog.open}
        onOpenChange={(open) =>
          setDeleteRoadmapDialog((prev) => ({ ...prev, open }))
        }
        title="Delete Roadmap"
        description="This will permanently delete the roadmap and all its phases and sprints."
        itemName={deleteRoadmapDialog.name}
        onConfirm={handleConfirmDeleteRoadmap}
        isDeleting={deleteRoadmapMutation.isPending}
      />

      {/* Delete Phase Confirmation */}
      <DeleteConfirmDialog
        open={deletePhaseDialog.open}
        onOpenChange={(open) =>
          setDeletePhaseDialog((prev) => ({ ...prev, open }))
        }
        title="Delete Phase"
        description="This will permanently delete the phase and all its sprints."
        itemName={deletePhaseDialog.name}
        onConfirm={handleConfirmDeletePhase}
        isDeleting={deletePhaseMutation.isPending}
      />
    </div>
  );
}
