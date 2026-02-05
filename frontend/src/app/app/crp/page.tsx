/**
 * CRP (Consultation Request Protocol) List Page
 * SDLC Orchestrator Dashboard
 *
 * @module frontend/src/app/app/crp/page
 * @description Sprint 151 - SASE Artifacts Enhancement - CRP Frontend
 * @sdlc SDLC 6.0.3 Universal Framework
 * @status Sprint 151 - SASE Artifacts Enhancement
 */

"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  useCrps,
  useCreateCrp,
  useMyPendingReviews,
  useAutoGenerateCrp,
  type CRPStatus,
  type CRPPriority,
  type ReviewerExpertise,
  type CRP,
  type CRPAutoGenerateRequest,
} from "@/hooks/useCrp";
import { useProjects } from "@/hooks/useProjects";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// Status badge styling
const getStatusBadge = (status: CRPStatus) => {
  const statusConfig: Record<CRPStatus, { variant: "outline" | "destructive"; label: string; className: string }> = {
    pending: { variant: "outline", label: "Pending", className: "border-yellow-500 text-yellow-600" },
    in_review: { variant: "outline", label: "In Review", className: "border-blue-500 text-blue-600" },
    approved: { variant: "outline", label: "Approved", className: "border-green-500 text-green-600" },
    rejected: { variant: "outline", label: "Rejected", className: "border-red-500 text-red-600" },
    cancelled: { variant: "outline", label: "Cancelled", className: "border-gray-500 text-gray-600" },
    expired: { variant: "outline", label: "Expired", className: "border-gray-400 text-gray-500" },
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

// Expertise area icons (simplified SVG icons)
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

function CodeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
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

function ChatIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 0 1-.825-.242m9.345-8.334a2.126 2.126 0 0 0-.476-.095 48.64 48.64 0 0 0-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0 0 11.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
    </svg>
  );
}

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
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

function ClockIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
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

function InboxIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 0 1 2.012 1.244l.256.512a2.25 2.25 0 0 0 2.013 1.244h3.218a2.25 2.25 0 0 0 2.013-1.244l.256-.512a2.25 2.25 0 0 1 2.013-1.244h3.859m-19.5.338V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 0 0-2.15-1.588H6.911a2.25 2.25 0 0 0-2.15 1.588L2.35 13.177a2.25 2.25 0 0 0-.1.661Z" />
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

