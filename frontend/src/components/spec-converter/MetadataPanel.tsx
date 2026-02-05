/**
 * MetadataPanel Component
 * Sprint 155 Day 1 - Track 1: Visual Editor Integration
 *
 * Editable panel for SpecIR metadata fields.
 *
 * Features:
 * - Text inputs for title, version, owner
 * - Status dropdown (DRAFT, PROPOSED, APPROVED, DEPRECATED)
 * - Multi-select tier (LITE, STANDARD, PROFESSIONAL, ENTERPRISE)
 * - Array inputs for tags, related_adrs, related_specs
 * - Validation with error messages
 * - Loading and readonly states
 *
 * Architecture: ADR-050 Visual Editor
 */

"use client";

import * as React from "react";
import { SpecIR, SpecStatus, SpecTier } from "@/hooks/useSpecConverter";
import { cn } from "@/lib/utils";
import { X, Plus, Loader2 } from "lucide-react";

// =============================================================================
// Types
// =============================================================================

interface MetadataPanelProps {
  spec: SpecIR;
  onChange: (spec: SpecIR) => void;
  loading?: boolean;
  readonly?: boolean;
  showValidation?: boolean;
  className?: string;
}

interface ChipInputProps {
  items: string[];
  onAdd: (item: string) => void;
  onRemove: (item: string) => void;
  placeholder: string;
  disabled?: boolean;
  readonly?: boolean;
}

// =============================================================================
// Constants
// =============================================================================

const STATUS_OPTIONS: SpecStatus[] = ["DRAFT", "PROPOSED", "APPROVED", "DEPRECATED"];
const TIER_OPTIONS: SpecTier[] = ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"];

// =============================================================================
// Helper Functions
// =============================================================================

function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateString;
  }
}

function isValidSemver(version: string): boolean {
  const semverRegex = /^\d+\.\d+\.\d+(-[\w.]+)?(\+[\w.]+)?$/;
  return semverRegex.test(version);
}

// =============================================================================
// Sub-Components
// =============================================================================

