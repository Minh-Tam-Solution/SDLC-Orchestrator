/**
 * =========================================================================
 * SSOT Tree View Component
 * SDLC Orchestrator - Sprint 152 (Context Authority UI)
 *
 * Version: 1.0.0
 * Date: February 3, 2026
 * Status: ACTIVE - Sprint 152 Implementation
 * Authority: Frontend Lead + Backend Lead Approved
 * Framework: SDLC 6.0.3
 *
 * Hierarchical view of Single Source of Truth (SSOT) context:
 * - Project context structure
 * - Gate status visualization
 * - Vibecoding zones
 * - Applied templates tree
 *
 * Zero Mock Policy: Production-ready with real API integration
 * =========================================================================
 */

"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  VibecodingZoneEnum,
  TierEnum,
  GateStatus,
  SnapshotResponse,
  getZoneColor,
  getTierColor,
} from "@/hooks/useContextAuthority";

// =========================================================================
// Types
// =========================================================================

interface TreeNode {
  id: string;
  label: string;
  value?: string | number | boolean;
  type: "root" | "branch" | "leaf" | "gate" | "zone" | "template" | "warning";
  children?: TreeNode[];
  expanded?: boolean;
  status?: "pass" | "fail" | "pending" | "warning";
}

interface SSOTTreeViewProps {
  snapshot?: SnapshotResponse | null;
  projectId?: string;
  projectTier?: TierEnum;
  vibecodingZone?: VibecodingZoneEnum;
  vibecodingIndex?: number;
  gateStatus?: GateStatus;
  className?: string;
}

// =========================================================================
// Icon Components
// =========================================================================

function ChevronRightIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="m8.25 4.5 7.5 7.5-7.5 7.5"
      />
    </svg>
  );
}

function ChevronDownIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="m19.5 8.25-7.5 7.5-7.5-7.5"
      />
    </svg>
  );
}

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z"
      />
    </svg>
  );
}

function DocumentIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
      />
    </svg>
  );
}

function ShieldCheckIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z"
      />
    </svg>
  );
}

function ExclamationTriangleIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
      />
    </svg>
  );
}

function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z"
      />
    </svg>
  );
}

// =========================================================================
// Helper Functions
// =========================================================================

function getNodeIcon(type: TreeNode["type"], status?: TreeNode["status"]) {
  switch (type) {
    case "root":
    case "branch":
      return <FolderIcon className="h-4 w-4 text-blue-500" />;
    case "gate":
      if (status === "pass") {
        return <ShieldCheckIcon className="h-4 w-4 text-green-500" />;
      } else if (status === "fail") {
        return <ShieldCheckIcon className="h-4 w-4 text-red-500" />;
      }
      return <ShieldCheckIcon className="h-4 w-4 text-gray-400" />;
    case "zone":
      return <SparklesIcon className="h-4 w-4 text-purple-500" />;
    case "template":
      return <DocumentIcon className="h-4 w-4 text-indigo-500" />;
    case "warning":
      return <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500" />;
    default:
      return <DocumentIcon className="h-4 w-4 text-gray-400" />;
  }
}

