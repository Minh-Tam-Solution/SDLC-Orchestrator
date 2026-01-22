/**
 * Phase Modal - SDLC Orchestrator
 *
 * @module frontend/src/app/app/planning/components/PhaseModal
 * @description Modal for creating/editing Phases (4-8 week theme-based grouping)
 * @sdlc SDLC 5.1.3 Framework - Sprint 92 (Planning Hierarchy Part 1)
 * @status Sprint 92 - Phase Management UI Implementation
 */

"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCreatePhase, useUpdatePhase } from "@/hooks/usePlanningHierarchy";
import type { Phase, PhaseInput } from "@/lib/types/planning";

// =============================================================================
// ICONS
// =============================================================================

function LoaderIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
    </svg>
  );
}

// =============================================================================
// TYPES
// =============================================================================

interface PhaseModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  roadmapId: string;
  roadmapName?: string;
  phase?: Phase | null; // null for create, Phase for edit
  onSuccess?: () => void;
}

interface FormState {
  name: string;
  description: string;
  theme: string;
  start_date: string;
  end_date: string;
  order: number;
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Get default dates for a new phase (6 weeks)
 */
function getDefaultDates(): { start_date: string; end_date: string } {
  const today = new Date();
  const startDate = new Date(today);
  const endDate = new Date(today);
  endDate.setDate(endDate.getDate() + 42); // 6 weeks

  return {
    start_date: startDate.toISOString().split("T")[0],
    end_date: endDate.toISOString().split("T")[0],
  };
}

/**
 * Validate form data
 */
function validateForm(form: FormState): string | null {
  if (!form.name.trim()) {
    return "Phase name is required";
  }
  if (form.name.length > 100) {
    return "Phase name must be 100 characters or less";
  }
  if (!form.start_date) {
    return "Start date is required";
  }
  if (!form.end_date) {
    return "End date is required";
  }
  if (new Date(form.start_date) >= new Date(form.end_date)) {
    return "End date must be after start date";
  }
  if (form.order < 0) {
    return "Order must be a positive number";
  }
  return null;
}

// =============================================================================
// THEME SUGGESTIONS
// =============================================================================

const THEME_SUGGESTIONS = [
  "Foundation",
  "Core Features",
  "User Experience",
  "Performance",
  "Security Hardening",
  "Integration",
  "Testing & QA",
  "Documentation",
  "Launch Prep",
  "Post-Launch",
];

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function PhaseModal({
  open,
  onOpenChange,
  roadmapId,
  roadmapName,
  phase,
  onSuccess,
}: PhaseModalProps) {
  const isEdit = !!phase;
  const defaults = getDefaultDates();

  const [form, setForm] = useState<FormState>({
    name: "",
    description: "",
    theme: "",
    start_date: defaults.start_date,
    end_date: defaults.end_date,
    order: 0,
  });
  const [error, setError] = useState<string | null>(null);
  const [showThemeSuggestions, setShowThemeSuggestions] = useState(false);

  // Initialize form when editing
  useEffect(() => {
    if (phase) {
      setForm({
        name: phase.name,
        description: phase.description || "",
        theme: phase.theme || "",
        start_date: phase.start_date.split("T")[0],
        end_date: phase.end_date.split("T")[0],
        order: phase.order,
      });
    } else {
      const defaults = getDefaultDates();
      setForm({
        name: "",
        description: "",
        theme: "",
        start_date: defaults.start_date,
        end_date: defaults.end_date,
        order: 0,
      });
    }
    setError(null);
  }, [phase, open]);

  // Mutations
  const createMutation = useCreatePhase();
  const updateMutation = useUpdatePhase(phase?.id || "");

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  // Handle form field changes
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: name === "order" ? parseInt(value) || 0 : value,
    }));
    setError(null);
  };

  // Handle theme selection
  const handleThemeSelect = (theme: string) => {
    setForm((prev) => ({ ...prev, theme }));
    setShowThemeSuggestions(false);
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const validationError = validateForm(form);
    if (validationError) {
      setError(validationError);
      return;
    }

    const data: PhaseInput = {
      name: form.name.trim(),
      description: form.description.trim() || undefined,
      roadmap_id: roadmapId,
      start_date: form.start_date,
      end_date: form.end_date,
      theme: form.theme.trim() || undefined,
      order: form.order,
    };

    try {
      if (isEdit) {
        await updateMutation.mutateAsync({
          name: data.name,
          description: data.description,
          start_date: data.start_date,
          end_date: data.end_date,
          theme: data.theme,
          order: data.order,
        });
      } else {
        await createMutation.mutateAsync(data);
      }
      onOpenChange(false);
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save phase");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FolderIcon className="h-5 w-5 text-blue-600" />
            {isEdit ? "Edit Phase" : "Create New Phase"}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update the phase details."
              : roadmapName
                ? `Add a new phase to "${roadmapName}". Phases are 4-8 week themed iterations.`
                : "Create a new phase. Phases are 4-8 week themed iterations within a roadmap."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Error Display */}
          {error && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Name Field */}
          <div className="space-y-2">
            <label htmlFor="name" className="text-sm font-medium text-gray-700">
              Phase Name <span className="text-red-500">*</span>
            </label>
            <Input
              id="name"
              name="name"
              value={form.name}
              onChange={handleChange}
              placeholder="e.g., Phase 1: Foundation"
              disabled={isSubmitting}
              maxLength={100}
            />
            <p className="text-xs text-gray-500">
              {form.name.length}/100 characters
            </p>
          </div>

          {/* Theme Field with Suggestions */}
          <div className="relative space-y-2">
            <label htmlFor="theme" className="text-sm font-medium text-gray-700">
              Theme
            </label>
            <div className="relative">
              <Input
                id="theme"
                name="theme"
                value={form.theme}
                onChange={handleChange}
                onFocus={() => setShowThemeSuggestions(true)}
                placeholder="e.g., Core Features"
                disabled={isSubmitting}
                maxLength={50}
              />
              {showThemeSuggestions && (
                <div className="absolute z-10 mt-1 w-full rounded-md border border-gray-200 bg-white shadow-lg">
                  <div className="max-h-40 overflow-auto p-1">
                    {THEME_SUGGESTIONS.filter((t) =>
                      t.toLowerCase().includes(form.theme.toLowerCase())
                    ).map((theme) => (
                      <button
                        key={theme}
                        type="button"
                        className="w-full rounded px-3 py-1.5 text-left text-sm hover:bg-gray-100"
                        onClick={() => handleThemeSelect(theme)}
                      >
                        {theme}
                      </button>
                    ))}
                  </div>
                  <button
                    type="button"
                    className="w-full border-t px-3 py-1.5 text-left text-xs text-gray-500 hover:bg-gray-50"
                    onClick={() => setShowThemeSuggestions(false)}
                  >
                    Close suggestions
                  </button>
                </div>
              )}
            </div>
            <p className="text-xs text-gray-500">
              Theme helps categorize the focus of this phase
            </p>
          </div>

          {/* Description Field */}
          <div className="space-y-2">
            <label htmlFor="description" className="text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              value={form.description}
              onChange={handleChange}
              placeholder="Describe the goals and deliverables for this phase..."
              disabled={isSubmitting}
              rows={3}
              className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>

          {/* Date Fields */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="start_date" className="text-sm font-medium text-gray-700">
                Start Date <span className="text-red-500">*</span>
              </label>
              <Input
                id="start_date"
                name="start_date"
                type="date"
                value={form.start_date}
                onChange={handleChange}
                disabled={isSubmitting}
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="end_date" className="text-sm font-medium text-gray-700">
                End Date <span className="text-red-500">*</span>
              </label>
              <Input
                id="end_date"
                name="end_date"
                type="date"
                value={form.end_date}
                onChange={handleChange}
                disabled={isSubmitting}
              />
            </div>
          </div>

          {/* Order Field */}
          <div className="space-y-2">
            <label htmlFor="order" className="text-sm font-medium text-gray-700">
              Display Order
            </label>
            <Input
              id="order"
              name="order"
              type="number"
              min="0"
              value={form.order}
              onChange={handleChange}
              disabled={isSubmitting}
            />
            <p className="text-xs text-gray-500">
              Lower numbers appear first in the hierarchy
            </p>
          </div>

          {/* Duration Info */}
          {form.start_date && form.end_date && new Date(form.start_date) < new Date(form.end_date) && (
            <div className="rounded-md bg-blue-50 p-3 text-sm text-blue-700">
              <strong>Duration:</strong>{" "}
              {Math.ceil(
                (new Date(form.end_date).getTime() - new Date(form.start_date).getTime()) /
                  (1000 * 60 * 60 * 24 * 7)
              )}{" "}
              weeks
              {(() => {
                const weeks = Math.ceil(
                  (new Date(form.end_date).getTime() - new Date(form.start_date).getTime()) /
                    (1000 * 60 * 60 * 24 * 7)
                );
                if (weeks < 4) return " (below recommended 4-8 weeks)";
                if (weeks > 8) return " (above recommended 4-8 weeks)";
                return " (within recommended range)";
              })()}
            </div>
          )}

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && (
                <LoaderIcon className="mr-2 h-4 w-4 animate-spin" />
              )}
              {isEdit ? "Save Changes" : "Create Phase"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default PhaseModal;
