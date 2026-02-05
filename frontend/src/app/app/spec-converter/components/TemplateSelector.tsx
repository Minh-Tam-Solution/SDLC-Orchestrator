/**
 * Template Selector Component
 * Sprint 154 Day 4 - TDD Phase 2 (GREEN)
 *
 * Grid of pre-built spec templates.
 * Architecture: ADR-050 Visual Editor
 */

"use client";

import { useState, useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Globe,
  Monitor,
  Database,
  Link,
  Shield,
  Zap,
  GitBranch,
  FileText,
  ArrowUpDown,
  Lock,
  Search,
  LayoutTemplate,
} from "lucide-react";
import { createEmptySpecIR, type SpecIR } from "@/hooks/useSpecConverter";

interface TemplateSelectorProps {
  onSelect: (spec: SpecIR) => void;
}

interface SpecTemplate {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  tier: string;
  spec: Partial<SpecIR>;
}

const TEMPLATES: SpecTemplate[] = [
  {
    id: "api-endpoint",
    name: "API Endpoint",
    description: "REST API endpoint specification with request/response schemas",
    icon: <Globe className="h-6 w-6" />,
    tier: "ALL",
    spec: {
      title: "API Endpoint Specification",
      tags: ["api", "rest", "backend"],
      requirements: [
        {
          id: "REQ-001",
          title: "Endpoint Definition",
          priority: "P0",
          tier: ["ALL"],
          given: "the API server is running",
          when: "a client sends a valid request",
          then: "the server returns the expected response",
          acceptance_criteria: [],
        },
      ],
    },
  },
  {
    id: "ui-feature",
    name: "UI Feature",
    description: "Frontend user interface feature with user interactions",
    icon: <Monitor className="h-6 w-6" />,
    tier: "ALL",
    spec: {
      title: "UI Feature Specification",
      tags: ["ui", "frontend", "ux"],
      requirements: [
        {
          id: "REQ-001",
          title: "User Interface Rendering",
          priority: "P0",
          tier: ["ALL"],
          given: "the user navigates to the feature page",
          when: "the page loads",
          then: "all UI elements are displayed correctly",
          acceptance_criteria: [],
        },
      ],
    },
  },
  {
    id: "database",
    name: "Database Schema",
    description: "Database table and schema changes with migrations",
    icon: <Database className="h-6 w-6" />,
    tier: "STANDARD",
    spec: {
      title: "Database Schema Specification",
      tier: ["STANDARD", "PROFESSIONAL", "ENTERPRISE"] as any,
      tags: ["database", "schema", "migration"],
      requirements: [
        {
          id: "REQ-001",
          title: "Schema Definition",
          priority: "P0",
          tier: ["STANDARD"],
          given: "the database is in the current schema version",
          when: "the migration script runs",
          then: "the new schema is applied successfully",
          acceptance_criteria: [],
        },
      ],
    },
  },
  {
    id: "integration",
    name: "Integration",
    description: "Third-party system integration specification",
    icon: <Link className="h-6 w-6" />,
    tier: "STANDARD",
    spec: {
      title: "Integration Specification",
      tier: ["STANDARD", "PROFESSIONAL", "ENTERPRISE"] as any,
      tags: ["integration", "api", "third-party"],
      requirements: [
        {
          id: "REQ-001",
          title: "Integration Connection",
          priority: "P0",
          tier: ["STANDARD"],
          given: "valid credentials are configured",
          when: "the integration service connects",
          then: "the connection is established successfully",
          acceptance_criteria: [],
        },
      ],
    },
  },
  {
    id: "security",
    name: "Security Feature",
    description: "Security-related feature with authentication/authorization",
    icon: <Shield className="h-6 w-6" />,
    tier: "PROFESSIONAL",
    spec: {
      title: "Security Feature Specification",
      tier: ["PROFESSIONAL", "ENTERPRISE"] as any,
      tags: ["security", "auth", "rbac"],
      requirements: [
        {
          id: "REQ-001",
          title: "Security Control",
          priority: "P0",
          tier: ["PROFESSIONAL"],
          given: "a user attempts to access a protected resource",
          when: "the security check is performed",
          then: "only authorized users can access the resource",
          acceptance_criteria: [],
        },
      ],
    },
  },
  {
    id: "performance",
    name: "Performance",
    description: "Performance requirements and optimization spec",
    icon: <Zap className="h-6 w-6" />,
    tier: "PROFESSIONAL",
    spec: {
      title: "Performance Specification",
      tier: ["PROFESSIONAL", "ENTERPRISE"] as any,
      tags: ["performance", "optimization", "latency"],
      requirements: [
        {
          id: "REQ-001",
          title: "Performance Target",
          priority: "P0",
          tier: ["PROFESSIONAL"],
          given: "the system is under normal load",
          when: "a standard operation is performed",
          then: "the response time is within acceptable limits",
          acceptance_criteria: [],
        },
      ],
    },
  },
  {
    id: "workflow",
    name: "Workflow",
    description: "Business workflow and process automation",
    icon: <GitBranch className="h-6 w-6" />,
    tier: "ALL",
    spec: {
      title: "Workflow Specification",
      tags: ["workflow", "automation", "process"],
      requirements: [
        {
          id: "REQ-001",
          title: "Workflow Trigger",
          priority: "P0",
          tier: ["ALL"],
          given: "the workflow trigger condition is met",
          when: "the workflow engine processes the trigger",
          then: "the workflow executes the defined steps",
          acceptance_criteria: [],
        },
      ],
    },
  },
  {
    id: "report",
    name: "Report",
    description: "Analytics and reporting feature specification",
    icon: <FileText className="h-6 w-6" />,
    tier: "STANDARD",
    spec: {
      title: "Report Specification",
      tier: ["STANDARD", "PROFESSIONAL", "ENTERPRISE"] as any,
      tags: ["report", "analytics", "dashboard"],
      requirements: [
        {
          id: "REQ-001",
          title: "Report Generation",
          priority: "P1",
          tier: ["STANDARD"],
          given: "the user has access to the reporting feature",
          when: "the user generates a report",
          then: "the report is created with accurate data",
          acceptance_criteria: [],
        },
      ],
    },
  },
  {
    id: "migration",
    name: "Migration",
    description: "Data migration specification with validation",
    icon: <ArrowUpDown className="h-6 w-6" />,
    tier: "PROFESSIONAL",
    spec: {
      title: "Migration Specification",
      tier: ["PROFESSIONAL", "ENTERPRISE"] as any,
      tags: ["migration", "data", "etl"],
      requirements: [
        {
          id: "REQ-001",
          title: "Data Migration",
          priority: "P0",
          tier: ["PROFESSIONAL"],
          given: "data exists in the source system",
          when: "the migration process runs",
          then: "data is correctly transferred to the target",
          acceptance_criteria: [],
        },
      ],
    },
  },
  {
    id: "compliance",
    name: "Compliance",
    description: "Regulatory compliance requirement specification",
    icon: <Lock className="h-6 w-6" />,
    tier: "ENTERPRISE",
    spec: {
      title: "Compliance Specification",
      tier: ["ENTERPRISE"] as any,
      tags: ["compliance", "regulatory", "audit"],
      requirements: [
        {
          id: "REQ-001",
          title: "Compliance Check",
          priority: "P0",
          tier: ["ENTERPRISE"],
          given: "the system processes regulated data",
          when: "a compliance audit is performed",
          then: "all regulatory requirements are met",
          acceptance_criteria: [],
        },
      ],
    },
  },
];