function buildTreeFromSnapshot(
  snapshot: SnapshotResponse,
  projectTier?: TierEnum,
  vibecodingZone?: VibecodingZoneEnum,
  vibecodingIndex?: number,
  gateStatus?: GateStatus
): TreeNode[] {
  const tree: TreeNode[] = [];

  // Root: Project Context
  const projectNode: TreeNode = {
    id: "project",
    label: "Project Context",
    type: "root",
    expanded: true,
    children: [],
  };

  // Project Info
  const infoNode: TreeNode = {
    id: "info",
    label: "Information",
    type: "branch",
    expanded: true,
    children: [
      {
        id: "project-id",
        label: "Project ID",
        value: snapshot.project_id,
        type: "leaf",
      },
      {
        id: "tier",
        label: "Tier",
        value: snapshot.tier || projectTier || "STANDARD",
        type: "leaf",
      },
      {
        id: "submission-id",
        label: "Submission ID",
        value: snapshot.submission_id,
        type: "leaf",
      },
      {
        id: "snapshot-at",
        label: "Snapshot At",
        value: new Date(snapshot.snapshot_at).toLocaleString(),
        type: "leaf",
      },
    ],
  };
  projectNode.children?.push(infoNode);

  // Gate Status
  const actualGateStatus = snapshot.gate_status as GateStatus || gateStatus;
  if (actualGateStatus) {
    const gateNode: TreeNode = {
      id: "gates",
      label: "Gate Status",
      type: "branch",
      expanded: true,
      children: [
        {
          id: "current-stage",
          label: "Current Stage",
          value: actualGateStatus.current_stage || "Unknown",
          type: "gate",
          status: "pass",
        },
        {
          id: "last-passed",
          label: "Last Passed Gate",
          value: actualGateStatus.last_passed_gate || "None",
          type: "gate",
          status: actualGateStatus.last_passed_gate ? "pass" : "pending",
        },
      ],
    };

    // Add pending gates
    if (actualGateStatus.pending_gates && actualGateStatus.pending_gates.length > 0) {
      const pendingNode: TreeNode = {
        id: "pending-gates",
        label: "Pending Gates",
        type: "branch",
        children: actualGateStatus.pending_gates.map((gate, idx) => ({
          id: `pending-gate-${idx}`,
          label: gate,
          type: "gate" as const,
          status: "pending" as const,
        })),
      };
      gateNode.children?.push(pendingNode);
    }
    projectNode.children?.push(gateNode);
  }

  // Vibecoding Zone
  const actualZone = (snapshot.vibecoding_zone as VibecodingZoneEnum) || vibecodingZone;
  const actualIndex = snapshot.vibecoding_index ?? vibecodingIndex;
  if (actualZone || actualIndex !== undefined) {
    const zoneNode: TreeNode = {
      id: "vibecoding",
      label: "Vibecoding Status",
      type: "branch",
      expanded: true,
      children: [],
    };

    if (actualZone) {
      zoneNode.children?.push({
        id: "zone",
        label: "Zone",
        value: actualZone,
        type: "zone",
        status: actualZone === "GREEN" ? "pass" : actualZone === "RED" ? "fail" : "warning",
      });
    }

    if (actualIndex !== undefined) {
      zoneNode.children?.push({
        id: "index",
        label: "Index",
        value: actualIndex,
        type: "leaf",
      });
    }
    projectNode.children?.push(zoneNode);
  }

  // Validation Status
  const validationNode: TreeNode = {
    id: "validation",
    label: "Validation",
    type: "branch",
    expanded: true,
    children: [
      {
        id: "is-valid",
        label: "Is Valid",
        value: snapshot.is_valid ? "Yes" : "No",
        type: "leaf",
        status: snapshot.is_valid ? "pass" : "fail",
      },
    ],
  };

  // V1 Result (if available)
  if (snapshot.v1_result) {
    const v1Node: TreeNode = {
      id: "v1-result",
      label: "V1 Checks",
      type: "branch",
      children: Object.entries(snapshot.v1_result).map(([key, value]) => ({
        id: `v1-${key}`,
        label: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        value: String(value),
        type: "leaf" as const,
        status: value === true ? ("pass" as const) : value === false ? ("fail" as const) : undefined,
      })),
    };
    validationNode.children?.push(v1Node);
  }

  // Gate Violations
  if (snapshot.gate_violations && snapshot.gate_violations.length > 0) {
    const violationsNode: TreeNode = {
      id: "violations",
      label: `Gate Violations (${snapshot.gate_violations.length})`,
      type: "branch",
      children: snapshot.gate_violations.map((violation, idx) => ({
        id: `violation-${idx}`,
        label: `Violation ${idx + 1}`,
        value: JSON.stringify(violation),
        type: "warning" as const,
        status: "fail" as const,
      })),
    };
    validationNode.children?.push(violationsNode);
  }

  // Index Warnings
  if (snapshot.index_warnings && snapshot.index_warnings.length > 0) {
    const warningsNode: TreeNode = {
      id: "warnings",
      label: `Index Warnings (${snapshot.index_warnings.length})`,
      type: "branch",
      children: snapshot.index_warnings.map((warning, idx) => ({
        id: `warning-${idx}`,
        label: `Warning ${idx + 1}`,
        value: JSON.stringify(warning),
        type: "warning" as const,
        status: "warning" as const,
      })),
    };
    validationNode.children?.push(warningsNode);
  }

  projectNode.children?.push(validationNode);

  // Applied Templates
  if (snapshot.applied_template_ids && snapshot.applied_template_ids.length > 0) {
    const templatesNode: TreeNode = {
      id: "templates",
      label: `Applied Templates (${snapshot.applied_template_ids.length})`,
      type: "branch",
      children: snapshot.applied_template_ids.map((templateId, idx) => ({
        id: `template-${idx}`,
        label: templateId,
        type: "template" as const,
      })),
    };
    projectNode.children?.push(templatesNode);
  }

  tree.push(projectNode);
  return tree;
}

