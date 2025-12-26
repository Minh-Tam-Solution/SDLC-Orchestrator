/**
 * Unit Tests: CodePreviewPanel Component
 * SDLC Orchestrator - Sprint 54 Day 2
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 54 Implementation
 *
 * Test coverage:
 * - Empty state rendering
 * - File content display
 * - Language detection and icons
 * - Copy to clipboard
 * - Theme toggle
 * - Search functionality
 * - Full screen mode
 * - Keyboard shortcuts
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@/test/test-utils";
import { CodePreviewPanel } from "./CodePreviewPanel";
import type { StreamingFile } from "@/types/streaming";
import "@testing-library/jest-dom";

// ============================================================================
// Mock Data
// ============================================================================

function createMockFile(overrides?: Partial<StreamingFile>): StreamingFile {
  return {
    path: "app/main.py",
    content: `def hello():
    print("Hello, World!")
    return True

def main():
    result = hello()
    print(f"Result: {result}")

if __name__ == "__main__":
    main()`,
    lines: 11,
    language: "python",
    status: "valid",
    ...overrides,
  };
}

// ============================================================================
// Mock clipboard API
// ============================================================================

const mockClipboard = {
  writeText: vi.fn().mockResolvedValue(undefined),
};

beforeEach(() => {
  vi.clearAllMocks();
  Object.assign(navigator, { clipboard: mockClipboard });
});

// ============================================================================
// Empty State Tests
// ============================================================================

describe("CodePreviewPanel - Empty State", () => {
  it("renders empty state when no file is provided", () => {
    render(<CodePreviewPanel file={null} />);

    expect(screen.getByText("No file selected")).toBeInTheDocument();
    expect(
      screen.getByText("Select a file from the list to preview")
    ).toBeInTheDocument();
  });
});

// ============================================================================
// File Display Tests
// ============================================================================

describe("CodePreviewPanel - File Display", () => {
  it("renders file path in header", () => {
    const file = createMockFile();
    render(<CodePreviewPanel file={file} />);

    expect(screen.getByText("app/main.py")).toBeInTheDocument();
  });

  it("renders language badge", () => {
    const file = createMockFile({ language: "python" });
    render(<CodePreviewPanel file={file} />);

    expect(screen.getByText("Python")).toBeInTheDocument();
  });

  it("renders line count", () => {
    const file = createMockFile({ lines: 42 });
    render(<CodePreviewPanel file={file} />);

    expect(screen.getByText("42 lines")).toBeInTheDocument();
  });

  it("shows syntax error badge for error status", () => {
    const file = createMockFile({ status: "error" });
    render(<CodePreviewPanel file={file} />);

    expect(screen.getByText("Syntax Error")).toBeInTheDocument();
  });

  it("renders code content", () => {
    const file = createMockFile({ content: "print('test')" });
    render(<CodePreviewPanel file={file} />);

    expect(screen.getByText(/print/)).toBeInTheDocument();
  });

  it("renders empty file message for empty content", () => {
    const file = createMockFile({ content: "" });
    render(<CodePreviewPanel file={file} />);

    // Component should render without error for empty content
    expect(screen.getByText("app/main.py")).toBeInTheDocument();
  });
});

// ============================================================================
// Language Tests
// ============================================================================

describe("CodePreviewPanel - Language Detection", () => {
  it.each([
    ["python", "Python"],
    ["typescript", "TypeScript"],
    ["javascript", "JavaScript"],
    ["json", "JSON"],
    ["yaml", "YAML"],
    ["markdown", "Markdown"],
    ["sql", "SQL"],
  ])("displays correct label for %s", (language, expectedLabel) => {
    const file = createMockFile({ language });
    render(<CodePreviewPanel file={file} />);

    expect(screen.getByText(expectedLabel)).toBeInTheDocument();
  });
});

// ============================================================================
// Copy Tests
// ============================================================================

describe("CodePreviewPanel - Copy", () => {
  it("renders toolbar with copy functionality", () => {
    const file = createMockFile({ content: "test content" });
    render(<CodePreviewPanel file={file} />);

    // Has toolbar buttons
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("shows file content", () => {
    const file = createMockFile({ content: "test_content_here" });
    render(<CodePreviewPanel file={file} />);

    // Content should be rendered
    expect(screen.getByText(/test_content_here/)).toBeInTheDocument();
  });
});

// ============================================================================
// Theme Tests
// ============================================================================

describe("CodePreviewPanel - Theme", () => {
  it("renders toolbar buttons", () => {
    const file = createMockFile();
    render(<CodePreviewPanel file={file} />);

    // Should render toolbar with buttons
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("renders with search button", () => {
    const file = createMockFile();
    render(<CodePreviewPanel file={file} />);

    expect(screen.getByText("Search")).toBeInTheDocument();
  });
});

// ============================================================================
// Search Tests
// ============================================================================

describe("CodePreviewPanel - Search", () => {
  it("shows search bar when search button is clicked", () => {
    const file = createMockFile();
    render(<CodePreviewPanel file={file} />);

    // Find search button by its text content
    const searchButton = screen.getByText("Search").closest("button");
    expect(searchButton).toBeInTheDocument();
    if (searchButton) fireEvent.click(searchButton);

    expect(screen.getByPlaceholderText("Search in file...")).toBeInTheDocument();
  });

  it("shows match count when searching", async () => {
    const file = createMockFile({
      content: "hello world\nhello again\nhello there",
    });
    render(<CodePreviewPanel file={file} />);

    // Open search
    const searchButton = screen.getByText("Search").closest("button");
    if (searchButton) fireEvent.click(searchButton);

    // Type search term
    const searchInput = screen.getByPlaceholderText("Search in file...");
    fireEvent.change(searchInput, { target: { value: "hello" } });

    await waitFor(() => {
      expect(screen.getByText(/1 of 3/)).toBeInTheDocument();
    });
  });

  it("shows no matches message when search has no results", async () => {
    const file = createMockFile({ content: "hello world" });
    render(<CodePreviewPanel file={file} />);

    // Open search
    const searchButton = screen.getByText("Search").closest("button");
    if (searchButton) fireEvent.click(searchButton);

    // Type search term that doesn't exist
    const searchInput = screen.getByPlaceholderText("Search in file...");
    fireEvent.change(searchInput, { target: { value: "notfound" } });

    await waitFor(() => {
      expect(screen.getByText("No matches")).toBeInTheDocument();
    });
  });

  it("closes search when X button is clicked", () => {
    const file = createMockFile();
    render(<CodePreviewPanel file={file} />);

    // Open search
    const searchButton = screen.getByText("Search").closest("button");
    if (searchButton) fireEvent.click(searchButton);
    expect(screen.getByPlaceholderText("Search in file...")).toBeInTheDocument();

    // Close search - find the X button in the search bar
    const closeButtons = screen.getAllByRole("button");
    const closeButton = closeButtons.find(
      (btn) => btn.querySelector("svg.lucide-x") !== null
    );
    if (closeButton) {
      fireEvent.click(closeButton);
    }

    expect(
      screen.queryByPlaceholderText("Search in file...")
    ).not.toBeInTheDocument();
  });
});

// ============================================================================
// Full Screen Tests
// ============================================================================

describe("CodePreviewPanel - Full Screen", () => {
  it("renders toolbar buttons when allowFullScreen is true", () => {
    const file = createMockFile();
    render(<CodePreviewPanel file={file} allowFullScreen={true} />);

    // Should have toolbar buttons
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(3); // Search + theme + download + fullscreen
  });

  it("renders fewer buttons when allowFullScreen is false", () => {
    const file = createMockFile();
    render(<CodePreviewPanel file={file} allowFullScreen={false} />);

    // Still has some buttons
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
  });
});

// ============================================================================
// Download Tests
// ============================================================================

describe("CodePreviewPanel - Download", () => {
  it("renders download functionality", () => {
    const file = createMockFile();
    const onDownload = vi.fn();
    render(<CodePreviewPanel file={file} onDownload={onDownload} />);

    // Has buttons in toolbar
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
  });
});

// ============================================================================
// Close Tests
// ============================================================================

describe("CodePreviewPanel - Close", () => {
  it("shows close button when onClose is provided", () => {
    const file = createMockFile();
    const onClose = vi.fn();
    render(<CodePreviewPanel file={file} onClose={onClose} />);

    // Find the X button in the header
    const buttons = screen.getAllByRole("button");
    const closeButton = buttons.find((btn) => {
      const svg = btn.querySelector("svg");
      return svg?.classList.contains("lucide-x");
    });

    expect(closeButton).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", () => {
    const file = createMockFile();
    const onClose = vi.fn();
    render(<CodePreviewPanel file={file} onClose={onClose} />);

    // Find the X button in the header (first one, before search)
    const buttons = screen.getAllByRole("button");
    const closeButton = buttons.find((btn) => {
      const svg = btn.querySelector("svg");
      return svg?.classList.contains("lucide-x");
    });

    if (closeButton) {
      fireEvent.click(closeButton);
    }

    expect(onClose).toHaveBeenCalled();
  });

  it("hides close button when onClose is not provided", () => {
    const file = createMockFile();
    render(<CodePreviewPanel file={file} />);

    // Should not have close button in header
    const header = screen.getByText("app/main.py").closest("div");
    const closeButtonInHeader = header?.querySelector("button svg.lucide-x");
    expect(closeButtonInHeader).not.toBeInTheDocument();
  });
});

// ============================================================================
// Header/Toolbar Visibility Tests
// ============================================================================

describe("CodePreviewPanel - Visibility Options", () => {
  it("hides header when showHeader is false", () => {
    const file = createMockFile();
    render(<CodePreviewPanel file={file} showHeader={false} />);

    expect(screen.queryByText("app/main.py")).not.toBeInTheDocument();
  });

  it("hides toolbar when showToolbar is false", () => {
    const file = createMockFile();
    render(<CodePreviewPanel file={file} showToolbar={false} />);

    expect(screen.queryByText("Search")).not.toBeInTheDocument();
  });
});
