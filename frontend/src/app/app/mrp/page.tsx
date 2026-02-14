/**
 * =========================================================================
 * MRP Dashboard Page
 * SDLC Orchestrator - Sprint 152 (MRP Integration)
 *
 * Version: 1.0.0
 * Date: February 3, 2026
 * Status: ACTIVE - Sprint 152 Implementation
 * Authority: Frontend Lead + Backend Lead Approved
 * Framework: SDLC 6.0.5
 *
 * Dashboard for MRP (Merge Readiness Protocol) with Context Authority integration.
 * Features:
 * - MRP 5-Point Validation
 * - VCR (Verification Completion Report)
 * - Policy Tier Management
 * - Context Authority SSOT Integration
 *
 * Zero Mock Policy: Production-ready React components
 * =========================================================================
 */

"use client";

import { useState } from "react";
import {
  useMRPHealth,
  usePolicyTiers,
  useTierCompliance,
  useVCRHistory,
  useValidateMRP,
  useEnforcePolicies,
  getMRPPointStatusColor,
  getVCRVerdictColor,
  getPolicyTierColor,
  getMRPPointLabel,
  getMRPSummary,
  getVibecodingZoneColor,
  hasContextValidation,
  getContextValidationStatus,
  type MRPValidation,
  type VCR,
  type PolicyTier,
  type ValidateMRPRequest,
} from "@/hooks/useMRP";
import { useProjectSnapshots } from "@/hooks/useContextAuthority";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";

// =========================================================================
// MRP Point Card Component
// =========================================================================

interface MRPPointCardProps {
  title: string;
  point: {
    status: string;
    message: string;
    required: boolean;
    details: Record<string, unknown>;
  };
  icon: React.ReactNode;
}

function MRPPointCard({ title, point, icon }: MRPPointCardProps) {
  const statusColor = getMRPPointStatusColor(point.status as any);

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {icon}
            <CardTitle className="text-sm font-medium">{title}</CardTitle>
          </div>
          <Badge className={statusColor} variant="outline">
            {point.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{point.message || "No message"}</p>
        {!point.required && (
          <Badge variant="secondary" className="mt-2">
            Optional
          </Badge>
        )}
      </CardContent>
    </Card>
  );
}

// =========================================================================
// MRP Validation Form Component
// =========================================================================

interface ValidationFormProps {
  onSubmit: (data: ValidateMRPRequest) => void;
  isLoading: boolean;
}

function ValidationForm({ onSubmit, isLoading }: ValidationFormProps) {
  const [projectId, setProjectId] = useState("");
  const [prId, setPrId] = useState("");
  const [commitSha, setCommitSha] = useState("");
  const [includeContext, setIncludeContext] = useState(true);
  const [forceRefresh, setForceRefresh] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId || !prId) return;

    onSubmit({
      project_id: projectId,
      pr_id: prId,
      commit_sha: commitSha || undefined,
      force_refresh: forceRefresh,
      include_context_validation: includeContext,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="project-id">Project ID</Label>
          <Input
            id="project-id"
            placeholder="Enter project UUID"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="pr-id">Pull Request ID</Label>
          <Input
            id="pr-id"
            placeholder="e.g., 123"
            value={prId}
            onChange={(e) => setPrId(e.target.value)}
            required
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="commit-sha">Commit SHA (Optional)</Label>
        <Input
          id="commit-sha"
          placeholder="e.g., abc123def456"
          value={commitSha}
          onChange={(e) => setCommitSha(e.target.value)}
        />
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="include-context"
            checked={includeContext}
            onCheckedChange={(checked) => setIncludeContext(checked as boolean)}
          />
          <Label htmlFor="include-context" className="text-sm">
            Include Context Authority Validation
          </Label>
        </div>

        <div className="flex items-center space-x-2">
          <Checkbox
            id="force-refresh"
            checked={forceRefresh}
            onCheckedChange={(checked) => setForceRefresh(checked as boolean)}
          />
          <Label htmlFor="force-refresh" className="text-sm">
            Force Refresh
          </Label>
        </div>
      </div>

      <Button type="submit" disabled={isLoading || !projectId || !prId}>
        {isLoading ? "Validating..." : "Validate MRP"}
      </Button>
    </form>
  );
}

// =========================================================================
// MRP Validation Result Component
// =========================================================================

interface ValidationResultProps {
  validation: MRPValidation;
  vcr: VCR | null;
  contextMessage: string | null;
}

