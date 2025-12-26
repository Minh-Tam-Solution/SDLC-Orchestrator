/**
 * Unit Tests: DownloadManager Component
 * SDLC Orchestrator - Sprint 54 Day 4
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 54 Implementation
 *
 * Test coverage:
 * - Empty state (no files)
 * - Button rendering
 * - Dialog opening/closing
 * - File selection
 * - Compact mode
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@/test/test-utils";
import { DownloadManager } from "./DownloadManager";
import type { StreamingFile } from "@/types/streaming";
import "@testing-library/jest-dom";

// ============================================================================
// Mock Data
// ============================================================================

function createMockFile(overrides?: Partial<StreamingFile>): StreamingFile {
  return {
    path: "app/main.py",
    content: 'print("hello")',
    lines: 1,
    language: "python",
    status: "valid",
    ...overrides,
  };
}

function createMockFiles(): StreamingFile[] {
  return [
    createMockFile({ path: "app/__init__.py", content: "" }),
    createMockFile({ path: "app/main.py", content: "print('main')" }),
    createMockFile({ path: "app/core/config.py", content: "CONFIG = {}" }),
    createMockFile({ path: "app/core/database.py", content: "DB = None" }),
    createMockFile({ path: "tests/test_main.py", content: "def test(): pass" }),
  ];
}

// ============================================================================
// Mock JSZip
// ============================================================================

vi.mock("jszip", () => {
  return {
    default: vi.fn().mockImplementation(() => ({
      file: vi.fn(),
      generateAsync: vi.fn().mockResolvedValue(new Blob(["test"])),
    })),
  };
});

// ============================================================================
// Empty State Tests
// ============================================================================

describe("DownloadManager - Empty State", () => {
  it("disables button when no files", () => {
    render(<DownloadManager files={[]} />);

    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
  });

  it("shows 0 files in button text when empty", () => {
    render(<DownloadManager files={[]} />);

    expect(screen.getByText(/0 files/)).toBeInTheDocument();
  });
});

// ============================================================================
// Button Rendering Tests
// ============================================================================

describe("DownloadManager - Button Rendering", () => {
  it("shows file count in button", () => {
    const files = createMockFiles();
    render(<DownloadManager files={files} />);

    expect(screen.getByText(/5 files/)).toBeInTheDocument();
  });

  it("renders download icon", () => {
    const files = createMockFiles();
    render(<DownloadManager files={files} />);

    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("is enabled when files are present", () => {
    const files = createMockFiles();
    render(<DownloadManager files={files} />);

    const button = screen.getByRole("button");
    expect(button).not.toBeDisabled();
  });

  it("can be disabled via prop", () => {
    const files = createMockFiles();
    render(<DownloadManager files={files} disabled={true} />);

    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
  });
});

// ============================================================================
// Dialog Tests
// ============================================================================

describe("DownloadManager - Dialog", () => {
  it("opens dialog when button is clicked", () => {
    const files = createMockFiles();
    render(<DownloadManager files={files} />);

    fireEvent.click(screen.getByRole("button"));

    expect(screen.getByText("Download Files")).toBeInTheDocument();
  });

  it("shows file selection instructions", () => {
    const files = createMockFiles();
    render(<DownloadManager files={files} />);

    fireEvent.click(screen.getByRole("button"));

    expect(screen.getByText(/Select files to include/)).toBeInTheDocument();
  });

  it("shows file count in dialog", () => {
    const files = createMockFiles();
    render(<DownloadManager files={files} />);

    fireEvent.click(screen.getByRole("button"));

    expect(screen.getByText(/5 of 5 files selected/)).toBeInTheDocument();
  });

  it("has select all button", () => {
    const files = createMockFiles();
    render(<DownloadManager files={files} />);

    fireEvent.click(screen.getByRole("button"));

    expect(screen.getByText(/Deselect All/)).toBeInTheDocument();
  });

  it("has download button in dialog", () => {
    const files = createMockFiles();
    render(<DownloadManager files={files} />);

    fireEvent.click(screen.getByRole("button"));

    // Find download button in dialog footer
    const buttons = screen.getAllByRole("button");
    const downloadButton = buttons.find((btn) =>
      btn.textContent?.includes("Download")
    );
    expect(downloadButton).toBeInTheDocument();
  });

  it("has cancel button", () => {
    const files = createMockFiles();
    render(<DownloadManager files={files} />);

    fireEvent.click(screen.getByRole("button"));

    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });
});

// ============================================================================
// Compact Mode Tests
// ============================================================================

describe("DownloadManager - Compact Mode", () => {
  it("shows simple button in compact mode", () => {
    const files = createMockFiles();
    render(<DownloadManager files={files} compact={true} />);

    expect(screen.getByText("Download ZIP")).toBeInTheDocument();
  });

  it("does not show file count in compact mode", () => {
    const files = createMockFiles();
    render(<DownloadManager files={files} compact={true} />);

    expect(screen.queryByText(/5 files/)).not.toBeInTheDocument();
  });

  it("does not open dialog in compact mode", () => {
    const files = createMockFiles();
    render(<DownloadManager files={files} compact={true} />);

    fireEvent.click(screen.getByRole("button"));

    expect(screen.queryByText("Download Files")).not.toBeInTheDocument();
  });
});

// ============================================================================
// Project Name Tests
// ============================================================================

describe("DownloadManager - Project Name", () => {
  it("accepts custom project name", () => {
    const files = createMockFiles();
    render(<DownloadManager files={files} projectName="my-awesome-project" />);

    // Component should render without errors
    expect(screen.getByRole("button")).toBeInTheDocument();
  });
});

// ============================================================================
// Class Name Tests
// ============================================================================

describe("DownloadManager - Styling", () => {
  it("applies custom className", () => {
    const files = createMockFiles();
    render(<DownloadManager files={files} className="custom-class" />);

    const button = screen.getByRole("button");
    expect(button).toHaveClass("custom-class");
  });
});
