/**
 * Policy Detail Page - Next.js App Router
 * @module frontend/landing/src/app/app/policies/[id]/page
 * @status Sprint 65 - Route Group Migration
 * @description Policy detail with Rego code viewer and metadata
 */
"use client";

import { use } from "react";
import Link from "next/link";
import { usePolicy } from "@/hooks/usePolicies";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

/**
 * Severity badge colors
 */
const severityColors: Record<string, string> = {
  INFO: "bg-blue-100 text-blue-800 border-blue-200",
  WARNING: "bg-yellow-100 text-yellow-800 border-yellow-200",
  ERROR: "bg-orange-100 text-orange-800 border-orange-200",
  CRITICAL: "bg-red-100 text-red-800 border-red-200",
};

/**
 * Severity icons
 */
function SeverityIcon({ severity }: { severity: string }) {
  switch (severity) {
    case "INFO":
      return (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    case "WARNING":
      return (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      );
    case "ERROR":
      return (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    case "CRITICAL":
      return (
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    default:
      return null;
  }
}

interface PageProps {
  params: { id: string } | Promise<{ id: string }>;
}

export default function PolicyDetailPage({ params }: PageProps) {
  // Handle both sync and async params (Next.js 14 compatibility)
  const resolvedParams = params instanceof Promise ? use(params) : params;
  const { id } = resolvedParams;
  const { data: policy, isLoading, error } = usePolicy(id);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 animate-pulse bg-gray-200 rounded" />
        <div className="h-4 w-48 animate-pulse bg-gray-200 rounded" />
        <div className="grid gap-4 md:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 animate-pulse bg-gray-200 rounded-lg" />
          ))}
        </div>
        <div className="h-64 animate-pulse bg-gray-200 rounded-lg" />
      </div>
    );
  }

  if (error || !policy) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <svg
          className="h-16 w-16 text-red-500 mb-4"
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
        <h2 className="text-xl font-semibold mb-2">Policy Not Found</h2>
        <p className="text-muted-foreground mb-4">
          {error instanceof Error ? error.message : "The policy you are looking for does not exist."}
        </p>
        <Link href="/app/policies">
          <Button>Back to Policies</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/app/policies" className="hover:text-foreground">
          Policies
        </Link>
        <span>/</span>
        <span className="text-foreground">{policy.policy_name}</span>
      </nav>

      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight">{policy.policy_name}</h1>
            <span
              className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm font-medium border ${
                severityColors[policy.severity] || "bg-gray-100 text-gray-800"
              }`}
            >
              <SeverityIcon severity={policy.severity} />
              {policy.severity}
            </span>
            {policy.is_active ? (
              <Badge className="bg-green-100 text-green-800 hover:bg-green-100">
                Active
              </Badge>
            ) : (
              <Badge variant="outline">Inactive</Badge>
            )}
          </div>
          <p className="text-muted-foreground mt-1">{policy.description}</p>
        </div>
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
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
            />
          </svg>
          Edit Policy
        </Button>
      </div>

      {/* Policy info grid */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Policy Code</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-mono">{policy.policy_code}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Stage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{policy.stage}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Version</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{policy.version}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Last Updated</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-medium">
              {new Date(policy.updated_at).toLocaleDateString()}
            </div>
            <div className="text-sm text-muted-foreground">
              {new Date(policy.updated_at).toLocaleTimeString()}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Rego Code Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Rego Policy Code</CardTitle>
              <CardDescription>
                Open Policy Agent (OPA) Rego language validation rules
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                navigator.clipboard.writeText(policy.rego_code || "");
              }}
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
                  d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"
                />
              </svg>
              Copy Code
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg bg-slate-900 p-4 overflow-x-auto">
            <pre className="text-sm font-mono text-slate-100 whitespace-pre-wrap">
              {policy.rego_code || "# No Rego code defined for this policy"}
            </pre>
          </div>
        </CardContent>
      </Card>

      {/* Policy Metadata Section */}
      <Card>
        <CardHeader>
          <CardTitle>Policy Information</CardTitle>
          <CardDescription>Detailed metadata and configuration</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-3">
              <div>
                <p className="text-sm text-muted-foreground">Policy ID</p>
                <p className="font-mono text-sm">{policy.id}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Created At</p>
                <p>{new Date(policy.created_at).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <p>
                  {policy.is_active
                    ? "Active - Enforced on gates"
                    : "Inactive - Not enforced"}
                </p>
              </div>
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-muted-foreground">Severity Level</p>
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium border ${
                      severityColors[policy.severity] || "bg-gray-100"
                    }`}
                  >
                    <SeverityIcon severity={policy.severity} />
                    {policy.severity}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {policy.severity === "INFO" && "- Informational only"}
                    {policy.severity === "WARNING" && "- Warning, may proceed"}
                    {policy.severity === "ERROR" && "- Error, should fix"}
                    {policy.severity === "CRITICAL" && "- Critical, must fix"}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">SDLC Stage</p>
                <Badge variant="outline">{policy.stage}</Badge>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Version</p>
                <p>{policy.version}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Usage Information */}
      <Card>
        <CardHeader>
          <CardTitle>Policy Usage</CardTitle>
          <CardDescription>How this policy is applied in the system</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <svg
              className="h-12 w-12 text-muted-foreground mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
              />
            </svg>
            <h3 className="text-lg font-medium">Policy Evaluation History</h3>
            <p className="text-muted-foreground mt-1 max-w-md">
              View evaluation history by navigating to gates that use this policy.
              Each gate evaluation includes the policy check results.
            </p>
            <Link href="/app/gates">
              <Button variant="outline" className="mt-4">
                View Gates
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
