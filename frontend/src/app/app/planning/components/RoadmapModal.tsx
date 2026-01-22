/**
 * Roadmap Modal - SDLC Orchestrator
 *
 * @module frontend/src/app/app/planning/components/RoadmapModal
 * @description Modal for creating/editing Roadmaps (12-month vision with quarterly milestones)
 * @sdlc SDLC 5.1.3 Framework - Sprint 92 (Planning Hierarchy Part 1)
 * @status Sprint 92 - Roadmap CRUD UI Implementation
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
import { useCreateRoadmap, useUpdateRoadmap } from "@/hooks/usePlanningHierarchy";
import type { Roadmap, RoadmapInput } from "@/lib/types/planning";

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

function MapIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498 4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 0 0-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0Z" />
    </svg>
  );
}

// =============================================================================
// TYPES
// =============================================================================

interface RoadmapModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: string;
  roadmap?: Roadmap | null; // null for create, Roadmap for edit
  onSuccess?: () => void;
}

interface FormState {
  name: string;
  description: string;
  start_date: string;
  end_date: string;
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Get default dates for a new roadmap (12-month span)
 */
function getDefaultDates(): { start_date: string; end_date: string } {
  const today = new Date();
  const startDate = new Date(today.getFullYear(), today.getMonth(), 1);
  const endDate = new Date(today.getFullYear() + 1, today.getMonth(), 0);

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
    return "Roadmap name is required";
  }
  if (form.name.length > 100) {
    return "Roadmap name must be 100 characters or less";
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
  return null;
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function RoadmapModal({
  open,
  onOpenChange,
  projectId,
  roadmap,
  onSuccess,
}: RoadmapModalProps) {
  const isEdit = !!roadmap;
  const defaults = getDefaultDates();

  const [form, setForm] = useState<FormState>({
    name: "",
    description: "",
    start_date: defaults.start_date,
    end_date: defaults.end_date,
  });
  const [error, setError] = useState<string | null>(null);

  // Initialize form when editing
  useEffect(() => {
    if (roadmap) {
      setForm({
        name: roadmap.name,
        description: roadmap.description || "",
        start_date: roadmap.start_date.split("T")[0],
        end_date: roadmap.end_date.split("T")[0],
      });
    } else {
      const defaults = getDefaultDates();
      setForm({
        name: "",
        description: "",
        start_date: defaults.start_date,
        end_date: defaults.end_date,
      });
    }
    setError(null);
  }, [roadmap, open]);

  // Mutations
  const createMutation = useCreateRoadmap();
  const updateMutation = useUpdateRoadmap(roadmap?.id || "");

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  // Handle form field changes
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setError(null);
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const validationError = validateForm(form);
    if (validationError) {
      setError(validationError);
      return;
    }

    const data: RoadmapInput = {
      name: form.name.trim(),
      description: form.description.trim() || undefined,
      project_id: projectId,
      start_date: form.start_date,
      end_date: form.end_date,
    };

    try {
      if (isEdit) {
        await updateMutation.mutateAsync({
          name: data.name,
          description: data.description,
          start_date: data.start_date,
          end_date: data.end_date,
        });
      } else {
        await createMutation.mutateAsync(data);
      }
      onOpenChange(false);
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save roadmap");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MapIcon className="h-5 w-5 text-purple-600" />
            {isEdit ? "Edit Roadmap" : "Create New Roadmap"}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update the roadmap details. Roadmaps represent 12-month strategic visions."
              : "Create a new roadmap to define a 12-month strategic vision with quarterly milestones."}
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
              Roadmap Name <span className="text-red-500">*</span>
            </label>
            <Input
              id="name"
              name="name"
              value={form.name}
              onChange={handleChange}
              placeholder="e.g., 2026 Product Roadmap"
              disabled={isSubmitting}
              maxLength={100}
            />
            <p className="text-xs text-gray-500">
              {form.name.length}/100 characters
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
              placeholder="Describe the strategic vision and goals for this roadmap..."
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

          {/* Duration Info */}
          {form.start_date && form.end_date && new Date(form.start_date) < new Date(form.end_date) && (
            <div className="rounded-md bg-purple-50 p-3 text-sm text-purple-700">
              <strong>Duration:</strong>{" "}
              {Math.ceil(
                (new Date(form.end_date).getTime() - new Date(form.start_date).getTime()) /
                  (1000 * 60 * 60 * 24 * 30)
              )}{" "}
              months
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
              {isEdit ? "Save Changes" : "Create Roadmap"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default RoadmapModal;
