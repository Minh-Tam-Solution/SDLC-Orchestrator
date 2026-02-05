/**
 * TemplateSelector Component
 * Sprint 155 Day 4 - Track 1: Visual Editor Integration
 *
 * Template library for spec creation.
 *
 * Features:
 * - 10 pre-built templates
 * - Template preview
 * - One-click apply
 * - Template search/filter
 * - Category filtering
 *
 * Architecture: ADR-050 Visual Editor
 */

"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Search, X, Eye, FileText } from "lucide-react";

// =============================================================================
// Types
// =============================================================================

export interface SpecTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  preview: string;
}

interface TemplateSelectorProps {
  templates: SpecTemplate[];
  onSelect: (template: SpecTemplate) => void;
  onPreview?: (template: SpecTemplate) => void;
  selectedTemplateId?: string;
  previewTemplate?: SpecTemplate | null;
  onClosePreview?: () => void;
  loading?: boolean;
  className?: string;
}

// =============================================================================
// Helper Functions
// =============================================================================

function getUniqueCategories(templates: SpecTemplate[]): string[] {
  const categories = new Set(templates.map((t) => t.category));
  return Array.from(categories);
}

function filterTemplates(
  templates: SpecTemplate[],
  search: string,
  category: string | null
): SpecTemplate[] {
  let filtered = templates;

  // Filter by category
  if (category && category !== "All") {
    filtered = filtered.filter((t) => t.category === category);
  }

  // Filter by search
  if (search.trim()) {
    const searchLower = search.toLowerCase();
    filtered = filtered.filter(
      (t) =>
        t.name.toLowerCase().includes(searchLower) ||
        t.description.toLowerCase().includes(searchLower) ||
        t.tags.some((tag) => tag.toLowerCase().includes(searchLower))
    );
  }

  return filtered;
}

// =============================================================================
// Sub-Components
// =============================================================================

interface TemplateCardProps {
  template: SpecTemplate;
  isSelected: boolean;
  onSelect: () => void;
  onPreview?: () => void;
}

function TemplateCard({
  template,
  isSelected,
  onSelect,
  onPreview,
}: TemplateCardProps) {
  return (
    <div
      data-testid="template-card"
      tabIndex={0}
      role="button"
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect();
        }
      }}
      className={cn(
        "group relative p-4 border rounded-lg cursor-pointer transition-all",
        "hover:border-primary hover:shadow-md focus:outline-none focus:ring-2 focus:ring-ring",
        isSelected && "selected border-primary bg-primary/5"
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <h4 className="font-semibold text-sm">{template.name}</h4>
        <span className="text-xs px-2 py-0.5 bg-muted rounded-full">
          {template.category}
        </span>
      </div>

      {/* Description */}
      <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
        {template.description}
      </p>

      {/* Tags */}
      <div className="flex flex-wrap gap-1 mb-3">
        {template.tags.slice(0, 3).map((tag) => (
          <span
            key={tag}
            className="text-xs px-1.5 py-0.5 bg-muted/50 rounded"
          >
            {tag}
          </span>
        ))}
      </div>

      {/* Actions (visible on hover) */}
      <div className="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {onPreview && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onPreview();
            }}
            aria-label="Preview template"
            className="p-1.5 bg-background border rounded hover:bg-muted"
          >
            <Eye className="h-3.5 w-3.5" />
          </button>
        )}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onSelect();
          }}
          aria-label="Use template"
          className="px-2 py-1 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90"
        >
          Use template
        </button>
      </div>
    </div>
  );
}

interface PreviewModalProps {
  template: SpecTemplate;
  onClose: () => void;
  onSelect: () => void;
}

function PreviewModal({ template, onClose, onSelect }: PreviewModalProps) {
  const headingId = `preview-heading-${template.id}`;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={headingId}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    >
      <div className="bg-background w-full max-w-2xl max-h-[80vh] rounded-lg shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h3 id={headingId} className="text-lg font-semibold">
            {template.name}
          </h3>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close preview"
            className="p-1 rounded hover:bg-muted"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          <pre className="p-4 bg-muted rounded-lg text-sm font-mono whitespace-pre-wrap">
            {template.preview}
          </pre>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-4 border-t">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm border rounded-md hover:bg-muted"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onSelect}
            className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Use Template
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export function TemplateSelector({
  templates,
  onSelect,
  onPreview,
  selectedTemplateId,
  previewTemplate,
  onClosePreview,
  loading = false,
  className,
}: TemplateSelectorProps) {
  const [search, setSearch] = React.useState("");
  const [activeCategory, setActiveCategory] = React.useState<string | null>(null);

  const categories = React.useMemo(
    () => getUniqueCategories(templates),
    [templates]
  );

  const filteredTemplates = React.useMemo(
    () => filterTemplates(templates, search, activeCategory),
    [templates, search, activeCategory]
  );

  const handleClearSearch = () => {
    setSearch("");
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header */}
      <div className="p-4 border-b">
        <h3 className="text-lg font-semibold mb-4">Templates</h3>

        {/* Search Input */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="search"
            role="searchbox"
            placeholder="Search templates..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-9 pl-9 pr-9 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
          {search && (
            <button
              type="button"
              onClick={handleClearSearch}
              aria-label="Clear search"
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-muted rounded"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Category Filters */}
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setActiveCategory(null)}
            className={cn(
              "px-3 py-1 text-xs rounded-full border transition-colors",
              !activeCategory
                ? "active bg-primary text-primary-foreground border-primary"
                : "hover:bg-muted"
            )}
          >
            All
          </button>
          {categories.map((category) => (
            <button
              key={category}
              type="button"
              onClick={() => setActiveCategory(category)}
              className={cn(
                "px-3 py-1 text-xs rounded-full border transition-colors",
                activeCategory === category
                  ? "active bg-primary text-primary-foreground border-primary"
                  : "hover:bg-muted"
              )}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto p-4">
        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center h-full gap-3">
            <div
              role="progressbar"
              className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin"
            />
            <div className="grid grid-cols-2 gap-4 w-full">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  data-testid="template-skeleton"
                  className="h-32 bg-muted rounded-lg animate-pulse"
                />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && templates.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground">
            <FileText className="h-12 w-12 opacity-50" />
            <p className="text-sm font-medium">No templates available</p>
          </div>
        )}

        {/* No Results */}
        {!loading && templates.length > 0 && filteredTemplates.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground">
            <Search className="h-12 w-12 opacity-50" />
            <p className="text-sm font-medium">No templates found</p>
            <p className="text-xs">Try a different search term or category</p>
          </div>
        )}

        {/* Template Grid */}
        {!loading && filteredTemplates.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {filteredTemplates.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                isSelected={selectedTemplateId === template.id}
                onSelect={() => onSelect(template)}
                onPreview={onPreview ? () => onPreview(template) : undefined}
              />
            ))}
          </div>
        )}
      </div>

      {/* Preview Modal */}
      {previewTemplate && onClosePreview && (
        <PreviewModal
          template={previewTemplate}
          onClose={onClosePreview}
          onSelect={() => {
            onSelect(previewTemplate);
            onClosePreview();
          }}
        />
      )}
    </div>
  );
}

export default TemplateSelector;
