/**
 * SOP Detail Page - Next.js App Router
 * @module frontend/landing/src/app/app/sop/[id]/page
 * @status Sprint 67 - SOP Migration (Sprint 68 - Budget Optimized)
 * @description View and manage individual SOP
 * @optimization Dynamic imports for tab content to reduce bundle size
 */
"use client";

import { use, lazy, Suspense } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  MoreVertical,
  Download,
  Edit,
  Trash2,
  CheckCircle,
  Clock,
  FileText,
  User,
  Hash,
  Loader2,
  History,
  Link as LinkIcon,
} from "lucide-react";
import { useSOPDetail, useUpdateSOPStatus, useExportSOP, useDeleteSOP } from "@/hooks/useSOP";
import { SOP_TYPE_META, SOP_STATUS_META, type SOPStatus } from "@/lib/types/sop";

// Lazy load tab content components
const SOPContentTab = lazy(() => import("./tabs/ContentTab"));
const SOPRevisionsTab = lazy(() => import("./tabs/RevisionsTab"));
const SOPEvidenceTab = lazy(() => import("./tabs/EvidenceTab"));
const SOPMetadataTab = lazy(() => import("./tabs/MetadataTab"));

// Loading fallback for tabs
function TabLoading() {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-4">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </CardContent>
    </Card>
  );
}

interface SOPDetailPageProps {
  params: { id: string } | Promise<{ id: string }>;
}

export default function SOPDetailPage({ params }: SOPDetailPageProps) {
  // Handle both sync and async params (Next.js 14 compatibility)
  const resolvedParams = params instanceof Promise ? use(params) : params;
  const { id: sopId } = resolvedParams;
  const router = useRouter();

  // Queries and mutations
  const { data: sop, isLoading, error } = useSOPDetail(sopId);
  const updateStatusMutation = useUpdateSOPStatus(sopId);
  const exportMutation = useExportSOP();
  const deleteMutation = useDeleteSOP();

  const handleStatusChange = async (newStatus: SOPStatus) => {
    try {
      await updateStatusMutation.mutateAsync({ status: newStatus });
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  };

  const handleExport = async (format: "pdf" | "docx" | "md") => {
    try {
      const blob = await exportMutation.mutateAsync({ sopId, format });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${sop?.title || "sop"}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed:", err);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this SOP?")) return;

    try {
      await deleteMutation.mutateAsync(sopId);
      router.push("/app/sop-history");
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  const getStatusBadgeVariant = (status: SOPStatus) => {
    switch (status) {
      case "active":
        return "default";
      case "approved":
        return "secondary";
      case "pending_review":
        return "outline";
      case "draft":
        return "outline";
      case "deprecated":
        return "destructive";
      case "archived":
        return "secondary";
      default:
        return "outline";
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !sop) {
    return (
      <div className="space-y-6">
        <nav className="flex items-center gap-2 text-sm text-muted-foreground">
          <Link href="/app" className="hover:text-foreground">
            Dashboard
          </Link>
          <span>/</span>
          <Link href="/app/sop-history" className="hover:text-foreground">
            SOP History
          </Link>
          <span>/</span>
          <span className="text-foreground">Error</span>
        </nav>

        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">SOP Not Found</h2>
            <p className="text-muted-foreground mb-4">
              {error?.message || "The requested SOP could not be found."}
            </p>
            <Button onClick={() => router.push("/app/sop-history")}>
              Back to History
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/app" className="hover:text-foreground">
          Dashboard
        </Link>
        <span>/</span>
        <Link href="/app/sop-history" className="hover:text-foreground">
          SOP History
        </Link>
        <span>/</span>
        <span className="text-foreground truncate max-w-[200px]">{sop.title}</span>
      </nav>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight">{sop.title}</h1>
            <Badge variant={getStatusBadgeVariant(sop.status)}>
              {SOP_STATUS_META[sop.status]?.label}
            </Badge>
          </div>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <FileText className="h-4 w-4" />
              {SOP_TYPE_META[sop.sop_type]?.label}
            </span>
            <span className="flex items-center gap-1">
              <Hash className="h-4 w-4" />
              v{sop.version}
            </span>
            <span className="flex items-center gap-1">
              <User className="h-4 w-4" />
              {sop.author_name}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              {new Date(sop.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Status Actions */}
          {sop.status === "draft" && (
            <Button
              variant="outline"
              onClick={() => handleStatusChange("pending_review")}
              disabled={updateStatusMutation.isPending}
            >
              Submit for Review
            </Button>
          )}
          {sop.status === "pending_review" && (
            <Button
              onClick={() => handleStatusChange("approved")}
              disabled={updateStatusMutation.isPending}
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Approve
            </Button>
          )}
          {sop.status === "approved" && (
            <Button
              onClick={() => handleStatusChange("active")}
              disabled={updateStatusMutation.isPending}
            >
              Activate
            </Button>
          )}

          {/* More actions */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="icon">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => handleExport("pdf")}>
                <Download className="h-4 w-4 mr-2" />
                Export as PDF
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport("docx")}>
                <Download className="h-4 w-4 mr-2" />
                Export as DOCX
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport("md")}>
                <Download className="h-4 w-4 mr-2" />
                Export as Markdown
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <Edit className="h-4 w-4 mr-2" />
                Edit SOP
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleDelete}
                className="text-red-600"
                disabled={deleteMutation.isPending}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete SOP
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Main content */}
      <Tabs defaultValue="content" className="space-y-4">
        <TabsList>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="revisions">
            <History className="h-4 w-4 mr-2" />
            Revisions ({sop.revisions?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="evidence">
            <LinkIcon className="h-4 w-4 mr-2" />
            Evidence ({sop.evidence?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="metadata">Metadata</TabsTrigger>
        </TabsList>

        {/* Content Tab - Lazy loaded */}
        <TabsContent value="content">
          <Suspense fallback={<TabLoading />}>
            <SOPContentTab sop={sop} />
          </Suspense>
        </TabsContent>

        {/* Revisions Tab - Lazy loaded */}
        <TabsContent value="revisions">
          <Suspense fallback={<TabLoading />}>
            <SOPRevisionsTab revisions={sop.revisions} />
          </Suspense>
        </TabsContent>

        {/* Evidence Tab - Lazy loaded */}
        <TabsContent value="evidence">
          <Suspense fallback={<TabLoading />}>
            <SOPEvidenceTab evidence={sop.evidence} />
          </Suspense>
        </TabsContent>

        {/* Metadata Tab - Lazy loaded */}
        <TabsContent value="metadata">
          <Suspense fallback={<TabLoading />}>
            <SOPMetadataTab sop={sop} />
          </Suspense>
        </TabsContent>
      </Tabs>
    </div>
  );
}
