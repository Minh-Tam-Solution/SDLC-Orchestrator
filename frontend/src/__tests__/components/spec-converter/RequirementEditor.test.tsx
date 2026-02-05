/**
 * RequirementEditor Component Tests
 * Sprint 155 Day 2 - Track 1: Visual Editor Integration
 *
 * TDD RED Phase: Write failing tests first
 *
 * Test Coverage:
 * - Renders all BDD fields (given, when, then)
 * - Handles priority selection
 * - Multi-select for tier
 * - User story field
 * - Acceptance criteria list
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { RequirementEditor } from "@/components/spec-converter/RequirementEditor";
import { SpecRequirement, Priority } from "@/hooks/useSpecConverter";

describe("RequirementEditor", () => {
  const mockOnChange = vi.fn();
  const mockOnDelete = vi.fn();

  const defaultRequirement: SpecRequirement = {
    id: "REQ-001",
    title: "User Authentication",
    priority: "P0",
    tier: ["STANDARD", "PROFESSIONAL"],
    given: "A user with valid credentials",
    when: "They submit the login form",
    then: "They should be authenticated",
    user_story: "As a user, I want to login so that I can access my account",
    acceptance_criteria: ["Password must be validated", "Session must be created"],
  };

  beforeEach(() => {
    mockOnChange.mockClear();
    mockOnDelete.mockClear();
  });

  describe("Rendering", () => {
    it("renders all BDD fields", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByLabelText(/given/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/when/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/then/i)).toBeInTheDocument();
    });

    it("displays current requirement values", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByDisplayValue("User Authentication")).toBeInTheDocument();
      expect(screen.getByDisplayValue("A user with valid credentials")).toBeInTheDocument();
      expect(screen.getByDisplayValue("They submit the login form")).toBeInTheDocument();
      expect(screen.getByDisplayValue("They should be authenticated")).toBeInTheDocument();
    });

    it("displays requirement ID as header", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText("REQ-001")).toBeInTheDocument();
    });

    it("displays user story field", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByLabelText(/user story/i)).toBeInTheDocument();
      expect(
        screen.getByDisplayValue(/As a user, I want to login/i)
      ).toBeInTheDocument();
    });

    it("displays acceptance criteria list", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText("Password must be validated")).toBeInTheDocument();
      expect(screen.getByText("Session must be created")).toBeInTheDocument();
    });
  });

  describe("BDD Field Changes", () => {
    it("calls onChange when given is changed", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      const givenInput = screen.getByLabelText(/given/i);
      fireEvent.change(givenInput, {
        target: { value: "A new user without credentials" },
      });

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({ given: "A new user without credentials" })
      );
    });

    it("calls onChange when when is changed", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      const whenInput = screen.getByLabelText(/when/i);
      fireEvent.change(whenInput, {
        target: { value: "They click the sign up button" },
      });

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({ when: "They click the sign up button" })
      );
    });

    it("calls onChange when then is changed", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      const thenInput = screen.getByLabelText(/then/i);
      fireEvent.change(thenInput, {
        target: { value: "They should see a success message" },
      });

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({ then: "They should see a success message" })
      );
    });
  });

  describe("Priority Selection", () => {
    it("displays all priority options", async () => {
      const user = userEvent.setup();
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      const prioritySelect = screen.getByLabelText(/priority/i);
      await user.click(prioritySelect);

      expect(screen.getByRole("option", { name: "P0" })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: "P1" })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: "P2" })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: "P3" })).toBeInTheDocument();
    });

    it("shows current priority selection", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      const prioritySelect = screen.getByLabelText(/priority/i);
      expect(prioritySelect).toHaveValue("P0");
    });

    it("calls onChange when priority is changed", async () => {
      const user = userEvent.setup();
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      const prioritySelect = screen.getByLabelText(/priority/i);
      await user.selectOptions(prioritySelect, "P2");

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({ priority: "P2" })
      );
    });
  });

  describe("Tier Multi-Select", () => {
    it("displays current tier selection", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      const standardCheckbox = screen.getByRole("checkbox", { name: /standard/i });
      const professionalCheckbox = screen.getByRole("checkbox", {
        name: /professional/i,
      });

      expect(standardCheckbox).toBeChecked();
      expect(professionalCheckbox).toBeChecked();
    });

    it("allows selecting multiple tiers", async () => {
      const user = userEvent.setup();
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      const enterpriseCheckbox = screen.getByRole("checkbox", {
        name: /enterprise/i,
      });
      await user.click(enterpriseCheckbox);

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          tier: expect.arrayContaining(["STANDARD", "PROFESSIONAL", "ENTERPRISE"]),
        })
      );
    });
  });

  describe("Acceptance Criteria", () => {
    it("allows adding a new acceptance criterion", async () => {
      const user = userEvent.setup();
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      const acInput = screen.getByPlaceholderText(/add acceptance criterion/i);
      await user.type(acInput, "Token must be returned");
      await user.keyboard("{Enter}");

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          acceptance_criteria: expect.arrayContaining([
            "Password must be validated",
            "Session must be created",
            "Token must be returned",
          ]),
        })
      );
    });

    it("allows removing an acceptance criterion", async () => {
      const user = userEvent.setup();
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      // Find and click remove button for first criterion
      const removeButtons = screen.getAllByRole("button", { name: /remove/i });
      await user.click(removeButtons[0]);

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          acceptance_criteria: ["Session must be created"],
        })
      );
    });
  });

  describe("Delete Requirement", () => {
    it("shows delete button", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByRole("button", { name: /delete/i })).toBeInTheDocument();
    });

    it("calls onDelete when delete button is clicked", async () => {
      const user = userEvent.setup();
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      const deleteButton = screen.getByRole("button", { name: /delete/i });
      await user.click(deleteButton);

      expect(mockOnDelete).toHaveBeenCalledWith("REQ-001");
    });

    it("hides delete button when canDelete is false", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
          canDelete={false}
        />
      );

      expect(
        screen.queryByRole("button", { name: /delete/i })
      ).not.toBeInTheDocument();
    });
  });

  describe("Collapsible State", () => {
    it("starts expanded by default", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      // Check body is not collapsed via data attribute
      const body = screen.getByTestId("requirement-body-REQ-001");
      expect(body).toHaveAttribute("data-collapsed", "false");
    });

    it("can start collapsed", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
          defaultCollapsed
        />
      );

      // Check body is collapsed via data attribute
      const body = screen.getByTestId("requirement-body-REQ-001");
      expect(body).toHaveAttribute("data-collapsed", "true");
    });

    it("toggles collapse state on header click", async () => {
      const user = userEvent.setup();
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
        />
      );

      const body = screen.getByTestId("requirement-body-REQ-001");

      // Initially expanded
      expect(body).toHaveAttribute("data-collapsed", "false");

      // Click to collapse
      const header = screen.getByText("REQ-001");
      await user.click(header);

      // Should now be collapsed
      expect(body).toHaveAttribute("data-collapsed", "true");
    });
  });

  describe("Validation", () => {
    it("shows error when given is empty", () => {
      const invalidRequirement = { ...defaultRequirement, given: "" };
      render(
        <RequirementEditor
          requirement={invalidRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
          showValidation
        />
      );

      expect(screen.getByText(/given is required/i)).toBeInTheDocument();
    });

    it("shows error when when is empty", () => {
      const invalidRequirement = { ...defaultRequirement, when: "" };
      render(
        <RequirementEditor
          requirement={invalidRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
          showValidation
        />
      );

      expect(screen.getByText(/when is required/i)).toBeInTheDocument();
    });

    it("shows error when then is empty", () => {
      const invalidRequirement = { ...defaultRequirement, then: "" };
      render(
        <RequirementEditor
          requirement={invalidRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
          showValidation
        />
      );

      expect(screen.getByText(/then is required/i)).toBeInTheDocument();
    });
  });

  describe("Readonly Mode", () => {
    it("disables all inputs when readonly", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
          readonly
        />
      );

      expect(screen.getByLabelText(/given/i)).toHaveAttribute("readonly");
      expect(screen.getByLabelText(/when/i)).toHaveAttribute("readonly");
      expect(screen.getByLabelText(/then/i)).toHaveAttribute("readonly");
    });

    it("hides add/remove buttons in readonly mode", () => {
      render(
        <RequirementEditor
          requirement={defaultRequirement}
          onChange={mockOnChange}
          onDelete={mockOnDelete}
          readonly
        />
      );

      expect(
        screen.queryByPlaceholderText(/add acceptance criterion/i)
      ).not.toBeInTheDocument();
    });
  });
});
