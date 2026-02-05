/**
 * RequirementEditor Component
 * Sprint 155 Day 2 - Track 1: Visual Editor Integration
 *
 * Editable component for a single SpecRequirement.
 *
 * Features:
 * - BDD fields (Given, When, Then)
 * - Priority dropdown (P0-P3)
 * - Multi-select tier
 * - User story field
 * - Acceptance criteria list
 * - Collapsible state
 * - Delete functionality
 *
 * Architecture: ADR-050 Visual Editor
 */

"use client";

import * as React from "react";
import { SpecRequirement, Priority } from "@/hooks/useSpecConverter";
import { cn } from "@/lib/utils";
import { X, Plus, ChevronDown, ChevronRight, Trash2 } from "lucide-react";

// =============================================================================
// Types
// =============================================================================

interface RequirementEditorProps {
  requirement: SpecRequirement;
  onChange: (requirement: SpecRequirement) => void;
  onDelete: (id: string) => void;
  canDelete?: boolean;
  defaultCollapsed?: boolean;
  collapsed?: boolean; // Controlled collapse state
  onToggleCollapse?: (id: string, collapsed: boolean) => void; // Callback for controlled mode
  readonly?: boolean;
  showValidation?: boolean;
  className?: string;
}

// =============================================================================
// Constants
// =============================================================================

const PRIORITY_OPTIONS: Priority[] = ["P0", "P1", "P2", "P3"];
const TIER_OPTIONS = ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"];

const PRIORITY_COLORS: Record<Priority, string> = {
  P0: "bg-red-100 text-red-700 border-red-200",
  P1: "bg-orange-100 text-orange-700 border-orange-200",
  P2: "bg-yellow-100 text-yellow-700 border-yellow-200",
  P3: "bg-green-100 text-green-700 border-green-200",
};

// =============================================================================
// Main Component
// =============================================================================

