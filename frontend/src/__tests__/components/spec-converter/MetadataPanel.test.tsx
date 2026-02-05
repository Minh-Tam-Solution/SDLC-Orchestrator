/**
 * MetadataPanel Component Tests
 * Sprint 155 Day 1 - Track 1: Visual Editor Integration
 *
 * TDD RED Phase: Write failing tests first
 *
 * Test Coverage:
 * - Renders all metadata fields correctly
 * - Handles input changes
 * - Multi-select for tier
 * - Array inputs for tags, related_adrs, related_specs
 * - Status select
 * - Validation and error states
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MetadataPanel } from "@/components/spec-converter/MetadataPanel";
import { SpecIR, createEmptySpecIR } from "@/hooks/useSpecConverter";

describe("MetadataPanel", () => {
  const mockOnChange = vi.fn();

  const defaultSpec: SpecIR = {
    spec_id: "SPEC-001",
    title: "Test Specification",
    version: "1.0.0",
    status: "DRAFT",
    tier: ["STANDARD"],
    owner: "test@example.com",
    last_updated: "2026-02-04T10:00:00Z",
    tags: ["auth", "security"],
    related_adrs: ["ADR-001", "ADR-002"],
    related_specs: ["SPEC-002"],
    requirements: [],
    acceptance_criteria: [],
  };

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  describe("Rendering", () => {
    it("renders all metadata fields", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      // Check for field labels (some use label, some use span)
      expect(screen.getByLabelText(/spec id/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/version/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/status/i)).toBeInTheDocument();
      expect(screen.getByText("Tier")).toBeInTheDocument(); // Tier uses span, not label
      expect(screen.getByLabelText(/owner/i)).toBeInTheDocument();
      expect(screen.getByText(/last updated/i)).toBeInTheDocument();
      expect(screen.getByText("Tags")).toBeInTheDocument();
      expect(screen.getByText(/related adrs/i)).toBeInTheDocument();
      expect(screen.getByText(/related specs/i)).toBeInTheDocument();
    });

    it("displays current spec values", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      expect(screen.getByDisplayValue("SPEC-001")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Test Specification")).toBeInTheDocument();
      expect(screen.getByDisplayValue("1.0.0")).toBeInTheDocument();
      expect(screen.getByDisplayValue("test@example.com")).toBeInTheDocument();
    });

    it("renders spec_id as readonly", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      const specIdInput = screen.getByLabelText(/spec id/i);
      expect(specIdInput).toHaveAttribute("readonly");
    });

    it("displays formatted last_updated date", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      // Should display formatted date, not raw ISO string
      expect(screen.getByText(/feb 4, 2026/i)).toBeInTheDocument();
    });

    it("renders tags as chips", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      expect(screen.getByText("auth")).toBeInTheDocument();
      expect(screen.getByText("security")).toBeInTheDocument();
    });

    it("renders related_adrs as chips", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      expect(screen.getByText("ADR-001")).toBeInTheDocument();
      expect(screen.getByText("ADR-002")).toBeInTheDocument();
    });

    it("renders related_specs as chips", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      expect(screen.getByText("SPEC-002")).toBeInTheDocument();
    });
  });

  describe("Input Changes", () => {
    it("calls onChange when title is changed", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      const titleInput = screen.getByLabelText(/title/i);
      fireEvent.change(titleInput, { target: { value: "New Title" } });

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({ title: "New Title" })
      );
    });

    it("calls onChange when version is changed", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      const versionInput = screen.getByLabelText(/version/i);
      fireEvent.change(versionInput, { target: { value: "2.0.0" } });

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({ version: "2.0.0" })
      );
    });

    it("calls onChange when owner is changed", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      const ownerInput = screen.getByLabelText(/owner/i);
      fireEvent.change(ownerInput, { target: { value: "new@example.com" } });

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({ owner: "new@example.com" })
      );
    });
  });

  describe("Status Select", () => {
    it("displays all status options", async () => {
      const user = userEvent.setup();
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      const statusSelect = screen.getByLabelText(/status/i);
      await user.click(statusSelect);

      expect(screen.getByRole("option", { name: /draft/i })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: /proposed/i })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: /approved/i })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: /deprecated/i })).toBeInTheDocument();
    });

    it("calls onChange when status is changed", async () => {
      const user = userEvent.setup();
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      const statusSelect = screen.getByLabelText(/status/i);
      await user.selectOptions(statusSelect, "APPROVED");

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({ status: "APPROVED" })
      );
    });
  });

  describe("Tier Multi-Select", () => {
    it("displays current tier selection", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      // Should show STANDARD is selected
      const tierSection = screen.getByText(/tier/i).closest("div");
      expect(tierSection).toHaveTextContent("STANDARD");
    });

    it("allows selecting multiple tiers", async () => {
      const user = userEvent.setup();
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      // Click to add PROFESSIONAL tier
      const professionalCheckbox = screen.getByRole("checkbox", { name: /professional/i });
      await user.click(professionalCheckbox);

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({ tier: expect.arrayContaining(["STANDARD", "PROFESSIONAL"]) })
      );
    });

    it("allows deselecting tiers", async () => {
      const user = userEvent.setup();
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      // Click to remove STANDARD tier
      const standardCheckbox = screen.getByRole("checkbox", { name: /standard/i });
      await user.click(standardCheckbox);

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({ tier: [] })
      );
    });
  });

  describe("Array Fields (Tags, Related ADRs, Related Specs)", () => {
    it("allows adding a new tag", async () => {
      const user = userEvent.setup();
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      const tagInput = screen.getByPlaceholderText(/add tag/i);
      await user.type(tagInput, "new-tag");
      await user.keyboard("{Enter}");

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          tags: expect.arrayContaining(["auth", "security", "new-tag"]),
        })
      );
    });

    it("allows removing a tag", async () => {
      const user = userEvent.setup();
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      // Find and click the remove button for "auth" tag
      const authTag = screen.getByText("auth").closest("span");
      const removeButton = authTag?.querySelector("button");
      if (removeButton) {
        await user.click(removeButton);
      }

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          tags: ["security"],
        })
      );
    });

    it("allows adding a new related ADR", async () => {
      const user = userEvent.setup();
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      const adrInput = screen.getByPlaceholderText(/add adr/i);
      await user.type(adrInput, "ADR-003");
      await user.keyboard("{Enter}");

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          related_adrs: expect.arrayContaining(["ADR-001", "ADR-002", "ADR-003"]),
        })
      );
    });

    it("allows adding a new related spec", async () => {
      const user = userEvent.setup();
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      const specInput = screen.getByPlaceholderText(/add spec/i);
      await user.type(specInput, "SPEC-003");
      await user.keyboard("{Enter}");

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          related_specs: expect.arrayContaining(["SPEC-002", "SPEC-003"]),
        })
      );
    });

    it("prevents duplicate tags", async () => {
      const user = userEvent.setup();
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      const tagInput = screen.getByPlaceholderText(/add tag/i);
      await user.type(tagInput, "auth"); // Already exists
      await user.keyboard("{Enter}");

      // Should not add duplicate
      expect(mockOnChange).not.toHaveBeenCalledWith(
        expect.objectContaining({
          tags: ["auth", "security", "auth"],
        })
      );
    });
  });

  describe("Validation", () => {
    it("shows error when title is empty", async () => {
      const user = userEvent.setup();
      const specWithEmptyTitle = { ...defaultSpec, title: "" };
      render(<MetadataPanel spec={specWithEmptyTitle} onChange={mockOnChange} showValidation />);

      expect(screen.getByText(/title is required/i)).toBeInTheDocument();
    });

    it("shows error when version format is invalid", async () => {
      const user = userEvent.setup();
      const specWithInvalidVersion = { ...defaultSpec, version: "invalid" };
      render(<MetadataPanel spec={specWithInvalidVersion} onChange={mockOnChange} showValidation />);

      expect(screen.getByText(/version must follow semver format/i)).toBeInTheDocument();
    });

    it("shows warning when no tier is selected", () => {
      const specWithNoTier = { ...defaultSpec, tier: [] };
      render(<MetadataPanel spec={specWithNoTier} onChange={mockOnChange} showValidation />);

      expect(screen.getByText(/at least one tier must be selected/i)).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("has accessible labels for all inputs", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      // All inputs should be labeled
      expect(screen.getByLabelText(/spec id/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/version/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/status/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/owner/i)).toBeInTheDocument();
      // Tier checkboxes have individual aria-labels
      expect(screen.getByLabelText("LITE")).toBeInTheDocument();
      expect(screen.getByLabelText("STANDARD")).toBeInTheDocument();
    });

    it("supports keyboard navigation", async () => {
      const user = userEvent.setup();
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} />);

      // Tab through inputs - first element gets focus
      await user.tab();
      expect(document.activeElement).toHaveAttribute("aria-label");
    });
  });

  describe("Loading State", () => {
    it("disables inputs when loading", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} loading />);

      expect(screen.getByLabelText(/title/i)).toBeDisabled();
      expect(screen.getByLabelText(/version/i)).toBeDisabled();
      expect(screen.getByLabelText(/status/i)).toBeDisabled();
      expect(screen.getByLabelText(/owner/i)).toBeDisabled();
    });

    it("shows loading indicator when loading", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} loading />);

      expect(screen.getByRole("progressbar")).toBeInTheDocument();
    });
  });

  describe("Readonly Mode", () => {
    it("makes all fields readonly when readonly prop is true", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} readonly />);

      expect(screen.getByLabelText(/title/i)).toHaveAttribute("readonly");
      expect(screen.getByLabelText(/version/i)).toHaveAttribute("readonly");
      expect(screen.getByLabelText(/owner/i)).toHaveAttribute("readonly");
    });

    it("hides add/remove buttons in readonly mode", () => {
      render(<MetadataPanel spec={defaultSpec} onChange={mockOnChange} readonly />);

      expect(screen.queryByPlaceholderText(/add tag/i)).not.toBeInTheDocument();
      expect(screen.queryByPlaceholderText(/add adr/i)).not.toBeInTheDocument();
    });
  });
});
