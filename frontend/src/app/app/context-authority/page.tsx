"use client";

/**
 * =========================================================================
 * Context Authority Dashboard - SSOT Visualization & Management
 * SDLC Orchestrator - Sprint 152 (Context Authority UI)
 *
 * Version: 1.0.0
 * Date: February 3, 2026
 * Status: ACTIVE - Sprint 152 Implementation
 * Authority: Frontend Lead + CTO Approved
 * Framework: SDLC 6.0.5
 *
 * Features:
 * - Health status monitoring
 * - Statistics dashboard with zone distribution
 * - Template management (CRUD)
 * - Snapshot viewer for audit trail
 * - Dynamic overlay preview
 *
 * Zero Mock Policy: Production-ready UI with real API calls
 * =========================================================================
 */

import React, { useState } from "react";
import {
  Activity,
  FileText,
  History,
  Layers,
  Plus,
  RefreshCw,
  Settings,
  TrendingUp,
  Eye,
  Edit,
  Trash2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  BarChart3,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";

import {
  useContextAuthorityHealth,
  useContextAuthorityStats,
  useTemplates,
  useCreateTemplate,
  useUpdateTemplate,
  getZoneColor,
  getZoneBadgeVariant,
  getTierColor,
  getTriggerTypeLabel,
  getHealthStatusColor,
  type TemplateResponse,
  type TemplateCreateRequest,
  type TriggerTypeEnum,
  type TierEnum,
} from "@/hooks/useContextAuthority";

// =========================================================================
// Health Status Card Component
// =========================================================================

function HealthStatusCard() {
  const { data: health, isLoading, refetch } = useContextAuthorityHealth();

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Service Health</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-4 w-32 mt-2" />
        </CardContent>
      </Card>
    );
  }

  const statusIcon =
    health?.status === "healthy" ? (
      <CheckCircle2 className="h-5 w-5 text-green-500" />
    ) : health?.status === "degraded" ? (
      <AlertTriangle className="h-5 w-5 text-yellow-500" />
    ) : (
      <XCircle className="h-5 w-5 text-red-500" />
    );

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Service Health</CardTitle>
        <Button variant="ghost" size="icon" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2">
          {statusIcon}
          <span
            className={`text-2xl font-bold capitalize ${getHealthStatusColor(
              health?.status || "unhealthy"
            )}`}
          >
            {health?.status || "Unknown"}
          </span>
        </div>
        <div className="mt-2 text-xs text-muted-foreground">
          <div>Version: {health?.version || "N/A"}</div>
          <div>Templates: {health?.template_count || 0}</div>
          <div>Snapshots (24h): {health?.snapshot_count_24h || 0}</div>
          <div>Avg Validation: {health?.avg_validation_ms?.toFixed(1) || 0}ms</div>
        </div>
      </CardContent>
    </Card>
  );
}

// =========================================================================
// Stats Overview Cards
// =========================================================================

function StatsOverview() {
  const [days, setDays] = useState(30);
  const { data: stats, isLoading } = useContextAuthorityStats(days);

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
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

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Statistics Overview</h3>
        <Select
          value={days.toString()}
          onValueChange={(v) => setDays(parseInt(v))}
        >
          <SelectTrigger className="w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
            <SelectItem value="90">Last 90 days</SelectItem>
            <SelectItem value="365">Last year</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Validations
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.total_validations?.toLocaleString() || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              In the last {days} days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pass Rate</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.validation_pass_rate
                ? (stats.validation_pass_rate * 100).toFixed(1)
                : 0}
              %
            </div>
            <p className="text-xs text-muted-foreground">Validation success</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Snapshots</CardTitle>
            <History className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.total_snapshots?.toLocaleString() || 0}
            </div>
            <p className="text-xs text-muted-foreground">Audit trail records</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Avg Templates/Validation
            </CardTitle>
            <Layers className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.avg_templates_per_validation?.toFixed(1) || 0}
            </div>
            <p className="text-xs text-muted-foreground">Templates applied</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// =========================================================================
// Zone Distribution Chart
// =========================================================================