export function RequirementEditor({
  requirement,
  onChange,
  onDelete,
  canDelete = true,
  defaultCollapsed = false,
  collapsed,
  onToggleCollapse,
  readonly = false,
  showValidation = false,
  className,
}: RequirementEditorProps) {
  // Support both controlled and uncontrolled modes
  const [uncontrolledCollapsed, setUncontrolledCollapsed] = React.useState(defaultCollapsed);
  const isControlled = collapsed !== undefined;
  const isCollapsed = isControlled ? collapsed : uncontrolledCollapsed;

  const handleToggleCollapse = () => {
    if (isControlled && onToggleCollapse) {
      onToggleCollapse(requirement.id, !isCollapsed);
    } else {
      setUncontrolledCollapsed(!isCollapsed);
    }
  };

  const [newCriterion, setNewCriterion] = React.useState("");

  // Validation
  const givenError = showValidation && !requirement.given ? "Given is required" : null;
  const whenError = showValidation && !requirement.when ? "When is required" : null;
  const thenError = showValidation && !requirement.then ? "Then is required" : null;

  // Update helpers
  const updateField = <K extends keyof SpecRequirement>(
    field: K,
    value: SpecRequirement[K]
  ) => {
    onChange({ ...requirement, [field]: value });
  };

  const handleTierChange = (tier: string, checked: boolean) => {
    const currentTiers = requirement.tier;
    const newTiers = checked
      ? [...currentTiers, tier]
      : currentTiers.filter((t) => t !== tier);
    updateField("tier", newTiers);
  };

  const handleAddCriterion = () => {
    if (newCriterion.trim()) {
      updateField("acceptance_criteria", [
        ...requirement.acceptance_criteria,
        newCriterion.trim(),
      ]);
      setNewCriterion("");
    }
  };

  const handleRemoveCriterion = (index: number) => {
    const newCriteria = requirement.acceptance_criteria.filter((_, i) => i !== index);
    updateField("acceptance_criteria", newCriteria);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddCriterion();
    }
  };

  return (
    <div
      className={cn(
        "border rounded-lg bg-card overflow-hidden",
        className
      )}
    >
      {/* Header */}
      <div
        className={cn(
          "flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-muted/50",
          PRIORITY_COLORS[requirement.priority]
        )}
        onClick={handleToggleCollapse}
      >
        <div className="flex items-center gap-2">
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
          <span className="font-semibold">{requirement.id}</span>
          <span className="text-sm truncate max-w-xs">{requirement.title}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-background/50">
            {requirement.priority}
          </span>
          {canDelete && !readonly && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(requirement.id);
              }}
              className="p-1 hover:text-destructive focus:outline-none"
              aria-label="Delete requirement"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Body - Collapsible */}
      <div
        data-testid={`requirement-body-${requirement.id}`}
        data-collapsed={isCollapsed}
        className={cn(
          "transition-all duration-200",
          isCollapsed ? "hidden" : "block"
        )}
      >
        <div className="p-4 space-y-4 border-t">
          {/* Title */}
          <div className="space-y-1">
            <label htmlFor={`${requirement.id}-title`} className="text-sm font-medium">
              Title
            </label>
            <input
              id={`${requirement.id}-title`}
              type="text"
              value={requirement.title}
              onChange={(e) => updateField("title", e.target.value)}
              readOnly={readonly}
              className={cn(
                "w-full h-9 px-3 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring",
                readonly && "cursor-not-allowed bg-muted"
              )}
              aria-label="Title"
            />
          </div>

          {/* Priority & Tier Row */}
          <div className="grid grid-cols-2 gap-4">
            {/* Priority */}
            <div className="space-y-1">
              <label htmlFor={`${requirement.id}-priority`} className="text-sm font-medium">
                Priority
              </label>
              <select
                id={`${requirement.id}-priority`}
                value={requirement.priority}
                onChange={(e) => updateField("priority", e.target.value as Priority)}
                disabled={readonly}
                className={cn(
                  "w-full h-9 px-3 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring",
                  readonly && "cursor-not-allowed bg-muted"
                )}
                aria-label="Priority"
              >
                {PRIORITY_OPTIONS.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>

            {/* Tier */}
            <div className="space-y-1">
              <span className="text-sm font-medium">Tier</span>
              <div className="flex flex-wrap gap-1">
                {TIER_OPTIONS.map((tier) => {
                  const isChecked = requirement.tier.includes(tier);
                  return (
                    <label
                      key={tier}
                      className="inline-flex items-center gap-1 text-xs cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={(e) => handleTierChange(tier, e.target.checked)}
                        disabled={readonly}
                        className="h-3 w-3 rounded border-gray-300"
                        aria-label={tier}
                      />
                      <span
                        className={cn(
                          "px-1 py-0.5 text-xs rounded",
                          isChecked ? "bg-primary/10 text-primary" : "bg-muted"
                        )}
                      >
                        {tier}
                      </span>
                    </label>
                  );
                })}
              </div>
            </div>
          </div>

          {/* BDD Fields */}
          <div className="space-y-3 bg-muted/30 rounded-lg p-3">
            <h4 className="text-sm font-semibold text-muted-foreground">
              BDD Specification
            </h4>

            {/* Given */}
            <div className="space-y-1">
              <label htmlFor={`${requirement.id}-given`} className="text-sm font-medium">
                Given
              </label>
              <input
                id={`${requirement.id}-given`}
                type="text"
                value={requirement.given}
                onChange={(e) => updateField("given", e.target.value)}
                readOnly={readonly}
                placeholder="A precondition or context..."
                className={cn(
                  "w-full h-9 px-3 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring",
                  readonly && "cursor-not-allowed bg-muted",
                  givenError && "border-destructive"
                )}
                aria-label="Given"
                aria-invalid={!!givenError}
              />
              {givenError && (
                <p className="text-xs text-destructive">{givenError}</p>
              )}
            </div>

            {/* When */}
            <div className="space-y-1">
              <label htmlFor={`${requirement.id}-when`} className="text-sm font-medium">
                When
              </label>
              <input
                id={`${requirement.id}-when`}
                type="text"
                value={requirement.when}
                onChange={(e) => updateField("when", e.target.value)}
                readOnly={readonly}
                placeholder="An action or event..."
                className={cn(
                  "w-full h-9 px-3 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring",
                  readonly && "cursor-not-allowed bg-muted",
                  whenError && "border-destructive"
                )}
                aria-label="When"
                aria-invalid={!!whenError}
              />
              {whenError && (
                <p className="text-xs text-destructive">{whenError}</p>
              )}
            </div>

            {/* Then */}
            <div className="space-y-1">
              <label htmlFor={`${requirement.id}-then`} className="text-sm font-medium">
                Then
              </label>
              <input
                id={`${requirement.id}-then`}
                type="text"
                value={requirement.then}
                onChange={(e) => updateField("then", e.target.value)}
                readOnly={readonly}
                placeholder="An expected outcome..."
                className={cn(
                  "w-full h-9 px-3 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring",
                  readonly && "cursor-not-allowed bg-muted",
                  thenError && "border-destructive"
                )}
                aria-label="Then"
                aria-invalid={!!thenError}
              />
              {thenError && (
                <p className="text-xs text-destructive">{thenError}</p>
              )}
            </div>
          </div>

          {/* User Story */}
          <div className="space-y-1">
            <label htmlFor={`${requirement.id}-user-story`} className="text-sm font-medium">
              User Story
            </label>
            <textarea
              id={`${requirement.id}-user-story`}
              value={requirement.user_story || ""}
              onChange={(e) => updateField("user_story", e.target.value)}
              readOnly={readonly}
              placeholder="As a [user], I want to [action] so that [benefit]..."
              rows={2}
              className={cn(
                "w-full px-3 py-2 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring resize-none",
                readonly && "cursor-not-allowed bg-muted"
              )}
              aria-label="User Story"
            />
          </div>

          {/* Acceptance Criteria */}
          <div className="space-y-2">
            <span className="text-sm font-medium">Acceptance Criteria</span>
            <div className="space-y-1">
              {requirement.acceptance_criteria.map((criterion, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 px-2 py-1 bg-muted/50 rounded text-sm"
                >
                  <span className="text-muted-foreground">•</span>
                  <span className="flex-1">{criterion}</span>
                  {!readonly && (
                    <button
                      type="button"
                      onClick={() => handleRemoveCriterion(index)}
                      className="p-0.5 hover:text-destructive focus:outline-none"
                      aria-label="Remove criterion"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  )}
                </div>
              ))}
            </div>
            {!readonly && (
              <div className="flex gap-1">
                <input
                  type="text"
                  value={newCriterion}
                  onChange={(e) => setNewCriterion(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Add acceptance criterion..."
                  className="flex-1 h-8 px-2 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <button
                  type="button"
                  onClick={handleAddCriterion}
                  disabled={!newCriterion.trim()}
                  className="h-8 px-2 text-sm border rounded-md hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                  aria-label="Add criterion"
                >
                  <Plus className="h-4 w-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default RequirementEditor;
