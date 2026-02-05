/**
 * RequirementsEditor Component
 * Sprint 155 Day 3 - Track 1: Visual Editor Integration
 *
 * Manages a list of SpecRequirement items.
 *
 * Features:
 * - Display list of requirements
 * - Add/Remove requirements
 * - Reorder with move up/down
 * - Expand/Collapse all
 * - Empty state
 * - Validation summary
 *
 * Architecture: ADR-050 Visual Editor
 */

"use client";

import * as React from "react";
import { SpecRequirement, createEmptyRequirement } from "@/hooks/useSpecConverter";
import { RequirementEditor } from "./RequirementEditor";
import { cn } from "@/lib/utils";
import { Plus, ChevronDown, ChevronUp, AlertCircle } from "lucide-react";

// =============================================================================
// Types
// =============================================================================

interface RequirementsEditorProps {
  requirements: SpecRequirement[];
  onChange: (requirements: SpecRequirement[]) => void;
  canDelete?: boolean;
  confirmDelete?: boolean;
  readonly?: boolean;
  showValidation?: boolean;
  defaultExpanded?: boolean;
  className?: string;
}

// =============================================================================
// Helper Functions
// =============================================================================

function generateUniqueId(existingIds: string[]): string {
  let id: string;
  let counter = Date.now();
  do {
    id = `REQ-${counter}`;
    counter++;
  } while (existingIds.includes(id));
  return id;
}

function validateRequirement(req: SpecRequirement): boolean {
  return Boolean(req.given && req.when && req.then);
}

// =============================================================================
// Main Component
// =============================================================================

export function RequirementsEditor({
  requirements,
  onChange,
  canDelete = true,
  confirmDelete = false,
  readonly = false,
  showValidation = false,
  defaultExpanded = false,
  className,
}: RequirementsEditorProps) {
  const [expandedIds, setExpandedIds] = React.useState<Set<string>>(
    defaultExpanded ? new Set(requirements.map((r) => r.id)) : new Set()
  );
  const [confirmingDeleteId, setConfirmingDeleteId] = React.useState<string | null>(
    null
  );

  // Validation
  const invalidCount = showValidation
    ? requirements.filter((r) => !validateRequirement(r)).length
    : 0;

  // Handlers
  const handleAdd = () => {
    const existingIds = requirements.map((r) => r.id);
    const newId = generateUniqueId(existingIds);
    const newRequirement = createEmptyRequirement(newId);
    onChange([...requirements, newRequirement]);
    // Auto-expand new requirement
    setExpandedIds((prev) => new Set([...prev, newId]));
  };

  const handleDelete = (id: string) => {
    if (confirmDelete && confirmingDeleteId !== id) {
      setConfirmingDeleteId(id);
      return;
    }
    onChange(requirements.filter((r) => r.id !== id));
    setConfirmingDeleteId(null);
  };

  const handleUpdate = (updated: SpecRequirement) => {
    onChange(requirements.map((r) => (r.id === updated.id ? updated : r)));
  };

  const handleMoveUp = (index: number) => {
    if (index === 0) return;
    const newReqs = [...requirements];
    [newReqs[index - 1], newReqs[index]] = [newReqs[index], newReqs[index - 1]];
    onChange(newReqs);
  };

  const handleMoveDown = (index: number) => {
    if (index === requirements.length - 1) return;
    const newReqs = [...requirements];
    [newReqs[index], newReqs[index + 1]] = [newReqs[index + 1], newReqs[index]];
    onChange(newReqs);
  };

  const handleExpandAll = () => {
    setExpandedIds(new Set(requirements.map((r) => r.id)));
  };

  const handleCollapseAll = () => {
    setExpandedIds(new Set());
  };

  const toggleExpanded = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold">Requirements</h3>
          <span className="text-sm text-muted-foreground">
            {requirements.length} requirements
          </span>
          {showValidation && invalidCount > 0 && (
            <span className="flex items-center gap-1 px-2 py-0.5 text-xs font-medium text-destructive bg-destructive/10 rounded">
              <AlertCircle className="h-3 w-3" />
              {invalidCount} invalid
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {requirements.length > 0 && (
            <>
              <button
                type="button"
                onClick={handleExpandAll}
                className="px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
                aria-label="Expand all"
              >
                <ChevronDown className="h-4 w-4" />
                Expand all
              </button>
              <button
                type="button"
                onClick={handleCollapseAll}
                className="px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
                aria-label="Collapse all"
              >
                <ChevronUp className="h-4 w-4" />
                Collapse all
              </button>
            </>
          )}
          {!readonly && (
            <button
              type="button"
              onClick={handleAdd}
              className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
              aria-label="Add requirement"
            >
              <Plus className="h-4 w-4" />
              Add Requirement
            </button>
          )}
        </div>
      </div>

      {/* Empty State */}
      {requirements.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 border-2 border-dashed rounded-lg bg-muted/20">
          <p className="text-muted-foreground mb-4">No requirements yet</p>
          {!readonly && (
            <button
              type="button"
              onClick={handleAdd}
              className="flex items-center gap-1 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
              aria-label="Add first requirement"
            >
              <Plus className="h-4 w-4" />
              Add Requirement
            </button>
          )}
        </div>
      )}

      {/* Requirements List */}
      <div className="space-y-3">
        {requirements.map((requirement, index) => (
          <div
            key={requirement.id}
            data-testid={`requirement-item-${requirement.id}`}
            className="relative"
          >
            {/* Reorder Controls */}
            {!readonly && requirements.length > 1 && (
              <div className="absolute -left-8 top-3 flex flex-col gap-1">
                {index > 0 && (
                  <button
                    type="button"
                    onClick={() => handleMoveUp(index)}
                    className="p-0.5 text-muted-foreground hover:text-foreground"
                    aria-label="Move up"
                  >
                    <ChevronUp className="h-4 w-4" />
                  </button>
                )}
                {index < requirements.length - 1 && (
                  <button
                    type="button"
                    onClick={() => handleMoveDown(index)}
                    className="p-0.5 text-muted-foreground hover:text-foreground"
                    aria-label="Move down"
                  >
                    <ChevronDown className="h-4 w-4" />
                  </button>
                )}
              </div>
            )}

            {/* Requirement Editor */}
            <RequirementEditor
              requirement={requirement}
              onChange={handleUpdate}
              onDelete={handleDelete}
              canDelete={canDelete && !readonly}
              collapsed={!expandedIds.has(requirement.id)}
              onToggleCollapse={(id, collapsed) => {
                setExpandedIds((prev) => {
                  const next = new Set(prev);
                  if (collapsed) {
                    next.delete(id);
                  } else {
                    next.add(id);
                  }
                  return next;
                });
              }}
              readonly={readonly}
              showValidation={showValidation}
            />

            {/* Delete Confirmation */}
            {confirmDelete && confirmingDeleteId === requirement.id && (
              <div className="absolute inset-0 flex items-center justify-center bg-background/80 rounded-lg z-10">
                <div className="flex items-center gap-2 p-4 bg-card border rounded-lg shadow-lg">
                  <p className="text-sm">Are you sure you want to delete this requirement?</p>
                  <button
                    type="button"
                    onClick={() => handleDelete(requirement.id)}
                    className="px-3 py-1 text-sm font-medium bg-destructive text-destructive-foreground rounded hover:bg-destructive/90"
                  >
                    Delete
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmingDeleteId(null)}
                    className="px-3 py-1 text-sm font-medium border rounded hover:bg-muted"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default RequirementsEditor;
