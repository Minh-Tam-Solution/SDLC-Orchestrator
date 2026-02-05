/**
 * AcceptanceCriteriaEditor Component
 * Sprint 155 Day 3 - Track 1: Visual Editor Integration
 *
 * Manages a list of AcceptanceCriterion items.
 *
 * Features:
 * - Display list of acceptance criteria
 * - Add/Remove criteria
 * - Edit BDD fields (scenario, given, when, then)
 * - Tier selection
 * - Testable toggle
 * - Validation
 *
 * Architecture: ADR-050 Visual Editor
 */

"use client";

import * as React from "react";
import { AcceptanceCriterion, createEmptyAcceptanceCriterion } from "@/hooks/useSpecConverter";
import { cn } from "@/lib/utils";
import { Plus, Trash2, ChevronDown, ChevronRight, AlertCircle, CheckCircle2 } from "lucide-react";

// =============================================================================
// Types
// =============================================================================

interface AcceptanceCriteriaEditorProps {
  criteria: AcceptanceCriterion[];
  onChange: (criteria: AcceptanceCriterion[]) => void;
  readonly?: boolean;
  showValidation?: boolean;
  defaultExpanded?: boolean;
  className?: string;
}

// =============================================================================
// Constants
// =============================================================================

const TIER_OPTIONS = ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"];

// =============================================================================
// Helper Functions
// =============================================================================

function generateUniqueId(existingIds: string[]): string {
  let id: string;
  let counter = Date.now();
  do {
    id = `AC-${counter}`;
    counter++;
  } while (existingIds.includes(id));
  return id;
}

function validateCriterion(criterion: AcceptanceCriterion): boolean {
  return Boolean(
    criterion.scenario &&
      criterion.given &&
      criterion.when &&
      criterion.then
  );
}

// =============================================================================
// CriterionEditor Sub-Component
// =============================================================================

interface CriterionEditorProps {
  criterion: AcceptanceCriterion;
  onChange: (criterion: AcceptanceCriterion) => void;
  onDelete: () => void;
  readonly?: boolean;
  showValidation?: boolean;
  defaultCollapsed?: boolean;
}