function buildDefaultTree(
  projectId?: string,
  projectTier?: TierEnum,
  vibecodingZone?: VibecodingZoneEnum,
  vibecodingIndex?: number,
  gateStatus?: GateStatus
): TreeNode[] {
  const tree: TreeNode[] = [];

  const projectNode: TreeNode = {
    id: "project",
    label: "Project Context",
    type: "root",
    expanded: true,
    children: [],
  };

  // Basic Info
  const infoNode: TreeNode = {
    id: "info",
    label: "Information",
    type: "branch",
    expanded: true,
    children: [],
  };

  if (projectId) {
    infoNode.children?.push({
      id: "project-id",
      label: "Project ID",
      value: projectId,
      type: "leaf",
    });
  }

  if (projectTier) {
    infoNode.children?.push({
      id: "tier",
      label: "Tier",
      value: projectTier,
      type: "leaf",
    });
  }

  if (infoNode.children && infoNode.children.length > 0) {
    projectNode.children?.push(infoNode);
  }

  // Gate Status
  if (gateStatus) {
    const gateNode: TreeNode = {
      id: "gates",
      label: "Gate Status",
      type: "branch",
      expanded: true,
      children: [
        {
          id: "current-stage",
          label: "Current Stage",
          value: gateStatus.current_stage || "Unknown",
          type: "gate",
          status: "pass",
        },
        {
          id: "last-passed",
          label: "Last Passed Gate",
          value: gateStatus.last_passed_gate || "None",
          type: "gate",
          status: gateStatus.last_passed_gate ? "pass" : "pending",
        },
      ],
    };

    if (gateStatus.pending_gates && gateStatus.pending_gates.length > 0) {
      const pendingNode: TreeNode = {
        id: "pending-gates",
        label: "Pending Gates",
        type: "branch",
        children: gateStatus.pending_gates.map((gate, idx) => ({
          id: `pending-gate-${idx}`,
          label: gate,
          type: "gate" as const,
          status: "pending" as const,
        })),
      };
      gateNode.children?.push(pendingNode);
    }
    projectNode.children?.push(gateNode);
  }

  // Vibecoding
  if (vibecodingZone || vibecodingIndex !== undefined) {
    const zoneNode: TreeNode = {
      id: "vibecoding",
      label: "Vibecoding Status",
      type: "branch",
      expanded: true,
      children: [],
    };

    if (vibecodingZone) {
      zoneNode.children?.push({
        id: "zone",
        label: "Zone",
        value: vibecodingZone,
        type: "zone",
        status: vibecodingZone === "GREEN" ? "pass" : vibecodingZone === "RED" ? "fail" : "warning",
      });
    }

    if (vibecodingIndex !== undefined) {
      zoneNode.children?.push({
        id: "index",
        label: "Index",
        value: vibecodingIndex,
        type: "leaf",
      });
    }
    projectNode.children?.push(zoneNode);
  }

  tree.push(projectNode);
  return tree;
}

// =========================================================================
// Tree Node Component
// =========================================================================

interface TreeNodeItemProps {
  node: TreeNode;
  level: number;
  onToggle: (nodeId: string) => void;
  expandedNodes: Set<string>;
}

