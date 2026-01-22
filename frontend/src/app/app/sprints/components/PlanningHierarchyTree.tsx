/**
 * Planning Hierarchy Tree View - SDLC Orchestrator
 *
 * @module frontend/src/app/app/sprints/components/PlanningHierarchyTree
 * @description Interactive tree visualization of Roadmap → Phase → Sprint hierarchy
 * @sdlc SDLC 5.1.3 Framework - Sprint 92 (Planning Hierarchy CRUD)
 * @reference SDLC 5.1.3 Pillar 2: Sprint Planning Governance
 * @status Sprint 92 - Edit/Delete Actions Implementation
 */

"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import Link from "next/link";
import type {
  PlanningHierarchyNode,
  SprintStatus,
  GateStatus,
  Roadmap,
  Phase,
} from "@/lib/types/planning";
import {
  getSprintStatusColor,
  getGateStatusColor,
  getGateStatusIcon,
} from "@/lib/types/planning";

// =============================================================================
// ICONS
// =============================================================================

function ChevronRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
    </svg>
  );
}

function ChevronDownIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
    </svg>
  );
}

function MapIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498 4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 0 0-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0Z" />
    </svg>
  );
}

function LayersIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6.429 9.75 2.25 12l4.179 2.25m0-4.5 5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0 4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0-5.571 3-5.571-3" />
    </svg>
  );
}

function SprintIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" />
    </svg>
  );
}

function CalendarDaysIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5m-9-6h.008v.008H12v-.008ZM12 15h.008v.008H12V15Zm0 2.25h.008v.008H12v-.008ZM9.75 15h.008v.008H9.75V15Zm0 2.25h.008v.008H9.75v-.008ZM7.5 15h.008v.008H7.5V15Zm0 2.25h.008v.008H7.5v-.008Zm6.75-4.5h.008v.008h-.008v-.008Zm0 2.25h.008v.008h-.008V15Zm0 2.25h.008v.008h-.008v-.008Zm2.25-4.5h.008v.008H16.5v-.008Zm0 2.25h.008v.008H16.5V15Z" />
    </svg>
  );
}

function EllipsisVerticalIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z" />
    </svg>
  );
}

function PencilIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
    </svg>
  );
}

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
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

// =============================================================================
// TYPES
// =============================================================================

interface TreeNodeActions {
  onEditRoadmap?: (roadmap: Roadmap) => void;
  onDeleteRoadmap?: (roadmapId: string, roadmapName: string) => void;
  onAddPhase?: (roadmapId: string, roadmapName: string) => void;
  onEditPhase?: (phase: Phase) => void;
  onDeletePhase?: (phaseId: string, phaseName: string, roadmapId?: string) => void;
  onAddSprint?: (phaseId: string, phaseName: string) => void;
}

interface TreeNodeProps {
  node: PlanningHierarchyNode;
  level: number;
  expandedNodes: Set<string>;
  toggleNode: (nodeId: string) => void;
  activeSprintId?: string | null;
  actions?: TreeNodeActions;
}

// =============================================================================
// ACTION MENU COMPONENT
// =============================================================================

interface ActionMenuProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

function ActionMenu({ isOpen, onClose, children }: ActionMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      ref={menuRef}
      className="absolute right-0 top-full z-50 mt-1 min-w-[140px] rounded-md border border-gray-200 bg-white py-1 shadow-lg"
    >
      {children}
    </div>
  );
}

interface ActionMenuItemProps {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  variant?: "default" | "danger";
}

