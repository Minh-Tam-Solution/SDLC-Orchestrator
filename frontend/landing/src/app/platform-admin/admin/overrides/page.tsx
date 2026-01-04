/**
 * Override Queue Page - Next.js App Router
 * @module frontend/landing/src/app/platform-admin/admin/overrides/page
 * @status Sprint 69 - Final Migration (100%)
 * @description VCR (Version Controlled Resolution) override queue management
 * @note Uses httpOnly cookies for auth (Sprint 63 migration)
 */
"use client";

import { useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  GitPullRequest,
  Shield,
  Loader2,
  AlertCircle,
  TrendingUp,
  FileWarning,
} from "lucide-react";
import {
  useOverrideQueue,
  useOverrideStats,
  useApproveOverride,
  useRejectOverride,
} from "@/hooks/useAdmin";
import {
  OVERRIDE_TYPE_META,
  OVERRIDE_STATUS_META,
  type OverrideItem,
  type OverrideType,
  type OverrideStatus,
} from "@/lib/types/admin";

// =========================================================================
// Override Card Component
// =========================================================================

interface OverrideCardProps {
  item: OverrideItem;
  onApprove: (item: OverrideItem) => void;
  onReject: (item: OverrideItem) => void;
  showActions?: boolean;
}

function OverrideCard({ item, onApprove, onReject, showActions = true }: OverrideCardProps) {
  const typeMeta = OVERRIDE_TYPE_META[item.override_type];
  const statusMeta = OVERRIDE_STATUS_META[item.status];

  const getTypeIcon = (type: OverrideType) => {
    switch (type) {
      case "false_positive":
        return <Shield className="h-4 w-4" />;
      case "approved_risk":
        return <AlertTriangle className="h-4 w-4" />;
      case "emergency":
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const getStatusIcon = (status: OverrideStatus) => {
    switch (status) {
      case "pending":
        return <Clock className="h-4 w-4" />;
      case "approved":
        return <CheckCircle className="h-4 w-4" />;
      case "rejected":
        return <XCircle className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  return (
    <Card className={item.override_type === "emergency" ? "border-red-300 bg-red-50/30" : ""}>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="space-y-3 flex-1">
            {/* Header with type and status badges */}
            <div className="flex items-center gap-2 flex-wrap">
              <Badge className={typeMeta.color}>
                {getTypeIcon(item.override_type)}
                <span className="ml-1">{typeMeta.label}</span>
              </Badge>
              <Badge className={statusMeta.color}>
                {getStatusIcon(item.status)}
                <span className="ml-1">{statusMeta.label}</span>
              </Badge>
              {item.post_merge_review_required && (
                <Badge variant="outline" className="text-orange-600 border-orange-300">
                  Post-merge review required
                </Badge>
              )}
              {item.is_expired && (
                <Badge variant="destructive">Expired</Badge>
              )}
            </div>

            {/* Project and PR info */}
            <div className="space-y-1">
              <p className="font-medium text-lg">
                {item.project_name || `Project ${item.project_id.slice(0, 8)}`}
              </p>
              {item.pr_number && (
                <p className="text-sm text-muted-foreground flex items-center gap-1">
                  <GitPullRequest className="h-4 w-4" />
                  PR #{item.pr_number}: {item.pr_title || "No title"}
                </p>
              )}
            </div>

            {/* Reason */}
            <div className="bg-muted/50 rounded-lg p-3">
              <p className="text-sm font-medium text-muted-foreground mb-1">Reason:</p>
              <p className="text-sm">{item.reason}</p>
            </div>

            {/* Failed validators */}
            {item.failed_validators && item.failed_validators.length > 0 && (
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm text-muted-foreground">Failed validators:</span>
                {item.failed_validators.map((validator) => (
                  <Badge key={validator} variant="outline" className="text-xs">
                    {validator}
                  </Badge>
                ))}
              </div>
            )}

            {/* Metadata */}
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span>Requested by: {item.requested_by_name || "Unknown"}</span>
              <span>{new Date(item.requested_at).toLocaleString()}</span>
              {item.expires_at && (
                <span className={item.is_expired ? "text-red-500" : ""}>
                  Expires: {new Date(item.expires_at).toLocaleString()}
                </span>
              )}
            </div>

            {/* Resolution info (for recent decisions) */}
            {item.resolved_by_name && (
              <div className="text-xs text-muted-foreground border-t pt-2 mt-2">
                <span>
                  {item.status === "approved" ? "Approved" : "Rejected"} by{" "}
                  {item.resolved_by_name} on{" "}
                  {item.resolved_at && new Date(item.resolved_at).toLocaleString()}
                </span>
                {item.resolution_comment && (
                  <p className="mt-1 italic">&quot;{item.resolution_comment}&quot;</p>
                )}
              </div>
            )}
          </div>

          {/* Actions */}
          {showActions && item.status === "pending" && !item.is_expired && (
            <div className="flex flex-col gap-2 ml-4">
              <Button
                size="sm"
                onClick={() => onApprove(item)}
                className="bg-green-600 hover:bg-green-700"
              >
                <CheckCircle className="h-4 w-4 mr-1" />
                Approve
              </Button>
              <Button
                size="sm"
                variant="destructive"
                onClick={() => onReject(item)}
              >
                <XCircle className="h-4 w-4 mr-1" />
                Reject
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// =========================================================================
// Stats Cards Component
// =========================================================================

interface StatsCardsProps {
  stats: {
    total: number;
    pending: number;
    approval_rate: number;
    by_type: Record<string, number>;
  } | undefined;
  isLoading: boolean;
}

function StatsCards({ stats, isLoading }: StatsCardsProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="grid gap-4 md:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Pending</CardTitle>
          <Clock className="h-4 w-4 text-orange-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.pending}</div>
          <p className="text-xs text-muted-foreground">Awaiting review</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Total (30d)</CardTitle>
          <FileWarning className="h-4 w-4 text-blue-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.total}</div>
          <p className="text-xs text-muted-foreground">Override requests</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Approval Rate</CardTitle>
          <TrendingUp className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {(stats.approval_rate * 100).toFixed(1)}%
          </div>
          <p className="text-xs text-muted-foreground">Last 30 days</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">By Type</CardTitle>
          <Shield className="h-4 w-4 text-purple-500" />
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 flex-wrap">
            {Object.entries(stats.by_type || {}).map(([type, count]) => (
              <Badge key={type} variant="outline" className="text-xs">
                {type}: {count}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// =========================================================================
// Main Page Component
// =========================================================================

export default function OverrideQueuePage() {
  const [selectedItem, setSelectedItem] = useState<OverrideItem | null>(null);
  const [dialogMode, setDialogMode] = useState<"approve" | "reject" | null>(null);
  const [comment, setComment] = useState("");
  const [reason, setReason] = useState("");

  // Queries
  const { data: queueData, isLoading: isLoadingQueue, error: queueError } = useOverrideQueue();
  const { data: statsData, isLoading: isLoadingStats } = useOverrideStats(30);

  // Mutations
  const approveMutation = useApproveOverride();
  const rejectMutation = useRejectOverride();

  const handleApprove = (item: OverrideItem) => {
    setSelectedItem(item);
    setDialogMode("approve");
    setComment("");
  };

  const handleReject = (item: OverrideItem) => {
    setSelectedItem(item);
    setDialogMode("reject");
    setReason("");
  };

  const submitApproval = async () => {
    if (!selectedItem) return;

    try {
      await approveMutation.mutateAsync({
        overrideId: selectedItem.id,
        comment: comment || "Approved",
      });
      setDialogMode(null);
      setSelectedItem(null);
    } catch (err) {
      console.error("Approval failed:", err);
    }
  };

  const submitRejection = async () => {
    if (!selectedItem || reason.length < 10) return;

    try {
      await rejectMutation.mutateAsync({
        overrideId: selectedItem.id,
        reason,
      });
      setDialogMode(null);
      setSelectedItem(null);
    } catch (err) {
      console.error("Rejection failed:", err);
    }
  };

  if (queueError) {
    return (
      <div className="space-y-6">
        <nav className="flex items-center gap-2 text-sm text-muted-foreground">
          <Link href="/platform-admin" className="hover:text-foreground">
            Dashboard
          </Link>
          <span>/</span>
          <Link href="/platform-admin/admin" className="hover:text-foreground">
            Admin
          </Link>
          <span>/</span>
          <span className="text-foreground">Override Queue</span>
        </nav>

        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
            <h2 className="text-xl font-semibold mb-2">Failed to Load Override Queue</h2>
            <p className="text-muted-foreground">{queueError.message}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/platform-admin" className="hover:text-foreground">
          Dashboard
        </Link>
        <span>/</span>
        <Link href="/platform-admin/admin" className="hover:text-foreground">
          Admin
        </Link>
        <span>/</span>
        <span className="text-foreground">Override Queue</span>
      </nav>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Override Queue</h1>
        <p className="text-muted-foreground">
          VCR (Version Controlled Resolution) - Review and approve gate override requests
        </p>
      </div>

      {/* Stats Cards */}
      <StatsCards stats={statsData} isLoading={isLoadingStats} />

      {/* Queue Tabs */}
      <Tabs defaultValue="pending" className="space-y-4">
        <TabsList>
          <TabsTrigger value="pending">
            Pending ({queueData?.total_pending || 0})
          </TabsTrigger>
          <TabsTrigger value="recent">Recent Decisions</TabsTrigger>
        </TabsList>

        {/* Pending Tab */}
        <TabsContent value="pending">
          <Card>
            <CardHeader>
              <CardTitle>Pending Override Requests</CardTitle>
              <CardDescription>
                Review and approve/reject override requests from developers
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingQueue ? (
                <div className="space-y-4">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-40 w-full" />
                  ))}
                </div>
              ) : queueData?.pending && queueData.pending.length > 0 ? (
                <div className="space-y-4">
                  {queueData.pending.map((item) => (
                    <OverrideCard
                      key={item.id}
                      item={item}
                      onApprove={handleApprove}
                      onReject={handleReject}
                    />
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                  <CheckCircle className="h-12 w-12 mb-4 text-green-500" />
                  <p className="text-lg font-medium">No pending overrides</p>
                  <p className="text-sm">All override requests have been processed</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Recent Decisions Tab */}
        <TabsContent value="recent">
          <Card>
            <CardHeader>
              <CardTitle>Recent Decisions</CardTitle>
              <CardDescription>
                Previously approved or rejected override requests
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingQueue ? (
                <div className="space-y-4">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-40 w-full" />
                  ))}
                </div>
              ) : queueData?.recent_decisions && queueData.recent_decisions.length > 0 ? (
                <div className="space-y-4">
                  {queueData.recent_decisions.map((item) => (
                    <OverrideCard
                      key={item.id}
                      item={item}
                      onApprove={handleApprove}
                      onReject={handleReject}
                      showActions={false}
                    />
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                  <Clock className="h-12 w-12 mb-4" />
                  <p className="text-lg font-medium">No recent decisions</p>
                  <p className="text-sm">Override decisions will appear here</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Approval Dialog */}
      <Dialog open={dialogMode === "approve"} onOpenChange={(open) => !open && setDialogMode(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve Override Request</DialogTitle>
            <DialogDescription>
              This will allow the PR to bypass the failed gate validators.
              {selectedItem?.override_type === "emergency" && (
                <span className="block mt-2 text-orange-600 font-medium">
                  Note: Emergency overrides require post-merge review.
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Comment (optional)</label>
              <Textarea
                placeholder="Add a comment for the audit trail..."
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogMode(null)}>
              Cancel
            </Button>
            <Button
              onClick={submitApproval}
              disabled={approveMutation.isPending}
              className="bg-green-600 hover:bg-green-700"
            >
              {approveMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Approving...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Approve
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rejection Dialog */}
      <Dialog open={dialogMode === "reject"} onOpenChange={(open) => !open && setDialogMode(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Override Request</DialogTitle>
            <DialogDescription>
              Provide a reason for rejecting this override request.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Reason <span className="text-red-500">*</span>
              </label>
              <Textarea
                placeholder="Explain why this override is being rejected (minimum 10 characters)..."
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={3}
              />
              {reason.length > 0 && reason.length < 10 && (
                <p className="text-xs text-red-500">
                  Reason must be at least 10 characters ({reason.length}/10)
                </p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogMode(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={submitRejection}
              disabled={rejectMutation.isPending || reason.length < 10}
            >
              {rejectMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Rejecting...
                </>
              ) : (
                <>
                  <XCircle className="h-4 w-4 mr-2" />
                  Reject
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