function TreeNodeItem({ node, level, onToggle, expandedNodes }: TreeNodeItemProps) {
  const hasChildren = node.children && node.children.length > 0;
  const isExpanded = expandedNodes.has(node.id);
  const paddingLeft = level * 20;

  return (
    <div className="select-none">
      <div
        className={cn(
          "flex items-center gap-2 py-1.5 px-2 rounded-md cursor-pointer transition-colors",
          "hover:bg-gray-100",
          node.status === "fail" && "bg-red-50",
          node.status === "warning" && "bg-yellow-50"
        )}
        style={{ paddingLeft: `${paddingLeft}px` }}
        onClick={() => hasChildren && onToggle(node.id)}
      >
        {/* Expand/Collapse Icon */}
        {hasChildren ? (
          isExpanded ? (
            <ChevronDownIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
          ) : (
            <ChevronRightIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
          )
        ) : (
          <span className="w-4" />
        )}

        {/* Node Icon */}
        {getNodeIcon(node.type, node.status)}

        {/* Label */}
        <span
          className={cn(
            "text-sm",
            node.type === "root" && "font-semibold text-gray-900",
            node.type === "branch" && "font-medium text-gray-700",
            node.type === "leaf" && "text-gray-600",
            node.status === "fail" && "text-red-700",
            node.status === "warning" && "text-yellow-700"
          )}
        >
          {node.label}
        </span>

        {/* Value */}
        {node.value !== undefined && (
          <span
            className={cn(
              "text-sm ml-2 px-2 py-0.5 rounded",
              node.type === "zone" && getZoneColor(node.value as VibecodingZoneEnum),
              node.type !== "zone" && "text-gray-500 bg-gray-100",
              node.status === "pass" && "text-green-700 bg-green-100",
              node.status === "fail" && "text-red-700 bg-red-100"
            )}
          >
            {String(node.value)}
          </span>
        )}

        {/* Status Badge */}
        {node.status && !node.value && (
          <span
            className={cn(
              "text-xs ml-2 px-1.5 py-0.5 rounded",
              node.status === "pass" && "text-green-700 bg-green-100",
              node.status === "fail" && "text-red-700 bg-red-100",
              node.status === "pending" && "text-gray-600 bg-gray-100",
              node.status === "warning" && "text-yellow-700 bg-yellow-100"
            )}
          >
            {node.status}
          </span>
        )}
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div>
          {node.children?.map((child) => (
            <TreeNodeItem
              key={child.id}
              node={child}
              level={level + 1}
              onToggle={onToggle}
              expandedNodes={expandedNodes}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// =========================================================================
// Main Component
// =========================================================================

export function SSOTTreeView({
  snapshot,
  projectId,
  projectTier,
  vibecodingZone,
  vibecodingIndex,
  gateStatus,
  className,
}: SSOTTreeViewProps) {
  // Build tree from snapshot or default values
  const tree = snapshot
    ? buildTreeFromSnapshot(snapshot, projectTier, vibecodingZone, vibecodingIndex, gateStatus)
    : buildDefaultTree(projectId, projectTier, vibecodingZone, vibecodingIndex, gateStatus);

  // Track expanded nodes
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(() => {
    const initialExpanded = new Set<string>();
    // Expand root and first level by default
    function collectExpandedNodes(nodes: TreeNode[], depth = 0) {
      nodes.forEach((node) => {
        if (depth < 2 || node.expanded) {
          initialExpanded.add(node.id);
        }
        if (node.children) {
          collectExpandedNodes(node.children, depth + 1);
        }
      });
    }
    collectExpandedNodes(tree);
    return initialExpanded;
  });

  const handleToggle = (nodeId: string) => {
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

  const handleExpandAll = () => {
    const allIds = new Set<string>();
    function collectAllIds(nodes: TreeNode[]) {
      nodes.forEach((node) => {
        allIds.add(node.id);
        if (node.children) {
          collectAllIds(node.children);
        }
      });
    }
    collectAllIds(tree);
    setExpandedNodes(allIds);
  };

  const handleCollapseAll = () => {
    setExpandedNodes(new Set());
  };

  if (tree.length === 0) {
    return (
      <div className={cn("p-4 text-center text-gray-500", className)}>
        <p className="text-sm">No context data available</p>
        <p className="text-xs mt-1">Run a validation to generate context snapshots</p>
      </div>
    );
  }

  return (
    <div className={cn("", className)}>
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-2 px-2">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
          SSOT Context Tree
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExpandAll}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            Expand All
          </button>
          <span className="text-gray-300">|</span>
          <button
            onClick={handleCollapseAll}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            Collapse All
          </button>
        </div>
      </div>

      {/* Tree */}
      <div className="border rounded-lg bg-white p-2">
        {tree.map((node) => (
          <TreeNodeItem
            key={node.id}
            node={node}
            level={0}
            onToggle={handleToggle}
            expandedNodes={expandedNodes}
          />
        ))}
      </div>
    </div>
  );
}

export default SSOTTreeView;
