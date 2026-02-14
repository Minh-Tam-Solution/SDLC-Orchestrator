/**
 * CRP (Consultation Request Protocol) Detail Page
 * SDLC Orchestrator Dashboard
 *
 * @module frontend/src/app/app/crp/[id]/page
 * @description Sprint 151 - SASE Artifacts Enhancement - CRP Detail View
 * @sdlc SDLC 6.0.5 Universal Framework
 * @status Sprint 151 - SASE Artifacts Enhancement
 */

"use client";

import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  useCrp,
  useAssignCrpReviewer,
  useResolveCrp,
  useAddCrpComment,
  type CRPStatus,
  type CRPPriority,
  type ReviewerExpertise,
  type CRPComment,
} from "@/hooks/useCrp";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

// Simple icon components (inline SVG)
function ArrowLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
    </svg>
  );
}

function RefreshIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
    </svg>
  );
}

function ChatIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 0 1-.825-.242m9.345-8.334a2.126 2.126 0 0 0-.476-.095 48.64 48.64 0 0 0-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0 0 11.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
    </svg>
  );
}

function UsersIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  );
}

function XIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m9.75 9.75 4.5 4.5m0-4.5-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  );
}

function CloseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
    </svg>
  );
}

function CodeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
    </svg>
  );
}

function UserPlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M18 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0ZM3 19.235v-.11a6.375 6.375 0 0 1 12.75 0v.109A12.318 12.318 0 0 1 9.374 21c-2.331 0-4.512-.645-6.374-1.766Z" />
    </svg>
  );
}

function SendIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" />
    </svg>
  );
}

function DocumentIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
    </svg>
  );
}

function ShieldIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
    </svg>
  );
}

function DatabaseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
    </svg>
  );
}

function CubeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 7.5-9-5.25L3 7.5m18 0-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
    </svg>
  );
}

function BoltIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
    </svg>
  );
}

function QuestionIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z" />
    </svg>
  );
}

// Status badge styling
const getStatusBadge = (status: CRPStatus) => {
  const statusConfig: Record<CRPStatus, { variant: "outline" | "destructive"; label: string; className: string }> = {
    pending: { variant: "outline", label: "Pending", className: "border-yellow-500 text-yellow-600 bg-yellow-50" },
    in_review: { variant: "outline", label: "In Review", className: "border-blue-500 text-blue-600 bg-blue-50" },
    approved: { variant: "outline", label: "Approved", className: "border-green-500 text-green-600 bg-green-50" },
    rejected: { variant: "outline", label: "Rejected", className: "border-red-500 text-red-600 bg-red-50" },
    cancelled: { variant: "outline", label: "Cancelled", className: "border-gray-500 text-gray-600 bg-gray-50" },
    expired: { variant: "outline", label: "Expired", className: "border-gray-400 text-gray-500 bg-gray-50" },
  };
  const config = statusConfig[status] || statusConfig.pending;
  return <Badge variant={config.variant} className={config.className}>{config.label}</Badge>;
};

// Priority badge styling
const getPriorityBadge = (priority: CRPPriority) => {
  const priorityConfig: Record<CRPPriority, { variant: "outline" | "destructive"; label: string; className: string }> = {
    low: { variant: "outline", label: "Low", className: "border-gray-400 text-gray-500" },
    medium: { variant: "outline", label: "Medium", className: "border-blue-400 text-blue-500" },
    high: { variant: "outline", label: "High", className: "border-orange-500 text-orange-600" },
    urgent: { variant: "destructive", label: "Urgent", className: "" },
  };
  const config = priorityConfig[priority] || priorityConfig.medium;
  return <Badge variant={config.variant} className={config.className}>{config.label}</Badge>;
};

// Expertise area icons and labels
const getExpertiseIcon = (expertise: ReviewerExpertise) => {
  const icons: Record<ReviewerExpertise, React.ComponentType<{ className?: string }>> = {
    security: ShieldIcon,
    database: DatabaseIcon,
    api: CodeIcon,
    architecture: CubeIcon,
    concurrency: BoltIcon,
    general: QuestionIcon,
  };
  return icons[expertise] || icons.general;
};

const expertiseLabels: Record<ReviewerExpertise, string> = {
  security: "Security",
  database: "Database",
  api: "API Design",
  architecture: "Architecture",
  concurrency: "Concurrency",
  general: "General",
};