function ZoneDistribution() {
  const { data: stats, isLoading } = useContextAuthorityStats(30);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Zone Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  const zones = stats?.zone_distribution || {};
  const total = Object.values(zones).reduce((a, b) => a + b, 0);

  const zoneColors = {
    GREEN: "bg-green-500",
    YELLOW: "bg-yellow-500",
    ORANGE: "bg-orange-500",
    RED: "bg-red-500",
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Vibecoding Zone Distribution
        </CardTitle>
        <CardDescription>Last 30 days validation breakdown</CardDescription>
      </CardHeader>
      <CardContent>
        {total === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            No validation data available
          </div>
        ) : (
          <div className="space-y-4">
            {(["GREEN", "YELLOW", "ORANGE", "RED"] as const).map((zone) => {
              const count = zones[zone] || 0;
              const percentage = total > 0 ? (count / total) * 100 : 0;
              return (
                <div key={zone} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{zone}</span>
                    <span className="text-muted-foreground">
                      {count} ({percentage.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-secondary overflow-hidden">
                    <div
                      className={`h-full ${zoneColors[zone]} transition-all duration-500`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// =========================================================================
// Template Management
// =========================================================================

function CreateTemplateDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const createTemplate = useCreateTemplate();
  const [formData, setFormData] = useState<TemplateCreateRequest>({
    name: "",
    trigger_type: "gate_pass",
    trigger_value: "",
    overlay_content: "",
    priority: 0,
    is_active: true,
    description: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createTemplate.mutateAsync(formData);
      onOpenChange(false);
      setFormData({
        name: "",
        trigger_type: "gate_pass",
        trigger_value: "",
        overlay_content: "",
        priority: 0,
        is_active: true,
        description: "",
      });
    } catch (error) {
      console.error("Failed to create template:", error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Overlay Template</DialogTitle>
          <DialogDescription>
            Create a new dynamic overlay template for context generation.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Template Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="e.g., Gate G2 Pass - Build Active"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="trigger_type">Trigger Type</Label>
                <Select
                  value={formData.trigger_type}
                  onValueChange={(v) =>
                    setFormData({
                      ...formData,
                      trigger_type: v as TriggerTypeEnum,
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gate_pass">Gate Pass</SelectItem>
                    <SelectItem value="gate_fail">Gate Fail</SelectItem>
                    <SelectItem value="index_zone">Index Zone</SelectItem>
                    <SelectItem value="stage_constraint">
                      Stage Constraint
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="trigger_value">Trigger Value</Label>
                <Input
                  id="trigger_value"
                  value={formData.trigger_value}
                  onChange={(e) =>
                    setFormData({ ...formData, trigger_value: e.target.value })
                  }
                  placeholder="e.g., G2, YELLOW, stage_02"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="tier">Tier Scope (Optional)</Label>
                <Select
                  value={formData.tier || "all"}
                  onValueChange={(v) =>
                    setFormData({
                      ...formData,
                      tier: v === "all" ? undefined : (v as TierEnum),
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Tiers</SelectItem>
                    <SelectItem value="LITE">LITE</SelectItem>
                    <SelectItem value="STANDARD">STANDARD</SelectItem>
                    <SelectItem value="PROFESSIONAL">PROFESSIONAL</SelectItem>
                    <SelectItem value="ENTERPRISE">ENTERPRISE</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="priority">Priority (0-1000)</Label>
                <Input
                  id="priority"
                  type="number"
                  min={0}
                  max={1000}
                  value={formData.priority}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      priority: parseInt(e.target.value) || 0,
                    })
                  }
                />
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="overlay_content">Overlay Content</Label>
              <Textarea
                id="overlay_content"
                value={formData.overlay_content}
                onChange={(e) =>
                  setFormData({ ...formData, overlay_content: e.target.value })
                }
                placeholder={`## Build Phase Active (Date: {date})

Current Stage: {stage}
Last Passed Gate: {gate}
Tier: {tier}

### Allowed Actions:
- Code implementation
- Unit tests
- Documentation updates

### Constraints:
- No breaking API changes without ADR
- Security review required for auth changes`}
                rows={10}
                className="font-mono text-sm"
                required
              />
              <p className="text-xs text-muted-foreground">
                Available variables: {"{date}"}, {"{stage}"}, {"{tier}"},{" "}
                {"{gate}"}, {"{index}"}, {"{top_signals}"}
              </p>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description">Description (Optional)</Label>
              <Input
                id="description"
                value={formData.description || ""}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="Brief description of when this template is used"
              />
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, is_active: checked })
                }
              />
              <Label htmlFor="is_active">Active</Label>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createTemplate.isPending}>
              {createTemplate.isPending ? "Creating..." : "Create Template"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function TemplateList() {
  const [page, setPage] = useState(1);
  const [triggerTypeFilter, setTriggerTypeFilter] = useState<string>("all");
  const [activeOnlyFilter, setActiveOnlyFilter] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const { data: templates, isLoading } = useTemplates({
    page,
    page_size: 10,
    trigger_type:
      triggerTypeFilter === "all"
        ? undefined
        : (triggerTypeFilter as TriggerTypeEnum),
    active_only: activeOnlyFilter,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Select value={triggerTypeFilter} onValueChange={setTriggerTypeFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="gate_pass">Gate Pass</SelectItem>
              <SelectItem value="gate_fail">Gate Fail</SelectItem>
              <SelectItem value="index_zone">Index Zone</SelectItem>
              <SelectItem value="stage_constraint">Stage Constraint</SelectItem>
            </SelectContent>
          </Select>

          <div className="flex items-center space-x-2">
            <Switch
              id="active-only"
              checked={activeOnlyFilter}
              onCheckedChange={setActiveOnlyFilter}
            />
            <Label htmlFor="active-only" className="text-sm">
              Active only
            </Label>
          </div>
        </div>

        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Template
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : templates?.templates.length === 0 ? (
        <Card>
          <CardContent className="py-8">
            <div className="text-center text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No templates found</p>
              <p className="text-sm">
                Create your first overlay template to get started.
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Trigger</TableHead>
                  <TableHead>Tier</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-24">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {templates?.templates.map((template) => (
                  <TableRow key={template.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{template.name}</div>
                        {template.description && (
                          <div className="text-xs text-muted-foreground truncate max-w-xs">
                            {template.description}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {getTriggerTypeLabel(
                          template.trigger_type as TriggerTypeEnum
                        )}
                      </Badge>
                      <span className="ml-2 text-sm text-muted-foreground">
                        = {template.trigger_value}
                      </span>
                    </TableCell>
                    <TableCell>
                      {template.tier ? (
                        <Badge className={getTierColor(template.tier as TierEnum)}>
                          {template.tier}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">All</span>
                      )}
                    </TableCell>
                    <TableCell>{template.priority}</TableCell>
                    <TableCell>
                      <Badge
                        variant={template.is_active ? "default" : "secondary"}
                      >
                        {template.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Button variant="ghost" size="icon">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon">
                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {templates && templates.pages > 1 && (
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                Page {templates.page} of {templates.pages} ({templates.total}{" "}
                total)
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= templates.pages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      <CreateTemplateDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
      />
    </div>
  );
}

// =========================================================================
// Top Triggered Templates
// =========================================================================

function TopTriggeredTemplates() {
  const { data: stats, isLoading } = useContextAuthorityStats(30);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Top Triggered Templates</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  const topTemplates = stats?.top_triggered_templates || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Top Triggered Templates
        </CardTitle>
        <CardDescription>Most frequently used templates</CardDescription>
      </CardHeader>
      <CardContent>
        {topTemplates.length === 0 ? (
          <div className="text-center text-muted-foreground py-4">
            No template usage data
          </div>
        ) : (
          <div className="space-y-3">
            {topTemplates.slice(0, 5).map((t: any, idx: number) => (
              <div
                key={t.template_id || idx}
                className="flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground w-6">#{idx + 1}</span>
                  <span className="font-medium truncate max-w-[200px]">
                    {t.template_name || t.name || "Unknown"}
                  </span>
                </div>
                <Badge variant="secondary">{t.count || 0} uses</Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// =========================================================================
// Main Page Component
// =========================================================================

export default function ContextAuthorityPage() {
  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Context Authority
          </h1>
          <p className="text-muted-foreground">
            Gate-aware dynamic context management (SSOT Dashboard)
          </p>
        </div>
        <Button variant="outline">
          <Settings className="h-4 w-4 mr-2" />
          Settings
        </Button>
      </div>

      {/* Health and Stats Row */}
      <div className="grid gap-4 md:grid-cols-4">
        <HealthStatusCard />
        <div className="md:col-span-3">
          <StatsOverview />
        </div>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="dashboard" className="space-y-4">
        <TabsList>
          <TabsTrigger value="dashboard">
            <BarChart3 className="h-4 w-4 mr-2" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="templates">
            <FileText className="h-4 w-4 mr-2" />
            Templates
          </TabsTrigger>
          <TabsTrigger value="snapshots">
            <History className="h-4 w-4 mr-2" />
            Snapshots
          </TabsTrigger>
          <TabsTrigger value="overlay">
            <Layers className="h-4 w-4 mr-2" />
            Overlay Preview
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <ZoneDistribution />
            <TopTriggeredTemplates />
          </div>

          {/* Tier Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Project Tier Distribution</CardTitle>
              <CardDescription>
                Validations by project tier classification
              </CardDescription>
            </CardHeader>
            <CardContent>
              <TierDistributionChart />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="templates">
          <Card>
            <CardHeader>
              <CardTitle>Overlay Templates</CardTitle>
              <CardDescription>
                Manage dynamic overlay templates for context generation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <TemplateList />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="snapshots">
          <Card>
            <CardHeader>
              <CardTitle>Context Snapshots</CardTitle>
              <CardDescription>
                Audit trail of context validations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SnapshotViewer />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="overlay">
          <Card>
            <CardHeader>
              <CardTitle>Overlay Preview</CardTitle>
              <CardDescription>
                Generate and preview dynamic overlays
              </CardDescription>
            </CardHeader>
            <CardContent>
              <OverlayPreview />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// =========================================================================
// Additional Components (Placeholders for next implementation)
// =========================================================================

function TierDistributionChart() {
  const { data: stats, isLoading } = useContextAuthorityStats(30);

  if (isLoading) {
    return <Skeleton className="h-32 w-full" />;
  }

  const tiers = stats?.tier_distribution || {};
  const total = Object.values(tiers).reduce((a, b) => a + b, 0);

  const tierColors = {
    LITE: "bg-blue-500",
    STANDARD: "bg-indigo-500",
    PROFESSIONAL: "bg-purple-500",
    ENTERPRISE: "bg-amber-500",
  };

  if (total === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No tier distribution data available
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {(["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"] as const).map(
        (tier) => {
          const count = tiers[tier] || 0;
          const percentage = total > 0 ? (count / total) * 100 : 0;
          return (
            <div key={tier} className="text-center p-4 border rounded-lg">
              <div
                className={`inline-block w-3 h-3 rounded-full ${tierColors[tier]} mb-2`}
              />
              <div className="font-semibold">{tier}</div>
              <div className="text-2xl font-bold">{count}</div>
              <div className="text-sm text-muted-foreground">
                {percentage.toFixed(1)}%
              </div>
            </div>
          );
        }
      )}
    </div>
  );
}

function SnapshotViewer() {
  const [projectId, setProjectId] = useState("");

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Input
          placeholder="Enter Project ID to view snapshots..."
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          className="max-w-md"
        />
        <Button variant="outline" disabled={!projectId}>
          <Clock className="h-4 w-4 mr-2" />
          Load Snapshots
        </Button>
      </div>

      <div className="text-center text-muted-foreground py-8">
        <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>Enter a project ID to view context validation snapshots</p>
        <p className="text-sm">
          Snapshots provide an immutable audit trail of all context validations
        </p>
      </div>
    </div>
  );
}

function OverlayPreview() {
  const [projectId, setProjectId] = useState("");
  const [stage, setStage] = useState("04-build");
  const [gate, setGate] = useState("G2");
  const [tier, setTier] = useState<TierEnum>("PROFESSIONAL");
  const [index, setIndex] = useState(25);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <div className="space-y-2">
          <Label>Project ID</Label>
          <Input
            placeholder="Project UUID"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label>Stage</Label>
          <Select value={stage} onValueChange={setStage}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="00-discover">00-discover</SelectItem>
              <SelectItem value="01-planning">01-planning</SelectItem>
              <SelectItem value="02-design">02-design</SelectItem>
              <SelectItem value="03-integrate">03-integrate</SelectItem>
              <SelectItem value="04-build">04-build</SelectItem>
              <SelectItem value="05-test">05-test</SelectItem>
              <SelectItem value="06-deploy">06-deploy</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Last Gate</Label>
          <Select value={gate} onValueChange={setGate}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="G0.1">G0.1</SelectItem>
              <SelectItem value="G0.2">G0.2</SelectItem>
              <SelectItem value="G1">G1</SelectItem>
              <SelectItem value="G2">G2</SelectItem>
              <SelectItem value="G3">G3</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Tier</Label>
          <Select value={tier} onValueChange={(v) => setTier(v as TierEnum)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="LITE">LITE</SelectItem>
              <SelectItem value="STANDARD">STANDARD</SelectItem>
              <SelectItem value="PROFESSIONAL">PROFESSIONAL</SelectItem>
              <SelectItem value="ENTERPRISE">ENTERPRISE</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Vibecoding Index</Label>
          <Input
            type="number"
            min={0}
            max={100}
            value={index}
            onChange={(e) => setIndex(parseInt(e.target.value) || 0)}
          />
        </div>
      </div>

      <Button disabled={!projectId}>
        <Layers className="h-4 w-4 mr-2" />
        Generate Overlay Preview
      </Button>

      <div className="border rounded-lg p-4 bg-muted/50">
        <div className="text-center text-muted-foreground">
          <Layers className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Configure parameters above and click Generate to preview</p>
          <p className="text-sm">
            The generated overlay will appear here in markdown format
          </p>
        </div>
      </div>
    </div>
  );
}
