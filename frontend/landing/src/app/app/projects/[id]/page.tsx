/**
 * Project Detail Page - SDLC Orchestrator Dashboard
 *
 * @module frontend/landing/src/app/app/projects/[id]/page
 * @description Project detail with gates list and SDLC stage timeline
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 64 - Route Group Migration
 */

"use client";

import { use, Suspense } from "react";
import Link from "next/link";
import { useProject } from "@/hooks/useProjects";
import { useAuth } from "@/hooks/useAuth";

// =============================================================================
// Types
// =============================================================================

interface ProjectGate {
  id: string;
  gate_name: string;
  gate_type: string;
  stage: string;
  status: "DRAFT" | "PENDING_APPROVAL" | "APPROVED" | "REJECTED";
  description: string | null;
  created_at: string | null;
}

// =============================================================================
// Constants
// =============================================================================

/**
 * SDLC 5.1.1 Stage Definitions (10 Stages: 00-09 + Archive)
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

// =============================================================================
// Icons
// =============================================================================

function ArrowLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
    </svg>
  );
}

function ShieldCheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
    </svg>
  );
}

function ChevronRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
    </svg>
  );
}

// =============================================================================
// Helpers
// =============================================================================

function getStatusColor(status: string): string {
  switch (status) {
    case "APPROVED":
      return "bg-green-100 text-green-700";
    case "REJECTED":
      return "bg-red-100 text-red-700";
    case "PENDING_APPROVAL":
      return "bg-yellow-100 text-yellow-700";
    case "DRAFT":
      return "bg-gray-100 text-gray-700";
    default:
      return "bg-blue-100 text-blue-700";
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "N/A";
  return new Date(dateStr).toLocaleDateString();
}

// =============================================================================
// Loading Component
// =============================================================================

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
        <div className="h-4 w-4 bg-gray-200 rounded animate-pulse" />
        <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
      </div>
      <div className="h-10 w-64 bg-gray-200 rounded animate-pulse" />
      <div className="h-5 w-96 bg-gray-200 rounded animate-pulse" />
      <div className="grid gap-4 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-lg border p-6">
            <div className="h-4 w-24 bg-gray-200 rounded animate-pulse mb-2" />
            <div className="h-8 w-20 bg-gray-200 rounded animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}

// =============================================================================
// Project Content Component (fetches data after auth check)
// =============================================================================

function ProjectContent({ projectId }: { projectId: string }) {
  const { data: project, isLoading, error, isError } = useProject(projectId);

  // Group gates by stage
  const gatesByStage = (project?.gates || []).reduce<Record<string, ProjectGate[]>>((acc, gate) => {
    const stageGates = acc[gate.stage] ?? [];
    stageGates.push(gate as ProjectGate);
    acc[gate.stage] = stageGates;
    return acc;
  }, {});

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (isError || error || !project) {
    // Check if it's an auth error (401) - redirect to login
    const isAuthError = error && typeof error === "object" && "status" in error && (error as { status: number }).status === 401;
    if (isAuthError) {
      return (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="text-amber-600 mb-4">Session expired. Please log in again.</div>
          <Link
            href="/login"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Go to Login
          </Link>
        </div>
      );
    }

    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="text-red-500 mb-4">Project not found</div>
        <Link
          href="/app/projects"
          className="px-4 py-2 border rounded-lg hover:bg-gray-50"
        >
          Back to Projects
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/app/projects" className="hover:text-gray-900 flex items-center gap-1">
          <ArrowLeftIcon className="h-4 w-4" />
          Projects
        </Link>
        <span>/</span>
        <span className="text-gray-900">{project.name}</span>
      </div>

      {/* Project header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{project.name}</h1>
          <p className="text-gray-500 mt-1">
            {project.description || "No description"}
          </p>
        </div>
      </div>

      {/* Project info cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <h3 className="text-sm font-medium text-gray-500">Current Stage</h3>
          <div className="mt-2">
            <div className="text-2xl font-bold">
              {SDLC_STAGES.find((s) => s.code === project.current_stage)?.name || project.current_stage}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {SDLC_STAGES.find((s) => s.code === project.current_stage)?.description}
            </p>
          </div>
        </div>
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <h3 className="text-sm font-medium text-gray-500">Total Gates</h3>
          <div className="mt-2">
            <div className="text-2xl font-bold">{project.gates?.length || 0}</div>
            <p className="text-xs text-gray-500 mt-1">
              {(project.gates || []).filter((g) => g.status === "APPROVED").length} approved
            </p>
          </div>
        </div>
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <h3 className="text-sm font-medium text-gray-500">Created</h3>
          <div className="mt-2">
            <div className="text-2xl font-bold">
              {formatDate(project.created_at)}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Updated {formatDate(project.updated_at)}
            </p>
          </div>
        </div>
      </div>

      {/* SDLC Stage Timeline */}
      <div className="bg-white rounded-lg border shadow-sm">
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold">SDLC 5.1.1 Stage Timeline</h2>
          <p className="text-sm text-gray-500 mt-1">Track progress through all 10 stages</p>
        </div>
        <div className="p-6">
          <div className="flex items-center justify-between overflow-x-auto pb-2 gap-2">
            {SDLC_STAGES.map((stage) => {
              const stageGates = gatesByStage[stage.code] || [];
              const hasGates = stageGates.length > 0;
              const allApproved = stageGates.length > 0 && stageGates.every((g) => g.status === "APPROVED");
              const hasPending = stageGates.some((g) => g.status === "DRAFT" || g.status === "PENDING_APPROVAL");
              const hasRejected = stageGates.some((g) => g.status === "REJECTED");

              let stageColor = "bg-gray-200 text-gray-500";
              if (allApproved) stageColor = "bg-green-500 text-white";
              else if (hasRejected) stageColor = "bg-red-500 text-white";
              else if (hasPending) stageColor = "bg-yellow-500 text-white";
              else if (hasGates) stageColor = "bg-blue-500 text-white";

              return (
                <div key={stage.code} className="flex flex-col items-center min-w-[80px]">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${stageColor}`}
                  >
                    {stage.code}
                  </div>
                  <div className="mt-2 text-xs font-medium text-center">{stage.name}</div>
                  <div className="text-xs text-gray-500">
                    {stageGates.length > 0 ? `${stageGates.length} gate${stageGates.length > 1 ? "s" : ""}` : "-"}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Gates list */}
      <div className="bg-white rounded-lg border shadow-sm">
        <div className="p-6 border-b">
          <div className="flex items-center gap-2">
            <ShieldCheckIcon className="h-5 w-5 text-gray-500" />
            <h2 className="text-lg font-semibold">Quality Gates</h2>
          </div>
          <p className="text-sm text-gray-500 mt-1">All gates for this project</p>
        </div>
        <div className="p-6">
          {project.gates && project.gates.length > 0 ? (
            <div className="space-y-3">
              {project.gates.map((gate) => (
                <Link
                  key={gate.id}
                  href={`/app/gates/${gate.id}`}
                  className="block"
                >
                  <div className="flex items-center justify-between rounded-lg border p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center gap-4">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-700 font-bold">
                        {gate.stage}
                      </div>
                      <div>
                        <p className="font-medium">{gate.gate_name}</p>
                        <p className="text-sm text-gray-500">
                          {gate.gate_type} • {SDLC_STAGES.find((s) => s.code === gate.stage)?.name}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(gate.status)}`}>
                        {gate.status.replace("_", " ")}
                      </span>
                      <ChevronRightIcon className="h-5 w-5 text-gray-400" />
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <ShieldCheckIcon className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-sm text-gray-500">No gates created yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Page Component with Auth Check
// =============================================================================

interface PageProps {
  params: { id: string } | Promise<{ id: string }>;
}

export default function ProjectDetailPage({ params }: PageProps) {
  // Handle both sync and async params (Next.js 14 compatibility)
  const resolvedParams = params instanceof Promise ? use(params) : params;
  const projectId = resolvedParams.id;

  const { isAuthenticated, isLoading: authLoading } = useAuth();

  // Show auth loading state
  if (authLoading) {
    return <LoadingSpinner />;
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="text-amber-600 mb-4">Please log in to view this project.</div>
        <Link
          href="/login"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Go to Login
        </Link>
      </div>
    );
  }

  // Render project content (data fetching happens here)
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <ProjectContent projectId={projectId} />
    </Suspense>
  );
}