function CriterionEditor({
  criterion,
  onChange,
  onDelete,
  readonly = false,
  showValidation = false,
  defaultCollapsed = true,
}: CriterionEditorProps) {
  const [isCollapsed, setIsCollapsed] = React.useState(defaultCollapsed);

  const scenarioError = showValidation && !criterion.scenario ? "Scenario is required" : null;
  const givenError = showValidation && !criterion.given ? "Given is required" : null;
  const whenError = showValidation && !criterion.when ? "When is required" : null;
  const thenError = showValidation && !criterion.then ? "Then is required" : null;

  const updateField = <K extends keyof AcceptanceCriterion>(
    field: K,
    value: AcceptanceCriterion[K]
  ) => {
    onChange({ ...criterion, [field]: value });
  };

  const handleTierChange = (tier: string, checked: boolean) => {
    const currentTiers = criterion.tier;
    const newTiers = checked
      ? [...currentTiers, tier]
      : currentTiers.filter((t) => t !== tier);
    updateField("tier", newTiers);
  };

  return (
    <div className="border rounded-lg bg-card overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-muted/50"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <div className="flex items-center gap-2">
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
          <span className="font-medium">{criterion.scenario || "(No scenario)"}</span>
          {criterion.testable && (
            <span className="flex items-center gap-1 px-2 py-0.5 text-xs font-medium text-green-700 bg-green-100 rounded">
              <CheckCircle2 className="h-3 w-3" />
              Testable
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">{criterion.id}</span>
          {!readonly && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="p-1 hover:text-destructive focus:outline-none"
              aria-label="Delete criterion"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Body - Collapsible */}
      <div
        data-testid={`criterion-body-${criterion.id}`}
        data-collapsed={isCollapsed}
        className={cn(
          "transition-all duration-200",
          isCollapsed ? "hidden" : "block"
        )}
      >
        <div className="p-4 space-y-4 border-t">
          {/* Scenario */}
          <div className="space-y-1">
            <label htmlFor={`${criterion.id}-scenario`} className="text-sm font-medium">
              Scenario
            </label>
            <input
              id={`${criterion.id}-scenario`}
              type="text"
              value={criterion.scenario}
              onChange={(e) => updateField("scenario", e.target.value)}
              readOnly={readonly}
              placeholder="Describe the test scenario..."
              className={cn(
                "w-full h-9 px-3 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring",
                readonly && "cursor-not-allowed bg-muted",
                scenarioError && "border-destructive"
              )}
              aria-label="Scenario"
            />
            {scenarioError && (
              <p className="text-xs text-destructive">{scenarioError}</p>
            )}
          </div>

          {/* BDD Fields */}
          <div className="space-y-3 bg-muted/30 rounded-lg p-3">
            <h4 className="text-sm font-semibold text-muted-foreground">
              BDD Specification
            </h4>

            {/* Given */}
            <div className="space-y-1">
              <label htmlFor={`${criterion.id}-given`} className="text-sm font-medium">
                Given
              </label>
              <input
                id={`${criterion.id}-given`}
                type="text"
                value={criterion.given}
                onChange={(e) => updateField("given", e.target.value)}
                readOnly={readonly}
                placeholder="A precondition..."
                className={cn(
                  "w-full h-9 px-3 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring",
                  readonly && "cursor-not-allowed bg-muted",
                  givenError && "border-destructive"
                )}
                aria-label="Given"
              />
              {givenError && (
                <p className="text-xs text-destructive">{givenError}</p>
              )}
            </div>

            {/* When */}
            <div className="space-y-1">
              <label htmlFor={`${criterion.id}-when`} className="text-sm font-medium">
                When
              </label>
              <input
                id={`${criterion.id}-when`}
                type="text"
                value={criterion.when}
                onChange={(e) => updateField("when", e.target.value)}
                readOnly={readonly}
                placeholder="An action..."
                className={cn(
                  "w-full h-9 px-3 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring",
                  readonly && "cursor-not-allowed bg-muted",
                  whenError && "border-destructive"
                )}
                aria-label="When"
              />
              {whenError && (
                <p className="text-xs text-destructive">{whenError}</p>
              )}
            </div>

            {/* Then */}
            <div className="space-y-1">
              <label htmlFor={`${criterion.id}-then`} className="text-sm font-medium">
                Then
              </label>
              <input
                id={`${criterion.id}-then`}
                type="text"
                value={criterion.then}
                onChange={(e) => updateField("then", e.target.value)}
                readOnly={readonly}
                placeholder="An expected outcome..."
                className={cn(
                  "w-full h-9 px-3 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring",
                  readonly && "cursor-not-allowed bg-muted",
                  thenError && "border-destructive"
                )}
                aria-label="Then"
              />
              {thenError && (
                <p className="text-xs text-destructive">{thenError}</p>
              )}
            </div>
          </div>

          {/* Tier & Testable Row */}
          <div className="grid grid-cols-2 gap-4">
            {/* Tier */}
            <div className="space-y-1">
              <span className="text-sm font-medium">Tier</span>
              <div className="flex flex-wrap gap-1">
                {TIER_OPTIONS.map((tier) => {
                  const isChecked = criterion.tier.includes(tier);
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

            {/* Testable */}
            <div className="space-y-1">
              <span className="text-sm font-medium">Testability</span>
              <label className="inline-flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={criterion.testable}
                  onChange={(e) => updateField("testable", e.target.checked)}
                  disabled={readonly}
                  className="h-4 w-4 rounded border-gray-300"
                  aria-label="Testable"
                />
                <span className="text-sm">Testable criterion</span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export function AcceptanceCriteriaEditor({
  criteria,
  onChange,
  readonly = false,
  showValidation = false,
  defaultExpanded = false,
  className,
}: AcceptanceCriteriaEditorProps) {
  // Validation
  const invalidCount = showValidation
    ? criteria.filter((c) => !validateCriterion(c)).length
    : 0;

  // Handlers
  const handleAdd = () => {
    const existingIds = criteria.map((c) => c.id);
    const newId = generateUniqueId(existingIds);
    const newCriterion = createEmptyAcceptanceCriterion(newId);
    onChange([...criteria, newCriterion]);
  };

  const handleDelete = (id: string) => {
    onChange(criteria.filter((c) => c.id !== id));
  };

  const handleUpdate = (updated: AcceptanceCriterion) => {
    onChange(criteria.map((c) => (c.id === updated.id ? updated : c)));
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold">Acceptance Criteria</h3>
          <span className="text-sm text-muted-foreground">
            {criteria.length} criteria
          </span>
          {showValidation && invalidCount > 0 && (
            <span className="flex items-center gap-1 px-2 py-0.5 text-xs font-medium text-destructive bg-destructive/10 rounded">
              <AlertCircle className="h-3 w-3" />
              {invalidCount} invalid
            </span>
          )}
        </div>
        {!readonly && (
          <button
            type="button"
            onClick={handleAdd}
            className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            aria-label="Add criterion"
          >
            <Plus className="h-4 w-4" />
            Add Criterion
          </button>
        )}
      </div>

      {/* Empty State */}
      {criteria.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 border-2 border-dashed rounded-lg bg-muted/20">
          <p className="text-muted-foreground mb-4">No acceptance criteria yet</p>
          {!readonly && (
            <button
              type="button"
              onClick={handleAdd}
              className="flex items-center gap-1 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
              aria-label="Add first criterion"
            >
              <Plus className="h-4 w-4" />
              Add Criterion
            </button>
          )}
        </div>
      )}

      {/* Criteria List */}
      <div className="space-y-3">
        {criteria.map((criterion) => (
          <CriterionEditor
            key={criterion.id}
            criterion={criterion}
            onChange={handleUpdate}
            onDelete={() => handleDelete(criterion.id)}
            readonly={readonly}
            showValidation={showValidation}
            defaultCollapsed={!defaultExpanded}
          />
        ))}
      </div>
    </div>
  );
}

export default AcceptanceCriteriaEditor;
