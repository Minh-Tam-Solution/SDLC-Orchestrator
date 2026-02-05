/**
 * TemplateSelector Component Tests
 * Sprint 155 Day 4 - Track 1: Visual Editor Integration
 *
 * TDD RED Phase: Write failing tests first
 *
 * Test Coverage:
 * - Displays template library (10 templates)
 * - Template preview functionality
 * - One-click apply
 * - Template search/filter
 * - Category filtering
 * - Loading and empty states
 *
 * Architecture: ADR-050 Visual Editor
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { TemplateSelector } from "@/components/spec-converter/TemplateSelector";
import { SpecIR } from "@/hooks/useSpecConverter";

describe("TemplateSelector", () => {
  const mockOnSelect = vi.fn();
  const mockOnPreview = vi.fn();

  // Sample template data
  const sampleTemplates = [
    {
      id: "template-auth",
      name: "User Authentication",
      description: "Complete authentication flow with login, logout, password reset",
      category: "Security",
      tags: ["auth", "security", "login"],
      preview: "# User Authentication Spec\n\n## Requirements...",
    },
    {
      id: "template-crud",
      name: "CRUD Operations",
      description: "Standard Create, Read, Update, Delete operations",
      category: "Data Management",
      tags: ["crud", "api", "data"],
      preview: "# CRUD Operations Spec\n\n## Requirements...",
    },
    {
      id: "template-payment",
      name: "Payment Integration",
      description: "Payment processing with multiple providers",
      category: "E-commerce",
      tags: ["payment", "stripe", "vnpay"],
      preview: "# Payment Integration Spec\n\n## Requirements...",
    },
    {
      id: "template-notification",
      name: "Notification System",
      description: "Push, email, and SMS notifications",
      category: "Communication",
      tags: ["notification", "push", "email"],
      preview: "# Notification System Spec\n\n## Requirements...",
    },
    {
      id: "template-file-upload",
      name: "File Upload",
      description: "File upload with validation and storage",
      category: "Data Management",
      tags: ["file", "upload", "storage"],
      preview: "# File Upload Spec\n\n## Requirements...",
    },
    {
      id: "template-search",
      name: "Search & Filter",
      description: "Full-text search with filters and pagination",
      category: "Data Management",
      tags: ["search", "filter", "pagination"],
      preview: "# Search & Filter Spec\n\n## Requirements...",
    },
    {
      id: "template-rbac",
      name: "Role-Based Access Control",
      description: "RBAC with roles, permissions, and policies",
      category: "Security",
      tags: ["rbac", "roles", "permissions"],
      preview: "# RBAC Spec\n\n## Requirements...",
    },
    {
      id: "template-audit-log",
      name: "Audit Logging",
      description: "Comprehensive audit trail for compliance",
      category: "Compliance",
      tags: ["audit", "log", "compliance"],
      preview: "# Audit Logging Spec\n\n## Requirements...",
    },
    {
      id: "template-api-gateway",
      name: "API Gateway",
      description: "API gateway with rate limiting and caching",
      category: "Infrastructure",
      tags: ["api", "gateway", "rate-limit"],
      preview: "# API Gateway Spec\n\n## Requirements...",
    },
    {
      id: "template-report",
      name: "Report Generation",
      description: "Dynamic report generation with export",
      category: "Reporting",
      tags: ["report", "export", "pdf"],
      preview: "# Report Generation Spec\n\n## Requirements...",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ===========================================================================
  // Rendering Tests
  // ===========================================================================

  describe("Rendering", () => {
    it("renders the template selector with header", () => {
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      expect(screen.getByText(/templates/i)).toBeInTheDocument();
    });

    it("displays all 10 templates", () => {
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      expect(screen.getByText("User Authentication")).toBeInTheDocument();
      expect(screen.getByText("CRUD Operations")).toBeInTheDocument();
      expect(screen.getByText("Payment Integration")).toBeInTheDocument();
      expect(screen.getByText("Notification System")).toBeInTheDocument();
      expect(screen.getByText("File Upload")).toBeInTheDocument();
      expect(screen.getByText("Search & Filter")).toBeInTheDocument();
      expect(screen.getByText("Role-Based Access Control")).toBeInTheDocument();
      expect(screen.getByText("Audit Logging")).toBeInTheDocument();
      expect(screen.getByText("API Gateway")).toBeInTheDocument();
      expect(screen.getByText("Report Generation")).toBeInTheDocument();
    });

    it("displays template descriptions", () => {
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      expect(screen.getByText(/complete authentication flow/i)).toBeInTheDocument();
      expect(screen.getByText(/standard create, read, update, delete/i)).toBeInTheDocument();
    });

    it("displays template categories", () => {
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      // Security category appears in: category filter button + 2 template cards (RBAC, Auth)
      expect(screen.getAllByText("Security").length).toBeGreaterThanOrEqual(2);
      // Data Management appears in: category filter button + 3 template cards
      expect(screen.getAllByText("Data Management").length).toBeGreaterThanOrEqual(3);
      // E-commerce appears in: category filter button + 1 template card
      expect(screen.getAllByText("E-commerce").length).toBeGreaterThanOrEqual(1);
    });

    it("displays template tags", () => {
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      expect(screen.getByText("auth")).toBeInTheDocument();
      expect(screen.getByText("crud")).toBeInTheDocument();
      expect(screen.getByText("payment")).toBeInTheDocument();
    });
  });

  // ===========================================================================
  // Template Selection Tests
  // ===========================================================================

  describe("Template Selection", () => {
    it("calls onSelect when template is clicked", async () => {
      const user = userEvent.setup();
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      const authTemplate = screen.getByText("User Authentication").closest("button, div[role='button']");
      if (authTemplate) {
        await user.click(authTemplate);
      }

      expect(mockOnSelect).toHaveBeenCalledWith(
        expect.objectContaining({ id: "template-auth" })
      );
    });

    it("shows use template button on hover", async () => {
      const user = userEvent.setup();
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      const templateCard = screen.getByText("User Authentication").closest("[data-testid='template-card']");
      if (templateCard) {
        await user.hover(templateCard);
      }

      // Multiple template cards have "Use template" buttons
      const useButtons = screen.getAllByRole("button", { name: /use template/i });
      expect(useButtons.length).toBeGreaterThanOrEqual(1);
    });

    it("highlights selected template", () => {
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
          selectedTemplateId="template-auth"
        />
      );

      const selectedCard = screen.getByText("User Authentication").closest("[data-testid='template-card']");
      expect(selectedCard).toHaveClass("selected");
    });
  });

  // ===========================================================================
  // Template Preview Tests
  // ===========================================================================

  describe("Template Preview", () => {
    it("shows preview button on template card", () => {
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
          onPreview={mockOnPreview}
        />
      );

      const previewButtons = screen.getAllByRole("button", { name: /preview/i });
      expect(previewButtons.length).toBeGreaterThan(0);
    });

    it("calls onPreview when preview button is clicked", async () => {
      const user = userEvent.setup();
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
          onPreview={mockOnPreview}
        />
      );

      const previewButtons = screen.getAllByRole("button", { name: /preview/i });
      await user.click(previewButtons[0]);

      expect(mockOnPreview).toHaveBeenCalledWith(
        expect.objectContaining({ id: "template-auth" })
      );
    });

    it("shows preview modal when preview is active", () => {
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
          previewTemplate={sampleTemplates[0]}
          onClosePreview={vi.fn()}
        />
      );

      expect(screen.getByRole("dialog")).toBeInTheDocument();
      // Preview content is shown in pre tag
      expect(screen.getByText(/User Authentication Spec/)).toBeInTheDocument();
    });

    it("closes preview modal when close button is clicked", async () => {
      const user = userEvent.setup();
      const mockOnClosePreview = vi.fn();
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
          previewTemplate={sampleTemplates[0]}
          onClosePreview={mockOnClosePreview}
        />
      );

      const closeButton = screen.getByRole("button", { name: /close/i });
      await user.click(closeButton);

      expect(mockOnClosePreview).toHaveBeenCalled();
    });
  });

  // ===========================================================================
  // Search/Filter Tests
  // ===========================================================================

  describe("Search and Filter", () => {
    it("shows search input", () => {
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      expect(screen.getByPlaceholderText(/search templates/i)).toBeInTheDocument();
    });

    it("filters templates by name when searching", async () => {
      const user = userEvent.setup();
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      const searchInput = screen.getByPlaceholderText(/search templates/i);
      await user.type(searchInput, "auth");

      expect(screen.getByText("User Authentication")).toBeInTheDocument();
      expect(screen.queryByText("CRUD Operations")).not.toBeInTheDocument();
      expect(screen.queryByText("Payment Integration")).not.toBeInTheDocument();
    });

    it("filters templates by tag when searching", async () => {
      const user = userEvent.setup();
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      const searchInput = screen.getByPlaceholderText(/search templates/i);
      await user.type(searchInput, "security");

      expect(screen.getByText("User Authentication")).toBeInTheDocument();
      expect(screen.queryByText("CRUD Operations")).not.toBeInTheDocument();
    });

    it("filters templates by description when searching", async () => {
      const user = userEvent.setup();
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      const searchInput = screen.getByPlaceholderText(/search templates/i);
      await user.type(searchInput, "compliance");

      expect(screen.getByText("Audit Logging")).toBeInTheDocument();
      expect(screen.queryByText("CRUD Operations")).not.toBeInTheDocument();
    });

    it("shows no results message when search has no matches", async () => {
      const user = userEvent.setup();
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      const searchInput = screen.getByPlaceholderText(/search templates/i);
      await user.type(searchInput, "nonexistent");

      expect(screen.getByText(/no templates found/i)).toBeInTheDocument();
    });

    it("clears search when clear button is clicked", async () => {
      const user = userEvent.setup();
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      const searchInput = screen.getByPlaceholderText(/search templates/i);
      await user.type(searchInput, "auth");

      const clearButton = screen.getByRole("button", { name: /clear search/i });
      await user.click(clearButton);

      expect(searchInput).toHaveValue("");
      expect(screen.getByText("CRUD Operations")).toBeInTheDocument();
    });
  });

  // ===========================================================================
  // Category Filter Tests
  // ===========================================================================

  describe("Category Filter", () => {
    it("shows category filter buttons", () => {
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      // All button exists
      expect(screen.getByRole("button", { name: /^all$/i })).toBeInTheDocument();
      // Security category filter exists (not the one in template cards)
      const securityButtons = screen.getAllByRole("button", { name: /security/i });
      expect(securityButtons.length).toBeGreaterThanOrEqual(1);
      // Data Management category filter exists
      const dataButtons = screen.getAllByRole("button", { name: /data management/i });
      expect(dataButtons.length).toBeGreaterThanOrEqual(1);
    });

    it("filters templates by category when category button is clicked", async () => {
      const user = userEvent.setup();
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      const securityButton = screen.getByRole("button", { name: /^security$/i });
      await user.click(securityButton);

      expect(screen.getByText("User Authentication")).toBeInTheDocument();
      expect(screen.getByText("Role-Based Access Control")).toBeInTheDocument();
      expect(screen.queryByText("CRUD Operations")).not.toBeInTheDocument();
      expect(screen.queryByText("Payment Integration")).not.toBeInTheDocument();
    });

    it("shows all templates when All category is selected", async () => {
      const user = userEvent.setup();
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      // First filter to Security
      const securityButton = screen.getByRole("button", { name: /^security$/i });
      await user.click(securityButton);

      // Then click All
      const allButton = screen.getByRole("button", { name: /all/i });
      await user.click(allButton);

      expect(screen.getByText("CRUD Operations")).toBeInTheDocument();
      expect(screen.getByText("Payment Integration")).toBeInTheDocument();
    });

    it("highlights active category filter", async () => {
      const user = userEvent.setup();
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      const securityButton = screen.getByRole("button", { name: /^security$/i });
      await user.click(securityButton);

      expect(securityButton).toHaveClass("active");
    });
  });

  // ===========================================================================
  // Loading State Tests
  // ===========================================================================

  describe("Loading State", () => {
    it("shows loading indicator when loading", () => {
      render(
        <TemplateSelector
          templates={[]}
          onSelect={mockOnSelect}
          loading
        />
      );

      expect(screen.getByRole("progressbar")).toBeInTheDocument();
    });

    it("shows loading skeletons when loading", () => {
      render(
        <TemplateSelector
          templates={[]}
          onSelect={mockOnSelect}
          loading
        />
      );

      const skeletons = screen.getAllByTestId("template-skeleton");
      expect(skeletons.length).toBeGreaterThanOrEqual(3);
    });
  });

  // ===========================================================================
  // Empty State Tests
  // ===========================================================================

  describe("Empty State", () => {
    it("shows empty state when no templates", () => {
      render(
        <TemplateSelector
          templates={[]}
          onSelect={mockOnSelect}
        />
      );

      expect(screen.getByText(/no templates available/i)).toBeInTheDocument();
    });
  });

  // ===========================================================================
  // Accessibility Tests
  // ===========================================================================

  describe("Accessibility", () => {
    it("has accessible search input", () => {
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      expect(screen.getByRole("searchbox")).toBeInTheDocument();
    });

    it("template cards are keyboard accessible", () => {
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      const templateCards = screen.getAllByTestId("template-card");
      // Template cards should have tabindex for keyboard navigation
      expect(templateCards[0]).toHaveAttribute("tabindex", "0");
      expect(templateCards[0]).toHaveAttribute("role", "button");
    });

    it("can select template with Enter key", async () => {
      const user = userEvent.setup();
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
        />
      );

      const firstCard = screen.getAllByTestId("template-card")[0];
      firstCard.focus();
      await user.keyboard("{Enter}");

      expect(mockOnSelect).toHaveBeenCalled();
    });

    it("preview modal has proper aria attributes", () => {
      render(
        <TemplateSelector
          templates={sampleTemplates}
          onSelect={mockOnSelect}
          previewTemplate={sampleTemplates[0]}
          onClosePreview={vi.fn()}
        />
      );

      const modal = screen.getByRole("dialog");
      expect(modal).toHaveAttribute("aria-labelledby");
      expect(modal).toHaveAttribute("aria-modal", "true");
    });
  });
});
