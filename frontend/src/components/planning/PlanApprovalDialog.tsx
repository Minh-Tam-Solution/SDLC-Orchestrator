/**
 * Plan Approval Dialog - SDLC Orchestrator
 *
 * @module frontend/src/components/planning/PlanApprovalDialog
 * @description Dialog component for approving/rejecting planning sessions
 * @sdlc SDLC 5.2.0 Framework - Sprint 99 (Planning Sub-agent Part 2)
 */

import { useState } from "react";
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { ConformanceScoreBadge } from "./ConformanceScoreBadge";
import type { PlanningResult } from "@/lib/types/planning-subagent";

interface PlanApprovalDialogProps {
  plan: PlanningResult | null;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onApprove: (notes?: string) => Promise<void>;
  onReject: (notes: string) => Promise<void>;
  isApproving?: boolean;
  isRejecting?: boolean;
}

export function PlanApprovalDialog({
  plan,
  isOpen,
  onOpenChange,
  onApprove,
  onReject,
  isApproving = false,
  isRejecting = false,
}: PlanApprovalDialogProps) {
  const [mode, setMode] = useState<"approval" | "rejection" | null>(null);
  const [notes, setNotes] = useState("");

  const handleApprove = async () => {
    await onApprove(notes || undefined);
    setNotes("");
    setMode(null);
  };

  const handleReject = async () => {
    if (!notes.trim()) {
      return; // Rejection requires notes
    }
    await onReject(notes);
    setNotes("");
    setMode(null);
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      setNotes("");
      setMode(null);
    }
    onOpenChange(open);
  };

  if (!plan) return null;

  return (
    <AlertDialog open={isOpen} onOpenChange={handleOpenChange}>
      <AlertDialogContent className="max-w-lg">
        <AlertDialogHeader>
          <AlertDialogTitle>
            {mode === "rejection" ? "Reject Plan" : "Approve Plan"}
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-4">
              <p>
                {mode === "rejection"
                  ? "Please provide a reason for rejection. This helps the team understand what changes are needed."
                  : "Review the planning session and decide whether to approve or reject."}
              </p>

              {mode === null && (
                <div className="p-4 bg-muted rounded-lg space-y-3">
                  <div>
                    <span className="text-xs text-muted-foreground">Task</span>
                    <p className="font-medium">{plan.task}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div>
                      <span className="text-xs text-muted-foreground">
                        Conformance
                      </span>
                      <div className="mt-1">
                        <ConformanceScoreBadge
                          score={plan.conformance.score}
                          level={plan.conformance.level}
                          size="sm"
                        />
                      </div>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground">
                        Estimated
                      </span>
                      <p className="font-medium">
                        ~{plan.plan.total_estimated_loc} LOC,{" "}
                        {plan.plan.total_estimated_hours.toFixed(1)}h
                      </p>
                    </div>
                  </div>
                  {plan.conformance.deviations.length > 0 && (
                    <div>
                      <span className="text-xs text-muted-foreground">
                        Deviations
                      </span>
                      <p className="text-sm text-yellow-600">
                        {plan.conformance.deviations.length} pattern deviation
                        {plan.conformance.deviations.length !== 1 ? "s" : ""}{" "}
                        detected
                      </p>
                    </div>
                  )}
                </div>
              )}

              {mode !== null && (
                <div className="space-y-2">
                  <Label htmlFor="notes">
                    {mode === "rejection" ? "Rejection Reason *" : "Notes (optional)"}
                  </Label>
                  <Textarea
                    id="notes"
                    placeholder={
                      mode === "rejection"
                        ? "Explain what changes are required..."
                        : "Add any notes for the approval..."
                    }
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={4}
                  />
                  {mode === "rejection" && !notes.trim() && (
                    <p className="text-xs text-red-500">
                      Rejection reason is required
                    </p>
                  )}
                </div>
              )}
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          {mode === null ? (
            <>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <Button
                variant="destructive"
                onClick={() => setMode("rejection")}
              >
                Reject
              </Button>
              <Button
                variant="default"
                onClick={() => setMode("approval")}
              >
                Approve
              </Button>
            </>
          ) : mode === "rejection" ? (
            <>
              <Button
                variant="ghost"
                onClick={() => {
                  setMode(null);
                  setNotes("");
                }}
              >
                Back
              </Button>
              <Button
                variant="destructive"
                onClick={handleReject}
                disabled={isRejecting || !notes.trim()}
              >
                {isRejecting ? "Rejecting..." : "Confirm Rejection"}
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="ghost"
                onClick={() => {
                  setMode(null);
                  setNotes("");
                }}
              >
                Back
              </Button>
              <Button
                variant="default"
                onClick={handleApprove}
                disabled={isApproving}
              >
                {isApproving ? "Approving..." : "Confirm Approval"}
              </Button>
            </>
          )}
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export default PlanApprovalDialog;
