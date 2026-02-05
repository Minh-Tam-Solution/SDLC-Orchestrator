/**
 * =========================================================================
 * Template Manager Component
 * SDLC Orchestrator - Sprint 152 (Context Authority UI)
 *
 * Version: 1.0.0
 * Date: February 3, 2026
 * Status: ACTIVE - Sprint 152 Implementation
 * Authority: Frontend Lead + Backend Lead Approved
 * Framework: SDLC 6.0.3
 *
 * Complete template management interface:
 * - Template list with filtering and search
 * - Create/Edit template forms
 * - Template preview and usage statistics
 * - Activation/deactivation toggle
 *
 * Zero Mock Policy: Production-ready with real API integration
 * =========================================================================
 */

"use client";

import { useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import {
  TierEnum,
  TriggerTypeEnum,
  TemplateResponse,
  TemplateCreateRequest,
  TemplateUpdateRequest,
  TemplateFilters,
  useTemplates,
  useTemplate,
  useTemplateUsage,
  useCreateTemplate,
  useUpdateTemplate,
  getTierColor,
  getTriggerTypeLabel,
} from "@/hooks/useContextAuthority";

// =========================================================================
// Types
// =========================================================================

interface TemplateManagerProps {
  className?: string;
}

interface TemplateFormData {
  name: string;
  trigger_type: TriggerTypeEnum;
  trigger_value: string;
  tier: TierEnum | "";
  overlay_content: string;
  priority: number;
  is_active: boolean;
  description: string;
}

// =========================================================================
// Icon Components
// =========================================================================

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  );
}

function PencilIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10"
      />
    </svg>
  );
}

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
      />
    </svg>
  );
}

function XMarkIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
    </svg>
  );
}

function MagnifyingGlassIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
      />
    </svg>
  );
}

function ChartBarIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z"
      />
    </svg>
  );
}

function EyeIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z"
      />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  );
}

// =========================================================================
// Template Form Component
// =========================================================================

