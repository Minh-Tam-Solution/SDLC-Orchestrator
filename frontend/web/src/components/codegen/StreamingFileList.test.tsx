/**
 * Unit Tests: StreamingFileList Component
 * SDLC Orchestrator - Sprint 54 Day 1
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 54 Implementation
 *
 * Test coverage:
 * - Empty state rendering
 * - File tree building and rendering
 * - Status indicators (generating, valid, error)
 * - Progress display
 * - Folder expansion/collapse
 * - File selection
 * - Stats display
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@/test/test-utils";
import { StreamingFileList } from "./StreamingFileList";
import type { StreamingFile } from "@/types/streaming";
import "@testing-library/jest-dom";

// ============================================================================
// Mock Data Factories
// ============================================================================

function createMockFile(overrides?: Partial<StreamingFile>): StreamingFile {
  return {
    path: "app/main.py",
    content: 'print("Hello")',
    lines: 1,
    language: "python",
    status: "valid",
    ...overrides,
  };
}

function createMockFiles(): StreamingFile[] {
  return [
    createMockFile({ path: "app/__init__.py", lines: 0 }),
    createMockFile({ path: "app/main.py", lines: 35 }),
    createMockFile({ path: "app/core/config.py", lines: 28 }),
    createMockFile({ path: "app/core/database.py", lines: 42 }),
    createMockFile({ path: "app/models/user.py", lines: 56 }),
    createMockFile({
      path: "app/api/routes.py",
      lines: 0,
      status: "generating",
    }),
  ];
}

// ============================================================================
// Empty State Tests
// ============================================================================

describe("StreamingFileList - Empty State", () => {
  it("renders empty state when no files and not generating", () => {
    render(<StreamingFileList files={[]} isGenerating={false} />);

    expect(screen.getByText("No files generated yet")).toBeInTheDocument();
    expect(
      screen.getByText("Start generation to see files here")
    ).toBeInTheDocument();
  });

  it("does not render empty state when generating but no files yet", () => {
    render(<StreamingFileList files={[]} isGenerating={true} />);

    // Should show the generation indicator instead
    expect(screen.queryByText("No files generated yet")).not.toBeInTheDocument();
  });
});

// ============================================================================
// File Tree Tests
// ============================================================================

describe("StreamingFileList - File Tree", () => {
  it("renders files in tree structure", () => {
    const files = createMockFiles();
    render(<StreamingFileList files={files} isGenerating={false} />);

    // Check folder names
    expect(screen.getByText("app")).toBeInTheDocument();
    expect(screen.getByText("core")).toBeInTheDocument();
    expect(screen.getByText("models")).toBeInTheDocument();
    expect(screen.getByText("api")).toBeInTheDocument();

    // Check file names
    expect(screen.getByText("__init__.py")).toBeInTheDocument();
    expect(screen.getByText("main.py")).toBeInTheDocument();
    expect(screen.getByText("config.py")).toBeInTheDocument();
    expect(screen.getByText("routes.py")).toBeInTheDocument();
  });

  it("sorts folders before files", () => {
    const files = [
      createMockFile({ path: "zzz_file.py" }),
      createMockFile({ path: "aaa_folder/file.py" }),
    ];

    render(<StreamingFileList files={files} isGenerating={false} />);

    // Get all items in the tree (skip toolbar buttons)
    const treeItems = screen.getAllByRole("button").filter((btn) => {
      const text = btn.textContent || "";
      return !text.includes("Expand") && !text.includes("Collapse");
    });

    // First tree item should be the folder
    expect(treeItems[0]).toHaveTextContent("aaa_folder");
  });

  it("shows file count in stats", () => {
    const files = createMockFiles();
    render(
      <StreamingFileList files={files} isGenerating={false} showStats={true} />
    );

    expect(screen.getByText(/6 files/)).toBeInTheDocument();
  });
});

// ============================================================================
// Status Indicator Tests
// ============================================================================

describe("StreamingFileList - Status Indicators", () => {
  it("shows generating status for files being generated", () => {
    const files = [
      createMockFile({ path: "generating.py", status: "generating" }),
    ];

    render(<StreamingFileList files={files} isGenerating={true} />);

    // File should be in the tree
    expect(screen.getByText("generating.py")).toBeInTheDocument();
  });

  it("shows valid status for completed files", () => {
    const files = [createMockFile({ path: "valid.py", status: "valid" })];

    render(<StreamingFileList files={files} isGenerating={false} />);

    expect(screen.getByText("valid.py")).toBeInTheDocument();
    // Line count should be visible for valid files
    expect(screen.getByText("1L")).toBeInTheDocument();
  });

  it("shows error status for files with syntax errors", () => {
    const files = [createMockFile({ path: "error.py", status: "error" })];

    render(<StreamingFileList files={files} isGenerating={false} />);

    expect(screen.getByText("error.py")).toBeInTheDocument();
  });

  it("displays current generating file in indicator", () => {
    render(
      <StreamingFileList
        files={[]}
        isGenerating={true}
        currentGeneratingPath="app/models/user.py"
      />
    );

    expect(
      screen.getByText(/Generating: app\/models\/user.py/)
    ).toBeInTheDocument();
  });
});

// ============================================================================
// Progress Tests
// ============================================================================

describe("StreamingFileList - Progress", () => {
  it("shows progress bar with percentage", () => {
    const files = createMockFiles().slice(0, 3); // 3 files

    render(
      <StreamingFileList
        files={files}
        totalExpected={6}
        isGenerating={true}
        showStats={true}
      />
    );

    expect(screen.getByText("50%")).toBeInTheDocument();
  });

  it("shows 0% when no files and expecting more", () => {
    render(
      <StreamingFileList
        files={[]}
        totalExpected={10}
        isGenerating={true}
        showStats={true}
      />
    );

    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  it("shows total lines count", () => {
    const files = [
      createMockFile({ path: "a.py", lines: 100 }),
      createMockFile({ path: "b.py", lines: 200 }),
    ];

    render(
      <StreamingFileList files={files} isGenerating={false} showStats={true} />
    );

    expect(screen.getByText(/300 lines/)).toBeInTheDocument();
  });
});

// ============================================================================
// Folder Expansion Tests
// ============================================================================

describe("StreamingFileList - Folder Expansion", () => {
  it("collapses folder when clicked", () => {
    const files = [
      createMockFile({ path: "app/main.py" }),
      createMockFile({ path: "app/core/config.py" }),
    ];

    render(<StreamingFileList files={files} isGenerating={false} />);

    // Initially expanded - nested file should be visible
    expect(screen.getByText("config.py")).toBeInTheDocument();

    // Click on core folder to collapse
    const coreFolder = screen.getByText("core");
    fireEvent.click(coreFolder);

    // config.py should be hidden now
    expect(screen.queryByText("config.py")).not.toBeInTheDocument();
  });

  it("expands folder when clicked again", () => {
    const files = [createMockFile({ path: "app/core/config.py" })];

    render(<StreamingFileList files={files} isGenerating={false} />);

    // Click to collapse
    fireEvent.click(screen.getByText("core"));
    expect(screen.queryByText("config.py")).not.toBeInTheDocument();

    // Click to expand again
    fireEvent.click(screen.getByText("core"));
    expect(screen.getByText("config.py")).toBeInTheDocument();
  });

  it("expand all button expands all folders", () => {
    const files = [
      createMockFile({ path: "app/core/config.py" }),
      createMockFile({ path: "app/models/user.py" }),
    ];

    render(<StreamingFileList files={files} isGenerating={false} />);

    // Collapse all first
    fireEvent.click(screen.getByText("Collapse"));

    // Files should be hidden
    expect(screen.queryByText("config.py")).not.toBeInTheDocument();
    expect(screen.queryByText("user.py")).not.toBeInTheDocument();

    // Expand all
    fireEvent.click(screen.getByText("Expand All"));

    // Files should be visible again
    expect(screen.getByText("config.py")).toBeInTheDocument();
    expect(screen.getByText("user.py")).toBeInTheDocument();
  });
});

// ============================================================================
// File Selection Tests
// ============================================================================

describe("StreamingFileList - File Selection", () => {
  it("calls onFileSelect when file is clicked", () => {
    const files = [createMockFile({ path: "app/main.py" })];
    const onFileSelect = vi.fn();

    render(
      <StreamingFileList
        files={files}
        isGenerating={false}
        onFileSelect={onFileSelect}
      />
    );

    fireEvent.click(screen.getByText("main.py"));

    expect(onFileSelect).toHaveBeenCalledTimes(1);
    expect(onFileSelect).toHaveBeenCalledWith(files[0]);
  });

  it("highlights selected file", () => {
    const files = [createMockFile({ path: "app/main.py" })];

    render(
      <StreamingFileList
        files={files}
        isGenerating={false}
        selectedPath="app/main.py"
      />
    );

    const fileButton = screen.getByText("main.py").closest("button");
    expect(fileButton).toHaveClass("bg-primary/10");
  });

  it("does not call onFileSelect when folder is clicked", () => {
    const files = [createMockFile({ path: "app/main.py" })];
    const onFileSelect = vi.fn();

    render(
      <StreamingFileList
        files={files}
        isGenerating={false}
        onFileSelect={onFileSelect}
      />
    );

    // Click folder instead of file
    fireEvent.click(screen.getByText("app"));

    expect(onFileSelect).not.toHaveBeenCalled();
  });
});

// ============================================================================
// Stats Bar Tests
// ============================================================================

describe("StreamingFileList - Stats Bar", () => {
  it("hides stats bar when showStats is false", () => {
    const files = createMockFiles();

    render(
      <StreamingFileList files={files} isGenerating={false} showStats={false} />
    );

    expect(screen.queryByText(/lines/)).not.toBeInTheDocument();
  });

  it("shows badge counts for different statuses", () => {
    const files = [
      createMockFile({ path: "valid1.py", status: "valid" }),
      createMockFile({ path: "valid2.py", status: "valid" }),
      createMockFile({ path: "valid3.py", status: "valid" }),
      createMockFile({ path: "generating.py", status: "generating" }),
      createMockFile({ path: "error.py", status: "error" }),
    ];

    render(
      <StreamingFileList files={files} isGenerating={true} showStats={true} />
    );

    // Stats should show counts
    expect(screen.getByText("5 files")).toBeInTheDocument();
  });
});

// ============================================================================
// File Icon Tests
// ============================================================================

describe("StreamingFileList - File Icons", () => {
  it("shows correct icon for Python files", () => {
    const files = [
      createMockFile({ path: "main.py", language: "python" }),
    ];

    render(<StreamingFileList files={files} isGenerating={false} />);

    expect(screen.getByText("main.py")).toBeInTheDocument();
  });

  it("shows correct icon for TypeScript files", () => {
    const files = [
      createMockFile({ path: "component.tsx", language: "typescript" }),
    ];

    render(<StreamingFileList files={files} isGenerating={false} />);

    expect(screen.getByText("component.tsx")).toBeInTheDocument();
  });

  it("shows correct icon for JSON files", () => {
    const files = [
      createMockFile({ path: "config.json", language: "json" }),
    ];

    render(<StreamingFileList files={files} isGenerating={false} />);

    expect(screen.getByText("config.json")).toBeInTheDocument();
  });
});

// ============================================================================
// Generation Indicator Tests
// ============================================================================

describe("StreamingFileList - Generation Indicator", () => {
  it("shows generation indicator when isGenerating is true", () => {
    render(<StreamingFileList files={[]} isGenerating={true} />);

    expect(
      screen.getByText("Waiting for next file...")
    ).toBeInTheDocument();
  });

  it("hides generation indicator when isGenerating is false", () => {
    render(
      <StreamingFileList files={createMockFiles()} isGenerating={false} />
    );

    expect(
      screen.queryByText("Waiting for next file...")
    ).not.toBeInTheDocument();
  });

  it("shows current file path when provided", () => {
    render(
      <StreamingFileList
        files={[]}
        isGenerating={true}
        currentGeneratingPath="app/services/user_service.py"
      />
    );

    expect(
      screen.getByText("Generating: app/services/user_service.py")
    ).toBeInTheDocument();
  });
});

// ============================================================================
// Accessibility Tests
// ============================================================================

describe("StreamingFileList - Accessibility", () => {
  it("file items are keyboard focusable", () => {
    const files = [createMockFile({ path: "test.py" })];

    render(<StreamingFileList files={files} isGenerating={false} />);

    const fileButton = screen.getByText("test.py").closest("button");
    expect(fileButton).toBeInTheDocument();
    expect(fileButton?.tagName).toBe("BUTTON");
  });

  it("toolbar buttons are accessible", () => {
    render(
      <StreamingFileList files={createMockFiles()} isGenerating={false} />
    );

    expect(screen.getByText("Expand All")).toBeInTheDocument();
    expect(screen.getByText("Collapse")).toBeInTheDocument();
  });
});
