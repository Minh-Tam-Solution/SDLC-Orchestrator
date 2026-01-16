/**
 * Gate Detail Page - Next.js App Router
 * @module frontend/landing/src/app/app/gates/[id]/page
 * @status Sprint 64 - Route Group Migration
 * @description Gate detail with approval workflow, exit criteria, and evidence
 */
"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import { useGate } from "@/hooks/useGates";
import { useAuth } from "@/hooks/useAuth";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * SDLC 5.1.1 Stage Definitions (10 Stages: 00-09)
 */
const SDLC_STAGES = [
  { code: "00", name: "FOUNDATION", description: "Strategic Discovery & Validation" },
  { code: "01", name: "PLANNING", description: "Requirements & User Stories" },
  { code: "02", name: "DESIGN", description: "Architecture & Technical Design" },
  { code: "03", name: "INTEGRATE", description: "API Contracts & Third-party Setup" },
  { code: "04", name: "BUILD", description: "Development & Implementation" },
  { code: "05", name: "TEST", description: "Quality Assurance & Validation" },
  { code: "06", name: "DEPLOY", description: "Release & Deployment" },
  { code: "07", name: "OPERATE", description: "Production Operations & Monitoring" },
  { code: "08", name: "COLLABORATE", description: "Team Coordination & Knowledge" },
  { code: "09", name: "GOVERN", description: "Compliance & Strategic Oversight" },
];

/**
 * Get status badge styling
 */
function getStatusStyle(status: string): string {
  switch (status) {
    case "APPROVED":
      return "bg-green-100 text-green-700 border-green-200";
    case "REJECTED":
      return "bg-red-100 text-red-700 border-red-200";
    case "PENDING_APPROVAL":
      return "bg-yellow-100 text-yellow-700 border-yellow-200";
    case "DRAFT":
      return "bg-blue-100 text-blue-700 border-blue-200";
    default:
      return "bg-gray-100 text-gray-700 border-gray-200";
  }
}

interface PageProps {
  params: { id: string } | Promise<{ id: string }>;
}