interface TemplateFormProps {
  template?: TemplateResponse;
  onSubmit: (data: TemplateCreateRequest | TemplateUpdateRequest) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

function TemplateForm({ template, onSubmit, onCancel, isLoading }: TemplateFormProps) {
  const [formData, setFormData] = useState<TemplateFormData>({
    name: template?.name || "",
    trigger_type: (template?.trigger_type as TriggerTypeEnum) || "gate_pass",
    trigger_value: template?.trigger_value || "",
    tier: (template?.tier as TierEnum) || "",
    overlay_content: template?.overlay_content || "",
    priority: template?.priority ?? 0,
    is_active: template?.is_active ?? true,
    description: template?.description || "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data: TemplateCreateRequest | TemplateUpdateRequest = {
      name: formData.name,
      trigger_type: formData.trigger_type,
      trigger_value: formData.trigger_value,
      tier: formData.tier || undefined,
      overlay_content: formData.overlay_content,
      priority: formData.priority,
      is_active: formData.is_active,
      description: formData.description || undefined,
    };
    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Template Name *
        </label>
        <input
          type="text"
          required
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="e.g., G2 Pass Guidelines"
        />
      </div>

      {/* Trigger Type & Value */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Trigger Type *
          </label>
          <select
            required
            value={formData.trigger_type}
            onChange={(e) =>
              setFormData({ ...formData, trigger_type: e.target.value as TriggerTypeEnum })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="gate_pass">Gate Pass</option>
            <option value="gate_fail">Gate Fail</option>
            <option value="index_zone">Index Zone</option>
            <option value="stage_constraint">Stage Constraint</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Trigger Value *
          </label>
          <input
            type="text"
            required
            value={formData.trigger_value}
            onChange={(e) => setFormData({ ...formData, trigger_value: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., G2, RED, BUILD"
          />
        </div>
      </div>

      {/* Tier & Priority */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tier (Optional)
          </label>
          <select
            value={formData.tier}
            onChange={(e) => setFormData({ ...formData, tier: e.target.value as TierEnum | "" })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Tiers</option>
            <option value="LITE">Lite</option>
            <option value="STANDARD">Standard</option>
            <option value="PROFESSIONAL">Professional</option>
            <option value="ENTERPRISE">Enterprise</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Priority
          </label>
          <input
            type="number"
            value={formData.priority}
            onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            min="0"
            max="100"
          />
        </div>
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <input
          type="text"
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Brief description of this template"
        />
      </div>

      {/* Overlay Content */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Overlay Content *
        </label>
        <textarea
          required
          value={formData.overlay_content}
          onChange={(e) => setFormData({ ...formData, overlay_content: e.target.value })}
          rows={8}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter template content with variables like {date}, {stage}, {tier}..."
        />
        <p className="mt-1 text-xs text-gray-500">
          Available variables: {"{date}"}, {"{stage}"}, {"{tier}"}, {"{gate}"}, {"{index}"}, {"{zone}"}, {"{top_signals}"}
        </p>
      </div>

      {/* Active Toggle */}
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="is_active"
          checked={formData.is_active}
          onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
          className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
        />
        <label htmlFor="is_active" className="text-sm text-gray-700">
          Template is active
        </label>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? "Saving..." : template ? "Update Template" : "Create Template"}
        </button>
      </div>
    </form>
  );
}

// =========================================================================
// Template Usage Panel
// =========================================================================

interface TemplateUsagePanelProps {
  templateId: string;
  onClose: () => void;
}

function TemplateUsagePanel({ templateId, onClose }: TemplateUsagePanelProps) {
  const { data: template } = useTemplate(templateId);
  const { data: usage, isLoading } = useTemplateUsage(templateId, 30);

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          Template Usage: {template?.name || "Loading..."}
        </h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
          <XMarkIcon className="h-5 w-5" />
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-8 text-gray-500">Loading usage data...</div>
      ) : usage ? (
        <div className="space-y-4">
          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-2xl font-bold text-blue-700">{usage.application_count}</p>
              <p className="text-sm text-blue-600">Total Applications</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm font-medium text-green-700">First Applied</p>
              <p className="text-sm text-green-600">
                {usage.first_applied_at
                  ? new Date(usage.first_applied_at).toLocaleDateString()
                  : "Never"}
              </p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <p className="text-sm font-medium text-purple-700">Last Applied</p>
              <p className="text-sm text-purple-600">
                {usage.last_applied_at
                  ? new Date(usage.last_applied_at).toLocaleDateString()
                  : "Never"}
              </p>
            </div>
          </div>

          {/* Recent Applications */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">
              Recent Applications (Last 30 days)
            </h4>
            {usage.recent_applications.length > 0 ? (
              <div className="space-y-2 max-h-60 overflow-auto">
                {usage.recent_applications.map((app, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-gray-50 rounded-lg text-sm"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs text-gray-500">
                        {app.snapshot_id.slice(0, 8)}...
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(app.applied_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No recent applications</p>
            )}
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">No usage data available</div>
      )}
    </div>
  );
}

// =========================================================================
// Main Component
// =========================================================================

export function TemplateManager({ className }: TemplateManagerProps) {
  const [filters, setFilters] = useState<TemplateFilters>({
    page: 1,
    page_size: 10,
  });
  const [searchTerm, setSearchTerm] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<TemplateResponse | null>(null);
  const [showUsage, setShowUsage] = useState<string | null>(null);

  const { data: templatesData, isLoading } = useTemplates(filters);
  const createMutation = useCreateTemplate();
  const updateMutation = useUpdateTemplate();

  const handleCreate = useCallback(async (data: TemplateCreateRequest) => {
    try {
      await createMutation.mutateAsync(data);
      setShowForm(false);
    } catch (error) {
      console.error("Failed to create template:", error);
    }
  }, [createMutation]);

  const handleUpdate = useCallback(
    async (data: TemplateUpdateRequest) => {
      if (!editingTemplate) return;
      try {
        await updateMutation.mutateAsync({ id: editingTemplate.id, data });
        setEditingTemplate(null);
      } catch (error) {
        console.error("Failed to update template:", error);
      }
    },
    [editingTemplate, updateMutation]
  );

  const handleToggleActive = useCallback(
    async (template: TemplateResponse) => {
      try {
        await updateMutation.mutateAsync({
          id: template.id,
          data: { is_active: !template.is_active },
        });
      } catch (error) {
        console.error("Failed to toggle template:", error);
      }
    },
    [updateMutation]
  );

  // Filter templates by search term (client-side)
  const filteredTemplates = templatesData?.templates.filter(
    (t) =>
      t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.trigger_value.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (t.description || "").toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className={cn("", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Template Manager</h2>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
        >
          <PlusIcon className="h-4 w-4" />
          New Template
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-4">
        {/* Search */}
        <div className="relative flex-1">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Trigger Type Filter */}
        <select
          value={filters.trigger_type || ""}
          onChange={(e) =>
            setFilters({
              ...filters,
              trigger_type: (e.target.value as TriggerTypeEnum) || undefined,
              page: 1,
            })
          }
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Triggers</option>
          <option value="gate_pass">Gate Pass</option>
          <option value="gate_fail">Gate Fail</option>
          <option value="index_zone">Index Zone</option>
          <option value="stage_constraint">Stage Constraint</option>
        </select>

        {/* Tier Filter */}
        <select
          value={filters.tier || ""}
          onChange={(e) =>
            setFilters({
              ...filters,
              tier: (e.target.value as TierEnum) || undefined,
              page: 1,
            })
          }
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Tiers</option>
          <option value="LITE">Lite</option>
          <option value="STANDARD">Standard</option>
          <option value="PROFESSIONAL">Professional</option>
          <option value="ENTERPRISE">Enterprise</option>
        </select>

        {/* Active Only */}
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={filters.active_only || false}
            onChange={(e) =>
              setFilters({ ...filters, active_only: e.target.checked || undefined, page: 1 })
            }
            className="h-4 w-4 text-blue-600 rounded"
          />
          Active only
        </label>
      </div>

      {/* Template List */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">Loading templates...</div>
      ) : filteredTemplates && filteredTemplates.length > 0 ? (
        <div className="border rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trigger
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tier
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Priority
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredTemplates.map((template) => (
                <tr key={template.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{template.name}</div>
                      {template.description && (
                        <div className="text-xs text-gray-500">{template.description}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">
                      {getTriggerTypeLabel(template.trigger_type as TriggerTypeEnum)}
                    </span>
                    <span className="ml-2 text-xs text-gray-500">{template.trigger_value}</span>
                  </td>
                  <td className="px-4 py-3">
                    {template.tier ? (
                      <span className={cn("text-xs px-2 py-1 rounded border", getTierColor(template.tier as TierEnum))}>
                        {template.tier}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">All</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{template.priority}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleToggleActive(template)}
                      className={cn(
                        "text-xs px-2 py-1 rounded transition-colors",
                        template.is_active
                          ? "bg-green-100 text-green-700 hover:bg-green-200"
                          : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                      )}
                    >
                      {template.is_active ? "Active" : "Inactive"}
                    </button>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setShowUsage(template.id)}
                        className="p-1 text-gray-400 hover:text-blue-600"
                        title="View Usage"
                      >
                        <ChartBarIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setEditingTemplate(template)}
                        className="p-1 text-gray-400 hover:text-blue-600"
                        title="Edit"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          {templatesData && templatesData.pages > 1 && (
            <div className="px-4 py-3 bg-gray-50 border-t flex items-center justify-between">
              <span className="text-sm text-gray-600">
                Page {templatesData.page} of {templatesData.pages} ({templatesData.total} templates)
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setFilters({ ...filters, page: (filters.page || 1) - 1 })}
                  disabled={(filters.page || 1) <= 1}
                  className="px-3 py-1 text-sm border rounded hover:bg-gray-100 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setFilters({ ...filters, page: (filters.page || 1) + 1 })}
                  disabled={(filters.page || 1) >= templatesData.pages}
                  className="px-3 py-1 text-sm border rounded hover:bg-gray-100 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-300">
          <p className="text-gray-500 mb-2">No templates found</p>
          <button
            onClick={() => setShowForm(true)}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            Create your first template
          </button>
        </div>
      )}

      {/* Create/Edit Form Modal */}
      {(showForm || editingTemplate) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-auto m-4">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">
                  {editingTemplate ? "Edit Template" : "Create New Template"}
                </h2>
                <button
                  onClick={() => {
                    setShowForm(false);
                    setEditingTemplate(null);
                  }}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>
              <TemplateForm
                template={editingTemplate || undefined}
                onSubmit={editingTemplate ? handleUpdate : handleCreate}
                onCancel={() => {
                  setShowForm(false);
                  setEditingTemplate(null);
                }}
                isLoading={createMutation.isPending || updateMutation.isPending}
              />
            </div>
          </div>
        </div>
      )}

      {/* Usage Panel Modal */}
      {showUsage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-auto m-4">
            <TemplateUsagePanel
              templateId={showUsage}
              onClose={() => setShowUsage(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default TemplateManager;
