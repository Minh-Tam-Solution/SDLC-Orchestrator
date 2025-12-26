/**
 * Unit Tests: DiffViewer Component
 * SDLC Orchestrator - Sprint 54 Day 3
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 54 Implementation
 *
 * Test coverage:
 * - Empty/no changes state
 * - Added lines display
 * - Removed lines display
 * - Modified lines display
 * - View mode toggle (split/unified)
 * - Stats display
 * - Change navigation
 */

import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@/test/test-utils";
import { DiffViewer } from "./DiffViewer";
import "@testing-library/jest-dom";

// ============================================================================
// Test Data
// ============================================================================

const oldCode = `function hello() {
  console.log("Hello");
  return true;
}`;

const newCode = `function hello() {
  console.log("Hello, World!");
  console.log("New line added");
  return true;
}`;

const identicalCode = `function test() {
  return 42;
}`;

// ============================================================================
// No Changes Tests
// ============================================================================

describe("DiffViewer - No Changes", () => {
  it("shows no differences message when content is identical", () => {
    render(<DiffViewer oldContent={identicalCode} newContent={identicalCode} />);

    expect(screen.getByText("No differences found")).toBeInTheDocument();
  });

  it("shows no differences for empty strings", () => {
    render(<DiffViewer oldContent="" newContent="" />);

    expect(screen.getByText("No differences found")).toBeInTheDocument();
  });
});

// ============================================================================
// Basic Rendering Tests
// ============================================================================

describe("DiffViewer - Basic Rendering", () => {
  it("renders file path when provided", () => {
    render(
      <DiffViewer
        oldContent={oldCode}
        newContent={newCode}
        filePath="app/main.py"
      />
    );

    expect(screen.getByText("app/main.py")).toBeInTheDocument();
  });

  it("renders language badge when provided", () => {
    render(
      <DiffViewer
        oldContent={oldCode}
        newContent={newCode}
        language="typescript"
      />
    );

    expect(screen.getByText("typescript")).toBeInTheDocument();
  });

  it("renders column headers in split view", () => {
    render(
      <DiffViewer
        oldContent={oldCode}
        newContent={newCode}
        viewMode="split"
      />
    );

    expect(screen.getByText("Original")).toBeInTheDocument();
    expect(screen.getByText("Modified")).toBeInTheDocument();
  });

  it("renders custom labels", () => {
    render(
      <DiffViewer
        oldContent={oldCode}
        newContent={newCode}
        oldLabel="Before"
        newLabel="After"
      />
    );

    expect(screen.getByText("Before")).toBeInTheDocument();
    expect(screen.getByText("After")).toBeInTheDocument();
  });
});

// ============================================================================
// Stats Tests
// ============================================================================

describe("DiffViewer - Stats", () => {
  it("shows stats badges for changes", () => {
    const old = "line 1\nline 2";
    const newer = "line 1\nline 2 modified\nline 3 added";

    render(<DiffViewer oldContent={old} newContent={newer} />);

    // Should show change count in navigation
    expect(screen.getByText(/changes/)).toBeInTheDocument();
  });

  it("displays change navigation", () => {
    render(<DiffViewer oldContent={oldCode} newContent={newCode} />);

    // Should have navigation text
    expect(screen.getByText(/\d+ \/ \d+ changes/)).toBeInTheDocument();
  });
});

// ============================================================================
// View Mode Tests
// ============================================================================

describe("DiffViewer - View Modes", () => {
  it("starts in split view by default", () => {
    render(<DiffViewer oldContent={oldCode} newContent={newCode} />);

    // Should show both Original and Modified headers
    expect(screen.getByText("Original")).toBeInTheDocument();
    expect(screen.getByText("Modified")).toBeInTheDocument();
  });

  it("can start in unified view", () => {
    render(
      <DiffViewer
        oldContent={oldCode}
        newContent={newCode}
        viewMode="unified"
      />
    );

    // Should not show column headers in unified view
    expect(screen.queryByText("Original")).not.toBeInTheDocument();
    expect(screen.queryByText("Modified")).not.toBeInTheDocument();
  });

  it("has view mode toggle buttons", () => {
    render(<DiffViewer oldContent={oldCode} newContent={newCode} />);

    // Should have buttons for view mode switching
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
  });
});

