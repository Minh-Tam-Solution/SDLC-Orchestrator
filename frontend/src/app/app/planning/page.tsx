/**
 * Planning Hierarchy Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/planning/page
 * @description Full Planning Hierarchy visualization (Roadmap → Phase → Sprint)
 * @sdlc SDLC 5.1.3 Framework - Sprint 92 (Planning Hierarchy CRUD)
 * @reference SDLC 5.1.3 Pillar 2: Sprint Planning Governance
 * @status Sprint 92 - Roadmap & Phase CRUD Implementation
 */

"use client";

import { useState } from "react";
import Link from "next/link";
import { useProjects } from "@/hooks/useProjects";
import { usePlanningHierarchy, useSprints } from "@/hooks/usePlanningHierarchy";
import { PlanningHierarchyTree, SprintTimeline } from "@/app/app/sprints/components";
import { RoadmapModal, PhaseModal } from "./components";
import type { Roadmap, Phase } from "@/lib/types/planning";

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

  // Get first project
  const { data: projects, isLoading: isLoadingProjects } = useProjects();
  const firstProject = projects?.[0];

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

  const isLoading = isLoadingProjects || isLoadingHierarchy || isLoadingSprints;

  // Render loading state
  if (isLoading) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Planning Hierarchy</h1>
          <p className="text-sm text-gray-500">
            SDLC 5.1.3 - Roadmap → Phase → Sprint Visualization
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
              SDLC 5.1.3 - {firstProject.name}
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
          activeSprintName={
            hierarchy?.active_sprint_id
              ? sprintsData?.sprints?.find((s) => s.id === hierarchy.active_sprint_id)?.name
              : undefined
          }
        />
      </div>

      {/* Main Content */}
      {viewMode === "tree" ? (
        <PlanningHierarchyTree
          hierarchy={hierarchy?.hierarchy || []}
          activeSprintId={hierarchy?.active_sprint_id}
          projectName={firstProject.name}
          defaultExpanded={true}
        />
      ) : (
        <SprintTimeline
          sprints={sprintsForTimeline}
          activeSprintId={hierarchy?.active_sprint_id}
        />
      )}

      {/* Help Text */}
      <div className="mt-6 rounded-lg bg-gray-50 p-4">
        <h4 className="text-sm font-medium text-gray-900">SDLC 5.1.3 Planning Hierarchy</h4>
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
    </div>
  );
}