function ValidationResult({ validation, vcr, contextMessage }: ValidationResultProps) {
  const progressValue = (validation.points_passed / 5) * 100;

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>MRP Validation Result</CardTitle>
              <CardDescription>PR #{validation.pr_id}</CardDescription>
            </div>
            <Badge
              className={validation.overall_passed ? "bg-green-100 text-green-600" : "bg-red-100 text-red-600"}
              variant="outline"
            >
              {validation.overall_passed ? "PASSED" : "FAILED"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between text-sm mb-1">
                <span>Points Passed</span>
                <span>{validation.points_passed}/{validation.points_required}</span>
              </div>
              <Progress value={progressValue} />
            </div>
            <Badge className={getPolicyTierColor(validation.tier)} variant="outline">
              {validation.tier}
            </Badge>
          </div>

          {/* Context Authority Status */}
          {hasContextValidation(validation) && (
            <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
              <div className="flex items-center gap-2">
                <LayersIcon className="h-4 w-4" />
                <span className="text-sm font-medium">Context Authority</span>
              </div>
              <div className="flex items-center gap-2">
                {validation.vibecoding_zone && (
                  <Badge className={getVibecodingZoneColor(validation.vibecoding_zone)} variant="outline">
                    {validation.vibecoding_zone} ({validation.vibecoding_index})
                  </Badge>
                )}
                <Badge
                  variant="outline"
                  className={
                    validation.context_validation_passed
                      ? "bg-green-100 text-green-600"
                      : "bg-red-100 text-red-600"
                  }
                >
                  {getContextValidationStatus(validation)}
                </Badge>
              </div>
            </div>
          )}

          {contextMessage && (
            <Alert>
              <AlertTitle>Context Authority</AlertTitle>
              <AlertDescription>{contextMessage}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* 5-Point Evidence Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <MRPPointCard
          title="Test Evidence"
          point={validation.test}
          icon={<BeakerIcon className="h-4 w-4" />}
        />
        <MRPPointCard
          title="Lint Evidence"
          point={validation.lint}
          icon={<CodeIcon className="h-4 w-4" />}
        />
        <MRPPointCard
          title="Security Evidence"
          point={validation.security}
          icon={<ShieldIcon className="h-4 w-4" />}
        />
        <MRPPointCard
          title="Build Evidence"
          point={validation.build}
          icon={<CubeIcon className="h-4 w-4" />}
        />
        <MRPPointCard
          title="Conformance Evidence"
          point={validation.conformance}
          icon={<ClipboardIcon className="h-4 w-4" />}
        />
      </div>

      {/* VCR Card */}
      {vcr && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>VCR (Verification Completion Report)</CardTitle>
                <CardDescription>ID: {vcr.id.slice(0, 8)}...</CardDescription>
              </div>
              <Badge className={getVCRVerdictColor(vcr.verdict)} variant="outline">
                {vcr.verdict}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="text-sm text-muted-foreground">{vcr.verdict_reason || "No reason provided"}</p>
            {vcr.evidence_hash && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>Evidence Hash:</span>
                <code className="font-mono">{vcr.evidence_hash.slice(0, 16)}...</code>
              </div>
            )}
            {vcr.context_snapshot_id && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>Context Snapshot:</span>
                <code className="font-mono">{vcr.context_snapshot_id.slice(0, 8)}...</code>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// =========================================================================
// Policy Tiers Tab Component
// =========================================================================

function PolicyTiersTab() {
  const { data: tiersData, isLoading } = usePolicyTiers();

  if (isLoading) {
    return <div className="text-center py-8">Loading policy tiers...</div>;
  }

  if (!tiersData?.tiers) {
    return <div className="text-center py-8 text-muted-foreground">No tiers available</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {tiersData.tiers.map((tier) => (
        <Card key={tier.tier}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">{tier.display_name}</CardTitle>
              <Badge className={getPolicyTierColor(tier.tier)} variant="outline">
                {tier.tier}
              </Badge>
            </div>
            <CardDescription>{tier.description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Target Audience</span>
              <span>{tier.target_audience}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Enforcement</span>
              <Badge variant="secondary">{tier.enforcement_mode}</Badge>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Test Coverage</span>
              <span>{tier.test_coverage_required}%</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">MRP Points Required</span>
              <span>{tier.mrp_points_required}/5</span>
            </div>
            <Separator />
            <div className="space-y-1">
              <span className="text-sm font-medium">Required Checks:</span>
              <div className="flex flex-wrap gap-1">
                {tier.required_checks.map((check) => (
                  <Badge key={check} variant="outline" className="text-xs">
                    {check}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// =========================================================================
// VCR History Tab Component
// =========================================================================

interface VCRHistoryTabProps {
  projectId: string;
}

function VCRHistoryTab({ projectId }: VCRHistoryTabProps) {
  const { data: historyData, isLoading } = useVCRHistory(projectId, undefined, 20, !!projectId);

  if (!projectId) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        Enter a Project ID to view VCR history
      </div>
    );
  }

  if (isLoading) {
    return <div className="text-center py-8">Loading VCR history...</div>;
  }

  if (!historyData?.vcrs || historyData.vcrs.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No VCR history found for this project
      </div>
    );
  }

  return (
    <ScrollArea className="h-[600px]">
      <div className="space-y-4 pr-4">
        {historyData.vcrs.map((vcr) => (
          <Card key={vcr.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm">PR #{vcr.pr_id}</CardTitle>
                  <CardDescription className="text-xs">
                    {new Date(vcr.created_at).toLocaleString()}
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className={getPolicyTierColor(vcr.tier)} variant="outline">
                    {vcr.tier}
                  </Badge>
                  <Badge className={getVCRVerdictColor(vcr.verdict)} variant="outline">
                    {vcr.verdict}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {getMRPSummary(vcr.mrp_validation)}
              </p>
              {vcr.context_snapshot_id && (
                <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
                  <LayersIcon className="h-3 w-3" />
                  <span>Context: {vcr.context_snapshot_id.slice(0, 8)}...</span>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
}

// =========================================================================
// Icon Components
// =========================================================================

function BeakerIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23-.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611l-.628.105a9 9 0 0 1-14.014 0l-.628-.105c-1.717-.293-2.3-2.379-1.067-3.61L5 14.5" />
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

function ShieldIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
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

function ClipboardIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M11.35 3.836c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m8.9-4.414c.376.023.75.05 1.124.08 1.131.094 1.976 1.057 1.976 2.192V16.5A2.25 2.25 0 0 1 18 18.75h-2.25m-7.5-10.5H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V18.75m-7.5-10.5h6.375c.621 0 1.125.504 1.125 1.125v9.375m-8.25-3 1.5 1.5 3-3.75" />
    </svg>
  );
}

function LayersIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6.429 9.75 2.25 12l4.179 2.25m0-4.5 5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0 4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0-5.571 3-5.571-3" />
    </svg>
  );
}

// =========================================================================
// Main Page Component
// =========================================================================

export default function MRPPage() {
  const [activeTab, setActiveTab] = useState("validate");
  const [historyProjectId, setHistoryProjectId] = useState("");
  const [validationResult, setValidationResult] = useState<{
    validation: MRPValidation;
    vcr: VCR | null;
    contextMessage: string | null;
  } | null>(null);

  const { data: healthData, isLoading: healthLoading } = useMRPHealth();
  const validateMutation = useValidateMRP();

  const handleValidate = async (data: ValidateMRPRequest) => {
    try {
      const result = await validateMutation.mutateAsync(data);
      setValidationResult({
        validation: result.mrp_validation,
        vcr: result.vcr,
        contextMessage: result.context_validation_message,
      });
    } catch (error) {
      console.error("Validation failed:", error);
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">MRP Dashboard</h1>
          <p className="text-muted-foreground">
            Merge Readiness Protocol - 5-Point Validation + Context Authority
          </p>
        </div>
        <div className="flex items-center gap-2">
          {healthLoading ? (
            <Badge variant="outline">Checking...</Badge>
          ) : healthData?.status === "healthy" ? (
            <Badge variant="outline" className="bg-green-100 text-green-600">
              Service Healthy
            </Badge>
          ) : (
            <Badge variant="destructive">Service Issue</Badge>
          )}
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="validate">Validate PR</TabsTrigger>
          <TabsTrigger value="tiers">Policy Tiers</TabsTrigger>
          <TabsTrigger value="history">VCR History</TabsTrigger>
        </TabsList>

        {/* Validate Tab */}
        <TabsContent value="validate" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>MRP Validation</CardTitle>
              <CardDescription>
                Validate a Pull Request against the 5-point MRP structure with optional Context Authority integration
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ValidationForm
                onSubmit={handleValidate}
                isLoading={validateMutation.isPending}
              />
            </CardContent>
          </Card>

          {validateMutation.isError && (
            <Alert variant="destructive">
              <AlertTitle>Validation Failed</AlertTitle>
              <AlertDescription>
                {validateMutation.error?.message || "An error occurred during validation"}
              </AlertDescription>
            </Alert>
          )}

          {validationResult && (
            <ValidationResult
              validation={validationResult.validation}
              vcr={validationResult.vcr}
              contextMessage={validationResult.contextMessage}
            />
          )}
        </TabsContent>

        {/* Policy Tiers Tab */}
        <TabsContent value="tiers">
          <PolicyTiersTab />
        </TabsContent>

        {/* VCR History Tab */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>VCR History</CardTitle>
              <CardDescription>
                View historical VCR records for a project
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                <div className="flex-1">
                  <Label htmlFor="history-project-id">Project ID</Label>
                  <Input
                    id="history-project-id"
                    placeholder="Enter project UUID"
                    value={historyProjectId}
                    onChange={(e) => setHistoryProjectId(e.target.value)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <VCRHistoryTab projectId={historyProjectId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