export default function CRPDetailPage() {
  const router = useRouter();
  const params = useParams();
  const crpId = params.id as string;
  const { user } = useAuth();

  // Fetch CRP
  const { data: crp, isLoading, error, refetch } = useCrp(crpId);

  // Modal states
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [isResolveModalOpen, setIsResolveModalOpen] = useState(false);
  const [resolveAction, setResolveAction] = useState<"approved" | "rejected" | "cancelled">("approved");
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [reviewerId, setReviewerId] = useState("");
  const [newComment, setNewComment] = useState("");

  // Mutations
  const assignReviewerMutation = useAssignCrpReviewer();
  const resolveCrpMutation = useResolveCrp();
  const addCommentMutation = useAddCrpComment();

  // Check if user can assign reviewer (admin/owner/cto)
  const canAssignReviewer = user && user.roles?.some((r: string) => ["admin", "owner", "cto", "tech_lead"].includes(r));

  // Check if user is the assigned reviewer
  const isReviewer = user && crp?.assigned_reviewer_id === user.id;

  // Check if user can resolve (reviewer or admin)
  const canResolve = isReviewer || canAssignReviewer;

  // Handle assign reviewer
  const handleAssignReviewer = async () => {
    if (!reviewerId) return;

    try {
      await assignReviewerMutation.mutateAsync({
        crpId,
        data: { reviewer_id: reviewerId },
      });
      setIsAssignModalOpen(false);
      setReviewerId("");
    } catch (error) {
      console.error("Failed to assign reviewer:", error);
    }
  };

  // Handle resolve CRP
  const handleResolveCRP = async () => {
    try {
      await resolveCrpMutation.mutateAsync({
        crpId,
        data: {
          status: resolveAction,
          resolution_notes: resolutionNotes,
        },
      });
      setIsResolveModalOpen(false);
      setResolutionNotes("");
    } catch (error) {
      console.error("Failed to resolve CRP:", error);
    }
  };

  // Handle add comment
  const handleAddComment = async () => {
    if (!newComment.trim()) return;

    try {
      await addCommentMutation.mutateAsync({
        crpId,
        data: { comment: newComment },
      });
      setNewComment("");
    } catch (error) {
      console.error("Failed to add comment:", error);
    }
  };

  // Open resolve modal
  const openResolveModal = (action: "approved" | "rejected" | "cancelled") => {
    setResolveAction(action);
    setIsResolveModalOpen(true);
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-12 flex items-center justify-center">
        <RefreshIcon className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !crp) {
    return (
      <div className="container mx-auto py-12">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <XIcon className="h-12 w-12 text-red-500 mb-4" />
            <p className="text-lg font-medium">CRP not found</p>
            <p className="text-sm text-muted-foreground mb-4">
              The consultation request you&apos;re looking for doesn&apos;t exist or you don&apos;t have access.
            </p>
            <Button onClick={() => router.push("/app/crp")}>
              <ArrowLeftIcon className="h-4 w-4 mr-2" />
              Back to CRP List
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const primaryExpertise = crp.required_expertise?.[0] || "general";
  const ExpertiseIcon = getExpertiseIcon(primaryExpertise);
  const isResolved = ["approved", "rejected", "cancelled", "expired"].includes(crp.status);

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/app/crp")}>
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div className="h-6 w-px bg-border" />
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{crp.title}</h1>
            {getStatusBadge(crp.status)}
            {getPriorityBadge(crp.priority)}
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            CRP-{crp.id.slice(0, 8).toUpperCase()} · Created {new Date(crp.created_at).toLocaleDateString()}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshIcon className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Description</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap">{crp.description}</p>
            </CardContent>
          </Card>

          {/* Diff URL */}
          {crp.diff_url && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <CodeIcon className="h-5 w-5" />
                  Related Pull Request
                </CardTitle>
              </CardHeader>
              <CardContent>
                <a
                  href={crp.diff_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  {crp.diff_url}
                </a>
              </CardContent>
            </Card>
          )}

          {/* Risk Analysis */}
          {crp.risk_analysis && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <ShieldIcon className="h-5 w-5 text-orange-500" />
                  Risk Analysis
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">Risk Score</p>
                  <p className="text-2xl font-bold">{crp.risk_analysis.risk_score}</p>
                </div>
                {crp.risk_analysis.risk_factors && crp.risk_analysis.risk_factors.length > 0 && (
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Risk Factors</p>
                    <ul className="list-disc list-inside space-y-1">
                      {crp.risk_analysis.risk_factors.map((factor: string, index: number) => (
                        <li key={index} className="text-sm">{factor}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {crp.risk_analysis.recommendation && (
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Recommendation</p>
                    <p className="text-sm">{crp.risk_analysis.recommendation}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Resolution Notes (if resolved) */}
          {isResolved && crp.resolution_notes && (
            <Card className={
              crp.status === "approved" ? "border-green-200 bg-green-50" :
              crp.status === "rejected" ? "border-red-200 bg-red-50" :
              "border-gray-200 bg-gray-50"
            }>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  {crp.status === "approved" ? (
                    <CheckIcon className="h-5 w-5 text-green-600" />
                  ) : crp.status === "rejected" ? (
                    <XIcon className="h-5 w-5 text-red-600" />
                  ) : (
                    <CloseIcon className="h-5 w-5 text-gray-600" />
                  )}
                  Resolution Notes
                </CardTitle>
                <CardDescription>
                  {crp.status === "approved" ? "This consultation was approved" :
                   crp.status === "rejected" ? "This consultation was rejected" :
                   "This consultation was cancelled/expired"}
                  {crp.resolved_at && ` on ${new Date(crp.resolved_at).toLocaleDateString()}`}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="whitespace-pre-wrap">{crp.resolution_notes}</p>
                {crp.conditions && crp.conditions.length > 0 && (
                  <div className="mt-4">
                    <p className="text-sm font-medium mb-2">Conditions:</p>
                    <ul className="list-disc list-inside space-y-1">
                      {crp.conditions.map((condition: string, index: number) => (
                        <li key={index} className="text-sm">{condition}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Discussion / Comments */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <ChatIcon className="h-5 w-5" />
                Discussion
                {crp.comment_count > 0 && (
                  <Badge variant="secondary">{crp.comment_count}</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Comments list */}
              {crp.comments && crp.comments.length > 0 ? (
                <div className="space-y-4">
                  {crp.comments.map((comment: CRPComment) => (
                    <div key={comment.id} className="flex gap-3">
                      <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                        <span className="text-xs font-medium">
                          {(comment.user_name || "U").charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">
                            {comment.user_name || "Unknown User"}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(comment.created_at).toLocaleString()}
                          </span>
                          {comment.is_resolution_note && (
                            <Badge variant="outline" className="text-xs">Resolution Note</Badge>
                          )}
                        </div>
                        <p className="text-sm mt-1 whitespace-pre-wrap">{comment.comment}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No comments yet. Start the discussion below.
                </p>
              )}

              {/* Add comment form */}
              {!isResolved && (
                <>
                  <div className="h-px bg-border my-4" />
                  <div className="flex gap-2">
                    <Textarea
                      placeholder="Add a comment or question..."
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      rows={2}
                      className="flex-1"
                    />
                    <Button
                      onClick={handleAddComment}
                      disabled={!newComment.trim() || addCommentMutation.isPending}
                      size="sm"
                    >
                      <SendIcon className="h-4 w-4" />
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Details Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Required Expertise */}
              <div>
                <p className="text-sm text-muted-foreground mb-1">Required Expertise</p>
                <div className="flex items-center gap-2">
                  <ExpertiseIcon className="h-5 w-5 text-blue-500" />
                  <span className="font-medium">{expertiseLabels[primaryExpertise]}</span>
                </div>
              </div>

              <div className="h-px bg-border" />

              {/* Requester */}
              <div>
                <p className="text-sm text-muted-foreground mb-1">Requester</p>
                <div className="flex items-center gap-2">
                  <div className="h-6 w-6 rounded-full bg-muted flex items-center justify-center">
                    <span className="text-xs">
                      {(crp.requester_name || "R").charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <span className="font-medium">{crp.requester_name || "Unknown"}</span>
                </div>
              </div>

              <div className="h-px bg-border" />

              {/* Reviewer */}
              <div>
                <p className="text-sm text-muted-foreground mb-1">Assigned Reviewer</p>
                {crp.assigned_reviewer_id ? (
                  <div className="flex items-center gap-2">
                    <div className="h-6 w-6 rounded-full bg-muted flex items-center justify-center">
                      <span className="text-xs">
                        {(crp.reviewer_name || "R").charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <span className="font-medium">{crp.reviewer_name || "Unknown"}</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <UsersIcon className="h-5 w-5" />
                    <span>Not assigned</span>
                  </div>
                )}
              </div>

              {/* Timestamps */}
              <div className="h-px bg-border" />
              <div className="text-sm space-y-2">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Created</span>
                  <span>{new Date(crp.created_at).toLocaleDateString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Updated</span>
                  <span>{new Date(crp.updated_at).toLocaleDateString()}</span>
                </div>
                {crp.resolved_at && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Resolved</span>
                    <span>{new Date(crp.resolved_at).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Actions Card */}
          {!isResolved && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Assign Reviewer (for admins when not assigned) */}
                {canAssignReviewer && !crp.assigned_reviewer_id && (
                  <Button
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => setIsAssignModalOpen(true)}
                  >
                    <UserPlusIcon className="h-4 w-4 mr-2" />
                    Assign Reviewer
                  </Button>
                )}

                {/* Resolution actions (for reviewer or admin) */}
                {canResolve && crp.status === "in_review" && (
                  <>
                    <Button
                      variant="default"
                      className="w-full justify-start bg-green-600 hover:bg-green-700"
                      onClick={() => openResolveModal("approved")}
                    >
                      <CheckIcon className="h-4 w-4 mr-2" />
                      Approve Consultation
                    </Button>
                    <Button
                      variant="destructive"
                      className="w-full justify-start"
                      onClick={() => openResolveModal("rejected")}
                    >
                      <XIcon className="h-4 w-4 mr-2" />
                      Reject Consultation
                    </Button>
                  </>
                )}

                {/* Cancel (for requester or admin) */}
                {(user?.id === crp.requester_id || canAssignReviewer) && crp.status !== "cancelled" && (
                  <Button
                    variant="outline"
                    className="w-full justify-start text-red-600 hover:text-red-700"
                    onClick={() => openResolveModal("cancelled")}
                  >
                    <CloseIcon className="h-4 w-4 mr-2" />
                    Cancel Request
                  </Button>
                )}
              </CardContent>
            </Card>
          )}

          {/* Info Card for resolved */}
          {isResolved && (
            <Card className="border-green-200 bg-green-50">
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-green-700">
                  <DocumentIcon className="h-5 w-5" />
                  <span className="font-medium">
                    This consultation has been {crp.status}
                  </span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Assign Reviewer Modal */}
      <Dialog open={isAssignModalOpen} onOpenChange={setIsAssignModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assign Reviewer</DialogTitle>
            <DialogDescription>
              Assign a reviewer with {expertiseLabels[primaryExpertise]} expertise to this consultation request.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="reviewer-id">Reviewer User ID</Label>
              <Input
                id="reviewer-id"
                value={reviewerId}
                onChange={(e) => setReviewerId(e.target.value)}
                placeholder="UUID of the reviewer"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAssignModalOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleAssignReviewer}
              disabled={!reviewerId || assignReviewerMutation.isPending}
            >
              {assignReviewerMutation.isPending ? "Assigning..." : "Assign Reviewer"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Resolve Modal */}
      <Dialog open={isResolveModalOpen} onOpenChange={setIsResolveModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {resolveAction === "approved" ? "Approve Consultation" :
               resolveAction === "rejected" ? "Reject Consultation" :
               "Cancel Request"}
            </DialogTitle>
            <DialogDescription>
              {resolveAction === "approved"
                ? "Confirm that this consultation request meets the requirements and can proceed."
                : resolveAction === "rejected"
                ? "Explain why this consultation request cannot be approved."
                : "Cancel this consultation request. This action cannot be undone."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="resolution-notes">
                {resolveAction === "approved" ? "Approval Notes" :
                 resolveAction === "rejected" ? "Rejection Reason *" :
                 "Cancellation Reason"}
              </Label>
              <Textarea
                id="resolution-notes"
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                placeholder={
                  resolveAction === "approved"
                    ? "Any notes or recommendations for proceeding..."
                    : resolveAction === "rejected"
                    ? "Please explain why this request is being rejected..."
                    : "Reason for cancellation..."
                }
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsResolveModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant={resolveAction === "approved" ? "default" : "destructive"}
              onClick={handleResolveCRP}
              disabled={!resolutionNotes || resolveCrpMutation.isPending}
            >
              {resolveCrpMutation.isPending
                ? "Processing..."
                : resolveAction === "approved"
                ? "Approve"
                : resolveAction === "rejected"
                ? "Reject"
                : "Cancel Request"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