export function TemplateSelector({ onSelect }: TemplateSelectorProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredTemplates = useMemo(() => {
    if (!searchQuery.trim()) return TEMPLATES;

    const query = searchQuery.toLowerCase();
    return TEMPLATES.filter(
      (template) =>
        template.name.toLowerCase().includes(query) ||
        template.description.toLowerCase().includes(query) ||
        template.tier.toLowerCase().includes(query)
    );
  }, [searchQuery]);

  const handleSelect = (template: SpecTemplate) => {
    const baseSpec = createEmptySpecIR();
    const spec: SpecIR = {
      ...baseSpec,
      ...template.spec,
      spec_id: `SPEC-${Date.now()}`,
    } as SpecIR;
    onSelect(spec);
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case "ALL":
        return "bg-green-100 text-green-800";
      case "LITE":
        return "bg-blue-100 text-blue-800";
      case "STANDARD":
        return "bg-yellow-100 text-yellow-800";
      case "PROFESSIONAL":
        return "bg-purple-100 text-purple-800";
      case "ENTERPRISE":
        return "bg-red-100 text-red-800";
      default:
        return "";
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <LayoutTemplate className="h-5 w-5" />
          Templates
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search templates..."
            className="pl-9"
          />
        </div>

        {/* Template Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {filteredTemplates.map((template) => (
            <button
              key={template.id}
              type="button"
              onClick={() => handleSelect(template)}
              className="flex items-start gap-3 p-3 rounded-lg border bg-card hover:bg-accent hover:text-accent-foreground transition-colors text-left"
            >
              <div className="flex-shrink-0 p-2 rounded-md bg-muted">
                {template.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium truncate">{template.name}</span>
                  <Badge
                    variant="secondary"
                    className={`text-xs ${getTierColor(template.tier)}`}
                  >
                    {template.tier}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  {template.description}
                </p>
              </div>
            </button>
          ))}
        </div>

        {filteredTemplates.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No templates found matching "{searchQuery}"</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default TemplateSelector;