function ChipInput({
  items,
  onAdd,
  onRemove,
  placeholder,
  disabled,
  readonly,
}: ChipInputProps) {
  const [inputValue, setInputValue] = React.useState("");

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && inputValue.trim()) {
      e.preventDefault();
      const newItem = inputValue.trim();
      if (!items.includes(newItem)) {
        onAdd(newItem);
      }
      setInputValue("");
    }
  };

  const handleAddClick = () => {
    if (inputValue.trim() && !items.includes(inputValue.trim())) {
      onAdd(inputValue.trim());
      setInputValue("");
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1">
        {items.map((item) => (
          <span
            key={item}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-muted rounded-md"
          >
            {item}
            {!readonly && (
              <button
                type="button"
                onClick={() => onRemove(item)}
                disabled={disabled}
                className="hover:text-destructive focus:outline-none disabled:opacity-50"
                aria-label={`Remove ${item}`}
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </span>
        ))}
      </div>
      {!readonly && (
        <div className="flex gap-1">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className="flex-1 h-8 px-2 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
          />
          <button
            type="button"
            onClick={handleAddClick}
            disabled={disabled || !inputValue.trim()}
            className="h-8 px-2 text-sm border rounded-md hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
            aria-label="Add"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export function MetadataPanel({
  spec,
  onChange,
  loading = false,
  readonly = false,
  showValidation = false,
  className,
}: MetadataPanelProps) {
  // Validation helpers
  const titleError = showValidation && !spec.title ? "Title is required" : null;
  const versionError =
    showValidation && spec.version && !isValidSemver(spec.version)
      ? "Version must follow semver format (e.g., 1.0.0)"
      : null;
  const tierError =
    showValidation && (!spec.tier || spec.tier.length === 0)
      ? "At least one tier must be selected"
      : null;

  // Update helpers
  const updateField = <K extends keyof SpecIR>(field: K, value: SpecIR[K]) => {
    onChange({
      ...spec,
      [field]: value,
      last_updated: new Date().toISOString(),
    });
  };

  const handleTierChange = (tier: SpecTier, checked: boolean) => {
    const currentTiers = spec.tier.filter((t): t is SpecTier =>
      TIER_OPTIONS.includes(t as SpecTier)
    );

    const newTiers = checked
      ? [...currentTiers, tier]
      : currentTiers.filter((t) => t !== tier);

    updateField("tier", newTiers);
  };

  const handleAddTag = (tag: string) => {
    updateField("tags", [...spec.tags, tag]);
  };

  const handleRemoveTag = (tag: string) => {
    updateField(
      "tags",
      spec.tags.filter((t) => t !== tag)
    );
  };

  const handleAddAdr = (adr: string) => {
    updateField("related_adrs", [...spec.related_adrs, adr]);
  };

  const handleRemoveAdr = (adr: string) => {
    updateField(
      "related_adrs",
      spec.related_adrs.filter((a) => a !== adr)
    );
  };

  const handleAddSpec = (relatedSpec: string) => {
    updateField("related_specs", [...spec.related_specs, relatedSpec]);
  };

  const handleRemoveSpec = (relatedSpec: string) => {
    updateField(
      "related_specs",
      spec.related_specs.filter((s) => s !== relatedSpec)
    );
  };

  return (
    <div className={cn("space-y-4 p-4 border rounded-lg bg-card", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Metadata</h3>
        {loading && (
          <div role="progressbar" aria-label="Loading">
            <Loader2 className="h-4 w-4 animate-spin" />
          </div>
        )}
      </div>

      {/* Spec ID (readonly) */}
      <div className="space-y-1">
        <label htmlFor="spec-id" className="text-sm font-medium">
          Spec ID
        </label>
        <input
          id="spec-id"
          type="text"
          value={spec.spec_id}
          readOnly
          className="w-full h-9 px-3 text-sm border rounded-md bg-muted cursor-not-allowed"
          aria-label="Spec ID"
        />
      </div>

      {/* Title */}
      <div className="space-y-1">
        <label htmlFor="title" className="text-sm font-medium">
          Title
        </label>
        <input
          id="title"
          type="text"
          value={spec.title}
          onChange={(e) => updateField("title", e.target.value)}
          disabled={loading}
          readOnly={readonly}
          className={cn(
            "w-full h-9 px-3 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50",
            readonly && "cursor-not-allowed bg-muted",
            titleError && "border-destructive"
          )}
          aria-label="Title"
          aria-invalid={!!titleError}
          aria-describedby={titleError ? "title-error" : undefined}
        />
        {titleError && (
          <p id="title-error" className="text-xs text-destructive">
            {titleError}
          </p>
        )}
      </div>

      {/* Version */}
      <div className="space-y-1">
        <label htmlFor="version" className="text-sm font-medium">
          Version
        </label>
        <input
          id="version"
          type="text"
          value={spec.version}
          onChange={(e) => updateField("version", e.target.value)}
          disabled={loading}
          readOnly={readonly}
          placeholder="1.0.0"
          className={cn(
            "w-full h-9 px-3 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50",
            readonly && "cursor-not-allowed bg-muted",
            versionError && "border-destructive"
          )}
          aria-label="Version"
          aria-invalid={!!versionError}
          aria-describedby={versionError ? "version-error" : undefined}
        />
        {versionError && (
          <p id="version-error" className="text-xs text-destructive">
            {versionError}
          </p>
        )}
      </div>

      {/* Status */}
      <div className="space-y-1">
        <label htmlFor="status" className="text-sm font-medium">
          Status
        </label>
        <select
          id="status"
          value={spec.status}
          onChange={(e) => updateField("status", e.target.value as SpecStatus)}
          disabled={loading || readonly}
          className={cn(
            "w-full h-9 px-3 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50",
            readonly && "cursor-not-allowed bg-muted"
          )}
          aria-label="Status"
        >
          {STATUS_OPTIONS.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </div>

      {/* Tier (Multi-select checkboxes) */}
      <div className="space-y-2">
        <span className="text-sm font-medium">Tier</span>
        <div className="flex flex-wrap gap-2">
          {TIER_OPTIONS.map((tier) => {
            const isChecked = spec.tier.includes(tier);
            return (
              <label
                key={tier}
                className="inline-flex items-center gap-1 text-sm cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={(e) => handleTierChange(tier, e.target.checked)}
                  disabled={loading || readonly}
                  className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary disabled:opacity-50"
                  aria-label={tier}
                />
                <span
                  className={cn(
                    "px-2 py-0.5 text-xs font-medium rounded",
                    isChecked ? "bg-primary/10 text-primary" : "bg-muted"
                  )}
                >
                  {tier}
                </span>
              </label>
            );
          })}
        </div>
        {tierError && (
          <p className="text-xs text-destructive">{tierError}</p>
        )}
      </div>

      {/* Owner */}
      <div className="space-y-1">
        <label htmlFor="owner" className="text-sm font-medium">
          Owner
        </label>
        <input
          id="owner"
          type="text"
          value={spec.owner}
          onChange={(e) => updateField("owner", e.target.value)}
          disabled={loading}
          readOnly={readonly}
          placeholder="owner@example.com"
          className={cn(
            "w-full h-9 px-3 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50",
            readonly && "cursor-not-allowed bg-muted"
          )}
          aria-label="Owner"
        />
      </div>

      {/* Last Updated (readonly) */}
      <div className="space-y-1">
        <span className="text-sm font-medium">Last Updated</span>
        <p className="text-sm text-muted-foreground">
          {formatDate(spec.last_updated)}
        </p>
      </div>

      {/* Tags */}
      <div className="space-y-2">
        <span className="text-sm font-medium">Tags</span>
        <ChipInput
          items={spec.tags}
          onAdd={handleAddTag}
          onRemove={handleRemoveTag}
          placeholder="Add tag..."
          disabled={loading}
          readonly={readonly}
        />
      </div>

      {/* Related ADRs */}
      <div className="space-y-2">
        <span className="text-sm font-medium">Related ADRs</span>
        <ChipInput
          items={spec.related_adrs}
          onAdd={handleAddAdr}
          onRemove={handleRemoveAdr}
          placeholder="Add ADR (e.g., ADR-001)..."
          disabled={loading}
          readonly={readonly}
        />
      </div>

      {/* Related Specs */}
      <div className="space-y-2">
        <span className="text-sm font-medium">Related Specs</span>
        <ChipInput
          items={spec.related_specs}
          onAdd={handleAddSpec}
          onRemove={handleRemoveSpec}
          placeholder="Add Spec (e.g., SPEC-002)..."
          disabled={loading}
          readonly={readonly}
        />
      </div>
    </div>
  );
}

// =============================================================================
// Exports
// =============================================================================

export default MetadataPanel;