export default function GateDetailPage({ params }: PageProps) {
  // Handle both sync and async params (Next.js 14 compatibility)
  const resolvedParams = params instanceof Promise ? use(params) : params;
  const { id } = resolvedParams;
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { data: gate, isLoading, error } = useGate(id);

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // Submit gate for approval
  const submitMutation = useMutation({
    mutationFn: async () => {
      const token = localStorage.getItem("access_token");
      if (!token) throw new Error("Not authenticated");

      const response = await fetch(`${API_BASE_URL}/gates/${id}/submit`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ message: "Submitting for approval" }),
      });
      if (!response.ok) throw new Error("Failed to submit gate");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gates", "detail", id] });
    },
  });

  // Approve/reject gate
  const approveMutation = useMutation({
    mutationFn: async (approved: boolean) => {
      const token = localStorage.getItem("access_token");
      if (!token) throw new Error("Not authenticated");

      const response = await fetch(`${API_BASE_URL}/gates/${id}/approve`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          approved,
          comments: approved ? "Approved" : "Rejected",
        }),
      });
      if (!response.ok) throw new Error("Failed to update gate");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gates", "detail", id] });
    },
  });

  // Delete gate
  const deleteMutation = useMutation({
    mutationFn: async () => {
      const token = localStorage.getItem("access_token");
      if (!token) throw new Error("Not authenticated");

      const response = await fetch(`${API_BASE_URL}/gates/${id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to delete gate");
    },
    onSuccess: () => {
      router.push("/app/gates");
    },
  });

  // Check if user can approve
  const canApprove = user?.is_superuser || user?.roles?.some((r: string) =>
    ["CTO", "CPO", "CEO", "Admin", "Platform Admin"].includes(r)
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
        <div className="grid gap-4 md:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-lg border p-6">
              <div className="h-4 w-20 bg-gray-200 rounded animate-pulse mb-2" />
              <div className="h-8 w-24 bg-gray-200 rounded animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !gate) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="text-red-500 mb-4">Gate not found</div>
        <Link href="/app/gates">
          <Button variant="outline">Back to Gates</Button>
        </Link>
      </div>
    );
  }

  const stage = SDLC_STAGES.find((s) => s.code === gate.stage);

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/app/projects" className="hover:text-foreground">
          Projects
        </Link>
        <span>/</span>
        <Link
          href={`/app/projects/${gate.project_id}`}
          className="hover:text-foreground"
        >
          Project
        </Link>
        <span>/</span>
        <span className="text-foreground">{gate.gate_name}</span>
      </div>

      {/* Gate header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight">{gate.gate_name}</h1>
            <span
              className={`rounded-full px-3 py-1 text-sm font-medium border ${getStatusStyle(gate.status)}`}
            >
              {gate.status}
            </span>
          </div>
          <p className="text-muted-foreground mt-1">
            {gate.gate_type} - Stage {gate.stage} ({stage?.name})
          </p>
        </div>
        <div className="flex gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <svg
                  className="mr-2 h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
                  />
                </svg>
                Options
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <svg
                  className="mr-2 h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
                Edit Gate
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-red-600 focus:text-red-600"
                onClick={() => setDeleteDialogOpen(true)}
              >
                <svg
                  className="mr-2 h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
                Delete Gate
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {gate.status === "DRAFT" && (
            <Button
              onClick={() => submitMutation.mutate()}
              disabled={submitMutation.isPending}
            >
              {submitMutation.isPending ? "Submitting..." : "Submit for Approval"}
            </Button>
          )}

          {gate.status === "PENDING_APPROVAL" && canApprove && (
            <>
              <Button
                variant="outline"
                onClick={() => approveMutation.mutate(false)}
                disabled={approveMutation.isPending}
                className="text-red-600 hover:text-red-700"
              >
                {approveMutation.isPending ? "Processing..." : "Reject"}
              </Button>
              <Button
                onClick={() => approveMutation.mutate(true)}
                disabled={approveMutation.isPending}
                className="bg-green-600 hover:bg-green-700"
              >
                {approveMutation.isPending ? "Approving..." : "Approve"}
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Gate</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete &quot;{gate.gate_name}&quot;? This action
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteMutation.mutate()}
              className="bg-red-600 hover:bg-red-700"
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Gate info grid */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Stage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stage?.name || gate.stage}</div>
            <p className="text-xs text-muted-foreground">{stage?.description}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Gate Type</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{gate.gate_type}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Evidence</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{gate.evidence_count}</div>
            <p className="text-xs text-muted-foreground">files attached</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Created</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold">
              {new Date(gate.created_at).toLocaleDateString()}
            </div>
            <p className="text-xs text-muted-foreground">
              {new Date(gate.created_at).toLocaleTimeString()}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Description */}
      {gate.description && (
        <Card>
          <CardHeader>
            <CardTitle>Description</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">{gate.description}</p>
          </CardContent>
        </Card>
      )}

      {/* Exit Criteria */}
      <Card>
        <CardHeader>
          <CardTitle>Exit Criteria</CardTitle>
          <CardDescription>
            Requirements that must be met to pass this gate
          </CardDescription>
        </CardHeader>
        <CardContent>
          {gate.exit_criteria && gate.exit_criteria.length > 0 ? (
            <div className="space-y-3">
              {gate.exit_criteria.map((criterion, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`h-6 w-6 rounded-full flex items-center justify-center ${
                        criterion.status === "met"
                          ? "bg-green-100 text-green-600"
                          : criterion.status === "not_met"
                          ? "bg-red-100 text-red-600"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {criterion.status === "met" ? (
                        <svg
                          className="h-4 w-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      ) : criterion.status === "not_met" ? (
                        <svg
                          className="h-4 w-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      ) : (
                        <svg
                          className="h-4 w-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                      )}
                    </div>
                    <span className="font-medium">{criterion.criterion}</span>
                  </div>
                  <span
                    className={`rounded-full px-2 py-1 text-xs font-medium ${
                      criterion.status === "met"
                        ? "bg-green-100 text-green-700"
                        : criterion.status === "not_met"
                        ? "bg-red-100 text-red-700"
                        : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {criterion.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-4">
              No exit criteria defined
            </p>
          )}
        </CardContent>
      </Card>

      {/* Approval History */}
      <Card>
        <CardHeader>
          <CardTitle>Approval History</CardTitle>
          <CardDescription>Track approval workflow progress</CardDescription>
        </CardHeader>
        <CardContent>
          {gate.approvals && gate.approvals.length > 0 ? (
            <div className="space-y-4">
              {gate.approvals.map((approval) => (
                <div
                  key={approval.id}
                  className="flex items-start justify-between rounded-lg border p-4"
                >
                  <div className="flex items-start gap-4">
                    <div
                      className={`h-10 w-10 rounded-full flex items-center justify-center ${
                        approval.is_approved
                          ? "bg-green-100 text-green-600"
                          : "bg-red-100 text-red-600"
                      }`}
                    >
                      {approval.is_approved ? (
                        <svg
                          className="h-5 w-5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      ) : (
                        <svg
                          className="h-5 w-5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      )}
                    </div>
                    <div>
                      <p className="font-medium">
                        {approval.approved_by_name || "Unknown"}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {approval.approved_by_role || "Reviewer"}
                      </p>
                      {approval.comments && (
                        <p className="text-sm mt-1">&quot;{approval.comments}&quot;</p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-medium ${
                        approval.is_approved
                          ? "bg-green-100 text-green-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {approval.is_approved ? "Approved" : "Rejected"}
                    </span>
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(approval.approved_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-4">
              No approvals yet
            </p>
          )}
        </CardContent>
      </Card>

      {/* Policy Violations */}
      {gate.policy_violations && gate.policy_violations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-red-600">Policy Violations</CardTitle>
            <CardDescription>Issues that must be resolved</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {gate.policy_violations.map((violation, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-3"
                >
                  <svg
                    className="h-5 w-5 text-red-500 mt-0.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                  <div>
                    <p className="font-medium text-red-700">{violation.message}</p>
                    <p className="text-sm text-red-600">
                      Policy: {violation.policy_code || violation.policy_id}
                    </p>
                    <p className="text-xs text-red-500 mt-1">
                      {new Date(violation.evaluated_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-2">
        <Link href={`/app/projects/${gate.project_id}`}>
          <Button variant="outline">Back to Project</Button>
        </Link>
        <Button variant="outline">
          <svg
            className="mr-2 h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
            />
          </svg>
          Upload Evidence
        </Button>
      </div>
    </div>
  );
}
