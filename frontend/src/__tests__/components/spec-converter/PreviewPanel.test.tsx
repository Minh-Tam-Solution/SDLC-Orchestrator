/**
 * PreviewPanel Component Tests
 * Sprint 155 Day 4 - Track 1: Visual Editor Integration
 *
 * TDD RED Phase: Write failing tests first
 *
 * Test Coverage:
 * - Renders preview in different formats (BDD, OpenSpec, User Story)
 * - Format selector functionality
 * - Syntax highlighting
 * - Copy to clipboard functionality
 * - Loading and error states
 * - Empty state handling
 *
 * Architecture: ADR-050 Visual Editor
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";
import { PreviewPanel } from "@/components/spec-converter/PreviewPanel";
import { SpecIR, SpecFormat } from "@/hooks/useSpecConverter";

// Mock clipboard API - vitest global setup
const mockWriteText = vi.fn().mockResolvedValue(undefined);

beforeAll(() => {
  Object.defineProperty(navigator, "clipboard", {
    value: {
      writeText: mockWriteText,
    },
    writable: true,
    configurable: true,
  });
});

describe("PreviewPanel", () => {
  const mockOnFormatChange = vi.fn();
  const mockOnRender = vi.fn();

  const sampleSpec: SpecIR = {
    spec_id: "SPEC-001",
    title: "User Authentication",
    version: "1.0.0",
    status: "APPROVED",
    tier: ["STANDARD", "PROFESSIONAL"],
    owner: "team@example.com",
    last_updated: "2026-02-04T10:00:00Z",
    tags: ["auth", "security"],
    related_adrs: ["ADR-001"],
    related_specs: [],
    requirements: [
      {
        id: "REQ-001",
        title: "Login with Email",
        priority: "P0",
        tier: ["ALL"],
        given: "A registered user",
        when: "They enter valid credentials",
        then: "They should be logged in",
        acceptance_criteria: ["User is redirected to dashboard"],
      },
    ],
    acceptance_criteria: [
      {
        id: "AC-001",
        scenario: "Successful login",
        given: "A registered user",
        when: "They enter valid credentials",
        then: "They should be logged in",
        tier: ["ALL"],
        testable: true,
      },
    ],
  };

  const sampleRenderedContent = `# SPEC-001: User Authentication

## Requirements

### REQ-001: Login with Email (P0)

**Given** A registered user
**When** They enter valid credentials
**Then** They should be logged in
`;

  beforeEach(() => {
    vi.clearAllMocks();
    mockWriteText.mockClear();
  });

  // ===========================================================================
  // Rendering Tests
  // ===========================================================================

  describe("Rendering", () => {
    it("renders the preview panel with header", () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      expect(screen.getByText(/preview/i)).toBeInTheDocument();
    });

    it("displays the rendered content", () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      expect(screen.getByText(/User Authentication/)).toBeInTheDocument();
      expect(screen.getByText(/Login with Email/)).toBeInTheDocument();
    });

    it("shows format selector with all format options", async () => {
      const user = userEvent.setup();
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      const formatSelector = screen.getByRole("combobox", { name: /format/i });
      expect(formatSelector).toBeInTheDocument();

      await user.click(formatSelector);

      expect(screen.getByRole("option", { name: /bdd/i })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: /openspec/i })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: /user.*story/i })).toBeInTheDocument();
    });

    it("displays current format as selected", () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="OPENSPEC"
          onFormatChange={mockOnFormatChange}
        />
      );

      const formatSelector = screen.getByRole("combobox", { name: /format/i });
      expect(formatSelector).toHaveValue("OPENSPEC");
    });

    it("shows copy button", () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      expect(screen.getByRole("button", { name: /copy/i })).toBeInTheDocument();
    });
  });

  // ===========================================================================
  // Format Selector Tests
  // ===========================================================================

  describe("Format Selector", () => {
    it("calls onFormatChange when format is changed to BDD", async () => {
      const user = userEvent.setup();
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="OPENSPEC"
          onFormatChange={mockOnFormatChange}
        />
      );

      const formatSelector = screen.getByRole("combobox", { name: /format/i });
      await user.selectOptions(formatSelector, "BDD");

      expect(mockOnFormatChange).toHaveBeenCalledWith("BDD");
    });

    it("calls onFormatChange when format is changed to USER_STORY", async () => {
      const user = userEvent.setup();
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      const formatSelector = screen.getByRole("combobox", { name: /format/i });
      await user.selectOptions(formatSelector, "USER_STORY");

      expect(mockOnFormatChange).toHaveBeenCalledWith("USER_STORY");
    });

    it("calls onFormatChange when format is changed to OPENSPEC", async () => {
      const user = userEvent.setup();
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      const formatSelector = screen.getByRole("combobox", { name: /format/i });
      await user.selectOptions(formatSelector, "OPENSPEC");

      expect(mockOnFormatChange).toHaveBeenCalledWith("OPENSPEC");
    });
  });

  // ===========================================================================
  // Copy to Clipboard Tests
  // ===========================================================================

  describe("Copy to Clipboard", () => {
    it("copies content to clipboard when copy button is clicked", async () => {
      // Re-setup mock for this specific test
      const localMockWriteText = vi.fn().mockResolvedValue(undefined);
      Object.defineProperty(navigator, "clipboard", {
        value: { writeText: localMockWriteText },
        writable: true,
        configurable: true,
      });

      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      const copyButton = screen.getByRole("button", { name: /copy/i });
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(localMockWriteText).toHaveBeenCalledWith(sampleRenderedContent);
      });
    });

    it("shows success feedback after copying", async () => {
      const user = userEvent.setup();
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      const copyButton = screen.getByRole("button", { name: /copy/i });
      await user.click(copyButton);

      await waitFor(() => {
        expect(screen.getByText(/copied/i)).toBeInTheDocument();
      });
    });

    it("resets copy feedback after timeout", async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });

      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      const copyButton = screen.getByRole("button", { name: /copy/i });
      fireEvent.click(copyButton);

      // Wait for copy feedback to appear
      await waitFor(() => {
        expect(screen.getByText(/copied/i)).toBeInTheDocument();
      });

      // Advance timers
      vi.advanceTimersByTime(2500);

      // Wait for feedback to disappear
      await waitFor(() => {
        expect(screen.queryByText(/copied/i)).not.toBeInTheDocument();
      });

      vi.useRealTimers();
    }, 10000);
  });

  // ===========================================================================
  // Syntax Highlighting Tests
  // ===========================================================================

  describe("Syntax Highlighting", () => {
    it("renders content with syntax highlighting container", () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      const codeBlock = screen.getByTestId("preview-content");
      expect(codeBlock).toHaveClass("syntax-highlight");
    });

    it("applies markdown highlighting class", () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      const codeBlock = screen.getByTestId("preview-content");
      expect(codeBlock).toHaveClass("language-markdown");
    });
  });

  // ===========================================================================
  // Loading State Tests
  // ===========================================================================

  describe("Loading State", () => {
    it("shows loading indicator when loading", () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content=""
          format="BDD"
          onFormatChange={mockOnFormatChange}
          loading
        />
      );

      expect(screen.getByRole("progressbar")).toBeInTheDocument();
    });

    it("disables copy button when loading", () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
          loading
        />
      );

      const copyButton = screen.getByRole("button", { name: /copy/i });
      expect(copyButton).toBeDisabled();
    });

    it("shows loading message", () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content=""
          format="BDD"
          onFormatChange={mockOnFormatChange}
          loading
        />
      );

      expect(screen.getByText(/generating preview/i)).toBeInTheDocument();
    });
  });

  // ===========================================================================
  // Error State Tests
  // ===========================================================================

  describe("Error State", () => {
    it("shows error message when error prop is provided", () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content=""
          format="BDD"
          onFormatChange={mockOnFormatChange}
          error="Failed to render specification"
        />
      );

      expect(screen.getByText(/failed to render specification/i)).toBeInTheDocument();
    });

    it("shows error icon in error state", () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content=""
          format="BDD"
          onFormatChange={mockOnFormatChange}
          error="Render error"
        />
      );

      expect(screen.getByTestId("error-icon")).toBeInTheDocument();
    });

    it("shows retry button on error", () => {
      const mockOnRetry = vi.fn();
      render(
        <PreviewPanel
          spec={sampleSpec}
          content=""
          format="BDD"
          onFormatChange={mockOnFormatChange}
          error="Render error"
          onRetry={mockOnRetry}
        />
      );

      expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
    });

    it("calls onRetry when retry button is clicked", async () => {
      const mockOnRetry = vi.fn();
      render(
        <PreviewPanel
          spec={sampleSpec}
          content=""
          format="BDD"
          onFormatChange={mockOnFormatChange}
          error="Render error"
          onRetry={mockOnRetry}
        />
      );

      const retryButton = screen.getByRole("button", { name: /retry/i });
      fireEvent.click(retryButton);

      expect(mockOnRetry).toHaveBeenCalled();
    });
  });

  // ===========================================================================
  // Empty State Tests
  // ===========================================================================

  describe("Empty State", () => {
    it("shows empty state when content is empty and not loading", () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content=""
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      expect(screen.getByText(/no preview available/i)).toBeInTheDocument();
    });

    it("shows hint to add requirements in empty state", () => {
      const emptySpec: SpecIR = {
        ...sampleSpec,
        requirements: [],
        acceptance_criteria: [],
      };

      render(
        <PreviewPanel
          spec={emptySpec}
          content=""
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      expect(screen.getByText(/add requirements to see preview/i)).toBeInTheDocument();
    });
  });

  // ===========================================================================
  // Accessibility Tests
  // ===========================================================================

  describe("Accessibility", () => {
    it("has accessible label for format selector", () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      expect(screen.getByRole("combobox", { name: /format/i })).toBeInTheDocument();
    });

    it("has accessible label for copy button", () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      expect(screen.getByRole("button", { name: /copy/i })).toBeInTheDocument();
    });

    it("announces copy success to screen readers", async () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      const copyButton = screen.getByRole("button", { name: /copy/i });
      fireEvent.click(copyButton);

      await waitFor(
        () => {
          expect(screen.getByRole("status")).toHaveTextContent(/copied/i);
        },
        { timeout: 3000 }
      );
    });

    it("has proper heading hierarchy", () => {
      render(
        <PreviewPanel
          spec={sampleSpec}
          content={sampleRenderedContent}
          format="BDD"
          onFormatChange={mockOnFormatChange}
        />
      );

      const heading = screen.getByRole("heading", { name: /preview/i });
      expect(heading).toBeInTheDocument();
    });
  });
});
