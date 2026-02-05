/**
 * Test Spec Converter Visual Editor Page
 * Sprint 154 Day 4 - TDD Phase 1 (RED)
 *
 * Tests for the Visual Editor components per ADR-050.
 *
 * Components tested:
 * - MetadataPanel - Edit spec metadata
 * - RequirementEditor - Single requirement form
 * - RequirementsEditor - Requirements list management
 * - AcceptanceCriteriaEditor - AC management
 * - PreviewPanel - Live preview
 * - TemplateSelector - Template selection
 * - SpecConverterPage - Main page integration
 *
 * TDD Workflow:
 * 1. Write these tests FIRST (RED - tests fail)
 * 2. Implement components to pass tests (GREEN)
 * 3. Refactor if needed
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi, describe, it, expect, beforeEach } from "vitest";

// Components to test (will be implemented in GREEN phase)
import { MetadataPanel } from "../components/MetadataPanel";
import { RequirementEditor } from "../components/RequirementEditor";
import { RequirementsEditor } from "../components/RequirementsEditor";
import { AcceptanceCriteriaEditor } from "../components/AcceptanceCriteriaEditor";
import { PreviewPanel } from "../components/PreviewPanel";
import { TemplateSelector } from "../components/TemplateSelector";
import SpecConverterPage from "../page";

// Mock hook
import * as useSpecConverterModule from "@/hooks/useSpecConverter";
import type {
  SpecIR,
  SpecRequirement,
  AcceptanceCriterion,
} from "@/hooks/useSpecConverter";

// =============================================================================
// Test Utilities
// =============================================================================

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
};

const createMockSpecIR = (overrides: Partial<SpecIR> = {}): SpecIR => ({
  spec_id: "SPEC-001",
  title: "Test Specification",
  version: "1.0.0",
  status: "DRAFT",
  tier: ["ALL"] as any,
  owner: "test@example.com",
  last_updated: "2026-02-04T10:00:00Z",
  tags: ["test"],
  related_adrs: ["ADR-001"],
  related_specs: [],
  requirements: [],
  acceptance_criteria: [],
  ...overrides,
});

const createMockRequirement = (
  overrides: Partial<SpecRequirement> = {}
): SpecRequirement => ({
  id: "REQ-001",
  title: "Test Requirement",
  priority: "P0",
  tier: ["ALL"],
  given: "a precondition",
  when: "an action",
  then: "a result",
  acceptance_criteria: [],
  ...overrides,
});

const createMockAcceptanceCriterion = (
  overrides: Partial<AcceptanceCriterion> = {}
): AcceptanceCriterion => ({
  id: "AC-001",
  scenario: "Test Scenario",
  given: "context",
  when: "action",
  then: "outcome",
  tier: ["ALL"],
  testable: true,
  ...overrides,
});

// =============================================================================
// MetadataPanel Tests
// =============================================================================

describe("MetadataPanel", () => {
  const defaultProps = {
    specIR: createMockSpecIR(),
    onChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Rendering", () => {
    it("should render all metadata fields", () => {
      renderWithProviders(<MetadataPanel {...defaultProps} />);

      expect(screen.getByLabelText(/spec id/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/version/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/status/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/owner/i)).toBeInTheDocument();
    });

    it("should display current spec values", () => {
      renderWithProviders(<MetadataPanel {...defaultProps} />);

      expect(screen.getByDisplayValue("SPEC-001")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Test Specification")).toBeInTheDocument();
      expect(screen.getByDisplayValue("1.0.0")).toBeInTheDocument();
      expect(screen.getByDisplayValue("test@example.com")).toBeInTheDocument();
    });

    it("should render tier checkboxes", () => {
      renderWithProviders(<MetadataPanel {...defaultProps} />);

      expect(screen.getByRole("checkbox", { name: /lite/i })).toBeInTheDocument();
      expect(screen.getByRole("checkbox", { name: /standard/i })).toBeInTheDocument();
      expect(screen.getByRole("checkbox", { name: /professional/i })).toBeInTheDocument();
      expect(screen.getByRole("checkbox", { name: /enterprise/i })).toBeInTheDocument();
    });

    it("should render tags input", () => {
      renderWithProviders(<MetadataPanel {...defaultProps} />);

      expect(screen.getByLabelText(/tags/i)).toBeInTheDocument();
      expect(screen.getByText("test")).toBeInTheDocument(); // Existing tag
    });

    it("should render related ADRs section", () => {
      renderWithProviders(<MetadataPanel {...defaultProps} />);

      expect(screen.getByText(/related adrs/i)).toBeInTheDocument();
      expect(screen.getByText("ADR-001")).toBeInTheDocument();
    });
  });

  describe("Interactions", () => {
    it("should call onChange when spec_id changes", async () => {
      const onChange = vi.fn();
      renderWithProviders(<MetadataPanel {...defaultProps} onChange={onChange} />);

      const input = screen.getByLabelText(/spec id/i);
      await userEvent.clear(input);
      await userEvent.type(input, "SPEC-002");

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ spec_id: "SPEC-002" })
      );
    });

    it("should call onChange when title changes", async () => {
      const onChange = vi.fn();
      renderWithProviders(<MetadataPanel {...defaultProps} onChange={onChange} />);

      const input = screen.getByLabelText(/title/i);
      await userEvent.clear(input);
      await userEvent.type(input, "New Title");

      expect(onChange).toHaveBeenCalled();
    });

    it("should call onChange when status changes", async () => {
      const onChange = vi.fn();
      renderWithProviders(<MetadataPanel {...defaultProps} onChange={onChange} />);

      const statusSelect = screen.getByLabelText(/status/i);
      await userEvent.click(statusSelect);
      await userEvent.click(screen.getByText("PROPOSED"));

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ status: "PROPOSED" })
      );
    });

    it("should allow adding new tags", async () => {
      const onChange = vi.fn();
      renderWithProviders(<MetadataPanel {...defaultProps} onChange={onChange} />);

      const tagInput = screen.getByPlaceholderText(/add tag/i);
      await userEvent.type(tagInput, "newtag{enter}");

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ tags: expect.arrayContaining(["test", "newtag"]) })
      );
    });

    it("should allow removing tags", async () => {
      const onChange = vi.fn();
      renderWithProviders(<MetadataPanel {...defaultProps} onChange={onChange} />);

      const removeButton = screen.getByRole("button", { name: /remove test/i });
      await userEvent.click(removeButton);

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ tags: [] })
      );
    });

    it("should toggle tier checkboxes", async () => {
      const onChange = vi.fn();
      renderWithProviders(<MetadataPanel {...defaultProps} onChange={onChange} />);

      const enterpriseCheckbox = screen.getByRole("checkbox", { name: /enterprise/i });
      await userEvent.click(enterpriseCheckbox);

      expect(onChange).toHaveBeenCalled();
    });
  });
});

// =============================================================================
// RequirementEditor Tests
// =============================================================================

describe("RequirementEditor", () => {
  const defaultProps = {
    requirement: createMockRequirement(),
    onChange: vi.fn(),
    onRemove: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Rendering", () => {
    it("should render BDD fields (Given/When/Then)", () => {
      renderWithProviders(<RequirementEditor {...defaultProps} />);

      expect(screen.getByLabelText(/given/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/when/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/then/i)).toBeInTheDocument();
    });

    it("should display requirement values", () => {
      renderWithProviders(<RequirementEditor {...defaultProps} />);

      expect(screen.getByDisplayValue("REQ-001")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Test Requirement")).toBeInTheDocument();
      expect(screen.getByDisplayValue("a precondition")).toBeInTheDocument();
      expect(screen.getByDisplayValue("an action")).toBeInTheDocument();
      expect(screen.getByDisplayValue("a result")).toBeInTheDocument();
    });

    it("should render priority selector", () => {
      renderWithProviders(<RequirementEditor {...defaultProps} />);

      expect(screen.getByLabelText(/priority/i)).toBeInTheDocument();
    });

    it("should render remove button", () => {
      renderWithProviders(<RequirementEditor {...defaultProps} />);

      expect(screen.getByRole("button", { name: /remove|delete/i })).toBeInTheDocument();
    });

    it("should be collapsible", () => {
      renderWithProviders(<RequirementEditor {...defaultProps} />);

      const header = screen.getByText(/REQ-001/i).closest("button");
      expect(header).toBeInTheDocument();
    });
  });

  describe("Interactions", () => {
    it("should call onChange when Given field changes", async () => {
      const onChange = vi.fn();
      renderWithProviders(<RequirementEditor {...defaultProps} onChange={onChange} />);

      const givenInput = screen.getByLabelText(/given/i);
      await userEvent.clear(givenInput);
      await userEvent.type(givenInput, "new precondition");

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ given: "new precondition" })
      );
    });

    it("should call onChange when When field changes", async () => {
      const onChange = vi.fn();
      renderWithProviders(<RequirementEditor {...defaultProps} onChange={onChange} />);

      const whenInput = screen.getByLabelText(/when/i);
      await userEvent.clear(whenInput);
      await userEvent.type(whenInput, "new action");

      expect(onChange).toHaveBeenCalled();
    });

    it("should call onChange when Then field changes", async () => {
      const onChange = vi.fn();
      renderWithProviders(<RequirementEditor {...defaultProps} onChange={onChange} />);

      const thenInput = screen.getByLabelText(/then/i);
      await userEvent.clear(thenInput);
      await userEvent.type(thenInput, "new result");

      expect(onChange).toHaveBeenCalled();
    });

    it("should call onRemove when remove button clicked", async () => {
      const onRemove = vi.fn();
      renderWithProviders(<RequirementEditor {...defaultProps} onRemove={onRemove} />);

      const removeButton = screen.getByRole("button", { name: /remove|delete/i });
      await userEvent.click(removeButton);

      expect(onRemove).toHaveBeenCalled();
    });

    it("should call onChange when priority changes", async () => {
      const onChange = vi.fn();
      renderWithProviders(<RequirementEditor {...defaultProps} onChange={onChange} />);

      const prioritySelect = screen.getByLabelText(/priority/i);
      await userEvent.click(prioritySelect);
      await userEvent.click(screen.getByText("P1"));

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ priority: "P1" })
      );
    });
  });
});

// =============================================================================
// RequirementsEditor Tests
// =============================================================================

describe("RequirementsEditor", () => {
  const defaultProps = {
    requirements: [createMockRequirement()],
    onChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Rendering", () => {
    it("should render requirements list", () => {
      renderWithProviders(<RequirementsEditor {...defaultProps} />);

      expect(screen.getByText(/requirements/i)).toBeInTheDocument();
      expect(screen.getByText(/REQ-001/i)).toBeInTheDocument();
    });

    it("should render add requirement button", () => {
      renderWithProviders(<RequirementsEditor {...defaultProps} />);

      expect(screen.getByRole("button", { name: /add requirement/i })).toBeInTheDocument();
    });

    it("should render empty state when no requirements", () => {
      renderWithProviders(<RequirementsEditor requirements={[]} onChange={vi.fn()} />);

      expect(screen.getByText(/no requirements/i)).toBeInTheDocument();
    });

    it("should render multiple requirements", () => {
      const requirements = [
        createMockRequirement({ id: "REQ-001" }),
        createMockRequirement({ id: "REQ-002" }),
        createMockRequirement({ id: "REQ-003" }),
      ];
      renderWithProviders(
        <RequirementsEditor requirements={requirements} onChange={vi.fn()} />
      );

      expect(screen.getByText(/REQ-001/i)).toBeInTheDocument();
      expect(screen.getByText(/REQ-002/i)).toBeInTheDocument();
      expect(screen.getByText(/REQ-003/i)).toBeInTheDocument();
    });
  });

  describe("Interactions", () => {
    it("should add new requirement when button clicked", async () => {
      const onChange = vi.fn();
      renderWithProviders(<RequirementsEditor {...defaultProps} onChange={onChange} />);

      const addButton = screen.getByRole("button", { name: /add requirement/i });
      await userEvent.click(addButton);

      expect(onChange).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({ id: "REQ-001" }),
          expect.objectContaining({ id: expect.stringMatching(/^REQ-/) }),
        ])
      );
    });

    it("should remove requirement when remove clicked", async () => {
      const onChange = vi.fn();
      const requirements = [
        createMockRequirement({ id: "REQ-001" }),
        createMockRequirement({ id: "REQ-002" }),
      ];
      renderWithProviders(
        <RequirementsEditor requirements={requirements} onChange={onChange} />
      );

      const removeButtons = screen.getAllByRole("button", { name: /remove|delete/i });
      await userEvent.click(removeButtons[0]);

      expect(onChange).toHaveBeenCalledWith(
        expect.arrayContaining([expect.objectContaining({ id: "REQ-002" })])
      );
    });

    it("should update requirement when edited", async () => {
      const onChange = vi.fn();
      renderWithProviders(<RequirementsEditor {...defaultProps} onChange={onChange} />);

      const titleInput = screen.getByDisplayValue("Test Requirement");
      await userEvent.clear(titleInput);
      await userEvent.type(titleInput, "Updated Title");

      expect(onChange).toHaveBeenCalled();
    });
  });
});

// =============================================================================
// AcceptanceCriteriaEditor Tests
// =============================================================================

describe("AcceptanceCriteriaEditor", () => {
  const defaultProps = {
    criteria: [createMockAcceptanceCriterion()],
    onChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Rendering", () => {
    it("should render acceptance criteria list", () => {
      renderWithProviders(<AcceptanceCriteriaEditor {...defaultProps} />);

      expect(screen.getByText(/acceptance criteria/i)).toBeInTheDocument();
      expect(screen.getByText(/AC-001/i)).toBeInTheDocument();
    });

    it("should render add criterion button", () => {
      renderWithProviders(<AcceptanceCriteriaEditor {...defaultProps} />);

      expect(screen.getByRole("button", { name: /add criterion/i })).toBeInTheDocument();
    });

    it("should render BDD fields for each criterion", () => {
      renderWithProviders(<AcceptanceCriteriaEditor {...defaultProps} />);

      expect(screen.getByDisplayValue("Test Scenario")).toBeInTheDocument();
      expect(screen.getByDisplayValue("context")).toBeInTheDocument();
      expect(screen.getByDisplayValue("action")).toBeInTheDocument();
      expect(screen.getByDisplayValue("outcome")).toBeInTheDocument();
    });

    it("should render testable checkbox", () => {
      renderWithProviders(<AcceptanceCriteriaEditor {...defaultProps} />);

      expect(screen.getByRole("checkbox", { name: /testable/i })).toBeInTheDocument();
    });
  });

  describe("Interactions", () => {
    it("should add new criterion when button clicked", async () => {
      const onChange = vi.fn();
      renderWithProviders(
        <AcceptanceCriteriaEditor {...defaultProps} onChange={onChange} />
      );

      const addButton = screen.getByRole("button", { name: /add criterion/i });
      await userEvent.click(addButton);

      expect(onChange).toHaveBeenCalledWith(expect.arrayContaining([
        expect.objectContaining({ id: "AC-001" }),
        expect.objectContaining({ id: expect.stringMatching(/^AC-/) }),
      ]));
    });

    it("should remove criterion when remove clicked", async () => {
      const onChange = vi.fn();
      renderWithProviders(
        <AcceptanceCriteriaEditor {...defaultProps} onChange={onChange} />
      );

      const removeButton = screen.getByRole("button", { name: /remove|delete/i });
      await userEvent.click(removeButton);

      expect(onChange).toHaveBeenCalledWith([]);
    });

    it("should toggle testable checkbox", async () => {
      const onChange = vi.fn();
      renderWithProviders(
        <AcceptanceCriteriaEditor {...defaultProps} onChange={onChange} />
      );

      const checkbox = screen.getByRole("checkbox", { name: /testable/i });
      await userEvent.click(checkbox);

      expect(onChange).toHaveBeenCalledWith([
        expect.objectContaining({ testable: false }),
      ]);
    });
  });
});

// =============================================================================
// PreviewPanel Tests
// =============================================================================

describe("PreviewPanel", () => {
  const mockUseSpecConverter = vi.spyOn(useSpecConverterModule, "useSpecConverter");

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseSpecConverter.mockReturnValue({
      render: vi.fn(),
      renderAsync: vi.fn().mockResolvedValue({ content: "# SPEC-001\n---", format: "OPENSPEC" }),
      isRendering: false,
      renderError: null,
      renderedContent: { content: "# SPEC-001\n---\nspec_id: SPEC-001", format: "OPENSPEC" },
    } as any);
  });

  const defaultProps = {
    specIR: createMockSpecIR(),
    format: "OPENSPEC" as const,
  };

  describe("Rendering", () => {
    it("should render preview panel with title", () => {
      renderWithProviders(<PreviewPanel {...defaultProps} />);

      expect(screen.getByText(/preview/i)).toBeInTheDocument();
    });

    it("should render format selector", () => {
      renderWithProviders(<PreviewPanel {...defaultProps} />);

      expect(screen.getByLabelText(/format/i)).toBeInTheDocument();
    });

    it("should display rendered content", () => {
      renderWithProviders(<PreviewPanel {...defaultProps} />);

      expect(screen.getByText(/spec_id: SPEC-001/i)).toBeInTheDocument();
    });

    it("should render copy button", () => {
      renderWithProviders(<PreviewPanel {...defaultProps} />);

      expect(screen.getByRole("button", { name: /copy/i })).toBeInTheDocument();
    });

    it("should render download button", () => {
      renderWithProviders(<PreviewPanel {...defaultProps} />);

      expect(screen.getByRole("button", { name: /download/i })).toBeInTheDocument();
    });

    it("should show loading state while rendering", () => {
      mockUseSpecConverter.mockReturnValue({
        isRendering: true,
        renderedContent: null,
      } as any);

      renderWithProviders(<PreviewPanel {...defaultProps} />);

      expect(screen.getByText(/loading|rendering/i)).toBeInTheDocument();
    });

    it("should show error state on render error", () => {
      mockUseSpecConverter.mockReturnValue({
        isRendering: false,
        renderError: new Error("Render failed"),
        renderedContent: null,
      } as any);

      renderWithProviders(<PreviewPanel {...defaultProps} />);

      expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
    });
  });

  describe("Interactions", () => {
    it("should change format when selector changes", async () => {
      const onFormatChange = vi.fn();
      renderWithProviders(
        <PreviewPanel {...defaultProps} onFormatChange={onFormatChange} />
      );

      const formatSelect = screen.getByLabelText(/format/i);
      await userEvent.click(formatSelect);
      await userEvent.click(screen.getByText("BDD"));

      expect(onFormatChange).toHaveBeenCalledWith("BDD");
    });

    it("should copy content to clipboard", async () => {
      const mockClipboard = { writeText: vi.fn().mockResolvedValue(undefined) };
      Object.assign(navigator, { clipboard: mockClipboard });

      renderWithProviders(<PreviewPanel {...defaultProps} />);

      const copyButton = screen.getByRole("button", { name: /copy/i });
      await userEvent.click(copyButton);

      expect(mockClipboard.writeText).toHaveBeenCalled();
    });
  });
});

// =============================================================================
// TemplateSelector Tests
// =============================================================================

describe("TemplateSelector", () => {
  const defaultProps = {
    onSelect: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Rendering", () => {
    it("should render template selector title", () => {
      renderWithProviders(<TemplateSelector {...defaultProps} />);

      expect(screen.getByText(/templates/i)).toBeInTheDocument();
    });

    it("should render available templates", () => {
      renderWithProviders(<TemplateSelector {...defaultProps} />);

      expect(screen.getByText(/api endpoint/i)).toBeInTheDocument();
      expect(screen.getByText(/ui feature/i)).toBeInTheDocument();
      expect(screen.getByText(/database/i)).toBeInTheDocument();
    });

    it("should render template descriptions", () => {
      renderWithProviders(<TemplateSelector {...defaultProps} />);

      // Each template should have a description
      const templateCards = screen.getAllByRole("button");
      expect(templateCards.length).toBeGreaterThanOrEqual(3);
    });

    it("should display tier badges for templates", () => {
      renderWithProviders(<TemplateSelector {...defaultProps} />);

      expect(screen.getByText(/ALL/i)).toBeInTheDocument();
    });
  });

  describe("Interactions", () => {
    it("should call onSelect when template clicked", async () => {
      const onSelect = vi.fn();
      renderWithProviders(<TemplateSelector onSelect={onSelect} />);

      const apiTemplate = screen.getByText(/api endpoint/i).closest("button");
      await userEvent.click(apiTemplate!);

      expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({
        spec_id: expect.stringMatching(/^SPEC-/),
        title: expect.any(String),
      }));
    });

    it("should filter templates by search", async () => {
      renderWithProviders(<TemplateSelector {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText(/search templates/i);
      await userEvent.type(searchInput, "api");

      expect(screen.getByText(/api endpoint/i)).toBeInTheDocument();
      expect(screen.queryByText(/database/i)).not.toBeInTheDocument();
    });
  });
});

// =============================================================================
// SpecConverterPage Integration Tests
// =============================================================================

describe("SpecConverterPage", () => {
  const mockUseSpecConverter = vi.spyOn(useSpecConverterModule, "useSpecConverter");

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseSpecConverter.mockReturnValue({
      parse: vi.fn(),
      parseAsync: vi.fn().mockResolvedValue(createMockSpecIR()),
      isParsing: false,
      parseError: null,
      parsedIR: null,
      render: vi.fn(),
      renderAsync: vi.fn().mockResolvedValue({ content: "# SPEC", format: "OPENSPEC" }),
      isRendering: false,
      renderError: null,
      renderedContent: { content: "# SPEC", format: "OPENSPEC" },
      convert: vi.fn(),
      convertAsync: vi.fn(),
      isConverting: false,
      convertError: null,
      convertedContent: null,
      detect: vi.fn(),
      detectAsync: vi.fn(),
      isDetecting: false,
      detectError: null,
      detectedFormat: null,
      isLoading: false,
    });
  });

  describe("Page Layout", () => {
    it("should render page title", () => {
      renderWithProviders(<SpecConverterPage />);

      expect(screen.getByText(/spec converter/i)).toBeInTheDocument();
    });

    it("should render metadata panel", () => {
      renderWithProviders(<SpecConverterPage />);

      expect(screen.getByLabelText(/spec id/i)).toBeInTheDocument();
    });

    it("should render requirements editor", () => {
      renderWithProviders(<SpecConverterPage />);

      expect(screen.getByText(/requirements/i)).toBeInTheDocument();
    });

    it("should render acceptance criteria editor", () => {
      renderWithProviders(<SpecConverterPage />);

      expect(screen.getByText(/acceptance criteria/i)).toBeInTheDocument();
    });

    it("should render preview panel", () => {
      renderWithProviders(<SpecConverterPage />);

      expect(screen.getByText(/preview/i)).toBeInTheDocument();
    });

    it("should render template selector", () => {
      renderWithProviders(<SpecConverterPage />);

      expect(screen.getByText(/templates/i)).toBeInTheDocument();
    });

    it("should render action buttons", () => {
      renderWithProviders(<SpecConverterPage />);

      expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /export/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /validate/i })).toBeInTheDocument();
    });
  });

  describe("Template Selection", () => {
    it("should populate form when template selected", async () => {
      renderWithProviders(<SpecConverterPage />);

      const apiTemplate = screen.getByText(/api endpoint/i).closest("button");
      await userEvent.click(apiTemplate!);

      // Form should be populated with template data
      await waitFor(() => {
        expect(screen.getByDisplayValue(/api endpoint/i)).toBeInTheDocument();
      });
    });
  });

  describe("Form Operations", () => {
    it("should update spec when metadata changes", async () => {
      renderWithProviders(<SpecConverterPage />);

      const titleInput = screen.getByLabelText(/title/i);
      await userEvent.type(titleInput, "New Feature");

      expect(titleInput).toHaveValue("New Feature");
    });

    it("should add requirement when button clicked", async () => {
      renderWithProviders(<SpecConverterPage />);

      const addButton = screen.getByRole("button", { name: /add requirement/i });
      await userEvent.click(addButton);

      // Should have at least one requirement item
      await waitFor(() => {
        expect(screen.getByText(/REQ-/i)).toBeInTheDocument();
      });
    });

    it("should update preview when spec changes", async () => {
      renderWithProviders(<SpecConverterPage />);

      const titleInput = screen.getByLabelText(/title/i);
      await userEvent.type(titleInput, "Updated Title");

      // Preview should update
      await waitFor(() => {
        expect(mockUseSpecConverter().renderAsync).toHaveBeenCalled();
      });
    });
  });

  describe("Import/Export", () => {
    it("should show import dialog when import clicked", async () => {
      renderWithProviders(<SpecConverterPage />);

      const importButton = screen.getByRole("button", { name: /import/i });
      await userEvent.click(importButton);

      expect(screen.getByText(/import spec/i)).toBeInTheDocument();
      expect(screen.getByRole("textbox", { name: /paste content/i })).toBeInTheDocument();
    });

    it("should parse imported content", async () => {
      const parseAsync = vi.fn().mockResolvedValue(createMockSpecIR({ title: "Imported" }));
      mockUseSpecConverter.mockReturnValue({
        ...mockUseSpecConverter(),
        parseAsync,
      } as any);

      renderWithProviders(<SpecConverterPage />);

      const importButton = screen.getByRole("button", { name: /import/i });
      await userEvent.click(importButton);

      const textarea = screen.getByRole("textbox", { name: /paste content/i });
      await userEvent.type(textarea, "Feature: Test");

      const confirmButton = screen.getByRole("button", { name: /import/i });
      await userEvent.click(confirmButton);

      expect(parseAsync).toHaveBeenCalled();
    });

    it("should download spec when export clicked", async () => {
      const mockCreateObjectURL = vi.fn(() => "blob:url");
      global.URL.createObjectURL = mockCreateObjectURL;

      renderWithProviders(<SpecConverterPage />);

      const exportButton = screen.getByRole("button", { name: /export/i });
      await userEvent.click(exportButton);

      expect(mockCreateObjectURL).toHaveBeenCalled();
    });
  });

  describe("Validation", () => {
    it("should show validation results when validate clicked", async () => {
      renderWithProviders(<SpecConverterPage />);

      const validateButton = screen.getByRole("button", { name: /validate/i });
      await userEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText(/validation/i)).toBeInTheDocument();
      });
    });

    it("should highlight missing required fields", async () => {
      renderWithProviders(<SpecConverterPage />);

      // Clear required field
      const titleInput = screen.getByLabelText(/title/i);
      await userEvent.clear(titleInput);

      const validateButton = screen.getByRole("button", { name: /validate/i });
      await userEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText(/title is required/i)).toBeInTheDocument();
      });
    });
  });

  describe("Keyboard Shortcuts", () => {
    it("should save on Ctrl+S", async () => {
      const consoleSpy = vi.spyOn(console, "log").mockImplementation(() => {});
      renderWithProviders(<SpecConverterPage />);

      await userEvent.keyboard("{Control>}s{/Control}");

      // Save action should be triggered
      expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining("save"));
      consoleSpy.mockRestore();
    });
  });

  describe("Accessibility", () => {
    it("should have proper heading structure", () => {
      renderWithProviders(<SpecConverterPage />);

      const h1 = screen.getByRole("heading", { level: 1 });
      expect(h1).toHaveTextContent(/spec converter/i);
    });

    it("should have proper form labels", () => {
      renderWithProviders(<SpecConverterPage />);

      // All inputs should have associated labels
      const inputs = screen.getAllByRole("textbox");
      inputs.forEach((input) => {
        expect(input).toHaveAccessibleName();
      });
    });

    it("should be keyboard navigable", async () => {
      renderWithProviders(<SpecConverterPage />);

      const firstInput = screen.getByLabelText(/spec id/i);
      firstInput.focus();

      await userEvent.tab();

      // Should move to next focusable element
      expect(document.activeElement).not.toBe(firstInput);
    });
  });
});