export default function CRPListPage() {
  const router = useRouter();
  const { data: projectsData } = useProjects();
  const projects = projectsData || [];

  // Filter state
  const [selectedProjectId, setSelectedProjectId] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [priorityFilter, setPriorityFilter] = useState<string>("all");

  // Modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newCRP, setNewCRP] = useState({
    project_id: "",
    risk_analysis_id: "",
    title: "",
    description: "",
    priority: "medium" as CRPPriority,
    required_expertise: ["general"] as ReviewerExpertise[],
    diff_url: "",
  });

  // Auto-generate state - Sprint 151 Day 4
  const [showAutoGenerate, setShowAutoGenerate] = useState(false);
  const [autoGenInput, setAutoGenInput] = useState({
    context: "",
    code_snippet: "",
    related_files: "",
    project_tech_stack: "",
  });
  const [autoGenMessage, setAutoGenMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Fetch CRPs
  const { data: crpsData, isLoading, refetch } = useCrps(
    selectedProjectId !== "all" ? { project_id: selectedProjectId } : undefined
  );
  const crps = crpsData?.consultations || [];

  // Fetch pending reviews for current user (returns CRP[] directly)
  const { data: pendingReviewsData } = useMyPendingReviews();
  const pendingReviews = pendingReviewsData || [];

  // Mutations
  const createCrpMutation = useCreateCrp();
  const autoGenerateMutation = useAutoGenerateCrp();

  // Handle auto-generate from context - Sprint 151 Day 4
  const handleAutoGenerate = async () => {
    if (!autoGenInput.context.trim()) {
      setAutoGenMessage({ type: "error", text: "Please provide development context" });
      return;
    }

    setAutoGenMessage(null);

    try {
      const request: CRPAutoGenerateRequest = {
        context: autoGenInput.context,
        code_snippet: autoGenInput.code_snippet || undefined,
        related_files: autoGenInput.related_files
          ? autoGenInput.related_files.split("\n").filter(f => f.trim())
          : undefined,
        project_tech_stack: autoGenInput.project_tech_stack
          ? autoGenInput.project_tech_stack.split(",").map(t => t.trim()).filter(t => t)
          : undefined,
      };

      const result = await autoGenerateMutation.mutateAsync(request);

      // Fill the form with generated content
      setNewCRP(prev => ({
        ...prev,
        title: result.title,
        description: `## Question\n${result.question}\n\n## Context\n${result.context}\n\n## Impact Assessment\n${result.impact_assessment}`,
        priority: result.priority_suggestion as CRPPriority || prev.priority,
        required_expertise: result.required_expertise.length > 0
          ? [result.required_expertise[0] as ReviewerExpertise]
          : prev.required_expertise,
      }));

      setAutoGenMessage({
        type: "success",
        text: `Generated in ${Math.round(result.generation_time_ms)}ms (${result.provider_used}${result.fallback_used ? " - fallback" : ""}, ${Math.round(result.confidence * 100)}% confidence)`
      });
      setShowAutoGenerate(false);
    } catch {
      setAutoGenMessage({ type: "error", text: "Failed to auto-generate CRP content" });
    }
  };

  // Filter CRPs
  const filteredCrps = useMemo(() => {
    return crps.filter((crp: CRP) => {
      if (statusFilter !== "all" && crp.status !== statusFilter) return false;
      if (priorityFilter !== "all" && crp.priority !== priorityFilter) return false;
      return true;
    });
  }, [crps, statusFilter, priorityFilter]);

  // Stats
  const stats = useMemo(() => {
    return {
      total: crps.length,
      pending: crps.filter((c: CRP) => c.status === "pending").length,
      inReview: crps.filter((c: CRP) => c.status === "in_review").length,
      approved: crps.filter((c: CRP) => c.status === "approved").length,
      rejected: crps.filter((c: CRP) => c.status === "rejected").length,
    };
  }, [crps]);

  // Handle create CRP
  const handleCreateCRP = async () => {
    if (!newCRP.project_id || !newCRP.title || !newCRP.description || !newCRP.risk_analysis_id) return;

    try {
      await createCrpMutation.mutateAsync({
        project_id: newCRP.project_id,
        risk_analysis_id: newCRP.risk_analysis_id,
        title: newCRP.title,
        description: newCRP.description,
        priority: newCRP.priority,
        required_expertise: newCRP.required_expertise,
        diff_url: newCRP.diff_url || undefined,
      });
      setIsCreateModalOpen(false);
      setNewCRP({
        project_id: "",
        risk_analysis_id: "",
        title: "",
        description: "",
        priority: "medium",
        required_expertise: ["general"],
        diff_url: "",
      });
    } catch (error) {
      console.error("Failed to create CRP:", error);
    }
  };

  // Navigate to detail
  const handleViewCRP = (crpId: string) => {
    router.push(`/app/crp/${crpId}`);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Consultation Requests (CRP)</h1>
          <p className="text-muted-foreground">
            Request expert consultation for high-risk or complex changes
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshIcon className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
            <DialogTrigger asChild>
              <Button>
                <PlusIcon className="h-4 w-4 mr-2" />
                New CRP
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Consultation Request</DialogTitle>
                <DialogDescription>
                  Request expert consultation for a high-risk or complex change.
                  The CRP will be assigned to a reviewer with the appropriate expertise.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                {/* Auto-Generate Section - Sprint 151 Day 4 */}
                <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5 text-purple-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456Z" />
                      </svg>
                      <span className="text-sm font-medium text-purple-900">AI-Assisted Generation</span>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowAutoGenerate(!showAutoGenerate)}
                      className="text-purple-600 hover:text-purple-800"
                    >
                      {showAutoGenerate ? "Hide" : "Auto-generate from context"}
                    </Button>
                  </div>

                  {showAutoGenerate && (
                    <div className="space-y-3">
                      <div className="space-y-1">
                        <Label htmlFor="auto_context" className="text-xs text-purple-700">
                          Development Context / Question *
                        </Label>
                        <Textarea
                          id="auto_context"
                          value={autoGenInput.context}
                          onChange={(e) => setAutoGenInput(prev => ({ ...prev, context: e.target.value }))}
                          placeholder="Describe your question or the decision you need help with..."
                          rows={3}
                          className="text-sm"
                        />
                      </div>
                      <div className="space-y-1">
                        <Label htmlFor="auto_code" className="text-xs text-purple-700">
                          Relevant Code Snippet (optional)
                        </Label>
                        <Textarea
                          id="auto_code"
                          value={autoGenInput.code_snippet}
                          onChange={(e) => setAutoGenInput(prev => ({ ...prev, code_snippet: e.target.value }))}
                          placeholder="def authenticate_user():&#10;    ..."
                          rows={3}
                          className="text-sm font-mono text-xs"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label htmlFor="auto_files" className="text-xs text-purple-700">
                            Related Files (one per line)
                          </Label>
                          <Textarea
                            id="auto_files"
                            value={autoGenInput.related_files}
                            onChange={(e) => setAutoGenInput(prev => ({ ...prev, related_files: e.target.value }))}
                            placeholder="src/auth.py&#10;src/models/user.py"
                            rows={2}
                            className="text-sm"
                          />
                        </div>
                        <div className="space-y-1">
                          <Label htmlFor="auto_tech" className="text-xs text-purple-700">
                            Tech Stack (comma-separated)
                          </Label>
                          <Input
                            id="auto_tech"
                            value={autoGenInput.project_tech_stack}
                            onChange={(e) => setAutoGenInput(prev => ({ ...prev, project_tech_stack: e.target.value }))}
                            placeholder="Python, FastAPI, PostgreSQL"
                            className="text-sm"
                          />
                        </div>
                      </div>
                      <Button
                        type="button"
                        onClick={handleAutoGenerate}
                        disabled={autoGenerateMutation.isPending}
                        className="w-full bg-purple-600 hover:bg-purple-700"
                      >
                        {autoGenerateMutation.isPending ? (
                          <>
                            <RefreshIcon className="w-4 h-4 mr-2 animate-spin" />
                            Generating...
                          </>
                        ) : (
                          <>
                            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
                            </svg>
                            Generate CRP Content
                          </>
                        )}
                      </Button>
                    </div>
                  )}

                  {autoGenMessage && (
                    <div className={`mt-2 p-2 rounded text-sm ${
                      autoGenMessage.type === "success"
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}>
                      {autoGenMessage.text}
                    </div>
                  )}
                </div>

                {/* Project */}
                <div className="space-y-2">
                  <Label htmlFor="project">Project *</Label>
                  <Select
                    value={newCRP.project_id}
                    onValueChange={(value) => setNewCRP({ ...newCRP, project_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a project" />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.isArray(projects) && projects.map((project) => (
                        <SelectItem key={project.id} value={project.id}>
                          {project.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Risk Analysis ID */}
                <div className="space-y-2">
                  <Label htmlFor="risk_analysis_id">Risk Analysis ID *</Label>
                  <Input
                    id="risk_analysis_id"
                    value={newCRP.risk_analysis_id}
                    onChange={(e) => setNewCRP({ ...newCRP, risk_analysis_id: e.target.value })}
                    placeholder="UUID of the triggering risk analysis"
                  />
                  <p className="text-xs text-muted-foreground">
                    The risk analysis that triggered this consultation request
                  </p>
                </div>

                {/* Title */}
                <div className="space-y-2">
                  <Label htmlFor="title">Title *</Label>
                  <Input
                    id="title"
                    value={newCRP.title}
                    onChange={(e) => setNewCRP({ ...newCRP, title: e.target.value })}
                    placeholder="Brief description of the consultation request"
                  />
                </div>

                {/* Description */}
                <div className="space-y-2">
                  <Label htmlFor="description">Description *</Label>
                  <Textarea
                    id="description"
                    value={newCRP.description}
                    onChange={(e) => setNewCRP({ ...newCRP, description: e.target.value })}
                    placeholder="Detailed explanation of what you need consultation on"
                    rows={4}
                  />
                </div>

                {/* Diff URL */}
                <div className="space-y-2">
                  <Label htmlFor="diff_url">Diff URL (Optional)</Label>
                  <Input
                    id="diff_url"
                    value={newCRP.diff_url}
                    onChange={(e) => setNewCRP({ ...newCRP, diff_url: e.target.value })}
                    placeholder="https://github.com/org/repo/pull/123"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {/* Required Expertise */}
                  <div className="space-y-2">
                    <Label>Required Expertise</Label>
                    <Select
                      value={newCRP.required_expertise[0]}
                      onValueChange={(value) => setNewCRP({ ...newCRP, required_expertise: [value as ReviewerExpertise] })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="security">Security</SelectItem>
                        <SelectItem value="database">Database</SelectItem>
                        <SelectItem value="api">API Design</SelectItem>
                        <SelectItem value="architecture">Architecture</SelectItem>
                        <SelectItem value="concurrency">Concurrency</SelectItem>
                        <SelectItem value="general">General</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Priority */}
                  <div className="space-y-2">
                    <Label>Priority</Label>
                    <Select
                      value={newCRP.priority}
                      onValueChange={(value) => setNewCRP({ ...newCRP, priority: value as CRPPriority })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="urgent">Urgent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateCRP}
                  disabled={!newCRP.project_id || !newCRP.title || !newCRP.description || !newCRP.risk_analysis_id || createCrpMutation.isPending}
                >
                  {createCrpMutation.isPending ? "Creating..." : "Create CRP"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total CRPs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <ChatIcon className="h-5 w-5 text-blue-500" />
              <span className="text-2xl font-bold">{stats.total}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <ClockIcon className="h-5 w-5 text-yellow-500" />
              <span className="text-2xl font-bold">{stats.pending}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">In Review</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <UsersIcon className="h-5 w-5 text-blue-500" />
              <span className="text-2xl font-bold">{stats.inReview}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Approved</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CheckIcon className="h-5 w-5 text-green-500" />
              <span className="text-2xl font-bold">{stats.approved}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Rejected</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <XIcon className="h-5 w-5 text-red-500" />
              <span className="text-2xl font-bold">{stats.rejected}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs: All CRPs / My Pending Reviews */}
      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All CRPs</TabsTrigger>
          <TabsTrigger value="reviews" className="relative">
            My Pending Reviews
            {pendingReviews.length > 0 && (
              <Badge variant="destructive" className="ml-2 h-5 w-5 p-0 flex items-center justify-center text-xs">
                {pendingReviews.length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* All CRPs Tab */}
        <TabsContent value="all" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            <div className="w-64">
              <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by project" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Projects</SelectItem>
                  {Array.isArray(projects) && projects.map((project) => (
                    <SelectItem key={project.id} value={project.id}>
                      {project.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="w-48">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="in_review">In Review</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                  <SelectItem value="expired">Expired</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="w-48">
              <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Priorities</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* CRP List */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshIcon className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : filteredCrps.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <InboxIcon className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-lg font-medium text-muted-foreground">No consultation requests found</p>
                <p className="text-sm text-muted-foreground">
                  Create a new CRP to request expert consultation
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {filteredCrps.map((crp: CRP) => {
                const primaryExpertise = crp.required_expertise?.[0] || "general";
                const ExpertiseIcon = getExpertiseIcon(primaryExpertise);
                return (
                  <Card
                    key={crp.id}
                    className="cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => handleViewCRP(crp.id)}
                  >
                    <CardContent className="py-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold">{crp.title}</h3>
                            {getStatusBadge(crp.status)}
                            {getPriorityBadge(crp.priority)}
                          </div>
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {crp.description}
                          </p>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <ExpertiseIcon className="h-4 w-4" />
                              <span>{expertiseLabels[primaryExpertise]}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <ClockIcon className="h-4 w-4" />
                              <span>{new Date(crp.created_at).toLocaleDateString()}</span>
                            </div>
                            {crp.assigned_reviewer_id && (
                              <div className="flex items-center gap-1">
                                <UsersIcon className="h-4 w-4" />
                                <span>Reviewer assigned</span>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2 ml-4">
                          {crp.comment_count > 0 && (
                            <Badge variant="secondary" className="flex items-center gap-1">
                              <ChatIcon className="h-3 w-3" />
                              {crp.comment_count}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* My Pending Reviews Tab */}
        <TabsContent value="reviews" className="space-y-4">
          {pendingReviews.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <CheckIcon className="h-12 w-12 text-green-500 mb-4" />
                <p className="text-lg font-medium text-muted-foreground">No pending reviews</p>
                <p className="text-sm text-muted-foreground">
                  You have no consultation requests assigned to you for review
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {pendingReviews.map((crp: CRP) => {
                const primaryExpertise = crp.required_expertise?.[0] || "general";
                const ExpertiseIcon = getExpertiseIcon(primaryExpertise);
                return (
                  <Card
                    key={crp.id}
                    className="cursor-pointer hover:shadow-md transition-shadow border-blue-200"
                    onClick={() => handleViewCRP(crp.id)}
                  >
                    <CardContent className="py-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="border-blue-500 text-blue-600">
                              Needs Review
                            </Badge>
                            <h3 className="font-semibold">{crp.title}</h3>
                            {getPriorityBadge(crp.priority)}
                          </div>
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {crp.description}
                          </p>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <ExpertiseIcon className="h-4 w-4" />
                              <span>{expertiseLabels[primaryExpertise]}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <ClockIcon className="h-4 w-4" />
                              <span>Created: {new Date(crp.created_at).toLocaleDateString()}</span>
                            </div>
                          </div>
                        </div>
                        <Button variant="default" size="sm" className="ml-4">
                          Review Now
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
