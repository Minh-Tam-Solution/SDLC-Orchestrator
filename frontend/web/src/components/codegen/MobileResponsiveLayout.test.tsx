/**
 * Unit Tests: MobileResponsiveLayout Component
 * SDLC Orchestrator - Sprint 54 Day 5
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 54 Implementation
 *
 * Test coverage:
 * - Desktop layout (3-column)
 * - Panel collapse/expand
 * - Full screen mode
 * - Custom props
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@/test/test-utils";
import { MobileResponsiveLayout } from "./MobileResponsiveLayout";
import "@testing-library/jest-dom";

// ============================================================================
// Mock useMediaQuery hooks
// ============================================================================

const mockUseIsMobile = vi.fn(() => false);
const mockUseIsTablet = vi.fn(() => false);

vi.mock("@/hooks/useMediaQuery", () => ({
  useIsMobile: () => mockUseIsMobile(),
  useIsTablet: () => mockUseIsTablet(),
}));

// ============================================================================
// Test Data
// ============================================================================

const LeftPanel = () => <div data-testid="left-panel">Left Content</div>;
const MainContent = () => <div data-testid="main-content">Main Content</div>;
const RightPanel = () => <div data-testid="right-panel">Right Content</div>;

// ============================================================================
// Desktop Layout Tests
// ============================================================================

describe("MobileResponsiveLayout - Desktop", () => {
  beforeEach(() => {
    mockUseIsMobile.mockReturnValue(false);
    mockUseIsTablet.mockReturnValue(false);
  });

  it("renders all three panels on desktop when expanded", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
        rightPanel={<RightPanel />}
        showLeftByDefault={true}
        showRightByDefault={true}
      />
    );

    expect(screen.getByTestId("left-panel")).toBeInTheDocument();
    expect(screen.getByTestId("main-content")).toBeInTheDocument();
    expect(screen.getByTestId("right-panel")).toBeInTheDocument();
  });

  it("renders without right panel when not provided", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
      />
    );

    expect(screen.getByTestId("left-panel")).toBeInTheDocument();
    expect(screen.getByTestId("main-content")).toBeInTheDocument();
    expect(screen.queryByTestId("right-panel")).not.toBeInTheDocument();
  });

  it("shows panel titles", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
        leftPanelTitle="File Explorer"
      />
    );

    expect(screen.getByText("File Explorer")).toBeInTheDocument();
  });

  it("has full screen button", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
      />
    );

    // Find button with maximize icon
    const buttons = screen.getAllByRole("button");
    const fullScreenButton = buttons.find(
      (btn) => btn.getAttribute("title") === "Full screen"
    );
    expect(fullScreenButton).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
        className="custom-layout"
      />
    );

    expect(container.firstChild).toHaveClass("custom-layout");
  });
});

// ============================================================================
// Panel Collapse Tests
// ============================================================================

describe("MobileResponsiveLayout - Panel Collapse", () => {
  beforeEach(() => {
    mockUseIsMobile.mockReturnValue(false);
    mockUseIsTablet.mockReturnValue(false);
  });

  it("can collapse left panel", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
        showLeftByDefault={true}
      />
    );

    // Left panel content should be visible initially
    expect(screen.getByTestId("left-panel")).toBeInTheDocument();

    // Find and click collapse button
    const collapseButton = screen.getByTitle("Collapse Files panel");
    fireEvent.click(collapseButton);

    // Left panel content should be hidden
    expect(screen.queryByTestId("left-panel")).not.toBeInTheDocument();
  });

  it("can expand collapsed left panel", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
        showLeftByDefault={false}
      />
    );

    // Left panel should be collapsed
    expect(screen.queryByTestId("left-panel")).not.toBeInTheDocument();

    // Find and click expand button
    const expandButton = screen.getByTitle("Show Files panel");
    fireEvent.click(expandButton);

    // Left panel should be visible
    expect(screen.getByTestId("left-panel")).toBeInTheDocument();
  });

  it("respects showLeftByDefault prop", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
        showLeftByDefault={false}
      />
    );

    expect(screen.queryByTestId("left-panel")).not.toBeInTheDocument();
  });

  it("respects showRightByDefault prop", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
        rightPanel={<RightPanel />}
        showRightByDefault={true}
      />
    );

    expect(screen.getByTestId("right-panel")).toBeInTheDocument();
  });
});

// ============================================================================
// Full Screen Mode Tests
// ============================================================================

describe("MobileResponsiveLayout - Full Screen", () => {
  beforeEach(() => {
    mockUseIsMobile.mockReturnValue(false);
    mockUseIsTablet.mockReturnValue(false);
  });

  it("can toggle full screen mode", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
      />
    );

    // Click full screen button
    const fullScreenButton = screen.getByTitle("Full screen");
    fireEvent.click(fullScreenButton);

    // Should show full screen header
    expect(screen.getByText("Code Generation")).toBeInTheDocument();

    // Should have minimize button
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("full screen mode shows all panels when expanded", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
        rightPanel={<RightPanel />}
        showLeftByDefault={true}
        showRightByDefault={true}
      />
    );

    // Enter full screen
    const fullScreenButton = screen.getByTitle("Full screen");
    fireEvent.click(fullScreenButton);

    // All content should still be visible
    expect(screen.getByTestId("left-panel")).toBeInTheDocument();
    expect(screen.getByTestId("main-content")).toBeInTheDocument();
    expect(screen.getByTestId("right-panel")).toBeInTheDocument();
  });
});

// ============================================================================
// Mobile Layout Tests
// ============================================================================

describe("MobileResponsiveLayout - Mobile", () => {
  beforeEach(() => {
    mockUseIsMobile.mockReturnValue(true);
    mockUseIsTablet.mockReturnValue(false);
  });

  it("renders mobile header with toggles", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
        rightPanel={<RightPanel />}
      />
    );

    expect(screen.getByText("Code Preview")).toBeInTheDocument();
  });

  it("shows main content by default", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
      />
    );

    expect(screen.getByTestId("main-content")).toBeInTheDocument();
  });

  it("has menu button for left panel", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
      />
    );

    // Should have at least one button (menu)
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
  });
});

// ============================================================================
// Tablet Layout Tests
// ============================================================================

describe("MobileResponsiveLayout - Tablet", () => {
  beforeEach(() => {
    mockUseIsMobile.mockReturnValue(false);
    mockUseIsTablet.mockReturnValue(true);
  });

  it("shows main content on tablet", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
      />
    );

    expect(screen.getByTestId("main-content")).toBeInTheDocument();
  });

  it("has menu button for left drawer", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
      />
    );

    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("shows panel title in toolbar", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
        leftPanelTitle="Files"
      />
    );

    expect(screen.getByText("Files")).toBeInTheDocument();
  });
});

// ============================================================================
// Custom Width Tests
// ============================================================================

describe("MobileResponsiveLayout - Custom Widths", () => {
  beforeEach(() => {
    mockUseIsMobile.mockReturnValue(false);
    mockUseIsTablet.mockReturnValue(false);
  });

  it("accepts custom left panel width", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
        leftPanelWidth="350px"
        showLeftByDefault={true}
      />
    );

    // Component should render without errors
    expect(screen.getByTestId("left-panel")).toBeInTheDocument();
  });

  it("accepts custom right panel width", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
        rightPanel={<RightPanel />}
        rightPanelWidth="400px"
        showRightByDefault={true}
      />
    );

    // Component should render without errors
    expect(screen.getByTestId("right-panel")).toBeInTheDocument();
  });
});

// ============================================================================
// Panel Titles Tests
// ============================================================================

describe("MobileResponsiveLayout - Panel Titles", () => {
  beforeEach(() => {
    mockUseIsMobile.mockReturnValue(false);
    mockUseIsTablet.mockReturnValue(false);
  });

  it("shows custom left panel title", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
        leftPanelTitle="File Browser"
      />
    );

    expect(screen.getByText("File Browser")).toBeInTheDocument();
  });

  it("shows custom right panel title", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
        rightPanel={<RightPanel />}
        rightPanelTitle="Settings"
        showRightByDefault={true}
      />
    );

    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("uses default titles when not provided", () => {
    render(
      <MobileResponsiveLayout
        leftPanel={<LeftPanel />}
        mainContent={<MainContent />}
        rightPanel={<RightPanel />}
        showRightByDefault={true}
      />
    );

    expect(screen.getByText("Files")).toBeInTheDocument();
    expect(screen.getByText("Properties")).toBeInTheDocument();
  });
});
