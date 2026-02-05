/**
 * RequirementsEditor Component Tests
 * Sprint 155 Day 3 - Track 1: Visual Editor Integration
 *
 * TDD RED Phase: Write failing tests first
 *
 * Test Coverage:
 * - Renders list of requirements
 * - Add new requirement
 * - Remove requirement
 * - Reorder requirements
 * - Empty state handling
 */

import { render, screen, fireEvent, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { RequirementsEditor } from "@/components/spec-converter/RequirementsEditor";
import { SpecRequirement } from "@/hooks/useSpecConverter";

describe("RequirementsEditor", () => {
  const mockOnChange = vi.fn();

  const defaultRequirements: SpecRequirement[] = [
    {
      id: "REQ-001",
      title: "User Authentication",
      priority: "P0",
      tier: ["STANDARD"],
      given: "A user with valid credentials",
      when: "They submit the login form",
      then: "They should be authenticated",
      acceptance_criteria: ["Password validated", "Session created"],
    },
    {
      id: "REQ-002",
      title: "Password Reset",
      priority: "P1",
      tier: ["STANDARD", "PROFESSIONAL"],
      given: "A user who forgot their password",
      when: "They request a password reset",
      then: "They should receive a reset email",
      acceptance_criteria: ["Email sent", "Token valid for 24h"],
    },
    {
      id: "REQ-003",
      title: "Session Management",
      priority: "P2",
      tier: ["PROFESSIONAL"],
      given: "An authenticated user",
      when: "They are inactive for 30 minutes",
      then: "Their session should expire",
      acceptance_criteria: ["Auto logout", "Warning shown"],
    },
  ];

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  describe("Rendering", () => {
    it("renders all requirements", () => {
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText("REQ-001")).toBeInTheDocument();
      expect(screen.getByText("REQ-002")).toBeInTheDocument();
      expect(screen.getByText("REQ-003")).toBeInTheDocument();
    });

    it("displays requirement titles", () => {
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText("User Authentication")).toBeInTheDocument();
      expect(screen.getByText("Password Reset")).toBeInTheDocument();
      expect(screen.getByText("Session Management")).toBeInTheDocument();
    });

    it("shows requirement count in header", () => {
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText(/3 requirements/i)).toBeInTheDocument();
    });

    it("displays priority badges", () => {
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      // Multiple elements may have "P0" text (badge + select options)
      expect(screen.getAllByText("P0").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("P1").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("P2").length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("Empty State", () => {
    it("shows empty state when no requirements", () => {
      render(<RequirementsEditor requirements={[]} onChange={mockOnChange} />);

      expect(screen.getByText(/no requirements yet/i)).toBeInTheDocument();
    });

    it("shows add button in empty state", () => {
      render(<RequirementsEditor requirements={[]} onChange={mockOnChange} />);

      // Should have button in empty state (may have header button too)
      const addButtons = screen.getAllByRole("button", { name: /add.*requirement/i });
      expect(addButtons.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("Add Requirement", () => {
    it("shows add requirement button", () => {
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      expect(
        screen.getByRole("button", { name: /add requirement/i })
      ).toBeInTheDocument();
    });

    it("calls onChange with new requirement when add button clicked", async () => {
      const user = userEvent.setup();
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      const addButton = screen.getByRole("button", { name: /add requirement/i });
      await user.click(addButton);

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.arrayContaining([
          ...defaultRequirements,
          expect.objectContaining({
            id: expect.stringMatching(/^REQ-/),
            title: "",
            priority: "P1",
          }),
        ])
      );
    });

    it("generates unique ID for new requirement", async () => {
      const user = userEvent.setup();
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      const addButton = screen.getByRole("button", { name: /add requirement/i });
      await user.click(addButton);

      const newRequirements = mockOnChange.mock.calls[0][0];
      const newReq = newRequirements[newRequirements.length - 1];

      // Should have a unique ID not matching existing ones
      expect(newReq.id).not.toBe("REQ-001");
      expect(newReq.id).not.toBe("REQ-002");
      expect(newReq.id).not.toBe("REQ-003");
    });
  });

  describe("Remove Requirement", () => {
    it("calls onChange without removed requirement", async () => {
      const user = userEvent.setup();
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      // Find and click delete button for first requirement
      const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
      await user.click(deleteButtons[0]);

      expect(mockOnChange).toHaveBeenCalledWith([
        defaultRequirements[1],
        defaultRequirements[2],
      ]);
    });

    it("hides delete buttons when canDelete is false", () => {
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
          canDelete={false}
        />
      );

      expect(
        screen.queryByRole("button", { name: /delete/i })
      ).not.toBeInTheDocument();
    });

    it("shows confirmation before deleting if confirmDelete is true", async () => {
      const user = userEvent.setup();
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
          confirmDelete
        />
      );

      const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
      await user.click(deleteButtons[0]);

      // Should show confirmation dialog
      expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    });
  });

  describe("Update Requirement", () => {
    it("calls onChange when requirement is updated", async () => {
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      // Expand first requirement to edit
      const expandButtons = screen.getAllByText("REQ-001");
      fireEvent.click(expandButtons[0]);

      // Find and change title
      const titleInput = screen.getByDisplayValue("User Authentication");
      fireEvent.change(titleInput, { target: { value: "New Title" } });

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({ id: "REQ-001", title: "New Title" }),
        ])
      );
    });
  });

  describe("Reorder Requirements", () => {
    it("shows move up/down buttons", () => {
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      expect(screen.getAllByRole("button", { name: /move up/i })).toHaveLength(2); // Not on first
      expect(screen.getAllByRole("button", { name: /move down/i })).toHaveLength(2); // Not on last
    });

    it("disables move up on first requirement", () => {
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      // First item shouldn't have move up button
      const firstItem = screen.getByText("REQ-001").closest("[data-testid]");
      if (firstItem) {
        const moveUpBtn = within(firstItem).queryByRole("button", {
          name: /move up/i,
        });
        expect(moveUpBtn).toBeNull();
      }
    });

    it("disables move down on last requirement", () => {
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      // Last item shouldn't have move down button
      const lastItem = screen.getByText("REQ-003").closest("[data-testid]");
      if (lastItem) {
        const moveDownBtn = within(lastItem).queryByRole("button", {
          name: /move down/i,
        });
        expect(moveDownBtn).toBeNull();
      }
    });

    it("moves requirement up when move up clicked", async () => {
      const user = userEvent.setup();
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      // Click move up on second requirement
      const moveUpButtons = screen.getAllByRole("button", { name: /move up/i });
      await user.click(moveUpButtons[0]); // First move up is on second item

      expect(mockOnChange).toHaveBeenCalledWith([
        defaultRequirements[1], // Now first
        defaultRequirements[0], // Now second
        defaultRequirements[2],
      ]);
    });

    it("moves requirement down when move down clicked", async () => {
      const user = userEvent.setup();
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      // Click move down on first requirement
      const moveDownButtons = screen.getAllByRole("button", {
        name: /move down/i,
      });
      await user.click(moveDownButtons[0]);

      expect(mockOnChange).toHaveBeenCalledWith([
        defaultRequirements[1], // Now first
        defaultRequirements[0], // Now second
        defaultRequirements[2],
      ]);
    });
  });

  describe("Collapse/Expand", () => {
    it("starts with all requirements collapsed by default", () => {
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      // BDD fields should not be visible when collapsed
      const bodies = screen.getAllByTestId(/requirement-body/);
      bodies.forEach((body) => {
        expect(body).toHaveAttribute("data-collapsed", "true");
      });
    });

    it("can expand all requirements", async () => {
      const user = userEvent.setup();
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
        />
      );

      const expandAllButton = screen.getByRole("button", { name: /expand all/i });
      await user.click(expandAllButton);

      const bodies = screen.getAllByTestId(/requirement-body/);
      bodies.forEach((body) => {
        expect(body).toHaveAttribute("data-collapsed", "false");
      });
    });

    it("can collapse all requirements", async () => {
      const user = userEvent.setup();
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
          defaultExpanded
        />
      );

      const collapseAllButton = screen.getByRole("button", {
        name: /collapse all/i,
      });
      await user.click(collapseAllButton);

      const bodies = screen.getAllByTestId(/requirement-body/);
      bodies.forEach((body) => {
        expect(body).toHaveAttribute("data-collapsed", "true");
      });
    });
  });

  describe("Readonly Mode", () => {
    it("hides add button in readonly mode", () => {
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
          readonly
        />
      );

      expect(
        screen.queryByRole("button", { name: /add requirement/i })
      ).not.toBeInTheDocument();
    });

    it("hides delete buttons in readonly mode", () => {
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
          readonly
        />
      );

      expect(
        screen.queryByRole("button", { name: /delete/i })
      ).not.toBeInTheDocument();
    });

    it("hides reorder buttons in readonly mode", () => {
      render(
        <RequirementsEditor
          requirements={defaultRequirements}
          onChange={mockOnChange}
          readonly
        />
      );

      expect(
        screen.queryByRole("button", { name: /move up/i })
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /move down/i })
      ).not.toBeInTheDocument();
    });
  });

  describe("Validation", () => {
    it("shows validation errors when showValidation is true", () => {
      const invalidRequirements = [
        {
          ...defaultRequirements[0],
          given: "",
          when: "",
          then: "",
        },
      ];

      render(
        <RequirementsEditor
          requirements={invalidRequirements}
          onChange={mockOnChange}
          showValidation
          defaultExpanded
        />
      );

      expect(screen.getByText(/given is required/i)).toBeInTheDocument();
    });

    it("shows count of invalid requirements", () => {
      const invalidRequirements = [
        { ...defaultRequirements[0], given: "" },
        { ...defaultRequirements[1], when: "" },
        defaultRequirements[2], // Valid
      ];

      render(
        <RequirementsEditor
          requirements={invalidRequirements}
          onChange={mockOnChange}
          showValidation
        />
      );

      expect(screen.getByText(/2 invalid/i)).toBeInTheDocument();
    });
  });
});