function ActionMenuItem({ icon, label, onClick, variant = "default" }: ActionMenuItemProps) {
  return (
    <button
      onClick={onClick}
      className={`flex w-full items-center gap-2 px-3 py-1.5 text-sm transition-colors ${
        variant === "danger"
          ? "text-red-600 hover:bg-red-50"
          : "text-gray-700 hover:bg-gray-100"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Get icon for node type
 */
function getNodeIcon(type: PlanningHierarchyNode["type"]) {
  switch (type) {
    case "roadmap":
      return <MapIcon className="h-4 w-4 text-purple-500" />;
    case "phase":
      return <LayersIcon className="h-4 w-4 text-blue-500" />;
    case "sprint":
      return <SprintIcon className="h-4 w-4 text-green-500" />;
    case "backlog":
      return <CalendarDaysIcon className="h-4 w-4 text-gray-500" />;
    default:
      return null;
  }
}

/**
 * Get background color for node based on type and status
 */
function getNodeBackground(
  type: PlanningHierarchyNode["type"],
  status?: string,
  isActive?: boolean
): string {
  if (isActive) {
    return "bg-blue-50 border-blue-300";
  }

  switch (type) {
    case "roadmap":
      return "bg-purple-50/50 border-purple-200";
    case "phase":
      if (status === "active") return "bg-blue-50/50 border-blue-200";
      if (status === "completed") return "bg-green-50/50 border-green-200";
      return "bg-gray-50 border-gray-200";
    case "sprint":
      if (status === "active") return "bg-blue-50 border-blue-300";
      if (status === "closed") return "bg-green-50/50 border-green-200";
      if (status === "closing") return "bg-yellow-50 border-yellow-200";
      return "bg-gray-50 border-gray-200";
    default:
      return "bg-gray-50 border-gray-200";
  }
}

/**
 * Format date range for display
 */
function formatDateRange(startDate?: string, endDate?: string): string {
  if (!startDate || !endDate) return "";
  const start = new Date(startDate);
  const end = new Date(endDate);
  const options: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" };
  return `${start.toLocaleDateString("en-US", options)} - ${end.toLocaleDateString("en-US", options)}`;
}

// =============================================================================
// TREE NODE COMPONENT
// =============================================================================

function TreeNode({ node, level, expandedNodes, toggleNode, activeSprintId, actions }: TreeNodeProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const isExpanded = expandedNodes.has(node.id);
  const hasChildren = node.children && node.children.length > 0;
  const isActive = node.id === activeSprintId;
  const metadata = node.metadata as Record<string, unknown> | undefined;
  const hasActions = actions && (node.type === "roadmap" || node.type === "phase");

  // Extract status safely
  const status = node.status || (metadata?.status as string);
  const gSprintStatus = metadata?.g_sprint_status as GateStatus | undefined;
  const gSprintCloseStatus = metadata?.g_sprint_close_status as GateStatus | undefined;
  const storyPointsPlanned = metadata?.story_points_planned as number | undefined;
  const storyPointsCompleted = metadata?.story_points_completed as number | undefined;
  const sprintsCount = metadata?.sprints_count as number | undefined;
  const sprintsCompleted = metadata?.sprints_completed as number | undefined;
  const phasesCount = metadata?.phases_count as number | undefined;

  return (
    <div className="relative">
      {/* Connector Lines */}
      {level > 0 && (
        <div
          className="absolute left-0 top-0 h-full w-px bg-gray-200"
          style={{ left: `${(level - 1) * 24 + 12}px` }}
        />
      )}

      {/* Node Content */}
      <div
        className={`
          relative flex items-center gap-2 rounded-lg border p-2 transition-all
          ${getNodeBackground(node.type, status, isActive)}
          ${isActive ? "ring-2 ring-blue-500 ring-offset-2" : ""}
        `}
        style={{ marginLeft: `${level * 24}px` }}
      >
        {/* Expand/Collapse Button */}
        {hasChildren && (
          <button
            onClick={() => toggleNode(node.id)}
            className="flex h-5 w-5 items-center justify-center rounded hover:bg-gray-200"
          >
            {isExpanded ? (
              <ChevronDownIcon className="h-3.5 w-3.5 text-gray-500" />
            ) : (
              <ChevronRightIcon className="h-3.5 w-3.5 text-gray-500" />
            )}
          </button>
        )}

        {/* Spacer if no children */}
        {!hasChildren && <div className="w-5" />}

        {/* Node Icon */}
        {getNodeIcon(node.type)}

        {/* Node Name (Link for sprints) */}
        {node.type === "sprint" ? (
          <Link
            href={`/app/sprints/${node.id}`}
            className="flex-1 truncate text-sm font-medium text-gray-900 hover:text-blue-600 hover:underline"
          >
            {node.name}
            {isActive && (
              <span className="ml-2 rounded bg-blue-500 px-1.5 py-0.5 text-xs text-white">
                Active
              </span>
            )}
          </Link>
        ) : (
          <span className="flex-1 truncate text-sm font-medium text-gray-900">{node.name}</span>
        )}

        {/* Status Badge */}
        {status && node.type === "sprint" && (
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${getSprintStatusColor(
              status as SprintStatus
            )}`}
          >
            {status}
          </span>
        )}

        {/* Phase Status */}
        {status && node.type === "phase" && (
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
              status === "active"
                ? "bg-blue-100 text-blue-700"
                : status === "completed"
                  ? "bg-green-100 text-green-700"
                  : "bg-gray-100 text-gray-700"
            }`}
          >
            {status}
          </span>
        )}

        {/* Date Range */}
        {node.start_date && node.end_date && (
          <span className="hidden text-xs text-gray-500 md:inline">
            {formatDateRange(node.start_date, node.end_date)}
          </span>
        )}

        {/* Metadata: Story Points for Sprint */}
        {node.type === "sprint" && storyPointsPlanned !== undefined && (
          <span className="hidden text-xs text-gray-500 lg:inline">
            {storyPointsCompleted || 0}/{storyPointsPlanned} SP
          </span>
        )}

        {/* Metadata: Sprints count for Phase */}
        {node.type === "phase" && sprintsCount !== undefined && (
          <span className="hidden text-xs text-gray-500 lg:inline">
            {sprintsCompleted || 0}/{sprintsCount} sprints
          </span>
        )}

        {/* Metadata: Phases count for Roadmap */}
        {node.type === "roadmap" && phasesCount !== undefined && (
          <span className="hidden text-xs text-gray-500 lg:inline">{phasesCount} phases</span>
        )}

        {/* Gate Status Indicators for Sprint */}
        {node.type === "sprint" && (gSprintStatus || gSprintCloseStatus) && (
          <div className="hidden items-center gap-1 lg:flex">
            {gSprintStatus && (
              <span
                className={`rounded px-1.5 py-0.5 text-xs ${getGateStatusColor(gSprintStatus)}`}
                title="G-Sprint Gate"
              >
                {getGateStatusIcon(gSprintStatus)} G
              </span>
            )}
            {gSprintCloseStatus && (
              <span
                className={`rounded px-1.5 py-0.5 text-xs ${getGateStatusColor(gSprintCloseStatus)}`}
                title="G-Sprint-Close Gate"
              >
                {getGateStatusIcon(gSprintCloseStatus)} GC
              </span>
            )}
          </div>
        )}

        {/* Action Menu for Roadmap/Phase */}
        {hasActions && (
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setMenuOpen(!menuOpen);
              }}
              className="flex h-6 w-6 items-center justify-center rounded hover:bg-gray-200"
              title="Actions"
            >
              <EllipsisVerticalIcon className="h-4 w-4 text-gray-500" />
            </button>
            <ActionMenu isOpen={menuOpen} onClose={() => setMenuOpen(false)}>
              {node.type === "roadmap" && (
                <>
                  {actions?.onAddPhase && (
                    <ActionMenuItem
                      icon={<PlusIcon className="h-4 w-4" />}
                      label="Add Phase"
                      onClick={() => {
                        setMenuOpen(false);
                        actions.onAddPhase?.(node.id, node.name);
                      }}
                    />
                  )}
                  {actions?.onEditRoadmap && (
                    <ActionMenuItem
                      icon={<PencilIcon className="h-4 w-4" />}
                      label="Edit Roadmap"
                      onClick={() => {
                        setMenuOpen(false);
                        const roadmap: Roadmap = {
                          id: node.id,
                          name: node.name,
                          description: (metadata?.description as string) || null,
                          project_id: (metadata?.project_id as string) || "",
                          start_date: node.start_date || "",
                          end_date: node.end_date || "",
                          phases_count: (metadata?.phases_count as number) || 0,
                          total_sprints: (metadata?.total_sprints as number) || 0,
                          completed_sprints: (metadata?.completed_sprints as number) || 0,
                          is_active: (metadata?.is_active as boolean) || false,
                          created_at: (metadata?.created_at as string) || "",
                          updated_at: (metadata?.updated_at as string) || "",
                        };
                        actions.onEditRoadmap?.(roadmap);
                      }}
                    />
                  )}
                  {actions?.onDeleteRoadmap && (
                    <ActionMenuItem
                      icon={<TrashIcon className="h-4 w-4" />}
                      label="Delete"
                      variant="danger"
                      onClick={() => {
                        setMenuOpen(false);
                        actions.onDeleteRoadmap?.(node.id, node.name);
                      }}
                    />
                  )}
                </>
              )}
              {node.type === "phase" && (
                <>
                  {actions?.onAddSprint && (
                    <ActionMenuItem
                      icon={<PlusIcon className="h-4 w-4" />}
                      label="Add Sprint"
                      onClick={() => {
                        setMenuOpen(false);
                        actions.onAddSprint?.(node.id, node.name);
                      }}
                    />
                  )}
                  {actions?.onEditPhase && (
                    <ActionMenuItem
                      icon={<PencilIcon className="h-4 w-4" />}
                      label="Edit Phase"
                      onClick={() => {
                        setMenuOpen(false);
                        const phase: Phase = {
                          id: node.id,
                          name: node.name,
                          description: (metadata?.description as string) || null,
                          roadmap_id: (metadata?.roadmap_id as string) || "",
                          start_date: node.start_date || "",
                          end_date: node.end_date || "",
                          status: (status as Phase["status"]) || "planned",
                          theme: (metadata?.theme as string) || null,
                          sprints_count: (metadata?.sprints_count as number) || 0,
                          sprints_completed: (metadata?.sprints_completed as number) || 0,
                          order: (metadata?.order as number) || 0,
                          created_at: (metadata?.created_at as string) || "",
                          updated_at: (metadata?.updated_at as string) || "",
                        };
                        actions.onEditPhase?.(phase);
                      }}
                    />
                  )}
                  {actions?.onDeletePhase && (
                    <ActionMenuItem
                      icon={<TrashIcon className="h-4 w-4" />}
                      label="Delete"
                      variant="danger"
                      onClick={() => {
                        setMenuOpen(false);
                        const roadmapId = (metadata?.roadmap_id as string) || "";
                        actions.onDeletePhase?.(node.id, node.name, roadmapId);
                      }}
                    />
                  )}
                </>
              )}
            </ActionMenu>
          </div>
        )}
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div className="mt-1 space-y-1">
          {node.children?.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              expandedNodes={expandedNodes}
              toggleNode={toggleNode}
              activeSprintId={activeSprintId}
              actions={actions}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

interface PlanningHierarchyTreeProps {
  hierarchy: PlanningHierarchyNode[];
  activeSprintId?: string | null;
  projectName?: string;
  className?: string;
  defaultExpanded?: boolean;
  /** Callback when user wants to edit a roadmap */
  onEditRoadmap?: (roadmap: Roadmap) => void;
  /** Callback when user wants to delete a roadmap */
  onDeleteRoadmap?: (roadmapId: string, roadmapName: string) => void;
  /** Callback when user wants to add a phase to a roadmap */
  onAddPhase?: (roadmapId: string, roadmapName: string) => void;
  /** Callback when user wants to edit a phase */
  onEditPhase?: (phase: Phase) => void;
  /** Callback when user wants to delete a phase */
  onDeletePhase?: (phaseId: string, phaseName: string, roadmapId?: string) => void;
  /** Callback when user wants to add a sprint to a phase */
  onAddSprint?: (phaseId: string, phaseName: string) => void;
}

export function PlanningHierarchyTree({
  hierarchy,
  activeSprintId,
  projectName,
  className = "",
  defaultExpanded = true,
  onEditRoadmap,
  onDeleteRoadmap,
  onAddPhase,
  onEditPhase,
  onDeletePhase,
  onAddSprint,
}: PlanningHierarchyTreeProps) {
  // Combine actions for passing to TreeNode
  const actions: TreeNodeActions = {
    onEditRoadmap,
    onDeleteRoadmap,
    onAddPhase,
    onEditPhase,
    onDeletePhase,
    onAddSprint,
  };
  // Initialize expanded nodes - expand all by default if defaultExpanded is true
  const initialExpanded = useMemo(() => {
    if (!defaultExpanded) return new Set<string>();

    const collectIds = (nodes: PlanningHierarchyNode[]): string[] => {
      const ids: string[] = [];
      for (const node of nodes) {
        ids.push(node.id);
        if (node.children) {
          ids.push(...collectIds(node.children));
        }
      }
      return ids;
    };

    return new Set(collectIds(hierarchy));
  }, [hierarchy, defaultExpanded]);

  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(initialExpanded);

  const toggleNode = (nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  const expandAll = () => {
    const collectIds = (nodes: PlanningHierarchyNode[]): string[] => {
      const ids: string[] = [];
      for (const node of nodes) {
        ids.push(node.id);
        if (node.children) {
          ids.push(...collectIds(node.children));
        }
      }
      return ids;
    };
    setExpandedNodes(new Set(collectIds(hierarchy)));
  };

  const collapseAll = () => {
    setExpandedNodes(new Set());
  };

  // Calculate stats
  const stats = useMemo(() => {
    let roadmaps = 0;
    let phases = 0;
    let sprints = 0;

    const countNodes = (nodes: PlanningHierarchyNode[]) => {
      for (const node of nodes) {
        if (node.type === "roadmap") roadmaps++;
        else if (node.type === "phase") phases++;
        else if (node.type === "sprint") sprints++;
        if (node.children) countNodes(node.children);
      }
    };

    countNodes(hierarchy);
    return { roadmaps, phases, sprints };
  }, [hierarchy]);

  if (hierarchy.length === 0) {
    return (
      <div className={`rounded-xl border border-dashed border-gray-300 bg-gray-50 p-8 ${className}`}>
        <div className="flex flex-col items-center justify-center text-center">
          <MapIcon className="mb-3 h-10 w-10 text-gray-400" />
          <h3 className="text-sm font-medium text-gray-900">No Planning Hierarchy</h3>
          <p className="mt-1 text-xs text-gray-500">
            Create roadmaps, phases, and sprints to visualize your planning hierarchy.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-xl border border-gray-200 bg-white ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">Planning Hierarchy</h3>
          {projectName && <p className="text-xs text-gray-500">{projectName}</p>}
        </div>
        <div className="flex items-center gap-2">
          {/* Stats */}
          <div className="hidden items-center gap-3 text-xs text-gray-500 md:flex">
            <span className="flex items-center gap-1">
              <MapIcon className="h-3.5 w-3.5 text-purple-500" />
              {stats.roadmaps}
            </span>
            <span className="flex items-center gap-1">
              <LayersIcon className="h-3.5 w-3.5 text-blue-500" />
              {stats.phases}
            </span>
            <span className="flex items-center gap-1">
              <SprintIcon className="h-3.5 w-3.5 text-green-500" />
              {stats.sprints}
            </span>
          </div>
          {/* Expand/Collapse Buttons */}
          <div className="flex items-center gap-1 border-l border-gray-200 pl-2">
            <button
              onClick={expandAll}
              className="rounded px-2 py-1 text-xs text-gray-600 hover:bg-gray-100"
              title="Expand All"
            >
              Expand
            </button>
            <button
              onClick={collapseAll}
              className="rounded px-2 py-1 text-xs text-gray-600 hover:bg-gray-100"
              title="Collapse All"
            >
              Collapse
            </button>
          </div>
        </div>
      </div>

      {/* Tree View */}
      <div className="max-h-[500px] overflow-y-auto p-4">
        <div className="space-y-1">
          {hierarchy.map((node) => (
            <TreeNode
              key={node.id}
              node={node}
              level={0}
              expandedNodes={expandedNodes}
              toggleNode={toggleNode}
              activeSprintId={activeSprintId}
              actions={actions}
            />
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="border-t border-gray-200 px-4 py-2">
        <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
          <span className="font-medium">Legend:</span>
          <span className="flex items-center gap-1">
            <MapIcon className="h-3.5 w-3.5 text-purple-500" />
            Roadmap
          </span>
          <span className="flex items-center gap-1">
            <LayersIcon className="h-3.5 w-3.5 text-blue-500" />
            Phase
          </span>
          <span className="flex items-center gap-1">
            <SprintIcon className="h-3.5 w-3.5 text-green-500" />
            Sprint
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-blue-500" />
            Active
          </span>
        </div>
      </div>
    </div>
  );
}

export default PlanningHierarchyTree;