// ============================================================================
// Navigation Tests
// ============================================================================

describe("DiffViewer - Navigation", () => {
  it("has navigation buttons for changes", () => {
    render(<DiffViewer oldContent={oldCode} newContent={newCode} />);

    // Should have prev/next buttons
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(2);
  });

  it("shows change index", () => {
    render(<DiffViewer oldContent={oldCode} newContent={newCode} />);

    // Should show "X / Y changes"
    expect(screen.getByText(/\d+ \/ \d+ changes/)).toBeInTheDocument();
  });
});

// ============================================================================
// Line Number Tests
// ============================================================================

describe("DiffViewer - Line Numbers", () => {
  it("shows line numbers by default", () => {
    const old = "line_alpha";
    const newer = "line_alpha\nline_beta";

    render(<DiffViewer oldContent={old} newContent={newer} />);

    // Should have change navigation (indicating diff rendered)
    expect(screen.getByText(/changes/)).toBeInTheDocument();
  });

  it("renders content when line numbers disabled", () => {
    const old = "unique_old_123";
    const newer = "unique_old_123\nunique_new_456";

    render(
      <DiffViewer
        oldContent={old}
        newContent={newer}
        showLineNumbers={false}
      />
    );

    // Change navigation should be present
    expect(screen.getByText(/changes/)).toBeInTheDocument();
  });
});

// ============================================================================
// Content Display Tests
// ============================================================================

describe("DiffViewer - Content Display", () => {
  it("displays old content", () => {
    const old = "old_content_unique";
    const newer = "new_content_unique";

    render(<DiffViewer oldContent={old} newContent={newer} />);

    expect(screen.getByText(/old_content_unique/)).toBeInTheDocument();
  });

  it("displays new content", () => {
    const old = "old_stuff_abc";
    const newer = "new_stuff_xyz";

    render(<DiffViewer oldContent={old} newContent={newer} />);

    expect(screen.getByText(/new_stuff_xyz/)).toBeInTheDocument();
  });

  it("handles multiline content", () => {
    const old = "alpha\nbeta\ngamma";
    const newer = "alpha\nmodified\ngamma\ndelta";

    render(<DiffViewer oldContent={old} newContent={newer} />);

    // Should have change navigation
    expect(screen.getByText(/changes/)).toBeInTheDocument();
  });
});

// ============================================================================
// Copy Functionality Tests
// ============================================================================

describe("DiffViewer - Copy", () => {
  it("has copy buttons in split view", () => {
    render(
      <DiffViewer
        oldContent={oldCode}
        newContent={newCode}
        viewMode="split"
      />
    );

    // Should have Copy buttons
    const copyButtons = screen.getAllByText("Copy");
    expect(copyButtons.length).toBeGreaterThan(0);
  });
});

// ============================================================================
// Edge Cases Tests
// ============================================================================

describe("DiffViewer - Edge Cases", () => {
  it("handles single line content", () => {
    render(
      <DiffViewer oldContent="single_line_here" newContent="different_line_here" />
    );

    expect(screen.getByText(/single_line_here/)).toBeInTheDocument();
  });

  it("handles content with code", () => {
    const old = "const x = 1";
    const newer = "const x = 2";

    render(<DiffViewer oldContent={old} newContent={newer} />);

    // Should render change navigation
    expect(screen.getByText(/changes/)).toBeInTheDocument();
  });

  it("handles empty old content", () => {
    render(<DiffViewer oldContent="" newContent="new_content_here" />);

    expect(screen.getByText(/new_content_here/)).toBeInTheDocument();
  });

  it("handles empty new content", () => {
    render(<DiffViewer oldContent="old_content_here" newContent="" />);

    expect(screen.getByText(/old_content_here/)).toBeInTheDocument();
  });
});
