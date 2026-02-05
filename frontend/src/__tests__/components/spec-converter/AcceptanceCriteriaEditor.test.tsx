/**
 * AcceptanceCriteriaEditor Component Tests
 * Sprint 155 Day 3 - Track 1: Visual Editor Integration
 *
 * TDD RED Phase: Write failing tests first
 *
 * Test Coverage:
 * - Renders list of acceptance criteria
 * - Add new criterion
 * - Remove criterion
 * - Edit criterion
 * - Validation
 */

import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AcceptanceCriteriaEditor } from "@/components/spec-converter/AcceptanceCriteriaEditor";
import { AcceptanceCriterion } from "@/hooks/useSpecConverter";

describe("AcceptanceCriteriaEditor", () => {
  const mockOnChange = vi.fn();

  const defaultCriteria: AcceptanceCriterion[] = [
    {
      id: "AC-001",
      scenario: "Valid login",
      given: "A registered user",
      when: "They enter correct credentials",
      then: "They are logged in",
      tier: ["STANDARD"],
      testable: true,
    },
    {
      id: "AC-002",
      scenario: "Invalid login",
      given: "A registered user",
      when: "They enter wrong password",
      then: "They see an error message",
      tier: ["STANDARD"],
      testable: true,
    },
  ];

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  describe("Rendering", () => {
    it("renders all acceptance criteria", () => {
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText("Valid login")).toBeInTheDocument();
      expect(screen.getByText("Invalid login")).toBeInTheDocument();
    });

    it("shows criteria count", () => {
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText(/2 criteria/i)).toBeInTheDocument();
    });

    it("displays BDD fields for each criterion", () => {
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
          defaultExpanded
        />
      );

      // Both criteria have same "given" value, so use getAllBy
      const givenInputs = screen.getAllByDisplayValue("A registered user");
      expect(givenInputs).toHaveLength(2);
      expect(screen.getByDisplayValue("They enter correct credentials")).toBeInTheDocument();
      expect(screen.getByDisplayValue("They are logged in")).toBeInTheDocument();
    });

    it("shows testable indicator", () => {
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
        />
      );

      // Both criteria are testable
      const testableIndicators = screen.getAllByText(/testable/i);
      expect(testableIndicators.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe("Empty State", () => {
    it("shows empty state when no criteria", () => {
      render(<AcceptanceCriteriaEditor criteria={[]} onChange={mockOnChange} />);

      expect(screen.getByText(/no acceptance criteria/i)).toBeInTheDocument();
    });

    it("shows add button in empty state", () => {
      render(<AcceptanceCriteriaEditor criteria={[]} onChange={mockOnChange} />);

      // Should have button in empty state (may have header button too)
      const addButtons = screen.getAllByRole("button", { name: /add.*criterion/i });
      expect(addButtons.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("Add Criterion", () => {
    it("shows add criterion button", () => {
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
        />
      );

      expect(
        screen.getByRole("button", { name: /add criterion/i })
      ).toBeInTheDocument();
    });

    it("calls onChange with new criterion when add button clicked", async () => {
      const user = userEvent.setup();
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
        />
      );

      const addButton = screen.getByRole("button", { name: /add criterion/i });
      await user.click(addButton);

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.arrayContaining([
          ...defaultCriteria,
          expect.objectContaining({
            id: expect.stringMatching(/^AC-/),
            scenario: "",
            testable: true,
          }),
        ])
      );
    });
  });

  describe("Remove Criterion", () => {
    it("calls onChange without removed criterion", async () => {
      const user = userEvent.setup();
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
        />
      );

      const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
      await user.click(deleteButtons[0]);

      expect(mockOnChange).toHaveBeenCalledWith([defaultCriteria[1]]);
    });

    it("hides delete buttons in readonly mode", () => {
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
          readonly
        />
      );

      expect(
        screen.queryByRole("button", { name: /delete/i })
      ).not.toBeInTheDocument();
    });
  });

  describe("Update Criterion", () => {
    it("calls onChange when scenario is updated", () => {
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
          defaultExpanded
        />
      );

      const scenarioInputs = screen.getAllByLabelText(/scenario/i);
      fireEvent.change(scenarioInputs[0], {
        target: { value: "Updated scenario" },
      });

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            id: "AC-001",
            scenario: "Updated scenario",
          }),
        ])
      );
    });

    it("calls onChange when given is updated", () => {
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
          defaultExpanded
        />
      );

      const givenInputs = screen.getAllByLabelText(/^given$/i);
      fireEvent.change(givenInputs[0], {
        target: { value: "New given condition" },
      });

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            id: "AC-001",
            given: "New given condition",
          }),
        ])
      );
    });

    it("can toggle testable status", async () => {
      const user = userEvent.setup();
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
          defaultExpanded
        />
      );

      const testableCheckboxes = screen.getAllByRole("checkbox", {
        name: /testable/i,
      });
      await user.click(testableCheckboxes[0]);

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            id: "AC-001",
            testable: false,
          }),
        ])
      );
    });
  });

  describe("Tier Selection", () => {
    it("displays current tier selection", () => {
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
          defaultExpanded
        />
      );

      const standardCheckboxes = screen.getAllByRole("checkbox", {
        name: /standard/i,
      });
      expect(standardCheckboxes[0]).toBeChecked();
    });

    it("can update tier selection", async () => {
      const user = userEvent.setup();
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
          defaultExpanded
        />
      );

      const professionalCheckboxes = screen.getAllByRole("checkbox", {
        name: /professional/i,
      });
      await user.click(professionalCheckboxes[0]);

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            id: "AC-001",
            tier: expect.arrayContaining(["STANDARD", "PROFESSIONAL"]),
          }),
        ])
      );
    });
  });

  describe("Validation", () => {
    it("shows error when scenario is empty", () => {
      const invalidCriteria = [{ ...defaultCriteria[0], scenario: "" }];
      render(
        <AcceptanceCriteriaEditor
          criteria={invalidCriteria}
          onChange={mockOnChange}
          showValidation
          defaultExpanded
        />
      );

      expect(screen.getByText(/scenario is required/i)).toBeInTheDocument();
    });

    it("shows error when given is empty", () => {
      const invalidCriteria = [{ ...defaultCriteria[0], given: "" }];
      render(
        <AcceptanceCriteriaEditor
          criteria={invalidCriteria}
          onChange={mockOnChange}
          showValidation
          defaultExpanded
        />
      );

      expect(screen.getByText(/given is required/i)).toBeInTheDocument();
    });

    it("shows validation summary with count", () => {
      const invalidCriteria = [
        { ...defaultCriteria[0], scenario: "" },
        defaultCriteria[1],
      ];
      render(
        <AcceptanceCriteriaEditor
          criteria={invalidCriteria}
          onChange={mockOnChange}
          showValidation
        />
      );

      expect(screen.getByText(/1 invalid/i)).toBeInTheDocument();
    });
  });

  describe("Readonly Mode", () => {
    it("hides add button in readonly mode", () => {
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
          readonly
        />
      );

      expect(
        screen.queryByRole("button", { name: /add criterion/i })
      ).not.toBeInTheDocument();
    });

    it("makes inputs readonly", () => {
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
          readonly
          defaultExpanded
        />
      );

      const scenarioInputs = screen.getAllByLabelText(/scenario/i);
      expect(scenarioInputs[0]).toHaveAttribute("readonly");
    });
  });

  describe("Collapse/Expand", () => {
    it("starts collapsed by default", () => {
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
        />
      );

      const bodies = screen.getAllByTestId(/criterion-body/);
      bodies.forEach((body) => {
        expect(body).toHaveAttribute("data-collapsed", "true");
      });
    });

    it("can expand individual criterion", async () => {
      const user = userEvent.setup();
      render(
        <AcceptanceCriteriaEditor
          criteria={defaultCriteria}
          onChange={mockOnChange}
        />
      );

      // Click on first criterion header
      const headers = screen.getAllByText(/valid login|invalid login/i);
      await user.click(headers[0]);

      const firstBody = screen.getByTestId("criterion-body-AC-001");
      expect(firstBody).toHaveAttribute("data-collapsed", "false");
    });
  });
});
